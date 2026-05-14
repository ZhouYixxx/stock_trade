# region imports
from AlgorithmImports import *
# endregion

class QQQLeapsDemo(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2019, 1, 1)
        self.set_end_date(2026, 1, 1)
        self.set_cash(50000)
        self.set_warm_up(200, Resolution.DAILY)

        self._cooldown_days = 7 # 合约冷静期
        self._max_contracts = 5 # 最大持仓量
        self._entry_rsi_threshold = 35
        self._daily_drop_threshold = -0.01
        self._hard_stop_loss_pct = -0.50
        self._last_entry_time = None
        self._tracked_contracts = set()
        self._trace = []
        self._trade_prices = {}

        # Add QQQ equity for signal generation.
        self._qqq = self.add_equity("QQQ", Resolution.DAILY).symbol

        # Add QQQ options for LEAPS selection.
        option = self.add_option("QQQ", Resolution.DAILY)
        self._option_symbol = option.symbol
        option.set_filter(self._option_filter)

        # Use QQQ RSI as the only timing signal.
        self._rsi = self.rsi(self._qqq, 14)
        self._sma_200 = self.sma(self._qqq, 200)

    def _option_filter(self, universe: OptionFilterUniverse) -> OptionFilterUniverse:
        """Filter for long-dated call candidates with high delta."""
        return (universe
                .strikes(-20, 5).calls_only()
                .expiration(330, 400)
                .delta(0.65, 1.00)
                .include_weeklys())

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        if not self._rsi.is_ready or not self._sma_200.is_ready:
            return

        self._apply_close_rules()

        qqq_bar = data.bars.get(self._qqq)
        if not qqq_bar:
            return

        if not self._should_enter(qqq_bar):
            return

        if self._in_cooldown():
            return

        self._trace_log(f"Signal triggered: date={self.time.date()}")
        capacity_freed = False
        if self._current_contract_count() >= self._max_contracts:
            capacity_freed = self._free_capacity_fifo()
            if not capacity_freed:
                return

        chain = list(self.option_chain(self._qqq))
        if not chain:
            self._trace_log("Signal triggered but no daily QQQ option chain")
            return

        selected_call = self._select_entry_contract(chain)
        if not selected_call:
            self._trace_log(
                f"Signal triggered but no eligable options found, chain_size={len(chain)}"
            )
            return

        if not capacity_freed and self._current_contract_count() >= self._max_contracts:
            self._trace_log("Signal triggered but exceed holdings limit")
            return

        self.market_order(selected_call.symbol, 1, tag="开仓")
        self._tracked_contracts.add(selected_call.symbol)
        self._last_entry_time = self.time
        self._trace_log(
            f"Bought LEAPS call: {selected_call.symbol}, RSI={self._rsi.current.value:.2f}, "
            f"QQQ={qqq_bar.price:.2f}, SMA200={self._sma_200.current.value:.2f} "
            f"DayMove={self._daily_return(qqq_bar):.2%}, Delta={selected_call.greeks.delta:.2f}, expire = {selected_call.expiry} "
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
            qqq_price = self.securities[self._qqq].price
            trade_record = self._trade_prices.get(symbol, {})
            entry_price = trade_record.get("entry_price", holding.average_price)
            exit_price = trade_record.get("exit_price", order_event.fill_price)
            self._trace_log(
                f"Sell filled: {symbol}, QQQ={qqq_price:.2f}, "
                f"entry_price={entry_price:.2f}, exit_price={exit_price:.2f}, "
                f"last_trade_profit={holding.last_trade_profit:.2f}, net_profit={holding.net_profit:.2f}"
            )

        if self.portfolio[symbol].invested and self.portfolio[symbol].quantity > 0:
            self._tracked_contracts.add(symbol)
        else:
            self._tracked_contracts.discard(symbol)



    def _should_enter(self, qqq_bar: TradeBar) -> bool:
        return (
            # qqq_bar.close > self._sma_200.current.value
            #and
            self._rsi.current.value < self._entry_rsi_threshold
            and self._daily_return(qqq_bar) <= self._daily_drop_threshold
        )

    def _daily_return(self, qqq_bar: TradeBar) -> float:
        if qqq_bar.open == 0:
            return 0
        return (qqq_bar.close / qqq_bar.open ) - 1

    def _in_cooldown(self) -> bool:
        return (
            self._last_entry_time is not None
            and self.time < self._last_entry_time + timedelta(days=self._cooldown_days)
        )

    def _current_contract_count(self) -> int:
        total:int = 0
        for symbol in self._active_contracts():
          qty = self.portfolio[symbol].quantity
          total += int(abs(qty))
        return total
    

    def _active_contracts(self) -> list[Symbol]:
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
        
        
    def _apply_close_rules(self):
        for symbol in list(self._active_contracts()):
            holding = self.portfolio[symbol]
            expiry = symbol.id.date
            days_to_expiry = (expiry.date() - self.time.date()).days
            profit_pct = holding.unrealized_profit_percent
            net_profit = holding.unrealized_profit
            qqq_price = self.securities[self._qqq].price
            trade_record = self._trade_prices.get(symbol, {})
            entry_price = trade_record.get("entry_price", holding.average_price)
            estimated_exit_price = holding.price
            if profit_pct <= self._hard_stop_loss_pct and days_to_expiry < 180:
                self._trace_log(
                    f"Close signal {symbol}: reason=hard_stop_loss_50, QQQ={qqq_price:.2f}, "
                    f"SMA200={self._sma_200.current.value:.2f}, entry_price={entry_price:.2f}, "
                    f"est_exit_price={estimated_exit_price:.2f}, PnL={profit_pct:.2%}, "
                    f"profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发止损")
                continue

            if days_to_expiry < 90:
                self._trace_log(
                    f"Close signal {symbol}: reason=<3m_to_expiry, QQQ={qqq_price:.2f}, "
                    f"entry_price={entry_price:.2f}, est_exit_price={estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发90天强制平仓")
                continue

            if profit_pct >= 0.5:
                self._trace_log(
                    f"Close signal {symbol}: reason=profit_target_50, QQQ={qqq_price:.2f}, "
                    f"entry_price={entry_price:.2f}, est_exit_price={estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发50%止盈")
                continue

            if 180 <= days_to_expiry <= 240 and profit_pct >= 0.30:
                self._trace_log(
                    f"Close signal {symbol}: reason=6_9m_profit_30, QQQ={qqq_price:.2f}, "
                    f"entry_price={entry_price:.2f}, est_exit_price={estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发30%止盈")
                continue

            if 90 <= days_to_expiry < 180 and profit_pct >= 0.10:
                self._trace_log(
                    f"Close signal {symbol}: reason=3_6m_profit_10, QQQ={qqq_price:.2f}, "
                    f"entry_price={entry_price:.2f}, est_exit_price={estimated_exit_price:.2f}, "
                    f"PnL={profit_pct:.2%}, profit={net_profit:.2f}"
                )
                self.liquidate(symbol, tag="触发10%止盈")

    def _free_capacity_fifo(self) -> bool:
        active_symbols = self._active_contracts()
        if not active_symbols:
            return False

        oldest_symbol = min(
            active_symbols,
            key=lambda symbol: self._trade_prices.get(symbol, {}).get(
                "last_entry_time", self.time
            )
        )

        entry_time = self._trade_prices.get(oldest_symbol, {}).get(
            "last_entry_time", self.time
        )
        self.market_order(oldest_symbol, -1, tag="仓位轮动")
        self._trace_log(
            f"Trimmed {oldest_symbol} to free capacity using FIFO, "
            f"entry_time={entry_time}"
        )
        return True

    def _select_entry_contract(self, chain):
        underlying_price = self.securities[self._qqq].price
        eligible_calls = [
            contract
            for contract in chain
            if contract.right == OptionRight.CALL
            and contract.expiry > self.time + timedelta(days=450)
            and contract.strike < underlying_price
            and contract.greeks.delta is not None
            and contract.greeks.delta > 0.65
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

    def _trace_log(self, message: str) -> None:
        line = f"{self.time},{message}"
        self._trace.append(line)
        self.log(line)

    def on_end_of_algorithm(self) -> None:
        key = f"qqq_leaps_trace.csv"
        content = "\n".join(self._trace)
        if self.object_store.save(key, content):
            self.log(f"Saved trace to Object Store: {key}")
        else:
            self.log(f"Failed to save trace to Object Store: {key}")
