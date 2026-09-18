#!/usr/bin/env python3
"""Regression checks for the 2009 Capital Spending editorial decision."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json"


def main() -> None:
    data = json.loads(DECISION.read_text(encoding="utf-8"))
    master = data["proposed_compilation"]
    components = master["components"]
    ids = [row["candidate_id"] for row in components]
    if len(components) != 24 or len(ids) != len(set(ids)):
        raise AssertionError("Expected exactly 24 unique master components")
    if sum(row["r2_status"] == "verified_public_r2" for row in components) != 20:
        raise AssertionError("Expected twenty current individual R2 originals")
    pending = [row["candidate_id"] for row in components if row["r2_status"] == "not_archived"]
    if pending != ["src-d2d3b593d77a2885", "src-5de108fb850c221f", "src-6fe3ca04cbe476d5", "src-5cea73d2df70dabb"]:
        raise AssertionError("Unarchived independent components changed")
    if len(data["separately_visible_records"]) != 4 or len(data["unrelated_nonmembers"]) != 3:
        raise AssertionError("Legal/nonmember presentation boundary changed")
    streets = ids.index("src-5cea73d2df70dabb"), ids.index("src-5066c9f642369e9b")
    if streets[0] >= streets[1]:
        raise AssertionError("Streets chronology order changed")
    conclusion = data["proposed_compilation"]["version_relationships"][0]["conclusion"]
    if "final/adopted precedence is not" not in conclusion:
        raise AssertionError("Streets finality safeguard changed")
    treatment = data["future_capital_spending_treatment"]
    if treatment["replace_current_link_count"] != 20 or treatment["expected_reduction_in_relevant_visible_entries"] != 19:
        raise AssertionError("Expected visible-entry reduction changed")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Decision records a prohibited side effect")
    print("PASS: 2009 decision preserves 24 components, four legal records, three UETF nonmembers, and the neutral Streets version treatment.")


if __name__ == "__main__":
    main()
