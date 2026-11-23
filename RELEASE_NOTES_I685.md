# TAK Map v1.4.0-i685 — Infrastructure Overlays and sidebar typography

**Baseline:** source-only v1.4.0-i684; all pre-existing Local Data, Token Mesh, routes, NDM, VEIL and offline map storage are unchanged.

## Infrastructure Overlays (first integrated implementation)

- New **INFRASTRUCTURE** sidebar card immediately after Basemap; matching existing sidebar typography, headers, chips and collapsibility.
- 14 shared built-in categories: Electrical Power; Communications; Oil & Natural Gas; Water & Wastewater; Rail Infrastructure; Bridges; Aviation; Maritime & Ports; Industrial Facilities; Emergency Services; Environmental Facilities; Dams & Flood Control; Space & Satellite; Logistics & Distribution. Categories remain visible in both Online and Offline modes even when empty. Users may create/rename custom categories, hide/restore built-ins, add/remove sources and import into a chosen category.
- Explicit **Online / Offline** selector in the card. Online queries provider FeatureServer/MapServer by viewport; Offline reads only indexed local GIS storage. Switching does not reset the shared catalog or change saved map objects. There is no silent network fallback in Offline mode.
- Built-in public candidate online layers: LA County Public Works sewer gravity mains, manholes and force mains; U.S. electric transmission lines. Other categories start empty but can accept user-added public ArcGIS REST sources or imported files. Built-in sources are disabled by default until selected. Coverage and update freshness depend on the provider.
- **Large sewer filtering:** sanitary sewer layers display features with a normalized diameter **at least 36 inches** by default; user can select 48, 60 or all diameters. Unknown sizes are hidden unless All is selected. Raw downloads retain original diameters so filtering can change offline.
- **Downloads:** choose current viewport or a two-corner rectangle; start a server-side download for a selected online layer. Download progress and saved feature counts persist; incomplete jobs support resume, and downloads only become visible offline after complete staging/commit. Existing offline datasets are not replaced by a failed refresh. No TAK Map bandwidth cap is applied. Provider rate limits and transient errors are handled without silently indicating completeness.
- **GIS import/export:** GeoJSON, GeoPackage, Shapefile ZIP, KML and KMZ. GeoPackage is the preferred exchange format. SQLite/RTree spatial indexes store local features independently under `/var/lib/tak-map/infrastructure`. Dataset exports are generated on the server; selected features may be exported to GeoJSON from Object Details.
- **Map interactions:** 2D Leaflet and basic 3D Cesium vectors; hover tooltips; direct **single-click** opening of the existing right-hand Object Details panel; readable category-specific attributes, source/online-offline context, original GIS attributes, zoom/copy coordinates/export actions. Normal Route Creation/Edit click isolation applies.
- **Safety:** authenticated TAK Map endpoints; only public HTTPS GIS service URLs, validated against private/local addresses; redirect rejection; bounded per-request size; untrusted UI text escaped; uploaded GIS geometry validated, persisted separately from all Local Data.

## Sidebar typography regression

- Reconcile legacy i675 late-injected collapsed-card header CSS (font size, family, weight, spacing, line height) with i684 uniform card styles. Reconcile Mesh Sync title/chip/header styling to match other cards when collapsed or expanded.
- Fix installer omission: explicitly install the i684 uniform-sidebar CSS and card-order JS along with new i685 assets.

## Limitations and testing scope

- This first implementation supports **ArcGIS REST feature-layer queries** for Online mode. OGC WFS/API Features providers, automatic source discovery, and state/county preset downloads are not included yet; users can import public datasets from these sources separately.
- Offline selection supports the current viewport or a two-click rectangle rather than administrative-region presets; GeoPackage remains an export format while the local working catalog uses a dedicated spatial SQLite database.
- Large viewport queries report when they reach the display safety threshold; *downloads do not silently truncate by that threshold*. Per-provider throughput is determined by available API pagination and the network; no arbitrary download-rate cap is configured.
- Real public-provider queries and Cesium map behavior require verification on the deployed TAK Map host. Automated tests use controlled GIS features and simulated provider responses. Source licensing and eligibility for redistribution must be checked for each chosen provider.
- Preserve backups of all application data before upgrading. Prior i684 remains the rollback package. No automatic migration or deletion of existing Local Data is performed.
