import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    SIMULATED_WALLET_MODE = os.getenv("SIMULATED_WALLET_MODE", "true").lower() == "true"
except Exception:
    print("[SIMULATION] Rodando em modo simulado por fallback (dotenv ausente ou erro de carregamento)")
    SIMULATED_WALLET_MODE = True

from utils.telegram import send_telegram_message

if __name__ == "__main__":
    message = (
        "🚀 Bot iniciado em modo simulado!"
        if SIMULATED_WALLET_MODE
        else "🚀 Bot iniciado com sucesso!"
    )
    send_telegram_message(message)
