"""Guard the PR #204 post-merge closeout as background-only work."""

import gzip
import hashlib
import json
from pathlib import Path

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

BASE = 'f4507ade4f0a76465843fd7277c636481028d576'
REVIEWED = '6210ec2452c46d63134bee657b42768cb278e4d3'
TASK = 'project-state/governance/pr204-postmerge-closeout-2026-09-29/'
PAGE = 'content/transportation/roadway-projects/_index.md'
REVIEW = 'project-state/governance/ordinary-county-roadway-2026-09-29/review-v4.json'


def guard_current_delta():
    stage = StageSnapshot('pr204-postmerge-closeout')
    assert stage.stage['baseline_commit'] == BASE
    assert git('rev-parse', BASE + '^{tree}') == git('rev-parse', REVIEWED + '^{tree}')
    stage.assert_no_visible_changes(BASE, git('rev-parse', BASE + ':content').decode().strip())
    active = stage.load_json('project-state/governance/active-task.json')
    population = stage.load_json(active['population'])
    selected = set(population['candidate_ids'])
    assert len(selected) == 6 and population['pages'] == [PAGE]
    paths = (set(git('diff', BASE, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(BASE)))
    assert paths <= set(population['artifact_paths']), 'PR204 closeout changed an unfrozen path'
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json',
                 'project-state/ordinary-queue-current.json',
                 'project-state/discovery/ordinary-county-roadway-2026-09-29/queue.json', REVIEW):
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', BASE + ':' + path)), path
    review = stage.load_json(REVIEW)
    assert {row['id'] for row in review['entries']} == selected
    assert review['preview_verification']['page_http_status'] == 200
    old = stage.load_json('project-state/governance/ordinary-county-roadway-2026-09-29/implementation-v19.json')
    assert old['status'] == 'complete'
    receipt_path = Path(__file__).resolve().parents[2] / (TASK + 'receipt.json')
    if not receipt_path.exists() and not stage.end:
        return
    receipt = stage.load_json(TASK + 'receipt.json')
    assert receipt['pr']['number'] == 204 and receipt['pr']['state'] == 'MERGED'
    assert receipt['merge_commit'] == BASE and receipt['reviewed_head'] == REVIEWED
    assert receipt['merge_tree_matches_reviewed_head'] and receipt['manual_review_gate_closed_by_merge']
    assert receipt['production_pages_verified'] == 1 and receipt['governed_records_verified'] == 6
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == receipt['closeout_r2_changes'] == 0
    for name, key in (('merge-deployment.json', 'merge_deployment_sha256'),
                      ('production-verification.json', 'production_verification_sha256'),
                      ('production.html.gz', 'production_html_gz_sha256'),
                      ('merge-deployment.html.gz', 'merge_deployment_html_gz_sha256'),
                      ('reviewed-preview.html.gz', 'reviewed_preview_html_gz_sha256')):
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(TASK + name))).hexdigest() == receipt[key]
    production = stage.load_json(TASK + 'production-verification.json')
    assert production['result'] == 'passed' and production['article_identical_across_witnesses']
    assert production['governed_record_count'] == 6 and len(production['witnesses']) == 3
    assert all(row['count'] == 1 for row in production['required_official_source_links'])
    assert len(production['required_official_source_links']) == 6
    assert len(production['required_anchors']) == 2
    for name, witness in (('production.html.gz', production['witnesses'][0]),
                          ('merge-deployment.html.gz', production['witnesses'][1]),
                          ('reviewed-preview.html.gz', production['witnesses'][2])):
        raw = gzip.decompress(stage.read_bytes(TASK + name))
        assert len(raw) == witness['size_bytes']
        assert hashlib.sha256(raw).hexdigest() == witness['html_sha256']
    active = stage.load_json('project-state/governance/active-task.json')
    assert active['contract'].startswith(TASK)
    if receipt.get('normal_validation') == 'passed':
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(TASK + 'validation.log'))).hexdigest() == receipt['validation_log_sha256']
