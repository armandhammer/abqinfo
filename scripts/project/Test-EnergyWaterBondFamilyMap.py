#!/usr/bin/env python3
"""Regression checks for the Energy/Water Capital Spending family map."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "project-state/discovery/energy-water-public-facilities-capital-spending-family-map-2026-09-18.json"


def main() -> None:
    data = json.loads(MAP.read_text(encoding="utf-8"))
    records = data["records"]
    ids = [x["candidate_id"] for x in records]
    if len(records) != 27 or len(ids) != len(set(ids)):
        raise AssertionError("Expected exactly 27 unique mapped visible records")
    families = {x["family"]: x for x in data["family_map"]}
    if families["2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes"]["membership_count"] != 6:
        raise AssertionError("Six-cycle Energy/Water family changed")
    if families["2009_general_obligation_bond_program"]["membership_count"] != 10:
        raise AssertionError("2009 mapped membership changed")
    if families["2007_2016_general_obligation_bond_decade_plan"]["membership_count"] != 8:
        raise AssertionError("2007--2016 mapped membership changed")
    if len(data["legal_governing_instruments"]) != 1 or len(data["settled_duplicates_or_delivery_copies"]) != 4:
        raise AssertionError("Legal or settled-delivery boundary changed")
    if data["next_family_to_review"] != "2011_2023_energy_water_public_facilities_system_modernization_cycle_scopes":
        raise AssertionError("Next review family changed")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Family map records a prohibited side effect")
    print("PASS: Energy/Water map preserves 27 visible records across the six-cycle, 2009, 2007, legal, and independent-plan boundaries.")


if __name__ == "__main__":
    main()
