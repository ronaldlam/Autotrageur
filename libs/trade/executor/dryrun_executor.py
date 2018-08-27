import logging
import time

from bot.common.ccxt_constants import (BUY_SIDE, ORDER_TYPE_LIMIT,
                                       ORDER_TYPE_MARKET, SELL_SIDE)
from bot.common.decimal_constants import ONE
from libs.utilities import split_symbol

from .base_executor import BaseExecutor


class DryRunExecutor(BaseExecutor):
    """An executor if a dry run is desired."""

    def __init__(self, exchange, fetcher, dry_run_exchange):
        """Constructor.

        Args:
            exchange (ccxt.Exchange): The ccxt exchange.
            fetcher (CCXTFetcher): The ccxt fetcher.
            dry_run_exchange (DryRunExchange): The dry run exchange to
                hold state for the dry run.
        """
        logging.debug("*** Dry run with: %s", exchange.name)
        self.exchange = exchange
        self.fetcher = fetcher
        self.dry_run_exchange = dry_run_exchange

    def _complete_order(self, side, order_type, symbol, amount, price):
        """Populates a fake ideal order as a dry run response.

        Args:
            side (str): Either 'buy' or 'sell'.
            order_type (str): Either 'market' or 'limit'.
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            amount (Decimal): The amount to buy or sell.
            price (Decimal): The target price to buy or sell.

        Returns:
            dict: A pre-defined order dictionary populated with the
                calling function's parameters.
        """
        local_ts = int(time.time())
        exchange_name = self.exchange.name.lower()
        base, quote = split_symbol(symbol)
        pre_fee_base = amount
        pre_fee_quote = amount * price
        taker_fee = self.fetcher.fetch_taker_fees()

        # Currently the only case of this is bithumb, where buy fees are
        # collected in the base asset after the specified quote amount
        # is used to purchase the pre_fee_base amount of base asset.
        if side == BUY_SIDE:
            if self.exchange.buy_target_includes_fee:
                fee_asset = base
                post_fee_base = pre_fee_base * (ONE - taker_fee)
                post_fee_quote = pre_fee_quote
                fees = pre_fee_base - post_fee_base
            else:
                fee_asset = quote
                post_fee_base = pre_fee_base
                post_fee_quote = pre_fee_quote * (ONE + taker_fee)
                fees = post_fee_quote - pre_fee_quote

            self.dry_run_exchange.buy(pre_fee_base, pre_fee_quote,
                                      post_fee_base, post_fee_quote)
        else:
            fee_asset = quote
            post_fee_base = pre_fee_base
            post_fee_quote = pre_fee_quote * (ONE - taker_fee)
            fees = pre_fee_quote - post_fee_quote

            self.dry_run_exchange.sell(pre_fee_base, pre_fee_quote,
                                       post_fee_quote)

        return {
            'exchange': exchange_name,
            'base': base,
            'quote': quote,
            'pre_fee_base': pre_fee_base,
            'pre_fee_quote': pre_fee_quote,
            'post_fee_base': post_fee_base,
            'post_fee_quote': post_fee_quote,
            'fees': fees,
            'fee_asset': fee_asset,
            'price': price,
            'true_price': post_fee_quote / post_fee_base,
            'side': side,
            'type': order_type,
            'order_id': 'DRYRUN',
            'exchange_timestamp': local_ts,
            'local_timestamp': local_ts,
            'extra_info':  {
                'options': 'dryrun',
                'exchange': exchange_name
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
        logging.debug("Arguments: %s", locals())
        (asset_volume, _) = (
            self.exchange.prepare_emulated_market_buy_order(
                symbol, quote_amount, asset_price, slippage)
        )

        # We use asset_price because it uses order book data for calculation;
        # limit_price assumes worst case taking slippage into account.
        return self._complete_order(
            BUY_SIDE, ORDER_TYPE_LIMIT, symbol, asset_volume, asset_price)

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
        logging.debug("Arguments: %s", locals())
        (rounded_amount, _) = (
            self.exchange.prepare_emulated_market_sell_order(
                symbol, asset_price, asset_amount, slippage)
        )

        # We use asset_price because it uses order book data for calculation;
        # rounded_limit_price assumes worst case taking slippage into account.
        return self._complete_order(
            SELL_SIDE, ORDER_TYPE_LIMIT, symbol, rounded_amount, asset_price)

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
        logging.debug("Arguments: %s", locals())
        return self._complete_order(
            BUY_SIDE, ORDER_TYPE_MARKET, symbol, asset_amount, asset_price)

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
        logging.debug("Arguments: %s", locals())
        return self._complete_order(
            SELL_SIDE, ORDER_TYPE_MARKET, symbol, asset_amount, asset_price)
