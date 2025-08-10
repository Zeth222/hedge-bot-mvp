import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from utils.telegram import send_telegram_message
from utils.logic import BotLogic
from utils.hyperliquid import (
    BASE_URL as HL_BASE_URL,
    get_eth_position,
)
from utils.uniswap import get_lp_position

ADDRESS = os.getenv("PUBLIC_ADDRESS")
if not ADDRESS:
    ADDRESS = (
        input("Endereço público para monitorar (enter para nenhum): ").strip()
        or "0x0000000000000000000000000000000000000000"
    )
interval_env = os.getenv("POLL_INTERVAL", "30")
INTERVAL = int(interval_env)


mode_env = os.getenv("BOT_MODE")
if mode_env is None:
    spectator_choice = (
        input("Ativar modo espectador? (s/N): ").strip().lower()
    )
    MODE = "spectator" if spectator_choice == "s" else "active"
else:
    mode_choice = mode_env.strip().lower()
    MODE = (
        "spectator"
        if mode_choice in ("s", "sim", "spectator", "espectador")
        else "active"
    )

subgraph = os.getenv(
    "UNISWAP_SUBGRAPH",
    "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum",
)

HL_ADDRESS = os.getenv("HYPERLIQUID_ADDRESS", ADDRESS)

# Checa posições existentes na Uniswap e Hyperliquid
print("Checando posições existentes para o endereço informado...")
lp_info = get_lp_position(ADDRESS)
if lp_info:
    print(
        f"LP encontrada entre {lp_info['lower']}-{lp_info['upper']} "
        f"com {lp_info['eth']:.4f} ETH"
    )
else:
    print("Nenhuma LP encontrada na Uniswap")
hl_pos = get_eth_position(HL_ADDRESS)
if hl_pos:
    print(f"Posição aberta na Hyperliquid: {hl_pos:.4f} ETH")
else:
    print("Nenhuma posição aberta na Hyperliquid")

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
bot = BotLogic(wallet, ADDRESS, mode=MODE)

if __name__ == "__main__":
    while True:
        try:
            bot.run_cycle()
        except Exception as exc:
            print(f"[ERRO] {exc}")
            send_telegram_message(f"Erro no ciclo: {exc}")
        time.sleep(INTERVAL)
