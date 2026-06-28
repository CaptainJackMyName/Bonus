# Skill 插件开发指南

## 概述

红利采用可插拔的 Skill 架构，每个信息源封装为独立 Skill。所有 Skill 继承自 `BaseSkill`，对外提供统一的 `fetch_news` 接口。

## BaseSkill 接口

```python
from bonus.skills.base import BaseSkill
from bonus.models.news import NewsItem

class MySkill(BaseSkill):
    name = "myskill"
    description = "我的信息源"

    async def fetch_news(self, query: str, top_k: int = 10) -> list[NewsItem]:
        ...
```

## 开发新 Skill 步骤

### 1. 创建 Skill 文件

在 `src/bonus/skills/` 下新建文件，如 `eastmoney_skill.py`：

```python
import hashlib
import httpx
from bonus.models.news import NewsItem
from bonus.skills.base import BaseSkill

class EastMoneySkill(BaseSkill):
    name = "eastmoney"
    description = "东方财富热点新闻"

    async def fetch_news(self, query: str, top_k: int = 10) -> list[NewsItem]:
        items = []
        headers = {"User-Agent": "Mozilla/5.0 ..."}
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            resp = await client.get("https://finance.eastmoney.com/...")
            # 解析响应，构建 NewsItem 列表
        return items[:top_k]

    @staticmethod
    def _gen_id(title: str, url: str) -> str:
        raw = f"eastmoney_{title}_{url}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]
```

### 2. 添加配置项

在 `config.yaml` 中添加：

```yaml
skills:
  eastmoney:
    enabled: true
    top_k: 10
    api_key: ""
```

### 3. 注册 Skill

在 `src/bonus/skills/registry.py` 的 `load_skills` 函数中添加注册逻辑。

### 4. 导出 Skill

在 `src/bonus/skills/__init__.py` 中添加导出。

## 最佳实践

1. **设置超时**: HTTP 请求设置合理超时（15-30 秒）
2. **User-Agent**: 添加合理的 User-Agent 头
3. **去重**: 使用内容哈希生成唯一 ID
4. **错误处理**: BaseSkill 的 safe_fetch 已自动捕获异常
5. **测试**: 为每个 Skill 编写单元测试
