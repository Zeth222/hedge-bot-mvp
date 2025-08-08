import requests

BASE_URL = "https://api.hyperliquid.xyz"


def get_eth_position(address: str, wallet=None) -> float:
    """Return ETH exposure on Hyperliquid for given address."""
    if wallet is not None and wallet.hedge_positions:
        return wallet.hedge_positions[0]["eth"]
    try:
        resp = requests.get(f"{BASE_URL}/positions?user={address}", timeout=10)
        data = resp.json()
        # Example response parsing; adjust according to real API
        for pos in data.get("positions", []):
            if pos.get("asset") == "ETH":
                return float(pos.get("size", 0))
    except Exception:
        pass
    return 0.0


def set_hedge_position(target_eth: float, price: float, simulated: bool, wallet=None) -> None:
    """Adjust hedge position to target ETH exposure."""
    if simulated and wallet is not None:
        wallet.rebalance_hedge(target_eth)
        return

    # Placeholder for real trading logic
    print(f"[HYPERLIQUID] Set hedge to {target_eth} ETH at price {price}")
