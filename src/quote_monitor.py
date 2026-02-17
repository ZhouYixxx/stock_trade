import yfinance as yf
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_ohlc_batch(tickers: List[str]) -> Dict[str, Any]:
    """
    Fetch OHLC data for a batch of stocks using yfinance.

    Args:
        tickers: List of stock symbols

    Returns:
        Dictionary mapping ticker to OHLC data
    """
    try:
        # Use Tickers for batch fetching
        ticker_objs = yf.Tickers(tickers)
        result = {}

        for symbol in tickers:
            try:
                ticker = ticker_objs.tickers[symbol]
                # Get the most recent daily OHLC data
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
                    logger.warning(f"⚠ {symbol}: No data available")

            except Exception as e:
                logger.error(f"✗ {symbol}: Error fetching data - {e}")

        return result

    except Exception as e:
        logger.error(f"Batch fetch error: {e}")
        return {}


def split_into_batches(items: List[str], batch_size: int) -> List[List[str]]:
    """Split list into batches of specified size."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def start(config: Dict[str, Any]):
    """
    Start the quote monitoring loop.

    Args:
        config: Configuration dictionary with 'monitor' section containing:
            - interval: polling interval in minutes
            - stocks: list of stock symbols to monitor
    """
    monitor_config = config.get('monitor', {})
    interval_minutes = monitor_config.get('interval', 10)
    stocks = monitor_config.get('stocks', [])
    batch_size = 500

    if not stocks:
        logger.error("No stocks configured in config.toml")
        return

    logger.info(f"Starting quote monitor with {len(stocks)} stocks")
    logger.info(f"Fetching OHLC data every {interval_minutes} minutes")
    logger.info(f"Batch size: {batch_size} stocks per request")

    while True:
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching OHLC data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}\n")

        # Split stocks into batches
        batches = split_into_batches(stocks, batch_size)
        all_data = {}

        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)} ({len(batch)} stocks)")
            batch_data = fetch_ohlc_batch(batch)
            all_data.update(batch_data)

        logger.info(f"\n{'='*60}")
        logger.info(f"Summary: {len(all_data)}/{len(stocks)} stocks fetched successfully")
        logger.info(f"{'='*60}\n")

        # Wait for next interval
        logger.info(f"Waiting {interval_minutes} minutes until next fetch...")
        time.sleep(interval_minutes * 60)
