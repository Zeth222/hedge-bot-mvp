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


def create_lp_position(wallet, price: float, width: float = 0.05, allocation: float = 0.5):
    """Create LP position around current price using wallet USDC balance."""
    lower = price * (1 - width)
    upper = price * (1 + width)
    eth_amount = 0.0
    usdc_amount = 0.0
    if wallet is not None:
        budget = wallet.usdc_balance * allocation
        usdc_for_eth = budget / 2
        wallet.swap("USDC", "ETH", usdc_for_eth, price)
        eth_amount = usdc_for_eth / price
        usdc_amount = budget - usdc_for_eth
        wallet.create_lp_position(lower, upper, eth_amount, usdc_amount)
    else:
        budget = 1000.0 * allocation
        eth_amount = (budget / 2) / price
        usdc_amount = budget / 2
        print(
            f"[UNISWAP] Would create LP with {eth_amount} ETH / {usdc_amount} USDC between {lower}-{upper}"
        )
    return {"lower": lower, "upper": upper, "eth": eth_amount, "usdc": usdc_amount}


def move_range(wallet, price: float, width: float = 0.05):
    """Move LP range to be centered around current price."""
    lower = price * (1 - width)
    upper = price * (1 + width)
    if wallet is None:
        print(f"[UNISWAP] Would move range to {lower}-{upper}")
        return {"lower": lower, "upper": upper, "eth": 0, "usdc": 0}
    if not wallet.lp_positions:
        return create_lp_position(wallet, price, width)
    lp = wallet.lp_positions[0]
    wallet.lp_positions[0] = {
        "lower": lower,
        "upper": upper,
        "eth": lp["eth"],
        "usdc": lp["usdc"],
    }
    print(f"[SIM] Range moved to {lower}-{upper}")
    return wallet.lp_positions[0]


def exit_position(wallet):
    if wallet is None:
        print("[UNISWAP] Would exit LP position")
        return
    if wallet.lp_positions:
        pos = wallet.lp_positions.pop(0)
        wallet.eth_balance += pos["eth"]
        wallet.usdc_balance += pos["usdc"]
        print("[SIM] LP position exited")
