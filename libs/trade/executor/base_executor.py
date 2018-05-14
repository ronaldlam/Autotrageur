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
            quote_amount (Decimal): The amount to buy in quote currency.
            asset_price (Decimal): The target buy price, quote per base.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.
        """
        pass

    @abstractmethod
    def create_emulated_market_sell_order(self, symbol, asset_price,
                                          asset_amount, slippage):
        """Creates an emulated market sell order with maximum slippage.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (Decimal): The price, quote per base.
            asset_amount (Decimal): The amount of the asset to be sold.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.
        """
        pass

    @abstractmethod
    def create_market_buy_order(self, symbol, asset_amount, asset_price):
        """Creates a market buy order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be bought.
            asset_price (Decimal); The target buy price, quote per base.
        """
        pass

    @abstractmethod
    def create_market_sell_order(self, symbol, asset_amount, asset_price):
        """Creates a market sell order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be sold.
            asset_price (Decimal); The target sell price, quote per base.
        """
        pass
