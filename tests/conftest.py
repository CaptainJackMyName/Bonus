"""pytest 共享配置与 fixtures"""

import asyncio
from typing import List

import pytest

from bonus.models.inference import CausalChain, CausalNode, CausalEdge, NodeType
from bonus.models.news import NewsItem
from bonus.utils.config import Config


@pytest.fixture
def event_loop():
    """事件循环 fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_config() -> Config:
    """示例配置"""
    return Config({
        "llm": {
            "provider": "openai",
            "api_key": "test-key",
            "model": "gpt-4o",
            "base_url": "",
            "temperature": 0.3,
        },
        "skills": {
            "sina": {"enabled": True, "top_k": 5},
            "tavily": {"api_key": "", "enabled": False, "top_k": 5},
        },
        "agent": {
            "default_mode": "auto",
            "max_inference_depth": 3,
            "min_confidence": 0.5,
        },
        "storage": {"db_path": ":memory:", "max_history": 50},
        "ui": {"theme": "dark", "window_width": 1200, "window_height": 800},
    })


@pytest.fixture
def sample_news() -> List[NewsItem]:
    """示例新闻列表"""
    from datetime import datetime
    return [
        NewsItem(
            id="news_1",
            title="央行宣布降准0.5个百分点",
            summary="中国人民银行决定下调存款准备金率0.5个百分点，释放长期资金约1万亿元。",
            source="sina",
            url="https://example.com/1",
            published_at=datetime(2024, 1, 15, 10, 0),
            related_stocks=["600036"],
        ),
        NewsItem(
            id="news_2",
            title="新能源汽车补贴政策延续",
            summary="财政部宣布新能源汽车购置补贴将延续至2025年底。",
            source="sina",
            url="https://example.com/2",
            published_at=datetime(2024, 1, 15, 11, 0),
            related_stocks=["300750"],
        ),
    ]


@pytest.fixture
def sample_chain() -> CausalChain:
    """示例因果链"""
    chain = CausalChain(query="今日热点")

    chain.add_node(CausalNode(
        id="n1", type=NodeType.EVENT,
        content="央行宣布降准0.5个百分点",
        confidence=0.95, sources=["news_1"],
    ))
    chain.add_node(CausalNode(
        id="n2", type=NodeType.MACRO,
        content="银行流动性宽松，负债成本下降",
        confidence=0.85, sources=["news_1"],
    ))
    chain.add_node(CausalNode(
        id="n3", type=NodeType.COMPANY,
        content="招商银行受益于降准，资产质量优",
        confidence=0.75, sources=[], stocks=["600036"],
    ))
    chain.add_node(CausalNode(
        id="n4", type=NodeType.PRICE_EXPECT,
        content="招商银行股价有望上涨",
        confidence=0.7, sources=[], stocks=["600036"],
    ))

    chain.add_edge(CausalEdge(from_node="n1", to_node="n2", relation="利好"))
    chain.add_edge(CausalEdge(from_node="n2", to_node="n3", relation="传导至"))
    chain.add_edge(CausalEdge(from_node="n3", to_node="n4", relation="预期"))

    return chain
