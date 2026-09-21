#!/usr/bin/env python3
"""Regression checks for the Capital Spending presentation-review closeout."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "project-state/discovery/capital-spending-consolidation-closeout-status-2026-09-18.json"


def main() -> None:
    data = json.loads(STATUS.read_text(encoding="utf-8"))
    boundaries = data["completed_future_compilation_boundaries"]
    names = [row["family"] for row in boundaries]
    expected = ["2011_preliminary_and_published_program_records", "2009_general_obligation_bond_program", "2007_2016_general_obligation_bond_decade_plan", "2005_2013_component_capital_improvement_plan", "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes"]
    if names != expected:
        raise AssertionError("Closeout no longer covers the five completed compilation decisions")
    if boundaries[0]["visible_entry_transition"] != {"current_visible_component_links": 63, "future_visible_compilation_entries": 2, "expected_reduction": 61}:
        raise AssertionError("2011 transition changed")
    if [row["component_count"] for row in boundaries[1:]] != [24, 18, 6, 6]:
        raise AssertionError("Future compilation boundaries changed")
    resume = data["ordinary_queue_resume"]
    if resume["generated_next_pending_id"] != "src-05ec421cb265b29a" or resume["next_actionable_candidate"]["candidate_id"] != "src-0634d4e49bad3dc6":
        raise AssertionError("Ordinary queue skip/resume guidance changed")
    if data["scope"]["finding"].find("No further consolidation-research candidate remains") < 0:
        raise AssertionError("Closeout must state that the page audit is exhausted")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Closeout records a prohibited side effect")
    print("PASS: Capital Spending closeout covers five future compilation decisions, retained individual records, and the MS4 ordinary-queue skip.")


if __name__ == "__main__":
    main()
