## 1.4.0-i621

- Adds prioritized backend ADS-B failover: Airplanes.live, ADSB.lol, ADSB.fi.
- Provider cooldowns and automatic recovery without changing aircraft UI, trails, or filtering.
- Keeps last-good aircraft snapshots through provider outages; empty successful results do not fail over.
- Advances the runtime and distribution version identity to 1.4.0-i621.
- Preserves all i620 sidebar identity and NIFC panel fixes.

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
