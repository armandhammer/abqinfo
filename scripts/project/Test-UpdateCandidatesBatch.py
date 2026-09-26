#!/usr/bin/env python3
"""A failed bulk approval gate must leave every requested row untouched."""
import collections,copy,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
real=load(ROOT/'project-state/master-inventory.json')
base=copy.deepcopy(next(r for r in real['candidates'] if r['id']=='src-b9f68064d83c5038'))
other=copy.deepcopy(next(r for r in real['candidates'] if r['id']=='src-48c77cfd3533626b'))
base['status']='pending review';scope=base.pop('scope_assessment');other['status']='pending review';other.pop('scope_assessment',None)
fixture={'candidates':[base,other],'allowed_statuses':real['allowed_statuses'],'counts':{s:(2 if s=='pending review' else 0) for s in real['allowed_statuses']},'next_pending_id':base['id']}
folder=ROOT/'tmp/second-campaign-batch-regression';folder.mkdir(parents=True,exist_ok=True)
inventory=folder/'inventory.json';requests=folder/'requests.json'
inventory.write_text(json.dumps(fixture),encoding='utf-8');original=inventory.read_bytes()
def run(rows):
 requests.write_text(json.dumps(rows),encoding='utf-8')
 return subprocess.run(['python','-B',str(ROOT/'scripts/project/Update-CandidatesBatch.py'),'--inventory',inventory.relative_to(ROOT).as_posix(),'--requests',requests.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True,text=True)
valid={'id':base['id'],'changes':{'status':'approved for addition','scope_assessment':scope}}
for invalid in [
 {'id':other['id'],'changes':{'status':'approved for addition'}},
 {'id':other['id'],'changes':{'status':'downloaded'}},
 {'id':other['id'],'changes':{'status':'invented status'}},
 {'id':other['id'],'changes':{'invented_field':True}},
]:
 result=run([valid,invalid]);assert result.returncode!=0 and inventory.read_bytes()==original,(result.stdout,result.stderr)
result=run([valid]);assert result.returncode==0,(result.stdout,result.stderr)
actual=load(inventory);rows={r['id']:r for r in actual['candidates']}
assert rows[other['id']]==other and rows[base['id']]['status']=='approved for addition' and rows[base['id']]['scope_assessment']==scope
counts=collections.Counter(r['status'] for r in rows.values());assert actual['counts']=={s:counts[s] for s in actual['allowed_statuses']}
assert actual['counts']['pending review']==actual['counts']['approved for addition']==1
print('PASS: bulk updates preserve atomic no-write on missing mission scope, invalid status and unknown fields; valid scoped approval leaves the protected fixture row untouched.')
