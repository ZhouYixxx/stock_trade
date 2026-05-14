# -*- coding: utf-8 -*-
"""
行情监控器使用示例
"""
from pathlib import Path
from src.config.settings import load_config, get_monitor_config
from src.monitor.quote_monitor import QuoteMonitor


def on_data_received(data):
    """数据接收回调"""
    print(f"\n接收到 {len(data)} 只股票的数据")
    for symbol, ohlc in data.items():
        print(f"  {symbol}: {ohlc['timestamp']} - 收盘价: {ohlc['close']:.2f}")


def on_error(error_info):
    """错误回调"""
    print(f"\n发生错误: {error_info}")


def main():
    """主函数"""
    # 加载配置
    # 从 src/config/config.toml 加载配置
    config_path = Path(__file__).parent.parent / "config" / "config.toml"
    config = load_config(config_path)

    # 获取监控配置
    monitor_config = get_monitor_config(config)

    # 创建监控器
    monitor = QuoteMonitor(monitor_config)

    # 注册回调
    monitor.add_callback('on_data_received', on_data_received)
    monitor.add_callback('on_error', on_error)

    # 启动监控
    monitor.start()

    try:
        # 主线程保持运行（实际应用中可能是其他逻辑）
        print("监控器已启动，按 Ctrl+C 停止...")

        # 这里可以添加其他主线程逻辑
        # 例如信号处理、通知等

        # 简单示例：主线程等待
        import time
        while monitor.is_monitoring():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n接收到停止信号")
    finally:
        # 停止监控
        monitor.stop()
        print("程序退出")


if __name__ == '__main__':
    main()
