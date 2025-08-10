import os
import time

from dotenv import load_dotenv

from utils.uniswap import UniswapClient, RpcUnavailable
from utils.hyperliquid import HyperliquidAPI
from utils.logic import BotLogic


def main() -> None:
    load_dotenv()
    rpc_url = os.getenv("RPC_URL_ARBITRUM")
    fallbacks = os.getenv("RPC_FALLBACKS", "")
    wallet = os.getenv("HYPERLIQUID_WALLET_ADDRESS")
    token_id_env = os.getenv("UNISWAP_POSITION_TOKEN_ID")
    token_id = int(token_id_env) if token_id_env else None

    hyper = HyperliquidAPI(wallet)
    bot = BotLogic(None, hyper, lp_token_id=token_id)
    try:
        while True:
            if bot.uniswap is None:
                try:
                    bot.uniswap = UniswapClient(rpc_url=rpc_url, fallbacks=fallbacks)
                except RpcUnavailable:
                    print("[WARN] All RPC endpoints unavailable; running in degraded mode (no chain reads)")
            try:
                bot.check_and_alert()
            except RpcUnavailable:
                print("[WARN] All RPC endpoints unavailable; running in degraded mode (no chain reads)")
                bot.uniswap = None
            time.sleep(30)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
