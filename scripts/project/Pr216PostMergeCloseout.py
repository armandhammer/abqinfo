"""PR216 production closeout: live presentation, unresolved provenance, no new review."""
import copy, gzip, hashlib, json, subprocess, sys, uuid
from datetime import datetime, timezone
import TaskGovernance as G
import Pr215PostMergeCloseout as Shared
from PgsLegislativePublication import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git
from Pr208209Reconciliation import presentation
from BrtPrizeVersionResolution import ID, PAGE, SHA, P as OLD

TASK='pr216-postmerge-closeout-2026-10-07'
P='project-state/governance/'+TASK+'/'
SCRIPT='scripts/project/Pr216PostMergeCloseout.py'
MERGE='01ac444f8bd02bd04b5e9859c25a30a858686e6e'
REVIEWED=PLANNING='dfb0d8f45aef1272f86d215974cfd62e1d888f85'
DEPLOYMENT='d561cce5-70d2-44d3-ae1d-436b7b62e303'
ROUTE='transportation/transit/abq-ride/'
ANCHOR='art-planning-and-development-history'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
OPS=['governance_implementation','inventory_disposition','background_integration']

def now():return datetime.now(timezone.utc).isoformat()
def freeze(path,value):G.write_once(path,value)
def refresh():
    Shared.TASK=TASK;Shared.P=P;Shared.MERGE=MERGE;Shared.OPS=OPS
    Shared.refresh()
def event(op,summary,evidence):
    Shared.P=P;Shared.ID=ID;Shared.event(op,summary,evidence)

def setup():
    assert G.git('rev-parse','HEAD')==MERGE and G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    names=['population.json','authority.json','supersession.json','starting-state.json','implementation.json','progress.json','merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','mobile-entry.png','archive-verification.json','source-verification.json','diagnostic.json','record-updates.json','source-record.json','queue.json','accounting.json','validation.log','receipt.json','integration-intent.json']+[f'contract-v{i}.json' for i in range(1,21)]+['page-'+label+'.html.gz' for label in ['production','merge','preview']]
    paths=[P+x for x in names]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1']
    freeze(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=[ID],families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=sorted(paths)))
    instruction='Explicit current owner PR216 post-merge production verification and background reconciliation ONLY. Verify owner merge '+MERGE+', reviewed head '+REVIEWED+' and successful Cloudflare deployment '+DEPLOYMENT+'. Inspect custom https://abqinfo.com ABQ RIDE / ART Planning and Development History directly in installed Chrome desktop/mobile: exactly one Preserved Copy entry, no Final Report label, complete41/42-page unverified-official-delivery/finality qualifier, unchanged R2/City source links, sound rendering. Compare full reviewed preview/merge deployment/production; fail closed and diagnose if genuine old production persists. Fresh public GET must match2766304 bytes / '+SHA+'. Only after production passes, reconcile '+ID+' as owner-reviewed merged production live BUT still pending review/source_provenance_unresolved, never validated/passed solely from content correction. Preserve all substantive review, source/finality prerequisite, source quality/currentness and historical evidence; close only manual content-review phase. Complete deterministic accounting, CURRENT, active task, receipt, history sealing, full normal/governance/Hugo/rendered/CURRENT/diff checks; integrate background-only main and synchronize planning to exact final main. No R2 or visitor-visible mutation, new source review/population or release of unresolved provenance.'
    freeze(P+'authority.json',dict(artifact_type='owner_authorization',instruction=instruction,authority='Explicit current owner PR216 merged closeout request',candidate_ids=[ID],merge_sha=MERGE,reviewed_head=REVIEWED,deployment_id=DEPLOYMENT,provenance_release_authorized=False,r2_mutation_authorized=False,visitor_visible_change_authorized=False))
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    assert row['status']=='pending review' and row['review_reason']=='source_provenance_unresolved'
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD,'scripts/project/BrtPrizeVersionResolution.py').decode().splitlines()
    protected=history+['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/discovery/retained-source-audit-queue.json']
    freeze(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,prior_planning_sha=PLANNING,content_tree_oid=G.git('rev-parse',MERGE+':content'),selected_row=row,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),protected_sha256={p:G.file_hash(p) for p in protected}))
    refresh()
    active=G.load(G.ACTIVE_TASK);active.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,active)
    G.active_check('mutation','governance_implementation',[ID])
    registry=G.registry();proposals={}
    replace=['owner-brt-prize-version-resolution-2026-10-07','owner-brt-prize-version-resolution-2026-10-07-resumption','decision-brt-prize-version-resolution-2026-10-07-august-finality-exception','decision-brt-prize-version-resolution-2026-10-07','quality-brt-prize-version-resolution-2026-10-07']
    for old in registry['entries'][:]:
        if old['state']!='active' or old['governance_id'] not in replace:continue
        gid=old['governance_id']+'-pr216-postmerge'
        requirement=old['binding_requirement']+' Explicit current owner PR216 closeout supersedes ONLY its prior open/unmerged, awaiting-content-review, feature-only-sync and main-unchanged phase boundaries for '+ID+'. The owner has merged; verify production and record live presentation while preserving pending review and unresolved exact42-page official delivery/finality. No validated/passed source lifecycle or provenance release. Integrate only background closeout main/planning after full validation. All unrelated scope, decisions, quality/currentness, original evidence and prohibitions on new visitor-visible/R2/population changes remain controlling.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Manual content-review phase only closes; factual provenance/finality hold and pending status remain; no unrelated authority or source decision changes.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=requirement,required_actions=[requirement],authority='Explicit current owner PR216 postmerge closeout instruction',effective_date='2026-10-07')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');registry['entries'].append(new)
    assert set(proposals)==set(replace)
    freeze(P+'supersession.json',dict(artifact_type='explicit_phase_only_supersession',proposals=proposals))
    registry['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No visitor-visible or R2 mutation, provenance release, validated transition or new population.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='exact production and blocked-source lifecycle closeout'))
    save(G.REGISTRY,registry);refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='brt-prize-version-resolution-2026-10-07';life['stages'][-1]['end_commit']=MERGE
    sealed={s['path'] for s in life['protected_evidence']}
    for path in history:
        if path not in sealed:life['protected_evidence'].append(dict(path=path,commit=MERGE,sha256=G.file_hash(path)))
    life['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr216PostMergeCloseout',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=f.read_text(encoding='utf-8-sig').replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr216PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR216 closeout guard failed.\' }\nSet-StrictMode -Version Latest',1).replace('$broken = @()','& python "$PSScriptRoot/Pr216PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw \'PR216 production/Hugo parity failed.\' }\n$broken = @()',1);f.write_text(s,encoding='utf-8',newline='\n')
    event('governance_implementation','Exact closeout population/complete registry frozen; phase-only exceptions registered, prior BRT evidence sealed at owner merge; no source/quality review reopened.',P+'starting-state.json');refresh();guard()

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    G.active_check('mutation','governance_implementation',[ID]);guard()
    pr=json.loads(subprocess.check_output(['gh','pr','view','216','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'));assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'))
    check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages');assert check['conclusion']=='success' and check['head_sha']==MERGE and DEPLOYMENT in check['details_url']
    deployment='https://'+DEPLOYMENT[:8]+'.abqinfo.pages.dev/'
    freeze(P+'merge-verification.json',dict(pr=pr,cloudflare_check=check,deployment_id=DEPLOYMENT,merge_deployment=deployment,reviewed_merge_trees_identical=True))
    visible=G.load(OLD+'quality-decision.json')['visible_change'];row=G.load(P+'starting-state.json')['selected_row'];previous=G.load(OLD+'preview-verification.json')
    urls=dict(production='https://abqinfo.com/'+ROUTE,merge=deployment+ROUTE,preview='https://8d7f0e3d.abqinfo.pages.dev/'+ROUTE)
    results=[];articles={};witnesses=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
            for name,width,height in [('desktop',1440,1100),('mobile',390,844)]:
                page=browser.new_page(viewport=dict(width=width,height=height))
                for label,url in dict(canonical=PROD,**urls).items():
                    target=url if label=='canonical' else url+'?pr216_chrome='+uuid.uuid4().hex+'#'+ANCHOR
                    response=page.goto(target,wait_until='networkidle',timeout=90000);assert response.status==200
                    link=page.locator('a[href="'+row['r2_url']+'"]');assert link.count()==1 and link.inner_text()==visible['new_label'],'Production report absent, duplicated or old Final Report label'
                    li=link.locator('xpath=ancestor::li[1]');text=li.inner_text();assert visible['new_description'] in ' '.join(text.split()) and '(Final Report)' not in text
                    assert text==previous['results'][0]['entry_text']
                    source=li.locator('a[href="'+row['source_url']+'"]');assert source.count()==1 and source.inner_text()=='Official City report page and marked draft'
                    assert page.locator('#'+ANCHOR).count()==1 and li.locator('xpath=ancestor::ul[1]/preceding-sibling::h2[1]').get_attribute('id')==ANCHOR
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    li.scroll_into_view_if_needed();box=li.bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
                    if label=='canonical':
                        page.screenshot(path=str(G.ROOT/(P+('production.png' if name=='desktop' else 'mobile.png'))))
                        if name=='mobile':li.screenshot(path=str(G.ROOT/(P+'mobile-entry.png')))
                    results.append(dict(label=label,viewport=name,url=page.url,status=response.status,entry_text=text,archive_url=link.get_attribute('href'),source_url=source.get_attribute('href'),exactly_one_entry=True,unsupported_final_label_absent=True,complete_qualifier=True,anchor_passed=True,no_horizontal_overflow=True))
                page.close()
            browser.close()
        for label,url in urls.items():
            r=requests.get(url+'?pr216_verify='+uuid.uuid4().hex,headers={'Cache-Control':'no-cache, no-store, max-age=0'},timeout=90);r.raise_for_status();value,_=presentation(r.content);articles[label]=value
            path=P+'page-'+label+'.html.gz';(G.ROOT/path).write_bytes(gzip.compress(r.content,mtime=0));witnesses.append(dict(label=label,url=r.url,status=r.status_code,witness=path,sha256=hashlib.sha256(r.content).hexdigest(),article_sha256=G.digest(value),observed_at=now()))
        assert articles['production']==articles['merge']==articles['preview'],'Full production/merge/reviewed article mismatch'
    except Exception as error:
        save(P+'diagnostic.json',dict(result='failed_closed',error=str(error),observations=results,witnesses=witnesses,inventory_mutated=False,merge_deployment_id=DEPLOYMENT,production_url=PROD,observed_at=now()));raise
    freeze(P+'production-render.json',dict(browser='Installed Google Chrome via Playwright',canonical_url=PROD,results=results,observed_at=now(),desktop_mobile_layout_passed=True,canonical_unbusted_and_cachebusted_custom_domain_checked=True))
    freeze(P+'production-verification.json',dict(result='passed',merge_sha=MERGE,reviewed_head=REVIEWED,deployment_id=DEPLOYMENT,production_url=PROD,merge_deployment=deployment,reviewed_preview=urls['preview'],canonical_rendered_production_verified=True,full_article_parity=True,article_sha256=G.digest(articles['production']),exactly_one_entry=True,unsupported_final_label_absent=True,description_qualifier_verified=True,unchanged_archive_source_links=True,desktop_mobile_layout_passed=True,witnesses=witnesses,rendering=P+'production-render.json'))
    r=requests.get(row['r2_url'],headers={'Cache-Control':'no-cache'},timeout=180);r.raise_for_status();assert len(r.content)==2766304 and hashlib.sha256(r.content).hexdigest()==SHA and r.content==(G.ROOT/(OLD+'preserved.pdf')).read_bytes()
    freeze(P+'archive-verification.json',dict(result='passed',url=r.url,r2_key=row['r2_key'],size_bytes=len(r.content),sha256=SHA,exact_public_original=True,full_get=True,status=r.status_code,etag=r.headers.get('ETag'),observed_at=now(),official42page_provenance_proved=False,r2_delta=dict(added=0,deleted=0,overwritten=0,bytes=0)))
    source=requests.get(row['source_url'],timeout=90);source.raise_for_status();assert 'f-scale-of-the-prize.pdf' in source.text
    freeze(P+'source-verification.json',dict(url=source.url,status=source.status_code,sha256=hashlib.sha256(source.content).hexdigest(),same_official_landing_links_marked_draft=True,official42page_delivery_finality_still_unverified=True,observed_at=now()))
    event('governance_implementation','Canonical abqinfo.com Chrome desktop/mobile and complete preview/merge/production article parity passed: one qualified Preserved Copy, same archive/City links, no Final Report label; fresh full public GET identical. This proves live presentation, not final provenance.',P+'production-verification.json');refresh();G.active_check('final');guard()

def current(state):
    f=G.ROOT/'project-state/CURRENT.md';tail=f.read_text(encoding='utf-8-sig').split('[Owner correction]')[1]
    s='# Current project state\n\nPR #216 owner-merged at '+MERGE+'. Production ABQ RIDE / ART Planning and Development History verified directly in Chrome desktop/mobile: one Preserved Copy entry, complete 42/41-page unverified-delivery/finality qualifier, no Final Report label, same R2 and City links. Reviewed preview, exact merge deployment and production article match; full public GET remains 2,766,304 bytes / 49fbec4922fd SHA-256 prefix.\n\nExactly src-e80e0b49a4723c9a is live but still provenance-blocked: pending review / source_provenance_unresolved, NOT validated. Manual content review closed; source/finality prerequisite and original evidence preserved. '+state+' No new population. Closeout visitor-visible/R2 delta 0.\n\nQueue 0 approved / 335 pending (321 governance-gated / 14 source-structural blocked); no owner decision or active publication population.\n\n[Closeout](governance/'+TASK+'/receipt.json) \u00b7 [Production](governance/'+TASK+'/production-verification.json) \u00b7 [Active task](governance/active-task.json) \u00b7 [Queue](ordinary-queue-current.json) \u00b7 [Workflow](governance-workflow.md) \u00b7 [Registry](governance-registry.json).\n\n[Owner correction]'+tail
    assert len(s)<=1800;f.write_text(s,encoding='utf8',newline='\n')

def reconcile():
    assert G.load(P+'production-verification.json')['result']==G.load(P+'archive-verification.json')['result']=='passed'
    prior=G.load(P+'starting-state.json')['selected_row'];quality=copy.deepcopy(prior['quality_assessment']);quality['owner_review_gate']='Owner manually merged PR216; production presentation verified. Content review complete; pending provenance/finality hold remains, no validated transition.'
    decision=copy.deepcopy(prior['publication_quality_decision']);decision['assessment']=quality
    changes=dict(validation_status='Production presentation live/verified after owner merge PR216; exact archive bytes verified. Official42-page delivery/finality remains unresolved: pending review, not validated.',quality_assessment=quality,publication_quality_decision=decision,processing_notes=prior['processing_notes']+['PR216 owner merge '+MERGE+' / deployment '+DEPLOYMENT+' production verified directly at abqinfo.com with Chrome desktop/mobile. Exactly one qualified Preserved Copy, no Final Report label, same R2/City links; complete preview/merge/production parity and exact2766304-byte SHA256 '+SHA+' public GET passed. Manual content review completed. Source status remains pending review / source_provenance_unresolved: live presentation is not conclusive official42-page delivery/finality and does not validate the source. Prior open/unmerged statements are sealed preparation history. Closeout '+P+'receipt.json; no R2/visible mutation or next population.'])
    G.active_check('mutation','inventory_disposition',[ID]);freeze(P+'record-updates.json',[dict(id=ID,changes=changes)]);refresh();G.active_check('mutation','inventory_disposition',[ID])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    inv=G.load('project-state/master-inventory.json');row=next(x for x in inv['candidates'] if x['id']==ID)
    save(P+'source-record.json',dict(candidate=row,lifecycle=dict(workflow_state='owner_reviewed_merged_production_live_provenance_blocked',production_live=True,owner_merge_verified=True,manual_content_review_pending=False,source_blocker_cleared=False,finality_established=False,status='pending review',review_reason='source_provenance_unresolved',validated=False),production_evidence=P+'production-verification.json'))
    start=G.load(P+'starting-state.json');old=G.load(start['source_queue']);q=copy.deepcopy(old);pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];gated=pending&set(old['gated_pending_ids']);blocked=pending&set(old['source_or_structural_blocked_pending_ids']);ungated=pending-gated-blocked
    assert ID in blocked and gated.isdisjoint(blocked) and (len(approved),len(pending),len(gated),len(blocked))==(0,335,321,14)
    q.update(artifact_type='pr216_postmerge_closeout_queue',recorded_at=inv['generated_at'],source_queue_artifact=start['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),approved_count=len(approved),pending_ids=sorted(pending),pending_review_count=len(pending),gated_pending_ids=sorted(gated),gated_pending_count=len(gated),source_or_structural_blocked_pending_ids=sorted(blocked),source_or_structural_blocked_pending_count=len(blocked),ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),actionable_ungated_pending_ids=sorted(ungated),genuinely_actionable_ungated_pending_count=len(ungated),in_progress_publication=None,actionability_basis='Production wording correction is live; exact42-page source/finality prerequisite remains. Pending/gated/source-blocked membership recomputed deterministically without hold release.',newly_approved_backlog=[])
    q['brt_prize_resolution']=dict(candidate_id=ID,finality_established=False,source_blocker_cleared=False,visible_correction_owner_review=False,pr=216,merged=True,merge_sha=MERGE,production_live=True,production_verification=P+'production-verification.json',canonical_status='pending review',review_reason='source_provenance_unresolved')
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    refresh();G.active_check('mutation','inventory_disposition',[ID]);subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True,stdout=subprocess.DEVNULL)
    cp=G.load('project-state/checkpoint.json');cp['pr216_postmerge_closeout']=dict(state='production_live_source_blocked_validation_pending',merge_sha=MERGE,reviewed_head=REVIEWED,receipt=P+'receipt.json',source_blocker_cleared=False);cp['resume_command']='PR216 merged/production verified; complete background closeout only. Source/finality remains pending; no next population authorized.';save('project-state/checkpoint.json',cp)
    save(P+'accounting.json',dict(live_provenance_blocked_ids=[ID],validated_ids=[],approved=0,pending=335,governance_gated=321,source_structural_blocked=14,actionable=0,owner_source_decisions=0,owner_content_review_pending=False,in_progress_publication=None,visitor_visible_delta=0,r2_delta=0))
    save(P+'progress.json',dict(state='production_live_source_blocked_reconciled',remaining=['full validation','background synchronization'],new_population_authorized=False))
    current('Full closeout validation/synchronization pending.');event('inventory_disposition','Only current content-review lifecycle reconciled: live presentation but source/finality remains pending and blocked. Historical quality/provenance untouched except completed owner-review phase; deterministic counts/membership unchanged.',P+'accounting.json');refresh();G.active_check('final');guard()

def check_row_delta(before,after,changes):
    allowed={'validation_status','quality_assessment','publication_quality_decision','processing_notes'}
    assert set(changes)==allowed
    assert {k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}<=allowed|{'updated_at'}
    expected=copy.deepcopy(before);expected.update(changes);expected['updated_at']=after['updated_at'];assert after==expected
    assert after['status']=='pending review' and after['review_reason']=='source_provenance_unresolved'
    assert after['validation_status']!='passed' and 'live/verified' in after['validation_status'] and 'unresolved' in after['validation_status']
    assert after['processing_notes'][:len(before['processing_notes'])]==before['processing_notes']
    for key in ['quality_assessment','publication_quality_decision']:
        prior=copy.deepcopy(before[key]);value=copy.deepcopy(after[key]);qa=prior if key=='quality_assessment' else prior['assessment'];qb=value if key=='quality_assessment' else value['assessment'];qa.pop('owner_review_gate');qb.pop('owner_review_gate');assert prior==value

def guard():
    stage=StageSnapshot(TASK);pop=stage.load_json(P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json'));start=stage.load_json(P+'starting-state.json')
    assert pop['candidate_ids']==[ID] and pop['baseline_commit']==MERGE and pop['operation_classes']==OPS
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid']);paths=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE));assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    before=json.loads(git('show',MERGE+':project-state/master-inventory.json'));after=stage.load_json('project-state/master-inventory.json');a={r['id']:r for r in before['candidates']};b={r['id']:r for r in after['candidates']};assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<={ID}
    derived={'candidates','counts','next_pending_id','generated_at'};assert {k:v for k,v in before.items() if k not in derived}=={k:v for k,v in after.items() if k not in derived}
    if a[ID]!=b[ID]:
        request=stage.load_json(P+'record-updates.json')[0];check_row_delta(a[ID],b[ID],request['changes'])
        for key,value in [('status','validated'),('review_reason',None),('r2_url','https://invalid.example/replacement.pdf'),('date','2014'),('validation_status','passed')]:
            bad=copy.deepcopy(b[ID]);bad[key]=value
            try:check_row_delta(a[ID],bad,request['changes'])
            except AssertionError:pass
            else:raise AssertionError('Unsafe lifecycle accepted: '+key)
        bad=copy.deepcopy(b[ID]);bad['quality_assessment']['provenance_gate']='resolved'
        try:check_row_delta(a[ID],bad,request['changes'])
        except AssertionError:pass
        else:raise AssertionError('Source gate release accepted')
        assert stage.load_json(P+'production-verification.json')['result']==stage.load_json(P+'archive-verification.json')['result']=='passed'
    if (G.ROOT/(P+'accounting.json')).exists():
        q=stage.load_json(P+'queue.json');old=stage.load_json(start['source_queue']);assert q['pending_ids']==sorted(r['id'] for r in b.values() if r['status']=='pending review')
        for field in ['pending_ids','gated_pending_ids','source_or_structural_blocked_pending_ids','actionable_ungated_pending_ids']:assert q[field]==old[field]
        assert ID in q['source_or_structural_blocked_pending_ids'] and (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,335,321,14) and q['in_progress_publication'] is None
        assert q['brt_prize_resolution']['visible_correction_owner_review'] is False and q['brt_prize_resolution']['production_live'] and not q['brt_prize_resolution']['source_blocker_cleared']
        cp=stage.load_json('project-state/checkpoint.json');allowed={'recorded_at','counts_by_status','next_pending_id','completed_item_range','remaining_nonterminal','resume_command','pr216_postmerge_closeout'};assert {k:v for k,v in cp.items() if k not in allowed}=={k:v for k,v in start['checkpoint_before'].items() if k not in allowed};assert cp['counts_by_status']==after['counts']
        assert stage.load_json(P+'source-record.json')['lifecycle']['validated'] is False
        if (G.ROOT/(P+'derived-queue-reconciliation.json')).exists():
            path='project-state/discovery/consolidated-human-review-queue.json';prior=json.loads(git('show',MERGE+':'+path));current_value=stage.load_json(path)
            assert current_value['record_count']==current_value['package_count']==0
            assert {k:v for k,v in prior.items() if k!='inventory_sha256'}=={k:v for k,v in current_value.items() if k!='inventory_sha256'}
    if (G.ROOT/(P+'receipt.json')).exists():
        r=stage.load_json(P+'receipt.json');assert r['visitor_visible_delta']==r['r2_delta']==0 and not r['source_blocker_cleared'] and r['validated_ids']==[]
        for path,h in r['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS PR216 exact live-but-provenance-blocked lifecycle; unchanged content/R2/unrelated rows; sealed BRT review and unchanged335 pending')

def repair_derived_queue():
    import importlib.util,re
    G.active_check('mutation','governance_implementation',[ID])
    pop=G.load(P+'population.json');pop['artifact_paths'] += [P+'population-v2.json',P+'validation-attempt-1.log',P+'derived-queue-reconciliation.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    freeze(P+'population-v2.json',pop)
    raw=(G.ROOT/'tmp/pr216-validation.log').read_text(encoding='utf8');raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    (G.ROOT/(P+'validation-attempt-1.log')).write_text('\n'.join(x.expandtabs(4).rstrip() for x in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    refresh();G.active_check('mutation','governance_implementation',[ID])
    path='project-state/discovery/consolidated-human-review-queue.json';before=G.load(path)
    spec=importlib.util.spec_from_file_location('pr216_zero_case_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);owner,report=module.build()
    assert before['record_count']==owner['record_count']==before['package_count']==owner['package_count']==0
    assert {k:v for k,v in before.items() if k!='inventory_sha256'}=={k:v for k,v in owner.items() if k!='inventory_sha256'}
    assert (G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').read_text(encoding='utf8')==report
    save(path,owner)
    freeze(P+'derived-queue-reconciliation.json',dict(artifact_type='deterministic_derived_queue_checksum_reconciliation',failed_validation=P+'validation-attempt-1.log',issue='Consolidated zero-case queue retained prior inventory SHA after authorized source lifecycle update.',resolved_by='Existing deterministic queue builder; exactly inventory_sha256 changed, records/packages remain0 and Markdown unchanged.',before_inventory_sha256=before['inventory_sha256'],after_inventory_sha256=owner['inventory_sha256'],same_frozen_candidate_ids=[ID],new_review_population=False))
    event('governance_implementation','Normal suite exposed stale derived zero-case owner-queue inventory checksum; deterministic builder refreshed exactly checksum. Failed-run log retained, no membership/owner decision or publication/source hold change.',P+'derived-queue-reconciliation.json');refresh();G.active_check('final');guard()

def render():
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS sealed PR216 production evidence');return
    value,_=presentation((G.ROOT/'tmp/site-build'/ROUTE/'index.html').read_bytes());assert G.digest(value)==stage.load_json(P+'production-verification.json')['article_sha256'];print('PASS PR216 Hugo complete article equals verified custom-domain production/merge/reviewed preview')

def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard();raw=(G.ROOT/'tmp/pr216-validation.log').read_text(encoding='utf8');assert '"Hugo": "passed"' in raw and 'PR216 Hugo complete article' in raw
    import re
    raw=re.sub(r'\x1b\[[0-9;]*m','',raw);(G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    freeze(P+'integration-intent.json',dict(authority=P+'authority.json',expected_main=MERGE,expected_planning_snapshot=PLANNING,strategy='Atomic non-force fast-forward of main and planning to background-only closeout; preserve owner merge and reviewed history.',final_ref_evidence='project-state/campaign-runtime/'+TASK+'/final-refs.json',no_visitor_visible_change=True,no_r2_mutation=True,no_new_population=True))
    evidence=['merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','mobile-entry.png','archive-verification.json','source-verification.json','record-updates.json','source-record.json','queue.json','accounting.json','validation.log'];c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    freeze(P+'receipt.json',dict(task_id=TASK,state='production_verified_live_source_blocked_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,deployment_id=DEPLOYMENT,production_result='passed',production_url=PROD,live_provenance_blocked_ids=[ID],validated_ids=[],source_blocker_cleared=False,lifecycle=G.load(P+'source-record.json')['lifecycle'],queue=G.load(P+'accounting.json'),visitor_visible_delta=0,r2_delta=0,normal_validation='passed',owner_decision_required=False,no_new_population=True,evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Owner-merged PR216 verified directly on custom production in Chrome desktop/mobile with exact links/qualifier/one entry and full preview/merge parity. Only live content-review lifecycle reconciled; source remains pending/provenance-blocked, never validated. Preserve all substantive quality/currentness/version research, original bytes/history/unrelated decisions and R2. Deterministic queue unchanged; no follow-on population; authorized background refs only.',evidence=[P+'production-verification.json',P+'archive-verification.json',P+'source-record.json',P+'accounting.json']) for r in c['resolved_rules']},integration_intent=P+'integration-intent.json',visual_inspection='Custom-domain desktop/mobile and full mobile entry screenshots inspected; complete qualifier legible, one Preserved Copy and same links, sound wrapping/no overflow.'))
    cp=G.load('project-state/checkpoint.json');cp['pr216_postmerge_closeout']['state']='complete_production_live_source_blocked';cp['resume_command']='PR216 production-verified closeout complete; source/finality remains pending. No next review population begun or authorized.';save('project-state/checkpoint.json',cp)
    current('Full normal/governance/sealed-history/Hugo/rendered checks passed; background main/planning synchronization authorized.')
    save(P+'progress.json',dict(state='complete',remaining=[],source_prerequisite='Exact authoritative42-page delivery/finality remains unresolved, not an owner-preference question.',integration='Atomic background main/planning synchronization authorized; final refs in runtime journal.',no_next_population=True))
    event('background_integration','Full normal suite and exact production/archive/source parity passed; live presentation plus unresolved source hold preserved, closeout ready for atomic background synchronization.',P+'integration-intent.json');refresh();G.active_check('final');guard()

def integrate():
    def refs():return {x.split()[1]:x.split()[0] for x in subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()}
    expected={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING};assert refs()==expected and G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active);G.active_check('final')
    paths=G.changed_paths(MERGE);assert not any(p.startswith('backups/') for p in paths)
    subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--check'],check=True);subprocess.run(['git','commit','--quiet','-m','Complete PR216 production closeout with provenance hold preserved'],check=True)
    head=G.git('rev-parse','HEAD');assert refs()==expected
    for old in [MERGE,PLANNING]:subprocess.run(['git','merge-base','--is-ancestor',old,head],check=True)
    journal='project-state/campaign-runtime/'+TASK+'/integration-journal.json';intent=dict(operation='atomic background closeout synchronization',authority=P+'authority.json',sha=head,expected_refs=expected,intent_at=now());save(journal,intent)
    result=subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],capture_output=True,text=True);intent.update(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,result_at=now());save(journal,intent);print(result.stdout+result.stderr);assert result.returncode==0
    subprocess.run(['git','switch','main'],check=True);subprocess.run(['git','merge','--ff-only',head],check=True);subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    remote=refs();assert remote=={'refs/heads/main':head,'refs/heads/chatgpt/planning-snapshot':head} and not G.git('status','--porcelain');G.active_check('final');guard()
    save('project-state/campaign-runtime/'+TASK+'/final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=remote,verified_at=now(),worktree_clean=True,merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,validation='passed',r2_delta=0,visitor_visible_delta=0,source_blocker_cleared=False,no_new_population=True))
    print('Final synchronized main/planning-snapshot:',head)

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
