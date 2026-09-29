"""Guard the post-PR202 queue rebuild against inventory or publication changes."""
import json
import runpy

from WorkflowStageLifecycle import ROOT, StageSnapshot, canonical_bytes, git

BASE = 'project-state/discovery/owner-decisions-2026-09-26/next-ordinary-queue.json'
NEW = 'project-state/discovery/pr202-ordinary-queue-reconcile-2026-09-28/queue.json'
BUILDER = runpy.run_path(str(ROOT / 'scripts/project/Build-Pr202OrdinaryQueue.py'))


def validate_queue(old, current, rows, pr202_ids):
    approved = {i for i, r in rows.items() if r['status'] == 'approved for addition'}
    pending = {i for i, r in rows.items() if r['status'] == 'pending review'}
    before_approved = {r['id'] for r in old['newly_approved_backlog']}
    assert before_approved - approved == pr202_ids and not approved - before_approved
    assert len(pr202_ids) == 21 and {rows[i]['status'] for i in pr202_ids} == {'implemented'}
    assert set(current['pr202_implemented_ids_removed_from_approved']) == pr202_ids
    assert {r['id'] for r in current['newly_approved_backlog']} == approved and len(approved) == 30
    assert set(current['pending_ids']) == pending and current['pending_review_count'] == len(pending) == 372
    gated = set(current['gated_pending_ids'])
    blocked = set(current['source_or_structural_blocked_pending_ids'])
    ungated = set(current['ungated_pending_ids'])
    assert gated | blocked | ungated == pending
    assert not (gated & blocked or gated & ungated or blocked & ungated)
    assert (len(gated), len(blocked), len(ungated)) == (321, 42, 9)
    assert {r['id'] for r in current['unresolved_ungated_prerequisites']} == ungated
    assert not current['actionable_ungated_pending_ids'] and current['genuinely_actionable_ungated_pending_count'] == 0
    assert current['mission_borderline_queue_size'] == 0
    allowed = {'artifact_type', 'recorded_at', 'source_queue_artifact', 'inventory_generated_at',
               'pr202_implemented_ids_removed_from_approved', 'newly_approved_backlog',
               'mission_borderline_queue_size'}
    assert {k: v for k, v in current.items() if k not in allowed} == \
           {k: v for k, v in old.items() if k not in allowed}
    assert current['newly_approved_backlog'] == [r for r in old['newly_approved_backlog'] if r['id'] in approved]
    assert current['existing_ia_blocked_approved_ids'] == old['existing_ia_blocked_approved_ids']


def guard_current_delta():
    stage = StageSnapshot('pr202-ordinary-queue-reconcile')
    baseline = stage.stage['baseline_commit']
    assert baseline == 'c901990afb47902755f6e293f2ea801fbaebc041'
    stage.assert_no_visible_changes(baseline, git('rev-parse', baseline + ':content').decode().strip())
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json', BASE,
                 'project-state/discovery/codex-human-review-followup-queue.json',
                 'project-state/discovery/mission-scope-borderline-human-review-queue.json'):
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline + ':' + path))
    old = json.loads(git('show', baseline + ':' + BASE).decode('utf-8-sig'))
    current = stage.load_json(NEW)
    inventory = stage.load_json('project-state/master-inventory.json')
    rows = {r['id']: r for r in inventory['candidates']}
    ids = set(json.loads(git('show', baseline + ':project-state/governance/pr202-postmerge-closeout-2026-09-28/population-v4.json').decode())['candidate_ids'])
    validate_queue(old, current, rows, ids)
    assert current == BUILDER['build'](current['recorded_at'])
    pointer = stage.load_json('project-state/ordinary-queue-current.json')
    assert pointer == {'schema_version': 1, 'artifact': NEW, 'task': 'pr202-ordinary-queue-reconcile-2026-09-28'}
    return current
