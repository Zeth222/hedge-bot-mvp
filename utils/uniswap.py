import os
import requests

SUBGRAPH_URL = os.getenv(
    "UNISWAP_SUBGRAPH",
    "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum",
)
POOL_ID = os.getenv(
    "UNISWAP_POOL_ID",
    "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d",
)


def get_lp_position(address: str):
    """Fetch LP position for address from Uniswap v3 subgraph."""
    address = address.lower()
    query = {
        "query": (
            "query($owner: Bytes!) { positions(where: {owner: $owner, pool: \"%s\"}) { "
            "id tickLower tickUpper depositedToken0 depositedToken1 "
            "token0 { symbol decimals } token1 { symbol decimals } } }"
            % POOL_ID
        ),
        "variables": {"owner": address},
    }
    try:
        resp = requests.post(SUBGRAPH_URL, json=query, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        positions = data.get("positions", [])
        if positions:
            p = positions[0]
            dec0 = 10 ** int(p["token0"]["decimals"])
            dec1 = 10 ** int(p["token1"]["decimals"])
            amt0 = float(p["depositedToken0"]) / dec0
            amt1 = float(p["depositedToken1"]) / dec1
            if p["token0"]["symbol"].upper() in ("USDC", "USDT"):
                usdc, eth = amt0, amt1
            else:
                usdc, eth = amt1, amt0
            return {
                "lower": int(p["tickLower"]),
                "upper": int(p["tickUpper"]),
                "usdc": usdc,
                "eth": eth,
            }
    except Exception as exc:
        print(f"[WARN] Uniswap LP fetch failed: {exc}")
    return None


def should_reposition(price: float, lp: dict, fee_rate: float = 0.0005) -> bool:
    """Decide whether moving the LP range is worth the gas cost."""
    gas_cost = float(os.getenv("GAS_COST_USD", "5"))
    center = (lp["lower"] + lp["upper"]) / 2
    deviation = abs(price - center) / center
    potential_fee = lp["usdc"] * fee_rate * deviation
    return potential_fee > gas_cost or price < lp["lower"] or price > lp["upper"]


def create_lp_position(price: float, width: float = 0.05, allocation: float = 0.5):
    """Solicita criação de LP em torno do preço atual."""
    lower = price * (1 - width)
    upper = price * (1 + width)
    budget = float(os.getenv("LP_BUDGET_USDC", "1000")) * allocation
    eth_amount = (budget / 2) / price
    usdc_amount = budget / 2
    print(
        f"[UNISWAP] Criar LP com {eth_amount} ETH / {usdc_amount} USDC entre {lower}-{upper}"
    )
    return {"lower": lower, "upper": upper, "eth": eth_amount, "usdc": usdc_amount}


def move_range(price: float, width: float = 0.05):
    """Reposiciona a faixa de LP para o centro atual."""
    lower = price * (1 - width)
    upper = price * (1 + width)
    print(f"[UNISWAP] Reposicionar faixa para {lower}-{upper}")
    return {"lower": lower, "upper": upper, "eth": 0, "usdc": 0}


def exit_position():
    """Remove a posição de LP atual."""
    print("[UNISWAP] Encerrar posição de LP")
