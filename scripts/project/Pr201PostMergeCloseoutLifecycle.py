"""Guard PR #201's background-only production closeout."""

import hashlib
import json

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

MERGE = '25a2fc516c888959dbb97d83829b06a9d8cd62ac'
REVIEWED = '7a3d1fb9708d8a2533793d3c45c3eedd97a87e03'
TASK = 'project-state/governance/pr201-postmerge-closeout-2026-09-28/'
ALLOWED = {
    'project-state/CURRENT.md',
    'project-state/governance-registry.json',
    'project-state/governance/active-task.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/governance/capital-title-case-2026-09-28/implementation.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr201PostMergeCloseoutLifecycle.py',
    'scripts/project/Verify-Pr201Production.py',
}


def guard_current_delta():
    stage = StageSnapshot('pr201-postmerge-closeout')
    assert stage.stage['baseline_commit'] == MERGE
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', MERGE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) for path in paths), 'Unexpected PR201 closeout delta'
    stage.assert_no_visible_changes(MERGE, git('rev-parse', MERGE + ':content').decode().strip())
    assert not paths.intersection({'project-state/master-inventory.json', 'project-state/r2-inventory.json'})
    old_plan = json.loads((ROOT / 'project-state/governance/capital-title-case-2026-09-28/implementation.json').read_text(encoding='utf-8'))
    assert old_plan['status'] == 'complete'

    receipt_path = ROOT / (TASK + 'receipt.json')
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['pr']['number'] == 201 and receipt['pr']['state'] == 'MERGED'
    assert receipt['pr']['mergeCommit']['oid'] == MERGE and receipt['pr']['headRefOid'] == REVIEWED
    assert receipt['merge_tree_matches_reviewed_head'] is True
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == 0 and receipt['closeout_r2_changes'] == 0
    assert receipt['manual_review_gate_closed_by_merge'] is True
    production_path = ROOT / (TASK + 'production-verification.json')
    production = json.loads(production_path.read_text(encoding='utf-8'))
    assert production['result'] == 'passed' and production['merge_commit'] == MERGE
    assert production['page']['article_identical_across_witnesses'] is True
    assert len(production['page']['witnesses']) == 3
    assert all(w['http_status'] == 200 for w in production['page']['witnesses'])
    assert production['archive']['exact_public_bytes'] is True
    assert hashlib.sha256(production_path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == receipt['production_verification_sha256']
