import os
import requests

# URLs e identificadores padrão do subgrafo Uniswap v3
DEFAULT_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum"
DEFAULT_POOL_ID = "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d"


def get_eth_usdc_price() -> float:
    """Obtém o preço do par ETH/USDC.

    A busca é feita em múltiplas fontes, em ordem de prioridade:
    1. API pública da Coinbase
    2. Subgrafo do Uniswap v3

    Se todas falharem, utiliza ETH_PRICE_FALLBACK ou lança exceção.
    """

    # 1) Tentativa via Coinbase
    try:
        resp = requests.get(
            "https://api.coinbase.com/v2/prices/ETH-USD/spot",
            timeout=10,
        )
        resp.raise_for_status()
        return float(resp.json()["data"]["amount"])
    except Exception as exc:
        print(f"[WARN] Coinbase price unavailable: {exc}")

    # 2) Tentativa via subgrafo do Uniswap
    subgraph_url = os.getenv("UNISWAP_SUBGRAPH", DEFAULT_SUBGRAPH_URL)

    # 2a) bundle com preço do ETH em USD (instrução oficial do Uniswap)
    try:
        bundle_query = {"query": "{ bundle(id: \"1\") { ethPriceUSD } }"}
        response = requests.post(subgraph_url, json=bundle_query, timeout=10)
        response.raise_for_status()
        price = response.json()["data"]["bundle"]["ethPriceUSD"]
        if price:
            return float(price)
    except Exception as exc:
        print(f"[WARN] Uniswap bundle price unavailable: {exc}")

    # 2b) fallback via pool específica WETH/USDC
    pool_id = os.getenv("UNISWAP_POOL_ID", DEFAULT_POOL_ID)
    pool_query = {
        "query": (
            "{ pool(id: \"%s\") { token0 { symbol } token1 { symbol } token0Price token1Price } }"
            % pool_id
        )
    }
    try:
        response = requests.post(subgraph_url, json=pool_query, timeout=10)
        response.raise_for_status()
        payload = response.json().get("data", {}).get("pool")
        if not payload:
            raise ValueError("pool data missing")
        t0 = payload["token0"]["symbol"].upper()
        t1 = payload["token1"]["symbol"].upper()
        if t0 == "WETH" and t1 in ("USDC", "USDT"):
            return float(payload["token0Price"])
        if t1 == "WETH" and t0 in ("USDC", "USDT"):
            return float(payload["token1Price"])
        raise ValueError("unexpected pool tokens")
    except Exception as exc:
        print(f"[WARN] Uniswap pool price unavailable: {exc}")

    # 3) Fallback via variável de ambiente
    fallback = os.getenv("ETH_PRICE_FALLBACK")
    if fallback:
        try:
            price = float(fallback)
            print("[INFO] Using fallback ETH price from environment")
            return price
        except ValueError:
            print(f"[WARN] Invalid ETH_PRICE_FALLBACK value: {fallback}")

    # Caso todas as fontes falhem, interrompe a execução
    raise RuntimeError("Não foi possível obter o preço ETH/USDC")
