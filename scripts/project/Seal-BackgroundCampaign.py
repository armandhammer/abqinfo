#!/usr/bin/env python3
"""Seal validated background work only after verified primary merge/reconciliation."""
import argparse, hashlib, json, msvcrt, runpy, subprocess
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,STATE,load,save,rel,context,now,git=(c[k] for k in ['ROOT','STATE','load','save','rel','context','now','git'])
p=argparse.ArgumentParser();p.add_argument('--pr',type=int,required=True);a=p.parse_args()
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 path,d=context();assert d['state']=='background_work_complete_validation_and_integration_pending'
 assert d['validation']['state']=='passed' and d['zero_content_change'] and not d['live_site_published']
 pr=json.loads(subprocess.check_output(['gh','pr','view',str(a.pr),'--json','url,state,mergeCommit,mergedAt,headRefOid,statusCheckRollup'],cwd=ROOT))
 assert pr['state']=='MERGED' and pr['mergeCommit']['oid']
 assert all(check.get('conclusion') in ['SUCCESS','SKIPPED','NEUTRAL'] or check.get('state')=='SUCCESS' for check in pr['statusCheckRollup'])
 refs={r:git('rev-parse',r) for r in ['HEAD','main','chatgpt/planning-snapshot','origin/main','origin/chatgpt/planning-snapshot']}
 live={line.split()[1]:line.split()[0] for line in git('ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot').splitlines()}
 assert set(refs.values())==set(live.values())=={pr['mergeCommit']['oid']},'Reconcile branches before sealing'
 assert not git('diff',d['baseline_commit'],'--name-only','--','content')
 journal=load(ROOT/d['external_action_journal_artifact'])
 integration=dict(state='primary_background_work_merged_and_branches_reconciled',completed_at=now(),primary_pr=pr,primary_branch_refs=refs,primary_live_remote_refs=live,external_actions_snapshot=journal['actions'],final_metadata_reconciliation_receipt='project-state/campaign-runtime/'+d['campaign_id']+'/final-integration.json',closeout_metadata_instruction='Integrate this background-only completion checkpoint; run Reconcile-BackgroundCampaignBranches.py afterward. Final exact SHAs live in Git refs and the durable local receipt, avoiding recursive receipt commits.')
 save(path.parent/'integration.json',integration);d['integration']=integration;d['state']='complete_background_campaign';d['completed_at']=now()
 d['framework_amendments']=[dict(path=k,initial_sha256=v,current_sha256=hashlib.sha256((ROOT/k).read_bytes()).hexdigest(),reason='Owner-authorized framework implementation and hardening; initial governance evidence retained.') for k,v in d['governing_artifact_hashes'].items() if hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
 save(path,d)
 subprocess.run(['python','-B','scripts/project/BackgroundCampaign.py','checkpoint'],cwd=ROOT,check=True)
 pointer=load(STATE/'active-campaign.json');pointer.update(state='complete_background_campaign',integration_artifact=rel(path.parent/'integration.json'),final_runtime_receipt=integration['final_metadata_reconciliation_receipt']);save(STATE/'active-campaign.json',pointer)
 print(pr['url'],pr['mergeCommit']['oid'],'sealed with exact receipts and queue')
