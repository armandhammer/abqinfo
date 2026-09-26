#!/usr/bin/env python3
"""Atomic explicit update batch; reuse the repository's exact mission-scope gate."""
import argparse,collections,copy,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--requests',required=True);p.add_argument('--inventory',default='project-state/master-inventory.json');a=p.parse_args()
path=ROOT/a.inventory;original=path.read_bytes();inventory=json.loads(original.decode('utf-8-sig'));rows={r['id']:r for r in inventory['candidates']}
request=json.loads((ROOT/a.requests).read_text(encoding='utf-8-sig'));request=request.get('approved_updates',request) if isinstance(request,dict) else request
assert len({r['id'] for r in request})==len(request)
now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');validation=[]
for x in request:
 row=rows[x['id']];before=copy.deepcopy(row)
 for key,value in x['changes'].items():
  assert key in row or key in ['scope_assessment','review_reason'], 'Unknown field '+key
  row[key]=value
 if row!=before:
  row['updated_at']=now
  if 'description' in x['changes']:row['description_word_count']=len((row['description'] or '').split())
 validation.append({'candidate':row})
receipt=ROOT/'tmp/candidate-batch-scope-requests.json';receipt.write_text(json.dumps(validation,ensure_ascii=False),encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/project/Test-CandidateBatchScope.ps1'),'-RequestsPath',str(receipt)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
counts=collections.Counter(r['status'] for r in rows.values());inventory['counts']={s:counts[s] for s in inventory['allowed_statuses']}
eligible=[r['id'] for r in rows.values() if r['status'] in ['pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'] or r['status']=='implemented' and r.get('validation_status')!='passed']
inventory['next_pending_id']=min(eligible) if eligible else None;inventory['generated_at']=now
assert path.read_bytes()==original,'Inventory changed during preflight; retry without overwriting'
temporary=path.with_name(path.name+'.batch-update.tmp');temporary.write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(path)
print('Applied',len(request),'explicit updates atomically; existing mission-scope policy passed.')
