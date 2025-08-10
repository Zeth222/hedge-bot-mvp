placeholder
import os
import time

from dotenv import load_dotenv

from utils.uniswap import UniswapClient
from utils.hyperliquid import HyperliquidAPI
from utils.logic import BotLogic


def main() -> None:
    load_dotenv()
    rpc_url = os.getenv("RPC_URL_ARBITRUM")
    fallbacks = os.getenv("RPC_FALLBACKS", "")
    uniswap = UniswapClient(rpc_url=rpc_url, fallbacks=fallbacks)
    hyper = HyperliquidAPI(os.getenv("WALLET_ADDRESS"))
    bot = BotLogic(uniswap, hyper)
    try:
        while True:
            bot.check_and_hedge()
            time.sleep(20)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
