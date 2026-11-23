## 1.4.0-i647

- Removes the normal AIS marker shadow; selected AIS markers alone display a red highlight, while selected ADS-B aircraft show a white highlight in the live map.
- ADS-B Owner / Operator remains visible even when unknown, showing “Not reported”. Preserves additional provider owner/operator names where supplied.
- Retains i646 Gateway Configure, native Shape Save, Replay, ADS-B failover and installed settings/data.

## 1.4.0-i646

- Replaces Gateway AIS civil/law point icons with the approved dark ship silhouette on a mint-green tile, stored as two 64×64 PNG files. AIS markers render at 12×12 pixels on the map; the AIS sidebar icon renders at 20×20.
- Preserves the incoming `Host` header including `:9444` in the Nginx proxy (`$http_host`), fixing the Gateway Configure "Same-origin request required" error without weakening origin checking.
- Retains the i645 Gateway Configure feature and the separate Replay certificate policy; installs over previous TAK Map releases without removing existing state/configuration.

## 1.4.0-i645

Adds administrator-only Gateway Data Configure modal next to Refresh, with connection/TLS/client-auth settings and a Test Connection action; saves persistent Gateway Data overrides without altering Replay or existing user data. Installs and verifies the new runtime module. See `GATEWAY-DATA-CONFIG-MODAL.md`.

## 1.4.0-i644

Gateway Data supports optional client certificates independently of Replay. Replay keeps its existing certificate-authenticated default and all API/payload behavior, with explicit HTTPS-only certificate-free opt-in if TAK Gateway permits it. Prior i643 Shape Save and OTS 1.7.13 behavior are preserved.

## 1.4.0-i643

Validated native Mission Shape Save release. Native `u-d-*` Shape CoT is sent over the authenticated per-user SSL CoT transport, verified through global exact-geometry CoT read-back, associated to existing Missions with `PUT /contents` using the same UID, and then verified through Mission `/cot` GET. Mission `/cot` POST/PUT is explicitly not used.

## 1.4.0-i642

Attempted direct Mission `/cot` Shape update release. Live OpenTAKServer 1.7.13 testing showed POST/PUT Mission `/cot` returns HTTP 405; superseded by i643.

## 1.4.0-i641

Persistent Shape edit session and center-translation release. Added explicit Save/Cancel transaction protection, edit-only center handle, Notes-last layout, larger Save/Cancel labels, and empty-map click protection.

## 1.4.0-i640

Corrective Shape-editor release. One authoritative edit draft now drives the rendered geometry, vector handles, map-side dimensions, computed measurements, and Save payload. Active drafts survive background/Data Sync redraws; Save persists the visible geometry and reports failure without discarding it; Cancel restores the pre-edit snapshot. Close Edit, Category, and Rotation are removed from the panel; Save/Cancel are equal-width; the Shape name uses normal weight.

## 1.4.0-i639

Native Shape editor release: compact field replacement, Center labeling, map-side geometry vectors, dynamic segment dimensions, silver/gray Shape controls, and server-authoritative native TAK CoT geometry updates with UID/Mission preservation.

## 1.4.0-i638

Stable Shape context/sidebar release: no unchanged-selection rerender flicker, explicit Edit button, correct Mission/Data Sync attribution, compact full-width context layout, regional-unit geometry measurements, and runtime-asset install validation.

# 1.4.0-i635

Server-authoritative Data Sync association normalization, per-user persistent card states, and reduced/no-shadow AIS vessel icons.

## 1.4.0-i633

ADS-B visual/cadence correction. The served v320 marker owner and sidebar interpolation now retain the aircraft icon's 0.75 scale on every heading update, removing refresh pulses. Active ADS-B cache reuse is limited to a 0.5-second coalescing window, allowing the configured 5-second worker cadence to issue a fresh upstream request on each normal poll. Existing provider failover, OFF gating, and OTS 1.7.13 behavior are unchanged.

## 1.4.0-i632

Corrective ADS-B runtime release. i631 added the backend provider failover/lease gate, but its deferred manifest still embedded the older ADS-B worker, so normal live polls omitted `active=1` and `client_id` and were treated as cache-only. i632 synchronizes the deferred manifest with the corrected worker and adds browser-level lease regression coverage. All i631 provider rules and i630 OpenTAKServer 1.7.13 automation are preserved.

## 1.4.0-i631

TAK Map i631 adds transparent backend ADS-B provider failover. airplanes.live remains primary; ADSB.lol is used only when the primary is unavailable. Primary recovery is retried every 10 minutes while ADS-B remains enabled. ADS-B OFF is a hard upstream-network gate, including revocation of the browser activity lease before any follow-on fallback can start. No provider-specific interface is exposed. i630 OpenTAKServer 1.7.13 automation is preserved.

## 1.4.0-i630

- Adds a first-class Configure OTS preflight for OpenTAKServer 1.7.13 deployments.
- Uses `10.10.10.2` as this build's deployment default while retaining an environment override.
- Automatically handles DNS-only certificate identities for IP-entered OTS servers by maintaining a bounded certificate-backed hostname mapping in `/etc/hosts`; strict CA and hostname verification remain enabled, and unrelated host entries are never rewritten.
- Automatically retries encrypted OTS truststore extraction with the installer-provided truststore-password fallback when no password was supplied, without persisting that password in TAK Map's OTS connection JSON.
- Verifies Web/API, trust, Marti HTTPS, enrollment, SSL CoT, administrator identity, per-user certificate enrollment, and client-certificate Marti HTTPS before enabling OTS login.
- Separates successful OTS login authentication from Data Sync certificate availability so a certificate provisioning fault does not lock a valid OTS user out of TAK Map.
- Preserves all i629 ADS-B emergency rendering and i628 Replay maintenance behavior.

## 1.4.0-i629

- Preserves ADS-B emergency status visually in both Live Map and Replay.
- Uses dedicated red emergency aircraft assets while preserving the existing civilian/government/military shape classification.
- Replay carries Gateway `emergency=true` and `#FF0000` CoT styling into the normalized aircraft state and forces icon refresh across normal/emergency transitions.
- Adds `Emergency: YES` to Replay aircraft details and retains existing CoT stale behavior.
- Preserves i628 maintenance-aware Jump recovery and the protected i602 Data Sync baseline.

## 1.4.0-i628

- Coordinates with TAK Gateway i196 to keep Replay Recorded Periods usable while Search/state checkpoints rebuild independently.
- Shows `Replay state index preparing…` as a retryable Jump state rather than a fatal error.
- Refreshes and safely remaps a stale selected recording ID once after Gateway maintenance, then retries the state-at-time request with the canonical ID.
- Never silently crosses into a different recording.

## 1.4.0-i627

Replay state proxy correction. TAK Map now forwards `/api/tak-map/replay/state` to TAK Gateway i195 instead of rejecting the endpoint locally. Preserves the i626 checkpoint/state-at-time long-jump architecture and transport lock.

## 1.4.0-i626

Replay checkpoint/state-at-time scalability correction. Long-distance Search and Jump seeks use TAK Gateway i195 persistent state checkpoints, transport is locked while seeking, target time is committed atomically, and multi-day period labels show both dates.

## 1.4.0-i625

Replay absolute-seek/state reconstruction correction. Search and Jump now share one serialized whole-state seek path, preserve the existing map while reconstructing, and use the real period end so Play resumes after Jump. Requires TAK Gateway i194.

## 1.4.0-i624

Replay Mode now includes a precise Jump to Date / Time interface below Recorded Period. It supports seconds, +/-1 minute stepping, period-bound validation, timeline/search synchronization, and out-of-buffer state reconstruction without resuming playback.

## 1.4.0-i623

Replay Search now uses TAK Gateway i194 stable period identities and remains valid when a selected recording grows or its indexed end boundary is reconciled. Legacy i193-style period IDs remain compatible.

## 1.4.0-i622

- Corrects the i621 packaging/finalization defect that removed Replay/Search from the final browser HTML.
- Adds final-served-HTML and browser-DOM release gates for Replay Search delivery and visibility.
- Added whole-recording Replay Search backed by TAK Gateway's persistent Replay identity index.
- Search scope: ADS-B flight/callsign, ICAO/hex, registration, owner/operator, aircraft type/model, EUD callsign/UID, vessel name, and AIS callsign.
- Search works beyond the currently buffered timeline and can target-load, seek, center, highlight, and open the matching Replay object.
- Added previous/next indexed appearance navigation without automatically enabling Track or Follow.

## 1.4.0-i620

- Corrective 1.4.0 package with authoritative sidebar identity: `1.4.0` / `i620`.
- First-frame server rendering plus a mutation guard prevents version/iteration flicker from delayed legacy startup hooks.
- NIFC Fire Perimeter context panels now select the narrowest practical width for their visible content and expand only when required.
- Other context panels retain the validated i618 sizing behavior.

## 1.4.0-i618

- Public 1.4.0 version and i618 iteration.
- Shared content-aware context-panel sizing for ADS-B, Local Data, Data Sync, Gateway Data, and Source Extensions.
- Responsive panel bounds, stable themed scrollbar gutter, no horizontal scrolling, and independent dual-panel collision avoidance.
- Preserves the validated i617 Gateway Data curation, i613 Source Extension drawing suppression, i612 deferred runtime, i610 ADS-B, and protected i602 Data Sync behavior.

## 1.3.0-i602

- Finalizes Data Sync deletion identity after authoritative Mission reconciliation.
- Uses exact Mission name plus CoT event UID for deletion and never discovery/content UUIDs.
- Preserves the deletion identity through membership-only generations and existing last-known-good behavior.
- Retains all i601 continuity and i600 performance corrections without unrelated UI changes.

## 1.3.0-i601

- Separates Mission discovery/content UUIDs from CoT event UIDs.
- Carries the complete last authoritative `/cot` object set through membership-only generations without discovery-UID filtering.
- Treats a discovery UID fingerprint change only as a trigger for an immediate full `/cot` refresh.
- Adds a regression using different discovery content UUIDs and CoT event UIDs.
- Retains the i600 performance fast path and all existing Data Sync/UI behavior.

## 1.3.0-i600

- Preserves completed per-Mission `/cot` objects and authority through membership-only generations.
- Treats only an actual successful empty `/cot` response as authoritative empty Mission content.
- Retains the established 10-second membership and 20-second CoT cadence with immediate refresh on unlock, manual refresh, or membership change.
- Removes redundant legacy PostgreSQL acquisition from the Data Sync critical path while retaining compatibility finalization for UID, geometry, symbology, custom icons, tombstones, packages, topology, and security.
- Refreshes optional Mission-scoped PostgreSQL supplemental metadata independently with bounded queries.
- Adds recursive-property cleanup, snapshot invariant validation, and stage timing diagnostics.
- Makes no unrelated Data Sync UI changes.

## 1.3.0-i599

- Replaces the overlapping Data Sync worker/reconciliation paths with one authoritative per-Mission pipeline.
- Reuses validated protected-Mission tokens and performs exactly one authorized `/cot` request per due unlocked Mission.
- Runs Mission discovery/membership every 10 seconds and full CoT enrichment every 20 seconds, with immediate CoT acquisition for newly discovered UIDs.
- Uses `/cot` events as authoritative membership when discovery omits `uids`, preserves per-Mission last-known-good map objects on failure, and treats successful empty results as authoritative.
- Uses discovery-embedded Mission contents/packages, makes no redundant GET `/contents` request, and prunes deleted Missions and removed UIDs.
- Makes security filtering read-only and publishes explicit generation, worker, and per-Mission content states.
- Uses one browser polling owner, preserves completed objects during transitional responses, and keeps status chips limited to Locked/Unlocked.

## 1.3.0-i598

- Preserves authorized Mission `/cot` XML when an empty parsed JSON object is also present.
- Parses top-level `<event>` and `<events>` XML responses into the existing Data Sync Mission-object pipeline.
- Leaves the Data Sync UI unchanged apart from the required i598 package iteration.

## 1.3.0-i597

- Limits the protected-Mission status chip text to **Locked** or **Unlocked**.
- Leaves the existing Mission refresh message and all other UI behavior unchanged.

## 1.3.0-i596

- Promotes Mission access state after the final Data Sync security filter.
- Uses the first nonempty Mission-access array and reconstructs Mission rows during post-password transitional refreshes.
- Keeps unlocked Missions visible while authorized contents are refreshing.

## 1.3.0-i595

- Preserves complete protected-Mission discovery `uids` and `contents` after successful password validation when the authorized detail endpoint omits them.
- Releases authorized Mission objects through Data Sync while retaining the locked metadata-only security boundary.

## TAK Map 1.3.0-i594

- Protected OpenTAKServer Mission names are discoverable before password entry.
- Locked Missions show Edit controls using the discovered Mission name.
- Protected Mission contents remain unavailable until password validation succeeds.
- Multiple locked Missions and mixed locked/unlocked Missions are supported.
- The i592 themed unenrollment dialog and all prior fixes remain included.
