"""Keep the reviewed PR198 content fixed while integrating main's snapshot."""

import json
from pathlib import Path

import TaskGovernance as G
from WorkflowStageLifecycle import ROOT, StageSnapshot, git

PR_HEAD = '073edabd10d9a0996eb897e2ed957943aed4de18'
MAIN_SNAPSHOT = '90c78020d7d7cc2fc3eaee8b1baa7689966ed7b9'
CONTENT_TREE = '833e473021f9fa58d6c361e6ea7a5e3f2b47fb1e'
TASK = 'project-state/governance/pr198-main-reconcile-2026-09-27/'


def guard_current_delta():
    stage = StageSnapshot('pr198-main-reconciliation')
    assert stage.stage['baseline_commit'] == PR_HEAD
    stage.assert_no_visible_changes(PR_HEAD, CONTENT_TREE)
    endpoint = stage.end or 'HEAD'
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json'):
        assert not git('diff', PR_HEAD, endpoint, '--name-only', '--', path).strip(), path
        if not stage.end:
            assert not git('diff', endpoint, '--name-only', '--', path).strip(), path
    assert G.file_hash('project-state/governance/pr198-approved-2026-09-27/owner-approval.json') == '802e1437e2f6aab185c48b8db1dacb0c0abec18a57c1410d6a7072d4e03811cf'
    assert G.load('project-state/governance/pr198-background-snapshot-2026-09-27/receipt.json')['baseline_main_and_planning'] == 'de48a74d8522806a0d68ce247eb1d5d6a309c0ca'
    assert json.loads(git('show', MAIN_SNAPSHOT + ':project-state/r2-inventory.json')) == G.load('project-state/r2-inventory.json')
    receipt = ROOT / (TASK + 'receipt.json')
    if receipt.is_file():
        evidence = G.load(TASK + 'receipt.json')
        assert evidence['reviewed_content_tree'] == CONTENT_TREE
        assert evidence['main_snapshot_commit'] == MAIN_SNAPSHOT
        assert evidence['r2_mutations'] == 0 and evidence['manual_review_gate'] is True
