# region imports
from AlgorithmImports import *
# endregion

class QQQBuyAndHold(QCAlgorithm):

    def initialize(self):
        # 设置与你期权策略一致的时间范围和初始资金，以便公平对比
        self.set_start_date(2020, 9, 1)
        self.set_end_date(2026, 1, 1)
        self.set_cash(50000)

        # 添加 QQQ 股票
        self._qqq = self.add_equity("QQQ", Resolution.DAILY).symbol
        
        # 记录初始买入状态
        self._is_invested = False

    def on_data(self, data: Slice):
        # 只需要在有数据的第一天买入一次
        if not self._is_invested:
            if data.bars.contains_key(self._qqq):
                # 将 100% 的购买力分配给 QQQ
                self.set_holdings(self._qqq, 1.0)
                
                self._is_invested = True
                self.log(f"已执行全仓买入 QQQ: 价格={data.bars[self._qqq].price}")

    def on_end_of_algorithm(self):
        # 输出最终表现，方便你在日志里直接看结果
        self.log(f"最终账户净值: {self.portfolio.total_portfolio_value}")
        self.log(f"总收益率: {self.portfolio.total_profit / 50000:.2%}")