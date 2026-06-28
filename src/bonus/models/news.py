"""新闻 / 事件数据模型"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """新闻条目数据模型"""

    id: str = Field(..., description="新闻唯一标识")
    title: str = Field(..., description="新闻标题")
    summary: str = Field(default="", description="新闻摘要")
    content: str = Field(default="", description="新闻正文内容")
    source: str = Field(default="", description="信息来源（如 sina, tavily）")
    url: str = Field(default="", description="新闻链接")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    related_stocks: List[str] = Field(default_factory=list, description="关联股票代码列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    def brief(self, max_length: int = 200) -> str:
        """返回新闻简要描述"""
        text = self.summary or self.content or ""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def to_display(self) -> str:
        """格式化为展示文本"""
        time_str = self.published_at.strftime("%Y-%m-%d %H:%M") if self.published_at else "未知时间"
        stocks_str = f" [{', '.join(self.related_stocks)}]" if self.related_stocks else ""
        return f"【{self.source}】{self.title}{stocks_str} ({time_str})"
