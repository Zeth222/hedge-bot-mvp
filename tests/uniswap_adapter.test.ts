import { describe, expect, test } from 'vitest'
import { Token } from '@uniswap/sdk-core'
import { FeeAmount, computePoolAddress } from '@uniswap/v3-sdk'
import { getQuote, getPoolState, buildSwapTx } from '../src/uniswap/adapter.js'

const chainId = 42161
const WETH = '0x82AF49447D8a07e3bd95BD0d56f35241523fBab1'
const USDC = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'

describe('uniswap adapter', () => {
  test('getQuote returns amount', async () => {
    const quote = await getQuote(WETH, USDC, 10n ** 18n, chainId)
    expect(quote.amountOut).greaterThan(0n)
  })

  test('fallback when routing unavailable', async () => {
    process.env.NO_SOR = '1'
    const quote = await getQuote(WETH, USDC, 10n ** 18n, chainId)
    expect(quote.fallback).toBe('quoter')
    delete process.env.NO_SOR
  })

  test('getPoolState returns essentials', async () => {
    const tokenA = new Token(chainId, WETH, 18, 'WETH')
    const tokenB = new Token(chainId, USDC, 6, 'USDC')
    const poolAddress = computePoolAddress({
      factoryAddress: '0x1F98431c8aD98523631AE4a59f267346ea31F984',
      tokenA,
      tokenB,
      fee: FeeAmount.LOW
    })
    const state = await getPoolState(poolAddress)
    expect(state.sqrtPriceX96).toBeDefined()
    expect(state.liquidity).toBeDefined()
    expect(state.fee).toBe(500)
  })

  test('buildSwapTx returns calldata and router', async () => {
    const tx = await buildSwapTx({
      tokenIn: WETH,
      tokenOut: USDC,
      amountIn: 10n ** 18n,
      recipient: '0x0000000000000000000000000000000000000001',
      chainId
    })
    expect(tx.to.toLowerCase()).toBe('0xe592427a0aece92de3edee1f18e0157c05861564')
    expect(tx.data.length).greaterThan(2)
  })
})

