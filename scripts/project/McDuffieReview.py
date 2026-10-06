"""Bounded McDuffie final-report review and owner-review publication stage."""
import copy, hashlib, json, subprocess, sys
import TaskGovernance as G
from PgsLegislativeResolution import save, audit, now
from WorkflowStageLifecycle import StageSnapshot, git, canonical_bytes
TASK='mcduffie-review-2026-10-06'
P='project-state/governance/'+TASK+'/'
BASE='0c4568484e19115a28a3258cc3b68eef821d8005'
ID='src-2f89e1bc040e1d33'
PRIOR='project-state/governance/mcduffie-source-recovery-2026-10-06/'
SCRIPT='scripts/project/McDuffieReview.py'
PAGE='content/transportation/roadway-projects/studies.md'
KEY='transportation/roadway-projects/studies/cabq-mcduffie-twin-parks-final-traffic-calming-study-2024.pdf'
def pop_path():
    if (G.ROOT/(P+'population-v3.json')).exists():return P+'population-v3.json'
    return P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json')

def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']: a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    n=max([int(p.stem.split('-v')[1]) for p in (G.ROOT/P).glob('contract-v*.json')],default=0)+1
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',pop_path(),'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path); assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(actions=G.load(P+'population.json')['operation_classes'],events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(artifact_type='task_implementation_plan',contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    receipt=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan['completion_evidence']={gid:[dict(path=receipt,sha256=G.file_hash(receipt))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=pop_path(),contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; no gates/conflicts')

def event(op,summary,evidence):
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',plan)

def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','starting-state.json','supersession.json','implementation.json','progress.json','receipt.json','review.json','family.json','page-analysis.json','report-text.txt','queue.json','accounting.json','updates.json','archive-plan.json','r2-live-before.json','r2-live-after.json','r2-preflight.json','r2-result.json','public-download.pdf','validation.log','rendered-check.json','preview.json','preview.png','pr-description.md','remote-final.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,101)]+[P+f'pages-{i}.png' for i in range(1,50)]
    paths += [SCRIPT,'scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/r2-inventory.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md',PAGE]
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=[PAGE],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','archive','external_mutation','content_implementation','content_removal','placement','visitor_visible_change','background_integration'],artifact_paths=paths))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));assert not c['conflicts']
    instruction='Current explicit owner instruction: independently review exactly src-2f89e1bc040e1d33 Final McDuffie-Twin Parks Traffic Calming Study under complete governance. Preserve conclusive preceding source recovery and exact original. Fresh two-gate scope and complete report/family/quality review; historical approved recommendations are evidence only. If justified, archive only unchanged verified 11940327-byte PDF under ordinary-review-large class after live storage/preflight, absent-key/no-overwrite guards, exact full public-byte verification. Prepare only substantively justified existing McDuffie section change in an UNMERGED owner-review content PR with Chrome/Playwright rendered Cloudflare preview. Never merge or deploy. If excluded, authorized background main/planning reconciliation. No Sandia or other population or R2 mutations. Full normal suite, fresh/final contract, sealed history, queues, Hugo/rendered, CURRENT/checkpoint and diff checks. This new stage replaces only completed source-recovery-stage no-R2/no-visible restrictions; preserves all original recovery evidence and unrelated settled governance.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction 2026-10-06',candidate_ids=[ID],instruction=instruction))
    r=G.registry();gid='owner-'+TASK
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title='Exact McDuffie substantive review and conditional publication preparation',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current user instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No merge/deploy; no other population or R2 object mutation.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='independent substantive review'))
    old=next(x for x in r['entries'] if x['governance_id']=='owner-mcduffie-source-recovery-2026-10-06')
    proposal=dict(existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=old['controlling_artifacts'],new_evidence=[PRIOR+'receipt.json',P+'authority.json'],proposed_replacement=instruction,consequences='Completed factual recovery remains sealed; new exact-record review and conditional archival/owner-review PR authority replaces prior stage-only restriction.',authorization_artifact=P+'authority.json',authorized=True)
    save(P+'supersession.json',dict(proposals={old['governance_id']:proposal}))
    old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'authority.json');save(G.REGISTRY,r)
    row=next(x for x in G.load('project-state/master-inventory.json')['candidates'] if x['id']==ID)
    protected=git('ls-tree','-r','--name-only',BASE,'--',PRIOR).decode().splitlines()
    save(P+'starting-state.json',dict(observed_at=now(),remote_refs=dict(main=BASE,planning_snapshot=BASE),remote_verification='Independent escalated git ls-remote; both equal clean local HEAD.',selected_row=row,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],protected_sha256={p:G.file_hash(p) for p in protected},r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json')))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    seal()

def seal():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    protected=git('ls-tree','-r','--name-only',BASE,'--',PRIOR).decode().splitlines()
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='mcduffie-source-recovery-2026-10-06'
    life['stages'][-1]['end_commit']=BASE
    existing={s['path'] for s in life['protected_evidence']}
    for p in protected:
        if p not in existing:life['protected_evidence'].append(dict(path=p,commit=BASE,sha256=G.file_hash(p)))
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='McDuffieReview',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf8').replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/McDuffieReview.py" guard\nif ($LASTEXITCODE) { throw \'McDuffie review exact-population guard failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(s,encoding='utf8',newline='\n')
    event('governance_implementation','One-record population frozen, complete registry resolved and source-recovery stage sealed at independently verified synchronized remote endpoint.',P+'starting-state.json')
    save(P+'progress.json',dict(state='governed_review_ready',remaining=['complete report and family review','scope/quality disposition','conditional archive/content PR','full validation'],population=[ID]))
    refresh();G.active_check('mutation','document_review',[ID]);guard()

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    for p,h in start['protected_sha256'].items():assert G.file_hash(p)==h,'Recovery evidence changed: '+p
    assert G.file_hash('project-state/r2-storage-policy.json')==start['r2_policy_sha256']
    a={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']}
    b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<={ID}
    for k in ['source_url','parent_url','local_path','checksum_sha256','size_bytes']:
        assert a[ID].get(k)==b[ID].get(k),(ID,k)
    assert b[ID]['processing_notes'][:len(a[ID]['processing_notes'])]==a[ID]['processing_notes']
    changed=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changed<=set(stage.load_json(pop_path())['artifact_paths']),changed-set(stage.load_json(pop_path())['artifact_paths'])
    visible=[p for p in changed if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'];assert set(visible)<={PAGE}
    if PAGE in visible:
        original=git('show',BASE+':'+PAGE).decode().replace('\r\n','\n');current=stage.read_text(PAGE)
        begin='### McDuffie-Twin Parks\n';end='### Rainbow Boulevard\n'
        assert original.split(begin)[0]==current.split(begin)[0] and original.split(end)[1]==current.split(end)[1],'Unrelated visible change'
        from PublicationQuality import require_publication_quality
        require_publication_quality(b[ID])
        result=stage.load_json(P+'r2-result.json');assert result['verified'] and result['size_bytes']==11940327 and result['sha256']==a[ID]['checksum_sha256']
    print('McDuffie exact one-record review guard passed; source evidence, unrelated rows and page sections preserved')

def approve():
    G.active_check('mutation','quality_assessment',[ID])
    scope=dict(assessed_at=now(),title='Final McDuffie-Twin Parks Traffic Calming Study',publisher='City of Albuquerque; prepared by Wilson & Company',date='2024-05-07',geographic_institutional_scope='City-commissioned neighborhood roadway and public-space safety study in Albuquerque, bounded by Lomas Boulevard, Indian School Road, Carlisle Boulevard and Washington Street.',specific_albuquerque_connection='Analyzes named Albuquerque City streets and access to McDuffie Hidden Park, using local tube counts, pedestrian/bicycle counts, crash records and City NTMP criteria to recommend specific infrastructure treatments.',abqinfo_public_information_value='Explains the evidence, eligibility findings, alternatives, resident concerns, recommended locations and conceptual expenditure estimates behind a City neighborhood traffic-calming project. Readers can inspect why different streets and intersections received different recommendations.',general_context_exclusion_test='The report is not statewide guidance, generic engineering context or incidental Albuquerque statistics. Its main function is a location-specific City infrastructure decision record; full analysis and maps provide substantive policy and safety information beyond transactional or peripheral agency paperwork.',final_scope_decision='passes_both_gates',substantive_rationale='The entire report concerns Albuquerque City streets and neighborhood park access. Its integrated measurements, NTMP warrant determinations, mapped alternatives, documented public responses and final recommended treatments let an ABQInfo reader understand the basis and tradeoffs of a material City infrastructure project. These are independently useful public-information findings, rather than eligibility inferred from provenance or a plausible page.',gate_one='passes: direct material City infrastructure connection',gate_two='passes: substantive project decision and public expenditure evidence')
    evidence=[P+'page-analysis.json',P+'report-text.txt']+[P+f'pages-{n}.png' for n in range(1,7)]+[PRIOR+'retrieval.json']
    family=dict(reviewed_inventory_ids=[ID,'src-804c31a041e2eb1f','src-87fd2a5755eea903','src-e0c0fec528761705'],mutation_candidate_ids=[ID],reviewed_pages=[PAGE,'content/transportation/roadway-projects/_index.md','content/transportation/roadway-projects/speed-management.md'],meeting_2_comparison=dict(local_pdf='research/staging/queue/src-804c31a041e2eb1f.pdf',page_count=24,final_report_pdf_pages=list(range(296,320)),all_24_normalized_page_texts_identical=True),decision='Final report is the primary standalone study on existing McDuffie-Twin Parks section, with the existing 2023 meeting entry explicitly related as earlier alternatives also reproduced in Appendix C.',rationale='The complete report adds integrated eligibility analysis, final recommendations, meeting summaries and conceptual costs to the earlier alternatives presentation. The 24-page, 1.36 MB original remains a useful compact historical delivery of what participants saw, under the settled September3 relationship and exact original/source links. Make finality and chronology explicit rather than presenting two undifferentiated studies. The live project entry serves current implementation updates; the final report records the 2024 basis. No new speed-management cross-list, duplicate report or generated consolidated PDF is needed.',existing_first_meeting_disposition='Preserve superseded inventory-only introductory presentation; it is incorporated in final Appendix C and does not need another public entry.',existing_other_rows_unchanged=True)
    save(P+'family.json',family)
    q=dict(document_function='Complete final neighborhood traffic-calming study commissioned by the City, synthesizing existing conditions, safety evaluation and recommended physical treatments.',substantive_content='Read the full main report PDF pages 1-43, including executive summary and sections 1-7; mapped project boundary and roadway sections, 18 counter locations, 2016-2020 crashes, NTMP evaluation, crossing matrix, concepts, both meeting findings and final cost figures. Examined the appendix structures and representative raw traffic data throughout pages 45-256, crash data page 258, meeting summaries pages 260-265 and 292-295, both presentations pages 266-291 and 296-319, and ending pages 320-321.',durable_public_usefulness='Preserves the rationale for neighborhood safety infrastructure, including streets that met or failed traffic-calming thresholds and treatment locations. It remains useful as the historical final 2024 decision basis even as implementation progresses.',information_density='321 pages and 107886 extracted words; 35 numbered main-report pages plus executive summary and extensive tabular supporting traffic data. Main report is dense with comparative tables, crash analysis, annotated aerial maps and recommendations; lengthy data appendices support rather than establish publication value.',unique_information='Integrates neighborhood-specific source measurements, NTMP eligibility determinations, selected improvements, public-meeting responses and conceptual costs absent from the short project webpage and earlier slide-only entry.',rationale='The substantive main report is a self-contained analysis with mapped alternatives and final recommendations, supported by measured traffic/crash data and documented public engagement. It materially helps readers understand Albuquerque neighborhood infrastructure choices. Appendix repetition does not diminish the independent value of the final synthesis, while its historical date and conceptual cost limits can be stated accurately.',standalone_public_value='high',publication_form='standalone',series_relationship='standalone',reviewed_document_content=True,visual_inspection_completed=True,page_count=321,extracted_word_count=107886,limited_content=False,public_engagement=True,engagement_assessment=dict(function='Meeting summaries analyze support, objections and design concerns, document project-team responses and distinguish February introductory alternatives from September proposals.',durable_unique_information='Examples include opposition to Avenida Del Sol one-way conversion, support for crossings and bulbouts, demand for bike-lane delineators, sight-distance rationale for Mackland/Montclaire traffic circle, and later design responses. Counts alone are not the publication basis.',substantive_basis='analysis',evidence=[P+'report-text.txt',P+'pages-5.png',P+'pages-6.png']),currentness_review_required=True,currentness_review=dict(status='historical_status_uncertain',authoritative_sources=[PRIOR+'parent.html.gz',PRIOR+'retrieval.json',P+'report-text.txt'],finding='Final report dated May7 2024; main field counts from September2022 with additional Solano counts in May2023; crash period 2016-2020. Recovered official City page is the live implementation source and reports 2026 construction. Report is a historical study, not current roadway conditions, current law or an as-built implementation record.',publication_qualification='Label final study 2024 and describe recommendations as recommendations. Keep official City share and project page so readers can consult current implementation information. Do not assert conceptual estimates are approved budget or that all alternatives were built.'),limitations=['Appendix D contains only its conceptual-cost-estimates divider, with no detailed worksheets in this 321-page original; numerical conceptual estimates are present in executive summary and sections7.', 'Inconsistent Washington Street/Drive and Constitution/Washington labels and some figure references; preserve exact original and use neutral summary rather than silently correct the source.', 'Engagement appendix contains official meeting attendee names and staff professional contacts; reviewed as public meeting documentation, not a new contact directory.'])
    review=dict(candidate_id=ID,scope_assessment=scope,quality_assessment=q,publication_quality_decision=dict(decision='passes',assessed_at=now(),assessment=q,evidence=evidence+[P+'family.json'],supersedes_findings=[]),family=family,final_disposition='approved for addition; conditional exact-original archive and owner-review PR',source_recovery_reopened=False,visual_pages=[1,7,9,15,25,28,29,30,32,33,37,38,39,40,41,42,43,45,58,100,150,200,233,258,260,264,284,286,290,295,296,302,309,311,314,320])
    save(P+'review.json',review)
    r=G.load(G.REGISTRY);r['entries'].append(dict(governance_id='decision-'+TASK,category='active family decision',title='Independent final-study scope, quality and family assessment',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Evidence-based review under explicit current owner instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+'review.json',sha256=G.file_hash(P+'review.json'),binding_pointers=['/'])],binding_requirement='Exact final report passes both mission gates and standalone publication quality; make it primary in existing McDuffie section, relate earlier meeting original, preserve all other inventory rows and historical evidence. Upload and content remain conditional on live storage and exact public-byte verification; owner-review PR only, no merge.',required_actions=['Implement the recorded scope, quality, family, historical qualification and conditional archival decision.'],prohibited_actions=['No other inventory disposition, duplicate generated master, Speed Management cross-list, merge or production deployment.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='independent eligibility completed'))
    save(G.REGISTRY,r)
    event('quality_assessment','Fresh explicit two-gate scope and full-report/representative visual publication review passes; measured content, limitations and final-study role recorded.',P+'review.json')
    event('family_review','Complete four-row local family inspected without adding mutation candidates; 24 meeting2 pages match embedded appendix. Final study primary, earlier original retained with explicit chronological relation; no duplicate cross-list.',P+'family.json')
    save(P+'updates.json',[dict(id=ID,changes=dict(status='approved for addition',date='2024-05-07',scope_assessment=scope,quality_assessment=q,publication_quality_decision=review['publication_quality_decision'],proposed_canonical_page=PAGE,processing_notes=G.load(P+'starting-state.json')['selected_row']['processing_notes']+['2026-10-06 independent substantive review passes both mission gates and final-report publication quality. Exact preserved 321-page report inspected; scope, main findings, appendices, visual evidence, family chronology and limits recorded in '+P+'review.json. Historical recommendations were not adopted as disposition. Archival/publication conditional on current preflight and public bytes; unmerged owner-review PR only.']))])
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    save(P+'progress.json',dict(state='independently_approved_archive_preflight_pending',completed=['scope','quality','complete local family','preserved original verification'],remaining=['live R2 preflight','exact original archive/public GET','content PR','normal validation'],population=[ID]))
    refresh();guard()

def queue():
    inv=G.load('project-state/master-inventory.json');q=copy.deepcopy(G.load(G.load(P+'starting-state.json')['source_queue']))
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'}
    q.update(artifact_type='mcduffie_independent_review_queue',recorded_at=now(),source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_ids=sorted(pending),pending_review_count=len(pending))
    assert set(q['gated_pending_ids'])<=pending and set(q['source_or_structural_blocked_pending_ids'])<=pending
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),actionable_ungated_pending_ids=[],genuinely_actionable_ungated_pending_count=0,next_actionable_background_family=None,next_actionable_background_families=[],next_work_category='Exact McDuffie owner-review preparation; no new population.')
    approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];q['approved_count']=len(approved)
    q['newly_approved_backlog']=[dict(id=r['id'],title=r['title']) for r in approved]
    q['in_progress_publication']=dict(task=TASK,candidate_ids=[ID],state=G.load(P+'progress.json')['state'])
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    counts=dict(approved=len(approved),pending=len(pending),gated=len(q['gated_pending_ids']),source_structural_blocked=len(q['source_or_structural_blocked_pending_ids']),ungated=len(ungated),actionable=0,human_review=sum(r['status']=='requires human review' for r in inv['candidates']),changed_record_ids=[ID],current_status=next(r['status'] for r in inv['candidates'] if r['id']==ID))
    save(P+'accounting.json',counts)
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],next_pending_id=inv['next_pending_id'],completed_item_range='Exact McDuffie final report independently reviewed under immutable governance; conditional archive and owner-review content preparation.',remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),resume_command='Read CURRENT and mcduffie-review-2026-10-06/progress.json. Resume exactly src-2f89e1bc040e1d33 only; preserve original source recovery. No new population or content merge authority.')
    save('project-state/checkpoint.json',cp)
    refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True,stdout=subprocess.DEVNULL)
    refresh();print(counts)

def preflight():
    live=G.load(P+'r2-live-before.json');saved=G.load('project-state/r2-inventory.json')
    sig=lambda d:{o['key']:(o['size_bytes'],o['etag']) for o in d['objects']}
    assert sig(live)==sig(saved),'Unexplained saved/live R2 drift'
    assert len({o['key'].casefold() for o in live['objects']})==len(live['objects'])
    assert KEY.casefold() not in {o['key'].casefold() for o in live['objects']}
    assert not [o for o in live['objects'] if o['size_bytes']==11940327],'Same-size duplicate needs full-byte disambiguation'
    raw=(G.ROOT/(PRIOR+'download.pdf')).read_bytes();sha=hashlib.sha256(raw).hexdigest();assert len(raw)==11940327 and sha==G.load(P+'starting-state.json')['selected_row']['checksum_sha256']
    assert live['total_bytes']+len(raw)<=G.load('project-state/r2-storage-policy.json')['maximum_projected_r2_bytes'] and len(raw)<=150000000
    pop=G.load(pop_path());pop['artifact_paths'] += [P+'population-v3.json','scripts/project/Archive-McDuffie.ps1']
    pop['archive_objects']=[dict(candidate_id=ID,r2_key=KEY,sha256=sha,size_bytes=len(raw))];G.write_once(P+'population-v3.json',pop)
    save(P+'r2-preflight.json',dict(checked_at=now(),saved_live_exact_key_size_etag_match=True,key_absent_casefold=True,same_size_candidates=[],current_objects=live['object_count'],current_bytes=live['total_bytes'],added_bytes=len(raw),projected_bytes=live['total_bytes']+len(raw),maximum_object_bytes=150000000,maximum_projected_bytes=13000000000,source=PRIOR+'download.pdf',sha256=sha,r2_key=KEY,authority=P+'authority.json',candidate_id=ID,state='upload_intent_saved_no_put_yet',no_overwrite=True,no_delete=True))
    save(P+'archive-plan.json',dict(candidate_ids=[ID],source=PRIOR+'download.pdf',r2_key=KEY,bytes=len(raw),sha256=sha,source_share=G.load(P+'starting-state.json')['selected_row']['source_url'],preflight=P+'r2-preflight.json',authorization='owner-'+TASK))
    event('archive','Exact unchanged-original archive object frozen; full saved/live listing agrees, no same-size candidate, absent casefold key and policy ceiling passed. Upload intent durable before PUT.',P+'r2-preflight.json')
    refresh();G.active_check('mutation','archive',[ID],r2_key=KEY,source_sha256=sha);guard()

def archive_complete():
    result=G.load(P+'r2-result.json');assert result['verified'] and result['size_bytes']==11940327 and result['sha256']==G.load(P+'starting-state.json')['selected_row']['checksum_sha256']
    before=G.load(P+'r2-live-before.json');after=G.load(P+'r2-live-after.json')
    old={o['key']:(o['size_bytes'],o['etag']) for o in before['objects']};new={o['key']:(o['size_bytes'],o['etag']) for o in after['objects']}
    assert set(new)-set(old)=={KEY} and all(new.get(k)==v for k,v in old.items())
    assert after['total_bytes']-before['total_bytes']==11940327 and new[KEY][0]==11940327
    obj=next(o for o in after['objects'] if o['key']==KEY)
    event('archive','Exact original uploaded to absent key; full public GET matches 11940327 bytes and pinned SHA-256. Refreshed listing has exactly one addition, all prior key/size/ETag values unchanged.',P+'r2-result.json')
    text=G.ROOT/(P+'report-text.txt');text.write_text('\n'.join(line.rstrip() for line in text.read_text(encoding='utf8').splitlines()).rstrip()+'\n',encoding='utf8',newline='\n')
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    save('project-state/r2-inventory.json',after)
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    save(P+'updates.json',[dict(id=ID,changes=dict(status='placement assigned',r2_key=KEY,r2_url='https://files.abqinfo.com/'+KEY,r2_etag=obj['etag'],r2_last_modified=obj['last_modified'],validation_status='Exact City original and full public R2 GET match size/SHA-256; archive complete; owner-review content implementation pending.',processing_notes=row['processing_notes']+['2026-10-06 unchanged independently verified official original archived without overwrite under exact owner authorization. Full public GET byte-identical: 11940327 bytes / SHA-256 '+row['checksum_sha256']+'. All prior R2 keys/sizes/ETags unchanged; added storage exactly 11940327 bytes. Receipt: '+P+'r2-result.json.']))])
    refresh();subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    save(P+'progress.json',dict(state='archive_exact_public_verified_content_pending',completed=['independent scope and quality','family','unchanged original archive and full public GET'],remaining=['bounded content','rendered preview','normal validation','unmerged owner-review PR'],population=[ID]))
    refresh();queue();guard()

def implement():
    G.active_check('mutation','content_implementation',[ID],[PAGE])
    assert G.load(P+'r2-result.json')['verified']
    description='Analyzes neighborhood traffic volumes, speeds, crashes, pedestrian crossings, and public feedback, then recommends crossings, bicycle-lane striping, bulbouts, a traffic circle, speed humps or cushions, and park-access markings. Includes NTMP eligibility findings, mapped concepts, and conceptual cost estimates.'
    page=G.ROOT/PAGE;s=page.read_text(encoding='utf8');begin='### McDuffie-Twin Parks\n\n'
    block='- [Final McDuffie-Twin Parks Traffic Calming Study (2024 archived PDF)](https://files.abqinfo.com/'+KEY+')\n\n  '+description+'\n\n  [Official City final-study share](https://sfftp.cabq.gov/f/cf8779d97e34c92c) · [City project page](https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/traffic-street-improvements/copy2_of_the-mcduffie-twin-parks-traffic-calming-study)\n\n  The May 7, 2024 final report records the study findings and recommendations; its cost estimates are conceptual. The earlier meeting presentation below is also reproduced in Appendix C. Consult the City project page for implementation updates.\n\n'
    assert s.count(begin)==1 and KEY not in s
    s=s.replace(begin,begin+block,1)
    obsolete='  The current City page reports that construction began in 2026. Its separately hosted May 2024 final study remains available through the official project page and is queued for archival after its transfer-service download can be captured deterministically.\n\n'
    assert s.count(obsolete)==1;s=s.replace(obsolete,'',1)
    page.write_text(s,encoding='utf8',newline='\n')
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    save(P+'updates.json',[dict(id=ID,changes=dict(status='implemented',description=description,implementation_location=PAGE,implementation_locations=[PAGE],cross_listing_approved=False,validation_status='Implemented on unmerged owner-review branch; exact public archive verified; full suite and preview pending; not live.',processing_notes=row['processing_notes']+['2026-10-06 final report added as primary 2024 study in existing Roadway Studies / McDuffie-Twin Parks section. Earlier 2023 original remains chronologically related and reproduced in Appendix C; obsolete retrieval-blocked sentence removed. No navigation, unrelated page or inventory-row changes. Owner review required before merge.']))])
    event('content_implementation','Final study primary entry and official share/project links added; earlier original explicitly related; obsolete retrieval-blocked sentence removed only within McDuffie section.',PAGE)
    refresh();subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    save(P+'progress.json',dict(state='content_implemented_validation_preview_pending',completed=['review','archive','bounded content'],remaining=['normal validation','Chrome/Playwright preview','unmerged PR'],population=[ID]))
    refresh();queue();guard()

if __name__=='__main__':globals()[sys.argv[1]]()
