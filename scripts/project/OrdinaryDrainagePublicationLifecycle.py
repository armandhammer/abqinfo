"""Guard the exact four-record County drainage publication stage."""

import json

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git

BASE = '65091aab385e43703e9870d97ebad89375589f1f'
PREFIX = 'project-state/governance/ordinary-drainage-projects-2026-09-29/'
PAGE = 'content/public-works/stormwater-drainage.md'


def guard_current_delta():
    stage = StageSnapshot('ordinary-drainage-projects-publication')
    assert stage.stage['baseline_commit'] == BASE
    population = stage.load_json(PREFIX + 'population.json')
    selected = set(population['candidate_ids'])
    assert len(selected) == 4 and PAGE in population['pages']
    paths = (set(git('diff', BASE, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(BASE)))
    assert paths <= set(population['artifact_paths']), 'Drainage stage changed a path outside its frozen population'
    visible = {path for path in paths if path.startswith(('content/', 'layouts/', 'assets/', 'static/')) or path == 'hugo.toml'}
    assert visible == {PAGE}, 'Drainage stage visible pages differ from the reviewed page'
    assert 'project-state/r2-inventory.json' not in paths
    before = json.loads(git('show', BASE + ':project-state/master-inventory.json'))
    after = stage.load_json('project-state/master-inventory.json')
    old = {row['id']: row for row in before['candidates']}
    new = {row['id']: row for row in after['candidates']}
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    assert changed == selected, 'Drainage inventory delta differs from frozen records'
    assert all(new[key]['status'] == 'implemented' for key in selected)
    assert all(new[key].get('r2_url') is None for key in selected)
    review = stage.load_json(PREFIX + 'review.json')
    assert {entry['id'] for entry in review['entries']} == selected
    page = stage.read_text(PAGE)
    for entry in review['entries']:
        assert page.count(entry['final_url']) == 1, 'Official source link missing or duplicated: ' + entry['id']
    queue = stage.load_json('project-state/discovery/ordinary-drainage-projects-2026-09-29/queue.json')
    assert len(queue['newly_approved_backlog']) == 20
    assert set(queue['drainage_implemented_ids_removed_from_approved']) == selected
    assert queue['pending_review_count'] == 372
