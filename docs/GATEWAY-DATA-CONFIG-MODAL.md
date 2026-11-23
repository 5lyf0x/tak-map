# Gateway Data Configure modal (TAK Map v1.4.0-i645)

The **Gateway Data** card has a new **Configure** button immediately beside **Refresh**.
A TAK Map administrator can enter the Gateway hostname/IP, protocol, port, and
client authentication mode (`none`, `auto`, `certificate`), plus optional
server CA and client certificate/key paths on the TAK Map host.

- Use `HTTP`, port `8090`, and **No client certificate** only over a private
  trusted LAN or VPN. No TLS or client certificate is used.
- Use `HTTPS`, port `9443`, and **No client certificate** when the Gateway
  permits certificate-free reads and its TLS server identity can be verified.
  Specify a trusted Gateway CA certificate path if necessary.
- **Require client certificate** uses HTTPS and certificate/key files already
  present on the TAK Map host. No credentials or certificate files go to the
  browser; the modal handles *paths only*.
- **Automatic** preserves the i644 prior-enrollment behavior. A broken
  enrollment fails closed; certificate mode never downgrades to HTTP.

**Test Connection** probes the Gateway Data `health` and `capabilities` API
through the TAK Map server without saving any changes. **Save** writes
`/var/lib/tak-map/gateway_data_connection.json` (or the configured
`TAK_DASHBOARD_DATA_DIR`) atomically with mode `0600`, and reloads the page
to request a fresh Gateway Data snapshot. Browser settings do not modify the
Gateway host's security policy. Configure Security in TAK Gateway must permit
the specified authentication mode and host/network.

The saved override takes precedence over `/etc/tak-map.env` only for Gateway
Data. The Replay API continues to read its existing certificate and HTTPS
settings unchanged. The existing i644 release and rollback remain untouched;
this functionality is part of the i645 source release.
