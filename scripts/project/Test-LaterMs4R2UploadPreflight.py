#!/usr/bin/env python3
"""Validate the exact six-record no-mutation later-MS4 upload manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / 'project-state/discovery/later-ms4-archive-preparation-2026-09-24.json'
PREFLIGHT = ROOT / 'project-state/discovery/later-ms4-r2-upload-preflight-2026-09-24.json'


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    prep, manifest = load(PREP), load(PREFLIGHT)
    assert manifest['state'] == 'no_mutation_preflight_complete_awaiting_explicit_upload_authorization'
    assert manifest['candidate_ids_in_order'] == prep['candidate_ids_in_order']
    assert len(manifest['candidate_ids_in_order']) == len(set(manifest['candidate_ids_in_order'])) == len(manifest['records']) == 6
    assert manifest['aggregate_staged_bytes'] == prep['summary']['total_staged_bytes'] == 426926738
    assert manifest['r2_baseline']['object_count'] == 1231
    assert manifest['r2_baseline']['total_bytes'] == 8791355104
    assert manifest['expected_r2_after_six_new_objects'] == {
        'object_count': 1237, 'total_bytes': 9218281842, 'added_objects': 6, 'added_bytes': 426926738,
    }
    assert manifest['collision_check']['result'] == 'passed_all_six_destinations_absent_no_known_duplicate_bytes'
    assert not manifest['collision_check']['exact_key_collisions']
    assert not manifest['collision_check']['same_size_live_objects']
    assert not manifest['collision_check']['known_same_sha256_archived_inventory_records']
    assert manifest['tooling_readiness']['credentials_accessible'] is True
    assert manifest['tooling_readiness']['six_whatif_probes_passed_without_upload'] is True
    assert manifest['tooling_readiness']['required_max_object_bytes_argument'] == 150000000
    assert manifest['tooling_readiness']['max_projected_storage_bytes_argument'] == 10000000000
    assert manifest['tooling_readiness']['large_object_ids_requiring_explicit_limit_override'] == [
        'src-fdc66c5b8de48584', 'src-7c1a063b817989bd', 'src-eda3280085776f61',
    ]
    assert manifest['r2_mutation'] is False and manifest['public_byte_verification_performed'] is False
    assert manifest['inventory_status_unchanged'] is True and manifest['inventory_r2_fields_unassigned'] is True
    assert manifest['visitor_visible_content_changed'] is False
    command = manifest['execution_after_authorization']['upload_command_and_public_byte_verification']
    for phrase in ('Get-R2Inventory.ps1', 'upload-r2-document.ps1', 'Test-R2PublicObject.ps1', '-MaxObjectBytes 150000000', 'Get-FileHash'):
        assert phrase in command
    assert manifest['execution_after_authorization']['authorization_required'].startswith('Explicit owner authorization')
    inventory = {r['id']: r for r in load(ROOT / 'project-state/master-inventory.json')['candidates']}
    for prepared, record in zip(prep['records'], manifest['records']):
        row = inventory[record['id']]
        path = ROOT / record['staged_path']
        assert record['id'] == prepared['id']
        assert record['staged_path'] == prepared['staged_original'] == row['local_path']
        assert record['source_size_bytes'] == prepared['size_bytes'] == row['size_bytes'] == path.stat().st_size
        assert record['source_sha256'] == prepared['checksum_sha256'] == row['checksum_sha256'] == digest(path)
        assert record['proposed_r2_key'] == prepared['proposed_r2_key']
        assert record['expected_public_archive_url'] == prepared['proposed_future_archive_url']
        assert row['status'] == 'approved for addition' and row['r2_key'] is None and row['r2_url'] is None
        assert record['current_r2_key_absent'] and record['current_r2_same_size_object_absent']
    print('later-MS4 R2 preflight: six exact staged originals, 426,926,738 bytes, 1,231 -> 1,237 objects; no mutation')


if __name__ == '__main__':
    main()
