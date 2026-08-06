# Context panels

TAK Map 1.4.0 i618 uses a single content-aware sizing policy for contextual object panels.

## Covered panels

- ADS-B aircraft
- Local Data points, routes, and shapes
- Data Sync objects
- Built-in Gateway Data
- Dynamic TAK Gateway Source Extensions

## Width behavior

The panel measures its visible title, labels, values, and controls and chooses the narrowest practical width that avoids excessive wrapping. Compact records remain compact. Long fields may expand the panel up to the responsive desktop maximum. On narrow screens, the panel is capped to the available viewport.

Horizontal scrolling is never used. Long source values wrap normally.

## Scrolling

The header remains fixed while the body scrolls. TAK Map reserves the scrollbar gutter even before scrolling is required, preventing row and header alignment from shifting when content grows. The scrollbar uses the TAK Map dark track and muted blue-gray thumb.

## Multiple panels

Pinned ADS-B panels retain their established bottom-left and bottom-right placement. When an ADS-B panel and another context panel are open together, each width is calculated independently and constrained to prevent overlap or clipping.

## Layer order

Context panels appear above ordinary map controls and toolbars. Account, configuration, save, and other true modal dialogs remain above context panels.
