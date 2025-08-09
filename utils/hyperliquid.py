import requests

BASE_URL = "https://api.hyperliquid.xyz"


def get_eth_position(address: str) -> float:
    """Return ETH exposure on Hyperliquid for given address."""
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


def set_hedge_position(target_eth: float, price: float, leverage: float = 5.0) -> None:
    """Adjust hedge position to target ETH exposure."""
    # Placeholder for real trading logic
    print(f"[HYPERLIQUID] Set hedge to {target_eth} ETH at price {price}")
