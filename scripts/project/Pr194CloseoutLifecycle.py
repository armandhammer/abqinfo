"""Background closeout guard: reviewed publication, dispositions and debt stay fixed."""
from WorkflowStageLifecycle import ROOT, StageSnapshot, git, canonical_bytes

PREFIX = 'project-state/discovery/pr194-production-closeout-2026-09-26/'
ALLOWED = {
    'project-state/CURRENT.md', 'project-state/checkpoint.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Pr194CloseoutLifecycle.py',
    'scripts/project/Test-Pr194Closeout.py',
    'scripts/project/Test-QualityCorrectionHugoImplementation.py',
    'scripts/project/Invoke-ProjectValidation.ps1',
    'scripts/project/QualityCorrectionLifecycle.py',
}

def guard_current_delta():
    stage = StageSnapshot('pr194-background-closeout')
    baseline = stage.stage['baseline_commit']
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', baseline, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
    assert all(p in ALLOWED or p.startswith(PREFIX) for p in paths), 'Unauthorized closeout delta'
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json',
                 'project-state/discovery/publication-quality-remediation-2026-09-26.json',
                 'project-state/discovery/publication-quality-remediation-2026-09-26.md'):
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline+':'+path))
    assert not git('diff', baseline, endpoint, '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').strip()
    if not stage.end:
        assert not git('diff', endpoint, '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').strip()
        assert not git('ls-files', '--others', '--exclude-standard', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').strip()
    receipt = stage.load_json(PREFIX+'merge-production-receipt.json')
    assert receipt['merge_commit'] == baseline and receipt['reviewed_tree_matches_merge']
    assert receipt['remediation_records'] == 1638 and receipt['unresolved_september_13_findings'] == 67
    assert receipt['inventory_changes'] is False and receipt['r2_mutation'] is False
    production = stage.load_json(PREFIX+'production-verification.json')
    assert production['result'] == 'passed' and len(production['responses']) == 7
    assert all(r['http_status'] == 200 and r['url'].startswith('https://abqinfo.com/') for r in production['responses'])
    for path, expected in receipt['historical_evidence_blobs'].items():
        assert git('rev-parse', baseline+':'+path).decode().strip() == expected
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline+':'+path))
