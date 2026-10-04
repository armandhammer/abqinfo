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
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],cwd=G.ROOT,check=True,stdout=subprocess.DEVNULL)
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
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
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
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
    print('Exact two-record / sealed PR209 / zero visible / zero R2 guard passed')
if __name__=='__main__':
    {'freeze':freeze,'refresh':refresh,'guard':guard}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
