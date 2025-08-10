# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.
O bot possui dois modos de operação: **espectador**, que apenas envia alertas e recomendações, e **ativo**, que executa as operações automaticamente.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis (incluindo `HYPERLIQUID_ADDRESS` caso utilize endereço diferente na Hyperliquid).
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute o bot: `python main.py`.
4. Escolha o modo de operação **espectador** ou **ativo** quando perguntado.
   Para automatizar, defina `BOT_MODE=espectador` ou `ativo` no `.env`.

Para ambientes sem acesso às APIs externas, defina `ETH_PRICE_FALLBACK` no `.env`
com um preço de referência para o par ETH/USDC.

Ao iniciar um ciclo o bot verifica se já existem posições de LP na Uniswap e de hedge na Hyperliquid,
criando-as se necessário quando no modo ativo. No modo espectador são enviados apenas alertas de recomendação.
A troca de faixa da LP considera o possível ganho em taxas menos o custo de gas,
e o hedge é ajustado dinamicamente para manter exposição neutra.
