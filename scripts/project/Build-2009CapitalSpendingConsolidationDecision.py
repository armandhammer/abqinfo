#!/usr/bin/env python3
"""Create the preparation-only 2009 Capital Spending consolidation decision."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
CLUSTER = ROOT / "project-state/discovery/go2009-bond-cluster-research-2026-09-11.json"
VERSIONS = ROOT / "project-state/discovery/go2009-bond-version-and-duplicate-review-2026-09-17.json"
RETAINED_PLAN = ROOT / "project-state/discovery/2009-go-bond-retained-11-r2-archive-plan.json"
RETAINED_VALIDATION = ROOT / "project-state/discovery/2009-go-bond-retained-11-r2-public-validation.json"
OUTPUT = ROOT / "project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json"


# The master has one overview pair followed by subject groups.  Streets retains
# both source-dated schedule editions in chronology only; the order is not an
# assertion of final/adopted precedence.
MASTER_ORDER = [
    "src-020571df6ddd5552", "src-fea1d0aef6dc4569",  # allocation / totals
    "src-4386e4a8fe337de9",  # ABQ RIDE
    "src-00d75ea75ac5c12a", "src-b3d0cd2df96d0bc6",  # Community Facilities
    "src-e12c77bb460b9c8f", "src-cb27c408e8c26a66",  # Council set-aside
    "src-999d681b4e75a4c1",  # Cultural Services
    "src-2938db47584ebb1c",  # Energy/Water/Public Facilities
    "src-0352ae60169eac10", "src-d2d3b593d77a2885",  # Family
    "src-e69e9150b150bc1a", "src-b7ef66c741b8a886",  # Fire
    "src-60615a9cae3d68d4", "src-2b015205e93852b3",  # Parks
    "src-5603714dac7351ba", "src-535234f371b3922c",  # Police
    "src-5de108fb850c221f", "src-6fe3ca04cbe476d5",  # Senior Affairs
    "src-ec2498a018d22816", "src-560e4635031fdaca",  # Storm drainage
    "src-e8df08f8bb47b981", "src-5cea73d2df70dabb", "src-5066c9f642369e9b",  # Streets
]

SEPARATE_VISIBLE = [
    "src-370fed4be1f1effa",  # enacted capital-priorities resolution
    "src-768a6855fcfaf443",  # Library authorization
    "src-7567c5f27fceba0a",  # Senior/Family authorization
    "src-b049c4df2812749b",  # Public Safety authorization
]
UETF_NONMEMBERS = ["src-f70c337140899545", "src-b9402ce7e2e6c22f", "src-10edc718610865b0"]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def links(text: str) -> set[str]:
    return set(re.findall(r"https://files\.abqinfo\.com/[^)\s]+", text))


def source_record(candidate: dict, pages_by_id: dict[str, int]) -> dict:
    locations = list(candidate.get("implementation_locations") or [])
    return {
        "candidate_id": candidate["id"],
        "title": candidate["title"],
        "source_date": candidate.get("date") or "source date not normalized in inventory",
        "official_source_url": candidate["direct_file_url"],
        "official_record_url": candidate.get("source_url"),
        "current_status": candidate["status"],
        "size_bytes": candidate["size_bytes"],
        "checksum_sha256": candidate.get("checksum_sha256"),
        "component_page_count": pages_by_id.get(candidate["id"]),
        "component_page_count_note": (
            "Saved research page count." if candidate["id"] in pages_by_id
            else "Not re-extracted for this research-only decision; determine during a separately authorized compilation build."
        ),
        "r2_status": "verified_public_r2" if candidate.get("r2_key") else "not_archived",
        "r2_key": candidate.get("r2_key"),
        "archive_url": candidate.get("r2_url"),
        "current_capital_spending_link": candidate.get("r2_url") or None,
        "current_implementation_locations": locations,
        "future_topical_cross_listings": [value for value in locations if value != "content/city-data/capital-spending.md"],
    }


def main() -> None:
    inventory = load(INVENTORY)
    candidates = {item["id"]: item for item in inventory["candidates"]}
    cluster = load(CLUSTER)
    versions = load(VERSIONS)
    retained_plan = load(RETAINED_PLAN)
    retained_validation = load(RETAINED_VALIDATION)
    page_links = links(PAGE.read_text(encoding="utf-8-sig"))

    required = set(MASTER_ORDER + SEPARATE_VISIBLE + UETF_NONMEMBERS)
    if set(MASTER_ORDER) & set(SEPARATE_VISIBLE) or len(MASTER_ORDER) != len(set(MASTER_ORDER)):
        raise ValueError("2009 presentation memberships must be disjoint and unique")
    if missing := required - set(candidates):
        raise ValueError(f"Missing inventory records: {sorted(missing)}")

    # The source research is authoritative for the four not-yet-archived
    # components, including their saved checksums and page counts.
    research_rows = {
        item["id"]: item
        for field in ("approved_for_addition", "requires_human_review")
        for item in cluster[field]
    }
    pages_by_id = {candidate_id: item["pages"] for candidate_id, item in research_rows.items()}
    for candidate_id in ("src-5cea73d2df70dabb", "src-5de108fb850c221f", "src-6fe3ca04cbe476d5", "src-d2d3b593d77a2885"):
        item = candidates[candidate_id]
        research = research_rows[candidate_id]
        if item["size_bytes"] != research["size_bytes"]:
            raise ValueError(f"Saved-size contradiction for {candidate_id}")

    # Preserve saved source hash evidence without altering the existing
    # requires-human-review inventory state.
    master_sources = []
    for index, candidate_id in enumerate(MASTER_ORDER, start=1):
        row = source_record(candidates[candidate_id], pages_by_id)
        row["order"] = index
        if candidate_id in research_rows:
            row["saved_research_checksum_sha256"] = research_rows[candidate_id]["checksum_sha256"]
        master_sources.append(row)

    archived = [row for row in master_sources if row["r2_status"] == "verified_public_r2"]
    pending = [row for row in master_sources if row["r2_status"] == "not_archived"]
    if len(master_sources) != 24 or len(archived) != 20 or len(pending) != 4:
        raise ValueError("Expected 24 master sources: 20 publicly verified and four pending")
    if not all(row["archive_url"] in page_links for row in archived):
        raise ValueError("A current archived master component is not linked on Capital Spending")

    plan_ids = {item["id"] for item in retained_plan["items"]}
    validation = {item["id"]: item for item in retained_validation["results"]}
    if not plan_ids <= {row["candidate_id"] for row in master_sources}:
        raise ValueError("Retained-11 plan must be wholly represented in the proposed master")
    if any(not validation[candidate_id]["byte_identical"] for candidate_id in plan_ids):
        raise ValueError("A retained-11 component lacks saved public byte verification")

    visible_rows = [source_record(candidates[candidate_id], pages_by_id) for candidate_id in SEPARATE_VISIBLE]
    nonmembers = [source_record(candidates[candidate_id], pages_by_id) for candidate_id in UETF_NONMEMBERS]
    for row in visible_rows:
        row["classification"] = "separately_visible_legal_governing_instrument"
    for row in nonmembers:
        row["classification"] = "unrelated_nonmember"
        row["reason"] = "Urban Enhancement Trust Fund is a separate City funding program, not a 2009 General Obligation Bond program component."

    decision = {
        "schema_version": 1,
        "artifact_type": "2009_capital_spending_consolidation_decision",
        "reviewed_at": "2026-09-18",
        "state": "research_complete_no_archive_or_page_change_authorized",
        "scope": {
            "page": "content/city-data/capital-spending.md",
            "current_relevant_visible_records": 27,
            "current_visible_master_components": 20,
            "additional_master_components_not_currently_visible": 4,
            "separately_visible_governing_records": 4,
            "unrelated_uetf_nonmembers": 3,
        },
        "source_artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in (CLUSTER, VERSIONS, RETAINED_PLAN, RETAINED_VALIDATION)],
        "decision": {
            "result": "one_provenance_preserving_2009_go_bond_program_master_record",
            "rationale": "The current page exposes twenty short but complementary 2009 program scope, schedule, and overview files across three presentation locations. A single organized master gives the public a coherent program record while retaining every source file, its provenance, and topical cross-listings.",
            "provenance_rule": "All 24 master components remain distinct original records. The two Streets schedules are distinct City editions; source chronology is recorded without a final/adopted inference. Senior Affairs and Family and Community Services components are independently material, not Community Facilities duplicates.",
            "presentation_rule": "Consolidation changes only the future Capital Spending browsing form. It does not collapse original archival records, settled duplicate relationships, or useful topical cross-listings.",
        },
        "proposed_compilation": {
            "title": "2009 General Obligation Bond Program: Historical Master Record",
            "filename": "abqinfo-2009-general-obligation-bond-program-historical-master-record.pdf",
            "future_r2_key": "city-data/capital-spending/abqinfo-2009-general-obligation-bond-program-historical-master-record.pdf",
            "component_count": 24,
            "ordering_rule": "Funding allocation and totals first; then program groups alphabetically. Within a group, scope before schedule except the Streets schedules, which follow the scope in established December 2008 then June 2009 source chronology without final/adopted implication.",
            "components": master_sources,
            "version_relationships": versions["version_relationships"],
            "archive_prerequisites": [
                "Separate authorization and public byte verification for the four currently unarchived components: src-5cea73d2df70dabb, src-5de108fb850c221f, src-6fe3ca04cbe476d5, and src-d2d3b593d77a2885.",
                "Resolve their inventory-status transition only under a future authorized archival/publication task; this decision does not alter those statuses.",
                "Build, archive, and publicly byte-verify the ABQInfo master PDF only after every component is archive-ready.",
                "Verify a temporary deployment before any Capital Spending presentation change.",
            ],
        },
        "separately_visible_records": visible_rows,
        "unrelated_nonmembers": nonmembers,
        "settled_duplicate_or_delivery_records": cluster["duplicate"] + versions["prior_duplicate_rulings"],
        "excluded_nonrecords": cluster["excluded"],
        "future_capital_spending_treatment": {
            "replace_current_links": [row["current_capital_spending_link"] for row in master_sources if row["current_capital_spending_link"]],
            "replace_current_link_count": 20,
            "new_visible_master_records": 1,
            "retain_individual_visible_records": [row["candidate_id"] for row in visible_rows] + [row["candidate_id"] for row in nonmembers],
            "expected_reduction_in_relevant_visible_entries": 19,
            "cross_listing_rule": "Do not replace individual topical links on Parks and Recreation, ABQ RIDE, Transportation Plans, Stormwater and Drainage, or Public Safety Data. They remain pointed to their individual, byte-verified originals.",
            "not_authorized_now": ["Capital Spending page edit", "R2 upload", "inventory-status transition", "compilation build", "merge", "deployment"],
        },
        "remaining_uncertainties": [
            "The four independently material components are not currently archived; saved source checksums and page counts exist, but a later authorized archival stage must re-verify them before publication.",
            "The December 2008 and June 2009 Streets schedules have established relative chronology only. Neither is final, adopted, or superseded by this decision.",
        ],
        "safeguards_observed": {
            "r2_mutation": False,
            "capital_spending_page_modified": False,
            "inventory_modified": False,
            "compilation_built": False,
            "merge_or_deploy": False,
        },
    }
    OUTPUT.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with 24 master components")


if __name__ == "__main__":
    main()
