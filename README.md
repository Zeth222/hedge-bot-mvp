# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.
Agora o bot possui dois modos de operação: **espectador**, que apenas envia alertas e recomendações, e **ativo**, que executa as operações automaticamente.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis.
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute o bot: `python main.py` e escolha entre carteira de **teste** ou **real** quando solicitado.
   Ao usar o modo de teste será pedido o saldo inicial de ETH e USDC a ser utilizado.
4. Escolha o modo de operação **espectador** ou **ativo** quando perguntado.
   Para automatizar, defina `BOT_MODE=espectador` ou `ativo` no `.env`.

## Modo de simulação

Durante a execução, o bot perguntará se deve utilizar uma carteira de teste (simulada) ou real.
Para automatizar, defina `SIMULATED_WALLET_MODE=True` ou `False` no `.env` e a pergunta será pulada.
Mesmo em simulação o bot consulta dados reais das APIs.

Ao iniciar um ciclo o bot verifica se já existem posições de LP na Uniswap e de hedge na Hyperliquid,
criando-as se necessário quando no modo ativo. No modo espectador são enviados apenas alertas de recomendação.
A troca de faixa da LP considera o possível ganho em taxas menos o custo de gas,
e o hedge é ajustado dinamicamente para manter exposição neutra.
