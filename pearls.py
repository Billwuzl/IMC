import json
import pandas as pd
import numpy as np
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

    def __init__(self):
        # max position size of all symbols: BANANAS	BERRIES COCONUTS DIVING_GEAR DOLPHIN_SIGHTINGS PEARLS PINA_COLADAS
        self.max_position_size_BANANAS = 20
        self.max_position_size_DIVING_GEAR = 50
        self.max_position_size_BERRIES = 2500
        self.max_position_size_COCONUTS = 600
        self.max_position_size_DOLPHIN_SIGHTINGS = 0
        self.max_position_size_PEARLS = 20
        self.max_position_size_PINA_COLADAS = 300
        self.ma1_period = 1000  # short-term moving average period
        self.ma2_period = 3000  # long-term moving average period
        # Initialize the dataframes to store the order book updates
        # store the order book updates in two dataframes for each asset respectively: include
        # the timestamp, TradingState, mid_price
        self.df_DIVING_GEAR = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_BERRIES = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_BANANAS = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_COCONUTS = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_DOLPHIN_SIGHTINGS = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_PEARLS = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])
        self.df_PINA_COLADAS = pd.DataFrame(columns=['timestamp', 'state', 'mid_price'])


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                # calculate the mid_price of the order book and if we do not have both buy_orders and sell_orders, set it to 10000
                # if len(state.order_depths[product].buy_orders) == 0 or len(state.order_depths[product].sell_orders) == 0:
                #     mid_price = 10000
                # else:
                #     mid_price = (min(state.order_depths[product].sell_orders.keys()) + max(state.order_depths[product].buy_orders.keys())) / 2
                # # update the order book dataframe
                # self.df_PEARLS = self.df_PEARLS.append({'timestamp': state.timestamp, 'state': state, 'mid_price': mid_price}, ignore_index=True)


                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 10000

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:

                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = order_depth.sell_orders[best_ask]

                    # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < acceptable_price:

                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        # check whether we have checked we can buy
                        if state.position[product] < self.max_position_size_PEARLS:
                            # obtain the max volume of PEARLS we can buy,
                            # make sure our new position is not greater than the max position size

                            max_volume = self.max_position_size_PEARLS - state.position[product]
                            # check whether the max volume is greater than the best ask volume
                            if max_volume > best_ask_volume:
                                # if so, buy the best ask volume
                                print("BUY", str(best_ask_volume) + "x", best_ask)
                                orders.append(Order(product, best_ask, best_ask_volume))
                            else:
                                # if not, buy the max volume
                                print("BUY", str(max_volume) + "x", best_ask)
                                orders.append(Order(product, best_ask, max_volume))


                # The below code block is similar to the one above,
                # the difference is that it find the highest bid (buy order)
                # If the price of the order is higher than the fair value
                # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = max(order_depth.buy_orders[best_bid], -20 - state.position[product])
                    if best_bid > acceptable_price:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))


                # Add all the above the orders to the result dict
                result[product] = orders

                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above

        logger.flush(state, result)
        return result