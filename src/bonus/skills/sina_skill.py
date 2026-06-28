"""新浪财经热点抓取 Skill"""

import hashlib
import re
from datetime import datetime
from typing import List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from bonus.models.news import NewsItem
from bonus.skills.base import BaseSkill
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class SinaSkill(BaseSkill):
    """新浪财经热点新闻抓取"""

    name = "sina"
    description = "新浪财经实时热点新闻抓取"

    # 新浪财经 RSS / 热点页面
    ROLL_URL = "https://finance.sina.com.cn/roll/index.d.html"
    NEWS_URL = "https://finance.sina.com.cn/"

    async def fetch_news(self, query: str = "", top_k: int = 10) -> List[NewsItem]:
        """抓取新浪财经热点新闻"""
        items: List[NewsItem] = []

        # 先尝试滚动新闻接口
        try:
            items = await self._fetch_roll_news(top_k)
        except Exception as e:
            logger.warning(f"滚动新闻抓取失败，尝试备用方式: {e}")

        # 如果滚动新闻不足，尝试搜索
        if len(items) < top_k and query:
            search_items = await self._fetch_search_news(query, top_k - len(items))
            items.extend(search_items)

        # 去重
        seen_ids = set()
        unique_items = []
        for item in items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)

        return unique_items[:top_k]

    async def _fetch_roll_news(self, top_k: int) -> List[NewsItem]:
        """从新浪滚动新闻获取"""
        items: List[NewsItem] = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://finance.sina.com.cn/",
        }

        async with httpx.AsyncClient(
            headers=headers, timeout=15.0, follow_redirects=True
        ) as client:
            # 新浪财经滚动新闻 API（JSON 格式）
            api_url = "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=50&zhibo_id=152&tag_id=0&type=0"
            resp = await client.get(api_url)
            resp.encoding = "utf-8"

            import json
            data = resp.json()
            feed = data.get("result", {}).get("feed", {}).get("list", [])

            for entry in feed[:top_k * 2]:
                rich_text = entry.get("rich_text", "")
                # 清理 HTML 标签
                soup = BeautifulSoup(rich_text, "lxml")
                title_tag = soup.find("a")
                title = title_tag.get_text(strip=True) if title_tag else entry.get("text", "")

                link = title_tag.get("href", "") if title_tag else ""
                summary = entry.get("text", "")

                if not title:
                    continue

                create_time = entry.get("create_time", "")
                published_at = None
                if create_time:
                    try:
                        published_at = datetime.strptime(create_time, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass

                news_id = self._gen_id(title, link)
                items.append(NewsItem(
                    id=news_id,
                    title=title,
                    summary=summary[:300],
                    source="sina",
                    url=link,
                    published_at=published_at,
                    related_stocks=self._extract_stocks(summary),
                ))

                if len(items) >= top_k:
                    break

        return items

    async def _fetch_search_news(self, query: str, top_k: int) -> List[NewsItem]:
        """从新浪搜索获取新闻"""
        items: List[NewsItem] = []
        if top_k <= 0:
            return items

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        search_url = f"https://search.sina.com.cn/?q={query}&c=news&sort=time"
        try:
            async with httpx.AsyncClient(
                headers=headers, timeout=15.0, follow_redirects=True
            ) as client:
                resp = await client.get(search_url)
                resp.encoding = "utf-8"
                soup = BeautifulSoup(resp.text, "lxml")

                result_divs = soup.select("div.box-result") or soup.select(".r-info")
                for div in result_divs[:top_k]:
                    title_tag = div.find("h2")
                    if not title_tag:
                        continue
                    link_tag = title_tag.find("a")
                    if not link_tag:
                        continue
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get("href", "")

                    desc_tag = div.find("p", class_="content") or div.find("p")
                    summary = desc_tag.get_text(strip=True) if desc_tag else ""

                    if not title:
                        continue

                    news_id = self._gen_id(title, link)
                    items.append(NewsItem(
                        id=news_id,
                        title=title,
                        summary=summary[:300],
                        source="sina_search",
                        url=link,
                        related_stocks=self._extract_stocks(summary),
                    ))
        except Exception as e:
            logger.error(f"新浪搜索抓取失败: {e}")

        return items

    @staticmethod
    def _gen_id(title: str, url: str) -> str:
        """生成新闻唯一 ID"""
        raw = f"sina_{title}_{url}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _extract_stocks(text: str) -> List[str]:
        """从文本中提取股票代码（6位数字）"""
        # A股股票代码模式：6开头(沪市)、0开头(深市)、3开头(创业板)
        codes = re.findall(r"\b([603]\d{5})\b", text)
        return list(set(codes))[:5]
