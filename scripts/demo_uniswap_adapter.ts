import 'dotenv/config'
import { Token } from '@uniswap/sdk-core'
import { FeeAmount, computePoolAddress } from '@uniswap/v3-sdk'
import { getQuote, getPoolState, buildSwapTx } from '../src/uniswap/adapter.js'

const chainId = 42161
const WETH = '0x82AF49447D8a07e3bd95BD0d56f35241523fBab1'
const USDC = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'

async function main() {
  const amountIn = 10n ** 18n
  const quote = await getQuote(WETH, USDC, amountIn, chainId)
  console.log('Quote WETH->USDC:', quote)

  const tokenA = new Token(chainId, WETH, 18, 'WETH')
  const tokenB = new Token(chainId, USDC, 6, 'USDC')
  const poolAddress = computePoolAddress({
    factoryAddress: '0x1F98431c8aD98523631AE4a59f267346ea31F984',
    tokenA,
    tokenB,
    fee: FeeAmount.LOW
  })

  const state = await getPoolState(poolAddress)
  console.log('Pool state:', state)

  const tx = await buildSwapTx({
    tokenIn: WETH,
    tokenOut: USDC,
    amountIn,
    recipient: process.env.WALLET_ADDRESS ?? '0x0000000000000000000000000000000000000000',
    chainId
  })
  console.log('Swap tx:', tx)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

