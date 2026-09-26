#!/usr/bin/env python3
"""Exact family/source/key/public/lifecycle and zero-publication campaign contract."""
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ART='project-state/discovery/approved-backlog-background-archive-campaign-2026-09-26.json'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def git_json(sha,p):return json.loads(subprocess.check_output(['git','show',sha+':'+p],cwd=ROOT).decode('utf-8-sig'))
def sha(p):return hashlib.file_digest((ROOT/p).open('rb'),'sha256').hexdigest()
d=load(ART);locked=git_json('38828d2',ART)
assert d['baseline_git_sha']=='c054c9af67f1984051462d75727bd7fb05ea3ed2'
assert len(d['records'])==27 and len(d['generated_packages'])==7
assert {r['id'] for r in d['records']}=={r['id'] for r in locked['records']}
assert d['exclusions']==locked['exclusions']
assert d['visitor_visible_content_changed'] is False
assert d['project_storage_limit_bytes']==10000000000
assert d['capacity_plan']==locked['capacity_plan']
baseline_inventory=git_json(d['baseline_git_sha'],'project-state/master-inventory.json')
inventory=load('project-state/master-inventory.json');rows={r['id']:r for r in inventory['candidates']};prior={r['id']:r for r in baseline_inventory['candidates']}
assert len(rows)==len(prior)==7137
assert {r['id'] for r in baseline_inventory['candidates'] if r['status']=='approved for addition'}=={r['id'] for r in d['records']}
counts=Counter(r['status'] for r in rows.values());assert {s:counts[s] for s in inventory['allowed_statuses']}==inventory['counts']
changed={rid for rid in rows if rows[rid]!=prior[rid]}
done=[r for r in d['records'] if r.get('inventory_reconciled')]
assert changed=={r['id'] for r in done},'Unrelated inventory rows changed'
allowed={'status','r2_key','r2_url','r2_etag','r2_last_modified','local_path','file_type','proposed_canonical_page','processing_notes','validation_status','updated_at'}
locked_rows={r['id']:r for r in locked['records']+locked['generated_packages']}
verified=[]
for r in d['records']+d['generated_packages']:
    old=locked_rows[r['id']]
    for field in ('id','family','classification','size_bytes','expected_sha256','expected_pages','r2_key','container_type','staged_path'):
        assert r[field]==old[field],(r['id'],field)
    p=ROOT/r['staged_path'];assert p.stat().st_size==r['size_bytes'] and sha(r['staged_path'])==r['expected_sha256']
    if r['id']=='generated-dpm-2018':
        assert r['outcome']=='deferred_human_review' and not r['archival_authorized']
        assert rows['src-7e7af2af147d96d7']==prior['src-7e7af2af147d96d7'] and rows['src-7e7af2af147d96d7']['status']=='requires human review'
        continue
    assert r['source_exact_verified']
    if r['container_type']=='PDF':
        assert r['qa']['structural_result']=='opens_without_password_or_repair'
        assert r['qa']['rendered_pages']==r['page_count']
        assert r['qa']['representative_visual_qa']=='passed_agent_visual_inspection_opening_middle_final'
    else:
        assert r['qa']['original_unchanged'] and r['qa']['no_conversion']
        assert r['qa']['dimensions']=={'xl/worksheets/sheet1.xml':{'ref':'A1:S15'}}
    if r['classification']=='unchanged_City_original':
        assert r['source_GET']['http_status']==200 and r['fresh_sha256']==r['expected_sha256'] and r['fresh_size_bytes']==r['size_bytes']
        assert rows[r['id']]['scope_assessment']==prior[r['id']]['scope_assessment']
        assert rows[r['id']]['checksum_sha256']==r['expected_sha256']
        assert {k for k in rows[r['id']] if rows[r['id']][k]!=prior[r['id']].get(k)}<=allowed
    else:
        assert all(x['rendered_source_pages_pixel_identical'] for x in r['component_integrity'])
        assert sha(r['component_manifest'])==d['governing_artifact_hashes'][r['component_manifest']]
    assert not r['same_sha256_inventory_rows'] and not r['exact_or_casefold_key_collisions']
    if r['outcome']=='archive_complete':
        v=r['public_verification'];assert v['byte_identical'] is True and v['verified_at']
        assert v['size_bytes']==r['size_bytes'] and v['checksum_sha256']==r['expected_sha256']
        assert v['public_url']=='https://files.abqinfo.com/'+r['r2_key']
        assert r['upload_intent']['key_was_absent'] and r['size_bytes']<=150000000
        verified.append(r)
        if r['classification']=='unchanged_City_original':
            row=rows[r['id']];assert row['status']=='placement assigned' and row['r2_key']==r['r2_key'] and row['r2_url']==v['public_url']
            assert row['proposed_canonical_page']==r['canonical_page']
    elif not r['r2_key']:
        assert r['outcome']=='prepared_unuploaded_unresolved_archive_namespace'
        assert rows[r['id']]==prior[r['id']]
    else:assert d['state']!='complete_background_campaign',r['id']
baseline=load(d['baseline_r2_artifact']);current=load('project-state/r2-inventory.json');objects={o['key']:o for o in current['objects']};old={o['key']:o for o in baseline['objects']}
assert (len(old),baseline['total_bytes'])==(1249,9340531168)
for k,o in old.items():assert all(objects[k][f]==o[f] for f in ('key','size_bytes','etag'))
assert set(objects)-set(old)=={r['r2_key'] for r in verified}
assert current['object_count']==len(objects)==1249+len(verified)
assert current['total_bytes']==sum(o['size_bytes'] for o in objects.values())==9340531168+sum(r['size_bytes'] for r in verified)
for r in verified:assert objects[r['r2_key']]['size_bytes']==r['size_bytes'] and objects[r['r2_key']]['etag']==r['r2_etag']
assert subprocess.check_output(['git','rev-parse','HEAD:content'],cwd=ROOT,text=True).strip()==d['content_tree_sha256_baseline']
assert not subprocess.check_output(['git','diff','--name-only',d['baseline_git_sha'],'--','content'],cwd=ROOT).strip()
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','content'],cwd=ROOT).strip()
for path,expected in d['governing_artifact_hashes'].items():assert sha(path)==expected,path
if d['state']=='complete_background_campaign':
    assert len(verified)==30 and sum(r['size_bytes'] for r in verified)==29783028
    assert counts['approved for addition']==3 and counts['placement assigned']==38
    assert d['accounting']['pre_existing_objects_unchanged'] and d['accounting']['saved_live_key_size_etag_match']
    final=load(d['final_live_listing_artifact']);assert current['objects']==final['objects']
    checkpoint=load('project-state/checkpoint.json');assert checkpoint['counts_by_status']==inventory['counts']
    dpm=checkpoint['dpm_annual_consolidation']
    assert dpm['state']=='corrected_packets_partially_archived_2018_human_review_deferred'
    assert [(p['year'],p['archive_outcome']) for p in dpm['packets']]==[(2014,'archive_complete'),(2015,'archive_complete'),(2016,'archive_complete'),(2017,'archive_complete'),(2018,'deferred_human_review')]
    assert not any(o['key']==locked_rows['generated-dpm-2018']['r2_key'] for o in current['objects'])
print(f'PASS: 27 approved originals / seven named generated outputs; {len(verified)} exact public archives; unchanged baseline objects and noncampaign inventory; no content changes.')
