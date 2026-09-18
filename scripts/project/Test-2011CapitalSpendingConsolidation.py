#!/usr/bin/env python3
"""Validate the 2011 Capital Spending consolidation preparation boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json"
PAGE = ROOT / "content/city-data/capital-spending.md"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def section_archive_urls(text: str, heading: str) -> list[str]:
    marker = f"### {heading}"
    start = text.index(marker) + len(marker)
    match = re.search(r"^###\s+", text[start:], flags=re.MULTILINE)
    end = start + match.start() if match else len(text)
    return re.findall(r"\]\((https://files\.abqinfo\.com/[^)]+)\)", text[start:end])


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    compilations = manifest["compilations"]
    if [len(item["sources"]) for item in compilations] != [21, 46]:
        raise AssertionError("Expected exact 21/46 compilation membership")
    all_sources = [source for compilation in compilations for source in compilation["sources"]]
    ids = [source["candidate_id"] for source in all_sources]
    if len(ids) != 67 or len(set(ids)) != 67:
        raise AssertionError("Expected 67 unique selected originals")
    archived = [source for source in all_sources if source["archive_status"] == "verified_public_r2"]
    pending = [source for source in all_sources if source["archive_status"] == "proposed_not_uploaded"]
    if len(archived) != 63 or len(pending) != 4:
        raise AssertionError("Expected 63 verified R2 originals and four not-yet-uploaded originals")
    if any(source["r2_key"] for source in pending):
        raise AssertionError("A pending original is incorrectly represented as present in R2")
    if any(not source["r2_key"] for source in archived):
        raise AssertionError("A verified R2 original lacks its key")

    published_ids = [source["candidate_id"] for source in compilations[1]["sources"]]
    for pair in manifest["version_relationships"]:
        earlier = published_ids.index(pair["earlier_id"])
        later = published_ids.index(pair["later_id"])
        if earlier >= later or "final/adopted status not established" not in pair["conclusion"]:
            raise AssertionError(f"Version chronology/finality rule failed for {pair['subject']}")

    excluded_ids = [item["candidate_id"] for item in manifest["nonmember_records"]]
    if len(excluded_ids) != len(set(excluded_ids)) or set(excluded_ids) & set(ids):
        raise AssertionError("Nonmember coverage overlaps selected compilation membership")

    for compilation in compilations:
        build_path = ROOT / compilation["build_validation_path"]
        qa_path = ROOT / compilation["qa_validation_path"]
        if not build_path.is_file() or not qa_path.is_file():
            raise AssertionError(f"Missing build or PDF QA evidence for {compilation['compilation_id']}")
        build = json.loads(build_path.read_text(encoding="utf-8"))
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        result = compilation["build_result"]
        if not result or build["checksum_sha256"] != result["checksum_sha256"] or build["size_bytes"] != result["size_bytes"]:
            raise AssertionError(f"Build identity mismatch for {compilation['compilation_id']}")
        if build["source_count"] != len(compilation["sources"]) or qa["source_document_count"] != len(compilation["sources"]):
            raise AssertionError(f"Source-count validation failed for {compilation['compilation_id']}")
        if not all((qa["rendered_source_pages_pixel_identical"], qa["extracted_source_text_identical"], qa["all_separator_provenance_links_present"])):
            raise AssertionError(f"Source fidelity validation failed for {compilation['compilation_id']}")
        built_by_id = {source["candidate_id"]: source for source in build["sources"]}
        for source in compilation["sources"]:
            built = built_by_id[source["candidate_id"]]
            expected = (
                built["source_pages"], built["section_page"], built["source_start_page"], built["source_end_page"]
            )
            actual = (
                source["component_page_count"], source["compilation_separator_page"],
                source["compilation_source_page_start"], source["compilation_source_page_end"],
            )
            if actual != expected:
                raise AssertionError(f"Page-range mismatch for {source['candidate_id']}")
        output = ROOT / compilation["local_output_path"]
        if output.exists():
            if output.stat().st_size != result["size_bytes"] or digest(output) != result["checksum_sha256"]:
                raise AssertionError(f"Local output identity mismatch for {compilation['compilation_id']}")
    if manifest["visual_inspection"]["status"] != "passed":
        raise AssertionError("Final compilation visual inspection is not recorded as passed")

    page_text = PAGE.read_text(encoding="utf-8-sig")
    standalone_urls = {source["archive_url"] for source in archived}
    master_urls = {
        "https://files.abqinfo.com/" + compilation["proposed_r2_key"]
        for compilation in compilations
    }
    if master_urls <= set(re.findall(r"https://files\.abqinfo\.com/[^)\s]+", page_text)):
        if any(url in page_text for url in standalone_urls):
            raise AssertionError("Published presentation regressed to standalone 2011 component links")
    else:
        if manifest["publication_state"] != "preparation_complete_not_published":
            raise AssertionError("Unpublished page does not match the preparation boundary")
        published_urls = section_archive_urls(page_text, "2011 Published Scope and Version Records")
        october_urls = section_archive_urls(page_text, "October 2010 Program Scope and Schedule Records")
        if len(published_urls) != 26 or len(october_urls) != 37 or set(published_urls + october_urls) != standalone_urls:
            raise AssertionError("Current 26/37 page baseline is not exactly covered by the manifest")

    safeguards = manifest["safeguards_observed"]
    if any(safeguards.values()):
        raise AssertionError("Preparation manifest records a prohibited side effect")
    print("PASS: 2011 Capital Spending preparation preserves 67 originals in 21/46 compilations, validates PDF fidelity, and enforces the future two-entry page contract.")


if __name__ == "__main__":
    main()
