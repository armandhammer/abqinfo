from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / 'project-state' / 'CURRENT.md'
text = CURRENT.read_text(encoding='utf-8-sig')

def malformed_link_separator(value):
    return re.search(r'\)[ \t]+\?[ \t]+\[[^\]\r\n]*\]\(', value) is not None


def test_link_separator_regression():
    assert malformed_link_separator('[Receipt](receipt.json) ? [Review](review.json)')
    assert malformed_link_separator('[Receipt](receipt.json)\t?\t[Review](review.json)')
    assert not malformed_link_separator('[Receipt](receipt.json) \u00b7 [Review](review.json)')
    assert not malformed_link_separator('What remains? See [Review](review.json).')
    assert not malformed_link_separator('[Search](search?q=receipt) [Review](review.json)')


test_link_separator_regression()
if malformed_link_separator(text):
    raise SystemExit('CURRENT.md contains a malformed question-mark Markdown-link separator; use U+00B7.')

if len(text) > 1800:
    raise SystemExit(f'CURRENT.md exceeds the 1800-character resume-pointer limit ({len(text)}).')
if len(re.findall(r'(?m)^# Current project state\s*$', text)) != 1:
    raise SystemExit('CURRENT.md must have exactly one current-state heading.')
if re.search(r'(?im)^##\s+(historical|superseded|previous|prior)\b', text):
    raise SystemExit('CURRENT.md contains an embedded historical resume block.')

required_links = (
    'governance/active-task.json',
    'governance/pr207-owner-correction-2026-09-30/receipt.json',
    'governance/pr207-postmerge-closeout-2026-09-30/receipt.json',
    'governance/pr207-final-ref-verification-2026-09-30/final-verification.json',
    'governance/approved-queue-lightweight-triage-2026-09-30/triage.json',
    'ordinary-queue-current.json',
    'governance-workflow.md',
    'governance-registry.json',
)
missing = [link for link in required_links if f']({link})' not in text]
if missing:
    raise SystemExit('CURRENT.md is missing resume links: ' + ', '.join(missing))
for link in required_links:
    if not (ROOT / 'project-state' / link).is_file():
        raise SystemExit('CURRENT.md links to a missing artifact: ' + link)

from PostMergeContinuity import validate
validate()
print('CURRENT.md resume-pointer regression passed.')


def guard_current_delta():
    """Keep this maintenance stage separate from the completed family review."""
    from WorkflowStageLifecycle import StageSnapshot, git, STATE_PATHS
    from TaskGovernance import changed_paths
    stage = StageSnapshot('current-separator-regression-2026-10-04')
    base = stage.stage['baseline_commit']
    population = stage.load_json('project-state/governance/current-separator-regression-2026-10-04/population.json')
    before = git('show', base + ':project-state/CURRENT.md').decode('utf-8').replace('\r\n', '\n')
    expected = before.replace(') ? [Family review]', ') \u00b7 [Family review]')
    assert expected != before and stage.read_text('project-state/CURRENT.md') == expected, 'CURRENT summary changed beyond the authorized separator'
    paths = set(git('diff', base, stage.end, '--name-only').decode().splitlines()) if stage.end else set(changed_paths(base))
    assert paths <= set(population['artifact_paths']), 'Unrelated maintenance mutation: ' + str(paths - set(population['artifact_paths']))
    for path in STATE_PATHS | {'project-state/r2-storage-policy.json'}:
        assert stage.read_bytes(path).replace(b'\r\n', b'\n') == git('show', base + ':' + path).replace(b'\r\n', b'\n'), path
    stage.assert_no_visible_changes(base, git('rev-parse', base + ':content').decode().strip())
    print('CURRENT separator maintenance boundary passed: unchanged inventory/queues, visible content and R2 state.')
