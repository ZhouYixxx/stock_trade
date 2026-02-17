"""
股票筛选模块
"""
from typing import List
import pandas as pd

from ..data.market_data import StockInfo


def screen_by_ma_distance(
    symbol: str,
    data: pd.DataFrame,
    ma_period: int,
    threshold: float,
    direction: str = "below"
) -> bool:
    """根据移动平均线距离筛选"""
    pass


def screen_by_bollinger_breakout(
    data: pd.DataFrame,
    config
) -> bool:
    """根据布林带突破筛选"""
    pass


def screen_by_market_cap(
    market_cap: float,
    threshold: float,
    category: str = "large_cap"
) -> bool:
    """根据市值筛选"""
    pass


def screen_by_index_constituent(
    symbol: str,
    index: str = "SP500"
) -> bool:
    """根据指数成分股筛选"""
    pass


def screen_composite(
    symbol: str,
    data: pd.DataFrame,
    stock_info: StockInfo,
    config
) -> bool:
    """综合筛选"""
    pass


def classify_market_cap(market_cap: float) -> str:
    """分类市值：large_cap / mid_cap / small_cap"""
    pass


def get_index_constituents(index: str) -> List[str]:
    """获取指数成分股列表"""
    pass
