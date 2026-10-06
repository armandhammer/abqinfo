"""One owner-merged historical entry: rendered production and background closeout."""
import copy,gzip,hashlib,json,subprocess,sys,uuid,time
from datetime import datetime,timezone
import TaskGovernance as G
from PgsLegislativeResolution import save,audit
from WorkflowStageLifecycle import StageSnapshot,canonical_bytes,git
from Pr208209Reconciliation import presentation

TASK='pr213-postmerge-closeout-2026-10-06'
P='project-state/governance/'+TASK+'/'
MERGE='3b0aa243e29d5d8c6ae1c91fce92b7eb35f9f555'
REVIEWED='6b6fad42764e248fb2f7eb328443c4665a008f87'
ID='src-4cb190564a688d42'
PAGE='content/transportation/bicycling/bike-plans.md'
ROUTE='transportation/bicycling/bike-plans/'
ANCHOR='related-bicycle-policy'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
OLD='project-state/governance/bike-boulevard-lifecycle-correction-2026-10-05/'
FAMILY='project-state/governance/council-finality-resolution-2026-10-05/'
SCRIPT='scripts/project/Pr213PostMergeCloseout.py'
OPS=['governance_implementation','inventory_disposition','background_integration']

def now():return datetime.now(timezone.utc).isoformat()

def refresh():
    registry=G.load(G.REGISTRY)
    for row in registry['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,registry)
    registered={a['path'] for r in registry['entries'] for a in r['controlling_artifacts']}
    paths=[p for p in G.changed_paths(MERGE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],P+'implementation.json'}]
    audit(paths)
    versions=list((G.ROOT/P).glob('contract-v*.json'));n=max(int(p.stem.split('-v')[1]) for p in versions)+1;assert n<=40
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population-v4.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates']
    plan=G.load(P+'implementation.json');subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,actions=OPS)
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'production-verification.json' if (G.ROOT/(P+'production-verification.json')).exists() else 'starting-state.json')
    plan['completion_evidence']={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population-v4.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules')

def event(op,summary,evidence):
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',plan)

def setup():
    assert G.git('rev-parse','HEAD')==MERGE
    pop=G.load(P+'population-v3.json');pop['operation_classes']=OPS
    outputs=['population-v4.json','execution-authority.json','supersession.json','starting-state.json','progress.json','merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates.json','queue.json','accounting.json','validation.log','receipt.json','integration-intent.json']+[f'contract-v{i}.json' for i in range(6,41)]+['page-'+label+'.html.gz' for label in ['production','merge','preview']]
    pop['artifact_paths'] += [P+x for x in outputs]+[SCRIPT,'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    pop['artifact_paths']=sorted(set(pop['artifact_paths']));G.write_once(P+'population-v4.json',pop)
    instruction='Explicit owner PR213 post-merge instruction and explicit Chrome/Playwright authorization: resume exact '+ID+' closeout. Verify owner merge '+MERGE+' / reviewed '+REVIEWED+', full preview/merge/production article and rendered canonical production section, historical title/qualification, original archive and both official links, anchor and layout. Only after conclusive production: mark exactly this already-implemented record validated/passed, preserve all Council finality and PR213 evidence, remove stale open/unmerged state, regenerate accounting and complete background-only main/planning synchronization. Full normal validation, sealed history, Hugo/rendered, CURRENT/checkpoint, governance/freshness and diff checks required. No new population, editorial decision, visitor-visible edit, source/archive or R2 mutation. This releases only the pending browser/initial-evidence and former PR-head synchronization phase restrictions; no new content merge authority.'
    G.write_once(P+'execution-authority.json',dict(authority='Explicit current owner post-merge instruction and Chrome/Playwright authorization',instruction=instruction,candidate_ids=[ID],merge_sha=MERGE,reviewed_head=REVIEWED))
    registry=G.registry();proposals={}
    for old in registry['entries'][:]:
        if old['governance_id'] not in ['owner-'+TASK,'owner-bike-boulevard-lifecycle-correction-2026-10-05']:continue
        gid=old['governance_id']+'-postmerge-lifecycle-authorized'
        requirement=old['binding_requirement']+' Explicit current owner exception in '+P+'execution-authority.json supersedes only the initial pending-evidence/browser restriction and former open-PR/PR-head synchronization boundary for '+ID+'. After conclusively verified production, exact one-record validated lifecycle and background-only main/planning reconciliation are authorized. Preserve all finality, source, original bytes, separate-map and historical-content findings. No new editorial, visitor-visible, R2 or other-record changes.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'execution-authority.json',proposed_replacement=requirement,consequences='Exactly one owner-merged record validated after production; reconcile durable background state and refs, no new content or storage.',authorization_artifact=P+'execution-authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=requirement,required_actions=[requirement],authority='Explicit current owner post-merge lifecycle and browser authorization',effective_date='2026-10-06')
        new['controlling_artifacts'].append(dict(path=P+'execution-authority.json',sha256=G.file_hash(P+'execution-authority.json'),binding_pointers=['/']))
        # The replacement retains substantive prohibitions, while releasing the
        # explicitly temporary pre-verification phase boundary.
        new['prohibited_actions']=['No visitor-visible, source/archive, R2 or unrelated record change. No integration before conclusive production verification.']
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');registry['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals));save(G.REGISTRY,registry)
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD,FAMILY).decode().splitlines()
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    assert row['status']=='implemented' and row['validation_status']=='passed'
    protected=history+['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/discovery/retained-source-audit-queue.json']
    # Earlier failed-browser evidence remains an immutable historical witness.
    protected += [p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.name in ['production-verification-incomplete.json','remote-state.json','read-only-content-evidence.json','production.html.gz','merge.html.gz','preview.html.gz']]
    G.write_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,content_tree_oid=G.git('rev-parse',MERGE+':content'),selected_row=row,protected_sha256={p:G.file_hash(p) for p in protected}))
    stages=G.load('project-state/workflow-stage-lifecycle.json');assert stages['stages'][-1]['id']=='bike-boulevard-lifecycle-correction-2026-10-05'
    stages['stages'][-1]['end_commit']=MERGE;stages['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr213PostMergeCloseout',function='guard')));save('project-state/workflow-stage-lifecycle.json',stages)
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=f.read_text(encoding='utf8');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr213PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR213 closeout exact-delta guard failed.\' }\nSet-StrictMode -Version Latest',1)
    s=s.replace('$broken = @()','& python "$PSScriptRoot/Pr213PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw \'PR213 production/Hugo parity failed.\' }\n$broken = @()',1);f.write_text(s,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='authorized_playwright_production_verification_pending',remaining=['rendered production','exact archive GET','one-record lifecycle reconciliation','full validation','background integration'],no_new_population=True))
    refresh();G.active_check('mutation','governance_implementation',[ID]);guard()

JS=r"""() => { const h=document.getElementById('related-bicycle-policy');if(!h)return {missing:true};const title=h.cloneNode(true);title.querySelectorAll('a.anchor').forEach(a=>a.remove());const nodes=[];let n=h.nextElementSibling;while(n&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}return {heading:title.textContent.trim(),anchor:h.id,heading_tag:h.tagName,text:nodes.map(n=>n.innerText).join('\n'),links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth}; }"""

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    G.active_check('mutation','governance_implementation',[ID])
    pr=json.loads(subprocess.check_output(['gh','pr','view','213','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'));assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'));check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages');assert check['conclusion']=='success' and check['head_sha']==MERGE
    deployment='https://'+check['external_id'][:8]+'.abqinfo.pages.dev/'
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    assert not G.git('diff','2ea0fb772cec9bd8c15da4bee1120af561620c76',MERGE,'--name-only','--','content','layouts','assets','static','hugo.toml')
    if not (G.ROOT/(P+'merge-verification.json')).exists():
        G.write_once(P+'merge-verification.json',dict(pr=pr,cloudflare_check=check,merge_deployment=deployment,reviewed_merge_trees_identical=True))
    else:
        saved=G.load(P+'merge-verification.json');assert saved['pr']['mergeCommit']['oid']==MERGE and saved['merge_deployment']==deployment
    urls=dict(production='https://abqinfo.com/'+ROUTE,merge=deployment+ROUTE,preview='https://41cb1e3d.abqinfo.pages.dev/'+ROUTE)
    values={};witnesses=[]
    for label,url in urls.items():
        r=requests.get(url+'?pr213_verify='+uuid.uuid4().hex,headers={'Cache-Control':'no-cache, no-store, max-age=0'},timeout=90);r.raise_for_status();value,_=presentation(r.content);values[label]=value;path=P+'page-'+label+'.html.gz';(G.ROOT/path).write_bytes(gzip.compress(r.content,mtime=0));witnesses.append(dict(label=label,url=r.url,status=r.status_code,witness=path,sha256=hashlib.sha256(r.content).hexdigest(),article_sha256=G.digest(value),observed_at=now()))
    assert values['production']==values['merge']==values['preview'],'HTTP production/merge/preview article mismatch'
    old=G.load(OLD+'preview.json');row=G.load(P+'starting-state.json')['selected_row'];expected_links=[row['r2_url'],row['direct_file_url'],row['source_url']]
    rendered={}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu']);page=browser.new_page(viewport=dict(width=1440,height=1100))
        for attempt in range(3):
            response=page.goto(PROD,wait_until='networkidle',timeout=90000);assert response.status==200
            result=page.evaluate(JS)
            if old['text']==result.get('text') and old['links']==result.get('links'):break
            if attempt<2:time.sleep(15);page.reload(wait_until='networkidle')
        assert old['text']==result.get('text') and old['links']==result.get('links'),'Canonical production still differs after bounded retries'
        canonical=dict(url=page.url,status=response.status,section=result,observed_at=now());assert page.url.startswith('https://abqinfo.com/')
        for label,url in urls.items():
            response=page.goto(url+'?pr213_chrome='+uuid.uuid4().hex+'#'+ANCHOR,wait_until='networkidle',timeout=90000);assert response.status==200
            result=page.evaluate(JS);assert result['heading']=='Related Bicycle Policy' and result['anchor']==ANCHOR and result['heading_tag']=='H2' and not result['overflow']
            assert result['text']==old['text'] and result['links']==old['links'];assert [x['url'] for x in result['links']]==expected_links
            page.locator('#'+ANCHOR).scroll_into_view_if_needed();rendered[label]=result
            if label=='production':page.screenshot(path=str(G.ROOT/(P+'production.png')))
        page.set_viewport_size(dict(width=390,height=844));page.goto(PROD,wait_until='networkidle',timeout=90000);mobile=page.evaluate(JS);assert not mobile['overflow'] and mobile['text']==old['text'];page.locator('#'+ANCHOR).scroll_into_view_if_needed();page.screenshot(path=str(G.ROOT/(P+'mobile.png')));browser.close()
    assert rendered['production']==rendered['merge']==rendered['preview']
    G.write_once(P+'production-render.json',dict(browser='Installed Google Chrome via explicitly owner-authorized Playwright',canonical_production=canonical,desktop=rendered,mobile=mobile,observed_at=now(),section_parity=True,layout_overflow=False))
    G.write_once(P+'production-verification.json',dict(result='passed',merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,merge_deployment=deployment,reviewed_preview=urls['preview']+'#'+ANCHOR,canonical_rendered_production_verified=True,full_article_parity=True,article_sha256=G.digest(values['production']),title=G.load(OLD+'receipt.json')['visible_title'],historical_current_law_qualification=True,required_links=expected_links,desktop_mobile_layout_passed=True,witnesses=witnesses,rendering=P+'production-render.json',screenshots=[P+'production.png',P+'mobile.png']))
    # Read-only downloads: preserve the one archive and prove the two official
    # destinations still work. No source or object mutation is performed.
    results=[]
    for url in expected_links:
        r=requests.get(url,timeout=90);r.raise_for_status();ev=dict(url=url,status=r.status_code,size_bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),observed_at=now())
        if url==row['r2_url']:assert ev['size_bytes']==row['size_bytes'] and ev['sha256']==row['checksum_sha256'];ev['exact_public_original']=True
        if url==row['direct_file_url']:assert ev['sha256']==G.load(FAMILY+'evidence-21.json')['sha256'];ev['exact_reviewed_official_final']=True
        results.append(ev)
    G.write_once(P+'archive-verification.json',dict(result='passed',results=results,r2_delta=dict(added=0,deleted=0,overwritten=0,bytes=0)))
    event('governance_implementation','Canonical production rendered in Chrome; full article/section parity with exact merge deployment and reviewed preview, three links/anchor and desktop/mobile layout pass; exact original full GET and official sources verified.',P+'production-verification.json')
    save(P+'progress.json',dict(state='production_verified_lifecycle_pending',remaining=['one-record lifecycle reconciliation','full validation','background integration'],no_new_population=True));refresh();G.active_check('final');guard()

def reconcile():
    assert G.load(P+'production-verification.json')['result']=='passed' and G.load(P+'archive-verification.json')['result']=='passed'
    G.active_check('mutation','inventory_disposition',[ID]);row=G.load(P+'starting-state.json')['selected_row']
    updates=[dict(id=ID,changes=dict(status='validated',validation_status='passed',processing_notes=row['processing_notes']+['PR213 owner merge '+MERGE+' conclusively verified at '+PROD+' in explicitly authorized Chrome/Playwright, with reviewed preview and merge-deployment article/section parity, exact original R2 public bytes and both official links. Publication lifecycle now live/validated; all settled Council finality and historical evidence preserved. Evidence: '+P+'production-verification.json.']))]
    if (G.ROOT/(P+'record-updates.json')).exists():assert G.load(P+'record-updates.json')==updates
    else:G.write_once(P+'record-updates.json',updates)
    refresh()
    live=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    if any(live.get(k)!=v for k,v in updates[0]['changes'].items()):
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    inv=G.load('project-state/master-inventory.json');pointer=json.loads(git('show',MERGE+':project-state/ordinary-queue-current.json'));q=copy.deepcopy(G.load(pointer['artifact']))
    q.update(artifact_type='pr213_postmerge_closeout_queue',recorded_at=inv['generated_at'],source_queue_artifact=pointer['artifact'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),in_progress_publication=None)
    assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,340,321,19)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],completed_item_range='PR213 owner-merged existing historical bike-boulevard correction verified live; exactly one implemented record validated/passed. No visible/R2 delta.',remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),resume_command='Read CURRENT and PR213 closeout receipt. Production and one-record lifecycle verified; full validation and background main/planning reconciliation pending. No next population authorized.');save('project-state/checkpoint.json',cp)
    refresh();G.active_check('mutation','governance_implementation',[ID])
    # Deterministic regeneration only, without a new family-review operation.
    import importlib.util
    spec=importlib.util.spec_from_file_location('pr213_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    prior_owner=G.load('project-state/discovery/consolidated-human-review-queue.json');owner,report=module.build();assert prior_owner['record_count']==owner['record_count']==0 and prior_owner['packages']==owner['packages']==[]
    save('project-state/discovery/consolidated-human-review-queue.json',owner);(G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').write_text(report,encoding='utf8',newline='\n')
    save(P+'accounting.json',dict(validated_ids=[ID],approved=0,pending=340,governance_gated=321,source_structural_blocked=19,human_review=0,remaining_nonterminal=cp['remaining_nonterminal'],in_progress_publication=None,visitor_visible_delta=0,r2_delta=0))
    f=G.ROOT/'project-state/CURRENT.md';text=f.read_text(encoding='utf8');tail=text[text.index('[Owner correction]'):]
    current='# Current project state\n\nPR #213 owner-merged at '+MERGE+'. Production Bike Plans / Related Bicycle Policy matches reviewed content and merge deployment: F/S R-07-268, enacted R-2007-109, historical/current-law qualification, original archive and two official links, correct anchor and desktop/mobile layout. Exactly src-4cb190564a688d42 validated/passed; correction live. Queue: 0 approved / 340 pending (321 governance-gated / 19 source-structural blocked), 0 human review; no active publication or new population. Exact original R2 public GET verified; zero visitor-visible/R2 delta. Full validation and background main/planning reconciliation pending.\n\n[PR213 closeout](governance/'+TASK+'/accounting.json) · [Production](governance/'+TASK+'/production-verification.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+tail
    f.write_text(current,encoding='utf8',newline='\n');event('inventory_disposition','Conclusive production permits exactly one implemented-to-validated lifecycle; preserved review fields and original notes, regenerated counts/queues and removed stale open-PR state.',P+'accounting.json')
    save(P+'progress.json',dict(state='production_verified_lifecycle_reconciled_validation_pending',remaining=['full validation','background integration'],no_new_population=True));refresh();G.active_check('final');guard()

def guard():
    stages=G.load('project-state/workflow-stage-lifecycle.json')['stages']
    if not any(s['id']==TASK for s in stages):return
    stage=StageSnapshot(TASK);pop=stage.load_json(P+'population-v4.json');start=stage.load_json(P+'starting-state.json')
    assert pop['candidate_ids']==[ID] and pop['baseline_commit']==MERGE
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE));assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    a={r['id']:r for r in json.loads(git('show',MERGE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys();delta={i for i in a if a[i]!=b[i]};assert delta<={ID}
    if delta:
        assert {k for k in a[ID] if a[ID][k]!=b[ID][k]}<={'status','validation_status','processing_notes','updated_at'}
        assert a[ID]['status']=='implemented' and b[ID]['status']=='validated' and b[ID]['validation_status']=='passed'
        assert b[ID]['processing_notes'][:len(a[ID]['processing_notes'])]==a[ID]['processing_notes']
        assert stage.load_json(P+'production-verification.json')['result']=='passed'
    if (G.ROOT/(P+'accounting.json')).exists():
        q=stage.load_json(P+'queue.json');assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,340,321,19) and q['in_progress_publication'] is None
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json');assert receipt['visitor_visible_delta']==receipt['r2_delta']==0 and receipt['validated_ids']==[ID]
        for path,h in receipt['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS: PR213 exact one-record validated lifecycle; all content/R2/source/review history protected')

def render():
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS: sealed PR213 rendered evidence');return
    v=stage.load_json(P+'production-verification.json');body=(G.ROOT/'tmp/site-build'/ROUTE/'index.html').read_bytes();actual,_=presentation(body)
    assert G.digest(actual)==v['article_sha256'];print('PASS: Hugo article text/links/anchors match verified PR213 production/merge/preview')

def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard()
    raw=(G.ROOT/'tmp/pr213-validation.log').read_text(encoding='utf8');assert '"Hugo": "passed"' in raw and '53 contiguous stage intervals' in raw
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    evidence=['merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates.json','queue.json','accounting.json','validation.log']
    G.write_once(P+'integration-intent.json',dict(authority=P+'execution-authority.json',expected_main=MERGE,expected_planning_snapshot=REVIEWED,strategy='Atomic fast-forward main and planning-snapshot to final background closeout commit; no force, visible changes or new population'))
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    G.write_once(P+'receipt.json',dict(task_id=TASK,state='production_verified_lifecycle_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_result='passed',production_url=PROD,validated_ids=[ID],lifecycle=dict(status='validated',validation_status='passed',correction_live=True,owner_merge_verified=True),queue=G.load(P+'accounting.json'),visitor_visible_delta=0,r2_delta=0,normal_validation='passed',owner_decision_required=False,no_new_population=True,evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact production-verified one-record post-merge lifecycle and background reconciliation; preserved all settled finality/quality, original/source bytes, unrelated records and historical evidence.',evidence=[P+'production-verification.json',P+'archive-verification.json',P+'accounting.json']) for r in c['resolved_rules']},integration_intent=P+'integration-intent.json'))
    cp=G.load('project-state/checkpoint.json');cp['resume_command']='PR213 production and background closeout complete; read CURRENT and immutable receipt. Main/planning-snapshot synchronized by the final closeout commit. No active publication, owner decision or next population.';save('project-state/checkpoint.json',cp)
    f=G.ROOT/'project-state/CURRENT.md';s=f.read_text(encoding='utf8').replace('Full validation and background main/planning reconciliation pending.','Full project/governance/sealed-history, Hugo/rendered, CURRENT/checkpoint and diff validation passed. Final background closeout commit synchronizes main and planning-snapshot; no owner action pending.').replace('governance/'+TASK+'/accounting.json','governance/'+TASK+'/receipt.json');f.write_text(s,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='closeout_complete_integration_authorized',remaining=['guarded atomic final ref synchronization'],no_new_population=True));event('background_integration','Full validation passed; production-verified closeout ready for guarded atomic main/planning synchronization.',P+'integration-intent.json');refresh();G.active_check('final');guard()

def integrate():
    refs=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines();d={line.split()[1]:line.split()[0] for line in refs};assert d=={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':REVIEWED}
    assert G.load(P+'receipt.json')['normal_validation']=='passed' and G.load(P+'production-verification.json')['result']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    save(P+'progress.json',dict(state='complete',remaining=[],no_new_population=True,integration='Final commit containing this completed receipt is atomically synchronized to main and planning-snapshot; verify concrete refs independently.'))
    refresh();G.active_check('mutation','background_integration',[ID]);plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active);G.active_check('final');guard()
    paths=[p for p in G.changed_paths(MERGE) if not p.startswith('backups/')];subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--check'],check=True);subprocess.run(['git','commit','-m','Close out PR213 production verification and reconcile lifecycle'],check=True)
    subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],check=True)
    subprocess.run(['git','switch','main'],check=True);subprocess.run(['git','merge','--ff-only','codex/pr213-postmerge-closeout'],check=True);subprocess.run(['git','branch','-f','chatgpt/planning-snapshot','HEAD'],check=True)
    head=G.git('rev-parse','HEAD');refs=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines();assert len(refs)==2 and all(line.split()[0]==head for line in refs);assert not G.git('status','--porcelain')
    save('tmp/pr213-final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=refs,worktree_clean=True,production_url=PROD,validation='passed'));print('Final synchronized main/planning-snapshot:',head)

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
