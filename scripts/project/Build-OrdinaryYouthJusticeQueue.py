"""Derive the exact queue delta for the two County youth-justice additions."""
import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'project-state/discovery/ordinary-drainage-projects-2026-09-29/queue.json'
PREFIX = 'project-state/governance/ordinary-youth-justice-publication-2026-09-30/'
OUTPUT = 'project-state/discovery/ordinary-youth-justice-2026-09-30/queue.json'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def build(recorded_at):
    prior = load(SOURCE)
    selected = set(load(PREFIX + 'population.json')['candidate_ids'])
    inventory = load('project-state/master-inventory.json')
    rows = {r['id']: r for r in inventory['candidates']}
    approved = {r['id'] for r in rows.values() if r['status'] == 'approved for addition'}
    previous = {r['id'] for r in prior['newly_approved_backlog']}
    pending = {r['id'] for r in rows.values() if r['status'] == 'pending review'}
    assert len(previous) == 20 and len(selected) == 2 and len(approved) == 18
    assert previous - approved == selected and not approved - previous
    assert pending == set(prior['pending_ids']) and len(pending) == 372
    assert all(rows[rid]['status'] == 'implemented' for rid in selected)
    result = copy.deepcopy(prior)
    result.update(artifact_type='ordinary_queue_post_youth_justice_publication',
                  recorded_at=recorded_at, source_queue_artifact=SOURCE,
                  inventory_generated_at=inventory['generated_at'],
                  youth_justice_implemented_ids_removed_from_approved=sorted(selected))
    result['newly_approved_backlog'] = [r for r in prior['newly_approved_backlog'] if r['id'] in approved]
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    date = load(OUTPUT)['recorded_at'] if args.check else datetime.now(timezone.utc).isoformat()
    output = json.dumps(build(date), ensure_ascii=False, indent=2) + '\n'
    path = ROOT / OUTPUT
    if args.check:
        assert path.read_text(encoding='utf-8') == output
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding='utf-8', newline='\n')
    print('PASS: exact 20-to-18 approved delta; 372 pending and all prior queue evidence preserved.')
