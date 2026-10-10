"""Preserve completed 2004 recovery evidence and push only its background branch."""
import copy, gzip, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes

TASK='progress-2004-remote-checkpoint-2026-10-10'
P='project-state/governance/'+TASK+'/'
OLD='project-state/governance/progress-2004-source-recovery-2026-10-09/'
BASE='c7eec9b6abd63f530750f40b5922dc0e839d2713'
REMOTE='349a6ca93a5df42fa8a332deb16f93ffb58d5580'
ID='src-352d880cb11386d3'
BRANCH='codex/progress-2004-source-recovery-2026-10-10'
SCRIPT='scripts/project/Progress2004RemoteCheckpoint.py'
RUNNER='scripts/project/Invoke-ProjectValidation.ps1'
OPS=['governance_implementation','background_integration']

def now():return datetime.now(timezone.utc).isoformat()

def remotes():
    return {line.split()[1]:line.split()[0] for line in subprocess.check_output(['git','ls-remote','--heads','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot','refs/heads/'+BRANCH],encoding='utf-8').splitlines()}

def refresh():
    baseline=G.git('show',BASE+':'+RUNNER)
    addition='& python "$PSScriptRoot/Progress2004RemoteCheckpoint.py" guard\nif ($LASTEXITCODE) { throw "2004 recovery remote checkpoint boundary failed" }\n'
    expected=baseline.replace('Set-StrictMode -Version Latest',addition+'Set-StrictMode -Version Latest',1)
    actual=(G.ROOT/RUNNER).read_text(encoding='utf-8').strip()
    assert actual in [baseline,expected],'Unexpected validation runner change'
    r=G.load(G.REGISTRY)
    if actual==expected:
        row=next(x for x in r['entries'] if x['governance_id']=='policy-durable-task-governance')
        a=next(x for x in row['controlling_artifacts'] if x['path']==RUNNER)
        assert a['binding_pointers']==['/implementation'];a['sha256']=G.file_hash(RUNNER);save(G.REGISTRY,r)
    paths=[x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/P).glob('*') if x.is_file() and x.name not in ['authority.json','supersession.json','implementation.json']]
    audit(paths)
    n=max([int(x.stem.split('-v')[1]) for x in (G.ROOT/P).glob('contract-v*.json')],default=0)+1
    assert n<=20;path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates'],c
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for field in row.get('constraints',[]):subjects.setdefault(field['subject'],{})[field['field']]=field['equals']
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'verification.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; no conflict/gate')

def event(op,summary,evidence):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)

def setup():
    assert G.git('rev-parse','HEAD')==BASE and G.git('branch','--show-current')==BRANCH
    assert remotes()=={'refs/heads/main':REMOTE,'refs/heads/chatgpt/planning-snapshot':REMOTE}
    subprocess.run(['git','merge-base','--is-ancestor',REMOTE,BASE],check=True)
    outputs=['population.json','authority.json','supersession.json','verification.json','implementation.json','receipt.json','progress.json','validation.log','integration-intent.json','remote-final.json']+[f'contract-v{i}.json' for i in range(1,21)]
    paths=[P+x for x in outputs]+[SCRIPT,RUNNER,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=['content/city-data/city-progress-surveys.md'],operation_classes=OPS,artifact_paths=sorted(paths)))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));assert not c['conflicts']
    requirement='Current 2026-10-10 owner instruction: continue exactly src-352d880cb11386d3, first inspect the local checkout and compare current remote main, preserve existing research and implementation, never use the obsolete August 30 codex/albuquerque-progress-report-history branch as baseline, preserve progressed research in durable task records, complete possible work and validation, and push completed background work or a resumable checkpoint to the remote repository. Completed research at '+BASE+' is reused without repeating the investigation or reopening settled dispositions. This phase authorizes a normal no-force push of this exact background evidence and checkpoint to '+BRANCH+' only. Remote main/planning-snapshot remain unchanged. No visitor-visible change or merge, R2 action, unrelated population, new disposition or custodian message; any publication proposal requires a reviewed content PR.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction',candidate_ids=[ID],instruction=requirement,remote_branch=BRANCH,remote_push_authorized=True,visitor_visible_mutation_authorized=False,r2_mutation_authorized=False))
    r=G.load(G.REGISTRY);old=next(x for x in r['entries'] if x['governance_id']=='owner-progress-2004-source-recovery-2026-10-09');assert old['state']=='active'
    new=copy.deepcopy(old);new_id=old['governance_id']+'-remote-checkpoint-authorized'
    revised=old['binding_requirement'].replace('No external storage or Git ref mutation is authorized by this initial contract.','No external storage mutation is authorized. The explicit 2026-10-10 owner continuation replaces only the former local-only Git boundary: the completed exact background recovery evidence and its durability checkpoint may be pushed without force to '+BRANCH+'. No visitor-visible merge or unrelated external effect.')
    assert revised!=old['binding_requirement']
    proposal=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=revised,consequences='Only background evidence remote durability; all original recovery findings, source hold, reports, queues and R2 preserved.',authorization_artifact=P+'authority.json')
    G.write_once(P+'supersession.json',dict(proposals={old['governance_id']:proposal}))
    new.update(governance_id=new_id,binding_requirement=revised,required_actions=[revised],authority='Explicit current owner continuation',implementation_status='background checkpoint push authorized; source hold unchanged');new['controlling_artifacts'] += [dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
    old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');r['entries'].append(new)
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='2004 recovery remote evidence checkpoint',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner continuation',decision_date='2026-10-10',effective_date='2026-10-10',state='active',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No visitor-visible or R2 mutation','No force push or unrelated remote ref change'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded remote checkpoint'))
    save(G.REGISTRY,r)
    receipt=G.load(OLD+'receipt.json');assert receipt['normal_validation']=='passed' and receipt['outcome']=='complete_original_not_recovered'
    for path in (G.ROOT/OLD).glob('retrieval-*.json'):
        e=G.load(path.relative_to(G.ROOT));compressed=e.get('preserved_response')
        if compressed:
            data=gzip.decompress((G.ROOT/compressed).read_bytes());assert len(data)==e['size_bytes'] and hashlib.sha256(data).hexdigest()==e['sha256'],path
    protected=['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']
    G.write_once(P+'verification.json',dict(verified_at=now(),local_baseline=BASE,remote_main=REMOTE,local_ahead_commits=1,uncommitted_research_found=False,obsolete_branch_used_as_baseline=False,prior_receipt=OLD+'receipt.json',prior_validation=OLD+'validation.log',all_preserved_response_sizes_sha256_reverified=True,prior_research_sha256={x.relative_to(G.ROOT).as_posix():G.file_hash(x.relative_to(G.ROOT)) for x in (G.ROOT/OLD).glob('*') if x.is_file()},protected_sha256={x:G.file_hash(x) for x in protected},content_tree=G.git('rev-parse',BASE+':content'),queue_counts=receipt['accounting'],remaining_evidence_prerequisite=receipt['remaining_evidence_prerequisite']))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='progress-2004-source-recovery-2026-10-09';life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Progress2004RemoteCheckpoint',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/RUNNER;s=runner.read_text(encoding='utf-8');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Progress2004RemoteCheckpoint.py" guard\nif ($LASTEXITCODE) { throw "2004 recovery remote checkpoint boundary failed" }\nSet-StrictMode -Version Latest',1);runner.write_text(s,encoding='utf-8',newline='\n')
    event('governance_implementation','Verified completed checkpoint and every preserved source response hash; whole prior evidence and protected state frozen. Explicit current push authority supersedes only the local-only boundary.',P+'verification.json')
    save(P+'progress.json',dict(state='prior_recovery_verified_remote_checkpoint_validation_pending',remaining=['full normal validation','background commit and remote push','remote verification'],r2_delta=0,visitor_visible_delta=0))
    refresh();G.active_check('final');guard()

def guard():
    st=StageSnapshot(TASK);v=st.load_json(P+'verification.json');pop=st.load_json(P+'population.json');assert pop['candidate_ids']==[ID] and pop['baseline_commit']==BASE
    st.assert_no_visible_changes(REMOTE,v['content_tree'])
    for path,h in {**v['prior_research_sha256'],**v['protected_sha256']}.items():assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==h,path
    paths=set(G.git('diff',BASE,st.end,'--name-only').splitlines()) if st.end else set(G.changed_paths(BASE));assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    print('PASS 2004 remote checkpoint: entire prior recovery evidence, source hold, reports, inventory, queues and R2 unchanged')

def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard()
    log=(G.ROOT/'tmp/progress2004-remote-validation.log').read_text(encoding='utf-8-sig')
    assert '"Hugo": "passed"' in log and 'CURRENT.md resume-pointer regression passed.' in log and '72 contiguous stage intervals' in log and 'Traceback (most recent call last)' not in log
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(x.expandtabs(4).rstrip() for x in log.splitlines())+'\n',encoding='utf-8',newline='\n')
    r=G.load(P+'receipt.json');r.update(state='validated_background_checkpoint_ready_for_push',normal_validation='passed',validation_log=P+'validation.log',validation_contract=G.load(G.ACTIVE_TASK)['contract'],validation_scope='Complete normal project suite: governance, exact delta, inventory/queues/checkpoint, historical lifecycle/evidence, quality/source/archive/crawler regressions, Hugo and rendered checks. Optional full-site external HTTP sweep not invoked.')
    for row in r['governance_accounting'].values():row['evidence'].append(P+'validation.log')
    save(P+'receipt.json',r)
    save(P+'progress.json',dict(state='full_validation_passed_background_push_ready',remaining=['normal no-force branch push','remote ref verification and durable receipt'],remaining_source_prerequisite=r['remaining_evidence_prerequisite'],r2_delta=0,visitor_visible_delta=0))
    current=G.ROOT/'project-state/CURRENT.md';s=current.read_text(encoding='utf-8').replace('is being validated.','passed full normal validation and is ready for the authorized push.');current.write_text(s,encoding='utf-8',newline='\n')
    event('background_integration','Fresh complete normal suite passed. Exact background-only branch push ready; all prior recovery findings, original evidence and protected state remain unchanged.',P+'validation.log')
    refresh();G.active_check('mutation','background_integration',[ID]);guard()

def integrate():
    assert G.git('branch','--show-current')==BRANCH
    assert remotes()=={'refs/heads/main':REMOTE,'refs/heads/chatgpt/planning-snapshot':REMOTE},'Remote refs changed before first push'
    assert G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    subprocess.run(['git','add','--',*G.changed_paths(BASE)],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','-m','Preserve and authorize remote 2004 report recovery checkpoint'],check=True)
    G.active_check('mutation','background_integration',[ID]);guard()
    subprocess.run(['git','push','-u','origin','HEAD:refs/heads/'+BRANCH],check=True)
    head=G.git('rev-parse','HEAD');assert remotes()=={'refs/heads/main':REMOTE,'refs/heads/chatgpt/planning-snapshot':REMOTE,'refs/heads/'+BRANCH:head}
    assert not G.git('status','--porcelain')
    print('Verified remote background checkpoint:',BRANCH,head)

def transport():
    assert G.git('branch','--show-current')==BRANCH
    head=G.git('rev-parse','HEAD');refs=remotes();assert refs=={'refs/heads/main':REMOTE,'refs/heads/chatgpt/planning-snapshot':REMOTE,'refs/heads/'+BRANCH:head}
    assert not G.git('status','--porcelain')
    G.active_check('mutation','background_integration',[ID]);guard()
    save(P+'remote-final.json',dict(verified_at=now(),remote_branch=BRANCH,checkpoint_commit=head,remote_refs=refs,worktree_clean_at_snapshot=True,validation='passed',preserved_recovery_commit=BASE,snapshot_phase='Verified completed background checkpoint before the separate remote-evidence transport commit; remote main/planning unchanged.',subsequent_transport='Containing commit carries this verified snapshot and completed state to the same branch without force; independently verify the branch afterward.'))
    r=G.load(P+'receipt.json');r.update(state='completed_background_checkpoint_pushed_and_verified',remote_checkpoint_commit=head,remote_verification=P+'remote-final.json',remote_push='Normal branch push completed and independently verified; containing evidence transport commit preserves the verified snapshot.',remote_main_unchanged=REMOTE,remote_planning_unchanged=REMOTE);save(P+'receipt.json',r)
    save(P+'progress.json',dict(state='complete_remote_background_checkpoint',remaining=[],remaining_source_prerequisite=r['remaining_evidence_prerequisite'],remote_branch=BRANCH,verified_checkpoint_commit=head,remote_main_unchanged=REMOTE,r2_delta=0,visitor_visible_delta=0,next_population_started=False))
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8');links=old[old.index('[Owner correction]'):]
    s='# Current project state\n\nExactly src-352d880cb11386d3 (2004 Albuquerque Progress Report): completed recovery at c7eec9b6 preserved without repeat research. Complete original not recovered; pending-review source hold unchanged. Remaining prerequisite: authoritative complete 2004 edition with date, contents and every page verified, or authenticated complete multipart edition. Existing reports and settled decisions preserved. Zero inventory/queue/R2/visitor-visible delta; no content PR, merge or deployment.\n\nFull normal validation passed. Background checkpoint pushed and verified on codex/progress-2004-source-recovery-2026-10-10; remote main/planning remain at 349a6ca9. [Verified remote snapshot](governance/'+TASK+'/remote-final.json) precedes its separate evidence transport commit.\n\nQueue: 0 approved /333 pending (321 gated /12 source-structural blocked), 0 actionable /human review; remaining nonterminal884.\n\n[Remote receipt](governance/'+TASK+'/receipt.json) · [Research](governance/progress-2004-source-recovery-2026-10-09/summary.md) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links
    assert len(s)<=1800;current.write_text(s,encoding='utf-8',newline='\n')
    event('background_integration','Normal background checkpoint push independently verified on the exact authorized branch. Remote main/planning, original recovery evidence, hold, reports and R2 unchanged; durable ref snapshot and completed resume state saved.',P+'remote-final.json')
    refresh();plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active)
    G.active_check('final');guard()
    subprocess.run(['git','add','--',*G.changed_paths(BASE)],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run([sys.executable,'scripts/project/Test-CurrentResumePointer.py'],check=True)
    subprocess.run(['git','commit','-m','Record verified 2004 recovery remote checkpoint and completed resume state'],check=True)
    # This carries the completed task's verified receipt; it starts no new work.
    G.active_check('final');guard()
    assert remotes()==refs,'Remote branch changed before evidence transport'
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],check=True)
    final=G.git('rev-parse','HEAD');assert remotes()=={'refs/heads/main':REMOTE,'refs/heads/chatgpt/planning-snapshot':REMOTE,'refs/heads/'+BRANCH:final}
    assert not G.git('status','--porcelain');G.active_check('final');guard()
    save('tmp/progress2004-remote-final-refs.json',dict(remote_branch=BRANCH,final_commit=final,verified_checkpoint=head,remote_refs=remotes(),worktree_clean=True,validation='passed',verified_at=now()))
    print('Final verified remote branch:',BRANCH,final)

if __name__=='__main__':globals()[sys.argv[1]]()
