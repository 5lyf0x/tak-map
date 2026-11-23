#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-$(cat "$ROOT/VERSION")}"; VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+-i[0-9]+$ ]]; then
  echo "ERROR: expected version like 1.4.0-i649: $VERSION" >&2
  exit 2
fi
DIST="$ROOT/dist"
OUT="$DIST/tak-map-v${VERSION}.zip"
STAGE="$(mktemp -d "/tmp/tak-map-build-${VERSION}-XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$DIST"

# Keep the ZIP root flat: extraction creates the one new, versioned source tree.
# Omit generated outputs, personal configuration and signing/certificate secrets.
(
  cd "$ROOT"
  tar --exclude='./.git' --exclude='./dist' --exclude='./build' \
      --exclude='./.gradle' --exclude='*/__pycache__' --exclude='./__pycache__' \
      --exclude='*.pyc' --exclude='*.class' --exclude='*.apk' --exclude='*.aab' \
      --exclude='*.jks' --exclude='*.keystore' \
      --exclude='*.log' --exclude='*.tmp' --exclude='*.pem' --exclude='*.key' \
      --exclude='*.crt' --exclude='*.p12' --exclude='*.pfx' \
      --exclude='.env' --exclude='*/.env' -cf - .
) | (cd "$STAGE" && tar -xf -)

# Hash the exact files that will be placed inside the ZIP.
(
 cd "$STAGE"
 LC_ALL=C find . -type f ! -path './SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
rm -f "$OUT"
(cd "$STAGE" && zip -q -r -X "$OUT" .)
echo "$OUT"
