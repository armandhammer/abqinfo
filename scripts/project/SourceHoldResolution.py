"""Exact two-record source research lifecycle; original evidence stays sealed."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git as git_bytes

TASK='source-hold-resolution-2026-10-04'
P='project-state/governance/'+TASK+'/'
BASE='36eff729645ad5f964d7626121d0d8fe0b636b3a'
IDS=['src-ed75a3cb5ecc3b0b','src-1f9cf39555e7be6f']
OWNER='owner-'+TASK
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value):
    p=G.ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def audit(paths):
    r=G.load(G.REGISTRY);a=G.load(r['audit_artifact']);indexed={x['path']:x for x in a['artifacts']}
    for p in paths:
        indexed[p]=dict(path=p,sha256=G.file_hash(p),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale='Exact source retrieval, comparison, execution and baseline evidence; no independent continuing instruction.')
    a['artifacts']=sorted(indexed.values(),key=lambda x:x['path']);save(r['audit_artifact'],a)
    r['audit_sha256']=G.file_hash(r['audit_artifact']);save(G.REGISTRY,r)
def bind(path,gid,requirement,scope):
    r=G.load(G.REGISTRY)
    assert not any(x['governance_id']==gid for x in r['entries'])
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=scope,authority='Explicit current owner two-record provenance/source-delivery research instruction',decision_date='2026-10-04',effective_date='2026-10-04',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded background research authority'))
    save(G.REGISTRY,r)
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old: audit([p.relative_to(G.ROOT).as_posix() for p in old])
    n=max([int(p.stem.split('-v')[1]) for p in old],default=0)+1
    path=P+f'contract-v{n}.json'
    populations=list((G.ROOT/P).glob('population-v*.json'))
    population_path=max(populations,key=lambda p:int(p.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if populations else P+'population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population_path,'--output',path],cwd=G.ROOT,check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','family_review','inventory_disposition','governance_implementation','background_integration','external_mutation'],events=[],status='research_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():
        plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    proposals=P+'integration.json' if (G.ROOT/(P+'integration.json')).exists() else P+'supersession.json'
    save(G.ACTIVE_TASK,dict(population=population_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=proposals))
    print(path,len(c['governance_ids']),'rules; no conflicts or gates')
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    inv=G.load('project-state/master-inventory.json');rows={x['id']:x for x in inv['candidates']}
    assert rows[IDS[0]]['status']=='pending review' and rows[IDS[1]]['status']=='approved for addition'
    outputs=['population.json','authority.json','starting-state.json','prior-records.json','implementation.json','supersession.json','progress.json','receipt.json','accounting.json','summary.md','owner-decisions-needed.json','validation.log','validation-attempt-1.log','validation-attempt-2.log','queue.json','remote-final.json','integration.json','second-street.json','sunport.json','sunport-comparison.json','search-evidence.json','research-journal.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,51)]
    paths += [P+f'retrieval-{i}.json' for i in range(1,101)]
    paths += [P+f'evidence-{i}.txt' for i in range(1,101)]
    paths += [P+f'visual-{i}.png' for i in range(1,31)]
    paths += ['scripts/project/SourceHoldResolution.py','scripts/project/Research-SourceHolds.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/ordinary-queue-current.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','inventory_disposition','governance_implementation','background_integration','external_mutation'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    G.write_once(P+'starting-state.json',dict(checked_at_utc=now(),refs={x:G.git('rev-parse',x) for x in ['HEAD','origin/main','origin/chatgpt/planning-snapshot']},remote_refs=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],cwd=G.ROOT).decode(),prs={str(n):json.loads(subprocess.check_output(['gh','pr','view',str(n),'--json','state,mergedAt,mergeCommit,closedAt,url'],cwd=G.ROOT)) for n in [208,209]},queue_counts={s:sum(x['status']==s for x in inv['candidates']) for s in ['approved for addition','pending review']},r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),prior_campaign_files={p.relative_to(G.ROOT).as_posix():G.file_hash(p) for root in ['project-state/governance/remaining-approved-review-2026-10-03','project-state/governance/pr209-reconciliation-2026-10-03'] for p in (G.ROOT/root).rglob('*') if p.is_file()}))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    instruction='Research exactly src-ed75a3cb5ecc3b0b selected historical FHWA /2nd-street identity and distinct family value to ordinary exhaustion, and src-1f9cf39555e7be6f official City smaller complete delivery equivalence. Preserve settled Sunport scope/quality; no substantive re-review. Related records are evidence only. Current user authorizes evidence-based background dispositions with explicit supersession of these two source holds when resolved, inventory/queue updates, full validation and zero-visible/zero-R2 integration into main followed by synchronized planning-snapshot. Preserve all prior PR209 evidence unchanged. No R2 upload, ceiling increase, derivative, recompression, direct-source-only exception, public link replacement or visitor-visible change is authorized. Only genuine remaining owner authorization choices may be recorded after research exhaustion. Stop after these two records.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',candidate_ids=IDS,instruction=instruction))
    bind(P+'authority.json',OWNER,instruction,{'candidate_ids':IDS,'task_ids':[TASK]})
    save(P+'supersession.json',dict(proposals={}))
    bind(P+'supersession.json','supersessions-'+TASK,'Apply only explicit evidence-based replacements of the exact two source/delivery holds under '+OWNER+'. Preserve prior assessments, history and all other population decisions.',{'task_ids':[TASK]})
    stages=G.load('project-state/workflow-stage-lifecycle.json');assert stages['stages'][-1]['id']=='pr209-reconciliation'
    stages['stages'][-1]['end_commit']=BASE
    stages['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/SourceHoldResolution.py'],exact_delta_guard=dict(module='SourceHoldResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=runner.read_text(encoding='utf-8')
    t=t.replace('Set-StrictMode -Version Latest', '& python "$PSScriptRoot/SourceHoldResolution.py" guard\nif ($LASTEXITCODE) { throw \'Two-record source resolution guard failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(t,encoding='utf-8',newline='\n')
    save(P+'progress.json',dict(state='governed_research_ready',completed=[],remaining=IDS,r2_mutations=0,visitor_visible_mutations=0))
    audit([P+'starting-state.json',P+'prior-records.json',P+'progress.json'])
    refresh();print(G.active_check('mutation','document_review'))
def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for p,k in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==start[k],p
    for p,h in start['prior_campaign_files'].items():assert G.file_hash(p)==h,'Prior PR209 evidence changed: '+p
    before={r['id']:r for r in stage.load_json(P+'prior-records.json')['records']}
    baseline=json.loads(git_bytes('show',BASE+':project-state/master-inventory.json'));a={r['id']:r for r in baseline['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    assert b[IDS[1]]['scope_assessment']==before[IDS[1]]['scope_assessment'] and b[IDS[1]]['quality_assessment']==before[IDS[1]]['quality_assessment'],'Settled Sunport review changed'
    for i in IDS:
        assert b[i]['processing_notes'][:len(before[i]['processing_notes'])]==before[i]['processing_notes'],'Prior history lost'
    changes=set(git_bytes('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    population_path=stage.load_json(G.ACTIVE_TASK)['population']
    assert changes<=set(stage.load_json(population_path)['artifact_paths']),changes-set(stage.load_json(population_path)['artifact_paths'])
    print('Exact two-record / sealed PR209 / zero visible / zero R2 guard passed')
def update_queue():
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    prior=G.load('project-state/governance/remaining-approved-review-2026-10-03/queue.json');q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'}
    q.update(artifact_type='two_record_source_hold_resolution_queue',recorded_at=now(),source_queue_artifact='project-state/governance/remaining-approved-review-2026-10-03/queue.json',inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending))
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending}
        q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q['ungated_pending_ids']=sorted(ungated);q['ungated_pending_count']=len(ungated)
    q['unresolved_ungated_prerequisites']=[r for r in prior['unresolved_ungated_prerequisites'] if r['id'] in ungated]
    q['actionable_ungated_pending_ids']=[i for i in prior['actionable_ungated_pending_ids'] if i in ungated]
    q['genuinely_actionable_ungated_pending_count']=len(q['actionable_ungated_pending_ids'])
    q['background_family_groups']=[dict(f,candidate_ids=[i for i in f['candidate_ids'] if i in pending],candidate_count=len(set(f['candidate_ids'])&pending)) for f in prior['background_family_groups'] if set(f['candidate_ids'])&pending]
    q['newly_approved_backlog']=[dict(r,reason='Exact printing/Legistar identity and official alternate delivery verified; all complete deliveries exceed150000000 bytes. Explicit archival policy/authorization choice remains; no duplicate entry.') for r in prior['newly_approved_backlog'] if rows[r['id']]['status']=='approved for addition']
    q['source_hold_resolution']=dict(task=TASK,population=P+'population.json',accounting=P+'accounting.json',removed_pending_ids=[IDS[0]])
    assert set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|set(q['ungated_pending_ids'])==pending
    assert set(r['id'] for r in q['newly_approved_backlog'])=={i for i,r in rows.items() if r['status']=='approved for addition'}
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
def register_and_apply():
    # Research receipts are final before turning them into controlling decisions.
    G.active_check('mutation','governance_implementation')
    registry=G.load(G.REGISTRY);proposals={}
    for rid,name in zip(IDS,['second-street.json','sunport.json']):
        finding=G.load(P+name);oldid='decision-remaining-approved-review-2026-10-03-'+rid
        old=next(r for r in registry['entries'] if r['governance_id']==oldid)
        new_id='decision-'+TASK+'-'+rid
        proposals[oldid]=dict(authorized=True,existing_governance_id=oldid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+name,proposed_replacement=finding['binding_requirement'],consequences=finding['supersession_consequences'],authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'integration.json')
    G.write_once(P+'integration.json',dict(artifact_type='source_hold_explicit_supersession_receipt',authorization_artifact=P+'authority.json',proposals=proposals))
    save(G.REGISTRY,registry)
    for rid,name in zip(IDS,['second-street.json','sunport.json']):
        bind(P+name,'decision-'+TASK+'-'+rid,G.load(P+name)['binding_requirement'],{'candidate_ids':[rid]})
    bind(P+'integration.json','explicit-supersessions-'+TASK,'Apply these two explicitly owner-authorized, evidence-based source-hold replacements; all historical PR209 source/review evidence and settled Sunport scope/quality remain sealed.',{'task_ids':[TASK]})
    evidence=[p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.is_file() and p.name not in ['authority.json','supersession.json','integration.json','second-street.json','sunport.json','implementation.json'] and not p.name.startswith('contract-v')]
    audit(evidence);refresh()
    apply_records()
def apply_records():
    for name in ['second-street.json','sunport.json']:
        audit(['project-state/master-inventory.json']);refresh()
        G.active_check('mutation','inventory_disposition',IDS)
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+name],cwd=G.ROOT,check=True)
    update_queue()
    audit(['project-state/master-inventory.json',P+'queue.json'])
    plan=G.load(P+'implementation.json')
    plan['events'] += [dict(operation='inventory_disposition',candidate_ids=[rid],action='implements',governance_ids=plan['respected_governance_ids'],summary=G.load(P+name)['binding_requirement'],evidence=P+name) for rid,name in zip(IDS,['second-street.json','sunport.json'])]
    save(P+'implementation.json',plan)
    save(P+'progress.json',dict(state='two_record_research_and_dispositions_complete_validation_pending',completed=IDS,remaining=[],next_population_authorized=False,r2_mutations=0,visitor_visible_mutations=0))
    audit([P+'progress.json']);refresh();G.active_check('mutation','inventory_disposition',IDS);guard()
def complete_findings():
    prior={r['id']:r for r in G.load(P+'prior-records.json')['records']}
    street=G.load(P+'second-street.json')
    street['state']='research_complete'
    street['current_redirect'].update(source='https://flh.fhwa.dot.gov/projects/nm/2nd-street',evidence=P+'retrieval-19.json')
    street['binding_requirement']='The exact selected FHWA endpoint historically identified NM FLAP Trail52000(1), the earlier Second Street SW Corridor project; the current52000(2) page is a later phase, not its migrated copy. Exclude this short historical companion for insufficient independent publication value relative to retained County parent src-492e95f3e1c0db70 and archived 2016 map/boards. Source identity is resolved. Preserve selected URL, all prior evidence and existing family publications. No additional row, visible or R2 action is authorized.'
    street['supersession_consequences']='Replace only the factual pending source-identity hold with an evidence-based companion exclusion. Preserve all prior PR209 reviews and unrelated decisions; County family is evidence only.'
    rationale=street['rationale']
    street['approved_updates']=[dict(id=IDS[0],changes=dict(status='excluded',review_reason='publication_quality_exclusion',exclusion_reason=rationale,provenance_status='Exact selected historical FHWA phase1 content recovered from May9 2017 archived original; current301 redirect goes to official NM index, not phase2.',validation_status='Two-record governed source research complete; exact identity resolved and companion excluded. '+P+'second-street.json',processing_notes=prior[IDS[0]]['processing_notes']+['2026-10-04 exact selected-source resolution: '+rationale+' Original approved/pending history is preserved; its identity hold is explicitly superseded. Evidence: '+P+'second-street.json'],publication_quality_decision=dict(decision='excluded',finding_id=TASK+':'+IDS[0],rationale=rationale,evidence=[P+'second-street.json',P+'retrieval-7.json',P+'retrieval-19.json','content/transportation/roadway-projects/_index.md'],supersedes_finding_id=prior[IDS[0]]['publication_quality_decision']['finding_id'])))]
    save(P+'second-street.json',street)
    comparison=G.load(P+'sunport-comparison.json')
    docs=comparison['documents'];assert docs['printing']['sha256']==docs['legistar']['sha256']=='d4583c4d9e5e1233c402f64222fd8837ff7f0fc0a352dc2d5153776842f39d02'
    assert docs['printing']['page_count']==601 and docs['onbase']['page_count']==607 and docs['onbase']['bytes']==196098909
    deliveries=[]
    for p in sorted((G.ROOT/P).glob('retrieval-*.json'),key=lambda p:int(p.stem.split('-')[1])):
        r=G.load(p)
        if r.get('pdf_valid'):deliveries.append({k:r[k] for k in ['requested_url','final_url','http_status','content_type','exact_byte_length','sha256','pdf_valid','pdf_pages','pdf_metadata','local_path']})
    requirement='Preserve the settled positive Sunport mission and quality review, exact December2019 printing original and existing adopted-plan family. Retain approved status with explicit archive size/authorization hold. Official OnBase12246971 is a607-page full adopted-plan family delivery of196098909 bytes;12246972 is a41-page executive summary, not an equivalent full plan. No complete official below150000000-byte delivery was found in the current City index, directory, airport site, Legistar or official-source search. The printing original and published Legistar8032966 are exactly byte-identical. Replace the unknown delivery facts with these exact results; do not authorize upload, derivative, ceiling change, direct-source-only exception, duplicate entry or public-link replacement.'
    findings=dict(id=IDS[1],state='official_delivery_research_complete',binding_requirement=requirement,supersession_consequences='Replace only unresolved delivery facts with exact retrieval/comparison results. Original source remains canonical; settled scope/quality and all PR209 evidence remain unchanged. Size and future archive/publication authorization remain explicit gates.',settled_document_review_preserved=True,deliveries=deliveries,comparison_receipt=P+'sunport-comparison.json',printing_legistar_relationship=dict(byte_identical=True,bytes=280024902,sha256=docs['printing']['sha256'],pages=601,wrapper_pages=0),onbase_relationship=dict(classification='Official full adopted-plan family delivery, with revised approval front matter and reflowed/corrected print layout; not a byte-identical or page-identical rendering of the601-page original.',pages=607,bytes=196098909,sha256=docs['onbase']['sha256'],below_object_ceiling=False,opening='Cover and approval/title page: Council Bill R-19-168, March4 2020, FINAL PRINTING.',chapter_sequence=['Introduction and Summary','1 Inventory','2 Aviation Demand Forecasts','3 Sustainability Analysis','4 Airport Facility Requirements','5 Airport Alternatives','6 Recommended Development Concept','7 Implementation Plan'],actual_appendix_sequence=['A Glossary of Terms','B Pavement Condition and History','C Forecast Approval Letter','D Hold Line White Paper','E TSS Runway8 White Paper','F SRM Runway12-30 Final Report','G Airport Layout Plan'],toc_difference='The December2019 printing ToC erroneously labels C/D/E as the separately delivered sustainability/water/energy supplemental reports; its actual C/D/E divider pages507/509/531 identify forecast/hold-line/TSS papers. OnBase ToC names these actual appendix subjects correctly.',sequence_coverage=comparison['whole_volume_sequence_comparison'],equivalence_limit='Full-volume text and page alignment establish family continuity and coverage of the core chapters, technical papers and ALP. Page reflow, blank insertions, graphic/text ordering, changed front matter and corrected ToC prevent calling it the exact same601-page rendering. No compliant below-ceiling candidate exists for which stronger replacement equivalence would enable archival.'),official_summary=dict(onbase_id=12246972,bytes=7259996,pages=41,sha256='ed70789e34827f65067f3fe8ff575bc017dab061117d75869ab5d932b9e9133b',airport_site_mirror_byte_identical=True,not_full_plan=True),supplemental_relationship='City index explicitly separates Sections1/2/3 from the full plan: Sustainability Management System Reference Document (78pages), Water Use Report and Conservation Plan Update (66pages), Energy Audit Report (270pages). Exact official bytes and validity recorded; these are not full master plans and no related row is dispositioned.',research_exhaustion=dict(routes=['Current City Planning adopted-plan index and all Sunport deliveries linked there','Live public Sunport documents directory (only printing PDF listed)','Official airport Facts and Figures master-plan link (executive summary only)','Existing adopted-plan Legistar attachment and adoption context','Official-domain title/filename/indexed-document search','Plausible legacy ReducedFileSize endpoint returns404'],result='No official complete full plan at or below150000000 bytes identified. Known complete printing and OnBase deliveries both exceed the ceiling; smaller summary and supplemental files cannot substitute.',limitation='This finding exhausts discoverable public official routes; it does not assert knowledge of unpublished agency files.'),preferred_resolved_delivery_candidate=dict(url=prior[IDS[1]]['source_url'],bytes=280024902,sha256=docs['printing']['sha256'],pages=601,reason='Exact canonical City original is byte-identical to the already-published Legistar family member; it supplies a fully verified source relationship without a version or duplicate-entry issue.',below_object_ceiling=False),factual_delivery_blocker_resolved=True,remaining_gates=['Explicit object-ceiling exception or explicitly authorized derivative/direct-source policy, if archival/public treatment is desired','Explicit unchanged-original R2 upload authorization and exact full public-byte verification before future static archive treatment','Separate governed visitor-visible PR and manual owner review before changing the existing Sunport entry'],owner_decision_artifact=P+'owner-decisions-needed.json',owner_decision_required_for_integration=False,implementation_ready_recommendation='Use the existing Airport Plans entry on transportation-plans.md. The canonical City printing link and current Legistar plan deliver identical bytes; do not create a duplicate entry. Retain approved inventory-only hold and existing public state by default. If the owner wants archival, prefer a narrowly scoped original-object ceiling exception for the exact280024902-byte printing PDF plus explicit upload authority. Future content/source-link changes require their own governed population and reviewed visitor-visible PR. No changes are made here.')
    # Do not repeat a large per-token comparison inside the binding record receipt.
    findings['onbase_relationship']['sequence_coverage']={k:v for k,v in comparison['whole_volume_sequence_comparison'].items() if k!='difference_ranges'}
    findings['approved_updates']=[dict(id=IDS[1],changes=dict(review_reason='archive_size_and_authorization_hold',validation_status='Settled scope/quality preserved; exact official delivery research complete. No complete under-limit City PDF found. Existing printing/Legistar byte identity verified; archive size/authorization gate remains. '+P+'sunport.json',processing_notes=prior[IDS[1]]['processing_notes']+['2026-10-04 source-delivery research only: '+findings['research_exhaustion']['result']+' City printing and existing Legistar delivery are byte-identical280024902-byte601-page originals. OnBase12246971 is196098909bytes/607pages, SHA-256 '+docs['onbase']['sha256']+'; summary12246972 is7259996bytes/41pages. Prior unknown delivery facts are explicitly superseded; positive mission/quality preserved. Evidence: '+P+'sunport.json']))]
    save(P+'sunport.json',findings)
    save(P+'owner-decisions-needed.json',dict(artifact_type='owner_authorization_options_evidence_only',items=[dict(id=IDS[1],question='If archival/public delivery is desired, which exception should govern this existing Sunport family?',factual_research_complete=True,evidence=[P+'sunport.json',P+'sunport-comparison.json'],exact_original=dict(bytes=280024902,pages=601,sha256=docs['printing']['sha256']),official_reduced=dict(bytes=196098909,pages=607,sha256=docs['onbase']['sha256']),normal_ceiling=150000000,default='Keep approved inventory-only archive hold and current published state; no new external or visitor-visible effect.',alternatives=[dict(option='Exact-original object-ceiling exception',effect='Authorize the exact280024902-byte canonical original above the150000000 ceiling and separately authorize its R2 upload/public-byte verification. Preferred if full-original archival is requested; no version ambiguity.'),dict(option='Explicit derivative authorization',effect='Authorize a separately identified compressed derivative with original retained and governed fidelity checks; requires a new task, no transformation is performed here.'),dict(option='Explicit direct-source-only policy exception',effect='Authorize a future official-source-only treatment for this existing family; current legacy site link remains as-is. Any visible link/text change still needs a reviewed PR.'),dict(option='Continue current hold',effect='No policy exception or external action; preserve the approved candidate and current existing entry.')],choice_is_not_authorization=True,required_for_background_integration=False)],genuine_owner_decision_count=1,immediate_owner_answer_required=False))
    save(P+'search-evidence.json',dict(observed_at_utc=now(),method='Web reader/search supplementary official-source evidence; locally blocked FHWA requests are not presented as successful live original-byte retrievals.',queries=['exact selected FHWA URL and variants','NM FLAP TRAIL52000(1) project identifier','NM FLAP TRAIL52000(2) Phase2 official program and shortlist','Albuquerque Sustainable Airport Master Plan official PDFs','ABQ_Sustainable_Airport_Master_Plan filename and ReducedFileSize variants','Official City and airport domain searches'],official_findings=[dict(url='https://highways.dot.gov/federal-lands/flap/accomplishments/2018-new-mexico-report',finding='3-page official program report names TRAIL52000(1),2nd Street SW Corridor, pedestrian/bicycle facilities, CFLHD delivery.'),dict(url='https://highways.dot.gov/media/46536',finding='Official Cycle4 shortlist explicitly names52000(2),1.7-mile urban reconstruction/multiuse path, Bernalillo County/FWS/NPS and Valle de Oro/El Camino Real.'),dict(url='https://highways.dot.gov/media/201951',finding='Current CFL TIP explicitly labels52000(2) as2nd Street SW Corridor Phase2, roadway reconstruction1.7miles,2028program year.'),dict(url='https://highways.dot.gov/federal-lands/projects/nm/flap-trail52000-2',finding='Current52000(2) project page proposes repaving, curb/gutter/sidewalk, stormwater/drainage; anticipated advertisement/construction March/June2028.')]))
    for p in (G.ROOT/P).glob('retrieval-*.json'):
        r=G.load(p)
        if 'response_headers' in r:
            r['response_headers']={k:v for k,v in r['response_headers'].items() if k.lower()!='set-cookie'};save(p.relative_to(G.ROOT).as_posix(),r)
    # Initial concurrent retrievals preceded the exclusive-intent fix; one orphan
    # 403 text body was never cited and is not part of the historical finding.
    orphan=G.ROOT/(P+'evidence-1.txt')
    if orphan.exists():orphan.unlink()
    evidence=[p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.is_file() and p.name not in ['authority.json','supersession.json','implementation.json'] and not p.name.startswith('contract-v')]
    audit(evidence);refresh();G.active_check('mutation','governance_implementation');guard()
def prepare_completion():
    G.active_check('mutation','governance_implementation');guard()
    inv=G.load('project-state/master-inventory.json');q=G.load(P+'queue.json')
    baseline=G.load('research/staging/source-hold-resolution-2026-10-04/r2-live-start.json');saved=G.load('project-state/r2-inventory.json')
    identity=lambda x:{o['key']:(o['size_bytes'],o['etag']) for o in x['objects']}
    assert identity(baseline)==identity(saved)
    accounting=dict(task_id=TASK,population=IDS,completed=2,outcomes=[dict(id=IDS[0],status='excluded',source_identity_resolved=True,treatment='Historical FHWA phase1 companion to retained County corridor; no distinct standalone value.'),dict(id=IDS[1],status='approved for addition',substantive_review_preserved=True,factual_delivery_question_resolved=True,verified_under_limit_complete_candidate=None,archive_hold=True)],counts_by_status=inv['counts'],final_queue_counts={k:q[k] for k in ['pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count','ungated_pending_count','genuinely_actionable_ungated_pending_count']},approved_count=inv['counts']['approved for addition'],genuine_owner_decisions=1,owner_decision_required_for_integration=False,r2=dict(object_count=baseline['object_count'],total_bytes=baseline['total_bytes'],added_objects=0,added_storage_bytes=0,changed_objects=0,deleted_objects=0,live_listing_matches_repository=True),visitor_visible_changes=0,preserved_prior_campaign_files=len(G.load(P+'starting-state.json')['prior_campaign_files']),next_population_authorized=False)
    save(P+'accounting.json',accounting)
    save(P+'receipt.json',dict(task_id=TASK,state='research_and_inventory_complete_validation_pending',accounting=P+'accounting.json',research=[P+'second-street.json',P+'sunport.json'],comparison=P+'sunport-comparison.json',settled_sunport_scope_quality_preserved=True,explicit_supersession=P+'integration.json',prior_campaign_evidence_preserved=True,r2_delta_bytes=0,visitor_visible_delta=0,approved=1,pending=372,genuine_owner_decision_count=1,owner_decision_artifact=P+'owner-decisions-needed.json',owner_decision_required_for_integration=False,normal_validation='pending',hugo_rendered_checks='pending',git_diff_check='passed'))
    current='# Current project state\n\nPRs [#208](https://github.com/armandhammer/abqinfo/pull/208) and [#209](https://github.com/armandhammer/abqinfo/pull/209) are merged/closed; PR209 campaign evidence is sealed. Exactly two source holds researched: historical FHWA2nd Street is phase1 TRAIL52000(1), excluded as a companion to the retained County corridor; phase2 is distinct. Sunport printing and published Legistar bytes match. City OnBase full-plan delivery is196,098,909bytes/607pages; no full official delivery below150MB found. Settled Sunport scope/quality preserved; archive hold remains. One optional Sunport archival-policy choice is documented; none is required for background integration. Queue:1 approved /372 pending. No active publication or next review population. R2 and visitor-visible content unchanged.\n\n[Two-record receipt](governance/source-hold-resolution-2026-10-04/receipt.json) · [Owner options](governance/source-hold-resolution-2026-10-04/owner-decisions-needed.json) · [PR209 reconciliation](governance/pr209-reconciliation-2026-10-03/receipt.json) · [Active task](governance/active-task.json) · [PR207 correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [PR207 closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n'
    assert len(current)<=1800
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    summary='''# Two-record source-hold research

The selected historical FHWA URL was recovered from the May 9, 2017 archive capture. It identifies NM FLAP Trail 52000(1), not the current Phase 2 number 52000(2). The 1.5-mile route, dates, photos and locator corroborate the already-retained County corridor and map/boards. It is excluded as a low-value independent companion; the selected URL and prior evidence remain intact.

Sunport scope/quality was not re-reviewed. Exact full City responses establish: printing/Legistar are byte-identical 280,024,902-byte / 601-page PDFs, SHA-256 d4583c4d9e5e1233c402f64222fd8837ff7f0fc0a352dc2d5153776842f39d02. OnBase 12246971 is 196,098,909 bytes / 607 pages, SHA-256 01e3595538a6c6d92dedc7563930fb09de08be75a5c8cc0eb099129745900ca1; its approved front matter, corrected contents and page reflow differ from the printing original. All core chapters and actual appendix subjects are present. OnBase 12246972 and the airport-site mirror are identical 7,259,996-byte / 41-page executive summaries, SHA-256 ed70789e34827f65067f3fe8ff575bc017dab061117d75869ab5d932b9e9133b. Supplemental files are separate components.

No discoverable official complete plan below 150,000,000 bytes was found. Research resolves the unknown delivery facts; size/authorization gates remain. Prefer the exact printing original for the existing Sunport family if a narrowly scoped object-ceiling exception and R2 upload are later authorized. No duplicate entry or new source-only exception is made. Optional owner alternatives are documented in owner-decisions-needed.json; integration needs no owner answer.

Accounting: one approved, 372 pending; only these two rows changed. Prior PR209 evidence, all other inventory rows, all visitor-visible paths and R2 are unchanged. No next population is launched. Full normal validation, Hugo/rendered checks and final synchronized refs are recorded in receipt.json and remote-final.json.
'''
    (G.ROOT/(P+'summary.md')).write_text(summary,encoding='utf-8',newline='\n')
    audit([P+'accounting.json',P+'receipt.json',P+'summary.md','project-state/CURRENT.md'])
    refresh();G.active_check('final');guard()
if __name__=='__main__':
    {'freeze':freeze,'refresh':refresh,'guard':guard,'apply':register_and_apply,'apply-records':apply_records,'findings':complete_findings,'prepare-completion':prepare_completion,'queue':update_queue}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
