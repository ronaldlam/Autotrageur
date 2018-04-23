import logging

from .base_executor import BaseExecutor

class DryRunExecutor(BaseExecutor):
    """An executor if a dry run is desired."""

    def __init__(self):
        """Constructor."""
        pass

    def create_emulated_market_buy_order(self, symbol, quote_amount,
                                         asset_price, slippage):
        """When an emulated market buy order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (float): The amount to buy in quote currency.
            asset_price (float): The target buy price, quote per base.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.
        """
        logging.log(logging.INFO, "create_emulated_market_buy_order() called with \
            symbol: %s, quote_amount: %s, asset_price: %s, slippage: %s",
            symbol, quote_amount, asset_price, slippage)

    def create_emulated_market_sell_order(self, symbol, target_amount,
                                         asset_price, slippage):
        """When an emulated market sell order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (float): The price, quote per base.
            asset_amount (float): The amount of the asset to be sold.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.
        """
        logging.log(logging.INFO, "create_emulated_market_sell_order() called with \
            symbol: %s, target_amount: %s, asset_price: %s, slippage: %s",
            symbol, target_amount, asset_price, slippage)

    def create_market_buy_order(self, symbol, asset_amount):
        """When a market buy order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be bought.
        """
        logging.log(logging.INFO, "create_market_buy_order() called with \
            symbol: %s and ammount: %s", symbol, asset_amount)

    def create_market_sell_order(self, symbol, asset_amount):
        """When a market sell order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be sold.
        """
        logging.log(logging.INFO, "create_market_sell_order() called with \
            symbol: %s and ammount: %s", symbol, asset_amount)
