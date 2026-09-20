#!/usr/bin/env python3
"""Validate the bounded MRA Appeal Form delivery-alias decision."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / 'project-state/discovery/mra-appeal-form-family-decision-2026-09-19.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'
CHECKPOINT = ROOT / 'project-state/checkpoint.json'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

decision, inventory, checkpoint = load(DECISION), load(INVENTORY), load(CHECKPOINT)
records = {record['id']: record for record in inventory['candidates']}
expected = {'src-090b501b1579de50', 'src-cb776cdbd1f3ec08'}
excluded = decision['dispositions']['excluded']

assert decision['family']['scope_candidate_ids'] == sorted(expected)
assert {record['id'] for record in excluded} == expected
assert len(excluded) == 2
assert not any(decision['dispositions'][key] for key in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review'))
assert decision['quality_assessments'] == []
assert decision['placement_review']['canonical_page'] is None
assert decision['family_relationships']['publication_canonical'] is None
for candidate_id in expected:
    candidate = records[candidate_id]
    assert candidate['status'] == 'excluded'
    assert candidate['size_bytes'] == 42712
    assert candidate['checksum_sha256'] == 'f87a15739db517f2dbeb4f2c1ee85d2e973f5566af1a9178420ade6cf219bee2'
    assert candidate['r2_url'] is None and candidate['r2_key'] is None
    assert candidate['implementation_location'] is None and not candidate['implementation_locations']
    assert candidate['exclusion_reason']
assert any(note.startswith('Discovered by deterministic crawl') for note in records['src-090b501b1579de50']['processing_notes'])
assert any(note.startswith('MRA Appeal Form family decision 2026-09-19:') for note in records['src-090b501b1579de50']['processing_notes'])
assert decision['ordinary_queue_handoff']['next_actionable_candidate'] == 'src-09592fba403c1e2f'
# The MRA artifact keeps its historical handoff. CURRENT checkpoint state may
# legitimately advance after that next family is completed.
assert 'src-090b501b1579de50' not in checkpoint['resume_command']
assert checkpoint['counts_by_status'] == inventory['counts']
assert checkpoint['remaining_nonterminal'] == sum(
    row['status'] in {'pending review', 'approved for addition', 'downloaded', 'parsed', 'description drafted', 'placement assigned'}
    or (row['status'] == 'implemented' and row['validation_status'] != 'passed')
    for row in inventory['candidates']
)
print('PASS: MRA Appeal Form aliases remain bounded, excluded, provenance-preserving, and non-publication records.')
