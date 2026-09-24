#!/usr/bin/env python3
"""Guard PGS production evidence and the exact 13-record validated transition."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "project-state/discovery"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    closeout = load(DISCOVERY / "planned-growth-strategy-production-closeout-2026-09-24.json")
    prepared = load(DISCOVERY / "planned-growth-strategy-archive-preparation-2026-09-23.json")
    archived = load(DISCOVERY / "planned-growth-strategy-archive-public-byte-verification-2026-09-23.json")
    inventory = load(ROOT / "project-state/master-inventory.json")
    rows = {row["id"]: row for row in inventory["candidates"]}
    records = prepared["records"]
    ids = [record["id"] for record in records]
    assert len(ids) == len(set(ids)) == 13
    assert closeout["pr_number"] == 168 and closeout["pr_state"] == "merged_manual_user_review"
    assert closeout["merge_commit_sha"] == "8cfba47b46a464a04f67b1fccbe3943dd30b74c9"
    assert closeout["production_page_url"] == "https://abqinfo.com/development-land-use/area-sector-plans/"
    assert closeout["production_http_status"] == 200 and closeout["production_verification_result"] == "passed"
    assert closeout["verified_section_heading"] == "Citywide Growth Strategy"
    assert closeout["expected_archive_link_count"] == closeout["verified_archive_link_count"] == 13
    assert closeout["expected_official_source_link_count"] == closeout["verified_official_source_link_count"] == 13
    assert closeout["ordered_inventory_ids"] == ids
    assert closeout["ordered_archive_and_official_source_links_match_preparation"] is True
    assert closeout["chapter_3_present"] is True and "src-44dedde405c00c2c" in ids
    assert closeout["verified_complete_combined_part_2_original"] is False
    assert closeout["unrelated_part2_pdf_exposed"] is closeout["stale_chapter_3_gap_language"] is False
    assert closeout["r2_mutation_during_closeout"] is closeout["visitor_visible_content_modified_during_closeout"] is False
    assert closeout["final_inventory_status"] == "validated" and closeout["family_state"] == "complete_live"
    assert archived["summary"]["public_byte_verified"] == 13
    for record in records:
        row = rows[record["id"]]
        assert row["status"] == "validated" and row["validation_status"].startswith("Passed: PR #168 merged;")
        assert row["implementation_location"] == "content/development-land-use/area-sector-plans.md"
        assert row["direct_file_url"] == record["authoritative_original_url"]
        assert row["r2_url"] == record["proposed_future_archive_url"]
        assert row["r2_key"] == record["proposed_r2_key"]
        assert row["size_bytes"] == record["size_bytes"] and row["checksum_sha256"] == record["checksum_sha256"]
        assert row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert any("PGS production closeout 2026-09-24" in note for note in row["processing_notes"])
    print("PASS: PGS production closeout preserves 13 exact archived originals and 13 validated live inventory records.")


if __name__ == "__main__":
    main()
