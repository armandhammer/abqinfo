#!/usr/bin/env python3
"""Re-fetch and inspect the exact 13 City PGS originals; do not mutate R2."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "research/staging/planned-growth-strategy-archive-preparation-2026-09-23"
QA_DIR = ROOT / "tmp/pgs-archive-qa-2026-09-23"
LEDGER = STAGING / "source-verification-ledger.json"
ARTIFACT = ROOT / "project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json"
INVENTORY = ROOT / "project-state/master-inventory.json"
R2 = ROOT / "project-state/r2-inventory.json"
DECISION = ROOT / "project-state/discovery/planned-growth-strategy-decision-2026-09-19.json"
RECOVERY = ROOT / "project-state/discovery/planned-growth-strategy-source-recovery-and-presentation-2026-09-23.json"
ORDER = (
    ("src-9aeb5f621800da58", "Part1.pdf", "Part 1 complete", 286, "part-1-findings-report"),
    ("src-08b6b68b53336462", "Part2-1a.pdf", "Part 2 Chapter 1.0a", 56, "part-2-chapter-01a-introduction-rationale"),
    ("src-3efa72bc100374a1", "Part2-1b.pdf", "Part 2 Chapter 1.0b", 22, "part-2-chapter-01b-introduction-rationale"),
    ("src-aee98d2ab382de65", "Part2-2.pdf", "Part 2 Chapter 2.0", 48, "part-2-chapter-02-subarea-descriptions"),
    ("src-44dedde405c00c2c", "part2-3.pdf", "Part 2 Chapter 3.0", 19, "part-2-chapter-03-preferred-alternative-summary"),
    ("src-bc069f52331eb293", "Part2-4.pdf", "Part 2 Chapter 4.0", 12, "part-2-chapter-04-mixed-use-redevelopment-examples"),
    ("src-c8e6f10731a478e6", "Part2-5.pdf", "Part 2 Chapter 5.0", 35, "part-2-chapter-05-level-of-service-standards"),
    ("src-cd72192082580abe", "Part2-6.pdf", "Part 2 Chapter 6.0", 16, "part-2-chapter-06-financial-implementation"),
    ("src-765624191ba169bd", "Part2-7.pdf", "Part 2 Chapter 7.0", 26, "part-2-chapter-07-regulatory-structure-approaches"),
    ("src-d15bbc358aeaec4d", "Part2-8.pdf", "Part 2 Chapter 8.0", 20, "part-2-chapter-08-level-of-service-and-finance"),
    ("src-8188148b0cd6c40d", "Part2-9.pdf", "Part 2 Chapter 9.0", 16, "part-2-chapter-09-city-county-requirements"),
    ("src-0e133db868401e77", "Part2-10.pdf", "Part 2 Chapter 10.0", 63, "part-2-chapter-10-growth-strategy-techniques"),
    ("src-c771ae9e41b9905c", "Part2-11.pdf", "Part 2 Chapter 11.0", 33, "part-2-chapter-11-regulatory-structure-outline"),
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, target: Path) -> tuple[int, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ABQInfo archival source verification)"})
    temporary = target.with_name(target.name + ".part")
    with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as stream:
        code, final_url, content_type = response.status, response.url, response.headers.get("Content-Type", "")
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            stream.write(chunk)
    if code != 200 or not temporary.open("rb").read(5).startswith(b"%PDF-"):
        temporary.unlink(missing_ok=True)
        raise ValueError(f"Non-PDF or non-200 source response: {code} {url} {content_type}")
    temporary.replace(target)
    return code, final_url, content_type


def inspect_pdf(path: Path, expected_pages: int, qa_prefix: str, fitz, Image, ImageDraw) -> dict:
    document = fitz.open(path)
    if document.needs_pass or document.is_repaired or document.page_count != expected_pages:
        raise ValueError(f"PDF structure/page-count problem: {path.name}, {document.page_count} vs {expected_pages}, repaired={document.is_repaired}")
    columns, thumb_width, thumb_height, group_size = 6, 152, 192, 72
    sheet_paths: list[str] = []
    low_ink_pages: list[int] = []
    text_pages = 0
    excerpt = ""
    for start in range(0, document.page_count, group_size):
        count = min(group_size, document.page_count - start)
        sheet = Image.new("RGB", (columns * thumb_width, math.ceil(count / columns) * thumb_height), "#e5e5e5")
        draw = ImageDraw.Draw(sheet)
        for i in range(start, start + count):
            page = document[i]
            page_text = page.get_text()
            if i == 0:
                excerpt = page_text[:900]
            if page_text.strip():
                text_pages += 1
            if page.rect.width <= 0 or page.rect.height <= 0:
                raise ValueError(f"Invalid page geometry: {path.name} page {i+1}")
            scale = min((thumb_width - 8) / page.rect.width, (thumb_height - 23) / page.rect.height)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, colorspace=fitz.csRGB)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            pixels = image.convert("L").tobytes()[::11]
            ink_fraction = sum(pixel < 245 for pixel in pixels) / max(1, len(pixels))
            if ink_fraction < 0.001:
                low_ink_pages.append(i + 1)
            col, row = (i-start) % columns, (i-start) // columns
            sheet.paste(image, (col * thumb_width + (thumb_width-image.width)//2, row * thumb_height + 1))
            draw.text((col * thumb_width + 5, row * thumb_height + thumb_height - 17), str(i+1), fill="#111111")
        out = QA_DIR / f"{qa_prefix}-contact-{start+1:03d}-{start+count:03d}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, quality=83)
        sheet_paths.append(str(out.relative_to(ROOT)).replace("\\", "/"))
    metadata = document.metadata
    document.close()
    return {
        "result": "all_pages_structurally_opened_and_rendered",
        "expected_pages": expected_pages,
        "rendered_pages": expected_pages,
        "text_layer_pages": text_pages,
        "low_ink_pages_1_based": low_ink_pages,
        "contact_sheets": sheet_paths,
        "pdf_metadata_title": metadata.get("title", ""),
        "first_page_text_excerpt": excerpt,
        "human_contact_sheet_review": "pending",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-deps", default="")
    parser.add_argument("--reuse-verified-local", action="store_true")
    args = parser.parse_args()
    if args.pdf_deps:
        sys.path.insert(0, args.pdf_deps)
    import pymupdf as fitz
    from PIL import Image, ImageDraw

    decision, recovery = load(DECISION), load(RECOVERY)
    inventory = {row["id"]: row for row in load(INVENTORY)["candidates"]}
    r2 = load(R2)
    r2_keys = {obj["key"].casefold() for obj in r2["objects"]}
    expected_ids = {decision["family_relationships"]["part_1_canonical"], *decision["family_relationships"]["part_2_obtainable_files"], recovery["chapter_3_result"]["inventory_id"]}
    assert len(ORDER) == len(expected_ids) == 13 and {item[0] for item in ORDER} == expected_ids
    assert r2["object_count"] == len(r2["objects"])

    STAGING.mkdir(parents=True, exist_ok=True)
    ledger = load(LEDGER) if LEDGER.exists() else {"records": {}}
    prepared = []
    proposed_keys = set()
    for order, (record_id, filename, identity, pages, stem) in enumerate(ORDER, 1):
        row = inventory[record_id]
        assert row["status"] == "approved for addition" and row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert row["direct_file_url"].endswith("/" + filename)
        key = f"development-land-use/area-sector-plans/cabq-planned-growth-strategy-{stem}.pdf"
        assert key.casefold() not in proposed_keys and key.casefold() not in r2_keys, key
        proposed_keys.add(key.casefold())
        target = STAGING / filename
        already_valid = target.exists() and target.stat().st_size == row["size_bytes"] and sha256(target) == row["checksum_sha256"]
        if args.reuse_verified_local and already_valid:
            status, final_url, content_type, method = 200, row["direct_file_url"], "application/pdf", "verified_local_city_original_against_saved_exact_bytes"
        else:
            status, final_url, content_type = fetch(row["direct_file_url"], target)
            method = "full_get_official_city_original_2026-09-23"
        size, checksum = target.stat().st_size, sha256(target)
        if (size, checksum) != (row["size_bytes"], row["checksum_sha256"]):
            raise ValueError(f"Source byte drift for {record_id}: {size} {checksum}")
        if final_url != row["direct_file_url"]:
            raise ValueError(f"Unexpected redirect for {record_id}: {final_url}")
        check = inspect_pdf(target, pages, stem, fitz, Image, ImageDraw)
        result = {
            "order": order,
            "id": record_id,
            "identity": identity,
            "title": row["title"],
            "official_source_page_url": row["source_url"],
            "authoritative_original_url": row["direct_file_url"],
            "served_filename": filename,
            "container": "PDF",
            "pdf_magic_verified": True,
            "http_status": status,
            "content_type": content_type,
            "final_url": final_url,
            "source_verification_method": method,
            "staged_original": str(target.relative_to(ROOT)).replace("\\", "/"),
            "size_bytes": size,
            "checksum_sha256": checksum,
            "page_count": pages,
            "pdf_qa": check,
            "proposed_r2_key": key,
            "proposed_future_archive_url": "https://files.abqinfo.com/" + key,
            "r2_key_collision": False,
            "family_relationship": "complete_original_part_1" if order == 1 else "separate_original_part_2_chapter_delivery",
            "preparation_blocker": None,
            "r2_action": "none",
        }
        prepared.append(result)
        ledger["records"][record_id] = {k: result[k] for k in ("order", "id", "authoritative_original_url", "staged_original", "size_bytes", "checksum_sha256", "page_count", "source_verification_method")}
        save(LEDGER, ledger)
        print(f"{order:02d}/13 {filename} {size} bytes {pages} pages SHA-256 {checksum}", flush=True)

    artifact = {
        "schema_version": 1,
        "artifact_type": "planned_growth_strategy_archive_preparation",
        "recorded_at": "2026-09-23",
        "state": "source_and_pdf_render_verified_pending_contact_sheet_review",
        "family_decision": str(DECISION.relative_to(ROOT)).replace("\\", "/"),
        "source_recovery_and_presentation_decision": str(RECOVERY.relative_to(ROOT)).replace("\\", "/"),
        "scope_candidate_ids": [r["id"] for r in prepared],
        "family_presentation_limit": "Part 1 is its single complete 286-page City original. Part 2 is complete against the City's named Chapter 1.0-11.0 roster as 12 separate City originals because Chapter 1 has two deliveries. No verified complete combined Part 2 original exists. The City's apparent Part2.pdf entire-report link opens an unrelated government-unification study. Do not describe these 12 chapter files as an original combined volume or synthesize a PDF.",
        "future_canonical_page": "content/development-land-use/area-sector-plans.md",
        "future_section": "Citywide Growth Strategy",
        "r2_inventory_snapshot": {"object_count": r2["object_count"], "total_bytes": r2["total_bytes"], "generated_at": r2["generated_at"]},
        "records": prepared,
        "summary": {"intended_originals": 13, "source_bytes_verified": len(prepared), "pdf_pages_rendered": sum(r["page_count"] for r in prepared), "source_bytes_total": sum(r["size_bytes"] for r in prepared), "r2_key_collisions": 0, "contact_sheet_reviews_pending": len(prepared)},
        "remaining_gates": ["Human review of contact sheets and any low-ink pages before declaring preparation complete.", "Separate explicit authorization for R2 upload/storage mutation.", "After authorized upload, exact public-byte size and SHA-256 verification for every object.", "Separate Hugo/editorial and PR stage."],
        "safeguards_observed": {"r2_mutation": False, "public_byte_verification": False, "hugo_content_edit": False, "pr_merge_or_deploy": False},
    }
    save(ARTIFACT, artifact)
    print(json.dumps(artifact["summary"], indent=2))


if __name__ == "__main__":
    main()
