#!/usr/bin/env python3
"""Create the research-only decision for the 2011--2023 Energy/Water scope series."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
FAMILY_MAP = ROOT / "project-state/discovery/energy-water-public-facilities-capital-spending-family-map-2026-09-18.json"
PLAN = ROOT / "project-state/discovery/energy-water-public-facilities-bond-scopes-r2-archive-plan-2026-09-09.json"
VALIDATION = ROOT / "project-state/discovery/energy-water-public-facilities-bond-scopes-r2-public-validation-2026-09-09.json"
OUTPUT = ROOT / "project-state/discovery/2011-2023-energy-water-public-facilities-system-modernization-cycle-scopes-decision-2026-09-18.json"

MASTER_ORDER = [
    "src-02e5a5bcff518eca", "src-3cc1912d7ac89cf9", "src-52bda6b47c8295b6",
    "src-3d31dcad9dec671a", "src-62f957e563e55b52", "src-d356c01557a3a067",
]
PAGES = {
    "src-02e5a5bcff518eca": 5, "src-3cc1912d7ac89cf9": 4,
    "src-52bda6b47c8295b6": 4, "src-3d31dcad9dec671a": 5,
    "src-62f957e563e55b52": 2, "src-d356c01557a3a067": 5,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def archive_links(text: str) -> set[str]:
    return set(re.findall(r"https://files\.abqinfo\.com/[^)\s]+", text))


def component(candidate: dict, plan: dict, order: int) -> dict:
    locations = list(candidate.get("implementation_locations") or [])
    return {
        "order": order,
        "candidate_id": candidate["id"],
        "title": candidate["title"],
        "source_date_or_election_cycle": candidate.get("date"),
        "classification": "compilation_component",
        "official_source_url": candidate.get("direct_file_url"),
        "official_record_url": candidate.get("source_url"),
        "current_status": candidate["status"],
        "current_r2_key": candidate.get("r2_key"),
        "current_archive_url": candidate.get("r2_url"),
        "current_r2_archive_status": "publicly_byte_verified",
        "size_bytes": candidate.get("size_bytes") or plan.get("size_bytes"),
        "checksum_sha256": candidate.get("checksum_sha256") or plan.get("sha256"),
        "known_component_page_count": PAGES[candidate["id"]],
        "current_implementation_locations": locations,
        "topical_cross_listings_to_remain_individual": [x for x in locations if x != "content/city-data/capital-spending.md"],
    }


def main() -> None:
    candidates = {row["id"]: row for row in load(INVENTORY)["candidates"]}
    family_map = load(FAMILY_MAP)
    plan = {row["id"]: row for row in load(PLAN)["items"]}
    validation = {row["id"]: row for row in load(VALIDATION)["results"]}
    family = next(row for row in family_map["family_map"] if row["family"] == "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes")
    if family["candidate_ids"] != MASTER_ORDER:
        raise ValueError("The approved family map no longer has the six expected cycle records in chronological order")
    if set(MASTER_ORDER) - set(candidates) or set(MASTER_ORDER) != set(plan) or set(MASTER_ORDER) != set(validation):
        raise ValueError("Expected six-record source/archive evidence is incomplete")
    if not all(candidates[item]["status"] == "validated" and candidates[item].get("r2_url") for item in MASTER_ORDER):
        raise ValueError("Every component must remain validated and archived")
    if not all(validation[item]["byte_identical"] for item in MASTER_ORDER):
        raise ValueError("Every component must retain public byte verification")
    if set(PAGES) != set(MASTER_ORDER):
        raise ValueError("Every component needs a known page count")

    components = [component(candidates[item], plan[item], order) for order, item in enumerate(MASTER_ORDER, 1)]
    capital_links = archive_links(PAGE.read_text(encoding="utf-8-sig"))
    current_links = [row["current_archive_url"] for row in components if row["current_archive_url"] in capital_links]
    if len(current_links) != 6:
        raise ValueError("Expected all six cycle records to remain visible on Capital Spending")
    if any(row["topical_cross_listings_to_remain_individual"] for row in components):
        raise ValueError("This decision expects no current topical cross-listings")

    data = {
        "schema_version": 1,
        "artifact_type": "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes_decision",
        "reviewed_at": "2026-09-18",
        "state": "research_complete_no_archive_or_page_change_authorized",
        "scope": {
            "page": "content/city-data/capital-spending.md",
            "family_map": str(FAMILY_MAP.relative_to(ROOT)).replace("\\", "/"),
            "family": "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes",
            "current_visible_entry_count": 6,
            "exact_candidate_ids": MASTER_ORDER,
        },
        "source_artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in (FAMILY_MAP, PLAN, VALIDATION)],
        "decision": {
            "result": "one_provenance_preserving_historical_compilation",
            "rationale": "The six short records share a stable subject label and function as a chronological series of distinct City election-cycle scope statements. One chronological master would make the series substantially easier to browse while retaining each election cycle, source, archive object, and checksum as an independent provenance record.",
            "provenance_rule": "Different election cycles are not duplicates. The compilation is an ABQInfo historical compilation, not an original City-issued single document; all six City originals remain individually preserved and individually traceable.",
        },
        "proposed_compilation": {
            "title": "2011--2023 Energy and Water Conservation, Public Facilities, and System Modernization Bond Scopes: Historical Compilation",
            "filename": "abqinfo-2011-2023-energy-water-public-facilities-system-modernization-bond-scopes-historical-compilation.pdf",
            "future_r2_key": "city-data/capital-spending/abqinfo-2011-2023-energy-water-public-facilities-system-modernization-bond-scopes-historical-compilation.pdf",
            "component_count": 6,
            "known_total_source_pages": sum(PAGES.values()),
            "ordering_rule": "Chronological election-cycle order: 2011, 2013, 2015, 2017, 2019, then 2023. This is a browsing order only and does not assert adopted, final, superseded, or other precedence.",
            "components": components,
            "version_relationships": "No version relationship is established among the six records. They are distinct election-cycle scope records, not duplicate deliveries or successive versions of one City-issued document.",
            "future_build_and_publication_prerequisites": [
                "Obtain separate explicit authorization for a local compilation build and R2 upload.",
                "Create an ABQInfo-labeled cover and index that identifies every retained original, source URL, checksum, size, page count, and compilation page range without altering component substance.",
                "Structurally and visually verify the compilation; calculate and record its exact output size and SHA-256.",
                "Archive and publicly byte-verify the future compilation before changing the Capital Spending page, then verify a temporary deployment before replacing the six links.",
            ],
        },
        "future_capital_spending_treatment": {
            "replace_current_individual_links": current_links,
            "replace_current_link_count": 6,
            "current_visible_entry_count": 6,
            "future_visible_entry_count": 1,
            "expected_reduction_in_visible_entries": 5,
            "future_visible_form": "One clearly labeled ABQInfo historical compilation in place of the six chronological component entries, with retained component provenance exposed in its cover/index and inventory records.",
            "topical_cross_listing_rule": "No current topical cross-listings exist for these six originals. If a future topical use needs a particular cycle, keep it pointed to that individual original rather than redirecting it to the broad compilation.",
            "not_authorized_now": ["Capital Spending page edit", "R2 upload or mutation", "inventory-status change", "compilation PDF build", "merge", "deployment"],
        },
        "unresolved_questions": [
            "No authoritative evidence establishes adopted/final/superseded precedence among these election-cycle records; none is implied here.",
            "Compilation page ranges, output size, output SHA-256, and final visible-page wording must be recorded during a separately authorized build/publication stage.",
        ],
        "safeguards_observed": {"r2_mutation": False, "capital_spending_page_modified": False, "inventory_modified": False, "compilation_built": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(components)} components")


if __name__ == "__main__":
    main()
