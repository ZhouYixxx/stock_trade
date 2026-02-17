"""
通知基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

from ..types.common import TradingSignal, Order


class BaseNotifier(ABC):
    """通知基类"""

    @abstractmethod
    def send(self, message: str) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    def send_signal(self, signal: TradingSignal) -> bool:
        """发送交易信号"""
        pass

    @abstractmethod
    def send_order(self, order: Order) -> bool:
        """发送订单通知"""
        pass

    @abstractmethod
    def send_alert(self, level: str, message: str) -> bool:
        """发送告警消息"""
        pass
