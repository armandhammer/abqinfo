#!/usr/bin/env python3
"""Validate the Form Based Zones final-parts inventory-only decision."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
decision = json.loads((root / 'project-state/discovery/form-based-zones-final-parts-family-decision-2026-09-20.json').read_text(encoding='utf-8'))
queue = json.loads((root / 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json').read_text(encoding='utf-8'))
inventory = json.loads((root / 'project-state/master-inventory.json').read_text(encoding='utf-8'))
records = {row['id']: row for row in inventory['candidates']}

assert decision['family']['scope_candidate_ids'] == ['src-77df51d4334f3749', 'src-bdb71a8eaf8a29fa']
assert all(records[key]['status'] == 'requires human review' for key in decision['family']['scope_candidate_ids'])
assert all(records[key]['date'] == '2009-04-02' for key in decision['family']['scope_candidate_ids'])
assert decision['relationship_findings']['truly_final_components'] is True
assert decision['relationship_findings']['independently_publishable'] is False
assert decision['safeguards_observed']['r2_mutation'] is False
assert queue['counts']['filtered_pending_review'] == 1
assert queue['next_actionable_cluster']['candidate_ids'] == ['src-e0624ecba79f3f17']
print('PASS: Form Based Zones final-parts decision and UNM-only queue handoff are consistent.')
