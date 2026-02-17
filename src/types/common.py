"""
通用类型定义
"""
from datetime import datetime
from typing import Optional, TypedDict, Literal, Dict, Any

# 策略相关
SignalType = Literal["bollinger_breakout", "yang_bao_yin", "break_high"]
OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market", "stop_limit"]
OrderStatus = Literal["pending", "filled", "cancelled", "rejected"]
PositionStatus = Literal["open", "closed"]
MarketCapCategory = Literal["large_cap", "mid_cap", "small_cap"]

# 数据结构
class OHLCData(TypedDict):
    """OHLC数据结构"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: str


class TradingSignal(TypedDict):
    """交易信号结构"""
    symbol: str
    signal_type: str              # 信号类型：bollinger_breakout, yang_bao_yin, break_high
    signal_time: datetime
    entry_price: float            # 建议入场价
    stop_loss: float              # 止损价
    target_price: float           # 目标价
    risk_reward_ratio: float      # 盈亏比
    confidence: float            # 信号置信度（0-1）
    indicators: Dict[str, Any]    # 关键指标快照


class Order(TypedDict):
    """订单结构"""
    order_id: str
    symbol: str
    side: str                    # buy / sell
    order_type: str              # limit / market / stop_limit
    quantity: int
    price: float
    stop_price: Optional[float]
    status: str                  # pending / filled / cancelled / rejected
    created_time: datetime
    updated_time: datetime
    filled_price: Optional[float]
    filled_quantity: int
    signal_id: Optional[str]     # 关联信号ID


class Position(TypedDict):
    """持仓结构"""
    position_id: str
    symbol: str
    entry_price: float
    current_price: float
    quantity: int
    stop_loss: float
    target_price: float
    status: str                  # open / closed
    entry_time: datetime
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    signal_id: Optional[str]     # 关联信号ID

# 配置相关
class ConfigDict(TypedDict, total=False):
    monitor: Dict[str, Any]
    strategy: Dict[str, Any]
    feishu: Dict[str, Any]
    storage: Dict[str, Any]
