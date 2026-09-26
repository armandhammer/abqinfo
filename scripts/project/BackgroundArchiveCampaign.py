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
    second_path=ROOT/'project-state/discovery/ordinary-queue-second-large-resolution-campaign-2026-09-26.json'
    if second_path.exists():
        second=json.loads(second_path.read_text(encoding='utf-8-sig'))
        assert second['baseline_commit']=='34ccc0fe230ffb8290652979cbe8603c69db3115'
        snapshot=json.loads(subprocess.check_output(['git','show',second['baseline_commit']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))
        before={r['id']:r for r in snapshot['candidates']};after={r['id']:r for r in current['candidates']}
        legacy=json.loads((ROOT/'project-state/discovery/inventory-legacy-relationship-hardening-2026-09-26.json').read_text(encoding='utf-8-sig'))
        resolved={r['id'] for r in second['resolved_records']};hardened=set(legacy['changed_ids'])
        assert after.keys()==before.keys() and not resolved&hardened
        assert {i for i in before if before[i]!=after[i]}==resolved|hardened
        assert all(before[i]['status']=='pending review' for i in resolved)
        for i in hardened:
            assert {k for k in after[i] if after[i][k]!=before[i].get(k)}<={'processing_notes','cited_successors','updated_at'}
            assert after[i]['status']==before[i]['status']
        # The second campaign's dedicated regression validates the live 700
        # transitions and archive delta. Preserve every earlier exact assertion
        # by handing it the immutable owner-reviewed first-campaign closeout.
        current=snapshot
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
