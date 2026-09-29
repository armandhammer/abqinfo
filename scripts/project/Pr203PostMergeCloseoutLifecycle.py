"""Guard PR #203's production closeout against new visible or archive changes."""

import hashlib
import json

from WorkflowStageLifecycle import ROOT, StageSnapshot, canonical_bytes, git

BASE = 'd6337416fd3de9e9610bb96316893150522d8a33'
MERGE = 'c901990afb47902755f6e293f2ea801fbaebc041'
HEAD = '164d955d72300824cd8c561290caeb3fbf4baac6'
TASK = 'project-state/governance/pr203-postmerge-closeout-2026-09-28/'
ALLOWED = {
    'project-state/CURRENT.md', 'project-state/checkpoint.json',
    'project-state/governance/active-task.json', 'project-state/governance-registry.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/Invoke-ProjectValidation.ps1',
    'scripts/project/Pr203PostMergeCloseoutLifecycle.py',
    'scripts/project/Verify-Pr203Production.py',
    'scripts/project/Test-Pr203PostMergeCloseout.py',
}


def guard_current_delta():
    stage = StageSnapshot('pr203-postmerge-closeout')
    assert stage.stage['baseline_commit'] == BASE
    assert git('rev-parse', MERGE + '^{tree}') == git('rev-parse', HEAD + '^{tree}')
    stage.assert_no_visible_changes(BASE, git('rev-parse', BASE + ':content').decode().strip())
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', BASE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(p in ALLOWED or p.startswith(TASK) for p in paths), 'Unexpected PR203 closeout delta'
    for path in ('project-state/master-inventory.json', 'project-state/r2-inventory.json',
                 'project-state/discovery/open-space-map-quality-2026-09-28/review-ready.json',
                 'project-state/discovery/open-space-map-quality-2026-09-28/preview-verification.json',
                 'project-state/discovery/open-space-map-quality-2026-09-28/public-byte-measurements.json',
                 'project-state/governance/open-space-quality-2026-09-28/implementation-v8.json'):
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', BASE + ':' + path))
    receipt_path = ROOT / (TASK + 'receipt.json')
    if not receipt_path.exists():
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['pr']['number'] == 203 and receipt['pr']['state'] == 'MERGED'
    assert receipt['merge_commit'] == MERGE and receipt['reviewed_head'] == HEAD
    assert receipt['merge_tree_matches_reviewed_head'] and receipt['manual_review_gate_closed_by_merge']
    assert receipt['production_pages_verified'] == 2 and receipt['family_records_verified'] == 18
    assert receipt['verified_archive_count'] == 16
    assert receipt['closeout_visitor_visible_changes'] == 0
    assert receipt['closeout_inventory_changes'] == 0 and receipt['closeout_r2_changes'] == 0
    for name, key in (('production-verification.json', 'production_verification_sha256'),
                      ('merge-deployment.json', 'deployment_sha256'),
                      ('public-byte-verification.json', 'public_byte_verification_sha256')):
        actual = hashlib.sha256(canonical_bytes((ROOT / (TASK + name)).read_bytes())).hexdigest()
        assert receipt[key] == actual
    production = json.loads((ROOT / (TASK + 'production-verification.json')).read_text(encoding='utf-8'))
    public = json.loads((ROOT / (TASK + 'public-byte-verification.json')).read_text(encoding='utf-8'))
    assert production['result'] == public['result'] == 'passed'
    assert len(production['pages']) == 2 and all(p['article_identical_across_witnesses'] for p in production['pages'])
    assert all(len(p['witnesses']) == 3 for p in production['pages'])
    assert production['family_records_with_official_source_links'] == 18
    assert production['family_records_with_archive_links'] == public['verified_archive_count'] == 16
    assert len(public['records']) == 16 and all(r['matches_reviewed_inventory'] for r in public['records'])
    active = json.loads((ROOT / 'project-state/governance/active-task.json').read_text(encoding='utf-8'))
    assert active['state'] == 'complete' and active['contract'].startswith(TASK)
    implementation = json.loads((ROOT / active['implementation']).read_text(encoding='utf-8'))
    assert implementation['status'] == 'complete'
    if receipt.get('normal_validation') == 'passed':
        log = canonical_bytes((ROOT / (TASK + 'validation.log')).read_bytes())
        assert receipt['validation_log_sha256'] == hashlib.sha256(log).hexdigest()
