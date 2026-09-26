#!/usr/bin/env python3
"""Save complete validation evidence before recording a passed campaign stage."""
import hashlib, msvcrt, runpy, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context,now=(c[k] for k in ['ROOT','load','save','rel','context','now'])
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 path,d=context();attempt=len(d.get('validation_history',[]))+1;log=path.parent/f'full-validation-{attempt:03d}.log';started=now()
 command=['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Invoke-ProjectValidation.ps1']
 with log.open('wb') as output:r=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
 diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True)
 visible=subprocess.check_output(['git','diff',d['baseline_commit'],'--name-only','--','content'],cwd=ROOT).strip()
 receipt=dict(started_at=started,completed_at=now(),command=command,exit_code=r.returncode,git_diff_check_exit_code=diff.returncode,content_tree_unchanged=not bool(visible),log_artifact=rel(log),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),state='passed' if r.returncode==0 and diff.returncode==0 and not visible else 'failed')
 save(path.parent/f'validation-{attempt:03d}.json',receipt);save(path.parent/'validation.json',receipt);d.setdefault('validation_history',[]).append(receipt);d['validation']=receipt;save(path,d)
 print(receipt)
 print(log.read_text(encoding='utf-8',errors='replace')[-2500:])
 if receipt['state']!='passed':sys.exit(1)
