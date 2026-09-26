#!/usr/bin/env python3
"""Persist Git/GitHub mutation intents/results without recursive receipt commits."""
import argparse, json, msvcrt, runpy, subprocess, sys
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,context,now=(c[k] for k in ['ROOT','load','save','context','now'])
p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command
if cmd and cmd[0]=='--':cmd=cmd[1:]
assert cmd and cmd[0] in ['git','gh'],'Only explicit Git/GitHub integration commands'
assert not any(x in cmd for x in ['--force','--force-with-lease','reset','clean','delete']),'Destructive reconciliation prohibited'
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 path,d=context();assert d['authorization']['background_only_integration_and_branch_reconciliation']
 assert not subprocess.check_output(['git','diff',d['baseline_commit'],'--name-only','--','content'],cwd=ROOT).strip(),'Visible changes prohibit integration'
 runtime=ROOT/'project-state/campaign-runtime'/d['campaign_id']/'external-action-journal.json'
 journal=load(runtime) if runtime.exists() else dict(schema_version=1,campaign_id=d['campaign_id'],actions=[],authority='Current campaign authorization; tracked workflow and campaign govern these local durable receipts.')
 entry=dict(label=a.label,command=cmd,started_at=now(),state='intent_saved_before_external_mutation');journal['actions'].append(entry);save(runtime,journal)
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 entry.update(completed_at=now(),state='completed' if r.returncode==0 else 'failed_requires_remote_reconciliation',exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
 save(runtime,journal)
 print(r.stdout);print(r.stderr,file=sys.stderr);sys.exit(r.returncode)
