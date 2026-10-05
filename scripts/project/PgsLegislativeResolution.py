"""Exactly three PGS legislative records; background only, historical evidence sealed."""
import copy, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git as git_bytes

TASK='pgs-legislative-resolution-2026-10-05'
P='project-state/governance/'+TASK+'/'
BASE='483bde8f1e660614417d7f7ab5b4e7a484b4d8be'
IDS=['src-f7c7bd5b273def22','src-68582bc4fe41fb4f','src-fcbe6a7ebcf916a1']
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value):
    p=G.ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def audit(paths):
    r=G.load(G.REGISTRY);a=G.load(r['audit_artifact']);indexed={x['path']:x for x in a['artifacts']}
    for p in paths:
        indexed[p]=dict(path=p,sha256=G.file_hash(p),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale='Exact research, source retrieval, comparison, accounting or execution evidence; no independent authority.')
    a['artifacts']=sorted(indexed.values(),key=lambda x:x['path']);save(r['audit_artifact'],a)
    r['audit_sha256']=G.file_hash(r['audit_artifact']);save(G.REGISTRY,r)
def bind(path,gid,requirement,scope,category='active owner decision'):
    r=G.load(G.REGISTRY);assert not any(x['governance_id']==gid for x in r['entries'])
    r['entries'].append(dict(governance_id=gid,category=category,title=gid,scope=scope,authority='Explicit current user three-record PGS legislative resolution instruction',decision_date='2026-10-05',effective_date='2026-10-05',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded background legislative research'))
    save(G.REGISTRY,r)
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:audit([p.relative_to(G.ROOT).as_posix() for p in old])
    n=max([int(p.stem.split('-v')[1]) for p in old],default=0)+1;path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=G.load(P+'population.json')['operation_classes'],events=[],status='research_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['use_contract_record_rules']=True
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; gates:',c['unresolved_gates'])
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    inv=G.load('project-state/master-inventory.json');rows={x['id']:x for x in inv['candidates']}
    assert all(rows[i]['status']=='pending review' for i in IDS)
    outputs=['population.json','authority.json','starting-state.json','prior-records.json','implementation.json','supersession.json','progress.json','receipt.json','accounting.json','summary.md','owner-decisions-needed.json','validation.log','queue.json','remote-final.json','decisions.json','updates.json','research-journal.json','comparison.json','integration-intent.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,101)]
    paths += [P+f'evidence-{i}.{ext}' for i in range(1,201) for ext in ['json','txt','png']]
    paths += ['scripts/project/PgsLegislativeResolution.py','scripts/project/Research-PgsLegislation.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    priorq=G.load(G.load('project-state/ordinary-queue-current.json')['artifact'])
    G.write_once(P+'starting-state.json',dict(checked_at_utc=now(),refs={x:G.git('rev-parse',x) for x in ['HEAD','origin/main','origin/chatgpt/planning-snapshot']},queue_counts={s:sum(x['status']==s for x in inv['candidates']) for s in ['approved for addition','pending review']},source_blocked_count=priorq['source_or_structural_blocked_pending_count'],source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));assert not c['conflicts']
    instruction='Resolve exactly src-f7c7bd5b273def22 F/S O-02-39 (2), src-68582bc4fe41fb4f O-03-132 and src-fcbe6a7ebcf916a1 O-04-9 together using existing durable PGS research and current authoritative Council/Legistar final files, variants, actions, amendments/substitutes, enactment numbers and required exhibits/incorporated plans. Do not reopen settled PGS chapters/package. Bill metadata alone cannot prove incomplete held PDF enacted completeness; reject MatterTextMatterId mismatches. Apply background inventory dispositions only on conclusive evidence; preserve historical originals/provenance. No visitor-visible or R2 mutation. Regenerate accounting, run full validation/governance/sealed-history/Hugo/rendered and diff checks; integrate clean background work into main and synchronize planning-snapshot. No other population. Current instruction authorizes resolution of factual holds, not arbitrary editorial supersession.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',candidate_ids=IDS,instruction=instruction))
    bind(P+'authority.json','owner-'+TASK,instruction,{'candidate_ids':IDS,'task_ids':[TASK]})
    save(P+'supersession.json',dict(proposals={}))
    bind(P+'supersession.json','supersessions-'+TASK,'Only conclusive current evidence may resolve the exact three factual enacted-package holds; no settled PGS chapter/package decisions are replaced. Preserve all historical evidence.',{'task_ids':[TASK]})
    save(P+'progress.json',dict(state='population_frozen_governed_research_ready',completed=[],remaining=IDS,r2_mutations=0,visitor_visible_mutations=0))
    audit([P+'starting-state.json',P+'prior-records.json',P+'progress.json']);refresh()
    print(G.active_check('mutation','document_review',IDS))
def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for p,k in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:
        import hashlib
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==start[k],p
    baseline=json.loads(git_bytes('show',BASE+':project-state/master-inventory.json'));a={r['id']:r for r in baseline['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes'],'Historical notes lost: '+i
        for field in ['source_url','local_path','sha256','file_size_bytes','r2_key','r2_url']:
            if field in a[i]:assert b[i].get(field)==a[i][field],(i,field)
    changes=set(git_bytes('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
    print('Exact three-record PGS / historical originals / zero visitor-visible / zero R2 guard passed')
def research_checkpoint():
    c=G.load(P+'comparison.json')
    assert all(r['held_prose_equal'] and r['word_prose_equal'] and all(e['held_numeric_sequence_equal'] and e['word_numeric_sequence_equal'] and e['held_labels_equal'] and e['word_labels_equal'] for e in r['exhibits']) for r in c['substantive_comparisons'])
    stages=G.load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id']=='pr211-postmerge-closeout-2026-10-05'
    stages['stages'][-1]['end_commit']=BASE
    stages['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/PgsLegislativeResolution.py'],exact_delta_guard=dict(module='PgsLegislativeResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=runner.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/PgsLegislativeResolution.py" guard\nif ($LASTEXITCODE) { throw \'Three-record PGS legislative background boundary failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(t,encoding='utf8',newline='\n')
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        for a in row['controlling_artifacts']:
            if a['path']=='scripts/project/Invoke-ProjectValidation.ps1':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    journal=dict(recorded_at=now(),state='research_complete_dispositions_not_yet_applied',population=IDS,existing_evidence_used=['project-state/discovery/planned-growth-strategy-cluster-research-2026-09-11.json','project-state/discovery/planned-growth-strategy-decision-2026-09-19.json','project-state/discovery/background-followup-2026-09-26/decisions.json','project-state/discovery/background-followup-2026-09-26/comparisons.json','project-state/discovery/human-review-reassessment-2026-09-26/family-evidence.json','project-state/discovery/codex-human-review-followup-queue.json'],critical_discovery='The /versions endpoint maps Key to MatterTextId and Value to MatterTextVersion. Old /texts/1 etc selected unrelated global text IDs. Correct IDs 2191/3192/3419 were checked against MatterTextMatterId 1463/2609/2802. Complete final operative clauses, headers, row labels and numeric exhibit sequences agree with held PDFs and exact listed Word attachments.',accepted_final_texts=[dict(matter_id=1463,text_id=2191,version='4',enactment='O-2002-034'),dict(matter_id=2609,text_id=3192,version='2',enactment='O-2003-047'),dict(matter_id=2802,text_id=3419,version='2',enactment='O-2004-007')],comparison=P+'comparison.json',visual_inspection='All 14/5/5 held PDF pages and 16/6/6 prior Word render pages inspected through contact sheets. Blank converter pages in the 6-page Word renders are pagination, not omitted exhibits. Both later original PDFs contain three legible forecast tables. Referenced R-02-111 Exhibit A water/wastewater/hydrology service tier and street traffic shed maps are present on pages30-31 of the separate official 32-page resolution; page32 is blank. No need to append the PGS study to these self-contained enactments.',invalid_routes_rejected=['/texts/{version} with mismatched MatterTextMatterId, retained only in historical evidence','/texts collection GET405','LegislationDetail legacy/API IDs return Invalid parameters!','ViewReport API matter ID1463 produces empty bill header; no legislative evidence'],next_action='Register conclusive three-record dispositions and narrow factual-hold resolution; preserve all settled study work.',r2_mutations=0,visitor_visible_mutations=0)
    save(P+'research-journal.json',journal)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='document_review',candidate_ids=IDS,action='research_unsettled',use_contract_record_rules=True,summary=journal['critical_discovery'],evidence=P+'research-journal.json'));save(P+'implementation.json',plan)
    save(P+'progress.json',dict(state=journal['state'],completed=['complete_source_and_version_comparison'],remaining=IDS,r2_mutations=0,visitor_visible_mutations=0))
    audit([p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.is_file() and p.name not in ['authority.json','supersession.json','implementation.json'] and not p.name.startswith('contract-v')])
    refresh();G.active_check('mutation','governance_implementation',IDS);guard()
if __name__=='__main__':
    {'freeze':freeze,'refresh':refresh,'guard':guard,'research-checkpoint':research_checkpoint}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
