"""Guard the one-label Capital Spending correction after PR #198."""

from WorkflowStageLifecycle import ROOT, StageSnapshot, git

BASE = '22186a1d26568a2fb2f5ae320fa125d3f4a8ae0b'
PAGE = 'content/city-data/capital-spending.md'
TASK = 'project-state/governance/capital-title-case-2026-09-28/'
OLD = b'EPC-stage book'
NEW = b'EPC-Stage Book'
ALLOWED = {
    PAGE,
    'project-state/governance/active-task.json',
    'project-state/workflow-stage-lifecycle.json',
    'scripts/project/CapitalTitleCaseLifecycle.py',
    'scripts/project/Pr198SettledLifecycle.py',
    'scripts/project/Test-Pr198Settled.py',
}


def guard_current_delta():
    stage = StageSnapshot('capital-title-case')
    assert stage.stage['baseline_commit'] == BASE
    endpoint = stage.end or 'HEAD'
    paths = set(git('diff', BASE, endpoint, '--name-only').decode().splitlines())
    if not stage.end:
        paths.update(git('diff', endpoint, '--name-only').decode().splitlines())
        paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    assert all(path in ALLOWED or path.startswith(TASK) for path in paths), 'Unexpected title-case task delta'
    assert not paths.intersection({'project-state/master-inventory.json', 'project-state/r2-inventory.json'})
    assert not paths.intersection({'layouts', 'assets', 'static', 'hugo.toml'})
    old = git('show', BASE + ':' + PAGE).replace(b'\r\n', b'\n')
    new = stage.read_bytes(PAGE).replace(b'\r\n', b'\n')
    assert old.count(OLD) == 1 and new == old.replace(OLD, NEW), 'Capital Spending changed beyond the one label'
    other_visible = git('diff', BASE, endpoint, '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').decode().splitlines()
    assert other_visible in ([], [PAGE]), 'Other visitor-visible files changed'
    if not stage.end:
        working_visible = git('diff', endpoint, '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').decode().splitlines()
        assert working_visible in ([], [PAGE]), 'Other working visitor-visible files changed'
