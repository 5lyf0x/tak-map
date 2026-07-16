#!/usr/bin/env bash
set -euo pipefail
trap 'find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true; find . -type f -name "*.pyc" -delete 2>/dev/null || true' EXIT

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
  for f in takmap.js combined_scripts_v287.js; do
    [[ -f "$f" ]] && node --check "$f"
  done
  if [[ -f embedded_takmap.js ]]; then
    python3 - <<'PYJS'
from pathlib import Path
s=Path('embedded_takmap.js').read_text()
if s.lstrip().startswith('<script'):
    s=s[s.find('>')+1:s.rfind('</script>')]
Path('/tmp/tak-map-embedded-check.js').write_text(s)
PYJS
    node --check /tmp/tak-map-embedded-check.js
  fi
else
  echo "node not found; skipping JavaScript syntax checks"
fi


echo "== i442 release/UI assertions =="
PYTHONWARNINGS=ignore::SyntaxWarning python3 - <<'PYREL'
import re
import runpy
from pathlib import Path

assert Path('VERSION').read_text().strip() == 'i442'
embedded = Path('embedded_takmap.js').read_text()
for needle in (
    "const V='i442'",
    "getTakMapReleaseDiagnosticsV442",
    "tak-offline-stepper-v442",
    "tak-tactical-rail-v442",
    "Buffering playback...",
):
    assert needle in embedded, needle

ns = runpy.run_path('tak_dashboard.py', run_name='tak_map_validation')
html = ns.get('TAK_MAP_HTML', '')
visible = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.I)
assert '<div class="title"><img src="/tak-map-logo.png" alt=""><span>TAK Map</span></div>' in visible
assert 'takMapHeaderRelease' not in visible
assert re.search(r'class="release-main"[^>]*>1\.3\.0<', visible)
assert re.search(r'class="iteration-chip"[^>]*>i442<', visible)
assert not re.search(r'>1\.2\.0<', visible)
assert not re.search(r'>v409<', visible)
print('i442 assertions passed')
PYREL

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
