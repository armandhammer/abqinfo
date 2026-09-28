"""Guard PR #198's background-only production closeout."""

import hashlib
import json

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

MERGE = '2cc6a349193004b41e42370b2554cd263bde1247'
REVIEWED = 'a4fb168cd0d758e1b702b00ab63cc83d1d93febe'
CONTENT_TREE = '833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e'
TASK = 'project-state/governance/pr198-postmerge-closeout-2026-09-27/'
ALLOWED = {
    'project-state/CURRENT.md',
    'project-state/governance-registry.json',
    'project-state/governance/active-task.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr198PostMergeCloseoutLifecycle.py',
    'scripts/project/Verify-Pr198Production.py',
}


def guard_current_delta():
    stage = StageSnapshot('pr198-postmerge-closeout')
    assert stage.stage['baseline_commit'] == MERGE
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    assert git('rev-parse', MERGE + ':content').decode().strip() == CONTENT_TREE
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', MERGE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) for path in paths), 'Unapproved PR198 closeout delta'
    stage.assert_no_visible_changes(MERGE, CONTENT_TREE)
    assert not paths.intersection({'project-state/master-inventory.json', 'project-state/r2-inventory.json'})

    receipt_path = ROOT / (TASK + 'receipt.json')
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['pr']['state'] == 'MERGED' and receipt['pr']['number'] == 198
    assert receipt['pr']['mergeCommit']['oid'] == MERGE and receipt['pr']['headRefOid'] == REVIEWED
    assert receipt['merge_tree_matches_reviewed_head'] is True
    assert receipt['reviewed_content_tree'] == CONTENT_TREE
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == 0 and receipt['closeout_r2_changes'] == 0
    assert receipt['manual_review_gate_closed_by_merge'] is True

    production = stage.load_json(TASK + 'production-verification.json')
    assert production['result'] == 'passed' and production['merge_commit'] == MERGE
    assert len(production['pages']) == 6 and len(production['archives']) == 4
    for page in production['pages']:
        assert page['article_identical_across_witnesses'] is True
        assert len(page['witnesses']) == 3
        assert len({w['article_sha256'] for w in page['witnesses']}) == 1
        assert all(w['http_status'] == 200 for w in page['witnesses'])
        assert page['witnesses'][0]['url'].startswith('https://abqinfo.com/')
    assert all(item['http_status'] == 200 and item['exact_public_bytes'] for item in production['archives'])

    deployment = stage.load_json(TASK + 'merge-deployment.json')
    check, = deployment['check_runs']
    assert check['head_sha'] == MERGE and check['conclusion'] == 'success'
    assert hashlib.sha256((ROOT / (TASK + 'production-verification.json')).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == receipt['production_verification_sha256']
