class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}
        for product in state.order_depths.keys():
            order_depth = state.order_depths[product]
            if self.position[product] >= 0:
                best_ask = min(order_depth.sell_orders.keys())
                orders = [Order(product, best_ask, -10)]
                result[product] = orders            
            else:
                best_bid = max(order_depth.buy_orders.keys())
                orders = [Order(product, best_bid, 10)]
                result[product] = orders
        return result