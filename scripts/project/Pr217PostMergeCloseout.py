"""Exact two-record PR217 production and lifecycle closeout; no visible or R2 change."""
import copy, gzip, hashlib, json, re, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
import Pr215PostMergeCloseout as Shared
from PgsLegislativePublication import save
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

TASK='pr217-postmerge-closeout-2026-10-08'
P='project-state/governance/'+TASK+'/'
SCRIPT='scripts/project/Pr217PostMergeCloseout.py'
MERGE='bf1384e3fd9b948160f4cd426a0252fcea32d321'
REVIEWED=PLANNING='e8d64710c144bcbee8a78fdf0de05a9a26d7f762'
IDS=['src-907f4de342216f97','src-0b1dfe6e620d7fe0']
PAGE='content/transportation/bicycling/bike-plans.md'
OLD='project-state/governance/bikeway-2024-edition-resolution-2026-10-07/'
ROUTE='transportation/bicycling/bike-plans/'
ANCHOR='current-bike-plan'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
PREVIEW='https://07549961.abqinfo.pages.dev/'+ROUTE+'#'+ANCHOR
MERGE_PREVIEW='https://b1d5d45c.abqinfo.pages.dev/'+ROUTE+'#'+ANCHOR
OPS=['governance_implementation','inventory_disposition','background_integration']

def now():return datetime.now(timezone.utc).isoformat()
def freeze_once(path,value):G.write_once(path,value)
def refresh():
    Shared.TASK=TASK;Shared.P=P;Shared.MERGE=MERGE;Shared.OPS=OPS
    Shared.refresh()
    if not (G.ROOT/(P+'supersession.json')).exists():
        active=G.load(G.ACTIVE_TASK);active.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,active)
def event(op,summary,evidence):
    plan=G.load(P+'implementation.json')
    plan['events'].append(dict(operation=op,candidate_ids=IDS,action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence))
    save(P+'implementation.json',plan)

def freeze():
    assert G.git('rev-parse','HEAD')==MERGE and set(G.changed_paths(MERGE))<={SCRIPT}
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    names=['population.json','authority.json','supersession.json','starting-state.json','baseline-records.json','implementation.json','progress.json','merge-verification.json','production-verification.json','source-verification.json','production.png','mobile.png','page-production.html.gz','page-merge.html.gz','page-preview.html.gz','accounting.json','queue.json','receipt.json','integration-intent.json','validation.log','summary.md']+[f'contract-v{i}.json' for i in range(1,41)]
    paths=[P+n for n in names]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1']
    freeze_once(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=IDS,families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=sorted(paths)))
    instruction='Explicit current owner PR217 post-merge closeout only: verify the owner merge '+MERGE+' and custom production Bike Plans page directly in Chrome; one primary current 2024 link to complete 513-page City edition, no current 144-page proposed-body link, intact component links. Compare reviewed preview, merge deployment and production; fresh exact public bytes for both preserved R2 originals and current City PDF. After successful production verification, reconcile exactly the already-decided two statuses (superseded proposed body and validated complete City edition), close owner-review phase, record accounting/CURRENT/active task/receipts and full validation, then synchronize main and chatgpt/planning-snapshot. Preserve both R2 objects, all historical evidence, all visitor-visible content, inventory values and unrelated queues. Do not start another review population.'
    freeze_once(P+'authority.json',dict(artifact_type='owner_postmerge_authorization',authority='Explicit current user PR217 post-merge closeout request',instruction=instruction,candidate_ids=IDS,merge_sha=MERGE,reviewed_head=REVIEWED,visitor_visible_change_authorized=False,r2_mutation_authorized=False,new_review_population_authorized=False))
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates'] if r['id'] in IDS}
    assert set(rows)==set(IDS) and rows[IDS[0]]['status']=='superseded' and rows[IDS[1]]['status']=='validated'
    freeze_once(P+'baseline-records.json',rows)
    protected=git('ls-tree','-r','--name-only',MERGE,'--',OLD).decode().splitlines()+[PAGE,'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md','project-state/discovery/retained-source-audit-queue.json']
    freeze_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,prior_planning_sha=PLANNING,content_tree_oid=G.git('rev-parse',MERGE+':content'),baseline_page_sha256=G.file_hash(PAGE),selected_rows=rows,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),protected_sha256={p:G.file_hash(p) for p in sorted(set(protected))},queue_counts=G.load(OLD+'accounting.json')['queue']))
    refresh();G.active_check('review','governance_implementation',IDS)
    save(P+'progress.json',dict(stage='merged_exact_two_record_population_frozen',production_verified=False,remaining=['production_and_public_source_verification','phase_only_governance_reconciliation','full_validation','background_main_planning_sync']))

def expected_links():
    s=(G.ROOT/PAGE).read_text(encoding='utf-8-sig');part=s[s.index('## Current Bike Plan'):s.index('### Interactive Plan Companions')]
    return [dict(text=t,url=u) for t,u in re.findall(r'\[([^\]]+)\]\((https://[^)]+)\)',part)]

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    G.active_check('review','governance_implementation',IDS)
    pr=json.loads(subprocess.check_output(['gh','pr','view','217','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'))
    assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','-X','GET','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'))
    check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages' and x['conclusion']=='success' and 'b1d5d45c' in x['details_url'])
    assert check['head_sha']==MERGE
    save(P+'merge-verification.json',dict(artifact_type='owner_merge_and_cloudflare_deployment_verification',pr=pr,cloudflare_check=check,merge_preview=MERGE_PREVIEW,reviewed_preview=PREVIEW,reviewed_merge_trees_identical=True))
    urls=dict(preview=PREVIEW,merge=MERGE_PREVIEW,production=PROD);expect=expected_links();assert len(expect)>=10
    results=[];sections={};html={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for viewport,w,h in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=w,height=h))
            for label,url in urls.items():
                target=url.split('#')[0]+'?pr217_closeout='+uuid.uuid4().hex+'#'+ANCHOR
                response=page.goto(target,wait_until='networkidle',timeout=90000);assert response.status==200,(label,viewport,response.status)
                section=page.locator('#'+ANCHOR).locator('xpath=following-sibling::ul[1]');assert section.count()==1
                links=section.locator('a').evaluate_all('(els)=>els.map(a=>({text:a.innerText.trim(),url:a.href}))')
                assert links==expect,(label,viewport,links,expect)
                text=' '.join(section.inner_text().split());assert 'complete adopted 513-page plan' in text and 'Combined City Edition' not in text
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                if label=='production':
                    section.scroll_into_view_if_needed();page.evaluate('window.scrollBy(0,-75)')
                    page.screenshot(path=str(G.ROOT/(P+('production.png' if viewport=='desktop' else 'mobile.png'))))
                sections[(label,viewport)]=dict(text=text,links=links)
                results.append(dict(site=label,viewport=viewport,url=page.url,status=response.status,anchor_count=1,links=links,section_text=text,former_proposed_current_link_absent=True,one_complete_current_plan=True,components_intact=True,no_horizontal_overflow=True))
                if viewport=='desktop':html[label]=page.content().encode('utf8')
            page.close()
        browser.close()
    for viewport in ['desktop','mobile']:
        assert sections[('preview',viewport)]==sections[('merge',viewport)]==sections[('production',viewport)]
    for label,body in html.items():(G.ROOT/(P+'page-'+label+'.html.gz')).write_bytes(gzip.compress(body,mtime=0))
    save(P+'production-verification.json',dict(artifact_type='direct_chrome_custom_domain_production_parity',checked_at=now(),production_url=PROD,reviewed_preview=PREVIEW,merge_deployment=MERGE_PREVIEW,expected_current_plan_links=expect,checks=results,full_section_parity=True,production_result='passed',screenshots=[P+'production.png',P+'mobile.png']))
    event('governance_implementation','Direct Chrome desktop/mobile confirms production Current Bike Plan exactly matches reviewed preview and merge deployment: one complete City entry, former proposal link absent, every component and City source link intact.',P+'production-verification.json')
    refresh()
    if any(s['id']==TASK for s in G.load('project-state/workflow-stage-lifecycle.json')['stages']):guard()

def verify_sources():
    import requests
    G.active_check('review','governance_implementation',IDS)
    assert G.load(P+'production-verification.json')['production_result']=='passed'
    rows=G.load(P+'baseline-records.json');checks=[]
    for id in IDS:
        row=rows[id];url=row['r2_url'];h=hashlib.sha256();count=0
        with requests.get(url,stream=True,timeout=90,headers={'Cache-Control':'no-cache'}) as response:
            response.raise_for_status()
            for block in response.iter_content(1024*1024):
                if block:h.update(block);count+=len(block)
            final_url=response.url;status=response.status_code
        assert count==row['size_bytes'] and h.hexdigest()==row['checksum_sha256']
        checks.append(dict(candidate_id=id,kind='existing_R2_original',requested_url=url,final_url=final_url,http_status=status,size_bytes=count,sha256=h.hexdigest(),matches_record=True))
    city=rows[IDS[1]];url=city['direct_file_url'];h=hashlib.sha256();count=0
    with requests.get(url,stream=True,timeout=90) as response:
        response.raise_for_status()
        for block in response.iter_content(1024*1024):
            if block:h.update(block);count+=len(block)
        final_url=response.url;status=response.status_code
    assert count==city['size_bytes'] and h.hexdigest()==city['checksum_sha256']
    checks.append(dict(candidate_id=IDS[1],kind='current_official_City_PDF',requested_url=url,final_url=final_url,http_status=status,size_bytes=count,sha256=h.hexdigest(),matches_record=True))
    component=[]
    for link in expected_links()[2:]:
        with requests.head(link['url'],allow_redirects=True,timeout=45) as response:
            assert response.status_code==200,(link,response.status_code)
            component.append(dict(title=link['text'],url=link['url'],status=response.status_code))
    save(P+'source-verification.json',dict(artifact_type='fresh_public_archive_and_official_source_checks',checked_at=now(),full_public_gets=checks,existing_component_links=component,component_method='Exact rendered link parity with reviewed/merge content plus fresh HTTP HEAD reachability; unchanged component records and bytes are outside this two-record closeout.',r2_writes=0,result='passed'))
    event('governance_implementation','Fresh full public GETs confirm both preserved R2 originals and current City PDF exact sizes and SHA-256; all unchanged component links reachable.',P+'source-verification.json')
    refresh()
    if any(s['id']==TASK for s in G.load('project-state/workflow-stage-lifecycle.json')['stages']):guard()

def reconcile():
    assert G.load(P+'production-verification.json')['production_result']=='passed'
    assert G.load(P+'source-verification.json')['result']=='passed'
    G.active_check('mutation','governance_implementation',IDS)
    registry=G.load(G.REGISTRY);prior=[x for x in registry['entries'] if x['state']=='active' and 'bikeway-2024-edition-resolution-2026-10-07' in x['governance_id']]
    assert len(prior)==8,[x['governance_id'] for x in prior]
    exception=' Explicit current owner PR217 post-merge phase exception solely for src-907f4de342216f97 and src-0b1dfe6e620d7fe0: the owner merged the reviewed correction at '+MERGE+'. Direct Chrome production verification and exact preview/merge parity close only the former open/unmerged owner-review and planning-only phase boundaries. Preserve the 144-page proposed body as superseded with exact former City PDF delivery still unproved, and the 513-page complete current City edition as validated. Preserve both original R2 objects, all source/version/quality evidence, content and unrelated records. Background main/planning synchronization after full validation only; no new review population.'
    proposals={}
    for old in prior:
        old_id=old['governance_id'];new_id=old_id+'-pr217-postmerge'
        requirement=old['binding_requirement']+exception
        proposals[old_id]=dict(authorized=True,existing_governance_id=old_id,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=[P+'merge-verification.json',P+'production-verification.json',P+'source-verification.json'],proposed_replacement=requirement,consequences='Only manual content-review phase closes and verified production/background refs are recorded. Two existing status values, complete-versus-proposed relationship, exact-byte provenance limit, archive objects and all unrelated decisions remain unchanged.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=new_id,title=old['title']+' — PR217 verified production phase',state='active',authority='Explicit current owner PR217 post-merge closeout instruction',decision_date='2026-10-08',effective_date='2026-10-08',binding_requirement=requirement,required_actions=[requirement],supersedes=[old_id],implementation_status='Owner-merged production verified; existing two-record dispositions preserved')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        new['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in old.get('settled_decisions',[])]+[dict(question_id=TASK+':production-lifecycle',decision='Exactly the already-decided 144-page superseded and 513-page validated records are production-reconciled; no inventory status transition or new source claim.')]
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');registry['entries'].append(new)
    freeze_once(P+'supersession.json',dict(artifact_type='explicit_postmerge_phase_only_supersession',proposals=proposals))
    owner=G.load(P+'authority.json')['instruction']
    registry['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='PR217 exact two-record post-merge closeout',scope=dict(candidate_ids=IDS,task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-08',effective_date='2026-10-08',state='active',controlling_artifacts=[dict(path=P+n,sha256=G.file_hash(P+n),binding_pointers=['/']) for n in ['authority.json','supersession.json']],binding_requirement=owner,required_actions=[owner],prohibited_actions=['No visitor-visible, inventory, R2 or new review-population mutation.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='exact production/lifecycle/background closeout'))
    save(G.REGISTRY,registry)
    refresh();G.active_check('mutation','governance_implementation',IDS)
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json');assert lifecycle['stages'][-1]['id']=='bikeway-2024-edition-resolution-2026-10-07'
    lifecycle['stages'][-1]['end_commit']=MERGE
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD).decode().splitlines();sealed={x['path'] for x in lifecycle['protected_evidence']}
    for path in history:
        if path not in sealed:lifecycle['protected_evidence'].append(dict(path=path,commit=MERGE,sha256=G.file_hash(path)))
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr217PostMergeCloseout',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';text=runner.read_text(encoding='utf-8-sig')
    text=text.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr217PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw "PR217 closeout exact-delta guard failed" }\nSet-StrictMode -Version Latest',1)
    text=text.replace('$broken = @()','& python "$PSScriptRoot/Pr217PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw "PR217 production/Hugo parity failed" }\n$broken = @()',1)
    runner.write_text(text,encoding='utf-8',newline='\n')
    q=G.load(G.load(P+'starting-state.json')['source_queue']);save(P+'queue.json',q)
    inv=G.load('project-state/master-inventory.json');after={x['id']:x for x in inv['candidates'] if x['id'] in IDS};before=G.load(P+'baseline-records.json')
    assert before==after and (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,334,321,13)
    save(P+'accounting.json',dict(artifact_type='exact_two_record_postmerge_lifecycle_accounting',statuses={i:after[i]['status'] for i in IDS},record_sha256={i:G.digest(after[i]) for i in IDS},status_transitions=0,owner_review_phase='closed_by_merged_PR217',production_result='passed',queue_counts=dict(approved=0,pending=334,governance_gated=321,source_structural_blocked=13,actionable=0,human_review=0),visitor_visible_delta=0,r2_delta=0,historical_evidence_preserved=True,new_review_population=False))
    cp=G.load('project-state/checkpoint.json');cp['pr217_postmerge_closeout']=dict(state='production_verified_lifecycle_reconciled_validation_pending',merge_sha=MERGE,candidate_ids=IDS,r2_delta=0,visitor_visible_delta=0);cp['resume_command']='PR217 production-verified two-record closeout: full validation and background main/planning sync pending; no new review population.';save('project-state/checkpoint.json',cp)
    previous=G.ROOT/'project-state/CURRENT.md';old=previous.read_text(encoding='utf-8-sig');links=old[old.index('[Owner correction]'):]
    current='# Current project state\n\nPR #217 owner-merged at '+MERGE+'. The 2024 Bikeway and Trail Facilities Plan Current Bike Plan section was verified directly on custom abqinfo.com in Chrome desktop/mobile against reviewed preview and merge deployment: one primary complete 513-page City plan entry, official City PDF, no current 144-page proposed-body link, and all ten component links intact. Both R2 originals and current City PDF passed fresh full size/SHA-256 checks.\n\nExisting exact two-record lifecycle remains: src-907f4de342216f97 superseded proposed body (former exact City delivery unproved); src-0b1dfe6e620d7fe0 validated complete current City edition. Owner content-review phase is closed. No visitor-visible, inventory or R2 mutation; no new review population. Full closeout validation and background main/planning synchronization pending.\n\nQueue 0 approved / 334 pending (321 governance-gated / 13 source-structural blocked), 0 actionable / human review.\n\n[Closeout](governance/'+TASK+'/receipt.json) · [Production](governance/'+TASK+'/production-verification.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links
    assert len(current)<1800,len(current);previous.write_text(current,encoding='utf-8',newline='\n')
    save(P+'progress.json',dict(stage='production_verified_lifecycle_reconciled',statuses={i:after[i]['status'] for i in IDS},remaining=['full_validation','background_main_planning_sync']))
    event('governance_implementation','Eight exact-record phase-only replacements close former unmerged-review boundary after verified production; both inventory rows and all original historical/quality/provenance evidence remain unchanged.',P+'supersession.json')
    event('inventory_disposition','Reconfirmed 144-page superseded and 513-page validated statuses without inventory mutation; 0/334/321/13 queue and zero human review unchanged.',P+'accounting.json')
    refresh();G.active_check('final');guard()

def render():
    from html.parser import HTMLParser
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS sealed PR217 production evidence');return
    class CurrentSection(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True);self.heading=False;self.depth=0;self.done=False;self.links=[];self.parts=[];self.href=None;self.link_parts=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='h2' and attrs.get('id')==ANCHOR:self.heading=True
            elif self.heading and not self.done:
                if tag=='ul':self.depth+=1
                elif self.depth and tag=='a':self.href=attrs.get('href');self.link_parts=[]
        def handle_endtag(self,tag):
            if not self.depth:return
            if tag=='a' and self.href is not None:
                self.links.append(dict(text=' '.join(' '.join(self.link_parts).split()),url=self.href));self.href=None
            elif tag=='ul':
                self.depth-=1
                if not self.depth:self.done=True
        def handle_data(self,data):
            if self.depth:
                self.parts.append(data)
                if self.href is not None:self.link_parts.append(data)
    path=G.ROOT/'tmp/site-build'/ROUTE/'index.html';section=CurrentSection();section.feed(path.read_text(encoding='utf8'))
    assert section.heading and section.done and section.depth==0
    assert section.links==expected_links(),(section.links,expected_links())
    text=' '.join(' '.join(section.parts).split());assert 'complete adopted 513-page plan' in text and 'Combined City Edition' not in text
    print('PASS PR217 Hugo Current Bike Plan links and text match verified custom-domain production')

def repair_derived_queue():
    import importlib.util
    G.active_check('mutation','governance_implementation',IDS)
    population=copy.deepcopy(G.load(P+'population.json'))
    population['artifact_paths']+= [P+'population-v2.json',P+'validation-attempt-1.log',P+'derived-queue-reconciliation.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    population['artifact_paths']=sorted(set(population['artifact_paths']))
    freeze_once(P+'population-v2.json',population)
    raw=(G.ROOT/'tmp/pr217-full-validation.log').read_text(encoding='utf8');raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    (G.ROOT/(P+'validation-attempt-1.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    refresh();G.active_check('mutation','governance_implementation',IDS)
    module_path=G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py';spec=importlib.util.spec_from_file_location('pr217_zero_queue_builder',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result,report=module.build();path='project-state/discovery/consolidated-human-review-queue.json';before=G.load(path)
    assert before['record_count']==result['record_count']==before['package_count']==result['package_count']==0
    assert {k:v for k,v in before.items() if k!='inventory_sha256'}=={k:v for k,v in result.items() if k!='inventory_sha256'}
    assert (G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').read_text(encoding='utf8')==report
    (G.ROOT/path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    freeze_once(P+'derived-queue-reconciliation.json',dict(artifact_type='deterministic_zero_member_queue_checksum_reconciliation',failed_validation=P+'validation-attempt-1.log',issue='Merged PR217 inventory bytes have a different exact SHA-256 than the saved zero-member consolidated queue pointer; normal full-suite freshness check failed.',resolved_by='Existing deterministic queue builder; only inventory_sha256 changes. Zero records/packages and Markdown are unchanged.',before_inventory_sha256=before['inventory_sha256'],after_inventory_sha256=result['inventory_sha256'],candidate_ids=IDS,new_review_population=False))
    event('governance_implementation','Full suite exposed a stale exact inventory checksum in the merged zero-case human-review queue; deterministic builder refreshed only that field with zero member/package/Markdown delta.',P+'derived-queue-reconciliation.json')
    refresh();G.active_check('final');guard()

def finish():
    G.active_check('mutation','governance_implementation',IDS);guard()
    raw=(G.ROOT/'tmp/pr217-full-validation-3.log').read_text(encoding='utf8')
    assert '"Hugo": "passed"' in raw and 'PASS PR217 Hugo Current Bike Plan links and text match verified custom-domain production' in raw
    raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    freeze_once(P+'integration-intent.json',dict(artifact_type='authorized_background_ref_synchronization',authority=P+'authority.json',expected_remote_main=MERGE,expected_remote_planning_snapshot=PLANNING,strategy='Atomic non-force fast-forward of main and planning-snapshot to this background-only closeout, retaining merge and reviewed history.',final_ref_evidence='project-state/campaign-runtime/'+TASK+'/final-refs.json',visitor_visible_delta=0,r2_delta=0,new_review_population=False))
    evidence=['merge-verification.json','production-verification.json','source-verification.json','production.png','mobile.png','accounting.json','queue.json','derived-queue-reconciliation.json','validation.log']
    contract=G.load(G.load(G.ACTIVE_TASK)['contract'])
    freeze_once(P+'receipt.json',dict(artifact_type='pr217_exact_two_record_postmerge_receipt',task_id=TASK,state='production_verified_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,production_result='passed',candidate_statuses={IDS[0]:'superseded',IDS[1]:'validated'},proposed_body_exact_former_city_delivery='unproved',complete_city_edition_exact_current_city_delivery=True,queue_counts=G.load(P+'accounting.json')['queue_counts'],visitor_visible_delta=0,inventory_status_transitions=0,r2_delta=0,historical_evidence_preserved=True,new_review_population=False,normal_validation='passed',validation_log=P+'validation.log',evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Owner-merged PR217 verified on custom production directly in Chrome, with exact preview and merge deployment parity. Existing superseded/validated statuses and all original R2/evidence retained; only background lifecycle and derived zero-case queue checksum reconciled.',evidence=[P+'production-verification.json',P+'source-verification.json',P+'accounting.json',P+'validation.log']) for r in contract['resolved_rules']},integration_intent=P+'integration-intent.json',visual_inspection='Chrome desktop and mobile screenshots inspected; one complete City plan entry, former proposed-body current link absent, City PDF and ten components intact, no overflow.'))
    cp=G.load('project-state/checkpoint.json');cp['pr217_postmerge_closeout']['state']='complete_production_verified_validation_passed';cp['resume_command']='PR217 exact two-record production closeout complete and full validation passed; authorized atomic main/planning-snapshot background synchronization pending. No new review population.';save('project-state/checkpoint.json',cp)
    current=G.ROOT/'project-state/CURRENT.md';body=current.read_text(encoding='utf8');body=body.replace('Full closeout validation and background main/planning synchronization pending.','Full closeout validation passed; authorized background main/planning synchronization pending.');current.write_text(body,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(stage='production_verified_validation_passed',remaining=['background_main_planning_sync'],candidate_statuses={IDS[0]:'superseded',IDS[1]:'validated'},new_review_population=False))
    event('background_integration','Full project validation and exact production/source parity passed; two-record lifecycle and R2 preserved, ready for authorized atomic background branch synchronization.',P+'integration-intent.json')
    refresh();G.active_check('final');guard()

def integrate():
    def refs():return {line.split()[1]:line.split()[0] for line in subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()}
    expected={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING}
    assert refs()==expected and G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',IDS);guard()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan)
    active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active)
    G.active_check('final');guard()
    paths=G.changed_paths(MERGE);assert not any(p.startswith('backups/') for p in paths)
    subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','--quiet','-m','Complete PR217 production closeout for 2024 Bikeway editions'],check=True)
    head=G.git('rev-parse','HEAD');assert refs()==expected
    for old in [MERGE,PLANNING]:subprocess.run(['git','merge-base','--is-ancestor',old,head],check=True)
    journal='project-state/campaign-runtime/'+TASK+'/integration-journal.json';intent=dict(operation='atomic background closeout synchronization',authority=P+'authority.json',sha=head,expected_refs=expected,intent_at=now());save(journal,intent)
    result=subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],capture_output=True,text=True)
    intent.update(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,result_at=now());save(journal,intent);print(result.stdout+result.stderr);assert result.returncode==0
    subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    remote=refs();assert remote=={'refs/heads/main':head,'refs/heads/chatgpt/planning-snapshot':head} and not G.git('status','--porcelain')
    G.active_check('final');guard()
    save('project-state/campaign-runtime/'+TASK+'/final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=remote,verified_at=now(),worktree_clean=True,merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,validation='passed',r2_delta=0,visitor_visible_delta=0,new_review_population=False))
    print('Final synchronized main/planning-snapshot:',head)

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json');pop=stage.load_json(P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json'))
    assert pop['candidate_ids']==IDS and pop['pages']==[PAGE] and pop['baseline_commit']==MERGE
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(G.changed_paths(MERGE)) if not stage.end else set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines())
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    derived='project-state/discovery/consolidated-human-review-queue.json'
    for path,hash_value in start['protected_sha256'].items():
        if path==derived and (G.ROOT/(P+'derived-queue-reconciliation.json')).exists():
            before=json.loads(git('show',MERGE+':'+path));after=stage.load_json(path)
            assert {k:v for k,v in before.items() if k!='inventory_sha256'}=={k:v for k,v in after.items() if k!='inventory_sha256'}
            assert after['record_count']==after['package_count']==0
            assert after['inventory_sha256']==hashlib.sha256(canonical_bytes(stage.read_bytes('project-state/master-inventory.json'))).hexdigest()
        else:assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==hash_value,path
    assert stage.load_json('project-state/master-inventory.json')==json.loads(git('show',MERGE+':project-state/master-inventory.json'))
    assert stage.load_json('project-state/r2-inventory.json')==json.loads(git('show',MERGE+':project-state/r2-inventory.json'))
    if (G.ROOT/(P+'accounting.json')).exists():
        a=stage.load_json(P+'accounting.json');assert a['statuses']=={IDS[0]:'superseded',IDS[1]:'validated'} and a['r2_delta']==0 and a['visitor_visible_delta']==0
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json');assert receipt['candidate_statuses']=={IDS[0]:'superseded',IDS[1]:'validated'} and receipt['r2_delta']==receipt['visitor_visible_delta']==0
        for path,h in receipt['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS PR217 exact two-record production closeout: content, inventory, R2 and historical evidence unchanged')

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
