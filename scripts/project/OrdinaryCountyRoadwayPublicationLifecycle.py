"""Guard the frozen six-record County roadway publication stage."""

import json

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git

BASELINE = '7b28ef1120f7faf7480bdda90a8f0df6a3e31f87'
PREFIX = 'project-state/governance/ordinary-county-roadway-2026-09-29/'
PAGE = 'content/transportation/roadway-projects/_index.md'


def guard_current_delta():
    stage = StageSnapshot('ordinary-county-roadway-publication')
    assert stage.stage['baseline_commit'] == BASELINE
    population = stage.load_json(PREFIX + 'population-v17.json')
    selected = set(population['candidate_ids'])
    assert len(selected) == 6 and population['pages'] == [PAGE]
    paths = (set(git('diff', BASELINE, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(BASELINE)))
    allowed = set(population['pages']) | set(population['artifact_paths'])
    assert paths <= allowed, 'County roadway stage changed a path outside its frozen population'
    visible = {path for path in paths if path.startswith(('content/', 'layouts/', 'assets/', 'static/')) or path == 'hugo.toml'}
    assert visible == {PAGE}, 'County roadway stage visible pages differ from the frozen set'
    assert 'project-state/r2-inventory.json' not in paths
    before = json.loads(git('show', BASELINE + ':project-state/master-inventory.json'))
    after = stage.load_json('project-state/master-inventory.json')
    old = {row['id']: row for row in before['candidates']}
    new = {row['id']: row for row in after['candidates']}
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    assert changed == selected, 'County roadway inventory delta differs from frozen records'
    assert all(new[key]['status'] == 'implemented' for key in selected)
    review = stage.load_json(PREFIX + 'review-v3.json')
    assert {entry['id'] for entry in review['entries']} == selected
    page = stage.read_text(PAGE)
    for entry in review['entries']:
        assert page.count(entry['final_url']) == 1, 'Source link missing or duplicated: ' + entry['id']
