import pytest

from libs.trade.executor.dryrun_executor import DryRunExecutor

@pytest.fixture
def executor():
    return DryRunExecutor("MockBinance")


@pytest.mark.parametrize("symbol, quote_amount, asset_price, slippage", [
    pytest.param('ETH/USDT', 10000, 600, 1),
])
def test_create_emulated_market_buy_order(
        executor, symbol, quote_amount, asset_price, slippage):
    result = executor.create_emulated_market_buy_order(
            symbol, quote_amount, asset_price, slippage)
    assert(result == RESULT)



RESULT = {
    "info": {
        "symbol": 'ETH/USDT',
        "exchange": 'MockBinance',
        "price": 600,
        "executed_amount": 10000/600,
    },
    "id": "DRYRUN"
}
