#!/usr/bin/env python3
"""Verify the live PGS section against the committed page and saved originals."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "project-state/discovery"
URL = "https://abqinfo.com/development-land-use/area-sector-plans/"
OUTPUT = DISCOVERY / "planned-growth-strategy-production-closeout-2026-09-24.json"


class SectionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_section = False
        self.heading_depth = 0
        self.heading_text = ""
        self.heading_count = 0
        self.links = []
        self.text = []
        self.part2_items = 0
        self.li_depth = 0
        self.ol_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h2":
            self.heading_depth = 1
            self.heading_text = ""
            if self.in_section:
                self.in_section = False
        elif self.heading_depth:
            self.heading_depth += 1
        if not self.in_section:
            return
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "ol":
            self.ol_depth += 1
        if tag == "li" and self.ol_depth:
            self.part2_items += 1

    def handle_endtag(self, tag):
        if self.heading_depth:
            if tag == "h2":
                if self.heading_text.rstrip("# ").strip() == "Citywide Growth Strategy":
                    self.heading_count += 1
                    self.in_section = True
                self.heading_depth = 0
            else:
                self.heading_depth = max(1, self.heading_depth - 1)
            return
        if self.in_section and tag == "ol":
            self.ol_depth -= 1

    def handle_data(self, data):
        if self.heading_depth:
            self.heading_text += data
        elif self.in_section:
            self.text.append(data)


def main():
    prep = json.loads((DISCOVERY / "planned-growth-strategy-archive-preparation-2026-09-23.json").read_text(encoding="utf-8-sig"))
    implementation = json.loads((DISCOVERY / "planned-growth-strategy-hugo-implementation-2026-09-23.json").read_text(encoding="utf-8-sig"))
    records = prep["records"]
    assert len(records) == 13
    request = urllib.request.Request(URL, headers={"User-Agent": "ABQInfo-PGS-production-closeout/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        status = response.status
        final_url = response.url
        body = response.read()
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    assert status == 200 and final_url.rstrip("/") == URL.rstrip("/")
    html = body.decode("utf-8-sig")
    parser = SectionParser()
    parser.feed(html)
    assert parser.heading_count == 1, parser.heading_count
    assert parser.part2_items == 12, parser.part2_items
    expected_links = [url for row in records for url in (row["proposed_future_archive_url"], row["authoritative_original_url"])]
    public_links = [url for url in parser.links if url.startswith("https://files.abqinfo.com/") or url.startswith("https://www.cabq.gov/council/documents/pgs/")]
    assert public_links == expected_links, "Production PGS link order/content differs from prepared originals"
    normalized_text = " ".join(" ".join(parser.text).split())
    markdown = (ROOT / implementation["page"]).read_text(encoding="utf-8-sig")
    heading = "## Citywide Growth Strategy"
    section = heading + markdown.split(heading, 1)[1].split("\n## ", 1)[0]
    assert hashlib.sha256(section.encode("utf-8")).hexdigest() == implementation["section_sha256"]
    expected_chapter_labels = re.findall(r"(?m)^\d+\. \[([^]]+)\]", section)
    assert len(expected_chapter_labels) == 12
    chapter_positions = [normalized_text.index(label) for label in expected_chapter_labels]
    assert chapter_positions == sorted(chapter_positions)
    for phrase in ("historical City and County study", "Complete Findings Report (286 Pages)", "All 11 named chapters", "12 files", "No verified complete combined Part 2 original", "Chapter 3.0 — Preferred Alternative Summary", "documented order rather than as a merged PDF"):
        assert phrase in normalized_text, phrase
    assert not re.search(r"Chapter 3(?:\.0)?[^.;]{0,70}(?:missing|unavailable|gap)", normalized_text, re.I)
    assert not any("/Part2.pdf" in url or re.search(r"Part1-", url, re.I) for url in parser.links)
    artifact = {
        "schema_version": 1,
        "artifact_type": "planned_growth_strategy_production_closeout",
        "pr_number": 168,
        "pr_state": "merged_manual_user_review",
        "merge_commit_sha": "8cfba47b46a464a04f67b1fccbe3943dd30b74c9",
        "production_page_url": URL,
        "production_verified_at": checked_at,
        "production_http_status": status,
        "production_final_url": final_url,
        "production_html_bytes": len(body),
        "production_html_sha256": hashlib.sha256(body).hexdigest(),
        "production_verification_result": "passed",
        "verified_section_heading": "Citywide Growth Strategy",
        "committed_section_sha256": implementation["section_sha256"],
        "expected_archive_link_count": 13,
        "verified_archive_link_count": 13,
        "expected_official_source_link_count": 13,
        "verified_official_source_link_count": 13,
        "ordered_inventory_ids": [row["id"] for row in records],
        "ordered_archive_and_official_source_links_match_preparation": True,
        "part_1_presentation": "One complete 286-page official City original; seven component duplicates are not exposed.",
        "part_2_presentation": "Twelve separate official City PDF deliveries in order cover all 11 named Chapters 1.0–11.0; Chapter 1 has two deliveries and Chapter 3.0 is present.",
        "chapter_3_present": True,
        "verified_complete_combined_part_2_original": False,
        "unrelated_part2_pdf_exposed": False,
        "stale_chapter_3_gap_language": False,
        "r2_mutation_during_closeout": False,
        "visitor_visible_content_modified_during_closeout": False,
        "final_inventory_status": "validated",
        "family_state": "complete_live",
        "evidence_method": "Public HTTP GET; parse the actual production h2 section; compare all 26 ordered URLs and presentation text to the committed implementation and 13-record preparation artifact.",
    }
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: production HTTP {status}; 1 PGS section; 13 ordered archive/City pairs; 12 Part 2 entries; {checked_at}")


if __name__ == "__main__":
    main()
