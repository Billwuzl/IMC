import json
from datamodel import Order, ProsperityEncoder, Symbol, TradingState, Trade, OrderDepth
from typing import Dict, List, Any


class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": self.compress_state(state),
            "orders": self.compress_orders(orders),
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

    def compress_state(self, state: TradingState) -> dict[str, Any]:
        listings = []
        for listing in state.listings.values():
            listings.append([listing["symbol"], listing["product"], listing["denomination"]])

        order_depths = {}
        for symbol, order_depth in state.order_depths.items():
            order_depths[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return {
            "t": state.timestamp,
            "l": listings,
            "od": order_depths,
            "ot": self.compress_trades(state.own_trades),
            "mt": self.compress_trades(state.market_trades),
            "p": state.position,
            "o": state.observations,
        }

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.buyer,
                    trade.seller,
                    trade.price,
                    trade.quantity,
                    trade.timestamp,
                ])

        return compressed

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed


logger = Logger()


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():
            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'BERRIES':
                if 'BERRIES' in state.position.keys():
                    position = state.position[product]
                else:
                    position = 0

                order_depth: OrderDepth = state.order_depths[product]
                # buy berries from time 100K to 200K
                if len(order_depth.sell_orders) > 0 and 100000 < state.timestamp < 200000:
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = min(-order_depth.sell_orders[best_ask], 250 - position)
                    print("BUY", str(-best_ask_volume) + "x", best_ask)
                    result[product] = [Order(product, best_ask, best_ask_volume)]

                # sell berries from time 450K to 550K
                if len(order_depth.buy_orders) > 0 and 450000 < state.timestamp < 550000:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = min(order_depth.buy_orders[best_bid],  250 + position)
                    print("SELL", str(best_bid_volume) + "x", best_bid)
                    result[product] = [Order(product, best_bid, - best_bid_volume)]
        logger.flush(state, result)
        return result
