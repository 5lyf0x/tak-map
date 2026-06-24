# TAK Map

Standalone TAK Map web interface for OpenTAKServer/mobile TAK server deployments.

This repository is prepared as a clean source package for GitHub. It keeps the application code from the latest TAK Map package while adding repository metadata, documentation, validation scripts, and GitHub Actions workflow support.

## Current build

- Release label: `v1.1.0`
- Internal package iteration: `v324`
- Main service file: `tak_dashboard.py`
- Default local backend port: `8092`
- HTTPS reverse proxy port: `9444`

## Features

- Browser-based TAK Map interface
- OpenTAKServer login/session support
- Data Sync object display
- Local Data import/export for points, routes, and shapes
- ADS-B aircraft display with class filtering and aircraft popups
- ADS-B tracking route save/export workflow
- External source and basemap tooling
- Terrain / elevation / viewshed tooling
- HTTPS certificate setup helper
- Raspberry Pi/mobile server oriented install script

## Repository layout

```text
tak-map/
├── tak_dashboard.py              # main Python service/application
├── install.sh                    # installer/upgrade script
├── uninstall.sh                  # uninstall helper
├── takmap.js                     # packaged JavaScript reference asset
├── embedded_takmap.js            # packaged JavaScript reference asset
├── combined_scripts_v287.js      # packaged combined JavaScript reference asset
├── assets/                       # ADS-B, lockscreen, and MIL-STD-2525 assets
├── nginx/                        # HTTPS reverse proxy example/config
├── docs/                         # GitHub-ready documentation
├── scripts/                      # validation/build helpers
└── .github/workflows/            # CI validation workflow
```

## Install on Raspberry Pi / Linux host

Download or clone the repository, then run:

```bash
cd tak-map
sudo ./install.sh
```

After installation, open:

```text
https://<server-ip>:9444
```

Direct HTTP fallback, when enabled by the service, is usually:

```text
http://<server-ip>:8092
```

## Upgrade from a downloaded ZIP

```bash
cd ~/Downloads/tak/tak-map
unzip -o tak-map-v324.zip
cd tak-map
sudo ./install.sh
cd ~/Downloads
```

## Security notes

Before making a fork or repo public, confirm that you have not committed:

- private keys, certificates, `.p12`, `.pfx`, `.pem`, `.key`, or `.crt` files
- `.env` files or local service configuration
- live TAK server credentials
- private ZeroTier/network details beyond generic example text
- exported missions, local data, map packages, logs, or screenshots containing sensitive locations

The included `.gitignore` is designed to keep common runtime files and secrets out of Git, but it is still worth reviewing `git status` before every commit.

## Validate locally

```bash
./scripts/validate_package.sh
```

## Build a distributable ZIP

```bash
./scripts/build_package.sh v324
```

The ZIP is written to `dist/`.

## License

Apache-2.0. See [LICENSE](LICENSE).
