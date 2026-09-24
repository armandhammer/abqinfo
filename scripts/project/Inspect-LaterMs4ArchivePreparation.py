#!/usr/bin/env python3
"""Check the six staged later-MS4 originals and render every page for archive QA.

Read-only with respect to inventory and R2. Source retrieval is a separate step.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "research/staging/later-ms4-archive-preparation-2026-09-24"
QA = ROOT / "tmp/later-ms4-archive-qa-2026-09-24"
OUTPUT = STAGING / "pdf-inspection-ledger.json"
EXPECTED = (
    ("src-5cdb4d5491c3a02d", "epa-middle-rio-grande-ms4-general-permit-2014.pdf", 1724506, "c9e368ec12280953ac8c20b5ada86ee9fea5e468f2a3babdbf5994402e361aef"),
    ("src-975528e01439f6df", "fy2016.pdf", 10027499, "e5b5713e32de6cb04119a11d5f4e2ef6183a81ddfda73b46dc56bad9e1be982e"),
    ("src-fdc66c5b8de48584", "fy2017.pdf", 138084248, "31cbc0412f4d655d9ff0f576383de02f23bc0529ddf5515eb9d8f1f50c922b01"),
    ("src-7c1a063b817989bd", "fy2019.pdf", 122657409, "b7d7008a39c470edc04c08a966bd4322d14cbedea96630daa898cc1382e71f3a"),
    ("src-eda3280085776f61", "fy2020-final.pdf", 133787450, "0b5a84bb81f5615feba687924c785b1a94528d4028b6630b43670eda8c65506b"),
    ("src-e531466aed7f5387", "fy2021-final.pdf", 20645626, "ac139129ef0e412e94970ec4725eebf6c1adcda5343a0f24ed14d3dc86174ce4"),
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    sys.path.insert(0, str(ROOT / "tmp/ms4-pdf-deps"))
    import pymupdf as fitz
    from PIL import Image, ImageDraw

    inventory = {r["id"]: r for r in json.loads((ROOT / "project-state/master-inventory.json").read_text(encoding="utf-8-sig"))["candidates"]}
    QA.mkdir(parents=True, exist_ok=True)
    completed = []
    for record_id, filename, size, sha in EXPECTED:
        row = inventory[record_id]
        assert row["status"] == "approved for addition"
        assert row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert (row["size_bytes"], row["checksum_sha256"]) == (size, sha)
        path = STAGING / filename
        assert path.read_bytes()[:5] == b"%PDF-", filename
        assert path.stat().st_size == size and digest(path) == sha, filename
        document = fitz.open(path)
        assert not document.needs_pass and not document.is_repaired and document.page_count > 0, filename
        count = document.page_count
        sheets = []
        low_ink = []
        text_pages = 0
        excerpts = {}
        width, height, columns, per_sheet = 160, 205, 6, 48
        for start in range(0, count, per_sheet):
            end = min(start + per_sheet, count)
            sheet = Image.new("RGB", (columns * width, math.ceil((end - start) / columns) * height), "#e6e6e6")
            draw = ImageDraw.Draw(sheet)
            for index in range(start, end):
                page = document[index]
                assert page.rect.width > 0 and page.rect.height > 0, (filename, index + 1)
                page_text = page.get_text()
                if page_text.strip():
                    text_pages += 1
                if index in (0, 5, 6, count - 1):
                    excerpts[str(index + 1)] = page_text[:600]
                scale = min((width - 8) / page.rect.width, (height - 25) / page.rect.height)
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                pixels = image.convert("L").tobytes()[::17]
                ink_fraction = sum(value < 245 for value in pixels) / max(1, len(pixels))
                if ink_fraction < 0.001:
                    low_ink.append(index + 1)
                slot = index - start
                x, y = (slot % columns) * width, (slot // columns) * height
                sheet.paste(image, (x + (width - image.width) // 2, y))
                draw.text((x + 5, y + height - 18), str(index + 1), fill="#111111")
            sheet_path = QA / f"{path.stem}-{start + 1:03d}-{end:03d}.jpg"
            sheet.save(sheet_path, quality=82)
            sheets.append(sheet_path.relative_to(ROOT).as_posix())
        metadata = document.metadata
        document.close()
        result = {
            "id": record_id,
            "staged_original": path.relative_to(ROOT).as_posix(),
            "size_bytes": size,
            "checksum_sha256": sha,
            "page_count": count,
            "structural_result": "opens_without_password_or_repair",
            "render_result": "all_pages_rendered",
            "rendered_pages": count,
            "text_layer_pages": text_pages,
            "low_ink_pages_1_based": low_ink,
            "contact_sheets": sheets,
            "pdf_metadata_title": metadata.get("title", ""),
            "page_text_excerpts": excerpts,
        }
        completed.append(result)
        OUTPUT.write_text(json.dumps({"records": completed}, indent=2) + "\n", encoding="utf-8")
        print(f"{record_id}: {size} bytes, {count} pages, {len(sheets)} sheets, low ink {low_ink}", flush=True)
    assert sum(item["size_bytes"] for item in completed) == 426926738


if __name__ == "__main__":
    main()
