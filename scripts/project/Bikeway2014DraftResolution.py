"""Exact 2014 draft review; 2015 final is an immutable read-only comparator."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativePublication import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git, VISIBLE_PATHS
TASK='bikeway-2014-draft-resolution-2026-10-08'
P='project-state/governance/'+TASK+'/'
BASE='7bf604d5c3078a6016099ee3da398e711dc265dd'
ID='src-a614f077ace20401';COMPARATOR='src-27b939c34a1c59fc'
PAGE='content/transportation/bicycling/bike-plans.md'
SCRIPT='scripts/project/Bikeway2014DraftResolution.py'

def now():return datetime.now(timezone.utc).isoformat()

def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        for artifact in row['controlling_artifacts']:
            if artifact['path']=='scripts/project/Invoke-ProjectValidation.ps1' and artifact.get('binding_pointers')==['/implementation']:
                artifact['sha256']=G.file_hash(artifact['path'])
    save(G.REGISTRY,r)
    r=G.registry();registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    n=max(int(p.stem.split('-v')[1]) for p in (G.ROOT/P).glob('contract-v*.json'))+1
    assert n<=50;path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for rule in row.get('constraints',[]):subjects.setdefault(rule['subject'],{})[rule['field']]=rule['equals']
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'authority.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,actions=G.load(P+'population.json')['operation_classes'],completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    # Replacement contracts cite the explicit successor rules; retain original
    # activity authority IDs as historical evidence rather than discarding them.
    successors={old:row['governance_id'] for row in r['entries'] if row['state']=='active' for old in row.get('supersedes',[])}
    for activity in plan['events']:
        prior=activity.get('governance_ids',[])
        revised=[successors.get(gid,gid) for gid in prior]
        if revised!=prior:
            activity.setdefault('historical_governance_ids',prior)
            activity['governance_ids']=revised
    save(P+'implementation.json',plan)
    a=dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress')
    if (G.ROOT/(P+'supersession.json')).exists():a['supersession_proposals_path']=P+'supersession.json'
    save(G.ACTIVE_TASK,a)
    print(path,len(c['governance_ids']),'rules',len(c['unresolved_gates']),'gates')

def event(operation,summary,evidence,candidates=None,action='implements'):
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation=operation,candidate_ids=candidates or [ID],governance_ids=plan['respected_governance_ids'],action=action,summary=summary,evidence=evidence,use_contract_record_rules=True));save(P+'implementation.json',plan)

def bootstrap():
    instruction='Resolve only src-a614f077ace20401, the preserved 131-page 2014 Bikeways and Trails Facilities Plan pre-adoption draft. Use validated 312-page 2015 final src-27b939c34a1c59fc as READ-ONLY version comparator. Reconstruct remote state and all Project instructions; frozen population and immutable complete registry contract. Determine exact identity/date/adoption stage/authoritative provenance, substantive complete-document differences using existing research, unique historical publication value, and accurate description/placement/lifecycle. Do not infer official provenance from R2 or filename. Preserve both originals without overwrite/deletion. If necessary prepare one owner-review visitor-visible correction PR with verified nonproduction preview; DO NOT MERGE. Otherwise only authorized background reconciliation. Preserve unrelated records/governance; full validation; report provenance, quality, lifecycle, visible changes, queues, R2 delta and final refs. This current instruction authorizes evidence-driven resolution of this exact draft prerequisite, not unrelated or comparator disposition changes.'
    G.write_once(P+'authority.json',dict(artifact_type='owner_exact_draft_source_and_quality_authorization',authority='Explicit current owner instruction 2026-10-08',instruction=instruction,mutable_candidate_ids=[ID],read_only_comparator_ids=[COMPARATOR],r2_mutation_authorized=False,content_merge_authorized=False))
    r=G.registry();r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Exact 2014 draft provenance and historical publication review',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner request',decision_date='2026-10-08',effective_date='2026-10-08',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No comparator mutation, R2 overwrite/deletion/upload, content PR merge or unrelated record/governance mutation.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='Exact draft review; final is read-only'))
    save(G.REGISTRY,r)
    rows={row['id']:row for row in G.load('project-state/master-inventory.json')['candidates'] if row['id'] in [ID,COMPARATOR]};G.write_once(P+'baseline-records.json',rows)
    (G.ROOT/(P+'baseline-page.md')).write_bytes((G.ROOT/PAGE).read_bytes())
    previous='project-state/governance/postmerge-continuity-2026-10-08/'
    protected=git('ls-tree','-r','--name-only',BASE,'--',previous).decode().splitlines()+['project-state/r2-inventory.json','project-state/r2-storage-policy.json']
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,remote_refs={'refs/heads/main':BASE,'refs/heads/chatgpt/planning-snapshot':BASE},mutable_candidate_ids=[ID],read_only_comparator_ids=[COMPARATOR],content_tree_oid=G.git('rev-parse',BASE+':content'),source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),protected_sha256={p:G.file_hash(p) for p in protected}))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='postmerge-continuity-2026-10-08';life['stages'][-1]['end_commit']=BASE
    existing={row['path'] for row in life['protected_evidence']}
    for path in protected:
        if path.startswith(previous) and path not in existing:life['protected_evidence'].append(dict(path=path,commit=BASE,sha256=G.file_hash(path)))
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Bikeway2014DraftResolution',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';text=runner.read_text(encoding='utf-8-sig');text=text.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Bikeway2014DraftResolution.py" guard\nif ($LASTEXITCODE) { throw "2014 Bikeway draft exact-population guard failed" }\nSet-StrictMode -Version Latest',1);runner.write_text(text,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='exact_draft_and_read_only_final_frozen',remaining=['Existing evidence and official-source recovery','Complete 131/312 page comparison and visual inspection','Factual quality/lifecycle/visible decision','Full validation and authorized integration/owner-review PR'],r2_delta=0))
    event('governance_implementation','Remote main/planning synchronized at frozen baseline; exact draft mutation population and read-only final comparator registered. Entire prior continuity stage sealed; existing 2024/2015 final and unrelated decisions remain preserved.',P+'starting-state.json')
    refresh();G.active_check('review','document_review',[ID,COMPARATOR]);guard()

def guard():
    stage=StageSnapshot(TASK);pop=stage.load_json(P+'population.json');start=stage.load_json(P+'starting-state.json')
    assert set(pop['candidate_ids'])=={ID,COMPARATOR} and pop['pages']==[PAGE] and pop['baseline_commit']==BASE
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    before={row['id']:row for row in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']}
    after={row['id']:row for row in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert before.keys()==after.keys() and {id for id in before if before[id]!=after[id]}<={ID},'Only the 2014 draft is mutable'
    assert before[COMPARATOR]==after[COMPARATOR],'2015 comparator changed'
    for key in ['r2_url','r2_key','size_bytes','checksum_sha256']:
        assert before[ID][key]==after[ID][key],'Preserved draft original identity changed'
    other=[p for p in changes if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'];assert set(other)<={PAGE},other
    before_page=git('show',BASE+':'+PAGE).decode('utf8').replace('\r\n','\n');after_page=stage.read_text(PAGE)
    if (G.ROOT/(P+'quality-decision.json')).exists():
        decision=stage.load_json(P+'quality-decision.json');old=decision['old_entry'];new=decision['new_entry'];assert before_page.count(old)==1
        assert after_page==before_page.replace(old,new,1),'Visible changes exceed exact draft entry'
    else:assert before_page==after_page,'Premature visible correction'
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json')
        for path,h in receipt.get('evidence_sha256',{}).items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS 2014 draft exact scope: read-only 2015 final, preserved originals/R2/history, unrelated rows and page sections unchanged')

def bind(path,gid,requirement):
    r=G.load(G.REGISTRY)
    assert not any(x['governance_id']==gid for x in r['entries'])
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner exact-draft resolution instruction',decision_date='2026-10-08',effective_date='2026-10-08',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No comparator, unrelated record, original-byte, R2 or production mutation; no content merge.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='Exact draft source/quality reconciliation and unmerged owner-review presentation'))
    save(G.REGISTRY,r)

def decide_and_apply():
    refresh();G.active_check('review','quality_assessment',[ID])
    f=G.load(P+'research-findings.json');assert f['all_pages_visually_inspected'] and f['provenance']['full_byte_equality_with_preserved_original']
    b=G.load(P+'baseline-records.json')[ID];old_page=(G.ROOT/(P+'baseline-page.md')).read_text(encoding='utf-8-sig')
    start=old_page.index('  - [2014 Pre-Adoption Draft]');end=old_page.index('  - [Appendix A',start)
    old=old_page[start:end]
    url=f['provenance']['former_official_url'];capture=f['provenance']['archived_official_delivery']
    description='The 131-page pre-adoption draft preserves Chapters 1–6, including earlier project and cost estimates, advisory-committee options, policies, and implementation proposals. It contains map placeholders; the separately issued design manual is not included.'
    new='  - [2014 Pre-Adoption Draft — Chapters 1–6]('+b['r2_url']+')\n\n    '+description+' [Archived official City draft]('+capture+')\n\n'
    scope=dict(assessed_at=now(),geographic_institutional_scope='City of Albuquerque bikeways and trails facilities planning, including named local infrastructure and municipal implementation.',specific_albuquerque_connection='The official City draft evaluates Albuquerque streets and trails, identifies corridor gaps and local projects/costs, and proposes City committee, funding and implementation responsibilities.',abqinfo_public_information_value='Residents can compare concrete policy and investment proposals before adoption against the 2015 final and trace the development of Albuquerque bicycle/trail infrastructure decisions.',general_context_exclusion_test='Admission rests on specific Albuquerque network/project tables and locally applied municipal policy choices. Generic cycling benefits and peer-community examples alone would not qualify; those examples have value only within the City committee options analysis.',final_scope_decision='passes_both_gates',substantive_rationale='The long City draft materially records the public-policy development preceding the adopted facilities plan. Earlier roadway treatments, named critical-link proposals, planning-level costs, advisory structure alternatives and implementation actions provide meaningful Albuquerque infrastructure information absent or revised in the final.')
    q=dict(document_function='Official pre-adoption Chapters 1–6 draft documenting development of Albuquerque bikeway and trail network policy and infrastructure priorities.',substantive_content='Dense planning framework, existing-network analysis, gap treatment, named project and cost tables, program recommendations, advisory-committee options and a multi-page implementation matrix.',durable_public_usefulness='Readers can examine consequential earlier Albuquerque policy, project estimates and governance proposals alongside the later adopted plan rather than losing the history of changed recommendations.',information_density='All 131 PDF pages and 57,426 extracted words reviewed; 125 chapter-body pages include substantial narrative, diagrams and detailed tables. Five map placeholders and absent separately issued design manual are disclosed.',unique_information='Complete comparison against all 312 final pages establishes earlier advisory case studies and staffing choices, an arterial shared-roadway treatment section, revised critical-link segments and cost quantities, and changed implementation wording.',rationale='Retain this distinct official historical version as a subordinate link beneath the 2015 final. It has substantive City-specific material, not an administrative fragment, and exposes the earlier choices and estimates that changed before adoption. Combining drafts and finals would obscure their stages. Its map placeholders and absent design manual limit completeness but do not remove the dense unique historical value.',reviewed_document_content=True,visual_inspection_completed=True,page_count=131,extracted_word_count=57426,standalone_public_value='substantive',publication_form='grouped_component',series_relationship='component',aggregation_decision=dict(form='grouped_component',rationale='Keep this substantial earlier policy/network/implementation version subordinate to the final under Previous Bike Plans. Do not consolidate draft and adopted wording into one synthetic original or duplicate the final as another primary plan.',evidence=[P+'comparison.json',P+'research-findings.json']),currentness_review_required=True,currentness_review=dict(status='historical_superseded',authoritative_sources=[P+'retrievals.json',P+'research-findings.json',P+'comparison.json'],finding='This 2014 Chapters 1–6 delivery predates the City EPC recommendation and Council adoption. The 2015 final cover, resolution and clerk memorandum establish the later adopted edition; that comparator remains unchanged.',publication_qualification='Explicit 2014 pre-adoption historical Chapters 1–6 label below the 2015 final; disclose map placeholders and absent separate design manual. Do not present as current, adopted or complete seven-chapter plan.'))
    pq=dict(decision='passes',finding_id=TASK+':historical-draft',assessment=q,evidence=[P+'comparison.json',P+'research-findings.json',P+'retrievals.json',P+'historical-evidence.json'])
    from PublicationQuality import prior_findings,finding_id,require_quality_transition
    if ID in prior_findings():pq['supersedes_findings']=[dict(finding_id=finding_id(ID),new_evidence_rationale='Exact original City delivery and complete actual-file version comparison now establish substantial unique historical Albuquerque policy information with explicit draft omissions.',new_evidence=pq['evidence'])]
    G.write_once(P+'scope-assessment.json',scope)
    G.write_once(P+'quality-decision.json',dict(artifact_type='exact_draft_scope_quality_and_presentation_decision',candidate_id=ID,read_only_comparator_id=COMPARATOR,decision='Retain separate subordinate historical draft link; source hold resolved; validated existing-publication lifecycle.',scope_assessment=scope,quality_assessment=q,publication_quality_decision=pq,old_entry=old,new_entry=new,existing_placement_correct=True,prior_description_design_material_claim_inaccurate=True,owner_review_required=True,merge_authorized=False))
    event('quality_assessment','Actual 131-page draft passes both mission-scope gates and substantial unique historical publication value. Retain as grouped historical version below unchanged final; correct only chapter coverage, omitted design manual/maps and official source citation.',P+'quality-decision.json')
    refresh();G.active_check('mutation','governance_implementation',[ID])
    registry=G.load(G.REGISTRY);proposals={};replacements=[]
    exception=' Explicit current owner exception solely for src-a614f077ace20401: the exact 131-page2014 Chapters1-6 City delivery is recovered from the20170125013542 Internet Archive capture with identical full4402773bytes/SHA256. Complete131/312-page comparison and visual review satisfy the preserved factual prerequisites and establish unique earlier Albuquerque policy/project/cost/committee/implementation information. Restore validated existing-publication lifecycle with positive actual-file scope/quality; retain a subordinate historical draft link under Previous Bike Plans, precisely describing its Chapters1-6 coverage, map placeholders and absent separate design manual, plus archived official source. Prepare one unmerged owner-review correction PR and verified nonproduction preview. Preserve all earlier evidence, every unrelated decision, the read-only2015final row and both original R2 objects. No merge, production action or new R2 mutation.'
    for n in range(1,5):
        old_id='decision-bikeway-2024-edition-resolution-2026-10-07-exception-'+str(n)+'-pr217-postmerge';prior=next(x for x in registry['entries'] if x['governance_id']==old_id);assert prior['state']=='active'
        new_id='decision-'+TASK+'-exception-'+str(n)
        proposal=dict(existing_governance_id=old_id,current_decision=prior['binding_requirement'],controlling_evidence=copy.deepcopy(prior['controlling_artifacts']),new_evidence=[P+'historical-evidence.json',P+'research-findings.json',P+'comparison.json',P+'retrievals.json',P+'quality-decision.json'],proposed_replacement=prior['binding_requirement']+exception,consequences='Resolve only the exact 2014 draft factual source hold and existing historical-entry accuracy; preserve all former controlling evidence and all other decisions.',authorization_artifact=P+'authority.json',authorized=True)
        proposals[old_id]=proposal
        replacement=copy.deepcopy(prior);replacement.update(governance_id=new_id,title=prior['title']+' with exact 2014 draft source/quality reconciliation',state='active',authority='Explicit current owner exact-draft instruction',decision_date='2026-10-08',effective_date='2026-10-08',binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],supersedes=[old_id],implementation_status='Evidence-backed exact draft reconciliation; presentation correction remains owner-review-only')
        replacement['controlling_artifacts'].append(dict(path=P+'governance-reconciliation.json',sha256='',binding_pointers=['/']))
        replacement['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in prior.get('settled_decisions',[])]+[dict(question_id=TASK+':draft-source-retention',decision='Exact former City delivery verified; complete actual-file comparison establishes unique historic value, retain separate subordinate historical link with accurately qualified chapter coverage.')]
        prior.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');replacements.append(replacement)
    G.write_once(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals=proposals))
    G.write_once(P+'governance-reconciliation.json',dict(artifact_type='exact_draft_source_and_existing_publication_reconciliation',mutable_candidate_ids=[ID],read_only_comparator_ids=[COMPARATOR],explicit_scoped_replacements=proposals,provenance_conclusion=f['provenance'],quality_decision='retain historical grouped component',lifecycle='validated',visitor_visible_change='Only 2014 draft entry label, description and archived official-source citation; unchanged archive target and placement.',owner_review_required=True,content_merge_authorized=False,r2_delta=0,historical_evidence_preserved=True))
    for x in replacements:x['controlling_artifacts'][-1]['sha256']=G.file_hash(P+'governance-reconciliation.json')
    registry['entries']+=replacements;save(G.REGISTRY,registry)
    bind(P+'supersession.json','authorization-'+TASK+'-supersession','Current explicit owner exact-draft resolution authority approves only the four recorded source/retention prerequisite exceptions for src-a614f077ace20401; preserve all historical evidence and other authority.')
    bind(P+'governance-reconciliation.json','decision-'+TASK,'Resolve exact draft factual source hold with verified former City bytes and complete comparison; retain distinct validated historical publication with only the precise owner-review entry correction.')
    bind(P+'quality-decision.json','quality-'+TASK,'Apply actual 131-page draft positive City mission-scope and unique historical grouped-component quality, with accurate pre-adoption chapter/design/map qualification and unmerged owner-review presentation.')
    changes=dict(status='validated',title='2014 Bikeways and Trails Facilities Plan — Pre-Adoption Draft (Chapters 1–6)',date='2014',source_url=url,direct_file_url=url,referring_urls=[G.load(P+'historical-evidence.json')['context_staff_capture'],capture],discovery_path=['City of Albuquerque Planning','2014 EPC proposed Bikeways & Trails Facilities Plan, Chapters1-6',url,capture],scope_assessment=scope,quality_assessment=q,publication_quality_decision=pq,review_reason=None,exclusion_reason=None,provenance_status='Exact former official City Chapters1-6 delivery verified: full Internet Archive20170125013542 original-response PDF matches all4402773bytes and SHA256cf557f83399bea7f5648f772bc49c6586c46918401bfd882c041047bc21ea6bc. Current City URL404; identity is not inferred from R2 or filename.',validation_status='passed',description=description,description_word_count=len(description.split()),processing_notes=b['processing_notes']+['2026-10-08 '+TASK+': verified exact former official BikewaysTrailsFacilityPlan.pdf delivery via full archived City GET and contemporaneous EPC source context. Cover2014; August4 PDF packaging metadata is not a precise issue/adoption date. All131/312pages compared and visually inspected. Earlier committee options, project/cost tables and policy/implementation wording provide unique historical value. Restore validated existing-publication lifecycle; correct only draft entry chapter/design/map qualification and source link in an unmerged owner-review PR. 2015final row and both R2 originals unchanged.'])
    require_quality_transition(b,dict(b,**changes))
    save(P+'record-updates.json',dict(approved_updates=[dict(id=ID,changes=changes)]))
    event('governance_implementation','Four explicit exact-draft exceptions preserve all original authority and evidence while resolving the now-satisfied source/comparison prerequisites; new actual-file quality and scoped proposal authority registered.',P+'governance-reconciliation.json')
    apply_mutations()

def apply_mutations():
    decision=G.load(P+'quality-decision.json');old=decision['old_entry'];new=decision['new_entry']
    old_page=(G.ROOT/(P+'baseline-page.md')).read_text(encoding='utf-8-sig')
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    refresh();G.active_check('mutation','content_implementation',[ID])
    path=G.ROOT/PAGE;assert path.read_text(encoding='utf-8-sig')==old_page
    path.write_text(old_page.replace(old,new,1),encoding='utf8',newline='\n')
    event('content_implementation','Only the nested historical2014draft entry now identifies Chapters1-6, actual unique proposals, map placeholders, absent separate design manual and the byte-verified archived City source; R2 target and all other entries remain unchanged.',PAGE)
    queue();refresh();guard()

def queue():
    inv=G.load('project-state/master-inventory.json');prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved={r['id'] for r in inv['candidates'] if r['status']=='approved for addition'}
    q.update(artifact_type='bikeway_2014_draft_resolution_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for k in ['gated','source_or_structural_blocked']:
        original=prior[k+'_pending_ids'];q[k+'_pending_ids']=({i:why for i,why in original.items() if i in pending} if isinstance(original,dict) else sorted(i for i in original if i in pending));q[k+'_pending_count']=len(q[k+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated),bikeway_2014_draft_resolution=dict(candidate_id=ID,source_blocker_cleared=1,restored_existing_publication_status='validated',owner_review_entry_correction_required=True))
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,333,321,12,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))

def local_receipt():
    refresh();G.active_check('final');guard()
    inv=G.load('project-state/master-inventory.json');after=next(r for r in inv['candidates'] if r['id']==ID);before=G.load(P+'baseline-records.json')[ID]
    q=G.load(P+'queue.json');h=G.load('project-state/discovery/consolidated-human-review-queue.json');checkpoint=G.load('project-state/checkpoint.json')
    assert after['status']=='validated' and checkpoint['remaining_nonterminal']==884
    save(P+'accounting.json',dict(task_id=TASK,mutable_candidate_ids=[ID],read_only_comparator_ids=[COMPARATOR],before_status=before['status'],after_status=after['status'],before_row_sha256=G.digest(before),after_row_sha256=G.digest(after),queue=dict(approved=q['approved_count'],pending=q['pending_review_count'],governance_gated=q['gated_pending_count'],source_structural_blocked=q['source_or_structural_blocked_pending_count'],actionable=q['ungated_pending_count'],human_review=len(h.get('records',[]))),checkpoint_remaining_nonterminal=checkpoint['remaining_nonterminal'],visitor_visible_change='Only draft label, accurate Chapters1-6 description and archived official source link; historical subordinate placement and preserved R2 target unchanged.',r2_delta=dict(objects=0,bytes=0,uploads=0,overwrites=0,deletions=0),unrelated_rows_unchanged=True,comparator_unchanged=True,historical_evidence_preserved=True))
    current=G.ROOT/'project-state/CURRENT.md';text=current.read_text(encoding='utf-8-sig');links=text[text.index('[Owner correction]'):]
    current.write_text('# Current project state\n\n2014 Bikeways and Trails Facilities Plan draft provenance/quality resolution is prepared for one unmerged owner-review PR. src-a614f077ace20401 is restored from pending factual review to validated historical publication: the former official City Chapters 1–6 delivery matches all 4,402,773 preserved bytes and SHA-256 through its January 25, 2017 Internet Archive capture. Cover2014; August4 PDF metadata is packaging, not an asserted issue/adoption date.\n\nComplete131/312-page comparison and visual review establish unique earlier committee, project/cost and policy/implementation information. Only the subordinate Previous Bike Plans draft label/description and archived City source link change, explicitly disclosing map placeholders and the absent separate design manual. The 2015 final comparator, both R2 originals and unrelated records remain unchanged. Full validation and verified nonproduction preview/PR are pending. Do not merge.\n\nQueue: 0 approved / 333 pending (321 gated / 12 source-structural blocked), 0 actionable / human review; remaining nonterminal884. R2 delta0. Main/planning baseline7bf604d5.\n\n[Receipt](governance/'+TASK+'/receipt.json) · [Research](governance/'+TASK+'/research-findings.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links,encoding='utf8',newline='\n')
    event('inventory_disposition','Only exact draft restored to validated historical existing-publication lifecycle; deterministic queue333/321/12, checkpoint884 and zero human review; comparator, other records and R2 unchanged.',P+'accounting.json')
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);evidence=[P+n for n in ['comparison.json','historical-evidence.json','research-findings.json','quality-decision.json','governance-reconciliation.json','record-updates.json','accounting.json','queue.json','retrievals.json']]
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,mutable_candidate_ids=[ID],read_only_comparator_ids=[COMPARATOR],status='source_quality_lifecycle_resolved_visible_correction_owner_review_pending',normal_validation='pending',owner_review_required=True,content_merge_authorized=False,accounting=G.load(P+'accounting.json'),evidence_sha256={p:G.file_hash(p) for p in evidence},governance_accounting={row['governance_id']:dict(requirement=row['binding_requirement'],implementation='Exact byte-recovered official City draft, all443-page comparison and visual review meet actual source and quality prerequisites. Four explicit exact-draft exceptions preserve all old authority/evidence. Only draft lifecycle and single historical-entry accuracy change; 2015 comparator, other rows/sections, current2024plan and R2 remain unchanged. Owner-review PR/preview only; no merge or production action.',evidence=evidence) for row in c['resolved_rules']}))
    save(P+'progress.json',dict(state='local_exact_draft_reconciliation_complete',remaining=['Full normal validation','One unmerged owner-review PR and verified nonproduction preview','Final remote refs'],r2_delta=0))
    refresh();G.active_check('final');guard()

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
