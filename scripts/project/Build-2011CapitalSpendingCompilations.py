#!/usr/bin/env python3
"""Build both local 2011 Capital Spending compilations and record exact ranges."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json"
BUILDER = ROOT / "scripts/project/Build-HistoricalCompilationPdf.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("historical_compilation_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load historical compilation builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compatibility_manifest(compilation: dict) -> dict:
    keys = (
        "title", "short_title", "record_label", "source_record_label", "date_label",
        "coverage_note", "editorial_note", "provenance_note", "preservation_notice",
        "contents_page_row_counts", "sources",
    )
    return {key: compilation[key] for key in keys}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    builder = load_builder()
    temp = ROOT / "tmp/pdfs/2011-capital-spending"
    temp.mkdir(parents=True, exist_ok=True)
    for compilation in manifest["compilations"]:
        compatibility_path = temp / f"{compilation['compilation_id']}-build-manifest.json"
        compatibility_path.write_text(json.dumps(compatibility_manifest(compilation), indent=2, ensure_ascii=False), encoding="utf-8")
        output = ROOT / compilation["local_output_path"]
        validation = ROOT / compilation["build_validation_path"]
        builder.build(compatibility_path, output, validation)
        result = json.loads(validation.read_text(encoding="utf-8"))
        if result["source_count"] != len(compilation["sources"]):
            raise ValueError(f"Source count mismatch for {compilation['compilation_id']}")
        by_id = {entry["candidate_id"]: entry for entry in result["sources"]}
        for source in compilation["sources"]:
            built = by_id[source["candidate_id"]]
            source["component_page_count"] = built["source_pages"]
            source["compilation_separator_page"] = built["section_page"]
            source["compilation_source_page_start"] = built["source_start_page"]
            source["compilation_source_page_end"] = built["source_end_page"]
        compilation["build_result"] = {
            "page_count": result["page_count"],
            "intro_pages": result["intro_pages"],
            "source_count": result["source_count"],
            "source_page_count": sum(entry["source_pages"] for entry in result["sources"]),
            "size_bytes": result["size_bytes"],
            "checksum_sha256": result["checksum_sha256"],
        }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({item["compilation_id"]: item["build_result"] for item in manifest["compilations"]}, indent=2))


if __name__ == "__main__":
    main()
