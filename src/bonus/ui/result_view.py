"""推理结果与因果链展示视图"""

from typing import List

import flet as ft

from bonus.models.inference import CausalChain
from bonus.models.stock import StockRecommendation
from bonus.ui.chain_widget import ChainWidget
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class ResultView(ft.Column):
    """推理结果展示视图"""

    def __init__(self):
        super().__init__()
        self.spacing = 15
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._chain_widget = ChainWidget()
        self._stock_list = ft.Column(spacing=8)
        self._build()

    def _build(self) -> None:
        self.controls.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.INSIGHTS, color=ft.Colors.PRIMARY, size=28),
                    ft.Text("分析结果", size=24, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            )
        )

        self.controls.append(
            ft.Container(
                content=self._chain_widget,
                expand=True,
                height=300,
            )
        )

        self.controls.append(ft.Divider())

        self.controls.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.TRENDING_UP, color=ft.Colors.GREEN, size=24),
                    ft.Text("推荐股票", size=20, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            )
        )

        self.controls.append(self._stock_list)

        # 初始空状态占位（构建期无需调用 update）
        self._stock_list.controls.append(
            ft.Container(
                content=ft.Text(
                    "请点击「开始分析」进行推理",
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                padding=40,
                alignment=ft.Alignment.CENTER,
            )
        )

    def show_results(
        self,
        chain: CausalChain,
        recommendations: List[StockRecommendation],
    ) -> None:
        """展示推理结果"""
        self._chain_widget.update_chain(chain)

        self._stock_list.controls.clear()

        if not recommendations:
            self._stock_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "暂无符合条件的推荐股票",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for rec in recommendations:
                self._stock_list.controls.append(self._build_stock_card(rec))

        self.update()

    def _build_stock_card(self, rec: StockRecommendation) -> ft.Container:
        """构建单只股票推荐卡片"""
        if rec.confidence >= 0.7:
            conf_color = ft.Colors.GREEN
        elif rec.confidence >= 0.5:
            conf_color = ft.Colors.ORANGE
        else:
            conf_color = ft.Colors.RED

        cause_controls = []
        for i, cause in enumerate(rec.cause_chain):
            cause_controls.append(
                ft.Row(
                    [
                        ft.Text(f"{i + 1}.", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(cause, size=12, expand=True),
                    ],
                    spacing=5,
                )
            )

        cause_section = ft.Column(
            cause_controls,
            spacing=3,
            visible=bool(cause_controls),
        ) if cause_controls else ft.Container()

        # 构建基本面展示区域
        fundamental_section = self._build_fundamental_section(rec)

        # 置信度调整提示
        confidence_badges = []
        if rec.original_confidence is not None and rec.original_confidence != rec.confidence:
            confidence_badges.append(
                ft.Text(
                    f"消息面:{rec.original_confidence:.0%} → 综合:{rec.confidence:.0%}",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.TRENDING_UP, color=conf_color, size=28),
                            ft.Column(
                                [
                                    ft.Text(
                                        rec.stock.name or rec.stock.code,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"{rec.stock.code} | {rec.stock.market} | {rec.stock.industry or '未知行业'}",
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=2,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{rec.confidence_label} {rec.confidence:.0%}",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=conf_color,
                                        ),
                                    ] + confidence_badges,
                                    spacing=1,
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                ),
                                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                bgcolor=conf_color.with_opacity(0.1, ft.Colors.RED),
                                border_radius=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "上涨逻辑:",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(rec.reason, size=14),
                            ],
                            spacing=4,
                        ),
                        padding=10,
                        bgcolor=ft.Colors.SURFACE_BRIGHT,
                        border_radius=8,
                    ),
                    cause_section,
                    fundamental_section,
                ],
                spacing=10,
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            ink=True,
        )

    def _build_fundamental_section(self, rec: StockRecommendation):
        """构建基本面数据展示区域"""
        fund = rec.fundamental
        if not fund:
            return ft.Container()

        controls = [
            ft.Row(
                [
                    ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.TEAL, size=18),
                    ft.Text(
                        "基本面数据",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=6,
            ),
        ]

        # 估值指标行
        valuation_chips = []
        if fund.pe_ttm is not None:
            valuation_chips.append(self._chip("PE", f"{fund.pe_ttm:.1f}", ft.Colors.BLUE))
        if fund.pb is not None:
            valuation_chips.append(self._chip("PB", f"{fund.pb:.2f}", ft.Colors.PURPLE))
        if fund.ps_ttm is not None:
            valuation_chips.append(self._chip("PS", f"{fund.ps_ttm:.1f}", ft.Colors.ORANGE))
        if fund.total_market_cap is not None:
            cap_yi = fund.total_market_cap / 1e8
            valuation_chips.append(
                self._chip("市值", f"{cap_yi:.1f}亿", ft.Colors.INDIGO)
            )

        if valuation_chips:
            controls.append(
                ft.Row(valuation_chips, spacing=6, wrap=True)
            )

        # 近期财务数据表格
        if fund.financials:
            table_rows = []
            for q in fund.financials[:4]:
                cells = [ft.DataCell(ft.Text(q.report_date[:10] if q.report_date else "-", size=11))]
                cells.append(ft.DataCell(
                    ft.Text(self._fmt_num(q.revenue), size=11)
                ))
                cells.append(ft.DataCell(
                    ft.Text(self._fmt_pct(q.revenue_yoy), size=11)
                ))
                cells.append(ft.DataCell(
                    ft.Text(self._fmt_pct(q.gross_margin), size=11)
                ))
                cells.append(ft.DataCell(
                    ft.Text(self._fmt_pct(q.roe), size=11)
                ))
                table_rows.append(ft.DataRow(cells=cells))

            if table_rows:
                controls.append(
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("报告期", size=11)),
                            ft.DataColumn(ft.Text("营收", size=11)),
                            ft.DataColumn(ft.Text("营收同比", size=11)),
                            ft.DataColumn(ft.Text("毛利率", size=11)),
                            ft.DataColumn(ft.Text("ROE", size=11)),
                        ],
                        rows=table_rows,
                        column_spacing=12,
                        horizontal_margin=6,
                        data_row_min_height=28,
                        data_row_max_height=32,
                    )
                )

        # 基本面评分与摘要
        if fund.fundamental_summary:
            score_color = ft.Colors.GREEN
            if fund.fundamental_score is not None:
                if fund.fundamental_score >= 0.7:
                    score_color = ft.Colors.GREEN
                elif fund.fundamental_score >= 0.5:
                    score_color = ft.Colors.ORANGE
                else:
                    score_color = ft.Colors.RED

            score_text = ""
            if fund.fundamental_score is not None:
                score_text = f"  基本面评分: {fund.fundamental_score:.0%}"

            controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "基本面分析:",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    ft.Text(
                                        score_text,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=score_color,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Text(fund.fundamental_summary, size=12),
                        ],
                        spacing=3,
                    ),
                    padding=8,
                    bgcolor=score_color.with_opacity(0.05, ft.Colors.RED),
                    border_radius=6,
                    border=ft.border.all(1, score_color.with_opacity(0.2)),
                )
            )

        return ft.Container(
            content=ft.Column(controls, spacing=6),
            padding=10,
            bgcolor=ft.Colors.SURFACE_VARIANT,
            border_radius=8,
        )

    @staticmethod
    def _chip(label: str, value: str, color) -> ft.Container:
        """构建指标标签"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(label, size=10, color=ft.Colors.WHITE),
                    ft.Text(value, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
            ),
            bgcolor=color,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            border_radius=10,
        )

    @staticmethod
    def _fmt_num(val) -> str:
        """格式化数值（亿元）"""
        if val is None:
            return "-"
        try:
            yi = float(val) / 1e8
            return f"{yi:.2f}亿"
        except (ValueError, TypeError):
            return str(val)

    @staticmethod
    def _fmt_pct(val) -> str:
        """格式化百分比"""
        if val is None:
            return "-"
        try:
            return f"{float(val):.2f}%"
        except (ValueError, TypeError):
            return str(val)

    def show_empty(self) -> None:
        """显示空状态"""
        self._chain_widget.update_chain(CausalChain())
        self._stock_list.controls.clear()
        self._stock_list.controls.append(
            ft.Container(
                content=ft.Text(
                    "请点击「开始分析」进行推理",
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                padding=40,
                alignment=ft.Alignment.CENTER,
            )
        )
        try:
            self.update()
        except RuntimeError:
            # 控件尚未添加到页面，无需手动刷新
            pass
