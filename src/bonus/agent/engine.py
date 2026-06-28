"""推理引擎 - 核心调度器，控制推理流程"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from bonus.agent.causal_chain import ChainBuilder
from bonus.agent.state_machine import StepwiseStateMachine, StepwiseState
from bonus.llm.client import LLMClient
from bonus.llm.parser import (
    parse_causal_chain_response,
    parse_deep_inference_response,
    parse_stepwise_node_response,
    parse_fundamental_assessment,
)
from bonus.llm.prompts import (
    CAUSAL_CHAIN_PROMPT,
    CONFIRMATION_PROMPT,
    DEEP_INFERENCE_PROMPT,
    FUNDAMENTAL_ANALYSIS_PROMPT,
    SYSTEM_PROMPT,
)
from bonus.models.fundamental import StockFundamental
from bonus.models.inference import CausalChain, CausalEdge, CausalNode, NodeType
from bonus.models.news import NewsItem
from bonus.models.stock import StockRecommendation
from bonus.skills.base import BaseSkill
from bonus.skills.fundamental_base import BaseFundamentalSkill
from bonus.utils.async_utils import gather_with_limit
from bonus.utils.logger import get_logger

logger = get_logger(__name__)

# 进度回调类型: (status_message: str, progress: float 0.0~1.0)
ProgressCallback = Callable[[str, float], Any]

# 逐步确认回调类型: (node: CausalNode) -> (confirmed: bool, modified_node: Optional[CausalNode])
ConfirmCallback = Callable[[CausalNode], Any]


class CausalEngine:
    """因果推理引擎，控制整个分析流程"""

    def __init__(
        self,
        skills: Dict[str, BaseSkill],
        llm_client: LLMClient,
        mode: str = "auto",
        max_inference_depth: int = 5,
        min_confidence: float = 0.5,
        fundamental_skills: Optional[Dict[str, BaseFundamentalSkill]] = None,
    ):
        self.skills = skills
        self.llm = llm_client
        self.mode = mode  # "auto" 或 "stepwise"
        self.max_inference_depth = max_inference_depth
        self.min_confidence = min_confidence
        self.fundamental_skills = fundamental_skills or {}
        self._cancel = False

    def cancel(self) -> None:
        """取消当前推理"""
        self._cancel = True
        logger.info("推理已请求取消")

    async def run(
        self,
        query: str = "今日热点",
        progress_callback: Optional[ProgressCallback] = None,
        confirm_callback: Optional[ConfirmCallback] = None,
    ) -> Tuple[CausalChain, List[StockRecommendation]]:
        """
        运行完整推理流程。

        Args:
            query: 搜索查询词
            progress_callback: 进度回调函数
            confirm_callback: 逐步确认回调函数（stepwise 模式必需）

        Returns:
            (因果链, 股票推荐列表)
        """
        self._cancel = False

        async def _progress(msg: str, pct: float):
            if progress_callback:
                result = progress_callback(msg, pct)
                if asyncio.iscoroutine(result):
                    await result

        # 1. 并发抓取所有 Skill 的新闻
        await _progress("正在抓取财经新闻...", 0.1)
        news_list = await self._gather_news(query, _progress)

        if self._cancel:
            return CausalChain(query=query), []

        if not news_list:
            await _progress("未获取到任何新闻，推理终止", 1.0)
            logger.warning("未获取到任何新闻")
            return CausalChain(query=query), []

        await _progress(f"已获取 {len(news_list)} 条新闻，开始因果推理...", 0.3)

        # 2. LLM 生成初始因果推断链
        chain = await self._initial_causal_chain(news_list, query, _progress)

        if self._cancel:
            return chain, []

        # 3. 根据模式分支
        if self.mode == "auto":
            final_chain = await self._auto_inference(chain, news_list, _progress)
        else:
            final_chain = await self._stepwise_inference(
                chain, news_list, _progress, confirm_callback
            )

        # 4. 提取股票推荐
        await _progress("正在整理推荐结果...", 0.95)
        recommendations = ChainBuilder.extract_recommendations(
            final_chain, self.min_confidence
        )

        # 5. 基本面数据验证（若有基本面 Skill）
        if recommendations and self.fundamental_skills:
            recommendations = await self._enhance_with_fundamentals(
                recommendations, _progress
            )

        await _progress("分析完成！", 1.0)
        return final_chain, recommendations

    async def _gather_news(
        self,
        query: str,
        progress: Optional[ProgressCallback] = None,
    ) -> List[NewsItem]:
        """并发调用所有 Skill 抓取新闻"""
        if not self.skills:
            logger.warning("没有可用的 Skill")
            return []

        coroutines = []
        skill_names = []
        for name, skill in self.skills.items():
            top_k = skill.config.get("top_k", 10)
            coroutines.append(skill.safe_fetch(query, top_k))
            skill_names.append(name)

        if progress:
            result = progress(f"正在抓取: {', '.join(skill_names)}...", 0.15)
            if asyncio.iscoroutine(result):
                await result

        results = await gather_with_limit(coroutines, limit=5)

        # 合并所有新闻
        all_news: List[NewsItem] = []
        for news_items in results:
            all_news.extend(news_items)

        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title_key = news.title.strip()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)

        logger.info(f"合并去重后共 {len(unique_news)} 条新闻")
        return unique_news

    async def _initial_causal_chain(
        self,
        news_list: List[NewsItem],
        query: str,
        progress: Optional[ProgressCallback] = None,
    ) -> CausalChain:
        """调用 LLM 生成初始因果链"""
        if progress:
            result = progress("正在生成因果推理链...", 0.4)
            if asyncio.iscoroutine(result):
                await result

        news_text = ChainBuilder.build_news_context(news_list)
        prompt = CAUSAL_CHAIN_PROMPT.format(query=query, news_text=news_text)

        logger.info("请求 LLM 生成初始因果链...")
        response = await self.llm.chat_json(prompt, system_prompt=SYSTEM_PROMPT)
        chain = parse_causal_chain_response(response, query=query)

        logger.info(
            f"初始因果链生成: {len(chain.nodes)} 节点, {len(chain.edges)} 边"
        )
        return chain

    async def _auto_inference(
        self,
        chain: CausalChain,
        news_list: List[NewsItem],
        progress: Optional[ProgressCallback] = None,
    ) -> CausalChain:
        """全自动模式：深度推理扩展因果链"""
        existing_stocks = set()
        for node in chain.nodes:
            existing_stocks.update(node.stocks)

        for depth in range(self.max_inference_depth):
            if self._cancel:
                break

            pct = 0.5 + 0.1 * depth
            if progress:
                result = progress(f"正在进行深度推理 (第 {depth + 1} 轮)...", pct)
                if asyncio.iscoroutine(result):
                    await result

            chain_text = ChainBuilder.build_chain_context(chain)
            stocks_str = ", ".join(existing_stocks) if existing_stocks else "无"
            prompt = DEEP_INFERENCE_PROMPT.format(
                chain_text=chain_text,
                existing_stocks=stocks_str,
            )

            try:
                response = await self.llm.chat_json(prompt, system_prompt=SYSTEM_PROMPT)
            except Exception as e:
                logger.error(f"深度推理第 {depth + 1} 轮失败: {e}")
                break

            new_nodes, new_edges = parse_deep_inference_response(response, chain)

            if not new_nodes:
                logger.info(f"深度推理第 {depth + 1} 轮未产生新节点，停止")
                break

            # 合并到因果链
            ChainBuilder.merge_into_chain(chain, new_nodes, new_edges)

            # 更新已有股票集合
            for node in new_nodes:
                existing_stocks.update(node.stocks)

            logger.info(
                f"深度推理第 {depth + 1} 轮: 新增 {len(new_nodes)} 节点, {len(new_edges)} 边"
            )

        return chain

    async def _stepwise_inference(
        self,
        initial_chain: CausalChain,
        news_list: List[NewsItem],
        progress: Optional[ProgressCallback] = None,
        confirm_callback: Optional[ConfirmCallback] = None,
    ) -> CausalChain:
        """逐步确认模式：每步需用户确认"""
        if not confirm_callback:
            logger.error("逐步确认模式需要 confirm_callback")
            return initial_chain

        state_machine = StepwiseStateMachine()
        state_machine.transition(StepwiseState.INFERRING)

        # 构建确认后的因果链（只包含用户确认的节点）
        confirmed_chain = CausalChain(query=initial_chain.query)

        # 遍历初始链的节点，逐个确认
        # 按拓扑顺序排序（从根节点开始）
        sorted_nodes = self._topological_sort(initial_chain)

        for node in sorted_nodes:
            if self._cancel:
                break

            if node.type == NodeType.EVENT:
                # 事件节点自动确认（不需要用户确认新闻事实）
                confirmed_chain.add_node(node)
                # 添加对应的边
                for edge in initial_chain.edges:
                    if edge.to_node == node.id:
                        confirmed_chain.add_edge(edge)
                continue

            state_machine.set_current_node(node)

            if progress:
                result = progress(
                    f"等待确认推理步骤: {node.content[:50]}...",
                    0.5,
                )
                if asyncio.iscoroutine(result):
                    await result

            # 调用确认回调，等待用户决策
            result = confirm_callback(node)
            if asyncio.iscoroutine(result):
                confirmed_bool, modified_node = await result
            else:
                confirmed_bool, modified_node = result

            if confirmed_bool:
                final_node = modified_node if modified_node else node
                state_machine.confirm()
                confirmed_chain.add_node(final_node)
                # 添加对应的边
                for edge in initial_chain.edges:
                    if edge.to_node == final_node.id:
                        # 确保父节点也在确认链中
                        if confirmed_chain.get_node(edge.from_node):
                            confirmed_chain.add_edge(edge)

                # 如果用户修改了节点，尝试继续推理
                if modified_node and modified_node.content != node.content:
                    # 基于修改后的节点继续推理下一步
                    await self._continue_stepwise(
                        confirmed_chain, final_node, state_machine,
                        progress, confirm_callback,
                    )
            else:
                state_machine.reject()
                if state_machine.is_max_rejections_reached():
                    logger.warning("达到最大否决次数，终止逐步推理")
                    if progress:
                        result = progress("达到最大否决次数，终止推理", 0.9)
                        if asyncio.iscoroutine(result):
                            await result
                    break
                # 否决后跳过此节点，继续下一个

        state_machine.transition(StepwiseState.COMPLETED)
        return confirmed_chain

    async def _continue_stepwise(
        self,
        chain: CausalChain,
        current_node: CausalNode,
        state_machine: StepwiseStateMachine,
        progress: Optional[ProgressCallback] = None,
        confirm_callback: Optional[ConfirmCallback] = None,
    ) -> None:
        """基于用户修改的节点，请求 LLM 生成下一步推理"""
        if not confirm_callback:
            return

        confirmed_text = state_machine.get_confirmed_summary()

        prompt = CONFIRMATION_PROMPT.format(
            confirmed_nodes=confirmed_text,
            current_node=current_node.model_dump_json(indent=2),
            user_feedback="用户修改了当前节点内容",
        )

        try:
            response = await self.llm.chat_json(prompt, system_prompt=SYSTEM_PROMPT)
        except Exception as e:
            logger.error(f"逐步推理继续失败: {e}")
            return

        next_node, is_final = parse_stepwise_node_response(response)

        if next_node and not is_final:
            next_node.parent_ids = [current_node.id]
            state_machine.set_current_node(next_node)

            if progress:
                result = progress(f"等待确认推理步骤: {next_node.content[:50]}...", 0.6)
                if asyncio.iscoroutine(result):
                    await result

            result = confirm_callback(next_node)
            if asyncio.iscoroutine(result):
                confirmed_bool, modified_node = await result
            else:
                confirmed_bool, modified_node = result

            if confirmed_bool:
                final_node = modified_node if modified_node else next_node
                state_machine.confirm()
                chain.add_node(final_node)
                chain.add_edge(CausalEdge(
                    from_node=current_node.id,
                    to_node=final_node.id,
                    relation="推导至",
                ))

                if not is_final:
                    await self._continue_stepwise(
                        chain, final_node, state_machine, progress, confirm_callback
                    )

    async def _enhance_with_fundamentals(
        self,
        recommendations: List[StockRecommendation],
        progress: Optional[ProgressCallback] = None,
    ) -> List[StockRecommendation]:
        """
        使用基本面 Skill 获取推荐股票的基本面数据，
        并调用 LLM 结合消息面与基本面重新评估置信度。
        """
        if not recommendations or not self.fundamental_skills:
            return recommendations

        total = len(recommendations)
        logger.info(f"开始基本面验证，共 {total} 只推荐股票")

        # 选择第一个可用的基本面 Skill
        fund_skill: Optional[BaseFundamentalSkill] = None
        for skill in self.fundamental_skills.values():
            if skill.enabled:
                fund_skill = skill
                break

        if not fund_skill:
            logger.warning("没有可用的基本面 Skill，跳过基本面验证")
            return recommendations

        # 收集所有股票代码
        stock_codes = [r.stock.code for r in recommendations]

        if progress:
            result = progress(
                f"正在通过 {fund_skill.name} 获取 {total} 只股票基本面数据...",
                0.96,
            )
            if asyncio.iscoroutine(result):
                await result

        # 批量获取基本面数据
        fundamentals = await fund_skill.fetch_fundamentals(stock_codes)
        fund_map: Dict[str, StockFundamental] = {f.code: f for f in fundamentals}

        logger.info(f"成功获取 {len(fund_map)}/{total} 只股票的基本面数据")

        # 逐只股票用 LLM 评估
        for i, rec in enumerate(recommendations):
            if self._cancel:
                break

            fund = fund_map.get(rec.stock.code)
            if not fund:
                logger.debug(f"未获取到 {rec.stock.code} 基本面数据，保持原置信度")
                continue

            # 回填股票名称和行业
            if fund.name and not rec.stock.name:
                rec.stock.name = fund.name
            if fund.industry and not rec.stock.industry:
                rec.stock.industry = fund.industry

            if progress:
                result = progress(
                    f"正在评估 {rec.stock.name or rec.stock.code} 基本面 ({i + 1}/{total})...",
                    0.96 + 0.03 * (i + 1) / max(total, 1),
                )
                if asyncio.iscoroutine(result):
                    await result

            # 调用 LLM 评估
            try:
                assessment = await self._assess_fundamental(rec, fund)
                if assessment:
                    fund.fundamental_score = assessment.fundamental_score
                    fund.fundamental_summary = assessment.fundamental_summary
                    if assessment.adjusted_confidence is not None:
                        rec.original_confidence = rec.confidence
                        rec.confidence = assessment.adjusted_confidence
                        logger.info(
                            f"{rec.stock.code} 置信度调整: "
                            f"{rec.original_confidence:.2f} -> {rec.confidence:.2f}"
                        )
            except Exception as e:
                logger.warning(f"评估 {rec.stock.code} 基本面失败: {e}")

            rec.fundamental = fund

        # 重新按调整后置信度排序
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        return recommendations

    async def _assess_fundamental(
        self, recommendation: StockRecommendation, fundamental: StockFundamental
    ):
        """调用 LLM 结合基本面数据评估股票"""
        prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(
            stock_code=recommendation.stock.code,
            reason=recommendation.reason,
            original_confidence=recommendation.confidence,
            fundamental_text=fundamental.to_context_text(),
        )

        response = await self.llm.chat_json(prompt, system_prompt=SYSTEM_PROMPT)
        return parse_fundamental_assessment(response, stock_code=recommendation.stock.code)

    @staticmethod
    def _topological_sort(chain: CausalChain) -> List[CausalNode]:
        """对因果链节点进行拓扑排序（根节点在前）"""
        # 构建邻接表和入度
        in_degree = {n.id: 0 for n in chain.nodes}
        adj = {n.id: [] for n in chain.nodes}

        for edge in chain.edges:
            if edge.from_node in adj and edge.to_node in in_degree:
                adj[edge.from_node].append(edge.to_node)
                in_degree[edge.to_node] += 1

        # BFS 拓扑排序
        from collections import deque
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result_ids = []

        while queue:
            nid = queue.popleft()
            result_ids.append(nid)
            for child in adj[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        # 添加未被处理的节点（可能存在环或孤立节点）
        for node in chain.nodes:
            if node.id not in result_ids:
                result_ids.append(node.id)

        id_to_node = {n.id: n for n in chain.nodes}
        return [id_to_node[nid] for nid in result_ids if nid in id_to_node]
