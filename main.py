"""Entry point for the hedge bot.

This module loads environment variables, decides whether to operate with a
real wallet or using the in-memory :class:`WalletSimulator` and sends a
startup notification via Telegram.
"""

import os

from dotenv import load_dotenv

from utils.telegram import send_telegram_message

load_dotenv()

SIMULATED_WALLET_MODE = os.getenv("SIMULATED_WALLET_MODE", "False").lower() == "true"


if __name__ == "__main__":
    if SIMULATED_WALLET_MODE:
        from wallet_simulator import WalletSimulator

        wallet = WalletSimulator()
        send_telegram_message("🚀 Bot iniciado em modo SIMULADO!")
        # Example actions showing the simulator in use
        wallet.rebalance(wallet.balances["ETH"], wallet.balances["USDC"])
    else:
        send_telegram_message("🚀 Bot iniciado com carteira REAL!")
        # Real wallet logic would be implemented here.
