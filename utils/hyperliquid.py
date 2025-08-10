"""Wrapper around the official Hyperliquid Python SDK."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange


class HyperliquidAPI:
    """Simple API client loading credentials from environment variables."""

    def __init__(self, wallet_address: Optional[str] = None) -> None:
        self.wallet_address = wallet_address or os.getenv("WALLET_ADDRESS")
        self.api_key = os.getenv("HYPERLIQUID_API_KEY")
        self.api_secret = os.getenv("HYPERLIQUID_API_SECRET")
        self.info = Info()
        self.exchange: Optional[Exchange] = None
        if self.api_key and self.api_secret:
            try:
                self.exchange = Exchange(self.api_key, self.api_secret)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[HYPERLIQUID] Failed to init exchange: {exc}")

    # ------------------------------------------------------------------
    def get_balances(self) -> Optional[Dict[str, Any]]:
        """Return wallet balances using the Info client."""

        try:
            if hasattr(self.info, "balances"):
                return self.info.balances(self.wallet_address)
            if hasattr(self.info, "user_state"):
                state = self.info.user_state(self.wallet_address)
                if isinstance(state, dict):
                    return state.get("balances")
                return state
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[HYPERLIQUID] balance error: {exc}")
        return None

    # ------------------------------------------------------------------
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return open position for ``symbol`` if it exists."""

        try:
            positions = None
            if hasattr(self.info, "positions"):
                positions = self.info.positions(self.wallet_address)
            elif hasattr(self.info, "user_state"):
                state = self.info.user_state(self.wallet_address)
                if isinstance(state, dict):
                    positions = state.get("positions")
            for pos in positions or []:
                coin = (pos.get("coin") or pos.get("symbol") or "").upper()
                if coin == symbol.upper():
                    return pos
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[HYPERLIQUID] position error: {exc}")
        return None

    # ------------------------------------------------------------------
    def ensure_hedge(self, symbol: str, target_size: float) -> None:
        """Adjust position in ``symbol`` towards ``target_size``."""

        pos = self.get_position(symbol)
        current = float(pos.get("szi") or pos.get("size") or 0) if pos else 0.0
        diff = target_size - current
        if abs(diff) < 1e-8:
            print(f"[HYPERLIQUID] Hedge for {symbol} already at target ({current})")
            return
        if not self.exchange:
            print(f"[HYPERLIQUID] Would adjust {symbol} by {diff}; exchange not configured")
            return
        try:
            side = "buy" if diff > 0 else "sell"
            size = abs(diff)
            if hasattr(self.exchange, "market_order"):
                self.exchange.market_order(symbol, side, size)
            elif hasattr(self.exchange, "order"):
                self.exchange.order(symbol, side, size)
            else:  # pragma: no cover - defensive
                print("[HYPERLIQUID] Exchange client missing order method; skipping")
                return
            print(f"[HYPERLIQUID] Submitted {side} order for {size} {symbol}")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[HYPERLIQUID] ensure_hedge error: {exc}")

    # ------------------------------------------------------------------
    def close_position(self, symbol: str) -> None:
        """Close any open position for ``symbol``."""

        self.ensure_hedge(symbol, 0.0)

