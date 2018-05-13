import logging

import ccxt


class ext_gemini(ccxt.gemini):
    """Subclass of ccxt's gemini.py for internal use.

    The name ext_gemini is to keep similar convention when initializing
    the exchange classes.
    """

    def describe(self):
        """Return gemini exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.gemini() object.

        NOTE: The taker/maker fees will have to be updated every time a gemini
        account has changed trading fee schedules (tiers).  See
        https://gemini.com/trading-fee-schedule/#maker-vs-taker

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'has': {
                'createMarketOrder': 'emulated'
            },
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.01,
                    'maker': 0.01,
                },
            },
        })

    def fetch_markets(self):
        """Retrieve data for the markets of the exchange.

        This gets called by load_markets() which dynamically fetches and
        populates information about a given exchange. Precision and
        limit data is added here for consistency. The ccxt.binance()
        module was used for reference.

        Returns:
            dict: The description of available markets on the exchange.
        """
        # See https://docs.gemini.com/rest-api/#symbols-and-minimums
        precision = {
            'BTC/USD': {
                'base': 10,     # The precision of min execution quantity
                'quote': 2,     # The precision of min execution quantity
                'amount': 8,    # The precision of min order increment
                'price': 2,     # The precision of min price increment
            },
            'ETH/USD': {
                'base': 8,
                'quote': 2,
                'amount': 6,
                'price': 2,
            },
            'ETH/BTC': {
                'base': 8,
                'quote': 10,
                'amount': 6,
                'price': 5,
            }
        }
        limits = {
            'BTC/USD': {
                'amount': {
                    'min': 0.00001,     # Only min order amounts are specified
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ETH/USD': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ETH/BTC': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            }
        }

        markets = super().fetch_markets()

        for market in markets:
            market['precision'] = precision[market['symbol']]
            market['limits'] = limits[market['symbol']]

        return markets

    def prepare_emulated_market_buy_order(
            self, symbol, quote_amount, asset_price, slippage):
        """Calculate data required for the ccxt market buy order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (float): The amount to buy in quote currency.
            asset_price (float): The target buy price, quote per base.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            (float, float): Tuple of asset volume and limit price.
        """
        # Calculated volume of asset expected to be purchased.
        asset_volume = quote_amount / asset_price
        # Maximum price we are willing to pay.
        # TODO: Implement failsafes for unreasonable slippage.
        ratio = (100.0 + slippage) / 100.0
        limit_price = asset_price * ratio
        a_precision = self.markets[symbol]['precision']['amount']
        p_precision = self.markets[symbol]['precision']['price']

        # Rounding is required for direct ccxt call.
        asset_volume = round(asset_volume, a_precision)
        limit_price = round(limit_price, p_precision)

        logging.info("Gemini emulated market buy.")
        logging.info("Estimated asset price: %s" % asset_price)
        logging.info("Asset volume: %s" % asset_volume)
        logging.info("Limit price: %s" % limit_price)

        return (asset_volume, limit_price)

    def create_emulated_market_buy_order(
            self, symbol, quote_amount, asset_price, slippage):
        """Create an emulated market buy order with maximum slippage.

        This is implemented as an 'immediate or cancel' trade which will
        execute on only immediately available liquidity. If the
        calculated limit price is above the maximum fill price, a market
        order is completed immediately. If the available liquidity is
        not enough for quote_amount of the asset, only fills under the
        limit price will complete and the order will not be completely
        filled.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (float): The amount to buy in quote currency.
            asset_price (float): The target buy price, quote per base.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        (asset_volume, limit_price) = self.prepare_emulated_market_buy_order(
            symbol, quote_amount, asset_price, slippage)
        result = self.create_limit_buy_order(
            symbol,
            asset_volume,
            limit_price,
            {"options": ["immediate-or-cancel"]})
        return result

    def prepare_emulated_market_sell_order(
            self, symbol, asset_price, asset_amount, slippage):
        """Calculate data required for the ccxt market sell order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (float): The price, quote per base.
            asset_amount (float): The amount of the asset to be sold.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            (float, float): Tuple of the rounded asset amount and limit
                price.
        """
        # Minimum price we are willing to sell.
        ratio = (100.0 - slippage) / 100.0
        a_precision = self.markets[symbol]['precision']['amount']
        p_precision = self.markets[symbol]['precision']['price']
        rounded_amount = round(asset_amount, a_precision)
        rounded_limit_price = round(asset_price * ratio, p_precision)

        logging.info("Gemini emulated market sell.")
        logging.info("Estimated asset price: %s" % asset_price)
        logging.info("Asset volume: %s" % rounded_amount)
        logging.info("Limit price: %s" % rounded_limit_price)

        return (rounded_amount, rounded_limit_price)

    def create_emulated_market_sell_order(
            self, symbol, asset_price, asset_amount, slippage):
        """Create an emulated market sell order with maximum slippage.

        This is implemented as an 'immediate or cancel' trade which will
        execute on only immediately available liquidity. If the
        calculated limit price is below the minimum fill price, a market
        order is completed immediately. If the available liquidity is
        not enough for asset_amount of the asset, only fills over the
        limit price will complete and the order will not be completely
        filled.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (float): The price, quote per base.
            asset_amount (float): The amount of the asset to be sold.
            slippage (float): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        (rounded_amount, rounded_limit_price) = (
            self.prepare_emulated_market_sell_order(
                symbol, asset_price, asset_amount, slippage))
        result = self.create_limit_sell_order(
            symbol,
            rounded_amount,
            rounded_limit_price,
            {"options": ["immediate-or-cancel"]})
        return result
