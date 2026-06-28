"""Flet 应用主逻辑 - 页面路由与应用初始化"""

import asyncio
import threading
from typing import Optional

import flet as ft

from bonus.agent.engine import CausalEngine
from bonus.llm.client import LLMClient
from bonus.skills.registry import load_skills, load_fundamental_skills
from bonus.storage.db import Database
from bonus.storage.history import HistoryManager
from bonus.ui.main_view import MainView
from bonus.utils.config import Config, load_config
from bonus.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


class BonusApp:
    """红利应用主控制器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config: Config = load_config(config_path)
        setup_logging()

        self.db: Optional[Database] = None
        self.history: Optional[HistoryManager] = None
        self.engine: Optional[CausalEngine] = None
        self._main_view: Optional[MainView] = None
        self._page: Optional[ft.Page] = None
        self._analyze_thread: Optional[threading.Thread] = None

    async def _init_async(self) -> None:
        """异步初始化数据库和引擎"""
        db_path = self.config.get("storage", "db_path", default="bonus.db")
        self.db = Database(db_path)
        await self.db.connect()

        max_history = self.config.get("storage", "max_history", default=100)
        self.history = HistoryManager(self.db, max_history)

        skills = load_skills(self.config)

        fundamental_skills = load_fundamental_skills(self.config)

        llm_config = self.config.llm_config
        llm_client = LLMClient.from_config(llm_config)

        agent_config = self.config.agent_config
        self.engine = CausalEngine(
            skills=skills,
            llm_client=llm_client,
            mode=agent_config.get("default_mode", "auto"),
            max_inference_depth=agent_config.get("max_inference_depth", 5),
            min_confidence=agent_config.get("min_confidence", 0.5),
            fundamental_skills=fundamental_skills,
        )

        logger.info("应用异步初始化完成")

    def main(self, page: ft.Page) -> None:
        """Flet 应用主入口"""
        self._page = page

        page.title = "红利 Bonus - 因果推断智能体"
        page.window.width = self.config.get("ui", "window_width", default=1200)
        page.window.height = self.config.get("ui", "window_height", default=800)
        page.window.min_width = 900
        page.window.min_height = 600

        theme_mode = (
            ft.ThemeMode.DARK
            if self.config.get("ui", "theme", default="dark") == "dark"
            else ft.ThemeMode.LIGHT
        )
        page.theme_mode = theme_mode

        # 异步初始化
        self._run_async_init()

        # 创建主视图
        self._main_view = MainView(on_analyze=self._start_analysis)
        page.add(self._main_view)

        page.on_close = self._on_page_close

    def _run_async_init(self) -> None:
        """在新线程中运行异步初始化"""
        def _init():
            asyncio.run(self._init_async())

        thread = threading.Thread(target=_init, daemon=True)
        thread.start()
        thread.join(timeout=10)

    def _start_analysis(self, query: str, mode: str) -> None:
        """启动分析流程"""
        if not self.engine:
            self._main_view.show_error("应用尚未初始化完成，请稍后再试")
            return

        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._analyze_async(query, mode))
            except Exception as e:
                logger.error(f"分析失败: {e}", exc_info=True)
                if self._page:
                    self._page.run_thread(
                        lambda: self._main_view.show_error(str(e))
                    )
            finally:
                loop.close()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        self._analyze_thread = thread

    async def _analyze_async(self, query: str, mode: str) -> None:
        """异步执行分析流程"""
        self.engine.mode = mode

        def progress_callback(message: str, progress: float):
            if self._main_view and self._page:
                self._page.run_thread(
                    lambda: self._main_view.update_progress(message, progress)
                )

        async def confirm_callback(node):
            if self._main_view and self._page:
                future = asyncio.get_event_loop().create_future()

                def _show_dialog():
                    try:
                        result = asyncio.run(
                            self._main_view.wait_for_confirmation(self._page, node)
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)

                self._page.run_thread(_show_dialog)
                return await future
            return (True, None)

        try:
            chain, recommendations = await self.engine.run(
                query=query,
                progress_callback=progress_callback,
                confirm_callback=confirm_callback if mode == "stepwise" else None,
            )

            # 保存历史
            if self.history:
                try:
                    await self.history.save(
                        query=query,
                        mode=mode,
                        chain=chain,
                        news_count=0,
                        stock_count=len(recommendations),
                    )
                except Exception as e:
                    logger.warning(f"保存历史失败: {e}")

            # 展示结果
            if self._main_view and self._page:
                self._page.run_thread(
                    lambda: self._main_view.show_results(chain, recommendations)
                )

        except Exception as e:
            logger.error(f"分析过程出错: {e}", exc_info=True)
            if self._main_view and self._page:
                self._page.run_thread(
                    lambda: self._main_view.show_error("分析过程出错")
                )

    def _on_page_close(self, e: ft.ControlEvent) -> None:
        """页面关闭时的清理"""
        logger.info("应用关闭，清理资源...")

        async def _cleanup():
            if self.db:
                await self.db.close()

        try:
            asyncio.run(_cleanup())
        except Exception:
            pass

    def run(self) -> None:
        """启动应用"""
        logger.info("启动红利 Bonus 应用...")
        ft.app(target=self.main)
