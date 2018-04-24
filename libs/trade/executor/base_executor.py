from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    """An Abstract Base Class for trade execution."""

    def __init__(self):
        """Constructor."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def create_market_buy_order(self, symbol, asset_amount):
        """Creates a market buy order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be bought.
        """
        pass

    @abstractmethod
    def create_market_sell_order(self, symbol, asset_amount):
        """Creates a market sell order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be sold.
        """
        pass
