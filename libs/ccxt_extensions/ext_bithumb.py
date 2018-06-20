import ccxt

class ext_bithumb(ccxt.bithumb):
    """Subclass of ccxt's bithumb.py for internal use.

    The name ext_bithumb is to keep similar convention when initializing
    the exchange classes.
    """

    def describe(self):
        """Return bithumb exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.bithumb() object.

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.0015,    # Without coupon.
                    'maker': 0.0015,
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
        # See tests/exploratory/test_bithumb_errors.py
        precision = {
            'BTC/KRW': {
                'base': 8,      # The precision of min execution quantity
                'quote': 0,     # The precision of min execution quantity
                'amount': 4,    # The precision of min order increment
                'price': -3,    # The precision of price in KRW
                                # 1000 KRW increment
            },
            'ETH/KRW': {
                'base': 8,
                'quote': 0,
                'amount': 4,
                'price': -3,    # Actual min increment is 500 KRW
            }
        }
        limits = {
            'BTC/KRW': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ETH/KRW': {
                'amount': {
                    'min': 0.01,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
        }

        markets = super().fetch_markets()

        for market in markets:
            if market['symbol'] in precision:
                market['precision'] = precision[market['symbol']]
            if market['symbol'] in limits:
                market['limits'] = limits[market['symbol']]

        return markets
