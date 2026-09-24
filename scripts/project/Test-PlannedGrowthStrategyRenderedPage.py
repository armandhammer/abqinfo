#!/usr/bin/env python3
"""Check the locally built PGS section's heading, list, and link order."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "tmp/site-build/development-land-use/area-sector-plans/index.html"
PREPARED = ROOT / "project-state/discovery/planned-growth-strategy-archive-preparation-2026-09-23.json"


def main() -> None:
    rendered = PAGE.read_text(encoding="utf-8")
    section = re.search(r"<h2 id=citywide-growth-strategy>.*?(?=<h2 id=)", rendered, re.S)
    assert section, "Citywide Growth Strategy H2 missing from rendered page"
    block = section.group()
    assert block.count("<ol>") == 1 and block.count("</ol>") == 1
    assert block.count("<li>") == 13  # Part 1 bullet plus twelve Part 2 chapters.
    urls = [html.unescape(quoted or bare) for quoted, bare in re.findall(r'href=(?:"([^"]+)"|([^ >]+))', block)]
    urls = [url for url in urls if url.startswith("https://")]
    prepared = json.loads(PREPARED.read_text(encoding="utf-8"))
    expected = [url for record in prepared["records"] for url in (
        record["proposed_future_archive_url"], record["authoritative_original_url"]
    )]
    assert urls == expected, (len(urls), len(expected))
    print("PASS: rendered Area & Sector Plans page has one PGS H2, one ordered Part 2 list, and 13 exact archive/City source link pairs.")


if __name__ == "__main__":
    main()
