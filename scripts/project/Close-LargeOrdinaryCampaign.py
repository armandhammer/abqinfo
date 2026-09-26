#!/usr/bin/env python3
"""Final live reconciliation, accounting and record-level queue recomputation."""
import collections,json,runpy,subprocess
from datetime import datetime,timezone
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,BASE,SELECTION,CAMPAIGN,load,save=(c[k] for k in ['ROOT','DISC','DATE','BASE','SELECTION','CAMPAIGN','load','save'])

def main():
    d=load(CAMPAIGN);s=load(SELECTION);inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    assert len(d['resolved_records'])==500
    assert len(d['archive_objects'])==sum(r['decision']=='approved for addition' for r in d['resolved_records'])==13,'Finish or accurately account for archive deferrals before closeout'
    baseline=load(ROOT/d['baseline_r2_artifact']);final_path=DISC/f'ordinary-queue-large-campaign-r2-final-{DATE}.json'
    final=load(final_path);old={o['key']:o for o in baseline['objects']};current={o['key']:o for o in final['objects']};added={o['key']:o for o in d['archive_objects']}
    for k,o in old.items():assert k in current and all(current[k][f]==o[f] for f in ['key','size_bytes','etag'])
    assert current.keys()-old.keys()==added.keys()
    assert final['total_bytes']==baseline['total_bytes']+sum(o['size_bytes'] for o in added.values())<=10000000000
    assert load(ROOT/'project-state/r2-inventory.json')['objects']==final['objects']
    evidence=[load(ROOT/f['artifact']) for f in d['families_processed']]
    qa=[r['fresh_source_qa'] for fam in evidence for r in fam['records'] if r.get('review_complete') and r.get('fresh_source_qa')]
    html=[r for fam in evidence for r in fam['records'] if r.get('review_complete') and r['saved_evidence']['content_kind']=='HTML']
    outcomes=collections.Counter(r['decision'] for r in d['resolved_records'])
    d['accounting']=dict(resolved_records=500,families_completed=sum(f['complete'] for f in d['families_processed']),families_attempted=len(d['families_processed']),outcomes=dict(outcomes),new_human_review=0,new_borderlines=0,exact_source_files_reviewed=len(qa),exact_source_bytes_reviewed=sum(q['size_bytes'] for q in qa),pdf_pages_reviewed=sum(q['page_count'] for q in qa),pages_rendered=sum(q['rendered_pages'] for q in qa),html_records_resolved_using_saved_full_GET=len(html),saved_html_bytes_measured=sum(r['saved_evidence']['size_bytes'] for r in html),current_source_health_samples=sum('source_health_sample' in fam for fam in evidence),archive_prepared=sum(r['decision']=='approved for addition' for r in d['resolved_records']),objects_archived=len(added),bytes_archived=sum(o['size_bytes'] for o in added.values()),placement_assigned_transitions=sum(rows[r['id']]['status']=='placement assigned' for r in d['resolved_records']),capacity_deferred=0,source_or_structural_blocked=len(d['deferred_records']),exact_duplicate_reconciliations=outcomes['duplicate'],additional_integrity_audit_status_changes=0,pre_existing_objects_unchanged=True,no_preexisting_overwrites=True,no_unexpected_objects_added=True,saved_live_key_size_etag_match=True)
    d['final_inventory_counts']=inv['counts'];d['final_r2']={'object_count':final['object_count'],'total_bytes':final['total_bytes'],'storage_headroom_bytes':10000000000-final['total_bytes']};d['final_live_listing_artifact']=final_path.relative_to(ROOT).as_posix()
    qs={q['id']:q for q in s['all_pending_records']};pending=[r for r in rows.values() if r['status']=='pending review'];gated={i:reason for i,reason in s['excluded_gated_pending_ids'].items() if rows[i]['status']=='pending review'};blocked={r['id'] for r in d['deferred_records']}
    groups=collections.defaultdict(list)
    for r in pending:
        if r['id'] in gated or r['id'] in blocked:continue
        q=qs[r['id']];groups[q['inferred_family']].append(q)
    ranked=[]
    for name,group in groups.items():
        count=len(group);saved=collections.Counter(q['saved_recommendation'] or 'unsaved' for q in group)
        rank=0 if 'planning/online-forms' in name else 1 if 'DocumentCenter' in name and 'mrcog' in name else 2 if 'municipaldevelopment/documents' in name else 3
        ranked.append(dict(family=name,count=count,candidate_ids=[q['id'] for q in group],saved_recommendations=dict(saved),reason='Pending rows with unapplied evidence or further source work; completed/gated rows excluded. Requires current scope/quality and full-document review before disposition.',rank=rank))
    ranked.sort(key=lambda f:(f['rank'],-f['count'],f['family']))
    # These isolated canonical measurement publications are the next small,
    # low-judgment program continuation; the library-wide group below is only
    # discovery accounting and never a licence to bundle unrelated records.
    cmp_next=['src-b9f68064d83c5038','src-ba0a4030fcc63e6e','src-d5e398345f6eec6b']
    next_family={'family':'MRCOG 2016 congestion profiles/rankings map and 2018 strategy matrix','candidate_ids':[i for i in cmp_next if rows[i]['status']=='pending review'],'estimated_size':3,'basis':'Separate later measurement-release unit; saved publication evidence exists, current originals/QA/scope remain to review. Do not treat the complete DocumentCenter host as one documentary family.'}
    queue=dict(schema_version=1,artifact_type='ordinary_queue_record_level_post_large_campaign',recorded_at=datetime.now(timezone.utc).isoformat(),pending_review_count=len(pending),gated_pending_count=len(gated),gated_pending_ids=gated,source_or_structural_blocked_pending_ids=sorted(blocked),ungated_pending_count=len(pending)-len(gated)-len(blocked),remaining_preselected_high_confidence_count=sum(bool(qs[r['id']]['actionable']) for r in pending if r['id'] not in gated and r['id'] not in blocked),next_actionable_background_family=next_family,source_directory_groups=ranked,newly_approved_backlog=[],archive_only_backlog=[],existing_ia_blocked_approved_ids=['src-06d0fc4cd0abdef6','src-070a763aa9701f86','src-51fb6dc80b316253'],mission_borderline_queue_size=0,visitor_visible_content_changed=False,selection_caveat='Directory groups are candidate discovery coverage, not automatic documentary-family boundaries or positive scope. Split program/project/legislative units before review. Historical classification coverage does not equal applied inventory state.')
    queue_path=DISC/f'ordinary-queue-next-position-post-large-campaign-{DATE}.json';save(queue_path,queue);d['remaining_queue_artifact']=queue_path.relative_to(ROOT).as_posix()
    queue['next_actionable_background_families']=[next_family]
    for family_id in ['family-211','family-212','family-207']:
        f=next(f for f in s['candidate_families'] if f['family_id']==family_id)
        ids=[i for i in f['candidate_ids'] if rows[i]['status']=='pending review' and i not in gated and i not in blocked]
        if ids:queue['next_actionable_background_families'].append(dict(family=f['family'],candidate_ids=ids,estimated_size=len(ids),basis='Small coherent City library directory with saved unapplied evidence; current originals and complete family QA/scope required. No disposition inferred from title or research classification alone.'))
    save(queue_path,queue)
    d['integrity_audit_artifact']=f'project-state/discovery/inventory-exact-identity-integrity-audit-{DATE}.json';d['completed_at']=datetime.now(timezone.utc).isoformat();d['state']='complete_background_campaign';d['validation_result']='pending_full_validation';save(CAMPAIGN,d)
    print(json.dumps({'accounting':d['accounting'],'final_r2':d['final_r2'],'remaining_queue':{'pending':len(pending),'gated':len(gated),'ungated':queue['ungated_pending_count']}}))

if __name__=='__main__':main()
