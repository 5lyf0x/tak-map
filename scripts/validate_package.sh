#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Bash syntax =="
bash -n install.sh
bash -n uninstall.sh

echo "== Python compile =="
python3 -m py_compile tak_dashboard.py
if [[ -f tak_dashboard.py.bak ]]; then
  python3 -m py_compile tak_dashboard.py.bak
fi

echo "== JavaScript syntax =="
if command -v node >/dev/null 2>&1; then
  for f in takmap.js embedded_takmap.js combined_scripts_v287.js; do
    [[ -f "$f" ]] && node --check "$f"
  done
else
  echo "node not found; skipping JavaScript syntax checks"
fi

echo "== Secret file check =="
if find . \
  -path './.git' -prune -o \
  -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name '*.pfx' -o -name '.env' \
  | grep -q .; then
  echo "Potential secret/runtime files found:" >&2
  find . \
    -path './.git' -prune -o \
    -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name '*.pfx' -o -name '.env' \
    -print >&2
  exit 1
fi

echo "Validation complete."
