# Bonus
A causal inference agent for stock analysis

## Introduction

**Bonus** is a causal inference desktop application designed for value investors. It automatically fetches trending news from multiple financial information sources (such as Sina Finance, Tavily Search, etc.), leverages large language models for in-depth causal reasoning, and ultimately outputs stocks likely to rise in price due to news events, presenting the complete causal inference chain. The application offers both fully-automatic analysis and step-by-step manual confirmation reasoning modes, helping users clarify market logic and assist investment decisions.

Built on Python and the Flet framework, the application runs natively on Windows desktop environments with a modern interface and easy operation. All underlying retrieval capabilities are implemented as pluggable Skills for easy extension and maintenance.

---

## Features

- **Multi-source Trending News Aggregation**: Simultaneously fetches the latest financial news and trending events from channels such as [GroundAPI](https://groundapi.net/), [Tavily](https://www.tavily.com/), and [SearchAPI](https://serpapi.com/) to ensure comprehensive information coverage.
- **LLM-driven Causal Inference**: Uses large language models to perform entity recognition, event correlation, and causal chain construction on news, deriving potentially affected listed companies.
- **Fundamental Data Validation**: Retrieves valuation metrics (PE/PB/PS/Market Cap) and recent quarterly financial data (revenue, gross margin, net margin, ROE) for recommended stocks via [akshare](https://akshare.akfamily.xyz/). The LLM then comprehensively evaluates the reliability of price increases by combining news sentiment with fundamentals, dynamically adjusting recommendation confidence.
- **Causal Chain Visualization**: Presents the complete reasoning path from "macro event → industry segment → company → price expectation" in tree or flowchart form.
- **Dual-mode Reasoning**:
  - **Fully-automatic Mode**: One-click analysis that directly provides final recommended stocks and reasoning chains.
  - **Step-by-step Confirmation Mode**: Each intermediate inference conclusion requires user confirmation before proceeding, enhancing credibility and interpretability.
- **Skill Plugin System**: Each information source and analysis tool is an independent Skill that can be freely enabled, disabled, or extended. News source Skills and fundamental data Skills are separated with clear responsibilities.
- **Local Execution**: A pure desktop application with no server deployment required, protecting data privacy (sensitive information like API Keys is stored locally).
- **Value Investing Oriented**: Focuses on fundamental logic and event-driven analysis, helping investors understand "why it rises" rather than simply chasing trends.

---

## Causal Inference Methodology

This agent follows the reasoning framework of "event → impact chain → beneficiary target → fundamental validation":

1. **Event Identification**: Extracts key events from massive news (policy releases, industry changes, company announcements, macro data, etc.).
2. **Impact Propagation**: Analyzes the propagation effects of events on upstream, midstream, and downstream industries, related sectors, and competitive landscapes.
3. **Target Mapping**: Maps affected segments to specific A-share / Hong Kong / US-listed companies.
4. **Price Expectation**: Combines market sentiment and historical reactions to similar events to assess the likelihood of short-term price increases.
5. **Fundamental Validation**: Calls akshare to obtain valuation metrics and recent quarterly financial data for candidate targets. The LLM comprehensively evaluates the combination of news-driven benefits and fundamental health, dynamically adjusting confidence.
6. **Confidence Assessment**: Combines source reliability, causal strength, fundamental conditions, and market environment to produce the final reasoning confidence.

The entire reasoning process is presented as structured data, with each step being traceable, challengeable, and modifiable.

---

## System Architecture

```
┌─────────────────────────────────────────┐
│              Flet Desktop UI             │
│  (Main page, analysis panel, causal      │
│   chain display, history records)        │
└──────────────────┬──────────────────────┘
                   │ User interaction / mode selection
┌──────────────────▼──────────────────────┐
│           Reasoning Engine (Agent)       │
│  - Fully-automatic / step-by-step mode  │
│    control                              │
│  - Causal inference state machine        │
│    management                           │
│  - Fundamental validation and            │
│    confidence adjustment                │
└──────┬──────────────────┬──────────────┘
       │                  │
┌──────▼──────┐   ┌──────▼──────────────┐
│  Skill Layer │   │  LLM Module         │
│  - Sina      │   │  - Chat Completion  │
│    Finance   │   │  - Structured output│
│  - Tavily    │   │    parsing          │
│  - akshare   │   │  - Prompt template  │
│  (fundamentals)  │    management       │
└──────┬──────┘   │  - Fundamental      │
       │          │    evaluation       │
       │          └─────────────────────┘
┌──────▼─────────────────────────────────┐
│       Local Configuration & Storage     │
│  - API Keys (encrypted storage)         │
│  - Reasoning History (SQLite)           │
└────────────────────────────────────────┘
```

- **UI Layer**: Built with Flet, responsible for user interaction and result display.
- **Reasoning Engine**: The core scheduler that controls the reasoning flow, calls Skills to fetch data, invokes the LLM for analysis, and manages both interaction modes. It automatically triggers fundamental validation after recommendation extraction, dynamically adjusting confidence.
- **Skill Layer**: Extensible plugin tools, divided into news source Skills (inheriting `BaseSkill`, exposing `async fetch_news(query, top_k)`) and fundamental data Skills (inheriting `BaseFundamentalSkill`, exposing `async fetch_fundamental(stock_code)`).
- **LLM Module**: Encapsulates calls to OpenAI / compatible interfaces, guiding the model to output structured reasoning chains and fundamental assessment results through carefully designed prompts.
- **Data Layer**: Local SQLite records historical analyses for easy review.

---

## Technology Stack

| Category | Technology | Description |
|----------|------------|-------------|
| Programming Language | Python 3.10+ | Primary language |
| Desktop Framework | Flet | Flutter-based Python desktop UI framework, supports Windows |
| Async Processing | asyncio | Multi-source concurrent fetching and LLM calls |
| HTTP Client | httpx, aiohttp | Requesting financial APIs and search engines |
| LLM Integration | openai Python SDK | Supports OpenAI, DeepSeek and other compatible interfaces |
| Search Engine | Tavily API | For retrieving real-time news and event background |
| Web Parsing | beautifulsoup4, lxml | Parsing HTML pages from Sina Finance, etc. (when no standard API is available) |
| Fundamental Data | akshare | Retrieving A-share valuation metrics (PE/PB/PS) and financial statements (revenue, gross margin, ROE) |
| Data Storage | aiosqlite | Lightweight async SQLite operations |
| Encrypted Storage | cryptography | Encrypting sensitive information like API Keys |
| Configuration Management | python-dotenv, yaml | Environment variables and configuration files |

---

## Installation and Running

### Requirements

- Windows 10 / 11 (64-bit)
- Python 3.10 or above (virtual environment recommended)
- Stable network connection

### Get the Code

```bash
git clone https://github.com/your-org/dividend-agent.git
cd dividend-agent
```

### Create a Virtual Environment (Recommended)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Example of core dependencies in `requirements.txt`:

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

### Configure API Keys

1. Copy the configuration template:

```bash
cp config.yaml.example config.yaml
```

2. Edit `config.yaml` and fill in the required API Keys:

```yaml
llm:
  provider: "openai"          # Optional: openai / deepseek / qwen
  api_key: "sk-xxxx"         # Your LLM API Key
  model: "gpt-4o"            # Models with strong reasoning capabilities recommended
  base_url: ""               # If using a proxy, fill in the base_url

skills:
  tavily:
    api_key: "tvly-xxxx"     # Tavily Search API Key
    enabled: true
  GroundAPI:
    api_key: "groundapi-xxxx" # GroundAPI API Key
    enabled: true
  akshare:
    enabled: true            # akshare fundamental data retrieval (requires pip install akshare)
    recent_quarters: 4       # Number of recent quarters of financial data to retrieve
  # Additional information sources can be added
```

> Security Reminder: Do not commit `config.yaml` to version control systems. The project includes `.gitignore` by default to ignore this file.

### Requirements
Windows 10 / 11 (64-bit)  
Python 3.10 or above  
Stable network connection  

### Install from PyPI (Recommended)  
```bash
pip install bonus
```
After installation, launch directly from the command line:
```bash
bonus
```

### Install from Source (Developers)
```bash
git clone https://github.com/your-org/Bonus.git
cd Bonus
pip install -e ".[dev]"
```
Launch the application:

```bash
bonus
```
On first launch, the local database and history table will be created automatically.

---

## Project Structure

```
Bonus/                          # Project root directory
├── pyproject.toml              # Project metadata, dependencies, build configuration
├── README.md                   # Project documentation (this file)
├── LICENSE                     # MIT License
├── .gitignore
├── src/
│   └── bonus/                  # Main package (publishable to PyPI)
│       ├── __init__.py
│       ├── __main__.py         # Entry point: invoked via python -m bonus
│       ├── app.py              # Flet application main logic, page routing
│       ├── config.yaml         # Default configuration template (no keys)
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_view.py    # Main interface layout and analysis buttons
│       │   ├── result_view.py  # Reasoning results and causal chain display
│       │   ├── chain_widget.py # Causal chain tree diagram component
│       │   └── confirm_dialog.py # Step-by-step confirmation dialog component
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── engine.py       # Reasoning engine, mode scheduling
│       │   ├── state_machine.py # State machine (step-by-step confirmation mode)
│       │   └── causal_chain.py # Causal chain data structure and construction
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── base.py         # Skill abstract base class (news sources)
│       │   ├── fundamental_base.py # Fundamental data Skill abstract base class
│       │   ├── sina_skill.py   # Sina Finance trending news fetching
│       │   ├── tavily_skill.py # Tavily search
│       │   ├── akshare_skill.py # akshare fundamental data retrieval
│       │   └── registry.py     # Skill registration and loading
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py       # Unified LLM call interface
│       │   ├── prompts.py      # Prompt template management
│       │   └── parser.py       # Structured output parsing
│       ├── models/
│       │   ├── __init__.py
│       │   ├── news.py         # News/event data models
│       │   ├── inference.py    # Reasoning node, causal edge models
│       │   ├── stock.py        # Stock information model
│       │   └── fundamental.py  # Fundamental data models (valuation, financial statements)
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── db.py           # SQLite database initialization and operations
│       │   └── history.py      # Reasoning history CRUD
│       └── utils/
│           ├── __init__.py
│           ├── config.py       # Configuration loading and encryption
│           ├── logger.py       # Logging configuration
│           └── async_utils.py  # Async utilities
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_skills.py
│   ├── test_engine.py
│   └── ...
└── docs/                       # Additional documentation
    ├── skills_guide.md
    └── architecture.md
```

---

## Core Module Design

### 1. Skill Plugin System

The Skill system is divided into two categories: **News Source Skills** (inheriting `BaseSkill`) and **Fundamental Data Skills** (inheriting `BaseFundamentalSkill`), with separated responsibilities and no coupling.

**News Source Skills**:

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
        """Asynchronously fetch news list"""
        ...
```

**Fundamental Data Skills**:

```python
# src/bonus/skills/fundamental_base.py
from abc import ABC, abstractmethod
from bonus.models.fundamental import StockFundamental

class BaseFundamentalSkill(ABC):
    name: str = "fundamental_base"
    description: str = "Fundamental data source"

    @abstractmethod
    async def fetch_fundamental(self, stock_code: str) -> StockFundamental | None:
        """Asynchronously fetch fundamental data for a single stock (valuation, financial statements)"""
        ...
```

**Implemented Skills:**

- **SinaSkill** (news source): Fetches Sina Finance real-time trending topics and watchlist news, parsing HTML to obtain titles, summaries, timestamps, and associated stocks.
- **TavilySkill** (news source): Calls the Tavily Search API with combined queries such as "A-shares latest policy industry impact" to return structured news.
- **AkShareSkill** (fundamentals): Retrieves A-share valuation metrics (PE-TTM / PB / PS-TTM / total market cap) and recent quarterly financial data (revenue and YoY growth, net profit and YoY growth, gross margin, net margin, ROE) via akshare. Since akshare is a synchronous library, it is executed in a thread pool via `asyncio.to_thread` internally to avoid blocking the event loop.

Skill registration and management:

```python
# src/bonus/skills/registry.py
from src.skills.sina_skill import SinaSkill
from src.skills.tavily_skill import TavilySkill
from src.skills.akshare_skill import AkShareSkill

def load_skills(config) -> dict:
    """Load news source Skills"""
    skills = {}
    if config['skills']['sina']['enabled']:
        skills['sina'] = SinaSkill()
    if config['skills']['tavily']['api_key']:
        skills['tavily'] = TavilySkill(api_key=config['skills']['tavily']['api_key'])
    return skills

def load_fundamental_skills(config) -> dict:
    """Load fundamental data Skills"""
    skills = {}
    if config['skills']['akshare']['enabled']:
        skills['akshare'] = AkShareSkill(recent_quarters=config['skills']['akshare']['recent_quarters'])
    return skills
```

### 2. Reasoning Engine and Two Modes

The `CausalEngine` is responsible for the entire analysis flow, adding a fundamental validation step after recommendation extraction:

```python
# src/bonus/agent/engine.py
class CausalEngine:
    def __init__(self, skills: dict, llm_client, mode: str = "auto",
                 fundamental_skills: dict | None = None):
        self.skills = skills
        self.llm = llm_client
        self.mode = mode  # "auto" or "stepwise"
        self.fundamental_skills = fundamental_skills or {}

    async def run(self, query: str = "today's hot topics", callback=None):
        # 1. Concurrently fetch from all Skills
        news_list = await self._gather_news(query)

        # 2. LLM generates causal inference chain (initial)
        chain = await self._initial_causal_chain(news_list)

        if self.mode == "auto":
            # Fully-automatic: directly deep-dive to final recommendations
            final_chain = await self._deep_inference(chain)
        else:
            # Step-by-step confirmation: interact with UI via callback
            final_chain = await self._stepwise_inference(chain, callback)

        # 3. Extract stock recommendations
        recommendations = ChainBuilder.extract_recommendations(final_chain)

        # 4. Fundamental validation (if akshare or other Skills are enabled)
        if recommendations and self.fundamental_skills:
            recommendations = await self._enhance_with_fundamentals(recommendations)

        return final_chain, recommendations
```

**Fundamental Validation Flow** (`_enhance_with_fundamentals`):
1. Collects all recommended stock codes and batch-calls `AkShareSkill.fetch_fundamentals` to obtain valuation and financial data.
2. For each stock, calls the LLM to comprehensively evaluate the "news-driven recommendation rationale + original confidence + fundamental data".
3. The LLM outputs a fundamental score, analysis summary, and adjusted confidence, which are written back to `StockRecommendation`.
4. Finally, re-sorts the recommendation list by adjusted confidence.

In **step-by-step confirmation mode**, each time the engine produces an intermediate conclusion node (e.g., "policy benefits new energy vehicles"), it pauses and calls the UI callback to display it to the user. After the user confirms or modifies it, the engine continues reasoning based on the confirmed content. This requires implementing a state machine on the UI side to manage the node currently awaiting confirmation.

### 3. Causal Chain Data Structure

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
    content: str           # Natural language description
    confidence: float      # 0.0 ~ 1.0
    sources: List[str]     # Referenced news IDs
    stocks: List[str] = [] # If a company node, contains stock codes

class CausalEdge(BaseModel):
    from_node: str
    to_node: str
    relation: str          # e.g., "bullish", "cost reduction", "intensified competition"
```

The complete chain is `List[CausalNode]` + `List[CausalEdge]`, which the frontend uses to render the graph.

Fundamental data model (`models/fundamental.py`):

```python
class StockFundamental(BaseModel):
    code: str
    name: str
    industry: str
    pe_ttm: float | None       # Trailing P/E ratio
    pb: float | None           # Price-to-book ratio
    ps_ttm: float | None       # Price-to-sales ratio
    total_market_cap: float | None  # Total market capitalization
    financials: list[FinancialQuarter]  # Recent quarterly financial data
    fundamental_score: float | None     # LLM fundamental score
    fundamental_summary: str            # Fundamental analysis summary
```

### 4. LLM Calls and Prompt Design

`llm/client.py` encapsulates the OpenAI-compatible API, supporting Function Calling to force structured causal chain output.

Key prompt templates (located in `prompts.py`):

- `CausalChainPrompt`: Asks the model to generate a causal graph of event → industry → company based on a set of news, outputting nodes and edges in JSON format.
- `DeepInferencePrompt`: In fully-automatic mode, lets the model expand based on existing nodes to find more beneficiary targets.
- `ConfirmationPrompt`: Displays the current node to the user and asks whether they agree or require supplementary information.
- `FundamentalAnalysisPrompt`: Combines the news-driven recommendation rationale with akshare fundamental data for the LLM to comprehensively assess the likelihood of a near-term stock price increase, outputting a fundamental score, analysis summary, and adjusted confidence.

The model output parser `parser.py` converts JSON into `CausalNode` / `CausalEdge` / `FundamentalAssessment` objects and performs validation.

### 5. Flet Frontend Interface

The main interface uses Flet components such as `ft.Column`, `ft.Row`, and `ft.Tabs`:

- **Analysis Panel**: Contains a query input box (default "today's hot topics"), a mode selection switch (auto / step-by-step), and a start analysis button.
- **Progress Display**: Shows the current status during analysis ("Fetching Sina Finance...", "Reasoning step 3...").
- **Causal Chain View**: Uses `ft.Treeview` or custom drawing components to display nodes and connections; clicking a node shows details.
- **Stock Recommendation List**: Bottom cards list recommended stocks, including name, code, upside logic, and confidence.

Step-by-step confirmation dialog:

```python
# src/bonus/ui/confirm_dialog.py
def show_confirmation(page, node: CausalNode, on_confirm, on_reject):
    def confirm_click(e):
        on_confirm(node)
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        title=ft.Text("Please Confirm Reasoning Step"),
        content=ft.Text(node.content),
        actions=[
            ft.TextButton("Confirm", on_click=confirm_click),
            ft.TextButton("Modify", on_click=...),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()
```

---

## Example Workflow

### Fully-automatic Mode

1. Open the "Bonus" application; the analysis panel is displayed by default.
2. Keep "today's hot topics" in the input box and select "Fully-automatic Analysis" mode.
3. Click "Start Analysis".
4. The interface shows progress: Fetching Sina Finance... Fetching Tavily... 12 news items completed.
5. The LLM begins reasoning; the status bar shows "Generating causal chain... discovering potential targets...";
6. After reasoning completes, it automatically enters the fundamental validation phase: the status bar shows "Fetching fundamental data via akshare... Evaluating China Merchants Bank fundamentals...".
7. After approximately 15-40 seconds, the final results are displayed:
   - Causal chain tree diagram (e.g., PBOC RRR cut → Bank liquidity easing → China Merchants Bank, Industrial Bank benefit → Stock prices expected to rise)
   - Recommended stock card list, each card showing: news-driven upside logic, fundamental data (PE/PB/Market Cap, recent quarterly financial table), fundamental analysis summary, and adjusted confidence.
8. Users can click any node to view detailed news sources.

### Step-by-step Confirmation Mode

1. Select "Step-by-step Confirmation Analysis" mode and click start.
2. After the system fetches news, the first reasoning node pops up: "Today the PBOC announced a 0.5 percentage point RRR cut, releasing approximately 1 trillion yuan in long-term funds", with confidence 0.97 and attached news links. The user clicks "Confirm".
3. The system continues reasoning and pops up the second node: "This event will increase banks' available funds, reduce liability costs, and benefit the banking sector". The user finds it reasonable and clicks "Confirm".
4. The system pops up the third node: "Beneficiary banks include China Merchants Bank (superior asset quality) and Bank of Ningbo (high elasticity in micro and small business)". The user can click "Modify" to add or remove stocks, then confirm.
5. The complete causal chain and recommended stocks are presented.
6. If the user selects "Reject" at any step, the system backtracks and attempts alternative reasoning paths.

---

## Development and Extension

### Adding a New News Source Skill

1. Create a new file under `src/bonus/skills/`, inherit `BaseSkill`, and implement the `fetch_news` method.
2. Add the corresponding configuration item in `config.yaml`.
3. Register the Skill in `load_skills` in `registry.py`.

```python
class EastMoneySkill(BaseSkill):
    name = "eastmoney"
    async def fetch_news(self, query, top_k=10):
        # Implement East Money trending news fetching
        ...
```

### Adding a New Fundamental Data Skill

1. Create a new file under `src/bonus/skills/`, inherit `BaseFundamentalSkill`, and implement the `fetch_fundamental` method.
2. Add the corresponding configuration item in `config.yaml`.
3. Register the Skill in `load_fundamental_skills` in `registry.py`.

```python
class TushareSkill(BaseFundamentalSkill):
    name = "tushare"
    async def fetch_fundamental(self, stock_code: str) -> StockFundamental | None:
        # Implement fundamental data retrieval via Tushare
        ...
```

### Changing the LLM Provider

Modify `llm.provider` and `model` in `config.yaml`, and adapt to different API differences in `llm/client.py`. Currently supports OpenAI, DeepSeek (using OpenAI-compatible interface), and Alibaba Tongyi Qianwen out of the box.

### Local Model Support

For fully local inference, tools like Ollama can be used by pointing `base_url` to the local service and setting `model` to the local model name. Note that local models need strong instruction-following and JSON output capabilities.

---

## Roadmap

- [x] Basic framework and dual-mode reasoning
- [x] GroundAPI and Tavily integration
- [x] akshare fundamental data validation (valuation, financial statements, LLM comprehensive evaluation)
- [ ] More information sources (East Money, Xueqiu, Cailian Press)
- [ ] Historical reasoning record query and comparison
- [ ] Causal chain graphical display optimization (D3.js style)
- [ ] User-defined reasoning rules
- [ ] Integrate stock price data, backtest reasoning accuracy
- [ ] Package as Windows installer (using PyInstaller + Flet packaging)

---

## FAQ

**Q: What if the analysis results are inaccurate?**
A: Causal inference depends on LLM capability and news quality. You can try: 1) Switch to a stronger model (e.g., gpt-4o, claude-3.5-sonnet); 2) Manually correct the reasoning path in step-by-step confirmation mode; 3) Expand more high-quality information sources; 4) Enable akshare fundamental validation to make confidence more reliable based on financial data.

**Q: What is the purpose of akshare fundamental validation?**
A: News-driven benefits only reflect "expectations", while fundamental data reflects "strength". Metrics such as PE/PB/revenue/gross margin/ROE obtained via akshare allow the LLM to judge whether candidate targets truly have fundamental support for price increases. For example, if a stock benefits from favorable policies but has excessively high valuation or declining revenue, the system will lower its confidence, avoiding the risk of "chasing news without considering quality".

**Q: How do I protect my API Key?**
A: All keys are stored in the local `config.yaml`. During application runtime, they are only decrypted in memory and never uploaded to any remote server. It is recommended to use Windows file permissions to restrict access.

**Q: Can it run on macOS or Linux?**
A: Flet itself is cross-platform, but this application was developed targeting Windows. Running on macOS/Linux may require minor adjustments to paths and dependencies, but it should theoretically work.

---

## Contributing

Issues and Pull Requests are welcome. Please follow these guidelines:

1. Fork this repository and create a feature branch.
2. Write test cases for new Skills or features.
3. Ensure the code passes `flake8` and `pytest`.
4. Update relevant documentation.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

> Disclaimer: This application is only an auxiliary investment research tool and does not constitute any investment advice. The stock market involves risks; please make decisions carefully. Users bear their own investment gains and losses.

---

*Bonus — Let every decision have a traceable cause.*
