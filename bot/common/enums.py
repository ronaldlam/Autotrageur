from enum import Enum

class Momentum(Enum):
    """An enum describing the momentum/direction of the last trade.

    Args:
        Enum (int): One of 'TO_E2', 'NEUTRAL', 'TO_E1' where:
            - NEUTRAL: Momentum should only be neutral at the beginning.
            - TO_E2: Momentum going towards Exchange 2.
            - TO_E1: Momentum going towards Exchange 1.
    """
    TO_E2 = 1
    NEUTRAL = 0
    TO_E1 = -1
