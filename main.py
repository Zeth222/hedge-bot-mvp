import os
import time
from dotenv import load_dotenv
from utils.telegram import send_telegram_message
from utils.wallet_simulator import WalletSimulator
from utils.logic import BotLogic

load_dotenv()

ADDRESS = os.getenv("PUBLIC_ADDRESS", "0x0000000000000000000000000000000000000000")
SIMULATED = os.getenv("SIMULATED_WALLET_MODE", "True") == "True"
INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

wallet = WalletSimulator() if SIMULATED else None
bot = BotLogic(wallet, ADDRESS, simulated=SIMULATED)

send_telegram_message("🚀 Bot iniciado com sucesso!")

if __name__ == "__main__":
    while True:
        try:
            bot.run_cycle()
        except Exception as exc:
            print(f"[ERRO] {exc}")
            send_telegram_message(f"Erro no ciclo: {exc}")
        time.sleep(INTERVAL)
