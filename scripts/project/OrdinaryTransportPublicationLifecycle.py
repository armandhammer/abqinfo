"""Guard the frozen approved transportation publication stage."""

import json

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git

BASELINE = '5829f4e66ea0c38006969a7dd34ff581b02efdc7'
PREFIX = 'project-state/governance/ordinary-transport-projects-2026-09-28/'


def guard_current_delta():
    stage = StageSnapshot('ordinary-transport-publication')
    assert stage.stage['baseline_commit'] == BASELINE
    population = stage.load_json(PREFIX + 'population-v15.json')
    selected = set(population['candidate_ids'])
    assert len(selected) == 21
    paths = set(git('diff', BASELINE, stage.end, '--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASELINE))
    allowed = set(population['pages']) | set(population['artifact_paths'])
    assert paths <= allowed, 'Transportation stage changed a path outside its frozen population'
    visible = {path for path in paths if path.startswith(('content/', 'layouts/', 'assets/', 'static/')) or path == 'hugo.toml'}
    assert visible == set(population['pages']), 'Transportation stage visible pages differ from the frozen set'
    assert 'project-state/r2-inventory.json' not in paths
    before = json.loads(git('show', BASELINE + ':project-state/master-inventory.json'))
    after = stage.load_json('project-state/master-inventory.json')
    old = {row['id']: row for row in before['candidates']}
    new = {row['id']: row for row in after['candidates']}
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    assert changed == selected, 'Transportation inventory delta differs from frozen records'
    assert all(new[key]['status'] == 'implemented' for key in selected)
    review = stage.load_json(PREFIX + 'review.json')
    assert {entry['id'] for entry in review['entries']} == selected
    for entry in review['entries']:
        assert stage.read_text(entry['page']).count(entry['source_url']) == 1, 'Source link missing or duplicated: ' + entry['id']
