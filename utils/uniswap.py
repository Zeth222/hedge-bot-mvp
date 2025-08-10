"""On-chain utilities for interacting with Uniswap v3 on Arbitrum."""

from __future__ import annotations

import math
import os
from typing import Dict, Tuple, Optional, List

from web3 import Web3
from tenacity import retry, stop_after_attempt, wait_exponential


class RpcUnavailable(Exception):
    """Raised when no RPC endpoint is reachable."""


def get_web3_client(rpc_url: Optional[str] = None, fallbacks: Optional[str] = None) -> Web3:
    """Return a connected Web3 instance or raise :class:`RpcUnavailable`."""

    primary = rpc_url or os.getenv("RPC_URL_ARBITRUM", "")
    fallback_str = fallbacks or os.getenv("RPC_FALLBACKS", "")
    urls: List[str] = [primary] + [u.strip() for u in fallback_str.split(",") if u.strip()]
    seen = set()
    ordered: List[str] = []
    for u in urls:
        if u and u not in seen:
            ordered.append(u)
            seen.add(u)
    for url in ordered:
        try:
            provider = Web3.HTTPProvider(url, request_kwargs={"timeout": 15})
            w3 = Web3(provider)
            if w3.is_connected():
                print(f"[UNISWAP] Connected to {url}")
                return w3
        except Exception:
            continue
    raise RpcUnavailable("no RPC endpoints reachable")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WETH = Web3.to_checksum_address("0x82AF49447D8a07e3bd95BD0d56f35241523fBab1")
USDC = Web3.to_checksum_address("0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8")
FEE_TIER_005 = 500
FACTORY_ADDRESS = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
QUOTER_V2_ADDRESS = Web3.to_checksum_address("0x61fFE014bA17989E743c5F6cB21bF9697530B21e")
NONFUNGIBLE_POSITION_MANAGER = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")
POOL_WETH_USDC_005 = Web3.to_checksum_address("0xC5aF84701f98Fa483eCe78aF83F11b6C38ACA71D")

# ---------------------------------------------------------------------------
# Minimal ABIs
# ---------------------------------------------------------------------------
UNISWAP_V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    }
]

QUOTER_V2_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

POSITION_MANAGER_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


# ---------------------------------------------------------------------------
# Client implementation
# ---------------------------------------------------------------------------
class UniswapClient:
    """Simple on-chain reader for Uniswap v3."""

    def __init__(self, rpc_url: Optional[str] = None, fallbacks: Optional[str] = None):
        self.w3 = get_web3_client(rpc_url, fallbacks)

    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5))
    def get_pool_state(self, pool_address: str) -> Dict[str, int]:
        """Return core state for a Uniswap v3 pool."""

        try:
            addr = self.w3.to_checksum_address(pool_address)
        except Exception as exc:  # pragma: no cover - validation
            raise ValueError(f"Invalid pool address {pool_address}") from exc
        pool = self.w3.eth.contract(address=addr, abi=UNISWAP_V3_POOL_ABI)
        try:
            slot0 = pool.functions.slot0().call()
            liquidity = pool.functions.liquidity().call()
            fee = pool.functions.fee().call()
            token0 = pool.functions.token0().call()
            token1 = pool.functions.token1().call()
            dec0 = self.w3.eth.contract(address=token0, abi=ERC20_ABI).functions.decimals().call()
            dec1 = self.w3.eth.contract(address=token1, abi=ERC20_ABI).functions.decimals().call()
            return {
                "sqrtPriceX96": slot0[0],
                "liquidity": liquidity,
                "tick": slot0[1],
                "fee": fee,
                "token0": token0,
                "token1": token1,
                "decimals0": dec0,
                "decimals1": dec1,
            }
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch pool state: {exc}") from exc

    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5))
    def get_quote_weth_usdc(self, amount_in_wei: int) -> Dict[str, int]:
        """Return a quote for WETH -> USDC using QuoterV2."""

        if amount_in_wei <= 0:
            raise ValueError("amount_in_wei must be positive")
        quoter = self.w3.eth.contract(address=QUOTER_V2_ADDRESS, abi=QUOTER_V2_ABI)
        try:
            amount_out, sqrt_after, _, gas_est = quoter.functions.quoteExactInputSingle(
                WETH, USDC, amount_in_wei, FEE_TIER_005, 0
            ).call()
            tick_after = self._sqrt_price_to_tick(sqrt_after)
            return {
                "amountOut": amount_out,
                "sqrtPriceX96After": sqrt_after,
                "tickAfter": tick_after,
                "gasEstimate": gas_est,
            }
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch quote: {exc}") from exc

    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5))
    def get_position_bounds(self, token_id: int) -> Tuple[int, int]:
        """Return lower and upper ticks for a position NFT."""

        manager = self.w3.eth.contract(
            address=NONFUNGIBLE_POSITION_MANAGER, abi=POSITION_MANAGER_ABI
        )
        try:
            pos = manager.functions.positions(token_id).call()
            return int(pos[5]), int(pos[6])
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch position bounds: {exc}") from exc

    # ------------------------------------------------------------------
    @staticmethod
    def _sqrt_price_to_tick(sqrt_price_x96: int) -> int:
        price = (sqrt_price_x96 / (1 << 96)) ** 2
        return int(math.log(price, 1.0001))

