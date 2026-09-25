#!/usr/bin/env python3
"""Read the actual production page and verify the bounded later-MS4 section."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_URL = 'https://abqinfo.com/public-works/stormwater-drainage/'
ANCHOR = 'municipal-stormwater-program-and-annual-reports'
EXPECTED_YEARS = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]
EXISTING_YEARS = [2025, 2024, 2023, 2022, 2018]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def verify(cache_control: bool) -> dict:
    headers = {'User-Agent': 'ABQInfo-production-verification/1.0'}
    if cache_control:
        headers.update({'Cache-Control': 'no-cache, no-store', 'Pragma': 'no-cache'})
    request = urllib.request.Request(PRODUCTION_URL, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
        result = {
            'requested_url': PRODUCTION_URL,
            'response_url': response.url,
            'verified_at': datetime.now(timezone.utc).isoformat(),
            'http_status': response.status,
            'request_cache_control': cache_control,
            'body_bytes': len(body),
            'body_sha256': hashlib.sha256(body).hexdigest(),
            'cf_cache_status': response.headers.get('CF-Cache-Status'),
            'age': response.headers.get('Age'),
            'cf_ray': response.headers.get('CF-Ray'),
        }
    assert result['http_status'] == 200 and result['response_url'] == PRODUCTION_URL, result
    page = body.decode('utf-8')
    match = re.search(
        rf'<h3\b[^>]*\bid=["\']?{ANCHOR}["\']?[^>]*>.*?(?=<h3\b)',
        page, re.I | re.S,
    )
    assert match, 'Production municipal-stormwater heading/anchor or following heading absent'
    section = match.group()
    implementation = load('project-state/discovery/later-ms4-hugo-implementation-2026-09-25.json')
    inventory = {r['id']: r for r in load('project-state/master-inventory.json')['candidates']}
    gate = load('project-state/discovery/2014-ms4-family-package-gate-2026-09-18.json')
    years = [int(y) for y in re.findall(r'City of Albuquerque MS4 Annual Report, FY ([0-9]{4})', section)]
    assert years == EXPECTED_YEARS, years
    assert len(years) == len(set(years)) == 10
    assert section.count('EPA Middle Rio Grande Watershed-Based MS4 General Permit') == 1
    assert 'NMR04A000' in section and 'NMR04A014' in section
    assert section.count('<li>') == 13
    link_checks = []
    positions = []
    for entry in implementation['visible_records_in_page_order']:
        archive, official = entry['archive_url'], entry['official_url']
        assert page.count(archive) == section.count(archive) == 1, (entry['id'], 'archive')
        assert page.count(official) == section.count(official) == 1, (entry['id'], 'official')
        assert section.index(archive) < section.index(official), entry['id']
        positions.append(section.index(archive))
        link_checks.append({'id': entry['id'], 'archive_url': archive, 'archive_occurrences': 1,
                            'official_url': official, 'official_occurrences': 1})
    assert positions == sorted(positions)
    for year in EXISTING_YEARS:
        marker = f'cabq-ms4-annual-report-fy{year}.pdf'
        assert section.count(marker) == 1, marker
    exclusions = []
    for excluded_id in ('src-185f33493177b085', 'src-3408f5b9a86bcb5c', *gate['scope']['candidate_ids']):
        candidate = inventory[excluded_id]
        for field in ('direct_file_url', 'r2_url'):
            url = candidate.get(field)
            if url:
                assert url not in page, (excluded_id, field)
        exclusions.append(excluded_id)
    assert not re.search(r'FY\s*2021 draft|2015 EPA coverage letter|2014 MS4 Annual Report', page, re.I)
    historical = re.search(r'<h3\b[^>]*\bid=["\']?historical-permit-and-water-quality-records["\']?[^>]*>.*?(?=<h[23]\b)', page, re.I | re.S)
    assert historical, 'Historical Permit and Water-Quality Records section absent'
    old_permit = 'https://files.abqinfo.com/public-works/stormwater-drainage/cabq-municipal-separate-storm-sewer-system-permit-2005.pdf'
    assert historical.group().count(old_permit) == page.count(old_permit) == 1
    result.update({
        'section_anchor': ANCHOR,
        'section_sha256': hashlib.sha256(section.encode('utf-8')).hexdigest(),
        'permit_title_occurrences': 1,
        'permit_identifiers': ['NMR04A000', 'NMR04A014'],
        'annual_report_years_in_order': years,
        'annual_report_entries_each_once': True,
        'section_list_entries': 13,
        'new_link_checks': link_checks,
        'existing_annual_report_years_preserved': EXISTING_YEARS,
        'excluded_and_gated_ids_absent': exclusions,
        'historical_2005_permit_url': old_permit,
        'historical_2005_permit_preserved': True,
        'result': 'passed',
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--ordinary-request', action='store_true')
    args = parser.parse_args()
    report = verify(cache_control=not args.ordinary_request)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('http_status', 'body_bytes', 'body_sha256', 'annual_report_years_in_order', 'result')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Production verification failed: {exc}', file=sys.stderr)
        raise
