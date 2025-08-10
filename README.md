# Hedge Bot MVP

Bot de hedge para posições de LP WETH/USDC na Uniswap v3 com integração à Hyperliquid.
O repositório agora inclui um adaptador em TypeScript para consultas e swaps via Uniswap.

## Configuração Python

1. Copie `.env.example` para `.env` e preencha as variáveis (incluindo `HYPERLIQUID_ADDRESS` caso utilize endereço diferente na Hyperliquid).
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute o bot: `python main.py`.
4. Escolha o modo de operação **espectador** ou **ativo`** quando perguntado.

Para ambientes sem acesso às APIs externas, defina `ETH_PRICE_FALLBACK` no `.env` com um preço de referência para o par ETH/USDC.

Ao iniciar um ciclo o bot verifica se já existem posições de LP na Uniswap e de hedge na Hyperliquid,
criando-as se necessário quando no modo ativo. No modo espectador são enviados apenas alertas de recomendação.
A troca de faixa da LP considera o possível ganho em taxas menos o custo de gas,
e o hedge é ajustado dinamicamente para manter exposição neutra.

## Adaptador Uniswap (TypeScript)

### Instalação

```bash
npm install
```

### Configuração do `.env`

Adicione ao `.env`:

```
RPC_URL_ARBITRUM=<sua URL RPC>
WALLET_ADDRESS=<opcional>
```

### Executar demo

```bash
npm run demo
```

O script realiza um quote WETH→USDC, lê o estado do pool 0.05% e exibe a transação de swap preparada.

### Testes

```bash
npm test
```

### Outras chains e tokens

Os endereços dos tokens e `chainId` podem ser alterados nos parâmetros das funções `getQuote`, `getPoolState` e `buildSwapTx`.
Para pools diferentes, informe os endereços dos tokens desejados.
