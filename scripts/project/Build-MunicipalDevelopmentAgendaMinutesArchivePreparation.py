#!/usr/bin/env python3
"""Build deterministic archive-preparation metadata for the settled AEC/GAATC family."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_PATH = ROOT / "project-state/discovery/municipaldevelopment-agenda-minutes-cluster-research-2026-09-12.json"
DECISION_PATH = ROOT / "project-state/discovery/municipaldevelopment-agenda-minutes-family-decision-2026-09-20.json"
INVENTORY_PATH = ROOT / "project-state/master-inventory.json"
R2_PATH = ROOT / "project-state/r2-inventory.json"
OUTPUT_PATH = ROOT / "project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json"

MISSING_LABEL = "Agenda (approved minutes not located). It must never be presented as minutes."


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def aec_filename(item: dict) -> str:
    date = item["date"]
    title = item["title"].lower()
    if "agenda and meeting minutes" in title:
        kind = "agenda-and-minutes"
    elif "agenda" in title:
        kind = "agenda"
    else:
        kind = "minutes"
    return f"cabq-albuquerque-energy-council-{kind}-{date}.pdf"


def quality(item: dict, orphan: bool) -> dict:
    if orphan:
        value = "Limited but sufficient: the verified surviving official agenda after the recorded exhaustive official-source review did not locate approved minutes."
        density = "One-page agenda; the missing-minutes exception and meeting-series context provide the required limited-content exception."
        relationship = "Verified orphan agenda preserved only under the missing-minutes policy; it is not minutes and does not establish that the meeting occurred."
        form = "One separately labeled original agenda in the Albuquerque Energy Council meeting-record series after authorized archival and public-byte verification."
        rationale = "The City-hosted agenda is the only identified official trace for this scheduled meeting after the saved exhaustive review; the warning must travel with the item."
    elif item["id"] == "src-95460bead0e780ee":
        value = "High: the 78-page packet preserves the earliest identified GAATC minutes and extends the maintained minutes history backward."
        density = "Substantive meeting packet: pages 3 onward contain the minutes and the packet supplies supporting meeting material."
        relationship = "Earliest retained GAATC meeting packet, complementing the existing minutes-only series without duplicating its later records."
        form = "One separately labeled original meeting packet in the Greater Albuquerque Active Transportation Committee minutes series after authorized archival and public-byte verification."
        rationale = "The packet carries actual meeting minutes, has high information density, and fills a documented early gap in the maintained GAATC history."
    else:
        value = "High: approved meeting minutes are the primary official record for the meeting."
        density = "Short minutes qualify through the meeting-record limited-content exception; every page carries substantive action or attendance content."
        relationship = "Minutes retained in preference to the same-meeting agenda where one exists; part of the chronological Albuquerque Energy Council series."
        form = "One separately labeled original minutes record in the Albuquerque Energy Council meeting-record series after authorized archival and public-byte verification."
        rationale = "Approved minutes provide the strongest available record of the meeting and supersede the corresponding agenda as a standalone archive item."
    return {
        "visual_inspection": item["evidence"],
        "measured_content": f"{item['pages']} pages; {item['size_bytes']} bytes; SHA-256 {item['checksum_sha256']}.",
        "standalone_public_value": value,
        "information_density": density,
        "series_component_relationship": relationship,
        "intended_publication_form": form,
        "rationale": rationale,
    }


def main() -> None:
    research = load(RESEARCH_PATH)
    decision = load(DECISION_PATH)
    inventory = {row["id"]: row for row in load(INVENTORY_PATH)["candidates"]}
    r2_keys = {row["key"] for row in load(R2_PATH)["objects"]}
    approved = research["approved_for_addition"]
    assert len(approved) == 18
    assert set(row["id"] for row in approved) == set(decision["dispositions"]["approved_for_addition"])

    records = []
    for item in approved:
        candidate = inventory[item["id"]]
        assert candidate["status"] == "approved for addition", item["id"]
        orphan = bool(item.get("preserved_under_the_missing_minutes_policy"))
        gaatc = item["id"] == "src-95460bead0e780ee"
        filename = "cabq-greater-albuquerque-active-transportation-committee-minutes-packet-2023-07-10.pdf" if gaatc else aec_filename(item)
        prefix = "transportation/bicycling" if gaatc else "city-data/climate-environment"
        key = f"{prefix}/{filename}"
        assert key not in r2_keys, f"R2 key collision: {key}"
        cross = (
            {"decision": "approved_for_future_archive_first_publication", "page": "content/public-works/city-facilities.md", "section": "Energy and city facilities", "reason": "The Energy Council's City-facility and energy business is independently useful on this page."}
            if not gaatc else
            {"decision": "rejected_for_future_publication", "page": None, "section": None, "reason": "The bicycling page is the clear home; a second listing would repeat a committee record without a distinct audience."}
        )
        records.append({
            "id": item["id"],
            "status": candidate["status"],
            "accepted_title": candidate["title"],
            "authoritative_source_url": item["authoritative_url"],
            "direct_original_file_url": item.get("raw_file_url", item["authoritative_url"]),
            "date": item["date"],
            "file_type": "PDF",
            "size_bytes": item["size_bytes"],
            "checksum_sha256": item["checksum_sha256"],
            "page_count": item["pages"],
            "container": "PDF",
            "leading_bytes": item["leading_bytes"],
            "quality_assessment": quality(item, orphan),
            "series_family_relationship": "Greater Albuquerque Active Transportation Committee minutes series." if gaatc else "Albuquerque Energy Council chronological meeting-record series.",
            "missing_minutes_label": MISSING_LABEL if orphan else None,
            "meeting_occurrence_caveat": "Agenda alone is not evidence that the meeting occurred; no such occurrence is asserted." if orphan else None,
            "canonical_placement": {
                "page": "content/transportation/bicycling/_index.md" if gaatc else "content/city-data/climate-environment.md",
                "section": "Greater Albuquerque Active Transportation Committee meeting records" if gaatc else "Albuquerque Energy Council meeting records",
                "decision": "approved_for_future_archive_first_publication",
            },
            "cross_listing": cross,
            "proposed_canonical_archive_filename": filename,
            "proposed_r2_key": key,
            "collision_check": "No exact proposed-key collision in project-state/r2-inventory.json; saved research found no R2-object or checksummed-inventory byte collision.",
            "remaining_gates": [
                "Obtain explicit authorization before any R2 upload, overwrite, or other storage mutation.",
                "Archive the original unchanged at the proposed key, then verify public download size and SHA-256 while retaining the City source URL.",
                "Only after public-byte verification, make the separately authorized public-content edit; do not mark this inventory-only record implemented or validated before then.",
            ],
        })

    artifact = {
        "schema_version": 1,
        "artifact_type": "municipal_development_agenda_minutes_archive_preparation",
        "recorded_at": "2026-09-20",
        "source_research": str(RESEARCH_PATH.relative_to(ROOT)).replace("\\", "/"),
        "family_decision": str(DECISION_PATH.relative_to(ROOT)).replace("\\", "/"),
        "state": "approved_for_addition_archive_preparation_complete_external_archive_and_publication_gated",
        "scope_candidate_ids": [row["id"] for row in approved],
        "family_assessment": {
            "relationship": "AEC minutes are the preferred records where available; ten verified orphan agendas remain separately labeled under the missing-minutes policy; the GAATC packet extends an established minutes series.",
            "publication_form": "If archive authorization and exact public-byte verification later pass, group the AEC records as a chronological meeting-record series and the GAATC packet with its minutes series. Do not represent an agenda as minutes or as proof the meeting occurred.",
        },
        "archive_publication_gates": [
            "No R2 mutation is authorized by this preparation artifact.",
            "No public Hugo content edit is authorized by this preparation artifact.",
            "Each original requires unchanged archival and exact public-byte verification before implementation or validation.",
        ],
        "records": records,
        "summary": {"prepared_records": len(records), "missing_minutes_agendas": sum(row["missing_minutes_label"] is not None for row in records), "r2_key_collisions": 0},
        "safeguards_observed": {"r2_mutation": False, "public_content_changed": False, "merge_or_deploy": False},
    }
    write(OUTPUT_PATH, artifact)
    print(json.dumps(artifact["summary"], indent=2))


if __name__ == "__main__":
    main()
