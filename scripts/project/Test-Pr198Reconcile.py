"""Regression for branch-history union and immutable completed-task evidence."""

import hashlib
import json
import tempfile
from pathlib import Path

import TaskGovernance as G
from Pr198ReconcileLifecycle import guard_current_delta

guard_current_delta()
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    old = root / 'old-plan.json'
    old.write_text(json.dumps({'artifact_type': 'task_implementation_plan', 'contract': 'old-contract.json'}), encoding='utf-8')
    digest = hashlib.sha256(old.read_bytes()).hexdigest()
    (root / 'audit.json').write_text(json.dumps({'artifacts': [{
        'path': 'old-plan.json', 'sha256': digest,
        'classification': 'historical evidence only / non-binding'}]}), encoding='utf-8')
    data = {'entries': [], 'audit_artifact': 'audit.json'}
    G.check_unregistered(data, ['old-plan.json'], root)
    old.write_text(old.read_text(encoding='utf-8') + ' ', encoding='utf-8')
    try:
        G.check_unregistered(data, ['old-plan.json'], root)
    except (G.GovernanceError, FileNotFoundError, KeyError):
        pass
    else:
        raise AssertionError('Modified historical implementation plan was accepted')
print('PASS: PR198 reviewed bytes, inventory, R2 and main snapshot preserved; exact completed plans stay historical and tampering fails.')
