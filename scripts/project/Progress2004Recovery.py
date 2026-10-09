"""Single-record source recovery with preserved inventory, publication and storage."""
import hashlib, json, re, subprocess, sys, urllib.request, urllib.error, gzip
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from PgsLegislativeResolution import save, audit

TASK='progress-2004-source-recovery-2026-10-09'
P='project-state/governance/'+TASK+'/'
BASE='349a6ca93a5df42fa8a332deb16f93ffb58d5580'
ID='src-352d880cb11386d3'
SCRIPT='scripts/project/Progress2004Recovery.py'
SCRATCH=G.ROOT/'research/staging'/TASK
def now(): return datetime.now(timezone.utc).isoformat()

def target():
    # Stream candidate blocks; parse only the selected record.
    with (G.ROOT/'project-state/master-inventory.json').open(encoding='utf-8-sig') as f:
        block=[]; inside=False
        for line in f:
            if line=='    {\n': block=[line]; inside=True
            elif inside:
                block.append(line)
                if line in ('    },\n','    }\n'):
                    if any(ID in s for s in block):
                        return json.loads(''.join(block).rstrip().rstrip(','))
                    inside=False
    raise ValueError('Selected candidate not found')

def refresh():
    runner='scripts/project/Invoke-ProjectValidation.ps1'
    baseline=G.git('show',BASE+':'+runner)
    expected=baseline.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Progress2004Recovery.py" guard\nif ($LASTEXITCODE) { throw "2004 Progress Report source recovery boundary failed" }\nSet-StrictMode -Version Latest',1)
    actual=(G.ROOT/runner).read_text(encoding='utf-8').strip()
    registry=G.load(G.REGISTRY)
    if actual==expected:
        row=next(r for r in registry['entries'] if r['governance_id']=='policy-durable-task-governance')
        artifact=next(a for a in row['controlling_artifacts'] if a['path']==runner)
        assert artifact['binding_pointers']==['/implementation']
        artifact['sha256']=G.file_hash(runner)
        save(G.REGISTRY,registry)
    else: assert actual==baseline, 'Unexpected validation runner change'
    old=list((G.ROOT/P).glob('contract-v*.json'))
    paths=[p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.is_file() and p.name not in ('authority.json','implementation.json')]
    audit(paths)
    n=max([int(p.stem.split('-v')[1]) for p in old],default=0)+1
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path); assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','governance_implementation'],events=[],status='research_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]): subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    ev=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan['completion_evidence']={gid:[dict(path=ev,sha256=G.file_hash(ev))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
    print(path, len(c['governance_ids']), 'rules', 'gates',c['unresolved_gates'])

def event(summary,evidence,op='document_review'):
    plan=G.load(P+'implementation.json')
    plan['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence))
    save(P+'implementation.json',plan)

def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','starting-state.json','prior-research.json','implementation.json','progress.json','receipt.json','summary.md','validation.log','final-refs.json','searches.json','research-journal.json','browser.json','browser.png','accounting.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,41)]+[P+f'retrieval-{i}.json' for i in range(1,201)]+[P+f'response-{i}.gz' for i in range(1,201)]
    paths += [SCRIPT,'scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK]
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=['content/city-data/city-progress-surveys.md'],operation_classes=['document_review','governance_implementation'],artifact_paths=paths))
    G.write_once(P+'starting-state.json',dict(observed_at=now(),selected_row=target(),refs={x:G.git('rev-parse',x) for x in ['HEAD','origin/main','origin/chatgpt/planning-snapshot']},remote_main=BASE,remote_planning_snapshot=BASE,open_prs=[],content_tree_oid=G.git('rev-parse',BASE+':content'),protected_sha256={p:G.file_hash(p) for p in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']}))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    c=G.load(P+'contract-v1.json'); G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY)); assert not c['conflicts']
    instruction='Recover exactly src-352d880cb11386d3, the 2004 Albuquerque Progress Report, after examining prior research and complete active governance. Investigate authoritative City sources, historical URLs, Internet Archive captures, alternate government repositories and other verifiable paths. Preserve settled dispositions, existing reports and governance. A complete original requires exact identity/date/completeness/authenticity/provenance and scope/quality/series review before any archival or owner-review publication PR; do not merge. If complete original is not recovered, preserve the existing hold and record the specific remaining evidence prerequisite, without substitutes. Run full validation; report outcome, publication/archive status, queues, R2 delta and final refs. This initial contract covers evidence recovery and background governance only; any successful recovery requiring inventory/archive/content operations requires a replacement frozen contract and the existing authorization gates. No external storage or Git ref mutation is authorized by this initial contract.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',candidate_ids=[ID],instruction=instruction))
    r=G.registry();r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Exact 2004 Progress Report source recovery',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-09',effective_date='2026-10-09',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No incomplete, unrelated or unauthenticated substitute; no merge.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='source recovery'))
    save(G.REGISTRY,r);refresh()
    G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json')
    assert life['stages'][-1]['id']=='pr218-postmerge-closeout-2026-10-08'
    life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Progress2004Recovery',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf-8')
    s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Progress2004Recovery.py" guard\nif ($LASTEXITCODE) { throw "2004 Progress Report source recovery boundary failed" }\nSet-StrictMode -Version Latest',1)
    runner.write_text(s,encoding='utf-8',newline='\n')
    event('Exact one-record population and complete active registry resolved; previous completed closeout sealed at verified remote baseline.',P+'starting-state.json','governance_implementation')
    save(P+'progress.json',dict(state='governed_recovery_in_progress',remaining=['new recovery paths','outcome receipt','full validation','local checkpoint'],r2_delta_bytes=0,visitor_visible_delta=0))
    refresh();G.active_check('mutation','document_review',[ID]);guard()

def guard():
    from WorkflowStageLifecycle import StageSnapshot, git, canonical_bytes
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,start['content_tree_oid'])
    for p,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==h,'Protected state changed: '+p
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
    print('2004 recovery exact population guard passed: unchanged inventory, reports, queues and R2')

def retrieve(url,label):
    G.active_check('mutation','document_review',[ID])
    SCRATCH.mkdir(parents=True,exist_ok=True)
    n=max([int(p.stem.split('-')[1]) for p in (G.ROOT/P).glob('retrieval-*.json')],default=0)+1
    receipt=dict(requested_url=url,label=label,requested_at=now(),method='GET',historical_archive_evidence=('archive.org' in url))
    G.write_once(P+f'retrieval-{n}.json',dict(receipt,state='request_intent'))
    data=b''
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo historical source research)'})
        try: resp=urllib.request.urlopen(req,timeout=25)
        except urllib.error.HTTPError as e:resp=e
        with resp:
            receipt.update(final_url=resp.geturl(),http_status=resp.status,content_type=resp.headers.get('Content-Type'),response_headers={k:v for k,v in resp.headers.items() if k.lower()!='set-cookie'})
            data=resp.read(150000001)
        assert len(data)<=150000000
        receipt.update(size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),complete_response=True)
        path=SCRATCH/f'{n}-{label}.bin';path.write_bytes(data);receipt['local_path']=path.relative_to(G.ROOT).as_posix()
        if len(data)<4000000:
            (G.ROOT/(P+f'response-{n}.gz')).write_bytes(gzip.compress(data,mtime=0))
            receipt['preserved_response']=P+f'response-{n}.gz'
        if data.startswith(b'%PDF-'): receipt['pdf_header']=True
    except Exception as e:receipt.update(error=str(e),complete_response=False)
    save(P+f'retrieval-{n}.json',receipt)
    if G.binding_artifact(P+f'retrieval-{n}.json',json.dumps(receipt)):
        refresh()
    print(json.dumps(receipt))
    return receipt

def outcome():
    refresh();G.active_check('mutation','governance_implementation',[ID]);guard()
    q=G.load(G.load('project-state/ordinary-queue-current.json')['artifact'])
    assert ID in q['source_or_structural_blocked_pending_ids']
    counts=dict(approved=q['approved_count'],pending=q['pending_review_count'],gated=q['gated_pending_count'],source_structural_blocked=q['source_or_structural_blocked_pending_count'],actionable=q['genuinely_actionable_ungated_pending_count'],human_review=G.load('project-state/discovery/consolidated-human-review-queue.json')['record_count'],remaining_nonterminal=G.load('project-state/checkpoint.json')['remaining_nonterminal'])
    save(P+'accounting.json',dict(counts,inventory_changed=False,queues_changed=False,r2_objects_added=0,r2_bytes_added=0,visitor_visible_delta=0))
    prerequisite='A complete City-issued 2004 Albuquerque Progress Report PDF or complete original scan, with authoritative custody/source provenance and verified edition, publication date, contents and every page. A multipart recovery would instead require an authenticated original edition manifest/order and every original component, plus demonstrated complete pagination/coverage. Indexed component URLs and three inspected fragments do not establish that prerequisite. No reconstructed or inferred compilation is a substitute.'
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    receipt=dict(task_id=TASK,candidate_ids=[ID],baseline_commit=BASE,observed_at=now(),outcome='complete_original_not_recovered',final_status='pending review',source_recovery_hold='preserved unchanged',remaining_evidence_prerequisite=prerequisite,identity='City hub and archived City landing pages identify the 2004 edition; a complete original with exact publication date and page coverage remains unverified.',publication_decision='No addition; no eligibility/quality approval inferred from fragments. Existing Progress Report series and its settled dispositions preserved.',archive_status='No complete original eligible for archival preparation. Three sampled official/archived component PDFs retained as local research evidence only; no R2 operation.',research_evidence=[P+'prior-research.json',P+'research-journal.json',P+'searches.json',P+'browser.json']+[P+f'retrieval-{i}.json' for i in range(1,30)],limitations=['Archive wildcard requests timed out or returned 503 and availability API returned 429; focused exact and subtree CDX queries succeeded. These failures are not proof of absence.','Obsolete guessed ContentDM route failed and is not a valid catalog no-hit. Current State Library rendered catalog exact-title and exact-publisher searches returned no results; title/year query returned unrelated works. Digital Collections broad full-text results are not an exhaustive negative.','Archived indexes identify component URLs, not a verified complete original; no claim that all components are missing or unrecoverable. No component compilation made.','No City/library inquiry or records request sent. Official Clerk records route recorded as a possible custodian recovery path.'],accounting=counts,r2_delta_bytes=0,r2_delta_objects=0,visitor_visible_delta=0,normal_validation='pending',remote_effects='none',local_checkpoint='Evidence persisted in task directory; initial contract does not authorize Git ref mutation.',governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],result='Exact factual source-recovery task; settled record/page decisions preserved. Whole inventory, queues, R2 policy/inventory and content tree protected by exact baseline guard. No unrelated eligibility, disposition, archive, publication, supersession or owner decision inferred.',evidence=[P+'starting-state.json',P+'prior-research.json',P+'research-journal.json',P+'accounting.json']) for r in c['resolved_rules']})
    save(P+'receipt.json',receipt)
    summary='''# 2004 Albuquerque Progress Report source recovery

Exactly `src-352d880cb11386d3` remains **pending review / source-recovery hold**. No complete original recovered and no publication or archive approval made.

The City hub still names the 2004 edition. Fresh anonymous Chrome and direct retrieval return 404 for its original delivery and UID route. The current 2004 documents folder exposes 56 indicator components. Internet Archive captures preserve the 2005 original City home and 2009/2023 landing pages. Its legacy PDF index identifies 66 component URL keys (10 front matter/appendix components and 56 indicators); the migrated subtree has 136 delivery URL keys, not 136 distinct documents. None of those inspected indexes identifies a single complete original report. Three sampled PDFs were downloaded, hashed, parsed and visually inspected: a report-card explanation, Appendix A and one indicator. They are authentic source components, not a complete edition. No compilation was produced.

Official City folders/search/document host, focused Internet Archive indexes/captures, Archive item catalog, Open Library, current New Mexico State Library rendered catalog and targeted government/university/library web searches did not yield a complete original. Exact State Library title/publisher searches returned no results; broader searches returned unrelated records. Broad archive failures and the digital collection's broad full-text result set limit negative conclusions; this is an outcome of the recorded investigation, not proof that no recoverable original exists anywhere.

The remaining prerequisite is a complete City-issued 2004 original PDF or complete original scan, authoritative provenance/custody, exact edition/date and verified contents/pagination. An original multipart edition would require an authenticated manifest/order, all original files and demonstrated complete coverage. A surviving outline or partial set alone cannot clear the hold. The City Clerk's official records route is recorded for a possible custodian request; none was sent.

Existing reports, all inventory fields/timestamps, queues, R2 state and storage policy remain unchanged. Queue: 0 approved; 333 pending, including 321 gated and 12 source/structural blocked; 0 actionable/human review; 884 remaining nonterminal. R2: 0 objects, 0 bytes. No visitor-visible change, PR, merge, deployment or remote write.

Full normal validation: pending. Final refs and validation results are recorded in the adjacent JSON receipt and log. This exact task is complete when validation passes; further work depends on new complete-original evidence, not a repeat of the failed retrievals.
'''
    (G.ROOT/(P+'summary.md')).write_text(summary,encoding='utf-8',newline='\n')
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8');links=old[old.index('[Owner correction]'):]
    current.write_text('# Current project state\n\nExactly src-352d880cb11386d3 (2004 Albuquerque Progress Report) source recovery finished without a complete original. City/Wayback component evidence preserved; existing pending-review source hold retained unchanged. Remaining prerequisite: authoritative complete 2004 edition with date, contents and every page verified; no inferred compilation. Existing reports and settled decisions preserved. Zero inventory/queue/R2/visitor-visible delta; no PR or remote write. Full normal validation pending; research evidence saved locally.\n\nQueue: 0 approved /333 pending (321 gated /12 source-structural blocked), 0 actionable /human review; remaining nonterminal884. Latest production closeout remains completed PR #218.\n\n[Recovery receipt](governance/'+TASK+'/receipt.json) · [Research](governance/'+TASK+'/summary.md) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links,encoding='utf-8',newline='\n')
    event('Recovery outcome: complete original not recovered. Existing factual hold, reports, queues and R2 preserved; complete-original prerequisite and search limitations recorded.',P+'receipt.json','governance_implementation')
    save(P+'progress.json',dict(state='recovery_complete_validation_pending',remaining=['full normal validation','final ref verification'],r2_delta_bytes=0,visitor_visible_delta=0))
    refresh();G.active_check('final');guard()

if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='refresh':refresh()
    elif sys.argv[1]=='guard':guard()
    elif sys.argv[1]=='get':retrieve(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='outcome':outcome()
