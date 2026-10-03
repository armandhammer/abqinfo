"""Two-record owner-invoked corrective review; preserves the original PR208 witnesses."""
import copy, hashlib, json, runpy, sys, subprocess, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
import TaskGovernance as G

P='project-state/governance/pr208-county-scope-correction-2026-10-03/'
OLD='project-state/governance/strong-five-review-2026-10-03/'
IDS=['src-5b7146d18ffadd1a','src-dfd205371e4664e5']
OWNER='owner-pr208-county-scope-correction-2026-10-03'
base_helpers=runpy.run_path(str(G.ROOT/'scripts/project/Review-StrongFive.py'))
save=base_helpers['save']; audit=base_helpers['audit']; bind=base_helpers['bind']

def refresh(name, pop_path=None):
    pop_path=pop_path or P+'population-v2.json'
    audit([f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).glob('contract*.json')],'Replaced immutable corrective-stage contracts remain historical evidence.')
    c=G.resolve(G.load(pop_path),G.registry(),G.file_hash(G.REGISTRY))
    while (G.ROOT/(P+name)).exists():
        name='contract-v'+str(int(name.split('-v')[1].split('.')[0])+1)+'.json'
    path=P+name;G.write_once(path,c)
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['governance_implementation'],events=[],status='corrective_review_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for x in r.get('constraints',[]):subjects.setdefault(x['subject'],{})[x['field']]=x['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for event in plan['events']:event['governance_ids']=c['governance_ids']
    if plan.get('completion_evidence'):plan['completion_evidence']={gid:plan['completion_evidence'][next(iter(plan['completion_evidence']))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=pop_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json',owner_review='pending',pr_url='https://github.com/armandhammer/abqinfo/pull/208'))
    print('Resolved',len(c['governance_ids']),'rules; conflicts',c['conflicts'],'gates',c['unresolved_gates'])

def setup():
    original=G.load(P+'contract.json');G.freshness(original,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    pop=G.load(P+'population.json')
    pop['artifact_paths'] += [P+'population-v2.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/governance/active-task.json',G.REGISTRY,G.registry()['audit_artifact'],'project-state/master-inventory.json','project-state/workflow-stage-lifecycle.json','project-state/discovery/retained-source-audit-queue.json','project-state/discovery/consolidated-human-review-queue.json']
    G.write_once(P+'population-v2.json',pop)
    G.write_once(P+'authority.json',dict(governance_metadata={'governance_id':OWNER},candidate_ids=IDS,baseline_commit=pop['baseline_commit'],instruction='Current owner directs the smallest corrective review of exactly Animal Care and Paradise Hills parks at PR208 head. Reassess independently under durable Albuquerque mission gates, requiring a specific material Albuquerque connection independent of County jurisdiction, postal address, proximity, adjacency or separate nearby retained records. Exclude and remove any record failing either gate through explicit supersession. Preserve October3 review, source captures/provenance, the two City additions, Sunport exclusion and unrelated PR207/PR208 state. Update PR description, durable state, full validation and regenerated verified preview. Keep PR208 open and unmerged. No R2 authority.'))
    bind(P+'authority.json',OWNER,'Reassess exactly these two County records independently against both mission gates. Prior positive scope outcomes are nonbinding for this authorized correction; exclude any record lacking independent substantive Albuquerque connection and remove its PR208 content. Preserve all other outcomes and historical evidence. No merge or R2 mutation.',{'candidate_ids':IDS,'task_ids':[pop['task_id']]})
    registry=G.load(G.REGISTRY);proposals={}
    for gid in ['decision-strong-five-record-review-2026-10-03','decision-decisions-b8452592-five-review-exception-2026-10-03','decision-next-ordinary-queue-b8bb5c70-five-review-exception-2026-10-03']:
        old=next(r for r in registry['entries'] if r['governance_id']==gid)
        replacement=copy.deepcopy(old);new_id=gid+'-two-county-correction'
        requirement='Preserve the October3 decisions and evidence for the two City resources and Sunport exclusion, and every unrelated prior decision. Explicit owner exception for exactly '+', '.join(IDS)+': their former positive eligibility/publication outcomes are nonbinding and replaced by the independently assessed corrective review under '+OWNER+'. Preserve original October3 evidence unchanged.'
        replacement.update(governance_id=new_id,effective_date='2026-10-03',authority='Explicit owner corrective review instruction',binding_requirement=requirement,required_actions=[requirement],settled_decisions=[],constraints=[])
        replacement['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        proposals[gid]=dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Only the two County records are reassessed; all other outcomes and historical witnesses preserved.',authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');registry['entries'].append(replacement)
    save(G.REGISTRY,registry);G.write_once(P+'supersession.json',dict(proposals=proposals))
    bind(P+'supersession.json','supersession-pr208-two-county-scope-correction','Apply only the three exact narrow authorized supersessions recorded here; preserve every other decision.',{'task_ids':[pop['task_id']]})
    audit([P+'prior-records.json',P+'contract.json'],'Frozen original corrective input; historical evidence only.')
    refresh('contract-v2.json');G.active_check('mutation','document_review')

def fetch(urls):
    from bs4 import BeautifulSoup
    G.active_check('mutation','document_review');records=G.load(P+'source-retrievals.json')['records'] if (G.ROOT/(P+'source-retrievals.json')).exists() else []
    for label,url in urls.items():
        row=dict(label=label,url=url,attempted_at=datetime.now(timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ABQInfo official-source verification'}),timeout=45) as response:
                body=response.read();row.update(http_status=response.status,final_url=response.url)
            path=P+'sources/'+label+'.html';(G.ROOT/path).parent.mkdir(parents=True,exist_ok=True);(G.ROOT/path).write_bytes(body)
            soup=BeautifulSoup(body,'html.parser');article=soup.select_one('#content-core') or soup
            text=article.get_text(' ',strip=True);textpath=P+'sources/'+label+'.txt';(G.ROOT/textpath).write_text(text,encoding='utf-8')
            row.update(saved_source=path,sha256=hashlib.sha256(body).hexdigest(),size_bytes=len(body),text_artifact=textpath)
        except Exception as e:row.update(http_status=getattr(e,'code',None),error=str(e))
        records.append(row);save(P+'source-retrievals.json',dict(records=records));print(label,row.get('http_status'))

def review():
    G.active_check('mutation','document_review')
    specs=[dict(id=IDS[0],page='content/public-works/capital-projects.md',
        institutional_scope='Bernalillo County Animal Care Services facility and County bond-funded construction; selected account updated November30 2017.',
        finding='About 90 percent of animals handled originated in the South Valley. The site was selected for that demand and access from other County areas. The source establishes County facility capacity, land selection and a sewer extension, but identifies no City expenditure, City animal-service obligation, Albuquerque regulatory decision or independently material City infrastructure-network function.',
        counterevidence='The owner-cited City Animal Shelters & Services page describes outside-city County service at 3001 Second SW. Its former URL currently returns404, including the query URL; indexed content is corroborating evidence, not a new HTTP200 capture. The fresh current official navigation target, Locations & Hours, instead specifies Albuquerque residency to bring animals and lists the Eastside/Westside City shelters. No ordinary official-source result establishes City participation in this selected County construction project. Broad adoption availability, an address or an incidental fiber connection to the facility would not establish its selected construction record as Albuquerque public information.',
        value='The 282-word original contains genuine County siting, designed capacity and utility/bond investment information. That substance is acknowledged; it does not independently establish material Albuquerque relevance or a separate ABQInfo entry.',
        family='County shelter-construction account, not an Albuquerque animal-service policy record or City facility component. Existing roadway fiber context cannot extend eligibility to the entire shelter investment.',
        rationale='Exclude: the selected County shelter construction account lacks a demonstrated specific material Albuquerque component independent of County service jurisdiction, South Valley proximity and postal location. The original positive scope statement inferred service to adjoining Albuquerque without evidence. Useful County project detail and official provenance do not repair the first mission gate.'),
      dict(id=IDS[1],page='content/public-works/parks-recreation.md',
        institutional_scope='Bernalillo County PROS-plan and Paradise Hills center/park/Pool/Park Lane phased capital program; selected update July27 2016.',
        finding='The update records County Commission PROS priorities, County campus redesign, State capital-outlay funds and proposed center/aquatics expansion. It does not identify Albuquerque funding, City program delivery changed by these works, City regulatory action, or a City transportation/recreation network obligation implemented by this specific program.',
        counterevidence='Current City material lists Paradise Hills as a Bernalillo County supper-meal site in a cooperative City/County program and as a cooling location. City Legistar R-22-62, adopted2022, identifies the County Paradise Hills pool in explaining the lack of City pools in District5 and the separate Cibola Loop decision. These are concrete City service/policy references, beyond postal proximity, and were independently checked. However, neither ties the selected 2016 park/center construction phases, appropriations or expansion to a material Albuquerque service change or City infrastructure undertaking. Hosting a later City-supported meal/cooling service and providing context for another project do not make this entire County capital program substantially about Albuquerque. The separate retained Paradise Hills Trail concept is a different network record; its eligibility is not transferred.',
        value='The 465-word update describes real County phases, budgets, proposed crossings and amenities, but it supplies mainly County program detail. Its historical project scope is not made into City public information by later use of one facility or a generic contextual reference.',
        family='One County campus/PROS capital program, distinct from the retained trail concept and separate City Cibola Loop policy; no consolidation or reassessment of those other records.',
        rationale='Exclude: ordinary official-source checks found City use and policy references to individual Paradise Hills facilities, but no sufficiently specific material Albuquerque component of the selected broad 2016 County construction program. The earlier inference from adjoining Albuquerque and the retained trail overextended the mission gate. The record is County contextual material rather than a substantiated Albuquerque capital/service record.')]
    sources=G.load(OLD+'source-retrievals.json')['records']
    for row in specs:
        old=next(x for x in sources if x['id']==row['id'])
        body=(G.ROOT/old['saved_source']).read_bytes();assert len(body)==old['size_bytes'] and hashlib.sha256(body).hexdigest()==old['sha256']
        row.update(outcome='excluded',source_url=old['url'],source_evidence=old,corrective_source_receipt=P+'source-retrievals.json',historical_review=OLD+'review.json',canonical_placement=None,
            scope_assessment=dict(assessed_at='2026-10-03',geographic_institutional_scope=row['institutional_scope'],specific_albuquerque_connection=row['finding'],abqinfo_public_information_value=row['value'],general_context_exclusion_test=row['counterevidence'],final_scope_decision='excluded',substantive_rationale=row['rationale']),
            gate_one='fails_record_specific_material_Albuquerque_connection',gate_two='County detail does not independently establish core Albuquerque public-information usefulness for this selected record.',human_scope_review='not a genuine mission borderline; contextual facility references do not establish substantive selected-program Albuquerque connection',currentness='Fresh County requests403; exact September26 originals preserved. City supplemental sources retrieved200; obsolete animal URL404 recorded. No completion/current-project inference.',duplication='Exclusion is mission scope, not byte duplication.',publication_form='inventory_only')
    G.write_once(P+'review.json',dict(artifact_type='independent_corrective_mission_scope_review',entries=specs,authority_artifact=P+'authority.json',historical_evidence_preserved=True))
    bind(P+'review.json','decision-pr208-two-county-scope-exclusion','Exclude exactly the two selected County project records for unsupported material Albuquerque scope. Remove only their PR208 additions, retain captures/provenance, City additions, Sunport exclusion and all unrelated decisions. No merge, R2 mutation or human-review escalation.',{'candidate_ids':IDS,'task_ids':['pr208-county-scope-correction-2026-10-03']},'Record-specific review under explicit owner corrective instruction')
    paths=[f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/(P+'sources')).glob('*')]
    audit(paths+[P+'contract-v4.json'],'Official source content or replaced setup contract, preserved as nonbinding evidence.')
    refresh('contract-v5.json',P+'population-v3.json')
    plan=G.load(P+'implementation.json');plan['events']=[dict(operation='document_review',candidate_ids=[r['id']],governance_ids=plan['respected_governance_ids'],action='implements',summary=r['rationale'],evidence=P+'review.json') for r in specs]
    plan['actions']=['document_review','family_review','inventory_disposition','content_implementation','visitor_visible_change','governance_implementation','background_integration','external_mutation'];save(P+'implementation.json',plan)

def implement():
    G.active_check('mutation','inventory_disposition',IDS)
    now=datetime.now(timezone.utc).isoformat();review=G.load(P+'review.json');inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    for e in review['entries']:
        row=rows[e['id']];row.update(status='excluded',scope_assessment=e['scope_assessment'],proposed_canonical_page=None,implementation_location=None,implementation_locations=[],cross_listing_approved=False,exclusion_reason=e['rationale'],review_reason='mission_scope_exclusion',validation_status='not applicable',updated_at=now)
        q=copy.deepcopy(row['quality_assessment']);q.update(intended_publication_form='inventory_only',publication_form='inventory_only',substantive_rationale=e['rationale']);row['quality_assessment']=q
        row['publication_quality_decision']=dict(decision='excluded',authority='decision-pr208-two-county-scope-exclusion',rationale=e['rationale'],evidence=P+'review.json')
        row['processing_notes'].append('2026-10-03 owner-invoked corrective review supersedes only this record eligibility. '+e['rationale']+' Original positive review retained at '+OLD+'review.json; corrective evidence '+P+'review.json.')
        G.active_check('mutation','content_implementation',[e['id']],[e['page']])
        original=subprocess.check_output(['git','show','9194c21f89d6ef5b711b17d009ed778f75601ce2:'+e['page']]).decode('utf-8')
        target=G.ROOT/e['page'];body=target.read_text(encoding='utf-8').replace('\r\n','\n')
        if e['id']==IDS[0]:body=body.split('\n### Animal Care and Resource Center (2017)')[0].rstrip()+'\n'
        else:
            start=body.index('## Historical County Parks Investment');end=body.index('## Historical Capital Programming',start);body=body[:start]+body[end:]
        assert body.rstrip()==original.replace('\r\n','\n').rstrip();target.write_bytes(original.encode('utf-8'))
    from collections import Counter
    counts=Counter(r['status'] for r in inv['candidates']);inv['counts']={s:counts[s] for s in inv['allowed_statuses']};inv['generated_at']=now;save('project-state/master-inventory.json',inv)
    roots=G.load('project-state/discovery/retained-source-audit-queue.json');removed=[r for r in roots['records'] if r['candidate_id'] in IDS];assert len(removed)==2
    roots['records']=[r for r in roots['records'] if r['candidate_id'] not in IDS];roots['generated_at']=now
    roots['counts']={s:sum(r['audit_status']==s for r in roots['records']) for s in roots['allowed_statuses']};save('project-state/discovery/retained-source-audit-queue.json',roots)
    stages=G.load('project-state/workflow-stage-lifecycle.json');assert stages['stages'][-1]['id']=='strong-five-review-publication'
    stages['stages'][-1]['end_commit']=G.load(P+'population.json')['baseline_commit'];stages['stages'].append(dict(id='pr208-county-scope-correction',baseline_commit=stages['stages'][-1]['end_commit'],regression_scripts=['scripts/project/Test-Pr208CountyScopeCorrection.py'],exact_delta_guard=dict(module='Test-Pr208CountyScopeCorrection',function='guard_current_delta')));save('project-state/workflow-stage-lifecycle.json',stages)
    save(P+'receipt.json',dict(artifact_type='pr208_corrective_accounting',excluded_ids=IDS,visible_additions_remaining=['src-0ce9e0677d08c174','src-0d8b434458a51c1d'],approved_remaining=13,pending_remaining=372,r2_objects_added=0,r2_bytes_added=0,removed_ineligible_descendant_roots=removed,source_limitation='County403; original September26 witnesses preserved; current City evidence captured. Old animal-service URL404 distinguished from current City navigation target200.',owner_review='pending',publication_stage='corrected_validation_pending'))
    plan=G.load(P+'implementation.json');plan['events'] += [dict(operation='inventory_disposition',candidate_ids=[rid],governance_ids=plan['respected_governance_ids'],action='implements',evidence=P+'review.json',summary='Applied record-specific mission exclusion and removed only its visible PR208 section.') for rid in IDS]
    plan['completion_evidence']={gid:[dict(path=P+'review.json',sha256=G.file_hash(P+'review.json'))] for gid in plan['respected_governance_ids']};save(P+'implementation.json',plan)

if __name__=='__main__':
    if sys.argv[1]=='setup':setup()
    elif sys.argv[1]=='review':review()
    elif sys.argv[1]=='implement':implement()
