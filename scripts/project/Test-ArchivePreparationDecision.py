#!/usr/bin/env python3
"""Validate a generic archive-preparation decision against inventory/R2 state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_FIELDS = {
    "status", "title", "source_url", "direct_file_url", "description",
    "date", "file_type", "checksum_sha256", "size_bytes",
    "validation_status", "exclusion_reason", "processing_notes",
    "cited_successors", "implementation_locations", "cross_listing_approved",
}
FORBIDDEN_ALIASES = {"document_date", "content_type", "sha256", "content_length"}


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
    stray = [(candidate_id, alias) for candidate_id, row in inventory.items() for alias in FORBIDDEN_ALIASES if alias in row]
    assert not stray, f"Inventory contains noncanonical archive-preparation aliases: {stray[:5]}"
    scope = decision.get("scope_candidate_ids") or decision.get("starting_candidate_ids")
    assert scope, "Decision needs an explicit candidate scope"
    assert len(records) == len(scope)
    assert {record["id"] for record in records} == set(scope)
    for record in records:
        update = record["inventory_update"]
        assert not (set(update) & FORBIDDEN_ALIASES), f"{record['id']} uses noncanonical inventory aliases"
        assert set(update) <= CANONICAL_FIELDS, f"{record['id']} uses unsupported inventory fields"
        assert inventory[record["id"]]["status"] == update["status"]
        assert record.get("r2_action") in {None, "none"}
        if record["disposition"] == "approved for addition":
            assessment = record["quality_assessment"]
            for field in ("visual_inspection", "measured_content", "standalone_public_value", "information_density", "series_component_relationship", "intended_publication_form", "rationale"):
                assert assessment.get(field), f"{record['id']} missing {field}"
            prep = record["archive_preparation"]
            assert prep["proposed_r2_key"] not in r2_keys
            assert update["checksum_sha256"] == record["source_evidence"]["sha256"]
            assert update["size_bytes"] == record["source_evidence"]["size_bytes"]
            assert inventory[record["id"]]["status"] not in {"implemented", "validated"}
        else:
            assert update["status"] in {"excluded", "duplicate", "superseded", "requires human review"}
            assert update.get("exclusion_reason")
    assert not any(decision["safeguards_observed"].values())
    print(f"PASS: {path.name} validates {len(records)} current archive-preparation decisions without R2 mutation.")


if __name__ == "__main__":
    main()
