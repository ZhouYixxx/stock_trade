"""
行情监控模块
"""
import logging
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Any

from ..types.common import OHLCData
from ..config.settings import MonitorConfig

# 配置日志
logger = logging.getLogger(__name__)


def split_stocks_into_batches(
    stocks: List[str],
    batch_size: int
) -> List[List[str]]:
    """
    将股票列表分批

    Args:
        stocks: 股票代码列表
        batch_size: 每批大小

    Returns:
        分批后的股票列表
    """
    batches = []
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i:i + batch_size]
        batches.append(batch)
    return batches


def fetch_ohlc_batch(symbols: List[str]) -> Dict[str, OHLCData]:
    """
    批量获取最新OHLC数据

    Args:
        symbols: 股票代码列表

    Returns:
        股票代码到OHLC数据的字典
    """
    try:
        import yfinance as yf

        result = {}

        # 使用 Tickers 批量获取
        ticker_objs = yf.Tickers(symbols)

        for symbol in symbols:
            try:
                ticker = ticker_objs.tickers[symbol]
                # 获取最新的日线数据
                hist = ticker.history(period="1d")

                if not hist.empty:
                    latest = hist.iloc[-1]
                    result[symbol] = {
                        'open': float(latest['Open']),
                        'high': float(latest['High']),
                        'low': float(latest['Low']),
                        'close': float(latest['Close']),
                        'volume': int(latest['Volume']),
                        'timestamp': latest.name.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    logger.info(f"✓ {symbol}: O={result[symbol]['open']:.2f} "
                               f"H={result[symbol]['high']:.2f} "
                               f"L={result[symbol]['low']:.2f} "
                               f"C={result[symbol]['close']:.2f}")
                else:
                    logger.warning(f"⚠ {symbol}: 无可用数据")

            except Exception as e:
                logger.error(f"✗ {symbol}: 获取数据失败 - {e}")

        return result

    except Exception as e:
        logger.error(f"批量获取失败: {e}")
        return {}


class QuoteMonitor:
    """行情监控器

    负责定时轮询股票行情数据，并通过回调通知订阅者
    """

    def __init__(self, config: MonitorConfig):
        """
        初始化监控器

        Args:
            config: 监控配置
        """
        self.config = config
        self.is_running = False
        self.callbacks = {}
        self._stop_event = threading.Event()
        self._monitor_thread = None

    def start(self):
        """启动监控（在后台线程中运行）"""
        if self.is_running:
            logger.warning("监控器已在运行中")
            return

        self.is_running = True
        self._stop_event.clear()

        # 创建并启动后台线程
        self._monitor_thread = threading.Thread(
            target=self._run_monitor_loop,
            name="QuoteMonitor",
            daemon=True
        )
        self._monitor_thread.start()

        logger.info(f"行情监控已启动，轮询间隔 {self.config.interval} 分钟")
        logger.info(f"监控股票数量: {len(self.config.stocks)}")

    def stop(self):
        """停止监控（优雅停止）"""
        if not self.is_running:
            logger.warning("监控器未在运行")
            return

        logger.info("正在停止行情监控...")
        self._stop_event.set()

        # 等待线程结束（最多等待5秒）
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("监控线程未能在5秒内停止")

        self.is_running = False
        logger.info("行情监控已停止")

    def add_callback(self, event: str, callback: Callable):
        """
        添加回调函数

        Args:
            event: 事件名称，如 'on_data_received', 'on_error'
            callback: 回调函数
        """
        self.callbacks[event] = callback
        logger.debug(f"已注册回调: {event}")

    def remove_callback(self, event: str):
        """
        移除回调函数

        Args:
            event: 事件名称
        """
        if event in self.callbacks:
            del self.callbacks[event]
            logger.debug(f"已移除回调: {event}")

    def is_monitoring(self) -> bool:
        """判断是否在运行中"""
        return self.is_running

    def _run_monitor_loop(self):
        """运行监控循环（在后台线程中执行）"""
        logger.info(f"监控线程启动，开始轮询")

        while not self._stop_event.is_set():
            try:
                # 执行一轮监控
                self._run_once()

                # 等待下一次轮询（支持中途停止）
                wait_seconds = self.config.interval * 60
                logger.info(f"等待 {self.config.interval} 分钟后进行下一次轮询...")

                self._stop_event.wait(timeout=wait_seconds)

            except KeyboardInterrupt:
                logger.info("接收到键盘中断信号")
                break

            except Exception as e:
                logger.error(f"监控循环异常: {e}", exc_info=True)

                # 出错后等待一段时间再重试
                if not self._stop_event.is_set():
                    retry_wait = min(60, self.config.interval * 60)
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    self._stop_event.wait(timeout=retry_wait)

        logger.info("监控线程已退出")

    def _run_once(self):
        """执行一次监控获取行情"""
        logger.info(f"\n{'='*70}")
        logger.info(f"开始获取行情数据: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*70}\n")

        # 分批处理股票
        batches = split_stocks_into_batches(
            self.config.stocks,
            self.config.batch_size
        )

        logger.info(f"股票分批处理: 共 {len(batches)} 批，每批 {self.config.batch_size} 只")

        all_data = {}
        failed_count = 0
        success_count = 0

        for i, batch in enumerate(batches, 1):
            logger.info(f"\n处理第 {i}/{len(batches)} 批，共 {len(batch)} 只股票")
            logger.info(f"股票列表: {', '.join(batch)}")

            batch_data = fetch_ohlc_batch(batch)
            all_data.update(batch_data)

            batch_success = len(batch_data)
            batch_failed = len(batch) - batch_success
            success_count += batch_success
            failed_count += batch_failed

            logger.info(f"本批结果: 成功 {batch_success}, 失败 {batch_failed}")

        # 汇总结果
        logger.info(f"\n{'='*70}")
        logger.info(f"本次轮询完成")
        logger.info(f"总股票数: {len(self.config.stocks)}")
        logger.info(f"成功获取: {success_count} 只")
        logger.info(f"获取失败: {failed_count} 只")
        logger.info(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*70}\n")

        # 触发数据接收回调
        if 'on_data_received' in self.callbacks:
            try:
                self.callbacks['on_data_received'](all_data)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}", exc_info=True)

        # 如果有失败，触发错误回调
        if failed_count > 0 and 'on_error' in self.callbacks:
            try:
                self.callbacks['on_error']({
                    'type': 'fetch_failed',
                    'failed_count': failed_count,
                    'timestamp': datetime.now()
                })
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}", exc_info=True)


# 便捷函数
def start_quote_monitor(
    stocks: List[str],
    interval: int,
    on_data_received: Callable[[Dict[str, OHLCData]], None],
    batch_size: int = 500
) -> QuoteMonitor:
    """
    启动行情监控（便捷函数）

    Args:
        stocks: 股票代码列表
        interval: 轮询间隔（分钟）
        on_data_received: 数据接收回调
        batch_size: 批量获取大小

    Returns:
        QuoteMonitor 实例
    """
    config = MonitorConfig(
        interval=interval,
        stocks=stocks,
        batch_size=batch_size
    )

    monitor = QuoteMonitor(config)
    monitor.add_callback('on_data_received', on_data_received)
    monitor.start()

    return monitor
