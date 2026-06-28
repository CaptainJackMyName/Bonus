"""Skill 插件单元测试"""

import pytest

from bonus.models.news import NewsItem
from bonus.skills.base import BaseSkill
from bonus.skills.sina_skill import SinaSkill
from bonus.skills.tavily_skill import TavilySkill
from bonus.skills.registry import load_skills
from bonus.utils.config import Config


class MockSkill(BaseSkill):
    """测试用 Mock Skill"""
    name = "mock"
    description = "测试 Skill"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._news = [
            NewsItem(id="mock_1", title="测试新闻1", summary="摘要1", source="mock"),
            NewsItem(id="mock_2", title="测试新闻2", summary="摘要2", source="mock"),
        ]

    async def fetch_news(self, query: str, top_k: int = 10):
        return self._news[:top_k]


@pytest.mark.asyncio
async def test_mock_skill():
    """测试 Mock Skill 基本功能"""
    skill = MockSkill(enabled=True)
    news = await skill.safe_fetch("test", top_k=5)
    assert len(news) == 2
    assert news[0].title == "测试新闻1"


@pytest.mark.asyncio
async def test_disabled_skill():
    """测试禁用的 Skill 返回空列表"""
    skill = MockSkill(enabled=False)
    news = await skill.safe_fetch("test")
    assert news == []


@pytest.mark.asyncio
async def test_sina_skill_creation():
    """测试新浪 Skill 创建"""
    skill = SinaSkill(enabled=True, top_k=5)
    assert skill.name == "sina"
    assert skill.enabled is True


def test_tavily_skill_no_key():
    """测试无 API Key 的 Tavily Skill"""
    skill = TavilySkill(api_key="", enabled=True)
    assert skill.api_key == ""


def test_load_skills(sample_config: Config):
    """测试 Skill 注册加载"""
    skills = load_skills(sample_config)
    assert "sina" in skills
    assert skills["sina"].name == "sina"


def test_load_skills_empty_config():
    """测试空配置下的 Skill 加载"""
    config = Config({"skills": {}})
    skills = load_skills(config)
    assert len(skills) == 0
