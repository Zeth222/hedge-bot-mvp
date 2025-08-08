import os
from datetime import datetime
from .prices import get_eth_usdc_price
from .uniswap import (
    get_lp_position,
    create_lp_position,
    move_range,
    should_reposition,
)
from .hyperliquid import get_eth_position, set_hedge_position
from .telegram import send_telegram_message


class BotLogic:
    def __init__(self, wallet, address: str, simulated: bool = True):
        self.wallet = wallet
        self.address = address
        self.simulated = simulated

    def run_cycle(self):
        price = get_eth_usdc_price()

        lp = get_lp_position(self.address)
        if lp and self.wallet is not None and not self.wallet.lp_positions:
            self.wallet.lp_positions.append(lp)
            ts = datetime.utcnow().strftime("%H:%M:%S")
            send_telegram_message(
                f"[{ts}] LP existente detectada {lp['lower']:.2f}-{lp['upper']:.2f}"
            )

        if not lp:
            alloc = float(os.getenv("LP_ALLOCATION", "0.5"))
            lp = create_lp_position(self.wallet, price, allocation=alloc)
            ts = datetime.utcnow().strftime("%H:%M:%S")
            send_telegram_message(
                f"[{ts}] LP criada {lp['lower']:.2f}-{lp['upper']:.2f} "
                f"com {lp['eth']:.4f} ETH / {lp['usdc']:.2f} USDC",
            )

        lower_price, upper_price = lp["lower"], lp["upper"]
        if abs(lower_price) > 1e5 or abs(upper_price) > 1e5:
            lower_price = self._tick_to_price(lower_price)
            upper_price = self._tick_to_price(upper_price)
        lp_prices = {
            "lower": lower_price,
            "upper": upper_price,
            "usdc": lp["usdc"],
            "eth": lp["eth"],
        }

        hedge_eth = get_eth_position(self.address, self.wallet)
        leverage = float(os.getenv("PERP_LEVERAGE", "5"))
        max_hedge = float("inf")
        if self.wallet is not None:
            max_hedge = (self.wallet.usdc_balance * leverage) / price
        target = min(lp_prices["eth"], max_hedge)
        if abs(hedge_eth - target) > 0.01:
            set_hedge_position(target, price, self.simulated, self.wallet, leverage)
            ts = datetime.utcnow().strftime("%H:%M:%S")
            send_telegram_message(
                f"[{ts}] Hedge {hedge_eth:.4f} -> {target:.4f} ETH",
            )
            hedge_eth = target

        if should_reposition(price, lp_prices):
            old_lower, old_upper = lp_prices["lower"], lp_prices["upper"]
            lp_prices = move_range(self.wallet, price)
            lower_price, upper_price = lp_prices["lower"], lp_prices["upper"]
            ts = datetime.utcnow().strftime("%H:%M:%S")
            send_telegram_message(
                f"[{ts}] Range {old_lower:.2f}-{old_upper:.2f} -> "
                f"{lower_price:.2f}-{upper_price:.2f}"
            )

        print(
            f"LP: [{lower_price:.2f}, {upper_price:.2f}] Exposição: {lp_prices['eth']:.4f} ETH Hedge: {hedge_eth:.4f}"
        )

    @staticmethod
    def _tick_to_price(tick: int) -> float:
        return 1.0001 ** tick
