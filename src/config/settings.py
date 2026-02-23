"""
配置管理模块
"""
import pathlib
import tomllib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


def load_config(config_path: pathlib.Path) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    except Exception as e:
        raise RuntimeError(f"加载配置文件失败: {e}")


def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置有效性"""
    pass


def get_monitor_config(config: Dict[str, Any]) -> 'MonitorConfig':
    """获取监控配置"""
    pass


def get_strategy_config(config: Dict[str, Any]) -> 'StrategyConfig':
    """获取策略配置"""
    pass


def get_feishu_config(config: Dict[str, Any]) -> 'FeishuConfig':
    """获取飞书配置"""
    pass


def get_storage_config(config: Dict[str, Any]) -> 'StorageConfig':
    """
    获取DB相关配置
    """
    storage_config = config.get('storage', {})
    # 设置默认值
    stc = StorageConfig(
        db_path=storage_config.get('db_path', 'data/stocks.db'),
        enable_history=storage_config.get('enable_history', True),
        history_days=storage_config.get('history_days', 365)
    )
    stc.db_path = pathlib.Path(__file__).resolve().parent.parent / stc.db_path
    return stc


@dataclass
class MonitorConfig:
    """监控配置数据类"""
    interval: int
    stocks: List[str]
    batch_size: int


@dataclass
class StrategyConfig:
    """策略配置数据类"""
    ma_period: int              # 移动平均线周期（120日）
    bollinger_period: int       # 布林带周期
    bollinger_std: float        # 布林带标准差倍数
    threshold_large_cap: float  # 大盘股偏离阈值（8%）
    threshold_small_cap: float  # 小盘股偏离阈值（20%）
    large_cap_market_cap: float # 大盘股市值阈值（3000亿USD）
    risk_reward_ratio: float    # 目标盈亏比


@dataclass
class FeishuConfig:
    """飞书配置数据类"""
    webhook_url: str
    enabled: bool


@dataclass
class StorageConfig:
    """存储配置数据类"""
    db_path: str
    enable_history: bool
    history_days: int
