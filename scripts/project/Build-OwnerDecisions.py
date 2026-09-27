"""Create explicit owner dispositions and absent-key original archive plan."""
from OwnerDecisions import *
a=load(F/'authorization.json');base={r['id']:r for r in load(F/'baseline-records.json')};inspect={r['id']:r for r in load(F/'inspection.json')};live=load(F/'r2-baseline.json');updates=[];items=[]
keys={'src-10209c5fcdce2906':'construction-stormwater-bmp-details-draft-2026-02-02.pdf','src-30b5123b798a30f3':'dpm-ch23-section-3-3-pavement-design-draft-2017-10-12.pdf','src-3ff7d77c284d06a8':'dpm-ch23-section-3-5-pedestrian-facilities-draft.pdf','src-967a816e5ddac695':'dpm-ch23-section-3-9-7-median-turn-lane-draft-2017-11-27.pdf','src-dda1163373f3754c':'dpm-chapter-7-proposed-changes-markups-2026-04-14.pdf','src-f904f6d8bf3787f5':'dpm-chapter-7-proposed-changes-letter-2026-02-24.pdf'}
for p in load(F/'baseline-owner-packages.json'):
 policy=a['decisions'][p['package_id']]
 for i in p['affected_record_ids']:
  r=base[i];notes=r.get('processing_notes',[])+['2026-09-26 explicit owner decision: '+policy+' Durable authority: '+(F/'authorization.json').relative_to(ROOT).as_posix()]
  c=dict(review_reason=None,processing_notes=notes)
  if p['package_id'] in ['fiber-correspondence','wireless-checklist']:
   c.update(status='excluded',exclusion_reason='Owner editorial exclusion: '+policy,validation_status='Owner decision applied; research and provenance retained; no public-facing publication authorized.')
   if p['package_id']=='wireless-checklist':
    scope=dict(r['scope_assessment']);scope.update(final_scope_decision='excluded_insufficient_abqinfo_usefulness',abqinfo_public_information_value='Owner prefers final wireless regulations over this staff application checklist.',general_context_exclusion_test='Specific Albuquerque code references do not justify a separate staff-routing record.',substantive_rationale='Owner resolved the genuine significance borderline by excluding the checklist; retain the prior assessment and research as historical evidence.');c['scope_assessment']=scope
  else:
   x=inspect[i];art=p['package_id']=='art-advocacy-primary-sources'
   connection='Substantive design, public-comment and participant evidence about Albuquerque Rapid Transit on Central Avenue.' if art else 'City of Albuquerque development-process proposals for local street design, pedestrian facilities, pavement criteria, stormwater protection or underground utility conflicts.'
   value='Explains attributed public positions and design alternatives in the history of a major Albuquerque transit investment.' if art else 'Explains how Albuquerque infrastructure design policy was proposed and debated; the complete historical draft series permits comparison with adopted DPM records without implying enactment.'
   scope=dict(assessed_at='2026-09-26',geographic_institutional_scope='Albuquerque ART historical advocacy' if art else 'Albuquerque DPM historical infrastructure proposals',specific_albuquerque_connection=connection,abqinfo_public_information_value=value,general_context_exclusion_test='Eligibility rests on substantive named Albuquerque infrastructure policy and historical evidence, not generic engineering guidance, incidental geography, publisher authenticity or successful archival.',final_scope_decision='passes_both_gates',substantive_rationale=connection+' '+value+' Owner explicitly approved this historical presentation.')
   relation='Three attributed ART advocacy originals; meeting account is a participant account, not approved minutes.' if art else 'Six retained historical DPM proposal originals, presented as one curated draft/proposal series. Chapter 7 proposal letter and marked-up draft are complementary components. Existing adopted DPM records remain distinct; no adoption or supersession is inferred. Existing section 3.9.6 draft src-75935732f3f11f34 is a related sibling. Preserve the 2017 draft dates, 02/02/26 BMP draft date, February 24 2026 letter and April 14 2026 delivery filenames; markup footer September 4 2020 is a base-document printing date.'
   quality=dict(reviewed_document_content=True,visual_inspection_completed=True,visual_inspection_evidence=x['visual_sheet'],visual_review='All pages rendered as contact sheets and visually reviewed with extracted text and saved family research.',page_count=x['page_count'],extracted_word_count=x['word_count'],standalone_public_value='high' if art else 'series_component',information_density='visual_or_tabular' if x['word_count']==0 else 'substantial',series_relationship=relation,publication_form='attributed_historical_evidence' if art else 'historical_proposal_series',rationale=value+' '+relation+' '+policy)
   if x['word_count']==0:quality['limited_content_exception']='Fourteen image-only annotated ART corridor drawings contain substantive design comments and cross sections; zero extractable words reflects scanning rather than skeletal content.'
   desc=(r.get('description') or r['title'])+' Historical evidence only. '+policy
   c.update(status='placement assigned' if art else 'approved for addition',scope_assessment=scope,quality_assessment=quality,exclusion_reason=None,validation_status='Owner historical-retention decision applied; original quality and identity reviewed; no visible content changes.',local_path=x['source_path'],size_bytes=x['size_bytes'],checksum_sha256=x['sha256'],description=desc)
   if not art:
    key='development-land-use/development-process/history/'+keys[i]
    assert not any(o['key'].casefold()==key.casefold() for o in live['objects'])
    assert not any(o['size_bytes']==x['size_bytes'] for o in live['objects']), 'Same-size comparison required'
    items.append(dict(id=i,r2_key=key,source_path=x['source_path'],source_url=r.get('direct_file_url') or r['source_url'],size_bytes=x['size_bytes'],sha256=x['sha256']))
   if i=='src-10209c5fcdce2906':c['processing_notes'].append('Original reviewed 10-page DRAFT 02/02/26 remains canonical at SHA-256 '+x['sha256']+'. Later 11-page BMP download (1811437 bytes, SHA-256 875840b89df30f58eb2ccb45723ae869502b2e7fc13d36aaf68a522a7b14e8ce) is different; retained as separate retrieval evidence, never used to replace this original.')
  updates.append(dict(id=i,changes=c,owner_package=p['package_id']))
assert set(base)=={x['id'] for x in updates}
save(F/'decisions.json',updates)
save(F/'archive-plan.json',dict(authorization_artifact=(F/'authorization.json').relative_to(ROOT).as_posix(),baseline=(F/'r2-baseline.json').relative_to(ROOT).as_posix(),maximum_object_bytes=150000000,maximum_storage_bytes=13000000000,added_bytes=sum(x['size_bytes'] for x in items),items=items))
print('11 decisions; six new archive originals;',sum(x['size_bytes'] for x in items),'bytes')
