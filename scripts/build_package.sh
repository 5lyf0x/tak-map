#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-v442}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
OUT="$DIST/tak-map-${VERSION}.zip"

mkdir -p "$DIST"
rm -f "$OUT"

cd "$(dirname "$ROOT")"
zip -qr "$OUT" "$(basename "$ROOT")" \
  -x '*/.git/*' \
     '*/__pycache__/*' \
     '*.pyc' \
     '*/dist/*' \
     '*.log' \
     '*.tmp' \
     '*.pem' '*.key' '*.crt' '*.p12' '*.pfx' '.env' '*/.env'

echo "$OUT"
