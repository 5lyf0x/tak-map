# TAK Map v1.4.0-i669 — Release Notes

Source baseline: v1.4.0-i668 (untouched rollback ZIP retained).

## Fixes and features
- VEIL LAN discovery uses POST, modal Select All/Clear All styled, and authenticated TAK Map administrator role accepted on secure HTTPS without a second Dashboard session.
- VEIL card is anchored immediately after BASEMAP without repeatedly moving GEOFENCES.
- VEIL ADS-B A3 segmented ring, using built-in category colors: military blue, civilian green, government purple, unknown yellow. The ring stays stationary while the aircraft glyph rotates clockwise with its reported heading; no fictitious heading is inferred.
- VEIL ADS-B marker clicks open the existing TAK Map ADS-B details panel through an external-data bridge; the live observation remains attributed to VEIL. Other source types retain their own detail content.
- VEIL 2D and Cesium 3D renderers use the same icon glyphs for aircraft, AIS, APRS, and Remote ID. Airborne targets use a validated reported CoT/Live-SA WGS84 HAE altitude when available; pressure altitude alone is not silently converted to ellipsoid height. Ground targets clamp to streamed terrain or sample local DEM when available.
- Range Rings toolbar button inserted between Pan and Coordinates, with equally spaced transparent light-gray ring icon. Independent geodesic sets with name/center label, interval units (m/ft/km/mi/nmi), count, color, width, opacity, solid/dashed, distance labels, per-set Remember after reload. Toolbar creates; click ONLY center to edit; Clear Rings removes only that set.
- Range Rings render in Leaflet and Cesium, using streamed terrain clamp or local DEM elevations where available, with one center marker/name and independent ring radii.
- Release metadata, runtime scripts and deferred ADS-B sidebar module cache updated to i669. Fatal i665 destructive root DOM selector remains guarded.

## Important limitations and validation status
- Live VEIL hardware, physical ADS-B and local DEM Cesium rendering require end-to-end verification on the target Raspberry Pi; synthetic tests cannot prove radio source compatibility, icon classification enrichment quality, or precise barometric-to-HAE conversion.
- When VEIL observations lack a trustworthy altitude reference, renderers do not invent an airborne height. Check details for altitude availability.
- Range Rings are accurate geodesic ground-projection radii; terrain-draped arc distances are not surface walked distances. In local DEM areas missing elevation samples, Cesium falls back to globe terrain clamp and may not match missing mesh detail.
- Range Rings persistence is in browser localStorage on this device; it does not automatically sync across browsers/Mesh.
- Cross-source deduplication remains optional and OFF by default. Phase 2 API sync and Phase 3 health continue unchanged.
- Installation preserves application data, certificates, and existing configuration.
