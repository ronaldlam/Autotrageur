import logging

from libs.constants.decimal_constants import ZERO


class FCFTradeChunker():
    """Class to encapsulate trade chunking logic."""

    def __init__(self, max_trade_size):
        """Constructor.

        Args:
            max_trade_size (Decimal): The maximum trade size per poll in
                USD.
        """
        self._max_trade_size = max_trade_size
        self._target = None
        self._current_trade_size = ZERO
        self.trade_completed = True

    def finalize_trade(self, post_fee_cost, min_trade_size):
        """Update the current trade execution progress.

        Args:
            post_fee_cost (Decimal): The executed USD amount on the buy
                exchange.
            min_trade_size (Decimal): The minimum USD amount that the
                exchanges support.
        """
        self._current_trade_size += post_fee_cost
        self.trade_completed = (
            self._target - self._current_trade_size < min_trade_size)
        logging.info('Chunk traded:')
        logging.info('Total target: {}'.format(self._target))
        logging.info('Current traded: {}'.format(self._current_trade_size))
        logging.info('Configured trade size: {}'.format(self._max_trade_size))
        logging.info('Executed trade size: {}'.format(post_fee_cost))
        logging.info('Trade completed: {}'.format(self.trade_completed))

    def get_next_trade(self):
        """Fetch the next trade target volume.

        Returns:
            Decimal: The next trade target amount in USD.
        """
        # 5) Is it possible for remaining to become negative here, or is it
        # implicitly guarded against because finalize_trade will never be hit?
        remaining = self._target - self._current_trade_size
        return min(self._max_trade_size, remaining)

    def reset(self, target):
        """Reset the state of the chunker with the given target.

        NOTE: Must be called before use of chunker.

        Args:
            target (Decimal): The total trade target.
        """
        # 4) Target set to 0.
        self._target = target
        self._current_trade_size = ZERO
        self.trade_completed = False
