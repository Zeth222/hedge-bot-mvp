import { AlphaRouter } from '@uniswap/smart-order-router'
import { CurrencyAmount, Percent, Token, TradeType } from '@uniswap/sdk-core'
import {
  FeeAmount,
  Pool,
  Route,
  SwapRouter,
  Trade,
  computePoolAddress
} from '@uniswap/v3-sdk'
import { createPublicClient, http } from 'viem'
import { arbitrum } from 'viem/chains'
import { JsonRpcProvider } from 'ethers'
import { z } from 'zod'

const QUOTER_V2_ADDRESS = '0x61fFE014bA179baCd3A1f8b409AfcD13d21be205'
const V3_ROUTER_ADDRESS = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
const V3_FACTORY_ADDRESS = '0x1F98431c8aD98523631AE4a59f267346ea31F984'

const ERC20_ABI = [
  {
    name: 'decimals',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint8' }]
  }
]

const POOL_ABI = [
  {
    name: 'slot0',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [
      { name: 'sqrtPriceX96', type: 'uint160' },
      { name: 'tick', type: 'int24' },
      { name: 'observationIndex', type: 'uint16' },
      { name: 'observationCardinality', type: 'uint16' },
      { name: 'observationCardinalityNext', type: 'uint16' },
      { name: 'feeProtocol', type: 'uint8' },
      { name: 'unlocked', type: 'bool' }
    ]
  },
  {
    name: 'liquidity',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: 'liquidity', type: 'uint128' }]
  },
  {
    name: 'fee',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: 'fee', type: 'uint24' }]
  },
  {
    name: 'token0',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: 'token0', type: 'address' }]
  },
  {
    name: 'token1',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: 'token1', type: 'address' }]
  }
]

const QUOTER_ABI = [
  {
    name: 'quoteExactInputSingle',
    type: 'function',
    stateMutability: 'view',
    inputs: [
      { name: 'tokenIn', type: 'address' },
      { name: 'tokenOut', type: 'address' },
      { name: 'fee', type: 'uint24' },
      { name: 'amountIn', type: 'uint256' },
      { name: 'sqrtPriceLimitX96', type: 'uint160' }
    ],
    outputs: [{ name: 'amountOut', type: 'uint256' }]
  }
]

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  let attempt = 0
  while (true) {
    try {
      return await fn()
    } catch (e) {
      if (attempt++ >= retries) throw e
      await sleep(2 ** attempt * 100)
    }
  }
}

function chainFromId(chainId: number) {
  if (chainId === arbitrum.id) return arbitrum
  throw new Error(`unsupported chain ${chainId}`)
}

export async function getQuote(
  tokenIn: string,
  tokenOut: string,
  amount: bigint,
  chainId: number
) {
  const schema = z.object({
    tokenIn: z.string().startsWith('0x'),
    tokenOut: z.string().startsWith('0x'),
    amount: z.bigint(),
    chainId: z.number()
  })
  const input = schema.parse({ tokenIn, tokenOut, amount, chainId })

  const client = createPublicClient({
    chain: chainFromId(input.chainId),
    transport: http(process.env.RPC_URL_ARBITRUM!)
  })

  const [decIn, decOut] = await withRetry(() =>
    Promise.all([
      client.readContract({ address: input.tokenIn as `0x${string}`, abi: ERC20_ABI, functionName: 'decimals' }),
      client.readContract({ address: input.tokenOut as `0x${string}`, abi: ERC20_ABI, functionName: 'decimals' })
    ])
  )

  const tIn = new Token(input.chainId, input.tokenIn, Number(decIn))
  const tOut = new Token(input.chainId, input.tokenOut, Number(decOut))

  try {
    if (process.env.NO_SOR === '1') throw new Error('SOR disabled')
    const provider = new JsonRpcProvider(process.env.RPC_URL_ARBITRUM)
    const router = new AlphaRouter({ chainId: input.chainId, provider })
    const route = await withRetry(() =>
      router.route(
        CurrencyAmount.fromRawAmount(tIn, input.amount),
        tOut,
        TradeType.EXACT_INPUT,
        {
          recipient: input.tokenIn,
          slippageTolerance: new Percent(5, 1000)
        }
      )
    )
    if (!route) throw new Error('no route')
    return {
      amountOut: BigInt(route.quote.toFixed(0)),
      route: route.route[0].tokenPath.map((t) => t.symbol)
    }
  } catch (e) {
    const amountOut = await withRetry(() =>
      client.readContract({
        address: QUOTER_V2_ADDRESS,
        abi: QUOTER_ABI,
        functionName: 'quoteExactInputSingle',
        args: [input.tokenIn, input.tokenOut, 500, input.amount, 0]
      })
    )
    return {
      amountOut: amountOut as bigint,
      route: ['direct'],
      fallback: 'quoter'
    }
  }
}

export async function getPoolState(poolAddress: string) {
  const schema = z.object({ pool: z.string().startsWith('0x') })
  const { pool } = schema.parse({ pool: poolAddress })

  const client = createPublicClient({
    chain: arbitrum,
    transport: http(process.env.RPC_URL_ARBITRUM!)
  })

  const [slot0, liquidity, fee, token0, token1] = await withRetry(() =>
    Promise.all([
      client.readContract({ address: pool as `0x${string}`, abi: POOL_ABI, functionName: 'slot0' }),
      client.readContract({ address: pool as `0x${string}`, abi: POOL_ABI, functionName: 'liquidity' }),
      client.readContract({ address: pool as `0x${string}`, abi: POOL_ABI, functionName: 'fee' }),
      client.readContract({ address: pool as `0x${string}`, abi: POOL_ABI, functionName: 'token0' }),
      client.readContract({ address: pool as `0x${string}`, abi: POOL_ABI, functionName: 'token1' })
    ])
  )

  const [dec0, dec1] = await withRetry(() =>
    Promise.all([
      client.readContract({ address: token0, abi: ERC20_ABI, functionName: 'decimals' }),
      client.readContract({ address: token1, abi: ERC20_ABI, functionName: 'decimals' })
    ])
  )

  return {
    sqrtPriceX96: slot0[0] as bigint,
    liquidity: liquidity as bigint,
    tick: Number(slot0[1]),
    fee: Number(fee),
    token0: token0 as string,
    token1: token1 as string,
    token0Decimals: Number(dec0),
    token1Decimals: Number(dec1)
  }
}

interface BuildSwapParams {
  tokenIn: string
  tokenOut: string
  amountIn: bigint
  recipient: string
  chainId: number
}

export async function buildSwapTx(params: BuildSwapParams) {
  const schema = z.object({
    tokenIn: z.string().startsWith('0x'),
    tokenOut: z.string().startsWith('0x'),
    amountIn: z.bigint(),
    recipient: z.string().startsWith('0x'),
    chainId: z.number()
  })
  const p = schema.parse(params)

  const client = createPublicClient({
    chain: chainFromId(p.chainId),
    transport: http(process.env.RPC_URL_ARBITRUM!)
  })

  const [decIn, decOut] = await withRetry(() =>
    Promise.all([
      client.readContract({ address: p.tokenIn as `0x${string}`, abi: ERC20_ABI, functionName: 'decimals' }),
      client.readContract({ address: p.tokenOut as `0x${string}`, abi: ERC20_ABI, functionName: 'decimals' })
    ])
  )

  const tokenIn = new Token(p.chainId, p.tokenIn, Number(decIn))
  const tokenOut = new Token(p.chainId, p.tokenOut, Number(decOut))

  const poolAddress = computePoolAddress({
    factoryAddress: V3_FACTORY_ADDRESS,
    tokenA: tokenIn,
    tokenB: tokenOut,
    fee: FeeAmount.LOW
  })

  const state = await getPoolState(poolAddress)

  const pool = new Pool(
    tokenIn,
    tokenOut,
    state.fee,
    state.sqrtPriceX96,
    state.liquidity,
    state.tick
  )

  const route = new Route([pool], tokenIn, tokenOut)
  const trade = Trade.fromRoute(
    route,
    CurrencyAmount.fromRawAmount(tokenIn, p.amountIn),
    TradeType.EXACT_INPUT
  )

  const { calldata, value } = SwapRouter.swapCallParameters(trade, {
    slippageTolerance: new Percent(5, 1000),
    recipient: p.recipient
  })

  return {
    to: V3_ROUTER_ADDRESS,
    data: calldata,
    value
  }
}

