"""Nine-record background interactive-application review; exact-delta lifecycle."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
import TaskGovernance as G
import SourceHoldResolution as S
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

TASK='interactive-app-resolution-2026-10-04'
P='project-state/governance/'+TASK+'/'
BASE='2756c058a4485022992ac7e697c3e046ca9031fc'
IDS=['src-29bec2b60308d513','src-58b6e48562da781c','src-5a12b40f6dcba285','src-a9ddff947a4282c9','src-fe8c43a2ca9b7417','src-4c2b3614256aaf20','src-27314f06651cc1c9','src-7867bdf940d22b3f','src-aece84c62701c551']
save=S.save

def bind(path,gid,requirement,scope):
    S.bind(path,gid,requirement,scope)
    data=G.load(G.REGISTRY)
    next(r for r in data['entries'] if r['governance_id']==gid)['authority']='Explicit current owner exact nine-record rendered/live-application background review instruction'
    save(G.REGISTRY,data)

def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:S.audit([x.relative_to(G.ROOT).as_posix() for x in old])
    n=max([int(x.stem.split('-v')[1]) for x in old],default=0)+1
    path=P+f'contract-v{n}.json'
    populations=list((G.ROOT/P).glob('population-v*.json'))
    population=max(populations,key=lambda x:int(x.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if populations else P+'population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration'],events=[],status='in_progress')
    subjects={}
    for rule in c['resolved_rules']:
        for f in rule.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    active=dict(population=population,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress')
    if (G.ROOT/(P+'evidence-41.json')).exists():active['supersession_proposals_path']=P+'evidence-41.json'
    save(G.ACTIVE_TASK,active)
    print(path,len(c['governance_ids']),'rules; no conflicts or gates')

def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    q=G.load(G.load('project-state/ordinary-queue-current.json')['artifact']);assert set(q['ungated_pending_ids'])==set(IDS)
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    assert all(rows[i]['status']=='pending review' for i in IDS)
    outputs=['population.json','authority.json','starting-state.json','prior-records.json','prior-preparation.json','implementation.json','progress.json','receipt.json','accounting.json','summary.md','queue.json','validation.log','remote-final.json','browser-capability.json']
    outputs += [f'contract-v{i}.json' for i in range(1,101)]
    outputs += [f'evidence-{i}.json' for i in range(1,201)]
    outputs += [f'render-{i}.json' for i in range(1,101)]
    outputs += [f'review-{i}.json' for i in range(1,10)]
    paths=[P+x for x in outputs]+['scripts/project/InteractiveAppResolution.py','scripts/project/Inspect-InteractiveApps.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/ordinary-queue-current.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    G.write_once(P+'starting-state.json',dict(checked_at_utc=S.now(),refs={x:G.git('rev-parse',x) for x in ['HEAD','main','origin/main','chatgpt/planning-snapshot']},remote_refs='2756c058a4485022992ac7e697c3e046ca9031fc refs/heads/main\n2756c058a4485022992ac7e697c3e046ca9031fc refs/heads/chatgpt/planning-snapshot\n',remote_verification='Live git ls-remote origin under approved network access',queue_counts={s:sum(r['status']==s for r in inv['candidates']) for s in ['approved for addition','pending review']},prior_active_task=G.load(G.ACTIVE_TASK),r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),prerequisites=q['unresolved_ungated_prerequisites']))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    authority='Current user authorizes exactly these nine pending records for rendered/live-application background review and evidence-based inventory dispositions. Require actual desktop application rendering where established by prior prerequisites; HTTP or ArcGIS metadata alone cannot establish usability. Review the two MRMPO portfolios together. Preserve original URLs, prior evidence and settled decisions. Save and push each completed record or coupled pair. No visitor-visible content/navigation, R2 action, publication PR, Sunport hold change or additional population is authorized. Complete normal/governance/sealed-history/Hugo/rendered validation before background-only main integration; synchronize planning-snapshot and CURRENT.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',candidate_ids=IDS,instruction=authority))
    bind(P+'authority.json','owner-'+TASK,authority,{'candidate_ids':IDS,'task_ids':[TASK]})
    stages=G.load('project-state/workflow-stage-lifecycle.json');stages['stages'][-1]['end_commit']=BASE
    stages['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/InteractiveAppResolution.py'],exact_delta_guard=dict(module='InteractiveAppResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=runner.read_text(encoding='utf-8');t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/InteractiveAppResolution.py" guard\nif ($LASTEXITCODE) { throw \'Nine-record interactive review guard failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(t,encoding='utf-8',newline='\n')
    save(P+'progress.json',dict(state='governed_review_ready',completed=[],remaining=IDS,visitor_visible_delta=0,r2_delta_bytes=0))
    S.audit([P+'starting-state.json',P+'prior-records.json',P+'progress.json']);refresh();G.active_check('mutation','document_review')

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for p,k in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==start[k],p
    a={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        assert a[i]['source_url']==b[i]['source_url'] and b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes']
        for key in ['r2_url','r2_key','r2_etag','r2_last_modified']:assert a[i].get(key)==b[i].get(key)
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    populations=list((G.ROOT/P).glob('population-v*.json'))
    population=max(populations,key=lambda x:int(x.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if populations else P+'population.json'
    pop=stage.load_json(population);assert pop['candidate_ids']==IDS
    assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    derived='project-state/discovery/consolidated-human-review-queue.json'
    if derived in changes:
        before=json.loads(git('show',BASE+':'+derived));after=stage.load_json(derived)
        before.pop('inventory_sha256');after.pop('inventory_sha256')
        assert before==after and after['record_count']==after['package_count']==0,'Owner queue may refresh only its derived inventory hash'
    if 'project-state/checkpoint.json' in changes:
        before=json.loads(git('show',BASE+':project-state/checkpoint.json'));after=stage.load_json('project-state/checkpoint.json')
        for key in ['recorded_at','completed_item_range','counts_by_status','remaining_nonterminal','resume_command']:before.pop(key);after.pop(key)
        assert before==after,'Preserve all historical and unrelated checkpoint metadata'
    print('Nine-record exact inventory / original provenance / zero visitor-visible / zero R2 guard passed')

def audit_refresh():
    files=[x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/P).glob('*') if x.is_file() and x.name not in ['authority.json','implementation.json'] and not x.name.startswith('contract-v') and not x.name.startswith('review-')]
    S.audit(files);refresh()

def queue():
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    prior=G.load('project-state/governance/source-hold-resolution-2026-10-04/queue.json');q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'}
    q.update(artifact_type='nine_record_interactive_application_resolution_queue',recorded_at=S.now(),source_queue_artifact='project-state/governance/source-hold-resolution-2026-10-04/queue.json',inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending))
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending};q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q['ungated_pending_ids']=sorted(ungated);q['ungated_pending_count']=len(ungated)
    q['unresolved_ungated_prerequisites']=[r for r in prior['unresolved_ungated_prerequisites'] if r['id'] in ungated]
    q['actionable_ungated_pending_ids']=[];q['genuinely_actionable_ungated_pending_count']=0
    q['newly_approved_backlog']=[r for r in prior['newly_approved_backlog'] if rows[r['id']]['status']=='approved for addition']
    for i in IDS:
        if rows[i]['status']=='approved for addition':q['newly_approved_backlog'].append(dict(id=i,title=rows[i]['title'],reason='Rendered and substantively assessed live application; separate reviewed visitor-visible PR required; no R2 object applicable.',canonical_page=rows[i].get('proposed_canonical_page'),evidence=P+f'review-{IDS.index(i)+1}.json'))
    q['background_family_groups']=[dict(f,candidate_ids=[i for i in f['candidate_ids'] if i in pending],candidate_count=len(set(f['candidate_ids'])&pending)) for f in prior['background_family_groups'] if set(f['candidate_ids'])&pending]
    q['interactive_app_resolution']=dict(task=TASK,population=P+'population.json',completed_ids=[i for i in IDS if rows[i]['status']!='pending review'])
    assert set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|set(q['ungated_pending_ids'])==pending
    assert set(r['id'] for r in q['newly_approved_backlog'])=={i for i,r in rows.items() if r['status']=='approved for addition'}
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))

def apply(numbers):
    G.active_check('mutation','governance_implementation')
    for n in numbers:
        path=P+f'review-{n}.json';review=G.load(path)
        assert review['id']==IDS[n-1] and review['state']=='review_complete'
        gid='decision-'+TASK+'-'+review['id']
        existing=next((x for x in G.load(G.REGISTRY)['entries'] if x['governance_id']==gid),None)
        if existing:assert existing['binding_requirement']==review['binding_requirement'] and existing['controlling_artifacts'][0]['sha256']==G.file_hash(path)
        else:bind(path,gid,review['binding_requirement'],{'candidate_ids':[review['id']]})
    audit_refresh()
    for n in numbers:
        G.active_check('mutation','inventory_disposition',[IDS[n-1]])
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+f'review-{n}.json'],check=True)
        S.audit(['project-state/master-inventory.json']);refresh()
    queue()
    plan=G.load(P+'implementation.json')
    for n in numbers:plan['events'].append(dict(operation='inventory_disposition',candidate_ids=[IDS[n-1]],action='implements',governance_ids=plan['respected_governance_ids'],summary=G.load(P+f'review-{n}.json')['binding_requirement'],evidence=P+f'review-{n}.json'))
    save(P+'implementation.json',plan)
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    save(P+'progress.json',dict(state='record_checkpoints_in_progress',completed=[i for i in IDS if rows[i]['status']!='pending review'],remaining=[i for i in IDS if rows[i]['status']=='pending review'],visitor_visible_delta=0,r2_delta_bytes=0))
    audit_refresh();guard();print(G.active_check('mutation','inventory_disposition',[IDS[n-1] for n in numbers])['task_id'])

def review(n,status,facts,rationale,evidence,page=None,canonical=None):
    """Prepare an explicit independently assessed review; no inventory mutation."""
    rid=IDS[n-1];prior=G.load(P+'prior-records.json')['records'][n-1]
    required=['source_identity','current_usability','mission_scope','information_density','unique_public_information_value','currentness','family_canonical_relationship','intended_publication_form','visual_observation','implementation_ready_recommendation']
    assert all(facts.get(k) for k in required)
    requirement=f'{rid}: {status}. {rationale} Preserve original URL/provenance and prior evidence; no visitor-visible or R2 action is authorized by this disposition.'
    changes=dict(status=status,review_reason='rendered_live_application_resolution',validation_status='Governed actual rendered/source/family review complete. '+P+f'review-{n}.json',processing_notes=prior['processing_notes']+['2026-10-04 rendered live-application review: '+rationale+' Evidence: '+P+f'review-{n}.json'])
    if status=='approved for addition':
        changes['scope_assessment']=dict(assessed_at=S.now(),geographic_institutional_scope=facts['mission_scope'],specific_albuquerque_connection=facts.get('specific_albuquerque_connection',facts['mission_scope']),abqinfo_public_information_value=facts['unique_public_information_value'],general_context_exclusion_test=facts['exclusion_test'],final_scope_decision='passes_both_gates',substantive_rationale=rationale)
        q=dict(document_function=facts['source_identity'],substantive_content=facts['information_density'],durable_public_usefulness=facts['unique_public_information_value'],information_density=facts['information_density'],unique_information=facts['family_canonical_relationship'],rationale=rationale,reviewed_document_content=True,visual_inspection_completed=True,publication_form='live_service',series_relationship='standalone',page_count=0,extracted_word_count=facts['measured_visible_word_count'],currentness_review_required=True,currentness_review=dict(status='current',authoritative_sources=evidence,finding=facts['currentness'],publication_qualification='Live official application; item modification is not a guarantee of individual dataset freshness. '+facts.get('publication_qualification','')))
        changes.update(proposed_canonical_page=page,description=facts.get('description'),quality_assessment=q,publication_quality_decision=dict(decision='passes',finding_id=TASK+':'+rid,rationale=rationale,evidence=evidence,assessment=q))
    else:changes.update(exclusion_reason=rationale,publication_quality_decision=dict(decision=status,finding_id=TASK+':'+rid,rationale=rationale,evidence=evidence))
    if canonical:changes['canonical_candidate_id']=canonical
    output=dict(id=rid,state='review_complete',binding_requirement=requirement,final_background_disposition=status,evidence=evidence,**facts,approved_updates=[dict(id=rid,changes=changes)])
    save(P+f'review-{n}.json',output)
    return output

def prepare_completion():
    G.active_check('mutation','governance_implementation');guard();queue()
    inv=G.load('project-state/master-inventory.json');q=G.load(P+'queue.json')
    rows={r['id']:r for r in inv['candidates']}
    reviews=[G.load(P+f'review-{n}.json') for n in range(1,10)]
    assert all(r['id']==i and rows[i]['status']==r['final_background_disposition'] for i,r in zip(IDS,reviews))
    assert inv['counts']['approved for addition']==7 and inv['counts']['pending review']==363
    assert q['ungated_pending_count']==0 and q['pending_review_count']==363
    accounting=dict(task_id=TASK,baseline_commit=BASE,population=IDS,fully_resolved=9,
        outcomes=[dict(id=r['id'],status=r['final_background_disposition'],review=P+f'review-{n}.json',recommendation=r['implementation_ready_recommendation']) for n,r in enumerate(reviews,1)],
        counts_by_status=inv['counts'],queue_counts={k:q[k] for k in ['pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count','ungated_pending_count','genuinely_actionable_ungated_pending_count']},
        approved=7,pending=363,new_live_approvals=6,new_exclusions=3,genuine_owner_decisions=0,blocked_selected_records=[],sunport_policy_choice='Unchanged optional choice; outside this task.',
        visitor_visible_changes=0,r2=dict(added_objects=0,changed_objects=0,deleted_objects=0,added_storage_bytes=0,verification='No R2 mutation tool or storage command invoked. Exact baseline R2 inventory/policy and all original record storage fields preserved by guard; no fresh remote listing claimed.'),next_population_authorized=False)
    save(P+'accounting.json',accounting)
    save(P+'receipt.json',dict(task_id=TASK,state='nine_record_review_complete_validation_pending',baseline=BASE,authority=P+'authority.json',population=P+'population.json',accounting=P+'accounting.json',review_artifacts=[P+f'review-{n}.json' for n in range(1,10)],fully_resolved=9,approved=7,pending=363,new_live_approvals=6,new_exclusions=3,genuine_owner_decision_count=0,owner_decision_required=False,blocked_selected_records=[],prior_evidence_preserved=True,original_urls_preserved=True,visitor_visible_delta=0,r2_delta_objects=0,r2_delta_bytes=0,sunport_hold_unchanged=True,no_publication_task_started=True,normal_validation='pending',hugo_rendered_checks='pending',git_diff_check='pending',validation_log=P+'validation.log',integration_authority=P+'authority.json',integration_targets=['refs/heads/main','refs/heads/chatgpt/planning-snapshot'],final_commit_locator='The commit containing the completed receipt is the completion seal; query authoritative refs after its atomic push.',final_runtime_evidence='research/staging/'+TASK+'/final-runtime.json'))
    text='''# Nine-record rendered application review

Exactly nine pending records were inspected using installed Chrome through Python Playwright at 1440 by 1000. The computer-use connector exposed no browser; installed Chromium execution under permitted network access supplied a real rendering surface. No installation was needed. Compact DOM/accessibility observations, actions, screenshot hashes/paths, and supporting source/API responses are retained here; browser caches and PNGs remain ignored research artifacts. APIs were supporting evidence, not usability substitutes.

Six approved live resources: City Council district map (nine polygons and Councilor popup); restored Bikeways wrapper (same app, new map/service); NTMP emergency/ineligible-roadways map (geographic policy component); two distinct MRMPO portfolios (five access maps versus six air-quality/health-equity maps); and one grouped historical City transportation-performance directory (seven functioning Cognos charts, 95 annual observations). Approvals are inventory-only recommendations. Publication still requires a separate governed and manually reviewed content PR.

Three exclusions: Parks/Open Space application requires City login and exposes no public facilities; retired School Crossing MapJournal has an Item Replacement screen with no recoverable replacement target; Walk Safe New Mexico Experience is statewide navigation whose only Albuquerque content is an outbound Vision Zero link. Preserve original URLs and prior evidence. The already-published School Crossings Dashboard is a related functional family resource, not a proven designated redirect successor. The PSAP StoryMap already represents substantive PSAP content; it is not this statewide portal.

Bikeways is restored at its original app ID, not a title-inferred successor. Its current City service replaces the obsolete service function; no outside inventory rows or public links were altered. The MRMPO portfolios have disjoint child dashboard IDs and separately labeled official MRCOG parent links. Both have genuine local geographic analysis. Historical demographic/model vintages constrain their descriptions: ACS 2016-2020; the air portfolio uses EPA 2021 EJScreen 2.0. The Transportation directory's flight/revenue charts end FY2018; other charts end FY2020. Working service/copyright/modified dates do not establish current data.

Limitations: Council address-search submission stalled; map district selection and legend were verified. Not every layer toggle or export option was exercised. Retired school item APIs do not disclose a designated successor; exclusion is resolved without inventing one. Render-review-2's visual observation lists screenshot 1 in its overview; the actual Council wrapper proof is render-3, supplemented by render-4/5 and official same-app metadata. No historical settlement was reopened.

Accounting: 9 of 9 fully resolved; six approved, three excluded. Overall queue: 7 approved / 363 pending (321 gated and 42 source/structural blockers); zero ungated pending and zero new owner decisions. The prior optional Sunport archive-policy choice and its approved hold are unchanged and outside this task. No additional population, publication PR, visible content/navigation, or R2 mutation was launched. Per-record or paired review/inventory checkpoints were pushed before closeout. The final receipt and normal validation log record completion validation and authorized background integration.
'''
    (G.ROOT/(P+'summary.md')).write_text(text,encoding='utf-8',newline='\n')
    old=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8')
    links=old[old.index('[Evidence closeout]'):]
    current='# Current project state\n\nExactly nine interactive-app prerequisites resolved through desktop Chrome rendering: six live-resource recommendations approved; parks/login-only app, retired school app and statewide PSAP navigation portal excluded. MRMPO portfolios are distinct (five access / six air-equity maps). City transportation charts end FY2018 or FY2020. Queue: 7 approved / 363 pending; zero ungated pending. No new owner decision or unfinished publication task. Sunport archive hold/optional policy choice remains outside this task. No visitor-visible or R2 changes. Full completion validation pending; reviewed checkpoints pushed.\n\n[Interactive review](governance/interactive-app-resolution-2026-10-04/receipt.json) · '+links
    assert len(current)<=1800
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    save(P+'progress.json',dict(state='nine_reviews_complete_validation_pending',completed=IDS,remaining=[],visitor_visible_delta=0,r2_delta_bytes=0,next_population_authorized=False))
    audit_refresh();G.active_check('final');guard()

if __name__=='__main__':{'freeze':freeze,'refresh':audit_refresh,'guard':guard,'prepare-completion':prepare_completion}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
