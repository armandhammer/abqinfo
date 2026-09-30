"""Guard the PR #206 evidence and inventory-note correction."""

import copy
import json

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

BASE = 'f51f6664d21e71c325c658ac0304ca82c30d5239'
PREFIX = 'project-state/governance/pr206-review-correction-2026-09-29/'
IDS = {
    'src-e41d6b432e52a7e1',
    'src-5dedef596ea61914',
    'src-b674369d94936b08',
    'src-ea28455d489f1c2c',
}


def guard_current_delta():
    stage = StageSnapshot('pr206-review-correction')
    assert stage.stage['baseline_commit'] == BASE
    population = stage.load_json(PREFIX + 'population.json')
    assert set(population['candidate_ids']) == IDS
    paths = (set(git('diff', BASE, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(BASE)))
    assert paths <= set(population['artifact_paths']), 'PR #206 correction changed an unfrozen path'
    content_tree = git('rev-parse', BASE + ':content').decode().strip()
    stage.assert_no_visible_changes(BASE, content_tree)
    assert canonical_bytes(stage.read_bytes('project-state/r2-inventory.json')) == canonical_bytes(
        git('show', BASE + ':project-state/r2-inventory.json'))

    before = json.loads(git('show', BASE + ':project-state/master-inventory.json'))
    after = stage.load_json('project-state/master-inventory.json')
    old = {row['id']: row for row in before['candidates']}
    new = {row['id']: row for row in after['candidates']}
    changed = {key for key in old.keys() | new.keys() if old.get(key) != new.get(key)}
    assert changed == IDS, 'PR #206 correction changed unrelated inventory rows'
    expected_note = ('Saved official source bytes and local visual review passed; '
                     'nonproduction preview verified; live County check returned HTTP 403; '
                     'owner review and production verification pending.')
    for key in IDS:
        expected = copy.deepcopy(old[key])
        expected['validation_status'] = expected_note
        expected['updated_at'] = new[key]['updated_at']
        assert new[key] == expected, 'PR #206 correction altered another inventory field: ' + key
        assert new[key]['status'] == 'implemented'
    before['generated_at'] = after['generated_at']
    before['candidates'] = after['candidates']
    assert before == after, 'PR #206 correction altered inventory metadata outside the generation timestamp'
