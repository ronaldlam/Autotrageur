import logging
from decimal import Decimal
import time

from bot.common.ccxt_constants import BUY_SIDE, SELL_SIDE
from libs.utilities import num_to_decimal
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

    def _populate_dry_run_order(self, side, symbol, amount, price=Decimal('0')):
        """Populates a fake ideal order as a dry run response.

        Args:
            side (str): Either 'buy' or 'sell'.
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            amount (Decimal): The amount to buy or sell.
            price (Decimal, optional): The target price to buy or sell.
                Used in emulated buy/sell orders.  Defaults to 0.

        Returns:
            dict: A pre-defined order dictionary populated with the
                calling function's parameters.
        """
        local_ts = int(time.time())
        dry_run_base = num_to_decimal(amount)
        dry_run_quote = dry_run_base * price
        return {
            'pre_fee_base': dry_run_base,
            'pre_fee_quote': dry_run_quote,
            'post_fee_base': dry_run_base,
            'post_fee_quote': dry_run_quote,
            'fees': num_to_decimal(0.00),
            'fee_asset': symbol.split('/')[1],
            'price': price,
            'true_price': price,
            'side': side,
            'type': 'market',
            'order_id': 'DRYRUN',
            'exchange_timestamp': local_ts,
            'local_timestamp': local_ts,
            'extra_info':  {
                'options': 'dryrun',
                'exchange': self.exchange.name
            }
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
        return self._populate_dry_run_order(
            BUY_SIDE, symbol, asset_volume, asset_price)

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
            SELL_SIDE, symbol, rounded_amount, asset_price)

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
        return self._populate_dry_run_order(
            BUY_SIDE, symbol, asset_amount, asset_price)

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
        return self._populate_dry_run_order(
            SELL_SIDE, symbol, asset_amount, asset_price)
