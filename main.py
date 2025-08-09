import os
import time
import requests
from dotenv import load_dotenv
from utils.telegram import send_telegram_message
from utils.wallet_simulator import WalletSimulator
from utils.logic import BotLogic
from utils.hyperliquid import BASE_URL as HL_BASE_URL, get_usdc_balance

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

def check_api_connections(subgraph_url: str):
    statuses = []
    try:
        requests.get(HL_BASE_URL, timeout=5)
        statuses.append("Hyperliquid API: OK")
    except Exception as exc:
        statuses.append(f"Hyperliquid API: FAIL ({exc})")
    try:
        resp = requests.post(
            subgraph_url,
            json={"query": "{ _meta { block { number } } }"},
            timeout=5,
        )
        if resp.status_code == 200:
            statuses.append("Uniswap subgraph: OK")
        else:
            statuses.append(f"Uniswap subgraph: status {resp.status_code}")
    except Exception as exc:
        statuses.append(f"Uniswap subgraph: FAIL ({exc})")
    return statuses

print("=== Skyfall Intelligence ===")
status_msgs = check_api_connections(subgraph)
for msg in status_msgs:
    print(msg)
mode_label = "ativo" if MODE == "active" else "espectador"
send_telegram_message(
    f"Skyfall Intelligence iniciado no modo {mode_label}: "
    + " | ".join(status_msgs)
)

wallet = None
if SIMULATED:
    usdc_bal = get_usdc_balance(ADDRESS)
    if usdc_bal == 0.0:
        try:
            usdc_bal = float(input("Saldo inicial de USDC para testes: ") or "10000")
        except ValueError:
            usdc_bal = 10000.0
    else:
        print(f"Saldo inicial de USDC para testes: {usdc_bal}")
    wallet = WalletSimulator(initial_usdc=usdc_bal)

bot = BotLogic(wallet, ADDRESS, simulated=SIMULATED, mode=MODE)

if __name__ == "__main__":
    while True:
        try:
            bot.run_cycle()
        except Exception as exc:
            print(f"[ERRO] {exc}")
            send_telegram_message(f"Erro no ciclo: {exc}")
        time.sleep(INTERVAL)
