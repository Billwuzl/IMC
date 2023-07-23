import json
from datamodel import Order, ProsperityEncoder, Symbol, TradingState, OrderDepth, Trade
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
        for product in state.order_depths.keys():
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
                    print("BUY", str(best_ask_volume) + "x", best_ask)
                    result[product] = [Order(product, best_ask, best_ask_volume)]

                # sell berries from time 450K to 550K
                if len(order_depth.buy_orders) > 0 and 450000 < state.timestamp < 550000:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = min(order_depth.buy_orders[best_bid],  250 + position)
                    print("SELL", str(best_bid_volume) + "x", best_bid)
                    result[product] = [Order(product, best_bid, - best_bid_volume)]

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

            if product == 'PEARLS':
                if 'PEARLS' in state.position.keys():
                    position = state.position[product]
                else:
                    position = 0

                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []
                acceptable_price = 10000

                if len(order_depth.sell_orders) > 0:

                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = min(-order_depth.sell_orders[best_ask], 20 - position)

                    if best_ask < acceptable_price:
                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, best_ask_volume))

                if len(order_depth.buy_orders) > 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = min(order_depth.buy_orders[best_bid], 20 + position)
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

            acceptable_buy = 370 - (0.3 * (pic_position) // 1)
            acceptable_sell = 430 - (0.3 * (pic_position) // 1)

            # buy basket
            if (
                    (len(BAG_order_depth.buy_orders) > 0) and
                    (len(DIP_order_depth.buy_orders) > 0) and
                    (len(UKU_order_depth.buy_orders) > 0) and
                    (len(PIC_order_depth.sell_orders) > 0)
            ):
                best_pic_ask = min(PIC_order_depth.sell_orders.keys())
                best_pic_ask_volume = PIC_order_depth.sell_orders[best_pic_ask]
                best_bag_bid = max(BAG_order_depth.buy_orders.keys())
                best_bag_bid_volume = BAG_order_depth.buy_orders[best_bag_bid]
                best_dip_bid = max(DIP_order_depth.buy_orders.keys())
                best_dip_bid_volume = DIP_order_depth.buy_orders[best_dip_bid]
                best_uku_bid = max(UKU_order_depth.buy_orders.keys())
                best_uku_bid_volume = UKU_order_depth.buy_orders[best_uku_bid]
                # volume to trade (positive)
                volume_market = min(best_bag_bid_volume // 2, best_dip_bid_volume // 4, best_uku_bid_volume,
                                    -best_pic_ask_volume)
                volume_max = 70 - pic_position

                basket_price = best_pic_ask - best_dip_bid * 4 - best_bag_bid * 2 - best_uku_bid

                trade_volume = min(volume_max * (400 - basket_price) / 200, volume_max) // 1

                if basket_price < acceptable_buy:
                    result['PICNIC_BASKET'] = [Order('PICNIC_BASKET', best_pic_ask, trade_volume)]
                    result['BAGUETTE'] = [Order('BAGUETTE', best_bag_bid, (-trade_volume) * 2)]
                    result['DIP'] = [Order('DIP', best_dip_bid, (-trade_volume) * 4)]
                    result['UKULELE'] = [Order('UKULELE', best_uku_bid, (-trade_volume))]

            # sell basket
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

                basket_price = best_pic_bid - best_dip_ask * 4 - best_bag_ask * 2 - best_uku_ask

                trade_volume = min(volume_max * (basket_price - 400) / 200, volume_max) // 1

                if basket_price > acceptable_sell:
                    result['PICNIC_BASKET'] = [Order('PICNIC_BASKET', best_pic_bid, -trade_volume)]
                    result['BAGUETTE'] = [Order('BAGUETTE', best_bag_ask, trade_volume * 2)]
                    result['DIP'] = [Order('DIP', best_dip_ask, trade_volume * 4)]
                    result['UKULELE'] = [Order('UKULELE', best_uku_ask, trade_volume)]

                    # coconut & pina colada pair trading starts here
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
                if coco_best_bid > coco_fair_price:
                    # obtain the max number of coco that can be sold given the max position
                    volume_max = coco_max_position + coco_position
                    coco_sell_quantity = min(volume_max, coco_order_depth.buy_orders[coco_best_bid])
                    result['COCONUTS'] = [Order('COCONUTS', coco_best_bid, - coco_sell_quantity)]

                if coco_best_ask < coco_fair_price:
                    # obtain the max number of coco that can be bought given the max position
                    volume_max = coco_max_position - coco_position
                    coco_buy_quantity = min(volume_max, - coco_order_depth.sell_orders[coco_best_ask])
                    result['COCONUTS'] = [Order('COCONUTS', coco_best_ask, coco_buy_quantity)]

                if pc_best_bid > pc_fair_price:
                    # obtain the max number of pc that can be sold given the max position
                    volume_max = pc_max_position + pc_position
                    pc_sell_quantity = min(volume_max, pc_order_depth.buy_orders[pc_best_bid])
                    result['PINA_COLADAS'] = [Order('PINA_COLADAS', pc_best_bid, - pc_sell_quantity)]

                if pc_best_ask < pc_fair_price:
                    # obtain the max number of pc that can be bought given the max position
                    volume_max = pc_max_position - pc_position
                    pc_buy_quantity = min(volume_max, - pc_order_depth.sell_orders[pc_best_ask])
                    result['PINA_COLADAS'] = [Order('PINA_COLADAS', pc_best_ask, pc_buy_quantity)]

        logger.flush(state, result)
        return result