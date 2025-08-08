import os
import requests

# Uniswap v3 pool configuration
SUBGRAPH_URL = os.getenv(
    "UNISWAP_SUBGRAPH",
    "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum",
)
POOL_ID = os.getenv(
    "UNISWAP_POOL_ID",
    "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d",
)


def get_eth_usdc_price() -> float:
    """Return current price of WETH in USDC using the Uniswap v3 subgraph."""
    query = {
        "query": f"{{ pool(id: \"{POOL_ID}\") {{ token1Price }} }}"
    }
    try:
        response = requests.post(SUBGRAPH_URL, json=query, timeout=10)
        data = response.json()["data"]["pool"]["token1Price"]
        return float(data)
    except Exception:
        # Fallback using Binance price if subgraph fails
        try:
            resp = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "ETHUSDT"},
                timeout=10,
            )
            return float(resp.json()["price"])
        except Exception:
            # Final fallback to environment variable or default value
            fallback = os.getenv("FALLBACK_ETH_PRICE", "2000")
            return float(fallback)
