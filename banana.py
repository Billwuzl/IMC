import json
from datamodel import Order, ProsperityEncoder, Symbol, TradingState, OrderDepth
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
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        result = {}

        for product in state.order_depths.keys():
            if product == 'BANANAS':
                if 'BANANAS' in state.position.keys():
                    position = state.position['BANANAS']
                else:
                    position = 0

                order_depth: OrderDepth = state.order_depths['BANANAS']

                orders: list[Order] = []

                if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                    best_ask = min(order_depth.sell_orders.keys())
                    best_bid = max(order_depth.buy_orders.keys())
                    mid_price = (best_ask + best_bid) / 2
                    spread = best_ask - best_bid
                    if spread < 3:
                        if len(order_depth.buy_orders.keys()) > 1:
                            bid2 = max([x for x in order_depth.buy_orders.keys() if x < best_bid])
                            if best_bid - bid2 > 2:
                                # weighted average of bid1 and bid2
                                # acceptable_price = (best_bid * order_depth.buy_orders[best_bid] + bid2 * order_depth.buy_orders[bid2]) / (order_depth.buy_orders[best_bid] + order_depth.buy_orders[bid2])
                                # acceptable_price = (acceptable_price + best_ask) // 2
                                # if best_bid > acceptable_price:
                                best_bid_volume = min(order_depth.buy_orders[best_bid], 20 + position)
                                orders.append(Order(product, best_bid, -best_bid_volume))

                        if len(order_depth.sell_orders.keys()) > 1:
                            ask2 = min([x for x in order_depth.sell_orders.keys() if x > best_ask])
                            if ask2 - best_ask > 2:
                                # weighted average of ask1 and ask2
                                # acceptable_price = (best_ask * order_depth.sell_orders[best_ask] + ask2 * order_depth.sell_orders[ask2]) / (order_depth.sell_orders[best_ask] + order_depth.sell_orders[ask2])
                                # acceptable_price = (acceptable_price + best_bid) // 2
                                # if best_ask < acceptable_price:
                                best_ask_volume = min(-order_depth.sell_orders[best_ask], 20 - position)
                                # we buy
                                orders.append(Order(product, best_ask, best_ask_volume))
                result[product] = orders
        logger.flush(state, result)
        return result