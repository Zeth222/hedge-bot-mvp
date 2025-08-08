import os
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
        send_telegram_message(f"Preço atual ETH/USDC: {price:.2f}")

        lp = get_lp_position(self.address)
        if not lp:
            alloc = float(os.getenv("LP_ALLOCATION", "0.5"))
            lp = create_lp_position(self.wallet, price, allocation=alloc)
            send_telegram_message("LP criada automaticamente")

        lower_price, upper_price = lp["lower"], lp["upper"]
        if abs(lower_price) > 1e5 or abs(upper_price) > 1e5:
            lower_price = self._tick_to_price(lp["lower"])
            upper_price = self._tick_to_price(lp["upper"])
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
        target = min(lp["eth"], max_hedge)
        if abs(hedge_eth - target) > 0.01:
            set_hedge_position(target, price, self.simulated, self.wallet, leverage)
            msg = "Hedge criado automaticamente" if hedge_eth == 0 else "Hedge rebalanceado"
            send_telegram_message(msg)
            hedge_eth = target

        if should_reposition(price, lp_prices):
            move_range(self.wallet, price)
            send_telegram_message("Range reposicionado")

        print(
            f"LP: [{lower_price:.2f}, {upper_price:.2f}] Exposição: {lp['eth']:.4f} ETH Hedge: {hedge_eth:.4f}"
        )

    @staticmethod
    def _tick_to_price(tick: int) -> float:
        return 1.0001 ** tick
