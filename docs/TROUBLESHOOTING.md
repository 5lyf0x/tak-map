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
