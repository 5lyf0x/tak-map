# TAK Map i681 — pre-release validation

## Source / functionality
- Base: i680 source archive (unchanged rollback ZIP retained). No saved Local Data files are packaged or modified. The i680 read-only recovery endpoint and i679 complete-route storage remain registered.
- MVUM button: browser harness confirms initial button placement above Undo and restoration with exactly one button and status element after route toolbar DOM replacement.
- Terrain camera: separate Chromium/Cesium mock confirms the ground-center target, terrain height, pitch and 3D-to-2D ground-scale translation, at example latitude 34.5°.
- Live profile: Chromium harness confirms 98 distance-spaced samples on a curved route containing only three route geometry anchors; data come from mocked NDM API, not waypoint elevations. NDM sampling uses full resolved/manual route geometry, batch sizes <=512, missing-data gaps, cancellation/cache and distance/elevation/grade inspection. Saved route profile tested. Bottom padding is 20 px before and after sidebar/map width change.
- 2D/3D camera parity in an actual Cesium terrain session has **not** been verified. The ArcGIS terrain provider and user NDM data are not available to this test environment.

## Automated checks
- 5 inherited i679 long-route persistence tests: PASS (including 50,001 vertices and edit/reopen).
- 2 inherited i679 server startup and legacy-data audit tests: PASS.
- 5 inherited i680 Local Data response recovery tests: PASS.
- 8 inherited MVUM/NDM i673 tests: PASS, after aligning prior version/caching expectations with the current implementation.
- 5 new i681 release invariants: PASS.
- Targeted Chromium browser harness: PASS (MVUM self-healing, live full-route profile, saved-route profile and 20 px anchoring).
- Separate camera conversion mock: PASS.
- Node syntax checks for changed JS, Python AST, Bash `bash -n`: PASS.

## Pre-install cautions
- Preserve `/root/tak-map-recovery-i679/` and keep the existing data directory untouched.
- The NDM elevation API requires a registered terrain package. On no/partial DEM coverage the profile should report missing samples rather than fabricate a profile. Initial terrain cache preparation may take time.
- Camera altitude is terrain-relative where a terrain height can be sampled. 2D has scale rather than true camera AGL; scale equivalence is an approximation.
- No live browser/server validation on the user’s TAK Gateway was possible before release.
