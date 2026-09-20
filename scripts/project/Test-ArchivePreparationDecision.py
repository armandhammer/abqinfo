#!/usr/bin/env python3
"""Validate a generic archive-preparation decision against inventory/R2 state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()
    path = ROOT / args.decision
    decision = load(path)
    inventory = {row["id"]: row for row in load(ROOT / "project-state/master-inventory.json")["candidates"]}
    r2_keys = {item["key"] for item in load(ROOT / "project-state/r2-inventory.json")["objects"]}
    records = decision["records"]
    assert len(records) == len(decision["scope_candidate_ids"])
    assert {record["id"] for record in records} == set(decision["scope_candidate_ids"])
    for record in records:
        update = record["inventory_update"]
        assert inventory[record["id"]]["status"] == update["status"]
        assert record.get("r2_action") in {None, "none"}
        if record["disposition"] == "approved for addition":
            assessment = record["quality_assessment"]
            for field in ("visual_inspection", "measured_content", "standalone_public_value", "information_density", "series_component_relationship", "intended_publication_form", "rationale"):
                assert assessment.get(field), f"{record['id']} missing {field}"
            prep = record["archive_preparation"]
            assert prep["proposed_r2_key"] not in r2_keys
            assert update["sha256"] == record["source_evidence"]["sha256"]
            assert update["size_bytes"] == record["source_evidence"]["size_bytes"]
            assert inventory[record["id"]]["status"] not in {"implemented", "validated"}
        else:
            assert update["status"] in {"excluded", "duplicate", "superseded", "requires human review"}
            assert update.get("exclusion_reason")
    assert not any(decision["safeguards_observed"].values())
    print(f"PASS: {path.name} validates {len(records)} current archive-preparation decisions without R2 mutation.")


if __name__ == "__main__":
    main()
