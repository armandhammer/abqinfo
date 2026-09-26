"""Record completed agent visual review and guarded campaign capacity plan."""
import importlib.util,json,hashlib,subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('Prepare-ApprovedBackgroundCampaign.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
d=c.load(c.ART);live=c.load(c.BASE);inv=c.load(c.ROOT/'project-state/master-inventory.json')['candidates']
if d['state']=='complete_background_campaign':raise SystemExit('Campaign complete; no readiness/state reset allowed.')
assert len(d['records'])==27 and all(r.get('source_exact_verified') for r in d['records'])
for r in d['records']+d['generated_packages']:
    if r.get('qa'):
        r['qa']['representative_visual_qa']='passed_agent_visual_inspection_opening_middle_final';r['qa']['visually_reviewed_at']=c.now()
        r['qa']['visual_finding']='Legible original layout, maps/tables/signatures and source pages; no rendering defect. No low-ink anomalies detected.'
    if r['id']=='generated-dpm-2018':
        r['outcome']='deferred_human_review';r['human_review_requirement']='src-7e7af2af147d96d7 March 21 2018 agenda remains requires human review; 2026-09-13 research indicates meeting apparently not held, while 2026-09-17 packet includes it. Current durable evidence does not deterministically resolve this conflict.'
        r['blocker']=r['human_review_requirement'];r['archival_authorized']=False
        r['conflicting_evidence']=['project-state/discovery/claude-consolidation-dpm-2018-2026-09-13.json','project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json']
        # The packet itself remains unchanged and measured even while upload is deferred.
        p=c.ROOT/r['staged_path'];assert (p.stat().st_size,c.sha(p))==(r['size_bytes'],r['expected_sha256'])
        r['stored_output_exact_verified']=True
        continue
    if not r.get('source_exact_verified'):continue
    key=r['r2_key']
    r['same_size_live_objects']=[o['key'] for o in live['objects'] if o['size_bytes']==r['size_bytes']]
    r['exact_or_casefold_key_collisions']=[o['key'] for o in live['objects'] if key and o['key'].casefold()==key.casefold()]
    if r['classification'].startswith('ABQInfo'):
        r['same_sha256_inventory_rows']=[{'id':x['id'],'r2_key':x.get('r2_key')} for x in inv if x.get('checksum_sha256')==r['expected_sha256']]
        r['near_name_live_keys']=[o['key'] for o in live['objects'] if ('dpm-executive-committee' in o['key'] and r['id'][-4:] in o['key']) or ('2011-go-bond' in o['key'] and 'program-record' in o['key'])]
        r['duplicate_canonical_relationship']='distinct corrected generated packet with identified unchanged original components; no exact alias'
    assert not r['same_size_live_objects'] and not r['exact_or_casefold_key_collisions'] and not r['same_sha256_inventory_rows']
    r['outcome']='ready_for_guarded_upload' if key else 'prepared_unuploaded_unresolved_archive_namespace'
    r['maximum_safe_stage']='archive_public_bytes_verified_placement_assigned' if key and r.get('canonical_page') else 'archive_public_bytes_verified_generated_package' if key else 'archive_prepared_only'
    r['archive_preparation_state']='exact_source_structural_all_page_render_and_visual_QA_complete'
qual=[r for r in d['records']+d['generated_packages'] if r['outcome']=='ready_for_guarded_upload']
total=sum(r['size_bytes'] for r in qual);assert all(r['size_bytes']<=150000000 for r in qual);assert live['total_bytes']+total<=d['project_storage_limit_bytes']
d['capacity_plan']={'qualifying_new_objects':len(qual),'qualifying_new_bytes':total,'largest_object_bytes':max(r['size_bytes'] for r in qual),'projected_final_object_count':live['object_count']+len(qual),'projected_final_total_bytes':live['total_bytes']+total,'storage_ceiling_unchanged':True,'max_object_override_needed':False,'priority_order':'approved originals, Capital Spending generated, DPM generated','capacity_deferred_ids':[]}
d['state']='preparation_complete_upload_authorized';d['content_tree_sha256_baseline']=subprocess.check_output(['git','rev-parse',d['baseline_git_sha']+':content'],cwd=c.ROOT,text=True).strip();c.save(d)
print(json.dumps(d['capacity_plan']))
