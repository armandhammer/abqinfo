#!/usr/bin/env python3
"""Generate the durable closeout of the completed Capital Spending review phase."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "project-state/discovery"
OUTPUT = DISCOVERY / "capital-spending-consolidation-closeout-status-2026-09-18.json"

SOURCES = {
    "2011": DISCOVERY / "2011-capital-spending-consolidation-manifest-2026-09-18.json",
    "2009": DISCOVERY / "2009-capital-spending-consolidation-decision-2026-09-18.json",
    "2007_2016": DISCOVERY / "2007-2016-capital-details-consolidation-decision-2026-09-18.json",
    "2005_2013_ccip": DISCOVERY / "2005-2013-impact-fee-ccip-consolidation-decision-2026-09-18.json",
    "energy_cycle": DISCOVERY / "2011-2023-energy-water-public-facilities-system-modernization-cycle-scopes-decision-2026-09-18.json",
    "energy_map": DISCOVERY / "energy-water-public-facilities-capital-spending-family-map-2026-09-18.json",
    "prior_status": DISCOVERY / "capital-spending-consolidation-status-2026-09-17.json",
    "2013": DISCOVERY / "go2013-department-set-decision-2026-09-17.json",
    "ms4_gate": DISCOVERY / "2014-ms4-family-package-gate-2026-09-18.json",
    "final_sweep": DISCOVERY / "final-sweep-cluster-research-2026-09-13.json",
}


def load(key: str) -> dict:
    return json.loads(SOURCES[key].read_text(encoding="utf-8-sig"))


def relative(key: str) -> str:
    return str(SOURCES[key].relative_to(ROOT)).replace("\\", "/")


def future_record(decision: dict, *, family: str, source: str, transition: dict, gate: str) -> dict:
    compilation = decision["proposed_compilation"]
    return {
        "family": family,
        "decision_artifact": source,
        "future_compilation_title": compilation["title"],
        "future_filename": compilation.get("filename", compilation.get("proposed_filename")),
        "future_r2_key": compilation.get("future_r2_key", compilation.get("proposed_r2_key")),
        "component_count": compilation["component_count"],
        "visible_entry_transition": transition,
        "provenance_preservation": decision["decision"]["provenance_rule"],
        "publication_gate": gate,
    }


def main() -> None:
    d2011 = load("2011")
    d2009 = load("2009")
    d2007 = load("2007_2016")
    dccip = load("2005_2013_ccip")
    denergy = load("energy_cycle")
    dmap = load("energy_map")
    d2013 = load("2013")
    ms4 = load("ms4_gate")
    final_sweep = load("final_sweep")

    if dmap["next_family_to_review"] != "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes":
        raise ValueError("Energy family map is not the expected pre-closeout boundary")
    if denergy["decision"]["result"] != "one_provenance_preserving_historical_compilation":
        raise ValueError("Energy cycle decision is not complete")
    if d2011["future_visible_page_treatment"]["visible_master_count"] != 2:
        raise ValueError("2011 visible treatment changed")
    if d2009["proposed_compilation"]["component_count"] != 24 or d2007["proposed_compilation"]["component_count"] != 18:
        raise ValueError("GO master boundaries changed")
    if dccip["proposed_compilation"]["component_count"] != 6:
        raise ValueError("CCIP boundary changed")
    next_row = next((row for row in final_sweep.get("excluded", []) if row.get("id") == "src-0634d4e49bad3dc6"), None)
    if not next_row or next_row.get("recommended_status") != "excluded":
        raise ValueError("Saved ordinary-queue successor is not the expected reviewed live-page record")

    compilations = [
        {
            "family": "2011_preliminary_and_published_program_records",
            "decision_artifact": relative("2011"),
            "future_compilations": [
                {"title": row["title"], "future_filename": row["proposed_filename"], "future_r2_key": row["proposed_r2_key"], "component_count": len(row["sources"])}
                for row in d2011["compilations"]
            ],
            "visible_entry_transition": {"current_visible_component_links": 63, "future_visible_compilation_entries": 2, "expected_reduction": 61},
            "provenance_preservation": d2011["decision"]["provenance_rule"],
            "publication_gate": "Four selected December 2010 originals and both already-built local compilation PDFs require separately authorized R2 archival and public byte verification, then temporary-deployment review before replacing the 63 links.",
        },
        future_record(d2009, family="2009_general_obligation_bond_program", source=relative("2009"), transition={"current_relevant_visible_entries": 27, "future_visible_entries": 8, "expected_reduction": 19}, gate="Four independently material components remain unarchived; separately authorize their archival and the master build/upload, publicly byte-verify all required objects, then review a temporary deployment."),
        future_record(d2007, family="2007_2016_general_obligation_bond_decade_plan", source=relative("2007_2016"), transition={"current_go_decade_plan_visible_entries": 21, "future_visible_entries": 4, "expected_reduction": 17}, gate="Separately authorize the master build/upload, retain the three individual noncomponents, publicly byte-verify the master, then review a temporary deployment."),
        future_record(dccip, family="2005_2013_component_capital_improvement_plan", source=relative("2005_2013_ccip"), transition={"current_capital_spending_visible_entries": 5, "future_visible_entries": 1, "expected_reduction": 4, "additional_topical_only_component": "src-fecd59ba99e137d1"}, gate="Separately authorize the master build/upload, publicly byte-verify it, and review a temporary deployment; retain the individual topical originals and later legal/current records."),
        future_record(denergy, family="2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes", source=relative("energy_cycle"), transition={"current_visible_entries": 6, "future_visible_entries": 1, "expected_reduction": 5}, gate="Separately authorize the compilation build/upload, verify it structurally and visually, publicly byte-verify it, and review a temporary deployment."),
    ]

    data = {
        "schema_version": 1,
        "artifact_type": "capital_spending_consolidation_closeout_status",
        "reviewed_at": "2026-09-18",
        "state": "presentation_review_phase_complete_publication_externally_gated",
        "supersedes_as_resume_state": relative("prior_status"),
        "scope": {"page": "content/city-data/capital-spending.md", "finding": "Every presentation-consolidation candidate identified by the September 18 Capital Spending page audit now has a durable decision or an intentional keep-individual treatment. No further consolidation-research candidate remains from that audit."},
        "completed_future_compilation_boundaries": compilations,
        "reviewed_and_intentionally_unconsolidated": [
            {"section_or_family": "2003-2004 General Obligation Bond Program", "treatment": "The 2003 family already has its ABQInfo master. The four 2004 Street Bond records remain individual because they are distinct program, amendment, process-summary, and ballot instruments.", "evidence": "project-state/discovery/claude-consolidation-2004-street-bond-program-history-2026-09-17.json"},
            {"section_or_family": "2013 General Obligation Bond Program and department editions", "treatment": "Keep the EPC-stage program book, material department editions, useful summary, and DMD scope individually visible. Existing evidence establishes neither edition precedence nor a master-record benefit.", "evidence": relative("2013")},
            {"section_or_family": "2007-2016 Decade Plan individual instruments", "treatment": "Keep the 2007 policies/criteria legal instrument, Enterprise Fund summary, and Metropolitan Redevelopment Fund plan individual; they are outside the 18-component GO-decade-plan master boundary.", "evidence": relative("2007_2016")},
            {"section_or_family": "Impact Fee Capital Improvement Plan Records", "treatment": "Keep the two enacted 2012/2013 CCIP resolutions and 2020 credit-holder summary individual; they are later legal/operational records, not 2005-2013 implementation-plan components.", "evidence": relative("2005_2013_ccip")},
            {"section_or_family": "Complete Program Books", "treatment": "Keep comprehensive program-level records and distinct purpose views individual; further consolidation would reduce clarity.", "evidence": relative("2011")},
            {"section_or_family": "Urban Enhancement Trust Fund records associated with the 2009 section", "treatment": "Keep the three UETF records individual because they are a separate funding program, not 2009 GO Bond master components.", "evidence": relative("2009")},
        ],
        "provenance_and_cross_listing_rule": "Every City original remains individually preserved in inventory and, where already archived, at its existing R2 key with official URL, size, checksum, and saved validation. Future masters are explicitly labeled ABQInfo historical compilations. Existing independently useful topical cross-listings remain pointed to their individual originals; no compilation changes a settled duplicate or version relationship.",
        "remaining_external_publication_archive_gates": [row["publication_gate"] for row in compilations] + ["No Capital Spending page edit, R2 mutation, inventory-status transition, merge, or deployment is authorized by this closeout artifact."],
        "ordinary_queue_resume": {
            "generated_next_pending_id": "src-05ec421cb265b29a",
            "skip_family": "2014 MS4 Annual Report package",
            "skip_reason": "This candidate is one of the package's 28 pending-review records. The package has a durable decision and remains externally gated for targeted contact/complaint-detail review and archive/publication authorization; do not treat its generated first ID as an ordinary single-record resume target.",
            "package_evidence": relative("ms4_gate"),
            "next_actionable_candidate": {"candidate_id": "src-0634d4e49bad3dc6", "family": "MRCOG live web-page disposition", "saved_research": relative("final_sweep"), "saved_recommendation": "excluded", "reason": "Saved research already establishes that Operations is a live HTML page, not an archival document. It is the next non-MS4 pending candidate in the deterministic inventory order; no action is taken by this closeout."},
        },
        "safeguards_observed": {"capital_spending_page_modified": False, "r2_mutation": False, "inventory_status_changed": False, "compilation_built": False, "ms4_sensitivity_review": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(compilations)} future compilation boundaries")


if __name__ == "__main__":
    main()
