"""Exact preparation boundary while the owner resolves the 31/32 population mismatch."""
from WorkflowStageLifecycle import ROOT, StageSnapshot, git, canonical_bytes, digest

PREFIX = 'project-state/discovery/go-capital-quality-remediation-2026-09-27/'
QUEUE = 'project-state/discovery/publication-quality-remediation-2026-09-26.json'
ALLOWED = {
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/GoCapitalQualityRemediationLifecycle.py',
    'scripts/project/Test-GoCapitalQualityRemediation.py',
    'scripts/project/Invoke-ProjectValidation.ps1',
}

def guard_current_delta():
    stage = StageSnapshot('go-capital-quality-remediation')
    baseline = stage.stage['baseline_commit']
    data = stage.load_json(PREFIX + 'preparation.json')
    assert baseline == data['baseline_commit'] == '940e3032d96f868eed8cff7c3deeaf1c556f50a2'
    assert data['state'] == 'awaiting_exact_population_clarification'
    endpoint = stage.end or 'HEAD'
    changed = set(git('diff', baseline, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        changed.update(git('diff', endpoint, '--name-only').decode().splitlines())
        changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(p in ALLOWED or p.startswith(PREFIX) or p.startswith('backups/') for p in changed), 'Unrelated preparation delta'
    for path in [QUEUE, QUEUE.removesuffix('.json') + '.md', 'project-state/master-inventory.json', 'project-state/r2-inventory.json', 'project-state/CURRENT.md', 'project-state/checkpoint.json']:
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline + ':' + path)), path
    for suffix in ('json', 'md'):
        assert canonical_bytes(stage.read_bytes(PREFIX+'baseline-remediation.'+suffix)) == canonical_bytes(git('show',baseline+':'+QUEUE.removesuffix('.json')+'.'+suffix))
    assert not git('diff', baseline, *([stage.end] if stage.end else []), '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').strip()
    q = stage.load_json(QUEUE)
    unresolved = [r for r in q['september_13_reconciliation'] if r['disposition'] == 'unresolved visible quality finding']
    negatives = [r for r in unresolved if r['prior_status'] == 'does not meet standalone standard']
    capital = [r for r in negatives if 'Bond' in r['title'] or 'Capital Facilities' in r['title']]
    assert len(q['failures']) == 1608 and len(unresolved) == 42
    assert len(capital) == 32 and len(negatives) == 35
    assert {r['id'] for r in capital} == set(data['capital_candidate_ids'])
    assert len(unresolved) - len(negatives) == 7
    rows = {r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert {i:digest(rows[i]) for i in data['capital_candidate_ids']} == data['original_row_digests']
    saved = stage.load_json(PREFIX+'candidate-reconciliation.json')
    assert len(saved) == 32 and {r['id'] for r in saved} == set(data['capital_candidate_ids'])
    originals = {r['candidate_id']:r for r in stage.load_json('project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json')['documents']}
    queue_rows = {r['id']:r for r in capital}
    for item in saved:
        rid = item['id']
        assert item['original_inventory_record'] == rows[rid]
        assert item['original_queue_finding'] == queue_rows[rid]
        assert item['original_september_13_finding'] == originals[rid]
    import json
    old_registry = json.loads(git('show',baseline+':project-state/workflow-stage-lifecycle.json').decode('utf-8-sig'))
    registry = stage.load_json('project-state/workflow-stage-lifecycle.json')
    assert registry['stages'][:-2] == old_registry['stages'][:-1]
    assert registry['stages'][-2] == dict(old_registry['stages'][-1],end_commit=baseline)
    assert {k:v for k,v in registry.items() if k!='stages'} == {k:v for k,v in old_registry.items() if k!='stages'}
    return data
