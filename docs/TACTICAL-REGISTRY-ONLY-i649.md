# i649 Tactical markers — registry-only rendering (staged, not packaged)

- All tactical CoT/SIDC symbols render from the shipped MIL-STD-2525C catalog (`/mil2525/svg/`).
- Retired the built-in inline frame/X and synthetic missing-usericon placeholders.
- Unknown tactical symbol subtypes fall back to a registered generic symbol matching affiliation/domain.
- Gateway AIS retains the 48px tactical symbol path; it does not switch to native AIS PNGs while the catalog loads.
- Gateway tactical markers refresh once the catalog becomes ready.
- Tactical CoT/SIDC objects use the MIL-STD-2525C catalog even if custom or stale iconset metadata is present. Explicitly non-tactical custom usericons, weather/fire symbols, route/shape controls, and source-specific device badges retain their separate visuals.
- No i649 ZIP is created by this staging change.
