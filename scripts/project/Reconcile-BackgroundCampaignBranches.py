#!/usr/bin/env python3
"""Non-destructive background branch reconciliation with durable final receipts."""
import json, msvcrt, runpy, subprocess, sys
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context,now,git=(c[k] for k in ['ROOT','load','save','rel','context','now','git'])
assert git('branch','--show-current')=='chatgpt/planning-snapshot','Run from the framework planning checkout'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Commit coherent tracked work before reconciliation'
def action(label,*command):
 subprocess.run([sys.executable,'-B','scripts/project/Invoke-BackgroundCampaignExternal.py','--label',label,'--',*command],cwd=ROOT,check=True)
action('reconcile-refresh-origin','git','fetch','origin')
action('reconcile-planning-fast-forward','git','merge','--ff-only','origin/main')
# A normal local fetch rejects non-fast-forward updates, without checking out an
# older main that lacks the framework and active pointer. No plus/force options.
action('reconcile-local-main-fast-forward','git','fetch','.','origin/main:refs/heads/main')
action('reconcile-remote-planning-fast-forward','git','push','origin','chatgpt/planning-snapshot')
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 path,d=context();refs={r:git('rev-parse',r) for r in ['HEAD','main','chatgpt/planning-snapshot','origin/main','origin/chatgpt/planning-snapshot']}
 live={line.split()[1]:line.split()[0] for line in git('ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot').splitlines()}
 assert len(set(refs.values()))==1 and set(live.values())==set(refs.values()),'Branches not synchronized; preserve state and investigate'
 assert git('rev-parse','HEAD:content')==d['content_tree_baseline'],'Content tree changed'
 receipt=dict(schema_version=1,campaign_id=d['campaign_id'],verified_at=now(),state='branches_reconciled',refs=refs,live_remote_refs=live,content_tree_sha=git('rev-parse','HEAD:content'),tracked_worktree_clean=not bool(git('status','--porcelain','--untracked-files=no')))
 output=ROOT/'project-state/campaign-runtime'/d['campaign_id']/'final-integration.json';save(output,receipt);print(json.dumps(receipt))
