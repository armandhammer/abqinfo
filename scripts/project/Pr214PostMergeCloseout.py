"""Exact PR214 production verification and background lifecycle reconciliation."""
import copy, gzip, hashlib, json, subprocess, sys, uuid
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git
from Pr208209Reconciliation import presentation

TASK='pr214-postmerge-closeout-2026-10-06'
P='project-state/governance/'+TASK+'/'
MERGE='e503ca2074675f653524e26002e5abf672d87016'
REVIEWED='a32091a748771fbe581f31fad39684b4575517c1'
PLANNING='0c4568484e19115a28a3258cc3b68eef821d8005'
ID='src-2f89e1bc040e1d33'
OLD='project-state/governance/mcduffie-review-2026-10-06/'
SOURCE='project-state/governance/mcduffie-source-recovery-2026-10-06/'
SCRIPT='scripts/project/Pr214PostMergeCloseout.py'
PAGE='content/transportation/roadway-projects/studies.md'
ROUTE='transportation/roadway-projects/studies/'
ANCHOR='mcduffie-twin-parks'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
KEY='transportation/roadway-projects/studies/cabq-mcduffie-twin-parks-final-traffic-calming-study-2024.pdf'
SHA='48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15'
OPS=['governance_implementation','inventory_disposition','background_integration']

def now():return datetime.now(timezone.utc).isoformat()

def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([p for p in G.changed_paths(MERGE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    n=max([int(p.stem.split('-v')[1]) for p in (G.ROOT/P).glob('contract-v*.json')],default=0)+1
    assert n<=15
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; no conflicts/gates')

def event(op,summary,evidence):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)

def setup():
    assert G.git('rev-parse','HEAD')==MERGE
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    outputs=['population.json','authority.json','supersession.json','starting-state.json','implementation.json','progress.json','merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates.json','queue.json','accounting.json','validation.log','receipt.json','integration-intent.json','next-owner-request.json']+[f'contract-v{i}.json' for i in range(1,16)]+['page-'+label+'.html.gz' for label in ['production','merge','preview']]
    paths=[P+x for x in outputs]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=[ID],families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=sorted(paths)))
    instruction='Explicit current owner instruction: PR214 manually merged. Verify actual remote main/planning, PR214 merge '+MERGE+' and reviewed '+REVIEWED+', exact reviewed merge tree, canonical production '+PROD+' in installed Chrome/Playwright desktop/mobile, reviewed preview and merge deployment parity, final description/archive/City share/project links, retained 2023 meeting and official PDF, absent obsolete blocker, sound anchor/layout. Verify exact public R2 original 11940327 bytes / SHA256 '+SHA+' read-only. After conclusive production verification, reconcile ONLY '+ID+' implemented/passed to live validated/passed, preserve source recovery, scope, quality, family, original archive, preview and owner-review history, regenerate queue/checkpoint/current state, complete normal validation and synchronize clean background main/planning. This explicitly replaces only prior unmerged-owner-review phase and feature-only synchronization boundary; it grants no new visitor-visible edit, R2 mutation, publication PR, other record or substantive population. Queue owner NEXT TASK ABQ Middle School and High School Zone Active Timings.pdf with supplied IPRA/local-review-folder/non-public City-or-APS importance/elementary-later/publication-intent context in CURRENT/checkpoint, but do not inspect, classify, archive, move, upload, publish or create its governance population.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner PR214 post-merge closeout instruction',instruction=instruction,candidate_ids=[ID],merge_sha=MERGE,reviewed_head=REVIEWED))
    # Preserve the owner's context as a request, not as verified source facts or eligibility.
    G.write_once(P+'next-owner-request.json',dict(state='queued_owner_requested_work_not_started',filename='ABQ Middle School and High School Zone Active Timings.pdf',owner_context=dict(local_location='Owner says the file was placed in the local document-review folder.',provenance='Owner says it was obtained through IPRA.',content='Albuquerque middle-school and high-school school-zone active timings.',public_availability='Owner says this important information is not available on City or APS public websites.',expected_followup='Elementary-school timing information is expected later.',publication_intent='Owner explicitly wants this information added to ABQInfo in an appropriate location.'),scope_of_this_closeout='Record request only; file not inspected, classified, moved, archived, uploaded or published; no governance population created for it.',authority=P+'authority.json'))
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    assert row['status']=='implemented' and row['validation_status']=='passed'
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD,SOURCE).decode().splitlines()
    protected=history+['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/discovery/retained-source-audit-queue.json']
    G.write_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,prior_planning_sha=PLANNING,content_tree_oid=G.git('rev-parse',MERGE+':content'),selected_row=row,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),active_run_present=(G.ROOT/'project-state/active-run.json').exists(),protected_sha256={p:G.file_hash(p) for p in protected}))
    refresh()  # Complete registry frozen before phase-boundary supersession.
    r=G.registry();proposals={}
    for old in r['entries'][:]:
        if old['governance_id'] not in ['owner-mcduffie-review-2026-10-06','decision-mcduffie-review-2026-10-06','supersession-mcduffie-review-2026-10-06']:continue
        gid=old['governance_id']+'-postmerge-lifecycle-authorized'
        requirement=old['binding_requirement']+' Explicit current owner PR214 closeout exception: the owner merged the reviewed content; preserve completed review/archive/editorial decisions as historical authority. Release only former unmerged/feature-only stop condition to verify production, mark exactly '+ID+' live/validated and synchronize background main/planning after full validation. No new substantive review, visitor-visible edit, R2 mutation, other record or population.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='One production-verified lifecycle transition and background ref synchronization; preserve all substantive history.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=requirement,required_actions=[requirement],authority='Explicit current owner post-merge lifecycle instruction',effective_date='2026-10-06',prohibited_actions=['No visitor-visible, R2, unrelated record or new substantive population change; no integration before verified production and normal validation.'])
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Exact PR214 production closeout and deferred owner request',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']),dict(path=P+'next-owner-request.json',sha256=G.file_hash(P+'next-owner-request.json'),binding_pointers=['/'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No visitor-visible or R2 mutation, unrelated inventory record, new substantive population or school-zone document processing.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='authorized exact production closeout'))
    r['entries'][-1]['controlling_artifacts'].append(dict(path=P+'supersession.json',sha256=G.file_hash(P+'supersession.json'),binding_pointers=['/']))
    save(G.REGISTRY,r);refresh();seal()

def seal():
    G.active_check('mutation','governance_implementation',[ID])
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD,SOURCE).decode().splitlines()
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='mcduffie-review-2026-10-06'
    life['stages'][-1]['end_commit']=MERGE
    existing={s['path'] for s in life['protected_evidence']}
    for path in history:
        if path not in existing:life['protected_evidence'].append(dict(path=path,commit=MERGE,sha256=G.file_hash(path)))
    life['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr214PostMergeCloseout',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf8').replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr214PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR214 closeout exact-delta guard failed.\' }\nSet-StrictMode -Version Latest',1).replace('$broken = @()','& python "$PSScriptRoot/Pr214PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw \'PR214 production/Hugo parity failed.\' }\n$broken = @()',1);runner.write_text(s,encoding='utf8',newline='\n')
    event('governance_implementation','Exact one-record closeout frozen; complete registry resolved; explicit phase exception registered; preceding source/review evidence sealed at owner merge.',P+'starting-state.json')
    save(P+'progress.json',dict(state='governed_production_verification_pending',remaining=['production and exact public bytes','lifecycle reconciliation','normal validation','background ref synchronization'],no_new_population=True));refresh();guard()

JS="""() => { const h=document.getElementById('mcduffie-twin-parks');if(!h)return {missing:true};let n=h.nextElementSibling;const nodes=[];while(n&&n.tagName!=='H3'&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}return {heading:h.innerText,text:nodes.map(n=>n.innerText).join('\\n'),links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),anchor:h.id,heading_tag:h.tagName,overflow:document.documentElement.scrollWidth>innerWidth}; }"""

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    G.active_check('mutation','governance_implementation',[ID]);guard()
    pr=json.loads(subprocess.check_output(['gh','pr','view','214','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'));assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'));check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages');assert check['conclusion']=='success' and check['head_sha']==MERGE
    deployment='https://'+check['external_id'][:8]+'.abqinfo.pages.dev/'
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    visible=G.git('diff',PLANNING,MERGE,'--name-only','--','content','layouts','assets','static','hugo.toml').splitlines();assert visible==[PAGE]
    G.write_once(P+'merge-verification.json',dict(pr=pr,cloudflare_check=check,merge_deployment=deployment,reviewed_merge_trees_identical=True,visible_changed_paths=visible))
    old=G.load(OLD+'preview.json');urls=dict(production='https://abqinfo.com/'+ROUTE,merge=deployment+ROUTE,preview=old['url'].split('#')[0])
    article={};witnesses=[]
    for label,url in urls.items():
        r=requests.get(url+'?pr214_verify='+uuid.uuid4().hex,headers={'Cache-Control':'no-cache, no-store, max-age=0'},timeout=90);r.raise_for_status();value,_=presentation(r.content);article[label]=value;path=P+'page-'+label+'.html.gz';(G.ROOT/path).write_bytes(gzip.compress(r.content,mtime=0));witnesses.append(dict(label=label,url=r.url,status=r.status_code,witness=path,sha256=hashlib.sha256(r.content).hexdigest(),article_sha256=G.digest(value),observed_at=now()))
    assert article['production']==article['merge']==article['preview'],'Complete article mismatch'
    rendered={}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu']);page=browser.new_page(viewport=dict(width=1440,height=1100))
        for label,url in dict(canonical=PROD,**urls).items():
            response=page.goto(url if label=='canonical' else url+'?pr214_chrome='+uuid.uuid4().hex+'#'+ANCHOR,wait_until='networkidle',timeout=90000);assert response.status==200
            section=page.evaluate(JS);assert section['text']==old['text'] and section['links']==old['links'] and section['heading']==old['heading'];assert not section['overflow'] and section['anchor']==ANCHOR and section['heading_tag']=='H3'
            assert 'queued for archival' not in section['text'] and 'captured deterministically' not in section['text']
            assert section['links'][0]['url']=='https://files.abqinfo.com/'+KEY
            assert len(section['links'])==5
            page.locator('#'+ANCHOR).evaluate('(h)=>h.scrollIntoView(true)');rendered[label]=section
            if label=='canonical':page.screenshot(path=str(G.ROOT/(P+'production.png')))
        page.set_viewport_size(dict(width=390,height=844));response=page.goto(PROD,wait_until='networkidle',timeout=90000);assert response.status==200
        mobile=page.evaluate(JS);assert mobile['text']==old['text'] and mobile['links']==old['links'] and not mobile['overflow'];page.locator('#'+ANCHOR).evaluate('(h)=>h.scrollIntoView(true)');page.screenshot(path=str(G.ROOT/(P+'mobile.png')));browser.close()
    assert all(v==rendered['canonical'] for v in rendered.values())
    G.write_once(P+'production-render.json',dict(browser='Installed Google Chrome via Playwright',canonical_url=PROD,desktop=rendered,mobile=mobile,observed_at=now(),section_parity=True,desktop_mobile_layout_passed=True))
    G.write_once(P+'production-verification.json',dict(result='passed',merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,merge_deployment=deployment,reviewed_preview=old['url'],canonical_rendered_production_verified=True,full_article_parity=True,article_sha256=G.digest(article['production']),reviewed_section_text_links_identical=True,required_links=old['links'],obsolete_blocker_absent=True,desktop_mobile_layout_passed=True,witnesses=witnesses,rendering=P+'production-render.json',screenshots=[P+'production.png',P+'mobile.png']))
    # Read-only full GET of precisely the already archived object.
    r=requests.get('https://files.abqinfo.com/'+KEY,headers={'Cache-Control':'no-cache'},timeout=180);r.raise_for_status();size=len(r.content);sha=hashlib.sha256(r.content).hexdigest();assert size==11940327 and sha==SHA
    source=(G.ROOT/(SOURCE+'download.pdf')).read_bytes();assert len(source)==size and hashlib.sha256(source).hexdigest()==sha
    G.write_once(P+'archive-verification.json',dict(result='passed',url=r.url,r2_key=KEY,size_bytes=size,sha256=sha,exact_public_original=True,full_get=True,status=r.status_code,observed_at=now(),r2_delta=dict(added=0,deleted=0,overwritten=0,bytes=0)))
    event('governance_implementation','Owner merge/tree, canonical production and cache-busted preview/merge full article plus rendered section match; exact five links, retained meeting, absent blocker, desktop/mobile and original full R2 GET pass.',P+'production-verification.json')
    save(P+'progress.json',dict(state='production_verified_lifecycle_pending',remaining=['one-record lifecycle','normal validation','background synchronization'],no_new_population=True));refresh();G.active_check('final');guard()

def reconcile():
    assert G.load(P+'production-verification.json')['result']=='passed' and G.load(P+'archive-verification.json')['result']=='passed'
    G.active_check('mutation','inventory_disposition',[ID]);row=G.load(P+'starting-state.json')['selected_row']
    updates=[dict(id=ID,changes=dict(status='validated',validation_status='passed',processing_notes=row['processing_notes']+['PR214 owner merge '+MERGE+' production verified at '+PROD+' with installed Chrome/Playwright desktop/mobile. Full article/section matches reviewed preview and merge deployment; exact R2 full GET matches 11940327 bytes / SHA256 '+SHA+'. Final report now live/validated. Previous unmerged/not-live notes describe historical preparation only. Source recovery, scope, quality, family, archive and owner-review history preserved. Evidence: '+P+'production-verification.json.']))]
    if (G.ROOT/(P+'record-updates.json')).exists():assert G.load(P+'record-updates.json')==updates
    else:G.write_once(P+'record-updates.json',updates)
    refresh();subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    inv=G.load('project-state/master-inventory.json');old=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(old)
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];gated=pending&set(old['gated_pending_ids']);blocked=pending&set(old['source_or_structural_blocked_pending_ids']);assert gated.isdisjoint(blocked)
    ungated=pending-gated-blocked
    q.update(artifact_type='pr214_postmerge_closeout_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),approved_count=len(approved),pending_ids=sorted(pending),pending_review_count=len(pending),gated_pending_ids=sorted(gated),gated_pending_count=len(gated),source_or_structural_blocked_pending_ids=sorted(blocked),source_or_structural_blocked_pending_count=len(blocked),ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),actionable_ungated_pending_ids=sorted(ungated),genuinely_actionable_ungated_pending_count=len(ungated),in_progress_publication=None,next_work_category='Queued owner school-zone IPRA request only; not started by PR214 closeout.',newly_approved_backlog=[])
    assert (len(approved),len(pending),len(gated),len(blocked),len(ungated))==(0,339,321,18,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],next_pending_id=inv['next_pending_id'],completed_item_range='PR214 owner merge '+MERGE+' verified in production; exactly McDuffie final report live validated/passed.',remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),resume_command='PR214 production verified; finish only closeout validation/ref synchronization. Next owner school-zone IPRA request is queued, not begun.',next_owner_requested_task=G.load(P+'next-owner-request.json'));save('project-state/checkpoint.json',cp)
    # Deterministic human queue derivation without beginning a family review.
    refresh();G.active_check('mutation','governance_implementation',[ID])
    finish_reconcile()

def finish_reconcile():
    inv=G.load('project-state/master-inventory.json');q=G.load(P+'queue.json');cp=G.load('project-state/checkpoint.json')
    approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];pending=q['pending_ids'];gated=q['gated_pending_ids'];blocked=q['source_or_structural_blocked_pending_ids'];ungated=q['ungated_pending_ids']
    import importlib.util
    spec=importlib.util.spec_from_file_location('pr214_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    owner,report=module.build();assert owner['record_count']==0 and not owner['packages'];save('project-state/discovery/consolidated-human-review-queue.json',owner);(G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').write_text(report,encoding='utf8',newline='\n')
    save(P+'accounting.json',dict(validated_ids=[ID],approved=len(approved),pending=len(pending),governance_gated=len(gated),source_structural_blocked=len(blocked),ungated=len(ungated),actionable=len(ungated),human_review=sum(r['status']=='requires human review' for r in inv['candidates']),remaining_nonterminal=cp['remaining_nonterminal'],in_progress_publication=None,visitor_visible_delta=0,r2_delta=0))
    f=G.ROOT/'project-state/CURRENT.md';tail=f.read_text(encoding='utf8').split('[Owner correction]')[1]
    current='# Current project state\n\nPR #214 owner-merged at '+MERGE+'. Production McDuffie section matches reviewed preview/merge: final 2024 study, exact archive and City links, retained 2023 meeting, no obsolete source blocker; Chrome desktop/mobile passed. Exactly src-2f89e1bc040e1d33 live validated/passed. Exact 11,940,327-byte R2 full GET/SHA-256 passed; no content/R2 closeout delta. Queue: 0 approved / 339 pending (321 gated / 18 blocked), 0 actionable / 0 human review. Full validation/ref synchronization pending.\n\nNEXT TASK (queued only): `ABQ Middle School and High School Zone Active Timings.pdf`. Owner placed it in local document-review folder, obtained through IPRA; important Albuquerque middle/high-school active timings unavailable on City/APS public websites. Elementary timings expected later. Owner wants appropriate ABQInfo publication. File untouched; no school-zone population created.\n\n[Closeout](governance/'+TASK+'/accounting.json) · [Owner request](governance/'+TASK+'/next-owner-request.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n[Owner correction]'+tail
    assert len(current)<=1800;f.write_text(current,encoding='utf8',newline='\n')
    event('inventory_disposition','Only production-verified McDuffie record advanced to validated; all substantive fields/history retained; regenerated queue/checkpoint and queued untouched owner request.',P+'accounting.json')
    save(P+'progress.json',dict(state='lifecycle_reconciled_validation_pending',remaining=['normal validation','background synchronization'],no_new_population=True));refresh();G.active_check('final');guard()

def guard():
    stage=StageSnapshot(TASK);pop=stage.load_json(P+'population.json');start=stage.load_json(P+'starting-state.json')
    assert pop['candidate_ids']==[ID] and pop['baseline_commit']==MERGE
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE));assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    a={r['id']:r for r in json.loads(git('show',MERGE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys();delta={i for i in a if a[i]!=b[i]};assert delta<={ID}
    if delta:
        assert a[ID].keys()==b[ID].keys() and {k for k in a[ID] if a[ID][k]!=b[ID][k]}<={'status','validation_status','processing_notes','updated_at'}
        assert a[ID]['status']=='implemented' and b[ID]['status']=='validated' and b[ID]['validation_status']=='passed'
        assert b[ID]['processing_notes'][:len(a[ID]['processing_notes'])]==a[ID]['processing_notes']
        assert stage.load_json(P+'production-verification.json')['result']=='passed' and stage.load_json(P+'archive-verification.json')['result']=='passed'
    if (G.ROOT/(P+'accounting.json')).exists():
        q=stage.load_json(P+'queue.json');pending=sorted(r['id'] for r in b.values() if r['status']=='pending review');assert q['pending_ids']==pending and q['approved_count']==sum(r['status']=='approved for addition' for r in b.values())
        assert (q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],q['ungated_pending_count'])==(339,321,18,0) and q['in_progress_publication'] is None
        old=stage.load_json(start['source_queue']);assert set(q['gated_pending_ids'])==set(old['gated_pending_ids']) and set(q['source_or_structural_blocked_pending_ids'])==set(old['source_or_structural_blocked_pending_ids'])
        cp=stage.load_json('project-state/checkpoint.json');assert cp['next_owner_requested_task']==stage.load_json(P+'next-owner-request.json') and cp['counts_by_status']==stage.load_json('project-state/master-inventory.json')['counts']
        current=stage.read_text('project-state/CURRENT.md');assert 'NEXT TASK (queued only)' in current and 'OPEN / UNMERGED' not in current and 'not live' not in current
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json');assert receipt['visitor_visible_delta']==receipt['r2_delta']==0 and receipt['validated_ids']==[ID]
        for path,h in receipt['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS: PR214 exact validated lifecycle, unchanged content/R2/other records, sealed McDuffie history and untouched queued owner request')

def render():
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS: sealed PR214 production evidence');return
    value,_=presentation((G.ROOT/'tmp/site-build'/ROUTE/'index.html').read_bytes());assert G.digest(value)==stage.load_json(P+'production-verification.json')['article_sha256'];print('PASS: Hugo complete article matches verified PR214 production/merge/reviewed preview')

def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard()
    raw=(G.ROOT/'tmp/pr214-validation.log').read_text(encoding='utf8')
    assert '"Hugo": "passed"' in raw and '56 contiguous stage intervals' in raw and 'PR214 production/merge/reviewed preview' in raw
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    G.write_once(P+'integration-intent.json',dict(authority=P+'authority.json',expected_main=MERGE,expected_planning_snapshot=PLANNING,strategy='Atomic non-force fast-forward main and planning-snapshot to exact final background closeout commit; preserve full review/merge ancestry.',final_ref_evidence='project-state/campaign-runtime/'+TASK+'/final-refs.json',no_visitor_visible_change=True,no_r2_mutation=True,no_new_substantive_population=True))
    evidence=['merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates.json','queue.json','accounting.json','validation.log','next-owner-request.json']
    c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    G.write_once(P+'receipt.json',dict(task_id=TASK,state='production_verified_lifecycle_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_result='passed',production_url=PROD,validated_ids=[ID],lifecycle=dict(status='validated',validation_status='passed',final_study_live=True,owner_merge_verified=True),queue=G.load(P+'accounting.json'),visitor_visible_delta=0,r2_delta=0,normal_validation='passed',owner_decision_required=False,no_new_population=True,next_owner_request=P+'next-owner-request.json',next_request_untouched=True,evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact production-verified one-record live/validated lifecycle and authorized background reconciliation. All scope/quality/family/source/archive/preview/owner-review decisions and bytes retained; all other rows and visitor-visible/R2 state unchanged. Untouched school-zone request preserved as queued owner context only.',evidence=[P+'production-verification.json',P+'archive-verification.json',P+'accounting.json',P+'next-owner-request.json']) for r in c['resolved_rules']},integration_intent=P+'integration-intent.json'))
    cp=G.load('project-state/checkpoint.json');cp['resume_command']='PR214 production/live validated closeout complete. Verify final-ref receipt; next owner school-zone IPRA request is durably queued and untouched. This closeout does not start it.';save('project-state/checkpoint.json',cp)
    f=G.ROOT/'project-state/CURRENT.md';s=f.read_text(encoding='utf8').replace('Full validation/ref synchronization pending.','Full normal/governance/sealed-history/Hugo validation passed. Final background closeout commit synchronizes main/planning; no owner decision required.').replace('governance/'+TASK+'/accounting.json','governance/'+TASK+'/receipt.json');assert len(s)<=1800;f.write_text(s,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='complete',remaining=[],no_new_population=True,integration='Final background commit contains the completed closeout; atomic main/planning synchronization and concrete final refs are independently recorded in the integration journal.',next_task='Queued owner request only; untouched.'))
    event('background_integration','Complete normal suite passed; exact production-verified lifecycle ready for guarded atomic main/planning synchronization. No content/R2 or school-zone processing.',P+'integration-intent.json')
    refresh();G.active_check('final');guard()

def integrate():
    def refs():
        lines=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()
        return {x.split()[1]:x.split()[0] for x in lines}
    assert refs()=={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING}
    assert G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active);G.active_check('final');guard()
    paths=G.changed_paths(MERGE);assert not any(p.startswith('backups/') for p in paths)
    subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','-m','Close out PR214 production verification and reconcile McDuffie lifecycle'],check=True)
    head=G.git('rev-parse','HEAD');assert refs()=={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING}
    for old in [MERGE,PLANNING]:subprocess.run(['git','merge-base','--is-ancestor',old,head],check=True)
    journal='project-state/campaign-runtime/'+TASK+'/integration-journal.json'
    intent=dict(operation='atomic background closeout synchronization',authority=P+'authority.json',sha=head,expected_main=MERGE,expected_planning_snapshot=PLANNING,intent_at=now());save(journal,intent)
    result=subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],capture_output=True,text=True)
    intent.update(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,result_at=now());save(journal,intent);print(result.stdout+result.stderr);assert result.returncode==0
    subprocess.run(['git','switch','main'],check=True);subprocess.run(['git','merge','--ff-only',head],check=True);subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    remote=refs();assert remote=={'refs/heads/main':head,'refs/heads/chatgpt/planning-snapshot':head} and not G.git('status','--porcelain')
    G.active_check('final');guard()
    save('project-state/campaign-runtime/'+TASK+'/final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=remote,verified_at=now(),worktree_clean=True,merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,validation='passed',no_visitor_visible_or_r2_delta=True,next_owner_request_untouched=True))
    print('Final synchronized main/planning-snapshot:',head)

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
