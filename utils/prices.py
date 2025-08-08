import os
import requests

# Default Uniswap v3 pool configuration
DEFAULT_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum"
DEFAULT_POOL_ID = "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d"


def get_eth_usdc_price() -> float:
    """Return current price of WETH in USDC.

    Fetches from Binance first, then Uniswap. Falls back to an environment
    variable or a hard-coded default if both sources fail.
    """

    # Try Binance
    try:
        headers = {}
        api_key = os.getenv("BINANCE_API_KEY")
        if api_key:
            headers["X-MBX-APIKEY"] = api_key
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "ETHUSDT"},
            headers=headers,
            timeout=10,
        )
        return float(resp.json()["price"])
    except Exception:
        pass

    # Fallback to Uniswap subgraph
    subgraph_url = os.getenv("UNISWAP_SUBGRAPH", DEFAULT_SUBGRAPH_URL)
    pool_id = os.getenv("UNISWAP_POOL_ID", DEFAULT_POOL_ID)
    query = {"query": f"{{ pool(id: \"{pool_id}\") {{ token1Price }} }}"}
    try:
        response = requests.post(subgraph_url, json=query, timeout=10)
        data = response.json()["data"]["pool"]["token1Price"]
        return float(data)
    except Exception:
        pass

    # Environment fallback or manual input
    env_fallback = os.getenv("FALLBACK_ETH_PRICE")
    if env_fallback:
        print("[WARN] Usando preço de fallback do ambiente.")
        return float(env_fallback)
    try:
        manual = float(input("Preço atual do ETH/USDC: "))
        print("[WARN] Usando preço manual fornecido.")
        return manual
    except Exception:
        print("[WARN] Usando preço de fallback padrão 2000.0")
        return 2000.0
