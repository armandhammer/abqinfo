#!/usr/bin/env python3
"""Validate the isolated, bounded mission-scope-borderline review queue."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
queue = json.loads((ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json').read_text(encoding='utf-8'))
REQUIRED = {'assessed_at', 'title', 'publisher', 'date', 'geographic_institutional_scope', 'specific_albuquerque_connection', 'potential_abqinfo_public_information_value', 'reason_does_not_confidently_pass', 'reason_does_not_clearly_fail', 'proposed_page_or_section_if_admitted', 'recommended_default_disposition', 'final_scope_decision', 'substantive_rationale'}

assert queue['artifact_type'] == 'mission_scope_borderline_human_review_queue'
assert queue['scope_outcome'] == 'requires_human_scope_review'
assert queue['inventory_status'] == 'requires human review'
assert queue['review_reason'] == 'mission_scope_borderline'
assert queue['decision_options'] == ['Add', 'Exclude', 'Needs more research']
assert queue['capacity']['maximum_unresolved_records'] == 20
assert queue['unresolved_count'] == len(queue['records']) <= 20

expected = []
for candidate in inventory['candidates']:
    if candidate['status'] == 'requires human review' and candidate.get('review_reason') == 'mission_scope_borderline':
        assessment = candidate['scope_assessment']
        assert set(assessment) == REQUIRED, candidate['id']
        assert assessment['final_scope_decision'] == 'requires_human_scope_review', candidate['id']
        expected.append(candidate['id'])
assert [record['id'] for record in queue['records']] == sorted(expected)
if len(expected) < 20:
    assert queue['state'] == 'open_under_threshold' and queue['new_borderline_intake_allowed'] is True and queue['next_user_facing_decision_task'] is None
else:
    assert queue['state'] == 'ready_for_user_decision_batch' and queue['new_borderline_intake_allowed'] is False and queue['next_user_facing_decision_task']
print(f"PASS: mission-scope-borderline queue is isolated from other human-review reasons and contains {len(expected)} unresolved record(s) within the 20-record cap.")
