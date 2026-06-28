"""AkShare 基本面数据 Skill

通过 akshare 获取 A 股股票的基本面数据，包括：
- 估值指标：市盈率(PE-TTM)、市净率(PB)、市销率(PS-TTM)、总市值
- 财务数据：近几个季度的营收、净利润、毛利率、净利率、ROE

akshare 为同步库，通过 asyncio.to_thread 在线程池中执行以避免阻塞事件循环。
"""

import asyncio
from typing import List, Optional

from bonus.models.fundamental import FinancialQuarter, StockFundamental
from bonus.skills.fundamental_base import BaseFundamentalSkill
from bonus.utils.logger import get_logger

logger = get_logger(__name__)


class AkShareSkill(BaseFundamentalSkill):
    """基于 akshare 的 A 股基本面数据获取"""

    name = "akshare"
    description = "akshare A股基本面数据（估值、财务报表）"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._recent_quarters: int = kwargs.get("recent_quarters", 4)
        self._ak = None
        self._init_akshare()

    def _init_akshare(self) -> None:
        """延迟导入并初始化 akshare"""
        try:
            import akshare as ak
            self._ak = ak
            logger.info("akshare 已加载")
        except ImportError:
            logger.error(
                "未安装 akshare，请执行 pip install akshare。"
                "AkShareSkill 将不可用。"
            )
            self._ak = None

    async def fetch_fundamental(self, stock_code: str) -> Optional[StockFundamental]:
        """获取单只股票的基本面数据"""
        if not self._ak:
            logger.warning("akshare 未加载，无法获取基本面数据")
            return None

        # 清理股票代码（去除可能的前缀）
        code = stock_code.strip()
        # akshare 多数接口需要纯 6 位代码
        if len(code) > 6:
            code = code[-6:]

        logger.info(f"akshare 获取 {code} 基本面数据...")

        try:
            # 并发获取各类数据（每个都在线程池中执行）
            info_task = asyncio.to_thread(self._fetch_stock_info, code)
            valuation_task = asyncio.to_thread(self._fetch_valuation, code)
            financials_task = asyncio.to_thread(
                self._fetch_financials, code, self._recent_quarters
            )

            info, valuation, financials = await asyncio.gather(
                info_task, valuation_task, financials_task,
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"akshare 获取 {code} 数据失败: {e}")
            return None

        # 处理异常结果
        if isinstance(info, Exception):
            logger.warning(f"获取 {code} 个股信息失败: {info}")
            info = {}
        if isinstance(valuation, Exception):
            logger.warning(f"获取 {code} 估值数据失败: {valuation}")
            valuation = {}
        if isinstance(financials, Exception):
            logger.warning(f"获取 {code} 财务数据失败: {financials}")
            financials = []

        # 合并信息
        name = info.get("name", "")
        industry = info.get("industry", "")

        return StockFundamental(
            code=code,
            name=name,
            industry=industry,
            pe_ttm=valuation.get("pe_ttm"),
            pb=valuation.get("pb"),
            ps_ttm=valuation.get("ps_ttm"),
            total_market_cap=valuation.get("total_market_cap"),
            financials=financials,
        )

    # ------------------------------------------------------------------
    # 以下为同步方法，通过 asyncio.to_thread 在线程池中调用
    # ------------------------------------------------------------------

    def _fetch_stock_info(self, code: str) -> dict:
        """获取个股基本信息（名称、行业）"""
        result = {}
        try:
            # akshare 个股信息接口
            df = self._ak.stock_individual_info_em(symbol=code)
            if df is not None and not df.empty:
                # df 为两列: item / value
                data = dict(zip(df["item"], df["value"]))
                result["name"] = str(data.get("股票简称", ""))
                result["industry"] = str(data.get("行业", ""))
                # 总市值
                market_cap_str = data.get("总市值", "")
                if market_cap_str:
                    try:
                        result["total_market_cap"] = float(market_cap_str)
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            logger.debug(f"stock_individual_info_em({code}) 失败: {e}")
        return result

    def _fetch_valuation(self, code: str) -> dict:
        """获取估值指标（PE/PB/PS）"""
        result = {}
        try:
            # akshare 实时行情接口（东方财富）
            df = self._ak.stock_individual_info_em(symbol=code)
            if df is not None and not df.empty:
                data = dict(zip(df["item"], df["value"]))
                # 市盈率等可能在其他接口
        except Exception as e:
            logger.debug(f"估值获取({code}) 失败: {e}")

        # 尝试通过 A 股实时行情获取估值
        try:
            df = self._ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                row = df[df["代码"] == code]
                if not row.empty:
                    r = row.iloc[0]
                    pe = r.get("市盈率-动态")
                    if pe is not None and str(pe) not in ("-", "", "nan"):
                        try:
                            result["pe_ttm"] = float(pe)
                        except (ValueError, TypeError):
                            pass
                    pb = r.get("市净率")
                    if pb is not None and str(pb) not in ("-", "", "nan"):
                        try:
                            result["pb"] = float(pb)
                        except (ValueError, TypeError):
                            pass
                    ps = r.get("市销率-动态") or r.get("PS")
                    if ps is not None and str(ps) not in ("-", "", "nan"):
                        try:
                            result["ps_ttm"] = float(ps)
                        except (ValueError, TypeError):
                            pass
                    cap = r.get("总市值")
                    if cap is not None and str(cap) not in ("-", "", "nan"):
                        try:
                            result["total_market_cap"] = float(cap)
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.debug(f"stock_zh_a_spot_em 估值获取({code}) 失败: {e}")

        return result

    def _fetch_financials(self, code: str, recent_quarters: int) -> List[FinancialQuarter]:
        """获取近几个季度的财务数据"""
        quarters: List[FinancialQuarter] = []

        try:
            # akshare 财务摘要接口
            df = self._ak.stock_financial_abstract(symbol=code)
            if df is None or df.empty:
                return quarters

            # 财务摘要的列名为各类指标，行为报告期
            # 转置以便按报告期遍历
            for _, row in df.iterrows():
                report_date = str(row.get("报告期", "")) or str(row.get("选项", ""))
                if not report_date:
                    continue

                def _safe_float(val) -> Optional[float]:
                    if val is None:
                        return None
                    s = str(val).strip()
                    if s in ("", "-", "nan", "None"):
                        return None
                    try:
                        return float(s)
                    except (ValueError, TypeError):
                        return None

                quarter = FinancialQuarter(
                    report_date=report_date,
                    revenue=_safe_float(row.get("营业收入")),
                    revenue_yoy=_safe_float(row.get("营业收入同比增长率")),
                    net_profit=_safe_float(row.get("净利润")),
                    net_profit_yoy=_safe_float(row.get("净利润同比增长率")),
                    gross_margin=_safe_float(row.get("销售毛利率")),
                    net_margin=_safe_float(row.get("销售净利率")),
                    roe=_safe_float(row.get("净资产收益率")),
                )
                quarters.append(quarter)

                if len(quarters) >= recent_quarters:
                    break

        except Exception as e:
            logger.debug(f"stock_financial_abstract({code}) 失败: {e}")

        # 备用方案：尝试财务分析指标接口
        if not quarters:
            try:
                df = self._ak.stock_financial_analysis_indicator(symbol=code, start_year="2023")
                if df is not None and not df.empty:
                    # 取最近几行
                    df_recent = df.head(recent_quarters)
                    for _, row in df_recent.iterrows():
                        report_date = str(row.get("日期", ""))
                        if not report_date:
                            continue

                        def _sf(val) -> Optional[float]:
                            if val is None:
                                return None
                            s = str(val).strip()
                            if s in ("", "-", "nan", "None"):
                                return None
                            try:
                                return float(s)
                            except (ValueError, TypeError):
                                return None

                        quarter = FinancialQuarter(
                            report_date=report_date,
                            gross_margin=_sf(row.get("销售毛利率(%)")),
                            net_margin=_sf(row.get("销售净利率(%)")),
                            roe=_sf(row.get("加权净资产收益率(%)")),
                        )
                        quarters.append(quarter)
            except Exception as e:
                logger.debug(f"stock_financial_analysis_indicator({code}) 失败: {e}")

        return quarters
