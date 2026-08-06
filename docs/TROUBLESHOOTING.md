# Troubleshooting

## Check service status

```bash
sudo systemctl status tak-map.service --no-pager
sudo journalctl -u tak-map.service -n 100 --no-pager
```

## Check Nginx

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
```

## Browser-side checks

Open Developer Tools and check the Console and Network tabs for failed requests, authentication errors, or JavaScript exceptions.

## Common ports

```text
9444  HTTPS TAK Map reverse proxy
8092  local backend/fallback service
```

## Reinstall / repair

```bash
cd tak-map
sudo ./install.sh
```

## Replay recording source

Historical recording is owned by TAK Gateway. If Replay periods are missing, check TAK Gateway recording status and the Replay API connection rather than browser storage.


## Context panel width or scrollbar

TAK Map 1.4.0 i620 sizes context panels from their visible content. If a panel appears to retain an older fixed width after upgrading, close all TAK Map tabs, reopen the application, and perform a hard refresh. The browser should load `tak-map-package-i580.js?v=1.4.0-i620`. Horizontal scrolling is not expected; long values should wrap and the panel body should use the themed vertical scrollbar.
