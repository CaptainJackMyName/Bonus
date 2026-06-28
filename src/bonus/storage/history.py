"""推理历史记录 CRUD"""

import json
from datetime import datetime
from typing import List, Optional

from bonus.models.inference import CausalChain
from bonus.storage.db import Database
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class HistoryManager:
    """分析历史管理器"""

    def __init__(self, db: Database, max_history: int = 100):
        self.db = db
        self.max_history = max_history

    async def save(
        self,
        query: str,
        mode: str,
        chain: CausalChain,
        news_count: int = 0,
        stock_count: int = 0,
    ) -> int:
        """保存一条分析历史记录"""
        chain_json = chain.model_dump_json(indent=2)
        cursor = await self.db.execute(
            """INSERT INTO analysis_history (query, mode, chain_json, news_count, stock_count)
               VALUES (?, ?, ?, ?, ?)""",
            (query, mode, chain_json, news_count, stock_count),
        )
        record_id = cursor.lastrowid
        logger.info(f"已保存历史记录 id={record_id}, query='{query}'")

        # 清理超额历史
        await self._cleanup()
        return record_id

    async def get(self, record_id: int) -> Optional[dict]:
        """根据 ID 获取历史记录"""
        return await self.db.fetchone(
            "SELECT * FROM analysis_history WHERE id = ?",
            (record_id,),
        )

    async def list_recent(self, limit: int = 20) -> List[dict]:
        """获取最近的分析记录列表"""
        return await self.db.fetchall(
            """SELECT id, query, mode, news_count, stock_count, created_at
               FROM analysis_history
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        )

    async def get_chain(self, record_id: int) -> Optional[CausalChain]:
        """根据 ID 获取完整因果链"""
        row = await self.get(record_id)
        if not row:
            return None
        chain_data = json.loads(row["chain_json"])
        return CausalChain(**chain_data)

    async def delete(self, record_id: int) -> None:
        """删除一条历史记录"""
        await self.db.execute(
            "DELETE FROM analysis_history WHERE id = ?",
            (record_id,),
        )
        logger.info(f"已删除历史记录 id={record_id}")

    async def _cleanup(self) -> None:
        """清理超额历史记录"""
        count_row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM analysis_history"
        )
        if count_row and count_row["cnt"] > self.max_history:
            excess = count_row["cnt"] - self.max_history
            await self.db.execute(
                """DELETE FROM analysis_history
                   WHERE id IN (
                       SELECT id FROM analysis_history
                       ORDER BY created_at ASC
                       LIMIT ?
                   )""",
                (excess,),
            )
            logger.info(f"已清理 {excess} 条超额历史记录")

    async def cache_news(self, news_items: list) -> None:
        """缓存新闻数据"""
        params = []
        for item in news_items:
            params.append((
                item.id,
                item.title,
                item.summary,
                item.content[:5000] if item.content else "",
                item.source,
                item.url,
                item.published_at.isoformat() if item.published_at else None,
                json.dumps(item.related_stocks, ensure_ascii=False),
                json.dumps(item.tags, ensure_ascii=False),
            ))
        await self.db.executemany(
            """INSERT OR REPLACE INTO news_cache
               (id, title, summary, content, source, url, published_at, related_stocks, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            params,
        )
