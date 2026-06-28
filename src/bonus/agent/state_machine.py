"""逐步确认模式状态机"""

from enum import Enum
from typing import Callable, Optional

from bonus.models.inference import CausalNode, NodeType
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class StepwiseState(str, Enum):
    """逐步确认模式状态"""

    IDLE = "idle"                    # 空闲
    FETCHING = "fetching"            # 正在抓取新闻
    INFERRING = "inferring"          # 正在推理
    WAITING_CONFIRM = "waiting_confirm"  # 等待用户确认
    CONFIRMED = "confirmed"          # 用户已确认
    REJECTED = "rejected"            # 用户已否决
    COMPLETED = "completed"          # 推理完成
    ERROR = "error"                  # 出错


class StepwiseStateMachine:
    """逐步确认推理状态机"""

    def __init__(self):
        self.state: StepwiseState = StepwiseState.IDLE
        self.current_node: Optional[CausalNode] = None
        self.confirmed_nodes: list[CausalNode] = []
        self.rejected_count: int = 0
        self.max_rejections: int = 3
        self._on_state_change: Optional[Callable] = None

    def set_callback(self, callback: Callable[[StepwiseState, Optional[CausalNode]], None]) -> None:
        """设置状态变更回调"""
        self._on_state_change = callback

    def transition(self, new_state: StepwiseState) -> None:
        """状态转换"""
        old_state = self.state
        self.state = new_state
        logger.info(f"状态机: {old_state.value} -> {new_state.value}")
        if self._on_state_change:
            self._on_state_change(new_state, self.current_node)

    def set_current_node(self, node: CausalNode) -> None:
        """设置当前待确认节点"""
        self.current_node = node
        self.transition(StepwiseState.WAITING_CONFIRM)

    def confirm(self) -> Optional[CausalNode]:
        """用户确认当前节点"""
        if self.state != StepwiseState.WAITING_CONFIRM:
            logger.warning(f"当前状态 {self.state.value} 不允许确认操作")
            return None

        if self.current_node:
            self.confirmed_nodes.append(self.current_node)
            confirmed = self.current_node
            self.current_node = None
            self.transition(StepwiseState.CONFIRMED)
            return confirmed
        return None

    def reject(self) -> None:
        """用户否决当前节点"""
        if self.state != StepwiseState.WAITING_CONFIRM:
            logger.warning(f"当前状态 {self.state.value} 不允许否决操作")
            return

        self.current_node = None
        self.rejected_count += 1
        self.transition(StepwiseState.REJECTED)
        logger.warning(f"用户否决推理节点 (第 {self.rejected_count} 次)")

    def is_max_rejections_reached(self) -> bool:
        """是否达到最大否决次数"""
        return self.rejected_count >= self.max_rejections

    def reset(self) -> None:
        """重置状态机"""
        self.state = StepwiseState.IDLE
        self.current_node = None
        self.confirmed_nodes = []
        self.rejected_count = 0
        logger.info("状态机已重置")

    def get_confirmed_summary(self) -> str:
        """获取已确认节点的摘要"""
        if not self.confirmed_nodes:
            return "暂无已确认的推理步骤"
        lines = []
        for i, node in enumerate(self.confirmed_nodes, 1):
            lines.append(f"步骤 {i} [{node.type.value}]: {node.content}")
        return "\n".join(lines)

    def is_final_node(self) -> bool:
        """当前节点是否为最终节点（股价预期）"""
        if self.current_node:
            return self.current_node.type == NodeType.PRICE_EXPECT
        return False
