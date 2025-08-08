class WalletSimulator:
    """In-memory simulator for testing without sending transactions."""

    def __init__(self, initial_eth: float = 10.0, initial_usdc: float = 10000.0):
        self.eth_balance = initial_eth
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

    def rebalance_hedge(self, target_eth):
        self.hedge_positions = [{"eth": target_eth}]
        print(f"[SIM] Hedge ajustado para {target_eth} ETH")
