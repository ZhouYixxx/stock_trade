# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

US stock trading application that fetches market data using yfinance and sends notifications via Feishu. Trading is performed at the daily level with manual execution.

## Dependencies

Key Python packages:
- `yfinance` - Fetches US stock market data
- `pandas` - Data manipulation
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

Simple entry-point architecture:

```
main.py
    └── loads config.toml
    └── calls quote_monitor.start(config)
```

- `src/main.py` - Entry point that loads TOML configuration and starts the quote monitor
- `src/quote_monitor.py` - Quote monitoring module (currently under development)
- `src/utils.py` - Utility functions (currently under development)
- `src/config.toml` - Configuration file

## Running the Application

```bash
python src/main.py
```

## Configuration

Configuration is loaded from `src/config.toml` using Python's built-in `tomllib` module (Python 3.11+).
