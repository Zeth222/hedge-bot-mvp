import os
import requests

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum"
POOL_ID = "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d"  # WETH/USDC 0.05%


def get_lp_position(address: str):
    """Fetch LP position for address from Uniswap v3 subgraph."""
    address = address.lower()
    query = {
        "query": (
            "query($owner: String!) { positions(where: {owner: $owner, pool: \"%s\"}) { "
            "id tickLower tickUpper depositedToken0 depositedToken1 }}"
            % POOL_ID
        ),
        "variables": {"owner": address},
    }
    try:
        resp = requests.post(SUBGRAPH_URL, json=query, timeout=10)
        positions = resp.json()["data"]["positions"]
        if positions:
            p = positions[0]
            return {
                "lower": int(p["tickLower"]),
                "upper": int(p["tickUpper"]),
                "usdc": float(p["depositedToken0"]) / 1e6,
                "eth": float(p["depositedToken1"]) / 1e18,
            }
    except Exception:
        pass
    return None


def create_lp_position(wallet, price: float, width: float = 0.05):
    """Create LP position around current price."""
    lower = price * (1 - width)
    upper = price * (1 + width)
    eth_amount = 1.0
    usdc_amount = eth_amount * price
    wallet.create_lp_position(lower, upper, eth_amount, usdc_amount)
    return {"lower": lower, "upper": upper, "eth": eth_amount, "usdc": usdc_amount}


def move_range(wallet, price: float, width: float = 0.05):
    """Move LP range to be centered around current price."""
    if not wallet.lp_positions:
        return create_lp_position(wallet, price, width)
    lp = wallet.lp_positions[0]
    wallet.lp_positions[0] = {
        "lower": price * (1 - width),
        "upper": price * (1 + width),
        "eth": lp["eth"],
        "usdc": lp["usdc"],
    }
    print(f"[SIM] Range moved to {price * (1 - width)}-{price * (1 + width)}")
    return wallet.lp_positions[0]


def exit_position(wallet):
    if wallet.lp_positions:
        pos = wallet.lp_positions.pop(0)
        wallet.eth_balance += pos["eth"]
        wallet.usdc_balance += pos["usdc"]
        print("[SIM] LP position exited")
