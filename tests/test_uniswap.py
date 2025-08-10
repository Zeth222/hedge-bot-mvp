import os

from utils.uniswap import UniswapClient, POOL_WETH_USDC_005


def test_get_pool_state():
    client = UniswapClient(os.getenv("RPC_URL_ARBITRUM", "https://arb1.arbitrum.io/rpc"))
    state = client.get_pool_state(POOL_WETH_USDC_005)
    assert state["sqrtPriceX96"] > 0
    assert isinstance(state["tick"], int)
