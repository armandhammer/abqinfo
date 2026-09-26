#!/usr/bin/env python3
"""Carry eligible prepared approvals forward without reopening closed decisions."""
import copy, hashlib, runpy
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context=(c[k] for k in ['ROOT','load','save','rel','context'])
path,d=context();folder=path.parent
old=load(ROOT/d['source_queue_artifact'])
rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
groups={}
for x in old['newly_approved_backlog']:
 row=rows[x['id']]
 if row['status']!='approved for addition':continue
 r=copy.deepcopy(next(r for r in load(ROOT/x['evidence_artifact'])['records'] if r['id']==x['id']))
 assert r['review_complete'] and row['scope_assessment']['final_scope_decision']=='passes_both_gates'
 qa=r['fresh_source_qa'];p=ROOT/qa['staged_path']
 assert p.stat().st_size==qa['size_bytes'] and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==qa['checksum_sha256']
 assert qa['source_exact_verified'] and qa['representative_visual_qa']=='passed_agent_inspection_opening_middle_ending'
 r['prior_review_artifact']=x['evidence_artifact'];r.pop('archive_deferred_reason',None)
 key=Path(x['evidence_artifact']).stem;groups.setdefault(key,[]).append(r)
for key,records in groups.items():
 p=folder/('approved-'+key+'.json')
 if p.exists():
  if rel(p) not in d['archive_family_artifacts']:d['archive_family_artifacts'].append(rel(p))
  continue
 save(p,dict(schema_version=1,family_id='approved-'+key,family='Previously approved unchanged originals; '+key,scope_ids=[r['id'] for r in records],records=records,visitor_visible_content_changed=False))
 d['archive_family_artifacts'].append(rel(p))
save(path,d)
print('Carried forward',sum(len(v) for v in groups.values()),'prepared approvals;',sum(r['fresh_source_qa']['size_bytes'] for v in groups.values() for r in v if r['fresh_source_qa']['size_bytes']<=150000000),'eligible bytes')
