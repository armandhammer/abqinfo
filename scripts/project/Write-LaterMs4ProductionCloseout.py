#!/usr/bin/env python3
"""Consolidate independently verified production and R2 evidence."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / 'project-state/discovery'
OUTPUT = DISCOVERY / 'later-ms4-production-closeout-2026-09-25.json'
MERGE_SHA = '04c5080cebf2ff094d569c941cc32b23a3e2ab6d'
PR_HEAD = '85f66b737eb4829d703bbe042697dac5cd0fab78'


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> None:
    fresh = load(ROOT / 'tmp/later-ms4-production-no-cache-2026-09-25.json')
    ordinary = load(ROOT / 'tmp/later-ms4-production-ordinary-2026-09-25.json')
    implementation = load(DISCOVERY / 'later-ms4-hugo-implementation-2026-09-25.json')
    archived = load(DISCOVERY / 'later-ms4-archive-public-byte-verification-2026-09-25.json')
    saved_r2 = load(ROOT / 'project-state/r2-inventory.json')
    live_r2 = load(ROOT / 'tmp/later-ms4-production-r2-live-2026-09-25.json')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == MERGE_SHA
    assert not subprocess.check_output(['git', 'status', '--porcelain', '--', 'content'], cwd=ROOT, text=True).strip()
    assert archived['state'] == 'complete_all_six_public_byte_verified_and_inventory_reconciled'
    assert archived['summary']['public_byte_verified'] == 6
    assert implementation['state'] == 'implemented_on_planning_branch_not_live'
    assert len(implementation['implemented_inventory_ids']) == 6
    for response in (fresh, ordinary):
        assert response['result'] == 'passed'
        assert response['http_status'] == 200
        assert response['response_url'] == 'https://abqinfo.com/public-works/stormwater-drainage/'
        assert response['section_anchor'] == 'municipal-stormwater-program-and-annual-reports'
        assert response['annual_report_years_in_order'] == [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016]
        assert response['permit_title_occurrences'] == 1
        assert response['permit_identifiers'] == ['NMR04A000', 'NMR04A014']
        assert len(response['new_link_checks']) == 6
        assert response['historical_2005_permit_preserved'] is True
    assert fresh['section_sha256'] == ordinary['section_sha256']
    assert [r['id'] for r in fresh['new_link_checks']] == [r['id'] for r in implementation['visible_records_in_page_order']]
    for check, entry in zip(fresh['new_link_checks'], implementation['visible_records_in_page_order']):
        assert check['archive_url'] == entry['archive_url'] and check['official_url'] == entry['official_url']
        assert check['archive_occurrences'] == check['official_occurrences'] == 1
    assert (saved_r2['object_count'], saved_r2['total_bytes']) == (live_r2['object_count'], live_r2['total_bytes']) == (1237, 9218281842)
    signature = lambda data: {o['key']: (o['size_bytes'], o['etag']) for o in data['objects']}
    assert signature(saved_r2) == signature(live_r2)
    records = {
        'schema_version': 1,
        'artifact_type': 'later_ms4_production_closeout',
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'pr_number': 174,
        'pr_head_sha': PR_HEAD,
        'merge_commit_sha': MERGE_SHA,
        'manual_review_and_merge_confirmed': True,
        'cloudflare_merge_commit_deployment_check': 'success',
        'production_url': fresh['requested_url'],
        'verification_timestamp': max(fresh['verified_at'], ordinary['verified_at']),
        'http_result': 200,
        'production_responses': [fresh, ordinary],
        'section_anchor': fresh['section_anchor'],
        'production_section_sha256': fresh['section_sha256'],
        'permit_marker_verification': {
            'title_occurrences': fresh['permit_title_occurrences'],
            'identifiers_present': fresh['permit_identifiers'],
        },
        'annual_report_years_in_visible_order': fresh['annual_report_years_in_order'],
        'annual_report_entries_each_once': fresh['annual_report_entries_each_once'],
        'annual_report_entries_each_once': fresh['annual_report_entries_each_once'],
        'six_new_archive_and_official_source_link_checks': fresh['new_link_checks'],
        'existing_annual_report_years_preserved': fresh['existing_annual_report_years_preserved'],
        'excluded_draft_letter_and_gated_2014_package_ids_absent': fresh['excluded_and_gated_ids_absent'],
        'historical_2005_permit_preserved': fresh['historical_2005_permit_preserved'],
        'historical_2005_permit_url': fresh['historical_2005_permit_url'],
        'r2_accounting_unchanged': {
            'object_count': saved_r2['object_count'],
            'total_bytes': saved_r2['total_bytes'],
            'every_key_size_etag_matches_fresh_live_listing': True,
        },
        'visitor_visible_content_changed_during_closeout': False,
        'r2_mutation': False,
        'production_verification_result': 'passed',
        'inventory_ids_to_validate': implementation['implemented_inventory_ids'],
    }
    OUTPUT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Production closeout evidence passed: {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
