"""Skill 抽象基类"""

from abc import ABC, abstractmethod
from typing import List

from bonus.models.news import NewsItem
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class BaseSkill(ABC):
    """所有信息源 Skill 的抽象基类"""

    name: str = "base"
    description: str = "基础信息源"

    def __init__(self, **kwargs):
        self.config = kwargs
        self.enabled: bool = kwargs.get("enabled", True)

    @abstractmethod
    async def fetch_news(self, query: str, top_k: int = 10) -> List[NewsItem]:
        """
        异步获取新闻列表。

        Args:
            query: 搜索查询词
            top_k: 返回的最大新闻条数

        Returns:
            新闻条目列表
        """
        ...

    async def safe_fetch(self, query: str, top_k: int = 10) -> List[NewsItem]:
        """安全的 fetch 包装，捕获异常返回空列表"""
        if not self.enabled:
            logger.info(f"Skill '{self.name}' 已禁用，跳过")
            return []
        try:
            logger.info(f"Skill '{self.name}' 开始获取新闻: query='{query}', top_k={top_k}")
            results = await self.fetch_news(query, top_k)
            logger.info(f"Skill '{self.name}' 获取到 {len(results)} 条新闻")
            return results
        except Exception as e:
            logger.error(f"Skill '{self.name}' 获取新闻失败: {e}", exc_info=True)
            return []

    def __repr__(self) -> str:
        return f"<Skill {self.name} enabled={self.enabled}>"
