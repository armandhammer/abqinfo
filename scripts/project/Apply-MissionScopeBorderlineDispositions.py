#!/usr/bin/env python3
"""Apply durable human Add/Exclude/Needs-more-research decisions to scope-borderline cases."""
import argparse
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
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

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
    candidates = {candidate['id']: candidate for candidate in inventory['candidates']}
    unresolved = {record['id'] for record in queue['records']}
    applied = []
    for item in request['dispositions']:
        candidate = candidates.get(item['id'])
        if candidate is None or item['id'] not in unresolved:
            raise ValueError(f"{item['id']} is not an unresolved mission-scope-borderline queue member.")
        if candidate['status'] != 'requires human review' or candidate.get('review_reason') != 'mission_scope_borderline':
            raise ValueError(f"{item['id']} no longer has the required mission-scope-borderline state.")
        action = item['decision']
        rationale = item['rationale']
        if action == 'Add':
            assessment = item['approved_scope_assessment']
            if set(assessment) != POSITIVE or assessment['final_scope_decision'] != 'passes_both_gates':
                raise ValueError(f"{item['id']} Add requires a complete positive scope assessment.")
            candidate['scope_assessment'] = assessment
            candidate['status'] = 'approved for addition'
            candidate.pop('review_reason', None)
        elif action == 'Exclude':
            candidate['status'] = 'excluded'
            candidate['exclusion_reason'] = rationale
            candidate.pop('review_reason', None)
        elif action == 'Needs more research':
            candidate['processing_notes'].append(f"Mission-scope human review: Needs more research. {rationale}")
        else:
            raise ValueError(f"{item['id']} has invalid decision {action!r}.")
        applied.append({'id': item['id'], 'decision': action, 'rationale': rationale})
    recompute(inventory)
    decision.setdefault('mission_scope_human_dispositions', []).append({'recorded_at': request.get('recorded_at'), 'dispositions': applied})
    queue.setdefault('resolved_records', []).extend([item for item in applied if item['decision'] != 'Needs more research'])
    write(args.inventory, inventory)
    write(decision_artifact, decision)
    # Queue must be regenerated after durable inventory and decision-artifact writes.
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT / 'scripts/project/Sync-MissionScopeBorderlineQueue.py'), '--inventory', str(args.inventory), '--queue', str(args.queue), '--recorded-at', request.get('recorded_at') or datetime.now(timezone.utc).date().isoformat()], check=True)
    print(json.dumps({'applied': applied, 'decision_artifact': str(decision_artifact)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
