from collections import namedtuple


class CCConfiguration(namedtuple('CCConfiguration', [
        'addresses', 'dryrun', 'dryrun_e1_base', 'dryrun_e1_quote',
        'dryrun_e2_base', 'dryrun_e2_quote', 'email_cfg_path', 'exchange1',
        'exchange1_pair', 'exchange2', 'exchange2_pair', 'use_test_api',
        'id', 'max_trade_size', 'poll_wait_default', 'poll_wait_short',
        'slippage', 'spread_min', 'start_timestamp', 'twilio_cfg_path'])):
    """Holds all of the configuration for the autotrageur bot.

    Args:
        addresses (dict): Dictionary of asset addresses.
        dryrun (bool): If True, this bot's run is considered to be a dry run
            against fake exchange objects and no real trades are performed.
        dryrun_e1_base (str): In dry run, the base used for exchange one.
        dryrun_e1_quote (str): In dry run, the quote used for exchange one.
        dryrun_e2_base (str): In dry run, the base used for exchange two.
        dryrun_e2_quote (str): In dry run, the quote used for exchange two.
        email_cfg_path (str): Path to the email config file, used for sending
            notifications.
        exchange1 (str): Name of exchange one.
        exchange1_pair (str): Symbol of the pair to use for exchange one.
        exchange2 (str): Name of the exchange two.
        exchange2_pair (str): Symbol of the pair to use for exchange two.
        use_test_api (bool): If True, will use the test APIs for both
            exchanges.
        id (str): The unique id tagged to the current configuration and bot
            run.  This is not provided from the config file and set during
            initialization.
        max_trade_size (float): The maximum USD value of any given trade.
        poll_wait_default (int): Default waiting time (in seconds) in between
            polls.
        poll_wait_short (int): The shortened poll waiting time (in seconds),
            used when trade is chunked and in progress.
        slippage (float): Percentage downside of limit order slippage tolerable
            for market order emulations.
        spread_min (float): The minimum spread increment for considering trade
            targets.
        start_timestamp (float): The unix timestamp tagged against the current
            bot run.  This is not provided from the config file and set during
            initialization.
        twilio_cfg_path (str): Path for the twilio config file, used for
            sending notifications.
    """
    __slots__ = ()
