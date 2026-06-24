# Configuration

Runtime configuration is stored on the target system, not in the GitHub source tree.

Common runtime locations:

```text
/etc/tak-server-dash.env
/var/lib/tak-server-dash/config.json
/etc/tak-server-dash/certs/
```

Do not commit those runtime files to this repository.

## HTTPS

TAK Map uses the Nginx configuration in `nginx/` as its HTTPS reverse-proxy template. The installer places the active runtime copy under `/etc/tak-server-dash/` and points it at the local Python service.

## OpenTAKServer

TAK Map is designed to work beside OpenTAKServer and can use OpenTAKServer admin credentials for TAK Map login/session workflows.

## ADS-B

ADS-B behavior is controlled from the TAK Map UI. Upstream aircraft data, class filters, update rate, and tracking are runtime behavior, not Git repository configuration.
