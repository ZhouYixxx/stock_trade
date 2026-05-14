# region imports
from AlgorithmImports import *
# endregion


class QQQLeapsSma200Ladder(QCAlgorithm):
    """
    策略3：QQQ 买入持有 + LEAPS Call 阶梯抄底 组合策略

    资金分配：
    - 50% 本金期初一次性买入 QQQ 并永久持有（跟踪牛市主升浪）
    - 50% 本金用于 LEAPS Call 阶梯抄底（在回调中获取超额收益）

    LEAPS 阶梯入场逻辑：
    - 阶梯0：QQQ 跌到 SMA200 → 买入
    - 阶梯1：QQQ 跌到 SMA200 × 0.95 → 买入
    - 阶梯2：QQQ 跌到 SMA200 × 0.90 → 买入
    - 以此类推，每 5% 一个阶梯

    当 QQQ 反弹回 SMA200 以上时，所有已触发阶梯重置，下次下跌可重新触发。
    最大持仓 5 张合约，满仓后 FIFO 轮动。
    买入约 2 年到期的 QQQ LEAPS Call（Delta > 0.65）。
    """

    def initialize(self):
        self.set_start_date(2018, 6, 1)
        self.set_end_date(2026, 1, 1)
        self.set_cash(50000)
        self.set_warm_up(200, Resolution.DAILY)

        # --- 策略参数 ---
        self._target_symbol_hold_pct = 0.50         # 期初买入 QQQ 的资金比例
        self._max_contracts = 5           # 最大持仓量
        self._level_step = 0.05           # 阶梯间距 5%
        self._cooldown_days = 14           # 开仓冷静期（天）
        self._hard_stop_loss_pct = -0.50  # 硬止损 -50%

        # --- 状态追踪 ---
        self._target_symbol_holding_established = False  # 是否已建立 QQQ 底仓
        self._last_entry_time = None      # 上一次开仓时间
        self._triggered_levels = set()    # 当前周期已触发的阶梯索引
        self._tracked_contracts = set()   # 当前持有的合约 Symbol
        self._trace = []                  # 日志记录
        self._trade_prices = {}           # 合约成交价格记录

        # Benchmark: 买入持有 QQQ 的收益率对比
        self.set_benchmark("QQQ")

        # Add QQQ equity for signal generation + 底仓持有.
        # self._target_symbol = self.add_equity("QQQ", Resolution.DAILY).symbol
        self._target_symbol = self.add_equity("TSLA", Resolution.DAILY).symbol
        

        # Add QQQ options for LEAPS selection.
        option = self.add_option("QQQ", Resolution.DAILY)
        self._option_symbol = option.symbol
        option.set_filter(self._option_filter)

        # Use SMA200 as the sole reference level.
        self._sma_200 = self.sma(self._target_symbol, 200)

    def _option_filter(self, universe: OptionFilterUniverse) -> OptionFilterUniverse:
        """筛选约 2 年到期的 LEAPS Call，高 Delta。"""
        return (universe
                .strikes(-20, 5).calls_only()
                .expiration(700, 760)
                .delta(0.65, 1.00)
                .include_weeklys())

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        if not self._sma_200.is_ready:
            return

        # --- 期初建立 QQQ 底仓（只执行一次） ---
        if not self._target_symbol_holding_established:
            self.set_holdings(self._target_symbol, self._target_symbol_hold_pct)
            self._target_symbol_holding_established = True
            self._trace_log(
                f"Established QQQ core holding: "
                f"target={self._target_symbol_hold_pct:.0%}, "
                f"portfolio_value={self.portfolio.total_portfolio_value:.2f}"
            )

        # 先处理期权平仓规则
        self._apply_close_rules()

        qqq_bar = data.bars.get(self._target_symbol)
        if not qqq_bar:
            return

        qqq_price = qqq_bar.close
        sma200 = self._sma_200.current.value

        # --- 阶梯重置逻辑 ---
        # QQQ 回到 SMA200 以上时，清空已触发阶梯，下一轮下跌可重新触发
        if qqq_price > sma200:
            if self._triggered_levels:
                self._trace_log(
                    f"QQQ ({qqq_price:.2f}) back above SMA200 ({sma200:.2f}), "
                    f"resetting {len(self._triggered_levels)} triggered levels"
                )
                self._triggered_levels.clear()
            return

        # --- 寻找下一个可触发的阶梯 ---
        # 从最浅的阶梯开始检查，找到第一个价格已到达但尚未触发的阶梯
        level_to_trigger = None
        level_idx = 1
        while True:
            level_price = sma200 * (1 - level_idx * self._level_step)
            if qqq_price <= level_price:
                if level_idx not in self._triggered_levels:
                    level_to_trigger = level_idx
                    break
                level_idx += 1
            else:
                break

        if level_to_trigger is None:
            return

        # --- 冷静期检查 ---
        if self._last_entry_time is not None and self.time < self._last_entry_time + timedelta(days=self._cooldown_days):
            return

        # --- 获取期权链并选择合约（先选再决定是否轮动） ---
        chain = list(self.option_chain(self._target_symbol))
        if not chain:
            self._trace_log(
                f"Signal at level {level_to_trigger} but no QQQ option chain"
            )
            return

        selected_call = self._select_entry_contract(chain)
        if not selected_call:
            self._trace_log(
                f"Signal at level {level_to_trigger} but no eligible options, "
                f"chain_size={len(chain)}"
            )
            return

        # --- 容量管理 ---
        if self._current_contract_count() >= self._max_contracts:
            # 选中的合约已经在持仓中，轮动无意义
            if selected_call.symbol in self._active_contracts():
                self._trace_log(
                    f"Skip rotation: selected {selected_call.symbol} already held"
                )
                return
            if not self._free_capacity_fifo():
                return

        # --- 执行买入 ---
        self.market_order(selected_call.symbol, 1, tag=f"开仓_L{level_to_trigger}")
        self._tracked_contracts.add(selected_call.symbol)
        self._last_entry_time = self.time
        self._triggered_levels.add(level_to_trigger)
        level_price = sma200 * (1 - level_to_trigger * self._level_step)
        self._trace_log(
            f"Bought LEAPS call (L{level_to_trigger}): {selected_call.symbol}, "
            f"QQQ={qqq_price:.2f}, SMA200={sma200:.2f}, "
            f"level_price={level_price:.2f}, dist_from_sma={qqq_price / sma200 - 1:.2%}, "
            f"Delta={selected_call.greeks.delta:.2f}, expire={selected_call.expiry}, "
            f"Ask={self._contract_cost(selected_call):.2f}"
        )

    def on_order_event(self, order_event: OrderEvent):
        symbol = order_event.symbol
        if symbol.security_type != SecurityType.OPTION:
            return

        if order_event.status == OrderStatus.FILLED:
            trade_record = self._trade_prices.setdefault(symbol, {})
            if order_event.fill_quantity > 0:
                trade_record["entry_price"] = order_event.fill_price
                trade_record["last_entry_time"] = self.time
            elif order_event.fill_quantity < 0:
                trade_record["exit_price"] = order_event.fill_price
                trade_record["last_exit_time"] = self.time

        if order_event.status == OrderStatus.FILLED and order_event.fill_quantity < 0:
            holding = self.portfolio[symbol]
            qqq_price = self.securities[self._target_symbol].price
            trade_record = self._trade_prices.get(symbol, {})
            entry_price = trade_record.get("entry_price", holding.average_price)
            exit_price = trade_record.get("exit_price", order_event.fill_price)
            self._trace_log(
                f"Sell filled: {symbol}, QQQ={qqq_price:.2f}, "
                f"entry_price={entry_price:.2f}, exit_price={exit_price:.2f}, "
                f"last_trade_profit={holding.last_trade_profit:.2f}, "
                f"net_profit={holding.net_profit:.2f}"
            )

        if self.portfolio[symbol].invested and self.portfolio[symbol].quantity > 0:
            self._tracked_contracts.add(symbol)
        else:
            self._tracked_contracts.discard(symbol)

    # ------------------------------------------------------------------
    #  平仓规则（比策略1更激进的止盈）
    # ------------------------------------------------------------------
    def _apply_close_rules(self):
        for symbol in list(self._active_contracts()):
            holding = self.portfolio[symbol]
            expiry = symbol.id.date
            days_to_expiry = (expiry.date() - self.time.date()).days
            profit_pct = holding.unrealized_profit_percent
            net_profit = holding.unrealized_profit
            qqq_price = self.securities[self._target_symbol].price
            trade_record = self._trade_prices.get(symbol, {})
            entry_price = trade_record.get("entry_price", holding.average_price)
            estimated_exit_price = holding.price

            # 距到期 < 180 天：强制平仓
            if days_to_expiry < 180:
                self._trace_log(
                    f"Close {symbol}: reason=<6m_to_expiry, QQQ={qqq_price:.2f}, "
                    f"entry={entry_price:.2f}, exit≈{estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}, "
                    f"days_to_expiry={days_to_expiry}"
                )
                self.liquidate(symbol, tag="触发180天强制平仓")
                continue

            # 止盈：距到期 180-240 天，盈利 >= 20%
            if 180 <= days_to_expiry <= 240 and profit_pct >= 0.20:
                self._trace_log(
                    f"Close {symbol}: reason=6_8m_profit_20, QQQ={qqq_price:.2f}, "
                    f"entry={entry_price:.2f}, exit≈{estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发20%止盈")
                continue

            # 止盈：距到期 240-360 天，盈利 >= 50%
            if 240 < days_to_expiry <= 360 and profit_pct >= 0.50:
                self._trace_log(
                    f"Close {symbol}: reason=8_12m_profit_50, QQQ={qqq_price:.2f}, "
                    f"entry={entry_price:.2f}, exit≈{estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发50%止盈")
                continue

            # 止盈：距到期 > 360 天，盈利 >= 100%（翻倍）
            if days_to_expiry > 360 and profit_pct >= 1.00:
                self._trace_log(
                    f"Close {symbol}: reason=profit_target_100, QQQ={qqq_price:.2f}, "
                    f"entry={entry_price:.2f}, exit≈{estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发100%止盈")

    # ------------------------------------------------------------------
    #  FIFO 轮动
    # ------------------------------------------------------------------
    def _free_capacity_fifo(self) -> bool:
        active_symbols = self._active_contracts()
        if not active_symbols:
            return False

        oldest_symbol = min(
            active_symbols,
            key=lambda s: self._trade_prices.get(s, {}).get(
                "last_entry_time", self.time
            )
        )
        entry_time = self._trade_prices.get(oldest_symbol, {}).get(
            "last_entry_time", self.time
        )
        self.market_order(oldest_symbol, -1, tag="仓位轮动")
        self._trace_log(
            f"Trimmed {oldest_symbol} to free capacity (FIFO), "
            f"entry_time={entry_time}"
        )
        return True

    # ------------------------------------------------------------------
    #  合约选择：2 年到期、实值、Delta > 0.65，选最便宜的
    # ------------------------------------------------------------------
    def _select_entry_contract(self, chain):
        underlying_price = self.securities[self._target_symbol].price
        eligible_calls = [
            contract
            for contract in chain
            if contract.right == OptionRight.CALL
            and contract.expiry > self.time + timedelta(days=700)
            and contract.strike < underlying_price
            and contract.greeks.delta is not None
            and contract.greeks.delta > 0.69
        ]

        if not eligible_calls:
            return None

        return min(eligible_calls, key=self._contract_cost)

    def _contract_cost(self, contract) -> float:
        if contract.ask_price and contract.ask_price > 0:
            return contract.ask_price
        if contract.last_price and contract.last_price > 0:
            return contract.last_price
        if contract.bid_price and contract.bid_price > 0:
            return contract.bid_price
        return float("inf")

    # ------------------------------------------------------------------
    #  辅助方法
    # ------------------------------------------------------------------
    def _current_contract_count(self) -> int:
        total = 0
        for symbol in self._active_contracts():
            total += int(abs(self.portfolio[symbol].quantity))
        return total

    def _active_contracts(self) -> list:
        active_symbols = []
        stale_symbols = []
        for symbol in self._tracked_contracts:
            if self.portfolio[symbol].invested and self.portfolio[symbol].quantity > 0:
                active_symbols.append(symbol)
            else:
                stale_symbols.append(symbol)

        for symbol in stale_symbols:
            self._tracked_contracts.discard(symbol)

        return active_symbols

    def _trace_log(self, message: str) -> None:
        line = f"{self.time},{message}"
        self._trace.append(line)
        self.log(line)

    def on_end_of_algorithm(self) -> None:
        key = "qqq_leaps_ladder_trace.csv"
        content = "\n".join(self._trace)
        if self.object_store.save(key, content):
            self.log(f"Saved trace to Object Store: {key}")
        else:
            self.log(f"Failed to save trace to Object Store: {key}")
