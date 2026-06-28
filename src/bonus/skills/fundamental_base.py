"""基本面数据 Skill 抽象基类

与 BaseSkill（新闻获取）不同，FundamentalSkill 用于获取股票基本面数据，
如市盈率、营收、毛利率等，在因果推断推荐股票后进行基本面验证。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from bonus.models.fundamental import StockFundamental
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class BaseFundamentalSkill(ABC):
    """基本面数据 Skill 抽象基类"""

    name: str = "fundamental_base"
    description: str = "基本面数据源"

    def __init__(self, **kwargs):
        self.config = kwargs
        self.enabled: bool = kwargs.get("enabled", True)

    @abstractmethod
    async def fetch_fundamental(self, stock_code: str) -> Optional[StockFundamental]:
        """
        异步获取单只股票的基本面数据。

        Args:
            stock_code: 股票代码（如 600036）

        Returns:
            基本面数据对象，获取失败返回 None
        """
        ...

    async def fetch_fundamentals(
        self, stock_codes: List[str]
    ) -> List[StockFundamental]:
        """
        批量获取多只股票的基本面数据。

        Args:
            stock_codes: 股票代码列表

        Returns:
            成功获取的基本面数据列表（失败的会被跳过）
        """
        results: List[StockFundamental] = []
        for code in stock_codes:
            data = await self.safe_fetch_fundamental(code)
            if data:
                results.append(data)
        return results

    async def safe_fetch_fundamental(
        self, stock_code: str
    ) -> Optional[StockFundamental]:
        """安全的基本面获取包装，捕获异常返回 None"""
        if not self.enabled:
            logger.info(f"基本面 Skill '{self.name}' 已禁用，跳过 {stock_code}")
            return None
        try:
            logger.info(
                f"基本面 Skill '{self.name}' 开始获取 {stock_code} 基本面数据..."
            )
            result = await self.fetch_fundamental(stock_code)
            if result:
                logger.info(
                    f"基本面 Skill '{self.name}' 成功获取 {stock_code} 基本面数据"
                )
            else:
                logger.warning(
                    f"基本面 Skill '{self.name}' 未获取到 {stock_code} 基本面数据"
                )
            return result
        except Exception as e:
            logger.error(
                f"基本面 Skill '{self.name}' 获取 {stock_code} 基本面失败: {e}",
                exc_info=True,
            )
            return None

    def __repr__(self) -> str:
        return f"<FundamentalSkill {self.name} enabled={self.enabled}>"
