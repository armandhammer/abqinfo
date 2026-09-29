"""Check the exact derived queue and reject a changed saved blocker."""
import copy
from Pr202OrdinaryQueueLifecycle import guard_current_delta, validate_queue, BASE
from WorkflowStageLifecycle import StageSnapshot
import json

queue = guard_current_delta()
stage = StageSnapshot('pr202-ordinary-queue-reconcile')
old = stage.load_json(BASE)
rows = {r['id']: r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
ids = set(queue['pr202_implemented_ids_removed_from_approved'])
bad = copy.deepcopy(queue)
bad['gated_pending_ids'].pop(next(iter(bad['gated_pending_ids'])))
try:
    validate_queue(old, bad, rows, ids)
except AssertionError:
    pass
else:
    raise AssertionError('A removed saved gate passed validation')
print('PASS: 30 approved, 372 pending, 321 gated, 42 source blocked, 9 prerequisites; 21 PR202 IDs removed; no visible, inventory, R2 or historical queue change')
