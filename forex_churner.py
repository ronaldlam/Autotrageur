from datetime import datetime as dt
import logging
import time

from forex_python.converter import CurrencyRates, RatesNotAvailableError

import libs.csv.csvmaker as csvmaker

# Constants.
DAYS_PER_YEAR = 365
MINUTES_TO_SECONDS = 60
HOURS_TO_SECONDS = MINUTES_TO_SECONDS * 60
DAYS_TO_SECONDS = HOURS_TO_SECONDS * 24
CSV_COL_HEADERS = ['date', 'forex_rate', 'base', 'quote']
BASE_CURRENCY = 'EUR'
QUOTE_CURRENCY = 'USD'
FOREX_PERIOD = 1 * DAYS_PER_YEAR * DAYS_TO_SECONDS #TODO: Make cmd arg
FOREX_FILENAME = "data/" + BASE_CURRENCY.lower() + QUOTE_CURRENCY.lower() + 'forexdaily.csv' # daily until we support hourly

# For debugging purposes.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")


class CurrencyConverter():
    """Converts Currencies based on forex rates"""

    def __init__(self):
        """Constructor."""
        self.converter = CurrencyRates()

    def forex_convert(self, io_price, base, quote, date=None):
        """Converts a base currency into a quote currency.

        Uses a third party library to convert a base currency into a quote
        currency.  E.g. If base is CAD and quote is USD, the price inputed
        will be converted into USD according to a CAD/USD forex rate.

        Args:
            io_price (float): The base currency's price to be converted.
            base (str): The base currency.
            quote (str): The quote currency.
            date (:obj:date, optional): The date used to determine the forex
                rate for the base/quote pair.  If no date provided, will return
                the latest forex rate.

        Returns:
            float: The converted price.
        """
        logging.log(logging.INFO, "Before conversion: %s", str(io_price))
        if io_price > 0:
            time.sleep(0.2) # Prevents exceeding api limit on fixer
            io_price = self.converter.convert(base, quote, io_price, date)
            logging.log(logging.INFO, "After conversion: %s", str(io_price))
            return io_price

if __name__ == "__main__":
    # Start time is current time for now.
    start_time = time.time()
    start_time = int(start_time - (start_time % DAYS_TO_SECONDS))
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

        # Build the KRW-USD forex dict as a row in the csv file.
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
        start_time = start_time - DAYS_TO_SECONDS

    # Write to csv file.
    csvmaker.dict_write_to_csv(
        CSV_COL_HEADERS,
        FOREX_FILENAME,
        forex_price_list)
