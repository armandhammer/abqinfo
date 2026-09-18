#!/usr/bin/env python3
"""Create the research-only 2007--2016 Capital Spending presentation decision."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
PLAN = ROOT / "project-state/discovery/capital-program-review-28-plan.json"
VALIDATION = ROOT / "project-state/discovery/capital-program-review-28-public-validation.json"
OUTPUT = ROOT / "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json"

# This is City source-directory order for the 2007--2016 GO program summaries:
# overview, Council allocation detail, functional programs, then departments.
MASTER_ORDER = [
    "src-ef823eb290efe729", "src-83f0d442beb438b9",
    "src-c862e9705c4818eb", "src-a9e35369bc0ff59e", "src-a4c924b7039b13da",
    "src-514c1cb1098dac8d", "src-be39966975e9924a", "src-c3b290c3fd2dd0a9",
    "src-baa2a3551783da18", "src-e665566329c4a04d", "src-857af4faf4a82a56",
    "src-3176f1245fb14160", "src-fbf2928dc2388b68", "src-d554e2dfdf46e98b",
    "src-d91051fe76863796", "src-0c38e48c453a12db", "src-1446091908574fda",
    "src-ab1f9d7ff3dfd004",
]
LEGAL = ["src-84fb340bc61d8443"]
INDEPENDENT = ["src-ce691b140ada313b", "src-43f135ae1e00492e"]
CCIP_NONMEMBERS = [
    "src-8ea637fcf3e9208a", "src-c83a5233716f5e1f", "src-c108ac10089df2fa",
    "src-389b414dbe0fb8b9", "src-89cf13c2d742e6d2",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def page_links(text: str) -> set[str]:
    return set(re.findall(r"https://files\.abqinfo\.com/[^)\s]+", text))


def record(candidate: dict, validation: dict, classification: str) -> dict:
    locations = list(candidate.get("implementation_locations") or [])
    key = candidate["r2_key"]
    archive_url = f"https://files.abqinfo.com/{key}" if key else None
    result = validation[candidate["id"]]
    return {
        "candidate_id": candidate["id"],
        "title": candidate["title"],
        "source_date": candidate.get("date"),
        "classification": classification,
        "official_source_url": candidate["direct_file_url"],
        "current_r2_key": key,
        "current_archive_url": archive_url,
        "current_r2_archive_status": "publicly_byte_verified" if result["byte_identical"] else "not_publicly_verified",
        "size_bytes": candidate["size_bytes"],
        "checksum_sha256": candidate["checksum_sha256"],
        "known_component_page_count": None,
        "page_count_note": "No page count is retained in the existing 2007 archive/source-validation artifacts; determine it from the preserved original during a separately authorized compilation build.",
        "current_implementation_locations": locations,
        "topical_cross_listings_to_remain_individual": [x for x in locations if x != "content/city-data/capital-spending.md"],
    }


def main() -> None:
    candidates = {x["id"]: x for x in load(INVENTORY)["candidates"]}
    plan = {x["id"]: x for x in load(PLAN)["items"]}
    validation = {x["id"]: x for x in load(VALIDATION)["results"]}
    required = MASTER_ORDER + LEGAL + INDEPENDENT + CCIP_NONMEMBERS
    if len(required) != len(set(required)) or len(required) != 26:
        raise ValueError("Expected 26 unique reviewed records")
    if set(required) - set(candidates) or set(required) - set(plan) or set(required) - set(validation):
        raise ValueError("A reviewed record is absent from saved inventory or archive evidence")
    if not all(validation[x]["byte_identical"] for x in required):
        raise ValueError("Every reviewed original must retain prior public byte verification")
    for candidate_id in required:
        if candidates[candidate_id]["size_bytes"] != plan[candidate_id]["size_bytes"]:
            raise ValueError(f"Size contradiction for {candidate_id}")

    master = [record(candidates[x], validation, "compilation_component") for x in MASTER_ORDER]
    for order, row in enumerate(master, 1):
        row["order"] = order
    legal = [record(candidates[x], validation, "separately_visible_legal_governing_instrument") for x in LEGAL]
    independent = [record(candidates[x], validation, "separately_visible_substantively_independent_record") for x in INDEPENDENT]
    nonmembers = [record(candidates[x], validation, "unrelated_nonmember") for x in CCIP_NONMEMBERS]
    for row in nonmembers:
        row["nonmember_reason"] = "This is a 2007 Component Capital Improvement Plan/impact-fee record with a 2005--2013 implementation horizon, not a 2007--2016 General Obligation Bond decade-plan summary. Its shared City download folder does not establish common documentary membership."
    links = page_links(PAGE.read_text(encoding="utf-8-sig"))
    if not all(row["current_archive_url"] in links for row in master + legal + independent + nonmembers):
        raise ValueError("A reviewed archived original is no longer linked on Capital Spending")

    decision = {
        "schema_version": 1,
        "artifact_type": "2007_2016_capital_details_consolidation_decision",
        "reviewed_at": "2026-09-18",
        "state": "research_complete_no_archive_or_page_change_authorized",
        "scope": {
            "page": "content/city-data/capital-spending.md",
            "starting_heading": "Department Capital Details",
            "finding": "The heading is not the documentary boundary. Its ten departmental summaries are part of an 18-record 2007--2016 General Obligation Bond decade-plan summary set that begins above the heading.",
            "reviewed_visible_records": 26,
            "go_decade_plan_visible_records": 21,
            "department_capital_details_records": 10,
            "same_directory_impact_fee_nonmembers": 5,
        },
        "source_artifacts": [
            "project-state/discovery/capital-program-review-28-decisions.json",
            "project-state/discovery/capital-program-review-28-plan.json",
            "project-state/discovery/capital-program-review-28-source-validation.json",
            "project-state/discovery/capital-program-review-28-public-validation.json",
            "project-state/discovery/cip-documents-cluster-research-2026-09-12.json",
            "project-state/discovery/capital-spending-consolidation-status-2026-09-17.json",
        ],
        "decision": {
            "result": "one_provenance_preserving_2007_2016_go_bond_decade_plan_master_record",
            "rationale": "The 18 overview, Council allocation, functional, and departmental summaries share the same 2007--2016 GO decade-plan program and complement one another. The current ten-entry department heading artificially separates departmental details from their program overview and other functional summaries. One labeled ABQInfo historical master would make the program intelligible while preserving every original and its City provenance.",
            "provenance_rule": "All 18 source PDFs remain separate City originals with their existing R2 keys, official URLs, sizes, and checksums. Consolidation is only a future Capital Spending browsing form and makes no adopted/final/superseded inference.",
        },
        "proposed_compilation": {
            "title": "2007--2016 General Obligation Bond Decade Plan: Historical Master Record",
            "filename": "abqinfo-2007-2016-general-obligation-bond-decade-plan-historical-master-record.pdf",
            "future_r2_key": "city-data/capital-spending/abqinfo-2007-2016-general-obligation-bond-decade-plan-historical-master-record.pdf",
            "component_count": 18,
            "ordering_rule": "City decade-plan order: overview, Council set-aside detail, functional program summaries, Community Facilities summary, then departmental summaries in current City-page order. This is an organizational order, not a claim of precedence among any versions.",
            "dates_and_bond_cycles": "2007 source documents presenting five planned GO bond cycles through 2016; no final/adopted or supersession relationship is asserted.",
            "components": master,
            "version_relationships": "No duplicate deliveries or materially distinct versions were identified in the reviewed 18-record summary set by the existing plan/public-validation evidence. Do not infer a final/adopted relationship merely from common program dates.",
            "archive_prerequisites": [
                "Obtain explicit authorization for a local compilation build and future R2 upload.",
                "Re-read every preserved original to record page counts, compilation page ranges, and component-fidelity QA in the build manifest.",
                "Create an ABQInfo-labeled cover/index without changing source-document substance; structurally and visually verify the result.",
                "Archive and public-byte-verify the new master, then verify a temporary deployment before a Capital Spending page change.",
            ],
        },
        "separately_visible_legal_governing_instruments": legal,
        "separately_visible_substantively_independent_records": independent,
        "unrelated_nonmembers": nonmembers,
        "duplicate_or_delivery_records": [],
        "unresolved_records": [],
        "future_capital_spending_treatment": {
            "replace_current_individual_links": [row["current_archive_url"] for row in master],
            "replace_current_link_count": 18,
            "retain_individual_visible_records": [row["candidate_id"] for row in legal + independent],
            "current_go_decade_plan_visible_entries": 21,
            "future_go_decade_plan_visible_entries": 4,
            "expected_reduction_in_visible_entries": 17,
            "future_visible_form": "One clearly labeled ABQInfo historical master record plus the policies/criteria, enterprise-fund summary, and Metropolitan Redevelopment Fund plan as individual records.",
            "cross_listing_rule": "Keep the individual originals on Transportation Plans, ABQ RIDE, Stormwater and Drainage, Parks and Recreation, City Facilities, and Metropolitan Redevelopment Plans. Those topical placements are independently useful and should not be redirected to the broad master.",
            "not_authorized_now": ["Capital Spending page edit", "R2 upload or mutation", "inventory-status change", "compilation PDF build", "merge", "deployment"],
        },
        "remaining_uncertainties": [
            "Existing evidence records exact source bytes and hashes but not component page counts; that mechanical detail belongs in a future compilation-build manifest.",
            "This decision does not decide whether the distinct 2005--2013 impact-fee component-plan family should later have its own master; it is expressly outside this family boundary.",
        ],
        "safeguards_observed": {"r2_mutation": False, "capital_spending_page_modified": False, "inventory_modified": False, "compilation_built": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(master)} master components")


if __name__ == "__main__":
    main()
