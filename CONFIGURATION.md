# Configuration

Main environment file:

```text
/etc/tak-server-dash.env
```

Runtime dashboard UI configuration:

```text
/var/lib/tak-server-dash/config.json
```

The dashboard UI can manage:

- ZeroTier peer IPs and callsigns
- Monitored services
- Top banner warning types
- Network neighbor saved hostnames/labels

Restart after editing the env file manually:

```bash
sudo systemctl restart tak-server-dash.service
```

The dashboard UI settings do not require a service restart.


## Remote Command Execution

Custom command buttons are stored in the runtime config file:

```text
/var/lib/tak-server-dash/config.json
```

Command output history is retained for five days in:

```text
/var/lib/tak-server-dash/command_history.json
```

Commands run as the dashboard service user. Root-level actions should be routed through the installed allowlist wrapper rather than exposing arbitrary root shell commands.


## Network Neighbor Labels

Saved Network Neighbors labels are stored under `neighbor_hostnames` in:

```text
/var/lib/tak-server-dash/config.json
```

Use the dashboard table to save or update labels rather than editing the file manually.


## File Uploads

File Uploads authenticate against local Linux/PAM accounts and do not require a dashboard-specific user database. No group membership requirement is enforced by default.

Environment settings:

```text
TAK_DASH_UPLOAD_LIMIT_MB=400
TAK_DASH_ALLOW_INSECURE_UPLOAD_AUTH=false
TAK_DASH_UPLOAD_SESSION_TTL_SECONDS=900
```

Allowed upload destinations are limited to the authenticated user's `~/Desktop`, `~/Downloads`, or home folder root `~/`.

Use HTTPS through Nginx for upload login. The installer copies an example Nginx config to `/etc/tak-server-dash/tak-server-dash-https-9443.conf.example`.


## HTTPS reverse proxy

When Nginx is installed, install.sh enables an HTTPS reverse proxy for the whole dashboard on port `9443`. The proxy config is stored at `/etc/tak-server-dash/tak-server-dash-https-9443.conf` and installed into Nginx. Direct HTTP on port `8091` remains available as a fallback.
