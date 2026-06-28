"""推理引擎单元测试"""

import pytest

from bonus.agent.causal_chain import ChainBuilder
from bonus.agent.engine import CausalEngine
from bonus.agent.state_machine import StepwiseStateMachine, StepwiseState
from bonus.llm.client import LLMClient
from bonus.models.inference import CausalChain, CausalNode, NodeType
from bonus.models.stock import StockRecommendation
from bonus.skills.base import BaseSkill
from bonus.models.news import NewsItem


class MockLLMClient:
    """测试用 Mock LLM 客户端"""

    def __init__(self):
        self._call_count = 0

    async def chat_json(self, prompt, system_prompt="", temperature=None):
        self._call_count += 1
        return {
            "nodes": [
                {
                    "id": "n1",
                    "type": "event",
                    "content": "测试事件",
                    "confidence": 0.9,
                    "sources": ["news_1"],
                    "stocks": [],
                },
                {
                    "id": "n2",
                    "type": "company",
                    "content": "测试公司受益",
                    "confidence": 0.7,
                    "sources": [],
                    "stocks": ["600036"],
                },
                {
                    "id": "n3",
                    "type": "price_expect",
                    "content": "股价预期上涨",
                    "confidence": 0.65,
                    "sources": [],
                    "stocks": ["600036"],
                },
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n2", "relation": "利好"},
                {"from_node": "n2", "to_node": "n3", "relation": "预期"},
            ],
        }

    async def chat(self, prompt, system_prompt="", temperature=None):
        return '{"nodes": [], "edges": []}'


class MockSkill(BaseSkill):
    """测试用 Mock Skill"""
    name = "mock"

    async def fetch_news(self, query: str, top_k: int = 10):
        from datetime import datetime
        return [
            NewsItem(
                id="news_1",
                title="测试新闻",
                summary="测试摘要",
                source="mock",
                published_at=datetime.now(),
            )
        ]


@pytest.mark.asyncio
async def test_engine_auto_mode(sample_news):
    """测试全自动模式推理"""
    skill = MockSkill(enabled=True)
    llm = MockLLMClient()
    engine = CausalEngine(
        skills={"mock": skill},
        llm_client=llm,
        mode="auto",
        max_inference_depth=1,
    )

    chain, recommendations = await engine.run(query="测试", progress_callback=None)

    assert len(chain.nodes) > 0
    assert llm._call_count >= 1


def test_chain_builder_news_context(sample_news):
    """测试新闻上下文构建"""
    text = ChainBuilder.build_news_context(sample_news)
    assert "央行宣布降准" in text
    assert "news_1" in text


def test_chain_builder_extract_recommendations(sample_chain):
    """测试从因果链提取推荐"""
    recommendations = ChainBuilder.extract_recommendations(sample_chain, min_confidence=0.5)
    assert len(recommendations) > 0
    assert recommendations[0].stock.code == "600036"
    assert recommendations[0].confidence > 0


def test_chain_builder_extract_low_confidence(sample_chain):
    """测试低置信度过滤"""
    recommendations = ChainBuilder.extract_recommendations(sample_chain, min_confidence=0.99)
    assert len(recommendations) == 0


def test_state_machine_basic():
    """测试状态机基本流程"""
    sm = StepwiseStateMachine()
    assert sm.state == StepwiseState.IDLE

    node = CausalNode(id="n1", type=NodeType.EVENT, content="测试", confidence=0.9)
    sm.set_current_node(node)
    assert sm.state == StepwiseState.WAITING_CONFIRM

    confirmed = sm.confirm()
    assert confirmed is not None
    assert sm.state == StepwiseState.CONFIRMED
    assert len(sm.confirmed_nodes) == 1


def test_state_machine_reject():
    """测试状态机否决流程"""
    sm = StepwiseStateMachine()
    node = CausalNode(id="n1", type=NodeType.EVENT, content="测试", confidence=0.9)
    sm.set_current_node(node)
    sm.reject()
    assert sm.state == StepwiseState.REJECTED
    assert sm.rejected_count == 1


def test_state_machine_max_rejections():
    """测试最大否决次数"""
    sm = StepwiseStateMachine()
    sm.max_rejections = 2
    for _ in range(2):
        sm.set_current_node(CausalNode(id="n", type=NodeType.EVENT, content="t", confidence=0.5))
        sm.reject()
    assert sm.is_max_rejections_reached()


def test_topological_sort(sample_chain):
    """测试拓扑排序"""
    sorted_nodes = CausalEngine._topological_sort(sample_chain)
    # 根节点（n1）应该在最前面
    assert sorted_nodes[0].id == "n1"
    # n4 应该在 n3 之后
    ids = [n.id for n in sorted_nodes]
    assert ids.index("n3") < ids.index("n4")
