import logging
from decimal import Decimal

import schedule

import libs.utils.schedule_utils as schedule_utils


class FCFBalanceChecker():
    """Sell side crypto balance checker."""

    CRYPTO_BELOW_THRESHOLD_MESSAGE = (
        "Sell side crypto balance on {exchange} below {ratio} x required threshold. "
        "Consider additional deposits or locking up capital.\n"
        "Required base: {req_base} {base}\n"
        "Actual base: {act_base} {base}\n"
    )
    CRYPTO_BELOW_THRESHOLD_SCHEDULE_TAG = 'CRYPTO_BELOW_THRESHOLD'

    # Ratio required of crypto balance before balance polling and notification.
    SELL_SIDE_CRYPTO_BALANCE_BUFFER = Decimal('1.05')

    def __init__(self, trader1, trader2, notification_func):
        """Constructor."""
        self.trader1 = trader1
        self.trader2 = trader2
        self.notification_func = notification_func
        self.crypto_balance_low = False

    def __create_low_balance_msg(
            self, buy_price, buy_volume, sell_balance, sell_exchange, base):
        """Create error message if the sell exchange has a low crypto balance.

        Args:
            buy_price (Decimal): The buy price in quote currency.
            buy_volume (Decimal): The buy volume in quote currency.
            sell_balance (Decimal): The sell exchange base balance.
            sell_exchange (str): The sell exchange.
            base (str): The base asset.

        Returns:
            str: Error message if the sell exchange has a crypto balance
                below the notification threshold, None otherwise.
        """
        required_base = buy_volume / buy_price
        if required_base * self.SELL_SIDE_CRYPTO_BALANCE_BUFFER > sell_balance:
            return self.CRYPTO_BELOW_THRESHOLD_MESSAGE.format(
                ratio=self.SELL_SIDE_CRYPTO_BALANCE_BUFFER,
                exchange=sell_exchange,
                req_base=required_base,
                act_base=sell_balance,
                base=base)
        else:
            return None

    def __send_balance_warning(self):
        """Send and log low crypto balance warnings."""
        logging.warning(self.low_balance_message)
        self.notification_func(
            "SELL SIDE BALANCE BELOW THRESHOLD", self.low_balance_message)

    def check_crypto_balances(self, spread_opp):
        """Check whether balances are below threshold and notify
        operator if so.

        Args:
            spread_opp (SpreadOpportunity): The current spread
                opportunity.
        """
        e1_message = self.__create_low_balance_msg(
            spread_opp.e2_buy, self.trader2.quote_bal, self.trader1.base_bal,
            self.trader1.exchange_name, self.trader1.base)
        e2_message = self.__create_low_balance_msg(
            spread_opp.e1_buy, self.trader1.quote_bal, self.trader2.base_bal,
            self.trader2.exchange_name, self.trader2.base)

        self.low_balance_message = ''

        if e1_message is not None:
            self.low_balance_message += e1_message
        if e2_message is not None:
            self.low_balance_message += e2_message

        if self.low_balance_message != '':
            if not self.crypto_balance_low:
                self.crypto_balance_low = True
                # Schedule warning notification and execute immediately.
                schedule.every(1).hour.do(self.__send_balance_warning).tag(
                    self.CRYPTO_BELOW_THRESHOLD_SCHEDULE_TAG)
                schedule_utils.fetch_only_job(
                    self.CRYPTO_BELOW_THRESHOLD_SCHEDULE_TAG).run()
            else:
                logging.warning(self.low_balance_message)
            self.trader1.update_wallet_balances()
            self.trader2.update_wallet_balances()
        else:
            schedule.clear(tag=self.CRYPTO_BELOW_THRESHOLD_SCHEDULE_TAG)
            self.crypto_balance_low = False
