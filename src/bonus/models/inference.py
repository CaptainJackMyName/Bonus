"""推理节点、因果边与因果链模型"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """因果节点类型"""

    EVENT = "event"              # 事件节点
    MACRO = "macro"              # 宏观影响节点
    INDUSTRY = "industry"        # 产业环节节点
    COMPANY = "company"          # 公司节点
    PRICE_EXPECT = "price_expect"  # 股价预期节点


class CausalNode(BaseModel):
    """因果推理节点"""

    id: str = Field(..., description="节点唯一标识")
    type: NodeType = Field(..., description="节点类型")
    content: str = Field(..., description="自然语言描述")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度 0.0~1.0")
    sources: List[str] = Field(default_factory=list, description="引用新闻 ID 列表")
    stocks: List[str] = Field(default_factory=list, description="公司节点关联的股票代码")
    parent_ids: List[str] = Field(default_factory=list, description="父节点 ID 列表")
    metadata: Dict[str, str] = Field(default_factory=dict, description="附加元数据")


class CausalEdge(BaseModel):
    """因果推理边"""

    from_node: str = Field(..., description="起始节点 ID")
    to_node: str = Field(..., description="目标节点 ID")
    relation: str = Field(..., description="因果关系描述（如 利好、成本下降）")


class CausalChain(BaseModel):
    """完整因果推理链"""

    nodes: List[CausalNode] = Field(default_factory=list, description="所有节点")
    edges: List[CausalEdge] = Field(default_factory=list, description="所有边")
    query: str = Field(default="", description="原始查询")

    def add_node(self, node: CausalNode) -> None:
        """添加节点（若 ID 已存在则更新）"""
        for i, existing in enumerate(self.nodes):
            if existing.id == node.id:
                self.nodes[i] = node
                return
        self.nodes.append(node)

    def add_edge(self, edge: CausalEdge) -> None:
        """添加边（去重）"""
        for existing in self.edges:
            if existing.from_node == edge.from_node and existing.to_node == edge.to_node:
                existing.relation = edge.relation
                return
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[CausalNode]:
        """根据 ID 获取节点"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_children(self, node_id: str) -> List[CausalNode]:
        """获取某节点的所有子节点"""
        child_ids = [e.to_node for e in self.edges if e.from_node == node_id]
        return [n for n in self.nodes if n.id in child_ids]

    def get_parents(self, node_id: str) -> List[CausalNode]:
        """获取某节点的所有父节点"""
        parent_ids = [e.from_node for e in self.edges if e.to_node == node_id]
        return [n for n in self.nodes if n.id in parent_ids]

    def get_root_nodes(self) -> List[CausalNode]:
        """获取根节点（没有父节点的节点）"""
        all_targets = {e.to_node for e in self.edges}
        return [n for n in self.nodes if n.id not in all_targets]

    def get_company_nodes(self) -> List[CausalNode]:
        """获取所有公司类型节点"""
        return [n for n in self.nodes if n.type == NodeType.COMPANY]

    def get_price_expect_nodes(self) -> List[CausalNode]:
        """获取所有股价预期节点"""
        return [n for n in self.nodes if n.type == NodeType.PRICE_EXPECT]

    def get_path_to_root(self, node_id: str) -> List[CausalNode]:
        """获取从指定节点到根节点的路径"""
        path = []
        current = self.get_node(node_id)
        visited = set()
        while current and current.id not in visited:
            visited.add(current.id)
            path.append(current)
            parents = self.get_parents(current.id)
            if parents:
                current = parents[0]
            else:
                break
        return path
