#!/usr/bin/env bash
set -euo pipefail
PURGE=false
if [[ "${1:-}" == "--purge" ]]; then PURGE=true; fi
if [[ "${EUID}" -ne 0 ]]; then echo "Run with sudo: sudo ./uninstall.sh [--purge]"; exit 1; fi
systemctl disable --now tak-map.service 2>/dev/null || true
rm -f /etc/systemd/system/tak-map.service
systemctl daemon-reload
rm -f /etc/nginx/sites-enabled/tak-map-https-9444 /etc/nginx/sites-available/tak-map-https-9444 /etc/nginx/conf.d/tak-map-https-9444.conf 2>/dev/null || true
if command -v nginx >/dev/null 2>&1; then
  nginx -t >/tmp/tak-map.service.nginx-test.log 2>&1 && (systemctl reload nginx || true) || true
fi
rm -rf /opt/tak-map
rm -rf /usr/share/tak-server-dash/vendor 2>/dev/null || true
echo "Removed TAK Map service and app files."
if [[ "$PURGE" == "true" ]]; then
  rm -f /etc/tak-map.env
  rm -rf /var/lib/tak-map
  echo "Purged /etc/tak-map.env and /var/lib/tak-map."
else
  echo "Kept /etc/tak-map.env and /var/lib/tak-map."
  echo "To remove preserved config/data too, run: sudo ./uninstall.sh --purge"
fi
