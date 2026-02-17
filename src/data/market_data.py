"""
市场数据获取模块
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict


class OHLCData(TypedDict):
    """OHLC数据结构"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: str


class StockInfo(TypedDict):
    """股票信息结构"""
    symbol: str
    name: str
    market_cap: float
    sector: str
    industry: str


def fetch_stock_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:
    """获取单只股票历史数据"""
    pass


def fetch_stock_data_batch(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    """批量获取股票历史数据"""
    pass


def fetch_ohlc_batch(
    symbols: List[str]
) -> Dict[str, OHLCData]:
    """批量获取最新OHLC数据"""
    pass


def fetch_market_cap(symbol: str) -> float:
    """获取股票市值"""
    pass


def fetch_stock_info(symbol: str) -> StockInfo:
    """获取股票基本信息"""
    pass


def get_trading_dates(
    start_date: datetime,
    end_date: datetime
) -> List[datetime]:
    """获取交易日期列表"""
    pass


def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日"""
    pass
