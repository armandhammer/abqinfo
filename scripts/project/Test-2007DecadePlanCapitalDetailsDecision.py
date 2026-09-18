#!/usr/bin/env python3
"""Regression checks for the 2007--2016 Capital Spending editorial decision."""

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "project-state/discovery/2007-2016-capital-details-consolidation-decision-2026-09-18.json"

def main() -> None:
    data = json.loads(DECISION.read_text(encoding="utf-8"))
    components = data["proposed_compilation"]["components"]
    ids = [row["candidate_id"] for row in components]
    if len(ids) != 18 or len(ids) != len(set(ids)):
        raise AssertionError("Expected exactly 18 unique GO decade-plan components")
    if any(row["current_r2_archive_status"] != "publicly_byte_verified" for row in components):
        raise AssertionError("Every component must retain saved public byte verification")
    if len(data["separately_visible_legal_governing_instruments"]) != 1:
        raise AssertionError("Policies/criteria must remain separately visible")
    if len(data["separately_visible_substantively_independent_records"]) != 2:
        raise AssertionError("Enterprise and redevelopment records must remain individual")
    if len(data["unrelated_nonmembers"]) != 5:
        raise AssertionError("Impact-fee component plans must remain outside this GO family")
    treatment = data["future_capital_spending_treatment"]
    if treatment["current_go_decade_plan_visible_entries"] != 21 or treatment["future_go_decade_plan_visible_entries"] != 4:
        raise AssertionError("Expected 21-to-4 presentation treatment changed")
    if treatment["expected_reduction_in_visible_entries"] != 17:
        raise AssertionError("Expected visible-entry reduction changed")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Decision records a prohibited side effect")
    print("PASS: 2007--2016 decision preserves 18 GO components, three individual records, and five impact-fee nonmembers.")

if __name__ == "__main__":
    main()
