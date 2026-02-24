# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

US stock trading application that fetches market data using yfinance and sends notifications via Feishu. Trading is performed at the daily level with manual execution.

## Dependencies

Key Python packages:
- `yfinance` - Fetches US stock market data
- `pandas` - Data manipulation
- `peewee` - ORM for SQLite database
- `aiohttp` - Async HTTP client for notifications
- `websockets` - WebSocket support

Install dependencies:
```bash
pip install -r requirements.txt
```

Or using the virtual environment:
```bash
# Activate venv (Windows)
stock_venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Architecture

The codebase follows a modular design with two distinct execution paths:

1. **Monitor Loop** - Real-time quote monitoring every 10 minutes for signal analysis
2. **Data Persistence** - Independent tool for daily data storage (scheduled via cron/Task Scheduler)

### Key Modules

- `src/main.py` - Entry point (placeholder - not yet implemented)
- `src/config/settings.py` - Configuration management with dataclasses (MonitorConfig, StrategyConfig, FeishuConfig, StorageConfig)
- `src/monitor/quote_monitor.py` - Real-time quote monitoring using background threads
- `src/monitor/signal_monitor.py` - Signal monitoring (placeholder)
- `src/tools/persist_data.py` - Standalone data persistence tool for daily EOD data
- `src/data/db_models.py` - Peewee ORM models (StockData, SignalRecord, OrderRecord, PositionRecord)
- `src/data/db_operations.py` - Database operations (placeholder)
- `src/data/market_data.py` - Market data fetching (placeholder)
- `src/strategy/` - Strategy modules (base.py, indicators.py, signals.py, screening.py - placeholders)
- `src/notification/` - Notification modules (feishu.py, formatter.py - placeholders)
- `src/trading/` - Trading modules (order.py, position.py - placeholders)
- `src/utils/` - Utilities (logging.py, time.py, decorators.py, third_api.py)
- `src/types/common.py` - Type definitions (OHLCData, SignalType, OrderSide, etc.)

### Data Flow

```
config.toml → QuoteMonitor (10-min polling) → yfinance → OHLC Data
                                            ↓
                                    Strategy Analysis
                                            ↓
                                    Feishu Notifications

Independent: persist_data.py (daily EOD, scheduled) → SQLite Database
```

### Important Design Decisions

1. **Monitoring vs Persistence Separation**: Real-time monitoring fetches data for signal analysis only. Historical data persistence is handled by the independent `persist_data.py` tool.
2. **Database**: SQLite with Peewee ORM - stores daily OHLC data and trading records.
3. **Batch Processing**: Quote monitor splits stock lists into batches (configurable batch_size) for API efficiency.
4. **Thread Safety**: QuoteMonitor runs in a daemon background thread with graceful shutdown via Event.

## Running the Application

### Main Application (placeholder)
```bash
python src/main.py
```

### Quote Monitor (Stand-alone)
```python
from src.monitor.quote_monitor import start_quote_monitor

monitor = start_quote_monitor(
    stocks=["AAPL", "MSFT", "GOOGL"],
    interval=10,
    on_data_received=lambda data: print(data)
)
```

### Data Persistence Tool

The persistence tool is designed to run independently via cron or Task Scheduler after market close.

```bash
# Persist today's data (all stocks)
python -m src.tools.persist_data

# Persist specific stock
python -m src.tools.persist_data --symbol AAPL

# Persist specific date
python -m src.tools.persist_data --date 2026-02-16

# Force overwrite existing data
python -m src.tools.persist_data --force

# Dry run (no database writes)
python -m src.tools.persist_data --dry-run
```

## Configuration

Configuration is loaded from `src/config.toml` using Python's built-in `tomllib` module (Python 3.11+).

Current config sections:
- `[monitor]` - interval (minutes), stocks list, batch_size
- Future: `[strategy]`, `[feishu]`, `[storage]` (not yet implemented)

## Database

### Database File
By default: `./data/trading.db` (configurable)

### Models (Peewee)
- `StockData` - Daily OHLC data
- `SignalRecord` - Trading signals
- `OrderRecord` - Orders
- `PositionRecord` - Positions

### Database Initialization
The `persist_data.py` tool handles database initialization via Peewee's `database.create_tables()`.

## Module Import Guidelines

See `src/MODULE_IMPORT_GUIDE.md` for detailed import patterns and common usage examples.

## Scheduled Tasks

### Linux/macOS (cron)
```bash
# Run daily at 4:30 AM (after US market close)
30 4 * * * cd /path/to/stock_trade && python -m src.tools.persist_data >> logs/persist.log 2>&1
```

### Windows (Task Scheduler)
1. Create a basic task triggered daily at 4:30 AM
2. Action: Start program `python.exe`
3. Arguments: `-m src.tools.persist_data`
4. Start in: `D:\CodeProjectsNew\stock_trade`
5. Check "Run whether user is logged on or not"

## Implementation Status

### Implemented (Functional)
- Quote monitor with background threading
- Batch stock fetching with yfinance
- Data persistence tool (single stock)
- Database models (Peewee)
- Configuration dataclasses
- Utility modules (logging, time, decorators)

### Placeholder/Incomplete
- Main application entry point
- Signal generation logic
- Strategy implementations
- Notification (Feishu)
- Trading order/position management
- Database operations wrapper functions
- Market data fetching utilities
