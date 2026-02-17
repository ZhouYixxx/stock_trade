"""
配置管理模块
"""
import pathlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


def load_config(config_path: pathlib.Path) -> Dict[str, Any]:
    """加载配置文件"""
    pass


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
    """获取存储配置"""
    pass


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
