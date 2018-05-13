import logging
from decimal import Decimal

from .base_executor import BaseExecutor


class DryRunExecutor(BaseExecutor):
    """An executor if a dry run is desired."""

    def __init__(self, exchange):
        """Constructor.

        Args:
            exchange (ccxt.Exchange): The ccxt exchange.
        """
        logging.log(logging.INFO, "*** Dry run with: %s", exchange.name)
        self.exchange = exchange

    def _populate_dry_run_order(self, symbol, amount, price=Decimal('0')):
        """Populates a fake ideal order as a dry run response.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            amount (Decimal): The amount to buy or sell.
            price (Decimal, optional): The target price to buy or sell.
                Used in emulated buy/sell orders.  Defaults to 0.

        Returns:
            dict: A pre-defined order dictionary populated with the
                calling function's parameters.
        """
        return {
            "info": {
                "symbol": symbol,
                "exchange": self.exchange.name,
                "price": price,
                "executed_amount": amount,
            },
            "id": "DRYRUN"
        }

    def create_emulated_market_buy_order(self, symbol, quote_amount,
                                         asset_price, slippage):
        """When an emulated market buy order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (Decimal): The amount to buy in quote currency.
            asset_price (Decimal): The target buy price, quote per base.
            slippage (Decimal): The percentage off asset_price the
                market buy will tolerate.

        Returns:
            dict: A pre-defined order dictionary populated with the
                function's parameters.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        (asset_volume, _) = (
            self.exchange.prepare_emulated_market_buy_order(
                symbol, quote_amount, asset_price, slippage)
        )

        # We use asset_price because it uses order book data for calculation;
        # limit_price assumes worst case taking slippage into account.
        return self._populate_dry_run_order(symbol, asset_volume, asset_price)

    def create_emulated_market_sell_order(self, symbol, asset_price,
                                          asset_amount, slippage):
        """When an emulated market sell order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (Decimal): The price, quote per base.
            asset_amount (Decimal): The amount of the asset to be sold.
            slippage (Decimal): The percentage off asset_price the
                market buy will tolerate.

        Returns:
            dict: A pre-defined order dictionary populated with the
                function's parameters.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        (rounded_amount, _) = (
            self.exchange.prepare_emulated_market_sell_order(
                symbol, asset_price, asset_amount, slippage)
        )

        # We use asset_price because it uses order book data for calculation;
        # rounded_limit_price assumes worst case taking slippage into account.
        return self._populate_dry_run_order(
            symbol, rounded_amount, asset_price)

    def create_market_buy_order(self, symbol, asset_amount, asset_price):
        """When a market buy order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be bought.
            asset_price (Decimal); The target buy price, quote per base.

        Returns:
            dict: A pre-defined order dictionary populated with the
                function's parameters.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        return self._populate_dry_run_order(symbol, asset_amount, asset_price)

    def create_market_sell_order(self, symbol, asset_amount, asset_price):
        """When a market sell order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be sold.
            asset_price (Decimal); The target sell price, quote per
                base.

        Returns:
            dict: A pre-defined order dictionary populated with the
                function's parameters.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        return self._populate_dry_run_order(symbol, asset_amount, asset_price)
