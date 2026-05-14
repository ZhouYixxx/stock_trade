# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

US stock trading application that fetches market data using yfinance and sends notifications via Feishu. Daily-level trading with manual execution. Written in Python 3.11+ (uses `tomllib`). Code comments and log messages are in Chinese.

## Common Commands

```bash
# Activate virtual environment (Windows)
stock_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run data persistence tool (main operational command)
python -m src.tools.persist_data --startdate 20260501 --enddate 20260506

# Run quote monitor example
python src/example_usage.py

# Debug configurations exist in .vscode/launch.json for:
#   - src.utils.third_api
#   - src.tools.persist_data
```

No test framework is configured. No build system (`pyproject.toml`, `Makefile`, etc.).

## Architecture

Two independent execution paths that share the database but never interact at runtime:

**1. Monitor Loop** (`src/monitor/quote_monitor.py`) — daemon background thread polls yfinance every N minutes for real-time OHLC data. Uses callback pattern (`add_callback('on_data_received', func)`) for extensibility. Stocks are fetched in configurable batch sizes.

**2. Data Persistence** (`src/tools/persist_data.py`) — standalone CLI tool for daily EOD data. Scheduled via cron/Task Scheduler after market close. Fetches NASDAQ-100 + S&P 500 constituents via `src/utils/third_api.py`, downloads in batches of 20 with 5-second delays, saves to SQLite.

```
config.toml → QuoteMonitor (polling) → yfinance → OHLC Data → callbacks
                                                                      ↓
                                                              Strategy Analysis (not yet built)
                                                                      ↓
                                                              Feishu Notifications (not yet built)

Independent: persist_data.py (daily EOD) → yfinance → SQLite Database
                                                   ↑
                                      third_api.py (NASDAQ-100, S&P 500 constituents)
```

## Key Design Patterns

- **Relative imports everywhere** — all modules use `from ..types.common import OHLCData` style. Must run as package (`python -m src.tools.persist_data`), never as standalone scripts.
- **Deferred database** — `db_models.py` creates `SqliteDatabase(None)`, then `db_operations.init_database(db_path)` calls `database.init()` at runtime. All four models share one `database` instance via `BaseModel.Meta.database`.
- **Type system** — `src/types/common.py` defines `TypedDict` structs (`OHLCData`, `TradingSignal`, `Order`, `Position`) and `Literal` enum-like types. These are the canonical data structures used across all modules.
- **Configuration** — TOML loaded via `tomllib` into dataclasses (`MonitorConfig`, `StrategyConfig`, `FeishuConfig`, `StorageConfig`). Path in `src/config/config.toml`. `get_storage_config()` resolves `db_path` relative to the project root.
- **Logging** — custom `setup_logger()` in `src/utils/logging.py` with console + optional file handler (supports `TimedRotatingFileHandler`). Do not use Python's root logger.

## Implementation Status

### Fully Implemented
| Module | File | What it does |
|--------|------|-------------|
| Config loading | `src/config/settings.py` | `load_config()`, `get_storage_config()` |
| Quote monitoring | `src/monitor/quote_monitor.py` | Background thread, yfinance batch fetch, callback system |
| Database models | `src/data/db_models.py` | Peewee ORM: StockData, SignalRecord, OrderRecord, PositionRecord |
| Database operations | `src/data/db_operations.py` | Full CRUD for all 4 tables, bulk DataFrame insert |
| Data persistence | `src/tools/persist_data.py` | CLI tool: batch EOD download, trading day detection |
| Type definitions | `src/types/common.py` | TypedDicts and Literal types |
| Logging | `src/utils/logging.py` | Logger setup, structured log helpers |
| Third-party APIs | `src/utils/third_api.py` | NASDAQ-100/S&P 500 constituent scrapers, trading day check |

### Placeholder (all function bodies are `pass`)
`src/main.py`, `src/monitor/signal_monitor.py`, `src/data/market_data.py`, `src/strategy/*`, `src/notification/*`, `src/trading/*`, `src/utils/time.py`, `src/utils/decorators.py`

Note: `src/tools/persist_data_example.py` is a non-functional design reference that imports nonexistent function names — do not use it.

## Database

SQLite at `./data/stocks.db` (configurable in `config.toml` `[storage]` section).

Tables: `StockData` (unique index on symbol+date), `SignalRecord`, `OrderRecord`, `PositionRecord`.

Database and `./data/` directory are auto-created by `persist_data.py` on first run.

## Persist Data CLI

```bash
# Batch download for date range (no args = all stocks, recent trading day)
python -m src.tools.persist_data

# Specific stock
python -m src.tools.persist_data --symbol AAPL

# Date range (YYYYMMDD format)
python -m src.tools.persist_data --startdate 20260501 --enddate 20260506
```

## Known Issues

- `pandas_market_calendars` is used in `src/utils/third_api.py` but not listed in `requirements.txt` — install manually if needed.
- `third_api.is_trading_day()` returns a `DatetimeIndex`, not a `bool`. It works as truthy/falsy in conditions but is semantically incorrect.
- `persist_data_example.py` imports `save_stock_history_data` which does not exist — the actual function is `save_stocks_data` in `db_operations.py`.
