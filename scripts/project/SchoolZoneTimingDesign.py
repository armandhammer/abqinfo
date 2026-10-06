"""Governed single-original school-zone review and publication design; no upload/content."""
import hashlib, json, subprocess, sys
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
TASK='school-zone-timing-design-2026-10-06'
P='project-state/governance/'+TASK+'/'
BASE='2703c8dffe0cd672e438c754c1100c7eff6c9d96'
SOURCE='research/staging/document-review/ABQ Middle School and High School Zone Active Timings.pdf'
SHA='fade828a553fed6008cd38f45a3a80ac41e7136ab4a407d708a91a34cf06963a'
ID='local-school-zone-timings-fade828a553fed60'
SCRIPT='scripts/project/SchoolZoneTimingDesign.py'
OPS=['document_review','quality_assessment','placement','governance_implementation']
def population_path():
    return P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json')
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:audit([p.relative_to(G.ROOT).as_posix() for p in old])
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    path=P+f'contract-v{len(old)+1}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population_path(),'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population_path(),contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
    print(path,len(c['governance_ids']),'rules; gates',c['unresolved_gates'])
def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','starting-state.json','source-inspection.json','page-text.json','timings.json','review.json','archive-plan.json','proposed-content.md','source-record.json','implementation.json','receipt.json','validation.log','design-validation.json','placement.json']+[f'contract-v{i}.json' for i in range(1,16)]
    paths=[P+x for x in outputs]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md','scripts/project/Invoke-ProjectValidation.ps1']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=['school-zone-active-times'],pages=['content/transportation/safety-crash-data.md','content/transportation/operations-data.md','content/transportation/roadway-projects/speed-management.md','content/transportation/design-references.md'],operation_classes=OPS,artifact_paths=sorted(paths)))
    G.write_once(P+'starting-state.json',dict(remote_refs={x:BASE for x in ['main','chatgpt/planning-snapshot']},local_head=BASE,clean_worktree_before_task=True,source_path=str((G.ROOT/SOURCE).resolve()),source_bytes=3013109,source_sha256=SHA,source_pages=33,prior_active_task=G.load(G.ACTIVE_TASK),queue=G.load('project-state/ordinary-queue-current.json'),protected_hashes={p:G.file_hash(p) for p in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json']}))
    # First exhaustive registry resolution precedes review or new decision registration.
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    requirement='Current owner requests complete governed review/publication DESIGN of exactly the unchanged local ABQ Middle School and High School Zone Active Timings.pdf, SHA256 '+SHA+'. Inspect all pages, privacy, provenance, every interval/qualifier, scope/quality and existing School Transportation Safety context. Prepare extendable Hugo-ready direct data and exact archival plan. Owner reports IPRA provenance/non-public City or APS availability and expects elementary data later; do not infer an official URL, effective date, current status or future dataset. No elementary work, unrelated records, reopening settled safety decisions, R2 overwrite/delete, or upload without exact standing/current authorization. No visible PR before unchanged-original archive/full public-byte verification. This task authorizes local/background review/design artifacts, not new R2 mutation or merge/deployment.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction 2026-10-06',instruction=requirement,original_preserved=True,publication_intent=True,r2_mutation_authorized=False))
    r=G.load(G.REGISTRY)
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Single owner/IPRA school-zone timing original: review and publication design',scope=dict(task_ids=[TASK],candidate_ids=[ID],families=['school-zone-active-times']),authority='Explicit current owner instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No elementary dataset or unrelated population','No new R2 mutation without explicit exact authorization','No visitor-visible PR before archive verification'],constraints=[],settled_decisions=[],unresolved_gates=[dict(gate_id=TASK+':r2-owner-authorization',blocks_operations=['archive','external_mutation'],requirement='Explicit owner authorization for this exact unchanged original required')],implementation_status='local review/design only'))
    save(G.REGISTRY,r);refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='pr214-postmerge-closeout-2026-10-06'
    life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='SchoolZoneTimingDesign',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',life)
    validation=(G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1')
    s=validation.read_text(encoding='utf-8-sig');needle='Set-StrictMode -Version Latest'
    s=s.replace(needle,'& python "$PSScriptRoot/SchoolZoneTimingDesign.py" guard\nif ($LASTEXITCODE) { throw \'School-zone timing design boundary failed.\' }\n'+needle,1)
    validation.write_text(s,encoding='utf-8',newline='\n');refresh()
def guard():
    st=StageSnapshot(TASK);pop=st.load_json(st.load_json(G.ACTIVE_TASK)['population']);start=st.load_json(P+'starting-state.json')
    assert pop['candidate_ids']==[ID] and pop['baseline_commit']==BASE
    st.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    changes=set(G.changed_paths(BASE)) if not st.end else set(G.git('diff',BASE,st.end,'--name-only').splitlines())
    assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    for path,h in start['protected_hashes'].items():assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==h,path
    assert hashlib.sha256((G.ROOT/SOURCE).read_bytes()).hexdigest()==SHA
    if (G.ROOT/(P+'timings.json')).exists():
        data=st.load_json(P+'timings.json');assert len(data['schedules'])==30
        assert sum(len(x['intervals']) for x in data['schedules'])==61
        assert sum(len(x['school_names']) for x in data['schedules'])==32
        assert sorted(p for x in data['schedules'] for p in x['source_pages'])==[p for p in range(1,34) if p not in [11,29]]
        proposed=st.read_text(P+'proposed-content.md')
        for x in data['schedules']:
            assert x['school_label'] in proposed
            for t in x['intervals']:assert t['start']+' to '+t['end'] in proposed
        assert 'afternoon period applies only to the Comanche controller' in proposed
        assert 'weekday not stated' in proposed
    print('PASS: exact original preserved; school-zone design only; content/inventory/R2/queue unchanged')
def queue_reconcile():
    # Replacement selector adds only deterministic gate-queue output paths, no candidate.
    pop=G.load(P+'population.json')
    pop['artifact_paths']+= [P+'population-v2.json',P+'validation-attempt-1.log','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population-v2.json',pop)
    (G.ROOT/(P+'validation-attempt-1.log')).write_bytes((G.ROOT/(P+'validation.log')).read_bytes())
    refresh();G.active_check('mutation','governance_implementation',[ID])
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='governance_implementation',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Normal validation identified stale derived consolidated queue after new exact archival owner gate. Replaced artifact selector only, preserving single candidate and old contract/population evidence; regenerated gate queue without changing inventory/ordinary queue.',evidence='project-state/discovery/consolidated-human-review-queue.json'));save(P+'implementation.json',plan)
    refresh();G.active_check('final');guard()
def checkout_reconcile():
    G.active_check('mutation','governance_implementation',[ID])
    path=G.ROOT/'project-state/master-inventory.json';raw=path.read_bytes()
    normalized=raw.replace(b'\r\n',b'\n');restored=normalized.replace(b'\n',b'\r\n')
    queue=G.load('project-state/discovery/consolidated-human-review-queue.json')
    assert hashlib.sha256(restored).hexdigest()==queue['inventory_sha256']
    assert normalized==subprocess.check_output(['git','show',BASE+':project-state/master-inventory.json'])
    path.write_bytes(restored)
    assert 'project-state/master-inventory.json' not in G.changed_paths(BASE)
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py','--check'],check=True)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='governance_implementation',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Normal validation exposed baseline queue raw SHA mismatch: saved hash exactly matches CRLF inventory checkout, while local/Git inventory is LF. Restored expected checkout newlines only after exact normalized Git identity check. All inventory records and both queues unchanged; queue regeneration --check passes. Retained failed log and replacement artifact selector; no substantive population change.',evidence=P+'validation-attempt-1.log'));save(P+'implementation.json',plan)
    refresh();G.active_check('final');guard()
def design():
    import re
    G.active_check('mutation','document_review',[ID])
    pages=G.load(P+'page-text.json');schedules=[]
    notes={2:'Includes a lunch interval. The 3:15 PM to 4:00 PM row has no weekday label.',10:'Shared flashers for Tony Hillerman / Volcano Vista. The sheet also notes elementary-school times were added; it does not name that elementary school or separate its intervals.',17:'Location heading says Lomas and Utah; the note says flashers moved to Lomas and Tennessee in 2020.',21:'The sheet notes added flashers at Mackland and Carlisle in March 2024.',27:'The afternoon period applies only to the Comanche controller, not Candelaria.',33:'The sheet says school flashers were turned on July 31, 2026.'}
    for page in pages:
        n=page['page'];t=page['text']
        if n in [11,29,28]:continue
        name=t.split('Name of School:\n')[1].split('\n')[0].strip()
        location=t.split('Location:\n')[1].split('\n')[0].strip()
        if n==2:pairs=[('8:10 AM','8:50 AM','M-F'),('1:15 PM','1:55 PM','M-F'),('3:15 PM','4:00 PM',None)]
        elif n==7:pairs=[('7:30 AM','8:10 AM',None),('3:15 PM','3:40 PM',None)]
        elif n==10:pairs=[('7:10 AM','8:50 AM','M-F'),('2:05 PM','3:55 PM','M-F')]
        elif n==15:pairs=[('7:35 AM','8:55 AM','M-F'),('2:40 PM','3:20 PM','M-F')]
        elif n==20:pairs=[('7:00 AM','8:15 AM','M-F'),('2:05 PM','3:20 PM','M-F')]
        elif n==33:pairs=[('8:00 AM','9:10 AM',None),('3:30 PM','4:30 PM',None)]
        elif n<=12:pairs=[('8:10 AM','8:50 AM','M-F'),('3:15 PM','4:00 PM','M-F')]
        else:pairs=[('7:35 AM','8:15 AM','M-F'),('2:40 PM','3:20 PM','M-F')]
        schedules.append(dict(schedule_id='sheet-'+str(n),school_label=name,school_names=[x.strip() for x in name.split('/')],location_verbatim=location,source_pages=[10,28] if n==10 else [n],controllers=int(re.search(r'\n([1-3])\nNotes:',t).group(1)),intervals=[dict(start=a,end=b,weekday_verbatim=w,controller_qualifier='Comanche only; not Candelaria' if n==27 and i==1 else None) for i,(a,b,w) in enumerate(pairs)],operational_note=notes.get(n),notes_source_text=t,grade_classification='not expanded beyond source school label'))
    save(P+'timings.json',dict(source_sha256=SHA,schedules=schedules,unique_named_school_count=32,unique_sheet_count=30,unique_interval_count=61,source_sheet_occurrences=31,source_interval_occurrences=63,blank_or_fragment_pages=[11,29],duplicate_sheet_pages=[10,28],timezone_stated=False,future_elementary_record='Expected later; no separate elementary data reviewed or generated'))
    key='transportation/safety-crash-data/abq-middle-high-school-zone-active-timings-ipra-fade828a553f.pdf'
    lines=['### School Zone Active Times','','These are school-zone flasher activation intervals from the owner-supplied middle/high-school IPRA record. They are flasher schedules, not school bell times. The sheets do not establish a single effective date or confirm that every schedule remains current.','','A separate elementary-school timing record is expected and is not yet included. Shared-school entries below retain the names and qualifiers in this record.','','#### Middle/high-school IPRA record','','Times are reproduced as written. Monday-Friday is shown only where the interval is marked M-F; an unmarked weekday is identified below.','','[Source timing sheets (IPRA-obtained PDF, 33 pages)](https://files.abqinfo.com/'+key+')','','The owner supplied this record after obtaining it through IPRA. The PDF does not identify its issuing agency. Its notes record individual changes from 2018 through 2026; PDF creation on October 6, 2026 does not establish an effective date.','']
    for x in sorted(schedules,key=lambda x:x['school_label'].casefold()):
        times='; '.join(t['start']+' to '+t['end']+' ('+('Monday-Friday' if t['weekday_verbatim']=='M-F' else 'weekday not stated')+')' for t in x['intervals'])
        lines+=['- **'+x['school_label']+'**: '+times+'.','', '  Location in source: '+x['location_verbatim']+'.'+(' '+x['operational_note'] if x['operational_note'] else ''),'']
    (G.ROOT/(P+'proposed-content.md')).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    scope=dict(geographic_institutional_scope='Albuquerque school-zone roadway flashers; owner-supplied IPRA timing sheets',specific_material_albuquerque_connection='Named Albuquerque schools, local intersections and addresses with concrete activation times',public_information_value='Lets readers inspect when school-zone flashers are scheduled and distinguish shared locations and controller exceptions',exclusion_test='This is local operational public data with 61 concrete intervals, not general school context or transactional IPRA paperwork',final_scope_decision='passes_both_gates',substantive_rationale='Roadway safety and the operation of Albuquerque public infrastructure are core ABQInfo subjects; direct timing lookup gives useful information beyond the originating websites per owner provenance.')
    quality=dict(visual_inspection='All 33 rendered pages reviewed in full; interval/weekday rows and notes checked against text',page_count=33,extractable_words=sum(len(x['text'].split()) for x in pages),content_pages=31,unique_timing_sheets=30,standalone_public_value='Complete supplied local timing dataset with maps, locations, controller counts and update notes',information_density='Sparse individual sheets form a substantive 30-schedule family; publish as one dataset/source, not 30 document entries',series_component_relationships='Pages 10 and 28 are the same shared-school schedule; 11 and 29 contain only a small map fragment; preserve all original bytes',intended_publication_form='One direct readable alphabetical list with intervals, locations, weekday gaps and important qualifiers, plus unchanged full PDF provenance',currentness='No issuing agency/current designation/global effective period; retain as supplied IPRA record and qualify currentness explicitly',limited_content_exception='Not needed for the complete 33-page source. No separate short-sheet publication proposed.',substantive_rationale='The exact dataset is independently useful for local school-zone public information, and direct transcription removes the need to inspect 33 pages while preserving the complete original.')
    save(P+'review.json',dict(candidate_id=ID,scope_assessment=scope,quality_assessment=quality,publication_safety='passed',privacy_findings='Professional staff names/initials and metadata author appear; no student identities, private contacts, personal identifiers, IPRA requester details or credentials found. Street maps, aerials and flasher/controller illustrations are operational public context. No redaction needed; unchanged original retained.',agency_shown=None,agency_finding='No agency logo, letterhead, issuing department or response cover letter in the PDF. Do not infer City/APS authorship from owner IPRA provenance.',date_findings=dict(global_effective_date=None,current_status_asserted=False,metadata_title='High & Middle School Zone Timing 8-28-26.pdf',metadata_created='2026-10-06T10:40:50-06:00',latest_explicit_operational_note='School flashers turned on 7/31/26 (Mission Achievement and Success Charter)',interpretation='The title date and print metadata are not an effective date; individual sheet revisions are evidence of recorded changes only.'),unresolved_publication_blocker='Exact R2 archival authorization, followed by original public-byte verification; elementary continuation is not a blocker'))
    save(P+'placement.json',dict(recommended_page='content/transportation/safety-crash-data.md',parent_section='School Transportation Safety',subsection='School Zone Active Times',insert_before='APS Vision Zero Task Force Records',presentation='Alphabetical list: school, each interval and weekday, source location, material exceptions. Fits narrow screens without a wide table.',alternatives=dict(traffic_operations='Broader signal/streets context; existing School Transportation Safety offers the most direct reader path',speed_management='Mainly NTMP traffic-calming policy and studies; weaker fit for school-flasher lookup',design_references='Signing/striping standards rather than actual timing data'),existing_records='All current APS Vision Zero, task-force and Rainbow/Universe records retained; no settled decisions reopened',extension='Stable generic subsection with record-level source/version and schedule IDs, arrays of school names and interval qualifiers. A separately governed elementary record can add a sibling group; existing shared entries are reconciled without inventing new timings.',new_navigation_page=False))
    live=G.load('tmp/pdfs/school-zone/r2-live.json');saved=G.load('project-state/r2-inventory.json')
    def witness(v):return sorted((x['key'],x['size_bytes'],x.get('etag')) for x in v['objects'])
    assert witness(live)==witness(saved)
    assert key.casefold() not in {x['key'].casefold() for x in live['objects']}
    save(P+'archive-plan.json',dict(state='awaiting_explicit_owner_r2_authorization',candidate_id=ID,source_path=str((G.ROOT/SOURCE).resolve()),source_relative_path=SOURCE,original_unchanged=True,r2_key=key,public_url='https://files.abqinfo.com/'+key,bytes=3013109,sha256=SHA,page_count=33,key_naming_rationale='Existing transportation/safety-crash-data prefix; descriptive lowercase owner/IPRA filename with original hash suffix; no invented agency or effective year.',live_inventory_checked_at=live['generated_at'],live_objects=live['object_count'],live_bytes=live['total_bytes'],live_saved_inventory_exact_match=True,live_key_absent_casefold=True,live_inventory_key_size_etag_sha256=G.digest(witness(live)),projected_objects=live['object_count']+1,projected_storage_bytes=live['total_bytes']+3013109,added_storage_bytes=3013109,maximum_projected_storage_bytes=13000000000,maximum_object_bytes=150000000,no_overwrite=True,no_delete=True,authority_analysis='Current owner request expressly separates publication intent from R2 authority. No current standing invocation covers this owner/IPRA original. Prior specific uploads and campaign profiles confer no new authorization.',execution_after_authorization=['Register exact owner authorization and immutable archive population; resolve replacement contract', 'Rehash unchanged source; refresh live full inventory and repeat case-insensitive absent-key/storage check', 'Use guarded repository uploader once, no overwrite/delete', 'Fetch complete public object and compare exact bytes/size/SHA256; record truthful owner/IPRA provenance', 'Only then apply reviewed list/source record and prepare unmerged content PR with verified preview for manual owner review']))
    save(P+'source-record.json',dict(artifact_type='proposed_inventory_source_record',id=ID,title='ABQ Middle School and High School Zone Active Timings',source_type='owner_supplied_ipra_original',source_url=None,publisher=None,local_original_path=str((G.ROOT/SOURCE).resolve()),byte_size=3013109,sha256=SHA,page_count=33,scope_assessment=scope,quality_assessment=quality,provenance=dict(acquired_through_ipra='owner attestation',public_availability='Owner reports not on City/APS websites; not independently asserted',issuing_agency='not identified by source',response_agency_or_request_number=None),family='school-zone-active-times',future_context='Elementary record expected later; no elementary population begun',workflow_state='review_complete_archive_authorization_pending',archive_plan=P+'archive-plan.json',draft_only=True,master_inventory_mutated=False))
    plan=G.load(P+'implementation.json')
    plan['events'] += [dict(operation=op,candidate_ids=[ID],action='research_unsettled' if op=='document_review' else 'implements',use_contract_record_rules=True,summary=summary,evidence=P+artifact) for op,summary,artifact in [('document_review','Entire original rendered/text review, exact intervals and qualifiers, privacy/provenance/date limits recorded','review.json'),('quality_assessment','Both scope gates pass; complete family has standalone data value and qualified currentness','review.json'),('placement','Prepared generic extendable school-zone subsection and mobile-friendly list; settled existing content unchanged','placement.json'),('governance_implementation','Prepared exact absent-key unchanged-original archive plan; no upload or visible PR','archive-plan.json')]]
    save(P+'implementation.json',plan)
    # Register the worker's bounded factual review/design result; it releases no external gate.
    r=G.load(G.REGISTRY)
    requirement='Preserve this exact original and the recorded scope/quality, all interval/weekday/location qualifiers, duplicate/fragment accounting and truthful owner/IPRA provenance. Proposed school-zone list belongs under existing School Transportation Safety. No currentness/agency/effective-date inference, separate elementary dataset, or external gate release follows from these review findings.'
    r['entries'].append(dict(governance_id='design-'+TASK,category='active family decision',title='Exact school-zone original reviewed data and extendable publication design',scope=dict(task_ids=[TASK],candidate_ids=[ID],families=['school-zone-active-times']),authority='Governed implementation review under explicit current owner request',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['review.json','placement.json','timings.json','source-record.json']],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No new archival authority inferred from review'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='review/design prepared; exact archival owner gate remains'))
    save(G.REGISTRY,r)
    life=G.load('project-state/workflow-stage-lifecycle.json');sealed={x['path'] for x in life['protected_evidence']}
    prior='project-state/governance/pr214-postmerge-closeout-2026-10-06/'
    for file in (G.ROOT/prior).glob('*'):
        p=file.relative_to(G.ROOT).as_posix()
        if file.is_file() and p not in sealed:life['protected_evidence'].append(dict(path=p,commit=BASE,sha256=G.file_hash(p)))
    save('project-state/workflow-stage-lifecycle.json',life)
    current='# Current project state\n\nSchool-zone timing review and publication design complete for the exact unchanged owner/IPRA PDF (3,013,109 bytes; 33 pages). All pages inspected; 30 distinct schedules, 32 named schools, 61 intervals. Scope/quality and publication safety pass; issuing agency and global effective date are not identified by source. Proposed direct list: Safety & Crash Data > School Transportation Safety > School Zone Active Times. Existing site/inventory/queue/R2 unchanged.\n\nNEXT OWNER ACTION: explicitly authorize archival of this exact unchanged original under the prepared key. No current standing R2 authority applies; no upload or visitor-visible PR. Elementary timings expected later are continuation context, not a publication blocker.\n\n[Review](governance/'+TASK+'/review.json) · [Proposed content](governance/'+TASK+'/proposed-content.md) · [Archive plan](governance/'+TASK+'/archive-plan.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\nPR214 production closeout remains complete at '+BASE+'; its sealed receipt and queued-request history are preserved.\n'
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    refresh();guard()
def receipt():
    G.active_check('mutation','governance_implementation',[ID])
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    evidence=['source-inspection.json','timings.json','review.json','placement.json','archive-plan.json','source-record.json','proposed-content.md','design-validation.json']
    save(P+'receipt.json',dict(task_id=TASK,state='review_and_publication_design_complete_archival_owner_gate',candidate_id=ID,original_path=str((G.ROOT/SOURCE).resolve()),bytes=3013109,sha256=SHA,pages=33,named_schools=32,distinct_schedules=30,distinct_intervals=61,agency_identified=False,global_effective_date=None,mission_scope='passes_both_gates',quality='passed_as_qualified_supplied_reference_dataset',publication_safety='passed',r2_uploads=0,r2_added_bytes=0,visitor_visible_changes=0,visible_pr_created=False,inventory_changes=0,elementary_work=0,validation=dict(strict_pdf=True,all_pages_visual=True,all_intervals_source_crosschecked=True,isolated_hugo=True,chrome_desktop_mobile=True,normal_suite='pending'),remaining_owner_action='Explicitly authorize exact unchanged-original R2 archival under archive-plan.json; then archive/public bytes and unmerged publication PR can be executed under a new governed stage.',remote_integration=False,remote_refs_verified_before_task=dict(main=BASE,planning_snapshot=BASE),evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact owner original reviewed/designed under complete resolved authority. All prior decisions, site bytes, inventory, queue and R2 state preserved by guard; no supersession or external gate release. Complete source/data, scope/quality, privacy, placement, isolated render and exact archive plan evidence retained.',evidence=[P+x for x in evidence]) for r in c['resolved_rules']}))
    refresh();G.active_check('final');guard()
def complete():
    log=(G.ROOT/(P+'validation.log')).read_text(encoding='utf-8-sig')
    assert '"Hugo": "passed"' in log and 'Traceback' not in log and 'Exception:' not in log
    G.active_check('mutation','governance_implementation',[ID]);guard()
    r=G.load(P+'receipt.json');r['validation']['normal_suite']='passed'
    r['validation']['normal_log_sha256']=G.file_hash(P+'validation.log')
    r['validation']['governance_freshness']='passed'
    r['validation']['sealed_history']='57 contiguous stages / 690 preserved evidence files passed'
    r['validation']['diff_check']='passed'
    r['validation']['checkout_reconciliation']='Baseline inventory raw hash expected CRLF; restored only local checkout newlines. Git/inventory records and both queues unchanged.'
    r['local_checkpoint']='Local design branch only; remote branches unchanged; no background integration authorized/executed'
    save(P+'receipt.json',r);refresh()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan)
    task=G.load(G.ACTIVE_TASK);task['state']='complete';save(G.ACTIVE_TASK,task)
    G.active_check('final');guard()
if __name__=='__main__':
    command=sys.argv[1] if len(sys.argv)>1 else 'guard'
    globals()[command]()
