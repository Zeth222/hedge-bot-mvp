import os
from datetime import datetime

from .prices import get_eth_usdc_price
from .uniswap import get_lp_position, create_lp_position, move_range, should_reposition
from .hyperliquid import get_eth_position, set_hedge_position
from .telegram import send_telegram_message


class BotLogic:
    """Encapsula o ciclo principal de operações do bot."""

    def __init__(self, wallet, address: str, mode: str = "active"):
        self.wallet = wallet
        self.address = address
        self.mode = mode

    def run_cycle(self) -> None:
        """Executa um ciclo completo de hedge e reposicionamento de LP."""
        price = get_eth_usdc_price()

        # Verifica se já existe uma posição de LP para o endereço
        lp = get_lp_position(self.address)
        if lp and self.wallet is not None and not self.wallet.lp_positions:
            self.wallet.lp_positions.append(lp)
            ts = datetime.utcnow().strftime("%H:%M:%S")
            send_telegram_message(
                f"[{ts}] LP existente detectada {lp['lower']:.2f}-{lp['upper']:.2f}"
            )

        # Caso não exista, cria uma nova posição ou alerta dependendo do modo
        if not lp:
            if self.mode == "active":
                alloc = float(os.getenv("LP_ALLOCATION", "0.5"))
                lp = create_lp_position(self.wallet, price, allocation=alloc)
                send_telegram_message("LP criada automaticamente")
            else:
                send_telegram_message("Nenhuma posição de LP encontrada. Considere criar uma.")
                return

        # Normaliza valores em ticks para preços reais, se necessário
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

        # Calcula hedge necessário e envia ordens ou alertas
        hedge_eth = get_eth_position(self.address)
        leverage = float(os.getenv("PERP_LEVERAGE", "5"))
        max_hedge = float("inf") if self.wallet is None else (
            self.wallet.usdc_balance * leverage / price
        )
        target = min(lp["eth"], max_hedge)
        if abs(hedge_eth - target) > 0.01:
            if self.mode == "active":
                set_hedge_position(target, price, leverage)
                msg = (
                    "Hedge criado automaticamente" if hedge_eth == 0 else "Hedge rebalanceado"
                )
                send_telegram_message(msg)
                hedge_eth = target
            else:
                send_telegram_message(
                    f"Hedge atual {hedge_eth:.4f} ETH difere do alvo {target:.4f} ETH; considere ajustar."
                )

        # Reposiciona faixa de LP se necessário
        need_reposition = should_reposition(price, lp_prices)
        if need_reposition:
            if self.mode == "active":
                old_lower, old_upper = lp_prices["lower"], lp_prices["upper"]
                lp_prices = move_range(self.wallet, price)
                lower_price, upper_price = lp_prices["lower"], lp_prices["upper"]
                ts = datetime.utcnow().strftime("%H:%M:%S")
                send_telegram_message(
                    f"[{ts}] Range {old_lower:.2f}-{old_upper:.2f} -> {lower_price:.2f}-{upper_price:.2f}"
                )
            else:
                send_telegram_message(
                    f"Faixa atual {lp_prices['lower']:.2f}-{lp_prices['upper']:.2f} pode ser reposicionada."
                )

        print(
            f"LP: [{lp_prices['lower']:.2f}, {lp_prices['upper']:.2f}] "
            f"Exposição: {lp_prices['eth']:.4f} ETH "
            f"Hedge: {hedge_eth:.4f}"
        )

    @staticmethod
    def _tick_to_price(tick: int) -> float:
        """Converte um tick do Uniswap em preço."""
        return 1.0001 ** tick
