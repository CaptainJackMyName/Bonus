# 红利
一个可用于股票分析的因果推断智能体。

## 项目简介

**红利** 是一款面向价值投资者的因果推断智能桌面应用。它能够自动从多个财经信息源（如新浪财经、Tavily搜索等）获取热点新闻，利用大语言模型进行深度因果推理，最终输出可能因新闻事件而价格上涨的股票，并展示完整的因果推断链。应用提供全自动分析和逐步人工确认两种推理模式，帮助用户理清市场逻辑，辅助投资决策。

本应用基于 Python 与 Flet 框架构建，可在 Windows 桌面环境原生运行，界面现代、操作简便，所有底层检索能力均以可插拔的 Skill 形式实现，便于扩展和维护。

---

## 功能特性

- **多源热点抓取**：同时从[GroundAPI](https://groundapi.net/)、[Tavily](https://www.tavily.com/)、[SearchAPI](https://serpapi.com/) 等渠道获取最新财经新闻与热点事件，确保信息覆盖面。
- **大模型因果推断**：利用大语言模型对新闻进行实体识别、事件关联、因果链构建，推导出可能受影响的上市公司。
- **基本面数据验证**：基于 [akshare](https://akshare.akfamily.xyz/) 获取推荐股票的估值指标（PE/PB/PS/市值）与近几个季度财务数据（营收、毛利率、净利率、ROE），结合消息面与基本面由 LLM 综合评估股价上涨的可靠性，动态调整推荐置信度。
- **因果链可视化**：以树状或流程图形式展示从“宏观事件→产业环节→公司→股价预期”的完整推理路径。
- **双模式推理**：
  - **全自动模式**：一键分析，直接给出最终推荐股票及推理链。
  - **逐步确认模式**：每一步中间推断结论都需用户确认，通过后方可继续，增强可信度与可解释性。
- **Skill 插件体系**：每个信息源、每种分析工具均作为独立 Skill，可自由启用、禁用或扩展。新闻信息源 Skill 与基本面数据 Skill 分离，职责清晰。
- **本地运行**：纯桌面应用，无需部署服务器，保护数据隐私（API Key 等敏感信息本地保存）。
- **价值投资导向**：聚焦基本面逻辑与事件驱动，帮助投资者理解“为什么涨”，而非单纯追热点。

---

## 因果推断方法论

本智能体遵循“事件→影响链条→受益标的→基本面验证”的推理框架：

1. **事件识别**：从海量新闻中提取关键事件（政策发布、行业变革、公司公告、宏观数据等）。
2. **影响扩散**：分析事件对产业链上中下游、相关行业、竞争格局的传导效应。
3. **标的映射**：将受影响的环节映射到具体 A 股 / 港股 / 美股上市公司。
4. **股价预期**：结合市场情绪、历史类似事件反应，判断股价短期上涨可能性。
5. **基本面验证**：调用 akshare 获取候选标的的估值指标与近几个季度财务数据，由 LLM 结合消息面利好与基本面健康度综合评估，动态调整置信度。
6. **置信度评估**：综合信息源可靠性、因果强度、基本面状况、市场环境，给出最终推理置信度。

整个推理过程以结构化数据呈现，每一步都可追溯、可质疑、可修正。

---

## 系统架构

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
│  - 基本面验证与置信度调整               │
└──────┬──────────────────┬──────────────┘
       │                  │
┌──────▼──────┐   ┌──────▼──────────────┐
│   Skill 层   │   │   LLM 调用模块      │
│  - 新浪财经  │   │  - Chat Completion │
│  - Tavily   │   │  - 结构化输出解析    │
│  - akshare  │   │  - Prompt 模板管理  │
│  (基本面)    │   │  - 基本面评估       │
└──────┬──────┘   └─────────────────────┘
       │
┌──────▼─────────────────────────────────┐
│         本地配置 & 数据存储              │
│  - API Keys (加密存储)                  │
│  - 推理历史 (SQLite)                    │
└────────────────────────────────────────┘
```

- **UI 层**：使用 Flet 构建，负责用户交互、结果展示。
- **推理引擎**：核心调度器，控制推理流程，调用 Skill 获取数据，调用 LLM 进行分析，并管理两种交互模式。在推荐提取后自动触发基本面验证，动态调整置信度。
- **Skill 层**：可扩展的插件式工具，分为新闻信息源 Skill（继承 `BaseSkill`，对外提供 `async fetch_news(query, top_k)`）和基本面数据 Skill（继承 `BaseFundamentalSkill`，对外提供 `async fetch_fundamental(stock_code)`）。
- **LLM 模块**：封装对 OpenAI / 兼容接口的调用，通过精心设计的 Prompt 引导模型输出结构化推理链与基本面评估结果。
- **数据层**：本地 SQLite 记录历史分析，便于回顾。

---

## 技术栈

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| 编程语言 | Python 3.10+ | 主语言 |
| 桌面框架 | Flet | 基于 Flutter 的 Python 桌面 UI 框架，支持 Windows |
| 异步处理 | asyncio | 多源并发抓取与 LLM 调用 |
| HTTP 客户端 | httpx, aiohttp | 请求财经接口与搜索引擎 |
| LLM 接入 | openai Python SDK | 支持 OpenAI、DeepSeek等兼容接口 |
| 搜索引擎 | Tavily API | 用于获取实时新闻与事件背景 |
| 网页解析 | beautifulsoup4, lxml | 解析新浪财经等 HTML 页面（若无标准 API） |
| 基本面数据 | akshare | 获取 A 股估值指标（PE/PB/PS）与财务报表（营收、毛利率、ROE） |
| 数据存储 | aiosqlite | 轻量级异步 SQLite 操作 |
| 加密存储 | cryptography | 加密保存 API Key 等敏感信息 |
| 配置管理 | python-dotenv, yaml | 环境变量与配置文件 |

---

## 安装与运行

### 环境要求

- Windows 10 / 11（64 位）
- Python 3.10 或以上（建议使用虚拟环境）
- 稳定的网络连接

### 获取代码

```bash
git clone https://github.com/your-org/dividend-agent.git
cd dividend-agent
```

### 创建虚拟环境（推荐）

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 安装依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 核心依赖示例：

```
flet>=0.23.0
openai>=1.0.0
httpx>=0.27.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
aiosqlite>=0.20.0
cryptography>=41.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
akshare>=1.18.0
```

### 配置 API Key

1. 复制配置模板：

```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml`，填入所需 API Key：

```yaml
llm:
  provider: "openai"          # 可选 openai / deepseek / qwen
  api_key: "sk-xxxx"         # 你的 LLM API Key
  model: "gpt-4o"            # 推荐具备强推理能力的模型
  base_url: ""               # 若使用中转，填入 base_url

skills:
  tavily:
    api_key: "tvly-xxxx"     # Tavily Search API Key
    enabled: true
  GroundAPI:
    api_key: "groundapi-xxxx" # GroundAPI API Key
    enabled: true
  akshare:
    enabled: true            # akshare 基本面数据获取（需 pip install akshare）
    recent_quarters: 4       # 获取近几个季度的财务数据
  # 可继续添加其他信息源
```

> 安全提醒：请勿将 `config.yaml` 提交至版本控制系统。项目默认包含 `.gitignore` 忽略该文件。

### 环境要求
Windows 10 / 11（64 位）  
Python 3.10 或以上  
稳定的网络连接  

### 从 PyPI 安装（推荐）  
```bash
pip install bonus
```
安装完成后，直接在命令行启动：
```bash
bonus
```

### 从源码安装（开发者）
```bash
git clone https://github.com/your-org/Bonus.git
cd Bonus
pip install -e ".[dev]"
```
启动应用：

```bash
bonus
```
首次启动将自动创建本地数据库和历史记录表。

---

## 项目结构

```
Bonus/                          # 项目根目录
├── pyproject.toml              # 项目元数据、依赖、构建配置
├── README.md                   # 项目文档（本文件）
├── LICENSE                     # MIT 许可证
├── .gitignore
├── src/
│   └── bonus/                  # 主包（可发布到 PyPI）
│       ├── __init__.py
│       ├── __main__.py         # 入口：python -m bonus 调用
│       ├── app.py              # Flet 应用主逻辑，页面路由
│       ├── config.yaml         # 默认配置模板（不含密钥）
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_view.py    # 主界面布局与分析按钮
│       │   ├── result_view.py  # 推理结果与因果链展示
│       │   ├── chain_widget.py # 因果链树状图组件
│       │   └── confirm_dialog.py # 逐步确认弹窗组件
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── engine.py       # 推理引擎，模式调度
│       │   ├── state_machine.py # 状态机（逐步确认模式）
│       │   └── causal_chain.py # 因果链数据结构与构建
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── base.py         # Skill 抽象基类（新闻信息源）
│       │   ├── fundamental_base.py # 基本面数据 Skill 抽象基类
│       │   ├── sina_skill.py   # 新浪财经热点抓取
│       │   ├── tavily_skill.py # Tavily 搜索
│       │   ├── akshare_skill.py # akshare 基本面数据获取
│       │   └── registry.py     # Skill 注册与加载
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py       # LLM 统一调用接口
│       │   ├── prompts.py      # Prompt 模板管理
│       │   └── parser.py       # 结构化输出解析
│       ├── models/
│       │   ├── __init__.py
│       │   ├── news.py         # 新闻/事件数据模型
│       │   ├── inference.py    # 推理节点、因果边模型
│       │   ├── stock.py        # 股票信息模型
│       │   └── fundamental.py  # 基本面数据模型（估值、财务报表）
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── db.py           # SQLite 数据库初始化与操作
│       │   └── history.py      # 推理历史 CRUD
│       └── utils/
│           ├── __init__.py
│           ├── config.py       # 配置加载与加密
│           ├── logger.py       # 日志配置
│           └── async_utils.py  # 异步工具
├── tests/                      # 单元测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_skills.py
│   ├── test_engine.py
│   └── ...
└── docs/                       # 额外文档
    ├── skills_guide.md
    └── architecture.md
```

---

## 核心模块设计

### 1. Skill 插件体系

Skill 体系分为两类：**新闻信息源 Skill**（继承 `BaseSkill`）与 **基本面数据 Skill**（继承 `BaseFundamentalSkill`），职责分离、互不耦合。

**新闻信息源 Skill**：

```python
# src/bonus/skills/base.py
from abc import ABC, abstractmethod
from typing import List
from src.models.news import NewsItem

class BaseSkill(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def fetch_news(self, query: str, top_k: int = 10) -> List[NewsItem]:
        """异步获取新闻列表"""
        ...
```

**基本面数据 Skill**：

```python
# src/bonus/skills/fundamental_base.py
from abc import ABC, abstractmethod
from bonus.models.fundamental import StockFundamental

class BaseFundamentalSkill(ABC):
    name: str = "fundamental_base"
    description: str = "基本面数据源"

    @abstractmethod
    async def fetch_fundamental(self, stock_code: str) -> StockFundamental | None:
        """异步获取单只股票的基本面数据（估值、财务报表）"""
        ...
```

**已实现 Skill：**

- **SinaSkill**（新闻源）：抓取新浪财经实时热点、自选股新闻，通过解析 HTML 获取标题、摘要、时间、关联股票。
- **TavilySkill**（新闻源）：调用 Tavily Search API，传入 “A股 最新 政策 行业 影响” 等组合查询，返回结构化新闻。
- **AkShareSkill**（基本面）：基于 akshare 获取 A 股估值指标（PE-TTM / PB / PS-TTM / 总市值）与近几个季度财务数据（营收及同比、净利润及同比、毛利率、净利率、ROE）。akshare 为同步库，内部通过 `asyncio.to_thread` 在线程池中执行以避免阻塞事件循环。

Skill 注册与管理：

```python
# src/bonus/skills/registry.py
from src.skills.sina_skill import SinaSkill
from src.skills.tavily_skill import TavilySkill
from src.skills.akshare_skill import AkShareSkill

def load_skills(config) -> dict:
    """加载新闻信息源 Skill"""
    skills = {}
    if config['skills']['sina']['enabled']:
        skills['sina'] = SinaSkill()
    if config['skills']['tavily']['api_key']:
        skills['tavily'] = TavilySkill(api_key=config['skills']['tavily']['api_key'])
    return skills

def load_fundamental_skills(config) -> dict:
    """加载基本面数据 Skill"""
    skills = {}
    if config['skills']['akshare']['enabled']:
        skills['akshare'] = AkShareSkill(recent_quarters=config['skills']['akshare']['recent_quarters'])
    return skills
```

### 2. 推理引擎与两种模式

引擎 `CausalEngine` 负责整个分析流程，在推荐提取后增加基本面验证环节：

```python
# src/bonus/agent/engine.py
class CausalEngine:
    def __init__(self, skills: dict, llm_client, mode: str = "auto",
                 fundamental_skills: dict | None = None):
        self.skills = skills
        self.llm = llm_client
        self.mode = mode  # "auto" 或 "stepwise"
        self.fundamental_skills = fundamental_skills or {}

    async def run(self, query: str = "今日热点", callback=None):
        # 1. 并发抓取所有 Skill
        news_list = await self._gather_news(query)

        # 2. LLM 生成因果推断链（初始）
        chain = await self._initial_causal_chain(news_list)

        if self.mode == "auto":
            # 全自动：直接深挖至最终推荐
            final_chain = await self._deep_inference(chain)
        else:
            # 逐步确认：通过 callback 与 UI 交互
            final_chain = await self._stepwise_inference(chain, callback)

        # 3. 提取股票推荐
        recommendations = ChainBuilder.extract_recommendations(final_chain)

        # 4. 基本面验证（若启用 akshare 等 Skill）
        if recommendations and self.fundamental_skills:
            recommendations = await self._enhance_with_fundamentals(recommendations)

        return final_chain, recommendations
```

**基本面验证流程** (`_enhance_with_fundamentals`)：
1. 收集所有推荐股票代码，批量调用 `AkShareSkill.fetch_fundamentals` 获取估值与财务数据。
2. 对每只股票，调用 LLM 结合「消息面推荐理由 + 原始置信度 + 基本面数据」进行综合评估。
3. LLM 输出基本面评分、分析摘要与调整后置信度，回填到 `StockRecommendation`。
4. 最终按调整后置信度重新排序推荐列表。

**逐步确认模式**下，引擎每产生一个中间结论节点（如“政策利好新能源汽车”），就暂停并调用 UI 的回调函数显示给用户。用户确认或修改后，引擎再基于确认内容继续推理。这要求在 UI 端实现一个状态机，管理当前等待确认的节点。

### 3. 因果链数据结构

```python
# src/bonus/models/inference.py
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class NodeType(Enum):
    EVENT = "event"
    MACRO = "macro"
    INDUSTRY = "industry"
    COMPANY = "company"
    PRICE_EXPECT = "price_expect"

class CausalNode(BaseModel):
    id: str
    type: NodeType
    content: str           # 自然语言描述
    confidence: float      # 0.0 ~ 1.0
    sources: List[str]     # 引用新闻 ID
    stocks: List[str] = [] # 若为 company 节点，则包含股票代码

class CausalEdge(BaseModel):
    from_node: str
    to_node: str
    relation: str          # 如 "利好", "成本下降", "竞争加剧"
```

完整链为 `List[CausalNode]` + `List[CausalEdge]`，前端据此绘制图形。

基本面数据模型（`models/fundamental.py`）：

```python
class StockFundamental(BaseModel):
    code: str
    name: str
    industry: str
    pe_ttm: float | None       # 滚动市盈率
    pb: float | None           # 市净率
    ps_ttm: float | None       # 市销率
    total_market_cap: float | None  # 总市值
    financials: list[FinancialQuarter]  # 近几个季度财务数据
    fundamental_score: float | None     # LLM 基本面评分
    fundamental_summary: str            # 基本面分析摘要
```

### 4. LLM 调用与 Prompt 设计

`llm/client.py` 封装 OpenAI 兼容 API，支持 Function Calling 以强制输出结构化因果链。

关键 Prompt 模板（位于 `prompts.py`）：

- `CausalChainPrompt`：要求模型根据一组新闻，生成事件 → 产业 → 公司的因果图，输出 JSON 格式节点和边。
- `DeepInferencePrompt`：在全自动模式下，让模型基于已有节点继续扩展，寻找更多受益标的。
- `ConfirmationPrompt`：将当前节点展示给用户，并询问是否同意，或要求用户提供补充信息。
- `FundamentalAnalysisPrompt`：结合消息面推荐理由与 akshare 基本面数据，由 LLM 综合评估股票近期上涨可能性，输出基本面评分、分析摘要与调整后置信度。

模型输出解析器 `parser.py` 将 JSON 转换为 `CausalNode` / `CausalEdge` / `FundamentalAssessment` 对象，并进行校验。

### 5. Flet 前端界面

主界面使用 Flet 的 `ft.Column`、`ft.Row`、`ft.Tabs` 等组件：

- **分析面板**：包含查询输入框（默认“今日热点”）、模式选择开关（自动 / 逐步）、开始分析按钮。
- **进度展示**：分析过程中展示当前状态（“正在抓取新浪财经…”、“正在推理第3步…”）。
- **因果链视图**：使用 `ft.Treeview` 或自定义绘图组件，展示节点与连线，点击节点可查看详情。
- **股票推荐列表**：底部卡片列出推荐股票，含名称、代码、上涨逻辑、置信度。

逐步确认对话框：

```python
# src/bonus/ui/confirm_dialog.py
def show_confirmation(page, node: CausalNode, on_confirm, on_reject):
    def confirm_click(e):
        on_confirm(node)
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        title=ft.Text("请确认推理步骤"),
        content=ft.Text(node.content),
        actions=[
            ft.TextButton("确认", on_click=confirm_click),
            ft.TextButton("修正", on_click=...),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()
```

---

## 操作流程示例

### 全自动模式

1. 打开“红利”应用，默认显示分析面板。
2. 在输入框保留“今日热点”，选择“全自动分析”模式。
3. 点击“开始分析”。
4. 界面显示进度：正在抓取新浪财经…正在抓取Tavily…已完成 12 条新闻。
5. LLM 开始推理，状态栏显示“生成因果链…发现潜在标的…”；
6. 推理完成后，自动进入基本面验证阶段：状态栏显示“正在通过 akshare 获取基本面数据…正在评估 招商银行 基本面…”。
7. 约 15-40 秒后，展示最终结果：
   - 因果链树状图（例如：央行降准 → 银行流动性宽松 → 招商银行、兴业银行受益 → 股价有望上涨）
   - 推荐股票卡片列表，每张卡片显示：消息面上涨逻辑、基本面数据（PE/PB/市值、近季财务表格）、基本面分析摘要、调整后置信度。
8. 用户可点击任意节点查看详细新闻来源。

### 逐步确认模式

1. 选择“逐步确认分析”模式，点击开始。
2. 系统抓取新闻后，弹出第一个推理节点：“今日央行宣布降准0.5个百分点，释放长期资金约1万亿元”，置信度 0.97，附带新闻链接。用户点击“确认”。
3. 系统继续推理，弹出第二个节点：“此事件将提升银行可用资金，降低负债成本，利好银行业”，用户认为合理，点击“确认”。
4. 系统弹出第三个节点：“受益银行包括招商银行（资产质量优）、宁波银行（小微业务弹性大）”，用户可点击“修正”添加或删除股票，然后确认。
5. 最终呈现完整的因果链和推荐股票。
6. 若用户在某一步选择“否决”，系统将回溯并尝试其他推理路径。

---

## 开发与扩展

### 添加新的信息源 Skill

1. 在 `src/bonus/skills/` 下新建文件，继承 `BaseSkill`，实现 `fetch_news` 方法。
2. 在 `config.yaml` 中添加对应配置项。
3. 在 `registry.py` 的 `load_skills` 中注册该 Skill。

```python
class EastMoneySkill(BaseSkill):
    name = "eastmoney"
    async def fetch_news(self, query, top_k=10):
        # 实现东方财富热点抓取
        ...
```

### 添加新的基本面数据 Skill

1. 在 `src/bonus/skills/` 下新建文件，继承 `BaseFundamentalSkill`，实现 `fetch_fundamental` 方法。
2. 在 `config.yaml` 中添加对应配置项。
3. 在 `registry.py` 的 `load_fundamental_skills` 中注册该 Skill。

```python
class TushareSkill(BaseFundamentalSkill):
    name = "tushare"
    async def fetch_fundamental(self, stock_code: str) -> StockFundamental | None:
        # 实现通过 Tushare 获取基本面数据
        ...
```

### 修改 LLM Provider

修改 `config.yaml` 中的 `llm.provider` 和 `model`，同时可在 `llm/client.py` 中适配不同 API 的差异。目前内置支持 OpenAI、DeepSeek（使用 OpenAI 兼容接口）、阿里通义千问。

### 本地模型支持

若希望完全本地推理，可使用 Ollama 等工具，将 `base_url` 指向本地服务，`model` 设为本地模型名。注意本地模型需具备较强的指令跟随和 JSON 输出能力。

---

## 路线图

- [x] 基础框架与双模式推理
- [x] GroundAPI 与 Tavily 集成
- [x] akshare 基本面数据验证（估值、财务报表、LLM 综合评估）
- [ ] 更多信息源（东方财富、雪球、财联社）
- [ ] 历史推理记录查询与对比
- [ ] 因果链图形化展示优化（D3.js 风格）
- [ ] 用户自定义推理规则
- [ ] 集成股价数据，回测推理准确率
- [ ] 打包为 Windows 安装包（使用 PyInstaller + Flet 打包）

---

## 常见问题

**Q: 分析结果不准确怎么办？**
A: 因果推断依赖 LLM 能力和新闻质量。可尝试：1) 更换更强模型（如 gpt-4o、claude-3.5-sonnet）；2) 在逐步确认模式中手动修正推理路径；3) 扩展更多高质量信息源；4) 启用 akshare 基本面验证，使置信度结合财务数据更可靠。

**Q: akshare 基本面验证的作用是什么？**
A: 消息面利好仅反映“预期”，而基本面数据反映“实力”。akshare 获取的 PE/PB/营收/毛利率/ROE 等指标，让 LLM 能判断候选标的是否真正具备上涨的基本面支撑。例如某股票虽受政策利好，但若估值过高、营收下滑，系统会下调其置信度，避免“只追消息、不看质地”的风险。

**Q: 如何保护我的 API Key？**
A: 所有密钥保存在本地 `config.yaml`，应用运行期间仅在内存中解密使用，不会上传至任何远程服务器。建议使用 Windows 文件权限限制访问。

**Q: 能在 macOS 或 Linux 上运行吗？**
A: Flet 本身跨平台，但本应用开发时以 Windows 为目标。在 macOS/Linux 上可能需微调路径和依赖，理论上可运行。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request。请遵循以下规范：

1. Fork 本仓库并创建特性分支。
2. 为新 Skill 或功能编写测试用例。
3. 确保代码通过 `flake8` 与 `pytest`。
4. 更新相关文档。

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

> 免责声明：本应用仅为辅助投资研究工具，不构成任何投资建议。股票市场存在风险，请谨慎决策。使用者需自行承担投资盈亏。

---

*红利 —— 让每一次决策都有因可循。*