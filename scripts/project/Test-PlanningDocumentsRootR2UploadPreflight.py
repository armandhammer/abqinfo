#!/usr/bin/env python3
"""Guard exact Barelas reconciliation and the twelve-original no-mutation preflight."""
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASELINE='8d5cc8731454a78546b089c87b265ce080ba14fd'
DUP='src-d9bf34830a9467e2'; CANONICAL='src-28418cab91a745a6'
SHA='c2081c6cbc60b029c2b558a73ad975b429b03e89cc1837c393f8b5c30191ae19'
ORDER=['src-16b33375ffbddc62','src-1fa6ae851ddf282d','src-513fe9056bf9b34c','src-c54e59cd5c25282d','src-7de0f5803d442e8f','src-8740362a1b751e26','src-99fe2201b73355c4','src-afac0cf84867a22f','src-c87775c045d8acc4','src-eb0f4b39798d29df','src-f528ec2e0e955690','src-fb6e95610a43c7a4']
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def baseline(path):return subprocess.run(['git','show',BASELINE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

master=load('project-state/master-inventory.json'); rows={r['id']:r for r in master['candidates']}
before={r['id']:r for r in json.loads(baseline('project-state/master-inventory.json').decode('utf-8-sig'))['candidates']}
recon=load('project-state/discovery/planning-documents-root-barelas-duplicate-reconciliation-2026-09-26.json')
prep=load('project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json')
m=load('project-state/discovery/planning-documents-root-r2-upload-preflight-2026-09-26.json')
r2=load('project-state/r2-inventory.json'); checkpoint=load('project-state/checkpoint.json')
archive_path=ROOT/'project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json'
archived=archive_path.exists() and load(archive_path.relative_to(ROOT).as_posix()).get('state')=='complete_all_12_public_byte_verified_and_inventory_reconciled'
assert set(rows)==set(before)
assert all(rows[rid]==before[rid] for rid in rows if rid!=DUP and not (archived and rid in ORDER)),'An unrelated or canonical inventory row changed'
for field in ('source_url','direct_file_url','title','size_bytes','checksum_sha256','referring_urls','discovery_path','quality_assessment','scope_assessment'):
    assert rows[DUP][field]==before[DUP][field]
assert rows[DUP]['status']=='duplicate' and rows[CANONICAL]['status']=='validated'
assert CANONICAL in rows[DUP]['exclusion_reason'] and rows[CANONICAL]['direct_file_url'] in rows[DUP]['cited_successors']
assert rows[DUP]['size_bytes']==rows[CANONICAL]['size_bytes']==recon['size_bytes']==8719030
assert rows[DUP]['checksum_sha256']==rows[CANONICAL]['checksum_sha256']==recon['checksum_sha256']==SHA
assert recon['duplicate_id']==DUP and recon['canonical_id']==CANONICAL and recon['page_count']==150
assert recon['state']=='reconciled_exact_duplicate' and recon['canonical_record_changed'] is False
public=recon['exact_public_byte_evidence']['record']
assert public['byte_identical'] and public['size_bytes']==8719030 and public['checksum_sha256']==SHA
assert public['public_url']==rows[CANONICAL]['r2_url']
assert recon['live_object_evidence']['object']['key']==rows[CANONICAL]['r2_key']
assert recon['live_object_evidence']['object']['etag']==rows[CANONICAL]['r2_etag']
assert any(o['key']==rows[CANONICAL]['r2_key'] and o['size_bytes']==8719030 for o in r2['objects'])
assert m['candidate_ids_in_order']==ORDER==[r['id'] for r in m['records']]
assert len(set(ORDER))==12 and DUP not in ORDER and m['excluded_exact_duplicate']['id']==DUP
assert m['aggregate_staged_bytes']==sum(r['size_bytes'] for r in m['records'])==122249326
assert m['aggregate_pages']==sum(r['page_count'] for r in m['records'])==928
assert len({r['proposed_r2_key'].casefold() for r in m['records']})==12
assert len({r['staged_path'] for r in m['records']})==12
assert m['state']=='upload-ready only after explicit R2 authorization'
assert m['expected_post_upload']=={'object_count':1249,'total_bytes':9340531168,'added_objects':12,'added_bytes':122249326}
assert (m['r2_baseline']['object_count'],m['r2_baseline']['total_bytes'])==(1237,9218281842)
assert m['r2_baseline']['saved_and_before_after_live_keys_sizes_etags_identical'] is True
keys={o['key'].casefold() for o in r2['objects']}
for r in m['records']:
    path=ROOT/r['staged_path']; p=next(x for x in prep['records'] if x['id']==r['id']); row=rows[r['id']]
    assert path.stat().st_size==r['size_bytes']==p['size_bytes']==row['size_bytes']
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    assert h.hexdigest()==r['checksum_sha256']==p['sha256']==row['checksum_sha256']
    assert r['page_count']==p['page_count']
    assert row['status']==('placement assigned' if archived else 'approved for addition')
    assert (row['r2_key'],row['r2_url'])==((r['proposed_r2_key'],r['expected_public_archive_url']) if archived else (None,None))
    assert r['proposed_r2_key']==p['proposed_r2_key'] and ((r['proposed_r2_key'].casefold() in keys) == archived)
    assert r['expected_public_archive_url']=='https://files.abqinfo.com/'+r['proposed_r2_key']
    checks=r['collision_checks']
    assert checks['exact_key_exists'] is False and checks['case_insensitive_key_exists'] is False
    assert checks['same_size_live_objects']==[] and checks['known_same_sha256_other_inventory_rows']==[] and checks['semantic_review']
    assert r['uploader_whatif_result']=='WhatIf: upload not performed'
    assert r['size_bytes']<100000000
family=m['planning_impact_area_family']
assert set(family['component_ids'])==set(ORDER[:4]) and len(family['component_ids'])==4
assert family['complete_study_recovered'] is False and family['other_chapters_inferred'] is False and family['synthesized_pdf'] is False
assert 'incomplete' in family['state'] and 'one grouped' in family['future_public_treatment']
assert rows['src-99fe2201b73355c4']['status']==('placement assigned' if archived else 'approved for addition') and rows['src-99fe2201b73355c4']['checksum_sha256']!=SHA
assert 'Barelas sector plan is unique' in load('project-state/discovery/approved-inventory-backlog-prioritization-post-later-ms4-2026-09-25.json')['ranked_units'][0]['placement']
tool=m['tooling_readiness']
assert tool['credentials_accessible'] and tool['twelve_default_limit_whatif_probes_passed'] and tool['public_verifier_ready']
assert tool['max_object_bytes']==100000000 and tool['max_projected_storage_bytes']==10000000000 and tool['object_size_override_required'] is False
assert tool['projected_storage_headroom_bytes']==659468832
for artifact in (m,recon):
    assert artifact['r2_mutation'] is False and artifact['visitor_visible_content_changed'] is False
counts=Counter(r['status'] for r in rows.values())
assert {s:counts[s] for s in master['allowed_statuses']}==master['counts']==checkpoint['counts_by_status']
assert counts['approved for addition']==(27 if archived else 39) and counts['duplicate']==1518
historical='project-state/discovery/planning-documents-root-residual-decision-2026-09-20.json'
assert (ROOT/historical).read_bytes()==baseline(historical),'Historical decision was rewritten'
if not archived: assert (ROOT/'project-state/r2-inventory.json').read_text(encoding='utf-8-sig').replace('\r\n','\n')==baseline('project-state/r2-inventory.json').decode('utf-8-sig').replace('\r\n','\n')
for args in (['git','diff','--name-only',BASELINE,'--','content'],['git','ls-files','--others','--exclude-standard','content']):
    assert not subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
print('Historical Planning preflight: exact Barelas duplicate reconciled; 39 approved / 1518 duplicate; 12 originals / 122,249,326 bytes / 928 pages; normal-limit WhatIf passed; no R2/content mutation')
