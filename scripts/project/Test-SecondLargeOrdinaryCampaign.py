#!/usr/bin/env python3
"""Check live second-campaign changes against the immutable owner-reviewed state."""
import collections,hashlib,json,runpy,subprocess
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('SecondLargeOrdinaryCampaign.py')))
ROOT,DISC,ART,SEL,BASE,load,digest=(c[k] for k in ['ROOT','DISC','ART','SEL','BASE','load','digest'])
d=load(ART);s=load(SEL);inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
prior={r['id']:r for r in json.loads(subprocess.check_output(['git','show',BASE+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))['candidates']}
resolved={r['id']:r for r in d['resolved_records']}
assert len(resolved)==len(d['resolved_records'])<=700
assert len(rows)==len(prior)==7137 and s['starting_population']==sorted(i for i,r in prior.items() if r['status']=='pending review')
assert {i:digest(r) for i,r in prior.items()}==s['baseline_row_digests']
assert not set(resolved)&(set(s['gated_pending_ids'])|set(s['structural_blocked_ids']))
hard=DISC/'inventory-legacy-relationship-hardening-2026-09-26.json'
legacy=load(hard) if hard.exists() else {'changed_ids':[]}
changed={i for i in rows if rows[i]!=prior[i]}
assert changed==set(resolved)|set(legacy['changed_ids']),('Unaccounted row mutation',changed-(set(resolved)|set(legacy['changed_ids'])))
for i in rows.keys()-resolved.keys()-set(legacy['changed_ids']):assert rows[i]==prior[i]
for i in legacy['changed_ids']:assert rows[i]['status']==prior[i]['status']
assert all(prior[i]['status']=='pending review' for i in resolved)
counts=collections.Counter(r['status'] for r in rows.values());assert inv['counts']=={x:counts[x] for x in inv['allowed_statuses']}
assert counts['pending review']==1112-len(resolved)
assert counts['requires human review']==205
allowed={'status','updated_at','processing_notes','validation_status','exclusion_reason','scope_assessment','checksum_sha256','size_bytes','title','agency','local_path','file_type','proposed_canonical_page','r2_key','r2_url','r2_etag','r2_last_modified','cited_successors'}
for i,x in resolved.items():
    row=rows[i];old=prior[i];assert {k for k in row if row[k]!=old.get(k)}<=allowed
    for field in ['source_url','direct_file_url','discovery_path','cited_predecessors']:assert row[field]==old[field]
    assert all(n in row['processing_notes'] for n in old['processing_notes'])
    rec=next(r for r in load(ROOT/x['evidence_artifact'])['records'] if r['id']==i)
    assert rec['review_complete'] and rec['disposition']==x['decision'] and rec['quality_assessment']['substantive_rationale']
    assert row['status'] in ['approved for addition','placement assigned','duplicate','superseded','excluded']
    qa=rec.get('fresh_source_qa')
    if qa:
        p=ROOT/qa['staged_path'];assert p.stat().st_size==qa['size_bytes'] and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==qa['checksum_sha256']
        assert qa['source_exact_verified'] and qa['source_GET']['http_status']==200
        assert qa['representative_visual_qa']=='passed_agent_inspection_opening_middle_ending'
    if x['decision']=='approved for addition':
        assert row['scope_assessment']['final_scope_decision']=='passes_both_gates'
        for key in ['specific_albuquerque_connection','abqinfo_public_information_value','general_context_exclusion_test','substantive_rationale']:assert row['scope_assessment'][key]
    if x['decision']=='duplicate':
        can=rows[rec['canonical_candidate_id']]
        if can['checksum_sha256'] is None and rec.get('existing_canonical_public_verification'):
            v=rec['existing_canonical_public_verification'];assert can['status']=='requires human review' and can==prior[can['id']]
            obj=next(o for o in load(ROOT/'project-state/r2-inventory.json')['objects'] if o['key']==can['r2_key'])
            assert v['byte_identical'] and v['public_url']==obj['public_url']
            assert (row['size_bytes'],row['checksum_sha256'])==(v['size_bytes'],v['checksum_sha256']) and obj['size_bytes']==row['size_bytes']
        else:assert (row['size_bytes'],row['checksum_sha256'])==(can['size_bytes'],can['checksum_sha256'])
        assert (can.get('direct_file_url') or can['source_url']) in row['cited_successors']
    if x['decision']=='superseded':assert rec['chronology_evidence']
baseline=load(ROOT/d['baseline_r2_artifact']);current=load(ROOT/'project-state/r2-inventory.json')
old={o['key']:o for o in baseline['objects']};objects={o['key']:o for o in current['objects']};added={a['key']:a for a in d['archive_objects']}
assert (len(old),baseline['total_bytes'])==(1292,9387544940)
for key,o in old.items():assert all(objects[key][f]==o[f] for f in ['key','size_bytes','etag'])
assert objects.keys()-old.keys()==added.keys()
assert len(objects)==current['object_count']==1292+len(added)
assert current['total_bytes']==sum(o['size_bytes'] for o in objects.values())==9387544940+sum(a['size_bytes'] for a in added.values())<=10000000000
assert len({k.casefold() for k in objects})==len(objects)
for key,a in added.items():
    assert a['upload_intent']['key_was_absent'] and a['size_bytes']<=150000000
    v=a['public_verification'];assert v['byte_identical'] and v['size_bytes']==a['size_bytes'] and v['checksum_sha256']==a['checksum_sha256']
    assert objects[key]['size_bytes']==a['size_bytes'] and objects[key]['etag']==a['etag']
    row=rows[a['id']];assert row['status']=='placement assigned' and row['r2_key']==key
assert not subprocess.check_output(['git','diff',BASE,'--name-only','--','content'],cwd=ROOT).strip()
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','content'],cwd=ROOT).strip()
assert subprocess.check_output(['git','rev-parse','HEAD:content'],cwd=ROOT,text=True).strip()==d['content_tree_baseline']
if d['state']=='complete_background_campaign':
    assert d['accounting']['resolved_records']==len(resolved)
    assert d['final_inventory_counts']==inv['counts']
    assert d['accounting']['outcomes']==dict(collections.Counter(r['decision'] for r in resolved.values()))
    assert load(ROOT/d['final_live_listing_artifact'])['objects']==current['objects']
    assert load(ROOT/'project-state/checkpoint.json')['counts_by_status']==inv['counts']
print(f'PASS: {len(resolved)} second-campaign transitions, {len(added)} exact-public originals; protected baseline and zero content changes preserved.')
