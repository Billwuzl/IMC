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
        # Initialize the method output dict as an empty dict
        result = {}

        # Round 1 code starts here
        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                if 'PEARLS' in state.position.keys():
                    position = state.position[product]
                else:
                    position = 0

                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 10000

                if len(order_depth.sell_orders) > 0:

                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = min(order_depth.sell_orders[best_ask], 20 - position)

                    # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < acceptable_price:
                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))

                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = max(order_depth.buy_orders[best_bid], -20 - position)
                    if best_bid > acceptable_price:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))
                # Add all the above the orders to the result dict
                result[product] = orders
                orders = []
                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above

        # Round 4 code starts here
        if (
                ('BAGUETTE' in state.order_depths.keys()) and
                ('DIP' in state.order_depths.keys()) and
                ('UKULELE' in state.order_depths.keys()) and
                ('PICNIC_BASKET' in state.order_depths.keys())
        ):
            BAG_order_depth = state.order_depths['BAGUETTE']
            DIP_order_depth = state.order_depths['DIP']
            UKU_order_depth = state.order_depths['UKULELE']
            PIC_order_depth = state.order_depths['PICNIC_BASKET']
            if 'PICNIC_BASKET' in state.position.keys():
                pic_position = state.position['PICNIC_BASKET']
            else:
                pic_position = 0

            acceptable_price = 400

            # sell basket when basket price > 400
            if (
                    (len(BAG_order_depth.sell_orders) > 0) and
                    (len(DIP_order_depth.sell_orders) > 0) and
                    (len(UKU_order_depth.sell_orders) > 0) and
                    (len(PIC_order_depth.buy_orders) > 0)
            ):
                best_pic_bid = max(PIC_order_depth.buy_orders.keys())
                best_pic_bid_volume = PIC_order_depth.buy_orders[best_pic_bid]
                best_bag_ask = min(BAG_order_depth.sell_orders.keys())
                best_bag_ask_volume = BAG_order_depth.sell_orders[best_bag_ask]
                best_dip_ask = min(DIP_order_depth.sell_orders.keys())
                best_dip_ask_volume = DIP_order_depth.sell_orders[best_dip_ask]
                best_uku_ask = min(UKU_order_depth.sell_orders.keys())
                best_uku_ask_volume = UKU_order_depth.sell_orders[best_uku_ask]
                # volume to trade (positive)
                volume_market = min((-best_bag_ask_volume) // 2, (-best_dip_ask_volume) // 4, -best_uku_ask_volume,
                                    best_pic_bid_volume)
                volume_max = 70 + pic_position
                trade_volume = min(volume_market, volume_max)

                basket_price = best_pic_bid - best_dip_ask - best_bag_ask - best_uku_ask

                if basket_price > acceptable_price:
                    result['PICNIC_BASKET'] = [Order('PICNIC_BASKET', best_pic_bid, -trade_volume)]
                    result['BAGUETTE'] = [Order('BAGUETTE', best_bag_ask, trade_volume * 2)]
                    result['DIP'] = [Order('DIP', best_dip_ask, trade_volume * 4)]
                    result['UKULELE'] = [Order('UKULELE', best_uku_ask, trade_volume)]

            # buy basket when basket price < 400
            if (
                    (len(BAG_order_depth.buy_orders) > 0) and
                    (len(DIP_order_depth.buy_orders) > 0) and
                    (len(UKU_order_depth.buy_orders) > 0) and
                    (len(PIC_order_depth.sell_orders) > 0)):
                best_pic_ask = max(PIC_order_depth.sell_orders.keys())
                best_pic_ask_volume = PIC_order_depth.sell_orders[best_pic_ask]
                best_bag_bid = min(BAG_order_depth.buy_orders.keys())
                best_bag_bid_volume = BAG_order_depth.buy_orders[best_bag_bid]
                best_dip_bid = min(DIP_order_depth.buy_orders.keys())
                best_dip_bid_volume = DIP_order_depth.buy_orders[best_dip_bid]
                best_uku_bid = min(UKU_order_depth.buy_orders.keys())
                best_uku_bid_volume = UKU_order_depth.buy_orders[best_uku_bid]
                # volume to trade (positive)
                volume_market = min(best_bag_bid_volume // 2, best_dip_bid_volume // 4, best_uku_bid_volume,
                                    -best_pic_ask_volume)
                volume_max = 70 - pic_position
                trade_volume = min(volume_market, volume_max)

                basket_price = best_pic_ask - best_dip_bid - best_bag_bid - best_uku_bid

                if basket_price < acceptable_price:
                    result['PICNIC_BASKET'] = [Order('PICNIC_BASKET', best_pic_ask, trade_volume)]
                    result['BAGUETTE'] = [Order('BAGUETTE', best_bag_bid, -trade_volume * 2)]
                    result['DIP'] = [Order('DIP', best_dip_bid, -trade_volume * 4)]
                    result['UKULELE'] = [Order('UKULELE', best_uku_bid, -trade_volume)]

        logger.flush(state, result)
        return result