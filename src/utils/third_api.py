"""
外部的一些公共API调用
"""
import traceback
import requests
import pandas as pd
from io import StringIO
from typing import List, Dict, Any
import pandas_market_calendars as mcal
from . import logging

nyse = mcal.get_calendar("NYSE")
logger = logging.get_logger(__name__)

def is_trading_day(date_str: str) -> bool:
    return nyse.valid_days(start_date=date_str, end_date=date_str)


def get_nasdaq_companies() -> List[str]:
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(
            "https://api.nasdaq.com/api/quote/list-type/nasdaq100",
            headers=headers,
            timeout=30
        )
        res.raise_for_status()

        data = res.json()
        main_data = data['data']['data']['rows']

        # 提取股票代码
        symbols = []
        for row in main_data:
            symbol = row.get('symbol')
            if symbol:
                symbols.append(symbol)

        print(f"获取到 {len(symbols)} 只 NASDAQ-100 成分股")
        return symbols

    except requests.exceptions.RequestException as e:
        print(f"获取 NASDAQ-100 失败: {e}")
        return []


def get_sp500_companies() -> List[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]

        # 查找 Ticker 列
        ticker_column = None
        for col in ['Ticker', 'Symbol', 'TICKER', 'SYMBOL']:
            if col in df.columns:
                ticker_column = col
                break
        if ticker_column is None:
            print(f"可用列: {df.columns.tolist()}")
            raise ValueError("无法找到 Ticker 列")
        
        symbols = df[ticker_column].tolist()
        symbols = [s for s in symbols if s and s != '-']

        print(f"获取到 {len(symbols)} 只 S&P 500 成分股")

        return symbols

    except Exception as e:
        logger.error(f"获取 S&P 500 失败: {traceback.format_exc()}")
        return []




if __name__ == '__main__':
    # 测试：获取 NASDAQ-100
    print("=" * 70)
    print("测试：获取 NASDAQ-100 成分股")
    print("=" * 70)

    nasdaq100 = get_nasdaq_companies()
    print(f"\n前 10 只股票: {nasdaq100[:10]}")

    # 测试：获取 S&P 500
    print("\n" + "=" * 70)
    print("测试：获取 S&P 500 成分股")
    print("=" * 70)

    sp500 = get_sp500_companies()
    print(f"\n前 10 只股票: {sp500[:10]}")
