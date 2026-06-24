# TAK Map

Standalone TAK Map web interface for OpenTAKServer/mobile TAK server deployments.

This repository is prepared as a clean source package for GitHub. It keeps the application code from the latest TAK Map package while adding repository metadata, documentation, validation scripts, and GitHub Actions workflow support.

## Current build

- Release label: `v1.1.0`
- Main service file: `tak_dashboard.py`
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

## License

Apache-2.0. See [LICENSE](LICENSE).
