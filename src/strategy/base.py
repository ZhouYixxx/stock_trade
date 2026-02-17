"""
策略基类
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from ..types.common import TradingSignal, Position, Order


class BaseStrategy(ABC):
    """策略基类"""

    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """分析股票，生成信号"""
        pass

    @abstractmethod
    def should_buy(self, signal: TradingSignal) -> bool:
        """判断是否应该买入"""
        pass

    @abstractmethod
    def should_sell(self, position: Position, data: pd.DataFrame) -> bool:
        """判断是否应该卖出"""
        pass

    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """计算仓位大小"""
        pass


class BollingerStrategy(BaseStrategy):
    """布林带策略实现"""

    def __init__(self, config):
        self.config = config

    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """分析股票，生成信号"""
        pass

    def should_buy(self, signal: TradingSignal) -> bool:
        """判断是否应该买入"""
        pass

    def should_sell(self, position: Position, data: pd.DataFrame) -> bool:
        """判断是否应该卖出"""
        pass

    def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """计算仓位大小"""
        pass


class MeanReversionStrategy(BaseStrategy):
    """均值回归策略实现"""

    def __init__(self, config):
        self.config = config

    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """分析股票，生成信号"""
        pass

    def should_buy(self, signal: TradingSignal) -> bool:
        """判断是否应该买入"""
        pass

    def should_sell(self, position: Position, data: pd.DataFrame) -> bool:
        """判断是否应该卖出"""
        pass

    def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """计算仓位大小"""
        pass
