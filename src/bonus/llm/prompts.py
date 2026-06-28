"""Prompt 模板管理"""

# 系统角色提示词
SYSTEM_PROMPT = """你是一位资深的财经分析师和因果推断专家，擅长从新闻事件中推导出对股票市场的影响链条。
你的任务是基于给定的新闻，构建从「事件→产业→公司→股价预期」的完整因果推理链。

推理原则：
1. 因果链条必须逻辑严密，每一步推导都有新闻依据
2. 节点内容要具体，避免空泛描述
3. 置信度要客观反映推理的确定性（0.0~1.0）
4. 股票推荐聚焦于因事件直接受益的标的
5. 所有输出必须为合法 JSON 格式

节点类型说明：
- event: 新闻事件本身
- macro: 宏观影响（如货币政策、行业政策）
- industry: 产业环节影响（如上游原材料、中游制造、下游应用）
- company: 受益公司（需附带股票代码）
- price_expect: 股价预期判断
"""

# 事件提取与因果链构建提示词
CAUSAL_CHAIN_PROMPT = """请根据以下新闻列表，构建因果推理链。

查询主题：{query}

新闻列表：
{news_text}

请输出 JSON 格式的因果链，结构如下：
{{
  "nodes": [
    {{
      "id": "n1",
      "type": "event",
      "content": "事件描述",
      "confidence": 0.95,
      "sources": ["news_id_1"],
      "stocks": []
    }},
    {{
      "id": "n2",
      "type": "macro",
      "content": "宏观影响描述",
      "confidence": 0.8,
      "sources": ["news_id_1"],
      "stocks": []
    }},
    {{
      "id": "n3",
      "type": "industry",
      "content": "产业环节影响描述",
      "confidence": 0.75,
      "sources": [],
      "stocks": []
    }},
    {{
      "id": "n4",
      "type": "company",
      "content": "受益公司描述",
      "confidence": 0.7,
      "sources": [],
      "stocks": ["600036"]
    }},
    {{
      "id": "n5",
      "type": "price_expect",
      "content": "股价预期描述",
      "confidence": 0.65,
      "sources": [],
      "stocks": ["600036"]
    }}
  ],
  "edges": [
    {{
      "from_node": "n1",
      "to_node": "n2",
      "relation": "利好"
    }},
    {{
      "from_node": "n2",
      "to_node": "n3",
      "relation": "传导至"
    }}
  ]
}}

要求：
1. 每条新闻至少生成一个 event 节点
2. 从 event 节点出发，逐层推导至 company 和 price_expect 节点
3. company 节点的 stocks 字段必须包含真实股票代码（A股6位数字）
4. edges 要完整描述节点间的因果关系
5. 仅输出 JSON，不要包含其他文字
"""

# 深度推理提示词（全自动模式扩展）
DEEP_INFERENCE_PROMPT = """请基于已有的因果链，进一步深挖更多可能受益的股票。

已有因果链：
{chain_text}

当前已推荐的股票：{existing_stocks}

请扩展因果链，寻找新的受益标的。输出 JSON 格式：
{{
  "new_nodes": [
    {{
      "id": "n_new_1",
      "type": "company",
      "content": "新受益公司描述",
      "confidence": 0.6,
      "sources": [],
      "stocks": ["000001"],
      "parent_ids": ["n3"]
    }},
    {{
      "id": "n_new_2",
      "type": "price_expect",
      "content": "股价预期",
      "confidence": 0.55,
      "sources": [],
      "stocks": ["000001"],
      "parent_ids": ["n_new_1"]
    }}
  ],
  "new_edges": [
    {{
      "from_node": "n3",
      "to_node": "n_new_1",
      "relation": "利好"
    }}
  ]
}}

要求：
1. 寻找已有因果链中尚未覆盖的受益公司
2. 新节点需指明 parent_ids 关联到已有节点
3. 避免重复推荐已有股票
4. 仅输出 JSON
"""

# 逐步确认提示词
CONFIRMATION_PROMPT = """请基于当前推理节点，生成下一步推理结论。

当前已确认的节点：
{confirmed_nodes}

当前待确认节点：
{current_node}

用户反馈：{user_feedback}

请生成下一步推理节点，输出 JSON 格式：
{{
  "node": {{
    "id": "n_next",
    "type": "industry|company|price_expect",
    "content": "推理结论描述",
    "confidence": 0.7,
    "sources": [],
    "stocks": [],
    "parent_ids": ["当前节点id"]
  }},
  "is_final": false
}}

如果当前节点已经是最终结论（price_expect），请设置 is_final 为 true。
仅输出 JSON。
"""

# 事件提取提示词
EVENT_EXTRACTION_PROMPT = """请从以下新闻中提取关键事件，并判断其对股票市场的影响。

新闻：
{news_text}

请输出 JSON 格式：
{{
  "events": [
    {{
      "title": "事件标题",
      "description": "事件描述",
      "event_type": "policy|industry|company|macro",
      "impact_level": "high|medium|low",
      "affected_sectors": ["行业1", "行业2"]
    }}
  ]
}}

仅输出 JSON。
"""

# 基本面分析提示词
FUNDAMENTAL_ANALYSIS_PROMPT = """请基于消息面推荐理由和股票基本面数据，综合评估该股票近期上涨的可能性。

股票代码：{stock_code}
消息面推荐理由：{reason}
原始置信度（仅基于消息面）：{original_confidence:.2f}

基本面数据：
{fundamental_text}

评估要求：
1. 结合消息面利好与基本面健康度，判断股价上涨的可靠性
2. 若基本面优秀（低估值、高增长、高毛利率），可适当上调置信度
3. 若基本面较差（高估值、营收下滑、亏损），应下调置信度
4. 若基本面与消息面逻辑一致（如降准利好银行，该银行 ROE 高），置信度提升更明显
5. 给出基本面评分（0.0~1.0）和简要分析

请输出 JSON 格式：
{{
  "stock_code": "{stock_code}",
  "fundamental_score": 0.7,
  "fundamental_summary": "基本面分析摘要（100字以内）",
  "adjusted_confidence": 0.75
}}

仅输出 JSON。
"""
