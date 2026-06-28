"""SQLite 数据库初始化与连接管理"""

import aiosqlite
from pathlib import Path
from typing import Optional

from bonus.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    query       TEXT NOT NULL,
    mode        TEXT NOT NULL DEFAULT 'auto',
    chain_json  TEXT NOT NULL,
    news_count  INTEGER DEFAULT 0,
    stock_count INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS news_cache (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    summary     TEXT,
    content     TEXT,
    source      TEXT,
    url         TEXT,
    published_at TEXT,
    related_stocks TEXT,
    tags        TEXT,
    cached_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_history_created ON analysis_history(created_at);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_cache(source);
"""


class Database:
    """异步 SQLite 数据库管理器"""

    def __init__(self, db_path: str = "bonus.db"):
        self.db_path = str(db_path)
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """连接数据库并初始化表"""
        db_dir = Path(self.db_path).parent
        if str(db_dir) and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"连接数据库: {self.db_path}")
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_CREATE_TABLES_SQL)
        await self._conn.commit()
        logger.info("数据库表已就绪")

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("数据库连接已关闭")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        """执行 SQL 语句"""
        cursor = await self.conn.execute(sql, params)
        await self.conn.commit()
        return cursor

    async def executemany(self, sql: str, params_list) -> aiosqlite.Cursor:
        """批量执行 SQL 语句"""
        cursor = await self.conn.executemany(sql, params_list)
        await self.conn.commit()
        return cursor

    async def fetchall(self, sql: str, params: tuple = ()) -> list:
        """查询所有结果"""
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        """查询单条结果"""
        cursor = await self.conn.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
