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

def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:S.audit([x.relative_to(G.ROOT).as_posix() for x in old])
    n=max([int(x.stem.split('-v')[1]) for x in old],default=0)+1
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration'],events=[],status='in_progress')
    subjects={}
    for rule in c['resolved_rules']:
        for f in rule.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
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
    S.bind(P+'authority.json','owner-'+TASK,authority,{'candidate_ids':IDS,'task_ids':[TASK]})
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
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
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
        S.bind(path,'decision-'+TASK+'-'+review['id'],review['binding_requirement'],{'candidate_ids':[review['id']]})
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

if __name__=='__main__':{'freeze':freeze,'refresh':audit_refresh,'guard':guard}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
