#!/usr/bin/env python3
"""Regression checks for the 2005--2013 CCIP editorial decision."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "project-state/discovery/2005-2013-impact-fee-ccip-consolidation-decision-2026-09-18.json"


def main() -> None:
    data = json.loads(DECISION.read_text(encoding="utf-8"))
    components = data["proposed_compilation"]["components"]
    ids = [row["candidate_id"] for row in components]
    if len(ids) != 6 or len(ids) != len(set(ids)):
        raise AssertionError("Expected six unique CCIP components")
    if "src-fecd59ba99e137d1" not in ids:
        raise AssertionError("Roadway component must remain part of the complete CCIP package")
    if any(row["current_r2_archive_status"] != "publicly_byte_verified" for row in components):
        raise AssertionError("Every component must retain public byte verification")
    if sum(row["known_component_page_count"] for row in components) != 8:
        raise AssertionError("Expected eight source pages across the six components")
    treatment = data["future_capital_spending_treatment"]
    if treatment["current_visible_entry_count"] != 5 or treatment["future_visible_entry_count"] != 1:
        raise AssertionError("Expected five-to-one Capital Spending treatment changed")
    if len(data["separately_visible_legal_governing_instruments"]) != 2 or len(data["unresolved_records"]) != 1:
        raise AssertionError("Later legal records or unresolved CCIP memorandum boundary changed")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Decision records a prohibited side effect")
    print("PASS: CCIP decision preserves six components, the Roadway member, later legal records, and the unresolved committee memorandum gate.")


if __name__ == "__main__":
    main()
