"""
飞书通知模块
"""
from typing import Dict, Any
import aiohttp

from .base import BaseNotifier
from ..types.common import TradingSignal, Order


class FeishuNotifier(BaseNotifier):
    """飞书通知实现"""

    def __init__(self, webhook_url: str):
        """初始化"""
        self.webhook_url = webhook_url

    def send(self, message: str) -> bool:
        """发送文本消息"""
        pass

    def send_signal(self, signal: TradingSignal) -> bool:
        """发送交易信号"""
        pass

    def send_order(self, order: Order) -> bool:
        """发送订单通知"""
        pass

    def send_alert(self, level: str, message: str) -> bool:
        """发送告警消息"""
        pass

    def send_card(self, card: Dict[str, Any]) -> bool:
        """发送卡片消息"""
        pass


def send_feishu_message(webhook_url: str, content: str) -> bool:
    """发送飞书消息（底层函数）"""
    pass


def build_signal_card(signal: TradingSignal) -> Dict[str, Any]:
    """构建信号卡片"""
    pass


def build_order_card(order: Order) -> Dict[str, Any]:
    """构建订单卡片"""
    pass


def build_alert_card(level: str, message: str) -> Dict[str, Any]:
    """构建告警卡片"""
    pass
