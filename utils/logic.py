"""Basic bot logic combining Uniswap and Hyperliquid clients."""

from __future__ import annotations

from .uniswap import UniswapClient, POOL_WETH_USDC_005
from .hyperliquid import HyperliquidAPI


class BotLogic:
    """Simple loop that reads price data and maintains a hedge."""

    def __init__(self, uniswap: UniswapClient, hyperliquid: HyperliquidAPI):
        self.uniswap = uniswap
        self.hyperliquid = hyperliquid

    def check_and_hedge(self) -> None:
        """Print pool state, quote price and adjust hedge if needed."""

        try:
            state = self.uniswap.get_pool_state(POOL_WETH_USDC_005)
            print(
                f"Pool sqrtPriceX96={state['sqrtPriceX96']} tick={state['tick']}"
            )
        except Exception as exc:
            print(f"[LOGIC] Failed to fetch pool state: {exc}")
            return

        try:
            quote = self.uniswap.get_quote_weth_usdc(10**18)
            print(f"Quote 1 WETH -> {quote['amountOut']} USDC")
        except Exception as exc:
            print(f"[LOGIC] Failed to fetch quote: {exc}")

        # Example strategy: stay delta neutral (no open position)
        self.hyperliquid.ensure_hedge("ETH", 0.0)

