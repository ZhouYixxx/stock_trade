# -*- coding: utf-8 -*-
"""
数据持久化工具示例
展示如何使用 utils/logging.py 和 utils/decorators.py
"""
import argparse
import pathlib
from datetime import datetime
from typing import List

import pandas as pd

# ========== 导入配置模块 ==========
# 注意：使用相对导入，从 src 目录开始
from ..config.settings import load_config, get_monitor_config, get_storage_config
from ..data.market_data import (
    fetch_stock_data,
    fetch_stock_data_batch,
    is_trading_day
)
from ..data.db_operations import init_database, save_stock_history_data, get_stock_data

# ========== 导入工具模块 ==========
# 方式 1：直接导入需要的函数
from ..utils.logging import setup_logger, get_logger
from ..utils.decorators import retry, log_execution_time, catch_exceptions


# 方式 2：导入整个模块，使用时指定模块名
# from ..utils import logging as log_utils
# from ..utils import decorators as deco_utils


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="股票数据持久化工具")
    parser.add_argument(
        '--config',
        type=str,
        default='./src/config/config.toml',
        help='配置文件路径'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        help='指定单只股票（可选）'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期 YYYY-MM-DD（可选，默认为今天）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖已存在的数据'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际写入数据库'
    )
    return parser.parse_args()


# ========== 使用装饰器示例 ==========
@retry(max_attempts=3, delay=1.0)  # 失败重试 3 次
def is_market_closed() -> bool:
    """判断市场是否收盘"""
    # 这里实现实际的收盘判断逻辑
    # 例如：美东时间 16:30 后收盘
    import pytz
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    current_time = now.time()

    # 市场开盘时间：9:30-16:00 EST
    market_close = datetime.strptime("16:30", "%H:%M").time()

    is_closed = current_time >= market_close
    return is_closed


@log_execution_time  # 自动记录函数执行时间
def should_persist_today(symbol: str, date: datetime) -> bool:
    """判断指定日期的数据是否已经持久化"""
    logger = get_logger(__name__)
    logger.debug(f"检查 {symbol} 在 {date} 的数据是否已持久化")

    # 这里实现实际的检查逻辑
    # 例如：查询数据库
    # exists = database.check_data_exists(symbol, date)
    # return not exists

    return False  # 示例返回值


@catch_exceptions(default_return=False, logger=get_logger(__name__))
def persist_single_stock(
    symbol: str,
    date: datetime,
    force: bool = False,
    dry_run: bool = False
) -> bool:
    """
    持久化单只股票的数据

    如果抛出异常，装饰器会捕获并返回 False
    """
    logger = get_logger(__name__)

    logger.info(f"开始持久化 {symbol} 的数据...")

    # 获取股票数据
    try:
        data = fetch_stock_data(symbol, period="1y", interval="1d")
    except Exception as e:
        logger.error(f"获取 {symbol} 数据失败: {e}")
        return False

    # 检查数据是否为空
    if data.empty:
        logger.warning(f"{symbol} 没有可用数据")
        return False

    # 模拟运行模式
    if dry_run:
        logger.info(f"[DRY RUN] 将保存 {symbol} 的 {len(data)} 天数据")
        return True

    # 持久化到数据库
    try:
        save_stock_history_data(symbol, data)
        logger.info(f"✓ {symbol} 数据持久化成功")
        return True
    except Exception as e:
        logger.error(f"✗ {symbol} 数据持久化失败: {e}")
        return False


def persist_all_stocks(
    stocks: List[str],
    date: datetime,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """持久化所有股票的数据"""
    logger = get_logger(__name__)

    results = {
        'success': [],
        'failed': [],
        'total': len(stocks)
    }

    logger.info(f"开始持久化 {len(stocks)} 只股票的数据...")

    for symbol in stocks:
        success = persist_single_stock(symbol, date, force, dry_run)

        if success:
            results['success'].append(symbol)
        else:
            results['failed'].append(symbol)

    # 输出汇总
    logger.info(f"\n{'='*60}")
    logger.info(f"持久化完成：成功 {len(results['success'])}, 失败 {len(results['failed'])}")
    logger.info(f"{'='*60}\n")

    return results


def persist_by_date(date: datetime, force: bool = False, dry_run: bool = False) -> dict:
    """按日期持久化数据"""
    logger = get_logger(__name__)

    # 加载配置
    config = load_config(pathlib.Path('./src/config/config.toml'))
    monitor_config = get_monitor_config(config)

    logger.info(f"持久化日期: {date.strftime('%Y-%m-%d')}")
    logger.info(f"股票数量: {len(monitor_config.stocks)}")

    # 持久化所有股票
    results = persist_all_stocks(
        monitor_config.stocks,
        date,
        force,
        dry_run
    )

    return results


def persist_missing_dates(
    start_date: datetime,
    end_date: datetime,
    dry_run: bool = False
) -> dict:
    """补齐缺失日期的数据"""
    logger = get_logger(__name__)

    results = {
        'success_dates': [],
        'failed_dates': [],
        'total_dates': 0
    }

    # 加载配置
    config = load_config(pathlib.Path('./src/config/config.toml'))
    monitor_config = get_monitor_config(config)
    storage_config = get_storage_config(config)

    # 初始化数据库
    init_database(storage_config.db_path)

    # 遍历日期范围
    current_date = start_date
    while current_date <= end_date:
        # 检查是否为交易日
        if is_trading_day(current_date):
            logger.info(f"检查日期: {current_date.strftime('%Y-%m-%d')}")

            # 对每只股票检查
            for symbol in monitor_config.stocks:
                if not should_persist_today(symbol, current_date):
                    # 数据缺失，需要持久化
                    logger.info(f"{symbol} 在 {current_date} 的数据缺失，开始持久化...")

                    success = persist_single_stock(
                        symbol,
                        current_date,
                        force=True,
                        dry_run=dry_run
                    )

                    if success:
                        results['success_dates'].append(current_date.strftime('%Y-%m-%d'))
                    else:
                        results['failed_dates'].append(current_date.strftime('%Y-%m-%d'))

        current_date += datetime.timedelta(days=1)

    logger.info(f"\n补齐完成: 成功 {len(results['success_dates'])}, 失败 {len(results['failed_dates'])}")

    return results


def run_persist_job(
    config_path: str,
    symbol: str = None,
    date: datetime = None,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """执行持久化任务"""
    # 设置日志
    logger = setup_logger(
        name="persist_data",
        log_file="logs/persist.log",  # 可选：输出到文件
    )

    logger.info("="*70)
    logger.info("数据持久化工具启动")
    logger.info("="*70)

    # 解析日期
    if date is None:
        date = datetime.now().date()
    else:
        date = datetime.strptime(date, '%Y-%m-%d').date()

    logger.info(f"目标日期: {date.strftime('%Y-%m-%d')}")
    logger.info(f"配置文件: {config_path}")

    # 检查市场是否收盘
    if not is_market_closed():
        logger.warning("市场尚未收盘，数据可能不完整")
        if not force:
            logger.info("使用 --force 参数可以强制执行")
            return {'status': 'skipped', 'reason': 'market_not_closed'}

    # 加载配置
    try:
        config = load_config(pathlib.Path(config_path))
        monitor_config = get_monitor_config(config)
        storage_config = get_storage_config(config)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {'status': 'error', 'reason': 'config_load_failed'}

    # 初始化数据库
    try:
        init_database(storage_config.db_path)
        logger.info(f"数据库初始化成功: {storage_config.db_path}")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return {'status': 'error', 'reason': 'db_init_failed'}

    # 执行持久化
    results = {}

    if symbol:
        # 持久化单只股票
        results['status'] = 'single_stock'
        success = persist_single_stock(symbol, date, force, dry_run)
        results['success'] = success
    else:
        # 持久化所有股票
        results['status'] = 'all_stocks'
        results = persist_by_date(date, force, dry_run)

    logger.info("="*70)
    logger.info("数据持久化任务完成")
    logger.info("="*70)

    return results


def main() -> None:
    """主入口"""
    # 解析参数
    args = parse_args()

    # 解析日期
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()

    # 执行持久化任务
    result = run_persist_job(
        config_path=args.config,
        symbol=args.symbol,
        date=target_date,
        force=args.force,
        dry_run=args.dry_run
    )

    # 输出结果
    logger = get_logger(__name__)
    logger.info(f"任务结果: {result}")


if __name__ == '__main__':
    main()
