from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional

from utils.telegram import send_telegram_message


@dataclass
class WalletSimulator:
    """Simple in-memory simulator for the bot's wallet and positions."""

    balances: Dict[str, Decimal] = field(
        default_factory=lambda: {"ETH": Decimal("1"), "USDC": Decimal("1000")}
    )
    lp_position: Optional[Dict[str, Decimal]] = field(default=None)
    hedge_position: Decimal = field(default=Decimal("0"))

    def _notify(self, message: str) -> None:
        """Prints and sends a telegram message with the simulated action."""
        print(message)
        try:
            send_telegram_message(message)
        except Exception:
            # In tests or when telegram is not configured, we do not want to fail.
            pass

    # ------------------------------- Balances ---------------------------------
    def swap(self, token_in: str, token_out: str, amount_in: Decimal, price: Decimal) -> None:
        """Simulate a token swap updating internal balances.

        Parameters
        ----------
        token_in: str
            Symbol of token being spent.
        token_out: str
            Symbol of token being received.
        amount_in: Decimal
            Amount of `token_in` to swap.
        price: Decimal
            Price of `token_out` in terms of `token_in` (token_out/token_in).
        """

        if amount_in <= 0:
            raise ValueError("amount_in must be positive")
        if self.balances.get(token_in, Decimal("0")) < amount_in:
            raise ValueError(f"Saldo insuficiente de {token_in}")

        amount_out = amount_in * price
        self.balances[token_in] -= amount_in
        self.balances[token_out] = self.balances.get(token_out, Decimal("0")) + amount_out
        self._notify(
            f"[SIM] Swap {amount_in} {token_in} -> {amount_out} {token_out} (preço: {price})"
        )

    def rebalance(self, target_eth: Decimal, target_usdc: Decimal) -> None:
        """Rebalanceia o saldo para os valores alvo."""
        self.balances["ETH"] = target_eth
        self.balances["USDC"] = target_usdc
        self._notify(
            f"[SIM] Rebalance para {target_eth} ETH e {target_usdc} USDC"
        )

    # --------------------------- Liquidity Provider ---------------------------
    def move_range(self, lower: Decimal, upper: Decimal) -> None:
        """Atualiza o range da posição de LP."""
        if not self.lp_position:
            self._notify("[SIM] Nenhuma posição LP existente para mover.")
            return
        self.lp_position["lower"] = lower
        self.lp_position["upper"] = upper
        self._notify(
            f"[SIM] Range da LP movido para {lower} - {upper}"
        )

    def create_lp_position(
        self,
        lower: Decimal,
        upper: Decimal,
        amount_eth: Decimal,
        amount_usdc: Decimal,
    ) -> None:
        """Cria uma posição de LP simulada e ajusta os saldos."""
        if self.balances["ETH"] < amount_eth or self.balances["USDC"] < amount_usdc:
            raise ValueError("Saldo insuficiente para criar LP")
        self.balances["ETH"] -= amount_eth
        self.balances["USDC"] -= amount_usdc
        self.lp_position = {
            "lower": lower,
            "upper": upper,
            "eth": amount_eth,
            "usdc": amount_usdc,
        }
        self._notify(
            f"[SIM] Criada LP {lower}-{upper} com {amount_eth} ETH e {amount_usdc} USDC"
        )

    # -------------------------------- Hedging ---------------------------------
    def hedge(self, direction: str, amount: Decimal, price: Decimal) -> None:
        """Simula ordem de hedge no mercado perp."""
        if direction not in {"buy", "sell"}:
            raise ValueError("direction deve ser 'buy' ou 'sell'")
        if amount <= 0:
            raise ValueError("amount deve ser positivo")

        if direction == "buy":
            # comprar ETH usando USDC
            cost = amount * price
            if self.balances["USDC"] < cost:
                raise ValueError("Saldo insuficiente de USDC para hedge de compra")
            self.balances["USDC"] -= cost
            self.hedge_position += amount
        else:
            # vender/short ETH recebendo USDC
            self.balances["USDC"] += amount * price
            self.hedge_position -= amount

        self._notify(
            f"[SIM] Hedge {direction} {amount} ETH @ {price} (posição: {self.hedge_position})"
        )

