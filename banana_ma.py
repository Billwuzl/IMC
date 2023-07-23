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

    def __init__(self) -> None:
        self.banana = []

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        if 'BANANAS' in state.order_depths.keys():
            short_period = 5
            long_period = 30

            if 'BANANAS' in state.position.keys():
                position = state.position['BANANAS']
            else:
                position = 0
            
            order_depth: OrderDepth = state.order_depths['BANANAS']

        if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
            best_bid = max(order_depth.buy_orders.keys())
            self.banana.append((best_ask+best_bid)/2)
            if len(self.banana) > 35:
                self.banana = self.banana[1:]
        
        if len(self.banana) > 32:

            ma_short = sum(self.banana[-5:])/5
            ma_short_prev = sum(self.banana[-30:])/30
            ma_long = sum(self.banana[-6:-1])/5
            ma_long_prev = sum(self.banana[-31:-1])/30


            if ma_short_prev < ma_long_prev and ma_short > ma_long:
                volume_max = 20 - position
                result['BANANAS'] = [Order('BANANAS',best_ask,volume_max)]
            if ma_short_prev > ma_long_prev and ma_short < ma_long:
                volume_max = - 20 - position
                result['BANANAS'] = [Order('BANANAS',best_bid,volume_max)]
            

        

        logger.flush(state, result)
        return result