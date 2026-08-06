# TAK Map i594 configuration

## Protected Mission access

TAK Map discovers Mission names from the authenticated OpenTAKServer Mission list and shows them in the Data Sync card before a Mission password is entered. A protected Mission appears as **Locked** with an **Edit** button.

Selecting **Edit** opens the Mission Password dialog with the Mission name already selected. The operator enters only the password. Mission contents, objects, files, packages, UIDs, logs, and roles remain hidden until OpenTAKServer validates the password for that Mission and authenticated user.

## Configure OTS unenrollment

The Configure OTS panel uses a TAK Map dark-grey and silver confirmation dialog for complete server unenrollment. The dialog is centered in the viewport and enables its final action only after the operator types the exact text `UNENROLL`.

## Context panel sizing in 1.4.0 i618

No operator setting is required. TAK Map automatically sizes ADS-B, Local Data, Data Sync, Gateway Data, and Source Extension context panels from their visible content. The shared policy reserves the themed scrollbar gutter, prevents horizontal scrolling, and constrains simultaneous panels to the available map viewport.
