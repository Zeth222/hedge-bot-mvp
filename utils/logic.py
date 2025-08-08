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
            lp = create_lp_position(self.wallet, price)
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
        if hedge_eth == 0 and lp["eth"] > 0:
            set_hedge_position(lp["eth"], price, self.simulated, self.wallet)
            send_telegram_message("Hedge criado automaticamente")
            hedge_eth = lp["eth"]
        elif abs(lp["eth"] - hedge_eth) > 0.01:
            set_hedge_position(lp["eth"], price, self.simulated, self.wallet)
            send_telegram_message("Hedge rebalanceado")

        if should_reposition(price, lp_prices):
            move_range(self.wallet, price)
            send_telegram_message("Range reposicionado")

        print(
            f"LP: [{lower_price:.2f}, {upper_price:.2f}] Exposição: {lp['eth']:.4f} ETH Hedge: {hedge_eth:.4f}"
        )

    @staticmethod
    def _tick_to_price(tick: int) -> float:
        return 1.0001 ** tick
