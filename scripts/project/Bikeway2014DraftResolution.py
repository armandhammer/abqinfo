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

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
