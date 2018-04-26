from .base_executor import BaseExecutor

class CCXTExecutor(BaseExecutor):
    """Executor for CCXT library."""

    def __init__(self, exchange):
        """Constructor."""
        self.exchange = exchange

    def create_emulated_market_buy_order(self, symbol, quote_amount,
                                         asset_price, slippage):
        """Creates an emulated market buy order with maximum slippage.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (float): The amount to buy in quote currency.
            asset_price (float): The target buy price, quote per base.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.
        """
        return self.exchange.create_emulated_market_buy_order(
            symbol,
            quote_amount,
            asset_price,
            slippage)
        # TODO: Error handling scenarios in accordance with ccxt

    def create_emulated_market_sell_order(self, symbol, asset_price,
                                          asset_amount, slippage):
        """Creates an emulated market sell order with maximum slippage.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (float): The price, quote per base.
            asset_amount (float): The amount of the asset to be sold.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.
        """
        return self.exchange.create_emulated_market_sell_order(
            symbol,
            asset_price,
            asset_amount,
            slippage)
        # TODO: Error handling scenarios in accordance with ccxt

    def create_market_buy_order(self, symbol, asset_amount, asset_price):
        """Creates a market buy order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be bought.
            asset_price (float); The target buy price, quote per base. (Unused)
        """
        return self.exchange.create_market_buy_order(symbol, asset_amount)
        # TODO: Error handling scenarios in accordance with ccxt

    def create_market_sell_order(self, symbol, asset_amount, asset_price):
        """Creates a market sell order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be sold.
            asset_price (float); The target sell price, quote per base. (Unused)
        """
        return self.exchange.create_market_sell_order(symbol, asset_amount)
        # TODO: Error handling scenarios in accordance with ccxt
