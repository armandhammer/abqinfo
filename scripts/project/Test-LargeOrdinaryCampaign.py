#!/usr/bin/env python3
"""Exact campaign population, transitions, archive identity and protected scope."""
import collections,hashlib,json,runpy,subprocess
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,BASE,SELECTION,CAMPAIGN,load,digest=(c[k] for k in ['ROOT','DISC','DATE','BASE','SELECTION','CAMPAIGN','load','digest'])
def git_json(path):return json.loads(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode('utf-8-sig'))

# A subsequent authorized campaign must not reinterpret this completed run's
# exact population/count/R2 contract. Run every original assertion against its
# immutable reviewed closeout. The second campaign regression checks current
# rows and preserves all first-campaign results against this same snapshot.
second_path=DISC/f'ordinary-queue-second-large-resolution-campaign-{DATE}.json'
second=load(second_path) if second_path.exists() else None
if second:
    assert second['baseline_commit']=='34ccc0fe230ffb8290652979cbe8603c69db3115'
    original_load=load
    def historical_load(path):
        relative=Path(path).relative_to(ROOT).as_posix()
        if relative in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/checkpoint.json']:
            return json.loads(subprocess.check_output(['git','show',second['baseline_commit']+':'+relative],cwd=ROOT).decode('utf-8-sig'))
        return original_load(path)
    load=historical_load
d=load(CAMPAIGN);s=load(SELECTION);inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};prior={r['id']:r for r in git_json('project-state/master-inventory.json')['candidates']}
resolved={r['id']:r for r in d['resolved_records']}
assert len(resolved)==len(d['resolved_records'])<=500
assert len(rows)==len(prior)==7137 and s['total_pending_population']==1612
assert all(isinstance(q['actionable'],bool) for q in s['all_pending_records'])
assert set(resolved).isdisjoint(s['excluded_gated_pending_ids'])
assert {i for i in rows if rows[i]!=prior[i]}==set(resolved),'Unexpected inventory change or missing campaign accounting'
for i in rows.keys()-resolved.keys():assert rows[i]==prior[i]
assert all(prior[i]['status']=='pending review' for i in resolved)
counts=collections.Counter(r['status'] for r in rows.values());assert inv['counts']=={x:counts[x] for x in inv['allowed_statuses']}
assert counts['pending review']==1612-len(resolved)
assert counts['requires human review']==205
allowed={'status','updated_at','processing_notes','validation_status','exclusion_reason','scope_assessment','checksum_sha256','size_bytes','title','agency','local_path','file_type','proposed_canonical_page','r2_key','r2_url','r2_etag','r2_last_modified','cited_successors'}
for i,r in resolved.items():
    row=rows[i];old=prior[i];assert {k for k in row if row[k]!=old.get(k)}<=allowed
    assert row['source_url']==old['source_url'] and row['direct_file_url']==old['direct_file_url']
    assert row['discovery_path']==old['discovery_path'] and row['cited_predecessors']==old['cited_predecessors']
    assert set(old['cited_successors'])<=set(row['cited_successors'])
    if r['decision'] not in ['duplicate','superseded']:assert row['cited_successors']==old['cited_successors']
    assert all(n in row['processing_notes'] for n in old['processing_notes'])
    assert row['status'] in ['approved for addition','placement assigned','duplicate','superseded','excluded']
    fam=load(ROOT/r['evidence_artifact']);rec=next(x for x in fam['records'] if x['id']==i)
    assert rec['review_complete'] and rec['disposition']==r['decision'] and rec['mission_scope_assessment']
    assert not fam['visitor_visible_content_changed']
    if rec.get('fresh_source_qa'):
        qa=rec['fresh_source_qa'];p=ROOT/qa['staged_path']
        assert p.stat().st_size==qa['size_bytes'] and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==qa['checksum_sha256']
        assert qa['source_GET']['http_status']==200 and qa['source_exact_verified']
        assert qa['representative_visual_qa']=='passed_agent_inspection_opening_middle_ending'
        assert qa['checksum_sha256']==rec['saved_evidence']['checksum_sha256']
    if r['decision']=='duplicate':
        canonical=rows[rec['canonical_candidate_id']]
        assert (row['size_bytes'],row['checksum_sha256'])==(canonical['size_bytes'],canonical['checksum_sha256'])
        assert (canonical.get('direct_file_url') or canonical['source_url']) in row['cited_successors']
    elif r['decision']=='approved for addition':
        assert row['scope_assessment']['final_scope_decision']=='passes_both_gates'
        assert rec['quality_assessment']['substantive_rationale']
        assert rec['fresh_source_qa']['rendered_pages']==rec['fresh_source_qa']['page_count']
    else:assert row['scope_assessment']['final_scope_decision']=='excluded'
baseline=load(ROOT/d['baseline_r2_artifact']);current=load(ROOT/'project-state/r2-inventory.json');old={o['key']:o for o in baseline['objects']};objects={o['key']:o for o in current['objects']};added={a['key']:a for a in d['archive_objects']}
assert (len(old),baseline['total_bytes'])==(1279,9370314196)
for key,o in old.items():assert all(objects[key][f]==o[f] for f in ['key','size_bytes','etag'])
assert objects.keys()-old.keys()==added.keys()
assert len(objects)==current['object_count']==1279+len(added)
assert current['total_bytes']==sum(o['size_bytes'] for o in objects.values())==9370314196+sum(a['size_bytes'] for a in added.values())<=10000000000
assert len({k.casefold() for k in objects})==len(objects)
for key,a in added.items():
    assert a['upload_intent']['key_was_absent'] and a['size_bytes']<=150000000
    v=a['public_verification'];assert v['byte_identical'] and v['size_bytes']==a['size_bytes'] and v['checksum_sha256']==a['checksum_sha256']
    assert objects[key]['size_bytes']==a['size_bytes'] and objects[key]['etag']==a['etag']
    row=rows[a['id']];assert row['status']=='placement assigned' and row['r2_key']==key and row['r2_url']==v['public_url']
assert not subprocess.check_output(['git','diff',BASE,'--name-only','--','content'],cwd=ROOT).strip()
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','content'],cwd=ROOT).strip()
assert subprocess.check_output(['git','rev-parse','HEAD:content'],cwd=ROOT,text=True).strip()==d['content_tree_baseline']
if d['state']=='complete_background_campaign':
    assert len(resolved)==500 and sum(f['complete'] for f in d['families_processed'])>=20
    a=d['accounting']
    assert a['resolved_records']==500 and a['families_completed']==201 and a['families_attempted']==202
    assert a['outcomes']=={'approved for addition':13,'duplicate':23,'excluded':464}
    assert a['outcomes']==dict(collections.Counter(r['decision'] for r in resolved.values()))
    assert a['new_human_review']==a['new_borderlines']==a['capacity_deferred']==0
    assert a['archive_prepared']==a['objects_archived']==a['placement_assigned_transitions']==len(added)==13
    assert a['bytes_archived']==sum(x['size_bytes'] for x in added.values())==17230744
    assert a['exact_source_files_reviewed']==96 and a['exact_source_bytes_reviewed']==169833087
    assert a['pdf_pages_reviewed']==1334 and a['pages_rendered']==359
    assert a['html_records_resolved_using_saved_full_GET']==404 and a['current_source_health_samples']==173
    assert {r['id'] for r in d['deferred_records']}=={'src-48c77cfd3533626b'}
    assert all(rows[r['id']]==prior[r['id']] for r in d['deferred_records'])
    assert d['final_r2']=={'object_count':1292,'total_bytes':9387544940,'storage_headroom_bytes':612455060}
    assert d['final_inventory_counts']==inv['counts']
    final=load(ROOT/d['final_live_listing_artifact']);assert final['objects']==current['objects']
    audit=load(DISC/f'inventory-exact-identity-integrity-audit-{DATE}.json')
    module=runpy.run_path(str(Path(__file__).with_name('Audit-InventoryExactIdentity.py')))
    if second:module['build'].__globals__['load']=historical_load
    actual=module['build']();actual.pop('recorded_at');expected=dict(audit);expected.pop('recorded_at');assert actual==expected
    assert audit['audit_population']==7137 and set(audit['newly_reconciled_aliases'])=={i for i,r in resolved.items() if r['decision']=='duplicate'}
    assert load(ROOT/'project-state/checkpoint.json')['counts_by_status']==inv['counts']
    queue=load(ROOT/d['remaining_queue_artifact']);assert queue['pending_review_count']==counts['pending review']
print(f'PASS: {len(resolved)} reviewed transitions; {len(added)} exact public originals; protected and unrelated rows unchanged; no content changes.')
