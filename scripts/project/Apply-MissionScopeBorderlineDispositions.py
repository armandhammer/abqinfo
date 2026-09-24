#!/usr/bin/env python3
"""Apply durable human Add/Exclude/Needs-more-research decisions to scope-borderline cases."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / 'project-state/master-inventory.json'
DEFAULT_QUEUE = ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json'
POSITIVE = {'assessed_at', 'geographic_institutional_scope', 'specific_albuquerque_connection', 'abqinfo_public_information_value', 'general_context_exclusion_test', 'final_scope_decision', 'substantive_rationale'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    temporary = path.with_name(path.name + '.mission-scope-tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)

def disposition_key(artifact, item):
    payload = {'decision_artifact': str(artifact), 'id': item['id'], 'decision': item['decision'],
               'rationale': item['rationale'], 'approved_scope_assessment': item.get('approved_scope_assessment')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

def excluded_assessment(borderline, rationale, recorded_at):
    return {
        'assessed_at': recorded_at,
        'geographic_institutional_scope': borderline['geographic_institutional_scope'],
        'specific_albuquerque_connection': borderline['specific_albuquerque_connection'],
        'abqinfo_public_information_value': borderline['potential_abqinfo_public_information_value'],
        'general_context_exclusion_test': borderline['reason_does_not_confidently_pass'],
        'final_scope_decision': 'excluded_insufficient_abqinfo_usefulness',
        'substantive_rationale': rationale,
    }

def recompute(inventory):
    counts = Counter(candidate['status'] for candidate in inventory['candidates'])
    inventory['counts'] = {status: counts[status] for status in inventory['allowed_statuses']}
    pending_statuses = {'pending review', 'approved for addition', 'downloaded', 'parsed', 'description drafted', 'placement assigned'}
    candidates = [candidate['id'] for candidate in inventory['candidates'] if candidate['status'] in pending_statuses or (candidate['status'] == 'implemented' and candidate['validation_status'] != 'passed')]
    inventory['next_pending_id'] = min(candidates) if candidates else None
    inventory['generated_at'] = datetime.now(timezone.utc).isoformat()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dispositions', required=True, type=Path, help='JSON with decision_artifact and dispositions[].')
    parser.add_argument('--inventory', type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument('--queue', type=Path, default=DEFAULT_QUEUE)
    args = parser.parse_args()
    request = read(args.dispositions)
    decision_artifact = Path(request['decision_artifact'])
    if not decision_artifact.is_absolute(): decision_artifact = ROOT / decision_artifact
    if not decision_artifact.exists(): raise ValueError('The relevant family decision artifact must exist before applying human dispositions.')
    inventory, queue, decision = read(args.inventory), read(args.queue), read(decision_artifact)
    prior_candidates = json.dumps(inventory['candidates'], sort_keys=True, ensure_ascii=False)
    prior_queue = json.dumps(queue, sort_keys=True, ensure_ascii=False)
    candidates = {candidate['id']: candidate for candidate in inventory['candidates']}
    unresolved = {record['id']: record for record in queue['records']}
    resolved = {record['id']: record for record in queue.get('resolved_records', [])}
    if len(resolved) != len(queue.get('resolved_records', [])):
        raise ValueError('Queue resolved history contains duplicate candidate IDs.')
    items = request['dispositions']
    if len({item['id'] for item in items}) != len(items):
        raise ValueError('A candidate may appear only once in a human disposition batch.')
    recorded_at = request.get('recorded_at') or datetime.now(timezone.utc).date().isoformat()
    applied = []
    for item in items:
        candidate = candidates.get(item['id'])
        key = disposition_key(decision_artifact, item)
        if item['id'] in resolved:
            if resolved[item['id']].get('disposition_key') != key:
                raise ValueError(f"{item['id']} already has a different resolved human scope disposition.")
            continue
        if candidate is None or item['id'] not in unresolved:
            raise ValueError(f"{item['id']} is not an unresolved mission-scope-borderline queue member.")
        action = item['decision']
        rationale = item['rationale'].strip()
        if not rationale:
            raise ValueError(f"{item['id']} requires a substantive human rationale.")
        borderline = unresolved[item['id']]['scope_assessment']
        if candidate['status'] != 'requires human review' or candidate.get('review_reason') != 'mission_scope_borderline':
            # A prior invocation can have saved inventory before saving queue history.
            if action == 'Add' and candidate['status'] == 'approved for addition' and candidate.get('scope_assessment') == item.get('approved_scope_assessment'):
                pass
            elif action == 'Exclude' and candidate['status'] == 'excluded' and candidate.get('scope_assessment') == excluded_assessment(borderline, rationale, recorded_at):
                pass
            else:
                raise ValueError(f"{item['id']} no longer has the required mission-scope-borderline state.")
        if action == 'Add':
            assessment = item['approved_scope_assessment']
            if set(assessment) != POSITIVE or assessment['final_scope_decision'] != 'passes_both_gates' or any(not str(value).strip() for value in assessment.values()):
                raise ValueError(f"{item['id']} Add requires a complete positive scope assessment.")
            candidate['scope_assessment'] = assessment
            candidate['status'] = 'approved for addition'
            candidate.pop('review_reason', None)
        elif action == 'Exclude':
            candidate['scope_assessment'] = excluded_assessment(borderline, rationale, recorded_at)
            candidate['status'] = 'excluded'
            candidate['exclusion_reason'] = rationale
            candidate.pop('review_reason', None)
        elif action == 'Needs more research':
            if candidate['status'] != 'requires human review' or candidate.get('review_reason') != 'mission_scope_borderline':
                raise ValueError(f"{item['id']} is no longer unresolved for more research.")
            note = f"Mission-scope human review: Needs more research. {rationale}"
            if note not in candidate['processing_notes']:
                candidate['processing_notes'].append(note)
        else:
            raise ValueError(f"{item['id']} has invalid decision {action!r}.")
        if action != 'Needs more research':
            history = candidate.setdefault('scope_assessment_history', [])
            if not any(entry.get('disposition_key') == key for entry in history):
                history.append({'disposition_key': key, 'recorded_at': recorded_at, 'review_reason': 'mission_scope_borderline',
                                'prior_scope_assessment': borderline, 'human_decision': action, 'human_rationale': rationale})
            resolved[item['id']] = {'id': item['id'], 'disposition_key': key, 'recorded_at': recorded_at,
                                    'decision': action, 'rationale': rationale, 'prior_scope_assessment': borderline,
                                    'resulting_status': candidate['status'], 'final_scope_assessment': candidate['scope_assessment'],
                                    'decision_artifact': str(decision_artifact)}
        applied.append({'id': item['id'], 'disposition_key': key, 'decision': action, 'rationale': rationale,
                        'resulting_status': candidate['status']})
    inventory_changed = json.dumps(inventory['candidates'], sort_keys=True, ensure_ascii=False) != prior_candidates
    if inventory_changed:
        recompute(inventory)
    existing = {entry['disposition_key'] for batch in decision.get('mission_scope_human_dispositions', []) for entry in batch['dispositions']}
    new_entries = [entry for entry in applied if entry['disposition_key'] not in existing]
    if new_entries:
        decision.setdefault('mission_scope_human_dispositions', []).append({'recorded_at': recorded_at, 'dispositions': new_entries})
    queue['resolved_records'] = [resolved[candidate_id] for candidate_id in sorted(resolved)]
    queue_changed = json.dumps(queue, sort_keys=True, ensure_ascii=False) != prior_queue
    if inventory_changed:
        write(args.inventory, inventory)
    if new_entries:
        write(decision_artifact, decision)
    if queue_changed:
        write(args.queue, queue)
    # Regeneration retains the persisted resolved history and leaves research cases unresolved.
    import subprocess, sys
    if inventory_changed or queue_changed:
        subprocess.run([sys.executable, str(ROOT / 'scripts/project/Sync-MissionScopeBorderlineQueue.py'), '--inventory', str(args.inventory), '--queue', str(args.queue), '--recorded-at', recorded_at], check=True)
    print(json.dumps({'applied': applied, 'decision_artifact': str(decision_artifact)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
