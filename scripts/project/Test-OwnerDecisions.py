"""Audit exact owner scope, preserved provenance, queues and archive deltas."""
from OwnerDecisions import *
a=load(F/'authorization.json');baseline={r['id']:r for r in json.loads(subprocess.check_output(['git','show',a['baseline_commit']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))['candidates']};inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};allowed=set(a['allowed_ids'])
assert a['baseline_row_digests']=={i:digest(r) for i,r in baseline.items()}
assert rows.keys()==baseline.keys() and {i for i in rows if rows[i]!=baseline[i]}==allowed and len(allowed)==11
packages=load(F/'baseline-owner-packages.json');decisions=load(F/'decisions.json');assert {x['id'] for x in decisions}==allowed
for p in packages:
 for i in p['affected_record_ids']:
  r,b=rows[i],baseline[i];retained=p['package_id'] in ['art-advocacy-primary-sources','dpm-historical-drafts']
  assert r['status']==('placement assigned' if retained else 'excluded'),i
  assert r['review_reason'] is None and a['decisions'][p['package_id']] in ' '.join(r['processing_notes'])
  assert set(b['processing_notes'])<=set(r['processing_notes'])
  for k in ['source_url','direct_file_url','discovery_path','implementation_locations','cited_predecessors','cited_successors']:assert r.get(k)==b.get(k),(i,k)
  if b.get('checksum_sha256'):assert (r['checksum_sha256'],r['size_bytes'])==(b['checksum_sha256'],b['size_bytes'])
  if retained:
   assert r['scope_assessment']['final_scope_decision']=='passes_both_gates' and r['quality_assessment']['visual_inspection_completed'] and r['r2_key']
  else:assert r['exclusion_reason'].startswith('Owner editorial exclusion:')
assert not any(r['status']=='requires human review' for r in rows.values())
queue=load(ROOT/'project-state/discovery/consolidated-human-review-queue.json');assert queue['record_count']==queue['package_count']==0 and queue['packages']==[]
scope=load(ROOT/'project-state/discovery/mission-scope-borderline-human-review-queue.json');assert scope['unresolved_count']==0 and any(r['id']=='src-333e4b4b3970edc1' for r in scope['resolved_records'])
follow=load(ROOT/'project-state/discovery/codex-human-review-followup-queue.json');assert follow==load(F/'baseline-followup-queue.json') and follow['record_count']==39 and all(rows[r['id']]['status']=='pending review' for r in follow['records'])
old=load(F/'r2-baseline.json');final=load(F/'r2-final.json');live=load(ROOT/'project-state/r2-inventory.json');assert live==final
bo={o['key']:o for o in old['objects']};fo={o['key']:o for o in final['objects']};receipts=load(F/'archive-receipts.json');plan=load(F/'archive-plan.json')
assert len(receipts)==len(plan['items'])==6 and fo.keys()-bo.keys()=={r['key'] for r in receipts}
for k,o in bo.items():assert (fo[k]['size_bytes'],fo[k]['etag'])==(o['size_bytes'],o['etag'])
for r in receipts:
 v=r['public_verification'];row=rows[r['id']];assert r['key_was_absent'] and r['state']=='inventory_reconciled' and v['byte_identical'];assert (v['size_bytes'],v['checksum_sha256'])==(row['size_bytes'],row['checksum_sha256'])==(r['size_bytes'],r['checksum_sha256']);assert fo[r['key']]['etag']==r['etag'];assert r['size_bytes']<=150000000
assert sum(r['size_bytes'] for r in receipts)==final['total_bytes']-old['total_bytes']==4522318
assert final['total_bytes']==sum(o['size_bytes'] for o in fo.values())<=13000000000 and final['object_count']==1610
art=load(F/'existing-art-public-verification.json');assert len(art)==3
for x in art:
 r=rows[x['id']];v=x['verification'];assert v['byte_identical'] and (v['size_bytes'],v['checksum_sha256'])==(r['size_bytes'],r['checksum_sha256']) and x['key']==r['r2_key']
cp=load(ROOT/'project-state/checkpoint.json');assert cp['counts_by_status']==inv['counts']
q=load(ROOT/load(ROOT/'project-state/ordinary-queue-current.json')['artifact']);assert set(q['pending_ids'])=={i for i,r in rows.items() if r['status']=='pending review'} and q['pending_review_count']==372
assert not git('diff',a['baseline_commit'],'--name-only','--','content','layouts','assets','static','hugo.toml') and git('rev-parse','HEAD:content')==a['content_tree']
print('PASS: 11 explicit owner dispositions; nine retained, two excluded; six exact archives / 4522318 bytes; zero owner cases; 39 factual prerequisites; unrelated rows/content preserved.')
