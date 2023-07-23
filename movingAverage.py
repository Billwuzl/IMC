# Changed
import json
from datamodel import Order, ProsperityEncoder, Symbol, TradingState
from typing import Dict, List, Any

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()

class Trader:

    def __init__(self):
        self.symbol = 'PEARLS'
        self.ma1_period = 1000  # short-term moving average period
        self.ma2_period = 3000  # long-term moving average period

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}

        for product in state.order_depths.keys():
            self.symbol = product

            # Retrieve historical price data for the selected symbol

            trades = state.market_trades[self.symbol]
            if len(trades) >= self.ma2_period + 1:
                trades = state.market_trades[self.symbol][-self.ma2_period - 1:]
                prices = [trade.price for trade in trades]

                # Compute the short-term moving average (MA1) and the long-term moving average (MA2) using the historical data
                ma1 = sum(prices[-self.ma1_period:]) / self.ma1_period
                ma2 = sum(prices[-self.ma2_period:]) / self.ma2_period
                ma1_prev = sum(prices[(-self.ma1_period - 1):-1]) / self.ma1_period
                ma2_prev = sum(prices[(-self.ma2_period - 1):-1]) / self.ma2_period

                # Determine the current position in the market (long or short) based on the relationship between MA1 and MA2
                position_prev = None
                if ma1_prev > ma2_prev:
                    position_prev = 'long'
                elif ma1_prev < ma2_prev:
                    position_prev = 'short'
                if (ma1 <= ma2 and position_prev == 'long') or (ma1 >= ma2 and position_prev == 'short'):
                    position = 'trade'

                # Generate orders to enter or exit positions based on the current position and the trading rules
                order_depth = state.order_depths[self.symbol]
                if position_prev == 'long' and position == 'trade':
                    # If the current position is long, we want to buy if there are more sell orders than buy orders at the best ask
                    best_ask = min(order_depth.sell_orders.keys())
                    volume = - 20 - self.position[product]
                    orders = [Order(self.symbol, best_ask, volume)]
                    result[self.symbol] = orders
                elif position_prev == 'short' and position == 'trade':
                    # If the current position is short, we want to sell if there are more buy orders than sell orders at the best bid
                    best_bid = max(order_depth.buy_orders.keys())
                    volume = 20 - self.position[product]
                    orders = [Order(self.symbol, best_bid, volume)]
                    result[self.symbol] = orders

        logger.flush(state, result)
        return result
