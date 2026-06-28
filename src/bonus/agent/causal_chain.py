"""因果链构建与操作工具"""

from typing import List, Optional

from bonus.models.inference import (
    CausalChain,
    CausalEdge,
    CausalNode,
    NodeType,
)
from bonus.models.news import NewsItem
from bonus.models.stock import Stock, StockRecommendation
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class ChainBuilder:
    """因果链构建与辅助操作"""

    @staticmethod
    def build_news_context(news_items: List[NewsItem], max_items: int = 15) -> str:
        """将新闻列表格式化为 LLM 可读的上下文文本"""
        lines = []
        for i, news in enumerate(news_items[:max_items], 1):
            time_str = ""
            if news.published_at:
                time_str = f" [{news.published_at.strftime('%Y-%m-%d %H:%M')}]"
            stocks_str = f" 关联股票: {', '.join(news.related_stocks)}" if news.related_stocks else ""
            lines.append(
                f"[{i}] (id={news.id}) {news.title}{time_str}{stocks_str}\n"
                f"    摘要: {news.brief(150)}"
            )
        return "\n".join(lines)

    @staticmethod
    def build_chain_context(chain: CausalChain) -> str:
        """将因果链格式化为 LLM 可读的上下文文本"""
        lines = ["已有因果链节点:"]
        for node in chain.nodes:
            stocks_str = f" 股票:{','.join(node.stocks)}" if node.stocks else ""
            lines.append(
                f"  [{node.id}] ({node.type.value}) {node.content} "
                f"(置信度:{node.confidence:.2f}){stocks_str}"
            )
        lines.append("\n因果边:")
        for edge in chain.edges:
            lines.append(f"  {edge.from_node} --({edge.relation})--> {edge.to_node}")
        return "\n".join(lines)

    @staticmethod
    def extract_recommendations(
        chain: CausalChain,
        min_confidence: float = 0.4,
    ) -> List[StockRecommendation]:
        """从因果链中提取股票推荐"""
        recommendations: List[StockRecommendation] = []
        seen_codes = set()

        # 查找所有公司节点
        company_nodes = chain.get_company_nodes()

        for company_node in company_nodes:
            if company_node.confidence < min_confidence:
                continue

            for stock_code in company_node.stocks:
                if stock_code in seen_codes:
                    continue
                seen_codes.add(stock_code)

                # 构建因果路径
                path_nodes = chain.get_path_to_root(company_node.id)
                cause_chain = [n.content for n in reversed(path_nodes)]

                # 查找对应的股价预期节点
                price_expect = None
                for pe_node in chain.get_price_expect_nodes():
                    if stock_code in pe_node.stocks:
                        price_expect = pe_node
                        break

                confidence = company_node.confidence
                if price_expect:
                    confidence = (confidence + price_expect.confidence) / 2

                stock = Stock(
                    code=stock_code,
                    name="",
                    market="A股",
                )

                # 从节点内容中尝试提取股票名称
                content = company_node.content
                # 尝试匹配 "公司名称（代码）" 格式
                import re
                name_match = re.match(r"([^\(（]+)", content)
                if name_match:
                    stock.name = name_match.group(1).strip()

                recommendations.append(StockRecommendation(
                    stock=stock,
                    reason=company_node.content,
                    confidence=confidence,
                    cause_chain=cause_chain,
                    related_news_ids=company_node.sources,
                    node_id=company_node.id,
                ))

        # 按置信度排序
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        # to be deleted: 暂时只取第一只股票
        recommendations = recommendations[:1]
        logger.info(f"提取了 {len(recommendations)} 个股票推荐")
        return recommendations

    @staticmethod
    def merge_into_chain(
        chain: CausalChain,
        new_nodes: List[CausalNode],
        new_edges: List[CausalEdge],
    ) -> CausalChain:
        """将新节点和边合并到已有因果链中"""
        for node in new_nodes:
            chain.add_node(node)
        for edge in new_edges:
            chain.add_edge(edge)
        return chain
