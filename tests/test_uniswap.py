import os
import pytest

from utils.uniswap import (
    UniswapClient,
    POOL_WETH_USDC_005,
    get_web3_client,
    RpcUnavailable,
)


@pytest.mark.skipif(os.getenv("OFFLINE") == "1", reason="offline")
def test_get_pool_state():
    rpc = os.getenv("RPC_URL_ARBITRUM", "https://arb1.arbitrum.io/rpc")
    fallbacks = os.getenv("RPC_FALLBACKS", "")
    try:
        w3 = get_web3_client(rpc, fallbacks)
    except RpcUnavailable:
        pytest.skip("no RPC available")
    if not w3.is_connected():  # pragma: no cover - defensive
        pytest.skip("no RPC available")
    client = UniswapClient(rpc_url=rpc, fallbacks=fallbacks)
    state = client.get_pool_state(POOL_WETH_USDC_005)
    assert state["sqrtPriceX96"] > 0
    assert isinstance(state["tick"], int)
