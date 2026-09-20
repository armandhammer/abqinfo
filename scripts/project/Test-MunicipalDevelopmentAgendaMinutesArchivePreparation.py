#!/usr/bin/env python3
"""Validate settled AEC/GAATC archive-preparation metadata."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json"
DECISION = ROOT / "project-state/discovery/municipaldevelopment-agenda-minutes-family-decision-2026-09-20.json"
INVENTORY = ROOT / "project-state/master-inventory.json"
R2 = ROOT / "project-state/r2-inventory.json"
LABEL = "Agenda (approved minutes not located). It must never be presented as minutes."

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

artifact = load(ARTIFACT)
decision = load(DECISION)
inventory = {row["id"]: row for row in load(INVENTORY)["candidates"]}
r2_keys = {row["key"] for row in load(R2)["objects"]}
expected = set(decision["dispositions"]["approved_for_addition"])
records = {row["id"]: row for row in artifact["records"]}

assert artifact["state"] == "approved_for_addition_archive_preparation_complete_external_archive_and_publication_gated"
assert len(records) == 18 and set(records) == expected
assert artifact["summary"] == {"prepared_records": 18, "missing_minutes_agendas": 10, "r2_key_collisions": 0}
assert not any(artifact["safeguards_observed"].values())
for candidate_id, record in records.items():
    candidate = inventory[candidate_id]
    assert candidate["status"] == record["status"] == "approved for addition"
    for field in ("date", "file_type", "size_bytes", "checksum_sha256"):
        assert candidate[field] == record[field], f"{candidate_id}: {field} drifted"
    assert record["authoritative_source_url"] == candidate["source_url"]
    assert record["direct_original_file_url"] == candidate["direct_file_url"]
    assert record["proposed_r2_key"] not in r2_keys
    assert candidate["r2_key"] is None and candidate["r2_url"] is None
    assert candidate["implementation_location"] is None and not candidate["implementation_locations"]
    assert record["canonical_placement"]["page"]
    assert record["canonical_placement"]["section"]
    assert record["cross_listing"]["decision"]
    for field in ("visual_inspection", "measured_content", "standalone_public_value", "information_density", "series_component_relationship", "intended_publication_form", "rationale"):
        assert record["quality_assessment"][field], f"{candidate_id}: missing {field}"
orphans = [row for row in records.values() if row["missing_minutes_label"]]
assert len(orphans) == 10
for record in orphans:
    assert record["missing_minutes_label"] == LABEL
    assert record["meeting_occurrence_caveat"] == "Agenda alone is not evidence that the meeting occurred; no such occurrence is asserted."
print("PASS: 18 settled Municipal Development records have complete archive preparation; ten agendas preserve their exact missing-minutes warning.")
