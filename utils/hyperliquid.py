"""Wrapper around the official Hyperliquid Python SDK."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from hyperliquid.info import Info


class HyperliquidAPI:
    """Read-only client that fetches data using a wallet address."""

    def __init__(self, wallet_address: Optional[str] = None) -> None:
        self.wallet_address = wallet_address or os.getenv("HYPERLIQUID_WALLET_ADDRESS")
        if not self.wallet_address:
            raise ValueError("wallet_address is required")
        try:
            self.info = Info()
        except Exception:
            self.info = None

    # ------------------------------------------------------------------
    def get_balances(self) -> Optional[Dict[str, Any]]:
        """Return wallet balances using the Info client."""

        if not self.info:
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
            return None
        try:
            if hasattr(self.info, "balances"):
                return self.info.balances(self.wallet_address)
            if hasattr(self.info, "user_state"):
                state = self.info.user_state(self.wallet_address)
                if isinstance(state, dict):
                    return state.get("balances")
                return state
        except Exception:  # pragma: no cover - defensive
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
        return None

    # ------------------------------------------------------------------
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return open position for ``symbol`` if it exists."""

        if not self.info:
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
            return None
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
        except Exception:  # pragma: no cover - defensive
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
        return None

    # ------------------------------------------------------------------
    def get_mark_price(self, symbol: str) -> Optional[float]:
        """Return current mid/mark price for ``symbol``."""

        if not self.info:
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
            return None
        try:
            if hasattr(self.info, "l2_snapshot"):
                snap = self.info.l2_snapshot(symbol.upper())
                if isinstance(snap, dict) and snap.get("mid") is not None:
                    return float(snap["mid"])
        except Exception:  # pragma: no cover - defensive
            print("[WARN] Hyperliquid API unreachable (read-only); skipping this cycle")
        return None

