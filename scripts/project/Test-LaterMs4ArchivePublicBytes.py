#!/usr/bin/env python3
"""Guard the exact six-object later-MS4 archival completion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'project-state/discovery'
IDS = (
    'src-5cdb4d5491c3a02d', 'src-975528e01439f6df',
    'src-fdc66c5b8de48584', 'src-7c1a063b817989bd',
    'src-eda3280085776f61', 'src-e531466aed7f5387',
)
KEYS = (
    'public-works/stormwater-drainage/epa-middle-rio-grande-watershed-ms4-general-permit-2014.pdf',
    'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2016.pdf',
    'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2017.pdf',
    'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2019.pdf',
    'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2020-final.pdf',
    'public-works/stormwater-drainage/cabq-ms4-annual-report-fy2021-final.pdf',
)
SIZES = (1724506, 10027499, 138084248, 122657409, 133787450, 20645626)
HASHES = (
    'c9e368ec12280953ac8c20b5ada86ee9fea5e468f2a3babdbf5994402e361aef',
    'e5b5713e32de6cb04119a11d5f4e2ef6183a81ddfda73b46dc56bad9e1be982e',
    '31cbc0412f4d655d9ff0f576383de02f23bc0529ddf5515eb9d8f1f50c922b01',
    'b7d7008a39c470edc04c08a966bd4322d14cbedea96630daa898cc1382e71f3a',
    '0b5a84bb81f5615feba687924c785b1a94528d4028b6630b43670eda8c65506b',
    'ac139129ef0e412e94970ec4725eebf6c1adcda5343a0f24ed14d3dc86174ce4',
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    prep = load(BASE / 'later-ms4-archive-preparation-2026-09-24.json')
    evidence = load(BASE / 'later-ms4-archive-public-byte-verification-2026-09-25.json')
    r2 = load(ROOT / 'project-state/r2-inventory.json')
    inventory = {r['id']: r for r in load(ROOT / 'project-state/master-inventory.json')['candidates']}
    implemented = (BASE / 'later-ms4-hugo-implementation-2026-09-25.json').exists()
    assert evidence['state'] == 'complete_all_six_public_byte_verified_and_inventory_reconciled'
    assert prep['candidate_ids_in_order'] == list(IDS)
    assert len(prep['records']) == len(evidence['preflight']) == len(evidence['results']) == 6
    assert [r['id'] for r in evidence['results']] == list(IDS)
    assert [r['r2_key'] for r in evidence['results']] == list(KEYS)
    assert [r['expected_size_bytes'] for r in evidence['results']] == list(SIZES)
    assert [r['expected_checksum_sha256'] for r in evidence['results']] == list(HASHES)
    assert evidence['max_object_bytes'] == 150000000
    assert evidence['max_projected_storage_bytes'] == 10000000000
    assert evidence['summary']['public_byte_verified'] == 6
    assert evidence['summary']['uploaded_now'] + evidence['summary']['exact_existing_after_interrupted_resume'] == 6
    assert evidence['summary']['added_bytes'] == sum(SIZES) == 426926738
    assert evidence['before_r2']['object_count'] == 1231
    assert evidence['before_r2']['total_bytes'] == 8791355104
    assert evidence['after_r2']['object_count'] == r2['object_count'] == 1237
    assert evidence['after_r2']['total_bytes'] == r2['total_bytes'] == 9218281842
    accounting = evidence['accounting']
    assert accounting['new_objects'] == 6 and accounting['new_bytes'] == 426926738
    assert accounting['pre_existing_object_count'] == 1231
    assert accounting['pre_existing_objects_unchanged'] is True and accounting['unexpected_objects_added'] is False
    assert accounting['pre_existing_manifest_sha256_before'] == accounting['pre_existing_manifest_sha256_after']
    assert len(accounting['pre_existing_manifest_sha256_before']) == 64
    assert evidence['r2_inventory_accounting']['records_updated'] == 6
    assert evidence['r2_inventory_accounting']['inventory_status'] == 'placement assigned'
    assert evidence['visitor_visible_content_changed'] is False
    assert inventory['src-185f33493177b085']['status'] == 'superseded'
    assert inventory['src-3408f5b9a86bcb5c']['status'] == 'excluded'
    objects = {o['key']: o for o in r2['objects']}
    assert len(objects) == r2['object_count']
    for prep_row, result, key, size, checksum in zip(prep['records'], evidence['results'], KEYS, SIZES, HASHES):
        row = inventory[result['id']]
        staged = ROOT / prep_row['staged_original']
        assert staged.stat().st_size == size and digest(staged) == checksum
        assert result['action'] in ('uploaded_now', 'exact_existing_after_interrupted_resume') and result['http_public_get'] == 'passed'
        assert result['byte_identical'] is True
        assert result['public_size_bytes'] == size and result['public_checksum_sha256'] == checksum
        assert result['public_url'] == 'https://files.abqinfo.com/' + key
        assert result['source_url'] == prep_row['authoritative_source_url'] == row['direct_file_url']
        assert objects[key]['size_bytes'] == size and objects[key]['public_url'] == result['public_url']
        assert row['status'] == ('implemented' if implemented else 'placement assigned')
        assert row['r2_key'] == key and row['r2_url'] == result['public_url']
        assert row['size_bytes'] == size and row['checksum_sha256'] == checksum
        assert row['local_path'] == prep_row['staged_original']
        assert row['proposed_canonical_page'] == 'content/public-works/stormwater-drainage.md'
        assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
    print('later-MS4 archive: six exact public objects, 426,926,738 added bytes, R2 1,237 / 9,218,281,842, ' + ('implemented on branch' if implemented else 'placement assigned'))


if __name__ == '__main__':
    main()
