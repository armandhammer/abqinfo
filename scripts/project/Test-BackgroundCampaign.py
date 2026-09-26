#!/usr/bin/env python3
"""Production guard fixtures plus active-population/recovery contract."""
import copy, hashlib, json, runpy, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
policy=load(ROOT/'project-state/r2-storage-policy.json')
assert policy['maximum_projected_r2_bytes']==13000000000 and policy['maximum_projected_r2_gb_decimal']==13
profile=load(ROOT/'project-state/campaign-profiles/ordinary-review-large.json')
assert profile['maximum_object_bytes']==150000000
assert not any(profile['authorization'][f] for f in ['r2_delete_or_overwrite','visitor_visible_changes','protected_or_human_review_families'])
source=(ROOT/'scripts/project/Invoke-BackgroundCampaignArchive.ps1').read_text(encoding='utf-8')
guard=source[source.index('function Guard {'):source.index('# The complete listing')]
folder=ROOT/'tmp/background-guard-regression';folder.mkdir(parents=True,exist_ok=True)
(folder/'Get-R2Inventory.ps1').write_text("param([string]$OutputPath)\nCopy-Item -LiteralPath $fixtureListing -Destination $OutputPath -Force\n",encoding='utf-8')
baseline={'objects':[{'key':'a/one.pdf','size_bytes':3,'etag':'One'}]}
intent={'r2_key':'c/new.pdf','fresh_source_qa':{'size_bytes':7},'upload_intent':{'key_was_absent':True}}
valid={'objects':baseline['objects']+[{'key':'c/new.pdf','size_bytes':7,'etag':'New'}],'total_bytes':10000000001}
cases=[('above_old_ceiling_passes',valid,[intent],True)]
def case(name,change,records=None):
 d=copy.deepcopy(valid);change(d);cases.append((name,d,[intent] if records is None else records,False))
case('missing_old',lambda d:d['objects'].pop(0))
case('changed_old_size',lambda d:d['objects'][0].update(size_bytes=4))
case('changed_old_etag',lambda d:d['objects'][0].update(etag='one'))
case('unknown_object',lambda d:d['objects'][-1].update(key='unknown'))
case('wrong_intent_size',lambda d:d['objects'][-1].update(size_bytes=8))
case('duplicate_intent',lambda d:None,[intent,intent])
case('casefold_collision',lambda d:d['objects'].append({'key':'A/ONE.pdf','size_bytes':3,'etag':'other'}))
case('above_new_ceiling',lambda d:d.update(total_bytes=13000000001))
tests=[]
for name,listing,intents,expected in cases:
 lp=folder/(name+'.json');lp.write_text(json.dumps(listing),encoding='utf-8');tests.append(dict(name=name,listing=str(lp),intents=intents,expected_pass=expected))
(folder/'fixtures.json').write_text(json.dumps(dict(baseline=baseline,tests=tests)),encoding='utf-8')
driver=folder/'Run.ps1';driver.write_text("Set-StrictMode -Version Latest\n$ErrorActionPreference='Stop'\n"+guard+"\n$policy=[pscustomobject]@{maximum_projected_r2_bytes=13000000000}\n$fx=Get-Content (Join-Path $PSScriptRoot 'fixtures.json') -Raw|ConvertFrom-Json\n$baseline=$fx.baseline\n$guardPath=Join-Path $PSScriptRoot 'result.json'\nforeach($test in $fx.tests){$fixtureListing=$test.listing;$allFamilyRecords=@($test.intents);$passed=$false;try{$result=Guard;$passed=$true}catch{};if($passed -ne $test.expected_pass){throw ('Unexpected guard result: '+$test.name)}}\n",encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(driver)],cwd=ROOT,check=True)
size_guard=source[source.index('function Assert-SameSizeCandidates'):source.index('# The complete listing')]
source_hash='a'*64;other_hash='b'*64
obj={'key':'existing.pdf','size_bytes':54320,'etag':'Current'}
receipt=dict(obj,source_sha256=source_hash,public_get_size_bytes=54320,public_get_sha256=other_hash,verified_at='2026-09-26')
size_cases=[dict(name='negative_full_get_passes',receipt=receipt,expected_pass=True)]
for name,changes in [('exact_hash_refused',dict(public_get_sha256=source_hash)),('wrong_etag_refused',dict(etag='Stale')),('wrong_size_refused',dict(public_get_size_bytes=3)),('wrong_source_refused',dict(source_sha256='c'*64)),('invalid_hash_refused',dict(public_get_sha256='not-a-hash'))]:
 size_cases.append(dict(name=name,receipt=dict(receipt,**changes),expected_pass=False))
size_cases.append(dict(name='missing_evidence_refused',receipt=None,expected_pass=False))
size_cases.append(dict(name='duplicate_evidence_refused',receipt=receipt,duplicate=True,expected_pass=False))
(folder/'size-fixtures.json').write_text(json.dumps(dict(object=obj,source_hash=source_hash,tests=size_cases)),encoding='utf-8')
size_driver=folder/'SameSize.ps1'
size_driver.write_text("Set-StrictMode -Version Latest\n$ErrorActionPreference='Stop'\n"+size_guard+"\n$fx=Get-Content (Join-Path $PSScriptRoot 'size-fixtures.json') -Raw|ConvertFrom-Json\nforeach($test in $fx.tests){$record=[pscustomobject]@{fresh_source_qa=[pscustomobject]@{checksum_sha256=$fx.source_hash};same_size_r2_disambiguation=@()};if($test.receipt){$record.same_size_r2_disambiguation=@($test.receipt);if($test.PSObject.Properties['duplicate']){$record.same_size_r2_disambiguation+=@($test.receipt)}};$passed=$false;try{Assert-SameSizeCandidates @($fx.object) $record;$passed=$true}catch{};if($passed -ne $test.expected_pass){throw ('Unexpected size guard result: '+$test.name)}}\n",encoding='utf-8')
subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(size_driver)],cwd=ROOT,check=True)

active=ROOT/'project-state/active-campaign.json'
if active.exists():
 pointer=load(active);d=load(ROOT/pointer['campaign_artifact'])
 # Seal this completed campaign at the next owner task's immutable baseline.
 # The independent reassessment audit constrains every subsequent changed row,
 # object and queue. Never grant this profile protected-family authorization.
 later=ROOT/'project-state/discovery/human-review-reassessment-2026-09-26/authorization.json'
 if later.exists() and d['state']=='complete_background_campaign' and d['campaign_id']=='ordinary-review-large-2026-09-26-third':
  sealed_commit=load(later)['baseline_commit']; live_load=load
  sealed_paths={'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/discovery/mission-scope-borderline-human-review-queue.json'}
  def load(p):
   relative=Path(p).resolve().relative_to(ROOT).as_posix()
   if relative in sealed_paths:return json.loads(subprocess.check_output(['git','show',sealed_commit+':'+relative],cwd=ROOT).decode('utf-8-sig'))
   return live_load(p)
 for receipt in d.get('validation_history',[]):
  assert hashlib.sha256((ROOT/receipt['log_artifact']).read_bytes()).hexdigest()==receipt['log_sha256'],'Durable validation log changed'
 s=load(ROOT/d['selection_artifact'])
 inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
 prior={r['id']:r for r in json.loads(subprocess.check_output(['git','show',d['baseline_commit']+':project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))['candidates']}
 digest=runpy.run_path(str(ROOT/'scripts/project/BackgroundCampaign.py'))['digest']
 assert s['baseline_row_digests']=={i:digest(r) for i,r in prior.items()}
 allowed={q['id'] for q in s['all_pending_records']}|{r['id'] for p in d['archive_family_artifacts'] for r in load(ROOT/p)['records']}|{r['id'] for r in d['recovery_records'] if r.get('review_authorized')}
 changed={i for i in rows if rows[i]!=prior[i]}
 assert changed<=allowed,('Unaccounted/protected row changes',changed-allowed)
 assert not changed&set(s['gated_pending_ids'])
 for i in changed:
  for f in ['source_url','direct_file_url','discovery_path','cited_predecessors']:assert rows[i][f]==prior[i][f]
  assert set(prior[i]['processing_notes'])<=set(rows[i]['processing_notes'])
 assert len({r['id'] for r in d['resolved_records']})==len(d['resolved_records'])
 family_records={r['id']:r for f in s['candidate_families'] for r in load(ROOT/f['evidence_artifact'])['records']}
 resolved={r['id']:r for r in d['resolved_records']}
 for i in {q['id'] for q in s['all_pending_records']}-resolved.keys():assert rows[i]==prior[i],('Unresolved row changed',i)
 for i,x in resolved.items():
  r=family_records[i];assert r['review_complete'] and r['disposition']==x['decision']
  assert r['quality_assessment']['substantive_rationale'] and r['mission_scope_assessment']['substantive_rationale']
  assert rows[i]['status']==x['decision'] or x['decision']=='approved for addition' and rows[i]['status']=='placement assigned'
  qa=r.get('fresh_source_qa')
  if qa:
   p=ROOT/qa['staged_path'];assert p.stat().st_size==qa['size_bytes'] and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==qa['checksum_sha256']
   assert qa['source_exact_verified'] and qa['representative_visual_qa']=='passed_agent_inspection_opening_middle_ending'
  if x['decision']=='approved for addition':
   assert rows[i]['scope_assessment']['final_scope_decision']=='passes_both_gates' and r['r2_key']
   for field in ['visual_inspection','standalone_public_value','information_density','series_component_relationship','intended_publication_form','substantive_rationale']:assert r['quality_assessment'][field]
  if x['decision']=='duplicate':
   canonical=rows[r['canonical_candidate_id']];assert (rows[i]['size_bytes'],rows[i]['checksum_sha256'])==(canonical['size_bytes'],canonical['checksum_sha256'])
 baseline=load(ROOT/d['baseline_r2_artifact']);current=load(ROOT/'project-state/r2-inventory.json')
 objects={o['key']:o for o in current['objects']};old={o['key']:o for o in baseline['objects']}
 for k,o in old.items():assert (objects[k]['size_bytes'],objects[k]['etag'])==(o['size_bytes'],o['etag'])
 receipts={r['key']:r for r in d['archive_objects']}
 # Pending intents permit a crash after PUT; completion requires exact receipt coverage.
 intents={r['r2_key']:r for p in d['archive_family_artifacts']+[f['evidence_artifact'] for f in s['candidate_families']] for r in load(ROOT/p)['records'] if r.get('upload_intent')}
 assert objects.keys()-old.keys()<=intents.keys()
 assert current['total_bytes']==sum(o['size_bytes'] for o in objects.values())<=13000000000
 assert len({k.casefold() for k in objects})==len(objects)
 for k,r in receipts.items():
  v=r['public_verification'];assert v['byte_identical'] and (v['size_bytes'],v['checksum_sha256'])==(r['size_bytes'],r['checksum_sha256'])
  assert r['size_bytes']<=150000000 and objects[k]['etag']==r['etag'] and rows[r['id']]['r2_key']==k
 assert not subprocess.check_output(['git','diff',d['baseline_commit'],'--name-only','--','content'],cwd=ROOT).strip()
 assert subprocess.check_output(['git','rev-parse','HEAD:content'],cwd=ROOT,text=True).strip()==d['content_tree_baseline']
 if d['state']=='complete_background_campaign':assert objects.keys()-old.keys()==receipts.keys()
 if d.get('next_queue_artifact'):
  queue=load(ROOT/d['next_queue_artifact']);pending={i for i,r in rows.items() if r['status']=='pending review'}
  gates=set(queue['gated_pending_ids']);blocked=set(queue['source_or_structural_blocked_pending_ids']);ungated=set(queue['ungated_pending_ids'])
  assert pending==set(queue['pending_ids'])==gates|blocked|ungated
  assert not (gates&blocked or gates&ungated or blocked&ungated)
  assert len(ungated)==queue['ungated_pending_count'] and queue['genuinely_actionable_ungated_pending_count']==0
  assert ungated=={r['id'] for r in queue['unresolved_ungated_prerequisites']}
  assert queue['mission_borderline_queue_size']==load(ROOT/'project-state/discovery/mission-scope-borderline-human-review-queue.json')['unresolved_count']<=20
print('PASS: background framework policy, actual guard failures, locked population, immutable baseline and exact archive receipts.')
