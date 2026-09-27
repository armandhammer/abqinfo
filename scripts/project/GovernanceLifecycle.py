"""Exact background-only delta; preserve all inventory, content, storage and prior evidence."""
from WorkflowStageLifecycle import StageSnapshot, git, canonical_bytes

ALLOWED = {
    'AGENTS.md','project-state/CURRENT.md','project-state/README.md',
    'project-state/campaign-workflow.md','project-state/workflow-stage-lifecycle.json',
    'project-state/PARALLEL-VERIFICATION.md','project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md',
    'project-state/governance-registry.json','project-state/governance-workflow.md',
    'scripts/project/TaskGovernance.py','scripts/project/Resolve-TaskGovernance.py',
    'scripts/project/Test-TaskGovernance.py','scripts/project/GovernanceLifecycle.py',
    'scripts/project/Invoke-ProjectValidation.ps1','scripts/project/Update-Candidate.ps1',
    'scripts/project/Update-CandidatesBatch.py','scripts/project/BackgroundCampaign.py',
    'scripts/upload-r2-document.ps1','scripts/project/Remove-R2Object.ps1',
}


def guard_current_delta():
    from TaskGovernance import load
    guarded_tools=set(load('project-state/governance/entrypoints.json')['tools'])
    stage=StageSnapshot('durable-governance')
    baseline=stage.stage['baseline_commit']
    endpoint=stage.end or 'HEAD'
    changed=set(git('diff',baseline,endpoint,'--name-only').decode().splitlines())
    if not stage.end:
        changed.update(git('diff',endpoint,'--name-only').decode().splitlines())
        changed.update(git('ls-files','--others','--exclude-standard').decode().splitlines())
    assert all(p in ALLOWED or p in guarded_tools or p in ('scripts/project/GovernedEntrypoint.py','scripts/project/Assert-TaskGovernance.ps1') or p.startswith(('project-state/governance/','backups/')) for p in changed), 'Unauthorized governance delta'
    for path in ('content','layouts','assets','static','hugo.toml','project-state/master-inventory.json',
                 'project-state/r2-inventory.json','project-state/checkpoint.json',
                 'project-state/discovery','project-state/campaigns','project-state/campaign-runtime'):
        assert not git('diff',baseline,endpoint,'--name-only','--',path).strip(), path
        if not stage.end:
            assert not git('diff',endpoint,'--name-only','--',path).strip(), path
            assert not git('ls-files','--others','--exclude-standard','--',path).strip(), path
    # PR198's unmerged implementation branch is evidence, not this stage's baseline.
    assert baseline=='940e3032d96f868eed8cff7c3deeaf1c556f50a2'
