"""Client utilities for interacting with the Hyperliquid API via the official SDK."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import get_account

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hyperliquid.xyz"


@dataclass
class HyperliquidAPI:
    """Thin wrapper around the Hyperliquid Python SDK."""

    wallet_address: str
    private_key: Optional[str] = None
    base_url: str = BASE_URL
    rate_limit: float = 1.0

    def __post_init__(self) -> None:
        self.info_client = Info(base_url=self.base_url)
        self.exchange_client = (
            Exchange(get_account(self.private_key), base_url=self.base_url)
            if self.private_key
            else None
        )

    # ------------------------------------------------------------------
    def _rate_limit(self) -> None:
        time.sleep(self.rate_limit)

    # ------------------------------------------------------------------
    def get_eth_position(self) -> float:
        """Return the current ETH exposure for ``wallet_address``."""

        try:
            positions: Any = self.info_client.positions(self.wallet_address)
            for pos in positions or []:
                coin = pos.get("coin") or pos.get("asset")
                if coin == "ETH":
                    size = pos.get("position", {}).get("szi") or pos.get("size", 0)
                    return float(size)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Hyperliquid position fetch failed: %s", exc)
        finally:
            self._rate_limit()
        return 0.0

    # ------------------------------------------------------------------
    def get_user_open_orders(self) -> Optional[Dict[str, Any]]:
        """Retrieve open orders for the configured wallet."""

        try:
            return self.info_client.open_orders(self.wallet_address)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Hyperliquid open orders fetch failed: %s", exc)
            return None
        finally:
            self._rate_limit()

    # ------------------------------------------------------------------
    def get_user_fills(self) -> Optional[Dict[str, Any]]:
        """Retrieve recent fills for the configured wallet."""

        try:
            return self.info_client.fills(self.wallet_address)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Hyperliquid fills fetch failed: %s", exc)
            return None
        finally:
            self._rate_limit()

    # ------------------------------------------------------------------
    def set_hedge_position(self, target_eth: float, price: float, leverage: float = 5.0) -> None:
        """Adjust hedge position to match ``target_eth`` exposure.

        This method is intentionally simplified and acts as a placeholder. A real
        implementation would place or cancel orders using ``self.exchange_client``.
        """

        if not self.exchange_client:
            logger.warning("Exchange client not configured; cannot send orders")
            return
        logger.info(
            "[HYPERLIQUID] Set hedge to %.4f ETH at %.2f (leverage %.1f)",
            target_eth,
            price,
            leverage,
        )
        # Placeholder: real trading logic would go here
        self._rate_limit()
