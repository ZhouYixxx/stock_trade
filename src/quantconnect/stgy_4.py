# region imports
from AlgorithmImports import *
# endregion


# S&P 100 成分股（剔除部分非美股/特殊标的后的约 100 只）
_SP100_TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "NVDA", "TSLA", "BRK.B", "UNH",
    "JPM", "XOM", "JNJ", "V", "PG", "MA", "HD", "COST", "ABBV", "CVX",
    "MRK", "AVGO", "PEP", "KO", "ADBE", "WMT", "CSCO", "MCD", "CRM", "AMD",
    "NFLX", "TMO", "ABT", "ACN", "INTC", "CMCSA", "ORCL", "NKE", "DHR", "VZ",
    "WFC", "TXN", "PM", "BMY", "UPS", "QCOM", "RTX", "LOW", "NEE", "LIN",
    "LLY", "HON", "SPGI", "AXP", "INTU", "GS", "CAT", "AMGN", "BLK", "DE",
    "ISRG", "SYK", "BKNG", "MDLZ", "NOW", "ADI", "BSX", "BA", "MMC", "CVS",
    "PLD", "CB", "AMT", "ELV", "MDT", "REGN", "VRTX", "TJX", "PGR", "CI",
    "LRCX", "PYPL", "SO", "EQIX", "CL", "MU", "CME", "NOC", "MO", "EOG",
    "ICE", "FCX", "PNC", "TGT", "MS", "CSX", "EMR", "ITW", "SHW", "SLB",
]


class SP100LeapsSignalMonitor(QCAlgorithm):
    """
    策略4：S&P 100 成分股 SMA200 阶梯信号监控（纯信号、无交易）

    核心逻辑（与 stgy_3 的阶梯检测一致）：
    - 为每只 SP100 成分股维护独立的 SMA200 指标和阶梯状态
    - 价格 > SMA200 → 重置该股票的 triggered_levels
    - 价格 <= SMA200 → 从阶梯1开始扫描，找第一个已到达但未触发的阶梯
    - 每只股票有独立的冷静期

    检测到信号后：
    - 记录日志
    - 发送 Webhook 通知（不做任何交易）
    """

    def initialize(self):
        self.set_start_date(2024, 1, 1)
        # Live Trading 模式：不设置 set_end_date
        self.set_cash(10000)
        self.set_warm_up(200, Resolution.DAILY)

        # --- 策略参数 ---
        self._level_step = 0.05           # 阶梯间距 5%
        self._cooldown_days = 14          # 冷静期（天）
        self._max_level = 10              # 最大阶梯深度（SMA200 × 0.5）

        # --- Webhook 配置 ---
        self._webhook_url = self.get_parameter(
            "webhook_url",
            "https://hooks.example.com/placeholder"
        )

        # --- Per-stock 状态 ---
        # { ticker: { "symbol": Symbol, "sma200": Indicator,
        #             "triggered_levels": set, "last_signal_time": datetime } }
        self._stock_state = {}

        # --- 日志 ---
        self._trace = []

        # 订阅所有 SP100 成分股的 DAILY 数据 + SMA200 指标
        for ticker in _SP100_TICKERS:
            try:
                equity = self.add_equity(ticker, Resolution.DAILY)
                sma200 = self.sma(equity.symbol, 200)
                self._stock_state[ticker] = {
                    "symbol": equity.symbol,
                    "sma200": sma200,
                    "triggered_levels": set(),
                    "last_signal_time": None,
                }
            except Exception as e:
                self._trace_log(f"Failed to subscribe {ticker}: {e}")

        self._trace_log(
            f"Initialized with {len(self._stock_state)} stocks, "
            f"level_step={self._level_step}, cooldown={self._cooldown_days}d"
        )

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        # 遍历每只股票，独立检测信号
        for ticker, state in self._stock_state.items():
            symbol = state["symbol"]
            sma200 = state["sma200"]

            if not sma200.is_ready:
                continue

            bar = data.bars.get(symbol)
            if not bar:
                continue

            price = bar.close
            sma200_val = sma200.current.value

            # --- 阶梯重置：价格回到 SMA200 以上 ---
            if price > sma200_val:
                if state["triggered_levels"]:
                    self._trace_log(
                        f"[{ticker}] Price ({price:.2f}) back above SMA200 ({sma200_val:.2f}), "
                        f"resetting {len(state['triggered_levels'])} triggered levels"
                    )
                    state["triggered_levels"].clear()
                continue

            # --- 寻找下一个可触发的阶梯 ---
            level_to_trigger = self._find_next_level(price, sma200_val, state["triggered_levels"])
            if level_to_trigger is None:
                continue

            # --- 冷静期检查（per-stock） ---
            if state["last_signal_time"] is not None:
                if self.time < state["last_signal_time"] + timedelta(days=self._cooldown_days):
                    continue

            # --- 触发信号 ---
            level_price = sma200_val * (1 - level_to_trigger * self._level_step)
            distance_pct = price / sma200_val - 1

            state["triggered_levels"].add(level_to_trigger)
            state["last_signal_time"] = self.time

            self._trace_log(
                f"[SIGNAL] [{ticker}] Level {level_to_trigger}: "
                f"price={price:.2f}, SMA200={sma200_val:.2f}, "
                f"level_price={level_price:.2f}, dist={distance_pct:.2%}"
            )

            # --- 发送 Webhook ---
            self._send_webhook(ticker, level_to_trigger, price, sma200_val, distance_pct, level_price)

    def _find_next_level(self, price: float, sma200_val: float, triggered_levels: set) -> int | None:
        """
        从阶梯1开始扫描，找第一个价格已到达但尚未触发的阶梯。
        与 stgy_3 的逻辑完全一致。
        """
        level_idx = 1
        while level_idx <= self._max_level:
            level_price = sma200_val * (1 - level_idx * self._level_step)
            if price <= level_price:
                if level_idx not in triggered_levels:
                    return level_idx
                level_idx += 1
            else:
                break
        return None

    def _send_webhook(self, ticker: str, level: int, price: float,
                      sma200: float, distance_pct: float, level_price: float) -> None:
        """发送 Webhook 通知。"""
        payload = {
            "ticker": ticker,
            "level": level,
            "price": round(price, 2),
            "sma200": round(sma200, 2),
            "distance_pct": round(distance_pct * 100, 2),
            "level_price": round(level_price, 2),
            "timestamp": str(self.time),
        }

        try:
            self.notify.web(self._webhook_url, payload)
            self._trace_log(f"[WEBHOOK] Sent signal for {ticker} L{level}")
        except Exception as e:
            self._trace_log(f"[WEBHOOK] Failed for {ticker}: {e}")

    # ------------------------------------------------------------------
    #  辅助方法
    # ------------------------------------------------------------------
    def _trace_log(self, message: str) -> None:
        line = f"{self.time},{message}"
        self._trace.append(line)
        self.log(line)

    def on_end_of_algorithm(self) -> None:
        key = "sp100_signal_monitor_trace.csv"
        content = "\n".join(self._trace)
        if self.object_store.save(key, content):
            self.log(f"Saved trace to Object Store: {key}")
        else:
            self.log(f"Failed to save trace to Object Store: {key}")
