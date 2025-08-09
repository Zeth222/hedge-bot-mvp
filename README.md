# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis.
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute o bot: `python main.py` e escolha o modo **spectator** ou **full**.
   No modo spectator o bot apenas monitora as posições existentes e envia sugestões pelo Telegram.
   O modo full executa as alterações automaticamente.
   Também é possível escolher entre carteira de **teste** ou **real**; em teste será pedido o saldo
   inicial de USDC a ser utilizado.

## Modos de operação

`RUN_MODE` controla se o bot opera em modo espectador (`spectator`) ou totalmente automático (`full`).
Já `SIMULATED_WALLET_MODE` define se as operações devem usar uma carteira simulada.
Para automatizar estas escolhas, defina as variáveis no `.env`.

Mesmo em simulação o bot consulta dados reais das APIs.

Ao iniciar um ciclo o bot verifica se já existem posições de LP na Uniswap e de hedge na Hyperliquid,
criando-as se necessário. A troca de faixa da LP considera o possível ganho em taxas menos o custo de gas,
e o hedge é ajustado dinamicamente para manter exposição neutra.
