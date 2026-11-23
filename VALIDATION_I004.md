# TAK Map v1.5.0-i004 — Full Source Validation

**Baseline:** original `tak-map-v1.5.0-i003.zip`, SHA-256 `81d33a4e847c0e92d741e8ba1c1399325b7c47260ad17c531b744d4809c1d279`; preserved unchanged.

## Completed offline and installer checks

- Installer fix patch applies to unmodified i003 `install.sh` with zero fuzz.
- Sandbox replay of the real `install -m 0644` helper line installs identical source bytes, with mode 0644, before backend copy/restart; the installed module imports successfully.
- Source Python AST and Bash installer syntax passed.
- Inherited i001 backend catalog/rename/send/101-record protections and Chromium Rename, sorting, 600px list and footer checks passed.
- Inherited i002 automatic map-list startup and duplicate Rename-control prevention passed.
- Inherited i003 tile HTTP, TMS/XYZ, cache behavior, resume, authenticated routes, 160-request threaded pool, imported selector and browser pan/zoom checks passed.
- Inherited i698 offline downloader backend and Chromium UI regressions passed.
- Inherited i699 Offline Maps card/source-dropdown Chromium regressions passed.
- Current app config and HTML release/iteration both report `1.5.0-i004`.

## Package handoff

- Root-flat source ZIP: extract into a new `tak-map-v1.5.0-i004` folder.
- No Android build outputs or private credentials added; no production files or stored `/var/lib/tak-map` data mutated.
- SHA256SUMS contains every packaged source file except SHA256SUMS itself.
- Archive CRC, checksum verification, source/extraction parity and executable installer mode verified separately in handoff report.
- Not tested on the user's running TAK Map host; the standalone OpenTAKServer 10.10.10.2 warnings are not addressed by this update.
