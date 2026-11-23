# TAK Map → TAK Gateway optional client certificates (Gateway i210+)

Gateway Data and Replay are independent read-only connections. The browser
never receives API private keys, and both proxies retain TAK Map's existing
logged-in-session gate. These options do not modify TAK Map's connection to
OpenTAKServer, its Data Sync, or its secure CoT/mission credentials.

TAK Map's operator settings live in `/etc/tak-map.env` and are retained on
normal in-place upgrades.

## Gateway Data — trusted LAN with no certificates

```text
TAK_MAP_GATEWAY_DATA_API_URL=http://10.10.10.101:8090/api/external-sources/v1
TAK_MAP_GATEWAY_DATA_AUTH_MODE=none
```

No client or server certificate is used; HTTP is **unencrypted** and should
only be used on a trusted private LAN/VPN. Gateway Configure Security must
permit certificate-free Gateway Data on the Map host's source address.

## Gateway Data — HTTPS, no client certificate

```text
TAK_MAP_GATEWAY_DATA_API_URL=https://10.10.10.101:9443/api/external-sources/v1
TAK_MAP_GATEWAY_DATA_AUTH_MODE=none
TAK_MAP_GATEWAY_DATA_CA_CERT=/etc/tak-map/replay-ca.crt
TAK_MAP_GATEWAY_DATA_VERIFY_TLS=true
```

HTTPS uses a **server certificate** for encryption and server identity. No
client certificate is presented. Provide the Gateway CA when Gateway's HTTPS
certificate is not trusted by the host's normal system trust store. Gateway's
policy and trusted-LAN/VPN check still apply.

## Gateway Data — certificate-authenticated HTTPS

```text
TAK_MAP_GATEWAY_DATA_API_URL=https://10.10.10.101:9443/api/external-sources/v1
TAK_MAP_GATEWAY_DATA_AUTH_MODE=certificate
TAK_MAP_GATEWAY_DATA_CLIENT_CERT=/etc/tak-map/replay-client.crt
TAK_MAP_GATEWAY_DATA_CLIENT_KEY=/etc/tak-map/replay-client.key
TAK_MAP_GATEWAY_DATA_CA_CERT=/etc/tak-map/replay-ca.crt
TAK_MAP_GATEWAY_DATA_VERIFY_TLS=true
```

The Gateway Data certificate/key variables default to the existing Replay
certificate/key paths for compatibility. In `auto` mode (default), an existing
complete client keypair continues to use certificates; if neither exists,
Gateway Data uses no client certificate. A partial or broken prior enrollment
fails closed until corrected or deliberately set to `none`.

Do not use an HTTP URL with `AUTH_MODE=certificate`. TAK Map will reject it.
No fallback from certificate-authenticated HTTPS to unencrypted HTTP occurs.

## Replay API

Replay uses a separate setting, `TAK_MAP_REPLAY_AUTH_MODE`, default
`certificate`. Set `none` only when Gateway's Replay policy explicitly permits
certificate-free reads from the TAK Map host. Replay always requires HTTPS and
server identity verification in certificate-free mode; see `REPLAY-MODE.md`.

Changing Replay authentication does **not** change Replay period discovery,
manifest, events, raw gzip chunk streaming, full-history search, state at time,
seek, playback controls, tombstones, or live/replay switching. The existing
TAK Map browser-session login requirement remains in both modes.

Authenticated status endpoints:
- `/api/tak-map/gateway-data/config`
- `/api/tak-map/replay/config`

To apply operator settings, restart the TAK Map service normally. Use the
existing Gateway enrollment assistant when you want to install certificates;
that assistant explicitly selects certificate-authenticated mode for both
Replay and Gateway Data.
