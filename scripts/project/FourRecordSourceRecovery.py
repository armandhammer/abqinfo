"""Exact four-record recovery; source evidence only unless a governed inventory update is recorded."""
import copy, gzip, hashlib, json, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
import Progress2004Recovery as Prior
TASK='four-record-source-recovery-2026-10-10'
P='project-state/governance/'+TASK+'/'
BASE='d63f04918d2437de176a4cbeb30d4a59c4348eb2'
REMOTE='349a6ca93a5df42fa8a332deb16f93ffb58d5580'
IDS=['lin-2f6fbe4ffb0b6564','lin-7bdbcdc09efe2035','src-158f843cc102a40f','src-352d880cb11386d3']
SCRIPT='scripts/project/FourRecordSourceRecovery.py'
RUNNER='scripts/project/Invoke-ProjectValidation.ps1'
OPS=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration']
def now():return datetime.now(timezone.utc).isoformat()
def rows():
    out=[]
    for i in IDS:Prior.ID=i;out.append(Prior.target())
    return out
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','starting-state.json','implementation.json','progress.json','receipt.json','summary.md','validation.log','prior-research.json','research-journal.json','accounting.json','supersession.json','integration-intent.json','remote-final.json','governance-review.json','updates.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,61)]+[P+f'evidence-{i}.{ext}' for i in range(1,161) for ext in ['json','gz','txt','png','pdf']]
    paths += [SCRIPT,RUNNER,G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md',P+'queue.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=['content/city-data/city-progress-surveys.md'],operation_classes=OPS,artifact_paths=paths))
    protected=['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']
    priorpaths=G.git('ls-files','project-state/governance/progress-2004-source-recovery-2026-10-09','project-state/governance/progress-2004-remote-checkpoint-2026-10-10').splitlines()
    G.write_once(P+'starting-state.json',dict(observed_at=now(),selected_records=rows(),baseline_commit=BASE,remote_refs={'main':REMOTE,'chatgpt/planning-snapshot':REMOTE,'codex/progress-2004-source-recovery-2026-10-10':BASE},protected_sha256={x:G.file_hash(x) for x in protected},prior_recovery_sha256={x:G.file_hash(x) for x in priorpaths},content_tree=G.git('rev-parse',BASE+':content'),queue_pointer=G.load('project-state/ordinary-queue-current.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    c=G.load(P+'contract-v1.json');assert not c['conflicts'],c['conflicts']
    print('Frozen exact four records; initial immutable contract:',P+'contract-v1.json')
def refresh():
    r=G.load(G.REGISTRY)
    actual=(G.ROOT/RUNNER).read_text(encoding='utf-8').strip();base=G.git('show',BASE+':'+RUNNER)
    addition='& python "$PSScriptRoot/FourRecordSourceRecovery.py" guard\nif ($LASTEXITCODE) { throw "Four-record recovery boundary failed" }\n'
    expected=base.replace('Set-StrictMode -Version Latest',addition+'Set-StrictMode -Version Latest',1)
    assert actual in (base,expected)
    if actual==expected:
        a=next(a for x in r['entries'] if x['governance_id']=='policy-durable-task-governance' for a in x['controlling_artifacts'] if a['path']==RUNNER);a['sha256']=G.file_hash(RUNNER);save(G.REGISTRY,r)
    audit([x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/P).glob('*') if x.is_file() and x.name not in ['authority.json','supersession.json','implementation.json']])
    n=max(int(x.stem.split('-v')[1]) for x in (G.ROOT/P).glob('contract-v*.json'))+1;assert n<=60
    path=P+f'contract-v{n}.json';subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='research_in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    ev=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=ev,sha256=G.file_hash(ev))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; gates:',c['unresolved_gates'])
def event(summary,evidence,ids=IDS,op='document_review',action='implements'):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=ids,action=action,use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)
def guard():
    st=StageSnapshot(TASK);v=st.load_json(P+'starting-state.json');pop=st.load_json(P+'population.json');assert pop['candidate_ids']==IDS and pop['baseline_commit']==BASE
    st.assert_no_visible_changes(REMOTE,v['content_tree'])
    for path,h in {**v['protected_sha256'],**v['prior_recovery_sha256']}.items():assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==h,'Protected evidence/state changed: '+path
    changes=set(G.git('diff',BASE,st.end,'--name-only').splitlines()) if st.end else set(G.changed_paths(BASE));assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    print('PASS exact four-record recovery: prior evidence, inventory, queues, R2 and visitor-visible state unchanged')
def get(url,label,ids=IDS,body=None):
    G.active_check('mutation','document_review',ids)
    n=max([int(x.stem.split('-')[1]) for x in (G.ROOT/P).glob('evidence-*.json')],default=0)+1
    rec=dict(requested_url=url,label=label,candidate_ids=ids,requested_at=now(),method=('POST read-only query' if body else 'GET'),query_body=body,state='request_intent');save(P+f'evidence-{n}.json',rec)
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,headers={'User-Agent':'Mozilla/5.0 (ABQInfo public source recovery)',**({'Content-Type':'application/json'} if body else {})})
        try:resp=urllib.request.urlopen(req,timeout=25)
        except urllib.error.HTTPError as e:resp=e
        with resp:data=resp.read(150000001);rec.update(final_url=resp.geturl(),http_status=resp.status,content_type=resp.headers.get('Content-Type'))
        assert len(data)<=150000000
        (G.ROOT/(P+f'evidence-{n}.gz')).write_bytes(gzip.compress(data,mtime=0))
        scratch=G.ROOT/'research/staging'/TASK;scratch.mkdir(parents=True,exist_ok=True);(scratch/f'{n}.bin').write_bytes(data)
        rec.update(state='response_saved',size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),preserved_response=P+f'evidence-{n}.gz',pdf_header=data.startswith(b'%PDF-'))
    except Exception as e:rec.update(state='request_failed',error=str(e))
    save(P+f'evidence-{n}.json',rec)
    print(json.dumps(rec));return rec
if __name__=='__main__':
    if sys.argv[1]=='get':get(sys.argv[2],sys.argv[3],sys.argv[4:] or IDS)
    else:globals()[sys.argv[1]]()
