"""Derive the ordinary queue after the governed County roadway publication."""

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'project-state/discovery/pr202-ordinary-queue-reconcile-2026-09-28/queue.json'
POPULATION = ROOT / 'project-state/governance/ordinary-county-roadway-2026-09-29/population-v19.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'
OUTPUT = ROOT / 'project-state/discovery/ordinary-county-roadway-2026-09-29/queue.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def build(recorded_at):
    old = load(SOURCE)
    selected = set(load(POPULATION)['candidate_ids'])
    inventory = load(INVENTORY)
    rows = {r['id']: r for r in inventory['candidates']}
    previous = {r['id'] for r in old['newly_approved_backlog']}
    approved = {i for i, r in rows.items() if r['status'] == 'approved for addition'}
    pending = {i for i, r in rows.items() if r['status'] == 'pending review'}
    assert len(previous) == 30 and len(selected) == 6
    assert previous - approved == selected and not approved - previous
    assert {rows[i]['status'] for i in selected} == {'implemented'}
    assert len(approved) == 24
    assert pending == set(old['pending_ids']) and len(pending) == 372
    result = copy.deepcopy(old)
    result['artifact_type'] = 'ordinary_queue_post_county_roadway_publication'
    result['recorded_at'] = recorded_at
    result['source_queue_artifact'] = SOURCE.relative_to(ROOT).as_posix()
    result['inventory_generated_at'] = inventory['generated_at']
    result['county_roadway_implemented_ids_removed_from_approved'] = sorted(selected)
    result['newly_approved_backlog'] = [r for r in old['newly_approved_backlog'] if r['id'] in approved]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    recorded_at = load(OUTPUT)['recorded_at'] if args.check else datetime.now(timezone.utc).isoformat()
    result = build(recorded_at)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert OUTPUT.read_text(encoding='utf-8') == payload
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(payload, encoding='utf-8')
    print('PASS: 6 County roadway records removed from 30 approvals; 24 approvals and 372 pending remain')


if __name__ == '__main__':
    main()
