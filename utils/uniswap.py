"""Utilities and API client for interacting with Uniswap v3 subgraphs."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class UniswapAPI:
    """Simple wrapper around the Uniswap v3 subgraph API.

    Parameters
    ----------
    api_key:
        API key for the Graph hosted service. If ``None`` the constructor will
        look for ``UNISWAP_API_KEY`` in the environment.
    rate_limit:
        Delay, in seconds, to wait between consecutive requests in order to
        avoid hitting API rate limits.
    """

    api_key: Optional[str] = None
    rate_limit: float = 1.0

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("UNISWAP_API_KEY")
        if not self.api_key:
            raise ValueError("UNISWAP_API_KEY not configured")
        self.endpoint = (
            "https://gateway.thegraph.com/api/"
            f"{self.api_key}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
        )

    # ------------------------------------------------------------------
    def _execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a GraphQL query against the Uniswap subgraph.

        Parameters
        ----------
        query:
            GraphQL query string.
        variables:
            Optional dictionary of variables to pass with the query.

        Returns
        -------
        Optional[Dict[str, Any]]
            The ``data`` field from the JSON response or ``None`` if the
            request failed.
        """

        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.endpoint, headers=headers, data=json.dumps(payload), timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.error("Uniswap API returned errors: %s", data["errors"])
                return None
            return data.get("data")
        except requests.RequestException as exc:
            logger.error("Uniswap API request failed: %s", exc)
            return None
        finally:
            # Basic rate limiting: sleep after every request.
            time.sleep(self.rate_limit)

    # ------------------------------------------------------------------
    def get_global_data(self) -> Optional[Dict[str, Any]]:
        """Return global factory data from the subgraph."""

        query = """
        {\n          factory(id: \"0x1F98431c8aD98523631AE4a59f267346ea31F984\") {\n            poolCount\n            txCount\n            totalVolumeUSD\n            totalVolumeETH\n          }\n        }\n        """
        return self._execute_query(query)

    # ------------------------------------------------------------------
    def get_position_data(self, position_id: int) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific position by tokenId."""

        query = """
        query GetPositionData($id: Int!) {\n          position(id: $id) {\n            id\n            collectedFeesToken0\n            collectedFeesToken1\n            liquidity\n            token0 { id symbol }\n            token1 { id symbol }\n          }\n        }\n        """
        return self._execute_query(query, {"id": position_id})

    # ------------------------------------------------------------------
    def get_lp_position(self, owner: str, pool_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return the first LP position for ``owner`` in ``pool_id``.

        Parameters
        ----------
        owner:
            Wallet address that owns the position.
        pool_id:
            Address of the pool. If omitted, ``UNISWAP_POOL_ID`` from the
            environment is used.
        """

        owner = owner.lower()
        pool_id = (pool_id or os.getenv("UNISWAP_POOL_ID", "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d")).lower()

        query = """
        query GetOwnerPosition($owner: Bytes!, $pool: String!) {\n          positions(where: {owner: $owner, pool: $pool}) {\n            id\n            tickLower\n            tickUpper\n            depositedToken0\n            depositedToken1\n            token0 { symbol decimals }\n            token1 { symbol decimals }\n          }\n        }\n        """
        data = self._execute_query(query, {"owner": owner, "pool": pool_id})
        if not data:
            return None

        positions = data.get("positions") or []
        if not positions:
            return None
        p = positions[0]
        try:
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
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to parse LP position: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Helper functions used by bot logic. These functions do not perform network
# operations and therefore remain as simple utilities.
# ---------------------------------------------------------------------------


def should_reposition(price: float, lp: Dict[str, Any], fee_rate: float = 0.0005) -> bool:
    """Decide whether moving the LP range is worth the gas cost."""

    gas_cost = float(os.getenv("GAS_COST_USD", "5"))
    center = (lp["lower"] + lp["upper"]) / 2
    deviation = abs(price - center) / center
    potential_fee = lp["usdc"] * fee_rate * deviation
    return potential_fee > gas_cost or price < lp["lower"] or price > lp["upper"]


def create_lp_position(price: float, width: float = 0.05, allocation: float = 0.5) -> Dict[str, float]:
    """Solicita criação de LP em torno do preço atual."""

    lower = price * (1 - width)
    upper = price * (1 + width)
    budget = float(os.getenv("LP_BUDGET_USDC", "1000")) * allocation
    eth_amount = (budget / 2) / price
    usdc_amount = budget / 2
    logger.info(
        "[UNISWAP] Criar LP com %.6f ETH / %.2f USDC entre %.2f-%.2f",
        eth_amount,
        usdc_amount,
        lower,
        upper,
    )
    return {"lower": lower, "upper": upper, "eth": eth_amount, "usdc": usdc_amount}


def move_range(price: float, width: float = 0.05) -> Dict[str, float]:
    """Reposiciona a faixa de LP para o centro atual."""

    lower = price * (1 - width)
    upper = price * (1 + width)
    logger.info("[UNISWAP] Reposicionar faixa para %.2f-%.2f", lower, upper)
    return {"lower": lower, "upper": upper, "eth": 0, "usdc": 0}


def exit_position() -> None:
    """Remove a posição de LP atual."""

    logger.info("[UNISWAP] Encerrar posição de LP")
