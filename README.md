# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis.
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute o bot: `python main.py`.

## Modo de simulação

Defina `SIMULATED_WALLET_MODE=True` para testar sem enviar transações reais. Mesmo em simulação o bot consulta dados reais das APIs.
