"""
数据库操作模块

提供数据库的增删改查操作
"""
from datetime import date
from ..utils import logging
from typing import Optional, List
from datetime import datetime
from .db_models import database, StockData, SignalRecord, OrderRecord, PositionRecord
from ..types.common import TradingSignal, Order, Position
import pandas as pd
import traceback

logger = logging.get_logger(__name__)

def init_database(db_path: str):
    """
    初始化数据库并创建表结构

    Args:
        db_path: 数据库文件路径
    """
    try:
        database.init(db_path)
        database.create_tables([StockData, SignalRecord, OrderRecord, PositionRecord])
        logger.info(f"数据库初始化成功: {db_path}")

        # 打印表结构信息
        logger.info("数据库表:")
        for model_class in [StockData, SignalRecord, OrderRecord, PositionRecord]:
            logger.info(f"  - {model_class.__name__}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


# ==================== 股票数据操作 ====================

def save_stocks_data(
    data: pd.DataFrame,
    overwrite: bool = False,
) -> bool:
    """
    批量保存股票的历史日线数据（多日）

    Args:
        data: DataFrame, 必须包含 symbol, date, open, high, low, close, volume 列
        overwrite: True = 覆盖重复的记录；False = 只插入不存在的记录

    Returns:
        bool: 是否成功
    """
    if data.empty:
        logger.info(f"数据为空，无需保存")
        return True

    try:
        data = data.rename(columns=str.lower)

        # 字段检查
        required = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in data.columns]
        if missing:
            raise ValueError(f"缺少必要字段: {missing}")

        insert_df = data[required].copy()

        # 数据清洗：过滤掉关键字段为 NaN 的行
        insert_df = insert_df.dropna(subset=['open', 'high', 'low', 'close'])
        insert_df['volume'] = insert_df['volume'].fillna(0).astype('int64')
        insert_df['date'] = insert_df['date'].dt.date
        insert_df['created_at'] = datetime.now()


        records = insert_df.to_dict('records')

        if not records:
            logger.info(f"过滤后无有效数据")
            return True

        with StockData._meta.database.atomic():
            if overwrite:
                # 覆盖模式：冲突时替换整个记录
                query = StockData.insert_many(records)
                saved_count = query.on_conflict_replace().execute()
            else:
                # 增量模式：只插入不存在的记录
                query = StockData.insert_many(records)
                saved_count = query.on_conflict_ignore().execute()


        logger.info(f"保存 {len(records)} 条数据成功，影响记录数：{saved_count}")
        return True

    except Exception as e:
        logger.exception(f"保存数据失败: {traceback.format_exc()}")
        return False


def get_stock_history_data(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[StockData]:
    """
    获取股票历史数据

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        DataFrame 包含历史数据
    """
    try:
        query = StockData.select().where(
            (StockData.symbol == symbol) &
            (StockData.date >= start_date) if start_date else True &
            (StockData.date <= end_date) if end_date else True
        ).order_by(StockData.date.desc())

        records = list(query)

        if not records:
            logger.warning(f"未找到 {symbol} 的历史数据")
            return []

        logger.info(f"查询到 {symbol} {len(records)} 条记录")
        return records

    except Exception as e:
        logger.error(f"获取 {symbol} 数据失败: {traceback.format_exc()}")
        return []


def get_stocks_latest_data(symbols: list[str], date: date) -> List[StockData] | None:
    """
    获取所有股票最新的一条日线数据

    Args:
        symbols: 股票代码列表

    Returns:
        StockData 对象，如果不存在返回 empty list
    """
    try:
        query = StockData.select().where(StockData.symbol.in_(symbols) 
                & (StockData.date == date)).order_by(StockData.date.desc())
        return list(query)

    except Exception as e:
        logger.error(f"获取最新K线数据失败: {traceback.format_exc()}")
        return None



# ==================== 信号操作 ====================

def save_signal(signal: TradingSignal) -> bool:
    """
    保存交易信号

    Args:
        signal: 交易信号字典

    Returns:
        是否成功
    """
    try:
        SignalRecord.create(
            signal_id=signal.get('signal_id', ''),
            symbol=signal['symbol'],
            signal_type=signal['signal_type'],
            signal_time=signal['signal_time'],
            entry_price=signal['entry_price'],
            stop_loss=signal['stop_loss'],
            target_price=signal['target_price'],
            risk_reward_ratio=signal['risk_reward_ratio'],
            confidence=signal['confidence'],
            indicators=signal.get('indicators', {})
        )

        logger.info(f"信号已保存: {signal['symbol']} - {signal['signal_type']}")
        return True

    except Exception as e:
        logger.error(f"保存信号失败: {e}")
        return False


def get_signals(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[SignalRecord]:
    """
    获取交易信号

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        信号记录列表
    """
    try:
        query = SignalRecord.select().where(
            (SignalRecord.symbol == symbol) &
            (SignalRecord.signal_time >= start_date) if start_date else True
        ).order_by(SignalRecord.signal_time.desc())

        records = list(query)
        logger.info(f"查询到 {symbol} {len(records)} 条信号")

        return records

    except Exception as e:
        logger.error(f"获取信号失败: {e}")
        return []


# ==================== 订单操作 ====================

def save_order(order: Order) -> bool:
    """
    保存订单

    Args:
        order: 订单字典

    Returns:
        是否成功
    """
    try:
        OrderRecord.create(
            order_id=order.get('order_id', ''),
            symbol=order['symbol'],
            side=order['side'],
            order_type=order['order_type'],
            quantity=order['quantity'],
            price=order['price'],
            stop_price=order.get('stop_price'),
            status=order.get('status'),
            created_time=order['created_time'],
            updated_time=order['updated_time'],
            filled_price=order.get('filled_price'),
            filled_quantity=order.get('filled_quantity', 0),
            signal_id=order.get('signal_id', None)
        )

        logger.info(f"订单已保存: {order['order_id']} - {order['status']}")
        return True

    except Exception as e:
        logger.error(f"保存订单失败: {e}")
        return False


def get_orders(
    symbol: str = None,
    status: str = None
) -> List[OrderRecord]:
    """
    获取订单

    Args:
        symbol: 股票代码（可选）
        status: 订单状态（可选）

    Returns:
        订单记录列表
    """
    try:
        query = OrderRecord.select()

        if symbol:
            query = query.where(OrderRecord.symbol == symbol)

        if status:
            query = query.where(OrderRecord.status == status)

        records = list(query.order_by(OrderRecord.created_time.desc()))

        logger.info(f"查询到 {len(records)} 条订单")
        return records

    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        return []


def get_order(order_id: str) -> Optional[OrderRecord]:
    """
    获取单个订单

    Args:
        order_id: 订单 ID

    Returns:
        订单记录，如果不存在返回 None
    """
    try:
        order = OrderRecord.get_by_id(order_id)
        return order

    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        return None


def update_order_status(
    order_id: str,
    status: str,
    filled_price: float = None,
    filled_quantity: int = None
) -> Optional[OrderRecord]:
    """
    更新订单状态

    Args:
        order_id: 订单 ID
        status: 新状态
        filled_price: 成交价格
        filled_quantity: 成交数量

    Returns:
        更新后的订单记录
    """
    try:
        query = OrderRecord.update(
            status=status,
            updated_time=datetime.now(),
            filled_price=filled_price,
            filled_quantity=filled_quantity
        ).where(OrderRecord.order_id == order_id)

        query.execute()

        # 重新查询获取更新后的订单
        order = OrderRecord.get_by_id(order_id)

        logger.info(f"订单状态已更新: {order_id} -> {status}")
        return order

    except Exception as e:
        logger.error(f"更新订单状态失败: {e}")
        return None


def cancel_order(order_id: str) -> bool:
    """
    取消订单

    Args:
        order_id: 订单 ID

    Returns:
        是否成功
    """
    return update_order_status(order_id, 'cancelled')


# ==================== 持仓操作 ====================

def save_position(position: Position) -> bool:
    """
    保存持仓

    Args:
        position: 持仓字典

    Returns:
        是否成功
    """
    try:
        PositionRecord.create(
            position_id=position.get('position_id', ''),
            symbol=position['symbol'],
            entry_price=position['entry_price'],
            current_price=position['current_price'],
            quantity=position['quantity'],
            stop_loss=position['stop_loss'],
            target_price=position['target_price'],
            status=position['status'],
            entry_time=position['entry_time'],
            unrealized_pnl=position.get('unrealized_pnl', 0),
            signal_id=position.get('signal_id', None)
        )

        logger.info(f"持仓已保存: {position['position_id']} - {position['status']}")
        return True

    except Exception as e:
        logger.error(f"保存持仓失败: {e}")
        return False


def get_positions(
    symbol: str = None,
    status: str = None
) -> List[PositionRecord]:
    """
    获取持仓

    Args:
        symbol: 股票代码（可选）
        status: 持仓状态（可选）

    Returns:
        持仓记录列表
    """
    try:
        query = PositionRecord.select()

        if symbol:
            query = query.where(PositionRecord.symbol == symbol)

        if status:
            query = query.where(PositionRecord.status == status)

        records = list(query.order_by(PositionRecord.entry_time.desc()))

        logger.info(f"查询到 {len(records)} 条持仓")
        return records

    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return []


def get_position(position_id: str) -> Optional[PositionRecord]:
    """
    获取单个持仓

    Args:
        position_id: 持仓 ID

    Returns:
        持仓记录，如果不存在返回 None
    """
    try:
        position = PositionRecord.get_by_id(position_id)
        return position

    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return None


def update_position(
    position_id: str,
    current_price: float,
    unrealized_pnl: float
) -> Optional[PositionRecord]:
    """
    更新持仓信息

    Args:
        position_id: 持仓 ID
        current_price: 当前价格
        unrealized_pnl: 浮动盈亏

    Returns:
        更新后的持仓记录
    """
    try:
        query = PositionRecord.update(
            current_price=current_price,
            unrealized_pnl=unrealized_pnl
        ).where(PositionRecord.position_id == position_id)

        query.execute()

        position = PositionRecord.get_by_id(position_id)

        logger.info(f"持仓已更新: {position_id} - 当前价格: {current_price}")
        return position

    except Exception as e:
        logger.error(f"更新持仓失败: {e}")
        return None


def close_position(
    position_id: str,
    exit_price: float,
    realized_pnl: float
) -> Optional[PositionRecord]:
    """
    平仓

    Args:
        position_id: 持仓 ID
        exit_price: 退出价格
        realized_pnl: 已实现盈亏

    Returns:
        更新后的持仓记录
    """
    try:
        query = PositionRecord.update(
            status='closed',
            exit_price=exit_price,
            exit_time=datetime.now(),
            realized_pnl=realized_pnl
        ).where(PositionRecord.position_id == position_id)

        query.execute()

        position = PositionRecord.get_by_id(position_id)

        logger.info(f"持仓已平仓: {position_id} - 实现盈亏: {realized_pnl}")
        return position

    except Exception as e:
        logger.error(f"平仓失败: {e}")
        return None
