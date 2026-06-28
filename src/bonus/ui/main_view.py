"""主界面布局与分析面板"""

import asyncio
import flet as ft

from typing import Callable, Optional

from bonus.models.inference import CausalChain, CausalNode
from bonus.models.stock import StockRecommendation
from bonus.ui.result_view import ResultView
from bonus.ui.confirm_dialog import show_confirmation
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class MainView(ft.Column):
    """主界面视图"""

    def __init__(self, on_analyze: Callable):
        """
        Args:
            on_analyze: 分析回调函数 (query: str, mode: str) -> None
        """
        super().__init__()
        self._on_analyze = on_analyze
        self._pending_confirm: Optional[asyncio.Future] = None
        self.spacing = 0
        self.expand = True
        self._build()

    def _build(self) -> None:
        # 顶部应用栏
        app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_GRAPH, color=ft.Colors.PRIMARY, size=32),
                    ft.Column(
                        [
                            ft.Text("红利 Bonus", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "因果推断智能体 · 股票分析",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            bgcolor=ft.Colors.SURFACE_BRIGHT,
        )

        # 分析面板
        self._query_input = ft.TextField(
            label="查询主题",
            value="今日热点",
            hint_text="输入感兴趣的主题，如：新能源政策、央行降准...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            expand=True,
        )

        self._mode_switch = ft.Switch(
            label="逐步确认模式",
            value=False,
            label_position=ft.LabelPosition.LEFT,
        )

        self._analyze_btn = ft.ElevatedButton(
            content="开始分析",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self._on_analyze_click,
        )

        self._cancel_btn = ft.TextButton(
            content="取消",
            icon=ft.Icons.STOP,
            on_click=self._on_cancel_click,
            visible=False,
        )

        control_panel = ft.Container(
            content=ft.Row(
                [
                    self._query_input,
                    ft.Container(
                        content=ft.Column(
                            [self._mode_switch],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding.symmetric(horizontal=10),
                    ),
                    self._analyze_btn,
                    self._cancel_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        )

        # 进度条
        self._progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            bgcolor=ft.Colors.SURFACE_BRIGHT,
            color=ft.Colors.PRIMARY,
        )
        self._progress_text = ft.Text(
            "",
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
            visible=False,
        )

        self._progress_section = ft.Container(
            content=ft.Column(
                [self._progress_bar, self._progress_text],
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=24),
            visible=False,
        )

        # 结果视图（初始空状态已在 ResultView._build 中设置）
        self._result_view = ResultView()

        # 组装
        self.controls = [
            app_bar,
            control_panel,
            self._progress_section,
            ft.Container(
                content=self._result_view,
                expand=True,
                padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            ),
        ]

    def _on_analyze_click(self, e: ft.ControlEvent) -> None:
        """开始分析按钮点击"""
        query = self._query_input.value or "今日热点"
        mode = "stepwise" if self._mode_switch.value else "auto"

        self._analyze_btn.visible = False
        self._cancel_btn.visible = True
        self._progress_section.visible = True
        self._progress_bar.value = 0
        self._progress_bar.color = ft.Colors.PRIMARY
        self._progress_text.value = "正在初始化..."
        self._progress_text.visible = True
        self._query_input.disabled = True
        self._mode_switch.disabled = True
        self.update()

        self._on_analyze(query, mode)

    def _on_cancel_click(self, e: ft.ControlEvent) -> None:
        """取消分析"""
        self._reset_controls()
        self._progress_text.value = "已取消"
        self.update()

    def _reset_controls(self) -> None:
        """重置控件状态"""
        self._analyze_btn.visible = True
        self._cancel_btn.visible = False
        self._progress_section.visible = False
        self._query_input.disabled = False
        self._mode_switch.disabled = False
        self.update()

    def update_progress(self, message: str, progress: float) -> None:
        """更新进度显示"""
        self._progress_bar.value = progress
        self._progress_text.value = message
        self.update()

    def show_results(
        self,
        chain: CausalChain,
        recommendations: list[StockRecommendation],
    ) -> None:
        """展示分析结果"""
        self._reset_controls()
        self._result_view.show_results(chain, recommendations)

    def show_error(self, message: str) -> None:
        """显示错误信息"""
        self._reset_controls()
        self._progress_section.visible = True
        self._progress_bar.visible = True
        self._progress_text.visible = True
        self._progress_text.value = f"错误: {message}"
        self._progress_bar.value = 0
        self._progress_bar.color = ft.Colors.RED
        self.update()

    async def wait_for_confirmation(
        self,
        page: ft.Page,
        node: CausalNode,
    ) -> tuple[bool, Optional[CausalNode]]:
        """
        等待用户确认推理节点（逐步确认模式）。
        """
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_confirm = future

        def on_confirm(modified_node=None):
            if not future.done():
                future.set_result((True, modified_node))

        def on_reject():
            if not future.done():
                future.set_result((False, None))

        show_confirmation(page, node, on_confirm=on_confirm, on_reject=on_reject)

        return await future
