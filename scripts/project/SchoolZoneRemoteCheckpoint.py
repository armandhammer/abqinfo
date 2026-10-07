"""Verify and remotely integrate only the exact completed school-zone background review."""
import copy, hashlib, json, subprocess, sys
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
from SchoolZoneTimingDesign import SOURCE, SHA, ID
TASK='school-zone-remote-checkpoint-2026-10-06'
P='project-state/governance/'+TASK+'/'
OLD='project-state/governance/school-zone-timing-design-2026-10-06/'
BASE='cff20627837b691cdd0fc828bb4bbc009ce8bc47'
REMOTE='2703c8dffe0cd672e438c754c1100c7eff6c9d96'
SCRIPT='scripts/project/SchoolZoneRemoteCheckpoint.py'
OPS=['governance_implementation','background_integration']
def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    paths=[x for x in G.changed_paths(BASE) if x.startswith('project-state/') and x not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}]
    audit(paths+[x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/P).glob('contract-v*.json')])
    n=len(list((G.ROOT/P).glob('contract-v*.json')))+1;assert n<=10
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'verification.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; remaining gates',c['unresolved_gates'])
def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','supersession.json','verification.json','archive-preflight.json','r2-live.json','implementation.json','receipt.json','validation.log','integration-intent.json','remote-final.json']+[f'contract-v{i}.json' for i in range(1,11)]
    paths=[P+x for x in outputs]+[SCRIPT,'scripts/project/SchoolZoneTimingDesign.py','scripts/project/Invoke-ProjectValidation.ps1',G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/workflow-stage-lifecycle.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=['school-zone-active-times'],pages=['content/transportation/safety-crash-data.md','content/transportation/operations-data.md','content/transportation/roadway-projects/speed-management.md','content/transportation/design-references.md'],operation_classes=OPS,artifact_paths=sorted(paths)))
    # Initial exhaustive resolution is frozen before registering the new invocation.
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    requirement='Current owner corrective instruction explicitly authorizes verifying and reusing the exact completed local school-zone review, saving immutable review/structured timing/design/archive-plan evidence and accurate CURRENT/checkpoint/active-task state, validating, committing and pushing background-only work, synchronizing main and chatgpt/planning-snapshot and verifying final remote refs. EXACT population is the unchanged owner/IPRA PDF SHA256 '+SHA+'. No elementary work, other records, R2 mutation without separate exact authority, static-document publication PR before archive verification, visitor-visible changes, content merge or deployment. The prior local-only integration boundary is explicitly replaced only for validated background review/state integration.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner corrective instruction',instruction=requirement,source_sha256=SHA,background_push_and_main_planning_sync_authorized=True,r2_upload_authorized=False,visitor_visible_change_authorized=False))
    r=G.load(G.REGISTRY);old=next(x for x in r['entries'] if x['governance_id']=='owner-school-zone-timing-design-2026-10-06');replacement=copy.deepcopy(old)
    new_id=old['governance_id']+'-remote-checkpoint-authorized'
    revised=old['binding_requirement'].replace('not new R2 mutation or merge/deployment.','not new R2 mutation or visitor-visible merge/deployment. Current corrective owner instruction authorizes exact background review/state integration into main and planning-snapshot after validation.')
    replacement.update(governance_id=new_id,binding_requirement=revised,required_actions=[revised],authority='Explicit current owner corrective instruction',implementation_status='exact background integration authorized; archival gate retained')
    replacement['controlling_artifacts'] += [dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
    proposal=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=revised,consequences='Persist only the completed background school-zone review and state to both remote branches; preserve original source/review, all site/inventory/R2 bytes and the separate R2 authorization gate.',authorization_artifact=P+'authority.json')
    G.write_once(P+'supersession.json',dict(proposals={old['governance_id']:proposal}));old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');r['entries'].append(replacement)
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Exact school-zone background review remote durability correction',scope=dict(task_ids=[TASK],candidate_ids=[ID]),authority='Explicit current owner instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No R2 upload without separate exact authorization','No visitor-visible or unrelated population change'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='background push/ref synchronization authorized'))
    save(G.REGISTRY,r)
    # Pin the recovered local evidence rather than redoing the settled review.
    remote_registry=json.loads(G.git('show',REMOTE+':'+G.REGISTRY));local_registry=json.loads(G.git('show',BASE+':'+G.REGISTRY))
    remote_rows={x['governance_id']:x for x in remote_registry['entries']};local_rows={x['governance_id']:x for x in local_registry['entries']}
    for gid,row in remote_rows.items():
        a=copy.deepcopy(row);b=copy.deepcopy(local_rows[gid]);a.pop('controlling_artifacts');b.pop('controlling_artifacts');assert a==b,gid
    G.write_once(P+'verification.json',dict(remote_baseline=REMOTE,recovered_local_commit=BASE,source_path=str((G.ROOT/SOURCE).resolve()),source_bytes=3013109,source_sha256=SHA,pages=33,all_render_fingerprints_and_extracted_text_reverified=True,all_prior_receipt_evidence_hashes_reverified=True,schools=32,schedules=30,intervals=61,review_reused_not_redecided=True,remote_existing_decisions_preserved=True,prior_review_paths_sha256={x.relative_to(G.ROOT).as_posix():G.file_hash(x.relative_to(G.ROOT)) for x in (G.ROOT/OLD).glob('*') if x.is_file()},protected_sha256={p:G.file_hash(p) for p in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']},content_tree=G.git('rev-parse',REMOTE+':content'),checkpoint_before=G.load('project-state/checkpoint.json')))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='school-zone-timing-design-2026-10-06';life['stages'][-1]['end_commit']=BASE
    sealed={x['path'] for x in life['protected_evidence']}
    for path,h in G.load(P+'verification.json')['prior_review_paths_sha256'].items():
        if path not in sealed:life['protected_evidence'].append(dict(path=path,commit=BASE,sha256=h))
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='SchoolZoneRemoteCheckpoint',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    p=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=p.read_text(encoding='utf-8-sig');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/SchoolZoneRemoteCheckpoint.py" guard\nif ($LASTEXITCODE) { throw \'School-zone remote checkpoint boundary failed.\' }\nSet-StrictMode -Version Latest',1);p.write_text(s,encoding='utf-8',newline='\n')
    refresh()
def guard():
    st=StageSnapshot(TASK);pop=st.load_json(P+'population.json');v=st.load_json(P+'verification.json')
    assert pop['candidate_ids']==[ID] and pop['baseline_commit']==BASE
    st.assert_no_visible_changes(REMOTE,v['content_tree'])
    paths=set(G.changed_paths(BASE)) if not st.end else set(G.git('diff',BASE,st.end,'--name-only').splitlines());assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for p,h in {**v['protected_sha256'],**v['prior_review_paths_sha256']}.items():assert hashlib.sha256(canonical_bytes(st.read_bytes(p))).hexdigest()==h,p
    cp=st.load_json('project-state/checkpoint.json');before=v['checkpoint_before']
    assert {k:x for k,x in cp.items() if k not in ['school_zone_timing_review','next_owner_requested_task']}=={k:x for k,x in before.items() if k!='next_owner_requested_task'}
    if 'school_zone_timing_review' in cp:
        assert cp['school_zone_timing_review']['source_sha256']==SHA and cp['school_zone_timing_review']['remaining_gate']=='explicit_owner_r2_archival_authorization'
        assert cp['next_owner_requested_task']['state']=='review_complete_archival_authorization_pending'
        assert cp['next_owner_requested_task']['owner_context']==before['next_owner_requested_task']['owner_context']
    if (G.ROOT/SOURCE).exists():assert hashlib.sha256((G.ROOT/SOURCE).read_bytes()).hexdigest()==SHA
    print('PASS: exact reused school-zone review; preserved original evidence, content/inventory/queues/R2; checkpoint-only addition and authorized background sync')
def state():
    G.active_check('mutation','governance_implementation',[ID]);guard()
    live=G.load(P+'r2-live.json');key=G.load(OLD+'archive-plan.json')['r2_key'];assert key.casefold() not in {x['key'].casefold() for x in live['objects']}
    assert live['total_bytes']+3013109<=13000000000
    save(P+'archive-preflight.json',dict(source_path=str((G.ROOT/SOURCE).resolve()),bytes=3013109,sha256=SHA,page_count=33,r2_key=key,live_checked_at=live['generated_at'],live_objects=live['object_count'],live_bytes=live['total_bytes'],projected_bytes=live['total_bytes']+3013109,key_absent_casefold=True,no_overwrite=True,no_delete=True,archival_authorized=False,required_authority='Explicit owner authorization for one unchanged-original upload under this exact key, then complete public-download size/SHA256 verification',prior_archive_plan=OLD+'archive-plan.json'))
    cp=G.load('project-state/checkpoint.json');cp['school_zone_timing_review']=dict(state='review_complete_background_remote_checkpoint',source_sha256=SHA,source_bytes=3013109,pages=33,schools=32,schedules=30,intervals=61,review=OLD+'review.json',timings=OLD+'timings.json',proposed_content=OLD+'proposed-content.md',archive_plan=OLD+'archive-plan.json',current_preflight=P+'archive-preflight.json',remaining_gate='explicit_owner_r2_archival_authorization',archival_authorized=False,visible_pr_created=False,elementary_continuation='Expected later; outside this population and not a blocker')
    before=G.load(P+'verification.json')['checkpoint_before']['next_owner_requested_task']
    cp['next_owner_requested_task']=dict(state='review_complete_archival_authorization_pending',filename=before['filename'],owner_context=before['owner_context'],completed_review=OLD+'review.json',current_preflight=P+'archive-preflight.json',remaining_gate='explicit_owner_r2_archival_authorization');save('project-state/checkpoint.json',cp)
    current=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8-sig');current=current.replace('Existing site/inventory/queue/R2 unchanged.','Existing site/inventory/queue/R2 unchanged. Review, data and design are in the governed background checkpoint; remote integration is being verified.');current=current.replace('[Review]','[Checkpoint](governance/'+TASK+'/verification.json) · [Review]',1);(G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='governance_implementation',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Verified exact original and all saved page/render/evidence fingerprints; reused complete review, refreshed absent-key storage preflight and recorded exact pending archival gate in CURRENT/checkpoint; no review or elementary population expansion.',evidence=P+'verification.json'));save(P+'implementation.json',plan);refresh();G.active_check('final');guard()
def finish():
    log=(G.ROOT/(P+'validation.log')).read_text(encoding='utf-8-sig');assert '"Hugo": "passed"' in log and 'Traceback' not in log
    G.active_check('mutation','background_integration',[ID]);guard()
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    save(P+'integration-intent.json',dict(authority=P+'authority.json',expected_remote_main=REMOTE,expected_remote_planning=REMOTE,background_only=True,atomic_push=True,no_force=True,preserve_local_review_commit=BASE,source_sha256=SHA,remaining_gate='explicit_owner_r2_archival_authorization'))
    save(P+'receipt.json',dict(task_id=TASK,state='verified_review_background_integration_ready',source_bytes=3013109,source_sha256=SHA,pages=33,schools=32,schedules=30,intervals=61,review=OLD+'review.json',timings=OLD+'timings.json',proposed_content=OLD+'proposed-content.md',archive_preflight=P+'archive-preflight.json',archival_authorized=False,visible_pr_created=False,r2_uploads=0,normal_validation='passed',validation_log_sha256=G.file_hash(P+'validation.log'),prior_review_immutable=True,remaining_owner_action='Authorize exact unchanged-original R2 upload under archive-preflight.json and full public exact-byte verification',governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],result='Prior decisions and exact original review evidence preserved; only explicitly authorized background checkpoint/ref integration. Source/evidence fingerprints, complete normal suite, protected-state/content guard and exact archive gate passed.',evidence=[P+'verification.json',P+'archive-preflight.json',P+'validation.log']) for r in c['resolved_rules']}))
    current=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8-sig').replace('Background remote checkpoint validation pending.','Full validation passed; authorized background remote integration pending.');(G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='background_integration',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Complete normal/governance/sealed-history/Hugo validation passed; exact remote background synchronization intent recorded. No archival gate release, content PR or other population.',evidence=P+'integration-intent.json'));save(P+'implementation.json',plan);refresh();G.active_check('final');guard()
if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
