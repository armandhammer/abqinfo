#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=json.loads((ROOT/'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json').read_text(encoding='utf-8'))
r2={r['key'] for r in json.loads((ROOT/'project-state/r2-inventory.json').read_text(encoding='utf-8-sig'))['objects']}
assert a['scope_candidate_ids']==['src-1f8378fe0d939884','src-1ce9fae6e4b2e675','src-a5f4c28aefd1ce20','src-57017bee270744dd','src-68d5d6b446b98b35','src-b07a77c5f6cd79b3','src-84c88a71842b2ed1']
assert a['state']=='archive_preparation_complete_external_r2_upload_and_public_byte_verification_gated'
assert a['superseded_by_mission_scope_audit']['historical_evidence_preserved'] is True
assert a['superseded_by_mission_scope_audit']['r2_or_publication_action_authorized'] is False
assert a['summary']=={'source_verification_passed':7,'docx_visual_qa_passed':5,'pdf_render_qa_passed':2,'r2_key_collisions':0,'total_source_bytes':88893781}
assert not any(a['safeguards_observed'].values())
for n,r in enumerate(a['records'],1):
 assert r['series_order']==n and r['proposed_r2_key'] not in r2 and r['r2_action']=='none'
 assert r['canonical_placement']['page']=='content/transportation/roadway-projects/studies.md'
 assert r['source_evidence']['source_byte_verification']=='passed_re_fetched_authoritative_original'
 assert r['visual_qa']['result'].startswith('passed_')
 if n==1: assert 'benign visual observation' in r['visual_qa']['detail']
 assert all(r['quality_assessment'][f] for f in ('visual_inspection','measured_content','standalone_public_value','information_density','series_component_relationship','intended_publication_form','rationale'))
print('PASS: NMDOT seven-record archive preparation preserves exact originals, source evidence, Roadway Studies placement, completed visual QA, and the external R2 gate without mutation.')
