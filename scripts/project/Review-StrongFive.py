"""Bounded five-record review evidence and governance setup; never uploads R2."""
import argparse, copy, hashlib, json, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
import TaskGovernance as G

P = 'project-state/governance/strong-five-review-2026-10-03/'
OWNER = 'owner-strong-five-record-specific-review-2026-10-03'

def save(path, data):
    target=G.ROOT/path; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def audit(paths, rationale):
    registry=G.load(G.REGISTRY); data=G.load(registry['audit_artifact'])
    indexed={r['path']:r for r in data['artifacts']}
    for path in paths:
        indexed[path]={'path':path,'sha256':G.file_hash(path),'hash_kind':'normalized-file-bytes',
                       'classification':'historical evidence only / non-binding','governance_ids':[], 'rationale':rationale}
    data['artifacts']=sorted(indexed.values(),key=lambda r:r['path'])
    save(registry['audit_artifact'],data);registry['audit_sha256']=G.file_hash(registry['audit_artifact']);save(G.REGISTRY,registry)

def bind(path, gid, requirement, scope, authority='Explicit owner instruction 2026-10-03'):
    registry=G.load(G.REGISTRY)
    registry['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,
        scope=scope,authority=authority,decision_date='2026-10-03',effective_date='2026-10-03',state='active',
        controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],
        binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],
        settled_decisions=[],unresolved_gates=[],implementation_status='in progress'))
    save(G.REGISTRY,registry)

def refresh(contract_name):
    population_path=G.load(G.ACTIVE_TASK)['population']
    if contract_name=='contract-v2.json':population_path=P+'population-v2.json'
    pop=G.load(population_path);contract=G.resolve(pop,G.registry(),G.file_hash(G.REGISTRY))
    path=P+contract_name;G.write_once(path,contract)
    prior=G.load(P+'implementation.json')
    subjects={}
    for row in contract['resolved_rules']:
        for rule in row.get('constraints',[]):subjects.setdefault(rule['subject'],{})[rule['field']]=rule['equals']
    prior.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=contract['population_sha256'],
                 respected_governance_ids=contract['governance_ids'],subjects=subjects)
    for e in prior['events']:e['governance_ids']=contract['governance_ids']
    save(P+'implementation.json',prior)
    active=G.load(G.ACTIVE_TASK);active.update(population=population_path,contract=path,
            contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress')
    save(G.ACTIVE_TASK,active)
    print('Fresh contract',path,len(contract['governance_ids']),'rules; conflicts',contract['conflicts'])

def setup():
    c=G.load(P+'contract.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    G.validate_plan(c,G.load(P+'implementation.json'))
    pop=G.load(P+'population.json')
    pop['artifact_paths'] += [P+'population-v2.json',P+'contract-v4.json',P+'contract-v5.json',P+'contract-v6.json',P+'source-rendering.json',P+'currentness.json',P+'supersession.json',P+'checkpoint-validation.log']
    pop['artifact_paths'] += [P+'sources/'+i+'.png' for i in pop['candidate_ids']]
    pop['artifact_paths'] += [P+'sources/'+i+'-current.html' for i in pop['candidate_ids']]
    G.write_once(P+'population-v2.json',pop)
    G.write_once(P+'authority.json',dict(governance_metadata={'governance_id':OWNER},
        candidate_ids=pop['candidate_ids'],authority='Current owner instruction',
        instruction='Take exactly the five strong_candidate records from the September 30 triage. Triage and existing approved status are nonbinding evidence, not publication permission. Freeze and resolve complete governance before record-specific review of mission fit, substantive durable public value, provenance/currentness, duplication, family role and placement. Implement survivors through publication quality on existing pages; record evidence-based failures and explicit supersession of generic approvals. Do not revive County-project generic approval logic. No inferred R2 authorization. Preserve provenance and source evidence. Visible changes require an unmerged owner-review content PR; validate and synchronize planning-snapshot.' ))
    bind(P+'authority.json',OWNER,'Review exactly these five records independently under current policies. Their prior approval and triage are nonbinding evidence for this new review. Preserve historical evidence; no R2 mutation or merge. Publish only independently qualified survivors through owner-review PR.',{'candidate_ids':pop['candidate_ids'],'task_ids':[pop['task_id']]})
    audit([P+'prior-records.json',P+'contract.json'], 'Frozen historical input or replaced setup contract; no current authority.')
    refresh('contract-v2.json')

def fetch():
    G.active_check('mutation','document_review')
    rows=G.load(P+'prior-records.json')['records']; old=G.load('project-state/discovery/human-review-reassessment-2026-09-26/retrievals.json')['records']
    receipts=[]
    for row in rows:
        rid=row['id'];url=row['source_url'];now=datetime.now(timezone.utc).isoformat()
        receipt={'id':rid,'url':url,'attempted_at':now}
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ABQInfo official-source verification'})
            with urllib.request.urlopen(req,timeout=40) as response:
                body=response.read();receipt.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'))
            assert receipt['http_status']==200 and b'<html' in body.lower()
            receipt['witness']='fresh_official_retrieval'
        except Exception as error:
            receipt.update(http_status=getattr(error,'code',None),error=str(error))
            saved=next(x for x in old if x['id']==rid and x['url'].rstrip('/')==url.rstrip('/') and x['http_status']==200)
            body=(G.ROOT/saved['saved_source']).read_bytes()
            assert len(body)==saved['size_bytes'] and hashlib.sha256(body).hexdigest()==saved['sha256']
            receipt.update(witness='saved_official_200_capture_not_fresh',prior_retrieval=saved)
        target=G.ROOT/(P+'sources/'+rid+'.html');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        receipt.update(saved_source=target.relative_to(G.ROOT).as_posix(),size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        soup=BeautifulSoup(body,'html.parser')
        if 'bernco.gov' in url:
            elements=soup.select('.et_pb_text_inner')
            content=next((x for x in elements if 'Project Scope' in x.get_text()),None)
            if content is None:content=max(elements,key=lambda x:len(x.get_text()))
        else:content=soup.select_one('#content-core')
        assert content is not None
        text=content.get_text(' ',strip=True).split('Project Contact Information')[0].strip()
        (G.ROOT/(P+'sources/'+rid+'.txt')).write_text(text,encoding='utf-8')
        (G.ROOT/(P+'sources/'+rid+'-article.html')).write_text('<html><meta charset="utf-8"><body>'+str(content)+'</body></html>',encoding='utf-8')
        receipt.update(extracted_word_count=len(text.split()),text_artifact=P+'sources/'+rid+'.txt',article_artifact=P+'sources/'+rid+'-article.html')
        receipts.append(receipt);save(P+'source-retrievals.json',{'records':receipts})
        print(rid,receipt['witness'],len(text.split()),'words')

def render():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(java_script_enabled=False,viewport={'width':1100,'height':900})
        ctx.route('**/*',lambda route:route.abort())
        images=[]
        for row in G.load(P+'source-retrievals.json')['records']:
            page=ctx.new_page();page.set_content((G.ROOT/row['article_artifact']).read_text(encoding='utf-8'))
            target=P+'sources/'+row['id']+'.png';page.screenshot(path=str(G.ROOT/target),full_page=True)
            images.append({'id':row['id'],'path':target,'sha256':hashlib.sha256((G.ROOT/target).read_bytes()).hexdigest()})
            page.close()
        browser.close()
    save(P+'source-rendering.json',dict(records=images,method='Offline Chromium artifact renderer with scripts and network disabled. Exact extracted article HTML; external images/styles unavailable. Not a current website screenshot.'))

def review():
    G.active_check('mutation','quality_assessment')
    sources={r['id']:r for r in G.load(P+'source-retrievals.json')['records']}
    specs=[
      dict(id='src-0a39e768262a9380d69d',outcome='excluded',page=None,heading=None,
        connection='The bounded Mountain View employment district between Second Street, Woodward/Sunport, I-25 and Rio Bravo is an Albuquerque-area transportation and land-use investment, not County jurisdiction alone.',
        substance='Explains roadway access, transit, freight, trails, complete streets requirements, right-of-way and proposed capital financing for the Sunport Commerce Center.',
        usefulness='The transportation and land-use framework is material public information; however, ABQInfo already presents the adopted 2019 plan and design overlay, with the original PDFs and official provenance.',
        unique='The 330-word project webpage summarizes the same adopted plan. Its approximately 860-acre wording differs from the existing plan summary; that alone is not a new record or an authoritative correction to the original plan.',
        family='src-0a39e768262a9380 is the retained validated original transportation plan; src-9a1ce13c6db23360 is the retained overlay. This HTML is a companion summary, not a byte-identical duplicate. Neither canonical record is changed.',
        currency='The page states adoption on May 14, 2019, but also retains a contradictory prospective Spring 2019 approval line. Current retrieval returned 403. Treat the preserved page as historical evidence only.',
        rationale='Exclude this redundant webpage summary from a separate public entry. Readers already have the more complete adopted transportation plan, its infrastructure framework and the coordinated overlay. No unique implementation result, later decision or substantive new analysis warrants another entry.',
        duplicate_pages=['content/transportation/transportation-plans.md','content/development-land-use/area-sector-plans.md']),
      dict(id='src-0ce9e0677d08c174',outcome='implemented',page='content/transportation/bicycling/_index.md',heading='Facility Types and Crossings',
        connection='The City explains actual Albuquerque facility types and names Silver Avenue, Central ART crossings, Lomas/Alvarado and several other local treatment examples.',
        substance='Defines routes, boulevards, standard/buffered/protected lanes, trails, sidepaths, bicycle detectors and bike boxes, plus HAWK and rapid flashing crossing beacons.',
        usefulness='Adds a readable infrastructure vocabulary for interpreting the existing Albuquerque bike maps, network plans and individual projects. The local treatment examples distinguish this page from a generic national bicycling guide.',
        unique='The Bicycling overview currently directs readers to plans, maps, projects and safety records but does not explain the differences between facility and crossing types. No existing site entry links this canonical City explainer.',
        family='A maintained City network explainer, complementary to Bike Maps, Bike Plans and Safety & Crash Data. The malformed resolveuid alias is excluded in inventory and is not revived. No attachment, legal excerpt or treatment is published separately.',
        currency='Fresh October 3 official HTTP 200 retrieval confirms the current City explainer. It includes dated Silver Avenue history and statute excerpts; publication summarizes infrastructure types without offering legal advice or claiming every example is newly built.',
        rationale='Publish one concise link and factual explanation on the existing Bicycling overview. Its local infrastructure definitions add enduring interpretive value to the network resources, avoiding a new page, duplicate map, fragmented treatment entries or unsupported safety claims.',duplicate_pages=['content/transportation/bicycling/bike-plans.md','content/transportation/bicycling/bike-maps.md','content/transportation/safety-crash-data.md']),
      dict(id='src-0d8b434458a51c1d',outcome='implemented',page='content/development-land-use/development-process.md',heading='Current City Review Process',
        connection='This is the City Planning Department gateway for Albuquerque land-use and zoning applications, building permits, licensing, code enforcement and public record searches.',
        substance='Explains online submissions, document uploads, review comments, payments and status tracking, and directs the public to searches for permits, applications, business licenses and violations.',
        usefulness='Public search and tracking access lets residents follow development decisions and permit activity rather than merely transact an individual application. It complements the existing policy manuals and review-agency overview.',
        unique='Development Review Services already describes review sections and mentions ABQ-PLAN. The selected gateway adds cross-division online services and public search functions that are not explained by the existing entry. One focused link is sufficient.',
        family='A maintained gateway for several City planning services; no business renewal tutorial, isolated form, Community Connect policing promotion or excluded ABQ-PLAN inventory row is added or reclassified.',
        currency='Fresh October 3 HTTP 200 official retrieval confirms land-use applications and online permit/search functions. The summary links the maintained City gateway so service URLs can change without asserting that every underlying transaction was tested.',
        rationale='Publish a focused gateway entry beside Development Review Services, emphasizing public record searches and status tracking alongside applications. This exposes meaningful access to Albuquerque development oversight while keeping forms, routine tutorials and unrelated promotional material out of the publication.',duplicate_pages=['content/development-land-use/development-process.md']),
      dict(id='src-5b7146d18ffadd1a',outcome='implemented',page='content/public-works/capital-projects.md',heading='Animal Care and Resource Center (2017)',
        connection='The County shelter near Second Street and Woodward serves the South Valley and adjoining Albuquerque urban area; the account ties location to the origin of animals, arterial access, zoning and infrastructure.',
        substance='Records a 17,143-square-foot shelter, approximately 115 dogs and 25 cats, veterinary/isolation space, evaluation of more than 15 properties, a 1,300-foot sewer extension and a $7.5 million bond-funded total including land.',
        usefulness='The site-selection criteria explain why a public-service facility was located here, connecting service demand, land constraints, access and utility investment. That reasoning and designed capacity are more informative than a construction percentage or generic capital-project blurb.',
        unique='No ABQInfo entry explains this shelter investment or siting criteria. The roadway page mentions a fiber connection to Animal Care; that incidental network reference neither documents nor duplicates facility planning.',
        family='One complete historical facility-development account, not separate capacity, sewer, cost or contractor entries. Capital Projects accepts County investments and is the canonical page; City Facilities explicitly covers City-owned buildings and remains unchanged.',
        currency='The substantive update is November 30, 2017, despite its 2021 migration URL. Fresh County project and department retrievals are blocked; the saved September 26 HTTP 200 bytes support historical design and estimates, not current capacity, completion or operating arrangements.',
        rationale='Publish a bounded historical investment account on Capital Projects, preserving County ownership and the 2017 date. Capacity, competing-site evaluation and utility criteria establish durable public infrastructure value independently of the rejected generic approval recipe. Exclude contractor contacts, obsolete completion percentages and present-day service claims.',duplicate_pages=['content/transportation/roadway-projects/_index.md','content/public-works/city-facilities.md']),
      dict(id='src-dfd205371e4664e5',outcome='implemented',page='content/public-works/parks-recreation.md',heading='Historical County Parks Investment',
        connection='The Paradise Hills community center, park, pool and Park Lane form a recreation campus in the adjoining northwest Albuquerque urban community. The record concerns specific pedestrian access, ADA viewing, trails and shared facilities rather than County-wide applicability.',
        substance='Connects 2013 campus planning and the October 2015 PROS priority to completed 2015 annex work, 2016 park/street redesign, planned center/pool additions, phased estimates and state capital-outlay funding.',
        usefulness='The integrated campus account explains how safe crossings, access, recreation capacity and funding were coordinated across phases. The distinction between completed annex improvements and contingent later proposals lets readers understand the actual historical planning program.',
        unique='Existing Paradise Hills records cover the 2013 trail concept and 2018 ADA roadway work. Neither presents this park, community center and aquatics investment program. Those originals stay separately accessible; no already-published map is duplicated.',
        family='A single program-level campus entry encompasses the phases. Little League and Sky View Acres appear as other NCA projects in the source; they are not new separately approved additions. PROS/master-plan references are source context, not new records or claims that all proposals were adopted or built.',
        currency='The source is an explicitly dated July 27, 2016 update, hosted at a 2021 migration URL. It records Phase 0 complete in summer 2015 but prospective 2017-2018 later work and conditional funding. Current retrieval is blocked; do not infer completion from elapsed schedules.',
        rationale='Publish one carefully qualified historical campus-investment account on Parks & Recreation. Coordinated access and recreation design, phase relationships and financing provide substantive value beyond a project list. Maintain completed-versus-proposed distinctions; the webpage is not a current construction tracker or confirmation of later appropriations.',duplicate_pages=['content/transportation/bicycling/projects/_index.md','content/transportation/roadway-projects/_index.md','content/maps-data/maps.md'])
    ]
    entries=[]
    for item in specs:
        source=sources[item['id']];evidence=[P+'source-retrievals.json',source['text_artifact'],P+'source-rendering.json']+item['duplicate_pages']
        q=dict(document_function=item['family'],substantive_content=item['substance'],durable_public_usefulness=item['usefulness'],
               information_density='Article-only extraction excludes global menus. Measured content includes the source narrative and local lists/tables; global HTML navigation counts are not document substance.',
               unique_information=item['unique'],rationale=item['rationale'],standalone_public_value='low' if item['outcome']=='excluded' else 'substantive',
               reviewed_document_content=True,visual_inspection_completed=True,
               visual_inspection_notes='Inspected offline article rendering; external images and styles are unavailable. Claims rely on the readable text, not unseen diagrams.',
               publication_form='inventory_only' if item['outcome']=='excluded' else ('live_service' if 'cabq.gov' in source['url'] else 'standalone'),
               series_relationship='standalone',family_component_review=item['family'],page_count=0,extracted_word_count=source['extracted_word_count'],
               measurement_method='HTML has no fixed document page count; zero records that fact. The complete substantive article was measured, not the entire website.',
               currentness_review_required=True,currentness_review=dict(status='current' if source['witness']=='fresh_official_retrieval' else 'historical_status_uncertain',
                  authoritative_sources=[source['url'],P+'source-retrievals.json'],finding=item['currency'],publication_qualification=item['currency']))
        scope=dict(assessed_at='2026-10-03',geographic_institutional_scope=item['connection'],specific_albuquerque_connection=item['connection'],
                   abqinfo_public_information_value=item['usefulness'],general_context_exclusion_test='Named local service demand, network treatments or campus investment supply material Albuquerque public information. County jurisdiction, an incidental geographic reference or a generic capital-project title would not establish either gate.',
                   final_scope_decision='passes_both_gates',substantive_rationale=item['rationale'])
        entries.append({**item,'scope_assessment':scope,'quality_assessment':q,'publication_quality_decision':dict(decision='excluded' if item['outcome']=='excluded' else 'passes',
            authority='decision-strong-five-record-review-2026-10-03',assessed_at='2026-10-03',evidence=evidence,assessment=q),
            'source_url':source['url'],'source_witness':source['witness'],'evidence':evidence,
            'archive_treatment':'Official maintained HTML page, not a downloadable static document. Publication links the source itself; local captures preserve research evidence only. No static attachment, generated document or R2 archive is introduced.'})
    G.write_once(P+'review.json',dict(artifact_type='record_specific_scope_quality_placement_review',entries=entries,
        supersedes_prior_generic_approval_for_exact_ids=[x['id'] for x in entries],authority_artifact=P+'authority.json',
        historical_evidence_preserved=True,r2_mutation_authorized=False))
    bind(P+'review.json','decision-strong-five-record-review-2026-10-03','Apply the exact five independently assessed outcomes and canonical placements recorded here. Exclude the redundant Sunport webpage; publish only the four reviewed HTML resources with their date/ownership/phase qualifications. No R2 changes, static attachment additions, City Facilities broadening, other candidate dispositions or merge.',{'candidate_ids':[e['id'] for e in entries],'task_ids':['strong-five-review-2026-10-03']},'Project review under explicit owner instruction 2026-10-03')
    registry=G.load(G.REGISTRY);proposals={}
    for gid in ['decision-decisions-b8452592','decision-next-ordinary-queue-b8bb5c70']:
        old=next(r for r in registry['entries'] if r['governance_id']==gid)
        replacement=copy.deepcopy(old);new_id=gid+'-five-review-exception-2026-10-03'
        replacement.update(governance_id=new_id,authority='Explicit owner record-specific review instruction 2026-10-03; all other earlier decisions retained',effective_date='2026-10-03',
             binding_requirement=old['binding_requirement']+' Explicit exception: prior approval/triage for exactly the five IDs in the owner instruction is nonbinding for this new review; their outcomes are replaced by decision-strong-five-record-review-2026-10-03. Preserve every other record decision and the original evidence.',
             required_actions=['Preserve every prior decision outside these five IDs; for exactly the five use the registered record-specific October 3 review.'],
             settled_decisions=[dict(question_id='five-record-exception:'+gid,decision='Five earlier approvals are replaced under current owner authorization; all other decisions remain unchanged.')])
        replacement['controlling_artifacts'] += [dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']),dict(path=P+'review.json',sha256=G.file_hash(P+'review.json'),binding_pointers=['/'])]
        proposals[gid]=dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),
            new_evidence=P+'review.json',proposed_replacement=replacement['binding_requirement'],consequences='Replace only the exact five approval outcomes; preserve all other rows and all historical controlling artifacts.',authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');registry['entries'].append(replacement)
    save(G.REGISTRY,registry);G.write_once(P+'supersession.json',{'proposals':proposals})
    bind(P+'supersession.json','supersession-strong-five-prior-approval-2026-10-03','Explicit narrowly scoped supersession of the two shared prior-decision authorities: retain every nonselected decision; only the exact five are replaced under the owner instruction.',{'task_ids':['strong-five-review-2026-10-03']})
    active=G.load(G.ACTIVE_TASK);active['supersession_proposals']=proposals;save(G.ACTIVE_TASK,active)
    audit([P+'contract-v3.json'],'Replaced pre-review setup contract; retained historical evidence.')
    refresh('contract-v4.json')
    plan=G.load(P+'implementation.json');c=G.load(plan['contract'])
    plan['events']=[dict(operation='quality_assessment',candidate_ids=[e['id']],governance_ids=c['record_rules'][e['id']],use_contract_record_rules=True,
                 action='implements',evidence=P+'review.json',summary=e['rationale']) for e in entries]
    plan['status']='review_complete_implementation_pending';save(P+'implementation.json',plan)
    G.active_check('mutation','inventory_disposition')
    print('Review durable: four qualified HTML resources; redundant Sunport summary excluded. Prior generic approvals explicitly superseded only for five IDs.')

def implement():
    from PublicationQuality import require_publication_quality
    review=G.load(P+'review.json');now=datetime.now(timezone.utc).isoformat()
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    additions={
      'src-0ce9e0677d08c174':('## Trail Advisory and Accessibility',
        '## Facility Types and Crossings\n\n- [Bike Facilities in Albuquerque — Live City Guide](https://www.cabq.gov/municipaldevelopment/our-department/engineering/bicycle-pedestrian-amenities/bike-facilities-in-albuquerque)\n\n  Explains the differences between Albuquerque bike routes, boulevards, standard, buffered and protected lanes, multi-use trails and sidepaths. The City guide also describes bicycle detection, bike boxes and crossing beacons, with local examples that help readers interpret the network maps and project plans.\n\n'),
      'src-0d8b434458a51c1d':('## Development Policy References',
        '- [Online Planning Services, Permitting & Applications — Live City Services](https://www.cabq.gov/planning/online-planning-permitting-applications)\n\n  Connects land-use and zoning applications, building permits, business licensing and code-enforcement services with the City’s online systems. Residents can also search permits, applications, licenses and violation records, while applicants can upload documents and track review progress. This service gateway complements the review-section overview above.\n\n'),
      'src-5b7146d18ffadd1a':('## Historical Project Snapshots',
        '### Animal Care and Resource Center (2017)\n\n- [Animal Care and Resource Center — Official County Project Page](https://www.bernco.gov/public-works/blog/2021/04/16/animal-care-and-resource-center)\n\n  The County’s November 30, 2017 account explains the planned 17,143-square-foot shelter near Second Street and Woodward, with space for approximately 115 dogs and 25 cats, veterinary care, isolation and recreation areas. The County evaluated more than 15 properties; its criteria included proximity to South Valley service demand, access from Broadway and Rio Bravo, industrial zoning, available utilities and environmental constraints. The account records a 1,300-foot sewer extension to Woodward.\n\n  The estimated $7.5 million general-obligation-bond investment included land acquisition. These are the County’s 2017 design and funding figures, not confirmation of present operating capacity or final spending. This is a County-owned facility; the historical construction account does not establish its current project status.\n\n'),
      'src-dfd205371e4664e5':('## Historical Capital Programming',
        '## Historical County Parks Investment\n\n- [Paradise Hills NCA Parks & Recreation Projects Update — Official County Project Page](https://www.bernco.gov/public-works/blog/2021/04/16/paradise-hills-nca-parks-recreation-projects-update)\n\n  The July 27, 2016 update connects Paradise Hills Community Center, Park Lane, the park and pool as one phased campus program. It traces the proposals to 2013 master planning and the County’s October 2015 Parks, Recreation and Open Space Facilities Plan. Senior Annex trail, parking, landscape and drainage work was completed in summer 2015.\n\n  Later phases proposed safer crossings between the center and park, accessible viewing areas, recreation and landscape changes, and center and aquatics additions. The account identifies approximately $800,000 in first-phase state funding, a $1.1 million park/street redesign budget and a projected $3 million center/aquatics phase seeking further funding. Those estimates and 2017–2018 schedules describe the proposals at the time; they do not confirm that later work was funded or completed. The separate [Paradise Hills Trail concept](/transportation/bicycling/projects/#paradise-hills-trail) remains available on Bicycle Projects.\n\n')}
    for entry in review['entries']:
        rid=entry['id'];row=rows[rid]
        G.active_check('mutation','inventory_disposition',[rid])
        row.update(scope_assessment=entry['scope_assessment'],quality_assessment=entry['quality_assessment'],
                   publication_quality_decision=entry['publication_quality_decision'],updated_at=now,review_reason=None)
        if entry['outcome']=='excluded':
            row.update(status='excluded',exclusion_reason='Redundant companion webpage: the substantive adopted Sunport transportation plan and design overlay are already published. Not a byte-identical duplicate or a mission-scope exclusion.',proposed_canonical_page=None,
                       implementation_location=None,implementation_locations=[],cross_listing_approved=False,
                       validation_status='Record-specific review excluded separate webpage publication; original plan and overlay retained.')
        else:
            require_publication_quality(row)
            page=entry['page'];G.active_check('mutation','content_implementation',[rid],[page])
            target=G.ROOT/page;body=target.read_text(encoding='utf-8-sig')
            marker,addition=additions[rid]
            assert entry['source_url'] not in body and body.count(marker)==1
            if rid=='src-5b7146d18ffadd1a':body=body.rstrip()+'\n\n'+addition.rstrip()+'\n'
            else:body=body.replace(marker,addition+marker,1)
            target.write_text(body,encoding='utf-8',newline='\n')
            description=' '.join((entry['substance']+' '+entry['usefulness']).split()[:50])
            row.update(status='implemented',description=description,proposed_canonical_page=page,
                       implementation_location=page,implementation_locations=[page],cross_listing_approved=False,exclusion_reason=None,
                       validation_status='Implemented under fresh record-specific governance; owner PR review and production verification pending.')
            row['description_word_count']=len(row['description'].split())
        row['processing_notes'].append('2026-10-03 independent five-record review replaces earlier generic eligibility evidence under current owner authority. '+entry['rationale']+' Evidence: '+P+'review.json. No R2 mutation.')
        plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='inventory_disposition',candidate_ids=[rid],use_contract_record_rules=True,
             governance_ids=plan['respected_governance_ids'],action='implements',summary=entry['rationale'],evidence=P+'review.json'))
        save(P+'implementation.json',plan)
        print('Prepared',rid,row['status'])
    G.active_check('mutation','inventory_disposition',[e['id'] for e in review['entries']])
    from collections import Counter
    counts=Counter(r['status'] for r in inv['candidates']);inv['counts']={s:counts[s] for s in inv['allowed_statuses']}
    inv['generated_at']=now;save('project-state/master-inventory.json',inv)
    print('Persisted exact five-record atomic inventory batch.')
    pointer=G.load('project-state/ordinary-queue-current.json');queue=G.load(pointer['artifact']);prior_path=pointer['artifact']
    queue.update(artifact_type='ordinary_queue_post_strong_five_review',recorded_at=now,source_queue_artifact=prior_path,
                 inventory_generated_at=now,strong_five_reviewed_ids=[e['id'] for e in review['entries']],strong_five_implemented_ids=[e['id'] for e in review['entries'] if e['outcome']=='implemented'],
                 strong_five_excluded_ids=[e['id'] for e in review['entries'] if e['outcome']=='excluded'])
    queue['newly_approved_backlog']=[r for r in queue['newly_approved_backlog'] if r['id'] not in {e['id'] for e in review['entries']}]
    queue_path='project-state/discovery/strong-five-review-2026-10-03/queue.json';save(queue_path,queue)
    save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=queue_path,task='strong-five-review-2026-10-03'))
    audit_queue=G.load('project-state/discovery/retained-source-audit-queue.json')
    for e in review['entries']:
        if e['outcome']=='implemented' and not any(r['source_url']==e['source_url'] for r in audit_queue['records']):
            row=rows[e['id']];audit_queue['records'].append(dict(candidate_id=row['id'],source_url=row['source_url'],title=row['title'],agency=row['agency'],canonical_page=e['page'],
                 audit_status='pending descendant crawl',crawl_output=None,discovered_documents=0,archived_documents=0,
                 processing_notes=['Added after governed HTML resource implementation; descendant crawl remains pending.'],created_at=now,updated_at=now))
    audit_queue['generated_at']=now
    for state in audit_queue['counts']:audit_queue['counts'][state]=sum(r['audit_status']==state for r in audit_queue['records'])
    save('project-state/discovery/retained-source-audit-queue.json',audit_queue)
    stages=G.load('project-state/workflow-stage-lifecycle.json');baseline=G.load(G.load(G.ACTIVE_TASK)['population'])['baseline_commit']
    assert stages['stages'][-1]['id']=='pr207-owner-correction' and not stages['stages'][-1].get('end_commit')
    stages['stages'][-1]['end_commit']=baseline
    stages['stages'].append(dict(id='strong-five-review-publication',baseline_commit=baseline,regression_scripts=['scripts/project/Test-StrongFiveReview.py'],
                   exact_delta_guard={'module':'Test-StrongFiveReview','function':'guard_current_delta'}))
    save('project-state/workflow-stage-lifecycle.json',stages)
    plan=G.load(P+'implementation.json');plan.update(actions=['document_review','family_review','quality_assessment','inventory_disposition','placement','content_implementation','visitor_visible_change','governance_implementation'],status='implemented_validation_pending')
    plan['completion_evidence']={gid:[dict(path=P+'review.json',sha256=G.file_hash(P+'review.json'))] for gid in plan['respected_governance_ids']}
    save(P+'implementation.json',plan)

def preview(base_url):
    import runpy
    from urllib.parse import urlparse
    host=urlparse(base_url).hostname
    assert host and host.endswith('.abqinfo.pages.dev') and urlparse(base_url).scheme=='https'
    G.active_check('mutation','external_mutation')
    helper=runpy.run_path(str(G.ROOT/'scripts/project/Verify-Pr198Production.py'))
    normalize_links=runpy.run_path(str(G.ROOT/'scripts/project/Verify-Pr202Production.py'))['normalize_protected_email_links']
    Article=helper['Article'];normalize=helper['normalize_cloudflare_email']
    routes=[('transportation/bicycling','facility-types-and-crossings','src-0ce9e0677d08c174'),
            ('development-land-use/development-process','current-city-review-process','src-0d8b434458a51c1d'),
            ('public-works/capital-projects','animal-care-and-resource-center-2017','src-5b7146d18ffadd1a'),
            ('public-works/parks-recreation','historical-county-parks-investment','src-dfd205371e4664e5')]
    entries={e['id']:e for e in G.load(P+'review.json')['entries']};results=[]
    for route,anchor,rid in routes:
        url=base_url.rstrip('/')+'/'+route+'/'
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ABQInfo owner review preview verification'}),timeout=60) as response:
            assert response.status==200 and response.url==url
            body=response.read()
        local=(G.ROOT/'tmp/site-build'/route/'index.html').read_text(encoding='utf-8')
        presentations=[]
        for html in [local,body.decode('utf-8')]:
            normalized,_=normalize(html);parser=Article();parser.feed(normalized);presentations.append(normalize_links(parser.result()))
        assert presentations[0]==presentations[1],route+' preview differs from validated local article'
        text,links,anchors=presentations[1]
        assert anchor in anchors and links.count(entries[rid]['source_url'])==1
        output=G.ROOT/'tmp/strong-five-preview'/route/'index.html';output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(body)
        semantic=json.dumps(presentations[1],ensure_ascii=False,separators=(',',':')).encode('utf-8')
        results.append(dict(id=rid,url=url+'#'+anchor,http_status=200,body_sha256=hashlib.sha256(body).hexdigest(),
            article_sha256=hashlib.sha256(semantic).hexdigest(),matches_validated_local_article=True,changed_anchor_present=True,source_link_present=True))
        print('Verified',url+'#'+anchor)
    save(P+'preview-verification.json',dict(result='passed',verified_at=datetime.now(timezone.utc).isoformat(),
        reviewed_head=G.git('rev-parse','HEAD'),content_tree_oid=G.git('rev-parse','HEAD:content'),preview_url=base_url,pages=results,
        comparison='Complete article text, ordered links and anchors match the validated local Hugo render; only Cloudflare email protection is normalized.'))

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='setup':setup()
    elif cmd=='fetch':fetch()
    elif cmd=='render':render()
    elif cmd=='review':review()
    elif cmd=='implement':implement()
    elif cmd=='preview':preview(sys.argv[2])
