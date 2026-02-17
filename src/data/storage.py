"""
数据存储模块
"""
import peewee
from datetime import datetime
from typing import Optional, List
import pandas as pd

from .models import StockData, SignalRecord, OrderRecord, PositionRecord
from ..types.common import TradingSignal, Order, Position


def init_database(db_path: str) -> peewee.Database:
    """初始化数据库"""
    pass


def save_stock_data(
    symbol: str,
    data: pd.DataFrame,
    overwrite: bool = False
) -> bool:
    """保存股票历史数据（批量导入或历史数据）"""
    pass


def get_stock_data(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """获取股票历史数据"""
    pass


def save_signal(
    symbol: str,
    signal: TradingSignal
) -> bool:
    """保存交易信号"""
    pass


def get_signals(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[TradingSignal]:
    """获取交易信号"""
    pass


def save_order(order: Order) -> bool:
    """保存订单"""
    pass


def get_orders(
    symbol: str,
    status: Optional[str] = None
) -> List[Order]:
    """获取订单"""
    pass


def save_position(position: Position) -> bool:
    """保存持仓"""
    pass


def get_positions(
    symbol: Optional[str] = None,
    status: Optional[str] = None
) -> List[Position]:
    """获取持仓"""
    pass
