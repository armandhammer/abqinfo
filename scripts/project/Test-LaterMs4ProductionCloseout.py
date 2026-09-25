#!/usr/bin/env python3
"""Guard the merged, production-verified six-record later-MS4 closeout."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / 'project-state/discovery'
IDS = (
    'src-5cdb4d5491c3a02d', 'src-975528e01439f6df',
    'src-fdc66c5b8de48584', 'src-7c1a063b817989bd',
    'src-eda3280085776f61', 'src-e531466aed7f5387',
)
YEARS = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> None:
    closeout = load(DISCOVERY / 'later-ms4-production-closeout-2026-09-25.json')
    implementation = load(DISCOVERY / 'later-ms4-hugo-implementation-2026-09-25.json')
    archive = load(DISCOVERY / 'later-ms4-archive-public-byte-verification-2026-09-25.json')
    inventory = {r['id']: r for r in load(ROOT / 'project-state/master-inventory.json')['candidates']}
    r2 = load(ROOT / 'project-state/r2-inventory.json')
    gate = load(DISCOVERY / '2014-ms4-family-package-gate-2026-09-18.json')
    assert closeout['artifact_type'] == 'later_ms4_production_closeout'
    assert closeout['pr_number'] == 174
    assert closeout['pr_head_sha'] == '85f66b737eb4829d703bbe042697dac5cd0fab78'
    assert closeout['merge_commit_sha'] == '04c5080cebf2ff094d569c941cc32b23a3e2ab6d'
    assert closeout['manual_review_and_merge_confirmed'] is True
    assert closeout['cloudflare_merge_commit_deployment_check'] == 'success'
    assert closeout['production_verification_result'] == 'passed'
    assert closeout['production_url'] == 'https://abqinfo.com/public-works/stormwater-drainage/'
    assert closeout['http_result'] == 200
    assert closeout['section_anchor'] == 'municipal-stormwater-program-and-annual-reports'
    assert closeout['permit_marker_verification'] == {
        'title_occurrences': 1, 'identifiers_present': ['NMR04A000', 'NMR04A014'],
    }
    assert closeout['annual_report_years_in_visible_order'] == YEARS
    assert closeout['annual_report_entries_each_once'] is True
    assert closeout['existing_annual_report_years_preserved'] == [2025, 2024, 2023, 2022, 2018]
    assert closeout['historical_2005_permit_preserved'] is True
    assert closeout['historical_2005_permit_url'].endswith('/cabq-municipal-separate-storm-sewer-system-permit-2005.pdf')
    assert closeout['r2_accounting_unchanged'] == {
        'object_count': 1237, 'total_bytes': 9218281842,
        'every_key_size_etag_matches_fresh_live_listing': True,
    }
    assert (r2['object_count'], r2['total_bytes']) == (1237, 9218281842)
    assert closeout['r2_mutation'] is closeout['visitor_visible_content_changed_during_closeout'] is False
    assert closeout['inventory_ids_to_validate'] == implementation['implemented_inventory_ids'] == list(IDS)
    assert archive['summary']['public_byte_verified'] == 6 and archive['summary']['added_bytes'] == 426926738
    responses = closeout['production_responses']
    assert len(responses) == 2
    assert [r['request_cache_control'] for r in responses] == [True, False]
    for response in responses:
        assert response['result'] == 'passed' and response['http_status'] == 200
        assert response['response_url'] == closeout['production_url']
        assert response['section_anchor'] == closeout['section_anchor']
        assert response['section_sha256'] == closeout['production_section_sha256']
        assert response['annual_report_years_in_order'] == YEARS
        assert response['permit_title_occurrences'] == 1
        assert response['permit_identifiers'] == ['NMR04A000', 'NMR04A014']
        assert response['historical_2005_permit_preserved'] is True
    visible = implementation['visible_records_in_page_order']
    links = closeout['six_new_archive_and_official_source_link_checks']
    assert len(links) == len(visible) == 6
    assert [r['id'] for r in links] == [r['id'] for r in visible]
    archived_by_id = {r['id']: r for r in archive['results']}
    for link, entry in zip(links, visible):
        row = inventory[link['id']]
        archived = archived_by_id[link['id']]
        assert link['archive_url'] == entry['archive_url'] == row['r2_url'] == archived['public_url']
        assert link['official_url'] == entry['official_url'] == row['direct_file_url']
        assert link['archive_occurrences'] == link['official_occurrences'] == 1
        assert archived['byte_identical'] is True
        assert row['status'] == 'validated'
        assert row['implementation_location'] == 'content/public-works/stormwater-drainage.md'
        assert row['implementation_locations'] == [row['implementation_location']]
        assert row['proposed_canonical_page'] == row['implementation_location']
        assert row['size_bytes'] == archived['expected_size_bytes']
        assert row['checksum_sha256'] == archived['expected_checksum_sha256']
        assert 'PR #174 merged' in row['validation_status']
        assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
    assert inventory['src-185f33493177b085']['status'] == 'superseded'
    assert inventory['src-3408f5b9a86bcb5c']['status'] == 'excluded'
    assert closeout['excluded_draft_letter_and_gated_2014_package_ids_absent'] == [
        'src-185f33493177b085', 'src-3408f5b9a86bcb5c', *gate['scope']['candidate_ids'],
    ]
    assert not set(gate['scope']['candidate_ids']) & set(IDS)
    print('PASS: later-MS4 PR #174 production closeout has two HTTP 200 section checks, six validated originals, ten ordered reports, unchanged R2, and preserved exclusions.')


if __name__ == '__main__':
    main()
