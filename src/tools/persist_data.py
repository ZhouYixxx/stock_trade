# -*- coding: utf-8 -*-
# @Time    : 2026-02-17 18:27
# @Author  : ZHOU YI
# @File    : persist_data.py
# @Software: stock_trade
# @Description:独立的数据持久化工具  每日收盘后运行，通过cron或task schedule调度


import argparse
import pathlib
import traceback
import time
import datetime as dt
from typing import List
from ..utils import decorators
from ..utils import logging 
import pandas as pd
from ..config import settings
import yfinance as yf
from ..utils import third_api
from ..types import common
from ..data.db_models import database
from ..data.db_models import StockData
from ..data import db_operations

logger = logging.setup_logger(
    name="persist_data",
    log_file=pathlib.Path(__file__).parent.parent / "logs" / "persist_data.log",  # 可选：输出到文件
    split_by_date=False
)

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="股票数据持久化工具")
    parser.add_argument(
        '--symbol',
        type=str,
        help='指定单只股票（可选）'
    )
    parser.add_argument(
        '--startdate',
        type=str,
        help='指定日期 YYYY-MM-DD（可选，默认为今天）'
    )
    parser.add_argument(
        '--enddate',
        type=str,
        help='指定日期 YYYY-MM-DD（可选，默认为今天）'
    )
    return parser.parse_args()

def load_config(config_path: pathlib.Path) -> None:
    """加载配置文件"""
    # 加载配置
    config = settings.load_config(config_path)
    monitor_config = settings.get_monitor_config(config)
    storage_config = settings.get_storage_config(config)

    # 初始化数据库
    db_operations.init_database(storage_config.db_path)

def get_prev_trading_day(date: dt.date, exchange:common.Exchange = "US") -> bool:
    """获取上一个交易日, 本函数一般在每日收盘后调用"""
    curr_date = date # 当前日期，注意为北京时间
    while True:
        curr_date = curr_date - dt.timedelta(days=1)
        if curr_date.weekday() < 5 and third_api.is_trading_day(curr_date, exchange):
            return curr_date


def persist_single_stock(
    symbol: str,
    date: dt.datetime,
    force: bool = False,
    dry_run: bool = False
) -> bool:
    """
    持久化单只股票的数据到 SQLite 数据库

    Args:
        symbol: 股票代码
        date: 目标日期
        force: 是否强制覆盖
        dry_run: 模拟运行，不实际写入

    Returns:
        是否成功
    """

    logger.info(f"{'='*70}")
    logger.info(f"开始处理: {symbol} @ {date.strftime('%Y-%m-%d')}")
    logger.info(f"{'='*70}")

    try:
        # ====================
        # 步骤 1: 获取数据
        # ====================
        logger.info(f"步骤 1/4: 获取股票数据...")

        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=date, end=date, interval="1d")

        if hist.empty:
            logger.warning(f"  无数据")
            return False

        # 获取最新的日线数据
        latest = hist.iloc[-1]

        # 检查数据完整性
        if pd.isna(latest['Open']) or pd.isna(latest['Close']):
            logger.warning(f"  数据不完整（Open 或 Close 为 NaN）")
            return False

        # ====================
        # 步骤 2: 组织数据
        # ====================
        logger.info(f"步骤 2/4: 组织数据...")

        # 检查数据是否已存在
        exists = StockData.select().where(
            (StockData.symbol == symbol) &
            (StockData.date == date.date())
        ).exists()

        if exists and not force:
            logger.info(f"  数据已存在，跳过（使用 --force 强制覆盖）")
            return True

        # 构建数据记录
        stock_record = {
            'symbol': symbol,
            'date': date.date(),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'close': float(latest['Close']),
            'volume': int(latest['Volume']),
            'created_at': dt.datetime.now()
        }

        logger.info(f"  数据: OHLC={stock_record['open']:.2f}/{stock_record['high']:.2f}/{stock_record['low']:.2f}/{stock_record['close']:.2f}, Vol={stock_record['volume']:,}")

        # ====================
        # 步骤 3: 写入数据库（如果非 dry-run）
        # ====================
        if dry_run:
            logger.info(f"步骤 3/4: [DRY RUN] 跳过数据库写入")
            logger.info(f"步骤 4/4: 完成（dry-run）")
        else:
            logger.info(f"步骤 3/4: 写入数据库...")

            try:
                # 删除旧数据（如果存在）
                if exists:
                    StockData.delete().where(
                        (StockData.symbol == symbol) &
                        (StockData.date == date.date())
                    ).execute()
                    logger.info(f"  删除旧数据")

                # 插入新数据
                StockData.create(**stock_record)
                database.commit()

                logger.info(f"  数据写入成功")

                logger.info(f"步骤 4/4: 完成")

                return True

            except Exception as e:
                database.rollback()
                logger.error(f"  数据库写入失败: {e}")
                logger.error(f"  已回滚事务")
                return False

    except Exception as e:
        logger.error(f"  处理失败: {e}")
        logger.error(f"  数据: {symbol}, 日期: {date}")
        return False


def persist_stocks_daily(
    tickers: List[str] = None,
    start_date: dt.date = None,
    end_date: dt.date = None,
    overwrite: bool = False,
) -> bool:
    """
    持久化所有股票的数据

    Args:
        tickers: List of stock symbols: if None use nasdaq index and SP500 index
        start_date: Start date of the data to be persisted, if none use current date
        end_date: End date of the data to be persisted, if none use current date
        overwrite: Whether to force overwrite existing data
        dry_run: Whether to perform a dry run (do not write to database)

    Returns:
        A dictionary containing the results of the data persistence
    """
    if not tickers or len(tickers) == 0:
        tickers = third_api.get_nasdaq_companies()
        lst2 = third_api.get_sp500_companies()
        tickers.extend(x for x in lst2 if x not in tickers)
    if start_date == None:
        start_date = get_prev_trading_day(dt.date.today())
    if end_date == None:
        end_date = get_prev_trading_day(dt.date.today())
    if start_date > end_date:
        raise ValueError("Start date must be before end date")
    
    #持久化股票数据
    success = True
    batch_size = 20
    delay = 5
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"处理批次 {i//batch_size + 1}: {len(batch)} 个股票")
        
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            batch_data = yf.download(tickers=batch, start=start_str, end=end_str, period='1d', group_by='ticker', progress=False)
            res = db_operations.save_stocks_data(data=batch_data, overwrite=overwrite)
            if res:
                logger.info(f"保存批次{i//batch_size + 1}成功!")
            else:
                logger.error(f"保存批次{i//batch_size + 1}失败!")
                success = False
        except Exception as e:
            logger.error(f"批次{i//batch_size + 1}失败: {traceback.format_exc()}")
            success = False
        
        if i + batch_size < len(tickers):
            logger.info(f"等待 {delay} 秒...")
            time.sleep(delay)
    
    return success


def download_in_batches(tickers:List[str], start:dt.date, end:dt.date, batch_size:int=50, delay:int=5) -> pd.DataFrame:
    all_data = {}
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"处理批次 {i//batch_size + 1}: {len(batch)} 个股票")
        
        try:
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            batch_data = yf.download(tickers=batch, start=start_str, end=end_str, period='1d', group_by='ticker', progress=False)
            all_data.update(batch_data)
        except Exception as e:
            logger.error(f"批次失败: {traceback.format_exc()}")
        
        if i + batch_size < len(tickers):
            print(f"等待 {delay} 秒...")
            time.sleep(delay)
    
    return all_data



def main() -> None:
    try:
        args = parse_args()

        # 解析日期参数
        start_date = None
        end_date = None
        if args.startdate:
            start_date = dt.datetime.strptime(args.startdate, '%Y%m%d').date()
        if args.enddate:
            end_date = dt.datetime.strptime(args.end_date, '%Y%m%d').date()
        load_config(pathlib.Path(__file__).parent.parent / "config" / "config.toml")
        # 每日执行持久化任务
        result = persist_stocks_daily(start_date=start_date, end_date=end_date, overwrite=True)

        # 输出结果
        logger.info(f"持久化任务完成: success = {result}")
    except Exception as e:
        logger.error(f"处理失败: {traceback.format_exc()}")


if __name__ == '__main__':
    main()
