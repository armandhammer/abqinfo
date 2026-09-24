#!/usr/bin/env python3
"""Guard the single curated PGS section and its 13 verified source/archive pairs."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "project-state/discovery"
PAGE = ROOT / "content/development-land-use/area-sector-plans.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    prepared = load(DISCOVERY / "planned-growth-strategy-archive-preparation-2026-09-23.json")
    verified = load(DISCOVERY / "planned-growth-strategy-archive-public-byte-verification-2026-09-23.json")
    implemented = load(DISCOVERY / "planned-growth-strategy-hugo-implementation-2026-09-23.json")
    decision = load(DISCOVERY / "planned-growth-strategy-decision-2026-09-19.json")
    inventory = {row["id"]: row for row in load(ROOT / "project-state/master-inventory.json")["candidates"]}
    page = PAGE.read_bytes().decode("utf-8-sig")
    heading = "## Citywide Growth Strategy"
    assert page.count(heading) == 1
    section = page.split(heading, 1)[1].split("\n## ", 1)[0]
    section = heading + section
    assert hashlib.sha256(section.encode("utf-8")).hexdigest() == implemented["section_sha256"]
    assert implemented["state"] == "implemented_on_planning_branch_not_live"
    assert implemented["page"] == "content/development-land-use/area-sector-plans.md"
    assert implemented["section"] == "Citywide Growth Strategy"
    assert implemented["archive_links"] == implemented["official_city_source_links"] == 13
    assert implemented["pr_created"] is implemented["merge_or_deploy"] is implemented["production_verified"] is False
    assert verified["state"] == "complete_all_13_public_byte_verified_and_inventory_reconciled"
    records = prepared["records"]
    assert len(records) == 13 and implemented["implemented_inventory_ids"] == [row["id"] for row in records]
    assert len(re.findall(r"(?m)^\d+\. \[Chapter ", section)) == 12
    assert "Complete Findings Report (286 Pages)" in section
    assert all(phrase in section for phrase in (
        "historical City and County study", "All 11 named chapters", "12 files",
        "No verified complete combined Part 2 original", "documented order rather than as a merged PDF",
    ))
    assert not re.search(r"Chapter 3(?:\.0)?[^\n.]{0,60}(?:missing|unavailable|gap)", section, re.I)
    assert "/Part2.pdf" not in section
    assert len(re.findall(r"https://files\.abqinfo\.com/[^)]+\.pdf", section)) == 13
    assert len(re.findall(r"https://www\.cabq\.gov/council/documents/pgs/[^)]+\.pdf", section)) == 13
    archive_positions = []
    for record in records:
        row = inventory[record["id"]]
        archive_url = record["proposed_future_archive_url"]
        city_url = record["authoritative_original_url"]
        assert section.count(archive_url) == section.count(city_url) == 1, record["id"]
        archive_positions.append(section.index(archive_url))
        assert section.index(archive_url) < section.index(city_url), record["id"]
        assert row["status"] == "implemented" and row["implementation_location"] == implemented["page"]
        assert row["implementation_locations"] == [implemented["page"]]
        assert row["r2_url"] == archive_url and row["direct_file_url"] == city_url
        assert row["r2_key"] == record["proposed_r2_key"]
    assert archive_positions == sorted(archive_positions)
    for duplicate_id in decision["family_relationships"]["part_1_duplicate_components"]:
        duplicate = inventory[duplicate_id]
        assert duplicate["direct_file_url"] not in section
    print("PASS: one PGS Citywide Growth Strategy section contains 13 ordered archive/City-source pairs, a complete Part 1 original, and a separate 12-file/11-chapter Part 2 series; all 13 records are branch-implemented only.")


if __name__ == "__main__":
    main()
