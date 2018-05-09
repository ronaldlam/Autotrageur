from enum import Enum

class SpreadOpportunity(Enum):
    """An enum for spread opportunity classification.

    Args:
        Enum (str): One of:
        - high (forward spread opportunity)
        - low (reverse spread opportunity)
    """
    HIGH = 'high',
    LOW = 'low'