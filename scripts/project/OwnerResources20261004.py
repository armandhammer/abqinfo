"""Governed exact Sunport archive and bounded owner resources publication lifecycle."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git

A='sunport-exact-archive-2026-10-04'
B='owner-resources-publication-2026-10-04'
BASE='cd83baeaddd361b5e561a522c90583aa33fac931'
SUN='src-1f9cf39555e7be6f'
KEY='transportation/transportation-plans/cabq-sunport-sustainable-airport-master-plan-2019.pdf'
SHA='d4583c4d9e5e1233c402f64222fd8837ff7f0fc0a352dc2d5153776842f39d02'
SOURCE='https://documents.cabq.gov/planning/MasterPlans/Sunport/ABQ_Sustainable_Airport_Master_Plan-printing.pdf'
SCRIPT='scripts/project/OwnerResources20261004.py'
def now(): return datetime.now(timezone.utc).isoformat()
def save(p,v):
    f=G.ROOT/p;f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def prefix(task): return 'project-state/governance/'+task+'/'
def audit(paths):
    r=G.load(G.REGISTRY);a=G.load(r['audit_artifact']);d={x['path']:x for x in a['artifacts']}
    for p in paths:
        if (G.ROOT/p).is_file():
            d[p]=dict(path=p,sha256=G.file_hash(p),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale='Execution evidence or derived task implementation; continuing authority is registered separately.')
    a['artifacts']=sorted(d.values(),key=lambda x:x['path']);save(r['audit_artifact'],a)
    r['audit_sha256']=G.file_hash(r['audit_artifact']);save(G.REGISTRY,r)
def bind(p,gid,text,scope):
    r=G.load(G.REGISTRY);assert not any(x['governance_id']==gid for x in r['entries'])
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=scope,authority='Explicit current owner two-phase instruction dated 2026-10-04',decision_date='2026-10-04',effective_date='2026-10-04',state='active',controlling_artifacts=[dict(path=p,sha256=G.file_hash(p),binding_pointers=['/'])],binding_requirement=text,required_actions=[text],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded owner task'))
    save(G.REGISTRY,r)
def refresh(task):
    p=prefix(task);r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']!='active':continue
        for a in row['controlling_artifacts']:
            if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r);r=G.registry();registered={a['path'] for x in r['entries'] for a in x['controlling_artifacts']}
    files=[x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/p).rglob('*') if x.is_file() and x.name!='implementation.json' and x.relative_to(G.ROOT).as_posix() not in registered]
    # Earlier contracts remain immutable historical evidence when authority changes.
    audit(files+[SCRIPT,'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1'])
    old=list((G.ROOT/p).glob('contract-v*.json'));n=max([int(x.stem.split('-v')[1]) for x in old],default=0)+1
    cpath=p+f'contract-v{n}.json'
    versions=list((G.ROOT/p).glob('population-v*.json'))
    poppath=max(versions,key=lambda x:int(x.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if versions else p+'population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',poppath,'--output',cpath],check=True,stdout=subprocess.DEVNULL)
    c=G.load(cpath);assert not c['conflicts'],c['conflicts']
    plan=G.load(p+'implementation.json') if (G.ROOT/(p+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=G.load(p+'population.json')['operation_classes'],events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for rule in row.get('constraints',[]):subjects.setdefault(rule['subject'],{})[rule['field']]=rule['equals']
    plan.update(contract=cpath,contract_sha256=G.file_hash(cpath),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    if (G.ROOT/(p+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=p+'receipt.json',sha256=G.file_hash(p+'receipt.json'))] for gid in c['governance_ids']}
    save(p+'implementation.json',plan)
    active=dict(population=poppath,contract=cpath,contract_sha256=G.file_hash(cpath),implementation=p+'implementation.json',state='in_progress')
    if (G.ROOT/(p+'supersession.json')).exists():active['supersession_proposals_path']=p+'supersession.json'
    save(G.ACTIVE_TASK,active)
    print(cpath,len(c['governance_ids']),'rules',json.dumps(c['unresolved_gates']))
def event(task,op,ids,text,evidence):
    p=prefix(task);v=G.load(p+'implementation.json');v['events'].append(dict(operation=op,candidate_ids=ids,governance_ids=v['respected_governance_ids'],action='implements',summary=text,evidence=evidence));save(p+'implementation.json',v)
def artifacts(task):
    p=prefix(task)
    names=['population.json','authority.json','supersession.json','starting-state.json','prior-records.json','implementation.json','progress.json','receipt.json','source-verification.json','public-verification.json','r2-before.json','r2-after.json','upload-intent.json','upload-result.json','validation.log','queue.json','integration.json','review.json','source-identities.json','external-checks.json','rendered-checks.json','preview.json','pr-body.md','remote-final.json','record-updates.json','download.py','archive.ps1','publish.py','inspect.py','render.json']
    return [p+n for n in names]+[p+f'contract-v{i}.json' for i in range(1,101)]+[p+f'evidence-{i}.json' for i in range(1,101)]+[SCRIPT,G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/ordinary-queue-current.json','project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1']
def stage(task,base):
    v=G.load('project-state/workflow-stage-lifecycle.json');v['stages'][-1]['end_commit']=base
    v['stages'].append(dict(id=task,baseline_commit=base,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='OwnerResources20261004',function='guard')));save('project-state/workflow-stage-lifecycle.json',v)
def freeze_a():
    p=prefix(A);assert G.git('rev-parse','HEAD')==BASE
    pop=dict(task_id=A,baseline_commit=BASE,candidate_ids=[SUN],families=[],pages=[],operation_classes=['archive','inventory_disposition','governance_implementation','background_integration','external_mutation'],artifact_paths=artifacts(A),archive_objects=[dict(candidate_id=SUN,r2_key=KEY,sha256=SHA,size_bytes=280024902)])
    G.write_once(p+'population.json',pop)
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',p+'population.json','--output',p+'contract-v1.json'],check=True)
    c=G.load(p+'contract-v1.json');G.freshness(c,G.population(pop),G.registry(),G.file_hash(G.REGISTRY))
    print('INITIAL GOVERNING REQUIREMENTS')
    for x in c['resolved_rules']:print(x['governance_id'],x['binding_requirement'])
def authorize_a():
    p=prefix(A);c=G.load(p+'contract-v1.json');G.freshness(c,G.population(G.load(p+'population.json')),G.registry(),G.file_hash(G.REGISTRY))
    text='Authorize archive of ONLY src-1f9cf39555e7be6f exact canonical official printing original: '+SOURCE+'; 280024902 bytes;601 pages;SHA256 '+SHA+'. Explicitly supersede this object\'s archive-size/authorization hold. Standing150000000-byte object policy and13000000000-byte project ceiling remain unchanged for all other objects. Use canonical absent key '+KEY+'; upload unchanged original, no overwrite/deletion, complete public GET exact byte/hash verification. Preserve settled scope/quality and all historical evidence. Phase A is background-only and must be integrated into main before Phase B. No visitor-visible Phase A changes.'
    G.write_once(p+'authority.json',dict(authority='Explicit current owner decision',candidate_id=SUN,source_url=SOURCE,size_bytes=280024902,page_count=601,sha256=SHA,r2_key=KEY,instruction=text))
    gid='owner-'+A;bind(p+'authority.json',gid,text,dict(candidate_ids=[SUN],task_ids=[A]))
    r=G.load(G.REGISTRY);oldid='decision-source-hold-resolution-2026-10-04-'+SUN;old=next(x for x in r['entries'] if x['governance_id']==oldid);assert old['state']=='active'
    proposal=dict(authorized=True,existing_governance_id=oldid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=p+'authority.json',proposed_replacement=text,consequences='Exact original archive hold released; no standing policy change, derivative or duplicate publication.',authorization_artifact=p+'authority.json')
    proposals={oldid:proposal}
    old.update(state='superseded',superseded_by=gid,supersession_evidence=p+'supersession.json');save(G.REGISTRY,r)
    # Earlier population authorities continue to govern other records. Release
    # only their no-R2/no-new-task restriction for this current exact object.
    for earlier in ['owner-source-hold-resolution-2026-10-04','owner-remaining-approved-review-2026-10-03-integration-exception']:
        r=G.load(G.REGISTRY);old=next(x for x in r['entries'] if x['governance_id']==earlier)
        replacement=earlier+'-sunport-exact-owner-exception'
        requirement=old['binding_requirement']+' Explicit current owner supersession ONLY for src-1f9cf39555e7be6f: '+text+' Subsequent Phase B may update the one existing Sunport entry to that verified archive under a separately frozen publication contract. All historical task boundaries and all other records remain preserved.'
        proposals[earlier]=dict(authorized=True,existing_governance_id=earlier,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=p+'authority.json',proposed_replacement=requirement,consequences='Release only the current exact Sunport original archival and subsequent one-entry publication action; preserve prior tasks and other records.',authorization_artifact=p+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=replacement,title=replacement,binding_requirement=requirement,required_actions=[requirement],controlling_artifacts=[dict(path=p+'authority.json',sha256=G.file_hash(p+'authority.json'),binding_pointers=['/'])])
        old.update(state='superseded',superseded_by=replacement,supersession_evidence=p+'supersession.json');r['entries'].append(new);save(G.REGISTRY,r)
    G.write_once(p+'supersession.json',dict(proposals=proposals))
    bind(p+'supersession.json','supersession-'+A,'Apply the explicit exact-object owner exception while preserving all earlier source, identity and substantive review evidence.',dict(task_ids=[A]))
    inv=G.load('project-state/master-inventory.json');row=next(x for x in inv['candidates'] if x['id']==SUN)
    G.write_once(p+'prior-records.json',dict(records=[row]))
    G.write_once(p+'starting-state.json',dict(baseline_commit=BASE,remote_refs={'main':BASE,'chatgpt/planning-snapshot':BASE},queue={'approved':7,'pending':363},r2={'object_count':1611,'total_bytes':10691241695},standing_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),content_tree=G.git('rev-parse',BASE+':content'),instruction_files={'AGENTS.md':G.file_hash('AGENTS.md'),'scripts/README.md':G.file_hash('scripts/README.md'),'scripts/upload-r2-document.ps1':G.file_hash('scripts/upload-r2-document.ps1')}))
    stage(A,BASE)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=runner.read_text(encoding='utf-8');t='& python "$PSScriptRoot/OwnerResources20261004.py" guard\nif ($LASTEXITCODE) { throw \'Owner resources exact-delta guard failed.\' }\n'+t;runner.write_text(t,encoding='utf-8',newline='\n')
    save(p+'progress.json',dict(state='authorized_archive_ready',remaining=['fresh_official_download','absent_key','upload','full_public_get','inventory','validation','main_integration']))
    refresh(A);G.active_check('mutation','archive',[SUN],r2_key=KEY,source_sha256=SHA)
def guard():
    stages=G.load('project-state/workflow-stage-lifecycle.json')['stages']
    for task in [A,B]:
        if not any(s['id']==task for s in stages):continue
        s=StageSnapshot(task);p=prefix(task)
        poppath=s.load_json(G.ACTIVE_TASK)['population']
        pop=s.load_json(poppath);base=pop['baseline_commit']
        before=json.loads(git('show',base+':project-state/master-inventory.json'));after=s.load_json('project-state/master-inventory.json')
        a={r['id']:r for r in before['candidates']};b={r['id']:r for r in after['candidates']}
        assert set(a)<=set(b) and (set(b)-set(a))<=set(pop['candidate_ids'])
        assert {i for i in a if a[i]!=b[i]}<=set(pop['candidate_ids'])
        old=a[SUN];new=b[SUN]
        assert new['scope_assessment']==old['scope_assessment'] and new['quality_assessment']==old['quality_assessment']
        changed=set(git('diff',base,s.end or 'HEAD','--name-only').decode().splitlines())
        if not s.end:changed=set(G.changed_paths(base))
        assert changed<=set(pop['artifact_paths']+pop['pages']),changed-set(pop['artifact_paths']+pop['pages'])
        if task==A:
            s.assert_no_visible_changes(base,G.git('rev-parse',base+':content'))
            assert G.file_hash('project-state/r2-storage-policy.json')==s.load_json(p+'starting-state.json')['standing_policy_sha256']
            prior=json.loads(git('show',base+':project-state/r2-inventory.json'));current=s.load_json('project-state/r2-inventory.json')
            akeys={x['key']:x for x in prior['objects']};bkeys={x['key']:x for x in current['objects']}
            assert set(akeys)<=set(bkeys) and set(bkeys)-set(akeys)<={KEY}
            assert all(akeys[k]==bkeys[k] for k in akeys),'Existing R2 object metadata changed'
            if KEY in bkeys:
                assert bkeys[KEY]['size_bytes']==280024902 and current['object_count']==1612 and current['total_bytes']==10971266597
                public=s.load_json(p+'public-verification.json')
                assert public['byte_identical'] and public['size_bytes']==280024902 and public['checksum_sha256']==SHA
        else:
            assert s.read_bytes('project-state/r2-inventory.json').replace(b'\r\n',b'\n')==git('show',base+':project-state/r2-inventory.json').replace(b'\r\n',b'\n')
    print('Owner resources frozen population / settled Sunport reviews / stage visible and R2 boundaries passed')
def finish_a():
    p=prefix(A);source=G.load(p+'source-verification.json');public=G.load(p+'public-verification.json')
    assert source['size_bytes']==public['size_bytes']==280024902 and source['sha256']==public['checksum_sha256']==SHA and public['byte_identical']
    before=G.load(p+'r2-before.json');after=G.load(p+'r2-after.json');a={x['key']:x for x in before['objects']};b={x['key']:x for x in after['objects']}
    assert set(b)-set(a)=={KEY} and set(a)-set(b)==set() and all(a[k]==b[k] for k in a)
    assert after['object_count']==1612 and after['total_bytes']==10971266597 and b[KEY]['size_bytes']==280024902
    old=G.load(p+'prior-records.json')['records'][0]
    changes=dict(r2_url='https://files.abqinfo.com/'+KEY,r2_key=KEY,r2_etag=b[KEY]['etag'],r2_last_modified=b[KEY]['last_modified'],size_bytes=280024902,checksum_sha256=SHA,local_path=source['local_path'],provenance_status='Exact official City printing original archived unchanged; complete public GET matches approved bytes/hash.',validation_status='Archive public bytes verified; existing-entry publication remains Phase B.',processing_notes=old['processing_notes']+['2026-10-04 owner exact-object exception releases archive-size hold ONLY for this601-page printing original. Unchanged280024902 bytes;SHA256 '+SHA+';public GET verified. Evidence: '+p+'authority.json;'+p+'public-verification.json. No visible Phase A change.'])
    save(p+'record-updates.json',[dict(id=SUN,changes=changes)])
    refresh(A);G.active_check('mutation','inventory_disposition',[SUN])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',p+'record-updates.json'],check=True)
    save('project-state/r2-inventory.json',after)
    pointer=G.load('project-state/ordinary-queue-current.json');q=copy.deepcopy(G.load(pointer['artifact']))
    q['artifact_type']='sunport_exact_archive_queue';q['recorded_at']=now();q['inventory_sha256']=G.file_hash('project-state/master-inventory.json')
    for x in q.get('newly_approved_backlog',[]):
        if x['id']==SUN:x['reason']='Exact owner-authorized original archived and public bytes verified. Update one existing Sunport entry in Phase B; no duplicate addition.'
    q['sunport_archive']=dict(receipt=p+'receipt.json',r2_key=KEY,public_verified=True)
    save(p+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=p+'queue.json',task=A))
    receipt=dict(task_id=A,state='archive_complete_validation_pending',authority=p+'authority.json',supersession=p+'supersession.json',source_verification=p+'source-verification.json',public_verification=p+'public-verification.json',r2_key=KEY,size_bytes=280024902,sha256=SHA,public_get_byte_identical=True,r2_objects=1612,r2_bytes=10971266597,added_objects=1,added_bytes=280024902,deleted_objects=0,overwritten_objects=0,standing_object_limit=150000000,project_ceiling=13000000000,remaining_project_bytes=2028733403,visitor_visible_changes=0,settled_scope_quality_preserved=True,queue=dict(approved=7,pending=363),normal_validation='pending')
    save(p+'receipt.json',receipt);save(p+'progress.json',dict(state='archive_verified_inventory_saved',remaining=['full_validation','main_integration']))
    event(A,'archive',[SUN],'Exact official original uploaded under owner exception; absent-key and full public GET verified.',p+'public-verification.json')
    event(A,'inventory_disposition',[SUN],'Archive metadata saved; approved status and substantive reviews preserved.',p+'record-updates.json')
    f=G.ROOT/'project-state/CURRENT.md';t=f.read_text(encoding='utf-8');links=t[t.index('[Interactive review]'):]
    f.write_text('# Current project state\n\nSunport exact original archived under the owner\'s single-object exception:280024902 bytes,601 pages, complete public GET verified. R2:1612 objects /10971266597 bytes; standing object ceiling150000000 and project ceiling13000000000 unchanged. Queue:7 approved /363 pending. Phase A full validation and background main integration pending; Phase B authorized for six reviewed live resources, one Sunport archive-link update and two owner-supplied links. No visible Phase A changes.\n\n[Sunport archive](governance/'+A+'/receipt.json) · '+links,encoding='utf-8',newline='\n')
    refresh(A);G.active_check('final');guard()
if __name__=='__main__':
    command=sys.argv[1] if len(sys.argv)>1 else 'guard'
    if command=='refresh':refresh(sys.argv[2])
    else:{'freeze-a':freeze_a,'authorize-a':authorize_a,'finish-a':finish_a,'guard':guard}[command]()
