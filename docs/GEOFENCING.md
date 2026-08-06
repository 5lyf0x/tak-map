# TAK Map Geofencing

## i499 route geometry correction

Route geofences use the route's complete polyline. Any route-center `lat/lon` stored for popup placement or map centering is ignored as geofence geometry, and at least two valid route points are required. Shape and route popups retain the i498 in-place Edit interaction and padded Edit + Geofence action row.

TAK Map i499 provides persistent geofencing to canonical Local Data and Data Sync shapes and routes.

## Create a geofence

1. Create or import a circle, rectangle, polygon, or route.
2. Open its TAK Map information popup and select **Geofence**.
3. Enter a name and select monitored object classes.
4. For an area, select Enter, Exit, Dwell, or any supported combination. Dwell duration is set in minutes. For a route, Cross is enabled.
5. Optionally configure ADS-B minimum altitude, maximum altitude, or an altitude band.
6. Select **Save & Activate**.

All controls use TAK Map-themed dialogs. Geofences can be created while recording is active.

## Monitoring and alerts

Supported sources are EUDs/TAK users, ADS-B aircraft, Local Data, Data Sync, Gateway Data, and Satellite objects. A confirmed event produces a pulsing red glow, an alert sound, and an entry in the movable lower-right Geofence Alerts window. The window is created only after the first geofence exists and disappears again when the final geofence is removed. It starts above the scale control, uses dense trigger chips, minimizes with a minus button, restores with a plus button, and preserves its dragged position for the browser session. Top and bottom resize grips adjust height only while keeping the width fixed; the chosen height is also preserved for the session.

Boundary changes require two seconds of confirmation. An object is rearmed after ten seconds, with one event per confirmed crossing. Stale source data cannot generate a new crossing or a false Exit; the prior inside/outside state is retained until fresh data returns.

## Management and protection

The Geofences sidebar card is positioned directly between Basemap and ADS-B and shows active and total counts, All/Area/Route filters, Armed or Paused state, and Center/Edit/Pause or Enable actions. Event history is kept only in the floating alert window.

A shape or route referenced by a geofence is protected from Local Data and Data Sync/Mission API deletion. Remove the geofence first to delete the underlying object. No Duplicate action is provided.

## Popup behavior

Shape and route popups pin on the first click. The normal read-only popup contains one **Edit** and one **Geofence / Edit Geofence** action. Selecting **Edit** changes the existing displayed rows in place to editable fields and presents **Save**, **Cancel**, and **Delete**; no collapsing `<details>` editor is rendered or stored. Cancel restores the read-only rows without reopening the popup. Hover popups remain open while the pointer is over the object or popup, and route hit lines no longer share popup ownership with the visible route line.
