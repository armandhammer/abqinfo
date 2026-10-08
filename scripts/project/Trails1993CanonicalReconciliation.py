"""Bounded canonical provenance repair; existing bytes and visible content unchanged."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from SourceHoldResolution import audit

TASK='trails-1993-canonical-reconciliation-2026-10-07'
BASE='83545b32f9958780d96799aae94ca25fe72bffb6'
P='project-state/governance/'+TASK+'/'
ID='src-395957636cb2fed0'
DUP='src-fee63a8f74f3f110'
SHA='c61bc45648f9fb2ec7e36262e71c61a68babaa6b3fbab37b436ce0603f415b92'
URL='https://files.abqinfo.com/transportation/bicycling/bike-plans/1993-trails-and-bikeways-facility-plan.pdf'
EVIDENCE=['project-state/discovery/'+s for s in ['ordinary-second-large-campaign-family-297-2026-09-26.json','ordinary-second-large-campaign-1993-canonical-correction-2026-09-26.json','bicycle-history-gap-analysis-2026-08-10.json','bicycle-history-benchmarks.json']]
def now():return datetime.now(timezone.utc).isoformat()
def save(path,value):
    p=G.ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    names=['population.json','authority.json','starting-state.json','baseline-records.json','implementation.json','supersession.json','evidence-verification.json','public-byte-verification.json','governance-reconciliation.json','record-updates.json','queue.json','accounting.json','receipt.json','progress.json','rendered-check.json','integration-intent.json','remote-final.json','summary.md','public-original.bin.gz','desktop.png','mobile.png']
    paths=[P+n for n in names]+[P+f'contract-v{i}.json' for i in range(1,41)]+[P+f'validation-attempt-{i}.log' for i in range(1,6)]
    paths+=['scripts/project/Trails1993CanonicalReconciliation.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    pop=dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=[],operation_classes=['document_review','inventory_disposition','governance_implementation','background_integration'],artifact_paths=paths)
    G.write_once(P+'population.json',pop)
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id'] in [ID,DUP]}
    G.write_once(P+'baseline-records.json',dict(canonical=rows[ID],duplicate_evidence_only=rows[DUP]))
    qp=G.load('project-state/ordinary-queue-current.json')['artifact'];q=G.load(qp)
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,remote_main=BASE,remote_planning_snapshot=BASE,source_queue=qp,queue_counts={k:q[k] for k in ['approved_count','pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count']},r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    save(P+'progress.json',dict(stage='exact_canonical_population_frozen_contract_saved',inventory_mutation=False))
def refresh():
    r=G.load(G.REGISTRY)
    for e in r['entries']:
        if e['state']=='active':
            for a in e['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r);r=G.registry();registered={a['path'] for e in r['entries'] for a in e['controlling_artifacts']}
    audit([p for p in G.changed_paths(BASE) if p not in registered and p not in [G.REGISTRY,r['audit_artifact'],P+'implementation.json'] and not p.startswith('backups/')])
    n=max(int(p.stem.split('-v')[1]) for p in (G.ROOT/P).glob('contract-v*.json'))+1;path=P+f'contract-v{n}.json'
    pop_path=next(P+s for s in ['population-v3.json','population-v2.json','population.json'] if (G.ROOT/(P+s)).exists())
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',pop_path,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'];plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',events=[],status='review_in_progress')
    subjects={}
    for e in c['resolved_rules']:
        for f in e.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(actions=G.load(pop_path)['operation_classes'],contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=pop_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules',len(c['unresolved_gates']),'gates')
def event(operation,summary,evidence):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=operation,candidate_ids=[ID],governance_ids=p['respected_governance_ids'],action='implements',summary=summary,evidence=evidence,use_contract_record_rules=True));save(P+'implementation.json',p)
def bind(path,gid,requirement):
    r=G.load(G.REGISTRY)
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope={'candidate_ids':[ID],'task_ids':[TASK]},authority='Explicit current user bounded canonical reconciliation instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded background reconciliation'))
    save(G.REGISTRY,r)
def bootstrap():
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals={}))
    refresh()
    active=G.load(G.ACTIVE_TASK);active.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,active)
    G.active_check('mutation','governance_implementation',[ID])
    save(P+'authority.json',dict(artifact_type='owner_authorization',authority='Explicit current user instruction',candidate_ids=[ID],instruction='Resolve exactly canonical src-395957636cb2fed0 using existing September26 authoritative identity and substantive historical-plan review first. Verify the recorded evidence and fresh full public R2 GET. Reconcile canonical source/provenance/lifecycle and clear the stale protected source prerequisite only if conclusive under resolved governance. This current instruction explicitly authorizes that bounded evidence-driven release and necessary scoped supersession of prior preservation of the stale hold; unrelated decisions and original evidence remain unchanged. Preserve duplicate src-fee63a8f74f3f110 unchanged as evidence only. Preserve July1993 adoption / November1996 map revision, not a current network. No fresh source campaign or quality re-review unless existing evidence or governance requires. No R2 upload/overwrite/deletion, visitor-visible change, new record/entry or unrelated population. Regenerate accounting, full normal/governance/sealed-history/Hugo/rendered/CURRENT/diff validation; if clean integrate background correction into main and synchronize planning-snapshot.'))
    bind(P+'authority.json','owner-'+TASK,'Apply only the current exact canonical provenance/lifecycle reconciliation; conclusive evidence permits bounded release of the stale source prerequisite through explicit registry supersession. No R2 mutation, visible edit, duplicate mutation or unrelated population; clean background main/planning synchronization authorized.')
    bind(P+'supersession.json','authorization-'+TASK+'-supersession','Only the explicit evidence-backed canonical hold replacement recorded in this task is authorized; preserve all unrelated governance and historical artifacts.')
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json')
    assert lifecycle['stages'][-1]['id']=='remaining-agenda-resolution-2026-10-07'
    lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/Trails1993CanonicalReconciliation.py'],exact_delta_guard=dict(module='Trails1993CanonicalReconciliation',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf-8-sig');i=s.index('Set-StrictMode')
    s=s[:i]+'& python "$PSScriptRoot/Trails1993CanonicalReconciliation.py" guard\nif ($LASTEXITCODE -ne 0) { throw "1993 canonical reconciliation regression failed" }\n\n'+s[i:]
    runner.write_text(s,encoding='utf-8',newline='\n');refresh();G.active_check('review','document_review',[ID])
def evidence():
    refresh();G.active_check('review','document_review',[ID])
    checks={}
    for path in EVIDENCE:
        raw=(G.ROOT/path).read_bytes();old=subprocess.check_output(['git','show',BASE+':'+path],cwd=G.ROOT)
        assert raw.replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n')
        checks[path]=dict(normalized_sha256=G.file_hash(path),unchanged_since_baseline=True)
    f=G.load(EVIDENCE[0])['records'][0];qa=f['fresh_source_qa'];correction=G.load(EVIDENCE[1])
    for obj in [qa,qa['source_GET'],f['saved_evidence'],f['existing_canonical_public_verification'],correction['canonical_public_verification'],correction['decisions'][0]]:
        assert obj['size_bytes']==4624017 and obj['checksum_sha256']==SHA
    assert qa['source_exact_verified'] and qa['page_count']==85 and qa['rendered_pages']==85 and f['review_complete']
    assert qa['source_GET']['requested_url']=='https://www.cabq.gov/planning/documents/trailbky.pdf'
    assert f['canonical_candidate_id']==ID and correction['decisions'][0]['canonical_id']==ID
    assert f['existing_canonical_public_verification']['public_url']==URL and f['existing_canonical_public_verification']['byte_identical']
    b=G.load(P+'baseline-records.json');dup=b['duplicate_evidence_only'];assert dup['status']=='duplicate' and dup['checksum_sha256']==SHA
    local=G.ROOT/qa['staged_path'];raw=local.read_bytes();assert len(raw)==4624017 and hashlib.sha256(raw).hexdigest()==SHA
    save(P+'evidence-verification.json',dict(artifact_type='canonical_identity_evidence_verification',candidate_id=ID,duplicate_evidence_only=DUP,evidence_files=checks,authoritative_source_url=qa['source_GET']['requested_url'],authoritative_record_url=f['saved_evidence']['authoritative_url'],authoritative_source_GET=qa['source_GET'],retained_local_original=dict(path=qa['staged_path'],size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),page_count=85,visual_review_reused_from=EVIDENCE[0],quality_review_reused=True,fresh_quality_review=False,scope_assessment=f['mission_scope_assessment'],quality_assessment=f['quality_assessment'],historical_qualification='Adopted July 1993; map revised November 1996. Historical predecessor, not a current-network plan.',older_benchmark_conclusion='August lineage/benchmark recovery established existence and succession, explicitly not exact archived-file identity. September26 exact official original and full public GET supply that missing identity; benchmark artifacts remain unchanged.',conclusive=True))
    event('document_review','Verify intact September26 official-source/full-GET identity and existing substantive scope/visual review; no new source campaign or fresh quality review required.',P+'evidence-verification.json')
def verify():
    G.active_check('review','document_review',[ID])
    e=G.load(P+'evidence-verification.json')
    r=subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-Command',"& ./scripts/project/Test-R2PublicObject.ps1 -SourcePath '"+e['retained_local_original']['path']+"' -PublicUrl '"+URL+"' | ConvertTo-Json -Depth 10"],check=True,capture_output=True,text=True)
    public=json.loads(r.stdout);assert public['size_bytes']==4624017 and public['checksum_sha256']==SHA and public['byte_identical']
    save(P+'public-byte-verification.json',dict(artifact_type='fresh_full_public_byte_verification',candidate_id=ID,verifier='scripts/project/Test-R2PublicObject.ps1',method='Fresh full public GET compared by size and SHA256 with the retained September26 unchanged authoritative original; no HEAD-only identity claim.',source_path=e['retained_local_original']['path'],source_url=e['authoritative_source_url'],public_verification=public,r2_write_operations=0))
    event('document_review','Fresh complete public R2 GET matches retained official original: 4624017 bytes and c61bc45648f9fb2ec7e36262e71c61a68babaa6b3fbab37b436ce0603f415b92.',P+'public-byte-verification.json')
    save(P+'progress.json',dict(stage='durable_identity_and_fresh_public_bytes_verified',inventory_mutation=False,remaining=['explicit_scoped_governance_replacement','canonical_inventory_reconciliation','validation','background_integration']))
def reconcile():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    e=G.load(P+'evidence-verification.json');public=G.load(P+'public-byte-verification.json');assert e['conclusive'] and public['public_verification']['byte_identical']
    r=G.load(G.REGISTRY);old_ids=['decision-decisions-2c491c71-remaining-thirteen-exception','decision-decisions-b8452592-five-review-exception-2026-10-03-two-county-correction-remaining-thirteen-exception','decision-inventory-overrides-09e22b5f','decision-next-ordinary-queue-b8bb5c70-five-review-exception-2026-10-03-two-county-correction-remaining-thirteen-exception','decision-ordinary-second-large-campaign-1993-canonical-correction-2026-09--27d3a38c']
    proposals={};replacements=[]
    exception=' Explicit current owner exception solely for src-395957636cb2fed0: the preserved source/structural prerequisite is conclusively satisfied by the unchanged September26 official trailbky.pdf original and fresh exact public GET. Reconcile authoritative source/identity/hash and restore validated existing-publication lifecycle under this task; retain July1993 adoption/November1996 map revision. Preserve every unrelated decision and all historical evidence, and leave duplicate src-fee63a8f74f3f110 unchanged. No new R2 or visible publication action.'
    for n,old_id in enumerate(old_ids,1):
        old=next(x for x in r['entries'] if x['governance_id']==old_id);assert old['state']=='active'
        new_id='decision-'+TASK+'-exception-'+str(n)
        proposal=dict(existing_governance_id=old_id,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=[P+'evidence-verification.json',P+'public-byte-verification.json'],proposed_replacement=old['binding_requirement']+exception,consequences='Only canonical stale provenance/hold and lifecycle fields may change. Earlier override/reassessment/queue/canonical-preservation documents remain intact. All other scoped decisions, duplicate terminal relationship, original bytes, public entry and R2 object remain unchanged.',authorization_artifact=P+'authority.json',authorized=True)
        proposals[old_id]=proposal
        replacement=copy.deepcopy(old);replacement.update(governance_id=new_id,title=old['title']+' with exact 1993 canonical prerequisite reconciliation',state='active',authority='Explicit current user bounded canonical reconciliation authority',decision_date='2026-10-07',effective_date='2026-10-07',binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],supersedes=[old_id],implementation_status='Exact canonical prerequisite satisfied; unrelated dispositions preserved')
        replacement['controlling_artifacts'].append(dict(path=P+'governance-reconciliation.json',sha256='',binding_pointers=['/']))
        replacement['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in old.get('settled_decisions',[])]+[dict(question_id=TASK+':canonical-identity',decision='Exact authoritative identity reconciled; stale source prerequisite cleared, duplicate and existing public bytes unchanged.')]
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');replacements.append(replacement)
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals=proposals))
    save(P+'governance-reconciliation.json',dict(artifact_type='bounded_canonical_provenance_decision',candidate_id=ID,conclusive=True,explicit_scoped_replacements=proposals,provenance_conclusion='City trailbky.pdf adopted July1993/map revised November1996 is byte-identical to the protected canonical R2 original. The 2024 update summary is historical lineage evidence only, not this file identity.',quality_conclusion='Reuse the recorded actual-original September26 historical-plan substantive/visual review and positive mission scope. Normalize its fields for current eligible lifecycle validation; no new quality research or change in publication composition.',final_lifecycle_status='validated',canonical_blocker_cleared=True,duplicate_candidate_id=DUP,duplicate_inventory_unchanged=True,owner_decision_required=False,historical_evidence_unchanged=True,visitor_visible_delta=0,r2_delta=0))
    for x in replacements:
        x['controlling_artifacts'][-1]['sha256']=G.file_hash(P+'governance-reconciliation.json')
    r['entries']+=replacements
    for x in r['entries']:
        for a in x['controlling_artifacts']:
            if a['path']==P+'supersession.json':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    bind(P+'governance-reconciliation.json','decision-'+TASK,'Implement the conclusive exact canonical provenance correction and validated existing-publication lifecycle. Reuse historical review; preserve duplicate, historical qualification, prior evidence, public entry and existing R2 bytes. No owner decision remains.')
    b=G.load(P+'baseline-records.json')['canonical'];oldq=e['quality_assessment']
    rationale=oldq['substantive_rationale']+' This is the same complete 85-page original already published under Previous Bike Plans, not a separate component or new entry. Its historical network priorities and revised map remain useful for comparing Albuquerque bicycle infrastructure policy across generations.'
    assessment=dict(document_function=oldq['actual_function'],substantive_content=oldq['standalone_public_value'],durable_public_usefulness='Preserves Albuquerque-specific historical trail/bikeway route priorities and capital-planning framework for comparison with later adopted City plans.',information_density='85 image-only pages, zero extractable words; complete pages rendered in existing source QA, substantive planning text and mapped route/facility proposals are carried visually.',unique_information='The full adopted July1993 City plan and November1996 map revision establish this historical planning generation; later plans and the 2024 lineage summary do not substitute for its original network proposals.',rationale=rationale,reviewed_document_content=True,visual_inspection_completed=True,page_count=85,extracted_word_count=0,standalone_public_value='substantive',publication_form='standalone',series_relationship='standalone',currentness_review_required=True,currentness_review=dict(status='historical_superseded',authoritative_sources=EVIDENCE,finding='Historical City plan adopted July1993, with map revised November1996; recorded official succession evidence identifies later replacement by the 2015 plan. Exact identity is established separately by the recovered 1993 official original.',publication_qualification='Historical predecessor under existing Previous Bike Plans heading; this does not describe the current bicycle network. Canonical inventory explicitly records July1993 adoption and November1996 map revision.'),reused_review_evidence=EVIDENCE[0],fresh_quality_review=False)
    changes=dict(status='validated',source_url=e['authoritative_record_url'],direct_file_url=e['authoritative_source_url'],title='Trails and Bikeways Facility Plan, adopted July 1993; map revised November 1996',date='1993-07',size_bytes=4624017,checksum_sha256=SHA,local_path=e['retained_local_original']['path'],provenance_status='Exact authoritative City trailbky.pdf original reconciled with existing canonical R2 object by retained original and fresh full public GET, size and SHA256; historical July1993 adoption / November1996 map revision.',review_reason=None,validation_status='passed',exclusion_reason=None,scope_assessment=e['scope_assessment'],quality_assessment=assessment,publication_quality_decision=dict(decision='passes',finding_id=TASK+':'+ID,assessment=assessment,evidence=[EVIDENCE[0],P+'evidence-verification.json',P+'public-byte-verification.json',P+'governance-reconciliation.json']),processing_notes=b['processing_notes']+['2026-10-07 '+TASK+': September26 authoritative original recovered via duplicate '+DUP+' conclusively establishes canonical identity: adopted July1993, map revised November1996; 85 pages, 4624017 bytes, SHA256 '+SHA+'. Fresh full public GET matches. The 2024 update-summary URL remains historical lineage evidence only; source_url/direct_file_url now identify the actual original. Explicit registered scoped supersession clears the stale work prerequisite and reconciles existing-publication lifecycle to validated. Existing historical scope/quality review reused; duplicate row and all prior evidence unchanged. No R2 or visitor-visible mutation.'])
    save(P+'record-updates.json',dict(approved_updates=[dict(id=ID,changes=changes)]))
    event('governance_implementation','Five explicit record-scoped replacements release only stale canonical source/hold/queue state; original governing artifacts, unrelated decisions and duplicate relationship preserved.',P+'governance-reconciliation.json')
    refresh();G.active_check('mutation','inventory_disposition',[ID])
def queue():
    inv=G.load('project-state/master-inventory.json');prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved={r['id'] for r in inv['candidates'] if r['status']=='approved for addition'}
    q.update(artifact_type='canonical_provenance_reconciliation_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for k in ['gated','source_or_structural_blocked']:
        original=prior[k+'_pending_ids'];q[k+'_pending_ids']=({i:why for i,why in original.items() if i in pending} if isinstance(original,dict) else sorted(i for i in original if i in pending));q[k+'_pending_count']=len(q[k+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated))
    q['canonical_provenance_reconciliation']=dict(task=TASK,validated_id=ID,cleared_source_blockers=1,duplicate_unchanged=DUP)
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,335,321,14,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
def queue_contract():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    pop=copy.deepcopy(G.load(P+'population.json'))
    pop['operation_classes'].append('family_review')
    pop['artifact_paths'].append(P+'population-v2.json')
    # The deterministic owner-queue builder is classified as family_review.
    # Add that operation only; the one canonical candidate population is identical.
    G.write_once(P+'population-v2.json',pop)
    plan=G.load(P+'implementation.json');plan['actions']=pop['operation_classes'];save(P+'implementation.json',plan)
    refresh()
def retained_queue():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    pop=copy.deepcopy(G.load(P+'population-v2.json'));pop['artifact_paths'] += [P+'population-v3.json','project-state/discovery/retained-source-audit-queue.json']
    G.write_once(P+'population-v3.json',pop);refresh();G.active_check('mutation','family_review',[ID])
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/New-RetainedSourceAuditQueue.ps1'],check=True)
    preserve_retained_metadata()
    event('family_review','Deterministic retained-source audit regeneration adds only this canonical City view URL as a pending root, preserving all 656 prior audits; no descendant crawl or new task population started. Operation class also covers regenerated zero-owner queue.', 'project-state/discovery/retained-source-audit-queue.json')
    a=G.load(P+'accounting.json');a['retained_source_audit_delta']=dict(prior_records=656,current_records=657,added_candidate_id=ID,added_source_url='https://www.cabq.gov/planning/documents/trailbky.pdf/view',added_status='pending descendant crawl',descendant_research_performed=False,prior_records_unchanged=True);save(P+'accounting.json',a)
    refresh();guard()
def preserve_retained_metadata():
    # ConvertFrom-Json can coerce ISO strings to DateTime and change their zone
    # on serialization. Preserve each original prior row exactly, not just time equivalence.
    path='project-state/discovery/retained-source-audit-queue.json'
    prior=json.loads(subprocess.check_output(['git','show',BASE+':'+path],cwd=G.ROOT));original={r['source_url']:r for r in prior['records']}
    current=G.load(path);assert len(current['records'])==len(original)+1
    assert {r['source_url'] for r in current['records']}==set(original)|{'https://www.cabq.gov/planning/documents/trailbky.pdf/view'}
    added=[r for r in current['records'] if r['source_url'] not in original]
    note='Eligibility bookkeeping only for the reconciled canonical original. No descendant crawl or additional task population started; source identity and existing review are conclusively settled.'
    if note not in added[0]['processing_notes']:added[0]['processing_notes'].append(note)
    current['records']=copy.deepcopy(prior['records'])+added
    save(path,current)
def recover_retained_metadata():
    refresh();G.active_check('mutation','family_review',[ID]);preserve_retained_metadata();refresh();guard()
def apply():
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    current=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID);changes=G.load(P+'record-updates.json')['approved_updates'][0]['changes']
    if current['status']=='validated':assert all(current.get(k)==v for k,v in changes.items()),'Interrupted mutation differs from frozen request'
    else:subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    p=G.ROOT/'project-state/master-inventory.json';p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    queue();refresh()
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True,stdout=subprocess.DEVNULL)
    refresh();subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    before=G.load(P+'baseline-records.json');after=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    save(P+'accounting.json',dict(task_id=TASK,candidate_ids=[ID],before_status=before['canonical']['status'],after_status=after['status'],before_row_sha256=G.digest(before['canonical']),after_row_sha256=G.digest(after),duplicate=dict(id=DUP,unchanged_row_sha256=G.digest(before['duplicate_evidence_only']),canonical_id=ID),queue=dict(approved=0,pending=335,governance_gated=321,source_structural_blocked=14,actionable=0,human_review=0),blocker_cleared=True,owner_decision_required=False,r2_delta=dict(objects=0,bytes=0,uploads=0,overwrites=0,deletions=0),visitor_visible_delta=0))
    event('inventory_disposition','Reconcile exactly canonical existing-publication row to validated using the conclusive exact official original, structured reused positive scope/quality evidence and fresh public GET; deterministically regenerate accounting.',P+'accounting.json')
    save(P+'progress.json',dict(stage='canonical_reconciled_accounting_saved_validation_pending',completed=[ID],remaining=['validation','authorized_background_integration']))
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8');links=old[old.index('[Owner correction]'):]
    text='# Current project state\n\n1993 Trails and Bikeways Facility Plan canonical src-395957636cb2fed0 reconciled to validated. Intact September26 official original and fresh full public GET match: 85 pages, 4624017 bytes, SHA256 c61bc45648f9fb2ec7e36262e71c61a68babaa6b3fbab37b436ce0603f415b92. Adopted July1993, map revised November1996; historical predecessor, not current network. Explicit scoped registry replacements clear the stale source hold. Duplicate src-fee63a8f74f3f110 and historical evidence unchanged; existing scope/quality review reused.\n\nQueue: 0 approved / 335 pending (321 gated / 14 source-structural blocked), 0 actionable / human review. No publication population or owner decision. Zero visible/R2 delta. Full validation and background main/planning synchronization pending; no other population. Prior agenda/DPM reconciliation unchanged.\n\n[Receipt](governance/trails-1993-canonical-reconciliation-2026-10-07/receipt.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links
    current.write_text(text,encoding='utf-8',newline='\n');refresh();guard()
def receipt():
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);evidence=[P+n for n in ['evidence-verification.json','public-byte-verification.json','governance-reconciliation.json','record-updates.json','accounting.json','queue.json']]
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],status='canonical_reconciliation_complete_validation_pending',accounting=G.load(P+'accounting.json'),normal_validation='pending',owner_decision_required=False,visitor_visible_delta=0,r2_delta=0,evidence_sha256={p:G.file_hash(p) for p in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact canonical row only: retained official original and fresh complete public GET establish size/hash identity; the existing September26 substantive/visual/mission-scope review is preserved and normalized for current positive lifecycle gates. Five registered explicit scope exceptions release only the stale canonical source prerequisite/queue state; all unrelated architecture, settled dispositions and history remain unchanged. Existing public entry and R2 object have zero delta. Duplicate row unchanged. No campaign, publication population, upload or owner-borderline referral begun.',evidence=evidence) for r in c['resolved_rules']}))
    refresh();G.active_check('final');guard()
def render():
    from playwright.sync_api import sync_playwright
    from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
    from functools import partial
    import threading
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(G.ROOT/'tmp/site-build')))
    threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for label,w,h in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=w,height=h));page.goto('http://127.0.0.1:%s/transportation/bicycling/bike-plans/'%server.server_port,wait_until='networkidle')
            link=page.locator('a[href="'+URL+'"]');assert link.count()==1 and link.inner_text()=='1993 Trails and Bikeways Facility Plan'
            previous=page.locator('#previous-bike-plans');assert previous.count()==1
            assert previous.evaluate('(h,a)=>!!(h.compareDocumentPosition(a)&Node.DOCUMENT_POSITION_FOLLOWING)',link.element_handle())
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            link.scroll_into_view_if_needed();path=P+label+'.png';page.screenshot(path=str(G.ROOT/path))
            results.append(dict(viewport=label,width=w,height=h,screenshot=path,canonical_link_count=1,canonical_label=link.inner_text(),historical_previous_plans_placement=True,no_horizontal_overflow=True))
            page.close()
        browser.close()
    server.shutdown();server.server_close()
    save(P+'rendered-check.json',dict(browser='Google Chrome via Playwright',built_root='tmp/site-build',route='transportation/bicycling/bike-plans',results=results,visitor_visible_source_tree_unchanged=True,note='Existing page identifies the 1993 historical predecessor under Previous Bike Plans; November1996 map revision is preserved in canonical metadata and underlying original, without a visible rewrite.'))
def guard():
    from WorkflowStageLifecycle import StageSnapshot,git,canonical_bytes
    stage=StageSnapshot(TASK);state=stage.load_json(P+'starting-state.json');pop_path=next(P+s for s in ['population-v3.json','population-v2.json','population.json'] if (G.ROOT/(P+s)).exists());pop=stage.load_json(pop_path)
    assert pop['candidate_ids']==[ID] and pop['pages']==[]
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for path,key in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==state[key]
    before={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']};after={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert before.keys()==after.keys() and {i for i in before if before[i]!=after[i]}<={ID}
    assert after[DUP]==before[DUP] and after[DUP]['status']=='duplicate'
    for path in EVIDENCE:assert canonical_bytes(stage.read_bytes(path))==canonical_bytes(git('show',BASE+':'+path))
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    retained='project-state/discovery/retained-source-audit-queue.json'
    old_retained=json.loads(git('show',BASE+':'+retained));new_retained=stage.load_json(retained)
    prior_roots={r['source_url']:r for r in old_retained['records']};current_roots={r['source_url']:r for r in new_retained['records']}
    assert all(current_roots.get(u)==r for u,r in prior_roots.items())
    assert new_retained['records'][:len(old_retained['records'])]==old_retained['records']
    added=set(current_roots)-set(prior_roots)
    assert added <= {'https://www.cabq.gov/planning/documents/trailbky.pdf/view'}
    if added:
        new=current_roots[next(iter(added))];assert new['candidate_id']==ID and new['audit_status']=='pending descendant crawl' and new['discovered_documents']==new['archived_documents']==0 and new['crawl_output'] is None
    if after[ID]!=before[ID]:
        expected=copy.deepcopy(before[ID]);expected.update(stage.load_json(P+'record-updates.json')['approved_updates'][0]['changes']);expected['updated_at']=after[ID]['updated_at'];assert after[ID]==expected
        assert after[ID]['status']=='validated' and after[ID]['validation_status']=='passed' and after[ID]['checksum_sha256']==SHA and after[ID]['size_bytes']==4624017
        assert after[ID]['source_url']=='https://www.cabq.gov/planning/documents/trailbky.pdf/view' and after[ID]['direct_file_url']=='https://www.cabq.gov/planning/documents/trailbky.pdf'
        assert after[ID]['processing_notes'][:len(before[ID]['processing_notes'])]==before[ID]['processing_notes']
        for k in ['r2_key','r2_url','r2_etag','r2_last_modified','implementation_location','implementation_locations','description']:assert after[ID][k]==before[ID][k]
        assert after[ID]['scope_assessment']==stage.load_json(P+'evidence-verification.json')['scope_assessment']
        from PublicationQuality import require_publication_quality
        require_publication_quality(after[ID])
        q=stage.load_json(P+'queue.json');assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,335,321,14)
        assert ID not in q['pending_ids'] and ID not in q['source_or_structural_blocked_pending_ids']
        assert stage.load_json(P+'public-byte-verification.json')['public_verification']['checksum_sha256']==SHA
    print('Exact canonical population, duplicate/history preservation and zero visible/R2 delta passed')

if __name__=='__main__':globals()[sys.argv[1]]()
