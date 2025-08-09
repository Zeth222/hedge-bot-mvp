import os
import requests

# URLs e identificadores padrão do subgrafo Uniswap v3
DEFAULT_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum"
DEFAULT_POOL_ID = "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d"


def get_eth_usdc_price() -> float:
    """Obtém o preço do par ETH/USDC.

    A busca é feita em múltiplas fontes, em ordem de prioridade:
    1. API pública da Binance
    2. Subgrafo do Uniswap v3

    Se ambas falharem, uma exceção é lançada.
    """

    # 1) Tentativa via Binance
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
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as exc:
        print(f"[WARN] Binance price unavailable: {exc}")

    # 2) Tentativa via subgrafo do Uniswap
    subgraph_url = os.getenv("UNISWAP_SUBGRAPH", DEFAULT_SUBGRAPH_URL)
    pool_id = os.getenv("UNISWAP_POOL_ID", DEFAULT_POOL_ID)
    query = {"query": f"{{ pool(id: \"{pool_id}\") {{ token1Price }} }}"}
    try:
        response = requests.post(subgraph_url, json=query, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]["pool"]["token1Price"]
        return float(data)
    except Exception as exc:
        print(f"[WARN] Uniswap price unavailable: {exc}")

    # Caso todas as fontes falhem, interrompe a execução
    raise RuntimeError("Não foi possível obter o preço ETH/USDC")
