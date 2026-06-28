# 红利 Bonus - 架构设计文档

## 整体架构

红利采用分层架构设计，各层职责清晰、解耦：

```
┌─────────────────────────────────────────┐
│                Flet 桌面 UI               │
│  (主页面、分析面板、因果链展示、历史记录)    │
└──────────────────┬──────────────────────┘
                   │ 用户交互 / 模式选择
┌──────────────────▼──────────────────────┐
│              推理引擎 (Agent)            │
│  - 全自动模式 / 逐步确认模式控制          │
│  - 因果推断状态机管理                   │
└──────┬──────────────────┬──────────────┘
       │                  │
┌──────▼──────┐   ┌──────▼──────────────┐
│   Skill 层   │   │   LLM 调用模块      │
│  - 新浪财经  │   │  - Chat Completion │
│  - Tavily   │   │  - 结构化输出解析    │
│  - 其他源    │   │  - Prompt 模板管理  │
└──────┬──────┘   └─────────────────────┘
       │
┌──────▼─────────────────────────────────┐
│         本地配置 & 数据存储              │
│  - API Keys (加密存储)                  │
│  - 推理历史 (SQLite)                    │
└────────────────────────────────────────┘
```

## 模块说明

### 1. UI 层 (`bonus/ui/`)

- `main_view.py`: 主界面，包含查询输入、模式选择、分析按钮和进度展示
- `result_view.py`: 结果展示视图，包含因果链树和推荐股票卡片
- `chain_widget.py`: 因果链树状图组件，递归渲染节点和关系边
- `confirm_dialog.py`: 逐步确认弹窗，支持确认/否决/修改

### 2. 推理引擎层 (`bonus/agent/`)

- `engine.py`: 核心调度器 `CausalEngine`，控制全自动和逐步确认两种模式
- `state_machine.py`: 逐步确认模式状态机，管理 WAITING_CONFIRM 等状态
- `causal_chain.py`: 因果链构建辅助工具，包括新闻上下文格式化和推荐提取

### 3. Skill 插件层 (`bonus/skills/`)

- `base.py`: 抽象基类 `BaseSkill`，定义 `fetch_news` 接口
- `sina_skill.py`: 新浪财经热点抓取
- `tavily_skill.py`: Tavily Search API 搜索
- `registry.py`: 根据配置动态加载和注册 Skill

### 4. LLM 模块 (`bonus/llm/`)

- `client.py`: OpenAI 兼容 API 客户端，支持 JSON 输出解析
- `prompts.py`: Prompt 模板（因果链构建、深度推理、逐步确认）
- `parser.py`: 结构化输出解析器，将 JSON 转为因果链模型

### 5. 数据模型层 (`bonus/models/`)

- `news.py`: `NewsItem` 新闻数据模型
- `inference.py`: `CausalNode`/`CausalEdge`/`CausalChain` 因果推理模型
- `stock.py`: `Stock`/`StockRecommendation` 股票推荐模型

### 6. 存储层 (`bonus/storage/`)

- `db.py`: 异步 SQLite 数据库管理器
- `history.py`: 分析历史 CRUD

### 7. 工具层 (`bonus/utils/`)

- `config.py`: 配置加载，支持多级路径查找
- `logger.py`: 日志配置
- `async_utils.py`: 异步工具函数（并发限制、超时控制）

## 因果推断流程

### 全自动模式

1. **新闻抓取**: 并发调用所有启用的 Skill，合并去重
2. **初始因果链**: LLM 根据新闻生成 event→macro→industry→company→price_expect 链
3. **深度推理**: 多轮 LLM 调用，扩展更多受益标的
4. **推荐提取**: 从因果链中提取公司节点，计算综合置信度

### 逐步确认模式

1. **新闻抓取**: 同全自动
2. **初始因果链**: 同全自动
3. **拓扑排序**: 对节点进行拓扑排序
4. **逐节点确认**: 每个非事件节点弹出确认对话框
   - 确认: 加入确认链，继续下一步
   - 否决: 跳过当前节点
   - 修改: 基于修改内容重新推理
5. **最大否决**: 达到最大否决次数终止

## 数据流

```
用户输入查询
    ↓
Skill 层并发抓取 → List[NewsItem]
    ↓
LLM 生成因果链 → CausalChain (nodes + edges)
    ↓
深度推理扩展 → CausalChain (更新)
    ↓
推荐提取 → List[StockRecommendation]
    ↓
UI 展示 + SQLite 持久化
```
