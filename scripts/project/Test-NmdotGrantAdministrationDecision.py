#!/usr/bin/env python3
"""Validate the saved NMDOT grant-administration inventory-only decision."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'project-state/discovery/nmdot-file-host-cluster-research-2026-09-13.json'
DECISION = ROOT / 'project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

research = load(RESEARCH)
saved = {}
for value in research.values():
    if isinstance(value, list):
        for record in value:
            if isinstance(record, dict) and record.get('group') == 'grant administration and application':
                saved[record['id']] = record
decision = load(DECISION)
records = {record['id']: record for record in decision['records']}
inventory = {record['id']: record for record in load(INVENTORY)['candidates']}

assert len(saved) == len(records) == 18
assert set(saved) == set(records)
assert decision['state'] == 'approved_for_addition_inventory_only'
assert decision['placement_review']['decision'] == 'unresolved_for_all_records'
for candidate_id, saved_record in saved.items():
    record, candidate = records[candidate_id], inventory[candidate_id]
    for field in ('title', 'description', 'publisher', 'served_filename', 'size_bytes', 'checksum_sha256'):
        assert record[field] == saved_record[field], f'{candidate_id} {field} drifted from saved research'
    assert record['container'] == saved_record['content_kind']
    assert record['leading_bytes'] == saved_record['leading_bytes']
    assert record['status'] == candidate['status'] == 'approved for addition'
    assert record['placement'] == 'unresolved'
    assert candidate['source_url'] == candidate['direct_file_url'] == saved_record['authoritative_url']
    assert candidate['agency'] == 'New Mexico Department of Transportation'
    assert candidate['size_bytes'] == saved_record['size_bytes']
    assert candidate['checksum_sha256'] == saved_record['checksum_sha256']
    assert candidate['proposed_canonical_page'] is None
    assert not candidate['implementation_locations'] and not candidate['implementation_location']
    assert not candidate['r2_url'] and not candidate['r2_key']
    assert any('Saved publisher: New Mexico Department of Transportation.' in note for note in candidate['processing_notes'])
    assert any('realfile.rtsclients.com delivery host is not treated as publisher.' in note for note in candidate['processing_notes'])

print('PASS: all 18 saved NMDOT grant-administration decisions retain metadata, original containers, unresolved placement, and archive gates.')
