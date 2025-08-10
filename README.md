# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis:
   - `RPC_URL_ARBITRUM`
   - `RPC_FALLBACKS`
   - `HYPERLIQUID_API_KEY` e `HYPERLIQUID_API_SECRET`
   - `WALLET_ADDRESS`
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o bot:
   ```bash
   python main.py
   ```

O script imprime o estado do pool WETH/USDC (sqrtPriceX96 e tick) e uma cotação via QuoterV2,
utilizando o SDK oficial da Hyperliquid para evitar o erro de import. Nunca versione suas chaves de API.
