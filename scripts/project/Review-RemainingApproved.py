"""Resume-safe isolated thirteen-record background review; no storage or site mutation."""
import copy, hashlib, json, subprocess, sys, runpy
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G

P='project-state/governance/remaining-approved-review-2026-10-03/'
TASK='remaining-approved-review-2026-10-03'
OWNER='owner-'+TASK
BASE='78327bed8cdc2cc25e540d1737cde22096ec8e83'
IDS=['src-ed75a3cb5ecc3b0b','src-1f9cf39555e7be6f','src-0e0cd2037365e977','src-751926439273bc52','src-255c53cabfcc83d6','src-93ef5bb0e94bfa97','src-28184729e8cc1326','src-3a4c39611a00e0a3','src-143f58c34ccb049a','src-93024cc660045c22','src-2c5c4a2267988a30','src-2aba4fa7ad3e22e2','src-ab94ccbf5e75b5d0']
def save(path,data):
    target=G.ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def audit(paths,rationale):
    registry=G.load(G.REGISTRY);data=G.load(registry['audit_artifact']);indexed={r['path']:r for r in data['artifacts']}
    for path in paths: indexed[path]=dict(path=path,sha256=G.file_hash(path),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale=rationale)
    data['artifacts']=sorted(indexed.values(),key=lambda r:r['path']);save(registry['audit_artifact'],data)
    registry['audit_sha256']=G.file_hash(registry['audit_artifact']);save(G.REGISTRY,registry)
def bind(path,gid,requirement,scope,authority='Explicit owner instruction 2026-10-03'):
    registry=G.load(G.REGISTRY)
    registry['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=scope,authority=authority,decision_date='2026-10-03',effective_date='2026-10-03',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='in progress'))
    save(G.REGISTRY,registry)
def now(): return datetime.now(timezone.utc).isoformat()
def git(*args): return subprocess.check_output(['git',*args],cwd=G.ROOT).decode().strip()
def freeze():
    assert git('rev-parse','HEAD')==BASE
    inventory=G.load('project-state/master-inventory.json')
    rows={r['id']:r for r in inventory['candidates']}
    assert all(rows[i]['status']=='approved for addition' for i in IDS)
    paths=[P+n for n in ['population.json','authority.json','starting-remote-state.json','progress.json','prior-records.json','implementation.json','supersession.json','owner-decisions-needed.json','receipt.json','summary.md','pr-body.md','remote-check.json','validation.log','bootstrap-validation.json','accounting.json','family-analysis.json']]
    paths += [P+f'contract-v{i}.json' for i in range(1,101)]
    paths += [P+f'milestone-{i}.json' for i in [3,6,9,13]]
    for rid in IDS:
        paths += [P+f'records/{rid}/{n}' for n in ['review.json','retrievals.json','research.json','family.json','publication-plan.json','validation.json','source.html','article.html','article.txt','article.png','current.html','current.txt','supplement.html','supplement.txt']]
    paths += ['scripts/project/Review-RemainingApproved.py','project-state/governance/active-task.json',G.REGISTRY,G.registry()['audit_artifact'],'project-state/master-inventory.json','project-state/ordinary-queue-current.json',P+'queue.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','external_mutation'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    pr=json.loads(subprocess.check_output(['gh','pr','view','208','--json','number,state,title,body,headRefName,headRefOid,baseRefName,url,updatedAt'],cwd=G.ROOT))
    assert pr['state']=='OPEN' and pr['headRefOid']==BASE
    refs={r:git('rev-parse',r) for r in ['origin/main','origin/codex/strong-five-review-2026-10-03','origin/chatgpt/planning-snapshot','origin/codex/remaining-approved-review-2026-10-03']}
    assert refs['origin/chatgpt/planning-snapshot']==BASE
    G.write_once(P+'starting-remote-state.json',dict(timestamp=now(),refs=refs,pr208=pr,protected_tree=git('ls-tree',BASE,'content','layouts','assets','static'),r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),production_baseline=refs['origin/main']))
    save(P+'progress.json',dict(task_id=TASK,baseline_commit=BASE,branch='codex/'+TASK,records=[dict(id=i,title=rows[i]['title'],state='not_started',research_evidence_paths=[],review_artifact_path=None,resulting_disposition=None,inventory_mutation_applied=False,validation_passed=False,checkpoint_commit_sha=None,unresolved_blocker=None,owner_decision_required=False) for i in IDS],last_pushed_commit=BASE,next_unfinished=IDS[0]))
    save(P+'owner-decisions-needed.json',dict(items=[]))
    save(P+'supersession.json',dict(proposals={}))
    c=G.resolve(G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));G.write_once(P+'contract-v1.json',c)
    print('Frozen',len(IDS),'records;',len(c['governance_ids']),'rules; gates',c['unresolved_gates'],'conflicts',c['conflicts'])
def refresh():
    old=[f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).glob('contract-v*.json')]
    audit(old,'Immutable prior resolver snapshots; historical evidence only after replacement.')
    population_path=P+('population-v3.json' if (G.ROOT/(P+'population-v3.json')).exists() else 'population.json')
    c=G.resolve(G.load(population_path),G.registry(),G.file_hash(G.REGISTRY))
    n=max([int(Path(p).stem.split('-v')[1]) for p in old],default=0)+1
    path=P+f'contract-v{n}.json';G.write_once(path,c)
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','external_mutation'],events=[],status='background_review_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for fact in r.get('constraints',[]): subjects.setdefault(fact['subject'],{})[fact['field']]=fact['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']: e['governance_ids']=c['governance_ids']
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print('Contract',path,'rules',len(c['governance_ids']),'conflicts',c['conflicts'],'gates',c['unresolved_gates'])
def setup():
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    G.write_once(P+'authority.json',dict(governance_metadata={'governance_id':OWNER},authority='Explicit current owner campaign instruction',candidate_ids=IDS,baseline_commit=BASE,instruction='Independently reassess exactly these thirteen remaining approved records under complete durable governance. September30 triage and existing approval are nonbinding for this review. Apply evidence-based scope/quality exclusions or strengthened candidate/blocked outcomes, explicitly superseding only population-specific prior approvals where needed; preserve historical evidence, all out-of-population rows, PR207 exclusions and settled family consolidation. Research provenance, currentness, family identity and quality; save implementation-ready future publication plans for survivors. No visitor-visible change, R2 upload/overwrite/delete/transform, merge, deployment, PR208 modification or planning-snapshot movement. Isolated branch starts at reviewed PR208 head. Commit/push bootstrap, then every completed individual record. Genuine unavailable owner choices are recorded and do not stop other reviews. Draft stacked PR is authorized with PR208 branch as base. Freshness checks precede each record and mutation. Validate exact population and protected trees, normal suite at milestones and completion.'))
    bind(P+'authority.json',OWNER,'Execute exactly the isolated thirteen-record background reassessment described in this current owner authority; previous population-specific approval/triage is nonbinding. Preserve every other settled decision. No site or R2 mutation, merge, PR208 change, or planning-snapshot movement. Push every completed review separately.',{'candidate_ids':IDS,'task_ids':[TASK]})
    audit([P+'prior-records.json',P+'starting-remote-state.json',P+'progress.json'],'Frozen input/progress/remote evidence; no independent binding instruction.')
    refresh()
    result=G.active_check('mutation','document_review')
    save(P+'bootstrap-validation.json',dict(timestamp=now(),result=result,review_started=False))
    print('Bootstrap validated')
def complete_bootstrap():
    # Owner expressly reopens only this population's approvals; other decisions survive.
    registry=G.load(G.REGISTRY);proposals={}
    prefixes=['decision-decisions-b8452592-five-review-exception-2026-10-03-two-county-correction','decision-next-ordinary-queue-b8bb5c70-five-review-exception-2026-10-03-two-county-correction','decision-decision-updates-b04354f2','decision-decisions-2c491c71']
    for gid in prefixes:
        old=next(r for r in registry['entries'] if r['governance_id']==gid)
        new_id=gid+'-remaining-thirteen-exception'
        new=copy.deepcopy(old)
        requirement=old['binding_requirement']+' Explicit current owner exception: prior eligibility/approval and triage for exactly the thirteen IDs in '+P+'population.json are nonbinding for independent reassessment under '+OWNER+'. All other record decisions, PR207 owner exclusions, five resolved PR208 records, settled consolidation, original provenance and size/storage gates are preserved.'
        new.update(governance_id=new_id,effective_date='2026-10-03',authority='Explicit current owner thirteen-record background review instruction',binding_requirement=requirement,required_actions=[requirement],settled_decisions=[])
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        proposals[gid]=dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Reassess only exact thirteen population approvals; preserve all other scope, provenance, consolidation, archive and owner decisions.',authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');registry['entries'].append(new)
    save(G.REGISTRY,registry);save(P+'supersession.json',dict(proposals=proposals))
    bind(P+'supersession.json','supersession-'+TASK,'Apply only the exact authorized approval exceptions recorded here. All other settled decisions and historical evidence remain controlling.',{'task_ids':[TASK]})
    pop=G.load(P+'population.json');pop['artifact_paths']+=['project-state/workflow-stage-lifecycle.json']
    # No review has begun; replacing the bootstrap population preserves the same 13 IDs.
    G.write_once(P+'population-v2.json',pop)
    pop['artifact_paths'] += [P+'population-v2.json']
    # Freeze the complete anticipated output list in a new immutable population.
    pop['artifact_paths'] += [P+'population-v3.json']
    G.write_once(P+'population-v3.json',pop)
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json')
    assert lifecycle['stages'][-1]['id']=='pr208-county-scope-correction'
    lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/Review-RemainingApproved.py'],exact_delta_guard=dict(module='Review-RemainingApproved',function='guard_current_delta')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    audit([P+'prior-records.json',P+'starting-remote-state.json',P+'progress.json'],'Frozen input/progress/remote evidence; no independent authority.')
    refresh()
    result=G.active_check('mutation','document_review')
    guard_current_delta()
    save(P+'bootstrap-validation.json',dict(timestamp=now(),result=result,review_started=False,protected_trees_unchanged=True,r2_changes=0))
def guard_current_delta():
    pop=G.load(G.load(G.ACTIVE_TASK)['population']); assert pop['candidate_ids']==IDS and pop['baseline_commit']==BASE
    assert not git('diff',BASE,'--name-only','--','content','layouts','assets','static','hugo.toml')
    assert not git('ls-files','--others','--exclude-standard','--','content','layouts','assets','static')
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert not git('diff',BASE,'--name-only','--',path)
    prior=json.loads(git('show',BASE+':project-state/master-inventory.json'));current=G.load('project-state/master-inventory.json')
    a={r['id']:r for r in prior['candidates']};b={r['id']:r for r in current['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for path in git('ls-tree','-r','--name-only',BASE,'--','project-state/governance/strong-five-review-2026-10-03','project-state/governance/pr208-county-scope-correction-2026-10-03','project-state/governance/pr207-owner-correction-2026-09-30').splitlines():
        assert not git('diff',BASE,'--name-only','--',path),path
    return True
if __name__=='__main__': globals()[sys.argv[1] if len(sys.argv)>1 else 'guard_current_delta']()
