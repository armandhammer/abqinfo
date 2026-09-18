#!/usr/bin/env python3
"""Create a research-only family map for the mixed Energy/Water page section."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
GO2007_DECISION = ROOT / "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json"
GO2009_DECISION = ROOT / "project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json"
ENERGY_PLAN = ROOT / "project-state/discovery/energy-water-public-facilities-bond-scopes-r2-archive-plan-2026-09-09.json"
ENERGY_VALIDATION = ROOT / "project-state/discovery/energy-water-public-facilities-bond-scopes-r2-public-validation-2026-09-09.json"
OUTPUT = ROOT / "project-state/discovery/energy-water-public-facilities-capital-spending-family-map-2026-09-18.json"

ENERGY_CYCLE = [
    "src-02e5a5bcff518eca", "src-3cc1912d7ac89cf9", "src-52bda6b47c8295b6",
    "src-3d31dcad9dec671a", "src-62f957e563e55b52", "src-d356c01557a3a067",
]
GO2009 = [
    "src-2938db47584ebb1c", "src-2b015205e93852b3", "src-4386e4a8fe337de9",
    "src-5066c9f642369e9b", "src-560e4635031fdaca", "src-60615a9cae3d68d4",
    "src-b3d0cd2df96d0bc6", "src-e8df08f8bb47b981", "src-ec2498a018d22816",
    "src-fea1d0aef6dc4569",
]
GO2007_MASTER = [
    "src-ef823eb290efe729", "src-83f0d442beb438b9", "src-c862e9705c4818eb",
    "src-a9e35369bc0ff59e", "src-a4c924b7039b13da", "src-514c1cb1098dac8d",
    "src-be39966975e9924a", "src-c3b290c3fd2dd0a9",
]
GO2007_LEGAL = ["src-84fb340bc61d8443"]
GO2007_INDEPENDENT = ["src-ce691b140ada313b", "src-43f135ae1e00492e"]

# The page itself presents six short-cycle labels, while the canonical inventory
# titles preserve the fuller City wording.  The 2009 energy scope is semantically
# associated but is physically located in the preceding 2009 program section.
VISIBLE_TITLES = {
    "src-2938db47584ebb1c": "2009 Energy, Water Conservation, Public Facilities, and System Modernization Bond Scopes (Archived PDF)",
    "src-02e5a5bcff518eca": "2011 Bond Scopes (Archived PDF)",
    "src-3cc1912d7ac89cf9": "2013 Bond Scopes (Archived PDF)",
    "src-52bda6b47c8295b6": "2015 Bond Scopes (Archived PDF)",
    "src-3d31dcad9dec671a": "2017 Bond Scopes (Archived PDF)",
    "src-62f957e563e55b52": "2019 Bond Scopes (Archived PDF)",
    "src-d356c01557a3a067": "2023 Bond Scopes (Archived PDF)",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def current_title(candidate: dict) -> str:
    return VISIBLE_TITLES.get(candidate["id"], f'{candidate["title"]} (Archived PDF)')


def row(candidate: dict, family: str, covered_by: str | None, separate: str, component: str) -> dict:
    return {
        "candidate_id": candidate["id"],
        "current_visible_title": current_title(candidate),
        "canonical_inventory_title": candidate["title"],
        "source_date_or_bond_cycle": candidate.get("date") or "2009 bond cycle (inventory date not normalized)",
        "official_source_url": candidate.get("direct_file_url"),
        "current_r2_status": "publicly_byte_verified" if candidate.get("r2_url") and candidate["status"] == "validated" else candidate["status"],
        "current_r2_key": candidate.get("r2_key"),
        "current_capital_spending_placement": "physically_under_energy_water_heading" if candidate["id"] in ENERGY_CYCLE else "associated_outside_heading" if candidate["id"] == "src-2938db47584ebb1c" else "physically_after_energy_water_heading_before_department_capital_details",
        "documentary_family": family,
        "covered_by_existing_consolidation_decision": covered_by,
        "should_remain_separately_visible": separate,
        "future_compilation_component": component,
        "unresolved_provenance_or_version_question": None,
    }


def main() -> None:
    candidates = {x["id"]: x for x in load(INVENTORY)["candidates"]}
    go2007 = load(GO2007_DECISION)
    go2009 = load(GO2009_DECISION)
    energy_plan = {x["id"]: x for x in load(ENERGY_PLAN)["items"]}
    energy_validation = {x["id"]: x for x in load(ENERGY_VALIDATION)["results"]}
    all_ids = ENERGY_CYCLE + GO2009 + GO2007_MASTER + GO2007_LEGAL + GO2007_INDEPENDENT
    if len(all_ids) != 27 or len(all_ids) != len(set(all_ids)) or set(all_ids) - set(candidates):
        raise ValueError("Expected 27 unique mapped canonical records")
    if not set(GO2007_MASTER) <= {x["candidate_id"] for x in go2007["proposed_compilation"]["components"]}:
        raise ValueError("2007 master membership differs from its approved decision")
    if not set(GO2009) <= {x["candidate_id"] for x in go2009["proposed_compilation"]["components"]}:
        raise ValueError("2009 master membership differs from its approved decision")
    if set(ENERGY_CYCLE) != set(energy_plan) or not all(energy_validation[x]["byte_identical"] for x in ENERGY_CYCLE):
        raise ValueError("Energy/water source archive evidence is incomplete")

    records = []
    records += [row(candidates[x], "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes", None, "not_decided_pending_family_review", "possible_pending_family_review") for x in ENERGY_CYCLE]
    records += [row(candidates[x], "2009_general_obligation_bond_program", "project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json", "no_future_capital_spending_master_replaces_component", "yes_approved_2009_master_component") for x in GO2009]
    records += [row(candidates[x], "2007_2016_general_obligation_bond_decade_plan", "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "no_future_capital_spending_master_replaces_component", "yes_approved_2007_2016_master_component") for x in GO2007_MASTER]
    records += [row(candidates[x], "2007_2016_governance_policy", "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "yes_legal_governing_instrument", "no") for x in GO2007_LEGAL]
    records += [row(candidates[x], "2007_2016_independent_fund_plan", "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "yes_substantively_independent_record", "no") for x in GO2007_INDEPENDENT]

    # Four currently visible 2007 archive URLs also have already-settled
    # delivery-copy inventory rows.  Cite the canonical record in the map and
    # preserve the delivery relationship rather than treating it as a new source.
    delivery_copies = {
        "src-84fb340bc61d8443": "src-c62bd3c09f6ff9ef",
        "src-514c1cb1098dac8d": "src-84cfc972a917709e",
        "src-43f135ae1e00492e": "src-8c270fb9cb3d6f72",
        "src-c3b290c3fd2dd0a9": "src-e91e185fc5c2a916",
    }
    for item in records:
        duplicate = delivery_copies.get(item["candidate_id"])
        if duplicate:
            item["settled_delivery_copy_id"] = duplicate
            item["settled_delivery_copy_note"] = "Current archive-link representation has a previously settled duplicate delivery row; this map uses the validated official-source canonical candidate."

    families = [
        {"family": "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes", "membership_count": 6, "candidate_ids": ENERGY_CYCLE, "existing_decision": None, "status": "archive_and_source_validation_complete_presentation_review_not_started", "next_action": "Review this six-cycle scope series as its own bounded presentation family; do not infer that different election cycles are duplicate or superseded editions."},
        {"family": "2009_general_obligation_bond_program", "membership_count": 10, "candidate_ids": GO2009, "existing_decision": "project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json", "status": "approved_future_24_component_master", "next_action": "No new review here; preserve the approved 2009 boundary and archive gates."},
        {"family": "2007_2016_general_obligation_bond_decade_plan", "membership_count": 8, "candidate_ids": GO2007_MASTER, "existing_decision": "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "status": "approved_future_18_component_master", "next_action": "No new review here; preserve the approved 2007--2016 boundary."},
        {"family": "2007_2016_governance_policy", "membership_count": 1, "candidate_ids": GO2007_LEGAL, "existing_decision": "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "status": "separately_visible_legal_governing_instrument", "next_action": "Remain separate."},
        {"family": "2007_2016_independent_fund_plan", "membership_count": 2, "candidate_ids": GO2007_INDEPENDENT, "existing_decision": "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json", "status": "separately_visible_substantively_independent_records", "next_action": "Remain separate."},
    ]
    data = {
        "schema_version": 1,
        "artifact_type": "energy_water_public_facilities_capital_spending_family_map",
        "reviewed_at": "2026-09-18",
        "state": "family_boundary_map_complete_no_new_consolidation_decision_or_publication_authorized",
        "scope": {"page": "content/city-data/capital-spending.md", "physical_heading": "Energy, Water, Public Facilities, and System Modernization Bond Scopes", "physically_grouped_visible_record_count": 26, "semantically_associated_visible_record_count": 1, "exact_total_visible_records_reviewed": 27},
        "source_artifacts": [str(x.relative_to(ROOT)).replace("\\", "/") for x in (GO2007_DECISION, GO2009_DECISION, ENERGY_PLAN, ENERGY_VALIDATION)],
        "family_map": families,
        "records": records,
        "legal_governing_instruments": GO2007_LEGAL,
        "unrelated_records": [],
        "settled_duplicates_or_delivery_copies": [{"canonical_candidate_id": key, "delivery_copy_candidate_id": value, "relationship": "previously_settled_duplicate_archive_delivery"} for key, value in delivery_copies.items()],
        "heading_reorganization": {"eventually_needed": True, "reason": "The present heading combines a distinct six-cycle 2011--2023 scope series with 2009 program-master components, 2007--2016 program-master components, and three 2007 records that must remain individual. It is not a coherent documentary family.", "future_direction_only": "After separately authorized publication stages, group the six-cycle scope series under its own family; represent 2009 and 2007 components through their already-approved program treatments; leave the 2007 policy, Enterprise Fund, and Metropolitan Redevelopment Fund records individual."},
        "next_family_to_review": "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes",
        "unresolved_questions": ["Whether the six distinct 2011--2023 election-cycle scope records are best browsed as one historical compilation remains unreviewed; their existing source/archive validation does not itself decide presentation.", "No adopted/final/superseded inference is made among the six election-cycle records."],
        "safeguards_observed": {"r2_mutation": False, "capital_spending_page_modified": False, "inventory_modified": False, "compilation_built": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(records)} mapped visible records")


if __name__ == "__main__":
    main()
