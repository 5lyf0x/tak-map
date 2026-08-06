#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
MIL=ROOT/'assets/mil2525'
SVG=MIL/'svg'
pink=[x.strip() for x in (MIL/'civilian-pink-files-i585.txt').read_text().splitlines() if x.strip()]
blue=[x.strip() for x in (MIL/'blue-utility-files-i585.txt').read_text().splitlines() if x.strip()]
assert len(pink)==38 and len(set(pink))==38
assert len(blue)==4 and len(set(blue))==4 and not set(pink)&set(blue)
for name in pink:
 data=(SVG/name).read_text(encoding='utf-8').lower()
 assert ('rgb(255,128,255)' in data or '#ff80ff' in data),name
 assert 'rgb(128,224,255)' not in data and '#80e0ff' not in data,name
for name in blue:
 data=(SVG/name).read_text(encoding='utf-8').lower()
 assert ('rgb(128,224,255)' in data or '#80e0ff' in data),name
 assert 'rgb(255,128,255)' not in data and '#ff80ff' not in data,name
tank=(SVG/'friendly-ground-equipment-tank.svg').read_text().lower()
assert 'rgb(128,224,255)' in tank or '#80e0ff' in tank
assert 'rgb(255,128,255)' not in tank and '#ff80ff' not in tank
assert not list(SVG.glob('atak-parity-friendly-civilian-*.svg'))
icon=(ROOT/'assets/tak-map-icon-registry-i572.js').read_text()
assert 'atak-parity-friendly-civilian-' not in icon
assert '.svg?v=i590-civilian-pink-v1' in icon
resolver=(ROOT/'assets/tak-map-milstd2525c-i553.js').read_text()
assert '.svg?v=i590-civilian-pink-v1' in resolver
server=(ROOT/'tak_dashboard.py').read_text()
assert "Path(os.environ.get('TAK_MAP_MIL_ROOT', '/usr/share/tak-server-dash/mil2525'))" in server
install=(ROOT/'install.sh').read_text()
assert 'rm -f "$APP_DIR/assets/mil2525/icons.json"' in install
assert 'rm -rf "$APP_DIR/assets/mil2525/svg"' in install
for conf in (ROOT/'nginx/tak-map-https-9444.conf',ROOT/'nginx/tak-map-https-9444.conf.example'):
 text=conf.read_text()
 assert 'max-age=604800, immutable' not in text
 assert text.count('no-cache, max-age=0, must-revalidate')>=2
# Alias hashes for recolored canonical files must match current bytes.
alias=json.loads((MIL/'atak-compatibility-aliases-i553.json').read_text())
checked=0
def walk(value):
 global checked
 if isinstance(value,dict):
  fn=value.get('file')
  if fn in set(pink)|set(blue) and 'image_sha256' in value:
   assert value['image_sha256']==hashlib.sha256((SVG/fn).read_bytes()).hexdigest(),fn
   checked+=1
  for v in value.values(): walk(v)
 elif isinstance(value,list):
  for v in value: walk(v)
walk(alias)
assert checked>0
print(json.dumps({'ok':True,'pink_canonical_files':38,'blue_utility_controls':4,'military_blue_control':True,'alternate_artwork_files':0,'single_authoritative_runtime_catalog':True,'cache_identity':'i590-civilian-pink-v1','alias_hashes_checked':checked},indent=2))
