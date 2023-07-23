import json
from datamodel import Order, ProsperityEncoder, Symbol, TradingState, Trade
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
        result = {}

        if (
                ('COCONUTS' in state.order_depths.keys()) and
                ('PINA_COLADAS' in state.order_depths.keys())
        ):

            coco_order_depth = state.order_depths['COCONUTS']
            pc_order_depth = state.order_depths['PINA_COLADAS']

            if 'COCONUTS' in state.position.keys():
                coco_position = state.position['COCONUTS']
            else:
                coco_position = 0

            if 'PINA_COLADAS' in state.position.keys():
                pc_position = state.position['PINA_COLADAS']
            else:
                pc_position = 0

            coco_max_position = 600
            pc_max_position = 300

            # coco_acceptable_price = 8000
            # pc_acceptable_price = 15000

            if (len(coco_order_depth.sell_orders) > 0 and
                len(coco_order_depth.buy_orders) > 0 and
                len(pc_order_depth.sell_orders) > 0 and
                len(pc_order_depth.buy_orders) > 0):

                coco_best_ask = min(coco_order_depth.sell_orders.keys())
                coco_best_bid = max(coco_order_depth.buy_orders.keys())
                pc_best_ask = min(pc_order_depth.sell_orders.keys())
                pc_best_bid = max(pc_order_depth.buy_orders.keys())
                coco_mid_price = (coco_best_ask + coco_best_bid) / 2
                pc_mid_price = (pc_best_ask + pc_best_bid) / 2

                # use fading to determine the fair price
                coco_fair_price = (coco_mid_price + pc_mid_price / 15 * 8) / 2
                pc_fair_price = (pc_mid_price + coco_mid_price * 15 / 8) / 2

                # sell coco if above the fair price
                if coco_best_bid > coco_fair_price+5:
                    # obtain the max number of coco that can be sold given the max position
                    volume_max = (coco_max_position + coco_position)*min(1,(coco_best_bid-coco_fair_price)/50) //1
                    coco_sell_quantity = min(volume_max, coco_order_depth.buy_orders[coco_best_bid])
                    result['COCONUTS'] = [Order('COCONUTS', coco_best_bid, - coco_sell_quantity)]

                if coco_best_ask < coco_fair_price-5:
                    # obtain the max number of coco that can be bought given the max position
                    volume_max = (coco_max_position - coco_position)*min(1,(coco_fair_price-coco_best_ask)/50) //1
                    coco_buy_quantity = min(volume_max, - coco_order_depth.sell_orders[coco_best_ask])
                    result['COCONUTS'] = [Order('COCONUTS', coco_best_ask, coco_buy_quantity)]

                if pc_best_bid > pc_fair_price+5:
                    # obtain the max number of pc that can be sold given the max position
                    volume_max = (pc_max_position + pc_position)*min(1,(pc_best_bid-pc_fair_price)/94) //1
                    pc_sell_quantity = min(volume_max, pc_order_depth.buy_orders[pc_best_bid])
                    result['PINA_COLADAS'] = [Order('PINA_COLADAS', pc_best_bid, - pc_sell_quantity)]

                if pc_best_ask < pc_fair_price-5:
                    # obtain the max number of pc that can be bought given the max position
                    volume_max = (pc_max_position - pc_position)*min(1,(pc_fair_price-pc_best_ask)/94) //1
                    pc_buy_quantity = min(volume_max, - pc_order_depth.sell_orders[pc_best_ask])
                    result['PINA_COLADAS'] = [Order('PINA_COLADAS', pc_best_ask, pc_buy_quantity)]

        logger.flush(state, result)
        return result