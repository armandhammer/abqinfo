"""Four-record agenda reconciliation; background-only, original history preserved."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
import TaskGovernance as G
from SourceHoldResolution import audit

TASK='remaining-agenda-resolution-2026-10-07'
BASE='67e2b9eed7d39d3e8b9ac556cf142a03c0b3c817'
P='project-state/governance/'+TASK+'/'
IDS=['src-7e7af2af147d96d7','src-dc3a192d194d3d65','src-9dbe491dce873f71','generated-dpm-2018']
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value):
    p=G.ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def bind(path,gid,requirement,scope):
    r=G.load(G.REGISTRY);assert not any(e['governance_id']==gid for e in r['entries'])
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=scope,
        authority='Explicit current user bounded agenda reconciliation instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',
        controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,
        required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded background reconciliation'))
    save(G.REGISTRY,r)
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    names=['population.json','authority.json','starting-state.json','baseline-records.json','implementation.json','supersession.json','historical-evidence.json','governance-reconciliation.json','meeting-findings.json','pdf-inspection.json','retrievals.json','record-updates.json','generated-manifest.json','queue.json','accounting.json','receipt.json','progress.json','validation.log','rendered-check.json','integration-intent.json','remote-final.json','summary.md','fetch-tasks.json']
    paths=[P+n for n in names]+[P+f'contract-v{i}.json' for i in range(1,31)]+[P+f'response-{i:03d}.bin.gz' for i in range(1,101)]+[P+f'visual-{i:02d}.png' for i in range(1,31)]+[P+f'validation-attempt-{i}.log' for i in range(1,6)]
    paths+=['scripts/project/RemainingAgendaResolution.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    population=dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','consolidation','inventory_disposition','governance_implementation','background_integration'],artifact_paths=paths)
    if (G.ROOT/(P+'population.json')).exists(): assert G.load(P+'population.json')==population
    else: G.write_once(P+'population.json',population)
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id'] in IDS}
    assert set(rows)==set(IDS[:3])
    generated=G.load('project-state/discovery/approved-background-archive-family-14-2026-09-26.json')
    rows[IDS[3]]=next(r for r in generated['records'] if r['id']==IDS[3])
    G.write_once(P+'baseline-records.json',rows)
    q=G.load(G.load('project-state/ordinary-queue-current.json')['artifact'])
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,remote_main=BASE,remote_planning_snapshot=BASE,
        source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],queue_counts={k:q[k] for k in ['approved_count','pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count']},
        r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    save(P+'progress.json',dict(stage='population_frozen_initial_contract_saved',inventory_mutation=False))
def refresh():
    r=G.load(G.REGISTRY)
    for e in r['entries']:
        if e['state']=='active':
            for a in e['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r);r=G.registry();registered={a['path'] for e in r['entries'] for a in e['controlling_artifacts']}
    paths=[p for p in G.changed_paths(BASE) if p not in registered and p not in [G.REGISTRY,r['audit_artifact'],P+'implementation.json'] and not p.startswith('backups/')]
    audit(paths)
    versions=list((G.ROOT/P).glob('contract-v*.json'));n=max(int(p.stem.split('-v')[1]) for p in versions)+1
    path=P+f'contract-v{n}.json'
    population_path=P+'population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else P+'population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population_path,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=G.load(P+'population.json')['operation_classes'],events=[],status='review_in_progress')
    subjects={}
    for e in c['resolved_rules']:
        for f in e.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules',len(c['unresolved_gates']),'gates')
def event(operation,summary,evidence,action='implements'):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=operation,candidate_ids=IDS,governance_ids=p['respected_governance_ids'],action=action,summary=summary,evidence=evidence,use_contract_record_rules=True));save(P+'implementation.json',p)
def findings():
    G.active_check('review','quality_assessment')
    retrievals=G.load(P+'retrievals.json')['records'];sources={r['label']:r for r in retrievals}
    inspections=G.load(P+'pdf-inspection.json')
    for r in inspections:
        r.update(inspection_completed=True,visual_inspection_completed=True,
            visual_finding='Every rendered page inspected. Agenda originals contain proposed business/notice text only; 2018 minutes contain roll call and decisions; adopted ABCWUA record contains substantive marked standards and a dimensional table.')
    save(P+'pdf-inspection.json',inspections)
    ins={r['id']:r for r in inspections}
    dates=['2018-03-21','2026-05-04','2026-04-16']
    titles=['DPM Executive Committee Agenda, March 21, 2018','DPM Executive Committee Agenda, May 4, 2026','Local Government Coordinating Commission Agenda, April 16, 2026']
    occurrence=[
        'Apparently not held: the refreshed April 4 agenda repeats both March 21 action items verbatim and still seeks approval of March 7 minutes. March 7 minutes only schedule March 21. Complete official 2018 family still consists of three agendas and three minutes ending March 7; no March 21 minutes, roll call, actions, cancellation or no-quorum instrument located. This supports nonoccurrence as an inference, not a proved formal cancellation.',
        'Occurrence supported by explicit City retrospective attribution: the official Amendments to the DPM page labels the linked Article 4-3 ABCWUA combined record as changes approved by this committee on May 4, 2026. The original includes the plot-style/scales and three-utility street standard outcomes. This establishes an official dated action; no original roll call or approved meeting minutes located in the official index/directory/search.',
        'Official County April 16 meeting entry confirms the scheduled 5 PM APS location and supplies an agenda/163-page packet. The later August 20 official agenda specifically schedules approval of April 16 LGCC minutes, corroborating an April meeting/minutes record. Neither the April entry nor the August entry supplies completed minutes/approval; the August nine-page packet omits the referenced April minutes. No April recording, actual roll call, cancellation or no-quorum proof located through reviewed City/County/APS routes. Occurrence is retrospectively corroborated, not independently proved by a completed meeting record.'
    ]
    substance=[
        'One page identifies two proposed items (field-change construction language and turn-lane/median design) without the proposed language, engineering design, deliberation or outcome. Its business list is repeated on April 4. No independent substantive value and no distinct historical meeting record established.',
        'Two pages identify four ABCWUA proposals and link out to the amendments page. They omit the actual revised language, dimensional table, rationale, vote and outcome. The substantive approved record is already preserved as src-d6f0d94a12b31a2d. Proposal identification and meeting logistics add no independent publication-worthy policy/infrastructure content.',
        'Three pages list members, opioid-funding/library/housing/behavioral-health presentation topics and speakers, then public-comment/accessibility instructions. They contain no underlying reports, allocations, resolutions, findings or decisions. The separately linked 163-page County packet carries supporting material; it is a distinct evidence object, not incorporated content of this three-page source and not admitted as a new candidate.'
    ]
    rows=[];updates=[];before=G.load(P+'baseline-records.json')
    for n,i in enumerate(IDS[:3]):
        rationale='Specific material Albuquerque institutional connection passes the first gate. '+substance[n]+' The actual original fails the independent substantive public-information and publication-quality gates. Missing minutes or official status do not cure this failure; no limited-content exception or owner-borderline referral is warranted.'
        scope=dict(assessed_at=now(),geographic_institutional_scope='City of Albuquerque DPM Executive Committee' if n<2 else 'Joint Albuquerque, Bernalillo County and APS Local Government Coordinating Commission',
            specific_albuquerque_connection='Exact dated agenda of the Albuquerque development standards committee.' if n<2 else 'Exact dated joint City/County/APS agenda at an Albuquerque meeting location addressing local programs.',
            abqinfo_public_information_value=substance[n],general_context_exclusion_test='A specific Albuquerque body and relevant topic names are insufficient without actual policy, spending, infrastructure or decision content; external subject-matter files cannot confer substance on this notice.',
            final_scope_decision='excluded_insufficient_public_information_value',substantive_rationale=rationale)
        quality=dict(reviewed_document_content=True,visual_inspection_completed=True,page_count=ins[i]['pages'],extracted_word_count=ins[i]['words'],
            standalone_public_value='low',information_density='limited proposed business and meeting logistics; no incorporated substantive report or decision',
            series_relationship='serial',publication_form='excluded',rationale=rationale,
            aggregation_rationale='March 21 adds a repeated proposed-business notice to the established 2018 family and is removed from the dependent packet; unrelated retained components remain governed. May 4 cannot add substance beyond its adopted record. LGCC reports are separately supplied in a different packet; the selected agenda remains a notice.',
            limited_content_exception='None warranted; no distinct legal instrument, dense map/table or substantive outcome in the original.',evidence=[P+'pdf-inspection.json',P+'retrievals.json'])
        row=dict(id=i,date=dates[n],title=titles[n],meeting_occurrence=occurrence[n],
            occurrence_state=['apparently_not_held_inference','official_dated_adoption_supports_occurrence','subsequent_minutes_reference_corroborates_occurrence'][n],
            approved_minutes_conclusion='No approved minutes original located; this is not a claim that minutes do not exist. '+('No missing-minutes retention representation is allowed because the record supports apparent nonoccurrence.' if n==0 else 'No qualification/retention exception invoked; independent negative substance decision controls.'),
            substantive_value=substance[n],scope_assessment=scope,quality_assessment=quality,final_disposition='excluded',owner_decision_required=False,qualified_missing_minutes_retention=False)
        rows.append(row)
        updates.append(dict(id=i,changes=dict(status='excluded',title=titles[n],date=dates[n],size_bytes=ins[i]['size_bytes'],checksum_sha256=ins[i]['sha256'],review_reason=None,
            exclusion_reason=rationale,scope_assessment=scope,quality_assessment=quality,
            publication_quality_decision=dict(decision='excluded',finding_id=TASK+':'+i,rationale=rationale,evidence=[P+'meeting-findings.json']),
            validation_status='Governed complete-original agenda exclusion; occurrence/minutes limits and explicit DPM component reconciliation preserved in '+P+'meeting-findings.json',
            processing_notes=before[i]['processing_notes']+['2026-10-07 '+TASK+': '+occurrence[n]+' '+substance[n]+' Conclusive independent substance/quality exclusion. Historical originals/evidence preserved; no archival or visitor-visible action.'])))
    save(P+'meeting-findings.json',dict(artifact_type='agenda_factual_and_quality_decision',records=rows,
        evidence_only_related_records=['src-d6f0d94a12b31a2d','lgcc-county-agenda-packet','lgcc-august-packet-april-minutes-check'],
        research_limits=['September 13 Internet Archive review is preserved historical research, not freshly repeated; no unsupported declaration of formal cancellation.','APS board page returned 403; streams and linked August video HTML did not establish an April recording/approval.','Separate LGCC packets are evidence only; their publication eligibility has not been reviewed or authorized.']))
    save(P+'record-updates.json',dict(approved_updates=updates))
    manifest_path='project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json'
    packet=copy.deepcopy(next(p for p in G.load(manifest_path)['annual_packets'] if p['year']==2018))
    removed=[p for p in packet['components'] if p['source_master_id']==IDS[0]]
    packet['components']=[p for p in packet['components'] if p['source_master_id']!=IDS[0]]
    assert len(packet['components'])==5 and len(removed)==1
    for p in packet['components']:
        source=sources[p['source_master_id']];p.update(size_bytes=source['size_bytes'],sha256=source['sha256'],source_page_count=source['page_count'],source_evidence=source['response_artifact'])
    for k in ['resulting_page_count','resulting_size_bytes','resulting_sha256','local_output_path','generated_at']:packet.pop(k,None)
    packet.update(component_count=5,total_original_pages=8,generated_id=IDS[3],status='composition_reconciled_local_manifest_only_not_archived',
        excluded_components=[dict(source_master_id=IDS[0],reason=occurrence[0],inclusion='exclude',missing_minutes_label_authorized=False)],
        old_package_metadata=before[IDS[3]],old_package_usable=False,corrected_pdf_generated=False,
        factual_composition_blocker_cleared=True,archival_authorized=False,publication_authorized=False,
        remaining_archival_prerequisites=['Rebuild a distinct local PDF under future bounded preparation authority; do not reuse stale six-component bytes/hash.','Verify exact component equivalence, contents/provenance and complete rendering of the rebuilt PDF.','Obtain explicit bounded R2 authority before any upload; verify absent key/no overwrite and full public bytes.'],
        existing_public_canonical_2018_compilation='src-cd13f7f4ba7ebf30 remains unchanged; its settled four-component historical master is not this never-archived generated packet.',
        composition_rationale='Remove only the March 21 component under current explicit reconciliation authority. Preserve all five other components of the active September 17 packet, including March 7 agenda, without reopening their inclusion. The September 13 proposed/implemented four-original master and its current public file are distinct and unchanged.')
    save(P+'generated-manifest.json',dict(artifact_type='corrected_generated_package_manifest',source_manifest=manifest_path,source_manifest_sha256=G.file_hash(manifest_path),packet=packet))
    event('quality_assessment','All six selected agenda pages and ten DPM family/adopted-record pages rendered and inspected; negative independent substance decisions recorded with factual limits.',P+'meeting-findings.json')
    event('family_review','Complete current DPM family, dated adopted amendment and official LGCC April/August records/packets reviewed. Separate supporting packets remain evidence only.',P+'retrievals.json')
    save(P+'progress.json',dict(stage='findings_saved_governance_reconciliation_pending',inventory_mutation=False))
def reconcile():
    refresh();G.active_check('mutation','governance_implementation',IDS)
    r=G.load(G.REGISTRY);old_id='decision-dpm-executive-committee-consolidation-manifest-2026-09-17-42aab495'
    old=next(e for e in r['entries'] if e['governance_id']==old_id);assert old['state']=='active'
    new_id='decision-dpm-executive-committee-manifest-march21-reconciliation-2026-10-07'
    proposal=dict(existing_governance_id=old_id,current_decision=old['binding_requirement'],
        controlling_evidence=copy.deepcopy(old['controlling_artifacts']),
        new_evidence=[P+'meeting-findings.json',P+'retrievals.json',P+'historical-evidence.json'],
        proposed_replacement='Preserve the exact September 17 packet architecture and every unrelated component decision, except exclude March 21 2018 from generated-dpm-2018 as apparently not held; do not label it approved minutes not located or an orphan meeting. Corrected dependent packet has five components, eight original pages. Preserve September 13 research and September 17 original manifest unchanged. Existing published four-original 2018 master remains unchanged.',
        consequences='Three exact source agendas excluded independently for insufficient substance; March 21 factual composition conflict cleared. Dependent generated manifest corrected locally; stale six-component bytes/hash forbidden for archival. No new archive/publication authority, no visitor-visible/R2 delta or unrelated record change.',
        authorization_artifact=P+'authority.json',authorized=True)
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals={old_id:proposal}))
    save(P+'governance-reconciliation.json',dict(artifact_type='bounded_governance_reconciliation',
        historical_research_classification='September 13 aggregate is historical evidence only/non-binding; factual conclusions evaluated using refreshed authoritative originals, not adopted because older.',
        prior_manifest_classification='September 17 manifest is registered active publication architecture; its March 21 agenda inclusion requires explicit authorized replacement, not a chronology override.',
        reconciliation=proposal,conditional_agenda_holds='September 11/26 holds required factual review before any retention/archive label. Current review conclusively fails the independent substance gate; uncertainty is preserved without attempting retention or invoking a minutes exception.',
        other_active_dpm_architecture='Annual master, years 2014-2018, exact originals/provenance and agenda-not-meeting-proof constraints remain implemented. Existing four-component published 2018 master is a distinct record and stays unchanged. Five remaining September 17 generated-packet components stay included.',
        owner_decision_required=False))
    replacement=copy.deepcopy(old)
    replacement.update(governance_id=new_id,title='DPM packet architecture with explicit March 21 2018 factual correction',state='active',
        authority='Explicit current user reconciliation authority plus refreshed City originals',decision_date='2026-10-07',effective_date='2026-10-07',
        controlling_artifacts=copy.deepcopy(old['controlling_artifacts'])+[dict(path=P+'governance-reconciliation.json',sha256=G.file_hash(P+'governance-reconciliation.json'),binding_pointers=['/']),dict(path=P+'generated-manifest.json',sha256=G.file_hash(P+'generated-manifest.json'),binding_pointers=['/'])],
        binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],
        settled_decisions=[dict(question_id='dpm-2018:march21-component',decision='Exclude March 21 agenda; apparent nonoccurrence and repeated business do not support orphan meeting retention. Five other September 17 generated-packet components retained.')],supersedes=[old_id])
    old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json')
    r['entries'].append(replacement)
    for e in r['entries']:
        for a in e['controlling_artifacts']:
            if a['path']==P+'supersession.json':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    bind(P+'meeting-findings.json','decision-'+TASK,'Exclude exactly the three frozen agendas for insufficient substantive public-information/publication value. Preserve their occurrence/minutes factual limits and original provenance/history. March 21 is apparently not held, not an orphan meeting. Use the corrected local dependent manifest; no upload/publication is authorized.',{'candidate_ids':IDS,'task_ids':[TASK]})
    event('governance_implementation','Explicitly supersede only disputed March 21 inclusion through registered current owner authority; preserve all other architecture and historical artifacts.',P+'governance-reconciliation.json')
    refresh();G.active_check('mutation','inventory_disposition',IDS[:3])
def queue():
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'};approved={i for i,r in rows.items() if r['status']=='approved for addition'}
    q.update(artifact_type='remaining_agenda_resolution_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for k in ['gated','source_or_structural_blocked']:
        original=prior[k+'_pending_ids']
        q[k+'_pending_ids']=({i:why for i,why in original.items() if i in pending} if isinstance(original,dict) else sorted(i for i in original if i in pending))
        q[k+'_pending_count']=len(q[k+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated))
    q['remaining_agenda_resolution']=dict(task=TASK,excluded_ids=IDS[:3],cleared_inventory_blockers=3,dependent_generated_composition_conflict_cleared=True)
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,336,321,15,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK));return q
def apply():
    refresh();G.active_check('mutation','inventory_disposition',IDS[:3])
    current={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']};requests=G.load(P+'record-updates.json')['approved_updates']
    if all(current[i]['status']=='excluded' for i in IDS[:3]):
        assert all(all(current[x['id']].get(k)==v for k,v in x['changes'].items()) for x in requests),'Saved state differs'
    else:
        assert all(current[i]['status']=='pending review' for i in IDS[:3])
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    p=G.ROOT/'project-state/master-inventory.json';p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    queue();refresh()
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True)
    refresh();subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    before=G.load(P+'baseline-records.json');after={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    save(P+'accounting.json',dict(task_id=TASK,records=[dict(id=i,before_status=before[i]['status'],after_status=after[i]['status'],before_row_sha256=G.digest(before[i]),after_row_sha256=G.digest(after[i])) for i in IDS[:3]],
        dependent_generated_record=dict(id=IDS[3],in_master_inventory=False,composition_conflict_cleared=True,component_count=5,status='local_manifest_only_not_archived'),
        queue=dict(approved=0,pending=336,governance_gated=321,source_structural_blocked=15,actionable=0,human_review=0),
        genuine_owner_decisions=0,r2_delta=dict(objects=0,bytes=0,uploads=0,overwrites=0,deletions=0),visitor_visible_delta=0))
    event('inventory_disposition','Apply exactly three conclusive exclusions and regenerate accounting; dependent generated record is outside inventory and updated through new local manifest only.',P+'accounting.json')
    event('consolidation','Corrected five-component manifest preserves all other September 17 components and supersedes disputed March 21 inclusion; no new PDF generated or archive/publication action.',P+'generated-manifest.json')
    save(P+'progress.json',dict(stage='three_dispositions_and_generated_manifest_saved_validation_pending',completed=IDS,remaining=['validation','authorized_background_integration']))
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8');links=old[old.index('[Owner correction]'):]
    text='# Current project state\n\nThree remaining DPM/LGCC agendas conclusively excluded for insufficient actual-record substance. March 21 2018 DPM apparently not held (inference, no formal cancellation proof); explicit scoped registry supersession reconciles September 13 research and September 17 inclusion. May 4 2026 DPM occurrence supported by dated official adopted amendment, approved minutes not located. April 16 LGCC occurrence/minutes record corroborated by August 20 agenda; approved minutes/approval not located, separate County supporting packet preserved as evidence only. Corrected generated-dpm-2018 local manifest has five components/eight original pages; composition conflict cleared, stale six-component bytes unusable, no rebuilt PDF or archival/publication authority. Existing public four-original master unchanged.\n\nQueue: 0 approved / 336 pending (321 governance-gated / 15 source-structural blocked), 0 actionable / 0 human review. No active publication or genuine owner decision. Zero R2/visitor-visible delta. Full validation and authorized background main/planning synchronization pending; no unrelated population begun.\n\n[Agenda findings](governance/'+TASK+'/meeting-findings.json) \u00b7 [Reconciliation](governance/'+TASK+'/governance-reconciliation.json) \u00b7 [Generated manifest](governance/'+TASK+'/generated-manifest.json) \u00b7 [Active task](governance/active-task.json) \u00b7 [Queue](ordinary-queue-current.json).\n\n'+links
    current.write_text(text,encoding='utf-8',newline='\n');refresh();guard()
def receipt():
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    evidence=[P+n for n in ['meeting-findings.json','governance-reconciliation.json','generated-manifest.json','historical-evidence.json','pdf-inspection.json','retrievals.json','record-updates.json','accounting.json','queue.json']]
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,status='review_and_inventory_complete_validation_pending',
        accounting=G.load(P+'accounting.json'),normal_validation='pending',owner_decision_required=False,visitor_visible_delta=0,r2_delta=0,
        evidence_sha256={p:G.file_hash(p) for p in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],
            implementation='Exact four-record bounded review implemented under complete active contract. Three negative scope/quality dispositions do not authorize eligible archive/publication states. Original source fields, historical evidence, unrelated component/annual decisions, currentness/storage limits and owner/publication gates preserved. March 21 explicit registered scope supersession and five-component local manifest implement the authorized factual correction. No campaign, Trails review or unrelated population begun.',evidence=evidence) for r in c['resolved_rules']}))
    refresh();G.active_check('final');guard()
def render():
    from playwright.sync_api import sync_playwright
    from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
    from functools import partial
    import threading
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(G.ROOT/'tmp/site-build')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]
    routes=['development-land-use/development-process','transportation/design-references']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        n=16
        for route in routes:
            for label,width,height in [('desktop',1440,1100),('mobile',390,844)]:
                page=browser.new_page(viewport=dict(width=width,height=height))
                page.goto('http://127.0.0.1:%s/%s/'%(server.server_port,route),wait_until='networkidle')
                body=page.locator('body').inner_text()
                assert 'Development Process Manual' in body and '2018' in body
                public_2018='https://files.abqinfo.com/development-land-use/development-process/cabq-dpm-executive-committee-records-2018-abqinfo-compilation.pdf'
                assert page.locator('a[href="'+public_2018+'"]').count()==1
                for i in IDS[:3]:
                    assert page.locator('a[href="'+G.load(P+'baseline-records.json')[i]['direct_file_url']+'"]').count()==0
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                n+=1;path=P+f'visual-{n:02d}.png';page.screenshot(path=str(G.ROOT/path),full_page=True)
                results.append(dict(route=route,viewport=label,width=width,height=height,screenshot=path,body_text_sha256=hashlib.sha256(body.encode()).hexdigest(),no_horizontal_overflow=True))
                page.close()
        browser.close()
    server.shutdown();server.server_close()
    save(P+'rendered-check.json',dict(browser='Google Chrome via Playwright',built_root='tmp/site-build',results=results,visitor_visible_source_tree_unchanged=True))
def guard():
    from WorkflowStageLifecycle import StageSnapshot,git,canonical_bytes
    stage=StageSnapshot(TASK);state=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for path,key in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==state[key],path
    before={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']}
    after={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert before.keys()==after.keys() and {i for i in before if before[i]!=after[i]}<=set(IDS),'Population widened'
    for i in IDS[:3]:
        assert after[i]['processing_notes'][:len(before[i]['processing_notes'])]==before[i]['processing_notes'],'History lost'
        for k in ['r2_key','r2_url','source_url','direct_file_url']:
            assert after[i].get(k)==before[i].get(k),'Original/source/archive field changed: '+k
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    population_path=P+'population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() or stage.end else P+'population.json'
    assert changes<=set(stage.load_json(population_path)['artifact_paths']),changes-set(stage.load_json(population_path)['artifact_paths'])
    historical=['project-state/discovery/claude-consolidation-dpm-2018-2026-09-13.json','project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json']
    for p in historical: assert canonical_bytes(stage.read_bytes(p))==canonical_bytes(git('show',BASE+':'+p)),p
    if (G.ROOT/(P+'generated-manifest.json')).exists() or stage.end:
        m=stage.load_json(P+'generated-manifest.json')['packet']
        original=next(p for p in stage.load_json(historical[1])['annual_packets'] if p['year']==2018)
        assert [p['source_master_id'] for p in m['components']]==[p['source_master_id'] for p in original['components'] if p['source_master_id']!=IDS[0]]
        assert m['component_count']==5 and m['total_original_pages']==8 and m['old_package_usable'] is False
        assert m['corrected_pdf_generated'] is False and m['archival_authorized'] is False and m['publication_authorized'] is False
        assert all(after[i]['status']=='excluded' for i in IDS[:3])
        findings=stage.load_json(P+'meeting-findings.json')['records']
        assert {x['id'] for x in findings}==set(IDS[:3])
        for x in findings:
            assert x['final_disposition']=='excluded' and x['quality_assessment']['visual_inspection_completed'] and x['qualified_missing_minutes_retention'] is False
        q=stage.load_json(P+'queue.json');assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,336,321,15)
    print('Four-record population, historical evidence, zero visible/R2 guard passed')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');globals()[sys.argv[1]]()
