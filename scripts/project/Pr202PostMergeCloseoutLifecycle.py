"""Exact-delta guard for PR #202's post-merge closeout."""

import hashlib
import json

import TaskGovernance as G
from WorkflowStageLifecycle import ROOT, StageSnapshot, git

MERGE = 'b6f25b238e5bbdfe9a6c31fc9197a4530a6c0e03'
REVIEWED = '5d8c5cdc1bf0d43c4d5b49d26e3774d354e43137'
TASK = 'project-state/governance/pr202-postmerge-closeout-2026-09-28/'
ALLOWED = {
    'project-state/CURRENT.md',
    'project-state/checkpoint.json',
    'project-state/governance/active-task.json',
    'project-state/governance-registry.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/governance/ordinary-transport-projects-2026-09-28/implementation-v15.json',
    'project-state/governance/pr202-recent-project-taxonomy-2026-09-28/implementation-v2.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr202PostMergeCloseoutLifecycle.py',
    'scripts/project/Verify-Pr202Production.py',
}


def guard_current_delta():
    stage = StageSnapshot('pr202-postmerge-closeout')
    assert stage.stage['baseline_commit'] == MERGE
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', MERGE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) or path.startswith('backups/') for path in paths), \
        'Unexpected PR202 closeout delta'
    stage.assert_no_visible_changes(MERGE, git('rev-parse', MERGE + ':content').decode().strip())
    assert not paths.intersection({'project-state/master-inventory.json', 'project-state/r2-inventory.json'})
    if not paths.intersection({'project-state/master-inventory.json', 'project-state/r2-inventory.json'}):
        assert git('rev-parse', MERGE + ':project-state/master-inventory.json') == \
               git('rev-parse', endpoint + ':project-state/master-inventory.json')
        assert git('rev-parse', MERGE + ':project-state/r2-inventory.json') == \
               git('rev-parse', endpoint + ':project-state/r2-inventory.json')
    receipt_path = ROOT / (TASK + 'receipt.json')
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['pr']['number'] == 202 and receipt['pr']['state'] == 'MERGED'
    assert receipt['merge_commit'] == MERGE and receipt['reviewed_head'] == REVIEWED
    assert receipt['merge_tree_matches_reviewed_head'] is True
    assert receipt['manual_review_gate_closed_by_merge'] is True
    assert receipt['production_pages_verified'] == 4
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == 0 and receipt['closeout_r2_changes'] == 0
    validation_log = ROOT / (TASK + 'validation.log')
    validation_hash = hashlib.sha256(validation_log.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    assert receipt['normal_validation'] == 'passed' and receipt['validation_log_sha256'] == validation_hash
    production = json.loads((ROOT / (TASK + 'production-verification.json')).read_text(encoding='utf-8'))
    assert production['result'] == 'passed' and production['merge_commit'] == MERGE
    assert len(production['pages']) == 4
    assert all(page['article_identical_across_witnesses'] and len(page['witnesses']) == 3 for page in production['pages'])
    assert all(w['http_status'] == 200 for page in production['pages'] for w in page['witnesses'])
    ordinary = json.loads((ROOT / 'project-state/governance/ordinary-transport-projects-2026-09-28/implementation-v15.json').read_text(encoding='utf-8'))
    taxonomy = json.loads((ROOT / 'project-state/governance/pr202-recent-project-taxonomy-2026-09-28/implementation-v2.json').read_text(encoding='utf-8'))
    assert ordinary['status'] == 'complete' and taxonomy['status'] == 'complete'
    active = json.loads((ROOT / 'project-state/governance/active-task.json').read_text(encoding='utf-8'))
    assert active['state'] in ('in_progress', 'complete') and active['contract'].startswith(TASK)
    if receipt.get('normal_validation') == 'passed':
        assert active['state'] == 'complete'
    lifecycle = stage.load_json('project-state/workflow-stage-lifecycle.json')
    assert next(s for s in lifecycle['stages'] if s['id'] == 'pr202-recent-project-taxonomy')['end_commit'] == MERGE
