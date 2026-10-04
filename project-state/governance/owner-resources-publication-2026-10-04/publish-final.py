"""Publish only the two newly rendered owner resources under durable scope/value findings."""
import copy,sys,subprocess
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
P=S.prefix(S.B)
S.G.active_check('mutation','document_review',S.NEW)
rows={r['id']:r for r in S.G.load('project-state/master-inventory.json')['candidates']}
app,dr=S.NEW;findings={}
scope=copy.deepcopy(rows[dr]['scope_assessment'])
appscope=dict(assessed_at='2026-10-04',geographic_institutional_scope='City of Albuquerque AGIS / Office of Neighborhood Coordination recognized associations and coalitions.',specific_albuquerque_connection='Rendered map depicts named Albuquerque neighborhood associations and local coalitions, their boundaries and areas outside City limits, including Downtown, Barelas, North Valley and the district coalitions.',abqinfo_public_information_value='Address search and mapped civic organizations help readers identify local association geography for City participation and development-review issues.',general_context_exclusion_test='This maps specific recognized Albuquerque civic organizations and their relation to City geography; it is not generic contextual mapping or incidental regional data. The website directory serves a separate organization-access function.',final_scope_decision='passes_both_gates',substantive_rationale='The actual rendered application provides meaningful Albuquerque civic geography and a working address-search and legend interface. It complements the association website directory and existing City reference maps without duplicating a separate existing application entry. One live City map entry gives readers useful neighborhood context without creating a copied roster, static snapshot or new page.')
for rid,sc,evidence in [(app,appscope,4),(dr,scope,5)]:
    render=S.G.load(P+f'evidence-{evidence}.json')
    words=len(render['steps'][0]['visible_text'].split())
    if rid==app:
        q=dict(document_function='Live City civic-reference map of recognized neighborhood associations and coalitions.',substantive_content='Rendered labeled association polygons and coalition outlines; legend identifies recognized associations, eight coalition categories and areas outside City limits.',durable_public_usefulness='Helps residents connect addresses and neighborhoods with City-recognized civic organizations and participation geography.',information_density='A complete labeled citywide map with search, zoom, information and legend controls presents meaningful neighborhood organization geography.',unique_information='Mapped recognized association and coalition geography complements website access in the ONC directory; no exact app or equivalent dedicated entry exists in the baseline content.',rationale='The actual map renders recognizable Albuquerque neighborhood boundaries and coalition geography. Its address search and legend operate successfully in isolated installed desktop Chrome. This provides substantive civic reference value alongside the directory, while one live link avoids redundant association entries or an invented archive.')
        description='Maps City-recognized neighborhood associations and coalitions, with address search and a legend. This maintained civic reference shows organization geography; it is not a legal boundary determination.'
        limitation='Address search for 1 Civic Plaza NW returned a local result and zoomed the map. Legend and information controls work. A tested map click did not expose association attributes; publication makes no promise about popup fields. No account or sign-in required, no page errors observed. Data are a maintained service, not an archived static snapshot or certified boundary determination.'
    else:
        q=dict(document_function='Maintained official ONC directory linking submitted websites of City-recognized neighborhood associations.',substantive_content='Rendered named local association website links and contacts, with explicit submitted-site limitation, independent association maintenance and HOA exclusion.',durable_public_usefulness='Directs readers to recognized neighborhood-level civic organizations for neighborhood issues and participation in City processes.',information_density='One organized directory provides direct access to numerous named associations instead of copying an unstable roster into ABQInfo.',unique_information='Organization website access complements mapped association geography and the existing task-force and facilitated-meeting policy references.',rationale='The rendered maintained City directory directly connects readers with recognized local civic organizations. Its explicit website-submission and HOA limitations are retained in the concise entry. Associations maintain their own sites, so ABQInfo links the directory once rather than publishing an unverified roster or duplicating individual organizations.')
        description='The City Office of Neighborhood Coordination links websites submitted by recognized neighborhood associations. Associations maintain their own sites; the directory excludes HOA websites.'
        limitation='Directory is limited to submitted websites, not all recognized associations; HOA websites excluded. Individual association sites are maintained independently and are not individually endorsed or freshly audited by this publication.'
    q.update(standalone_public_value='high',publication_form='live_service',series_relationship='standalone',reviewed_document_content=True,visual_inspection_completed=True,page_count=0,extracted_word_count=words)
    findings[rid]=dict(candidate_id=rid,title=rows[rid]['title'],source_url=rows[rid]['source_url'],scope_assessment=sc,quality_assessment=q,limitations=limitation,description=description,render_evidence=P+f'evidence-{evidence}.json',duplicate_review='Exact URL/app ID absent in baseline; existing generic map library/demographic geography links are different resources. One canonical entry per new resource with internal cross-references only.',placement='content/maps-data/maps.md#citywide-reference-maps' if rid==app else 'content/development-land-use/development-process.md#current-city-review-process')
if not (S.G.ROOT/(P+'review-final.json')).exists():
    S.G.write_once(P+'review-final.json',dict(artifact_type='final_new_resource_scope_quality_placement_decisions',reviewed_at=S.now(),records=findings,existing_six_reviews='Binding and unchanged; not re-reviewed.'))
    S.bind(P+'review-final.json','decision-'+S.B+'-final-neighborhood-resources','Implement the two exact owner resources once each using the rendered authoritative titles, positive scope/value findings, concise descriptions, limitations and canonical placements in this artifact; use only internal cross-references, no new pages or archives.',dict(task_ids=[S.B],candidate_ids=S.NEW,pages=[S.PAGES[0],S.PAGES[6]]))
else:
    findings=S.G.load(P+'review-final.json')['records']
S.refresh(S.B)
updates=[]
for rid,f in findings.items():
    quality=dict(decision='passes',assessed_at=S.now(),evidence=[P+'review-final.json',f['render_evidence']],assessment=f['quality_assessment'])
    updates.append(dict(id=rid,changes=dict(status='approved for addition',scope_assessment=f['scope_assessment'],quality_assessment=f['quality_assessment'],publication_quality_decision=quality,description=f['description'],proposed_canonical_page=f['placement'].split('#')[0],provenance_status='Exact official URL rendered in isolated installed Google Chrome; City maintained live service verified.',validation_status='Rendered scope and publication-quality review passed; final content/preview validation pending.',processing_notes=rows[rid]['processing_notes']+['2026-10-04 rendered owner resource review passes scope and publication quality; canonical placement, limitations and duplicate analysis saved in '+P+'review-final.json.'])))
S.save(P+'new-source-updates.json',updates);S.refresh(S.B)
if not all(rows[rid].get('publication_quality_decision',{}).get('decision')=='passes' for rid in S.NEW):
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'new-source-updates.json'],check=True)
S.refresh(S.B)
for rid in S.NEW:
    f=findings[rid];page,anchor=f['placement'].split('#')
    if rows[rid]['status']=='implemented':
        assert f['source_url'] in (S.G.ROOT/page).read_text(encoding='utf-8')
        continue
    S.G.active_check('mutation','content_implementation',[rid],[page])
    raw=(S.G.ROOT/page).read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8')
    if rid==app:
        marker='### Regional Long-Range Transportation Maps'
        title=f['title']+' (live City map)'
        ref='[Neighborhood Association Websites](/development-land-use/development-process/#current-city-review-process) provides links to association websites.'
    else:
        marker='## Development Policy References'
        title=f['title']+' (live City directory)'
        ref='Use the [recognized association and coalition map](/maps-data/maps/#citywide-reference-maps) to explore neighborhood geography.'
    block=f'- [{title}]({f["source_url"]})\n\n  {f["description"]}\n\n  {ref}\n\n'
    assert text.count(marker)==1 and f['source_url'] not in text
    (S.G.ROOT/page).write_bytes(text.replace(marker,block.replace('\n',nl)+marker).encode('utf-8'))
    row=next(r for r in S.G.load('project-state/master-inventory.json')['candidates'] if r['id']==rid)
    S.save(P+'new-source-updates.json',[dict(id=rid,changes=dict(status='implemented',implementation_location=f['placement'],implementation_locations=[f['placement']],cross_listing_approved=False,validation_status='Implemented on unmerged content branch; final validation/preview pending; not live.',processing_notes=row['processing_notes']+['One canonical live resource entry and internal cross-reference implemented under final rendered review.']))])
    S.refresh(S.B)
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'new-source-updates.json'],check=True)
    S.event(S.B,'document_review',[rid],'Actual installed Chrome rendered review; positive independent scope and publication value.',P+'review-final.json')
    S.event(S.B,'content_implementation',[rid],'One canonical concise live entry, with internal map/directory cross-reference.',P+'review-final.json')
    S.refresh(S.B)
S.refresh(S.B);S.guard()
