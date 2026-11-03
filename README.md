# TAK Map v1.4.0 i621
## Features

- **Interactive Tactical Map** – Browser-based mapping with real-time positioning, object tracking, and multiple basemap options.
- **Map Toolbar** – Quick access to coordinates, measurements, point placement, drawing tools, routes, viewshed analysis, 3D terrain, and map navigation.
- **Coordinate Tools** – Inspect, copy, navigate to, and save geographic coordinates.
- **Distance Measurement** – Measure multi-point distances with selectable units.
- **Drawing Tools** – Create and edit points, lines, squares, rectangles, circles, ellipses, polygons, and freehand shapes.
- **Route Planning** – Create, edit, and manage multi-point routes with customizable styles and metadata.
- **Viewshed Analysis** – Perform terrain visibility analysis with configurable observer height, radius, elevation sources, and overlay settings.
- **3D Terrain Visualization** – Explore terrain in 3D with adjustable camera angles, elevation, and terrain quality.
- **Geofencing** – Create geographic boundaries with entry, exit, dwell, and route-crossing alerts.
- **ADS-B Aircraft Tracking** – Monitor aircraft positions, headings, identifiers, movement trails, and aircraft details.
- **ADS-B Automatic Provider Failover** – Retrieves live aircraft data in priority order: Airplanes.live → ADSB.lol → ADSB.fi, with automatic recovery, provider cooldowns, and last-known-good aircraft retention. No TAK Gateway or OpenTAKServer required.
- **Aircraft Follow & Pin** – Follow aircraft and display persistent aircraft information panels.
- **ADS-B Filtering** – Configure aircraft monitoring radius, geographic center, and update frequency.
- **MIL-STD-2525C Symbology** – Support standardized military tactical symbols for map objects.
- **Local Data Management** – Create, edit, organize, and manage local points, routes, and shapes.
- **Geographic File Import/Export** – Support GPX, KML/KMZ, GeoJSON, and shapefile data.
- **Multiple Basemaps** – Access Esri, USGS, topographic, street, satellite imagery, and shaded-relief map sources.
- **Custom Basemaps** – Import and manage additional map sources.
- **Offline Mapping** – Download geographic areas for offline use with configurable zoom levels and MBTiles support.
- **Satellite Imagery** – Access Landsat 8, Sentinel-2, and NASA VIIRS imagery with date-based comparisons.
- **Satellite Tracking** – Display orbital satellite positions, ground tracks, categories, and CelesTrak data.
- **Contextual Information Panels** – Display detailed object information, metadata, and available actions in expandable panels.
- **Searchable Interface** – Navigate map data and tools using a searchable sidebar and collapsible panels.
- **Authentication & Access Control** – Local account authentication, password management, and protected account workflows.

- **TAK Server / OpenTAKServer Integration** – Requires a configured and accessible TAK server for connected functionality.
  - **Live TAK Tracking** – Display connected TAK users, End User Devices (EUDs), GPS positions, and Cursor on Target (CoT) objects.
  - **Mission Data Sync (OpenTAKServer)** – Discover, access, and synchronize OpenTAKServer missions, objects, routes, shapes, and files.
  - **Protected Missions (OpenTAKServer)** – Access password-protected missions.
  - **Mission Object Management (OpenTAKServer)** – Manage synchronized mission content and refresh shared data.
  - **Basemap Distribution** – Send supported basemaps to connected EUDs.
  - **Connection Monitoring** – Display TAK Server connectivity and connected EUD status.
  - **OpenTAKServer Unenrollment** – Protected server unenrollment workflow.

- **TAK Gateway Integration** – Requires a separately deployed and configured TAK Gateway instance.
  - **Earthquake Monitoring** – Display USGS earthquake events with magnitude, location, and depth information.
  - **Weather Alerts** – Visualize National Weather Service alerts and affected geographic areas.
  - **Wildfire Monitoring** – Display NIFC wildfire perimeters and NASA FIRMS satellite fire detections.
  - **Tropical Storm Tracking** – Display NOAA National Hurricane Center tropical cyclone information.
  - **AIS Maritime Tracking** – Monitor supported maritime vessel positions and associated information.
  - **Dynamic Data Sources** – Automatically discover supported TAK Gateway source extensions with individual enable/disable controls.
  - **Historical Replay** – Review recorded TAK Gateway activity with object tracking and historical playback.
  - **External Sensor Integration** – Display supported geographic and sensor data supplied by TAK Gateway.
  - **Gateway Data Controls** – Independently enable, disable, and manage available external data feeds.
  - **Gateway Status Monitoring** – Monitor connected external data sources and sensor availability.
## Install

```bash
cd ~/Downloads
unzip -o tak-map-v1.4.0-i621.zip
cd ~/Downloads/tak-map-v1.4.0-i621
chmod +x install.sh
sudo ./install.sh
cd ~/Downloads
```

After installation, close and reopen TAK Map and hard-refresh the page.

See `docs/CONTEXT-PANELS.md` for the shared sizing and scrollbar behavior.
