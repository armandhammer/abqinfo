#!/usr/bin/env python3
"""Build the final 12-original no-mutation manifest and current derived state."""
from __future__ import annotations
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PREP='project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json'
RECON='project-state/discovery/planning-documents-root-barelas-duplicate-reconciliation-2026-09-26.json'
OUT='project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json'
BACKLOG='project-state/discovery/approved-inventory-backlog-prioritization-post-later-ms4-2026-09-25.json'
DUP='src-d9bf34830a9467e2'
CANONICAL='src-28418cab91a745a6'
ORDER=['src-16b33375ffbddc62','src-1fa6ae851ddf282d','src-513fe9056bf9b34c','src-c54e59cd5c25282d','src-7de0f5803d442e8f','src-8740362a1b751e26','src-99fe2201b73355c4','src-afac0cf84867a22f','src-c87775c045d8acc4','src-eb0f4b39798d29df','src-f528ec2e0e955690','src-fb6e95610a43c7a4']

def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def save(path,value):
    p=ROOT/path; t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); t.replace(p)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def object_identity(source):return {o['key']:(o['size_bytes'],o['etag']) for o in source['objects']}

def main():
    prep,recon=load(PREP),load(RECON)
    assert recon['state']=='reconciled_exact_duplicate' and recon['duplicate_id']==DUP and recon['canonical_id']==CANONICAL
    master=load('project-state/master-inventory.json'); rows={r['id']:r for r in master['candidates']}
    counts=Counter(r['status'] for r in rows.values()); assert {s:counts[s] for s in master['allowed_statuses']}==master['counts']
    assert rows[DUP]['status']=='duplicate' and rows[CANONICAL]['status']=='validated'
    before=load('tmp/planning-documents-root-live-r2-preflight-2026-09-26.json')
    after=load('tmp/planning-documents-root-live-r2-preflight-after-2026-09-26.json')
    saved=load('project-state/r2-inventory.json')
    assert object_identity(before)==object_identity(after)==object_identity(saved)
    assert after['object_count']==len(after['objects']) and after['total_bytes']==sum(o['size_bytes'] for o in after['objects'])
    tooling=load('tmp/planning-documents-root-upload-tool-readiness-2026-09-26.json')
    assert tooling['state']=='twelve_default_limit_whatif_probes_passed_no_mutation' and len(tooling['records'])==12 and tooling['credentials_accessible']
    assert tooling['public_byte_verification_script_parse']=='passed' and tooling['r2_mutation'] is False
    prepared={r['id']:r for r in prep['records']}
    assert set(ORDER)==set(prepared)-{DUP}
    targets={r['key']:r for r in tooling['records']}
    exact_keys={o['key'] for o in after['objects']}; folded={k.casefold() for k in exact_keys}
    terms={
      **{rid:['planning-impact-area'] for rid in ORDER[:4]},
      'src-7de0f5803d442e8f':['electric-system','transmission-generation'],
      'src-8740362a1b751e26':['planned-communities'],
      'src-99fe2201b73355c4':['barelas'],
      'src-afac0cf84867a22f':['bosque-action','rio-grande-valley-state-park'],
      'src-c87775c045d8acc4':['old-town','h1-'],
      'src-eb0f4b39798d29df':['unser-boulevard','unser-blvd'],
      'src-f528ec2e0e955690':['volcano-trails'],
      'src-fb6e95610a43c7a4':['major-public-open-space'],
    }
    semantic_notes={
      'src-99fe2201b73355c4':'The 2008 Barelas Sector Development Plan is distinct from the canonical commercial-area revitalization plan, South Barelas industrial-park MRA plan, and stop-sign proposal; different instrument, scope, size and hash.',
      'src-afac0cf84867a22f':'The 1993 final Bosque Action Plan is distinct from the revised 2017 Rio Grande Valley State Park map.',
      'src-c87775c045d8acc4':'The one-page former H-1 guidelines amended through 1998 are distinct from 2018 HPO-5 standards/maps, task-force rankings and station-area planning.',
      'src-f528ec2e0e955690':'The settled enacted 2011 package includes the held plan plus adopting legislation. The existing standalone plan, adoption resolution and EPC notice have separate identities; saved 2026-09-13 research establishes this bound-package relationship.',
      'src-fb6e95610a43c7a4':'The 1999 systemwide facility plan is distinct from the West Side steering-committee presentation.',
    }
    records=[]
    for rid in ORDER:
        p=prepared[rid]; row=rows[rid]; path=ROOT/p['staged_local_path']; key=p['proposed_r2_key']
        assert row['status']=='approved for addition' and row['scope_assessment']['final_scope_decision']=='passes_both_gates'
        assert row['r2_key'] is None and row['r2_url'] is None
        assert path.stat().st_size==p['size_bytes']==row['size_bytes']
        assert digest(path)==p['sha256']==row['checksum_sha256']
        assert targets[key]['bytes']==p['size_bytes'] and targets[key]['result']=='WhatIf: upload not performed'
        same_hash=[{'id':r['id'],'status':r['status'],'r2_key':r.get('r2_key')} for r in rows.values() if r['id']!=rid and r.get('checksum_sha256')==p['sha256']]
        assert not same_hash
        sizes=[o['key'] for o in after['objects'] if o['size_bytes']==p['size_bytes']]
        assert not sizes, f'Same-size live objects require narrow identity review before readiness: {rid}: {sizes}'
        near=[o for o in after['objects'] if any(term in o['key'].lower() for term in terms[rid])]
        near_evidence=[]
        for obj in near:
            aliases=[{'id':r['id'],'title':r['title'],'size_bytes':r.get('size_bytes'),'checksum_sha256':r.get('checksum_sha256'),'direct_file_url':r.get('direct_file_url')} for r in rows.values() if r.get('r2_key')==obj['key']]
            near_evidence.append({'r2_key':obj['key'],'size_bytes':obj['size_bytes'],'inventory_relationships':aliases})
        assert key not in exact_keys and key.casefold() not in folded and p['size_bytes']<100000000
        records.append({'id':rid,'title':p['title'],'source_url':p['source_url'],'direct_file_url':p['direct_file_url'],'staged_path':p['staged_local_path'],'size_bytes':p['size_bytes'],'checksum_sha256':p['sha256'],'page_count':p['page_count'],'proposed_r2_key':key,'expected_public_archive_url':p['proposed_public_archive_url'],'proposed_canonical_page':p['proposed_canonical_page'],'collision_checks':{'exact_key_exists':False,'case_insensitive_key_exists':False,'same_size_live_objects':sizes,'known_same_sha256_other_inventory_rows':same_hash,'near_name_objects':near_evidence,'semantic_review':semantic_notes.get(rid,'No meaningful same-subject archived name found in the complete live listing; inventory-wide exact-hash comparison found no other row.')},'uploader_whatif_result':targets[key]['result']})
    assert len({r['proposed_r2_key'].casefold() for r in records})==12
    assert len({r['staged_path'] for r in records})==12
    added=sum(r['size_bytes'] for r in records); pages=sum(r['page_count'] for r in records)
    assert (added,pages)==(122249326,928)
    projected=after['total_bytes']+added; assert projected<=10000000000
    manifest={'schema_version':1,'artifact_type':'planning_documents_root_final_no_mutation_r2_upload_preflight','recorded_at':datetime.now(timezone.utc).isoformat(),'date_basis':'UTC execution date','reviewed_baseline_commit':'8d5cc8731454a78546b089c87b265ce080ba14fd','state':'upload-ready only after explicit R2 authorization','candidate_ids_in_order':ORDER,'excluded_exact_duplicate':{'id':DUP,'canonical_id':CANONICAL,'reconciliation_artifact':RECON,'size_bytes':8719030,'page_count':150,'reason':'already archived exact-byte canonical original; no second object or standalone entry'},'records':records,'aggregate_staged_bytes':added,'aggregate_pages':pages,'r2_baseline':{'object_count':after['object_count'],'total_bytes':after['total_bytes'],'generated_at':after['generated_at'],'saved_and_before_after_live_keys_sizes_etags_identical':True},'expected_post_upload':{'object_count':after['object_count']+12,'total_bytes':projected,'added_objects':12,'added_bytes':added},'collision_result':'all_12_keys_absent_and_no_known_same_hash_canonical_objects','tooling_readiness':{'credentials_accessible':True,'uploader':'scripts/upload-r2-document.ps1','overwrite_protection':'head-object must confirm 404 before ShouldProcess; existing objects rejected','twelve_default_limit_whatif_probes_passed':True,'max_object_bytes':100000000,'max_projected_storage_bytes':10000000000,'object_size_override_required':False,'projected_storage_headroom_bytes':10000000000-projected,'public_exact_byte_verifier':'scripts/project/Test-R2PublicObject.ps1','public_verifier_ready':True,'public_verifier_checks':['fresh full public GET','exact size','exact SHA-256'],'public_verifier_executed':False,'readiness_evidence':tooling},'planning_impact_area_family':prep['planning_impact_area_family'],'preparation_artifact':PREP,'r2_mutation':False,'public_byte_verification_performed':False,'visitor_visible_content_changed':False,'inventory_r2_fields_unassigned':True,'next_gate':'Explicit authorization for exactly these 12 unchanged Planning uploads and exact public-byte verification; later visible Hugo implementation requires separate manual-review content PR.','execution_after_authorization':{'workflow':'Recheck complete live listing and all 12 absent keys; rehash each staged path; use scripts/upload-r2-document.ps1 with defaults; verify each with scripts/project/Test-R2PublicObject.ps1; checkpoint each result and reconcile saved R2 accounting.','no_overwrite':True,'no_150MB_exception':True}}
    save(OUT,manifest)
    prep.setdefault('historical_preparation_blockers',prep['blockers'])
    prep['blockers']=[]
    prep['current_derived_state']={'recorded_at':manifest['recorded_at'],'verified_authoritative_source_deliveries':13,'exact_duplicate_deliveries_reconciled':1,'unique_new_upload_candidates':12,'unique_upload_candidate_ids':ORDER,'unique_upload_bytes':added,'unique_upload_pages':pages,'duplicate_reconciliation_artifact':RECON,'final_no_mutation_preflight':OUT,'inventory_transition':{DUP:'duplicate'},'other_12_status':'approved for addition','r2_mutation':False,'visitor_visible_content_changed':False}
    prep['preparation_readiness']='13_deliveries_source_and_QA_verified;_one_exact_duplicate_reconciled;_12_unique_originals_upload_ready_after_explicit_authorization'
    prep['next_gate']=manifest['next_gate']
    prepared[DUP]['preparation_blocker']=None
    prepared[DUP]['current_disposition']='duplicate'
    prepared[DUP]['duplicate_reconciliation_artifact']=RECON
    prepared[DUP]['collision_resolution']['action']='resolved_exact_duplicate; canonical already archived; no second object or standalone entry'
    prep['summary']['duplicate_deliveries_reconciled']=1
    prep['summary']['current_preparation_blockers']=0
    prep['summary']['unique_upload_bytes']=added; prep['summary']['unique_upload_pages']=pages
    save(PREP,prep)
    backlog=load(BACKLOG)
    unit=backlog['ranked_units'][0]
    assert unit['unit']=='Planning documents-root historical plans and policy'
    backlog.setdefault('historical_planning_selection_before_reconciliation',json.loads(json.dumps(unit)))
    backlog['current_state_after_barelas_reconciliation']={'recorded_at':manifest['recorded_at'],'inventory_status_counts':master['counts'],'positive_scope_approved_records':counts['approved for addition'],'historical_source_state_preserved':True,'reconciliation_artifact':RECON,'preflight_artifact':OUT,'no_broad_reprioritization_performed':True}
    unit['count']=12; unit['record_ids']=ORDER
    unit['archive_preparation']='Complete: 13 authoritative source deliveries QA verified; one exact archived duplicate reconciled; 12 unique originals / 122,249,326 bytes / 928 pages final no-mutation upload preflight passed.'
    unit['source_provenance']='All 13 historical City deliveries freshly matched canonical sizes and hashes during preparation; one is now reconciled as the exact archived Barelas alias. The 12 unique staged originals passed final size/hash rechecks.'
    unit['reason']='Preparation and no-mutation preflight are complete; the next useful progress is externally gated unchanged archival of the 12 unique originals.'
    unit['next_progress_stage']='Separately authorized 12 unchanged R2 uploads and exact public-byte verification.'
    unit['current_gate']='Explicit current R2 authorization required; later visible content remains separately manual-review gated.'
    unit['placement']='Completed background presentation plan retained. Four Planning Impact Area components form one incomplete grouped treatment. Barelas sector plan is unique; commercial revitalization delivery resolves to the existing canonical archive.'
    unit['reconciliation_artifact']=RECON; unit['preflight_artifact']=OUT
    assert sum(u['count'] for u in backlog['ranked_units'])==counts['approved for addition']
    save(BACKLOG,backlog)
    print(f'12 unique upload candidates: {added:,} bytes / {pages} pages; projected {after["object_count"]+12} objects / {projected:,} bytes. No mutation.')

if __name__=='__main__':main()
