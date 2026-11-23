# HTTPS Cert Setup UI — next iteration staging

The existing i649 account-header cleanup removed the earlier Cert Setup button and modal. A new dedicated JS runtime asset restores a visible Cert Setup button beside Account.

## Behavior
- Show CA/server status and CA SHA-256 fingerprint from authenticated `GET /api/tak-map/cert-setup/status`.
- Download existing CA through the already supported `/ca-cert.crt` route.
- Do not generate or reissue certificates on opening or refreshing the modal.
- Advanced regeneration is admin-only, requires same-origin POST to `/api/tak-map/cert-setup/generate`, JSON body, and a typed confirmation matched to CA presence.
- Retire the old `POST /api/cert-setup` to eliminate the unaudited bypass.
- Installer deploys the new runtime asset and verifies that the backend serves it.

## Trust
Windows users should compare the downloaded CA certificate SHA-256 fingerprint to the trusted server-side fingerprint before adding it to Trusted Root Certification Authorities. Server certificates also require SAN coverage of the actual access IP/DNS name. Regeneration may require re-trusting the new CA on clients.

## Validation
Focused Chromium and backend tests under scripts/test_cert_setup_i650_browser.py and scripts/test_cert_setup_i650_backend.py. No certificate is regenerated during tests.
