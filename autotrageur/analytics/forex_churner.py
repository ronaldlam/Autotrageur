import os
import sys
import inspect

# Add parent dir onto the sys.path.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from datetime import datetime as dt
import logging
import time

from forex_python.converter import CurrencyRates, RatesNotAvailableError

import fp_libs.csv.csvmaker as csvmaker
from fp_libs.time_utils import SECONDS_PER_DAY, DAYS_PER_YEAR


# Constants.
CSV_COL_HEADERS = ['date', 'forex_rate', 'base', 'quote']
BASE_CURRENCY = 'EUR'
QUOTE_CURRENCY = 'USD'
FOREX_PERIOD = 1 * DAYS_PER_YEAR * SECONDS_PER_DAY #TODO: Make cmd arg
FOREX_FILENAME = "data/" + BASE_CURRENCY.lower() + QUOTE_CURRENCY.lower() + 'forexdaily.csv' # daily until we support hourly

# Rate limiting counter and timer.  Fixer.io API seems to be 5 requests/sec max:
# https://github.com/fixerAPI/fixer/issues/59
REQ_COUNTER = 0
REQ_TIMER = time.time()

# For debugging purposes.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

class NegativeAmountException(Exception):
    """Thrown when trying to convert an amount less than 0

    NOTE: This is because the forex_python library will throw a misleading
    exception if trying to convert an amount of less than 0.
    """
    pass


class CurrencyConverter():
    """Converts Currencies based on forex rates"""

    def __init__(self):
        """Constructor."""
        self.converter = CurrencyRates()

    def _rate_limit(self):
        """Rate limit according to APIs restriction.

        Will increment the global request counter if less than 5.  Or resets it
        to 1 if at 5.  If exceeding the APIs restriction, will wait until API
        restriction is met.
        """
        global REQ_COUNTER
        global REQ_TIMER

        if REQ_COUNTER is 5:
            timediff = time.time() - REQ_TIMER
            if (timediff < 1):
                logging.log(logging.INFO, "Rate limit hit, sleep for 1 second")
                # NOTE: Looks like sleeping for a whole second makes it far
                # less likely to encounter rate limit and causing RatesNotAvailableError
                # to be thrown below.
                time.sleep(1)

        # Increment counter if less than 5, or reset to 1.
        REQ_COUNTER = REQ_COUNTER + 1 if REQ_COUNTER < 5 else 1
        if REQ_COUNTER is 1:
            REQ_TIMER = time.time()

    def forex_convert(self, price, base, quote, date=None):
        """Converts a base currency into a quote currency.

        Uses a third party library to convert a base currency into a quote
        currency.  E.g. If base is CAD and quote is USD, the price inputted
        will be converted into USD according to a CAD/USD forex rate.

        Note: Requires a price >= 0 for the API to convert.

        Args:
            price (float): The base currency's price to be converted.
            base (str): The base currency.
            quote (str): The quote currency.
            date (:obj:date, optional): The date used to determine the forex
                rate for the base/quote pair.  If no date provided, will return
                the latest forex rate.

        Raises:
            NegativeAmountException: Thrown when the price to be converted is
                less than 0.

        Returns:
            float: The converted price.
        """
        logging.log(logging.INFO, "Before conversion: %s", str(price))
        if price < 0:
            raise NegativeAmountException("Price cannot be less than 0")
        self._rate_limit()
        price = self.converter.convert(base, quote, price, date)
        logging.log(logging.INFO, "After conversion: %s", str(price))
        return price

if __name__ == "__main__":
    # Start time is current time for now.
    start_time = time.time()
    start_time = int(start_time - (start_time % SECONDS_PER_DAY))
    end_time = start_time - FOREX_PERIOD
    logging.log(logging.INFO, "End date: %s",
        dt.utcfromtimestamp(end_time).strftime('%Y-%m-%d'))

    forex_price_list = []
    while start_time >= end_time:
        currency_converter = CurrencyConverter()
        start_time_datetime = dt.utcfromtimestamp(start_time)
        logging.log(logging.INFO, "Start date: %s",
            start_time_datetime.strftime('%Y-%m-%d'))
        forex_row = {}

        # Build the forex dict as a row in the csv file.
        forex_row[CSV_COL_HEADERS[0]] = start_time
        try:
            forex_row[CSV_COL_HEADERS[1]] = currency_converter.forex_convert(1,
                BASE_CURRENCY, QUOTE_CURRENCY, start_time_datetime)
        except RatesNotAvailableError as e:
            logging.log(logging.INFO, "Pausing and retrying forex conversion \
                in case api being flakey.")
            time.sleep(5)
            forex_row[CSV_COL_HEADERS[1]] = currency_converter.forex_convert(1,
                BASE_CURRENCY, QUOTE_CURRENCY, start_time_datetime)
        forex_row[CSV_COL_HEADERS[2]] = BASE_CURRENCY
        forex_row[CSV_COL_HEADERS[3]] = QUOTE_CURRENCY
        forex_price_list.insert(0, forex_row)
        start_time = start_time - SECONDS_PER_DAY

    # Write to csv file.
    # TODO: Consider batching up writes to avoid size limitations with large
    # datasets
    csvmaker.dict_write_to_csv(
        CSV_COL_HEADERS,
        FOREX_FILENAME,
        forex_price_list)
