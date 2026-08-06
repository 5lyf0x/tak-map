# TAK Map i578 icon resolver shadow audit

## Scope and method

- Compared all 872 reviewed SIDC aliases and 948 reviewed CoT-type aliases in `assets/mil2525/atak-compatibility-aliases-i553.json` against the 1,448 canonical icon rows in `assets/mil2525/icons.json`.
- Flagged only cases where an exact canonical SIDC exists but the i553 reviewed alias selects a different icon name.
- Compared the actual SVG bytes for every canonical/alias pair.
- Confirmed the standalone i553 resolver and the active deferred-manifest copy are byte-identical.

## Summary

- Exact SIDC aliases shadowing a different canonical icon: **92**
- Exact CoT-type aliases producing the same conflict: **92**
- Unique semantic icon families affected: **23**
- Affiliations affected: **friendly, hostile, neutral, unknown**
- Canonical/alias SVG pairs that are actually byte-identical: **0 of 92**
- Standalone/deferred resolver parity: **True**

The conflict is active because `resolveBySidc()` checks `REVIEWED_ALIASES_I553.by_sidc[sidc]` before `canonicalFileForSidc(sidc)`, and `resolveByCotType()` checks its alias table before converting to and resolving the canonical SIDC.

## Affected semantic families

| # | Exact canonical icon | Alias-selected icon | Example friendly SIDC / CoT | Alias classification |
|---:|---|---|---|---|
| 1 | `air-drone-fixed-wing` | `air-high-altitude-uav` | `SFAPMFQ--------` / `a-f-a-m-f-q` | `review-candidate`; `closest-standard` |
| 2 | `air-drone-rotary-wing` | `air-hexacopter` | `SFAPMHQ--------` / `a-f-a-m-h-q` | `review-candidate`; `closest-standard` |
| 3 | `ground-equipment-civilian-automobile` | `ground-equipment-sedan` | `SFGPEVCA-------` / `a-f-g-e-v-c-a` | `review-candidate-prefix-identical-artwork`; `exact-standard` |
| 4 | `ground-equipment-civilian-large-bus` | `ground-equipment-school-bus` | `SFGPEVCMH------` / `a-f-g-e-v-c-m-h` | `review-candidate`; `closest-standard` |
| 5 | `ground-equipment-civilian-large-open-bed-truck` | `ground-equipment-pickup-heavy` | `SFGPEVCOH------` / `a-f-g-e-v-c-o-h` | `review-candidate`; `closest-standard` |
| 6 | `ground-equipment-civilian-pickup` | `ground-equipment-pickup` | `SFGPEVCOL------` / `a-f-g-e-v-c-o-l` | `review-candidate`; `exact-standard` |
| 7 | `ground-equipment-civilian-sedan` | `ground-equipment-sedan` | `SFGPEVCAH------` / `a-f-g-e-v-c-a-h` | `review-candidate`; `exact-standard` |
| 8 | `ground-equipment-civilian-small-open-bed-truck` | `ground-equipment-pickup-light` | `SFGPEVCOM------` / `a-f-g-e-v-c-o-m` | `review-candidate`; `closest-standard` |
| 9 | `ground-equipment-civilian-suv` | `ground-equipment-suv` | `SFGPEVCUL------` / `a-f-g-e-v-c-u-l` | `review-candidate`; `exact-standard` |
| 10 | `ground-equipment-civilian-utility-vehicle` | `ground-equipment-suv` | `SFGPEVCU-------` / `a-f-g-e-v-c-u` | `review-candidate-prefix-identical-artwork`; `exact-standard` |
| 11 | `ground-equipment-civilian-van` | `ground-equipment-minivan` | `SFGPEVCML------` / `a-f-g-e-v-c-m-l` | `review-candidate`; `closest-standard` |
| 12 | `ground-equipment-radar` | `ground-equipment-radar-vehicle` | `SFGPESR--------` / `a-f-g-e-s-r` | `review-candidate`; `closest-standard` |
| 13 | `ground-equipment-sensor` | `ground-equipment-radar-vehicle` | `SFGPES---------` / `a-f-g-e-s` | `review-candidate-prefix-identical-artwork`; `closest-standard` |
| 14 | `ground-equipment-utility-vehicle` | `ground-equipment-utility-truck` | `SFGPEVU--------` / `a-f-g-e-v-u` | `review-candidate`; `closest-standard` |
| 15 | `ground-unit-anti-armor` | `ground-unit-tank-destroyer` | `SFGPUCAA-------` / `a-f-g-u-c-a-a` | `review-candidate`; `closest-standard` |
| 16 | `ground-unit-armor` | `ground-unit-tank-destroyer` | `SFGPUCA--------` / `a-f-g-u-c-a` | `review-candidate-prefix-identical-artwork`; `closest-standard` |
| 17 | `ground-unit-field-artillery` | `ground-unit-artillery` | `SFGPUCF--------` / `a-f-g-u-c-f` | `review-candidate`; `exact-standard` |
| 18 | `ground-unit-infantry-light` | `ground-unit-light-infantry` | `SFGPUCIL-------` / `a-f-g-u-c-i-l` | `review-candidate`; `exact-standard` |
| 19 | `ground-unit-infantry-mechanized` | `ground-unit-mechanized-infantry` | `SFGPUCIZ-------` / `a-f-g-u-c-i-z` | `review-candidate`; `exact-standard` |
| 20 | `ground-unit-infantry-motorized` | `ground-unit-motorized-infantry` | `SFGPUCIM-------` / `a-f-g-u-c-i-m` | `review-candidate`; `exact-standard` |
| 21 | `ground-unit-internal-security-forces` | `ground-unit-security` | `SFGPUCS--------` / `a-f-g-u-c-s` | `review-candidate`; `closest-standard` |
| 22 | `ground-unit-maintenance` | `ground-equipment-maintenance-point` | `SFGPUSX--------` / `a-f-g-u-s-x` | `review-candidate`; `closest-standard` |
| 23 | `subsurface-sonar-array` | `subsurface-submarine` | `SFUPS----------` / `a-f-u-s` | `review-candidate`; `exact-standard` |

Every family appears once per affiliation, producing four exact SIDC collisions per family. The corresponding CoT-type aliases duplicate the same problem through the event-type path.

## Duplicate canonical SIDCs found in the icon collection

- Duplicate exact SIDC keys: **8**
- Four rotary-wing duplicates have different SVG bytes; four generic-installation duplicates have identical SVG bytes.

| SIDC | Canonical names sharing the SIDC | Same SVG bytes |
|---|---|---|
| `SFAPMH---------` | `friendly-air-military-rotary-wing`, `friendly-air-rotary-wing` | False |
| `SFGPI-----H----` | `friendly-ground-installation`, `friendly-ground-installation-installation` | True |
| `SHAPMH---------` | `hostile-air-military-rotary-wing`, `hostile-air-rotary-wing` | False |
| `SHGPI-----H----` | `hostile-ground-installation`, `hostile-ground-installation-installation` | True |
| `SNAPMH---------` | `neutral-air-military-rotary-wing`, `neutral-air-rotary-wing` | False |
| `SNGPI-----H----` | `neutral-ground-installation`, `neutral-ground-installation-installation` | True |
| `SUAPMH---------` | `unknown-air-military-rotary-wing`, `unknown-air-rotary-wing` | False |
| `SUGPI-----H----` | `unknown-ground-installation`, `unknown-ground-installation-installation` | True |

## Source integrity

- i578 ZIP SHA-256: `776308307d80101cc6d27a3ab684bfbbc6232ee3842fbdde7d15f1f9268a1f47`
- Resolver SHA-256: `4192aab0b139870ac0108a031ed1d230e2cdf120c1b84a18ce27c91165e97bcd`
- Alias catalog SHA-256: `344433deae19c8df92bbd7dd93537bf443f99afffa18757d5fd9c263a5ec0e94`
- Canonical icons catalog SHA-256: `c46dde983c566aa8983de57651aadc1dd3fe283029fc4bfbbd8c98e6103d8edf`

## Correctness rule indicated by the audit

An exact canonical SIDC must be resolved before any compatibility alias. Reviewed aliases should be consulted only when the exact SIDC is absent from the canonical catalog. The same rule must apply after converting an exact CoT type to SIDC. This single ordering correction removes all 92 exact shadow collisions without deleting compatibility aliases used for genuinely unmapped ATAK identities.
