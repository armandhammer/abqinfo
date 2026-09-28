"""Exact delta guard for PR #202's recent-project taxonomy correction."""

import json

import TaskGovernance as G
from WorkflowStageLifecycle import ROOT, git


BASELINE = '176a4c8f2347864e852b38d46807277320041f1b'
POPULATION = 'project-state/governance/pr202-recent-project-taxonomy-2026-09-28/population-v2.json'
PAGES = (
    'content/transportation/bicycling/projects/_index.md',
    'content/transportation/roadway-projects/_index.md',
)


def guard_current_delta():
    population = json.loads((ROOT / POPULATION).read_text(encoding='utf-8'))
    assert population['baseline_commit'] == BASELINE
    assert set(population['pages']) == set(PAGES)
    assert population['candidate_ids'] == []
    paths = set(G.changed_paths(BASELINE))
    allowed = set(population['pages']) | set(population['artifact_paths'])
    assert paths <= allowed, 'Taxonomy correction changed a path outside its frozen population'
    visible = {p for p in paths if p.startswith(('content/', 'layouts/', 'assets/', 'static/')) or p == 'hugo.toml'}
    assert visible == set(PAGES), 'Taxonomy correction changed unexpected visitor-visible pages'
    assert 'project-state/master-inventory.json' not in paths
    assert 'project-state/r2-inventory.json' not in paths
    old_heading = '## Current Projects (2021\u20132026)'
    new_heading = '## Recent Projects (2021\u20132026)'
    for page in PAGES:
        before = git('show', BASELINE + ':' + page).decode('utf-8-sig').replace('\r\n', '\n')
        after = (ROOT / page).read_text(encoding='utf-8-sig').replace('\r\n', '\n')
        assert before.count(old_heading) == 1
        assert before.count('grouped as current') == 1
        expected = before.replace(old_heading, new_heading).replace('grouped as current', 'grouped as recent')
        assert after == expected, 'Taxonomy correction changed more than the two intended phrases: ' + page
        assert after.count('## Past Projects (2020 and Earlier)') == 1
