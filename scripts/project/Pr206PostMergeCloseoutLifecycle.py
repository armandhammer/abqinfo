"""Guard PR #206 closeout and preserve its reproducible source evidence."""

import gzip
import hashlib
import json

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

BASE = 'dd8d7b49878cf48c62a6c1dedddbd40289ecf803'
REVIEWED = '0d63d57f9be4d39909e23cb078fd6c6c982660d0'
TASK = 'project-state/governance/pr206-postmerge-closeout-2026-09-29/'
PAGE = 'content/public-works/stormwater-drainage.md'
CORRECTION = 'project-state/governance/pr206-review-correction-2026-09-29/'
IDS = {'src-e41d6b432e52a7e1', 'src-5dedef596ea61914',
       'src-b674369d94936b08', 'src-ea28455d489f1c2c'}


def guard_current_delta():
    stage = StageSnapshot('pr206-postmerge-closeout')
    assert stage.stage['baseline_commit'] == BASE
    assert git('rev-parse', BASE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    stage.assert_no_visible_changes(BASE, git('rev-parse', BASE + ':content').decode().strip())
    active = stage.load_json('project-state/governance/active-task.json')
    population = stage.load_json(active['population'])
    assert set(population['candidate_ids']) == IDS and population['pages'] == [PAGE]
    paths = (set(git('diff', BASE, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(BASE)))
    assert paths <= set(population['artifact_paths']), 'Unfrozen PR206 closeout path'
    protected = ['project-state/master-inventory.json', 'project-state/r2-inventory.json',
                 'project-state/ordinary-queue-current.json',
                 'project-state/discovery/ordinary-drainage-projects-2026-09-29/queue.json',
                 'scripts/project/Test-OrdinaryDrainagePublication.py',
                 'scripts/project/OrdinaryDrainageReviewCorrectionLifecycle.py']
    protected += git('ls-tree', '-r', '--name-only', BASE, '--', CORRECTION,
                     'project-state/governance/ordinary-drainage-projects-2026-09-29').decode().splitlines()
    for path in protected:
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', BASE + ':' + path)), path
    receipt = stage.load_json(TASK + 'receipt.json')
    assert receipt['pr']['number'] == 206 and receipt['pr']['state'] == 'MERGED'
    assert receipt['merge_commit'] == BASE and receipt['reviewed_head'] == REVIEWED
    assert receipt['merge_tree_matches_reviewed_head'] and receipt['manual_review_gate_closed_by_merge']
    assert receipt['production_pages_verified'] == 1 and receipt['governed_records_verified'] == 4
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == receipt['closeout_r2_changes'] == 0
    for name, expected in receipt['evidence_hashes'].items():
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(TASK + name))).hexdigest() == expected, name
    production = stage.load_json(TASK + 'production-verification.json')
    assert production['result'] == 'passed' and production['article_identical_across_witnesses']
    assert production['governed_record_count'] == 4 and len(production['witnesses']) == 3
    assert {r['id'] for r in production['required_official_source_links']} == IDS
    assert all(r['count'] == 1 for r in production['required_official_source_links'])
    assert production['required_anchors'] == ['county-drainage-projects']
    for name, witness in zip(('production.html.gz', 'merge-deployment.html.gz', 'reviewed-preview.html.gz'),
                             production['witnesses']):
        raw = gzip.decompress(stage.read_bytes(TASK + name))
        assert len(raw) == witness['size_bytes']
        assert hashlib.sha256(raw).hexdigest() == witness['html_sha256']
    sources = stage.load_json(TASK + 'source-link-verification.json')
    assert {r['id'] for r in sources['records']} == IDS
    assert sources['publication_form'] == 'live_service' and sources['archive_objects'] == 0
    assert all(r['http_status'] in (200, 403) for r in sources['records'])
    checkpoint = stage.load_json('project-state/checkpoint.json')
    assert checkpoint['pr206_postmerge_closeout']['state'] == 'complete_postmerge_closeout'
    assert checkpoint['counts_by_status']['approved for addition'] == 20
    assert checkpoint['counts_by_status']['pending review'] == 372
    assert active['contract'].startswith(TASK)
    if receipt['normal_validation'] == 'passed':
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(TASK + 'validation.log'))).hexdigest() == receipt['validation_log_sha256']
        clean = stage.load_json(TASK + 'clean-worktree-verification.json')
        assert clean['normal_validation'] == 'passed' and clean['untracked_source_captures_present'] is False
