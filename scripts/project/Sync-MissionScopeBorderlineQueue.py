#!/usr/bin/env python3
"""Regenerate the dedicated queue of unresolved mission-scope-borderline cases."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / 'project-state/master-inventory.json'
DEFAULT_QUEUE = ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json'
REQUIRED = {
    'assessed_at', 'title', 'publisher', 'date', 'geographic_institutional_scope',
    'specific_albuquerque_connection', 'potential_abqinfo_public_information_value',
    'reason_does_not_confidently_pass', 'reason_does_not_clearly_fail',
    'proposed_page_or_section_if_admitted', 'recommended_default_disposition',
    'final_scope_decision', 'substantive_rationale',
}

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def queue_records(inventory):
    records = []
    for candidate in inventory['candidates']:
        if candidate['status'] != 'requires human review' or candidate.get('review_reason') != 'mission_scope_borderline':
            continue
        assessment = candidate.get('scope_assessment', {})
        if set(assessment) != REQUIRED or assessment.get('final_scope_decision') != 'requires_human_scope_review':
            raise ValueError(f"{candidate['id']} is a mission-scope borderline record without a complete structured assessment.")
        records.append({
            'id': candidate['id'], 'title': candidate['title'], 'publisher': candidate['agency'], 'date': candidate['date'],
            'source_url': candidate['direct_file_url'] or candidate['source_url'],
            'scope_assessment': assessment,
        })
    return sorted(records, key=lambda record: record['id'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument('--queue', type=Path, default=DEFAULT_QUEUE)
    parser.add_argument('--recorded-at', default='2026-09-22')
    args = parser.parse_args()
    inventory = read(args.inventory)
    prior = read(args.queue) if args.queue.exists() else {}
    records = queue_records(inventory)
    count = len(records)
    if count > 20:
        raise ValueError('Mission-scope borderline queue exceeds 20 unresolved records; stop adding cases and obtain human decisions first.')
    at_capacity = count == 20
    queue = {
        'schema_version': 1,
        'artifact_type': 'mission_scope_borderline_human_review_queue',
        'recorded_at': args.recorded_at,
        'purpose': 'Rapid human editorial decisions for genuinely borderline mission-scope cases only. This queue excludes privacy, provenance, version/finality, legal-status, source-recovery, and every other human-review reason.',
        'scope_outcome': 'requires_human_scope_review',
        'inventory_status': 'requires human review',
        'review_reason': 'mission_scope_borderline',
        'unresolved_count': count,
        'capacity': {
            'maximum_unresolved_records': 20,
            'below_capacity_policy': 'Continue ordinary work while fewer than 20 unresolved scope-borderline records exist.',
            'at_capacity_policy': 'At exactly 20 unresolved records, stop adding scope-borderline cases and make this 20-record batch the next user-facing decision task before continuing reviews that could add more.',
            'early_smaller_batch_exception': 'Surface a smaller batch only when it is necessary to resolve the currently active family or no other productive ungated work remains.',
        },
        'state': 'ready_for_user_decision_batch' if at_capacity else 'open_under_threshold',
        'new_borderline_intake_allowed': not at_capacity,
        'next_user_facing_decision_task': 'Decide the 20-record mission-scope-borderline batch: Add, Exclude, or Needs more research.' if at_capacity else None,
        'decision_options': ['Add', 'Exclude', 'Needs more research'],
        'records': records,
        'resolved_records': prior.get('resolved_records', []),
        'prospective_only_note': 'No completed 2026-09-22 mission-scope-audit disposition was changed to populate this workflow. The audit identified no ambiguous scope cases.',
    }
    write(args.queue, queue)
    print(json.dumps({'queue': str(args.queue), 'unresolved_count': count, 'state': queue['state']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
