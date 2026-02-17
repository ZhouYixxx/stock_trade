# Stock Trade 项目架构设计

## 目录结构

```
stock_trade/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── config/                    # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py            # 配置加载和验证
│   ├── data/                      # 数据模块
│   │   ├── __init__.py
│   │   ├── market_data.py         # 市场数据获取
│   │   ├── storage.py             # 数据持久化
│   │   └── models.py              # 数据模型
│   ├── strategy/                  # 策略模块
│   │   ├── __init__.py
│   │   ├── base.py                # 策略基类
│   │   ├── indicators.py          # 技术指标计算
│   │   ├── signals.py             # 信号生成
│   │   └── screening.py           # 股票筛选
│   ├── notification/              # 通知模块
│   │   ├── __init__.py
│   │   ├── base.py                # 通知基类
│   │   ├── feishu.py              # 飞书通知
│   │   └── formatter.py           # 消息格式化
│   ├── trading/                   # 交易模块
│   │   ├── __init__.py
│   │   ├── order.py               # 订单管理
│   │   └── position.py            # 持仓管理
│   ├── tools/                     # 工具模块
│   │   ├── __init__.py
│   │   └── persist_data.py        # 数据持久化工具（独立运行）
│   ├── monitor/                   # 监控模块
│   │   ├── __init__.py
│   │   ├── quote_monitor.py       # 行情监控
│   │   └── signal_monitor.py      # 信号监控
│   ├── utils/                     # 工具模块
│   │   ├── __init__.py
│   │   ├── logging.py             # 日志工具
│   │   ├── time.py                # 时间工具
│   │   └── decorators.py          # 装饰器
│   └── types/                     # 类型定义
│       ├── __init__.py
│       └── common.py              # 通用类型
├── tests/                         # 测试模块
│   ├── __init__.py
│   ├── test_data/
│   ├── test_indicators.py
│   ├── test_signals.py
│   └── test_screening.py
├── config.toml                    # 主配置文件
├── requirements.txt
├── README.md
└── CLAUDE.md
```

---

## 模块设计

### 1. main.py (应用入口)

```python
def main() -> None:
    """应用主入口"""

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""

def run_in_monitor_mode(config: Dict[str, Any]) -> None:
    """监控模式运行"""

def run_in_backtest_mode(config: Dict[str, Any]) -> None:
    """回测模式运行"""

def run_in_analysis_mode(config: Dict[str, Any]) -> None:
    """分析模式运行"""
```

---

### 2. config/settings.py (配置管理)

```python
def load_config(config_path: pathlib.Path) -> Dict[str, Any]:
    """加载配置文件"""

def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置有效性"""

def get_monitor_config(config: Dict[str, Any]) -> MonitorConfig:
    """获取监控配置"""

def get_strategy_config(config: Dict[str, Any]) -> StrategyConfig:
    """获取策略配置"""

def get_feishu_config(config: Dict[str, Any]) -> FeishuConfig:
    """获取飞书配置"""

class MonitorConfig:
    """监控配置数据类"""
    interval: int
    stocks: List[str]
    batch_size: int

class StrategyConfig:
    """策略配置数据类"""
    ma_period: int              # 移动平均线周期（120日）
    bollinger_period: int       # 布林带周期
    bollinger_std: float        # 布林带标准差倍数
    threshold_large_cap: float  # 大盘股偏离阈值（8%）
    threshold_small_cap: float  # 小盘股偏离阈值（20%）
    large_cap_market_cap: float # 大盘股市值阈值（3000亿USD）

class FeishuConfig:
    """飞书配置数据类"""
    webhook_url: str
    enabled: bool
```

---

### 3. data/market_data.py (市场数据获取)

```python
def fetch_stock_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:
    """获取单只股票历史数据"""

def fetch_stock_data_batch(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    """批量获取股票历史数据"""

def fetch_ohlc_batch(
    symbols: List[str]
) -> Dict[str, OHLCData]:
    """批量获取最新OHLC数据"""

def fetch_market_cap(symbol: str) -> float:
    """获取股票市值"""

def fetch_stock_info(symbol: str) -> StockInfo:
    """获取股票基本信息"""

def get_trading_dates(
    start_date: datetime,
    end_date: datetime
) -> List[datetime]:
    """获取交易日期列表"""

def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日"""

class OHLCData(TypedDict):
    """OHLC数据结构"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: str

class StockInfo(TypedDict):
    """股票信息结构"""
    symbol: str
    name: str
    market_cap: float
    sector: str
    industry: str
```

---

### 4. data/storage.py (数据存储)

```python
def init_database(db_path: str) -> peewee.Database:
    """初始化数据库"""

def save_stock_data(
    symbol: str,
    data: pd.DataFrame,
    overwrite: bool = False
) -> bool:
    """保存股票历史数据（批量导入或历史数据）"""

def get_stock_data(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """获取股票历史数据"""

def save_signal(
    symbol: str,
    signal: TradingSignal
) -> bool:
    """保存交易信号"""

def get_signals(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[TradingSignal]:
    """获取交易信号"""

def save_order(order: Order) -> bool:
    """保存订单"""

def get_orders(
    symbol: str,
    status: Optional[str] = None
) -> List[Order]:
    """获取订单"""

def save_position(position: Position) -> bool:
    """保存持仓"""

def get_positions(
    symbol: Optional[str] = None,
    status: Optional[str] = None
) -> List[Position]:
    """获取持仓"""
```

---

### 5. data/models.py (数据模型)

```python
class StockData(peewee.Model):
    """股票数据模型"""

class SignalRecord(peewee.Model):
    """信号记录模型"""

class OrderRecord(peewee.Model):
    """订单记录模型"""

class PositionRecord(peewee.Model):
    """持仓记录模型"""
```

---

### 6. strategy/indicators.py (技术指标计算)

```python
def calculate_sma(
    data: pd.Series,
    period: int
) -> pd.Series:
    """计算简单移动平均线"""

def calculate_ema(
    data: pd.Series,
    period: int
) -> pd.Series:
    """计算指数移动平均线"""

def calculate_bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> BollingerBands:
    """计算布林带"""

def calculate_rsi(
    data: pd.Series,
    period: int = 14
) -> pd.Series:
    """计算RSI指标"""

def calculate_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> MACD:
    """计算MACD指标"""

def is_bullish_engulfing(
    prev_candle: pd.Series,
    curr_candle: pd.Series
) -> bool:
    """判断是否为阳包阴形态"""

def is_break_high(
    prev_candle: pd.Series,
    curr_candle: pd.Series
) -> bool:
    """判断是否突破前一日高点"""

class BollingerBands(NamedTuple):
    """布林带数据"""
    upper: pd.Series
    middle: pd.Series
    lower: pd.Series

class MACD(NamedTuple):
    """MACD数据"""
    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series
```

---

### 7. strategy/signals.py (信号生成)

```python
def generate_bollinger_breakout_signal(
    data: pd.DataFrame,
    config: StrategyConfig
) -> Optional[TradingSignal]:
    """生成布林带突破信号"""

def generate_yang_bao_yin_signal(
    data: pd.DataFrame,
    config: StrategyConfig
) -> Optional[TradingSignal]:
    """生成阳包阴信号"""

def generate_break_high_signal(
    data: pd.DataFrame,
    config: StrategyConfig
) -> Optional[TradingSignal]:
    """生成突破高点信号"""

def generate_composite_signal(
    data: pd.DataFrame,
    config: StrategyConfig
) -> Optional[TradingSignal]:
    """生成综合信号"""

def calculate_signal_price(
    signal_type: str,
    data: pd.DataFrame
) -> float:
    """计算信号价格（挂单价格）"""

def calculate_stop_loss(
    entry_price: float,
    signal: TradingSignal,
    config: StrategyConfig
) -> float:
    """计算止损价格"""

def calculate_target_price(
    entry_price: float,
    risk_reward_ratio: float
) -> float:
    """计算目标价格"""

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
```

---

### 8. strategy/screening.py (股票筛选)

```python
def screen_by_ma_distance(
    symbol: str,
    data: pd.DataFrame,
    ma_period: int,
    threshold: float,
    direction: str = "below"
) -> bool:
    """根据移动平均线距离筛选"""

def screen_by_bollinger_breakout(
    data: pd.DataFrame,
    config: StrategyConfig
) -> bool:
    """根据布林带突破筛选"""

def screen_by_market_cap(
    market_cap: float,
    threshold: float,
    category: str = "large_cap"
) -> bool:
    """根据市值筛选"""

def screen_by_index_constituent(
    symbol: str,
    index: str = "SP500"
) -> bool:
    """根据指数成分股筛选"""

def screen_composite(
    symbol: str,
    data: pd.DataFrame,
    stock_info: StockInfo,
    config: StrategyConfig
) -> bool:
    """综合筛选"""

def classify_market_cap(market_cap: float) -> str:
    """分类市值：large_cap / mid_cap / small_cap"""

def get_index_constituents(index: str) -> List[str]:
    """获取指数成分股列表"""
```

---

### 9. strategy/base.py (策略基类)

```python
class BaseStrategy(ABC):
    """策略基类"""

    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        """分析股票，生成信号"""

    @abstractmethod
    def should_buy(self, signal: TradingSignal) -> bool:
        """判断是否应该买入"""

    @abstractmethod
    def should_sell(self, position: Position, data: pd.DataFrame) -> bool:
        """判断是否应该卖出"""

    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """计算仓位大小"""

class BollingerStrategy(BaseStrategy):
    """布林带策略实现"""

class MeanReversionStrategy(BaseStrategy):
    """均值回归策略实现"""
```

---

### 10. notification/base.py (通知基类)

```python
class BaseNotifier(ABC):
    """通知基类"""

    @abstractmethod
    def send(self, message: str) -> bool:
        """发送消息"""

    @abstractmethod
    def send_signal(self, signal: TradingSignal) -> bool:
        """发送交易信号"""

    @abstractmethod
    def send_order(self, order: Order) -> bool:
        """发送订单通知"""

    @abstractmethod
    def send_alert(self, level: str, message: str) -> bool:
        """发送告警消息"""
```

---

### 11. notification/feishu.py (飞书通知)

```python
class FeishuNotifier(BaseNotifier):
    """飞书通知实现"""

    def __init__(self, webhook_url: str):
        """初始化"""

    def send(self, message: str) -> bool:
        """发送文本消息"""

    def send_signal(self, signal: TradingSignal) -> bool:
        """发送交易信号"""

    def send_order(self, order: Order) -> bool:
        """发送订单通知"""

    def send_alert(self, level: str, message: str) -> bool:
        """发送告警消息"""

    def send_card(self, card: Dict[str, Any]) -> bool:
        """发送卡片消息"""

def send_feishu_message(webhook_url: str, content: str) -> bool:
    """发送飞书消息（底层函数）"""

def build_signal_card(signal: TradingSignal) -> Dict[str, Any]:
    """构建信号卡片"""

def build_order_card(order: Order) -> Dict[str, Any]:
    """构建订单卡片"""

def build_alert_card(level: str, message: str) -> Dict[str, Any]:
    """构建告警卡片"""
```

---

### 12. notification/formatter.py (消息格式化)

```python
def format_signal_message(signal: TradingSignal) -> str:
    """格式化信号消息为文本"""

def format_order_message(order: Order) -> str:
    """格式化订单消息为文本"""

def format_position_message(position: Position) -> str:
    """格式化持仓消息为文本"""

def format_daily_summary(
    signals: List[TradingSignal],
    orders: List[Order],
    positions: List[Position]
) -> str:
    """格式化每日汇总"""

def format_table(data: List[Dict[str, Any]]) -> str:
    """格式化表格"""

def format_emoji(level: str) -> str:
    """获取表情符号"""
```

---

### 13. trading/order.py (订单管理)

```python
def create_order(
    symbol: str,
    side: str,
    quantity: int,
    price: float,
    order_type: str = "limit"
) -> Order:
    """创建订单"""

def validate_order(order: Order) -> bool:
    """验证订单有效性"""

def calculate_order_value(order: Order) -> float:
    """计算订单金额"""

def update_order_status(
    order_id: str,
    status: str,
    fill_price: Optional[float] = None
) -> Order:
    """更新订单状态"""

def cancel_order(order_id: str) -> bool:
    """取消订单"""

def get_pending_orders() -> List[Order]:
    """获取待处理订单"""

def check_order_fills(order: Order, current_price: float) -> bool:
    """检查订单是否成交"""

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
```

---

### 14. trading/position.py (持仓管理)

```python
def create_position(
    symbol: str,
    entry_price: float,
    quantity: int,
    stop_loss: float
) -> Position:
    """创建持仓"""

def update_position(
    position_id: str,
    **kwargs
) -> Position:
    """更新持仓"""

def close_position(
    position_id: str,
    exit_price: float
) -> Position:
    """平仓"""

def calculate_pnl(position: Position, current_price: float) -> float:
    """计算盈亏"""

def calculate_pnl_percent(position: Position, current_price: float) -> float:
    """计算盈亏百分比"""

def should_stop_loss(position: Position, current_price: float) -> bool:
    """判断是否应该止损"""

def should_take_profit(
    position: Position,
    current_price: float,
    target_price: float
) -> bool:
    """判断是否应该止盈"""

def get_open_positions() -> List[Position]:
    """获取未平仓持仓"""

def get_position_by_symbol(symbol: str) -> Optional[Position]:
    """根据股票代码获取持仓"""

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
```

---

### 15. monitor/quote_monitor.py (行情监控)

**重要说明**：监控每10分钟获取一次实时行情用于策略分析，数据持久化由独立工具 `tools/persist_data.py` 处理。

```python
def start_quote_monitor(
    stocks: List[str],
    interval: int,
    on_data_received: Callable[[Dict[str, OHLCData]], None]
) -> None:
    """启动行情监控"""

def stop_quote_monitor() -> None:
    """停止行情监控"""

def fetch_quotes_in_loop(
    stocks: List[str],
    interval: int,
    callback: Callable
) -> None:
    """循环获取行情"""

def split_stocks_into_batches(
    stocks: List[str],
    batch_size: int
) -> List[List[str]]:
    """将股票列表分批"""

class QuoteMonitor:
    """行情监控器"""

    def __init__(self, config: MonitorConfig):
        """初始化"""

    def start(self) -> None:
        """启动监控"""

    def stop(self) -> None:
        """停止监控"""

    def add_callback(
        self,
        event: str,
        callback: Callable
    ) -> None:
        """添加回调函数"""

    def is_running(self) -> bool:
        """判断是否运行中"""
```

---

### 16. monitor/signal_monitor.py (信号监控)

```python
def start_signal_monitor(
    stocks: List[str],
    strategy: BaseStrategy,
    notifier: BaseNotifier
) -> None:
    """启动信号监控"""

def stop_signal_monitor() -> None:
    """停止信号监控"""

def check_signals(
    stocks: List[str],
    strategy: BaseStrategy
) -> List[TradingSignal]:
    """检查所有股票的信号"""

def process_signal(
    signal: TradingSignal,
    notifier: BaseNotifier
) -> None:
    """处理信号（发送通知、生成订单等）"""

def evaluate_signal_quality(signal: TradingSignal) -> float:
    """评估信号质量"""

class SignalMonitor:
    """信号监控器"""

    def __init__(
        self,
        strategy: BaseStrategy,
        notifier: BaseNotifier,
        config: StrategyConfig
    ):
        """初始化"""

    def start(self) -> None:
        """启动监控"""

    def stop(self) -> None:
        """停止监控"""

    def run_once(self) -> List[TradingSignal]:
        """执行一次检查"""

    def add_signal_filter(
        self,
        filter_func: Callable[[TradingSignal], bool]
    ) -> None:
        """添加信号过滤器"""
```

---

### 17. tools/persist_data.py (数据持久化工具)

**重要说明**：独立运行的数据持久化工具，通过 cron 或 task schedule 调度，每日收盘后执行。主监控程序无需考虑数据持久化。

```python
def parse_args() -> argparse.Namespace:
    """解析命令行参数"""

def is_market_closed() -> bool:
    """判断市场是否收盘"""

def should_persist_today(symbol: str, date: datetime) -> bool:
    """判断指定日期的数据是否已经持久化"""

def persist_single_stock(
    symbol: str,
    date: datetime,
    force: bool = False,
    dry_run: bool = False
) -> bool:
    """持久化单只股票的数据"""

def persist_all_stocks(
    stocks: List[str],
    date: datetime,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """持久化所有股票的数据"""

def persist_by_date(date: datetime, force: bool = False, dry_run: bool = False) -> dict:
    """按日期持久化数据"""

def persist_missing_dates(
    start_date: datetime,
    end_date: datetime,
    dry_run: bool = False
) -> dict:
    """补齐缺失日期的数据"""

def run_persist_job(
    config_path: str,
    symbol: str = None,
    date: datetime = None,
    force: bool = False,
    dry_run: bool = False
) -> dict:
    """执行持久化任务"""

def main() -> None:
    """主入口"""
```

---

### 18. utils/logging.py (日志工具)

```python
def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """设置日志器"""

def get_logger(name: str) -> logging.Logger:
    """获取日志器"""

class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

def log_signal(signal: TradingSignal) -> None:
    """记录信号日志"""

def log_order(order: Order) -> None:
    """记录订单日志"""

def log_position(position: Position) -> None:
    """记录持仓日志"""
```

---

### 19. utils/time.py (时间工具)

```python
def get_trading_day(date: datetime) -> datetime:
    """获取交易日（跳过周末）"""

def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日"""

def is_market_open() -> bool:
    """判断市场是否开盘"""

def get_next_trading_day(date: datetime) -> datetime:
    """获取下一个交易日"""

def get_previous_trading_day(date: datetime) -> datetime:
    """获取上一个交易日"""

def format_timestamp(ts: datetime) -> str:
    """格式化时间戳"""

def parse_timestamp(ts_str: str) -> datetime:
    """解析时间戳"""
```

---

### 20. utils/decorators.py (装饰器)

```python
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> Callable:
    """重试装饰器"""

def log_execution_time(func: Callable) -> Callable:
    """记录执行时间装饰器"""

def catch_exceptions(
    default_return: Any = None,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """捕获异常装饰器"""

def rate_limit(calls: int, period: float) -> Callable:
    """限流装饰器"""

def cache_result(ttl: int = 60) -> Callable:
    """缓存结果装饰器"""
```

---

### 21. types/common.py (类型定义)

```python
# 策略相关
SignalType = Literal["bollinger_breakout", "yang_bao_yin", "break_high"]
OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market", "stop_limit"]
OrderStatus = Literal["pending", "filled", "cancelled", "rejected"]
PositionStatus = Literal["open", "closed"]
MarketCapCategory = Literal["large_cap", "mid_cap", "small_cap"]

# 配置相关
class ConfigDict(TypedDict, total=False):
    monitor: MonitorConfig
    strategy: StrategyConfig
    feishu: FeishuConfig
    storage: StorageConfig

class StorageConfig(TypedDict):
    db_path: str
    enable_history: bool
    history_days: int
```

---

## 数据流图

```
config.toml
    ↓
main.py
    ↓
┌─────────────────────────────────────────────┐
│  QuoteMonitor (行情监控 - 每10分钟)           │
│  ┌─────────────────────────────────────┐   │
│  │  fetch_ohlc_batch()                │   │ ← 实时行情
│  └─────────────────────────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │ OHLC Data
                  ↓
┌─────────────────────────────────────────────┐
│  Strategy Engine (策略引擎)                  │
│  ┌─────────────────────────────────────┐   │
│  │  screening.screen_composite()      │   │
│  │  indicators.calculate_*()          │   │
│  │  signals.generate_*()              │   │
│  └─────────────────────────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │ TradingSignal
                  ↓
┌─────────────────────────────────────────────┐
│  Order Manager (订单管理)                    │
│  ┌─────────────────────────────────────┐   │
│  │  order.create_order()               │   │
│  │  position.create_position()        │   │
│  └─────────────────────────────────────┘   │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  Notification (通知)                         │
│  ┌─────────────────────────────────────┐   │
│  │  feishu.FeishuNotifier.send_*()    │   │
│  │  formatter.format_*()              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

独立运行：数据持久化工具（每日收盘后，cron/task schedule调度）
┌─────────────────────────────────────────────┐
│  tools/persist_data.py                     │
│  ┌─────────────────────────────────────┐   │
│  │  is_market_closed()                │   │
│  │  should_persist_today()           │   │
│  │  persist_single_stock()            │   │
│  │  persist_all_stocks()              │   │
│  │  fetch_stock_data() → Database    │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                  ↓
            ┌──────────────┐
            │  Database    │
            │  (日线数据)   │
            └──────┬───────┘
                   │
                   ↑
                   │ 查询
┌──────────────────┴──────────────────────────┐
│  Strategy Engine (回测/分析)                 │
│  get_stock_data() ← 从数据库获取历史数据    │
└─────────────────────────────────────────────┘

说明：
- 实时监控：每10分钟获取一次行情，用于策略分析和信号生成
- 数据持久化：通过独立工具 persist_data.py 执行，每日收盘后由系统级定时任务调度
- 历史数据查询：策略分析时直接从数据库获取历史日线数据
```

---

## 模块依赖关系

```
main.py
  ├── config/settings.py
  ├── monitor/quote_monitor.py
  ├── monitor/signal_monitor.py
  └── notification/feishu.py

monitor/signal_monitor.py
  ├── data/market_data.py
  ├── data/storage.py
  ├── strategy/base.py
  ├── strategy/screening.py
  ├── strategy/indicators.py
  ├── strategy/signals.py
  ├── trading/order.py
  ├── trading/position.py
  └── notification/feishu.py

strategy/
  ├── strategy/base.py (依赖: types/common.py)
  ├── strategy/screening.py (依赖: indicators.py, data/market_data.py)
  ├── strategy/indicators.py (依赖: 无)
  └── strategy/signals.py (依赖: indicators.py, types/common.py)

trading/
  ├── trading/order.py (依赖: types/common.py)
  └── trading/position.py (依赖: types/common.py)

notification/
  ├── notification/base.py (依赖: types/common.py)
  ├── notification/feishu.py (依赖: base.py)
  └── notification/formatter.py (依赖: types/common.py)

data/
  ├── data/market_data.py (依赖: 无)
  ├── data/storage.py (依赖: data/models.py)
  └── data/models.py (依赖: 无)

tools/
  ├── tools/persist_data.py (依赖: config/settings.py, data/market_data.py, data/storage.py, utils/logging.py)

utils/
  ├── utils/logging.py (依赖: 无)
  ├── utils/time.py (依赖: 无)
  └── utils/decorators.py (依赖: 无)
```

---

## 扩展点

### 1. 策略扩展
通过继承 `BaseStrategy` 类添加新策略：
```python
class MyCustomStrategy(BaseStrategy):
    def analyze(self, symbol: str, data: pd.DataFrame) -> Optional[TradingSignal]:
        # 自定义逻辑
        pass
```

### 2. 通知扩展
通过继承 `BaseNotifier` 类添加新通知渠道：
```python
class TelegramNotifier(BaseNotifier):
    def send(self, message: str) -> bool:
        # Telegram 通知逻辑
        pass
```

### 3. 数据源扩展
可以新增 `data/alpaca_data.py` 或 `data/ib_data.py` 等模块
统一接口：`fetch_stock_data()`, `fetch_ohlc_batch()`

### 4. 技术指标扩展
在 `strategy/indicators.py` 中添加新指标计算函数

---

## 配置示例

```toml
[monitor]
interval = 10  # 分钟
batch_size = 500
stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]

[strategy]
ma_period = 120
bollinger_period = 20
bollinger_std = 2.0
threshold_large_cap = 0.08    # 8%
threshold_small_cap = 0.20    # 20%
large_cap_market_cap = 300000000000  # 3000亿 USD
risk_reward_ratio = 5.0

[feishu]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/..."
enabled = true

[storage]
db_path = "./data/trading.db"
enable_history = true
history_days = 365
```

---

## 定时任务配置

### Linux/macOS (cron)

每日收盘后（美东时间 16:30，北京时间凌晨 4:30）执行：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 4:30 执行）
30 4 * * * cd /path/to/stock_trade && python -m src.tools.persist_data >> logs/persist.log 2>&1
```

### Windows (Task Scheduler)

1. 打开 "任务计划程序"
2. 创建基本任务
3. 设置触发器：每天凌晨 4:30
4. 操作：启动程序 `python.exe`
5. 参数：`-m src.tools.persist_data`
6. 起始于：`D:\CodeProjectsNew\stock_trade`
7. 勾选"不管用户是否登录都要运行"

### 命令行示例

```bash
# 持久化今天的数据（所有股票）
python -m src.tools.persist_data

# 持久化指定股票
python -m src.tools.persist_data --symbol AAPL

# 持久化指定日期的数据
python -m src.tools.persist_data --date 2026-02-16

# 强制覆盖
python -m src.tools.persist_data --force

# 模拟运行（不写入数据库）
python -m src.tools.persist_data --dry-run

# 补齐缺失日期的数据
python -m src.tools.persist_data --date 2026-02-01 --date 2026-02-17
```

---

## 测试策略

```python
# tests/test_indicators.py
def test_bollinger_bands():
    data = pd.Series([...])
    bands = calculate_bollinger_bands(data)
    assert bands.upper[-1] > bands.middle[-1] > bands.lower[-1]

# tests/test_signals.py
def test_bollinger_breakout_signal():
    data = load_test_data()
    signal = generate_bollinger_breakout_signal(data, config)
    assert signal is not None

# tests/test_screening.py
def test_screen_by_ma_distance():
    data = load_test_data()
    result = screen_by_ma_distance("AAPL", data, 120, 0.08)
    assert isinstance(result, bool)
```

---

## 开发优先级建议

1. **Phase 1 - 基础框架**
   - 配置管理
   - 数据获取和存储
   - 数据持久化工具 (`tools/persist_data.py`)
   - 技术指标计算

2. **Phase 2 - 策略实现**
   - 股票筛选
   - 信号生成
   - 策略基类和实现

3. **Phase 3 - 交易功能**
   - 订单管理
   - 持仓管理

4. **Phase 4 - 通知集成**
   - 飞书通知
   - 消息格式化

5. **Phase 5 - 监控和回测**
   - 信号监控
   - 回测功能
