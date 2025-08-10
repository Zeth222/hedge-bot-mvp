#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip setuptools wheel || true
if ! pip install -r requirements.txt; then
  echo "[WARN] Falling back to web3==6.17.2"
  sed -i 's/^web3==6\.18\.0$/web3==6.17.2/' requirements.txt
  pip install -r requirements.txt
fi
