"""Basic bot logic combining Uniswap and Hyperliquid clients."""

from __future__ import annotations

from .uniswap import UniswapClient, POOL_WETH_USDC_005, RpcUnavailable
from .hyperliquid import HyperliquidAPI


class BotLogic:
    """Monitor pool state and Hyperliquid position and raise alerts."""

    def __init__(
        self,
        uniswap: UniswapClient | None,
        hyperliquid: HyperliquidAPI,
        lp_token_id: int | None = None,
        alert_ticks: int = 100,
    ) -> None:
        self.uniswap = uniswap
        self.hyperliquid = hyperliquid
        self.lp_token_id = lp_token_id
        self.alert_ticks = alert_ticks

    def check_and_alert(self) -> None:
        """Print pool state and warn if near LP bounds."""

        tick = None
        if self.uniswap is not None:
            try:
                state = self.uniswap.get_pool_state(POOL_WETH_USDC_005)
                tick = state["tick"]
                print(f"Pool sqrtPriceX96={state['sqrtPriceX96']} tick={tick}")
            except RpcUnavailable:
                raise
            except Exception as exc:
                print(f"[LOGIC] Failed to fetch pool state: {exc}")
        else:
            print("[LOGIC] Skipping pool state (no RPC)")

        pos = self.hyperliquid.get_position("ETH")
        print(f"Hyperliquid position: {pos}")

        if tick is not None and self.lp_token_id is not None and self.uniswap is not None:
            try:
                lower, upper = self.uniswap.get_position_bounds(self.lp_token_id)
                if tick <= lower + self.alert_ticks:
                    print("[ALERT] Price near lower bound")
                elif tick >= upper - self.alert_ticks:
                    print("[ALERT] Price near upper bound")
            except RpcUnavailable:
                raise
            except Exception as exc:
                print(f"[LOGIC] Failed to fetch position bounds: {exc}")

