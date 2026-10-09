"""Existing draft PR218 production/lifecycle closeout with read-only final; no visible or R2 change."""
import copy, gzip, hashlib, json, re, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
import Pr215PostMergeCloseout as Shared
from PgsLegislativePublication import save
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

TASK='pr218-postmerge-closeout-2026-10-08'
P='project-state/governance/'+TASK+'/'
SCRIPT='scripts/project/Pr218PostMergeCloseout.py'
MERGE='c6c0dd74f771a9686faf55692f5d1da70aeaa1ad'
REVIEWED='587a61091be6505724151c05254a7b53fda4c20e'
PLANNING='7bf604d5c3078a6016099ee3da398e711dc265dd'
IDS=['src-a614f077ace20401','src-27b939c34a1c59fc']
PAGE='content/transportation/bicycling/bike-plans.md'
OLD='project-state/governance/bikeway-2014-draft-resolution-2026-10-08/'
ROUTE='transportation/bicycling/bike-plans/'
ANCHOR='previous-bike-plans'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
PREVIEW='https://a61ce7de.abqinfo.pages.dev/'+ROUTE+'#'+ANCHOR
MERGE_PREVIEW='https://5f7fccc3.abqinfo.pages.dev/'+ROUTE+'#'+ANCHOR
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
    names=['population.json','authority.json','supersession.json','starting-state.json','baseline-records.json','implementation.json','progress.json','merge-verification.json','production-verification.json','source-verification.json','production.png','mobile.png','page-production.html.gz','page-merge.html.gz','page-preview.html.gz','accounting.json','queue.json','receipt.json','integration-intent.json','validation.log','summary.md','final-refs.json']+[f'contract-v{i}.json' for i in range(1,41)]
    paths=[P+n for n in names]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1']
    freeze_once(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=IDS,families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=sorted(paths)))
    instruction='Explicit current owner PR218 closeout: verify owner merge '+MERGE+' and custom abqinfo.com directly in installed Chrome against reviewed preview and successful merge deployment. Confirm exact 2014 Pre-Adoption Draft — Chapters 1–6 label, description and archived official City source, subordinate to unchanged 2015 final; desktop/mobile rendering and links. On success close existing validated lifecycle and owner review through additive immutable-history reconciliation; run full validation and synchronize main/planning with durable tracked refs. Preserve original provenance, all historical evidence, inventory, R2 and content. No new document-review population or visitor-visible changes.'
    freeze_once(P+'authority.json',dict(artifact_type='owner_postmerge_authorization',authority='Explicit current user PR218 post-merge closeout request',instruction=instruction,candidate_ids=IDS,merge_sha=MERGE,reviewed_head=REVIEWED,visitor_visible_change_authorized=False,r2_mutation_authorized=False,new_review_population_authorized=False))
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates'] if r['id'] in IDS}
    assert set(rows)==set(IDS) and rows[IDS[0]]['status']=='validated' and rows[IDS[1]]['status']=='validated'
    freeze_once(P+'baseline-records.json',rows)
    protected=git('ls-tree','-r','--name-only',MERGE,'--',OLD).decode().splitlines()+[PAGE,'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md','project-state/discovery/retained-source-audit-queue.json']
    freeze_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,prior_planning_sha=PLANNING,content_tree_oid=G.git('rev-parse',MERGE+':content'),baseline_page_sha256=G.file_hash(PAGE),selected_rows=rows,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),protected_sha256={p:G.file_hash(p) for p in sorted(set(protected))},queue_counts=G.load(OLD+'accounting.json')['queue']))
    refresh();G.active_check('review','governance_implementation',IDS)
    save(P+'progress.json',dict(stage='merged_exact_two_record_population_frozen',production_verified=False,remaining=['production_and_public_source_verification','phase_only_governance_reconciliation','full_validation','background_main_planning_sync']))

def expected_links():
    s=(G.ROOT/PAGE).read_text(encoding='utf-8-sig');part=s[s.index('## Previous Bike Plans'):s.index('## Related Bicycle Policy')]
    return [dict(text=t,url=u) for t,u in re.findall(r'\[([^\]]+)\]\((https://[^)]+)\)',part)]

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    G.active_check('review','governance_implementation',IDS)
    pr=json.loads(subprocess.check_output(['gh','pr','view','218','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'))
    assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','-X','GET','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'))
    check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages' and x['conclusion']=='success' and '5f7fccc3' in x['details_url'])
    assert check['head_sha']==MERGE
    save(P+'merge-verification.json',dict(artifact_type='owner_merge_and_cloudflare_deployment_verification',pr=pr,cloudflare_check=check,merge_preview=MERGE_PREVIEW,reviewed_preview=PREVIEW,reviewed_merge_trees_identical=True))
    urls=dict(preview=PREVIEW,reviewed_pr_body='https://fbf691db.abqinfo.pages.dev/'+ROUTE+'#'+ANCHOR,merge=MERGE_PREVIEW,production=PROD);expect=expected_links();assert len(expect)==16
    results=[];sections={};html={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for viewport,w,h in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=w,height=h))
            for label,url in urls.items():
                target=url.split('#')[0]+'?pr218_closeout='+uuid.uuid4().hex+'#'+ANCHOR
                response=page.goto(target,wait_until='networkidle',timeout=90000);assert response.status==200,(label,viewport,response.status)
                section=page.locator('#'+ANCHOR).locator('xpath=following-sibling::ul[1]');assert section.count()==1
                links=section.locator('a').evaluate_all('(els)=>els.map(a=>({text:a.innerText.trim(),url:a.href}))')
                assert links==expect,(label,viewport,links,expect)
                text=' '.join(section.inner_text().split());assert '2014 Pre-Adoption Draft — Chapters 1–6' in text and DESCRIPTION in text
                draft=section.get_by_role('link',name=TITLE,exact=True)
                parent=draft.locator('xpath=ancestor::li[1]/ancestor::li[1]')
                assert parent.locator('a').first.inner_text()=='2015 Bikeways and Trails Facilities Plan — Final'
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                if label=='production':
                    section.scroll_into_view_if_needed();page.evaluate('window.scrollBy(0,-75)')
                    page.screenshot(path=str(G.ROOT/(P+('production.png' if viewport=='desktop' else 'mobile.png'))))
                sections[(label,viewport)]=dict(text=text,links=links)
                results.append(dict(site=label,viewport=viewport,url=page.url,status=response.status,anchor_count=1,links=links,section_text=text,exact_draft_label_description_source=True,subordinate_to_unchanged_2015_final=True,all_historical_links_intact=True,no_horizontal_overflow=True))
                if viewport=='desktop' and label!='reviewed_pr_body':html[label]=page.content().encode('utf8')
            page.close()
        browser.close()
    for viewport in ['desktop','mobile']:
        assert sections[('preview',viewport)]==sections[('reviewed_pr_body',viewport)]==sections[('merge',viewport)]==sections[('production',viewport)]
    for label,body in html.items():(G.ROOT/(P+'page-'+label+'.html.gz')).write_bytes(gzip.compress(body,mtime=0))
    save(P+'production-verification.json',dict(artifact_type='direct_chrome_custom_domain_production_parity',checked_at=now(),production_url=PROD,reviewed_preview=PREVIEW,merge_deployment=MERGE_PREVIEW,expected_historical_links=expect,checks=results,full_section_parity=True,production_result='passed',screenshots=[P+'production.png',P+'mobile.png']))
    event('governance_implementation','Direct Chrome desktop/mobile confirms production Previous Bike Plans exactly matches reviewed preview and merge deployment: exact draft label/description/archived City link, subordinate to unchanged 2015 final, all 16 links intact.',P+'production-verification.json')
    refresh()
    if any(s['id']==TASK for s in G.load('project-state/workflow-stage-lifecycle.json')['stages']):guard()

def verify_sources():
    import requests
    G.active_check('review','governance_implementation',IDS)
    assert G.load(P+'production-verification.json')['production_result']=='passed'
    rows=G.load(P+'baseline-records.json');checks=[]
    urls=[(i,rows[i]['r2_url'],'existing_R2_original') for i in IDS]
    urls.append((IDS[0],ARCHIVE,'archived_official_City_draft'))
    for id,url,kind in urls:
        h=hashlib.sha256();count=0
        with requests.get(url,stream=True,timeout=90,headers={'Cache-Control':'no-cache'}) as response:
            response.raise_for_status()
            for block in response.iter_content(1024*1024):
                if block:h.update(block);count+=len(block)
            final_url=response.url;status=response.status_code
        assert count==rows[id]['size_bytes'] and h.hexdigest()==rows[id]['checksum_sha256']
        checks.append(dict(candidate_id=id,kind=kind,requested_url=url,final_url=final_url,http_status=status,size_bytes=count,sha256=h.hexdigest(),matches_record=True))
    save(P+'source-verification.json',dict(artifact_type='fresh_public_archive_and_official_source_checks',checked_at=now(),full_public_gets=checks,r2_writes=0,result='passed',other_links='All 16 exact rendered historical targets match reviewed preview and successful merge deployment.'))
    event('governance_implementation','Fresh full GETs confirm both unchanged preserved R2 originals and archived official City draft exact sizes/SHA256.',P+'source-verification.json');refresh()

def reconcile():
    assert G.load(P+'production-verification.json')['production_result']=='passed'
    assert G.load(P+'source-verification.json')['result']=='passed'
    G.active_check('mutation','governance_implementation',IDS)
    registry=G.load(G.REGISTRY);prior=[x for x in registry['entries'] if x['state']=='active' and 'bikeway-2014-draft-resolution-2026-10-08' in x['governance_id']]
    assert len(prior)==8,[x['governance_id'] for x in prior]
    exception=' Explicit current owner PR218 phase exception solely for src-a614f077ace20401: owner merge '+MERGE+' and direct Chrome preview/merge/production parity close only former unmerged owner-review and feature-only phase boundaries. The existing validated historical Chapters 1–6 draft remains subordinate to the unchanged 2015 final. Preserve the exact former City-delivery finding, scope/quality, date limitations, originals, R2 and all other decisions. Complete background closeout and main/planning synchronization after full validation; no new document review.'
    proposals={}
    for old in prior:
        old_id=old['governance_id'];new_id=old_id+'-pr218-postmerge'
        requirement=old['binding_requirement']+exception
        proposals[old_id]=dict(authorized=True,existing_governance_id=old_id,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=[P+'merge-verification.json',P+'production-verification.json',P+'source-verification.json'],proposed_replacement=requirement,consequences='Only manual content-review phase closes and verified production/background refs are recorded. Existing validated draft status, draft/final relationship, exact-byte provenance finding, archive objects and all unrelated decisions remain unchanged.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=new_id,title=old['title']+' — PR218 verified production phase',state='active',authority='Explicit current owner PR218 post-merge closeout instruction',decision_date='2026-10-08',effective_date='2026-10-08',binding_requirement=requirement,required_actions=[requirement],supersedes=[old_id],implementation_status='Owner-merged production verified; existing two-record dispositions preserved')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        new['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in old.get('settled_decisions',[])]+[dict(question_id=TASK+':production-lifecycle',decision='Existing validated draft publication is production-reconciled and owner review closed; comparator and all inventory unchanged.')]
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');registry['entries'].append(new)
    freeze_once(P+'supersession.json',dict(artifact_type='explicit_postmerge_phase_only_supersession',proposals=proposals))
    owner=G.load(P+'authority.json')['instruction']
    registry['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='PR218 exact two-record post-merge closeout',scope=dict(candidate_ids=IDS,task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-08',effective_date='2026-10-08',state='active',controlling_artifacts=[dict(path=P+n,sha256=G.file_hash(P+n),binding_pointers=['/']) for n in ['authority.json','supersession.json']],binding_requirement=owner,required_actions=[owner],prohibited_actions=['No visitor-visible, inventory, R2 or new review-population mutation.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='exact production/lifecycle/background closeout'))
    save(G.REGISTRY,registry)
    refresh();G.active_check('mutation','governance_implementation',IDS)
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json');assert lifecycle['stages'][-1]['id']=='bikeway-2014-draft-resolution-2026-10-08'
    lifecycle['stages'][-1]['end_commit']=MERGE
    history=git('ls-tree','-r','--name-only',MERGE,'--',OLD).decode().splitlines();sealed={x['path'] for x in lifecycle['protected_evidence']}
    for path in history:
        if path not in sealed:lifecycle['protected_evidence'].append(dict(path=path,commit=MERGE,sha256=G.file_hash(path)))
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr218PostMergeCloseout',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';text=runner.read_text(encoding='utf-8-sig')
    text=text.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr218PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw "PR218 closeout exact-delta guard failed" }\nSet-StrictMode -Version Latest',1)
    text=text.replace('$broken = @()','& python "$PSScriptRoot/Pr218PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw "PR218 production/Hugo parity failed" }\n$broken = @()',1)
    runner.write_text(text,encoding='utf-8',newline='\n')
    q=G.load(G.load(P+'starting-state.json')['source_queue'])
    assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,333,321,12)
    save(P+'accounting.json',dict(artifact_type='existing_draft_postmerge_lifecycle_accounting',statuses={i:'validated' for i in IDS},status_transitions=0,owner_review_phase='closed_by_merged_PR218',production_result='passed',queue_counts=dict(approved=0,pending=333,governance_gated=321,source_structural_blocked=12,actionable=0,human_review=0),remaining_nonterminal=884,source_queue=G.load(P+'starting-state.json')['source_queue'],visitor_visible_delta=0,r2_delta=0,historical_evidence_preserved=True,new_review_population=False))
    cp=G.load('project-state/checkpoint.json')
    cp['pr218_postmerge_closeout']=dict(state='production_verified_validation_required',merge_sha=MERGE,candidate_ids=IDS,r2_delta=0,visitor_visible_delta=0,owner_review_pending=False)
    cp['resume_command']='PR218 production verified; complete background validation and branch synchronization. No new document review.'
    save('project-state/checkpoint.json',cp)
    current('Full closeout validation and branch synchronization remain to be completed.')
    save(P+'progress.json',dict(stage='production_verified_lifecycle_reconciled',remaining=['full_validation','background_main_planning_sync']))
    event('governance_implementation','Eight scoped phase replacements close former unmerged-review boundary; sealed provenance/quality/history, inventory and queues preserved.',P+'supersession.json')
    event('inventory_disposition','Existing validated draft lifecycle confirmed; zero transitions, comparator unchanged, owner review closed.',P+'accounting.json')
    refresh();G.active_check('final');guard()


TITLE='2014 Pre-Adoption Draft — Chapters 1–6'
ARCHIVE='https://web.archive.org/web/20170125013542id_/http://www.cabq.gov/planning/documents/BikewaysTrailsFacilityPlan.pdf'
DESCRIPTION='The 131-page pre-adoption draft preserves Chapters 1–6, including earlier project and cost estimates, advisory-committee options, policies, and implementation proposals. It contains map placeholders; the separately issued design manual is not included.'

def current(status):
    path=G.ROOT/'project-state/CURRENT.md'
    tail=path.read_text(encoding='utf-8-sig').split('[Owner correction]')[1]
    body='# Current project state\n\nPR #218 owner-merged at '+MERGE+'. Production Previous Bike Plans was verified directly on custom abqinfo.com in Chrome desktop/mobile against reviewed preview and successful merge deployment. Exact 2014 Pre-Adoption Draft — Chapters 1–6 label, qualified description and archived official City source match; subordinate placement under the unchanged 2015 final and all 16 historical links are correct. Both preserved R2 originals and archived City draft pass fresh full size/SHA256 checks.\n\nExisting draft remains validated; owner review closed. Original provenance, date limitations, complete-document comparison and sealed receipts preserved. ZERO visitor-visible/inventory/R2 delta; no new document review. '+status+'\n\nQueue: 0 approved /333 pending (321 gated /12 source-structural blocked), 0 actionable /human review; remaining nonterminal884.\n\n[Receipt](governance/'+TASK+'/receipt.json) · [Production](governance/'+TASK+'/production-verification.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n[Owner correction]'+tail
    if not (G.ROOT/(P+'receipt.json')).exists():
        body=body.replace('[Receipt](governance/'+TASK+'/receipt.json)','[Closeout accounting](governance/'+TASK+'/accounting.json)')
    assert len(body)<=1800,len(body)
    path.write_text(body,encoding='utf8',newline='\n')

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json');pop=stage.load_json(P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json'))
    assert pop['candidate_ids']==IDS and pop['pages']==[PAGE] and pop['baseline_commit']==MERGE
    assert pop['operation_classes']==OPS
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    paths=set(G.changed_paths(MERGE)) if not stage.end else set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines())
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():
        if path=='project-state/discovery/consolidated-human-review-queue.json' and (G.ROOT/(P+'derived-queue-reconciliation.json')).exists():
            before=json.loads(git('show',MERGE+':'+path));after=stage.load_json(path)
            assert {k:v for k,v in before.items() if k!='inventory_sha256'}=={k:v for k,v in after.items() if k!='inventory_sha256'}
            assert after['record_count']==after['package_count']==0
            assert after['inventory_sha256']==hashlib.sha256(canonical_bytes(stage.read_bytes('project-state/master-inventory.json'))).hexdigest()
        else:assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    original=json.loads(git('show',MERGE+':'+G.REGISTRY));registered=stage.load_json(G.REGISTRY)
    original_by={x['governance_id']:x for x in original['entries']};after_by={x['governance_id']:x for x in registered['entries']}
    replacements=stage.load_json(P+'supersession.json')['proposals'] if (G.ROOT/(P+'supersession.json')).exists() else {}
    for id,row in original_by.items():
        after=copy.deepcopy(after_by[id]);prior=copy.deepcopy(row)
        if id in replacements:
            for key in ['state','superseded_by','supersession_evidence']:after.pop(key,None);prior.pop(key,None)
        # Existing implementation-code hash refresh is required by standing registry rules.
        for value in [after,prior]:
            for item in value['controlling_artifacts']:
                if item.get('binding_pointers')==['/implementation']:item.pop('sha256',None)
        assert after==prior,id
    assert set(after_by)-set(original_by)=={'owner-'+TASK}|{id+'-pr218-postmerge' for id in replacements}
    cp=stage.load_json('project-state/checkpoint.json');before=start['checkpoint_before']
    allowed={'pr218_postmerge_closeout','resume_command','completed_item_range'}
    assert {k:v for k,v in cp.items() if k not in allowed}=={k:v for k,v in before.items() if k not in allowed}
    if (G.ROOT/(P+'accounting.json')).exists():
        a=stage.load_json(P+'accounting.json');assert a['statuses']=={i:'validated' for i in IDS}
        assert a['status_transitions']==a['visitor_visible_delta']==a['r2_delta']==0
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json')
        assert receipt['normal_validation']=='passed' and receipt['owner_review_pending'] is False
        for path,h in receipt['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS PR218 exact closeout: existing validated draft, read-only final, content/inventory/R2, queue membership and sealed evidence unchanged')

def render():
    from html.parser import HTMLParser
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS sealed PR218 production evidence');return
    class Section(HTMLParser):
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
    section=Section();section.feed((G.ROOT/'tmp/site-build'/ROUTE/'index.html').read_text(encoding='utf8'))
    assert section.heading and section.done and section.links==expected_links()
    text=' '.join(' '.join(section.parts).split())
    assert text==G.load(P+'production-verification.json')['checks'][0]['section_text']
    print('PASS PR218 Hugo historical section matches direct Chrome production/merge/reviewed preview')

def finish():
    G.active_check('mutation','governance_implementation',IDS);guard()
    raw=(G.ROOT/'tmp/pr218-full-validation.log').read_text(encoding='utf8')
    assert '"Hugo": "passed"' in raw and 'PASS PR218 Hugo historical section' in raw
    raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(x.expandtabs(4).rstrip() for x in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    evidence=['merge-verification.json','production-verification.json','source-verification.json','production.png','mobile.png','accounting.json','summary.md','derived-queue-reconciliation.json','validation-attempt-2.log','validation.log']
    contract=G.load(G.load(G.ACTIVE_TASK)['contract'])
    freeze_once(P+'receipt.json',dict(artifact_type='existing_draft_postmerge_closeout_receipt',task_id=TASK,state='production_verified_lifecycle_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,production_result='passed',lifecycle=dict(candidate_id=IDS[0],status='validated',production_live=True,owner_review_pending=False),owner_review_pending=False,read_only_comparator=IDS[1],inventory_status_transitions=0,visitor_visible_delta=0,r2_delta=dict(objects=0,bytes=0,uploads=0,overwrites=0,deletions=0),queue_counts=G.load(P+'accounting.json')['queue_counts'],remaining_nonterminal=884,historical_evidence_preserved=True,new_document_review_population=False,normal_validation='passed',validation_log=P+'validation.log',evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Only current production/live lifecycle and owner-review phase close. Complete prior source/scope/quality decisions and sealed receipts preserved; no content/inventory/R2/queue membership changes.',evidence=[P+'production-verification.json',P+'source-verification.json',P+'accounting.json',P+'validation.log']) for r in contract['resolved_rules']},visual_inspection='Production Chrome screenshots inspected at desktop 1440x1100 and mobile 390x844; draft nested under final, clear wrapping, exact description/source and no horizontal overflow.',final_refs='Tracked final-refs.json will record the independently observed completed background integration, followed by one evidence transport commit; no recursive self-reference.'))
    cp=G.load('project-state/checkpoint.json');cp['pr218_postmerge_closeout']['state']='production_verified_validation_passed_owner_review_closed'
    cp['completed_item_range']='PR218 owner merge '+MERGE+' production verified; existing 2014 Chapters1–6 draft validated historical lifecycle confirmed, owner review closed, original provenance/R2 unchanged.'
    cp['resume_command']='PR218 production-verified closeout and full validation complete; perform authorized background branch integration. No new document review.'
    save('project-state/checkpoint.json',cp)
    current('Full normal validation passed; authorized background branch integration is the remaining closeout step.')
    save(P+'progress.json',dict(stage='production_verified_validation_passed',remaining=['background_main_planning_sync'],new_document_review_population=False))
    event('background_integration','Full validation passed; authorized non-force synchronization of background closeout and durable observed ref evidence only.',P+'receipt.json')
    refresh();G.active_check('final');guard()

def refs():
    return {line.split()[1]:line.split()[0] for line in subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()}

def integrate():
    expected={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING}
    assert refs()==expected
    G.active_check('mutation','background_integration',IDS);guard()
    G.active_check('final');guard()
    paths=G.changed_paths(MERGE);subprocess.run(['git','add','--',*paths],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','--quiet','-m','Complete PR218 governed production and historical draft lifecycle closeout'],check=True)
    head=G.git('rev-parse','HEAD');assert refs()==expected
    for old in expected.values():subprocess.run(['git','merge-base','--is-ancestor',old,head],check=True)
    subprocess.run(['git','-c','http.version=HTTP/1.1','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],check=True)
    subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    actual=refs();assert actual=={k:head for k in expected} and not G.git('status','--porcelain')
    G.active_check('mutation','background_integration',IDS)
    # The snapshot names a completed synchronization observed before its own transport.
    freeze_once(P+'final-refs.json',dict(artifact_type='observed_completed_background_ref_snapshot',main=head,planning_snapshot=head,remote_refs=actual,verified_at=now(),worktree_clean=True,merge_sha=MERGE,reviewed_head=REVIEWED,validation='passed',snapshot_boundary='Independently verified completed closeout synchronization before this tracked evidence transport commit. The containing commit is a descendant, not a self-referential SHA.',r2_delta=0,visitor_visible_delta=0,new_document_review_population=False))
    freeze_once(P+'integration-intent.json',dict(artifact_type='authorized_background_ref_synchronization',authority=P+'authority.json',expected_remote_main=MERGE,expected_remote_planning_snapshot=PLANNING,strategy='Atomic non-force completed background integration followed by one tracked observed-ref evidence transport commit; no redundant state generation.',completed_integration_sha=head,final_ref_evidence=P+'final-refs.json',visitor_visible_delta=0,r2_delta=0,new_document_review_population=False))
    cp=G.load('project-state/checkpoint.json');cp['pr218_postmerge_closeout']['state']='complete_production_verified_synchronized';cp['pr218_postmerge_closeout']['verified_integration_sha']=head
    cp['resume_command']='PR218 production-verified closeout complete; main/planning synchronization completed at tracked verified integration snapshot '+head+'. No owner review or new document review.';save('project-state/checkpoint.json',cp)
    current('Full normal validation passed; main/planning synchronization completed. [Verified integration refs](governance/'+TASK+'/final-refs.json) record the completed snapshot before its evidence transport commit.')
    save(P+'progress.json',dict(stage='complete_production_verified_synchronized',remaining=[],verified_integration_sha=head,new_document_review_population=False))
    refresh();plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active)
    subprocess.run(['git','add','--',*G.changed_paths(MERGE)],check=True)
    G.active_check('final');guard()
    print('Verified integration snapshot:',head,'; evidence transport awaiting final validation and synchronization.')

def repair_queue():
    import importlib.util
    G.active_check('mutation','governance_implementation',IDS)
    pop=copy.deepcopy(G.load(P+'population.json'))
    pop['artifact_paths']=sorted(set(pop['artifact_paths']+[P+'population-v2.json',P+'derived-queue-reconciliation.json',P+'validation-attempt-2.log','project-state/discovery/consolidated-human-review-queue.json']))
    freeze_once(P+'population-v2.json',pop)
    raw=(G.ROOT/'tmp/pr218-full-validation.log').read_text(encoding='utf8');raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    (G.ROOT/(P+'validation-attempt-2.log')).write_text('\n'.join(x.expandtabs(4).rstrip() for x in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    refresh();G.active_check('mutation','governance_implementation',IDS)
    spec=importlib.util.spec_from_file_location('closeout_queue_check',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result,report=module.build();path='project-state/discovery/consolidated-human-review-queue.json';before=G.load(path)
    assert before['record_count']==before['package_count']==result['record_count']==result['package_count']==0
    assert {k:v for k,v in before.items() if k!='inventory_sha256'}=={k:v for k,v in result.items() if k!='inventory_sha256'}
    assert (G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').read_text(encoding='utf8')==report
    raw=(G.ROOT/'project-state/master-inventory.json').read_bytes()
    assert before['inventory_sha256']==hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest()
    assert result['inventory_sha256']==hashlib.sha256(raw).hexdigest()
    save(path,result)
    freeze_once(P+'derived-queue-reconciliation.json',dict(artifact_type='zero_member_queue_checksum_reconciliation',reason='Merged queue fingerprint hashes CRLF pre-Git inventory serialization; authoritative committed inventory is LF under existing .gitattributes.',before_inventory_sha256=before['inventory_sha256'],after_inventory_sha256=result['inventory_sha256'],sole_changed_field='inventory_sha256',record_count=0,package_count=0,inventory_unchanged=True,markdown_unchanged=True,no_new_document_review_population=True,failed_validation=P+'validation-attempt-2.log',builder='Existing Build-ConsolidatedHumanReviewQueue.py; no new generator or queue population.'))
    a=G.load(P+'accounting.json');a['derived_queue_reconciliation']=P+'derived-queue-reconciliation.json';save(P+'accounting.json',a)
    event('governance_implementation','Full validation found pre-Git CRLF checksum in merged empty queue. Existing deterministic builder reconciles only inventory_sha256 to committed LF bytes; zero membership/count/Markdown/inventory delta.',P+'derived-queue-reconciliation.json')
    refresh();G.active_check('final');guard()

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
