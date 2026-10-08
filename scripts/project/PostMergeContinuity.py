"""Validate tracked post-merge evidence and resume claims; never generate state.

Historical integration intents stay immutable. Additive reconciliation can map
an old runtime reference to its exact tracked snapshot. Snapshots name a verified
completed synchronization, not their containing commit, avoiding recursive seals.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from WorkflowStageLifecycle import ROOT, StageSnapshot, canonical_bytes, git, STATE_PATHS

TASK = 'postmerge-continuity-2026-10-08'
P = 'project-state/governance/' + TASK + '/'
BASE = '3015ba9eae4c575b527c26370cdbab50448a5735'


def sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require_durable(path, tracked, exists, ignored):
    value = Path(path)
    assert not value.is_absolute() and '..' not in value.parts, 'Evidence escapes repository: ' + path
    assert exists and path in tracked and not ignored, 'Final-ref evidence must exist in Git outside ignored runtime: ' + path


def require_synced(snapshot):
    head = snapshot['main']
    assert re.fullmatch(r'[0-9a-f]{40}', head)
    assert snapshot['planning_snapshot'] == head
    assert snapshot['remote_refs'] == {'refs/heads/main': head, 'refs/heads/chatgpt/planning-snapshot': head}
    assert snapshot['worktree_clean'] and snapshot['validation'] == 'passed'
    return head


def require_current_claim(text, synchronized):
    if synchronized:
        assert not re.search(r'(?:synchron\w*|\bsync\b)[^\n.;]{0,100}\bpending\b|\bpending\b[^\n.;]{0,100}(?:synchron\w*|\bsync\b)', text, re.I), 'Resume pointer reports completed synchronization as pending'


def regression():
    path = 'project-state/governance/example/final-refs.json'
    require_durable(path, {path}, True, False)
    for tracked, exists, ignored in [(set(), True, False), ({path}, False, False), ({path}, True, True)]:
        try:
            require_durable(path, tracked, exists, ignored)
        except AssertionError:
            pass
        else:
            raise AssertionError('Unavailable evidence accepted')
    for text in ['authorized main/planning synchronization pending.', 'Pending branch synchronization.', 'main/planning sync pending.']:
        try:
            require_current_claim(text, True)
        except AssertionError:
            pass
        else:
            raise AssertionError('Stale synchronization claim accepted')
    require_current_claim('Synchronization completed; source delivery remains pending.', True)
    require_current_claim('Synchronization pending.', False)
    good = dict(main=BASE, planning_snapshot=BASE, remote_refs={'refs/heads/main': BASE, 'refs/heads/chatgpt/planning-snapshot': BASE}, worktree_clean=True, validation='passed')
    require_synced(good)
    try:
        require_synced({**good, 'planning_snapshot': '0' * 40})
    except AssertionError:
        pass
    else:
        raise AssertionError('Unequal branch snapshot accepted')


def validate():
    regression()
    tracked = set(git('ls-files').decode().splitlines())
    mappings = {}
    for path in sorted((ROOT / 'project-state/governance').glob('*/reconciliation.json')):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if data.get('artifact_type') != 'postmerge_ref_reconciliation':
            continue
        relative = path.relative_to(ROOT).as_posix()
        require_durable(relative, tracked, path.is_file(), False)
        for row in data['reconciliations']:
            intent = row['integration_intent']
            assert intent not in mappings, 'Ambiguous additive reconciliation: ' + intent
            assert sha((ROOT / intent).read_bytes()) == row['integration_intent_sha256'], 'Historical integration intent changed'
            evidence = row['durable_final_ref_evidence']
            ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-q', '--', evidence], cwd=ROOT).returncode == 0
            require_durable(evidence, tracked, (ROOT / evidence).is_file(), ignored)
            assert sha((ROOT / evidence).read_bytes()) == row['final_ref_sha256'], 'Final-ref evidence changed'
            snapshot = json.loads((ROOT / evidence).read_text(encoding='utf-8-sig'))
            head = require_synced(snapshot)
            subprocess.run(['git', 'merge-base', '--is-ancestor', snapshot['merge_sha'], head], cwd=ROOT, check=True)
            subprocess.run(['git', 'merge-base', '--is-ancestor', head, data['baseline_commit']], cwd=ROOT, check=True)
            original = json.loads((ROOT / intent).read_text(encoding='utf-8-sig'))
            assert original['final_ref_evidence'] == row['original_final_ref_evidence']
            mappings[intent] = evidence
    # Enforce durable evidence for every new/changed intent after the repair
    # baseline; unrelated historical intents retain their original authority.
    paths = set(git('diff', BASE, '--name-only').decode().splitlines())
    paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    for path in sorted(paths):
        if not path.startswith('project-state/') or not path.endswith('integration-intent.json') or not (ROOT / path).is_file():
            continue
        intent = json.loads((ROOT / path).read_text(encoding='utf-8-sig'))
        if 'final_ref_evidence' in intent:
            evidence = mappings.get(path, intent['final_ref_evidence'])
            ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-q', '--', evidence], cwd=ROOT).returncode == 0
            require_durable(evidence, tracked, (ROOT / evidence).is_file(), ignored)
    current = (ROOT / 'project-state/CURRENT.md').read_text(encoding='utf-8-sig')
    synchronized = False
    primary = re.search(r'PR\s*#(\d+)', current.split('\n\n')[1])
    primary_pr = primary.group(1) if primary else None
    for link in re.findall(r'\]\(([^)]+)\)', current):
        if '://' in link or link.startswith('#'):
            continue
        target = (ROOT / 'project-state' / link.split('#')[0]).resolve()
        relative = target.relative_to(ROOT).as_posix()
        require_durable(relative, tracked, target.is_file(), False)
        if target.name == 'receipt.json' and primary_pr and target.parent.name.startswith('pr' + primary_pr + '-postmerge-closeout-'):
            intent_path = target.parent / 'integration-intent.json'
            if intent_path.is_file():
                intent = intent_path.relative_to(ROOT).as_posix()
                value = json.loads(intent_path.read_text(encoding='utf-8-sig'))
                evidence = mappings.get(intent, value.get('final_ref_evidence', ''))
                if evidence and evidence in tracked and (ROOT / evidence).is_file():
                    require_synced(json.loads((ROOT / evidence).read_text(encoding='utf-8-sig')))
                    synchronized = True
    require_current_claim(current, synchronized)
    checkpoint = json.loads((ROOT / 'project-state/checkpoint.json').read_text(encoding='utf-8-sig'))
    require_current_claim(checkpoint['resume_command'], synchronized)
    print('PASS post-merge continuity: tracked PR216/217 ref evidence, current resume claims, new integration references and negative regressions')


def guard():
    from TaskGovernance import changed_paths
    stage = StageSnapshot(TASK)
    pop = stage.load_json(P + 'population.json')
    assert pop['baseline_commit'] == BASE and not pop['candidate_ids'] and not pop['pages'] and not pop['families']
    paths = set(git('diff', BASE, stage.end, '--name-only').decode().splitlines()) if stage.end else set(changed_paths(BASE))
    assert paths <= set(pop['artifact_paths']), paths - set(pop['artifact_paths'])
    stage.assert_no_visible_changes(BASE, git('rev-parse', BASE + ':content').decode().strip())
    for path in STATE_PATHS | {'project-state/r2-storage-policy.json'}:
        before = git('show', BASE + ':' + path)
        after = stage.read_bytes(path)
        if path == 'project-state/checkpoint.json':
            before = json.loads(before); after = json.loads(after)
            before.pop('resume_command'); after.pop('resume_command')
            assert before == after, 'Checkpoint change exceeds resume instruction'
        else:
            assert canonical_bytes(before) == canonical_bytes(after), path
    # Existing governance entries and the entire completed PR216/217 evidence
    # remain exact; only the current task's owner authority is additive.
    before = json.loads(git('show', BASE + ':project-state/governance-registry.json'))
    after = stage.load_json('project-state/governance-registry.json')
    assert after['entries'][:len(before['entries'])] == before['entries']
    assert [r['governance_id'] for r in after['entries'][len(before['entries']):]] == ['owner-' + TASK]
    for folder in ['pr216-postmerge-closeout-2026-10-07', 'pr217-postmerge-closeout-2026-10-08']:
        for path in git('ls-tree', '-r', '--name-only', BASE, '--', 'project-state/governance/' + folder + '/').decode().splitlines():
            assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', BASE + ':' + path)), path
    print('PASS continuity exact delta: sealed closeouts, existing governance, content, inventory, queues and R2 preserved')
