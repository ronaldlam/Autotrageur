from enum import Enum
import time


# Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 60
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24
DAYS_PER_YEAR = 365
HOURS_PER_YEAR = DAYS_PER_YEAR * 24

class TimeInterval(Enum):
    """An enum for time intervals

    Args:
        Enum (int): One of:
        - Minute
        - Hour
        - Day
    """
    MINUTE = 'minute'
    HOUR = 'hour'
    DAY = 'day'

    @classmethod
    def has_value(cls, value):
        """Checks if a value is in the TimeInterval Enum.

        Args:
            value (str): A string value to check against the TimeInterval Enum.

        Returns:
            bool: True if value belongs in TimeInterval Enum. Else, false.
        """
        return any(value.lower() == item.value for item in cls)

def get_most_recent_rounded_timestamp(interval):
    """Obtains the most recent, rounded timestamp.

    Args:
        interval (str): The time interval.  One of 'day', 'hour', 'minute'.

    Returns:
        float: The most recent, rounded timestamp.
    """
    curr_time = time.time()
    if interval == TimeInterval.MINUTE.value:
        return curr_time - (curr_time % SECONDS_PER_MINUTE)
    elif interval == TimeInterval.HOUR.value:
        return curr_time - (curr_time % SECONDS_PER_HOUR)
    elif interval == TimeInterval.DAY.value:
        return curr_time - (curr_time % SECONDS_PER_DAY)
