"""Guard the background-only reconciliation of review-ready PR #198."""

import hashlib
import json

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

BASELINE = 'de48a74d8522806a0d68ce247eb1d5d6a309c0ca'
PR_HEAD = '073edabd10d9a0996eb897e2ed957943aed4de18'
KEY = 'city-data/capital-spending/abqinfo-2009-general-obligation-bond-program-historical-master-record.pdf'
SHA256 = 'ae2a1567476cf966b87b87c268dfd8795ad5ea6a5bc474ed4e009bc4b42830af'
PREFIX = 'project-state/governance/pr198-background-snapshot-2026-09-27/'
ALLOWED = {
    'project-state/CURRENT.md', 'project-state/r2-inventory.json',
    'project-state/workflow-stage-lifecycle.json', 'project-state/governance-registry.json',
    'project-state/governance/active-task.json',
    'project-state/governance/audit-2026-09-27/artifact-audit.json',
    'project-state/governance/pr198-approved-2026-09-27/owner-approval.json',
    'project-state/governance/pr198-remote-resume-2026-09-27/archive-request.json',
    'project-state/governance/pr198-archive-authorized-2026-09-27/receipt.json',
    'project-state/governance/pr198-archive-authorized-2026-09-27/public-verification.json',
    'scripts/project/Pr198BackgroundSnapshotLifecycle.py',
    'scripts/project/Test-Pr198BackgroundSnapshot.py',
    'scripts/project/Invoke-ProjectValidation.ps1',
}


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def guard_current_delta():
    stage = StageSnapshot('pr198-background-snapshot')
    assert stage.stage['baseline_commit'] == BASELINE
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', BASELINE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(PREFIX) for path in paths), 'Unapproved PR198 snapshot delta'
    stage.assert_no_visible_changes(BASELINE, git('rev-parse', BASELINE + ':content').decode().strip())
    assert not git('diff', BASELINE, endpoint, '--name-only', '--', 'project-state/master-inventory.json').strip()
    if not stage.end:
        assert not git('diff', endpoint, '--name-only', '--', 'project-state/master-inventory.json').strip()

    before = json.loads(git('show', BASELINE + ':project-state/r2-inventory.json'))
    after = stage.load_json('project-state/r2-inventory.json')
    old = {obj['key']: obj for obj in before['objects']}
    new = {obj['key']: obj for obj in after['objects']}
    assert set(new) - set(old) == {KEY} and set(old) <= set(new)
    assert all(old[key] == new[key] for key in old), 'Existing R2 inventory entry changed'
    assert new[KEY]['size_bytes'] == 1303860
    assert after['object_count'] == before['object_count'] + 1 == len(new)
    assert after['total_bytes'] == before['total_bytes'] + 1303860

    approval = stage.load_json('project-state/governance/pr198-approved-2026-09-27/owner-approval.json')
    assert approval['archive_objects'][0]['r2_key'] == KEY
    assert approval['archive_objects'][0]['sha256'] == SHA256
    assert approval['merge_authorized'] is False and approval['overwrite_or_delete_authorized'] is False
    verification = stage.load_json('project-state/governance/pr198-archive-authorized-2026-09-27/public-verification.json')
    assert any(item['r2_key'] == KEY and item['sha256'] == SHA256 and
               item['size_bytes'] == 1303860 and item['full_get_byte_identical'] for item in verification)
    receipt = stage.load_json(PREFIX + 'receipt.json')
    assert receipt['pr198_head'] == PR_HEAD and receipt['pr198_open_unmerged'] is True
    assert receipt['manual_editorial_review_required'] is True
    assert receipt['visitor_visible_pr_content_integrated'] is False
    assert receipt['main_content_tree'] == git('rev-parse', BASELINE + ':content').decode().strip()
    assert receipt['r2_new_object_sha256'] == SHA256
    registry = stage.load_json('project-state/governance-registry.json')
    owner = [row for row in registry['entries'] if row['governance_id'] == 'owner-pr198-exact-archive-publication-2026-09-27']
    assert len(owner) == 1 and owner[0]['state'] == 'active'
    assert owner[0]['controlling_artifacts'][0]['sha256'] == sha256('project-state/governance/pr198-approved-2026-09-27/owner-approval.json')
