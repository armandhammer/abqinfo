#!/usr/bin/env python3
"""Check the locally rendered Stormwater section and exact link order."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / 'tmp/site-build/public-works/stormwater-drainage/index.html'
ARTIFACT = ROOT / 'project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json'


def main() -> None:
    rendered = PAGE.read_text(encoding='utf-8')
    match = re.search(r'<h3 id=municipal-stormwater-program-and-annual-reports>.*?(?=<h3 id=)', rendered, re.S)
    assert match, 'Municipal Stormwater section or following heading missing'
    block = match.group()
    artifact = json.loads(ARTIFACT.read_text(encoding='utf-8-sig'))
    assert block.count('<ul>') == block.count('</ul>') == 1
    assert block.count('<li>') == 13  # Permit, ten annual reports, and two existing program records.
    urls = [html.unescape(quoted or bare) for quoted, bare in re.findall(r'href=(?:"([^"]+)"|([^ >]+))', block)]
    urls = [url for url in urls if url.startswith('https://')]
    for entry in artifact['visible_records_in_page_order']:
        assert urls.count(entry['archive_url']) == urls.count(entry['official_url']) == 1
        assert urls.index(entry['archive_url']) < urls.index(entry['official_url'])
    positions = [urls.index(entry['archive_url']) for entry in artifact['visible_records_in_page_order']]
    assert positions == sorted(positions)
    labels = [int(y) for y in re.findall(r'City of Albuquerque MS4 Annual Report, FY (\d{4})', block)]
    assert labels == artifact['annual_report_fiscal_years_in_visible_order']
    print('PASS: rendered Stormwater section has its anchor, 13 list entries, ten descending annual reports, and six exact archive/source pairs.')


if __name__ == '__main__':
    main()
