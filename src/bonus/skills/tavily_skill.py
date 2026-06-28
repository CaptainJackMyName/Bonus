"""Tavily 搜索 Skill"""

import hashlib
from datetime import datetime
from typing import List

import httpx

from bonus.models.news import NewsItem
from bonus.skills.base import BaseSkill
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class TavilySkill(BaseSkill):
    """Tavily Search API 新闻搜索"""

    name = "tavily"
    description = "Tavily 搜索引擎实时新闻获取"

    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    async def fetch_news(self, query: str = "", top_k: int = 10) -> List[NewsItem]:
        """通过 Tavily API 搜索新闻"""
        if not self.api_key:
            logger.warning("Tavily API Key 为空，跳过")
            return []

        search_query = f"股票 财经 {query}" if query else "今日 A股 财经热点 行业政策"

        payload = {
            "api_key": self.api_key,
            "query": search_query,
            "search_depth": "advanced",
            "topic": "news",
            "max_results": top_k,
            "include_answer": False,
        }

        items: List[NewsItem] = []

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(self.API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        for i, result in enumerate(results):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")

            if not title:
                continue

            published_at = None
            published_date = result.get("published_date", "")
            if published_date:
                try:
                    published_at = datetime.fromisoformat(
                        published_date.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            news_id = self._gen_id(title, url, i)

            items.append(NewsItem(
                id=news_id,
                title=title,
                summary=content[:300],
                content=content,
                source="tavily",
                url=url,
                published_at=published_at,
                tags=result.get("score", []) if isinstance(result.get("score"), list) else [],
            ))

        return items

    @staticmethod
    def _gen_id(title: str, url: str, index: int) -> str:
        """生成新闻唯一 ID"""
        raw = f"tavily_{index}_{title}_{url}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]
