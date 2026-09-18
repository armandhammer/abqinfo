#!/usr/bin/env python3
"""Regression checks for the six-cycle Energy/Water editorial decision."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "project-state/discovery/2011-2023-energy-water-public-facilities-system-modernization-cycle-scopes-decision-2026-09-18.json"
EXPECTED = [
    "src-02e5a5bcff518eca", "src-3cc1912d7ac89cf9", "src-52bda6b47c8295b6",
    "src-3d31dcad9dec671a", "src-62f957e563e55b52", "src-d356c01557a3a067",
]


def main() -> None:
    data = json.loads(DECISION.read_text(encoding="utf-8"))
    compilation = data["proposed_compilation"]
    components = compilation["components"]
    if [row["candidate_id"] for row in components] != EXPECTED:
        raise AssertionError("Six-cycle membership or chronological order changed")
    if len({row["candidate_id"] for row in components}) != 6:
        raise AssertionError("Components must be unique")
    if sum(row["known_component_page_count"] for row in components) != 25:
        raise AssertionError("Expected 25 source pages across the six components")
    if any(row["current_r2_archive_status"] != "publicly_byte_verified" for row in components):
        raise AssertionError("Every component must retain public byte verification")
    treatment = data["future_capital_spending_treatment"]
    if (treatment["current_visible_entry_count"], treatment["future_visible_entry_count"], treatment["expected_reduction_in_visible_entries"]) != (6, 1, 5):
        raise AssertionError("Six-to-one future presentation changed")
    if "No version relationship is established" not in compilation["version_relationships"]:
        raise AssertionError("Decision must not infer cycle precedence")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Decision records a prohibited side effect")
    print("PASS: six distinct Energy/Water election-cycle scopes remain ordered, verified, and proposed as one 25-page-source historical compilation.")


if __name__ == "__main__":
    main()
