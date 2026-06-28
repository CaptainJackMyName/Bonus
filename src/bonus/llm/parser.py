"""结构化输出解析器"""

import json
from typing import Any, Dict, List, Tuple

from bonus.models.fundamental import FundamentalAssessment
from bonus.models.inference import (
    CausalChain,
    CausalEdge,
    CausalNode,
    NodeType,
)
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_node(data: Dict[str, Any]) -> CausalNode:
    """解析单个节点"""
    node_type_str = data.get("type", "event")
    try:
        node_type = NodeType(node_type_str)
    except ValueError:
        logger.warning(f"未知节点类型: {node_type_str}，默认为 event")
        node_type = NodeType.EVENT

    return CausalNode(
        id=str(data.get("id", "")),
        type=node_type,
        content=str(data.get("content", "")),
        confidence=float(data.get("confidence", 0.5)),
        sources=[str(s) for s in data.get("sources", [])],
        stocks=[str(s) for s in data.get("stocks", [])],
        parent_ids=[str(p) for p in data.get("parent_ids", [])],
        metadata=data.get("metadata", {}),
    )


def _parse_edge(data: Dict[str, Any]) -> CausalEdge:
    """解析单条边"""
    return CausalEdge(
        from_node=str(data.get("from_node", "")),
        to_node=str(data.get("to_node", "")),
        relation=str(data.get("relation", "相关")),
    )


def parse_causal_chain_response(
    response: Any,
    query: str = "",
) -> CausalChain:
    """
    解析 LLM 返回的因果链 JSON。

    Args:
        response: 解析后的 JSON 对象（dict）
        query: 原始查询

    Returns:
        CausalChain 对象
    """
    if isinstance(response, str):
        response = json.loads(response)

    nodes_data = response.get("nodes", [])
    edges_data = response.get("edges", [])

    chain = CausalChain(query=query)

    for node_data in nodes_data:
        try:
            node = _parse_node(node_data)
            chain.add_node(node)
        except Exception as e:
            logger.warning(f"解析节点失败: {e}, data={node_data}")

    for edge_data in edges_data:
        try:
            edge = _parse_edge(edge_data)
            chain.add_edge(edge)
        except Exception as e:
            logger.warning(f"解析边失败: {e}, data={edge_data}")

    logger.info(
        f"因果链解析完成: {len(chain.nodes)} 个节点, {len(chain.edges)} 条边"
    )
    return chain


def parse_deep_inference_response(
    response: Any,
    existing_chain: CausalChain,
) -> Tuple[List[CausalNode], List[CausalEdge]]:
    """
    解析深度推理返回的新增节点和边。

    Args:
        response: 解析后的 JSON 对象
        existing_chain: 已有因果链

    Returns:
        (新增节点列表, 新增边列表)
    """
    if isinstance(response, str):
        response = json.loads(response)

    new_nodes_data = response.get("new_nodes", [])
    new_edges_data = response.get("new_edges", [])

    new_nodes: List[CausalNode] = []
    new_edges: List[CausalEdge] = []

    existing_stock_codes = set()
    for node in existing_chain.nodes:
        existing_stock_codes.update(node.stocks)

    for node_data in new_nodes_data:
        try:
            node = _parse_node(node_data)
            # 跳过已推荐股票的重复节点
            if node.type == NodeType.COMPANY and node.stocks:
                if all(s in existing_stock_codes for s in node.stocks):
                    logger.info(f"跳过重复股票节点: {node.stocks}")
                    continue
            new_nodes.append(node)
            existing_stock_codes.update(node.stocks)
        except Exception as e:
            logger.warning(f"解析深度推理节点失败: {e}")

    for edge_data in new_edges_data:
        try:
            edge = _parse_edge(edge_data)
            new_edges.append(edge)
        except Exception as e:
            logger.warning(f"解析深度推理边失败: {e}")

    logger.info(
        f"深度推理解析完成: {len(new_nodes)} 个新节点, {len(new_edges)} 条新边"
    )
    return new_nodes, new_edges


def parse_stepwise_node_response(response: Any) -> Tuple[CausalNode | None, bool]:
    """
    解析逐步确认模式的单步推理响应。

    Args:
        response: 解析后的 JSON 对象

    Returns:
        (下一步节点, 是否为最终结论)
    """
    if isinstance(response, str):
        response = json.loads(response)

    node_data = response.get("node")
    is_final = response.get("is_final", False)

    if not node_data:
        return None, is_final

    try:
        node = _parse_node(node_data)
        return node, is_final
    except Exception as e:
        logger.error(f"解析逐步推理节点失败: {e}")
        return None, is_final


def parse_fundamental_assessment(response: Any, stock_code: str = "") -> FundamentalAssessment:
    """
    解析 LLM 基本面评估响应。

    Args:
        response: 解析后的 JSON 对象
        stock_code: 股票代码（用于回填）

    Returns:
        FundamentalAssessment 对象
    """
    if isinstance(response, str):
        response = json.loads(response)

    code = str(response.get("stock_code", stock_code))
    score = float(response.get("fundamental_score", 0.5))
    score = max(0.0, min(1.0, score))

    adjusted = response.get("adjusted_confidence")
    if adjusted is not None:
        adjusted = max(0.0, min(1.0, float(adjusted)))

    return FundamentalAssessment(
        stock_code=code,
        fundamental_score=score,
        fundamental_summary=str(response.get("fundamental_summary", "")),
        adjusted_confidence=adjusted,
    )
