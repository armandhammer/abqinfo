"""Guard the background-only PR #198 continuity pointer."""

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

BASELINE = '90c78020d7d7cc2fc3eaee8b1baa7689966ed7b9'
TASK = 'project-state/governance/pr198-continuity-2026-09-27/'
REVIEW_TREE = '833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e'
REVIEW_CONTRACT = 'b8225e04b2e97e77055e8519b8e9287ca12ed2ad69d23d5df7d6f6f7ee4f7707'
OLD_HEAD = '073edabd10d9a0996eb897e2ed957943aed4de18'
ALLOWED = {
    'project-state/CURRENT.md',
    'project-state/governance/active-task.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr198ContinuityLifecycle.py',
    'scripts/project/Test-Pr198Continuity.py',
    'scripts/project/Invoke-ProjectValidation.ps1',
}


def guard_current_delta():
    stage = StageSnapshot('pr198-continuity')
    assert stage.stage['baseline_commit'] == BASELINE
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', BASELINE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) for path in paths), 'Unapproved PR198 continuity delta'
    stage.assert_no_visible_changes(BASELINE, git('rev-parse', BASELINE + ':content').decode().strip())
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json'):
        assert path not in paths, 'Inventory or R2 changed: ' + path

    current = stage.read_text('project-state/CURRENT.md')
    assert REVIEW_TREE in current and REVIEW_CONTRACT in current, 'Stable PR review identifiers missing'
    assert OLD_HEAD not in current, 'CURRENT pins obsolete PR branch head'
    assert 'open, unmerged, and mergeable' in current and 'manual PR review' in current
    assert 'none are integrated into `main`' in current
    assert 'https://github.com/armandhammer/abqinfo/pull/198' in current

    receipt = ROOT / (TASK + 'receipt.json')
    if receipt.is_file():
        import json
        evidence = json.loads(receipt.read_text(encoding='utf-8'))
        assert evidence['reviewed_content_tree'] == REVIEW_TREE
        assert evidence['review_contract_sha256'] == REVIEW_CONTRACT
        assert evidence['visitor_visible_changes'] == 0
        assert evidence['inventory_changes'] == 0 and evidence['r2_changes'] == 0
        assert evidence['manual_review_gate'] is True
