#!/usr/bin/env python3
"""Guard the exact six-original later-MS4 archive plan and its upload gate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("later_ms4_inspection", Path(__file__).with_name("Inspect-LaterMs4ArchivePreparation.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    artifact = load("project-state/discovery/later-ms4-archive-preparation-2026-09-24.json")
    inventory = {row["id"]: row for row in load("project-state/master-inventory.json")["candidates"]}
    keys_expected = (
        "public-works/stormwater-drainage/epa-middle-rio-grande-watershed-ms4-general-permit-2014.pdf",
        "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2016.pdf",
        "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2017.pdf",
        "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2019.pdf",
        "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2020-final.pdf",
        "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2021-final.pdf",
    )
    expected = module.EXPECTED
    completed = (ROOT / 'project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json').exists() and load('project-state/discovery/later-ms4-archive-public-byte-verification-2026-09-25.json').get('state') == 'complete_all_six_public_byte_verified_and_inventory_reconciled'
    implemented = (ROOT / 'project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json').exists()
    validated = (ROOT / 'project-state/discovery/later-ms4-production-closeout-2026-09-25.json').exists() and load('project-state/discovery/later-ms4-production-closeout-2026-09-25.json').get('production_verification_result') == 'passed'
    ids = [item[0] for item in expected]
    assert len(ids) == len(set(ids)) == 6
    assert ids == artifact["candidate_ids_in_order"] == [record["id"] for record in artifact["records"]]
    assert "src-185f33493177b085" not in ids and "src-3408f5b9a86bcb5c" not in ids
    assert inventory["src-185f33493177b085"]["status"] == "superseded"
    assert inventory["src-3408f5b9a86bcb5c"]["status"] == "excluded"
    assert artifact["state"] == "archive_preparation_complete_ready_for_separately_authorized_upload"
    assert artifact["summary"]["total_staged_bytes"] == sum(item[2] for item in expected) == 426926738
    assert artifact["summary"]["pdf_pages_rendered"] == 5917
    assert artifact["summary"]["blockers"] == []
    assert artifact["safeguards"] == {
        "r2_mutation": False, "public_byte_verification_performed": False,
        "visitor_visible_content_changed": False, "site_content_pr_created": False,
        "gated_2014_ms4_package_touched": False,
    }
    assert [(artifact[name]["object_count"], artifact[name]["total_bytes"]) for name in ("saved_r2_snapshot", "live_r2_snapshot")] == [(1231, 8791355104)] * 2
    assert artifact["summary"]["saved_exact_key_collisions"] == artifact["summary"]["live_exact_key_collisions"] == artifact["summary"]["same_size_r2_objects"] == 0
    keys = set()
    for number, ((record_id, filename, size, checksum), record) in enumerate(zip(expected, artifact["records"]), 1):
        row = inventory[record_id]
        path = ROOT / record["staged_original"]
        assert record["order"] == number and record["id"] == record_id
        assert record["staged_original"] == (module.STAGING / filename).relative_to(ROOT).as_posix()
        assert path.stat().st_size == record["size_bytes"] == row["size_bytes"] == size
        assert sha256(path) == record["checksum_sha256"] == row["checksum_sha256"] == checksum
        assert row["status"] == ("validated" if validated else "implemented" if implemented else "placement assigned" if completed else "approved for addition") and row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert row["local_path"] == record["staged_original"]
        assert row["r2_key"] == (record["proposed_r2_key"] if completed else None)
        assert row["r2_url"] == (record["proposed_future_archive_url"] if completed else None)
        assert record["authoritative_source_url"] == row["direct_file_url"]
        assert record["retrieval"] == {"method": "official_source_full_GET_2026-09-24", "http_status": 200, "content_type": "application/pdf", "pdf_magic_verified": True}
        assert record["pdf_qa"]["rendered_pages"] == record["page_count"] and record["pdf_qa"]["structure"] == "opens_without_password_or_repair"
        assert record["pdf_qa"]["visual_result"].startswith("passed_")
        key = record["proposed_r2_key"].casefold()
        assert record["proposed_r2_key"] == keys_expected[number - 1] and key not in keys
        assert record["collision_check"]["saved_exact_key"] is False and record["collision_check"]["live_exact_key"] is False
        assert record["collision_check"]["saved_or_live_same_size_object"] is False and record["collision_check"]["inventory_archived_same_sha256"] is False
        assert not record["r2_mutation"]
        assert record["proposed_future_archive_url"] == "https://files.abqinfo.com/" + record["proposed_r2_key"]
        keys.add(key)
    assert artifact["records"][1]["page_count"] == 173
    assert artifact["records"][5]["page_count"] == 382
    assert "404" in artifact["records"][1]["source_path_history"]
    assert "lowercase" in artifact["records"][4]["source_path_history"]
    assert artifact["future_canonical_page"] == "content/public-works/stormwater-drainage.md"
    print("later-MS4 preparation: exact six IDs, 426,926,738 bytes, 5,917 rendered pages, collision-free, historical upload gate preserved")


if __name__ == "__main__":
    main()
