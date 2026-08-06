#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-v1.4.0-i618}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
OUT="$DIST/tak-map-${VERSION}.zip"
ITERATION="${VERSION##*-}"
if [[ ! "$ITERATION" =~ ^i[0-9]+$ ]]; then
  echo "ERROR: version must end in an iteration such as i575: $VERSION" >&2
  exit 2
fi
ROOT_NAME="tak-map-v${ITERATION#i}"
STAGE="$(mktemp -d /tmp/tak-map-build-${ITERATION}-XXXXXX)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$DIST" "$STAGE/$ROOT_NAME"
rm -f "$OUT"

# Stage a clean, correctly named install root regardless of the source checkout name.
(
  cd "$ROOT"
  tar \
    --exclude='./.git' \
    --exclude='./__pycache__' \
    --exclude='*/__pycache__' \
    --exclude='./dist' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='*.tmp' \
    --exclude='*.pem' --exclude='*.key' --exclude='*.crt' \
    --exclude='*.p12' --exclude='*.pfx' \
    --exclude='.env' --exclude='*/.env' \
    -cf - .
) | (cd "$STAGE/$ROOT_NAME" && tar -xf -)

(cd "$STAGE" && zip -qr "$OUT" "$ROOT_NAME")
echo "$OUT"
