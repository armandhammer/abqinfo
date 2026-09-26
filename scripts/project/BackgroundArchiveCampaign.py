"""Evidence helpers for historical regressions after authorized archive progress."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
def campaign(): return json.loads(PATH.read_text(encoding='utf-8-sig')) if PATH.exists() else None
def completed_originals():
    d=campaign()
    return {r['id']:r for r in d['records'] if r.get('inventory_reconciled') and r['outcome']=='archive_complete' and r['public_verification']['byte_identical']} if d else {}
def historical_r2(current):
    d=campaign()
    if not d:return current
    baseline=json.loads((ROOT/d['baseline_r2_artifact']).read_text(encoding='utf-8-sig'))
    actual={o['key']:o for o in current['objects']}
    for o in baseline['objects']:
        assert all(actual[o['key']][f]==o[f] for f in ('key','size_bytes','etag')),o['key']
    return baseline
def ordinary_baseline_inventory(current):
    ordinary_path=ROOT/'project-state/discovery/ordinary-queue-large-resolution-campaign-2026-09-26.json'
    if ordinary_path.exists():
        ordinary=json.loads(ordinary_path.read_text(encoding='utf-8-sig'))
        assert ordinary['baseline_commit']=='b8a52bbdef5f78599187b1020d1f10b65c1a17b4'
        completed=json.loads(subprocess.check_output(['git','show',ordinary['baseline_commit']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))
        checkpoint={r['id']:r for r in completed['candidates']}
        expected={r['id'] for r in ordinary['resolved_records']}
        assert {r['id'] for r in current['candidates'] if r!=checkpoint[r['id']]}==expected
        assert all(checkpoint[i]['status']=='pending review' for i in expected)
        # The ordinary campaign's dedicated regression checks each current
        # transition and archive. Keep this earlier campaign's original exact
        # completion contract against its immutable post-merge snapshot.
        return completed
    return current

def historical_inventory(current):
    d=campaign()
    if not d:return current
    current=ordinary_baseline_inventory(current)
    prior=json.loads(subprocess.check_output(['git','show',d['baseline_git_sha']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))
    before={r['id']:r for r in prior['candidates']}; permitted=set(completed_originals())
    assert {r['id'] for r in current['candidates'] if r!=before[r['id']]}<=permitted
    return prior
