import os
import time
from dotenv import load_dotenv
from utils.telegram import send_telegram_message
from utils.wallet_simulator import WalletSimulator
from utils.logic import BotLogic

load_dotenv()

ADDRESS = os.getenv("PUBLIC_ADDRESS")
if not ADDRESS:
    ADDRESS = (
        input("Endereço público para monitorar (enter para nenhum): ").strip()
        or "0x0000000000000000000000000000000000000000"
    )
interval_env = os.getenv("POLL_INTERVAL", "30")
INTERVAL = int(interval_env)

simulated_env = os.getenv("SIMULATED_WALLET_MODE")
if simulated_env is None:
    choice = input("Usar carteira de 'teste' ou 'real'? [teste/real]: ").strip().lower()
    SIMULATED = choice != "real"
else:
    SIMULATED = simulated_env.lower() == "true"

mode_env = os.getenv("BOT_MODE")
if mode_env is None:
    mode_choice = (
        input("Modo de operação? [espectador/ativo]: ").strip().lower()
        or "espectador"
    )
else:
    mode_choice = mode_env.lower()
MODE = "active" if mode_choice in ("ativo", "active") else "spectator"

subgraph = os.getenv("UNISWAP_SUBGRAPH") or input(
    "URL do subgrafo Uniswap (enter para padrão Arbitrum): "
).strip()
if not subgraph:
    subgraph = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum"
os.environ["UNISWAP_SUBGRAPH"] = subgraph

pool = os.getenv("UNISWAP_POOL_ID") or input(
    "ID da pool Uniswap (enter para WETH/USDC 0.05%): "
).strip()
if not pool:
    pool = "0x88f38662f45c78302b556271cd0a4da9d1cb1a0d"
os.environ["UNISWAP_POOL_ID"] = pool

wallet = None
if SIMULATED:
    try:
        usdc_bal = float(input("Saldo inicial de USDC para testes: ") or "10000")
    except ValueError:
        usdc_bal = 10000.0
    wallet = WalletSimulator(initial_usdc=usdc_bal)

bot = BotLogic(wallet, ADDRESS, simulated=SIMULATED, mode=MODE)

mode_label = "ativo" if MODE == "active" else "espectador"
send_telegram_message(f"🚀 Bot iniciado no modo {mode_label}!")

if __name__ == "__main__":
    while True:
        try:
            bot.run_cycle()
        except Exception as exc:
            print(f"[ERRO] {exc}")
            send_telegram_message(f"Erro no ciclo: {exc}")
        time.sleep(INTERVAL)
