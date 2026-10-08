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
    from bs4 import BeautifulSoup
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS sealed PR217 production evidence');return
    path=G.ROOT/'tmp/site-build'/ROUTE/'index.html';soup=BeautifulSoup(path.read_bytes(),'html.parser');heading=soup.find(id=ANCHOR);assert heading and heading.name=='h2'
    section=heading.find_next_sibling('ul');assert section
    links=[dict(text=a.get_text(' ',strip=True),url=a.get('href')) for a in section.find_all('a')]
    assert links==expected_links()
    text=' '.join(section.get_text(' ',strip=True).split());assert 'complete adopted 513-page plan' in text and 'Combined City Edition' not in text
    print('PASS PR217 Hugo Current Bike Plan links and text match verified custom-domain production')

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json');pop=stage.load_json(P+'population.json')
    assert pop['candidate_ids']==IDS and pop['pages']==[PAGE] and pop['baseline_commit']==MERGE
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(G.changed_paths(MERGE)) if not stage.end else set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines())
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,hash_value in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==hash_value,path
    assert stage.load_json('project-state/master-inventory.json')==json.loads(git('show',MERGE+':project-state/master-inventory.json'))
    assert stage.load_json('project-state/r2-inventory.json')==json.loads(git('show',MERGE+':project-state/r2-inventory.json'))
    if (G.ROOT/(P+'accounting.json')).exists():
        a=stage.load_json(P+'accounting.json');assert a['statuses']=={IDS[0]:'superseded',IDS[1]:'validated'} and a['r2_delta']==0 and a['visitor_visible_delta']==0
    print('PASS PR217 exact two-record production closeout: content, inventory, R2 and historical evidence unchanged')

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
