"""Derive the post-PR202 ordinary queue without changing prior dispositions."""
import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'project-state/discovery/owner-decisions-2026-09-26/next-ordinary-queue.json'
OUTPUT = ROOT / 'project-state/discovery/pr202-ordinary-queue-reconcile-2026-09-28/queue.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'
PR202 = ROOT / 'project-state/governance/pr202-postmerge-closeout-2026-09-28/population-v4.json'
SCOPE = ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def build(recorded_at):
    old = load(SOURCE)
    inventory = load(INVENTORY)
    rows = {r['id']: r for r in inventory['candidates']}
    implemented = set(load(PR202)['candidate_ids'])
    approved = {i for i, r in rows.items() if r['status'] == 'approved for addition'}
    pending = {i for i, r in rows.items() if r['status'] == 'pending review'}
    prior_approved = {r['id'] for r in old['newly_approved_backlog']}
    assert prior_approved - approved == implemented and not approved - prior_approved
    assert len(implemented) == 21 and {rows[i]['status'] for i in implemented} == {'implemented'}
    assert pending == set(old['pending_ids']) and len(pending) == 372
    gated = set(old['gated_pending_ids'])
    blocked = set(old['source_or_structural_blocked_pending_ids'])
    ungated = set(old['ungated_pending_ids'])
    assert not (gated & blocked or gated & ungated or blocked & ungated)
    assert gated | blocked | ungated == pending and (len(gated), len(blocked), len(ungated)) == (321, 42, 9)
    assert {r['id'] for r in old['unresolved_ungated_prerequisites']} == ungated
    assert all(set(group['candidate_ids']) <= pending for group in old['background_family_groups'])
    assert {rows[i]['status'] for i in old['existing_ia_blocked_approved_ids']} == {'placement assigned'}
    result = copy.deepcopy(old)
    result['artifact_type'] = 'ordinary_queue_post_pr202_inventory_reconciliation'
    result['recorded_at'] = recorded_at
    result['source_queue_artifact'] = SOURCE.relative_to(ROOT).as_posix()
    result['inventory_generated_at'] = inventory['generated_at']
    result['pr202_implemented_ids_removed_from_approved'] = sorted(implemented)
    result['newly_approved_backlog'] = [r for r in old['newly_approved_backlog'] if r['id'] in approved]
    result['mission_borderline_queue_size'] = load(SCOPE)['unresolved_count']
    assert len(result['newly_approved_backlog']) == 30
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    recorded_at = load(OUTPUT)['recorded_at'] if args.check else datetime.now(timezone.utc).isoformat()
    result = build(recorded_at)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert OUTPUT.read_text(encoding='utf-8') == payload, 'Derived ordinary queue changed'
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(payload, encoding='utf-8')
    print('PASS: 21 PR202 records removed from 51 approvals; 30 approvals and 372 pending remain; all gates and prerequisites preserved')


if __name__ == '__main__':
    main()
