"""Guard the background-only import of main's PR #198 continuity update."""

import json

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

BASELINE = '700515a90de68294936e21925e7ac5b8f0d65d3d'
MAIN = 'dc649b4f68510381c38902e615cae8246461cb94'
CONTENT_TREE = '833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e'
TASK = 'project-state/governance/pr198-continuity-pr-merge-2026-09-27/'
MAIN_TASK = 'project-state/governance/pr198-continuity-2026-09-27/'
ALLOWED = {
    'project-state/CURRENT.md',
    'project-state/governance-registry.json',
    'project-state/governance/active-task.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr198ContinuityLifecycle.py',
    'scripts/project/Test-Pr198Continuity.py',
    'scripts/project/Pr198ContinuityPrMergeLifecycle.py',
    'scripts/project/Test-Pr198ContinuityPrMerge.py',
}


def guard_current_delta():
    stage = StageSnapshot('pr198-continuity-pr-merge')
    assert stage.stage['baseline_commit'] == BASELINE
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', BASELINE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) or path.startswith(MAIN_TASK)
               for path in paths), 'Unapproved PR198 continuity import delta'
    stage.assert_no_visible_changes(BASELINE, CONTENT_TREE)
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json'):
        assert path not in paths, 'Inventory or R2 changed: ' + path

    current = stage.read_text('project-state/CURRENT.md')
    assert CONTENT_TREE in current and 'b8225e04b2e97e77055e8519b8e9287ca12ed2ad69d23d5df7d6f6f7ee4f7707' in current
    assert '073edabd10d9a0996eb897e2ed957943aed4de18' not in current
    assert 'manual PR review' in current and 'open, unmerged, and mergeable' in current
    main_receipt = json.loads((ROOT / (MAIN_TASK + 'receipt.json')).read_text(encoding='utf-8'))
    assert main_receipt['reviewed_content_tree'] == CONTENT_TREE
    assert main_receipt['visitor_visible_changes'] == main_receipt['inventory_changes'] == main_receipt['r2_changes'] == 0

    receipt = ROOT / (TASK + 'receipt.json')
    if receipt.is_file():
        evidence = json.loads(receipt.read_text(encoding='utf-8'))
        assert evidence['main_continuity_commit'] == MAIN
        assert evidence['reviewed_content_tree'] == CONTENT_TREE
        assert evidence['visitor_visible_changes'] == evidence['inventory_changes'] == evidence['r2_changes'] == 0
        assert evidence['manual_review_gate'] is True
