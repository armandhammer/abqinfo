#!/usr/bin/env python3
"""Exercise Add, Exclude, research, persisted history, and safe reruns."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts/project'
TEMPLATE = ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json'

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def run(script, *args):
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True, capture_output=True, text=True)

with tempfile.TemporaryDirectory(prefix='abqinfo-scope-dispositions-') as directory:
    root = Path(directory)
    inventory_path, queue_path = root / 'inventory.json', root / 'queue.json'
    artifact_path, request_path = root / 'decision.json', root / 'request.json'
    borderline = {
        'assessed_at': '2026-09-23', 'title': 'Borderline City study', 'publisher': 'City of Albuquerque',
        'date': '2026-01-01', 'geographic_institutional_scope': 'A City program',
        'specific_albuquerque_connection': 'A material City project',
        'potential_abqinfo_public_information_value': 'May clarify a City decision',
        'reason_does_not_confidently_pass': 'Its policy significance is close.',
        'reason_does_not_clearly_fail': 'The City project is substantive.',
        'proposed_page_or_section_if_admitted': 'City Projects',
        'recommended_default_disposition': 'Needs more research',
        'final_scope_decision': 'requires_human_scope_review',
        'substantive_rationale': 'A material City connection exists, while the public value calls for editorial judgment.',
    }
    candidates = [{
        'id': f'test-scope-{action}', 'status': 'requires human review', 'review_reason': 'mission_scope_borderline',
        'scope_assessment': dict(borderline), 'title': borderline['title'], 'agency': borderline['publisher'],
        'date': borderline['date'], 'source_url': f'https://example.invalid/{action}', 'direct_file_url': None,
        'validation_status': None, 'processing_notes': [],
    } for action in ('add', 'exclude', 'research')]
    inventory = {'allowed_statuses': ['pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned','implemented','validated','excluded','duplicate','superseded','blocked','requires human review'],
                 'candidates': candidates, 'counts': {'requires human review': 3}, 'next_pending_id': None}
    write(inventory_path, inventory)
    write(queue_path, read(TEMPLATE))
    write(artifact_path, {'artifact_type': 'test_family_decision'})
    run('Sync-MissionScopeBorderlineQueue.py', '--inventory', inventory_path, '--queue', queue_path, '--recorded-at', '2026-09-23')
    positive = {
        'assessed_at': '2026-09-23', 'geographic_institutional_scope': 'A City program',
        'specific_albuquerque_connection': 'A material City project',
        'abqinfo_public_information_value': 'Clarifies a City decision',
        'general_context_exclusion_test': 'The specific City project is the subject.',
        'final_scope_decision': 'passes_both_gates',
        'substantive_rationale': 'The human editor found that this record materially explains the City project.',
    }
    write(request_path, {'recorded_at': '2026-09-23', 'decision_artifact': str(artifact_path), 'dispositions': [
        {'id': 'test-scope-add', 'decision': 'Add', 'rationale': 'Material City value.', 'approved_scope_assessment': positive},
        {'id': 'test-scope-exclude', 'decision': 'Exclude', 'rationale': 'Too little public information beyond the City source.'},
        {'id': 'test-scope-research', 'decision': 'Needs more research', 'rationale': 'Clarify the decision context.'},
    ]})
    run('Apply-MissionScopeBorderlineDispositions.py', '--dispositions', request_path,
        '--inventory', inventory_path, '--queue', queue_path)
    output, queue, decision = read(inventory_path), read(queue_path), read(artifact_path)
    by_id = {candidate['id']: candidate for candidate in output['candidates']}
    assert by_id['test-scope-add']['scope_assessment'] == positive
    assert by_id['test-scope-add']['status'] == 'approved for addition'
    excluded = by_id['test-scope-exclude']
    assert excluded['status'] == 'excluded'
    assert excluded['scope_assessment']['final_scope_decision'] == 'excluded_insufficient_abqinfo_usefulness'
    assert excluded['scope_assessment_history'][0]['prior_scope_assessment'] == borderline
    assert excluded['exclusion_reason'] == 'Too little public information beyond the City source.'
    assert by_id['test-scope-research']['status'] == 'requires human review'
    assert by_id['test-scope-research']['scope_assessment']['final_scope_decision'] == 'requires_human_scope_review'
    assert len(queue['resolved_records']) == 2
    assert [record['id'] for record in queue['records']] == ['test-scope-research']
    assert len(decision['mission_scope_human_dispositions']) == 1
    before = [path.read_bytes() for path in (inventory_path, queue_path, artifact_path)]
    run('Apply-MissionScopeBorderlineDispositions.py', '--dispositions', request_path,
        '--inventory', inventory_path, '--queue', queue_path)
    assert before == [path.read_bytes() for path in (inventory_path, queue_path, artifact_path)]
    assert len(read(inventory_path)['candidates'][2]['processing_notes']) == 1

print('PASS: Add and Exclude persist final assessments and prior borderline history; research remains queued; reruns are byte-identical.')
