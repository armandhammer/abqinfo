#!/usr/bin/env python3
"""Recompute exact queue/actionability and archive accounting at quiescence."""
import argparse, collections, hashlib, json, runpy, subprocess
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,STATE,load,save,rel,context,now,digest=(c[k] for k in ['ROOT','STATE','load','save','rel','context','now','digest'])
p=argparse.ArgumentParser();p.add_argument('--live',required=True);a=p.parse_args()
path,d=context();s=load(ROOT/d['selection_artifact']);before=load(ROOT/d['source_queue_artifact'])
import msvcrt
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 inv=load(STATE/'master-inventory.json');rows={r['id']:r for r in inv['candidates']}
 live=load(ROOT/a.live);saved=load(STATE/'r2-inventory.json')
 identity=lambda x:{o['key']:(o['size_bytes'],o['etag']) for o in x['objects']}
 assert identity(live)==identity(saved)
 baseline=load(ROOT/d['baseline_r2_artifact']);old=identity(baseline);objects=identity(live)
 assert all(objects[k]==v for k,v in old.items())
 assert live['total_bytes']==sum(o['size_bytes'] for o in live['objects'])<=d['project_storage_limit_bytes']
 archives={r['key']:r for r in d['archive_objects']};assert len(archives)==len(d['archive_objects'])
 assert objects.keys()-old.keys()==archives.keys()
 assert live['total_bytes']==baseline['total_bytes']+sum(r['size_bytes'] for r in archives.values())
 records={r['id']:r for f in s['candidate_families'] for r in load(ROOT/f['evidence_artifact'])['records']}
 archive_paths=[f['evidence_artifact'] for f in s['candidate_families']]+d['archive_family_artifacts']
 archive_records=[dict(r,evidence_artifact=p) for p in archive_paths for r in load(ROOT/p)['records']]
 deferrals=[]
 for r in archive_records:
  if r.get('review_complete') and r['disposition']=='approved for addition':
   if r.get('archive_complete'):
    assert r['r2_key'] in archives and rows[r['id']]['status']=='placement assigned'
    v=r['public_verification'];qa=r['fresh_source_qa'];assert v['byte_identical'] and (v['size_bytes'],v['checksum_sha256'])==(qa['size_bytes'],qa['checksum_sha256'])
   else:
    assert r.get('archive_deferred_reason') and (r['fresh_source_qa']['size_bytes']>d['maximum_object_bytes'] or live['total_bytes']+r['fresh_source_qa']['size_bytes']>d['project_storage_limit_bytes']),'Eligible archive unfinished'
    deferrals.append(dict(id=r['id'],reason=r['archive_deferred_reason'],size_bytes=r['fresh_source_qa']['size_bytes'],preparation_complete=True,evidence_artifact=r['evidence_artifact'],title=r.get('reviewed_title'),prepared_key=r['r2_key']))
 pending={i for i,r in rows.items() if r['status']=='pending review'}
 gates={i:why for i,why in before['gated_pending_ids'].items() if i in pending}
 blocked={i:why for i,why in before['source_or_structural_blocked_pending_ids'].items() if i in pending}
 for r in d['recovery_records']:
  assert r['id'] in blocked and r['inventory_unchanged'];blocked[r['id']]=r['reason']
 ungated=pending-gates.keys()-blocked.keys();deferred={r['id']:r for r in d['deferred_records']}
 assert ungated==deferred.keys(),'Ungated queue still has unreviewed actionable work'
 assert not (set(gates)&set(blocked) or ungated&set(gates) or ungated&set(blocked))
 assert pending==set(gates)|set(blocked)|ungated
 families=[]
 for f in s['candidate_families']:
  ids=sorted(set(f['candidate_ids'])&ungated)
  if ids:families.append(dict(f,candidate_ids=ids,candidate_count=len(ids),saved_preparation_artifact=f['evidence_artifact'],selection_is_not_a_disposition=True))
 queue=dict(schema_version=1,artifact_type='ordinary_queue_post_background_campaign',recorded_at=now(),campaign_artifact=rel(path),selection_artifact=d['selection_artifact'],pending_review_count=len(pending),pending_ids=sorted(pending),gated_pending_count=len(gates),gated_pending_ids=gates,source_or_structural_blocked_pending_count=len(blocked),source_or_structural_blocked_pending_ids=blocked,ungated_pending_count=len(ungated),ungated_pending_ids=sorted(ungated),genuinely_actionable_ungated_pending_count=0,actionable_ungated_pending_ids=[],unresolved_ungated_prerequisites=list(deferred.values()),actionability_basis='All remaining ungated records are meaningful live applications or shell-identity relationships requiring rendered browser/content or successor verification. No browser surface was available. These are unresolved prerequisites, not exclusions or editorial human gates; reassess if browser availability changes.',mission_borderline_queue_size=load(STATE/'discovery/mission-scope-borderline-human-review-queue.json')['unresolved_count'],background_family_groups=families,next_actionable_background_families=[],next_actionable_background_family=None,existing_ia_blocked_approved_ids=before['existing_ia_blocked_approved_ids'],newly_approved_backlog=deferrals,visitor_visible_content_changed=False)
 qpath=path.parent/'next-ordinary-queue.json';save(qpath,queue);save(STATE/'ordinary-queue-current.json',dict(schema_version=1,artifact=rel(qpath),campaign= d['campaign_id']))
 outcomes=dict(collections.Counter(r['decision'] for r in d['resolved_records']))
 d.update(state='background_work_complete_validation_and_integration_pending',review_completed_at=now(),accounting=dict(resolved_records=len(d['resolved_records']),outcomes=outcomes,archive_objects_added=len(archives),archive_bytes_added=sum(r['size_bytes'] for r in archives.values()),prior_approved_archives=sum(r['id'] not in records for r in archives.values()),newly_approved_archives=sum(r['id'] in records for r in archives.values()),existing_source_blockers=len(blocked),unresolved_live_service_prerequisites=len(ungated),currently_actionable_ungated_pending=0,new_human_review_cases=0,new_scope_borderlines=0),archive_deferrals=deferrals,latest_r2=dict(object_count=live['object_count'],total_bytes=live['total_bytes'],headroom_bytes=d['project_storage_limit_bytes']-live['total_bytes']),final_live_listing_artifact=a.live,next_queue_artifact=rel(qpath),final_inventory_counts=inv['counts'],zero_content_change=True,live_site_published=False,stop_reason=f'Actionable ordinary queue exhausted; {len(ungated)} concrete ungated prerequisites and {len(blocked)} source/structural blockers preserved.',validation=dict(state='pending_full_validation_and_integration'))
 amendments=[]
 for p,oldsha in d['governing_artifact_hashes'].items():
  current=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
  if current!=oldsha:amendments.append(dict(path=p,initial_sha256=oldsha,current_sha256=current,reason='Owner-authorized framework hardening and explicit profile invocation authority during current implementation.'))
 d['framework_amendments']=amendments
 save(path,d)
 subprocess.run(['python','-B','scripts/project/BackgroundCampaign.py','checkpoint'],cwd=ROOT,check=True)
 print(json.dumps(dict(accounting=d['accounting'],queue={k:queue[k] for k in ['pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count','ungated_pending_count','genuinely_actionable_ungated_pending_count']},r2=d['latest_r2'])))
