#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/tak-map"
DATA_DIR="/var/lib/tak-map"
LOCKSCREEN_ASSET_DIR="/usr/share/tak-server-dash/lockscreen"
ENV_FILE="/etc/tak-map.env"
SERVICE_FILE="/etc/systemd/system/tak-map.service"
WRAPPER="/usr/local/sbin/tak-map-action"
SUDOERS="/etc/sudoers.d/tak-map"
USER_NAME="takmap"
PAM_SERVICE_FILE="/etc/pam.d/tak-map"
if [[ "${EUID}" -ne 0 ]]; then echo "Run with sudo: sudo ./install.sh"; exit 1; fi

# Remember the extracted installer folder so one-off Downloads installs can
# clean up after themselves without touching a source checkout.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_ROOT_BASENAME="$(basename "$INSTALL_ROOT")"
CLEAN_INSTALL_ROOT=false
case "$INSTALL_ROOT_BASENAME" in
  tak-dashboard-v*-install|tak-server-dash-v*-install) CLEAN_INSTALL_ROOT=true ;;
esac

INSTALL_INVOKING_USER="${SUDO_USER:-}"
if [[ -z "$INSTALL_INVOKING_USER" || "$INSTALL_INVOKING_USER" == "root" ]]; then
  INSTALL_INVOKING_USER="$(logname 2>/dev/null || true)"
fi
if [[ "$INSTALL_INVOKING_USER" == "root" ]]; then INSTALL_INVOKING_USER=""; fi
INSTALL_INVOKING_HOME=""
if [[ -n "$INSTALL_INVOKING_USER" ]]; then
  INSTALL_INVOKING_HOME="$(getent passwd "$INSTALL_INVOKING_USER" 2>/dev/null | cut -d: -f6 || true)"
fi
if ! python3 - <<'PYYAMLCHK' >/dev/null 2>&1
import yaml
PYYAMLCHK
then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing optional OTS config update dependency: python3-yaml"
    DEBIAN_FRONTEND=noninteractive apt-get update || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3-yaml || echo "WARNING: python3-yaml install failed. ADS-B Apply to OTS may not work until PyYAML is installed."
  fi
fi

if ! python3 - <<'PYCHK' >/dev/null 2>&1
try:
    import pam
except Exception:
    import PAM
PYCHK
then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing optional upload-auth dependency: python3-pam"
    DEBIAN_FRONTEND=noninteractive apt-get update || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pam || echo "WARNING: python3-pam install failed. File upload login will not work until python3-pam or a compatible PAM module is installed."
  else
    echo "WARNING: Python PAM module not found. File upload login will not work until a PAM module for Python is installed."
  fi
fi

# Optional themed-lockscreen dependency. The dashboard still falls back to the
# system lock screen if no image-capable locker is available, but i3lock allows
# the bundled tactical-map image to be shown on X11 desktop sessions.
if ! command -v i3lock >/dev/null 2>&1 && ! command -v swaylock >/dev/null 2>&1 && ! command -v waylock >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing optional themed lock-screen dependency: i3lock"
    DEBIAN_FRONTEND=noninteractive apt-get update || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y i3lock || echo "WARNING: i3lock install failed. Lock Screen will still fall back to the existing system locker."
  fi
fi

# Optional topology-identification tools. Passive topology works without these,
# but the Scan for Details button uses them when available.
if ! command -v nmap >/dev/null 2>&1 || ! command -v arp-scan >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing optional topology scan dependencies: nmap arp-scan"
    DEBIAN_FRONTEND=noninteractive apt-get update || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y nmap arp-scan || echo "WARNING: nmap/arp-scan install failed. Passive topology will still work; Scan for Details may be limited."
  fi
fi

# Optional ACL helper used to give the locked-down dashboard service read-only
# access to the OpenTAKServer SQLite DB when OTS lives under a real user's home.
if ! command -v setfacl >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installing optional TAK Map auth dependency: acl"
    DEBIAN_FRONTEND=noninteractive apt-get update || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y acl || echo "WARNING: acl install failed. TAK Map OpenTAKServer DB auth may need manual permissions."
  fi
fi

# Remove the newer experimental dashboard service/config if it was installed.
# This package intentionally returns to the last known-good v72 layout:
#   private dashboard backend on 127.0.0.1:8091 via tak-server-dash.service
#   HTTPS entrypoint on 0.0.0.0:9444/[::]:9444 via nginx
if systemctl list-unit-files tak-server-dashboard.service >/dev/null 2>&1 || systemctl status tak-server-dashboard.service >/dev/null 2>&1; then
  systemctl disable --now tak-server-dashboard.service >/dev/null 2>&1 || true
fi
rm -f /etc/systemd/system/tak-server-dashboard.service 2>/dev/null || true
rm -f /etc/nginx/sites-enabled/tak-server-dashboard.conf /etc/nginx/sites-available/tak-server-dashboard.conf 2>/dev/null || true
rm -f /etc/nginx/conf.d/99-tak-server-dashboard-proxy-hash.conf 2>/dev/null || true
rm -f /etc/nginx/conf.d/tak-server-dashboard.conf /etc/nginx/conf.d/tak-server-dashboard-https-9443.conf 2>/dev/null || true

mkdir -p "$APP_DIR" "$DATA_DIR" "$DATA_DIR/diagnostics" "$DATA_DIR/config_backups" "$DATA_DIR/upload_staging"
cp tak_dashboard.py "$APP_DIR/tak_dashboard.py"
chmod 0755 "$APP_DIR/tak_dashboard.py"
mkdir -p "$LOCKSCREEN_ASSET_DIR"
# Keep the installed lockscreen asset set lean going forward. Remove prior bundled
# dashboard lockscreen variants, but leave unrelated/custom files alone.
find "$LOCKSCREEN_ASSET_DIR" -maxdepth 1 -type f \
  \( -name 'tactical-map-burgundy*.png' -o -name 'tactical-topo-swaylock-*.png' \) \
  ! -name 'tactical-topo-swaylock-3840x2160.png' \
  ! -name 'tactical-topo-swaylock-1920x1080.png' \
  -delete 2>/dev/null || true
if [[ -d assets/lockscreen ]]; then
  cp -f assets/lockscreen/* "$LOCKSCREEN_ASSET_DIR"/
  chmod 0644 "$LOCKSCREEN_ASSET_DIR"/* 2>/dev/null || true
fi
MIL2525_ASSET_DIR="/usr/share/tak-server-dash/mil2525"
if [[ -d assets/mil2525 ]]; then
  rm -rf "$MIL2525_ASSET_DIR"
  mkdir -p "$MIL2525_ASSET_DIR"
  cp -a assets/mil2525/. "$MIL2525_ASSET_DIR"/
  find "$MIL2525_ASSET_DIR" -type f -exec chmod 0644 {} + 2>/dev/null || true
  find "$MIL2525_ASSET_DIR" -type d -exec chmod 0755 {} + 2>/dev/null || true
fi

ADSB_ASSET_DIR="/usr/share/tak-server-dash/adsb"
if [[ -d assets/adsb ]]; then
  rm -rf "$ADSB_ASSET_DIR"
  mkdir -p "$ADSB_ASSET_DIR"
  cp -a assets/adsb/. "$ADSB_ASSET_DIR"/
  find "$ADSB_ASSET_DIR" -type f -exec chmod 0644 {} + 2>/dev/null || true
  find "$ADSB_ASSET_DIR" -type d -exec chmod 0755 {} + 2>/dev/null || true
fi

VENDOR_ASSET_DIR="/usr/share/tak-server-dash/vendor"
if [[ -d assets/vendor ]]; then
  rm -rf "$VENDOR_ASSET_DIR"
  mkdir -p "$VENDOR_ASSET_DIR"
  cp -a assets/vendor/. "$VENDOR_ASSET_DIR"/
  find "$VENDOR_ASSET_DIR" -type f -exec chmod 0644 {} + 2>/dev/null || true
  find "$VENDOR_ASSET_DIR" -type d -exec chmod 0755 {} + 2>/dev/null || true
fi
if ! id "$USER_NAME" >/dev/null 2>&1; then useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$USER_NAME"; fi
for grp in i2c gpio dialout netdev plugdev video; do if getent group "$grp" >/dev/null 2>&1; then usermod -aG "$grp" "$USER_NAME" || true; fi; done

# Give the dashboard service the minimum filesystem access needed to register
# ATAK fileshare/offline-map ZIPs in OpenTAKServer's upload folder.
OTS_WORKDIR=""
if systemctl list-unit-files opentakserver.service >/dev/null 2>&1 || systemctl status opentakserver.service >/dev/null 2>&1; then
  OTS_WORKDIR="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
fi
OTS_WORKDIR="${OTS_WORKDIR:-${INSTALL_INVOKING_HOME:+$INSTALL_INVOKING_HOME/ots}}"
OTS_WORKDIR="${OTS_WORKDIR:-${INSTALL_INVOKING_HOME:+$INSTALL_INVOKING_HOME/ots}}"
OTS_WORKDIR="${OTS_WORKDIR:-/var/lib/opentakserver}"
OTS_UPLOAD_DIR="${UPLOAD_FOLDER:-$OTS_WORKDIR/uploads}"
mkdir -p "$OTS_UPLOAD_DIR" 2>/dev/null || true
if command -v setfacl >/dev/null 2>&1; then
  setfacl -m "u:$USER_NAME:rx" "$OTS_WORKDIR" 2>/dev/null || true
  setfacl -m "u:$USER_NAME:rwx" "$OTS_UPLOAD_DIR" 2>/dev/null || true
  setfacl -d -m "u:$USER_NAME:rwx" "$OTS_UPLOAD_DIR" 2>/dev/null || true
else
  chmod a+rx "$OTS_WORKDIR" 2>/dev/null || true
  chmod a+rwx "$OTS_UPLOAD_DIR" 2>/dev/null || true
fi
chown -R "$USER_NAME:$USER_NAME" "$DATA_DIR"
chmod 0750 "$DATA_DIR"

# Repair older/corrupted CPU temperature history before starting the service.
# Malformed entries in temp_history.json caused /api/status to crash and nginx
# to show HTTP 502. Keep valid samples; back up the original when repaired.
python3 - <<PYFIX || true
import json, math, shutil, time
from pathlib import Path
data_dir = Path("$DATA_DIR")
p = data_dir / "temp_history.json"
diag = data_dir / "diagnostics"
diag.mkdir(parents=True, exist_ok=True)
now = time.time()
cutoff = now - 86400
raw = []
changed = False
if p.exists():
    try:
        raw = json.loads(p.read_text())
    except Exception:
        raw = []
        changed = True
else:
    changed = True
if not isinstance(raw, list):
    raw = []
    changed = True
fixed = []
for item in raw:
    if not isinstance(item, dict):
        changed = True
        continue
    try:
        ts = float(item.get("ts", item.get("time", item.get("timestamp"))))
        temp = float(item.get("temp_c", item.get("temp", item.get("temperature"))))
    except Exception:
        changed = True
        continue
    if not (math.isfinite(ts) and math.isfinite(temp)) or ts < cutoff or temp < -40 or temp > 150:
        changed = True
        continue
    fixed.append({"ts": ts, "temp_c": round(temp, 1)})
fixed.sort(key=lambda x: x.get("ts", 0))
if len(fixed) > 2000:
    fixed = fixed[-2000:]
    changed = True
if changed and p.exists():
    try:
        shutil.copy2(p, diag / ("temp_history.repaired.%s.json" % time.strftime("%Y%m%d-%H%M%S")))
    except Exception:
        pass
p.write_text(json.dumps(fixed))
PYFIX
chown "$USER_NAME:$USER_NAME" "$DATA_DIR/temp_history.json" 2>/dev/null || true
chmod 0664 "$DATA_DIR/temp_history.json" 2>/dev/null || true

chown -R "$USER_NAME:$USER_NAME" "$DATA_DIR/tak_map_imports" "$DATA_DIR/tak_map_offline" 2>/dev/null || true


# Clear cached gateway capability result so source/meta scraping is re-run after updates.
rm -f "$DATA_DIR/gateway_halow_cache.json" 2>/dev/null || true

# Raspberry Pi firmware interface for vcgencmd.
# Some minimal/updated installs can lose /dev/vcio, which makes commands like
# `vcgencmd pmic_read_adc` fail with:
#   Can't open device file: /dev/vcio
# Create it now and install a tmpfiles rule so it comes back after reboot.
VCIO_GROUP="root"
if getent group video >/dev/null 2>&1; then VCIO_GROUP="video"; fi
if [[ ! -e /dev/vcio ]]; then
  mknod /dev/vcio c 100 0 2>/dev/null || true
fi
if [[ -e /dev/vcio ]]; then
  chown root:"$VCIO_GROUP" /dev/vcio 2>/dev/null || true
  chmod 0660 /dev/vcio 2>/dev/null || true
fi
cat > /etc/tmpfiles.d/tak-server-dash-vcio.conf <<EOFVCIO
# Ensure Raspberry Pi firmware mailbox device exists for vcgencmd/PMIC readings.
c /dev/vcio 0660 root $VCIO_GROUP - 100:0
EOFVCIO
systemd-tmpfiles --create /etc/tmpfiles.d/tak-server-dash-vcio.conf >/dev/null 2>&1 || true
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DEFAULT_ALLOWED_SERVICES="opentakserver eud_handler_ssl rabbitmq-server"
ENV_FILE="/etc/tak-map.env"
# Load dashboard environment for configurable actions such as GPS CoT push.
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE" || true
  set +a
  ALLOWED_SERVICES="$(grep -E '^TAK_DASHBOARD_SERVICES=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- | tr ',' ' ' || true)"
fi
ALLOWED_SERVICES="${ALLOWED_SERVICES:-$DEFAULT_ALLOWED_SERVICES}"
DATA_DIR="/var/lib/tak-map"
DIAG_DIR="$DATA_DIR/diagnostics"
is_allowed_service() { local target="$1"; [[ "$target" =~ ^[A-Za-z0-9_.@-]{1,120}$ ]]; }
run_and_capture() { local title="$1"; shift; { echo; echo "===== $title ====="; echo "\$ $*"; "$@" 2>&1 || true; }; }

set_default_route_for_iface() {
  local iface="$1"
  if ! [[ "$iface" =~ ^[A-Za-z0-9_.:-]{1,32}$ ]]; then
    echo "Invalid interface name: $iface" >&2
    exit 2
  fi
  if ! /usr/sbin/ip link show "$iface" >/dev/null 2>&1; then
    echo "Interface not found: $iface" >&2
    echo
    echo "Available interfaces:" >&2
    /usr/sbin/ip -br link >&2 || true
    exit 1
  fi

  /usr/sbin/ip link set "$iface" up >/dev/null 2>&1 || true

  local gw=""
  if command -v nmcli >/dev/null 2>&1; then
    gw="$(nmcli -g IP4.GATEWAY device show "$iface" 2>/dev/null | awk 'NF && $1 != "--" {print; exit}' || true)"
  fi
  if [[ -z "$gw" ]]; then
    gw="$(/usr/sbin/ip -4 route show default dev "$iface" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="via") {print $(i+1); exit}}' || true)"
  fi
  if [[ -z "$gw" ]]; then
    gw="$(/usr/sbin/ip -4 route show dev "$iface" 2>/dev/null | awk '/via/ {for(i=1;i<=NF;i++) if($i=="via") {print $(i+1); exit}}' || true)"
  fi

  echo "Setting preferred default route for interface: $iface"
  if [[ -n "$gw" ]]; then
    echo "Using gateway: $gw"
    /usr/sbin/ip route replace default via "$gw" dev "$iface" metric 10
  elif [[ "$iface" == wwan* || "$iface" == ppp* || "$iface" == tun* || "$iface" == usb* ]]; then
    echo "No gateway detected; using direct interface default route for point-to-point style interface."
    /usr/sbin/ip route replace default dev "$iface" metric 10
  else
    echo "No gateway detected for $iface; refusing to set a direct default route on a non-cellular/non-tunnel interface." >&2
    echo
    echo "Current IPv4 routes for $iface:" >&2
    /usr/sbin/ip -4 route show dev "$iface" >&2 || true
    exit 1
  fi

  echo
  echo "Default routes after change:"
  /usr/sbin/ip route show default || true
  echo
  echo "Route test to 1.1.1.1:"
  /usr/sbin/ip route get 1.1.1.1 || true
}

if [[ "${1:-}" == "adsb-update-ots-config" || "${1:-}" == "adsb-write-ots-config" ]]; then
  ADSB_ACTION="${1:-}"
  CFG_PATH="${2:-}"
  CENTER_LAT="${3:-}"
  CENTER_LON="${4:-}"
  CENTER_RADIUS="${5:-}"
  export ADSB_ACTION CFG_PATH CENTER_LAT CENTER_LON CENTER_RADIUS
  exec /usr/bin/python3 - <<'PYADSBOTS'
import os, sys, re, shutil, subprocess
from pathlib import Path
from datetime import datetime, timezone

def fail(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)

action=os.environ.get('ADSB_ACTION','adsb-update-ots-config').strip()
restart_after_write = action != 'adsb-write-ots-config'

cfg_raw=os.environ.get('CFG_PATH','').strip()
if not cfg_raw:
    fail('Missing config path.',2)
cfg=Path(cfg_raw).expanduser()
try:
    cfg=cfg.resolve(strict=True)
except Exception as e:
    fail(f'Config path not found: {e}',2)
if cfg.name not in ('config.yml','config.yaml'):
    fail(f'Refusing to edit unexpected config filename: {cfg}',2)
allowed_roots=[]
for raw in ('/home','/opt/opentakserver','/etc/opentakserver','/var/lib/opentakserver','/usr/local/share/opentakserver','/srv/opentakserver'):
    try:
        allowed_roots.append(Path(raw).resolve())
    except Exception:
        pass
if not any(str(cfg).startswith(str(root) + os.sep) or cfg == root for root in allowed_roots):
    fail(f'Refusing to edit config outside allowed OTS locations: {cfg}',2)

def parse_coord(name, low, high):
    raw=str(os.environ.get(name,'')).strip()
    if not raw:
        fail(f'Missing {name}.',2)
    try:
        value=float(raw)
    except Exception:
        fail(f'Invalid {name}: {raw}',2)
    if not (low <= value <= high):
        fail(f'{name} out of range: {value}',2)
    return value
lat=parse_coord('CENTER_LAT', -90, 90)
lon=parse_coord('CENTER_LON', -180, 180)

def parse_radius(name):
    raw=str(os.environ.get(name,'')).strip()
    if not raw:
        return None
    try:
        value=float(raw)
    except Exception:
        fail(f'Invalid {name}: {raw}',2)
    if not (1 <= value <= 250):
        fail(f'{name} out of range: {value}',2)
    return value
radius=parse_radius('CENTER_RADIUS')

def fmt_coord(v):
    return f'{float(v):.6f}'

def fmt_radius(v):
    return str(int(round(float(v))))

def update_yaml_scalar(text, key, value):
    value=str(value)
    pattern=re.compile(r'^(\s*'+re.escape(key)+r'\s*:\s*)([^#\r\n]*)(\s*(?:#.*)?)$', re.M)
    if pattern.search(text):
        return pattern.sub(lambda m: m.group(1)+value+(m.group(3) or ''), text, count=1), True
    if text and not text.endswith('\n'):
        text += '\n'
    return text + f'{key}: {value}\n', False

def update_yaml_line(text, key, value):
    return update_yaml_scalar(text, key, fmt_coord(value))

try:
    raw=cfg.read_text()
except Exception as e:
    fail(f'Could not read config: {e}',3)
backups=Path('/var/lib/tak-server-dash/config_backups/opentakserver')
try:
    backups.mkdir(parents=True, exist_ok=True)
except Exception:
    backups=cfg.parent
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=backups/(cfg.name+'.adsb-'+stamp+'.bak')
try:
    shutil.copy2(cfg, backup)
except Exception as e:
    fail(f'Could not create backup: {e}',3)
rendered, lat_existing = update_yaml_line(raw, 'OTS_ADSB_LAT', lat)
rendered, lon_existing = update_yaml_line(rendered, 'OTS_ADSB_LON', lon)
radius_existing = False
if radius is not None:
    rendered, radius_existing = update_yaml_scalar(rendered, 'OTS_ADSB_RADIUS', fmt_radius(radius))
try:
    tmp=cfg.with_name(cfg.name + f'.takdash-{os.getpid()}.tmp')
    tmp.write_text(rendered)
    shutil.copystat(cfg, tmp, follow_symlinks=True)
    os.replace(tmp, cfg)
except Exception as e:
    try:
        tmp.unlink()
    except Exception:
        pass
    fail(f'Could not write updated config: {e}',4)
systemctl=shutil.which('systemctl') or '/usr/bin/systemctl'
r=None
if restart_after_write:
    r=subprocess.run([systemctl,'restart','opentakserver'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
print(f'CONFIG_PATH={cfg}')
print(f'BACKUP_PATH={backup}')
print(f'OTS_ADSB_LAT={fmt_coord(lat)}')
print(f'OTS_ADSB_LON={fmt_coord(lon)}')
if radius is not None:
    print(f'OTS_ADSB_RADIUS={fmt_radius(radius)}')
print(f'LAT_KEY_EXISTED={int(lat_existing)}')
print(f'LON_KEY_EXISTED={int(lon_existing)}')
print(f'RADIUS_KEY_EXISTED={int(radius_existing)}')
if r is not None and r.returncode != 0:
    print(r.stdout or '', end='')
    print(r.stderr or '', end='', file=sys.stderr)
    fail(f'opentakserver restart failed rc={r.returncode}',5)
if restart_after_write:
    print('OTS_ADSB_LAT / OTS_ADSB_LON / OTS_ADSB_RADIUS updated and opentakserver restarted.' if radius is not None else 'OTS_ADSB_LAT / OTS_ADSB_LON updated and opentakserver restarted.')
else:
    print('OTS_ADSB_LAT / OTS_ADSB_LON / OTS_ADSB_RADIUS updated. opentakserver was not restarted yet.' if radius is not None else 'OTS_ADSB_LAT / OTS_ADSB_LON updated. opentakserver was not restarted yet.')
PYADSBOTS
fi

if [[ "${1:-}" == "restart-opentakserver" ]]; then
  exec /usr/bin/systemctl restart opentakserver
fi

if [[ "${1:-}" == "remote-default" ]]; then
  cmd_id="${2:-}"
  case "$cmd_id" in
    restart-networkmanager) exec /usr/bin/systemctl restart NetworkManager ;;
    toggle-networking) exec /bin/bash -lc 'nmcli networking off && sleep 3 && nmcli networking on' ;;
    bounce-wwan0) exec /bin/bash -lc 'ip link set wwan0 down && sleep 3 && ip link set wwan0 up' ;;
    restart-4g-modem) exec /usr/bin/systemctl restart 4gmodem ;;
    restart-zerotier) exec /usr/bin/systemctl restart zerotier-one ;;
    set-default-route-wwan0) set_default_route_for_iface wwan0; exit $? ;;
    set-default-route-wlan0) set_default_route_for_iface wlan0; exit $? ;;
    set-default-route-eth0) set_default_route_for_iface eth0; exit $? ;;
    restart-dashboard) exec /usr/bin/systemctl restart tak-map.service || true ;;
    reload-nginx) exec /bin/bash -lc 'nginx -t && systemctl reload nginx' ;;
    restart-nginx) exec /usr/bin/systemctl restart nginx ;;
    restart-opentakserver) exec /usr/bin/systemctl restart opentakserver ;;
    find-tak-services) exec /bin/bash -lc 'systemctl list-units --type=service --all | grep -i tak || true' ;;
    restart-mediamtx) exec /usr/bin/systemctl restart mediamtx ;;
    restart-mumble) exec /usr/bin/systemctl restart mumble-server ;;
    restart-mosquitto) exec /usr/bin/systemctl restart mosquitto ;;
    show-ip-addresses) exec /usr/sbin/ip -br addr ;;
    show-routes) exec /usr/sbin/ip route ;;
    show-nm-devices) exec /usr/bin/nmcli device status ;;
    show-failed-services) exec /usr/bin/systemctl --failed ;;
    show-recent-warnings) exec /usr/bin/journalctl -p warning -n 100 --no-pager ;;
    show-dashboard-logs) exec /usr/bin/journalctl -u tak-server-dash.service -n 100 --no-pager ;;
    check-pi-throttling) exec /usr/bin/vcgencmd get_throttled ;;
    check-pi-temperature) exec /usr/bin/vcgencmd measure_temp ;;
    check-pmic-voltage) exec /usr/bin/vcgencmd pmic_read_adc ;;
    vacuum-old-logs) exec /usr/bin/journalctl --vacuum-time=7d ;;
    show-disk-usage) exec /usr/bin/df -h ;;
    show-memory-usage) exec /usr/bin/free -h ;;
    *) echo "Unknown default command ID: $cmd_id" >&2; exit 2 ;;
  esac
fi

if [[ "${1:-}" == "config-backup" ]]; then
  exec /usr/bin/python3 - <<'PYCONFIGBACKUP'
import json, os, zipfile, shutil
from pathlib import Path
from datetime import datetime, timezone
DATA_DIR=Path('/var/lib/tak-server-dash')
BACKUP_DIR=DATA_DIR/'config_backups'
ENV_FILE=Path('/etc/tak-server-dash.env')
FILES=[
    ('etc/tak-server-dash.env', ENV_FILE),
    ('var/lib/tak-server-dash/config.json', DATA_DIR/'config.json'),
    ('var/lib/tak-server-dash/neighbor_hostname_cache.json', DATA_DIR/'neighbor_hostname_cache.json'),
    ('var/lib/tak-server-dash/topology_layout.json', DATA_DIR/'topology_layout.json'),
    ('var/lib/tak-server-dash/gateway_halow_cache.json', DATA_DIR/'gateway_halow_cache.json'),
]
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
ts=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')
out=BACKUP_DIR/f'tak-server-dash-config-backup-{ts}.zip'
manifest={'created_utc':ts,'format':'tak-server-dash-config-backup-v1','files':[],'note':'Contains dashboard configuration, including environment values. Store securely.'}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for arc, src in FILES:
        if src.exists() and src.is_file():
            z.write(src, arc)
            manifest['files'].append({'archive_name':arc,'source_path':str(src),'size_bytes':src.stat().st_size})
    z.writestr('manifest.json', json.dumps(manifest, indent=2))
os.chmod(out,0o640)
try:
    shutil.chown(out, 'takserverdash', 'takserverdash')
except Exception:
    pass
print(f'BACKUP_PATH={out}')
print(f'FILES={len(manifest["files"])}')
PYCONFIGBACKUP
fi

if [[ "${1:-}" == "config-restore" ]]; then
  RESTORE_SRC="${2:-}"
  export RESTORE_SRC
  exec /usr/bin/python3 - <<'PYCONFIGRESTORE'
import json, os, zipfile, shutil, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone
DATA_DIR=Path('/var/lib/tak-server-dash')
BACKUP_DIR=DATA_DIR/'config_backups'
ENV_FILE=Path('/etc/tak-server-dash.env')
SRC=Path(os.environ.get('RESTORE_SRC',''))
ALLOWED={
    'etc/tak-server-dash.env': ENV_FILE,
    'var/lib/tak-server-dash/config.json': DATA_DIR/'config.json',
    'var/lib/tak-server-dash/neighbor_hostname_cache.json': DATA_DIR/'neighbor_hostname_cache.json',
    'var/lib/tak-server-dash/topology_layout.json': DATA_DIR/'topology_layout.json',
    'var/lib/tak-server-dash/gateway_halow_cache.json': DATA_DIR/'gateway_halow_cache.json',
}
def fail(msg, code=1):
    print(msg, file=sys.stderr); sys.exit(code)
def make_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    out=BACKUP_DIR/f'tak-server-dash-pre-restore-backup-{ts}.zip'
    manifest={'created_utc':ts,'format':'tak-server-dash-config-backup-v1','reason':'automatic pre-restore backup','files':[]}
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for arc,target in ALLOWED.items():
            if target.exists() and target.is_file():
                z.write(target, arc)
                manifest['files'].append({'archive_name':arc,'source_path':str(target),'size_bytes':target.stat().st_size})
        z.writestr('manifest.json', json.dumps(manifest, indent=2))
    os.chmod(out,0o640)
    try: shutil.chown(out, 'takserverdash', 'takserverdash')
    except Exception: pass
    return out
if not str(SRC): fail('No restore source path provided.',2)
try:
    SRC=SRC.resolve(strict=True)
except Exception:
    fail(f'Restore source not found: {SRC}',2)
# Only allow restoring from dashboard-owned staging/backup locations.
allowed_roots=[(DATA_DIR/'upload_staging').resolve(), BACKUP_DIR.resolve()]
if not any(str(SRC).startswith(str(root) + os.sep) or SRC == root for root in allowed_roots):
    fail(f'Restore source path is outside allowed dashboard staging folders: {SRC}',2)
if SRC.stat().st_size > 25*1024*1024:
    fail('Restore ZIP is too large.',2)
try:
    z=zipfile.ZipFile(SRC,'r')
except Exception as e:
    fail(f'Invalid ZIP file: {e}',2)
with z:
    names=z.namelist()
    restore_names=[n for n in names if n in ALLOWED]
    if not restore_names:
        fail('Backup ZIP did not contain recognized dashboard config files.',2)
    for n in names:
        if n.startswith('/') or '..' in Path(n).parts:
            fail(f'Unsafe ZIP path rejected: {n}',2)
    pre=make_backup()
    print(f'PRE_RESTORE_BACKUP={pre}')
    restored=[]
    for n in restore_names:
        info=z.getinfo(n)
        if info.file_size > 1024*1024:
            fail(f'Config entry too large: {n}',2)
        data=z.read(n)
        if b'\x00' in data:
            fail(f'Config entry contains NUL byte and was rejected: {n}',2)
        if n.endswith('.json'):
            try: json.loads(data.decode('utf-8'))
            except Exception as e: fail(f'Invalid JSON in {n}: {e}',2)
        target=ALLOWED[n]
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp=target.with_name(target.name + f'.restore-{os.getpid()}.tmp')
        tmp.write_bytes(data)
        if target == ENV_FILE:
            os.chmod(tmp,0o600)
            try: shutil.chown(tmp, 'root', 'root')
            except Exception: pass
        else:
            os.chmod(tmp,0o640)
            try: shutil.chown(tmp, 'takserverdash', 'takserverdash')
            except Exception: pass
        os.replace(tmp, target)
        restored.append(str(target))
    print('RESTORED_FILES=' + ','.join(restored))
    print('Restore complete. Restart tak-server-dash.service to apply environment-file changes.')
PYCONFIGRESTORE
fi

if [[ "${1:-}" == "topology-scan" ]]; then
  exec /usr/bin/python3 - <<'PYTOPOSCAN'
import json, os, re, shutil, subprocess, time, ipaddress, xml.etree.ElementTree as ET

def run(cmd, timeout=25):
    try:
        p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {'cmd':' '.join(cmd),'rc':p.returncode,'stdout':p.stdout or '','stderr':p.stderr or ''}
    except Exception as e:
        return {'cmd':' '.join(cmd),'rc':127,'stdout':'','stderr':str(e)}

def ip_json(args):
    r=run(['/usr/sbin/ip','-j']+args,10)
    try:
        return json.loads(r['stdout'] or '[]')
    except Exception:
        return []

def safe_networks():
    nets=[]; seen=set()
    addrs=ip_json(['addr'])
    for iface in addrs:
        name=iface.get('ifname') or ''
        if name=='lo':
            continue
        for a in iface.get('addr_info') or []:
            if a.get('family')!='inet' or not a.get('local'):
                continue
            try:
                pref=int(a.get('prefixlen') or 24)
                net=ipaddress.ip_network(f"{a.get('local')}/{pref}", strict=False)
                if not (net.is_private or net.is_link_local):
                    continue
                # Keep scans bounded. /23 and smaller are okay; larger networks are not actively scanned.
                if net.num_addresses>512:
                    continue
                key=(str(net),name)
                if key not in seen:
                    seen.add(key); nets.append({'network':str(net),'interface':name,'address':a.get('local')})
            except Exception:
                pass
    return nets[:8]

def parse_nmap_xml(text):
    nodes={}
    if not text.strip().startswith('<?xml') and '<nmaprun' not in text:
        return nodes
    try:
        root=ET.fromstring(text)
    except Exception:
        return nodes
    for host in root.findall('host'):
        status=(host.find('status').get('state') if host.find('status') is not None else '')
        ip=''; mac=''; vendor=''
        for addr in host.findall('address'):
            if addr.get('addrtype')=='ipv4': ip=addr.get('addr') or ip
            if addr.get('addrtype')=='mac':
                mac=addr.get('addr') or mac
                vendor=addr.get('vendor') or vendor
        if not ip:
            continue
        hostnames=[]
        hn=host.find('hostnames')
        if hn is not None:
            for h in hn.findall('hostname'):
                if h.get('name'):
                    hostnames.append(h.get('name'))
        os_family=''; os_name=''; os_accuracy=''; device_type=''; os_vendor=''
        osel=host.find('os')
        if osel is not None:
            best=osel.find('osmatch')
            if best is not None:
                os_name=best.get('name') or ''
                os_accuracy=best.get('accuracy') or ''
                cls=best.find('osclass')
                if cls is not None:
                    os_family=cls.get('osfamily') or ''
                    device_type=cls.get('type') or ''
                    os_vendor=cls.get('vendor') or ''
        services=[]
        ports=host.find('ports')
        if ports is not None:
            for port in ports.findall('port'):
                svc=port.find('service')
                state=port.find('state')
                if svc is not None and (state is None or state.get('state')=='open'):
                    services.append({'port':port.get('portid'),'name':svc.get('name') or '', 'product':svc.get('product') or '', 'ostype':svc.get('ostype') or ''})
        if not os_family:
            low=(os_name+' '+' '.join((x.get('ostype') or '')+' '+(x.get('product') or '') for x in services)).lower()
            if 'android' in low: os_family='Android'
            elif 'linux' in low or 'ubuntu' in low or 'debian' in low: os_family='Linux'
            elif 'windows' in low or 'microsoft' in low: os_family='Windows'
            elif 'mac os' in low or 'apple' in low or 'darwin' in low: os_family='macOS'
        if not device_type:
            low=(os_name+' '+(hostnames[0] if hostnames else '')+' '+vendor).lower()
            if re.search(r'phone|iphone|android|galaxy|pixel', low): device_type='phone'
            elif re.search(r'ipad|tablet|tab|eud|atak', low): device_type='tablet'
            elif re.search(r'router|gateway|wap|access point', low): device_type='router'
            elif re.search(r'server|raspberry|linux|ubuntu|debian', low): device_type='server'
            elif re.search(r'laptop|desktop|pc|workstation|macbook|thinkpad|surface|latitude', low): device_type='computer'
            else: device_type='endpoint'
        conf='low'
        try:
            acc=int(os_accuracy or 0)
            conf='high' if acc>=90 else ('medium' if acc>=70 else 'low')
        except Exception:
            conf='medium' if vendor or services else 'low'
        nodes[ip]={'ip':ip,'mac':mac,'hostname':hostnames[0] if hostnames else '', 'manufacturer':vendor or os_vendor, 'os_family':os_family or '', 'device_type':device_type or '', 'os_name':os_name, 'confidence':conf, 'services':services[:8], 'status':status or 'unknown', 'source':'nmap'}
    return nodes

def parse_arp_scan(text, iface):
    nodes={}
    for line in (text or '').splitlines():
        line=line.strip()
        if not line or line.startswith('Interface:') or line.startswith('Starting') or line.startswith('Ending'):
            continue
        parts=line.split('\t') if '\t' in line else re.split(r'\s{2,}', line)
        if len(parts)<2:
            parts=line.split(None,2)
        if len(parts)>=2 and re.match(r'^\d+\.\d+\.\d+\.\d+$', parts[0]) and re.match(r'^[0-9a-fA-F:]{11,17}$', parts[1]):
            nodes[parts[0]]={'ip':parts[0],'mac':parts[1], 'manufacturer':parts[2].strip() if len(parts)>2 else '', 'interface':iface, 'source':'arp-scan', 'confidence':'medium'}
    return nodes

started=time.time()
tools={'nmap':bool(shutil.which('nmap')),'arp-scan':bool(shutil.which('arp-scan'))}
networks=safe_networks()
all_nodes={}
notes=[]
# ARP scan local Ethernet/Wi-Fi style interfaces only.
if tools['arp-scan']:
    for net in networks:
        iface=net.get('interface') or ''
        if iface.startswith(('eth','en','wlan','wl')):
            r=run(['arp-scan','--interface',iface,'--localnet'],25)
            for ip,node in parse_arp_scan(r['stdout'], iface).items():
                all_nodes.setdefault(ip,{}).update(node)
            if r['rc']!=0 and r['stderr']:
                notes.append(f"arp-scan {iface}: {r['stderr'][:180]}")
else:
    notes.append('arp-scan not installed')
# Nmap discovery and limited detail scan on bounded private networks.
if tools['nmap']:
    discovered=set()
    for net in networks:
        r=run(['nmap','-sn','-oX','-',net['network']],45)
        parsed=parse_nmap_xml(r['stdout'])
        for ip,node in parsed.items():
            discovered.add(ip); all_nodes.setdefault(ip,{}).update(node)
        if r['rc'] not in (0,1) and r['stderr']:
            notes.append(f"nmap discovery {net['network']}: {r['stderr'][:180]}")
    targets=sorted(discovered or all_nodes.keys())[:32]
    if targets:
        r=run(['nmap','-O','--osscan-guess','--max-os-tries','1','-sV','--version-light','--top-ports','30','-oX','-']+targets,120)
        parsed=parse_nmap_xml(r['stdout'])
        for ip,node in parsed.items():
            base=all_nodes.setdefault(ip,{})
            base.update({k:v for k,v in node.items() if v not in ('',[],None)})
        if r['rc'] not in (0,1) and r['stderr']:
            notes.append(f"nmap detail: {r['stderr'][:300]}")
else:
    notes.append('nmap not installed')
out={'ok':True,'timestamp':int(time.time()),'duration_sec':round(time.time()-started,2),'mode':'active scan','tools':tools,'networks':networks,'nodes':all_nodes,'notes':notes,'warning':'Active scan is limited to detected private/local networks with 512 addresses or fewer.'}
print(json.dumps(out, separators=(',',':')))
PYTOPOSCAN
fi
if [[ "${1:-}" == "service" ]]; then
  action="${2:-}"; service="${3:-}"
  case "$action" in start|stop|restart) ;; *) echo "Invalid action: $action" >&2; exit 2 ;; esac
  is_allowed_service "$service" || { echo "Service not allowed: $service" >&2; exit 2; }
  exec /usr/bin/systemctl "$action" "$service"
fi
if [[ "${1:-}" == "dhclient" ]]; then
  if command -v dhclient >/dev/null 2>&1; then exec "$(command -v dhclient)" -v wwan0; fi
  echo "dhclient not found" >&2; exit 127
fi
if [[ "${1:-}" == "modem-gps" ]]; then
  exec /usr/bin/python3 - <<'PYGPS'
import json, os, re, shutil, subprocess, sys, time, glob, termios, select
from pathlib import Path

attempts=[]
GPS_START=time.time()

def env_int(name, default):
    try:
        return int(str(os.environ.get(name, str(default))).strip())
    except Exception:
        return int(default)

def env_float(name, default):
    try:
        return float(str(os.environ.get(name, str(default))).strip())
    except Exception:
        return float(default)

GPS_TOTAL_TIMEOUT=max(60, env_int('TAK_DASH_GPS_TOTAL_TIMEOUT_SECONDS', 330))

def gps_elapsed():
    return time.time()-GPS_START

def gps_time_left():
    return max(0.0, GPS_TOTAL_TIMEOUT-gps_elapsed())

def gps_time_low(min_left=3):
    return gps_time_left() <= float(min_left)

def gps_timeout_note():
    return f'GPS total diagnostic time limit reached after {int(gps_elapsed())}s of {GPS_TOTAL_TIMEOUT}s'

def env(name, default=''):
    return os.environ.get(name, default)

def env_bool(name, default=False):
    val=str(os.environ.get(name, 'true' if default else 'false')).strip().lower()
    return val in ('1','true','yes','on')

def run(cmd, timeout=10):
    try:
        p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {'cmd':' '.join(cmd), 'rc':p.returncode, 'stdout':p.stdout or '', 'stderr':p.stderr or '', 'ok':p.returncode==0}
    except Exception as e:
        return {'cmd':' '.join(cmd), 'rc':127, 'stdout':'', 'stderr':str(e), 'ok':False}

def brief(s, n=900):
    s=str(s or '').strip()
    return s[:n]

def add_attempt(method, ok=False, note='', rc=None, stdout='', stderr=''):
    item={'method':method,'ok':bool(ok),'note':str(note or '')}
    if rc is not None: item['rc']=rc
    if stdout: item['stdout']=brief(stdout)
    if stderr: item['stderr']=brief(stderr)
    attempts.append(item)
    return item

def fnum(v):
    try:
        if v is None or str(v).strip() in ('','--','unknown'):
            return None
        return float(str(v).strip().strip("'\""))
    except Exception:
        return None

def nmea_deg(raw, hemi):
    raw=str(raw or '').strip()
    if not raw or not hemi:
        return None
    try:
        val=float(raw)
        deg=int(val/100)
        minutes=val-(deg*100)
        dec=deg+(minutes/60.0)
        if str(hemi).upper() in ('S','W'):
            dec=-dec
        return dec
    except Exception:
        return None

def valid_lat_lon(lat, lon):
    return lat is not None and lon is not None and -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180 and not (float(lat)==0 and float(lon)==0)

def parse_nmea(text):
    for line in (text or '').splitlines():
        line=line.strip().strip("'")
        if not line.startswith('$'):
            continue
        parts=line.split('*',1)[0].split(',')
        typ=parts[0].upper()
        if typ.endswith('GGA') and len(parts) >= 10:
            lat=nmea_deg(parts[2], parts[3]); lon=nmea_deg(parts[4], parts[5])
            fix=parts[6] if len(parts)>6 else ''
            if valid_lat_lon(lat, lon) and fix not in ('0',''):
                alt=fnum(parts[9])
                return {'latitude':lat,'longitude':lon,'altitude_m':alt,'utc_time':parts[1] or None,'note':'Parsed GPS fix from NMEA GGA'}
        if typ.endswith('RMC') and len(parts) >= 7:
            if (parts[2] or '').upper() != 'A':
                continue
            lat=nmea_deg(parts[3], parts[4]); lon=nmea_deg(parts[5], parts[6])
            if valid_lat_lon(lat, lon):
                return {'latitude':lat,'longitude':lon,'utc_time':parts[1] or None,'note':'Parsed GPS fix from NMEA RMC'}
    return None

def parse_mmcli_location(text):
    out={}
    m=re.search(r'latitude\s*:\s*\'?([-+0-9.]+)\'?', text, re.I)
    if m: out['latitude']=fnum(m.group(1))
    m=re.search(r'longitude\s*:\s*\'?([-+0-9.]+)\'?', text, re.I)
    if m: out['longitude']=fnum(m.group(1))
    m=re.search(r'altitude\s*:\s*\'?([-+0-9.]+)\'?', text, re.I)
    if m: out['altitude_m']=fnum(m.group(1))
    m=re.search(r'accuracy\s*:\s*\'?([-+0-9.]+)', text, re.I)
    if m: out['accuracy_m']=fnum(m.group(1))
    m=re.search(r'utc\s*time\s*:\s*\'?([^\'\n]+)\'?', text, re.I)
    if m: out['utc_time']=m.group(1).strip()
    if valid_lat_lon(out.get('latitude'), out.get('longitude')):
        out['note']='Pulled GPS coordinates through ModemManager'
        return out
    n=parse_nmea(text)
    if n:
        return n
    return None

def parse_cgpsinfo(text):
    # SIMCom/SIM7600 style: +CGPSINFO: lat,N,lon,W,date,utc,alt,speed,course
    m=re.search(r'\+CGPSINFO:\s*([^\r\n]+)', text, re.I)
    if not m:
        return None
    fields=[x.strip().strip('"') for x in m.group(1).split(',')]
    if len(fields) < 4 or not fields[0] or not fields[2]:
        return None
    lat=nmea_deg(fields[0], fields[1] if len(fields)>1 else '')
    lon=nmea_deg(fields[2], fields[3] if len(fields)>3 else '')
    if not valid_lat_lon(lat, lon):
        return None
    return {'latitude':lat,'longitude':lon,'utc_time':fields[5] if len(fields)>5 else None,'altitude_m':fnum(fields[6] if len(fields)>6 else None),'note':'Parsed GPS fix from SIMCom AT+CGPSINFO'}

def parse_cgnsinf(text):
    # SIMCom newer style: +CGNSINF: run,fix,utc,lat,lon,alt,...
    m=re.search(r'\+CGNSINF:\s*([^\r\n]+)', text, re.I)
    if not m:
        return None
    fields=[x.strip().strip('"') for x in m.group(1).split(',')]
    if len(fields) < 5:
        return None
    fix=fields[1] if len(fields)>1 else ''
    lat=fnum(fields[3] if len(fields)>3 else None)
    lon=fnum(fields[4] if len(fields)>4 else None)
    if fix not in ('1','2','3') or not valid_lat_lon(lat, lon):
        return None
    return {'latitude':lat,'longitude':lon,'utc_time':fields[2] if len(fields)>2 else None,'altitude_m':fnum(fields[5] if len(fields)>5 else None),'note':'Parsed GPS fix from SIMCom AT+CGNSINF'}

def parse_qgpsloc(text):
    # Quectel style: +QGPSLOC: utc,lat,lon,hdop,alt,fix,...
    m=re.search(r'\+QGPSLOC:\s*([^\r\n]+)', text, re.I)
    if not m:
        return None
    fields=[x.strip().strip('"') for x in m.group(1).split(',')]
    if len(fields) < 3:
        return None
    lat=fnum(fields[1]); lon=fnum(fields[2])
    # Some outputs may use NMEA degrees; decimal mode should not, but try a fallback if needed.
    if not valid_lat_lon(lat, lon) and len(fields) >= 3:
        # No hemisphere is provided in QGPSLOC, so avoid guessing if not already valid decimal.
        return None
    return {'latitude':lat,'longitude':lon,'utc_time':fields[0] if fields else None,'accuracy_m':fnum(fields[3] if len(fields)>3 else None),'altitude_m':fnum(fields[4] if len(fields)>4 else None),'note':'Parsed GPS fix from Quectel AT+QGPSLOC'}

def parse_gpsacp(text):
    # Telit style: $GPSACP: utc,latH,lonH,hdop,alt,fix,... or decimal variants.
    m=re.search(r'\$GPSACP:\s*([^\r\n]+)', text, re.I)
    if not m:
        return None
    fields=[x.strip().strip('"') for x in m.group(1).split(',')]
    if len(fields) < 3:
        return None
    lat_raw=fields[1]; lon_raw=fields[2]
    lat=lon=None
    lm=re.match(r'([0-9.]+)([NS])$', lat_raw, re.I)
    om=re.match(r'([0-9.]+)([EW])$', lon_raw, re.I)
    if lm and om:
        lat=nmea_deg(lm.group(1), lm.group(2)); lon=nmea_deg(om.group(1), om.group(2))
    else:
        lat=fnum(lat_raw); lon=fnum(lon_raw)
    if not valid_lat_lon(lat, lon):
        return None
    return {'latitude':lat,'longitude':lon,'utc_time':fields[0] if fields else None,'accuracy_m':fnum(fields[3] if len(fields)>3 else None),'altitude_m':fnum(fields[4] if len(fields)>4 else None),'note':'Parsed GPS fix from Telit AT$GPSACP'}

def parse_any_gps(text):
    return (parse_nmea(text) or parse_qgpsloc(text) or parse_cgpsinfo(text) or parse_cgnsinf(text) or parse_gpsacp(text))

def disable_modem_gps(mid):
    if not env_bool('TAK_DASH_GPS_DISABLE_AFTER_PULL', True):
        add_attempt(f'ModemManager/mmcli modem {mid} disable', False, 'GPS disable after pull is disabled by TAK_DASH_GPS_DISABLE_AFTER_PULL=false')
        return []
    disables=[]
    for opt in ('--location-disable-gps-raw','--location-disable-gps-nmea'):
        dr=run(['mmcli','-m',mid,opt],8)
        disables.append(f'{opt}: rc {dr["rc"]}')
        add_attempt(f'ModemManager/mmcli modem {mid} {opt}', dr['ok'], 'Attempted to disable modem GPS source after pull', dr['rc'], dr['stdout'], dr['stderr'])
    return disables

def try_modemmanager():
    if not shutil.which('mmcli'):
        add_attempt('ModemManager/mmcli', False, 'mmcli not installed')
        return None
    r=run(['mmcli','-L'],8)
    modem_ids=re.findall(r'/Modem/(\d+)', r['stdout']+r['stderr'])
    if not modem_ids:
        add_attempt('ModemManager/mmcli', False, 'No modem listed by mmcli', r['rc'], r['stdout'], r['stderr'])
        return None
    wait_seconds=max(30, int(env('TAK_DASH_GPS_FIX_WAIT_SECONDS','300') or 300))
    poll_seconds=max(2, int(env('TAK_DASH_GPS_FIX_POLL_SECONDS','3') or 5))
    combo_seconds=max(30, env_int('TAK_DASH_GPS_MMCLI_COMBO_SECONDS', 300))
    for mid in modem_ids:
        status_before=run(['mmcli','-m',mid,'--location-status'],8)
        add_attempt(f'ModemManager/mmcli modem {mid} status-before', status_before['ok'], 'Location status before enabling GPS', status_before['rc'], status_before['stdout'], status_before['stderr'])
        for opt in ('--location-enable-gps-raw','--location-enable-gps-nmea'):
            er=run(['mmcli','-m',mid,opt],10)
            add_attempt(f'ModemManager/mmcli modem {mid} {opt}', er['ok'], 'Attempted to enable modem GPS source for this pull', er['rc'], er['stdout'], er['stderr'])
        status_after=run(['mmcli','-m',mid,'--location-status'],8)
        add_attempt(f'ModemManager/mmcli modem {mid} status-after-enable', status_after['ok'], 'Location status after enabling GPS', status_after['rc'], status_after['stdout'], status_after['stderr'])
        parsed=None; raw=''; get_rc=None
        deadline=time.time()+min(wait_seconds, combo_seconds, max(1, gps_time_left()-6))
        poll=0
        while time.time() < deadline and not gps_time_low(5):
            poll += 1
            gr=run(['mmcli','-m',mid,'--location-get'],15)
            raw=(gr['stdout'] or '')+'\n'+(gr['stderr'] or '')
            get_rc=gr['rc']
            parsed=parse_mmcli_location(raw)
            if parsed:
                break
            time.sleep(poll_seconds)
        if parsed:
            disable_notes=disable_modem_gps(mid)
            parsed.update({'ok':True,'source':f'ModemManager modem {mid}','modem_id':mid,'raw':raw[:3000],'gps_was_enabled_for_pull':True,'gps_disable_after_pull':env_bool('TAK_DASH_GPS_DISABLE_AFTER_PULL', True),'poll_count':poll,'wait_seconds':wait_seconds})
            add_attempt(f'ModemManager/mmcli modem {mid} location-get', True, f'GPS fix found after {poll} poll(s). GPS disable attempts: {"; ".join(disable_notes)}', get_rc, raw, '')
            return parsed
        if env_bool('TAK_DASH_GPS_DISABLE_AFTER_NO_FIX', False):
            disable_notes=disable_modem_gps(mid)
            disable_text='GPS disabled after no-fix timeout: '+('; '.join(disable_notes) or 'requested')
        else:
            disable_text='GPS left enabled after no-fix timeout so the receiver can continue acquiring. Set TAK_DASH_GPS_DISABLE_AFTER_NO_FIX=true to disable on timeout.'
            add_attempt(f'ModemManager/mmcli modem {mid} keep-gps-enabled', True, disable_text)
        add_attempt(f'ModemManager/mmcli modem {mid} location-get', False, f'No GPS fix after {poll} poll(s). {disable_text}', get_rc, raw, '')
    return None

def try_gpsd():
    if not shutil.which('gpspipe'):
        add_attempt('gpsd/gpspipe', False, 'gpspipe not installed')
        return None
    r=run(['gpspipe','-w','-n','20'],25)
    for line in (r['stdout'] or '').splitlines():
        try:
            item=json.loads(line)
        except Exception:
            continue
        if item.get('class')=='TPV' and item.get('lat') is not None and item.get('lon') is not None:
            add_attempt('gpsd/gpspipe', True, 'GPS fix found', r['rc'])
            return {'ok':True,'source':'gpsd/gpspipe','latitude':item.get('lat'),'longitude':item.get('lon'),'altitude_m':item.get('altHAE') or item.get('altMSL'),'accuracy_m':item.get('epx') or item.get('epy') or item.get('eph'),'utc_time':item.get('time'),'note':'Pulled GPS coordinates through gpsd. The dashboard did not control modem GPS power for this gpsd source.','raw':line[:3000]}
    add_attempt('gpsd/gpspipe', False, 'No TPV fix returned by gpspipe', r['rc'], r['stdout'], r['stderr'])
    return None

BAUD_CONST={
    4800:termios.B4800, 9600:termios.B9600, 19200:termios.B19200, 38400:termios.B38400,
    57600:termios.B57600, 115200:termios.B115200, 230400:getattr(termios,'B230400',termios.B115200),
    460800:getattr(termios,'B460800',termios.B115200), 921600:getattr(termios,'B921600',termios.B115200)
}

def split_env_list(value):
    return [x.strip() for x in re.split(r'[\s,;:]+', str(value or '')) if x.strip()]

def serial_ports():
    configured=split_env_list(env('TAK_DASH_GPS_SERIAL_PORTS',''))
    ports=[]
    if configured:
        ports.extend(configured)
    else:
        # Most USB LTE modems expose AT/NMEA ports as ttyUSB* or ttyACM*.
        for pat in ('/dev/serial/by-id/*','/dev/ttyUSB*','/dev/ttyACM*'):
            ports.extend(glob.glob(pat))
        # Optional: include Pi UARTs only when explicitly enabled to avoid touching console serial unexpectedly.
        if env_bool('TAK_DASH_GPS_SCAN_PI_UARTS', False):
            for pat in ('/dev/ttyAMA*','/dev/ttyS*'):
                ports.extend(glob.glob(pat))
    out=[]; seen=set()
    for port in ports:
        try:
            real=str(Path(port).resolve())
        except Exception:
            real=port
        key=real
        if key not in seen and os.path.exists(real):
            seen.add(key); out.append(real)
    return out

def serial_bauds():
    raw=split_env_list(env('TAK_DASH_GPS_SERIAL_BAUDS','115200,9600'))
    vals=[]
    for x in raw:
        try:
            b=int(x)
            if b in BAUD_CONST and b not in vals:
                vals.append(b)
        except Exception:
            pass
    return vals or [115200,9600]

def configure_serial(fd, baud):
    b=BAUD_CONST.get(int(baud), termios.B115200)
    attrs=termios.tcgetattr(fd)
    attrs[0]=0
    attrs[1]=0
    attrs[2]=b | termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3]=0
    attrs[4]=b
    attrs[5]=b
    attrs[6][termios.VMIN]=0
    attrs[6][termios.VTIME]=0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)

def serial_read(fd, seconds=1.5):
    chunks=[]; deadline=time.time()+float(seconds)
    while time.time() < deadline and not gps_time_low(5):
        timeout=max(0.05, min(0.25, deadline-time.time()))
        r,_,_=select.select([fd], [], [], timeout)
        if not r:
            continue
        try:
            data=os.read(fd, 4096)
        except BlockingIOError:
            continue
        except Exception:
            break
        if data:
            chunks.append(data)
    return b''.join(chunks).decode('utf-8','replace')

def serial_cmd(fd, cmd, timeout=2.0):
    try:
        os.write(fd, (cmd+'\r').encode('ascii','ignore'))
    except Exception as e:
        return f'WRITE ERROR: {e}'
    return serial_read(fd, timeout)

def gps_command_sets(identity=''):
    """Return GNSS command sets. The wrapper tries a status command first when
    available, treats an already-enabled receiver as a valid selection, then falls
    back to enable commands. Telit/LE910 identity strings are prioritized for the
    user's modem family."""
    ident=str(identity or '').upper()
    sets=[]
    custom_enable=split_env_list(env('TAK_DASH_GPS_SERIAL_ENABLE_CMDS','').replace('|',','))
    custom_poll=split_env_list(env('TAK_DASH_GPS_SERIAL_POLL_CMDS','').replace('|',','))
    custom_disable=split_env_list(env('TAK_DASH_GPS_SERIAL_DISABLE_CMDS','').replace('|',','))
    if custom_enable and custom_poll:
        # Custom commands keep legacy behavior: any custom enable/status command
        # returning OK selects the custom set and then the custom poll commands run.
        sets.append({'name':'Custom','enable':custom_enable,'poll':custom_poll,'disable':custom_disable or []})
    default_sets=[
        {'name':'Quectel QGPS','enable':['AT+QGPS=1'],'poll':['AT+QGPSLOC=2','AT+QGPSGNMEA="GGA"','AT+QGPSGNMEA="RMC"'],'disable':['AT+QGPSEND']},
        {'name':'SIMCom CGPS','enable':['AT+CGPS=1'],'poll':['AT+CGPSINFO'],'disable':['AT+CGPS=0']},
        {'name':'SIMCom CGNS','enable':['AT+CGNSPWR=1'],'poll':['AT+CGNSINF'],'disable':['AT+CGNSPWR=0']},
        {'name':'Telit GPS','status':['AT$GPSP?'],'status_on_regex':r'\$GPSP:\s*1','enable':['AT$GPSP=1'],'poll':['AT$GPSACP'],'disable':['AT$GPSP=0']},
    ]
    if 'TELIT' in ident or 'LE910' in ident:
        default_sets=sorted(default_sets, key=lambda cs: 0 if cs['name']=='Telit GPS' else 1)
    sets.extend(default_sets)
    return sets

def serial_disable(fd, cmds=None, name='selected command set'):
    if not env_bool('TAK_DASH_GPS_DISABLE_AFTER_PULL', True):
        add_attempt('Serial AT disable', False, 'GPS disable after pull is disabled by TAK_DASH_GPS_DISABLE_AFTER_PULL=false')
        return
    cmds=list(cmds or [])
    if not cmds:
        # Fallback only when no command set was selected.
        cmds=['AT+QGPSEND','AT+CGPS=0','AT+CGNSPWR=0','AT$GPSP=0']
    for cmd in cmds:
        resp=serial_cmd(fd, cmd, min(1.2, env_float('TAK_DASH_GPS_SERIAL_CMD_TIMEOUT_SECONDS', 1.0)))
        add_attempt(f'Serial AT {cmd}', ('OK' in resp), f'Attempted to disable modem GNSS using {name}', None, resp, '')

def try_serial_at_and_nmea():
    ports=serial_ports()
    bauds=serial_bauds()
    if not ports:
        add_attempt('Serial AT/NMEA', False, 'No /dev/ttyUSB*, /dev/ttyACM*, or configured serial GPS ports were found. Set TAK_DASH_GPS_SERIAL_PORTS=/dev/ttyUSB2 if needed.')
        return None
    add_attempt('Serial AT/NMEA scan', True, f'Ports: {", ".join(ports)}; baud rates: {", ".join(map(str,bauds))}; total timeout: {GPS_TOTAL_TIMEOUT}s')
    max_ports=max(1, env_int('TAK_DASH_GPS_SERIAL_MAX_PORTS', 8))
    max_bauds=max(1, env_int('TAK_DASH_GPS_SERIAL_MAX_BAUDS', 2))
    if len(ports) > max_ports:
        add_attempt('Serial AT/NMEA scan limit', False, f'Limiting scan to first {max_ports} port(s). Set TAK_DASH_GPS_SERIAL_PORTS=/dev/ttyUSBx to force the correct GPS/AT port.')
        ports=ports[:max_ports]
    if len(bauds) > max_bauds:
        add_attempt('Serial AT/NMEA baud limit', False, f'Limiting scan to first {max_bauds} baud rate(s). Set TAK_DASH_GPS_SERIAL_BAUDS if your modem uses another rate.')
        bauds=bauds[:max_bauds]

    wait_seconds=max(30, int(env('TAK_DASH_GPS_FIX_WAIT_SECONDS','300') or 300))
    wait_seconds=min(wait_seconds, max(8, int(gps_time_left()-8)))
    poll_seconds=max(2, int(env('TAK_DASH_GPS_FIX_POLL_SECONDS','5') or 5))
    cmd_timeout=max(0.3, env_float('TAK_DASH_GPS_SERIAL_CMD_TIMEOUT_SECONDS', 1.0))
    read_seconds=max(0.2, env_float('TAK_DASH_GPS_SERIAL_READ_SECONDS', 0.6))
    combo_seconds=max(30, env_int('TAK_DASH_GPS_SERIAL_COMBO_SECONDS', 300))
    cmdsets=gps_command_sets()

    for port in ports:
        if gps_time_low(10):
            add_attempt('Serial AT/NMEA scan stopped', False, gps_timeout_note())
            break
        for baud in bauds:
            if gps_time_low(10):
                add_attempt('Serial AT/NMEA scan stopped', False, gps_timeout_note())
                break
            fd=None
            selected=None
            try:
                fd=os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
                configure_serial(fd, baud)
                raw0=serial_read(fd, min(1.0, read_seconds))
                n=parse_any_gps(raw0)
                if n:
                    n.update({'ok':True,'source':f'Serial NMEA {port} @ {baud}','port':port,'at_port':port,'baud':baud,'raw':raw0[:3000],'gps_was_enabled_for_pull':False,'gps_disable_after_pull':False})
                    add_attempt(f'Serial NMEA {port} @ {baud}', True, 'GPS fix found from raw NMEA stream before AT enable', None, raw0, '')
                    return n

                at_resp=''
                for _ in range(2):
                    at_resp += serial_cmd(fd, 'AT', cmd_timeout)
                    if re.search(r'\bOK\b', at_resp):
                        break
                if not re.search(r'\bOK\b', at_resp):
                    add_attempt(f'Serial AT {port} @ {baud}', False, 'Port did not respond to AT; raw NMEA also had no fix', None, raw0, at_resp)
                    continue
                identity=''
                for idcmd in ('ATI','AT+CGMI','AT+CGMM'):
                    identity += f'\n{idcmd}:\n' + serial_cmd(fd, idcmd, cmd_timeout)
                add_attempt(f'Serial AT {port} @ {baud}', True, 'Port responded to AT; selecting GNSS command set for this request', None, at_resp, '')
                add_attempt(f'Serial AT identity {port} @ {baud}', bool(identity.strip()), 'Modem identity probe used to prioritize Telit/LE910 GPS commands when detected', None, identity, '')

                # Select exactly one command set for this request. This keeps support broad
                # while avoiding repeated enable/poll/disable commands from unrelated modem brands.
                for cs in gps_command_sets(identity):
                    if gps_time_low(15):
                        add_attempt('Serial AT command-set selection stopped', False, gps_timeout_note())
                        break
                    enable_ok=False
                    already_enabled=False
                    status_checked=False
                    last_enable=''

                    # Some Telit modems return ERROR if AT$GPSP=1 is sent while GPS is already
                    # powered on. Check AT$GPSP? first and accept $GPSP: 1 as enabled.
                    for cmd in cs.get('status',[]):
                        status_checked=True
                        resp=serial_cmd(fd, cmd, cmd_timeout)
                        last_enable += resp + '\n'
                        rx=cs.get('status_on_regex')
                        if rx and re.search(rx, resp, re.I):
                            enable_ok=True
                            already_enabled=True
                            break

                    if not enable_ok:
                        for cmd in cs.get('enable',[]):
                            resp=serial_cmd(fd, cmd, cmd_timeout)
                            last_enable += resp + '\n'
                            if re.search(r'\bOK\b', resp):
                                enable_ok=True
                                break

                    if enable_ok and already_enabled:
                        note='Selected this GNSS command set because GPS is already enabled'
                    elif enable_ok:
                        note='Selected this GNSS command set for the request'
                    elif status_checked:
                        note='Status/enable command(s) did not show enabled GPS or return OK'
                    else:
                        note='Enable command(s) did not return OK'
                    add_attempt(f'Serial AT {port} {cs["name"]} enable/status', enable_ok, note, None, last_enable, '')
                    if enable_ok:
                        selected=cs
                        selected['already_enabled']=already_enabled
                        break

                if not selected:
                    # Some devices may stream NMEA without an AT enable command. Check briefly before moving on.
                    raw_stream=serial_read(fd, min(3.0, max(1.0, gps_time_left()-6)))
                    parsed=parse_any_gps(raw_stream)
                    if parsed:
                        parsed.update({'ok':True,'source':f'Serial NMEA {port} @ {baud}','port':port,'at_port':port,'baud':baud,'raw':raw_stream[:3000],'gps_was_enabled_for_pull':False,'gps_disable_after_pull':False})
                        add_attempt(f'Serial NMEA {port} @ {baud}', True, 'GPS fix found from raw NMEA stream without AT enable', None, raw_stream, '')
                        return parsed
                    add_attempt(f'Serial AT {port} @ {baud}', False, 'No supported GNSS command set returned OK on this AT port')
                    continue

                deadline=time.time()+min(wait_seconds, combo_seconds, max(1, gps_time_left()-8))
                poll=0
                last_poll_resp=''
                fix_result=None
                fix_source_attempt=''
                while time.time() < deadline and not gps_time_low(6):
                    poll += 1
                    raw_stream=serial_read(fd, read_seconds)
                    parsed=parse_any_gps(raw_stream)
                    if parsed:
                        parsed.update({'ok':True,'source':f'Serial AT/NMEA {port} @ {baud} ({selected["name"]})','port':port,'at_port':port,'baud':baud,'raw':raw_stream[:3000],'gps_was_enabled_for_pull':True,'gps_disable_after_pull':env_bool('TAK_DASH_GPS_DISABLE_AFTER_PULL', True),'poll_count':poll,'wait_seconds':wait_seconds,'command_set':selected['name']})
                        add_attempt(f'Serial AT/NMEA {port} raw poll', True, f'GPS fix found from serial stream after {poll} poll(s)', None, raw_stream, '')
                        fix_result=parsed
                        fix_source_attempt='raw serial stream'
                        break
                    for cmd in selected.get('poll',[]):
                        resp=serial_cmd(fd, cmd, cmd_timeout)
                        last_poll_resp=resp
                        parsed=parse_any_gps(resp)
                        if parsed:
                            parsed.update({'ok':True,'source':f'Serial AT {port} @ {baud} ({selected["name"]})','port':port,'at_port':port,'baud':baud,'raw':resp[:3000],'gps_was_enabled_for_pull':True,'gps_disable_after_pull':env_bool('TAK_DASH_GPS_DISABLE_AFTER_PULL', True),'poll_count':poll,'wait_seconds':wait_seconds,'poll_command':cmd,'command_set':selected['name']})
                            add_attempt(f'Serial AT {port} {cmd}', True, f'GPS fix found after {poll} poll(s) using {selected["name"]}', None, resp, '')
                            fix_result=parsed
                            fix_source_attempt=cmd
                            break
                    if fix_result:
                        break
                    time.sleep(poll_seconds)

                if fix_result:
                    serial_disable(fd, selected.get('disable',[]), selected.get('name','selected command set'))
                    return fix_result

                # Important: report the no-fix condition before disabling, so the UI's attempt order
                # reflects enable -> poll/wait -> no fix -> disable.
                nofix_note=f'No GPS fix after waiting {int(min(wait_seconds, combo_seconds))} seconds with selected command set. Last poll response indicates the modem was reachable but did not have a usable GNSS fix.'
                if '$GPSACP:' in (last_poll_resp or '') and re.search(r'\$GPSACP:\s*,', last_poll_resp or ''):
                    nofix_note='Telit GPS receiver is on, but AT$GPSACP returned no coordinates before timeout. This usually means no satellite fix yet, weak/missing GNSS antenna or sky view, or cold-start acquisition needs more time.'
                add_attempt(f'Serial AT/NMEA {port} @ {baud} ({selected["name"]})', False, nofix_note, None, last_poll_resp, '')
                if env_bool('TAK_DASH_GPS_DISABLE_AFTER_NO_FIX', False):
                    serial_disable(fd, selected.get('disable',[]), selected.get('name','selected command set'))
                else:
                    add_attempt('Serial AT keep-gps-enabled after no-fix', True, 'GPS left enabled after no-fix timeout so the receiver can continue acquiring. Set TAK_DASH_GPS_DISABLE_AFTER_NO_FIX=true to disable on timeout.')
                # Once a real command set enabled successfully, do not waste time retrying unrelated baud rates/ports.
                # A selected command set plus no coordinates is a no-fix condition, not a scan failure.
                return None
            except Exception as e:
                add_attempt(f'Serial AT/NMEA {port} @ {baud}', False, str(e))
            finally:
                if fd is not None:
                    try: os.close(fd)
                    except Exception: pass
    return None

# Try managed sources first, then direct serial/AT, then gpsd. Serial/AT works for many unmanaged USB LTE modems.
result=try_modemmanager() or try_serial_at_and_nmea() or try_gpsd()
if result:
    result.setdefault('ok', True)
    result.setdefault('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    result['attempts']=attempts
    print(json.dumps(result))
    sys.exit(0)
print(json.dumps({'ok':False,'status':'No GPS fix','source':'Server GPS','note':'No GPS coordinates were returned. The dashboard tried ModemManager, direct serial AT/NMEA probing, and gpsd. For Telit/LE910 modems, the wrapper now checks AT$GPSP? first and treats $GPSP: 1 as GPS already enabled before polling AT$GPSACP. If AT$GPSACP returns empty fields, the GPS receiver is on but does not yet have a satellite fix. Check the GNSS antenna/sky view and allow extra cold-start acquisition time. After a no-fix timeout, GPS is left enabled by default so the modem can keep acquiring for the next pull; set TAK_DASH_GPS_DISABLE_AFTER_NO_FIX=true to disable on timeout.','attempts':attempts,'elapsed_seconds':int(gps_elapsed()),'total_timeout_seconds':GPS_TOTAL_TIMEOUT,'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}))
sys.exit(1)
PYGPS
fi
if [[ "${1:-}" == "modem-gps-push" ]]; then
  exec /usr/bin/python3 - <<'PYPUSHGPS'
import datetime as _dt
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import xml.sax.saxutils as xml_escape

WRAPPER='/usr/local/sbin/tak-server-dash-action'

def run(cmd, timeout=120):
    try:
        p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {'rc':p.returncode,'stdout':p.stdout or '', 'stderr':p.stderr or '', 'ok':p.returncode==0}
    except Exception as e:
        return {'rc':127,'stdout':'','stderr':str(e),'ok':False}

def env(name, default=''):
    return os.environ.get(name, default)

def env_bool(name, default=False):
    val=str(os.environ.get(name, 'true' if default else 'false')).strip().lower()
    return val in ('1','true','yes','on','tls','ssl')

def iso_z(dt):
    return dt.replace(microsecond=0).isoformat().replace('+00:00','Z')

def fnum(value, default=None):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default

def default_uid():
    host=socket.gethostname().split('.')[0].strip() or 'tak-server'
    host=re.sub(r'[^A-Za-z0-9_.@-]+','-',host).strip('-') or 'tak-server'
    return host + '-dash'

def build_cot(gps):
    now=_dt.datetime.now(_dt.timezone.utc)
    stale_minutes=int(env('TAK_DASH_GPS_COT_STALE_MINUTES','5') or 5)
    stale=now+_dt.timedelta(minutes=max(1, stale_minutes))
    lat=fnum(gps.get('latitude'))
    lon=fnum(gps.get('longitude'))
    if lat is None or lon is None:
        raise ValueError('GPS data does not include latitude/longitude')
    hae=fnum(gps.get('altitude_m'), 9999999.0)
    acc=fnum(gps.get('accuracy_m'), 9999999.0)
    uid=env('TAK_DASH_GPS_COT_UID','').strip() or default_uid()
    callsign=env('TAK_DASH_GPS_COT_CALLSIGN','TAK-SERVER-GPS').strip() or 'TAK-SERVER-GPS'
    cot_type=env('TAK_DASH_GPS_COT_TYPE','a-f-G-U-C').strip() or 'a-f-G-U-C'
    source=str(gps.get('source') or 'Server GPS')
    note=str(gps.get('note') or '')
    remarks='Manual dashboard GPS push. Source: ' + source + ('. ' + note if note else '') + f' Marker expires after {max(1, stale_minutes)} minutes.'
    uid_e=xml_escape.escape(uid)
    callsign_e=xml_escape.escape(callsign)
    type_e=xml_escape.escape(cot_type)
    remarks_e=xml_escape.escape(remarks)
    cot='<?xml version="1.0" encoding="UTF-8"?>\n<event version="2.0" uid="{}" type="{}" how="m-g" time="{}" start="{}" stale="{}"><point lat="{:.7f}" lon="{:.7f}" hae="{:.1f}" ce="{:.1f}" le="{:.1f}"/><detail><contact callsign="{}"/><remarks>{}</remarks></detail></event>\n'.format(uid_e, type_e, iso_z(now), iso_z(now), iso_z(stale), lat, lon, hae, acc, acc, callsign_e, remarks_e)
    return cot, {'uid':uid,'callsign':callsign,'stale_minutes':max(1, stale_minutes),'stale_utc':iso_z(stale)}

def send_cot(cot):
    host=env('TAK_DASH_GPS_COT_HOST','127.0.0.1') or '127.0.0.1'
    port=int(env('TAK_DASH_GPS_COT_PORT','8088') or 8088)
    use_tls=env_bool('TAK_DASH_GPS_COT_TLS', False)
    timeout=int(env('TAK_DASH_GPS_COT_TIMEOUT','10') or 10)
    with socket.create_connection((host, port), timeout=timeout) as sock:
        if use_tls:
            ca=env('TAK_DASH_GPS_COT_CA_FILE','').strip()
            cert=env('TAK_DASH_GPS_COT_CLIENT_CERT','').strip()
            key=env('TAK_DASH_GPS_COT_CLIENT_KEY','').strip()
            verify=env_bool('TAK_DASH_GPS_COT_VERIFY_PEER', False)
            if verify:
                ctx=ssl.create_default_context(cafile=ca or None)
            else:
                ctx=ssl._create_unverified_context()
            if cert and key:
                ctx.load_cert_chain(certfile=cert, keyfile=key)
            with ctx.wrap_socket(sock, server_hostname=host if verify else None) as ssock:
                ssock.sendall(cot.encode('utf-8'))
        else:
            sock.sendall(cot.encode('utf-8'))
    return {'host':host,'port':port,'tls':use_tls}

gps_run=run([WRAPPER,'modem-gps'], 140)
try:
    gps=json.loads(gps_run.get('stdout') or '{}')
except Exception:
    gps={'ok':False,'note':'GPS pull did not return JSON','stdout':gps_run.get('stdout',''),'stderr':gps_run.get('stderr','')}

if not gps.get('ok') or gps.get('latitude') is None or gps.get('longitude') is None:
    print(json.dumps({'ok':False,'status':'GPS push failed','stage':'gps-pull','note':'No usable GPS fix was available, so no CoT marker was pushed. Modem GPS was disabled again after the attempt.','gps':gps,'rc':gps_run.get('rc'),'stderr':gps_run.get('stderr','')}))
    sys.exit(1)

try:
    cot,meta=build_cot(gps)
    dest=send_cot(cot)
    print(json.dumps({'ok':True,'status':'GPS pushed to OpenTAKServer','source':gps.get('source'),'latitude':gps.get('latitude'),'longitude':gps.get('longitude'),'altitude_m':gps.get('altitude_m'),'accuracy_m':gps.get('accuracy_m'),'utc_time':gps.get('utc_time') or gps.get('timestamp'),'note':f'Manual Server GPS CoT marker pushed to local OpenTAKServer CoT ingest. Marker expires after {meta["stale_minutes"]} minutes. Modem GPS was disabled after the fix.','destination':dest,'callsign':meta['callsign'],'uid':meta['uid'],'stale_minutes':meta['stale_minutes'],'stale_utc':meta['stale_utc']}))
    sys.exit(0)
except Exception as e:
    print(json.dumps({'ok':False,'status':'GPS push failed','stage':'cot-send','note':str(e),'source':gps.get('source'),'latitude':gps.get('latitude'),'longitude':gps.get('longitude'),'altitude_m':gps.get('altitude_m'),'accuracy_m':gps.get('accuracy_m'),'utc_time':gps.get('utc_time') or gps.get('timestamp'),'destination':{'host':env('TAK_DASH_GPS_COT_HOST','127.0.0.1'),'port':env('TAK_DASH_GPS_COT_PORT','8088'),'tls':env('TAK_DASH_GPS_COT_TLS','false')}}))
    sys.exit(1)
PYPUSHGPS
fi
if [[ "${1:-}" == "diagnostics" ]]; then
  mkdir -p "$DIAG_DIR"; stamp="$(date -u +%Y%m%dT%H%M%SZ)"; tmpdir="$(mktemp -d)"; outfile="$DIAG_DIR/tak-dashboard-diagnostics-$stamp.tar.gz"; report="$tmpdir/report.txt"
  {
    echo "Mobile TAK Server Diagnostics"; echo "Generated UTC: $stamp"; echo "Hostname: $(hostname 2>/dev/null || true)"; echo
    run_and_capture "uname" uname -a
    run_and_capture "uptime" uptime
    run_and_capture "date" date -Is
    run_and_capture "ip addr" ip addr
    run_and_capture "ip route" ip route
    run_and_capture "ip route get 8.8.8.8" ip route get 8.8.8.8
    run_and_capture "resolv.conf" cat /etc/resolv.conf
    run_and_capture "NetworkManager devices" nmcli device status
    run_and_capture "NetworkManager active connections" nmcli connection show --active
    run_and_capture "ZeroTier status" zerotier-cli status
    run_and_capture "ZeroTier listnetworks" zerotier-cli listnetworks
    run_and_capture "df -h" df -h
    run_and_capture "free -h" free -h
    run_and_capture "vcgencmd get_throttled" vcgencmd get_throttled
    run_and_capture "CPU temp" sh -c 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || true'
    run_and_capture "I2C detect bus 1" i2cdetect -y 1
    run_and_capture "Power supplies" sh -c 'for d in /sys/class/power_supply/*; do echo "--- $d"; grep -H . "$d"/* 2>/dev/null || true; done'
    run_and_capture "QMI devices" sh -c 'ls -l /dev/cdc-wdm* 2>/dev/null || true'
    run_and_capture "qmicli signal strength" sh -c 'for d in /dev/cdc-wdm*; do echo "--- $d"; qmicli -d "$d" --nas-get-signal-strength 2>&1 || true; done'
    run_and_capture "qmicli system info" sh -c 'for d in /dev/cdc-wdm*; do echo "--- $d"; qmicli -d "$d" --nas-get-system-info 2>&1 || true; done'
    for svc in $ALLOWED_SERVICES tak-dashboard zerotier-one NetworkManager; do
      run_and_capture "systemctl status $svc" systemctl status "$svc" --no-pager
      run_and_capture "journalctl $svc last 120 lines" journalctl -u "$svc" -n 120 --no-pager
    done
  } > "$report" 2>&1
  tar -czf "$outfile" -C "$tmpdir" report.txt
  chown takserverdash:takserverdash "$outfile" 2>/dev/null || true
  chmod 0640 "$outfile" 2>/dev/null || true
  rm -rf "$tmpdir"
  echo "$outfile"
  exit 0
fi
if [[ "${1:-}" == "auth-user" ]]; then
  username="${2:-}"
  [[ "$username" =~ ^[A-Za-z_][A-Za-z0-9_.-]{0,63}$ ]] || { echo '{"ok":false,"error":"Invalid username"}'; exit 2; }
  user_line="$(getent passwd "$username" || true)"
  [[ -n "$user_line" ]] || { echo '{"ok":false,"error":"Server account was not found"}'; exit 1; }
  # Read password from stdin so it never appears in process arguments.
  password="$(cat)"
  if [[ -z "$password" ]]; then echo '{"ok":false,"error":"Password was empty"}'; exit 1; fi
  pam_services="$(grep -E '^TAK_DASH_PAM_SERVICE=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  pam_services="${pam_services:-tak-server-dash,sshd,login}"
  export TAK_DASH_AUTH_USERNAME="$username"
  export TAK_DASH_AUTH_PASSWORD="$password"
  export TAK_DASH_PAM_SERVICE="$pam_services"
  exec /usr/bin/python3 - <<'PYAUTH'
import json, os, pwd, re, sys
username = os.environ.get('TAK_DASH_AUTH_USERNAME', '')
password = os.environ.get('TAK_DASH_AUTH_PASSWORD', '')
raw_services = os.environ.get('TAK_DASH_PAM_SERVICE', 'tak-server-dash,sshd,login')
services = []
for item in re.split(r'[,\s]+', raw_services or ''):
    item = item.strip()
    if item and re.match(r'^[A-Za-z0-9_.@-]{1,80}$', item) and item not in services:
        services.append(item)
services = services or ['tak-server-dash', 'sshd', 'login']
try:
    pw = pwd.getpwnam(username)
except Exception:
    print(json.dumps({'ok': False, 'error': 'Server account was not found'})); sys.exit(1)
last_error = ''
module_found = False
try:
    import pam as pam_mod
    module_found = True
    for service in services:
        try:
            p = pam_mod.pam()
            if bool(p.authenticate(username, password, service=service)):
                print(json.dumps({'ok': True, 'home': pw.pw_dir, 'service': service})); sys.exit(0)
            last_error = getattr(p, 'reason', '') or f'{service} rejected login'
        except Exception as e:
            last_error = f'{service}: {e}'
except Exception as e:
    last_error = f'import pam failed: {e}'
try:
    import PAM
    module_found = True
    def conv_factory(secret):
        def conv(auth, query_list, user_data):
            responses = []
            for item in query_list:
                query_type = item[1] if len(item) > 1 else 0
                if query_type in (PAM.PAM_PROMPT_ECHO_ON, PAM.PAM_PROMPT_ECHO_OFF):
                    responses.append((secret, 0))
                else:
                    responses.append(('', 0))
            return responses
        return conv
    for service in services:
        try:
            auth = PAM.pam()
            auth.start(service)
            auth.set_item(PAM.PAM_USER, username)
            auth.set_item(PAM.PAM_CONV, conv_factory(password))
            auth.authenticate()
            try:
                auth.acct_mgmt()
            except Exception:
                pass
            print(json.dumps({'ok': True, 'home': pw.pw_dir, 'service': service})); sys.exit(0)
        except Exception as e:
            last_error = f'{service}: {e}'
except Exception as e:
    last_error = f'import PAM failed: {e}'
if not module_found:
    print(json.dumps({'ok': False, 'error': 'No usable Python PAM module found. Install python3-pam.'})); sys.exit(1)
print(json.dumps({'ok': False, 'error': 'PAM rejected login', 'detail': last_error})); sys.exit(1)
PYAUTH
fi
if [[ "${1:-}" == "browse-dirs" ]]; then
  username="${2:-}"
  path_spec="${3:-~}"
  export TAK_DASH_BROWSE_USERNAME="$username"
  export TAK_DASH_BROWSE_PATH="$path_spec"
  exec /usr/bin/python3 - <<'PYBROWSE'
import json, os, pwd, re, sys
from pathlib import Path

username = os.environ.get('TAK_DASH_BROWSE_USERNAME','')
path_spec = os.environ.get('TAK_DASH_BROWSE_PATH','~') or '~'

def fail(msg, rc=2):
    print(json.dumps({'ok': False, 'error': msg}))
    sys.exit(rc)

if not re.match(r'^[A-Za-z_][A-Za-z0-9_.-]{0,63}$', username or ''):
    fail('Invalid username')
if len(path_spec) > 240 or re.search(r'[\x00\r\n`$;&|<>]', path_spec):
    fail('Invalid browse path')
try:
    pw = pwd.getpwnam(username)
except Exception:
    fail('User not found')
home = Path(pw.pw_dir).resolve(strict=False)
uid, gid = pw.pw_uid, pw.pw_gid

def path_from_spec(spec):
    spec = (spec or '~').strip() or '~'
    if spec in ('~', '~/'):
        return home
    if spec.startswith('~/'):
        return home / spec[2:]
    if spec.startswith('/'):
        return Path(spec)
    return home / spec

def display_for(path):
    try:
        rp = Path(path).resolve(strict=False)
    except Exception:
        rp = Path(path)
    try:
        rel = rp.relative_to(home)
        if str(rel) == '.':
            return '~'
        return '~/' + str(rel)
    except Exception:
        return str(rp)

try:
    target = path_from_spec(path_spec).resolve(strict=False)
except Exception:
    fail('Invalid browse path')
if not target.exists() or not target.is_dir():
    fail('Folder does not exist')

entries = []
orig_euid, orig_egid = os.geteuid(), os.getegid()
try:
    try:
        os.setgroups([gid])
    except Exception:
        pass
    os.setegid(gid)
    os.seteuid(uid)
    try:
        names = list(os.scandir(str(target)))
    except PermissionError:
        fail('Authenticated user cannot read that folder', 1)
    for ent in names:
        try:
            if not ent.is_dir(follow_symlinks=True):
                continue
            if ent.name in ('.','..'):
                continue
            # Keep hidden folders browseable when explicitly needed, but sort them after normal folders.
            ep = Path(ent.path).resolve(strict=False)
            entries.append({'name': ent.name, 'path': str(ep), 'display_path': display_for(ep), 'hidden': ent.name.startswith('.')})
        except Exception:
            continue
finally:
    try:
        os.seteuid(orig_euid)
        os.setegid(orig_egid)
    except Exception:
        pass

entries.sort(key=lambda x: (bool(x.get('hidden')), x.get('name','').lower()))
parent = None
try:
    if target != target.parent:
        parent = display_for(target.parent)
except Exception:
    parent = None
print(json.dumps({'ok': True, 'path': str(target), 'display_path': display_for(target), 'parent_display': parent, 'entries': entries[:500]}))
PYBROWSE
fi
if [[ "${1:-}" == "upload-file" ]]; then
  username="${2:-}"
  dest_spec="${3:-}"
  staging_name="${4:-}"
  original_name="${5:-}"
  export TAK_DASH_UPLOAD_USERNAME="$username"
  export TAK_DASH_UPLOAD_DEST_SPEC="$dest_spec"
  export TAK_DASH_UPLOAD_STAGING_NAME="$staging_name"
  export TAK_DASH_UPLOAD_ORIGINAL_NAME="$original_name"
  export TAK_DASH_DATA_DIR="$DATA_DIR"
  exec /usr/bin/python3 - <<'PYUPLOAD'
import json, os, pwd, re, shutil, sys
from pathlib import Path

username = os.environ.get('TAK_DASH_UPLOAD_USERNAME','')
dest_spec = os.environ.get('TAK_DASH_UPLOAD_DEST_SPEC','')
staging_name = os.environ.get('TAK_DASH_UPLOAD_STAGING_NAME','')
original_name = os.environ.get('TAK_DASH_UPLOAD_ORIGINAL_NAME','')
data_dir = Path(os.environ.get('TAK_DASH_DATA_DIR','/var/lib/tak-server-dash'))

def fail(msg, rc=2):
    print(msg, file=sys.stderr)
    sys.exit(rc)

if not re.match(r'^[A-Za-z_][A-Za-z0-9_.-]{0,63}$', username or ''):
    fail('Invalid username')
if not re.match(r'^[A-Za-z0-9_.()@#,+-]{1,260}$', staging_name or ''):
    fail('Invalid staging filename')
if not re.match(r'^[A-Za-z0-9_.()@#,+-]{1,180}$', original_name or ''):
    fail('Invalid upload filename')
if not dest_spec or len(dest_spec) > 240 or re.search(r'[\x00\r\n`$;&|<>]', dest_spec):
    fail('Invalid destination path')
try:
    pw = pwd.getpwnam(username)
except Exception:
    fail('User not found')
home = Path(pw.pw_dir).resolve()
uid = pw.pw_uid
gid = pw.pw_gid

if dest_spec == 'desktop':
    target = home / 'Desktop'
elif dest_spec == 'downloads':
    target = home / 'Downloads'
elif dest_spec == 'home':
    target = home
elif dest_spec in ('~','~/'):
    target = home
elif dest_spec.startswith('~/'):
    target = home / dest_spec[2:]
elif dest_spec.startswith('/'):
    target = Path(dest_spec)
else:
    target = home / dest_spec

try:
    target_real = target.resolve(strict=False)
except Exception:
    fail('Invalid destination path')

# Never allow a destination path to resolve through parent traversal above root logic unexpectedly.
# Paths inside the authenticated user's home can be created automatically.
inside_home = False
try:
    target_real.relative_to(home)
    inside_home = True
except Exception:
    inside_home = False

if inside_home:
    target_real.mkdir(parents=True, exist_ok=True)
    try:
        os.chown(target_real, uid, gid)
    except Exception:
        pass
else:
    # For outside-home destinations, require the directory to already exist and
    # be writable/executable by the authenticated user. This avoids root-backed
    # arbitrary writes while still supporting environments with shared upload dirs
    # or mounted media.
    if not target_real.exists() or not target_real.is_dir():
        fail('Outside-home destination must already exist')
    original_euid = os.geteuid()
    original_egid = os.getegid()
    try:
        os.setegid(gid)
        os.seteuid(uid)
        allowed = os.access(str(target_real), os.W_OK | os.X_OK, effective_ids=True)
    finally:
        os.seteuid(original_euid)
        os.setegid(original_egid)
    if not allowed:
        fail('Authenticated user cannot write to that destination')

staging_dir = (data_dir / 'upload_staging').resolve(strict=False)
src = (staging_dir / staging_name).resolve(strict=False)
try:
    src.relative_to(staging_dir)
except Exception:
    fail('Invalid staging path')
if not src.exists() or not src.is_file():
    fail('Staged upload not found')

base = Path(original_name).name
if not base:
    base = 'upload.bin'
name = base
stem = Path(base).stem if Path(base).suffix else base
suffix = Path(base).suffix
final = target_real / name
n = 1
while final.exists():
    final = target_real / f"{stem}-{n}{suffix}"
    n += 1
try:
    shutil.copyfile(src, final)
    os.chown(final, uid, gid)
    os.chmod(final, 0o644)
    src.unlink(missing_ok=True)
except Exception as e:
    fail(f'Failed to place uploaded file: {e}', 1)
print(str(final))
PYUPLOAD
fi
if [[ "${1:-}" == "cert-detect" ]]; then
  python3 - <<'PYCERTDETECT'
import json, socket, subprocess
ips=[]
try:
    out=subprocess.check_output(['ip','-o','addr','show','scope','global'], text=True, stderr=subprocess.DEVNULL)
    for line in out.splitlines():
        parts=line.split()
        if len(parts) >= 4:
            ip=parts[3].split('/')[0]
            if ip and ip not in ips:
                ips.append(ip)
except Exception:
    pass
hostnames=[]
for cmd in (['hostname'], ['hostname','-f']):
    try:
        h=subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if h and h not in hostnames:
            hostnames.append(h)
    except Exception:
        pass
for h in ['tak-server-dash.local']:
    if h not in hostnames:
        hostnames.append(h)
print(json.dumps({'ips': ips, 'hostnames': hostnames}))
PYCERTDETECT
  exit 0
fi
if [[ "${1:-}" == "cert-setup" ]]; then
  extra_sans="${2:-}"
  exclude_sans="${3:-}"
  CERT_DIR="/etc/tak-server-dash/certs"
  CA_DIR="$CERT_DIR/ca"
  CA_KEY="$CA_DIR/takdash-local-ca.key"
  CA_CRT="$CA_DIR/takdash-local-ca.crt"
  SERVER_KEY="$CERT_DIR/tak-server-dash.key"
  SERVER_CSR="$CERT_DIR/tak-server-dash.csr"
  SERVER_CRT="$CERT_DIR/tak-server-dash.crt"
  CNF="$(mktemp)"
  command -v openssl >/dev/null 2>&1 || { echo "openssl not found" >&2; exit 127; }
  mkdir -p "$CA_DIR" "$CERT_DIR"
  if [[ ! -f "$CA_KEY" || ! -f "$CA_CRT" ]]; then
    echo "Creating TAK Dashboard Local CA..."
    openssl genrsa -out "$CA_KEY" 4096 >/dev/null 2>&1
    openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 3650 -out "$CA_CRT" -subj "/CN=TAK Dashboard Local CA" \
      -addext "basicConstraints=critical,CA:TRUE" \
      -addext "keyUsage=critical,keyCertSign,cRLSign" \
      -addext "subjectKeyIdentifier=hash" >/dev/null 2>&1
  fi
  if [[ ! -f "$SERVER_KEY" ]]; then
    echo "Creating dashboard server key..."
    openssl genrsa -out "$SERVER_KEY" 2048 >/dev/null 2>&1
  fi
  hostname_short="$(hostname 2>/dev/null || echo tak-server-dash)"
  hostname_fqdn="$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo tak-server-dash)"
  declare -a dns_names ip_names
  is_ip() { python3 -c 'import ipaddress,sys; ipaddress.ip_address(sys.argv[1])' "$1" >/dev/null 2>&1; }
  add_dns() { local v="$1"; [[ -n "$v" ]] || return 0; [[ "$v" =~ ^[A-Za-z0-9_.-]{1,253}$ ]] || return 0; for x in "${dns_names[@]:-}"; do [[ "$x" == "$v" ]] && return 0; done; dns_names+=("$v"); }
  add_ip() { local v="$1"; [[ -n "$v" ]] || return 0; is_ip "$v" || return 0; for x in "${ip_names[@]:-}"; do [[ "$x" == "$v" ]] && return 0; done; ip_names+=("$v"); }
  remove_dns() { local v="$1"; local out=(); for x in "${dns_names[@]:-}"; do [[ "$x" == "$v" ]] || out+=("$x"); done; dns_names=("${out[@]:-}"); }
  remove_ip() { local v="$1"; local out=(); for x in "${ip_names[@]:-}"; do [[ "$x" == "$v" ]] || out+=("$x"); done; ip_names=("${out[@]:-}"); }
  add_dns "$hostname_short"
  add_dns "$hostname_fqdn"
  add_dns "tak-server-dash.local"
  while read -r ip; do add_ip "$ip"; done < <(ip -o addr show scope global 2>/dev/null | awk '{split($4,a,"/"); print a[1]}')
  # Extra SANs can be supplied from the dashboard popup, one per line or comma-separated.
  while IFS= read -r item; do
    item="$(echo "$item" | xargs 2>/dev/null || true)"
    [[ -n "$item" ]] || continue
    if is_ip "$item"; then add_ip "$item"; else add_dns "$item"; fi
  done < <(printf '%s\n' "$extra_sans" | tr ',' '\n')
  # Excluded SANs can be supplied from the dashboard popup, one per line or comma-separated.
  while IFS= read -r item; do
    item="$(echo "$item" | xargs 2>/dev/null || true)"
    [[ -n "$item" ]] || continue
    if is_ip "$item"; then remove_ip "$item"; else remove_dns "$item"; fi
  done < <(printf '%s\n' "$exclude_sans" | tr ',' '\n')
  {
    echo "[req]"
    echo "distinguished_name = req_distinguished_name"
    echo "req_extensions = v3_req"
    echo "prompt = no"
    echo
    echo "[req_distinguished_name]"
    echo "CN = tak-server-dash"
    echo
    echo "[v3_req]"
    echo "basicConstraints = critical, CA:FALSE"
    echo "keyUsage = critical, digitalSignature, keyEncipherment"
    echo "extendedKeyUsage = serverAuth"
    echo "subjectAltName = @alt_names"
    echo
    echo "[alt_names]"
    n=1
    for dns in "${dns_names[@]:-}"; do echo "DNS.$n = $dns"; n=$((n+1)); done
    n=1
    for ip in "${ip_names[@]:-}"; do echo "IP.$n = $ip"; n=$((n+1)); done
  } > "$CNF"
  openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" -config "$CNF" >/dev/null 2>&1
  openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CRT" -CAkey "$CA_KEY" -CAcreateserial -out "$SERVER_CRT" -days 397 -sha256 -extensions v3_req -extfile "$CNF" >/dev/null 2>&1
  chmod 0600 "$CA_KEY" "$SERVER_KEY" 2>/dev/null || true
  chmod 0644 "$CA_CRT" "$SERVER_CRT" 2>/dev/null || true

  # The CA certificate remains in the protected dashboard cert directory.
  # Client devices get this CA through the dashboard Download CA Certificate button.
  # Do not copy it into user Downloads folders.

  rm -f "$CNF" "$SERVER_CSR"
  if command -v nginx >/dev/null 2>&1; then
    if nginx -t >/tmp/tak-server-dash-nginx-cert-test.log 2>&1; then
      systemctl reload nginx || systemctl restart nginx || true
      echo "Nginx reloaded."
    else
      echo "WARNING: nginx -t failed after certificate generation:" >&2
      cat /tmp/tak-server-dash-nginx-cert-test.log >&2 || true
    fi
  fi
  echo ""
  echo "Dashboard server certificate regenerated."
  echo "Included DNS names: ${dns_names[*]:-none}"
  echo "Included IP addresses: ${ip_names[*]:-none}"
  echo "Nginx HTTPS certificate installed: $SERVER_CRT"
  echo "Nginx HTTPS private key installed: $SERVER_KEY"
  echo "Client CA certificate source: $CA_CRT"
  echo "Client CA dashboard download URL: /ca-cert.crt"
  echo "Client CA is available from the dashboard Download CA Certificate button."
  exit 0
fi
if [[ "${1:-}" == "system" ]]; then
  action="${2:-}"
  case "$action" in
    reboot)
      if command -v systemd-run >/dev/null 2>&1; then systemd-run --on-active=5 --unit=tak-dashboard-reboot /usr/bin/systemctl reboot; else /usr/sbin/shutdown -r +0 "TAK dashboard requested reboot"; fi
      echo "TAK server reboot scheduled."; exit 0 ;;
    shutdown)
      if command -v systemd-run >/dev/null 2>&1; then systemd-run --on-active=5 --unit=tak-dashboard-poweroff /usr/bin/systemctl poweroff; else /usr/sbin/shutdown -h +0 "TAK dashboard requested shutdown"; fi
      echo "TAK server shutdown scheduled."; exit 0 ;;
    lock-screen)
      locked=0
      attempted=0
      echo "TAK Dashboard screen lock requested."
      echo "This action targets the local monitor/desktop session on the TAK server."
      echo ""

      command_exists() { command -v "$1" >/dev/null 2>&1; }
      lockscreen_image="${TAK_DASH_LOCKSCREEN_IMAGE:-/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-3840x2160.png}"
      if [[ -f "$lockscreen_image" ]]; then
        echo "Themed lock-screen image: $lockscreen_image"
      else
        echo "Themed lock-screen image not found: $lockscreen_image"
        echo "The lock action will fall back to the desktop default lock screen."
      fi


      try_loginctl_session() {
        local sid="$1"
        [[ -n "$sid" ]] || return 1
        attempted=$((attempted + 1))
        echo "Trying loginctl lock-session $sid..."
        if loginctl lock-session "$sid" >/tmp/tak-dash-lock.log 2>&1; then
          locked=1
          echo "  OK: loginctl accepted lock request for session $sid."
          return 0
        fi
        echo "  FAILED: $(tr '\n' ' ' </tmp/tak-dash-lock.log 2>/dev/null || true)"
        return 1
      }

      run_user_env() {
        local user="$1" uid="$2" display="$3" wayland="$4" home_dir="$5"
        shift 5
        attempted=$((attempted + 1))
        local label="$*"
        echo "Trying as $user: $label"
        if runuser -u "$user" -- env \
          XDG_RUNTIME_DIR="/run/user/$uid" \
          DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" \
          DISPLAY="$display" \
          WAYLAND_DISPLAY="$wayland" \
          XAUTHORITY="$home_dir/.Xauthority" \
          "$@" >/tmp/tak-dash-lock.log 2>&1; then
          locked=1
          echo "  OK: $label"
          return 0
        fi
        echo "  FAILED: $(tr '\n' ' ' </tmp/tak-dash-lock.log 2>/dev/null || true)"
        return 1
      }

      run_user_shell_env() {
        local user="$1" uid="$2" display="$3" wayland="$4" home_dir="$5" shell_cmd="$6"
        attempted=$((attempted + 1))
        echo "Trying as $user: $shell_cmd"
        if runuser -u "$user" -- env \
          XDG_RUNTIME_DIR="/run/user/$uid" \
          DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" \
          DISPLAY="$display" \
          WAYLAND_DISPLAY="$wayland" \
          XAUTHORITY="$home_dir/.Xauthority" \
          sh -lc "$shell_cmd" >/tmp/tak-dash-lock.log 2>&1; then
          locked=1
          echo "  OK: $shell_cmd"
          return 0
        fi
        echo "  FAILED: $(tr '\n' ' ' </tmp/tak-dash-lock.log 2>/dev/null || true)"
        return 1
      }

      sessions=""
      if command_exists loginctl; then
        sessions="$(loginctl list-sessions --no-legend 2>/dev/null || true)"
        echo "Detected login sessions:"
        if [[ -n "$sessions" ]]; then echo "$sessions"; else echo "  none"; fi
        echo ""

        while read -r sid uid user seat tty rest; do
          [[ -n "${sid:-}" ]] || continue
          [[ -n "${uid:-}" ]] || continue
          [[ -n "${user:-}" ]] || continue
          session_class="$(loginctl show-session "$sid" -p Class --value 2>/dev/null || true)"
          session_state="$(loginctl show-session "$sid" -p State --value 2>/dev/null || true)"
          session_type="$(loginctl show-session "$sid" -p Type --value 2>/dev/null || true)"
          session_remote="$(loginctl show-session "$sid" -p Remote --value 2>/dev/null || true)"
          echo "Session $sid: user=$user uid=$uid class=${session_class:-unknown} type=${session_type:-unknown} state=${session_state:-unknown} remote=${session_remote:-unknown}"
          # Lock only local user/greeter sessions. Skip SSH/remote sessions where possible.
          if [[ "$session_remote" == "yes" ]]; then
            echo "  Skipping remote session $sid."
            continue
          fi
          if [[ -f "$lockscreen_image" ]]; then
            echo "  Deferring loginctl fallback until after themed lock-screen attempts."
          else
            try_loginctl_session "$sid" || true
          fi
        done <<< "$sessions"
      else
        echo "loginctl not found."
      fi

      echo ""
      echo "Trying desktop-specific lock commands..."

      # Build a unique list of candidate local graphical users from loginctl and common Pi desktop fallback.
      candidate_lines=""
      if [[ -n "${sessions:-}" ]]; then
        while read -r sid uid user seat tty rest; do
          [[ -n "${uid:-}" && -n "${user:-}" ]] || continue
          remote="$(loginctl show-session "$sid" -p Remote --value 2>/dev/null || true)"
          [[ "$remote" == "yes" ]] && continue
          candidate_lines+="$uid $user"$'\n'
        done <<< "$sessions"
      fi
      if id pi >/dev/null 2>&1; then candidate_lines+="$(id -u pi) pi"$'\n'; fi
      if [[ -n "${SUDO_USER:-}" ]] && id "$SUDO_USER" >/dev/null 2>&1; then candidate_lines+="$(id -u "$SUDO_USER") $SUDO_USER"$'\n'; fi
      candidate_lines="$(printf '%s' "$candidate_lines" | awk 'NF>=2 && !seen[$1":"$2]++ {print $1, $2}')"

      if [[ -z "$candidate_lines" ]]; then
        echo "No candidate desktop users found."
      fi

      while read -r uid user; do
        [[ -n "${uid:-}" && -n "${user:-}" ]] || continue
        home_dir="$(getent passwd "$user" | cut -d: -f6 || true)"
        [[ -n "$home_dir" ]] || continue
        display=":0"
        if [[ -e /tmp/.X11-unix/X1 ]]; then display=":1"; fi
        wayland=""
        if compgen -G "/run/user/$uid/wayland-*" >/dev/null 2>&1; then
          wayland="$(basename "$(ls /run/user/$uid/wayland-* 2>/dev/null | head -n1)")"
        else
          wayland="wayland-0"
        fi
        echo ""
        echo "Candidate desktop user: $user uid=$uid DISPLAY=$display WAYLAND_DISPLAY=$wayland"

        # Prefer the orange tactical swaylock visual when supported.
        # This intentionally makes the styled swaylock path the primary lock
        # behavior instead of treating it as an optional theme. i3lock remains
        # only as a non-swaylock fallback for systems without swaylock.
        if [[ -f "$lockscreen_image" ]]; then
          lock_img_escaped="$(printf "%s" "$lockscreen_image" | sed "s/'/'\''/g")"
          if command_exists swaylock; then
            run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" "nohup swaylock -f -i '$lock_img_escaped' --scaling fill --indicator-idle-visible --indicator-radius 95 --indicator-thickness 10 --inside-color 080604cc --ring-color ff7a1aee --line-color 2a0f00ff --separator-color 00000000 --text-color ffe0b3ff --key-hl-color ffb347ff --bs-hl-color ff3b1fff --inside-ver-color 140b00dd --ring-ver-color ffd166ff --text-ver-color ffd166ff --inside-wrong-color 190300dd --ring-wrong-color ff3b1fff --text-wrong-color ffc2b3ff --inside-clear-color 080604cc --ring-clear-color ff7a1aee --text-clear-color ffe0b3ff >/dev/null 2>&1 &" || true
          elif command_exists i3lock; then
            run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" "nohup i3lock -i '$lock_img_escaped' >/dev/null 2>&1 &" || true
          fi
        fi

        if command_exists gdbus; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" gdbus call --session --dest org.freedesktop.ScreenSaver --object-path /org/freedesktop/ScreenSaver --method org.freedesktop.ScreenSaver.Lock || true
        fi
        if command_exists qdbus; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock || true
        fi
        if command_exists xdg-screensaver; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" xdg-screensaver lock || true
        fi
        if command_exists lxlock; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" lxlock || true
        fi
        if command_exists dm-tool; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" dm-tool lock || true
        fi
        if command_exists light-locker-command; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" light-locker-command -l || true
        fi
        if command_exists xscreensaver-command; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" xscreensaver-command -lock || true
        fi
        if command_exists mate-screensaver-command; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" mate-screensaver-command -l || true
        fi
        if command_exists gnome-screensaver-command; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" gnome-screensaver-command -l || true
        fi
        if command_exists cinnamon-screensaver-command; then
          run_user_env "$user" "$uid" "$display" "$wayland" "$home_dir" cinnamon-screensaver-command -l || true
        fi
        # Wayland/i3-style lockers usually stay in the foreground, so launch them detached.
        if command_exists swaylock && [[ ! -f "$lockscreen_image" ]]; then
          run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" 'nohup swaylock -f -c 000000 >/dev/null 2>&1 &' || true
        fi
        if command_exists waylock; then
          run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" 'nohup waylock >/dev/null 2>&1 &' || true
        fi
        if command_exists gtklock; then
          run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" 'nohup gtklock >/dev/null 2>&1 &' || true
        fi
        if command_exists i3lock && [[ ! -f "$lockscreen_image" ]]; then
          run_user_shell_env "$user" "$uid" "$display" "$wayland" "$home_dir" 'nohup i3lock -c 000000 >/dev/null 2>&1 &' || true
        fi
      done <<< "$candidate_lines"

      if [[ "$locked" -eq 0 && -n "${sessions:-}" ]]; then
        echo ""
        echo "Trying loginctl fallback after themed lock-screen attempts..."
        while read -r sid uid user seat tty rest; do
          [[ -n "${sid:-}" ]] || continue
          [[ -n "${uid:-}" ]] || continue
          [[ -n "${user:-}" ]] || continue
          session_remote="$(loginctl show-session "$sid" -p Remote --value 2>/dev/null || true)"
          if [[ "$session_remote" == "yes" ]]; then
            echo "  Skipping remote session $sid."
            continue
          fi
          try_loginctl_session "$sid" || true
        done <<< "$sessions"
      fi

      echo ""
      if [[ "$locked" -eq 1 ]]; then
        echo "TAK server screen lock command was sent."
        echo "If an image-capable locker such as i3lock or swaylock was used, the tactical map lock screen should appear on the attached monitor."
        echo "If the attached monitor used the default desktop lock screen instead, that desktop/session may not support custom lock images through this wrapper."
      else
        echo "No working lock command was detected."
        echo "Install/enable a lock screen tool for the Pi desktop, then try again. Common options include lxlock, xscreensaver, light-locker, swaylock, waylock, or gtklock depending on your desktop/session type."
      fi
      exit 0 ;;
    *) echo "Invalid system action: $action" >&2; exit 2 ;;
  esac
fi
echo "Invalid command" >&2; exit 2
EOF
chmod 0755 "$WRAPPER"
chown root:root "$WRAPPER"
cat > "$SUDOERS" <<EOF
$USER_NAME ALL=(root) NOPASSWD: $WRAPPER *
$USER_NAME ALL=(root) NOPASSWD: /usr/sbin/dhclient -v wwan0, /sbin/dhclient -v wwan0
$USER_NAME ALL=(root) NOPASSWD: /usr/bin/ss -H -ltnup, /bin/ss -H -ltnup
EOF
chmod 0440 "$SUDOERS"
visudo -cf "$SUDOERS" >/dev/null

# Dedicated PAM service for file-upload authentication.
# This avoids tty-oriented rules from services like login while still using
# the server's normal Linux password/account policy.
cat > "$PAM_SERVICE_FILE" <<'EOF'
#%PAM-1.0
auth    include common-auth
account include common-account
EOF
chmod 0644 "$PAM_SERVICE_FILE"
chown root:root "$PAM_SERVICE_FILE"
if [[ ! -f "$ENV_FILE" ]]; then
  PASSWORD="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(18))
PY
)"
  cat > "$ENV_FILE" <<EOF
TAK_DASHBOARD_USER=admin
TAK_DASHBOARD_PASSWORD=$PASSWORD
TAK_DASHBOARD_BIND=127.0.0.1
TAK_DASHBOARD_PORT=8092
TAK_DASHBOARD_DATA_DIR=/var/lib/tak-map
TAK_DASHBOARD_AUTH=linux-pam
TAK_DASHBOARD_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server
TAK_DASHBOARD_REQUIRED_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server
TAK_DASHBOARD_INTERFACES=auto
TAK_DASHBOARD_ZEROTIER_DEVICES=
TAK_DASHBOARD_HALOW_SSID_PREFIX=
TAK_DASHBOARD_INTERNET_PING_TARGET=1.1.1.1
TAK_DASHBOARD_COMMAND_TIMEOUT=90
TAK_DASH_UPLOAD_LIMIT_MB=400
TAK_DASH_ALLOW_INSECURE_UPLOAD_AUTH=false
TAK_DASH_UPLOAD_SESSION_TTL_SECONDS=900
TAK_DASH_SESSION_TTL_SECONDS=43200
TAK_DASH_LOGIN_FAIL_LIMIT=3
TAK_DASH_LOGIN_FAIL_WINDOW_SECONDS=1800
TAK_DASH_PAM_SERVICE=tak-server-dash,sshd,login
TAK_DASH_TAK_MAP_LOGO=/usr/share/tak-server-dash/lockscreen/tak-map-logo.png
TAK_DASH_TAK_MAP_SESSION_TTL_SECONDS=3600
TAK_DASH_MAP_DEFAULT_BASEMAP=esri_topo
TAK_DASH_ADSB_SOURCE=auto
TAK_DASH_ADSB_AIRCRAFT_JSON_URL=
TAK_DASH_ADSB_STALE_SECONDS=60
TAK_DASH_OTS_DB_PATHS=
TAK_DASH_OTS_ADMIN_AUTH_URL=
TAK_DASH_OTS_LOGIN_URLS=
TAK_DASH_OTS_CLIENT_CERT=
TAK_DASH_OTS_CLIENT_KEY=
TAK_DASH_OTS_CLIENT_NAME=
TAK_DASH_OTS_CLIENT_PASSWORD=
TAK_DASH_COT_SOCKET_HOLD_SECONDS=2.0
TAK_DASH_GPS_COT_HOST=127.0.0.1
TAK_DASH_GPS_COT_PORT=8088
TAK_DASH_GPS_COT_TLS=false
TAK_DASH_GPS_COT_CALLSIGN=TAK-SERVER-GPS
TAK_DASH_GPS_COT_UID=
TAK_DASH_GPS_COT_TYPE=a-f-G-U-C
TAK_DASH_LOCKSCREEN_IMAGE=/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-3840x2160.png
TAK_DASH_GPS_COT_STALE_MINUTES=5
TAK_DASH_GPS_SERIAL_PORTS=
TAK_DASH_GPS_SERIAL_BAUDS=115200,9600
TAK_DASH_GPS_SCAN_PI_UARTS=false
TAK_DASH_GPS_SERIAL_ENABLE_CMDS=
TAK_DASH_GPS_SERIAL_POLL_CMDS=
TAK_DASH_GPS_SERIAL_DISABLE_CMDS=
EOF
  chmod 0600 "$ENV_FILE"
else
  PASSWORD="$(grep '^TAK_DASHBOARD_PASSWORD=' "$ENV_FILE" | cut -d= -f2- || true)"
fi
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=TAK Map
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
EnvironmentFile=$ENV_FILE
ExecStart=/usr/bin/python3 $APP_DIR/tak_dashboard.py
Restart=always
RestartSec=3
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

# Force dashboard backend to localhost-only. Public access is HTTPS via nginx on 9443.
if grep -q '^TAK_DASHBOARD_BIND=' "$ENV_FILE"; then
  sed -i 's/^TAK_DASHBOARD_BIND=.*/TAK_DASHBOARD_BIND=127.0.0.1/' "$ENV_FILE"
else
  echo 'TAK_DASHBOARD_BIND=127.0.0.1' >> "$ENV_FILE"
fi
if grep -q '^TAK_DASHBOARD_PORT=' "$ENV_FILE"; then
  sed -i 's/^TAK_DASHBOARD_PORT=.*/TAK_DASHBOARD_PORT=8092/' "$ENV_FILE"
else
  echo 'TAK_DASHBOARD_PORT=8092' >> "$ENV_FILE"
fi
if grep -q '^TAK_DASHBOARD_AUTH=' "$ENV_FILE"; then
  sed -i 's/^TAK_DASHBOARD_AUTH=.*/TAK_DASHBOARD_AUTH=linux-pam/' "$ENV_FILE"
else
  echo 'TAK_DASHBOARD_AUTH=linux-pam' >> "$ENV_FILE"
fi


# Split package role/port
if grep -q '^TAK_DASH_APP_ROLE=' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_APP_ROLE=.*/TAK_DASH_APP_ROLE=map/' "$ENV_FILE"
else
  echo 'TAK_DASH_APP_ROLE=map' >> "$ENV_FILE"
fi

# Ensure generic configurable settings exist.
ensure_env_var() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "$ENV_FILE"; then
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
}
ensure_env_var TAK_DASHBOARD_DATA_DIR "/var/lib/tak-map"
ensure_env_var TAK_DASH_APP_ROLE "map"
ensure_env_var TAK_DASHBOARD_SERVICES "opentakserver,eud_handler_ssl,rabbitmq-server"
ensure_env_var TAK_DASHBOARD_REQUIRED_SERVICES "opentakserver,eud_handler_ssl,rabbitmq-server"
ensure_env_var TAK_DASHBOARD_INTERFACES "auto"
ensure_env_var TAK_DASHBOARD_ZEROTIER_DEVICES ""
ensure_env_var TAK_DASHBOARD_HALOW_SSID_PREFIX ""
ensure_env_var TAK_DASHBOARD_INTERNET_PING_TARGET "1.1.1.1"
ensure_env_var TAK_DASHBOARD_COMMAND_TIMEOUT "90"
ensure_env_var TAK_DASH_UPLOAD_LIMIT_MB "400"
ensure_env_var TAK_DASH_ALLOW_INSECURE_UPLOAD_AUTH "false"
ensure_env_var TAK_DASH_UPLOAD_SESSION_TTL_SECONDS "900"
ensure_env_var TAK_DASH_SESSION_TTL_SECONDS "43200"
ensure_env_var TAK_DASH_LOGIN_FAIL_LIMIT "3"
ensure_env_var TAK_DASH_LOGIN_FAIL_WINDOW_SECONDS "1800"
ensure_env_var TAK_DASH_PAM_SERVICE "tak-server-dash,sshd,login"
ensure_env_var TAK_DASH_TAK_MAP_LOGO "/usr/share/tak-server-dash/lockscreen/tak-map-logo.png"
ensure_env_var TAK_DASH_TAK_MAP_SESSION_TTL_SECONDS "3600"
ensure_env_var TAK_DASH_MAP_DEFAULT_BASEMAP "esri_topo"
ensure_env_var TAK_DASH_ADSB_SOURCE "auto"
ensure_env_var TAK_DASH_ADSB_AIRCRAFT_JSON_URL ""
ensure_env_var TAK_DASH_ADSB_STALE_SECONDS "60"
ensure_env_var TAK_DASH_OTS_DB_PATHS ""
ensure_env_var TAK_DASH_OTS_ADMIN_AUTH_URL ""
ensure_env_var TAK_DASH_OTS_LOGIN_URLS ""
ensure_env_var TAK_DASH_OTS_CONFIG_PATHS ""
ensure_env_var TAK_DASH_OTS_POSTGRES_URI ""
ensure_env_var TAK_DASH_OTS_PYTHON ""
ensure_env_var TAK_DASH_OTS_CLIENT_CERT ""
ensure_env_var TAK_DASH_OTS_CLIENT_KEY ""
ensure_env_var TAK_DASH_OTS_CLIENT_NAME ""
ensure_env_var TAK_DASH_OTS_CLIENT_PASSWORD ""
ensure_env_var TAK_DASH_COT_SOCKET_HOLD_SECONDS "2.0"

detect_opentakserver_python() {
  local existing=""
  existing="$(grep -E '^TAK_DASH_OTS_PYTHON=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  if [[ -n "${existing//[[:space:]]/}" && -x "$existing" ]]; then
    printf '%s\n' "$existing"
    return 0
  fi

  local candidates=()
  local exec_line="" wd="" owner=""
  exec_line="$(systemctl show -p ExecStart --value opentakserver 2>/dev/null || true)"
  if [[ "$exec_line" =~ (/[^[:space:];]*/bin/opentakserver) ]]; then
    local ots_exe="${BASH_REMATCH[1]}"
    candidates+=("$(dirname "$ots_exe")/python3" "$(dirname "$ots_exe")/python")
  fi
  wd="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
  if [[ "$wd" == /home/*/* ]]; then
    owner="$(printf '%s' "$wd" | cut -d/ -f3)"
    candidates+=("/home/$owner/.opentakserver_venv/bin/python3" "/home/$owner/.opentakserver_venv/bin/python")
  fi
  for home_venv in /home/*/.opentakserver_venv/bin/python3 /home/*/.opentakserver_venv/bin/python; do
    [[ -x "$home_venv" ]] && candidates+=("$home_venv")
  done
  candidates+=("/opt/opentakserver/venv/bin/python3")
  local c
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
  done
  return 0
}

detect_opentakserver_db() {
  local existing=""
  existing="$(grep -E '^TAK_DASH_OTS_DB_PATHS=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  if [[ -n "${existing//[[:space:],]/}" ]]; then
    printf '%s\n' "$existing" | tr ',' '\n' | awk 'NF {print; exit}'
    return 0
  fi

  local candidates=()
  local wd=""
  wd="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
  if [[ -n "$wd" && "$wd" != "/" && "$wd" != "n/a" ]]; then
    candidates+=("$wd/ots.db" "$wd/opentakserver.db" "$wd/app.db" "$wd/database.db" "$wd/db.sqlite")
  fi

  # Common OpenTAKServer locations and dynamic user-home install patterns.
  for home_ots in /home/*/ots; do
    [[ -d "$home_ots" ]] && candidates+=("$home_ots/ots.db" "$home_ots/opentakserver.db")
  done
  candidates+=(
    "/var/lib/opentakserver/ots.db"
    "/var/lib/opentakserver/opentakserver.db"
    "/opt/opentakserver/ots.db"
    "/opt/OpenTAKServer/ots.db"
    "/srv/opentakserver/ots.db"
  )

  local c
  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
  done

  # Last-resort root-time search. Keep it shallow enough for fast installs.
  find /home /var/lib /opt /srv -maxdepth 5 -type f \( -name 'ots.db' -o -name 'opentakserver.db' -o -name 'app.db' -o -name 'database.db' -o -name 'db.sqlite' \) 2>/dev/null | head -n1 || true
}

detect_opentakserver_config() {
  local existing=""
  existing="$(grep -E '^TAK_DASH_OTS_CONFIG_PATHS=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  if [[ -n "${existing//[[:space:],;]/}" ]]; then
    printf '%s\n' "$existing" | tr ',;' '\n' | awk 'NF {print; exit}'
    return 0
  fi

  local candidates=()
  local wd=""
  wd="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
  if [[ -n "$wd" && "$wd" != "/" && "$wd" != "n/a" ]]; then
    candidates+=("$wd/config.yml" "$wd/config.yaml")
  fi
  for home_ots in /home/*/ots; do
    [[ -d "$home_ots" ]] && candidates+=("$home_ots/config.yml" "$home_ots/config.yaml")
  done
  candidates+=(
    "/etc/opentakserver/config.yml"
    "/etc/ots/config.yml"
    "/opt/opentakserver/config.yml"
    "/opt/OpenTAKServer/config.yml"
    "/srv/opentakserver/config.yml"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
  done
  return 0
}

grant_opentakserver_config_acl() {
  local cfg="$1"
  [[ -n "$cfg" ]] || return 0
  local dir
  dir="$(dirname "$cfg")"
  grant_opentakserver_dir_acl "$dir"
  [[ -f "$cfg" ]] || return 0
  if ! command -v setfacl >/dev/null 2>&1; then
    echo "WARNING: setfacl not available; cannot auto-grant TAK Map read access to $cfg"
    return 0
  fi
  setfacl -m "u:$USER_NAME:r" "$cfg" 2>/dev/null || true
}

config_has_postgres_uri() {
  local cfg="$1"
  [[ -f "$cfg" ]] || return 1
  grep -Eq '^SQLALCHEMY_DATABASE_URI:[[:space:]]*(postgresql|postgres)(\+|://)' "$cfg" 2>/dev/null
}

grant_opentakserver_dir_acl() {
  local dir="$1"
  [[ -n "$dir" && -d "$dir" ]] || return 0
  if ! command -v setfacl >/dev/null 2>&1; then
    echo "WARNING: setfacl not available; cannot auto-grant TAK Map traversal access to $dir"
    return 0
  fi
  # Grant execute-only traversal on parents, and read/execute on the OTS directory.
  python3 - "$dir" <<'PARENTS' | while IFS= read -r parent; do
from pathlib import Path
import sys
p=Path(sys.argv[1]).resolve()
for parent in reversed(list(p.parents)):
    if str(parent) == '/':
        continue
    print(parent)
PARENTS
    setfacl -m "u:$USER_NAME:--x" "$parent" 2>/dev/null || true
  done || true
  setfacl -m "u:$USER_NAME:rx" "$dir" 2>/dev/null || true
}


grant_opentakserver_python_acl() {
  local py="$1"
  [[ -n "$py" && -e "$py" ]] || return 0
  if ! command -v setfacl >/dev/null 2>&1; then
    echo "WARNING: setfacl not available; cannot auto-grant TAK Map access to OpenTAKServer Python verifier: $py"
    return 0
  fi
  local bindir venvdir
  bindir="$(dirname "$py")"
  if [[ "$(basename "$bindir")" == "bin" ]]; then
    venvdir="$(dirname "$bindir")"
  else
    venvdir="$bindir"
  fi
  [[ -d "$venvdir" ]] || return 0
  grant_opentakserver_dir_acl "$venvdir"
  # The dashboard runs as takserverdash. It needs read/execute access to the
  # OTS virtualenv so it can verify Flask-Security/Passlib password hashes
  # with the same libraries OpenTAKServer uses. This does not grant write access.
  find "$venvdir" -type d -exec setfacl -m "u:$USER_NAME:rx" {} + 2>/dev/null || true
  find "$venvdir" -type f -exec setfacl -m "u:$USER_NAME:r" {} + 2>/dev/null || true
  for exe in "$py" "$venvdir/bin/python" "$venvdir/bin/python3"; do
    if [[ -e "$exe" ]]; then
      setfacl -m "u:$USER_NAME:rx" "$exe" 2>/dev/null || true
    fi
  done
  echo "Granted TAK Map read/execute access to OpenTAKServer Python verifier: $py"
}

grant_opentakserver_db_acl() {
  local db="$1"
  [[ -n "$db" ]] || return 0
  local dir
  dir="$(dirname "$db")"
  grant_opentakserver_dir_acl "$dir"
  [[ -f "$db" ]] || return 0
  if ! command -v setfacl >/dev/null 2>&1; then
    echo "WARNING: setfacl not available; cannot auto-grant TAK Map read access to $db"
    return 0
  fi
  setfacl -m "u:$USER_NAME:r" "$db" 2>/dev/null || true
  for sidecar in "$db-wal" "$db-shm" "$db-journal"; do
    if [[ -e "$sidecar" ]]; then
      setfacl -m "u:$USER_NAME:r" "$sidecar" 2>/dev/null || true
    fi
  done
}

configure_tak_map_ots_auth() {
  local current_db="" detected_db="" current_cfg="" detected_cfg="" current_py="" detected_py="" wd=""

  current_py="$(grep -E '^TAK_DASH_OTS_PYTHON=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  detected_py="$(detect_opentakserver_python | head -n1 || true)"
  if [[ -z "${current_py//[[:space:]]/}" && -n "$detected_py" ]]; then
    sed -i "s#^TAK_DASH_OTS_PYTHON=.*#TAK_DASH_OTS_PYTHON=$detected_py#" "$ENV_FILE"
    echo "Configured TAK Map OpenTAKServer Python verifier: $detected_py"
    current_py="$detected_py"
  fi
  if [[ -n "${current_py//[[:space:]]/}" ]]; then
    grant_opentakserver_python_acl "$current_py"
  elif [[ -n "$detected_py" ]]; then
    grant_opentakserver_python_acl "$detected_py"
  fi

  current_cfg="$(grep -E '^TAK_DASH_OTS_CONFIG_PATHS=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  detected_cfg="$(detect_opentakserver_config | head -n1 || true)"
  if [[ -z "${current_cfg//[[:space:],;]/}" && -n "$detected_cfg" ]]; then
    sed -i "s#^TAK_DASH_OTS_CONFIG_PATHS=.*#TAK_DASH_OTS_CONFIG_PATHS=$detected_cfg#" "$ENV_FILE"
    echo "Configured TAK Map OpenTAKServer config path: $detected_cfg"
    current_cfg="$detected_cfg"
  fi

  if [[ -n "${current_cfg//[[:space:],;]/}" ]]; then
    while IFS= read -r cfg; do
      cfg="$(printf '%s' "$cfg" | xargs || true)"
      if [[ -n "$cfg" ]]; then
        grant_opentakserver_config_acl "$cfg"
        if config_has_postgres_uri "$cfg"; then
          echo "TAK Map auth will use OpenTAKServer PostgreSQL URI from config.yml."
        fi
      fi
    done < <(printf '%s\n' "$current_cfg" | tr ',;' '\n') || true
  fi

  # SQLite fallback remains for older OpenTAKServer installs. It is skipped at
  # runtime when SQLALCHEMY_DATABASE_URI is PostgreSQL in config.yml.
  current_db="$(grep -E '^TAK_DASH_OTS_DB_PATHS=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  detected_db="$(detect_opentakserver_db | head -n1 || true)"
  if [[ -z "${current_db//[[:space:],]/}" && -n "$detected_db" ]]; then
    sed -i "s#^TAK_DASH_OTS_DB_PATHS=.*#TAK_DASH_OTS_DB_PATHS=$detected_db#" "$ENV_FILE"
    echo "Configured TAK Map OpenTAKServer SQLite DB auth path: $detected_db"
    current_db="$detected_db"
  fi

  if [[ -n "${current_db//[[:space:],]/}" ]]; then
    while IFS= read -r db; do
      db="$(printf '%s' "$db" | xargs || true)"
      if [[ -n "$db" ]]; then
        grant_opentakserver_db_acl "$db"
      fi
    done < <(printf '%s\n' "$current_db" | tr ',' '\n') || true
  elif [[ -z "${current_cfg//[[:space:],;]/}" ]]; then
    wd="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
    if [[ -n "$wd" && "$wd" != "/" && "$wd" != "n/a" ]]; then
      grant_opentakserver_dir_acl "$wd"
      echo "TAK Map OpenTAKServer auth source was not auto-detected; granted traversal to OTS working directory: $wd"
      echo "Set TAK_DASH_OTS_CONFIG_PATHS or TAK_DASH_OTS_DB_PATHS in $ENV_FILE if TAK Map login cannot find OTS auth."
    else
      echo "TAK Map OpenTAKServer auth source was not auto-detected; set TAK_DASH_OTS_CONFIG_PATHS or TAK_DASH_OTS_DB_PATHS in $ENV_FILE if needed."
    fi
  fi
  return 0
}
configure_tak_map_ots_auth || true

detect_opentakserver_client_cert_pair() {
  # Print candidate cert|key pairs in preference order. The caller will grant ACL
  # and verify readability before writing TAK_DASH_OTS_CLIENT_CERT/KEY.
  local current_cert="" current_key="" wd="" cfg="" home="" base="" rel="" certname="" keyname="" cert="" key=""
  local -a bases=()
  local -a pairs=()

  current_cert="$(grep -E '^TAK_DASH_OTS_CLIENT_CERT=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
  current_key="$(grep -E '^TAK_DASH_OTS_CLIENT_KEY=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"

  # Prefer the user who invoked sudo. This avoids picking stale /root/ots certs
  # simply because the installer itself is running as root.
  if [[ -n "${INSTALL_INVOKING_HOME:-}" && -d "${INSTALL_INVOKING_HOME:-/nonexistent}/ots" ]]; then
    bases+=("$INSTALL_INVOKING_HOME/ots")
  fi

  # Next, scan normal user homes.
  for home in /home/*; do
    [[ -d "$home/ots" ]] || continue
    bases+=("$home/ots")
  done

  wd="$(systemctl show -p WorkingDirectory --value opentakserver 2>/dev/null || true)"
  if [[ -n "$wd" && "$wd" != "/" && "$wd" != "n/a" ]]; then bases+=("$wd"); fi
  if [[ -n "${OTS_WORKDIR:-}" && -d "${OTS_WORKDIR:-/nonexistent}" ]]; then bases+=("$OTS_WORKDIR"); fi
  cfg="$(detect_opentakserver_config | head -n1 || true)"
  if [[ -n "$cfg" ]]; then bases+=("$(dirname "$cfg")"); fi

  bases+=("/var/lib/opentakserver" "/opt/opentakserver" "/opt/OpenTAKServer" "/srv/opentakserver")

  # Existing env comes after user-home paths if it points under /root. Otherwise
  # keep manually configured env as a high-priority candidate.
  if [[ -n "${current_cert//[[:space:]]/}" && -n "${current_key//[[:space:]]/}" ]]; then
    case "$current_cert" in
      /root/*) : ;;
      *) pairs+=("$current_cert|$current_key") ;;
    esac
  fi

  # /root/ots is a last resort for systems genuinely installed under root.
  bases+=("/root/ots")

  local seen_bases=""
  for base in "${bases[@]}"; do
    [[ -n "$base" && -d "$base" ]] || continue
    case ";$seen_bases;" in *";$base;"*) continue;; esac
    seen_bases="$seen_bases;$base"
    for rel in \
      "ca/certs/takdash|takdash.pem|takdash.nopass.key" \
      "ca/certs/takdash|takdash.pem|takdash.key" \
      "ca/certs/takdash|takdash.pem|../keys/takdash.nopass.key" \
      "ca/certs/takdash|takdash.pem|../keys/takdash.key" \
      "ca/certs/tak-dashboard|tak-dashboard.pem|tak-dashboard.nopass.key" \
      "ca/certs/administrator|administrator.pem|administrator.nopass.key" \
      "ca/certs/admin|admin.pem|admin.nopass.key"; do
      IFS='|' read -r sub certname keyname <<< "$rel"
      cert="$base/$sub/$certname"
      key="$base/$sub/$keyname"
      if [[ -f "$cert" && -f "$key" ]]; then
        pairs+=("$cert|$key")
      fi
    done
  done

  # Append root env as absolute last resort.
  if [[ -n "${current_cert//[[:space:]]/}" && -n "${current_key//[[:space:]]/}" ]]; then
    case "$current_cert" in
      /root/*) pairs+=("$current_cert|$current_key") ;;
    esac
  fi

  local seen_pairs="" pair=""
  for pair in "${pairs[@]}"; do
    [[ -n "$pair" ]] || continue
    case ";$seen_pairs;" in *";$pair;"*) continue;; esac
    seen_pairs="$seen_pairs;$pair"
    cert="${pair%%|*}"
    key="${pair#*|}"
    [[ -f "$cert" && -f "$key" ]] || continue
    printf '%s|%s\n' "$cert" "$key"
  done
  return 0
}

dash_user_can_read_path() {
  local path="$1"
  if command -v runuser >/dev/null 2>&1; then
    runuser -u "$USER_NAME" -- test -r "$path" 2>/dev/null
  elif command -v sudo >/dev/null 2>&1; then
    sudo -u "$USER_NAME" test -r "$path" 2>/dev/null
  else
    return 1
  fi
}

grant_ots_client_cert_acl() {
  local cert="$1" key="$2"
  [[ -n "$cert" && -n "$key" && -f "$cert" && -f "$key" ]] || return 0
  if ! command -v setfacl >/dev/null 2>&1; then
    echo "WARNING: setfacl not available; cannot auto-grant TLS client cert access to $cert"
    return 0
  fi
  python3 - "$cert" "$key" <<'CERTPARENTS' | while IFS= read -r parent; do
from pathlib import Path
import sys
seen=[]
for raw in sys.argv[1:]:
    p=Path(raw).resolve()
    chain=list(p.parents)
    for parent in reversed(chain):
        if str(parent) == '/':
            continue
        s=str(parent)
        if s not in seen:
            seen.append(s)
for s in seen:
    print(s)
CERTPARENTS
    setfacl -m "u:$USER_NAME:--x" "$parent" 2>/dev/null || true
  done || true
  setfacl -m "u:$USER_NAME:r" "$cert" 2>/dev/null || true
  setfacl -m "u:$USER_NAME:r" "$key" 2>/dev/null || true

  if dash_user_can_read_path "$cert" && dash_user_can_read_path "$key"; then
    sed -i '/^TAK_DASH_OTS_CLIENT_CERT=/d;/^TAK_DASH_OTS_CLIENT_KEY=/d' "$ENV_FILE"
    {
      printf 'TAK_DASH_OTS_CLIENT_CERT=%s\n' "$cert"
      printf 'TAK_DASH_OTS_CLIENT_KEY=%s\n' "$key"
    } >> "$ENV_FILE"
    local client_name
    client_name="$(basename "$(dirname "$cert")")"
    if [[ -n "${client_name//[[:space:]]/}" ]]; then
      ensure_env_var TAK_DASH_OTS_CLIENT_NAME "$client_name"
      current_sender_callsign="$(grep -E '^TAK_DASH_FILESHARE_SENDER_CALLSIGN=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
      current_sender_uid="$(grep -E '^TAK_DASH_FILESHARE_SENDER_UID=' "$ENV_FILE" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
      if [[ -z "${current_sender_callsign//[[:space:]]/}" ]]; then ensure_env_var TAK_DASH_FILESHARE_SENDER_CALLSIGN "$client_name"; fi
      if [[ -z "${current_sender_uid//[[:space:]]/}" ]]; then ensure_env_var TAK_DASH_FILESHARE_SENDER_UID "$client_name"; fi
    fi
    echo "Configured TAK Dashboard TLS CoT client certificate ACLs: $cert"
  else
    echo "WARNING: TLS client cert/key were found but are still not readable by $USER_NAME after ACL update: $cert / $key"
  fi
}

configure_ots_client_cert_acl() {
  local pair="" cert="" key=""
  local configured="0"
  while IFS= read -r pair; do
    [[ -n "$pair" ]] || continue
    cert="${pair%%|*}"
    key="${pair#*|}"
    grant_ots_client_cert_acl "$cert" "$key"
    if dash_user_can_read_path "$cert" && dash_user_can_read_path "$key"; then
      configured="1"
      break
    fi
  done < <(detect_opentakserver_client_cert_pair || true)

  if [[ "$configured" != "1" ]]; then
    sed -i '/^TAK_DASH_OTS_CLIENT_CERT=/d;/^TAK_DASH_OTS_CLIENT_KEY=/d' "$ENV_FILE" 2>/dev/null || true
    echo "WARNING: OpenTAKServer administrator client cert/key were not auto-detected as readable by $USER_NAME. TLS CoT socket send will skip unreadable certs. Set TAK_DASH_OTS_CLIENT_CERT and TAK_DASH_OTS_CLIENT_KEY manually in $ENV_FILE if needed."
  fi
}
configure_ots_client_cert_acl || true

ensure_env_var TAK_DASH_GPS_COT_HOST "127.0.0.1"
ensure_env_var TAK_DASH_GPS_COT_PORT "8088"
ensure_env_var TAK_DASH_GPS_COT_TLS "false"
ensure_env_var TAK_DASH_OTS_COT_HOST "127.0.0.1"
ensure_env_var TAK_DASH_OTS_COT_PORT "8088"
ensure_env_var TAK_DASH_OFFLINE_SENDER_CALLSIGN "tak-dashboard"
ensure_env_var TAK_DASH_OFFLINE_SENDER_UID "TAK-DASHBOARD"
ensure_env_var TAK_DASH_GPS_COT_CALLSIGN "TAK-SERVER-GPS"
ensure_env_var TAK_DASH_GPS_COT_UID ""
ensure_env_var TAK_DASH_GPS_COT_TYPE "a-f-G-U-C"
ensure_env_var TAK_DASH_GPS_COT_STALE_MINUTES "5"
ensure_env_var TAK_DASH_LOCKSCREEN_IMAGE "/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-3840x2160.png"
# Tactical topo swaylock migration: update prior bundled lockscreen paths
# to the current no-form tactical/topographic background. Custom paths are left alone.
if grep -Eq '^TAK_DASH_LOCKSCREEN_IMAGE=/usr/share/tak-server-dash/lockscreen/tactical-map-burgundy(-swaylock)?-[0-9]+x[0-9]+\.png$' "$ENV_FILE"; then
  sed -i 's#^TAK_DASH_LOCKSCREEN_IMAGE=.*#TAK_DASH_LOCKSCREEN_IMAGE=/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-3840x2160.png#' "$ENV_FILE"
fi
if grep -Eq '^TAK_DASH_LOCKSCREEN_IMAGE=/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-[0-9]+x[0-9]+\.png$' "$ENV_FILE"; then
  sed -i 's#^TAK_DASH_LOCKSCREEN_IMAGE=.*#TAK_DASH_LOCKSCREEN_IMAGE=/usr/share/tak-server-dash/lockscreen/tactical-topo-swaylock-3840x2160.png#' "$ENV_FILE"
fi

# GPS CoT defaults: use hostname-dash so the UID shows the marker came from the dashboard.
GPS_DEFAULT_UID="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo tak-server)-dash"
GPS_DEFAULT_UID="$(printf '%s' "$GPS_DEFAULT_UID" | sed 's/[^A-Za-z0-9_.@-]/-/g; s/--*/-/g; s/^-//; s/-$//')"
if [[ -z "$GPS_DEFAULT_UID" || "$GPS_DEFAULT_UID" == "-dash" ]]; then GPS_DEFAULT_UID="tak-server-dash"; fi
if ! grep -q '^TAK_DASH_GPS_COT_UID=' "$ENV_FILE"; then
  echo "TAK_DASH_GPS_COT_UID=$GPS_DEFAULT_UID" >> "$ENV_FILE"
elif grep -Eq '^TAK_DASH_GPS_COT_UID=(|tak-server-dash-gps)$' "$ENV_FILE"; then
  sed -i "s/^TAK_DASH_GPS_COT_UID=.*/TAK_DASH_GPS_COT_UID=$GPS_DEFAULT_UID/" "$ENV_FILE"
fi
if grep -q '^TAK_DASH_GPS_COT_STALE_MINUTES=10$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_COT_STALE_MINUTES=.*/TAK_DASH_GPS_COT_STALE_MINUTES=5/' "$ENV_FILE"
fi
if grep -Eq '^TAK_DASH_GPS_FIX_WAIT_SECONDS=(45|90)$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_FIX_WAIT_SECONDS=.*/TAK_DASH_GPS_FIX_WAIT_SECONDS=300/' "$ENV_FILE"
fi
if grep -q '^TAK_DASH_GPS_FIX_POLL_SECONDS=3$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_FIX_POLL_SECONDS=.*/TAK_DASH_GPS_FIX_POLL_SECONDS=5/' "$ENV_FILE"
fi
if grep -q '^TAK_DASH_GPS_SERIAL_BAUDS=115200,9600,57600,38400,19200,4800$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_SERIAL_BAUDS=.*/TAK_DASH_GPS_SERIAL_BAUDS=115200,9600/' "$ENV_FILE"
fi

if grep -Eq '^TAK_DASH_GPS_TOTAL_TIMEOUT_SECONDS=(110|180)$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_TOTAL_TIMEOUT_SECONDS=.*/TAK_DASH_GPS_TOTAL_TIMEOUT_SECONDS=330/' "$ENV_FILE"
fi
if grep -Eq '^TAK_DASH_GPS_SERIAL_COMBO_SECONDS=(22|45)$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASH_GPS_SERIAL_COMBO_SECONDS=.*/TAK_DASH_GPS_SERIAL_COMBO_SECONDS=300/' "$ENV_FILE"
fi
ensure_env_var TAK_DASH_GPS_FIX_WAIT_SECONDS "300"
ensure_env_var TAK_DASH_GPS_FIX_POLL_SECONDS "5"
ensure_env_var TAK_DASH_GPS_DISABLE_AFTER_PULL "true"
ensure_env_var TAK_DASH_GPS_SERIAL_PORTS ""
ensure_env_var TAK_DASH_GPS_SERIAL_BAUDS "115200,9600"
# GPS diagnostics are intentionally capped so the dashboard returns useful output instead of timing out.
ensure_env_var TAK_DASH_GPS_TOTAL_TIMEOUT_SECONDS "330"
ensure_env_var TAK_DASH_GPS_SERIAL_MAX_PORTS "8"
ensure_env_var TAK_DASH_GPS_SERIAL_MAX_BAUDS "2"
ensure_env_var TAK_DASH_GPS_SERIAL_CMD_TIMEOUT_SECONDS "1.0"
ensure_env_var TAK_DASH_GPS_SERIAL_READ_SECONDS "0.6"
ensure_env_var TAK_DASH_GPS_SERIAL_COMBO_SECONDS "300"
ensure_env_var TAK_DASH_GPS_SCAN_PI_UARTS "false"
ensure_env_var TAK_DASH_GPS_SERIAL_ENABLE_CMDS ""
ensure_env_var TAK_DASH_GPS_SERIAL_POLL_CMDS ""
ensure_env_var TAK_DASH_GPS_SERIAL_DISABLE_CMDS ""


# v46 default-service cleanup: remove older generic defaults from the env file.
if grep -q '^TAK_DASHBOARD_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server,4gmodem,adsbcot$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASHBOARD_SERVICES=.*/TAK_DASHBOARD_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server/' "$ENV_FILE"
fi
if grep -q '^TAK_DASHBOARD_REQUIRED_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server,4gmodem,adsbcot$' "$ENV_FILE"; then
  sed -i 's/^TAK_DASHBOARD_REQUIRED_SERVICES=.*/TAK_DASHBOARD_REQUIRED_SERVICES=opentakserver,eud_handler_ssl,rabbitmq-server/' "$ENV_FILE"
fi

# Install HTTPS reverse proxy for the whole dashboard when Nginx is available.
mkdir -p /etc/tak-server-dash
if [[ -f nginx/tak-map-https-9444.conf.example ]]; then
  cp nginx/tak-map-https-9444.conf.example /etc/tak-server-dash/tak-map-https-9444.conf.example
fi
if [[ -f nginx/tak-map-https-9444.conf ]]; then
  cp nginx/tak-map-https-9444.conf /etc/tak-server-dash/tak-map-https-9444.conf
fi
if command -v nginx >/dev/null 2>&1; then
  mkdir -p /etc/tak-server-dash/certs
  if [[ -d /etc/nginx/conf.d ]]; then
    rm -f /etc/nginx/conf.d/99-tak-server-dashboard-proxy-hash.conf 2>/dev/null || true
    cat > /etc/nginx/conf.d/00-tak-server-dash-proxy-hash.conf <<'EOF'
# TAK Server Dash: avoid nginx proxy header hash warnings on systems with larger proxy header sets.
proxy_headers_hash_max_size 4096;
proxy_headers_hash_bucket_size 256;
EOF
  fi
  echo "Regenerating dashboard HTTPS certificate with serverAuth key usage and current IP SANs..."
  if ! "$WRAPPER" cert-setup "" "" >/tmp/tak-server-dash-cert-setup.log 2>&1; then
    echo "WARNING: Certificate regeneration failed. Details:"
    cat /tmp/tak-server-dash-cert-setup.log || true
  fi
  if [[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]]; then
    cp /etc/tak-server-dash/tak-map-https-9444.conf /etc/nginx/sites-available/tak-map-https-9444
    ln -sf /etc/nginx/sites-available/tak-map-https-9444 /etc/nginx/sites-enabled/tak-map-https-9444
  elif [[ -d /etc/nginx/conf.d ]]; then
    cp /etc/tak-server-dash/tak-map-https-9444.conf /etc/nginx/conf.d/tak-map-https-9444.conf
  else
    echo "WARNING: Nginx config directories not found. HTTPS config copied to /etc/tak-server-dash/tak-map-https-9444.conf only."
  fi
  if nginx -t >/tmp/tak-server-dash-nginx-test.log 2>&1; then
    systemctl reload nginx || systemctl restart nginx || true
    echo "Nginx HTTPS proxy enabled on port 9444."
    if command -v ufw >/dev/null 2>&1; then
      ufw delete allow 8092 >/dev/null 2>&1 || true
    fi
  else
    echo "WARNING: Nginx config test failed. HTTPS proxy was not enabled correctly. Details:"
    cat /tmp/tak-server-dash-nginx-test.log || true
    rm -f /etc/nginx/sites-enabled/tak-map-https-9444 2>/dev/null || true
    rm -f /etc/nginx/conf.d/tak-map-https-9444.conf 2>/dev/null || true
  fi
else
  echo "Nginx not found. HTTPS config copied to /etc/tak-server-dash/ but not enabled."
fi

systemctl daemon-reload
systemctl enable --now tak-map.service
systemctl restart tak-map.service || true
echo
echo "Installed and started tak-map.service"
echo
echo "Authentication: enabled for dashboard viewing"
echo "  Sign in with a Raspberry Pi OS/Linux account."
echo "  Sessions expire after 12 hours. Three failed login attempts lock that username/IP for 30 minutes."
echo "  Direct HTTP fallback on port 8092 has been disabled; the backend now binds to localhost only."
echo
echo "Open from any reachable Pi IP using HTTPS:"
echo "  https://<PI_IP>:9444"
echo "  Do not use http:// on port 9444; nginx will reject plain HTTP on the HTTPS port."
echo ""
echo "HTTPS proxy config:"
echo "  /etc/tak-server-dash/tak-map-https-9444.conf"
echo "  /etc/tak-server-dash/tak-map-https-9444.conf.example"
echo
echo "Detected IP addresses:"
hostname -I | tr ' ' '\n' | sed '/^$/d' | while read -r ip; do echo "  https://$ip:9444"; done
echo "Useful commands:"
echo "  sudo systemctl status tak-map.service"
echo "  sudo journalctl -u tak-map.service -f"
echo "  sudo cat /etc/tak-map.env"



echo "Install folder left in place so uninstall.sh remains available."

# Return to Downloads at script exit for interactive runs. Note: a normal executed
# script cannot change the parent shell directory, so the install instructions also
# include an explicit final cd ~/Downloads command.
if [[ -n "${INSTALL_INVOKING_HOME:-}" && -d "${INSTALL_INVOKING_HOME}/Downloads" ]]; then
  cd "${INSTALL_INVOKING_HOME}/Downloads" || true
  echo "Installer finished from: $(pwd)"
fi
