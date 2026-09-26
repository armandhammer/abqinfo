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
pgs_validated_ids = set()
later_ms4_archived_ids = set()
later_ms4_implemented_ids = set()
later_ms4_validated_ids = set()
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
pgs_closeout_path = DISCOVERY / 'planned-growth-strategy-production-closeout-2026-09-24.json'
if pgs_closeout_path.exists():
    pgs_closeout = json.loads(pgs_closeout_path.read_text(encoding='utf-8'))
    assert pgs_closeout['production_verification_result'] == 'passed'
    pgs_validated_ids = set(pgs_closeout['ordered_inventory_ids'])
    assert len(pgs_validated_ids) == 13 and pgs_validated_ids == pgs_implemented_ids
later_ms4_archive_path = DISCOVERY / 'later-ms4-archive-public-byte-verification-2026-09-25.json'
if later_ms4_archive_path.exists():
    later_ms4_archive = json.loads(later_ms4_archive_path.read_text(encoding='utf-8-sig'))
    if later_ms4_archive['state'] == 'complete_all_six_public_byte_verified_and_inventory_reconciled':
        assert later_ms4_archive['summary']['public_byte_verified'] == 6
        later_ms4_archived_ids = {result['id'] for result in later_ms4_archive['results']}
        assert len(later_ms4_archived_ids) == 6
later_ms4_implementation_path = DISCOVERY / 'later-ms4-hugo-implementation-2026-09-25.json'
if later_ms4_implementation_path.exists():
    later_ms4_implementation = json.loads(later_ms4_implementation_path.read_text(encoding='utf-8-sig'))
    assert later_ms4_implementation['state'] == 'implemented_on_planning_branch_not_live'
    later_ms4_implemented_ids = set(later_ms4_implementation['implemented_inventory_ids'])
    assert later_ms4_implemented_ids == later_ms4_archived_ids
later_ms4_closeout_path = DISCOVERY / 'later-ms4-production-closeout-2026-09-25.json'
if later_ms4_closeout_path.exists():
    later_ms4_closeout = json.loads(later_ms4_closeout_path.read_text(encoding='utf-8-sig'))
    assert later_ms4_closeout['production_verification_result'] == 'passed'
    later_ms4_validated_ids = set(later_ms4_closeout['inventory_ids_to_validate'])
    assert later_ms4_validated_ids == later_ms4_implemented_ids

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
barelas_reconciliation_path = DISCOVERY / 'planning-documents-root-barelas-duplicate-reconciliation-2026-09-26.json'
barelas_reconciled_id = None
if barelas_reconciliation_path.exists():
    reconciliation = json.loads(barelas_reconciliation_path.read_text(encoding='utf-8-sig'))
    assert reconciliation['state'] == 'reconciled_exact_duplicate'
    assert reconciliation['duplicate_id'] == 'src-d9bf34830a9467e2'
    assert reconciliation['canonical_id'] == 'src-28418cab91a745a6'
    alias, canonical = by_id[reconciliation['duplicate_id']], by_id[reconciliation['canonical_id']]
    assert canonical['status'] == 'validated'
    assert alias['size_bytes'] == canonical['size_bytes'] == reconciliation['size_bytes'] == 8719030
    assert alias['checksum_sha256'] == canonical['checksum_sha256'] == reconciliation['checksum_sha256'] == 'c2081c6cbc60b029c2b558a73ad975b429b03e89cc1837c393f8b5c30191ae19'
    assert reconciliation['exact_public_byte_evidence']['record']['byte_identical'] is True
    assert canonical['direct_file_url'] in alias['cited_successors']
    barelas_reconciled_id = reconciliation['duplicate_id']
for record in records:
    assert set(record['scope_assessment']) == required
    candidate = by_id[record['id']]
    expected_status = ('validated' if record['id'] in pgs_validated_ids else 'implemented' if record['id'] in pgs_implemented_ids else 'placement assigned') if record['id'] in pgs_archived_ids and record['resulting_status'] == 'approved for addition' else record['resulting_status']
    if record['id'] in later_ms4_archived_ids and record['resulting_status'] == 'approved for addition':
        expected_status = 'validated' if record['id'] in later_ms4_validated_ids else 'implemented' if record['id'] in later_ms4_implemented_ids else 'placement assigned'
    if record['id'] == barelas_reconciled_id:
        assert record['resulting_status'] == 'approved for addition'
        expected_status = 'duplicate'
    assert candidate['status'] == expected_status
    assert candidate['scope_assessment'] == record['scope_assessment']
for candidate in inventory['candidates']:
    if candidate['status'] == 'approved for addition':
        assessment = candidate.get('scope_assessment', {})
        assert set(assessment) == required, candidate['id']
        assert assessment['final_scope_decision'] == 'passes_both_gates', candidate['id']
print('PASS: mission-scope audit reconciles the 86-record starting population, preserves one structured disposition per record, and ranks only the 58 positive-scope records.')
