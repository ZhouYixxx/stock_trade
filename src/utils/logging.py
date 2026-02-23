"""
日志工具模块
"""
import logging
import sys
from typing import Optional
from pathlib import Path
from ..types.common import TradingSignal, Order, Position


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    split_by_date: bool = False,
    level: int = logging.INFO
) -> logging.Logger:
    """
    设置日志器

    Args:
        name: 日志器名称
        log_file: 日志文件路径（可选）
        level: 日志级别

    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的处理器
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if split_by_date:
            # 按天创建一个日志文件
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',          # 'midnight' 表示每天午夜0:00创建新日志文件
                interval=1,
                encoding='utf-8'
            )
            file_handler.suffix = '%Y-%m-%d'
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称（通常使用 __name__）

    Returns:
        已配置的日志器，如果不存在则使用默认配置创建
    """
    logger = logging.getLogger(name)

    # # 如果日志器没有处理器，使用默认配置
    # if not logger.handlers:
    #     formatter = logging.Formatter(
    #         fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #         datefmt='%Y-%m-%d %H:%M:%S'
    #     )
    #     handler = logging.StreamHandler(sys.stdout)
    #     handler.setLevel(logging.INFO)
    #     handler.setFormatter(formatter)
    #     logger.addHandler(handler)
    #     logger.setLevel(logging.INFO)

    return logger


def log_signal(signal: TradingSignal) -> None:
    """
    记录信号日志

    Args:
        signal: 交易信号
    """
    logger = get_logger(__name__)
    logger.info(
        f"信号: {signal['symbol']} - {signal['signal_type']} - "
        f"入场价: {signal['entry_price']:.2f} - "
        f"止损: {signal['stop_loss']:.2f} - "
        f"目标: {signal['target_price']:.2f} - "
        f"盈亏比: {signal['risk_reward_ratio']:.2f} - "
        f"置信度: {signal['confidence']:.2f}"
    )


def log_order(order: Order) -> None:
    """
    记录订单日志

    Args:
        order: 订单
    """
    logger = get_logger(__name__)
    logger.info(
        f"订单: {order['order_id']} - {order['symbol']} - "
        f"{order['side']} - {order['order_type']} - "
        f"数量: {order['quantity']} - 价格: {order['price']:.2f} - "
        f"状态: {order['status']}"
    )


def log_position(position: Position) -> None:
    """
    记录持仓日志

    Args:
        position: 持仓
    """
    logger = get_logger(__name__)
    logger.info(
        f"持仓: {position['position_id']} - {position['symbol']} - "
        f"入场价: {position['entry_price']:.2f} - "
        f"当前价: {position['current_price']:.2f} - "
        f"数量: {position['quantity']} - "
        f"状态: {position['status']} - "
        f"浮盈: {position['unrealized_pnl']:.2f}"
    )
