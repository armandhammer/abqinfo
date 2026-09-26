"""Reconcile complete saved/live R2, derive family evidence and remaining backlog."""
import json,hashlib,subprocess
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DISC=ROOT/'project-state/discovery'
ART=DISC/'approved-backlog-background-archive-campaign-2026-09-26.json'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def stamp():return datetime.now(timezone.utc).isoformat()
def digest(objects):
    return hashlib.sha256('\n'.join(f"{o['key']}\t{o['size_bytes']}\t{o['etag']}" for o in sorted(objects,key=lambda o:o['key'])).encode()).hexdigest()
def main():
    d=load(ART);inv=load(ROOT/'project-state/master-inventory.json');baseline=load(ROOT/d['baseline_r2_artifact']);live=load(ROOT/'tmp/background-campaign-final-live-2026-09-26.json');saved=load(ROOT/'project-state/r2-inventory.json')
    done=[r for r in d['records']+d['generated_packages'] if r['outcome']=='archive_complete']
    before={o['key']:o for o in baseline['objects']};after={o['key']:o for o in live['objects']}
    assert len(done)==30 and sum(r['size_bytes'] for r in done)==29783028
    assert all(r['public_verification']['byte_identical'] for r in done)
    assert set(after)-set(before)=={r['r2_key'] for r in done}
    for key,old in before.items():assert all(after[key][f]==old[f] for f in ('key','size_bytes','etag'))
    assert live['object_count']==1279 and live['total_bytes']==9370314196
    for r in done:assert after[r['r2_key']]['size_bytes']==r['size_bytes'] and after[r['r2_key']]['etag']==r['r2_etag']
    assert saved['objects']==live['objects']
    assert not subprocess.check_output(['git','diff','--name-only',d['baseline_git_sha'],'--','content'],cwd=ROOT).strip()
    final=DISC/'approved-backlog-background-archive-campaign-r2-final-2026-09-26.json';write(final,live)
    d['final_live_listing_artifact']=final.relative_to(ROOT).as_posix()
    d['accounting']={'baseline_objects':1249,'baseline_bytes':9340531168,'final_objects':1279,'final_bytes':9370314196,'added_objects':30,'added_bytes':29783028,'pre_existing_objects_unchanged':True,'pre_existing_manifest_sha256_before':digest(baseline['objects']),'pre_existing_manifest_sha256_after':digest([after[k] for k in before]),'saved_live_key_size_etag_match':True,'unexpected_additions':[],'deletions':[],'overwrites':[]}
    for r in d['records']:
        if r['family']=='Six captured final City enactments':
            for comparison in r['canonical_comparisons']:
                comparison['text_similarity_is_substantive_evidence']=False
                comparison['limitation']='Final enacted containers are scanned; text-layer similarity is not a reliable substantive comparison.'
                comparison['visual_canonical_finding']='Saved legislative capture identifies signed numbered final enactment; representative rendered legal pages confirm enacted number and/or signatures. Held substitute is an earlier bill form with blank enactment line. Retain final original container; no existing identical authoritative final original was found.'
        if r['id']=='src-c5ed372e33966029':
            r['source_finality_caveat']='City code-enforcement source preserves O-17-39 ordinance text with blank enactment-number line; archival does not infer a signed final enactment or silently change the approved identity.'
        if not r['r2_key']:
            r['unuploaded_reason']='No accepted existing canonical public home or stable R2 namespace independent of new information architecture. Exact unchanged source, structural/render/visual QA and collision analysis complete; remains approved for addition.'
    groups=defaultdict(list)
    for r in d['records']+d['generated_packages']:groups[r['family']].append(r)
    d['family_evidence_artifacts']=[]
    for i,(family,records) in enumerate(groups.items(),1):
        p=DISC/f'approved-background-archive-family-{i:02d}-2026-09-26.json'
        evidence={'artifact_type':'background_archive_family_result','recorded_at':stamp(),'family':family,'campaign_artifact':ART.relative_to(ROOT).as_posix(),'record_ids':[r['id'] for r in records],'records':[{k:r.get(k) for k in ('id','title','classification','governing_decision_artifact','component_manifest','direct_source_url','source_GET','staged_path','size_bytes','expected_sha256','page_count','container_type','r2_key','r2_etag','upload_action','public_verification','outcome','inventory_status_after','unuploaded_reason','human_review_requirement','blocker','source_finality_caveat')} for r in records],'visitor_visible_content_changed':False,'content_publication_deferred':True}
        write(p,evidence);d['family_evidence_artifacts'].append(p.relative_to(ROOT).as_posix())
    counts=Counter(r['status'] for r in inv['candidates']);approved=[r for r in inv['candidates'] if r['status']=='approved for addition']
    assert len(approved)==3 and counts['placement assigned']==38
    d['summary']={'reviewed_current_approved':27,'approved_units_processed':12,'generated_package_units_processed':2,'exact_source_preparations':27,'pdf_original_pages_rendered':sum(r.get('page_count',0) for r in d['records']),'original_XLSX_preserved':1,'duplicates_reconciled':0,'objects_uploaded':30,'bytes_uploaded':29783028,'exact_public_byte_verifications_passed':30,'records_moved_to_placement_assigned':24,'remaining_approved':3,'prepared_unuploaded_ids':[r['id'] for r in d['records'] if not r['r2_key']],'human_review_deferred_generated_ids':['generated-dpm-2018'],'capacity_deferred':[],'source_drift_deferred':[],'capital_spending_originals_archived':4,'capital_spending_generated_archived':2,'dpm_generated_archived_years':[2014,2015,2016,2017],'dpm_2018':'deferred_human_review_conflicting_agenda_evidence'}
    priority={'artifact_type':'pre_implementation_backlog_after_background_archive_campaign','recorded_at':stamp(),'supersedes_resume_selection':'project-state/discovery/approved-inventory-backlog-prioritization-post-later-ms4-2026-09-25.json','campaign_artifact':ART.relative_to(ROOT).as_posix(),'counts':inv['counts'],'approved_record_ids':[r['id'] for r in approved],'archive_prepared_only':[{'id':r['id'],'title':r['title'],'reason':'unresolved canonical public home and archive namespace; requires owner IA decision'} for r in approved],'newly_archive_complete_placement_assigned_ids':[r['id'] for r in d['records'] if r.get('inventory_reconciled')],'existing_planning_archive_complete_placement_assigned_count':12,'legacy_placement_assigned_count':2,'generated_packages':[{'id':r['id'],'outcome':r['outcome'],'reason':r.get('human_review_requirement')} for r in d['generated_packages']],'substantive_ungated_background_work_remaining_in_campaign':False,'recommended_next_background_only_task':'No ungated campaign unit remains. Owner must resolve DPM 2018 agenda conflict or authorize an archive namespace/IA for three prepared originals; existing content implementation remains deferred. Other Capital Spending build/archive packages are outside this campaign and need separate scope authorization.','recommended_model_if_decision_authorized':'GPT-5.6 Terra, High for conflicting DPM evidence; Medium for namespace decision implementation','visitor_visible_content_changed':False}
    p=DISC/'approved-inventory-backlog-status-post-background-archive-campaign-2026-09-26.json';write(p,priority);d['remaining_backlog_artifact']=p.relative_to(ROOT).as_posix()
    d['state']='complete_background_campaign';d['completed_at']=stamp();write(ART,d)
    print(json.dumps(d['summary']))
if __name__=='__main__':main()
