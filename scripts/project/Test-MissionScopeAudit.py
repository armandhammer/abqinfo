#!/usr/bin/env python3
"""Regression checks for the 2026-09-22 mission-scope correction."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / 'project-state/discovery'
inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
audit = json.loads((DISCOVERY / 'approved-inventory-mission-scope-audit-2026-09-22.json').read_text(encoding='utf-8'))
priority = json.loads((DISCOVERY / 'approved-inventory-backlog-prioritization-mission-scope-2026-09-22.json').read_text(encoding='utf-8'))
pgs_archive_path = DISCOVERY / 'planned-growth-strategy-archive-public-byte-verification-2026-09-23.json'
pgs_archived_ids = set()
pgs_implemented_ids = set()
if pgs_archive_path.exists():
    pgs_archive = json.loads(pgs_archive_path.read_text(encoding='utf-8'))
    assert pgs_archive['state'] == 'complete_all_13_public_byte_verified_and_inventory_reconciled'
    assert pgs_archive['summary']['public_byte_verified'] == 13
    pgs_archived_ids = {result['id'] for result in pgs_archive['results']}
    assert len(pgs_archived_ids) == 13
pgs_implementation_path = DISCOVERY / 'planned-growth-strategy-hugo-implementation-2026-09-23.json'
if pgs_implementation_path.exists():
    pgs_implementation = json.loads(pgs_implementation_path.read_text(encoding='utf-8'))
    assert pgs_implementation['state'] == 'implemented_on_planning_branch_not_live'
    pgs_implemented_ids = set(pgs_implementation['implemented_inventory_ids'])
    assert pgs_implemented_ids == pgs_archived_ids

required = {'assessed_at', 'geographic_institutional_scope', 'specific_albuquerque_connection', 'abqinfo_public_information_value', 'general_context_exclusion_test', 'final_scope_decision', 'substantive_rationale'}
records = audit['records']
assert audit['starting_population']['count'] == 86 == len(records)
assert len({r['id'] for r in records}) == 86
assert audit['accounting'] == {'starting_approved': 86, 'remains_approved': 58, 'excluded_insufficient_albuquerque_relevance': 25, 'excluded_insufficient_abqinfo_usefulness': 3, 'requires_human_review': 0, 'reconciled_total': 86}
assert sum(1 for r in records if r['resulting_status'] == 'approved for addition') == 58
assert sum(1 for r in records if r['scope_assessment']['final_scope_decision'] == 'excluded_insufficient_albuquerque_relevance') == 25
assert sum(1 for r in records if r['scope_assessment']['final_scope_decision'] == 'excluded_insufficient_abqinfo_usefulness') == 3
assert sum(g['candidate_count'] for g in priority['family_groups']) == 58
assert priority['eligible_population']['count'] == 58

by_id = {c['id']: c for c in inventory['candidates']}
for record in records:
    assert set(record['scope_assessment']) == required
    candidate = by_id[record['id']]
    expected_status = ('implemented' if record['id'] in pgs_implemented_ids else 'placement assigned') if record['id'] in pgs_archived_ids and record['resulting_status'] == 'approved for addition' else record['resulting_status']
    assert candidate['status'] == expected_status
    assert candidate['scope_assessment'] == record['scope_assessment']
for candidate in inventory['candidates']:
    if candidate['status'] == 'approved for addition':
        assessment = candidate.get('scope_assessment', {})
        assert set(assessment) == required, candidate['id']
        assert assessment['final_scope_decision'] == 'passes_both_gates', candidate['id']
print('PASS: mission-scope audit reconciles the 86-record starting population, preserves one structured disposition per record, and ranks only the 58 positive-scope records.')
