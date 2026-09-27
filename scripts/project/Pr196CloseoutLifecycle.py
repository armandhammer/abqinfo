"""Preserve the immutable reviewed PR #196 tree during background closeout."""
from WorkflowStageLifecycle import StageSnapshot, git, canonical_bytes

PREFIX = 'project-state/discovery/pr196-production-closeout-2026-09-27/'
ALLOWED = {'project-state/CURRENT.md', 'project-state/checkpoint.json',
           'project-state/workflow-stage-lifecycle.json',
           'scripts/project/Pr196CloseoutLifecycle.py', 'scripts/project/Test-Pr196Closeout.py',
           'scripts/project/Invoke-ProjectValidation.ps1'}

def guard_current_delta():
    stage = StageSnapshot('pr196-background-closeout')
    baseline = stage.stage['baseline_commit']
    endpoint = stage.end or 'HEAD'
    changed = set(git('diff', baseline, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        changed.update(git('diff', endpoint, '--name-only').decode().splitlines())
        changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(p in ALLOWED or p.startswith(PREFIX) or p.startswith('backups/') for p in changed), 'Unauthorized closeout delta'
    receipt = stage.load_json(PREFIX+'merge-production-receipt.json')
    assert baseline == receipt['merge_commit']
    assert git('rev-parse', baseline+'^{tree}') == git('rev-parse', receipt['reviewed_head']+'^{tree}')
    assert receipt['remediation_records'] == 1608 and receipt['unresolved_september_13_findings'] == 42
    assert not receipt['inventory_changes'] and not receipt['r2_mutation']
    for path in receipt['preserved_blobs']:
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline+':'+path)), path
    for path in ('content', 'layouts', 'assets', 'static', 'hugo.toml'):
        assert not git('diff', baseline, endpoint, '--name-only', '--', path).strip()
        if not stage.end:
            assert not git('diff', endpoint, '--name-only', '--', path).strip()
    production = stage.load_json(PREFIX+'production-verification.json')
    assert production['result'] == 'passed' and len(production['responses']) == 3
    assert all(r['http_status'] == 200 and r['url'].startswith('https://abqinfo.com/') for r in production['responses'])
    assert all(r['exact_main_matches_reviewed_preview_and_merge_deployment'] for r in production['responses'])
    assert all(len(r['presentation_witnesses']) == 3 and len({w['main_sha256'] for w in r['presentation_witnesses']}) == 1 for r in production['responses'])
    registry = stage.load_json('project-state/workflow-stage-lifecycle.json')
    assert next(s for s in registry['stages'] if s['id']=='quality-remediation-first')['end_commit']==baseline
    assert receipt['deployment']['check_runs'][0]['conclusion']=='success'
    assert receipt['deployment']['check_runs'][0]['head_sha']==baseline
