#!/usr/bin/env python3
"""Validate the two-record Municipal Development archive-preparation decision."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'project-state/discovery/municipaldevelopment-procurement-cluster-research-2026-09-12.json'
DECISION = ROOT / 'project-state/discovery/municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'
R2 = ROOT / 'project-state/r2-inventory.json'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

research = {r['id']: r for r in load(RESEARCH)['approved_for_addition']}
decision = load(DECISION)
records = {r['id']: r for r in decision['records']}
inventory = {r['id']: r for r in load(INVENTORY)['candidates']}
r2_keys = {r['key'] for r in load(R2)['objects']}
expected = {'src-b3d8dcb56e000437', 'src-4952ea05cd055792'}

assert decision['state'] == 'approved_for_addition_archive_preparation_complete_external_archive_and_publication_gated'
assert decision['superseded_by_mission_scope_audit']['historical_evidence_preserved'] is True
assert decision['superseded_by_mission_scope_audit']['r2_or_publication_action_authorized'] is False
assert set(records) == expected == set(research)
assert decision['placement_review']['canonical_page'] == 'content/development-land-use/development-process.md'
assert decision['placement_review']['cross_listing']['decision'] == 'rejected_for_future_publication'
for candidate_id in sorted(expected):
    record, saved, candidate = records[candidate_id], research[candidate_id], inventory[candidate_id]
    assert record['status'] == 'approved for addition'
    assert candidate['status'] == 'excluded'
    assert record['accepted_title'] == candidate['title'] == saved['title']
    assert record['authoritative_source_url'] == candidate['direct_file_url'] == saved['authoritative_url']
    for field in ('size_bytes', 'checksum_sha256'):
        assert record[field] == candidate[field] == saved[field], f'{candidate_id} {field} drifted'
    assert record['page_count'] == saved['pages']
    assert record['container'] == saved['content_kind'] == candidate['file_type'] == 'PDF'
    assert record['leading_bytes'] == saved['leading_bytes'] == '25504446'
    assert record['proposed_r2_key'] not in r2_keys
    assert candidate['r2_key'] is None and candidate['r2_url'] is None
    assert candidate['implementation_location'] is None and not candidate['implementation_locations']
    assert candidate['validation_status'].startswith('approved for addition:')
    assessment = record['quality_assessment']
    assert set(assessment) == {'visual_document_quality', 'page_text_content', 'standalone_public_value', 'information_density', 'family_companion_relationship', 'intended_publication_form', 'substantive_rationale'}
assert records['src-b3d8dcb56e000437']['date_handling'].startswith('Use 2017-10-04')
assert records['src-4952ea05cd055792']['date_handling'].startswith('No date may be assigned')
print('PASS: Municipal Development standard-form archive preparation retains exact source evidence, future-only placement, and external archive/publication gates.')
