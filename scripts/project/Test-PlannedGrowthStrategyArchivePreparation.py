#!/usr/bin/env python3
"""Guard the exact 13-original PGS preparation and its presentation/R2 gates."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def main() -> None:
    artifact = load("project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json")
    inventory = {r["id"]: r for r in load("project-state/master-inventory.json")["candidates"]}
    r2 = load("project-state/r2-inventory.json")
    decision = load("project-state/discovery/planned-growth-strategy-decision-2026-09-19.json")
    recovery = load("project-state/discovery/planned-growth-strategy-source-recovery-and-presentation-2026-09-23.json")
    archive_path = "project-state/discovery/planned-growth-strategy-archive-public-byte-verification-2026-09-23.json"
    archive = load(archive_path) if (ROOT / archive_path).exists() else None
    expected = [
        ("src-9aeb5f621800da58", "Part1.pdf", 286),
        ("src-08b6b68b53336462", "Part2-1a.pdf", 56),
        ("src-3efa72bc100374a1", "Part2-1b.pdf", 22),
        ("src-aee98d2ab382de65", "Part2-2.pdf", 48),
        ("src-44dedde405c00c2c", "part2-3.pdf", 19),
        ("src-bc069f52331eb293", "Part2-4.pdf", 12),
        ("src-c8e6f10731a478e6", "Part2-5.pdf", 35),
        ("src-cd72192082580abe", "Part2-6.pdf", 16),
        ("src-765624191ba169bd", "Part2-7.pdf", 26),
        ("src-d15bbc358aeaec4d", "Part2-8.pdf", 20),
        ("src-8188148b0cd6c40d", "Part2-9.pdf", 16),
        ("src-0e133db868401e77", "Part2-10.pdf", 63),
        ("src-c771ae9e41b9905c", "Part2-11.pdf", 33),
    ]
    expected_ids = {decision["family_relationships"]["part_1_canonical"], *decision["family_relationships"]["part_2_obtainable_files"], recovery["chapter_3_result"]["inventory_id"]}
    records = artifact["records"]
    assert len(records) == 13 and len(expected_ids) == 13
    assert [(r["id"], r["served_filename"], r["page_count"]) for r in records] == expected
    assert {r["id"] for r in records} == expected_ids == set(artifact["scope_candidate_ids"])
    assert artifact["state"] == "archive_preparation_complete_ready_for_separately_authorized_upload"
    assert all(phrase in artifact["family_presentation_limit"] for phrase in (
        "12 separate City originals", "No verified complete combined Part 2 original", "Do not describe these 12 chapter files as an original combined volume"
    ))
    assert artifact["future_canonical_page"] == "content/development-land-use/area-sector-plans.md"
    assert artifact["summary"] == {
        "intended_originals": 13,
        "source_bytes_verified": 13,
        "pdf_structural_checks_passed": 13,
        "pdf_contact_sheet_reviews_passed": 13,
        "pdf_pages_rendered": 652,
        "source_bytes_total": 109212492,
        "r2_key_collisions_saved": 0,
        "r2_key_collisions_live": 0,
        "preparation_blockers": 0,
    }
    assert artifact["pdf_qa_attestation"]["result"] == "passed"
    assert artifact["r2_inventory_snapshot"]["object_count"] == artifact["live_r2_inventory_snapshot"]["object_count"] == 1218
    assert artifact["r2_inventory_snapshot"]["total_bytes"] == artifact["live_r2_inventory_snapshot"]["total_bytes"] == 8682142612
    if archive:
        assert archive["state"] == "complete_all_13_public_byte_verified_and_inventory_reconciled"
        assert archive["summary"] == {"intended": 13, "uploaded_now": 13, "already_present_identical": 0, "public_byte_verified": 13, "added_bytes": 109212492}
        assert archive["before_r2"]["object_count"] == 1218 and archive["before_r2"]["total_bytes"] == 8682142612
        assert archive["after_r2"]["object_count"] == r2["object_count"] == 1231
        assert archive["after_r2"]["total_bytes"] == r2["total_bytes"] == 8791355104
        assert {result["id"] for result in archive["results"]} == expected_ids and len(archive["results"]) == 13
        results = {result["id"]: result for result in archive["results"]}
        objects = {obj["key"]: obj for obj in r2["objects"]}
    else:
        assert r2["object_count"] == 1218 and r2["total_bytes"] == 8682142612
    keys, hashes = set(), set()
    saved_r2_keys = {obj["key"].casefold() for obj in r2["objects"]}
    for n, record in enumerate(records, 1):
        row = inventory[record["id"]]
        assert record["order"] == n and record["container"] == "PDF" and record["pdf_version"].startswith("%PDF-")
        assert record["http_status"] == 200 and record["pdf_magic_verified"] is True
        assert record["final_url"] == record["authoritative_original_url"] == row["direct_file_url"]
        assert record["authoritative_original_url"].startswith("https://www.cabq.gov/council/documents/pgs/")
        assert record["size_bytes"] == row["size_bytes"] and record["checksum_sha256"] == row["checksum_sha256"]
        assert record["checksum_sha256"] not in hashes
        hashes.add(record["checksum_sha256"])
        assert row["status"] == ("placement assigned" if archive else "approved for addition")
        assert row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert row["local_path"] == record["staged_original"]
        if archive:
            result = results[record["id"]]
            obj = objects[record["proposed_r2_key"]]
            assert result["action"] == "uploaded_now" and result["http_public_get"] == "passed" and result["byte_identical"] is True
            assert result["source_url"] == record["authoritative_original_url"] == row["direct_file_url"]
            assert result["public_url"] == record["proposed_future_archive_url"] == row["r2_url"] == obj["public_url"]
            assert result["r2_key"] == row["r2_key"] == obj["key"]
            assert result["expected_size_bytes"] == result["public_size_bytes"] == obj["size_bytes"] == record["size_bytes"]
            assert result["expected_checksum_sha256"] == result["public_checksum_sha256"] == record["checksum_sha256"]
            assert row["r2_etag"] == obj["etag"] and row["r2_last_modified"] == obj["last_modified"]
            assert "public R2 bytes match exact size and SHA-256" in row["validation_status"]
        else:
            assert "archive preparation complete" in row["validation_status"]
            assert row["r2_key"] is None and row["r2_url"] is None
        assert record["proposed_future_archive_url"] == "https://files.abqinfo.com/" + record["proposed_r2_key"]
        assert record["proposed_r2_key"].startswith("development-land-use/area-sector-plans/")
        if not archive:
            assert record["proposed_r2_key"].casefold() not in keys | saved_r2_keys
        keys.add(record["proposed_r2_key"].casefold())
        assert record["r2_key_collision"] is False and record["inventory_sha256_collision"] is False
        assert record["r2_action"] == "none" and record["preparation_blocker"] is None
        assert record["pdf_qa"]["rendered_pages"] == record["page_count"]
        assert record["pdf_qa"]["low_ink_pages_1_based"] == []
        assert record["pdf_qa"]["human_contact_sheet_review"].startswith("passed_")
        assert record["quality_assessment"] and record["source_identity_check"]
        staged = ROOT / record["staged_original"]
        if staged.exists():
            digest = hashlib.sha256(staged.read_bytes()).hexdigest()
            assert staged.stat().st_size == record["size_bytes"] and digest == record["checksum_sha256"]
    assert records[4]["checksum_sha256"] == "56401ff3c1a17c2e19465c8b71f7b2afa893ad00e20a2bf6a5e92a66e60e1b08"
    assert records[4]["size_bytes"] == 6068014
    assert recovery["chapter_3_result"]["recovered"] is True
    assert recovery["combined_part_2_result"]["verified_complete_combined_original_found"] is False
    assert records[4]["quality_assessment"] == recovery["quality_assessment_for_recovered_chapter"]
    older_part_2_ids = set(decision["family_relationships"]["part_2_obtainable_files"])
    assert len(older_part_2_ids) == 11
    for record in records[1:]:
        prose = " ".join(str(value) for value in record["quality_assessment"].values() if isinstance(value, str)).casefold()
        assert not any(phrase in prose for phrase in (
            "unavailable summary chapter", "permanent chapter 3.0 gap",
            "permanently lacks chapter 3.0", "missing-chapter notice",
        )), record["id"]
        assert not re.search(r"chapter 3(?:\.0)? (?:is |remains )?(?:unavailable|missing|absent|not found|not located)", prose), record["id"]
        if record["id"] in older_part_2_ids:
            assert all(phrase in prose for phrase in (
                "11 named chapters", "12 separate official city pdf deliveries", "recovered chapter 3.0",
                "no verified complete combined part 2 original", "curated multipart family",
            )), record["id"]
    assert all(value is False for value in artifact["safeguards_observed"].values())
    assert not any("Part1-" in r["served_filename"] or r["served_filename"] == "Part2.pdf" for r in records)
    print("PASS: PGS has exactly 13 City originals, 109,212,492 source bytes, 652 previously rendered pages, and " + ("13/13 exact public-byte-verified R2 objects with no content change." if archive else "zero prepared R2 key collisions with no upload/publication action."))


if __name__ == "__main__":
    main()
