#!/usr/bin/env python3
"""Build TAK Map i551 ATAK compatibility aliases from the accepted 2525C review.

The Phase 4 review promoted replacement SVG artwork but intentionally kept the
legacy runtime identities in icons.json. This builder turns accepted reviewed
original/candidate identities into a deterministic compatibility layer without
mutating the 1,448-row selector catalog.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MIL = ROOT / "assets" / "mil2525"
REVIEW = MIL / "milstd2525c-phase3-review-2026-07-25.json"
ICONS = MIL / "icons.json"
OUT = MIL / "atak-compatibility-aliases-i551.json"
REPORT = ROOT / "reports" / "milstd2525c-atak-aliases-i551-report.json"
AFFILIATION_SLUG = {"F": "friendly", "H": "hostile", "N": "neutral", "U": "unknown"}
STATUS_PRIORITY = {"exact-standard": 40, "closest-standard": 30, "legacy-alias": 20, "unsupported": 0, "": 10}


def norm_sidc(value: Any) -> str:
    raw = re.sub(r"[^A-Z0-9-]", "", str(value or "").upper().replace("*", "-"))
    if len(raw) < 4 or not raw.startswith("S"):
        return ""
    return (raw + "---------------")[:15]


def norm_cot(value: Any) -> str:
    return "-".join(part for part in re.split(r"-+", str(value or "").strip().lower()) if part)


def cot_to_sidc(value: Any) -> str:
    parts = norm_cot(value).split("-")
    if len(parts) < 3 or parts[0] != "a":
        return ""
    affiliation = {"f": "F", "h": "H", "n": "N", "u": "U"}.get(parts[1])
    dimension = {"g": "G", "a": "A", "s": "S", "u": "U", "p": "P", "e": "E"}.get(parts[2])
    if not affiliation or not dimension:
        return ""
    function_id = re.sub(r"[^A-Z0-9]", "", "".join(parts[3:]).upper())[:6]
    return norm_sidc("S" + affiliation + dimension + "P" + function_id)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    icons = json.loads(ICONS.read_text(encoding="utf-8"))
    icon_by_name = {str(row.get("name") or "").strip(): row for row in icons if isinstance(row, dict)}

    accepted: list[dict[str, Any]] = []
    missing_files: list[str] = []
    for record in review.get("records") or []:
        if not isinstance(record, dict) or record.get("decision") != "accept":
            continue
        concept = str(record.get("concept") or "").strip()
        status = str(record.get("candidate_status") or "").strip()
        for affiliation in record.get("affiliations") or []:
            if not isinstance(affiliation, dict):
                continue
            code = str(affiliation.get("affiliation") or "").upper()
            slug = AFFILIATION_SLUG.get(code)
            if not slug or not concept:
                continue
            name = f"{slug}-{concept}"
            svg = MIL / "svg" / f"{name}.svg"
            if not svg.is_file():
                missing_files.append(str(svg.relative_to(ROOT)))
                continue
            catalog = icon_by_name.get(name) or {}
            accepted.append({
                "concept": concept,
                "candidate_status": status,
                "priority": STATUS_PRIORITY.get(status, 10),
                "affiliation": code,
                "name": name,
                "file": f"{name}.svg",
                "catalog_sidc": norm_sidc(catalog.get("sidc")),
                "label": str(catalog.get("label") or "").strip(),
                "image_sha256": sha256(svg),
                "original_sidc": norm_sidc(affiliation.get("original_sidc")),
                "original_cot_type": norm_cot(affiliation.get("original_cot_type")),
                "candidate_sidc": norm_sidc(affiliation.get("candidate_sidc")),
                "candidate_cot_type": norm_cot(affiliation.get("candidate_cot_type")),
            })

    claims_sidc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    claims_cot: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def claim(entry: dict[str, Any], kind: str, sidc: str = "", cot: str = "") -> None:
        row = dict(entry)
        row["alias_kind"] = kind
        if sidc:
            claims_sidc[norm_sidc(sidc)].append(row)
        if cot:
            claims_cot[norm_cot(cot)].append(row)

    for entry in accepted:
        if entry["original_sidc"]:
            claim(entry, "review-original", sidc=entry["original_sidc"])
        if entry["original_cot_type"]:
            claim(entry, "review-original", cot=entry["original_cot_type"])
        if entry["candidate_sidc"]:
            claim(entry, "review-candidate", sidc=entry["candidate_sidc"])
        if entry["candidate_cot_type"]:
            claim(entry, "review-candidate", cot=entry["candidate_cot_type"])

    # ATAK sometimes emits an abbreviated hierarchy rather than the full review
    # candidate (for example a-f-G-E-W-H instead of a-f-G-E-W-H-M-S). Promote a
    # prefix only when every reviewed descendant renders byte-identical artwork.
    candidate_by_cot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in accepted:
        if entry["candidate_cot_type"]:
            candidate_by_cot[entry["candidate_cot_type"]].append(entry)
    prefix_groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for cot_type, rows in candidate_by_cot.items():
        parts = cot_type.split("-")
        for length in range(5, len(parts)):  # at least two function hierarchy tokens
            prefix = "-".join(parts[:length])
            for row in rows:
                prefix_groups[prefix][row["name"]] = row

    prefix_promoted = 0
    prefix_ambiguous: list[dict[str, Any]] = []
    for prefix, rows_by_name in sorted(prefix_groups.items()):
        rows = list(rows_by_name.values())
        digests = {row["image_sha256"] for row in rows}
        if len(digests) != 1:
            prefix_ambiguous.append({
                "cot_type": prefix,
                "candidate_files": sorted(row["file"] for row in rows),
                "image_sha256_count": len(digests),
            })
            continue
        for row in rows:
            claim(row, "review-candidate-prefix-identical-artwork", cot=prefix)
            sidc = cot_to_sidc(prefix)
            if sidc:
                claim(row, "review-candidate-prefix-identical-artwork", sidc=sidc)
        prefix_promoted += 1

    alias_kind_priority = {
        "review-candidate": 40,
        "review-candidate-prefix-identical-artwork": 35,
        "review-original": 30,
    }

    def build_aliases(groups: dict[str, list[dict[str, Any]]], alias_type: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        output: dict[str, Any] = {}
        omitted: list[dict[str, Any]] = []
        for alias, claims in sorted(groups.items()):
            if not alias:
                continue
            unique = {row["name"]: row for row in claims}
            rows = list(unique.values())
            digests = {row["image_sha256"] for row in rows}
            if len(digests) != 1:
                omitted.append({
                    alias_type: alias,
                    "reason": "conflicting-reviewed-artwork",
                    "candidate_files": sorted(row["file"] for row in rows),
                    "image_sha256_count": len(digests),
                })
                continue
            rows.sort(key=lambda row: (
                -alias_kind_priority.get(str(row.get("alias_kind") or ""), 0),
                -int(row.get("priority") or 0),
                str(row.get("name") or ""),
            ))
            chosen = rows[0]
            kinds = sorted({str(row.get("alias_kind") or "") for row in rows if row.get("alias_kind")})
            output[alias] = {
                "name": chosen["name"],
                "file": chosen["file"],
                "catalog_sidc": chosen["catalog_sidc"],
                "label": chosen["label"],
                "image_sha256": chosen["image_sha256"],
                "alias_kinds": kinds,
                "candidate_status": chosen["candidate_status"],
                "concepts": sorted({row["concept"] for row in rows}),
                "equivalent_files": sorted({row["file"] for row in rows}),
                "reviewed_alias": True,
            }
        return output, omitted

    by_sidc, omitted_sidc = build_aliases(claims_sidc, "sidc")
    by_cot, omitted_cot = build_aliases(claims_cot, "cot_type")

    payload = {
        "schema": "tak-map-milstd2525c-atak-compatibility-aliases-i551-v1",
        "version": "i551",
        "source_review": REVIEW.name,
        "selector_catalog_unchanged": True,
        "policy": {
            "exact_reviewed_alias_before_catalog_parent_fallback": True,
            "candidate_alias_overrides_legacy_catalog_identity": True,
            "prefix_alias_requires_identical_reviewed_svg_bytes": True,
            "multiple_names_may_share_one_visual": True,
            "conflicting_artwork_aliases_omitted": True,
        },
        "summary": {
            "accepted_affiliation_artworks": len(accepted),
            "sidc_aliases": len(by_sidc),
            "cot_type_aliases": len(by_cot),
            "prefix_cot_groups_promoted": prefix_promoted,
            "ambiguous_prefix_groups_omitted": len(prefix_ambiguous),
            "conflicting_sidc_aliases_omitted": len(omitted_sidc),
            "conflicting_cot_aliases_omitted": len(omitted_cot),
            "missing_reviewed_svg_files": len(missing_files),
        },
        "by_sidc": by_sidc,
        "by_cot_type": by_cot,
        "omitted": {
            "prefix_groups": prefix_ambiguous,
            "sidc_aliases": omitted_sidc,
            "cot_type_aliases": omitted_cot,
            "missing_files": sorted(set(missing_files)),
        },
    }

    # Required field checks for the two operator-reported examples.
    construction = by_cot.get("a-f-g-u-c-e-n") or {}
    howitzer = by_cot.get("a-f-g-e-w-h") or {}
    assert construction.get("file") == "friendly-emergency-construction.svg", construction
    assert howitzer.get("file") in {
        "friendly-ground-equipment-self-propelled-artillery.svg",
        "friendly-ground-equipment-self-propelled-howitzer.svg",
    }, howitzer
    assert not missing_files, missing_files

    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps({
        "result": "pass",
        "version": "i551",
        "output": str(OUT.relative_to(ROOT)),
        "summary": payload["summary"],
        "construction_alias": construction,
        "howitzer_alias": howitzer,
        "policy": payload["policy"],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
