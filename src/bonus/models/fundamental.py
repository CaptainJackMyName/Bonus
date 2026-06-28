"""股票基本面数据模型"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FinancialQuarter(BaseModel):
    """单季度财务数据"""

    report_date: str = Field(default="", description="报告期，如 2024-09-30")
    revenue: Optional[float] = Field(default=None, description="营业收入（元）")
    revenue_yoy: Optional[float] = Field(default=None, description="营收同比增长率")
    net_profit: Optional[float] = Field(default=None, description="净利润（元）")
    net_profit_yoy: Optional[float] = Field(default=None, description="净利润同比增长率")
    gross_margin: Optional[float] = Field(default=None, description="毛利率（%）")
    net_margin: Optional[float] = Field(default=None, description="净利率（%）")
    roe: Optional[float] = Field(default=None, description="净资产收益率 ROE（%）")


class StockFundamental(BaseModel):
    """股票基本面数据汇总"""

    code: str = Field(..., description="股票代码")
    name: str = Field(default="", description="股票名称")
    industry: str = Field(default="", description="所属行业")

    # 估值指标
    pe_ttm: Optional[float] = Field(default=None, description="滚动市盈率 PE-TTM")
    pb: Optional[float] = Field(default=None, description="市净率 PB")
    ps_ttm: Optional[float] = Field(default=None, description="市销率 PS-TTM")
    total_market_cap: Optional[float] = Field(default=None, description="总市值（元）")

    # 近几个季度财务数据
    financials: List[FinancialQuarter] = Field(
        default_factory=list, description="近几个季度财务数据"
    )

    # 基本面评分与摘要（由 LLM 生成）
    fundamental_score: Optional[float] = Field(
        default=None, description="基本面评分 0.0~1.0（越高越好）"
    )
    fundamental_summary: str = Field(
        default="", description="基本面分析摘要（自然语言）"
    )

    def to_context_text(self) -> str:
        """转换为 LLM 可读的上下文文本"""
        lines = [f"股票: {self.name}({self.code}) 行业: {self.industry or '未知'}"]

        # 估值指标
        valuation_parts = []
        if self.pe_ttm is not None:
            valuation_parts.append(f"PE(TTM)={self.pe_ttm:.2f}")
        if self.pb is not None:
            valuation_parts.append(f"PB={self.pb:.2f}")
        if self.ps_ttm is not None:
            valuation_parts.append(f"PS(TTM)={self.ps_ttm:.2f}")
        if self.total_market_cap is not None:
            cap_yi = self.total_market_cap / 1e8
            valuation_parts.append(f"总市值={cap_yi:.2f}亿")
        if valuation_parts:
            lines.append(f"  估值: {', '.join(valuation_parts)}")

        # 财务数据
        if self.financials:
            lines.append("  近期财务数据:")
            for q in self.financials:
                q_parts = [f"报告期={q.report_date}"]
                if q.revenue is not None:
                    rev_yi = q.revenue / 1e8
                    q_parts.append(f"营收={rev_yi:.2f}亿")
                if q.revenue_yoy is not None:
                    q_parts.append(f"营收同比={q.revenue_yoy:.2f}%")
                if q.net_profit is not None:
                    profit_yi = q.net_profit / 1e8
                    q_parts.append(f"净利润={profit_yi:.2f}亿")
                if q.net_profit_yoy is not None:
                    q_parts.append(f"净利同比={q.net_profit_yoy:.2f}%")
                if q.gross_margin is not None:
                    q_parts.append(f"毛利率={q.gross_margin:.2f}%")
                if q.net_margin is not None:
                    q_parts.append(f"净利率={q.net_margin:.2f}%")
                if q.roe is not None:
                    q_parts.append(f"ROE={q.roe:.2f}%")
                lines.append(f"    {', '.join(q_parts)}")

        return "\n".join(lines)


class FundamentalAssessment(BaseModel):
    """LLM 基本面评估结果"""

    stock_code: str = Field(..., description="股票代码")
    fundamental_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="基本面评分"
    )
    fundamental_summary: str = Field(default="", description="基本面分析摘要")
    adjusted_confidence: Optional[float] = Field(
        default=None, description="结合基本面调整后的置信度"
    )
