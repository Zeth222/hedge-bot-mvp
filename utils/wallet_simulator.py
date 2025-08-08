class WalletSimulator:
    """In-memory simulator for testing without sending transactions."""

    def __init__(self, initial_usdc: float = 10000.0):
        self.eth_balance = 0.0
        self.usdc_balance = initial_usdc
        self.lp_positions = []
        self.hedge_positions = []

    def create_lp_position(self, lower, upper, eth_amount, usdc_amount):
        self.eth_balance -= eth_amount
        self.usdc_balance -= usdc_amount
        self.lp_positions.append(
            {
                "lower": lower,
                "upper": upper,
                "eth": eth_amount,
                "usdc": usdc_amount,
            }
        )
        print(
            f"[SIM] LP criada: {eth_amount} ETH / {usdc_amount} USDC entre {lower}-{upper}"
        )

    def swap(self, from_token, to_token, amount, price):
        if from_token == "ETH" and self.eth_balance >= amount:
            self.eth_balance -= amount
            self.usdc_balance += amount * price
        elif from_token == "USDC" and self.usdc_balance >= amount:
            self.usdc_balance -= amount
            self.eth_balance += amount / price
        print(f"[SIM] Swap {amount} {from_token} para {to_token} @ {price}")

    def rebalance_hedge(self, target_eth, price, leverage):
        margin_required = abs(target_eth) * price / leverage
        if margin_required > self.usdc_balance:
            margin_required = self.usdc_balance
            target_eth = (margin_required * leverage) / price
        self.usdc_balance -= margin_required
        self.hedge_positions = [
            {"eth": target_eth, "margin": margin_required, "leverage": leverage}
        ]
        print(
            f"[SIM] Hedge ajustado para {target_eth} ETH com margem {margin_required} USDC"
        )
