"""Background-only production verification and twelve-component publication closeout."""
import copy
import gzip
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import TaskGovernance as G
import OwnerResources20261004 as S
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git
from Pr208209Reconciliation import presentation

TASK='pr211-postmerge-closeout-2026-10-05'
P='project-state/governance/'+TASK+'/'
MERGE='18e2a24d85676e187ea97c7d693cae7245504c99'
REVIEWED='f7acea5086edfd8577c46b55b4c1a81e889e1c22'
OLD='project-state/governance/central-avenue-master-correction-2026-10-04/'
FAMILY='project-state/governance/central-station-area-family-resolution-2026-10-04/'
PAGE='content/development-land-use/area-sector-plans.md'
ROUTE='development-land-use/area-sector-plans/'
ANCHOR='central-avenue-station-area-planning'
IDS=G.load(FAMILY+'receipt.json')['frozen_population']
APPROVED=IDS[:12]
SCRIPT='scripts/project/Pr211PostMergeCloseout.py'
OPS=['governance_implementation','inventory_disposition','background_integration']

def save(path,value): S.save(path,value)

def refresh():
    registry=G.load(G.REGISTRY)
    for row in registry['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']: a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,registry)
    registered={a['path'] for r in registry['entries'] for a in r['controlling_artifacts']}
    paths=[f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).glob('*') if f.is_file() and f.name!='implementation.json' and f.relative_to(G.ROOT).as_posix() not in registered]
    paths += [SCRIPT,'project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    S.audit(paths)
    versions=list((G.ROOT/P).glob('contract-v*.json'))
    n=max([int(f.stem.split('-v')[1]) for f in versions],default=0)+1
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True)
    c=G.load(path); assert not c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for x in r.get('constraints',[]): subjects.setdefault(x['subject'],{})[x['field']]=x['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']: e['governance_ids']=c['governance_ids']
    evidence=next((P+name for name in ['receipt.json','accounting.json','production-verification.json','starting-state.json'] if (G.ROOT/(P+name)).exists()),None)
    if evidence: plan['completion_evidence']={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',supersession_proposals_path=P+'supersession.json',state='in_progress'))

def event(operation,text,evidence,ids=IDS):
    p=G.load(P+'implementation.json')
    p['events'].append(dict(operation=operation,candidate_ids=ids,governance_ids=p['respected_governance_ids'],action='implements',summary=text,evidence=evidence,use_contract_record_rules=True))
    save(P+'implementation.json',p)

def freeze():
    assert G.git('rev-parse','HEAD')==MERGE
    outputs=['population.json','authority.json','supersession.json','starting-state.json','implementation.json','progress.json','merge-verification.json','production-verification.json','production-render.json','production.png','archive-verification.json','r2-live.json','record-updates.json','queue.json','accounting.json','validation.log','receipt.json','integration-intent.json']
    outputs += ['page-'+x+'.html.gz' for x in ['production','merge','preview']]
    artifacts=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,101)]
    artifacts += [SCRIPT,G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/CURRENT.md','project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=IDS,families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=artifacts))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.population(G.load(P+'population.json')),G.registry(),G.file_hash(G.REGISTRY))
    authority=('Current owner confirms manual merge of PR211 and authorizes only background post-merge direct production verification and publication-lifecycle reconciliation for its twelve approved Central Avenue components. Verify production against exact merge deployment, reviewed content and inspected preview, using cache-busted direct HTTP and installed Chrome. Require one historical master, eleven report components with settled provenance/draft/finality explanation, separate Crabtree Infrastructure and all twelve retained archive links; Urban3 must be absent from public presentation and remain pending with unchanged blocker, bytes and provenance. Reverify retained R2 originals; derive live object/byte totals; no R2 mutations or 2018 oversized-study exception. After production succeeds, advance the twelve approved records through the normal implementation lifecycle and regenerate deterministic queue/accounting, checkpoint and CURRENT. Preserve completed review and all visitor-visible content. Full validation, governance/sealed-history/Hugo/rendered/CURRENT/diff checks are required. Save immutable closeout evidence, integrate background-only into main and synchronize planning-snapshot to the same final main. No further population or visitor-visible edits; material production discrepancy requires stopping for the smallest corrective PR. This explicitly releases the former pending-manual-review inventory boundary for the twelve merged components only; substantive family findings remain binding.')
    G.write_once(P+'authority.json',dict(authority='Explicit current owner PR211 merged-closeout instruction',merge_sha=MERGE,reviewed_head=REVIEWED,instruction=authority,candidate_ids=IDS,implementation_ids=APPROVED))
    S.bind(P+'authority.json','owner-'+TASK,authority,dict(task_ids=[TASK],candidate_ids=IDS,pages=[PAGE]))
    r=G.load(G.REGISTRY)
    owner=next(x for x in r['entries'] if x['governance_id']=='owner-'+TASK);owner['authority']='Explicit current owner background PR211 post-merge instruction'
    gid='owner-central-avenue-master-correction-2026-10-04'
    old=next(x for x in r['entries'] if x['governance_id']==gid)
    new=copy.deepcopy(old);newgid=gid+'-postmerge-lifecycle-exception'
    replacement=old['binding_requirement']+' Explicit current owner PR211 post-merge exception: the twelve manually merged approved components may advance through the normal publication implementation lifecycle under owner-'+TASK+' after direct production verification. Preserve all review findings, Urban3 factual hold, original bytes and no-content/no-R2 boundaries. The prior review/merge restriction remains historical authority for the preparation stage.'
    proposals={gid:dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=old['controlling_artifacts'],new_evidence=P+'authority.json',proposed_replacement=replacement,consequences='Twelve approved components become implemented after production verification; no substantive disposition, Urban3, content or storage change.',authorization_artifact=P+'authority.json')}
    old.update(state='superseded',superseded_by=newgid,supersession_evidence=P+'authority.json')
    new.update(governance_id=newgid,title=newgid,authority='Explicit owner PR211 post-merge publication-lifecycle exception',binding_requirement=replacement,required_actions=[replacement],supersedes=gid)
    new['controlling_artifacts'] += [dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
    r['entries'].append(new);save(G.REGISTRY,r)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r=G.load(G.REGISTRY);owner=next(x for x in r['entries'] if x['governance_id']=='owner-'+TASK)
    owner['controlling_artifacts'].append(dict(path=P+'supersession.json',sha256=G.file_hash(P+'supersession.json'),binding_pointers=['/']));save(G.REGISTRY,r)
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    inv=G.load('project-state/master-inventory.json');rows={x['id']:x for x in inv['candidates']}
    assert all(rows[i]['status']=='approved for addition' for i in APPROVED) and rows[IDS[-1]]['status']=='pending review'
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD,FAMILY).decode().splitlines()
    G.write_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,trees_identical=True,content_tree_oid=G.git('rev-parse',MERGE+':content'),selected_rows=[dict(id=i,row=rows[i],row_sha256=G.digest(rows[i])) for i in IDS],protected_sha256={x:G.file_hash(x) for x in history+['project-state/r2-inventory.json','project-state/r2-storage-policy.json']},queue=G.load(FAMILY+'receipt.json')['queue']))
    stages=G.load('project-state/workflow-stage-lifecycle.json');assert stages['stages'][-1]['id']=='central-avenue-master-correction-2026-10-04'
    stages['stages'][-1]['end_commit']=MERGE
    stages['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr211PostMergeCloseout',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=f.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr211PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR211 background publication closeout boundary failed.\' }\nSet-StrictMode -Version Latest',1)
    f.write_text(t,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='governed_production_verification_pending',remaining=['direct_production','archive_GETs_and_live_totals','publication_lifecycle','full_validation','immutable_receipt','main_and_planning_integration'],no_new_population=True))
    refresh();G.active_check('mutation','governance_implementation');guard()

def get(url):
    target=url+(' & ' if '?' in url else '?')+'abqinfo_pr211_verify='+uuid.uuid4().hex
    target=target.replace(' & ','&')
    req=urllib.request.Request(target,headers={'User-Agent':'Mozilla/5.0 (ABQInfo PR211 direct production verification)','Cache-Control':'no-cache, no-store, max-age=0','Pragma':'no-cache'})
    with urllib.request.urlopen(req,timeout=90) as r:
        data=r.read();assert r.status==200
        return data,dict(url=target,resolved_url=r.url,http_status=r.status,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),headers=dict(r.headers),observed_at=S.now())

JS=r'''() => {
  const h=document.getElementById('central-avenue-station-area-planning');
  const nodes=[];let n=h.nextElementSibling;
  while(n&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}
  return {heading:h.innerText,anchor:h.id,text:nodes.map(n=>n.innerText).join('\n'),
    links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),
    master_entries:nodes.flatMap(n=>Array.from(n.matches('ul')?n.children:[])).length,
    overflow:document.documentElement.scrollWidth>innerWidth};
}'''

def verify():
    G.active_check('mutation','governance_implementation')
    pr=json.loads(subprocess.check_output(['gh','pr','view','211','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'))
    assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'))
    check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages')
    assert check['head_sha']==MERGE and check['conclusion']=='success'
    deployment='https://'+check['details_url'].rstrip('/').split('/')[-1].split('-')[0]+'.abqinfo.pages.dev/'
    G.write_once(P+'merge-verification.json',dict(pr=pr,cloudflare_check=check,merge_deployment=deployment,merge_reviewed_trees_identical=True))
    old=G.load(OLD+'preview.json');preview=old['url'].split(ROUTE)[0]
    urls={'production':'https://abqinfo.com/'+ROUTE,'merge':deployment+ROUTE,'preview':preview+ROUTE}
    values=[];witnesses=[]
    for label,url in urls.items():
        body,ev=get(url);value,decoded=presentation(body);values.append(value)
        path=P+'page-'+label+'.html.gz';(G.ROOT/path).write_bytes(gzip.compress(body,mtime=0))
        ev.update(witness=path,article_sha256=hashlib.sha256(G.canonical(value)).hexdigest(),email_decodes=decoded);witnesses.append(ev)
    reviewed=(G.ROOT/'tmp/pr211-reviewed-build'/ROUTE/'index.html').read_bytes()
    reviewed_value,_=presentation(reviewed)
    assert values[0]==values[1]==values[2]==reviewed_value,'PRODUCTION DEFECT: article text, links or anchors differ from reviewed/merge/preview'
    from playwright.sync_api import sync_playwright
    rendered={}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        page=browser.new_page(viewport=dict(width=1440,height=1100))
        for label,url in urls.items():
            response=page.goto(url+'?abqinfo_pr211_chrome='+uuid.uuid4().hex,wait_until='networkidle',timeout=90000)
            assert response.status==200
            result=page.evaluate(JS);rendered[label]=result
            assert not result['overflow'] and result['master_entries']==1
            if label=='production':
                page.locator('#'+ANCHOR).evaluate('(h)=>h.scrollIntoView(true)')
                page.wait_for_timeout(1500)
                page.screenshot(path=str(G.ROOT/(P+'production.png')))
        page.set_viewport_size(dict(width=390,height=844))
        page.goto(urls['production']+'?abqinfo_pr211_mobile='+uuid.uuid4().hex,wait_until='networkidle',timeout=90000)
        mobile=page.evaluate(JS);assert not mobile['overflow']
        browser.close()
    assert rendered['production']==rendered['merge']==rendered['preview']
    expected=G.load(OLD+'preview-render.json')
    assert all(rendered['production'][k]==expected[k] for k in ['heading','text','links','master_entries'])
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    actual=[x['url'] for x in rendered['production']['links'] if x['url'].startswith('https://files.abqinfo.com/')]
    assert actual==[rows[i]['r2_url'] for i in APPROVED]
    text=rendered['production']['text']
    for phrase in ['eleven continuously paginated','September 2017','City-commissioned','nonbinding draft','released for public comment','2018 revised completed study superseded','not an adopted plan','not section 12','Infrastructure — Crabtree supporting assessment/draft']:
        assert phrase in text,phrase
    assert 'Impact of Transit' not in text and 'Urban3' not in text and rows[IDS[-1]]['r2_url'] not in actual
    G.write_once(P+'production-render.json',dict(browser='Installed Google Chrome via Playwright',observed_at=S.now(),desktop=rendered,mobile=mobile,rendered_section_parity=True,layout_overflow=False))
    G.write_once(P+'production-verification.json',dict(result='passed',merge_sha=MERGE,reviewed_head=REVIEWED,canonical_url=urls['production']+'#'+ANCHOR,merge_deployment=deployment,prior_inspected_preview=old['url'],direct_cache_busted_HTTP=True,full_article_parity=True,reviewed_commit_build_article_sha256=hashlib.sha256(G.canonical(reviewed_value)).hexdigest(),section_text_links_heading_anchor_parity=True,one_master=True,retained_archive_links=actual,urban3_presentation_absent=True,desktop_and_mobile_layout_passed=True,witnesses=witnesses,rendering=P+'production-render.json',screenshot=P+'production.png'))
    event('governance_implementation','Direct cache-busted production, exact merge deployment, reviewed commit build and prior inspected preview agree; installed Chrome section, twelve links and layout pass.',P+'production-verification.json')
    save(P+'progress.json',dict(state='production_verified_archive_and_lifecycle_pending',production_result='passed',no_new_population=True))
    refresh();G.active_check('final')

def archives():
    G.active_check('mutation','governance_implementation')
    assert G.load(P+'production-verification.json')['result']=='passed'
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    results=[]
    def one(rid):
        row=rows[rid];h=hashlib.sha256();size=0
        req=urllib.request.Request(row['r2_url']+'?abqinfo_pr211_archive='+uuid.uuid4().hex,headers={'Cache-Control':'no-cache','User-Agent':'Mozilla/5.0 (ABQInfo exact archive verification)'})
        with urllib.request.urlopen(req,timeout=180) as response:
            assert response.status==200
            while block:=response.read(1024*1024):size+=len(block);h.update(block)
        assert size==row['size_bytes'] and h.hexdigest()==row['checksum_sha256'],rid
        print(rid,size,'full GET verified',flush=True)
        return dict(id=rid,url=row['r2_url'],size_bytes=size,sha256=h.hexdigest(),full_public_GET=True,verified_at=S.now(),retained_public_component=rid in APPROVED)
    for attempt in range(3):
        done={r['id'] for r in results}
        with ThreadPoolExecutor(max_workers=2) as pool:
            for f in as_completed([pool.submit(one,i) for i in IDS if i not in done]):
                try: results.append(f.result())
                except Exception as e: print('Archive retry',attempt+1,str(e),flush=True)
        if len(results)==13:break
    assert len(results)==13,'Incomplete exact archive verification'
    live=G.load(P+'r2-live.json');prior=G.load('project-state/r2-inventory.json')
    assert live['objects']==prior['objects'],'Live R2 metadata differs from recorded originals'
    objects=len(live['objects']);bytes_total=sum(x['size_bytes'] for x in live['objects'])
    assert objects==1612 and bytes_total==10971266597
    assert live['object_count']==objects and live['total_bytes']==bytes_total
    bykey={x['key']:x for x in live['objects']}
    assert bykey[rows[IDS[-1]]['r2_key']]['size_bytes']==rows[IDS[-1]]['size_bytes']
    assert not any(x['size_bytes']==260287731 and 'central' in x['key'].lower() for x in live['objects'])
    G.write_once(P+'archive-verification.json',dict(result='passed',objects=objects,bytes=bytes_total,totals_derived_from='Complete live R2 objects list; count and sum recomputed',complete_live_metadata_matches_baseline=True,retained_twelve_verified=True,urban3_original_preserved_and_verified=True,results=sorted(results,key=lambda r:IDS.index(r['id'])),unarchived_2018=dict(size_bytes=260287731,sha256='d95ccfefc099546a69148180421fcfbda1ff378881dd30471fcb26fbe52ca06e',unchanged_archival_hold=True,no_exception_authorized=True),r2_delta=dict(added=0,deleted=0,overwritten=0,bytes=0)))
    event('governance_implementation','Twelve retained R2 full GETs plus unchanged Urban3 original verified; complete live listing metadata and recomputed totals match baseline.',P+'archive-verification.json')
    refresh()

def reconcile():
    assert G.load(P+'production-verification.json')['result']=='passed' and G.load(P+'archive-verification.json')['result']=='passed'
    G.active_check('mutation','inventory_disposition',APPROVED)
    start=G.load(P+'starting-state.json');rows={x['id']:x['row'] for x in start['selected_rows']}
    changes=[]
    for rid in APPROVED:
        note='PR211 owner-merged historical master verified in production at '+MERGE+'; implemented as '+('a separate Crabtree supporting draft within the single curated historical master' if rid==APPROVED[-1] else 'a grouped component of the eleven-section September 2017 public-comment report')+'. No standalone public entry. Direct production/merge/reviewed/preview parity and exact public archive bytes passed. Evidence: '+P+'production-verification.json and archive-verification.json.'
        changes.append(dict(id=rid,changes=dict(status='implemented',validation_status='passed',implementation_location=PAGE,implementation_locations=[PAGE],processing_notes=rows[rid]['processing_notes']+[note])))
    if (G.ROOT/(P+'record-updates.json')).exists():
        assert G.load(P+'record-updates.json')==changes
    else:
        G.write_once(P+'record-updates.json',changes)
    # The requests preserve instruction-bearing historical notes; classify
    # their exact bytes before the batch's independent mutation preflight.
    refresh()
    currentrows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    if any(any(currentrows[x['id']][k]!=v for k,v in x['changes'].items()) for x in changes):
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    refresh()
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True)
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Write-ProjectCheckpoint.ps1','-CompletedRange','PR211 owner-merged Central Avenue historical master production verified; exactly twelve approved components implemented/passed; Urban3 unchanged.','-ResumeCommand','PR211 background closeout: production/archive/publication lifecycle complete; full validation and authorized main/planning synchronization pending. No new review population.'],check=True)
    refresh()
    G.active_check('mutation','governance_implementation')
    # This is deterministic metadata regeneration, not a family review or
    # human disposition. Use the existing builder and verify zero case delta.
    import importlib.util
    spec=importlib.util.spec_from_file_location('pr211_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    oldowner=G.load('project-state/discovery/consolidated-human-review-queue.json')
    owner,report=module.build()
    assert oldowner['record_count']==owner['record_count']==0 and oldowner['packages']==owner['packages']==[]
    save('project-state/discovery/consolidated-human-review-queue.json',owner)
    (G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').write_text(report,encoding='utf8',newline='\n')
    inv=G.load('project-state/master-inventory.json');current={x['id']:x for x in inv['candidates']}
    pointer=json.loads(git('show',MERGE+':project-state/ordinary-queue-current.json'))
    prior=json.loads(git('show',MERGE+':'+pointer['artifact']))
    q=copy.deepcopy(prior);pending={i for i,r in current.items() if r['status']=='pending review'}
    q.update(artifact_type='pr211_postmerge_publication_queue',recorded_at=inv['generated_at'],source_queue_artifact=pointer['artifact'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=sum(r['status']=='approved for addition' for r in current.values()),newly_approved_backlog=[],in_progress_publication=None)
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending}
        q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    assert q['source_or_structural_blocked_pending_ids'][IDS[-1]]==prior['source_or_structural_blocked_pending_ids'][IDS[-1]]
    q['pr211_publication_closeout']=dict(task=TASK,merge_sha=MERGE,implemented_components=APPROVED,one_public_master=True,urban3_pending_unchanged=IDS[-1],production_evidence=P+'production-verification.json')
    G.write_once(P+'queue.json',q)
    save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    assert q['approved_count']==0 and len(pending)==351
    ledger=[dict(id=i,before_row_sha256=G.digest(rows[i]),after_row_sha256=G.digest(current[i]),before_status=rows[i]['status'],after_status=current[i]['status'],role='unchanged factual hold' if i==IDS[-1] else 'separate supporting draft' if i==APPROVED[-1] else 'report component',publication_master=PAGE+'#'+ANCHOR) for i in IDS]
    G.write_once(P+'accounting.json',dict(result='passed',records=ledger,exactly_once=True,implemented_ids=APPROVED,unchanged_pending_id=IDS[-1],queue=dict(approved=q['approved_count'],pending=len(pending),governance_gated=q['gated_pending_count'],source_or_structural_blocked=q['source_or_structural_blocked_pending_count'],ungated=q['ungated_pending_count']),visitor_visible_delta=0,r2_delta=0))
    event('inventory_disposition','Advance exactly twelve owner-merged components to implemented/passed in one master; preserve all prior review fields and Urban3 blocker; derive queue/checkpoint accounting.',P+'accounting.json',APPROVED)
    save(P+'progress.json',dict(state='production_archive_and_publication_lifecycle_complete_validation_pending',remaining=['full_validation','immutable_receipt','main_and_planning_integration'],no_new_population=True))
    currentfile=G.ROOT/'project-state/CURRENT.md';text=currentfile.read_text(encoding='utf8');links=text[text.index('[Active task]'):]
    currentfile.write_text('# Current project state\n\nPR #211 manually merged at '+MERGE+'. Direct production agrees with exact merge deployment, reviewed content and inspected preview: one Central Avenue historical master, eleven report components and separate Crabtree Infrastructure supporting draft. Twelve components are implemented/passed. Derived queue: 0 approved / 351 pending (321 governance-gated / 30 source-structural blocked). Urban3 remains pending with its factual provenance/completeness blocker unchanged. Thirteen full archive GETs verified, including preserved Urban3; R2 unchanged. No new review/publication population. Full validation and background-only main/planning integration pending.\n\n[PR211 closeout](governance/'+TASK+'/accounting.json) · [Production evidence](governance/'+TASK+'/production-verification.json) · [Family review](governance/central-station-area-family-resolution-2026-10-04/decisions.json) · '+links,encoding='utf8',newline='\n')
    refresh();guard();G.active_check('final')

def finish():
    G.active_check('mutation','governance_implementation');guard()
    f=G.ROOT/(P+'validation.log');raw=f.read_text(encoding='utf8');assert '"Hugo": "passed"' in raw and '"BrokenLinks": 0' in raw
    f.write_text('\n'.join(x.rstrip() for x in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    checkpoint=G.load('project-state/checkpoint.json')
    checkpoint['resume_command']='PR211 background production verification and twelve-component publication closeout complete. Read CURRENT and the immutable closeout receipt. Urban3 remains a factual source/completeness hold; no new review/publication population or owner decision is pending.'
    save('project-state/checkpoint.json',checkpoint)
    G.write_once(P+'integration-intent.json',dict(authority=P+'authority.json',expected_main=MERGE,expected_planning_snapshot=REVIEWED,strategy='Atomically fast-forward both refs to the same final background closeout commit; no visible content or R2 mutation',no_new_population=True))
    evidence=['merge-verification.json','production-verification.json','production-render.json','production.png','archive-verification.json','r2-live.json','record-updates.json','queue.json','accounting.json','validation.log']
    G.write_once(P+'receipt.json',dict(task_id=TASK,state='production_verified_publication_lifecycle_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_result='passed',section_text_links_heading_anchor_parity=True,production_url='https://abqinfo.com/'+ROUTE+'#'+ANCHOR,merge_deployment=G.load(P+'production-verification.json')['merge_deployment'],one_master=True,implemented_records=APPROVED,urban3=dict(id=IDS[-1],status='pending review',factual_blocker_unchanged=True,original_preserved=True),queue=G.load(P+'accounting.json')['queue'],r2=dict(objects=G.load(P+'archive-verification.json')['objects'],bytes=G.load(P+'archive-verification.json')['bytes'],added=0,deleted=0,overwritten=0,byte_delta=0),visitor_visible_delta=0,inventory_transitions=12,normal_validation='passed',evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},integration_intent=P+'integration-intent.json',owner_action_required=False,no_new_population=True))
    f=G.ROOT/'project-state/CURRENT.md';t=f.read_text(encoding='utf8').replace('Full validation and background-only main/planning integration pending.','Full project, governance/sealed-history, Hugo/rendered, CURRENT and diff checks passed. Background-only closeout integration synchronizes main and planning-snapshot; zero visitor-visible/R2 delta. No owner action pending.').replace('governance/'+TASK+'/accounting.json','governance/'+TASK+'/receipt.json');f.write_text(t,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='closeout_complete',remaining=[],no_new_population=True,integration_intent=P+'integration-intent.json'))
    event('background_integration','Complete production-verified background publication closeout; persist authorized atomic main/planning integration intent.',P+'integration-intent.json')
    refresh();G.active_check('mutation','background_integration');G.active_check('final');guard()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan)
    active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active)
    G.active_check('final')

def guard():
    stages=G.load('project-state/workflow-stage-lifecycle.json')['stages']
    if not any(s['id']==TASK for s in stages):return
    stage=StageSnapshot(TASK);pop=stage.load_json(P+'population.json');start=stage.load_json(P+'starting-state.json')
    assert pop['candidate_ids']==IDS and pop['baseline_commit']==MERGE
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE))
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items(): assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    before=json.loads(git('show',MERGE+':project-state/master-inventory.json'));after=stage.load_json('project-state/master-inventory.json')
    a={r['id']:r for r in before['candidates']};b={r['id']:r for r in after['candidates']}
    assert a.keys()==b.keys()
    oldcp=json.loads(git('show',MERGE+':project-state/checkpoint.json'))
    newcp=stage.load_json('project-state/checkpoint.json')
    allowedcp={'recorded_at','completed_item_range','counts_by_status','remaining_nonterminal','resume_command','history'}
    assert set(oldcp)==set(newcp) and all(oldcp[k]==newcp[k] for k in oldcp if k not in allowedcp),'Unrelated checkpoint metadata changed'
    assert newcp['history'][:len(oldcp['history'])]==oldcp['history'],'Prior checkpoint history changed'
    delta={i for i in a if a[i]!=b[i]};assert delta<=set(APPROVED) and a[IDS[-1]]==b[IDS[-1]]
    for i in delta:
        assert {k for k in a[i] if a[i][k]!=b[i][k]}<={'status','validation_status','implementation_location','implementation_locations','processing_notes','updated_at'}
        assert a[i]['status']=='approved for addition' and b[i]['status']=='implemented' and b[i]['validation_status']=='passed'
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes']
        from PublicationQuality import require_publication_quality
        require_publication_quality(b[i])
    if (G.ROOT/(P+'accounting.json')).exists():
        assert delta==set(APPROVED)
        q=stage.load_json(P+'queue.json');pending={i for i,r in b.items() if r['status']=='pending review'}
        assert set(q['pending_ids'])==pending and len(pending)==351
        assert not q['newly_approved_backlog'] and not any(r['status']=='approved for addition' for r in b.values())
    if (G.ROOT/(P+'production-verification.json')).exists():
        v=stage.load_json(P+'production-verification.json');assert v['result']=='passed' and v['section_text_links_heading_anchor_parity']
        for w in v['witnesses']:
            body=gzip.decompress(stage.read_bytes(w['witness']));assert hashlib.sha256(body).hexdigest()==w['sha256']
            value,_=presentation(body);assert hashlib.sha256(G.canonical(value)).hexdigest()==w['article_sha256']
    if (G.ROOT/(P+'receipt.json')).exists():
        r=stage.load_json(P+'receipt.json');assert r['visitor_visible_delta']==r['r2']['byte_delta']==0 and r['inventory_transitions']==12
        for path,h in r['evidence_sha256'].items(): assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PR211 closeout: exact twelve publication transitions; Urban3/review/originals preserved; zero visitor-visible/R2 delta')

if __name__=='__main__': globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
