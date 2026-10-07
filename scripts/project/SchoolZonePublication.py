"""Exact owner-authorized school-zone archive and unmerged publication stage."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativePublication import save, audit
from SchoolZoneTimingDesign import ID, SOURCE, SHA
from WorkflowStageLifecycle import StageSnapshot
TASK='school-zone-publication-2026-10-07'
P='project-state/governance/'+TASK+'/'
OLD='project-state/governance/school-zone-timing-design-2026-10-06/'
BASE='bdb6d440091f28fa88d0753dad34849b53e703b8'
PAGE='content/transportation/safety-crash-data.md'
SCRIPT='scripts/project/SchoolZonePublication.py'
KEY='transportation/safety-crash-data/abq-middle-high-school-zone-active-timings-ipra-fade828a553f.pdf'
URL='https://files.abqinfo.com/'+KEY
OPS=['archive','content_implementation','inventory_disposition','governance_implementation','family_review']
GATE='school-zone-timing-design-2026-10-06:r2-owner-authorization'
def now():return datetime.now(timezone.utc).isoformat()
def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([x for x in G.changed_paths(BASE) if x.startswith('project-state/') and x not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    n=len(list((G.ROOT/P).glob('contract-v*.json')))+1
    path=P+f'contract-v{n}.json'
    population=P+('population-v4.json' if (G.ROOT/(P+'population-v4.json')).exists() else 'population-v3.json' if (G.ROOT/(P+'population-v3.json')).exists() else 'population-v2.json')
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    evidence=P+'receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else P+'authority.json'
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,satisfied_gates={GATE:dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'))},completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules')
def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','population-v2.json','authority.json','supersession.json','starting-state.json','source-check.json','r2-before.json','r2-after.json','archive-preflight.json','upload-intent.json','upload.json','public-verification.json','editorial.json','publication.md','source-record.json','implementation.json','receipt.json','queue.json','validation.log','preview.json','preview-desktop.png','preview-mobile.png','pr-description.md','pr.json','final-refs.json']+[f'contract-v{i}.json' for i in range(1,31)]
    paths=[P+x for x in outputs]+[SCRIPT,'scripts/project/Test-MasterInventory.ps1','scripts/project/Invoke-ProjectValidation.ps1',G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/r2-inventory.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population-v2.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=['school-zone-active-times'],pages=[PAGE],operation_classes=OPS,artifact_paths=paths,archive_objects=[dict(candidate_id=ID,source_path=SOURCE,r2_key=KEY,sha256=SHA,size_bytes=3013109)]))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population-v2.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    instruction='Explicit owner authorization 2026-10-07 covers exactly one unchanged original '+SOURCE+' (3013109 bytes, 33 pages, SHA256 '+SHA+') upload to '+KEY+', no overwrite/delete, complete public GET byte verification, then already-reviewed alphabetical School Zone Active Times section on Safety & Crash Data and an OPEN UNMERGED manual-review content PR. No general R2 authority, elementary work, unrelated records, content merge or production deployment. Preserve all prior verbatim source/structured evidence and operational qualifiers; public provenance says obtained through an Inspection of Public Records Act (IPRA) request and archived by ABQInfo, no owner wording, no invented agency/effective date/official URL. Correct only independently unambiguous school spelling, never infer locations/times/ambiguous names. Full governance/freshness, sealed-history, normal validation, Hugo, actual nonproduction Chrome desktop/mobile inspection, all rendered timing checks, link verification, anchor/overflow and polished PR description required.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction',instruction=instruction,source_sha256=SHA,bytes=3013109,pages=33,r2_key=KEY,one_upload_only=True,no_overwrite=True,no_delete=True,unmerged_content_pr_authorized=True,merge_authorized=False))
    r=G.registry();proposals={}
    for old in r['entries'][:]:
        if old['state']!='active' or old['governance_id'] not in ['owner-school-zone-timing-design-2026-10-06-remote-checkpoint-authorized','owner-school-zone-remote-checkpoint-2026-10-06']:continue
        revised=old['binding_requirement']+' Current explicit owner authority in '+P+'authority.json replaces only the prior phase boundary for this exact original: one authorized archive/public verification and visitor-visible unmerged PR. All completed review, safety, scope, quality and settled family decisions remain controlling. No content merge or unrelated authority.'
        gid=old['governance_id']+'-publication-authorized'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=revised,consequences='Only exact source archive and unmerged content stage authorized; immutable prior review and elementary boundary retained.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=revised,required_actions=[revised],prohibited_actions=['No overwrite/delete, elementary or unrelated population, content merge or deployment'],authority='Explicit current owner school-zone archival/publication instruction',effective_date='2026-10-07')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,state='active',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-07',effective_date='2026-10-07',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No merge/deploy, unrelated R2 or elementary population'],constraints=[],settled_decisions=[],unresolved_gates=[],releases_gates=[GATE],implementation_status='authorized exact archival and manual-review publication'))
    save(G.REGISTRY,r)
    prior={}
    for folder in [OLD,'project-state/governance/school-zone-remote-checkpoint-2026-10-06/']:
        for path in (G.ROOT/folder).iterdir():
            if path.is_file():
                if path.suffix=='.json':G.load(path)
                else:path.read_bytes()
                prior[path.relative_to(G.ROOT).as_posix()]=G.file_hash(path)
    G.write_once(P+'starting-state.json',dict(remote_refs={'main':BASE,'chatgpt/planning-snapshot':BASE},prior_evidence_sha256=prior,prior_active_task=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),review_freshness='complete prior registry active final and prior exact guard passed',source_review_reused=True))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='school-zone-remote-checkpoint-2026-10-06';life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='SchoolZonePublication',function='guard')))
    protected={x['path'] for x in life['protected_evidence']}
    for path,h in prior.items():
        if path not in protected:life['protected_evidence'].append(dict(path=path,commit=BASE,sha256=h))
    save('project-state/workflow-stage-lifecycle.json',life)
    v=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=v.read_text(encoding='utf-8-sig');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/SchoolZonePublication.py" guard\nif ($LASTEXITCODE) { throw \'School-zone publication guard failed.\' }\nSet-StrictMode -Version Latest',1);v.write_text(s,encoding='utf-8',newline='\n')
    refresh()
def source_check():
    sys.path.insert(0,str(G.ROOT/'tmp/pr198-resume-pdf-deps'))
    from pypdf import PdfReader
    import pymupdf
    raw=(G.ROOT/SOURCE).read_bytes();assert len(raw)==3013109 and hashlib.sha256(raw).hexdigest()==SHA
    pdf=PdfReader(G.ROOT/SOURCE,strict=True);assert len(pdf.pages)==33 and not pdf.is_encrypted
    doc=pymupdf.open(G.ROOT/SOURCE);assert not doc.is_repaired and len(doc)==33
    inspected=G.load(OLD+'source-inspection.json')
    save(P+'source-check.json',dict(source_path=str((G.ROOT/SOURCE).resolve()),size_bytes=len(raw),sha256=SHA,pages=len(pdf.pages),strict_parse_passed=True,repair=False,checked_at=now(),prior_inspection_sha256=G.file_hash(OLD+'source-inspection.json')))
    print('PASS unchanged original: 3013109 bytes / expected SHA / valid 33 pages')
def preflight():
    G.active_check('mutation','archive',[ID],r2_key=KEY,source_sha256=SHA)
    s=G.load(P+'source-check.json');assert s['sha256']==SHA and s['size_bytes']==3013109 and s['pages']==33
    assert hashlib.sha256((G.ROOT/SOURCE).read_bytes()).hexdigest()==SHA
    live=G.load(P+'r2-before.json');assert KEY.casefold() not in {x['key'].casefold() for x in live['objects']}
    assert sum(x['size_bytes'] for x in live['objects'])==live['total_bytes'] and len(live['objects'])==live['object_count']
    assert 3013109<=150000000 and live['total_bytes']+3013109<=13000000000
    G.write_once(P+'archive-preflight.json',dict(source=s,r2_key=KEY,inventory_sha256=G.file_hash(P+'r2-before.json'),inventory_checked_at=live['generated_at'],key_absent_casefold=True,no_overwrite=True,no_delete=True,current_objects=live['object_count'],current_bytes=live['total_bytes'],projected_objects=live['object_count']+1,projected_bytes=live['total_bytes']+3013109,object_limit=150000000,storage_limit=13000000000,authority=P+'authority.json'))
    G.write_once(P+'upload-intent.json',dict(state='one_exact_upload_intended',r2_key=KEY,source_sha256=SHA,source_bytes=3013109,authority=P+'authority.json',created_at=now(),recovery='If interrupted, inspect object and saved evidence; never repeat a successful upload or overwrite.'))
    refresh();G.active_check('mutation','archive',[ID],r2_key=KEY,source_sha256=SHA)
def editorial():
    data=G.load(OLD+'timings.json')
    text=(G.ROOT/(OLD+'proposed-content.md')).read_text(encoding='utf-8-sig')
    start=text.index('- **Albuquerque**')
    intro='''### School Zone Active Times

These are school-zone flasher activation schedules, not school bell times. This middle/high-school record contains 30 distinct schedules covering 32 named schools and 61 intervals, including shared-school entries. A separate elementary-school timing record is expected later and is not yet included.

#### Middle/High-School IPRA Record

[Source timing sheets (archived PDF, 33 pages)]('''+URL+''')

The source document was obtained through an Inspection of Public Records Act (IPRA) request and is archived unchanged by ABQInfo. The PDF itself does not identify an issuing agency or establish one single effective date, and it does not confirm that every schedule remains current.

Monday-Friday is shown only where the source marks an interval M-F. "Weekday not stated" means the interval has no weekday qualification in the source. Locations are reproduced as written; important operational notes appear with the affected schedule.

'''
    body=text[start:].replace('**Clevland Middle School**','**Cleveland Middle School**').replace('Location in source: Natalie & Louisiana.','Location in source: Natalie & Louisiana. The source sheet misspells the school name as "Clevland."').replace('**Valley high school**','**Valley High School**')
    (G.ROOT/(P+'publication.md')).write_text(intro+body,encoding='utf-8',newline='\n')
    save(P+'editorial.json',dict(source_dataset=OLD+'timings.json',source_dataset_sha256=G.file_hash(OLD+'timings.json'),changes=[dict(source='Clevland Middle School',display='Cleveland Middle School',independent_source='https://www.aps.edu/schools/schools/cleveland-middle-school',finding='APS school directory identifies Cleveland Middle School at 6910 Natalie St. NE; matches source Natalie/Louisiana location. Source spelling preserved in verbatim dataset and public concise note.'),dict(source='Valley high school',display='Valley High School',finding='Capitalization only; no school identity or substantive source inference.')],no_location_time_or_ambiguous_name_inference=True,provenance='Owner-provided to project; IPRA acquisition owner attestation; agency/global effective date unknown; no public City/APS source URL established',public_availability='Owner reports source record unavailable on City/APS sites; no independent broader negative web claim',future_elementary='Sibling record can be added under generic h3 without redesign; none reviewed'))
def implement():
    G.active_check('mutation','content_implementation',[ID],pages=[PAGE])
    v=G.load(P+'public-verification.json');assert v['byte_identical'] and v['size_bytes']==3013109 and v['checksum_sha256']==SHA
    after=G.load(P+'r2-after.json');before=G.load(P+'r2-before.json')
    assert after['object_count']==before['object_count']+1 and after['total_bytes']==before['total_bytes']+3013109
    oldobjects={x['key']:x['size_bytes'] for x in before['objects']};newobjects={x['key']:x['size_bytes'] for x in after['objects']};assert newobjects=={**oldobjects,KEY:3013109}
    page=(G.ROOT/PAGE).read_text(encoding='utf-8-sig');assert '### School Zone Active Times' not in page
    page=page.replace('### APS Vision Zero Task Force Records',(G.ROOT/(P+'publication.md')).read_text(encoding='utf-8-sig').rstrip()+'\n\n### APS Vision Zero Task Force Records',1)
    (G.ROOT/PAGE).write_text(page,encoding='utf-8',newline='\n')
    save('project-state/r2-inventory.json',after)
    G.active_check('mutation','inventory_disposition',[ID])
    proposed=G.load(OLD+'source-record.json');review=G.load(OLD+'review.json');sc=review['scope_assessment']
    scope=dict(assessed_at=now(),geographic_institutional_scope=sc['geographic_institutional_scope'],specific_albuquerque_connection=sc['specific_material_albuquerque_connection'],abqinfo_public_information_value=sc['public_information_value'],general_context_exclusion_test=sc['exclusion_test'],final_scope_decision='passes_both_gates',substantive_rationale=sc['substantive_rationale'])
    q=dict(document_function='One complete supplied IPRA school-zone flasher schedule reference dataset.',substantive_content='Thirty distinct schedules, thirty-two named schools and sixty-one active intervals with maps, weekdays and controller qualifications.',durable_public_usefulness='Direct alphabetical lookup of Albuquerque school-zone flasher schedules alongside the unchanged source original.',information_density='Thirty substantive timing sheets within one full thirty-three-page dataset; duplicate sheet and map fragments retained only in original.',unique_information='Concrete local flasher intervals unavailable on City or APS public websites per owner provenance attestation.',rationale=sc['substantive_rationale'],reviewed_document_content=True,visual_inspection_completed=True,publication_form='standalone',series_relationship='standalone',page_count=33,extracted_word_count=2543,currentness_review_required=True,currentness_review=dict(status='historical_status_uncertain',authoritative_sources=[OLD+'review.json'],finding='PDF has individual dated notes but no issuing agency, global effective date or confirmation all schedules remain current.',publication_qualification='Public introduction expressly disclaims one global effective date and confirmation that every schedule remains current.'))
    description='Provides Albuquerque school-zone flasher activation schedules for middle and high schools, including shared-school entries, weekday gaps and controller exceptions. This IPRA-obtained record has no identified issuing agency or single effective date; the full original is archived unchanged.'
    row=dict(id=ID,status='implemented',source_url=None,direct_file_url=None,r2_url=URL,r2_key=KEY,r2_etag=next(x['etag'] for x in after['objects'] if x['key']==KEY),r2_last_modified=next(x['last_modified'] for x in after['objects'] if x['key']==KEY),agency=None,title=proposed['title'],date=None,file_type='PDF',size_bytes=3013109,checksum_sha256=SHA,page_count=33,parent_url=None,referring_urls=[],discovery_path=[SOURCE],discovery_method='owner-provided unchanged original obtained through IPRA',crawl_depth=0,cited_predecessors=[],cited_successors=[],provenance_status='owner-provided IPRA original; exact source and full public archive bytes verified; source identifies no agency or public official URL',provenance=proposed['provenance'],scope_assessment=scope,quality_assessment=review['quality_assessment'],publication_quality_decision=dict(decision='passes',evidence=[OLD+'review.json',OLD+'source-inspection.json'],assessment=q),proposed_canonical_page=PAGE,description=description,description_word_count=len(description.split()),processing_notes=['Complete prior review preserved at '+OLD,'One exact owner-authorized original upload; public exact-byte receipt '+P+'public-verification.json','Implemented only on unmerged PR branch; not deployed. Elementary record expected later and outside population.'],implementation_location=PAGE,implementation_locations=[PAGE],cross_listing_approved=False,validation_status='passed',exclusion_reason=None,local_path=SOURCE,discovered_at='2026-10-06',updated_at=now(),workflow_state='archive_verified_publication_pr_preparation',source_record_evidence=P+'source-record.json')
    from PublicationQuality import require_publication_quality
    require_publication_quality(row)
    inv=G.load('project-state/master-inventory.json');assert ID not in {x['id'] for x in inv['candidates']};inv['candidates'].append(row)
    from collections import Counter
    counts=Counter(x['status'] for x in inv['candidates']);inv['counts']={s:counts[s] for s in inv['allowed_statuses']};inv['generated_at']=now();save('project-state/master-inventory.json',inv)
    save(P+'source-record.json',row)
    # Truthful null official URL is supported only for this exact verified IPRA record.
    validator=G.ROOT/'scripts/project/Test-MasterInventory.ps1';s=validator.read_text(encoding='utf-8-sig')
    old="if ($candidate.status -eq 'validated' -and $candidate.r2_url -and -not $candidate.source_url)"
    # Keep existing validated-source policy unchanged: this row is implemented on an unmerged PR.
    assert old in s
    queue=G.load('project-state/governance/pr214-postmerge-closeout-2026-10-06/queue.json');queue.update(artifact_type='school_zone_publication_queue',recorded_at=now(),source_queue_artifact='project-state/governance/pr214-postmerge-closeout-2026-10-06/queue.json',inventory_generated_at=inv['generated_at'],school_zone_implemented_ids_added=[ID]);save(P+'queue.json',queue)
    save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp['school_zone_timing_review'].update(state='archive_verified_publication_pr_preparation',archival_authorized=True,archive_verified=True,remaining_gate='owner_manual_pr_review',public_verification=P+'public-verification.json',publication=P+'publication.md');cp['next_owner_requested_task'].update(state='archive_verified_publication_pr_preparation',remaining_gate='owner_manual_pr_review',publication=P+'publication.md');save('project-state/checkpoint.json',cp)
    plan=G.load(P+'implementation.json');plan['events']+=[dict(operation=o,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=t,evidence=e) for o,t,e in [('archive','Uploaded exact authorized original once after complete live absent-key/storage preflight; full public GET size/hash verified.',P+'public-verification.json'),('content_implementation','Added reviewed alphabetical schedules with all intervals and operational qualifiers, truthful IPRA/currentness provenance and independently verified Cleveland spelling.',P+'publication.md'),('inventory_disposition','Added exact source record with positive scope and publication quality; existing inventory rows unchanged.',P+'source-record.json')]];save(P+'implementation.json',plan)
    refresh()
def guard():
    st=StageSnapshot(TASK);pop=st.load_json(st.load_json(G.ACTIVE_TASK)['population']);assert pop['candidate_ids']==[ID]
    paths=set(G.git('diff',BASE,st.end,'--name-only').splitlines()) if st.end else set(G.changed_paths(BASE));assert paths<=set(pop['artifact_paths'])|{PAGE},paths-set(pop['artifact_paths'])-{PAGE}
    start=st.load_json(P+'starting-state.json')
    for path,h in start['prior_evidence_sha256'].items():assert G.file_hash(path)==h,path
    a={x['id']:x for x in json.loads(G.git('show',BASE+':project-state/master-inventory.json'))['candidates']};b={x['id']:x for x in st.load_json('project-state/master-inventory.json')['candidates']};assert all(b.get(i)==x for i,x in a.items());assert set(b)-set(a)<={ID}
    page=st.read_text(PAGE);old=G.git('show',BASE+':'+PAGE).replace('\r\n','\n')+'\n'
    if '### School Zone Active Times' in page:
        content=st.read_text(P+'publication.md');assert page==old.replace('### APS Vision Zero Task Force Records',content.rstrip()+'\n\n### APS Vision Zero Task Force Records',1)
        data=st.load_json(OLD+'timings.json');assert sum(len(s['intervals']) for s in data['schedules'])==61
        for s in data['schedules']:
            label=s['school_label'].replace('Clevland Middle School','Cleveland Middle School').replace('Valley high school','Valley High School');assert '**'+label+'**' in content
            for t in s['intervals']:assert t['start']+' to '+t['end'] in content
        assert 'owner' not in content.lower() and 'not school bell times' in content and 'does not identify an issuing agency' in content
        v=st.load_json(P+'public-verification.json');assert v['size_bytes']==3013109 and v['checksum_sha256']==SHA and v['byte_identical']
        from PublicationQuality import require_publication_quality
        require_publication_quality(b[ID]);assert b[ID]['source_url'] is None
    else:assert page==old
    cp=st.load_json('project-state/checkpoint.json');before=start['checkpoint_before'];derived=['school_zone_timing_review','next_owner_requested_task','resume_command','total_candidates','counts_by_status','recorded_at','history','completed_item_range'];assert {k:v for k,v in cp.items() if k not in derived}=={k:v for k,v in before.items() if k not in derived}
    if ID in b:
        assert cp['total_candidates']==len(b) and cp['counts_by_status']['implemented']==before['counts_by_status']['implemented']+1
        assert cp['history'][:len(before['history'])]==before['history']
    print('PASS exact single-source archive/publication stage; prior evidence and unrelated school safety records preserved')
def checkpoint():
    receipt=dict(task_id=TASK,state='archive_verified_content_implemented_validation_pending',source_bytes=3013109,source_sha256=SHA,pages=33,schools=32,schedules=30,intervals=61,r2_uploads=1,archive_verification=P+'public-verification.json',archive_http_result='Complete successful Invoke-WebRequest GET with no-cache; exact bytes/hash match authorized original.',r2_objects=1617,r2_bytes=10986353284,prior_review_preserved=True,elementary_work=False,content_merge_authorized=False,normal_validation='pending',remaining_owner_action='Manual review and merge decision after preview verified and PR open')
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    receipt['governance_accounting']={row['governance_id']:dict(requirement=row['binding_requirement'],result='Prior exact review and all settled source/family decisions preserved. Explicit source-bound owner authority released archive gate; complete absent-key preflight and exact original/public byte verification recorded. Only one source/inventory addition and reviewed existing-page subsection; no elementary work, unrelated edits or merge.',evidence=[P+'authority.json',P+'source-check.json',P+'archive-preflight.json',P+'upload.json',P+'public-verification.json',P+'editorial.json',P+'source-record.json',OLD+'review.json']) for row in c['resolved_rules']}
    save(P+'receipt.json',receipt)
    current=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8-sig')
    links=current[current.index('[Owner correction]'):]
    current='# Current project state\n\nSchool-zone original archived unchanged and full public download verified (3,013,109 bytes; expected SHA-256; 33 pages). R2: 1,617 objects / 10,986,353,284 bytes. School Zone Active Times implemented on publication branch: 30 schedules, 32 named schools, 61 intervals. Scope/quality/safety pass; agency/global effective date remain unstated. Original review and exhaustive dataset preserved. Elementary timing record expected later; outside this population.\n\nNEXT: complete normal/rendered preview checks and open an UNMERGED content PR for owner review. No content merge or production deployment authorized.\n\n[Publication receipt](governance/'+TASK+'/receipt.json) · [Public-byte verification](governance/'+TASK+'/public-verification.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='family_review',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Deterministic consolidated queue regeneration reflects released exact archival owner gate and source record; no substantive review or family population expansion.',evidence='project-state/discovery/consolidated-human-review-queue.json'));save(P+'implementation.json',plan)
    refresh();G.active_check('final');guard()
def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2];verify_only='--verification-only' in sys.argv[3:]
    data=G.load(OLD+'timings.json');results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for name,width,height in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=width,height=height))
            response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
            result=page.evaluate(r'''() => {
              const h=document.getElementById('school-zone-active-times'); if(!h) throw Error('missing anchor');
              let n=h.nextElementSibling; const nodes=[];
              while(n && !(n.tagName==='H2' || n.tagName==='H3')) { nodes.push(n);n=n.nextElementSibling; }
              return {heading:h.innerText,text:nodes.map(n=>n.innerText).join('\n'),entries:nodes.flatMap(n=>Array.from(n.querySelectorAll('li')).map(x=>x.innerText)),links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth};
            }''')
            assert not result['overflow'] and len(result['entries'])==30
            for s in data['schedules']:
                label=s['school_label'].replace('Clevland Middle School','Cleveland Middle School').replace('Valley high school','Valley High School')
                entry=next(e for e in result['entries'] if e.startswith(label+':'))
                expected='; '.join(t['start']+' to '+t['end']+' ('+('Monday-Friday' if t['weekday_verbatim']=='M-F' else 'weekday not stated')+')' for t in s['intervals'])
                assert expected in entry,(label,entry,expected)
                assert ' '.join(s['location_verbatim'].split()) in ' '.join(entry.split()),label
                if s['operational_note']:assert s['operational_note'] in entry,label
                # Scroll every record into view, verify all schedule lines fit the viewport horizontally.
                node=page.locator('li').filter(has=page.locator('strong',has_text=label)).filter(has_text=expected).first
                node.scroll_into_view_if_needed();box=node.bounding_box();assert box and box['x']>=0 and box['x']+box['width']<=width+1
            assert 'the owner' not in result['text'].lower()
            assert [x['url'] for x in result['links'] if x['url'].startswith('https://files.abqinfo.com/')]==[URL]
            archive=page.request.get(URL,headers={'Cache-Control':'no-cache'},timeout=180000);raw=archive.body();assert archive.status==200 and len(raw)==3013109 and hashlib.sha256(raw).hexdigest()==SHA
            page.goto('about:blank');page.goto(url.split('#')[0]+'#school-zone-active-times',wait_until='networkidle')
            page.wait_for_function("document.getElementById('school-zone-active-times').getBoundingClientRect().top >= -1 && document.getElementById('school-zone-active-times').getBoundingClientRect().top < innerHeight",timeout=10000)
            anchor=page.locator('#school-zone-active-times').bounding_box();assert anchor and -1<=anchor['y']<height
            # Full new section capture, without unrelated site sections.
            page.evaluate('''() => { const h=document.getElementById('school-zone-active-times');const w=document.createElement('div');h.parentNode.insertBefore(w,h);let n=h;while(n){const next=n.nextElementSibling;if(n!==h&&(n.tagName==='H2'||n.tagName==='H3'))break;w.appendChild(n);n=next;}w.id='school-zone-review-capture'; }''')
            output=G.ROOT/('tmp/school-zone-final-'+name+'.png' if verify_only else P+'preview-'+name+'.png')
            page.locator('#school-zone-review-capture').screenshot(path=str(output))
            result.update(viewport=name,width=width,anchor_passed=True,every_interval_weekday_location_and_material_note_matched=True,all_30_entries_scrolled_and_fit_width=True,public_get_http_status=archive.status,public_get_bytes=len(raw),public_get_sha256=hashlib.sha256(raw).hexdigest(),screenshot_sha256=hashlib.sha256(output.read_bytes()).hexdigest());results.append(result);page.close()
        browser.close()
    value=dict(url=url,head_sha=G.git('rev-parse','HEAD'),rendered_at=now(),browser='Installed Google Chrome via Playwright',results=results)
    if verify_only:
        old=G.load(P+'preview.json');assert [x['text'] for x in old['results']]==[x['text'] for x in results];print('PASS final-head preview exactly matches inspected section')
    else:save(P+'preview.json',value);print('PASS nonproduction desktop/mobile: all 30 schedules and 61 intervals/qualifiers, archive full GET, anchor, no overflow')
if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
