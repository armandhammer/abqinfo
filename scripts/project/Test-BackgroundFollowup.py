"""Independent exact-population, untouched-owner and archive/public-byte audit."""
import collections,gzip,hashlib,json,subprocess
from BackgroundFollowup import ROOT,F,load,digest
a=load(F/'authorization.json')
prior={r['id']:r for r in json.loads(subprocess.check_output(['git','show',a['baseline_commit']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))['candidates']}
inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
assert rows.keys()==prior.keys()
assert a['baseline_row_digests']=={i:digest(r) for i,r in prior.items()}
assert set(a['followup_ids'])=={r['id'] for r in load(F/'baseline-followup-queue.json')['records']} and len(a['followup_ids'])==55
assert set(a['approved_ids'])=={i for i,r in prior.items() if r['status']=='approved for addition'} and len(a['approved_ids'])==64
assert set(a['allowed_ids'])==set(a['approved_ids'])|set(a['followup_ids'])
assert {i for i,r in rows.items() if r!=prior[i]}<=set(a['allowed_ids'])
owners={i for i,r in prior.items() if r['status']=='requires human review'}
assert len(owners)==11 and all(rows[i]==prior[i] for i in owners)
queue=load(ROOT/'project-state/discovery/consolidated-human-review-queue.json')
assert queue['packages']==load(F/'owner-packages-baseline.json') and queue['package_count']==4 and queue['record_count']==11
assert load(ROOT/'project-state/discovery/mission-scope-borderline-human-review-queue.json')['unresolved_count']==1
for i in a['allowed_ids']:
 r,p=rows[i],prior[i]
 for field in ['source_url','direct_file_url','discovery_path','cited_predecessors','cited_successors']:
  assert r.get(field)==p.get(field),(i,field)
 assert set(p['processing_notes'])<=set(r['processing_notes']),i
 if p.get('checksum_sha256'):assert (r['checksum_sha256'],r['size_bytes'])==(p['checksum_sha256'],p['size_bytes']),i
 if r!=p and r['status'] in ['approved for addition','placement assigned']:
  assert r['scope_assessment']['final_scope_decision']=='passes_both_gates'
  if r.get('size_bytes'):assert r['quality_assessment']['visual_inspection_completed'] and r['quality_assessment']['reviewed_document_content']
decisions={r['id']:r for r in load(F/'decisions.json')['records']}
assert set(decisions)==set(a['followup_ids'])|{'src-06d0fc4cd0abdef6','src-070a763aa9701f86','src-51fb6dc80b316253'}
work=load(ROOT/'project-state/discovery/codex-human-review-followup-queue.json')
assert work['record_count']==len(work['records'])==39 and work['resolved_count']==16
assert {r['id'] for r in work['records']}=={i for i in a['followup_ids'] if rows[i]['status']=='pending review'}
for r in work['records']:
 assert r['required_evidence'] and r['research_authorized'] and not r['owner_decision_required']
 assert decisions[r['id']]['outcome']=='unresolved_evidence_prerequisite'
old=load(F/'r2-baseline.json');final=load(F/'r2-final.json');current=load(ROOT/'project-state/r2-inventory.json')
oldobjects={o['key']:o for o in old['objects']};objects={o['key']:o for o in final['objects']}
assert (len(oldobjects),old['total_bytes'])==(1588,10670960837)
for k,o in oldobjects.items():assert (objects[k]['size_bytes'],objects[k]['etag'])==(o['size_bytes'],o['etag']),k
assert current['objects']==final['objects'] and current['total_bytes']==final['total_bytes']
receipts=load(F/'archive-receipts.json');plan=load(F/'archive-plan.json')
assert len(receipts)==len(plan['items'])==16 and {r['key'] for r in receipts}==objects.keys()-oldobjects.keys()
assert len({r['id'] for r in receipts})==16 and len({k.casefold() for k in objects})==len(objects)
assert sum(r['size_bytes'] for r in receipts)==final['total_bytes']-old['total_bytes']==14454680
assert final['total_bytes']==sum(o['size_bytes'] for o in objects.values())==10685415517<=a['maximum_storage_bytes']==13000000000
assert final['object_count']==len(objects)==1604
for r in receipts:
 row=rows[r['id']];v=r['public_verification'];item=next(x for x in plan['items'] if x['id']==r['id'])
 assert r['key_was_absent'] and r['state']=='inventory_reconciled' and v['byte_identical']
 assert (v['size_bytes'],v['checksum_sha256'])==(r['size_bytes'],r['checksum_sha256'])==(row['size_bytes'],row['checksum_sha256'])==(item['size_bytes'],item['sha256'])
 assert 0<r['size_bytes']<=a['maximum_object_bytes']==150000000 and objects[r['key']]['etag']==r['etag']
 assert row['r2_key']==r['key'] and row['status']=='placement assigned'
 p=ROOT/item['source_path'];assert p.stat().st_size==r['size_bytes']
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['checksum_sha256']
 assert any(x.get('sha256')==r['checksum_sha256'] and x.get('size_bytes')==r['size_bytes'] and x.get('http_status')==200 and not x.get('truncated') and x['url']==item['source_url'] for x in load(F/'retrievals.json')['records'])
approved={i for i,r in rows.items() if r['status']=='approved for addition'}
assert all(not rows[i].get('size_bytes') or rows[i]['size_bytes']>150000000 for i in approved)
assert rows['src-1f9cf39555e7be6f']==prior['src-1f9cf39555e7be6f']
assert 'Early Head Start' in rows['src-070a763aa9701f86']['title']
assert 'unique personnel' in rows['src-51fb6dc80b316253']['description']
counts=collections.Counter(r['status'] for r in rows.values());assert inv['counts']=={s:counts[s] for s in inv['allowed_statuses']}
assert load(ROOT/'project-state/checkpoint.json')['counts_by_status']==inv['counts']
q=load(ROOT/load(ROOT/'project-state/ordinary-queue-current.json')['artifact']);pending={i for i,r in rows.items() if r['status']=='pending review'}
assert set(q['pending_ids'])==pending and q['pending_review_count']==len(pending)==372
assert set(q['source_or_structural_blocked_pending_ids'])<=pending and q['source_or_structural_blocked_pending_count']==42
assert {r['id'] for r in work['records']}<=set(q['source_or_structural_blocked_pending_ids'])
assert {r['id'] for r in q['newly_approved_backlog']}==approved
gated=set(q['gated_pending_ids']);blocked=set(q['source_or_structural_blocked_pending_ids']);ungated=set(q['ungated_pending_ids'])
assert not gated&blocked and not gated&ungated and not blocked&ungated and gated|blocked|ungated==pending
assert (len(gated),len(blocked),len(ungated))==(321,42,9)
assert not q['actionable_ungated_pending_ids'] and q['genuinely_actionable_ungated_pending_count']==0
link_bytes=(F/'source-links.json.gz').read_bytes();links=json.loads(gzip.decompress(link_bytes))
for r in load(F/'retrievals.json')['records']:
 if r.get('links_artifact'):
  assert r['links_artifact_sha256']==hashlib.sha256(link_bytes).hexdigest() and r['link_count']==len(links[r['url']])
assert not subprocess.check_output(['git','diff',a['baseline_commit'],'--name-only','--','content','layouts','assets','static','hugo.toml'],cwd=ROOT).strip()
assert subprocess.check_output(['git','rev-parse','HEAD:content'],cwd=ROOT,text=True).strip()==a['content_tree']
print('PASS: exact 55 follow-ups; 16 resolved, 39 factual prerequisites; four owner packages unchanged; 16 exact archives, 14454680 added bytes; unrelated rows and visible content preserved.')
