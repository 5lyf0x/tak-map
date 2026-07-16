# TAK Map Replay Mode (v419)

TAK Map v419 adds a read-only integration with the TAK Gateway Replay API v1.

## Behavior

- Live Map and Replay Mode are mutually exclusive.
- Entering Replay Mode pauses TAK Map live-data requests and hides the live Leaflet map.
- A separate Leaflet replay map is created with the same configured basemap catalog.
- Leaving Replay Mode destroys the replay map, clears replay objects/trails, restores Live Map, and requests immediate live refreshes.
- Replay Mode never publishes CoT, writes to OpenTAKServer, or adds content to Data Sync.
- Page reloads always start in Live Map.

## Object controls

Every replay point object can expose these popup controls:

- **Track**: fixed label with a red/green status lamp. Trails begin at the current replay time and are off by default.
- **Follow**: fixed label with a red/green status lamp. Only one object may be followed at a time.
- **Clear Trail**: removes the selected object's existing trail without changing other tracked objects.

Multiple objects may be tracked simultaneously. Trail histories are bounded to 5,000 points per object.

## TAK Gateway certificate configuration

TAK Map proxies Replay API requests server-side. Browser clients never receive the Replay client private key.

On the TAK Gateway host, create a Replay API client certificate:

```bash
sudo tak-gateway-auth create-replay-client-cert tak-map-mobile-server --gateway-url https://<gateway-ip>:9443
```

The Gateway command creates a PKCS#12 bundle. Copy it securely to the TAK Map server and extract PEM files:

```bash
sudo mkdir -p /etc/tak-map
sudo openssl pkcs12 -in tak-map-mobile-server.p12 -clcerts -nokeys -out /etc/tak-map/replay-client.crt
sudo openssl pkcs12 -in tak-map-mobile-server.p12 -nocerts -nodes -out /etc/tak-map/replay-client.key
```

Copy the CA certificate used to verify TAK Gateway HTTPS to:

```text
/etc/tak-map/replay-ca.crt
```

Set `/etc/tak-map.env`:

```bash
TAK_MAP_REPLAY_API_URL=https://<gateway-ip>:9443/api/replay/v1
TAK_MAP_REPLAY_CLIENT_CERT=/etc/tak-map/replay-client.crt
TAK_MAP_REPLAY_CLIENT_KEY=/etc/tak-map/replay-client.key
TAK_MAP_REPLAY_CA_CERT=/etc/tak-map/replay-ca.crt
TAK_MAP_REPLAY_VERIFY_TLS=true
TAK_MAP_REPLAY_TIMEOUT=120
```

Apply permissions and restart:

```bash
sudo chown root:takmap /etc/tak-map/replay-client.crt /etc/tak-map/replay-client.key /etc/tak-map/replay-ca.crt
sudo chmod 0640 /etc/tak-map/replay-client.crt /etc/tak-map/replay-client.key /etc/tak-map/replay-ca.crt
sudo systemctl restart tak-map
```

For temporary lab testing only, `TAK_MAP_REPLAY_VERIFY_TLS=false` disables Gateway server-certificate verification. Client-certificate authentication is still required.

## TAK Map proxy endpoints

Authenticated TAK Map sessions can access:

- `/api/tak-map/replay/config`
- `/api/tak-map/replay/health`
- `/api/tak-map/replay/capabilities`
- `/api/tak-map/replay/periods`
- `/api/tak-map/replay/manifest`
- `/api/tak-map/replay/events`
- `/api/tak-map/replay/chunk`

The first v419 browser integration uses bounded Events API windows for playback. The manifest and chunk proxy endpoints are also present for later worker-based large-period optimization.
