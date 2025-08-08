import os
from .prices import get_eth_usdc_price
from .uniswap import get_lp_position, create_lp_position, move_range, exit_position
from .hyperliquid import get_eth_position, set_hedge_position
from .telegram import send_telegram_message


class BotLogic:
    def __init__(self, wallet, address: str, simulated: bool = True):
        self.wallet = wallet
        self.address = address
        self.simulated = simulated
        self.upper_strategy = os.getenv("UPPER_STRATEGY", "move")
        self.lower_strategy = os.getenv("LOWER_STRATEGY", "move")

    def run_cycle(self):
        price = get_eth_usdc_price()
        send_telegram_message(f"Preço atual ETH/USDC: {price:.2f}")

        lp = get_lp_position(self.address)
        if not lp:
            lp = create_lp_position(self.wallet, price)
            send_telegram_message("LP criada automaticamente")

        hedge_eth = get_eth_position(self.address)
        exposure = lp["eth"] - hedge_eth
        if abs(exposure) > 0.01:
            set_hedge_position(lp["eth"], price, self.simulated, self.wallet)
            send_telegram_message("Hedge rebalanceado")

        lower_price, upper_price = lp["lower"], lp["upper"]
        # Detect if values are ticks (large integers) and convert to prices
        if abs(lower_price) > 1e5 or abs(upper_price) > 1e5:
            lower_price = self._tick_to_price(lp["lower"])
            upper_price = self._tick_to_price(lp["upper"])

        if price > upper_price * 0.99:
            if self.upper_strategy == "swap":
                exit_position(self.wallet)
                self.wallet.swap("USDC", "ETH", lp["usdc"], price)
                send_telegram_message("Swap total para ETH executado")
            else:
                move_range(self.wallet, price)
                send_telegram_message("Range movido para cima")
        elif price < lower_price * 1.01:
            if self.lower_strategy == "swap":
                exit_position(self.wallet)
                self.wallet.swap("ETH", "USDC", lp["eth"], price)
                send_telegram_message("Swap total para USDC executado")
            else:
                move_range(self.wallet, price)
                send_telegram_message("Range movido para baixo")

        print(
            f"LP: [{lower_price:.2f}, {upper_price:.2f}] Exposição: {lp['eth']:.4f} ETH Hedge: {hedge_eth:.4f}"
        )

    @staticmethod
    def _tick_to_price(tick: int) -> float:
        return 1.0001 ** tick
