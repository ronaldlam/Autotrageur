import logging

from .base_executor import BaseExecutor


DRYRUN_FAKE_RESPONSE = {
    "info": {
        "order_id": "DRYRUN",
        "id": "DRYRUN",
        "executed_amount": 1
    },
    "id": "DRYRUN"
}


class DryRunExecutor(BaseExecutor):
    """An executor if a dry run is desired."""

    def __init__(self, exchange_name):
        """Constructor.

        Args:
            exchange_name (str): The name of the exchange; used for logging.
        """
        logging.log(logging.INFO, "*** Dry run with: %s", exchange_name)
        self.exchange_name = exchange_name

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
        logging.log(logging.INFO, "Arguments: %s", locals())
        return DRYRUN_FAKE_RESPONSE

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
        logging.log(logging.INFO, "Arguments: %s", locals())
        return DRYRUN_FAKE_RESPONSE

    def create_market_buy_order(self, symbol, asset_amount):
        """When a market buy order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be bought.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        return DRYRUN_FAKE_RESPONSE

    def create_market_sell_order(self, symbol, asset_amount):
        """When a market sell order has been requested from the bot.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (float): The amount of asset to be sold.
        """
        logging.log(logging.INFO, "Arguments: %s", locals())
        return DRYRUN_FAKE_RESPONSE
