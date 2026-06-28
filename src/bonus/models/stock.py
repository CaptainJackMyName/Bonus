"""股票信息模型"""

from typing import List, Optional

from pydantic import BaseModel, Field

from bonus.models.fundamental import StockFundamental


class Stock(BaseModel):
    """股票基础信息"""

    code: str = Field(..., description="股票代码")
    name: str = Field(default="", description="股票名称")
    market: str = Field(default="A股", description="市场（A股/港股/美股）")
    industry: str = Field(default="", description="所属行业")


class StockRecommendation(BaseModel):
    """股票推荐结果"""

    stock: Stock = Field(..., description="股票信息")
    reason: str = Field(default="", description="上涨逻辑")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度")
    cause_chain: List[str] = Field(default_factory=list, description="因果推理路径描述")
    related_news_ids: List[str] = Field(default_factory=list, description="相关新闻 ID")
    node_id: Optional[str] = Field(default=None, description="对应的因果链节点 ID")
    fundamental: Optional[StockFundamental] = Field(
        default=None, description="基本面数据（由 akshare 等 Skill 获取）"
    )
    original_confidence: Optional[float] = Field(
        default=None, description="结合基本面调整前的原始置信度"
    )

    @property
    def confidence_label(self) -> str:
        """置信度文字标签"""
        if self.confidence >= 0.8:
            return "高"
        elif self.confidence >= 0.6:
            return "中"
        elif self.confidence >= 0.4:
            return "低"
        else:
            return "很低"

    def to_display(self) -> str:
        """格式化为展示文本"""
        return (
            f"{self.stock.name}({self.stock.code}) "
            f"[{self.stock.market}] "
            f"置信度:{self.confidence_label}({self.confidence:.0%}) "
            f"- {self.reason}"
        )
