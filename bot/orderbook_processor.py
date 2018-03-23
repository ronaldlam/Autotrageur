def get_price_from_orderbook(bids_or_asks, target_amount):
    """Get market buy or sell price

    Return potential market buy or sell price given bids or asks and
    amount to be sold. Input of bids will retrieve market sell price;
    input of asks will retrieve market buy price.

    Args:
        bids_or_asks (list[(int, int)]): The bids or asks in the form of
            (price, volume).
        target_amount (int): The amount to prospectively market buy.

    Returns:
        float: Prospective price of a market sell.

    Raises:
        RuntimeError: If the orderbook is not deep enough.
    """

    index = 0
    asset_amount = 0.0
    original_amount = target_amount

    # Subtract from amount until enough of the order book is eaten up by
    # the trade.
    while target_amount > 0.0 and index < len(bids_or_asks):
        target_amount -= bids_or_asks[index][0] * bids_or_asks[index][1]
        asset_amount += bids_or_asks[index][1]
        index += 1

    if index == len(bids_or_asks) and target_amount > 0.0:
        raise RuntimeError("Order book not deep enough for trade.")

    # Add the zero or negative excess amount to trim off the overshoot
    asset_amount += target_amount / bids_or_asks[index - 1][0]

    return original_amount/asset_amount
