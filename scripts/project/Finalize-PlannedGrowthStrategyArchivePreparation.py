#!/usr/bin/env python3
"""Record completed visual QA and saved/live key checks for the exact PGS batch."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json"
DECISION = ROOT / "project-state/discovery/planned-growth-strategy-decision-2026-09-19.json"
RECOVERY = ROOT / "project-state/discovery/planned-growth-strategy-source-recovery-and-presentation-2026-09-23.json"
INVENTORY = ROOT / "project-state/master-inventory.json"
R2 = ROOT / "project-state/r2-inventory.json"
ORDER = (
    "src-9aeb5f621800da58", "src-08b6b68b53336462", "src-3efa72bc100374a1",
    "src-aee98d2ab382de65", "src-44dedde405c00c2c", "src-bc069f52331eb293",
    "src-c8e6f10731a478e6", "src-cd72192082580abe", "src-765624191ba169bd",
    "src-d15bbc358aeaec4d", "src-8188148b0cd6c40d", "src-0e133db868401e77",
    "src-c771ae9e41b9905c",
)

LIVE_R2 = ROOT / "tmp/pgs-live-r2-inventory-2026-09-23.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    artifact, decision, recovery = load(ARTIFACT), load(DECISION), load(RECOVERY)
    candidates = load(INVENTORY)["candidates"]
    inventory = {r["id"]: r for r in candidates}
    inventory_hashes = defaultdict(list)
    for candidate in candidates:
        if candidate.get("checksum_sha256"):
            inventory_hashes[candidate["checksum_sha256"]].append(candidate["id"])
    saved, live = load(R2), load(LIVE_R2)
    assert len(artifact["records"]) == 13 and [r["id"] for r in artifact["records"]] == list(ORDER)
    assert (saved["object_count"], saved["total_bytes"]) == (live["object_count"], live["total_bytes"])
    saved_keys, live_keys = ({r["key"].casefold() for r in source["objects"]} for source in (saved, live))
    quality = {r["id"]: r["quality_assessment"] for r in decision["dispositions"]["approved_for_addition"]}
    older_part_2_ids = decision["family_relationships"]["part_2_obtainable_files"]
    assert len(older_part_2_ids) == 11
    assert recovery["chapter_3_result"]["recovered"] is True
    assert recovery["combined_part_2_result"]["verified_complete_combined_original_found"] is False
    assert "all 11 named chapters are represented by 12 separate City PDF deliveries" in recovery["final_family_determination"]["part_2_chapter_roster"]
    for record_id in older_part_2_ids:
        # The September 19 assessment is historical; the later recovery controls presentation.
        quality[record_id] = {
            **quality[record_id],
            "rationale": "This substantive City chapter is a component of the complete named Part 2 chapter roster. All 11 named chapters are represented by 12 separate official City PDF deliveries, including recovered Chapter 3.0, and belong in one curated multipart family.",
            "aggregation_rationale": "No verified complete combined Part 2 original has been found. Keeping the 12 separate City originals in documented chapter order preserves provenance without inventing a derivative combined volume.",
            "standalone_exception": "Present this original City delivery with the other Part 2 components in a curated multipart family. Chapter 3.0 is recovered, so no gap warning is required; the chapter series must not be described as an original combined volume.",
        }
    quality[recovery["chapter_3_result"]["inventory_id"]] = recovery["quality_assessment_for_recovered_chapter"]
    warnings = []
    for record in artifact["records"]:
        record_id, key = record["id"], record["proposed_r2_key"]
        row = inventory[record_id]
        staged = ROOT / record["staged_original"]
        assert staged.exists() and staged.stat().st_size == record["size_bytes"] == row["size_bytes"]
        assert sha256(staged) == record["checksum_sha256"] == row["checksum_sha256"]
        assert staged.read_bytes()[:5] == b"%PDF-"
        assert record["authoritative_original_url"] == row["direct_file_url"] == record["final_url"]
        assert "Planned Growth Strategy" in record["pdf_qa"]["pdf_metadata_title"]
        assert record["pdf_qa"]["rendered_pages"] == record["page_count"]
        assert record["pdf_qa"]["low_ink_pages_1_based"] == []
        assert all((ROOT / sheet).exists() for sheet in record["pdf_qa"]["contact_sheets"])
        assert key.casefold() not in saved_keys and key.casefold() not in live_keys
        assert inventory_hashes[record["checksum_sha256"]] == [record_id]
        record["container"] = "PDF"
        record["pdf_version"] = staged.open("rb").read(8).decode("ascii", errors="replace").strip()
        record["quality_assessment"] = quality[record_id]
        record["r2_key_collision"] = False
        record["inventory_sha256_collision"] = False
        record["collision_check"] = "No case-insensitive exact-key collision in saved or read-only live R2 inventory, each 1,218 objects / 8,682,142,612 bytes."
        record["source_identity_check"] = "Official City PDF metadata identifies the Planned Growth Strategy and correct part/chapter; rendered opening and closing pages agree with the settled family manifest. No HTML, redirected, duplicate, or unrelated container observed."
        record["pdf_qa"]["human_contact_sheet_review"] = "passed_all_pages_contact_sheet_reviewed_no_missing_or_obviously_corrupt_page"
        record["preparation_blocker"] = None
        if record_id == "src-9aeb5f621800da58":
            record["pdf_qa"]["review_note"] = "Dense Appendix A capital-cost tables on PDF pages 204-212 appear dark at thumbnail scale. Full-size PDFium and MuPDF renders of representative pages 204, 205, 208 and 211 show readable tables; this is not source corruption."
            record["pdf_qa"]["second_renderer_sample"] = {"renderer": "PDFium", "pdf_pages_1_based": [204, 205, 208, 211], "result": "passed_readable_tables"}
        elif record_id == "src-cd72192082580abe":
            record["pdf_qa"]["review_note"] = "The official Chapter 6 file begins at printed page 203 and ends at 218; the saved table-of-contents range 211-218 understates its start. It is the correct 16-page original and joins Chapter 5, which ends at printed page 202."
            warnings.append("Chapter 6 source pagination 203-218 differs from the saved TOC-derived 211-218 range; identity and source bytes pass.")
        elif record_id in {"src-c8e6f10731a478e6", "src-c771ae9e41b9905c"}:
            record["pdf_qa"]["review_note"] = "MuPDF emitted an embedded color-profile parse warning during rendering; all pages rendered and the contact sheet shows readable, normally colored content."
            warnings.append(f"{record['served_filename']}: nonfatal MuPDF color-profile warning; visual render passed.")
        else:
            record["pdf_qa"]["review_note"] = "Every page rendered; contact sheet review found the expected chapter content, figures/tables, and no obvious missing or corrupt pages."
    artifact["state"] = "archive_preparation_complete_ready_for_separately_authorized_upload"
    artifact["live_r2_inventory_snapshot"] = {k: live[k] for k in ("generated_at", "object_count", "total_bytes")}
    artifact["summary"] = {
        "intended_originals": 13,
        "source_bytes_verified": 13,
        "pdf_structural_checks_passed": 13,
        "pdf_contact_sheet_reviews_passed": 13,
        "pdf_pages_rendered": sum(r["page_count"] for r in artifact["records"]),
        "source_bytes_total": sum(r["size_bytes"] for r in artifact["records"]),
        "r2_key_collisions_saved": 0,
        "r2_key_collisions_live": 0,
        "preparation_blockers": 0,
    }
    assert artifact["summary"]["pdf_pages_rendered"] == 652
    assert artifact["summary"]["source_bytes_total"] == 109212492
    artifact["pdf_qa_attestation"] = {
        "reviewed_at": "2026-09-23",
        "method": "All 652 pages opened and rendered with PyMuPDF; all 16 contact sheets visually inspected. Representative dense Part 1 appendix pages were also rendered at full size with PDFium and PyMuPDF.",
        "result": "passed",
        "nonblocking_observations": warnings,
    }
    artifact["remaining_gates"] = [
        "Obtain separate explicit authorization for R2 upload/storage mutation of precisely these 13 unchanged originals.",
        "After authorized upload, verify each public object against this artifact's exact size and SHA-256 and preserve the official City source URL.",
        "Hugo/content, PR, merge and deployment remain separate stages; preserve the Part 2 chapter-series limitation."
    ]
    save(ARTIFACT, artifact)
    print(json.dumps(artifact["summary"], indent=2))


if __name__ == "__main__":
    main()
