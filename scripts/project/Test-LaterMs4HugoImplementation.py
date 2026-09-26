#!/usr/bin/env python3
"""Guard the bounded six-record Stormwater and Drainage page addition."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / 'project-state/discovery'
PAGE = ROOT / 'content/public-works/stormwater-drainage.md'
IDS = (
    'src-5cdb4d5491c3a02d', 'src-975528e01439f6df',
    'src-fdc66c5b8de48584', 'src-7c1a063b817989bd',
    'src-eda3280085776f61', 'src-e531466aed7f5387',
)
VISIBLE_IDS = (IDS[0], IDS[5], IDS[4], IDS[3], IDS[2], IDS[1])
YEARS = (2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> None:
    implementation = load(DISCOVERY / 'later-ms4-hugo-implementation-2026-09-25.json')
    prepared = load(DISCOVERY / 'later-ms4-archive-preparation-2026-09-24.json')
    verified = load(DISCOVERY / 'later-ms4-archive-public-byte-verification-2026-09-25.json')
    gate = load(DISCOVERY / '2014-ms4-family-package-gate-2026-09-18.json')
    inventory = {r['id']: r for r in load(ROOT / 'project-state/master-inventory.json')['candidates']}
    from BackgroundArchiveCampaign import historical_r2
    r2 = historical_r2(load(ROOT / 'project-state/r2-inventory.json'))
    closeout_path = DISCOVERY / 'later-ms4-production-closeout-2026-09-25.json'
    closeout = load(closeout_path) if closeout_path.exists() else None
    if closeout:
        assert closeout['production_verification_result'] == 'passed'
    page = PAGE.read_text(encoding='utf-8-sig')
    heading = '### Municipal Stormwater Program and Annual Reports'
    assert page.count(heading) == 1
    section = heading + page.split(heading, 1)[1].split('\n### ', 1)[0]
    assert hashlib.sha256(section.encode()).hexdigest() == implementation['section_sha256']
    assert implementation['state'] == 'implemented_on_planning_branch_not_live'
    assert implementation['page'] == 'content/public-works/stormwater-drainage.md'
    assert implementation['section'] == 'Municipal Stormwater Program and Annual Reports'
    assert implementation['section_anchor'] == 'municipal-stormwater-program-and-annual-reports'
    assert implementation['implemented_inventory_ids'] == list(IDS)
    assert [r['id'] for r in implementation['visible_records_in_page_order']] == list(VISIBLE_IDS)
    assert implementation['annual_report_fiscal_years_in_visible_order'] == list(YEARS)
    assert implementation['existing_annual_reports_preserved'] == [2025, 2024, 2023, 2022, 2018]
    assert implementation['inventory_status'] == 'implemented'
    assert implementation['r2_mutation'] is implementation['production_or_live'] is implementation['merge_or_deploy'] is False
    assert verified['state'] == 'complete_all_six_public_byte_verified_and_inventory_reconciled'
    assert verified['summary']['public_byte_verified'] == 6 and verified['summary']['added_bytes'] == 426926738
    planning_path=ROOT/'project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json'
    if planning_path.exists():
        planning=json.loads(planning_path.read_text(encoding='utf-8-sig'))
        assert planning['state']=='complete_all_12_public_byte_verified_and_inventory_reconciled'
        assert planning['accounting']['pre_existing_objects_unchanged'] is True
        assert (r2['object_count'],r2['total_bytes'])==(1249,9340531168)
    else:
        assert (r2['object_count'], r2['total_bytes']) == (1237, 9218281842)
    assert tuple(int(y) for y in re.findall(r'City of Albuquerque MS4 Annual Report, FY (\d{4}) \(', section)) == YEARS
    assert section.count('EPA Middle Rio Grande Watershed-Based MS4 General Permit') == 1
    assert section.index('NMR04A000') < section.index('City of Albuquerque MS4 Annual Report, FY 2025')
    assert 'NMR04A014' in section
    assert 'Albuquerque Municipal Separate Storm Sewer System Permit (2005 Archived PDF)' not in section
    assert page.count('Albuquerque Municipal Separate Storm Sewer System Permit (2005 Archived PDF)') == 1
    prepared_by_id = {r['id']: r for r in prepared['records']}
    verified_by_id = {r['id']: r for r in verified['results']}
    positions = []
    for entry in implementation['visible_records_in_page_order']:
        record_id = entry['id']
        prep = prepared_by_id[record_id]
        result = verified_by_id[record_id]
        row = inventory[record_id]
        archive_url, official_url = entry['archive_url'], entry['official_url']
        assert archive_url == prep['proposed_future_archive_url'] == result['public_url'] == row['r2_url']
        assert official_url == prep['authoritative_source_url'] == row['direct_file_url']
        assert result['byte_identical'] is True and result['public_size_bytes'] == prep['size_bytes'] == row['size_bytes']
        assert result['public_checksum_sha256'] == prep['checksum_sha256'] == row['checksum_sha256']
        assert page.count(archive_url) == page.count(official_url) == 1
        assert section.index(archive_url) < section.index(official_url)
        positions.append(section.index(archive_url))
        assert row['status'] == ('validated' if closeout else 'implemented')
        assert row['implementation_location'] == implementation['page']
        assert row['implementation_locations'] == [implementation['page']]
        assert row['proposed_canonical_page'] == implementation['page']
        assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
        assert ('production Stormwater and Drainage' if closeout else 'not live') in row['validation_status']
    assert positions == sorted(positions)
    assert inventory['src-185f33493177b085']['status'] == 'superseded'
    assert inventory['src-3408f5b9a86bcb5c']['status'] == 'excluded'
    for excluded_id in ('src-185f33493177b085', 'src-3408f5b9a86bcb5c', *gate['scope']['candidate_ids']):
        excluded = inventory[excluded_id]
        for field in ('direct_file_url', 'r2_url'):
            if excluded.get(field):
                assert excluded[field] not in section, (excluded_id, field)
    assert not re.search(r'FY\s*2021 draft|2015 EPA coverage letter|2014 MS4 Annual Report', section, re.I)
    print('PASS: Stormwater section has six exact archived/source pairs, ten annual reports in descending FY order, one permit context, and six ' + ('validated live' if closeout else 'implemented') + ' rows; no excluded or gated records.')


if __name__ == '__main__':
    main()
