# TAK Map v1.4.0-i674 — Selective Backup/Restore

This release replaces Tools > Export All Data with Tools > Backup/Restore and adds a password-encrypted TAK Map-owned backup format (`.takmbk`) for thirteen separately selectable categories.

Categories: points, shapes, routes, custom basemaps, XTAK VEIL nodes and local credentials, geofences, ADS-B settings, Gateway Data client settings and keys, Mesh Sync settings/keys/journal, Data Sync local settings/journal, local data, offline maps, satellite tracking settings.

A browser snapshot accompanies server-stored data: scoped TAK Map localStorage keys and recognized local IndexedDB databases. Large browser-only IndexedDB exports over 28 MiB fail explicitly instead of silently omitting data; server-backed offline packages are not subject to that inline limit. An archive contains TAK Map data only, not TAK Gateway/NDM server data.

Passwords are not persisted. The private backup format uses scrypt key derivation, per-chunk AES-256-GCM, a ZIP manifest and per-file SHA-256 verification. Administrator TAK Map login, same-origin requests and HTTPS are required. Selected restore categories are validated, backed up temporarily and applied without modifying nonselected categories. Mesh/Data Sync journal restore uses an explicitly confirmed maintenance job: the archive is verified before scheduling, the TAK Map service is stopped, the selected journal files are restored, and the service is restarted automatically. Peer revision conflicts are not resolved by a local restore and must be reconciled before enabling synchronization.

Restore credentials are preserved but third-party service endpoint changes, expired/invalid certificates and remotes remain external constraints. Preflight tested against synthetic fixtures; live end-to-end Gateway/VEIL/NDM dependencies were not available.

The prior i673 source archive is preserved unchanged.
