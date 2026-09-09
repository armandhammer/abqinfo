#!/usr/bin/env python3
"""Extract and fingerprint locally staged historical Legistar PDFs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="project-state/master-inventory.json")
    parser.add_argument("--output-dir", default="research/staging/legistar-transportation-history/extracted")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8-sig"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        row for row in inventory["candidates"]
        if row.get("status") == "downloaded"
        and row.get("file_type") == "PDF"
        and str(row.get("local_path") or "").startswith("research/staging/legistar-transportation-history/")
    ]

    results = []
    for row in sorted(rows, key=lambda item: item["id"]):
        path = Path(row["local_path"])
        reader = PdfReader(path)
        page_texts: list[str] = []
        fallback_pages: list[int] = []
        with pdfplumber.open(path) as plumber:
            for number, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = plumber.pages[number - 1].extract_text() or ""
                    fallback_pages.append(number)
                page_texts.append(text)
        text = "\n\n".join(page_texts)
        normalized = normalize(text)
        text_path = output_dir / f"{row['id']}.txt"
        text_path.write_text(text, encoding="utf-8")
        page_characters = [len(normalize(value)) for value in page_texts]
        results.append({
            "id": row["id"],
            "title": row.get("title"),
            "date": row.get("date"),
            "local_path": row.get("local_path"),
            "size_bytes": row.get("size_bytes"),
            "checksum_sha256": row.get("checksum_sha256"),
            "pages": len(reader.pages),
            "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
            "text_characters": len(normalized),
            "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "pages_with_under_40_text_characters": [
                index for index, count in enumerate(page_characters, start=1) if count < 40
            ],
            "pdfplumber_fallback_pages": fallback_pages,
            "text_path": text_path.as_posix(),
            "opening_text": normalize(text)[:800],
        })

    report = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "Every locally staged PDF was opened with pypdf, text-extracted page by page with pdfplumber fallback, and fingerprinted after whitespace normalization and lowercasing.",
        "count": len(results),
        "items": results,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(results), "report": report_path.as_posix()}))


if __name__ == "__main__":
    main()
