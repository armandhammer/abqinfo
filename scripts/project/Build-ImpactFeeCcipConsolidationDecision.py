#!/usr/bin/env python3
"""Create the research-only 2005--2013 CCIP presentation decision."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
PAGE = ROOT / "content/city-data/capital-spending.md"
PRECEDING = ROOT / "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json"
CAPITAL_PLAN = ROOT / "project-state/discovery/capital-program-review-28-plan.json"
CAPITAL_VALIDATION = ROOT / "project-state/discovery/capital-program-review-28-public-validation.json"
IMPACT_FEES = ROOT / "project-state/discovery/impact-fees-cluster-research-2026-09-11.json"
OUTPUT = ROOT / "project-state/discovery/2005-2013-impact-fee-ccip-consolidation-decision-2026-09-18.json"

# The overview explains the package.  The five implementation plans then follow
# their City subjects; this is organizational only, not a version-precedence claim.
MASTER_ORDER = [
    "src-8ea637fcf3e9208a", "src-fecd59ba99e137d1", "src-c83a5233716f5e1f",
    "src-c108ac10089df2fa", "src-389b414dbe0fb8b9", "src-89cf13c2d742e6d2",
]
PAGES = {
    "src-8ea637fcf3e9208a": 1, "src-fecd59ba99e137d1": 1,
    "src-c83a5233716f5e1f": 1, "src-c108ac10089df2fa": 1,
    "src-389b414dbe0fb8b9": 2, "src-89cf13c2d742e6d2": 2,
}
LATER_LEGAL = ["src-db74fbcfb6e04b9e", "src-f0d6744711099a88"]
LATER_INDEPENDENT = ["src-49533d311cc95fe9"]
UNRESOLVED = ["src-0d81ec5c9bdeb726"]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def links(text: str) -> set[str]:
    return set(re.findall(r"https://files\.abqinfo\.com/[^)\s]+", text))


def source_record(candidate: dict, classification: str) -> dict:
    locations = list(candidate.get("implementation_locations") or [])
    return {
        "candidate_id": candidate["id"],
        "title": candidate["title"],
        "source_date": candidate.get("date"),
        "implementation_horizon": "2005--2013" if candidate["id"] in MASTER_ORDER else None,
        "classification": classification,
        "official_source_url": candidate.get("direct_file_url"),
        "official_record_url": candidate.get("source_url"),
        "current_status": candidate["status"],
        "current_r2_key": candidate.get("r2_key"),
        "current_archive_url": candidate.get("r2_url"),
        "current_r2_archive_status": "publicly_byte_verified" if candidate.get("r2_url") else "not_archived",
        "size_bytes": candidate.get("size_bytes"),
        "checksum_sha256": candidate.get("checksum_sha256"),
        "known_component_page_count": PAGES.get(candidate["id"]),
        "current_implementation_locations": locations,
        "topical_cross_listings_to_remain_individual": [x for x in locations if x != "content/city-data/capital-spending.md"],
    }


def main() -> None:
    candidates = {x["id"]: x for x in load(INVENTORY)["candidates"]}
    plan = {x["id"]: x for x in load(CAPITAL_PLAN)["items"]}
    validation = {x["id"]: x for x in load(CAPITAL_VALIDATION)["results"]}
    preceding = load(PRECEDING)
    impact_fees = load(IMPACT_FEES)
    required = MASTER_ORDER + LATER_LEGAL + LATER_INDEPENDENT + UNRESOLVED
    if len(required) != len(set(required)) or set(required) - set(candidates):
        raise ValueError("Reviewed IDs must be unique and present in the inventory")
    if set(MASTER_ORDER[:1] + MASTER_ORDER[2:]) - set(plan):
        raise ValueError("Capital-plan archive evidence is incomplete")
    # The roadway original was independently archived to its topical page; the
    # other five source files were part of the 26-file capital-program batch.
    for candidate_id in MASTER_ORDER[::]:
        row = candidates[candidate_id]
        if row["status"] != "validated" or not row.get("r2_url"):
            raise ValueError(f"Expected validated, archived component: {candidate_id}")
    if not all(validation[x]["byte_identical"] for x in MASTER_ORDER if x in validation):
        raise ValueError("A capital-page component lacks saved byte verification")
    if PAGES.keys() != set(MASTER_ORDER):
        raise ValueError("Every master component needs a saved local page count")
    preceding_nonmembers = {x["candidate_id"] for x in preceding["unrelated_nonmembers"]}
    expected_preceding_nonmembers = set(MASTER_ORDER) - {"src-fecd59ba99e137d1"}
    if preceding_nonmembers != expected_preceding_nonmembers:
        raise ValueError("Preceding GO-boundary decision no longer identifies the expected five CCIP nonmembers")

    components = [source_record(candidates[x], "compilation_component") for x in MASTER_ORDER]
    for order, row in enumerate(components, 1):
        row["order"] = order
    legal = [source_record(candidates[x], "separately_visible_legal_governing_instrument") for x in LATER_LEGAL]
    independent = [source_record(candidates[x], "separately_visible_substantively_independent_record") for x in LATER_INDEPENDENT]
    unresolved = [source_record(candidates[x], "unresolved") for x in UNRESOLVED]
    unresolved[0]["reason"] = "The 2005 Impact Fee Committee CCIP memorandum is a related consultative record, but its existing requires-human-review status and lack of R2 archive remain intact. It is not a 2005--2013 implementation-plan component and cannot be folded into this master."
    for row in legal:
        row["reason"] = "This is an enacted later legal amendment to a different 2012--2022 CCIP period, not a 2005--2013 component-plan document."
    independent[0]["reason"] = "The 2020 credit-holder summary is a later operational record, not a 2005--2013 program-plan component."

    capital_links = links(PAGE.read_text(encoding="utf-8-sig"))
    current_capital = [row for row in components if row["current_archive_url"] in capital_links]
    if len(current_capital) != 5:
        raise ValueError("Expected exactly five current Capital Spending CCIP links")
    if candidates[MASTER_ORDER[1]]["r2_url"] in capital_links:
        raise ValueError("Roadway component should remain a topical-only current placement")

    decision = {
        "schema_version": 1,
        "artifact_type": "2005_2013_impact_fee_ccip_consolidation_decision",
        "reviewed_at": "2026-09-18",
        "state": "research_complete_no_archive_or_page_change_authorized",
        "scope": {
            "page": "content/city-data/capital-spending.md",
            "starting_heading": "Impact-Fee Component Plans",
            "finding": "The five current Capital Spending entries are not the complete package. The separately displayed Roadway Component Capital Implementation Plan is the sixth parallel 2005--2013 implementation-plan component and belongs in the same future historical master.",
            "current_capital_spending_visible_entries": 5,
            "complete_historical_package_components": 6,
            "additional_component_currently_topical_only": "src-fecd59ba99e137d1",
        },
        "source_artifacts": [str(x.relative_to(ROOT)).replace("\\", "/") for x in (PRECEDING, CAPITAL_PLAN, CAPITAL_VALIDATION, IMPACT_FEES)],
        "decision": {
            "result": "one_provenance_preserving_2005_2013_ccip_historical_master_record",
            "rationale": "The overview and five service-system implementation plans are a small, complementary impact-fee CCIP package with a shared 2005--2013 horizon. A master resolves the artificial split that leaves Roadway on a topical page while the other systems are on Capital Spending, without collapsing any originals or their subject-specific access.",
            "provenance_rule": "All six original City PDFs remain individually preserved with their existing official URLs, R2 keys, sizes, checksums, and public byte-verification. Their ordering is organizational only and asserts no adopted/final/superseded relation.",
        },
        "proposed_compilation": {
            "title": "2005--2013 Component Capital Improvement Plan: Historical Master Record",
            "filename": "abqinfo-2005-2013-component-capital-improvement-plan-historical-master-record.pdf",
            "future_r2_key": "city-data/capital-spending/abqinfo-2005-2013-component-capital-improvement-plan-historical-master-record.pdf",
            "component_count": 6,
            "ordering_rule": "Program overview first, then Roadway, Drainage, Public Safety, Open Space/Trails/Recreation, and Park Development implementation plans. It preserves the overview-to-system reading sequence rather than asserting source precedence.",
            "dates_and_implementation_horizon": "The overview is dated 2007; Roadway is inventory-dated 2004; the five service-system plans share the 2005--2013 implementation horizon. These dates are recorded without an adopted/final inference.",
            "components": components,
            "version_relationships": "No duplicate deliveries or distinct versions were found among the six canonical originals. The previously settled duplicate delivery src-4d544b5320a8e8d7 remains a duplicate of the canonical Roadway original and is not a component.",
            "archive_prerequisites": [
                "Obtain separate authorization for a local compilation build and R2 upload.",
                "Create an ABQInfo-labeled cover/index, retain each original without substantive alteration, and record compilation page ranges and source-fidelity QA.",
                "Structurally and visually verify the master, archive it, and publicly byte-verify it before any Capital Spending page change.",
                "Verify a temporary deployment before replacing the five Capital Spending component links.",
            ],
        },
        "separately_visible_legal_governing_instruments": legal,
        "separately_visible_substantively_independent_records": independent,
        "duplicate_or_delivery_records": [{"candidate_id": "src-4d544b5320a8e8d7", "classification": "duplicate_delivery_copy", "canonical_candidate_id": "src-fecd59ba99e137d1", "reason": "Previously settled duplicate R2 representation of the Roadway plan; retain the settled relationship and do not compile the delivery copy."}],
        "unrelated_nonmembers": [{"family": "2004 Council impact-fee adoption, studies, methodology, maps, and committee-comment records", "classification": "unrelated_nonmember", "reason": "The existing impact-fees research identifies this as a distinct 2004 fee-adoption and technical-justification package, with separate legal and unresolved-enactment issues. It is not a 2005--2013 CCIP implementation-plan component family."}],
        "unresolved_records": unresolved,
        "future_capital_spending_treatment": {
            "replace_current_individual_links": [row["current_archive_url"] for row in current_capital],
            "replace_current_link_count": 5,
            "current_visible_entry_count": 5,
            "future_visible_entry_count": 1,
            "expected_reduction_in_visible_entries": 4,
            "future_visible_form": "One clearly labeled ABQInfo historical master record under Impact-Fee Component Plans; later 2012/2013 enacted CCIP resolutions and the 2020 credit-holder summary remain separately visible in their later-record section.",
            "cross_listing_rule": "Keep the individual Drainage original on Stormwater and Drainage; the Open Space/Trails/Recreation and Park Development originals on Parks and Recreation; and the Roadway original on Roadway Studies. Do not redirect those topical placements to the broad master.",
            "not_authorized_now": ["Capital Spending page edit", "R2 upload or mutation", "inventory-status change", "compilation PDF build", "merge", "deployment"],
        },
        "remaining_uncertainties": [
            "The related 2005 Impact Fee Committee CCIP memorandum remains requires human review and unarchived; this decision preserves that state and excludes it from the master.",
            "The separate 2004 Council impact-fee adoption package has unresolved enactment questions and a missing roadway study; it is intentionally outside this 2005--2013 implementation-plan decision.",
        ],
        "safeguards_observed": {"r2_mutation": False, "capital_spending_page_modified": False, "inventory_modified": False, "compilation_built": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(components)} CCIP components")


if __name__ == "__main__":
    main()
