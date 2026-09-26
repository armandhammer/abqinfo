#!/usr/bin/env python3
"""Durable single-worker campaign coordinator. No inferred editorial decisions."""
import argparse, hashlib, json, runpy, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'project-state'
ACTIVE=STATE/'active-campaign.json'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def context():
    pointer=load(ACTIVE);path=ROOT/pointer['campaign_artifact'];return path,load(path)
def start(a):
    profile=load(STATE/'campaign-profiles'/f'{a.profile}.json')
    if ACTIVE.exists():assert context()[1]['state']=='complete_background_campaign','Resume the unfinished campaign; never reset it'
    assert not git('status','--porcelain','--','content'),'Visible changes prohibit background launch'
    queue=load(ROOT/a.queue);inv=load(STATE/'master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    pending={i for i,r in rows.items() if r['status']=='pending review'}
    assert pending==set(queue['pending_ids']),'Queue stale: regenerate before launch'
    assert pending==set(queue['gated_pending_ids'])|set(queue['source_or_structural_blocked_pending_ids'])|set(queue['ungated_pending_ids'])
    folder=STATE/'campaigns'/a.id;assert not folder.exists(),'Campaign id already exists; resume'
    folder.mkdir(parents=True)
    old=load(STATE/'discovery/ordinary-queue-second-large-campaign-selection-2026-09-26.json')
    qrows={q['id']:q for q in old['all_pending_records']}
    candidates=[];families=[]
    for order,f in enumerate(queue['background_family_groups'],1):
        ff=dict(f);ff.update(order=order,boundary='Complete saved family; split by substantive function before decisions.',evidence_artifact=rel(folder/(f['family_id']+'.json')))
        families.append(ff)
        records=[]
        if f.get('saved_preparation_artifact'):records=load(ROOT/f['saved_preparation_artifact'])['records']
        records=[r for r in records if r['id'] in f['candidate_ids']]
        for r in records:assert not r.get('review_complete'),'Completed record cannot be reopened'
        save(ROOT/ff['evidence_artifact'],dict(schema_version=1,family_id=f['family_id'],family=f['family'],scope_ids=f['candidate_ids'],records=records,visitor_visible_content_changed=False,state='saved_evidence_reused_pending_review'))
        for i in f['candidate_ids']:
            q=dict(qrows[i]);q.update(gated=False,baseline_row_sha256=digest(rows[i]));candidates.append(q)
    selection=dict(schema_version=1,all_pending_records=candidates,candidate_families=families,gated_pending_ids=queue['gated_pending_ids'],structural_blocked_ids=list(queue['source_or_structural_blocked_pending_ids']),starting_population=sorted(pending),baseline_row_digests={i:digest(r) for i,r in rows.items()},visitor_visible_content_changed=False)
    save(folder/'selection.json',selection)
    baseline=load(ROOT/a.live);saved=load(STATE/'r2-inventory.json')
    identity=lambda d:{o['key']:(o['size_bytes'],o['etag']) for o in d['objects']}
    assert identity(baseline)==identity(saved),'Live/saved drift requires reconciliation before campaign launch'
    save(folder/'r2-baseline.json',baseline)
    policy=load(STATE/'r2-storage-policy.json')
    campaign=dict(schema_version=1,artifact_type='autonomous_background_campaign',campaign_id=a.id,profile=a.profile,started_at=now(),state='review_and_archive_in_progress',baseline_commit=git('rev-parse','HEAD'),content_tree_baseline=git('rev-parse','HEAD:content'),baseline_inventory_counts=inv['counts'],baseline_r2=dict(object_count=baseline['object_count'],total_bytes=baseline['total_bytes']),baseline_r2_artifact=rel(folder/'r2-baseline.json'),selection_artifact=rel(folder/'selection.json'),source_queue_artifact=a.queue,project_storage_limit_bytes=policy['maximum_projected_r2_bytes'],maximum_object_bytes=profile['maximum_object_bytes'],authorization=profile['authorization'],families_processed=[],resolved_records=[],archive_objects=[],archive_family_artifacts=[],deferred_records=[],recovery_records=[],integration={},visitor_visible_content_changed=False,governing_artifact_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['AGENTS.md','project-state/campaign-workflow.md',f'project-state/campaign-profiles/{a.profile}.json','project-state/r2-storage-policy.json']})
    save(folder/'campaign.json',campaign);save(ACTIVE,dict(schema_version=1,campaign_id=a.id,profile=a.profile,campaign_artifact=rel(folder/'campaign.json'),workflow='project-state/campaign-workflow.md'))
    print(json.dumps(dict(campaign=a.id,pending=len(pending),ungated=len(candidates),families=len(families))))
def review_module(d):
    m=runpy.run_path(str(ROOT/'scripts/project/SecondLargeOrdinaryCampaign.py'))
    g=m['prepare'].__globals__;folder=(ROOT/load(ACTIVE)['campaign_artifact']).parent
    g.update(ART=folder/'campaign.json',SEL=folder/'selection.json',STAGE=ROOT/'research/staging'/d['campaign_id'],QA=ROOT/'tmp'/d['campaign_id'],DATE=d['campaign_id'])
    g['family_path']=lambda f:ROOT/f['evidence_artifact']
    # Existing explicitly-reviewed mutation engine; no decision is inferred here.
    return m
def checkpoint(a):
    path,d=context();d['last_checkpoint_at']=now();save(path,d)
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Write-ProjectCheckpoint.ps1','-CompletedRange',f"Active background campaign {d['campaign_id']}: {len(d['resolved_records'])} resolutions; {len(d['archive_objects'])} exact archives",'-ResumeCommand','Read AGENTS.md, CURRENT.md, campaign-workflow.md and active-campaign.json; resume saved campaign without resetting or repeating completed families.'],cwd=ROOT,check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['start','status','prepare','show','review','apply','checkpoint']);p.add_argument('--profile',default='ordinary-review-large');p.add_argument('--id');p.add_argument('--queue');p.add_argument('--live');p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=999);p.add_argument('--workers',type=int,default=4);p.add_argument('--text',type=int,default=0);p.add_argument('--images',action='store_true');p.add_argument('--decisions');a=p.parse_args()
    if a.operation=='start':start(a);return
    path,d=context()
    if a.operation=='status':print(json.dumps(d,indent=2));return
    if a.operation=='checkpoint':checkpoint(a);return
    assert d['state']!='complete_background_campaign','Completed campaign is sealed'
    m=review_module(d);m[a.operation](a)
    if a.operation=='apply':checkpoint(a)
if __name__=='__main__':main()
