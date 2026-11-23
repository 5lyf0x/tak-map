# TAK Map v1.4.0-i666 — Release notes

See CHANGELOG.md and README.md for changes and limits.

### VEIL API pairing

Discover or manually add a VEIL node, enable the XTAK VEIL card, and choose **Connect API** on that node. The modal allows API credentials with an opt-in Remember credentials checkbox (OFF by default). Existing nodes added in i665 remain UDP-only and never automatically subscribe. Multi-node discovery adds nodes together without a login-modal cascade.

- The existing VEIL CoT UDP unicast receiver still listens on the configured port (6970 default); pairing does not change VEIL's CoT output configuration.
- Login prompts are allowed only when all four conditions are simultaneously true: card ON; node explicitly API subscribed; verified reachable VEIL API and matching nodeId; confirmed unauthorized access after silent recovery attempts. Network faults never trigger a login prompt.
- Remembering credentials saves them with permissions 0600 under the existing TAK Map VEIL data directory, without hardware-backed encryption. Do not enable this on an untrusted computer. HTTP/WS on LAN are unencrypted; use only trusted networks.
- API state uses a single per-node observation key across UDP/snapshot/WebSocket. Cross-node and other-source dedup remain Phase 3.

### Release safety

The i665 hotfix for accidental `<html>` root `textContent` replacement is embedded in this release. No rollback or configuration/data deletion is part of the installer. Validate the installed map and pairing with your physical nodes after installation; hardware testing was not available in the build environment.
