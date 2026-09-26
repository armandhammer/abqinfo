#!/usr/bin/env python3
"""Exact authorized archive identities, lifecycle, and complete R2 accounting."""
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE='6f2f181a81e75dd95faac1c0bf2283176964824c'
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def old(p): return json.loads(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT).decode('utf-8-sig'))
m=load('project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json')
assert m==old('project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json')
a=load('project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json')
assert a['state']=='complete_all_12_public_byte_verified_and_inventory_reconciled'
ids=set(m['candidate_ids_in_order']); assert len(ids)==12
assert ids=={r['id'] for r in a['results']}==set(a['inventory_reconciled_ids'])
assert len(a['results'])==12 and a['summary']['public_byte_verified']==12
assert sum(r['size_bytes'] for r in a['results'])==122249326
assert sum(r['page_count'] for r in a['results'])==928
rows={r['id']:r for r in load('project-state/master-inventory.json')['candidates']}
before={r['id']:r for r in old('project-state/master-inventory.json')['candidates']}
assert {rid for rid in rows if rows[rid]!=before[rid]}==ids
allowed={'status','r2_key','r2_url','r2_etag','r2_last_modified','local_path','processing_notes','validation_status','updated_at'}
for r in a['results']:
    p=next(p for p in m['records'] if p['id']==r['id']);row=rows[r['id']]
    assert r['byte_identical'] is True and r['http_public_get']=='passed' and r['verified_at']
    assert r['size_bytes']==r['public_size_bytes']==p['size_bytes']==row['size_bytes']
    assert r['checksum_sha256']==r['public_checksum_sha256']==p['checksum_sha256']==row['checksum_sha256']
    assert r['page_count']==p['page_count'] and r['staged_path']==p['staged_path']
    assert r['r2_key']==p['proposed_r2_key']==row['r2_key']
    assert r['public_url']==p['expected_public_archive_url']==row['r2_url']
    assert row['status']=='placement assigned' and row['local_path']==p['staged_path']
    assert {k for k in row if row[k]!=before[r['id']][k]}<=allowed
    assert row['scope_assessment']['final_scope_decision']=='passes_both_gates'
    assert r['authoritative_source_url']==row['direct_file_url']
r2=load('project-state/r2-inventory.json'); b=old('project-state/r2-inventory.json')
objects={o['key']:o for o in r2['objects']}; prior={o['key']:o for o in b['objects']}
assert len(objects)==r2['object_count']==1249 and sum(o['size_bytes'] for o in objects.values())==r2['total_bytes']==9340531168
assert len(prior)==1237 and b['total_bytes']==9218281842
assert set(objects)-set(prior)=={r['r2_key'] for r in a['results']}
for k,o in prior.items():
    assert all(objects[k][f]==o[f] for f in ('key','size_bytes','etag'))
for r in a['results']:assert objects[r['r2_key']]['size_bytes']==r['size_bytes']
assert a['accounting']['added_objects']==12 and a['accounting']['added_bytes']==122249326
assert a['accounting']['pre_existing_manifest_sha256_before']==a['accounting']['pre_existing_manifest_sha256_after']
assert a['accounting']['pre_existing_objects_unchanged'] is True
assert a['accounting']['unexpected_objects_added'] is False and a['accounting']['overwrite_or_deletion_performed'] is False
assert a['r2_inventory_accounting']['saved_live_key_size_etag_match'] is True
live=ROOT/a['after_r2']['listing_local_path']
if live.exists():assert r2['objects']==json.loads(live.read_text(encoding='utf-8-sig'))['objects']
assert a['r2_mutation'] is True and a['visitor_visible_content_changed'] is False
assert a['max_object_bytes']==100000000 and a['max_projected_storage_bytes']==10000000000
dup='src-d9bf34830a9467e2'; canonical='src-28418cab91a745a6'
assert dup not in ids and rows[dup]['status']=='duplicate' and rows[canonical]['status']=='validated'
assert rows[dup]==before[dup] and rows[canonical]==before[canonical]
assert 'src-99fe2201b73355c4' in ids and rows['src-99fe2201b73355c4']['checksum_sha256']!=rows[dup]['checksum_sha256']
f=a['planning_impact_area_family']; assert len(f['component_ids'])==4 and set(f['component_ids'])<=ids
assert 'incomplete' in f['state'] and 'one grouped' in f['future_public_treatment']
assert not f['complete_study_recovered'] and not f['other_chapters_inferred'] and not f['synthesized_pdf']
assert len(list((ROOT/'research/staging/planning-documents-root-archive-preparation-2026-09-25').glob('*.pdf')))==13
for args in (['git','diff','--name-only',BASE,'--','content'],['git','ls-files','--others','--exclude-standard','content']):
    assert not subprocess.check_output(args,cwd=ROOT).strip()
print('PASS: 12 exact public-byte archives; 122,249,326 bytes / 928 pages; R2 1,249 / 9,340,531,168; only authorized inventory transitions; no content changes.')
