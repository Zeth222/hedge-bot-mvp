# Hedge Bot MVP

Bot de monitoramento para posições de LP WETH/USDC na Uniswap v3 com leitura de posições na Hyperliquid.

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis:
   - `RPC_URL_ARBITRUM`
   - `RPC_FALLBACKS`
   - `HYPERLIQUID_WALLET_ADDRESS`
2. Instale as dependências com script de fallback:
   ```bash
   bash scripts/setup_env.sh
   ```
3. Execute o bot:
   ```bash
   python main.py
   ```

O script consulta o estado do pool WETH/USDC 0.05% na Uniswap v3 e a posição de hedge na Hyperliquid
utilizando apenas o endereço público, emitindo alertas quando o preço se aproxima dos limites da posição LP.

### Testes

Para rodar testes sem acesso à rede:

```bash
OFFLINE=1 python -m pytest -q
```

Sem a variável `OFFLINE`, os testes tentam acessar o RPC e serão pulados caso nenhum endpoint esteja disponível.

### Comportamento offline

Se todos os RPCs estiverem indisponíveis, o bot exibe:

```
[WARN] All RPC endpoints unavailable; running in degraded mode (no chain reads)
```

Caso a API da Hyperliquid não responda, será logado:

```
[WARN] Hyperliquid API unreachable (read-only); skipping this cycle
```
