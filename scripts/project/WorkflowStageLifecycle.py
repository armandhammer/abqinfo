"""Explicit stage snapshots and active guards, without changing historical evidence."""
import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / 'project-state/workflow-stage-lifecycle.json'
VISIBLE_PATHS = ('content', 'layouts', 'assets', 'static', 'hugo.toml')
STATE_PATHS = {
    'project-state/master-inventory.json', 'project-state/r2-inventory.json',
    'project-state/checkpoint.json', 'project-state/ordinary-queue-current.json',
    'project-state/discovery/codex-human-review-followup-queue.json',
    'project-state/discovery/consolidated-human-review-queue.json',
    'project-state/discovery/mission-scope-borderline-human-review-queue.json',
}

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def canonical_bytes(value):
    return value.replace(b'\r\n', b'\n')

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()

@lru_cache(maxsize=1)
def registry():
    return json.loads(REGISTRY.read_text(encoding='utf-8'))

class StageSnapshot:
    """Read stage-owned state at its explicit endpoint; preserve live evidence checks."""
    def __init__(self, stage_id):
        self.stage_id = stage_id
        self.stage = next(s for s in registry()['stages'] + registry().get('completed_audits', []) if s['id'] == stage_id)
        self.end = self.stage.get('end_commit')

    def relative(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        return path.resolve().relative_to(ROOT).as_posix()

    def read_bytes(self, path):
        relative = self.relative(path)
        return git('show', self.end + ':' + relative) if self.end else (ROOT / relative).read_bytes()

    def read_text(self, path):
        return self.read_bytes(path).decode('utf-8-sig').replace('\r\n', '\n')

    def load_json(self, path):
        return json.loads(self.read_text(path))

    def load_state_or_live_evidence(self, path):
        relative = self.relative(path)
        if relative in STATE_PATHS:
            return self.load_json(path)
        return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))

    def assert_no_visible_changes(self, baseline, expected_content_tree):
        """Retain the complete original content invariant over the stage interval."""
        endpoint = self.end or 'HEAD'
        assert not git('diff', baseline, endpoint, '--name-only', '--', *VISIBLE_PATHS).strip()
        assert git('rev-parse', endpoint + ':content').decode().strip() == expected_content_tree
        if not self.end:
            assert not git('diff', endpoint, '--name-only', '--', *VISIBLE_PATHS).strip()
            assert not git('ls-files', '--others', '--exclude-standard', '--', *VISIBLE_PATHS).strip()

def validate_registry(data):
    stages = data['stages']
    assert len({s['id'] for s in stages}) == len(stages)
    active = [s for s in stages if not s.get('end_commit')]
    assert len(active) == 1 and active[0] == stages[-1]
    for index, stage in enumerate(stages):
        assert stage['regression_scripts']
        assert len(stage['baseline_commit']) == 40
        if stage.get('end_commit'):
            assert len(stage['end_commit']) == 40
            assert index + 1 < len(stages)
            assert stage['end_commit'] == stages[index + 1]['baseline_commit'], 'Uncovered stage boundary'
        else:
            assert stage['exact_delta_guard'], 'Active stage must declare an exact delta guard'
    audits=data.get('completed_audits',[])
    assert len({s['id'] for s in stages+audits})==len(stages)+len(audits)
    for audit in audits:
        assert len(audit['end_commit'])==40 and audit['regression_scripts']
    return active[0]

def validate_evidence(data):
    """Old evidence must still equal its sealed bytes, even though live state advances."""
    for seal in data['protected_evidence']:
        old = canonical_bytes(git('show', seal['commit'] + ':' + seal['path']))
        live = canonical_bytes((ROOT / seal['path']).read_bytes())
        validate_evidence_bytes(seal['sha256'],old,live)

def validate_evidence_bytes(expected,old,live):
    assert hashlib.sha256(old).hexdigest()==expected, 'Historical witness changed'
    assert live==old, 'Completed-stage evidence changed'
