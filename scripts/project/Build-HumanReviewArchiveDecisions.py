"""Explicit eligibility decisions for the three obsolete storage-only holds."""
import hashlib,json
from pathlib import Path

if __name__ == '__main__':
    from GovernedEntrypoint import require_tool_governance
    require_tool_governance(__file__)

ROOT=Path(__file__).resolve().parents[2]
F=ROOT/'project-state/discovery/human-review-reassessment-2026-09-26'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
base={r['id']:r for r in load(F/'baseline-records.json')};retrievals=load(F/'retrievals.json')['records']
live=load(F/'r2-baseline.json');saved=load(ROOT/'project-state/r2-inventory.json')
assert {(o['key'],o['size_bytes'],o['etag']) for o in live['objects']}=={(o['key'],o['size_bytes'],o['etag']) for o in saved['objects']}
specs=[
 ('src-4996854ae4e1a349','maps/open-space/volcano-view-trailhead-west-mesa-trails-2025.pdf','City of Albuquerque West Mesa open-space trail infrastructure','Volcano View Trailhead, West Mesa Open Space, and connected Albuquerque trail facilities','Explains City open-space access, trail distances and surfaces, public boundaries, and connections with Petroglyph National Monument.'),
 ('src-a738fd67bc6abac6','development-land-use/projects/unm-integrated-campus-plan-2025.pdf','University of New Mexico campus land-use and infrastructure planning','The plan devotes its main frameworks and zones to Albuquerque Main, North and South campuses and their transportation, housing, public realm and capital development','Documents substantial Albuquerque land-use, mobility and institutional infrastructure decisions; branch-campus context does not establish eligibility.'),
 ('src-c7fcd58b9998999c','transportation/transportation-plans/mrmpo-annual-performance-expenditure-report-ffy2025.pdf','MRMPO metropolitan transportation planning and expenditure accountability','The Albuquerque MPO work program records Albuquerque transportation studies, ABQ RIDE coordination, network safety, metropolitan development review and actual expenditures','Explains public planning deliverables and spending for the Albuquerque metropolitan transportation system, beyond generic agency administration.')]
updates=[];items=[]
for i,key,geo,connection,value in specs:
    row=base[i];r=next(x for x in retrievals if x['id']==i and x.get('page_count'))
    source=ROOT/r['saved_source'];data=source.read_bytes();sha=hashlib.sha256(data).hexdigest()
    assert len(data)==r['size_bytes']<=150000000 and sha==r['sha256']
    if row.get('checksum_sha256'):assert sha==row['checksum_sha256']
    assert r['size_bytes']==row['size_bytes'] and not r['truncated']
    assert not any(o['key'].casefold()==key.casefold() for o in live['objects'])
    same=[o for o in live['objects'] if o['size_bytes']==len(data)]
    assert not same,'Same-size public comparison required before archive'
    scope=dict(assessed_at='2026-09-26',geographic_institutional_scope=geo,specific_albuquerque_connection=connection,abqinfo_public_information_value=value,general_context_exclusion_test='Eligibility rests on substantive named Albuquerque infrastructure and policy, not publisher jurisdiction, incidental references, generic context or successful retrieval.',final_scope_decision='passes_both_gates',substantive_rationale=connection+'. '+value)
    rationale=value+' The complete unchanged original provides interpretable maps, frameworks or financial tables with substantial public value. The former 100 MB hold is superseded by the current 150000000-byte authorization; this decision adds no visitor-visible entry.'
    quality=dict(reviewed_document_content=True,visual_inspection_completed=True,standalone_public_value='high',information_density='visual_or_tabular' if i==specs[0][0] else 'substantial',series_relationship='standalone',publication_form='standalone',rationale=rationale,page_count=r['page_count'],extracted_word_count=r['word_count'],visual_inspection_evidence='tmp/pdfs/human-review/'+i+'.png',visual_review='Complete map reviewed; all 50 report pages reviewed; representative UNM pages across the complete plan reviewed alongside full extracted text.')
    description=row.get('description')
    if i==specs[1][0]:description='Sets out UNM’s May 2025 campus development framework, including Albuquerque Main, North and South campus land use, housing, transportation, open space, building zones, design guidelines and implementation priorities. The full original also contains branch-campus frameworks, which provide context rather than the basis for ABQInfo inclusion.'
    if i==specs[2][0]:description='Documents MRMPO work, deliverables and expenditures during FFY 2025, including Albuquerque transportation planning, safety, traffic monitoring, development review, incident management, transit studies, ABQ RIDE coordination, consultant work and Title VI compliance.'
    changes=dict(status='approved for addition',scope_assessment=scope,quality_assessment=quality,review_reason=None,exclusion_reason=None,validation_status='Positive scope and quality reviewed; obsolete 100 MB gate removed; exact current official-source original verified; authorized archive preflight complete',local_path=r['saved_source'],size_bytes=len(data),checksum_sha256=sha,description=description,processing_notes=row.get('processing_notes',[])+['2026-09-26 owner-invoked human-review reassessment: obsolete storage-only hold cleared after current-source exact size/SHA-256, substantive scope, visual quality and complete live storage reconciliation. Historical approval warnings remain dated evidence, not current authorization gates.'])
    updates.append(dict(id=i,changes=changes))
    items.append(dict(id=i,r2_key=key,source_path=r['saved_source'],source_url=r['url'],size_bytes=len(data),sha256=sha,scope_assessment=scope,quality_assessment=quality,same_size_baseline_objects=same))
plan=dict(authorization_artifact=(F/'authorization.json').relative_to(ROOT).as_posix(),baseline=(F/'r2-baseline.json').relative_to(ROOT).as_posix(),maximum_object_bytes=150000000,maximum_storage_bytes=13000000000,baseline_bytes=live['total_bytes'],added_bytes=sum(x['size_bytes'] for x in items),items=items)
assert plan['baseline_bytes']+plan['added_bytes']<=plan['maximum_storage_bytes']
for name,v in [('archive-decisions.json',updates),('archive-plan.json',plan)]:
    (F/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Three eligible unchanged originals;',plan['added_bytes'],'added bytes planned')
