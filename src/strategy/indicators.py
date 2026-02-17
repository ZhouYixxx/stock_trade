"""
技术指标计算模块
"""
import pandas as pd
from typing import NamedTuple


class BollingerBands(NamedTuple):
    """布林带数据"""
    upper: pd.Series
    middle: pd.Series
    lower: pd.Series


class MACD(NamedTuple):
    """MACD数据"""
    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series


def calculate_sma(
    data: pd.Series,
    period: int
) -> pd.Series:
    """计算简单移动平均线"""
    pass


def calculate_ema(
    data: pd.Series,
    period: int
) -> pd.Series:
    """计算指数移动平均线"""
    pass


def calculate_bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> BollingerBands:
    """计算布林带"""
    pass


def calculate_rsi(
    data: pd.Series,
    period: int = 14
) -> pd.Series:
    """计算RSI指标"""
    pass


def calculate_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> MACD:
    """计算MACD指标"""
    pass


def is_bullish_engulfing(
    prev_candle: pd.Series,
    curr_candle: pd.Series
) -> bool:
    """判断是否为阳包阴形态"""
    pass


def is_break_high(
    prev_candle: pd.Series,
    curr_candle: pd.Series
) -> bool:
    """判断是否突破前一日高点"""
    pass
