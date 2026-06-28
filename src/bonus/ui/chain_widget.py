"""因果链树状图组件"""

from typing import Optional

import flet as ft

from bonus.models.inference import CausalChain, CausalNode, NodeType
from bonus.utils.logger import get_logger

logger = get_logger(__name__)

NODE_ICONS = {
    NodeType.EVENT: ft.icons.Icons.ANNOUNCEMENT,
    NodeType.MACRO: ft.icons.Icons.PUBLIC,
    NodeType.INDUSTRY: ft.icons.Icons.FACTORY,
    NodeType.COMPANY: ft.icons.Icons.BUSINESS,
    NodeType.PRICE_EXPECT: ft.icons.Icons.TRENDING_UP,
}

NODE_COLORS = {
    NodeType.EVENT: ft.Colors.BLUE,
    NodeType.MACRO: ft.Colors.PURPLE,
    NodeType.INDUSTRY: ft.Colors.ORANGE,
    NodeType.COMPANY: ft.Colors.GREEN,
    NodeType.PRICE_EXPECT: ft.Colors.RED,
}

NODE_TYPE_LABELS = {
    NodeType.EVENT: "事件",
    NodeType.MACRO: "宏观",
    NodeType.INDUSTRY: "产业",
    NodeType.COMPANY: "公司",
    NodeType.PRICE_EXPECT: "预期",
}


class ChainWidget(ft.Column):
    """因果链树状图展示组件"""

    def __init__(self, chain: Optional[CausalChain] = None):
        super().__init__()
        self.chain = chain
        self.spacing = 5
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._build()

    def update_chain(self, chain: CausalChain) -> None:
        """更新因果链并刷新显示"""
        self.chain = chain
        self._build()
        try:
            self.update()
        except RuntimeError:
            # 控件尚未添加到页面，无需手动刷新
            pass

    def _build(self) -> None:
        """构建树状图"""
        self.controls.clear()

        if not self.chain or not self.chain.nodes:
            self.controls.append(
                ft.Container(
                    content=ft.Text(
                        "暂无因果链数据",
                        size=16,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                    padding=40,
                )
            )
            return

        title_row = ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_TREE, color=ft.Colors.PRIMARY, size=24),
                ft.Text("因果推理链", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"({len(self.chain.nodes)} 节点 / {len(self.chain.edges)} 关系)",
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=10,
        )
        self.controls.append(title_row)

        tree = self._build_tree()
        self.controls.append(
            ft.Container(
                content=tree,
                padding=10,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                expand=True,
            )
        )

    def _build_tree(self) -> ft.Column:
        """构建树形结构"""
        tree_col = ft.Column(spacing=3, scroll=ft.ScrollMode.AUTO)

        roots = self.chain.get_root_nodes()
        if not roots:
            roots = self.chain.nodes[:1]

        for root in roots:
            tree_col.controls.append(self._build_node_tree(root, depth=0))

        return tree_col

    def _build_node_tree(self, node: CausalNode, depth: int) -> ft.Column:
        """递归构建节点树"""
        indent = depth * 24
        children = self.chain.get_children(node.id) if self.chain else []

        node_card = self._build_node_card(node, indent)

        result = ft.Column(spacing=3, controls=[node_card])

        for child in children:
            child_tree = self._build_node_tree(child, depth + 1)
            result.controls.append(child_tree)

        return result

    def _build_node_card(self, node: CausalNode, indent: int) -> ft.Container:
        """构建单个节点卡片"""
        node_type = node.type
        icon = NODE_ICONS.get(node_type, ft.Icons.HELP)
        color = NODE_COLORS.get(node_type, ft.Colors.GREY)
        type_label = NODE_TYPE_LABELS.get(node_type, node_type.value)

        if node.confidence >= 0.7:
            conf_color = ft.Colors.GREEN
        elif node.confidence >= 0.5:
            conf_color = ft.Colors.ORANGE
        else:
            conf_color = ft.Colors.RED

        content_parts = [
            ft.Icon(icon, color=color, size=20),
            ft.Container(
                content=ft.Text(type_label, size=11, color=color, weight=ft.FontWeight.BOLD),
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                bgcolor=color.with_opacity(0.1, ft.Colors.RED),
                border_radius=4,
            ),
            ft.Text(
                node.content,
                size=14,
                expand=True,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]

        if node.stocks:
            for stock in node.stocks[:3]:
                content_parts.append(
                    ft.Container(
                        content=ft.Text(stock, size=11, color=ft.Colors.WHITE),
                        bgcolor=color,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4,
                    )
                )

        content_parts.append(
            ft.Text(
                f"{node.confidence:.0%}",
                size=12,
                color=conf_color,
                weight=ft.FontWeight.BOLD,
            )
        )

        relation_text = ""
        if self.chain:
            edges = [e for e in self.chain.edges if e.to_node == node.id]
            if edges:
                relation_text = edges[0].relation

        card_content = ft.Column(
            [ft.Row(content_parts, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)],
            spacing=2,
        )

        if relation_text:
            card_content.controls.append(
                ft.Text(
                    f"  关系: {relation_text}",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        return ft.Container(
            content=card_content,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            margin=ft.Margin.only(left=indent),
            bgcolor=ft.Colors.SURFACE_BRIGHT,
            border_radius=8,
            border=ft.Border.all(1, color.with_opacity(0.3, ft.Colors.RED)),
            ink=True,
            tooltip=(
                f"ID: {node.id}\n"
                f"类型: {type_label}\n"
                f"置信度: {node.confidence:.2%}\n"
                f"来源: {', '.join(node.sources) if node.sources else '无'}"
            ),
        )
