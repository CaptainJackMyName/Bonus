"""逐步确认弹窗组件"""

from typing import Callable, Optional

import flet as ft

from bonus.models.inference import CausalNode, NodeType
from bonus.utils.logger import get_logger

logger = get_logger(__name__)

# 节点类型中文映射
NODE_TYPE_LABELS = {
    NodeType.EVENT: "事件",
    NodeType.MACRO: "宏观影响",
    NodeType.INDUSTRY: "产业环节",
    NodeType.COMPANY: "公司标的",
    NodeType.PRICE_EXPECT: "股价预期",
}

NODE_TYPE_COLORS = {
    NodeType.EVENT: ft.Colors.BLUE,
    NodeType.MACRO: ft.Colors.PURPLE,
    NodeType.INDUSTRY: ft.Colors.ORANGE,
    NodeType.COMPANY: ft.Colors.GREEN,
    NodeType.PRICE_EXPECT: ft.Colors.RED,
}


def show_confirmation(
    page: ft.Page,
    node: CausalNode,
    on_confirm: Callable,
    on_reject: Optional[Callable] = None,
    on_modify: Optional[Callable] = None,
) -> None:
    """
    显示逐步确认对话框。

    Args:
        page: Flet 页面对象
        node: 待确认的因果节点
        on_confirm: 确认回调
        on_reject: 否决回调
        on_modify: 修正回调
    """
    node_type_label = NODE_TYPE_LABELS.get(node.type, node.type.value)
    node_color = NODE_TYPE_COLORS.get(node.type, ft.colors.GREY)

    # 修改输入框
    modify_field = ft.TextField(
        label="修改推理内容（可选）",
        value=node.content,
        multiline=True,
        min_lines=2,
        max_lines=5,
        border_color=ft.colors.OUTLINE,
    )

    # 股票代码输入框（公司节点专用）
    stocks_field: Optional[ft.TextField] = None
    if node.type == NodeType.COMPANY:
        stocks_field = ft.TextField(
            label="股票代码（逗号分隔）",
            value=", ".join(node.stocks) if node.stocks else "",
            border_color=ft.colors.OUTLINE,
        )

    def confirm_click(e):
        # 如果用户修改了内容，使用修改后的内容
        modified_node = None
        if modify_field.value and modify_field.value.strip() != node.content:
            modified_node = node.model_copy()
            modified_node.content = modify_field.value.strip()
            if stocks_field and stocks_field.value:
                modified_node.stocks = [
                    s.strip() for s in stocks_field.value.split(",") if s.strip()
                ]
        dlg.open = False
        page.update()
        on_confirm(modified_node)

    def reject_click(e):
        dlg.open = False
        page.update()
        if on_reject:
            on_reject()

    def modify_click(e):
        # 修改即确认但带修改内容
        confirm_click(e)

    content_controls = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.QUESTION_MARK, color=node_color),
                    ft.Text(
                        f"{node_type_label}  |  置信度: {node.confidence:.0%}",
                        size=14,
                        color=node_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                ]
            ),
            padding=ft.padding.only(bottom=10),
        ),
        ft.Text("推理内容:", size=13, color=ft.colors.ON_SURFACE_VARIANT),
        modify_field,
    ]

    if stocks_field:
        content_controls.append(stocks_field)

    if node.sources:
        content_controls.append(
            ft.Text(
                f"来源新闻: {', '.join(node.sources)}",
                size=12,
                color=ft.colors.ON_SURFACE_VARIANT,
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("请确认推理步骤", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(content_controls, tight=True, scroll=ft.ScrollMode.AUTO),
            width=500,
            padding=ft.padding.all(5),
        ),
        actions=[
            ft.TextButton("否决", on_click=reject_click, style=ft.ButtonStyle(color=ft.colors.RED)),
            ft.TextButton("确认", on_click=confirm_click, style=ft.ButtonStyle(color=ft.colors.GREEN)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.open(dlg)
