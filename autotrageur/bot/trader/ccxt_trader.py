import logging
from collections import namedtuple
from statistics import stdev

import ccxt

import fp_libs.forex.currency_converter as forex
import fp_libs.ccxt_extensions as ccxt_extensions
from fp_libs.constants.ccxt_constants import BUY_SIDE
from fp_libs.constants.decimal_constants import HUNDRED, ONE, ZERO
from fp_libs.db.maria_db_handler import execute_parametrized_query
from fp_libs.trade.executor.ccxt_executor import CCXTExecutor
from fp_libs.trade.executor.dryrun_executor import DryRunExecutor
from fp_libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from fp_libs.utilities import keys_exists, num_to_decimal

EXTENSION_PREFIX = "ext_"


PricePair = namedtuple('PricePair', ['usd_price', 'quote_price'])


class OrderbookException(Exception):
    """Exception for orderbook related errors."""
    pass


class ExchangeLimitException(Exception):
    """Exception for exchange limit breaches."""
    pass


class MalformedForexRatioException(Exception):
    """Exception when the forex ratio is malformed, or not present."""
    pass


class NoQuoteBalanceException(Exception):
    """Exception when there is no quote balance set."""
    pass

class CCXTTrader():
    """CCXT Trader for performing trades."""

    def __init__(self, base, quote, exchange_name, exchange_id, slippage,
        exchange_config={}, dry_run_exchange=None):
        """Constructor.

        The trading client for interacting with the CCXT library.
        Main responsibilities include:
            1) Fetching real-time data from the specified exchange.
            2) Executing orders against the specified exchange.

        Args:
            base (str): The base (first) token/currency of the exchange
                pair.
            quote (str): The quote (second) token/currency of the
                exchange pair.
            exchange_name (str): Desired exchange to query against.
            exchange_id (str): The exchange id, either 'e1' or e2'.
            slippage (Decimal): Maximum desired slippage from emulated
                market trades.
            exchange_config (dict): The exchange's configuration in
                accordance with the ccxt library for instantiating an
                exchange, ex.
                {
                    "apiKey": [SOME_API_KEY]
                    "secret": [SOME_API_SECRET]
                    "verbose": False,
                }
            dry_run_exchange (DryRunExchange): The object to hold the state of
                the dry run for the associated exchange. Is None if not
                a dry run.
        """
        # Instantiate the CCXT Exchange object, or a custom extended CCXT
        # Exchange object.
        exchange_name = exchange_name.lower()
        if EXTENSION_PREFIX + exchange_name in dir(ccxt_extensions):
            self.ccxt_exchange = getattr(
                ccxt_extensions, EXTENSION_PREFIX + exchange_name)(exchange_config)
        else:
            self.ccxt_exchange = getattr(ccxt, exchange_name)(exchange_config)

        self.base = base
        self.quote = quote
        self.exchange_name = exchange_name
        self.exchange_id = exchange_id
        self.fetcher = CCXTFetcher(self.ccxt_exchange)
        self.slippage = slippage
        self.dry_run_exchange = dry_run_exchange

        if dry_run_exchange:
            self.executor = DryRunExecutor(
                self.ccxt_exchange, self.fetcher, dry_run_exchange)
        else:
            self.executor = CCXTExecutor(self.ccxt_exchange)

        # Initialized variables not from config.
        self._forex_ratio = ONE
        self.quote_target_amount = ZERO
        self.quote_rough_sell_amount = ZERO
        self.conversion_needed = False
        self.forex_id = None
        self.base_bal = None
        self.quote_bal = None
        self.adjusted_quote_bal = None

    @property
    def forex_ratio(self):
        """Property getter for the ccxt_trader's forex_ratio.

        Raises:
            MalformedForexRatioException: Exception when the forex ratio is
                malformed, or not present.

        Returns:
            Decimal: The forex ratio of [FOREX_QUOTE_CURR]/USD.
        """
        if self._forex_ratio is None or self._forex_ratio <= ZERO:
            raise MalformedForexRatioException(
                "The forex_ratio is either malformed or non-existent.")
        return self._forex_ratio

    @forex_ratio.setter
    def forex_ratio(self, forex_ratio):
        """Property setter for the ccxt_trader's forex_ratio.

        Args:
            forex_ratio (Decimal): The forex ratio to be set.
        """
        self._forex_ratio = forex_ratio

    def __adjust_working_balance(self, is_dry_run):
        """Subtracts reasonable slippage from quote_bal.

        Retrieves trade data and use slippage of executed trades to
        calculate the desired working quote balance. We assume that the
        slippage follows a normal distribution about mean 0 and we use
        the sample standard deviation for our calculations. This should
        be adjusted every time a trade is executed, since that gives us
        an additional datapoint.

        This is a measure to reduce likelihood of failed buy executions
        when the quote_target_amount is equal to quote_bal. If there is
        any orderbook movement driving price up, then the quote_bal will
        not be sufficient to cover the trade, since it is issued to the
        exchange in terms of base desired to be purchased.

        Args:
            is_dry_run (bool): Whether or not the current run is a dry
                run.
        """
        # See spreadcalculator.calc_fixed_spread for details.
        if self.ccxt_exchange.buy_target_includes_fee:
            buy_op = '/'
            buy_fee_ratio = ONE - self.get_taker_fee()
        else:
            buy_op = '*'
            buy_fee_ratio = ONE + self.get_taker_fee()

        query = """
            SELECT
                IF(
                    t.side = 'buy',
                    t_o.{exchange_id}_buy {buy_op} CAST(%s AS DECIMAL(27,8)) / t.true_price,
                    t_o.{exchange_id}_sell * CAST(%s AS DECIMAL(27,8)) / t.true_price) AS trade_predict_ratio
            FROM
                fcf_autotrageur_config AS c,
                trade_opportunity AS t_o,
                trades AS t
            WHERE
                c.dryrun = %s
                AND c.id = t.autotrageur_config_id
                AND c.start_timestamp = t.autotrageur_config_start_timestamp
                AND t.trade_opportunity_id = t_o.id
                AND t.exchange = %s
        """.format(exchange_id=self.exchange_id, buy_op=buy_op)
        sell_fee_ratio = ONE - self.get_taker_fee()
        data = execute_parametrized_query(query, (
            buy_fee_ratio,
            sell_fee_ratio,
            1 if is_dry_run else 0,
            self.exchange_name))

        # Turn ratios into percentages.
        # TODO: Store fee data with executed trades to take into account
        # dynamic fee structures and better post-trade analysis.
        # NOTE: Eventually the number of trades processed should be
        # limited for performance, but likely not until the hundreds or
        # thousands.
        data = [(x[0] - ONE) * HUNDRED for x in data]

        self.adjusted_quote_bal = self.quote_bal

        # This requires existing trades; stdev will fail for < 2 trades.
        if len(data) >= 2:
            std_dev = stdev(data)
            # We use 1.96 standard deviations to make 97.5% of samples
            # be within the true balance, assuming a normal distribution.
            buffer_percentage = std_dev * num_to_decimal('1.96')
            self.adjusted_quote_bal -= self.quote_bal * (buffer_percentage / 100)

    def __calc_vol_by_book(self, orders, quote_target_amount):
        """Calculates the asset volume with which to execute a trade.

        Uses data from the orderbook to calculate the base asset volume
        to fulfill the quote_target_amount.

        Args:
            orders (list[list(float)]): The bids or asks in the
                form of (price, volume).
            quote_target_amount (Decimal): Targeted amount to buy or
                sell, in quote currency.

        Raises:
            OrderbookException: If the orderbook is not deep enough.

        Returns:
            Decimal: The base asset volume required to fulfill
                target_amount via the orderbook.
        """
        index = 0
        base_asset_volume = ZERO
        remaining_amount = quote_target_amount

        # The decimal orders.
        d_orders = []
        for entry in orders:
            d_orders.append(
                [num_to_decimal(entry[0]), num_to_decimal(entry[1])])

        # Subtract from amount until enough of the order book is eaten up by
        # the trade.
        while remaining_amount > ZERO and index < len(d_orders):
            remaining_amount -= d_orders[index][0] * d_orders[index][1]
            base_asset_volume += d_orders[index][1]
            index += 1

        if index == len(d_orders) and remaining_amount > ZERO:
            raise OrderbookException("Order book not deep enough for trade.")

        # Add the zero or negative excess amount to trim off the overshoot
        base_asset_volume += remaining_amount / d_orders[index - 1][0]

        return base_asset_volume

    def __check_exchange_limits(self, amount, price):
        """Verify amount and price are within exchange limits.

        Args:
            amount (Decimal): Amount of the base asset to trade.
            price (Decimal): Price of base asset in quote currency.

        Raises:
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.
        """
        symbol = "%s/%s" % (self.base, self.quote)
        limits = self.ccxt_exchange.markets[symbol]['limits']

        for measure in [ ('amount', amount), ('price', price) ]:
            for range_limit in ['min', 'max']:
                if (measure[1] and keys_exists(limits, measure[0],
                                               range_limit)):
                    limit = num_to_decimal(limits[measure[0]][range_limit])
                    if limit:
                        if range_limit == 'min' and limit > measure[1]:
                            raise ExchangeLimitException(
                            "Order %s %s %s less than exchange limit %s %s."
                                % (measure[0], measure[1], self.base, limit,
                                   self.base))
                        elif range_limit == 'max' and limit < measure[1]:
                            raise ExchangeLimitException(
                            "Order %s %s %s more than exchange limit %s %s."
                                % (measure[0], measure[1], self.base, limit,
                                   self.base))

    def __round_exchange_precision(self, market_order, asset_amount):
        """Rounds the asset amount by a precision provided by the exchange.

        Args:
            market_order (bool or string): Is one of: True, False,
                'emulated' to specify if market order is supported, not
                supported, or emulated.
            asset_amount (Decimal): The amount that is to be rounded.

        Returns:
            Decimal: If precision specified by exchange, the rounded
                asset amount is returned.  Else, the asset amount is
                returned unchanged.
        """
        if market_order is True:
            # Rounding is required for direct ccxt call.
            precision = self.get_amount_precision()

            # In the case the exchange supports arbitrary precision.
            if precision is not None:
                asset_amount = round(asset_amount, precision)

        return asset_amount

    def connect_test_api(self):
        """Connect to the test API of the exchange.

        Raises:
            NotImplementedError: There is no test API support.
        """
        if 'test' in self.ccxt_exchange.urls:
            self.ccxt_exchange.urls['api'] = self.ccxt_exchange.urls['test']
        else:
            raise NotImplementedError(
                "Test connection to %s not implemented." %
                self.ccxt_exchange.id)

    def execute_market_buy(self, asset_price):
        """Execute a market buy order.

        Args:
            asset_price (Decimal): Target asset price for the trade.

        Raises:
            NotImplementedError: If not implemented.
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
                and 'id'. The 'info' includes all raw response contents
                and result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        quote_target_amount = self.quote_target_amount
        asset_amount = quote_target_amount / asset_price

        # If the buy target does not include fees, we want to deduct the fees
        # from the original quote_target_amount. Since the price per unit base
        # is always a fixed price, we can divide by the fee ratio to get both
        # the true target asset_amount and quote_target_amount. Note that all
        # exchanges MUST implement buy_target_includes_fee.
        if self.ccxt_exchange.buy_target_includes_fee is False:
            fee_ratio = num_to_decimal(1) + self.get_taker_fee()
            asset_amount /= fee_ratio
            quote_target_amount /= fee_ratio

        asset_amount = self.__round_exchange_precision(
            market_order, asset_amount)

        # For 'emulated', We check before rounding which is not strictly
        # correct, but it is likely larger issues are at hand if the error is
        # raised.
        self.__check_exchange_limits(asset_amount, asset_price)

        if market_order is True:
            result = self.executor.create_market_buy_order(
                symbol, asset_amount, asset_price)
        elif market_order == 'emulated':
            # Rounding will be deferred to emulated implementation.
            result = self.executor.create_emulated_market_buy_order(
                symbol,
                quote_target_amount,
                asset_price,
                self.slippage)
        else:
            raise NotImplementedError(
                "Exchange %s has no market buy functionality." %
                self.ccxt_exchange.id)

        return result

    def execute_market_sell(self, asset_price, asset_amount):
        """Execute a market sell order.

        Args:
            asset_price (Decimal): Target asset price for exchanges with
                no market sell support.
            asset_amount (Decimal): Target amount of the asset to be sold.

        Raises:
            NotImplementedError: If not implemented.
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
                and 'id'. The 'info' includes all raw response contents and
                result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        asset_amount = self.__round_exchange_precision(
            market_order, asset_amount)

        # For 'emulated', We check before rounding which is not strictly
        # correct, but it is likely larger issues are at hand if the error is
        # raised.
        self.__check_exchange_limits(asset_amount, asset_price)

        if market_order is True:
            result = self.executor.create_market_sell_order(
                symbol,
                asset_amount,
                asset_price)
        elif market_order == 'emulated':
            result = self.executor.create_emulated_market_sell_order(
                symbol,
                asset_price,
                asset_amount,
                self.slippage)
        else:
            raise NotImplementedError(
                "Exchange %s has no market sell functionality." %
                self.ccxt_exchange.id)

        return result

    def get_amount_precision(self):
        """Gets the base amount precision for the current market.

        NOTE: The `None` value represents arbitrary precision, currently
        only for future proofing.

        Returns:
            int: The precision.
        """
        symbol = "%s/%s" % (self.base, self.quote)
        precision = self.ccxt_exchange.markets[symbol]['precision']

        if 'amount' in precision and precision['amount'] is not None:
            return precision['amount']
        else:
            return None

    def get_buy_target_includes_fee(self):
        """Gets whether the exchange includes fees in its buy orders.

        Please refer to `spreadcalculator.calc_fixed_spread` for more detail.

        Returns:
            bool: True if an exchange's buy order will have fees factored into
                the price (Scenario 1, as described above). Else, False.
        """
        return self.ccxt_exchange.buy_target_includes_fee

    def get_full_orderbook(self):
        """Gets the full orderbook (bids and asks) from the exchange.

        Please refer to `ccxt_fetcher.get_full_orderbook` for sample orderbook
        response.

        Returns:
            dict: The full orderbook.
        """
        return self.fetcher.get_full_orderbook(self.base, self.quote)

    def get_min_base_limit(self):
        """Retrieves the minimum base amount limit of the trader's 'base/quote'
        pair.

        Returns:
            Decimal: The minimum base amount limit.
        """
        symbol = "{}/{}".format(self.base, self.quote)
        return num_to_decimal(
            self.ccxt_exchange.markets[symbol]['limits']['amount']['min'])

    def get_prices_from_orderbook(self, side, bids_or_asks):
        """Get market buy or sell price in USD and quote currency.

        Return adjusted market buy or sell prices given bids or asks and
        amount to be sold. The market price is adjusted based on
        orderbook depth and the `quote_target_amount`, `rough_sell_amount`
        set by `set_buy_target_amount` and `set_rough_sell_amount`.

        Input of bids will retrieve market sell price; input of asks
        will retrieve market buy price.

        Args:
            side (str): Which side of the orderbook is used.  One of BUY_SIDE
                or SELL_SIDE.
            bids_or_asks (list[list(float)]): The bids or asks in the
                form of (price, volume).

        Raises:
            OrderbookException: If the orderbook is not deep enough.

        Returns:
            PricePair (Decimal, Decimal): Prospective USD and quote
                prices of a market buy or sell.
        """
        target_amount = (self.quote_target_amount
            if side is BUY_SIDE
            else self.quote_rough_sell_amount)
        asset_volume = self.__calc_vol_by_book(bids_or_asks, target_amount)
        usd_price = self.get_usd_from_quote(target_amount) / asset_volume
        quote_price = target_amount / asset_volume
        return PricePair(usd_price, quote_price)

    def get_taker_fee(self):
        """Obtains the exchange's takers fee.

        Raises:
            NotImplementedError: If not accessible through ccxt.

        Returns:
            Decimal: The taker fee, given as a ratio.
        """
        return self.fetcher.fetch_taker_fees()

    def get_quote_from_usd(self, usd_amount):
        """Get converted quote amount from USD amount.

        Args:
            usd_amount (Decimal): The USD amount to convert.

        Raises:
            NoForexQuoteException: If forex_ratio is needed and not set.

        Returns:
            Decimal: The quote amount.
        """
        if self.conversion_needed:
            return usd_amount * self.forex_ratio
        else:
            return usd_amount

    def get_adjusted_usd_balance(self):
        """Gets the slippage adjusted balance in terms of US Dollars.

        If the quote balance is in a different fiat other than USD (e.g.
        KRW), we will have to use a forex ratio to convert the dollar
        amount to USD.

        NOTE: The `adjusted_quote_bal` and `forex_ratio` will need to be
        set appropriately in order for the function to work as expected.

        Raises:
            NoForexQuoteException: If forex_ratio is needed and not set.
            NoQuoteBalanceException: If adjusted_quote_bal is not set.

        Returns:
            Decimal: The balance in terms of USD.
        """
        if self.adjusted_quote_bal is None:
            raise NoQuoteBalanceException(
                "Unable to retrieve USD balance as a quote balance has not "
                "been set yet.")
        if self.conversion_needed:
            return self.adjusted_quote_bal / self.forex_ratio
        else:
            return self.adjusted_quote_bal

    def get_usd_from_quote(self, quote_amount):
        """Get converted USD amount from quote amount.

        Args:
            quote_amount (Decimal): The quote amount to convert.

        Raises:
            NoForexQuoteException: If forex_ratio is needed and not set.

        Returns:
            Decimal: The USD amount.
        """
        if self.conversion_needed:
            return quote_amount / self.forex_ratio
        else:
            return quote_amount

    def load_markets(self):
        """Load the markets of the exchange.

        Allows manual calling of `load_markets` from either a ccxt Exchange
        object or a `ccxt_extensions` ext_ Exchange object.

        Refer https://github.com/ccxt/ccxt/wiki/Manual in the Loading Markets
        section for details.

        Returns:
            dict: Information about the `markets` which have been loaded into
                memory.
        """
        self.fetcher.load_markets()

    def round_exchange_precision(self, amount):
        """Rounds the amount based on an exchange's precision.

        Args:
            amount (Decimal): The amount to be rounded.

        Returns:
            Decimal: The rounded amount based on an exchange's precision.  Can
                return the original amount if the exchange supports arbitrary
                precision.
        """
        return self.__round_exchange_precision(True, amount)

    def set_buy_target_amount(self, buy_target_amount, is_usd=True):
        """Sets the internal buy amount which is used for the trading
        algorithm.

        `quote_target_amount` is used for calculating spreads and setting an
        amount to purchase a buy order with.

        NOTE: This is only valid for fiat currency with support for the
        currencies supported by the forex_python API. Will fail for
        crypto pairs.

        Args:
            buy_target_amount (Decimal): The amount to use for calculating buy
                targets.  Can be USD or quote currency.
            is_usd (bool, optional): Defaults to True. Whether
                buy_target_amount is USD or quote currency.

        Raises:
            NoForexQuoteException: If forex_ratio is needed and not set.
        """
        if is_usd and self.conversion_needed:
            self.quote_target_amount = self.get_quote_from_usd(
                buy_target_amount)
        else:
            self.quote_target_amount = buy_target_amount

        logging.debug('{} quote_target_amount updated to: {}'.format(
            self.exchange_name, self.quote_target_amount))

    def set_forex_ratio(self):
        """Get foreign currency per USD.

        `forex_ratio` is set when the quote currency is not USD.
        """
        self.forex_ratio = forex.convert_currencies(
            'USD', self.quote, ONE)
        logging.info("forex_ratio set to {}".format(self.forex_ratio))

    def set_rough_sell_amount(self, rough_sell_amount, is_usd=True):
        """Sets the internal sell amount which is used for calculating
        the spread.

        `rough_sell_amount` is only used for the spread calculation. The
        actual sell amount will be determined after the buy order has
        executed.

        NOTE: This is only valid for fiat currency with support for the
        currencies supported by the forex_python API. Will fail for
        crypto pairs.

        Args:
            rough_sell_amount (Decimal): The amount to use as a sell
                amount when calculating spreads. Only used for
                calculations, not to be used for actually executing sell
                orders.
            is_usd (bool, optional): Defaults to True. Whether
                buy_target_amount and rough_sell_amount is USD or quote
                currency.

        Raises:
            NoForexQuoteException: If forex_ratio is needed and not set.
        """
        if is_usd and self.conversion_needed:
            self.quote_rough_sell_amount = self.get_quote_from_usd(
                rough_sell_amount)
        else:
            self.quote_rough_sell_amount = rough_sell_amount

        logging.debug('{} quote_rough_sell_amount updated to: {}'.format(
            self.exchange_name, self.quote_rough_sell_amount))

    def update_wallet_balances(self):
        """Fetches and saves the wallet balances of the base and quote
        currencies on the exchange.
        """
        logging.debug("%s balances:", self.exchange_name)

        # TODO: Perhaps create DryRunFetcher to keep reference to
        # DryRunExchange to avoid introspection.
        if isinstance(self.executor, DryRunExecutor):
            self.base_bal = self.executor.dry_run_exchange.base_balance
            self.quote_bal = self.executor.dry_run_exchange.quote_balance
            logging.debug("%s: %s", self.quote, self.quote_bal)
            self.__adjust_working_balance(True)
        else:
            self.base_bal, self.quote_bal = self.fetcher.fetch_free_balances(
                self.base, self.quote)
            logging.debug("%s: %s", self.quote, self.quote_bal)
            self.__adjust_working_balance(False)

        logging.debug("%s: %s", self.base, self.base_bal)
        logging.debug("%s after adjustment: %s", self.quote, self.quote_bal)
