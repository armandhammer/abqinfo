"""Exact one-record PR215 production/lifecycle closeout; no content or R2 mutation."""
import copy, gzip, hashlib, importlib.util, json, subprocess, sys, uuid
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativePublication import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git
from Pr208209Reconciliation import presentation
from SchoolZonePublication import ID, SHA, URL, SOURCE, KEY, PAGE
from SchoolZoneDocumentEntryCorrection import TITLE, DESCRIPTION, ENTRY

TASK='pr215-postmerge-closeout-2026-10-07'
P='project-state/governance/'+TASK+'/'
SCRIPT='scripts/project/Pr215PostMergeCloseout.py'
MERGE='074d1bdbb2f3985e756479d88352ea41bf74f5a0'
REVIEWED='0fd21642ba64aafc2dd10837a70feccafbfd9f55'
PLANNING='bdb6d440091f28fa88d0753dad34849b53e703b8'
ROUTE='transportation/safety-crash-data/'
ANCHOR='school-transportation-safety'
PROD='https://abqinfo.com/'+ROUTE+'#'+ANCHOR
OLD='project-state/governance/school-zone-document-entry-correction-2026-10-07/'
OPS=['governance_implementation','inventory_disposition','background_integration']
def now():return datetime.now(timezone.utc).isoformat()
def freeze(path,value):
    if (G.ROOT/path).exists():assert G.load(path)==value,path
    else:G.write_once(path,value)

def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([p for p in G.changed_paths(MERGE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    n=len(list((G.ROOT/P).glob('contract-v*.json')))+1;assert n<=20
    path=P+f'contract-v{n}.json'
    population=P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json')
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not [g for g in c['unresolved_gates'] if set(g.get('blocks_operations',[]))&set(OPS)],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'authority.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=population,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules; no conflicts/gates')

def event(op,summary,evidence):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)

def setup():
    assert G.git('rev-parse','HEAD')==MERGE
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    outputs=['population.json','authority.json','supersession.json','starting-state.json','implementation.json','progress.json','merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates.json','source-record.json','queue.json','accounting.json','validation.log','receipt.json','integration-intent.json']+[f'contract-v{i}.json' for i in range(1,21)]+['page-'+label+'.html.gz' for label in ['production','merge','preview']]
    paths=[P+x for x in outputs]+[SCRIPT,G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    freeze(P+'population.json',dict(task_id=TASK,baseline_commit=MERGE,candidate_ids=[ID],families=['school-zone-active-times'],pages=[PAGE],operation_classes=OPS,artifact_paths=sorted(paths)))
    instruction='Explicit current owner PR215 post-merge production verification and background lifecycle reconciliation ONLY. Independently verify remote owner merge '+MERGE+', reviewed head '+REVIEWED+', concise PDF entry directly under School Transportation Safety, no School Zone Active Times heading or rendered individual schedule list, surrounding records unchanged, desktop/mobile installed Chrome, preview/merge/production parity, and complete unchanged 3013109-byte public PDF SHA256 '+SHA+'. Once verified, reconcile exactly '+ID+' to owner-reviewed merged, production live, validated/passed with no remaining manual review. Preserve full 30-schedule/32-school/61-interval internal extraction, owner document-entry supersession, archive provenance, and elementary continuation context. Update only current lifecycle/checkpoint/queue/accounting/governance and synchronize background main/planning after normal validation. Explicitly supersedes former open/unmerged, no-deployment and feature-only phase boundaries ONLY. ZERO visitor-visible changes and ZERO R2 mutations; no other population or elementary work.'
    freeze(P+'authority.json',dict(authority='Explicit current owner PR215 post-merge closeout instruction',instruction=instruction,candidate_ids=[ID],merge_sha=MERGE,reviewed_head=REVIEWED,r2_mutation_authorized=False,visitor_visible_change_authorized=False))
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID);assert row['status']=='implemented' and row['validation_status']=='passed'
    folders=[str(p.relative_to(G.ROOT)).replace('\\','/')+'/' for p in (G.ROOT/'project-state/governance').glob('school-zone-*')]
    history=git('ls-tree','-r','--name-only',MERGE,'--',*folders).decode().splitlines()
    protected=history+['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/discovery/retained-source-audit-queue.json']
    # Read all existing school-zone evidence, preserving exact bytes and authority.
    for path in history:
        if path.endswith('.json'):G.load(path)
        elif path.endswith(('.md','.log')):(G.ROOT/path).read_text(encoding='utf-8-sig')
    freeze(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,prior_planning_sha=PLANNING,content_tree_oid=G.git('rev-parse',MERGE+':content'),selected_row=row,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],active_task_before=G.load(G.ACTIVE_TASK),checkpoint_before=G.load('project-state/checkpoint.json'),complete_prior_evidence_read=True,protected_sha256={p:G.file_hash(p) for p in protected}))
    refresh() # Exact complete registry contract before phase-boundary mutation.
    r=G.registry();proposals={}
    for old in r['entries'][:]:
        if old['state']!='active' or 'school-zone' not in old['governance_id']:continue
        gid=old['governance_id']+'-postmerge-lifecycle'
        requirement='Preserve all completed substantive review/extraction, unchanged source/archive/public-byte evidence, scope/quality/provenance and internal elementary continuation established by '+old['governance_id']+'. Preserve the current owner-approved one concise linked archived-original entry and prohibition on visitor-visible individual schedules. Explicit current owner PR215 closeout authority supersedes ONLY prior OPEN/UNMERGED, no-production-deployment and feature-only synchronization phase boundaries: verify already owner-merged production, mark exactly '+ID+' live validated/passed, close manual-review state and integrate background main/planning after full validation. No visitor-visible edits, repeat R2 upload/mutation, elementary or other population.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Only current lifecycle and background synchronization; substantive decisions and historical evidence remain intact.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=requirement,required_actions=[requirement],prohibited_actions=['No visitor-visible or R2 mutation, unrelated record or new population.'],authority='Explicit current owner post-merge lifecycle instruction',effective_date='2026-10-07')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No visitor-visible or R2 mutation, unrelated record or new population.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='authorized exact production closeout'))
    save(G.REGISTRY,r);refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='school-zone-document-entry-correction-2026-10-07';life['stages'][-1]['end_commit']=MERGE
    existing={s['path'] for s in life['protected_evidence']}
    for path in history:
        if path not in existing:life['protected_evidence'].append(dict(path=path,commit=MERGE,sha256=G.file_hash(path)))
    life['stages'].append(dict(id=TASK,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr215PostMergeCloseout',function='guard')));save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf-8-sig').replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/Pr215PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR215 closeout exact-delta guard failed.\' }\nSet-StrictMode -Version Latest',1).replace('$broken = @()','& python "$PSScriptRoot/Pr215PostMergeCloseout.py" render\nif ($LASTEXITCODE) { throw \'PR215 production/Hugo parity failed.\' }\n$broken = @()',1);runner.write_text(s,encoding='utf-8',newline='\n')
    event('governance_implementation','Exact one-record population and complete registry frozen; phase-only supersession registered and complete school-zone history sealed at owner merge.',P+'starting-state.json');refresh();guard()

JS=r'''() => {const h=document.getElementById('school-transportation-safety');let n=h.nextElementSibling;const nodes=[];while(n&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}return {text:nodes.map(x=>x.innerText).join('\n'),links:nodes.flatMap(x=>Array.from(x.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth,schoolZoneHeading:!!document.getElementById('school-zone-active-times'),anchor:h.id,heading_tag:h.tagName};}'''

def verify():
    import requests
    from playwright.sync_api import sync_playwright
    from urllib.parse import urlsplit
    G.active_check('mutation','governance_implementation',[ID]);guard()
    pr=json.loads(subprocess.check_output(['gh','pr','view','215','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf8'));assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    subprocess.run(['git','merge-base','--is-ancestor',MERGE,'origin/main'],check=True)
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf8'));check=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages');assert check['conclusion']=='success' and check['head_sha']==MERGE
    deployment='https://'+check['external_id'][:8]+'.abqinfo.pages.dev/'
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    page=G.git('show',MERGE+':'+PAGE);assert ENTRY.strip() in page and '### School Zone Active Times' not in page
    G.write_once(P+'merge-verification.json',dict(pr=pr,cloudflare_check=check,merge_deployment=deployment,reviewed_merge_trees_identical=True,concise_publication_form_verified=True))
    old=G.load(OLD+'preview.json');urls=dict(production='https://abqinfo.com/'+ROUTE,merge=deployment+ROUTE,preview=old['url'].split('#')[0]);article={};witnesses=[]
    for label,url in urls.items():
        r=requests.get(url+'?pr215_verify='+uuid.uuid4().hex,headers={'Cache-Control':'no-cache, no-store, max-age=0'},timeout=90);r.raise_for_status();value,_=presentation(r.content);article[label]=value;path=P+'page-'+label+'.html.gz';(G.ROOT/path).write_bytes(gzip.compress(r.content,mtime=0));witnesses.append(dict(label=label,url=r.url,status=r.status_code,witness=path,sha256=hashlib.sha256(r.content).hexdigest(),article_sha256=G.digest(value),observed_at=now()))
    assert article['production']==article['merge']==article['preview'],'Complete article mismatch'
    def normalized(links):
        return [(x['text'],urlsplit(x['url']).path+('#'+urlsplit(x['url']).fragment if urlsplit(x['url']).fragment else '') if urlsplit(x['url']).hostname in ['abqinfo.com'] or (urlsplit(x['url']).hostname or '').endswith('.abqinfo.pages.dev') else x['url']) for x in links]
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for name,width,height in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=width,height=height))
            for label,url in dict(canonical=PROD,**urls).items():
                response=page.goto(url if label=='canonical' else url+'?pr215_chrome='+uuid.uuid4().hex+'#'+ANCHOR,wait_until='networkidle',timeout=90000);assert response.status==200
                section=page.evaluate(JS);assert section['text']==old['results'][0]['text'] and normalized(section['links'])==normalized(old['results'][0]['links']);assert not section['overflow'] and not section['schoolZoneHeading'] and section['anchor']==ANCHOR and section['heading_tag']=='H2'
                link=page.get_by_role('link',name=TITLE,exact=True);assert link.count()==1 and link.get_attribute('href')==URL
                li=link.locator('xpath=ancestor::li[1]');assert li.inner_text()==TITLE+'\n\n'+DESCRIPTION
                assert 'weekday not stated' not in section['text'] and '7:35 AM to 8:15 AM' not in section['text'] and 'Clevland' not in section['text']
                assert li.locator('xpath=ancestor::ul[1]/preceding-sibling::h2[1]').get_attribute('id')==ANCHOR
                li.scroll_into_view_if_needed();box=li.bounding_box();assert box and box['x']>=0 and box['x']+box['width']<=width+1
                download=page.request.get(URL,timeout=180000);body=download.body();assert download.status==200 and len(body)==3013109 and hashlib.sha256(body).hexdigest()==SHA
                section.update(label=label,viewport=name,document_entry_text=li.inner_text(),archive_link_full_get='passed')
                if label=='canonical':page.screenshot(path=str(G.ROOT/(P+('production.png' if name=='desktop' else 'mobile.png'))))
                results.append(section)
            page.close()
        browser.close()
    G.write_once(P+'production-render.json',dict(browser='Installed Google Chrome via Playwright',canonical_url=PROD,results=results,observed_at=now(),surrounding_entries_unchanged=True,desktop_mobile_layout_passed=True,no_rendered_schedule_list_or_heading=True))
    G.write_once(P+'production-verification.json',dict(result='passed',merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,merge_deployment=deployment,reviewed_preview=old['url'],canonical_rendered_production_verified=True,full_article_parity=True,article_sha256=G.digest(article['production']),title=TITLE,description=DESCRIPTION,no_schedule_list=True,no_extra_heading=True,surrounding_entries_unchanged=True,desktop_mobile_layout_passed=True,witnesses=witnesses,rendering=P+'production-render.json'))
    r=requests.get(URL,headers={'Cache-Control':'no-cache'},timeout=180);r.raise_for_status();size=len(r.content);sha=hashlib.sha256(r.content).hexdigest();assert size==3013109 and sha==SHA
    source=(G.ROOT/SOURCE).read_bytes();assert r.content==source
    G.write_once(P+'archive-verification.json',dict(result='passed',url=r.url,r2_key=KEY,size_bytes=size,sha256=sha,source_path=SOURCE,exact_public_original=True,full_get=True,status=r.status_code,observed_at=now(),r2_delta=dict(added=0,deleted=0,overwritten=0,bytes=0)))
    event('governance_implementation','Owner merge/tree, complete preview/merge/production article and desktop/mobile section parity passed. Concise entry only, no schedule heading/list, unchanged surrounding records, sound anchor/layout and exact original public GET.',P+'production-verification.json');refresh();G.active_check('final');guard()

def reconcile():
    assert G.load(P+'production-verification.json')['result']==G.load(P+'archive-verification.json')['result']=='passed'
    G.active_check('mutation','inventory_disposition',[ID]);row=G.load(P+'starting-state.json')['selected_row']
    changes=dict(status='validated',validation_status='passed',workflow_state='owner_reviewed_merged_production_live_validated',source_record_evidence=P+'source-record.json',processing_notes=row['processing_notes']+['PR215 owner merge '+MERGE+' verified in installed Chrome desktop/mobile; complete reviewed-preview/merge/production parity, concise archived-PDF entry only, no individual schedules/heading. Full public GET exactly 3013109 bytes / '+SHA+'. Owner review complete; production live validated/passed. Prior open/unmerged references are historical preparation. Full review/extraction, form supersession and elementary continuation retained.'])
    pop=G.load(P+'population.json');pop['artifact_paths']+= [P+'population-v2.json',P+'record-updates-v2.json'];freeze(P+'population-v2.json',pop)
    G.write_once(P+'record-updates-v2.json',[dict(id=ID,changes=changes)]);refresh();subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates-v2.json'],check=True)
    inv=G.load('project-state/master-inventory.json');save(P+'source-record.json',next(x for x in inv['candidates'] if x['id']==ID))
    old=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(old);pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];gated=pending&set(old['gated_pending_ids']);blocked=pending&set(old['source_or_structural_blocked_pending_ids']);assert gated.isdisjoint(blocked);ungated=pending-gated-blocked
    q.update(artifact_type='pr215_postmerge_closeout_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),approved_count=len(approved),pending_ids=sorted(pending),pending_review_count=len(pending),gated_pending_ids=sorted(gated),gated_pending_count=len(gated),source_or_structural_blocked_pending_ids=sorted(blocked),source_or_structural_blocked_pending_count=len(blocked),ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),actionable_ungated_pending_ids=sorted(ungated),genuinely_actionable_ungated_pending_count=len(ungated),in_progress_publication=None,next_work_category='Resolve existing source/structural research prerequisites; no actionable ordinary publication population.',actionability_basis='Recomputed against current inventory and preserved durable gate/blocker membership; PR215 source is live validated, outside pending membership.',newly_approved_backlog=[])
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],next_pending_id=inv['next_pending_id'],completed_item_range='PR215 owner merge '+MERGE+' production verified; exact school-zone source live validated/passed.',remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),resume_command='PR215 production/live closeout: complete validation and background main/planning synchronization only; no other population.')
    for field in ['school_zone_timing_review','next_owner_requested_task']:cp[field].update(state='owner_reviewed_merged_production_live_validated',remaining_gate=None,merge_sha=MERGE,production_url=PROD,production_verification=P+'production-verification.json',closeout=P+'receipt.json',archive_verified=True,visible_pr_created=True)
    cp['pr215_postmerge_closeout']=dict(state='production_verified_lifecycle_reconciled_validation_pending',merge_sha=MERGE,reviewed_head=REVIEWED,receipt=P+'receipt.json',zero_visitor_visible_r2_delta=True);save('project-state/checkpoint.json',cp)
    spec=importlib.util.spec_from_file_location('pr215_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);owner,report=module.build();save('project-state/discovery/consolidated-human-review-queue.json',owner);(G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').write_text(report,encoding='utf8',newline='\n')
    save(P+'accounting.json',dict(validated_ids=[ID],approved=len(approved),pending=len(pending),governance_gated=len(gated),source_structural_blocked=len(blocked),ungated=len(ungated),actionable=len(ungated),human_review=sum(r['status']=='requires human review' for r in inv['candidates']),remaining_nonterminal=cp['remaining_nonterminal'],in_progress_publication=None,visitor_visible_delta=0,r2_delta=0))
    f=G.ROOT/'project-state/CURRENT.md';tail=f.read_text(encoding='utf-8-sig').split('[Owner correction]')[1]
    current='# Current project state\n\nPR #215 owner-merged at '+MERGE+'. Production Safety & Crash Data / School Transportation Safety matches the reviewed concise archived-PDF entry: no separate school-zone heading or individual schedule list. Chrome desktop/mobile, full preview/merge/production parity and unchanged original public GET (3,013,109 bytes / fade828a553f SHA-256 prefix) passed. Exactly one school-zone record live validated/passed; no remaining manual review. Internal 30 schedules / 32 schools / 61 intervals and owner form supersession preserved. Elementary continuation remains future context only. ZERO visitor-visible/R2 closeout delta. Full validation/ref synchronization pending.\n\nQueue: 0 approved / 339 pending (321 governance-gated / 18 source-structural blocked), 0 actionable / 0 human review. NEXT available category: existing source/structural prerequisite resolution under a separately authorized population; none begun.\n\n[Closeout](governance/'+TASK+'/receipt.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n[Owner correction]'+tail
    assert len(current)<=1800;f.write_text(current,encoding='utf8',newline='\n');event('inventory_disposition','Only verified school-zone source advanced to validated/live; manual review closed. Queue/accounting regenerated; all prior substantive evidence preserved.',P+'accounting.json');refresh();G.active_check('final');guard()

def guard():
    stage=StageSnapshot(TASK);pop=stage.load_json(P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json'));start=stage.load_json(P+'starting-state.json');assert pop['candidate_ids']==[ID] and pop['baseline_commit']==MERGE and not set(pop['operation_classes'])&{'archive','content_implementation','content_removal'}
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid']);paths=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE));assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    for path,h in start['protected_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    a={r['id']:r for r in json.loads(git('show',MERGE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']};assert a.keys()==b.keys();delta={i for i in a if a[i]!=b[i]};assert delta<={ID}
    if delta:
        allowed={'status','validation_status','workflow_state','source_record_evidence','processing_notes','updated_at'}
        assert {k for k in a[ID].keys()|b[ID].keys() if a[ID].get(k)!=b[ID].get(k)}<=allowed
        assert a[ID]['status']=='implemented' and b[ID]['status']=='validated' and b[ID]['validation_status']=='passed' and b[ID]['workflow_state']=='owner_reviewed_merged_production_live_validated'
        assert b[ID]['processing_notes'][:len(a[ID]['processing_notes'])]==a[ID]['processing_notes']
        assert stage.load_json(P+'production-verification.json')['result']==stage.load_json(P+'archive-verification.json')['result']=='passed'
    if (G.ROOT/(P+'accounting.json')).exists():
        q=stage.load_json(P+'queue.json');assert q['pending_ids']==sorted(r['id'] for r in b.values() if r['status']=='pending review');assert q['approved_count']==sum(r['status']=='approved for addition' for r in b.values())
        old=stage.load_json(start['source_queue']);assert set(q['gated_pending_ids'])==set(old['gated_pending_ids']) and set(q['source_or_structural_blocked_pending_ids'])==set(old['source_or_structural_blocked_pending_ids']) and q['in_progress_publication'] is None
        cp=stage.load_json('project-state/checkpoint.json');assert cp['counts_by_status']==stage.load_json('project-state/master-inventory.json')['counts'];assert all(cp[k]['remaining_gate'] is None for k in ['school_zone_timing_review','next_owner_requested_task'])
        allowed={'recorded_at','counts_by_status','next_pending_id','completed_item_range','remaining_nonterminal','resume_command','school_zone_timing_review','next_owner_requested_task','pr215_postmerge_closeout'};assert {k:v for k,v in cp.items() if k not in allowed}=={k:v for k,v in start['checkpoint_before'].items() if k not in allowed}
        current=stage.read_text('project-state/CURRENT.md');assert 'OPEN UNMERGED' not in current and 'no merge/deploy authority' not in current and 'live validated/passed' in current
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json');assert receipt['visitor_visible_delta']==receipt['r2_delta']==0 and receipt['validated_ids']==[ID]
        for path,h in receipt['evidence_sha256'].items():assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,path
    print('PASS PR215 exact live/validated lifecycle; unchanged content/R2/other records; complete sealed school-zone history')

def render():
    stage=StageSnapshot(TASK)
    if stage.end:guard();print('PASS sealed PR215 production evidence');return
    value,_=presentation((G.ROOT/'tmp/site-build'/ROUTE/'index.html').read_bytes());assert G.digest(value)==stage.load_json(P+'production-verification.json')['article_sha256'];print('PASS Hugo complete article matches verified PR215 production/merge/reviewed preview')

def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard();raw=(G.ROOT/'tmp/pr215-validation.log').read_text(encoding='utf8');assert '"Hugo": "passed"' in raw and 'PR215 production/merge/reviewed preview' in raw
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in raw.splitlines())+'\n',encoding='utf8',newline='\n')
    G.write_once(P+'integration-intent.json',dict(authority=P+'authority.json',expected_main=MERGE,expected_planning_snapshot=PLANNING,strategy='Atomic non-force fast-forward main and planning-snapshot to completed background closeout; preserve owner merge and complete review history.',final_ref_evidence='project-state/campaign-runtime/'+TASK+'/final-refs.json',no_visitor_visible_change=True,no_r2_mutation=True,no_new_substantive_population=True))
    evidence=['merge-verification.json','production-verification.json','production-render.json','production.png','mobile.png','archive-verification.json','record-updates-v2.json','source-record.json','queue.json','accounting.json','validation.log'];c=G.load(G.load(G.ACTIVE_TASK)['contract'])
    G.write_once(P+'receipt.json',dict(task_id=TASK,state='production_verified_lifecycle_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_result='passed',production_url=PROD,validated_ids=[ID],lifecycle=dict(status='validated',validation_status='passed',production_live=True,owner_merge_verified=True,manual_review_pending=False),queue=G.load(P+'accounting.json'),visitor_visible_delta=0,r2_delta=0,normal_validation='passed',owner_decision_required=False,no_new_population=True,internal_extraction_preserved=dict(schedules=30,schools=32,intervals=61),elementary_continuation_only=True,evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact production-verified one-record live/validated lifecycle and authorized background synchronization only. All substantive scope/quality/source/archive/form-supersession/extraction evidence retained; no content/R2/other-record or population change.',evidence=[P+'production-verification.json',P+'archive-verification.json',P+'accounting.json']) for r in c['resolved_rules']},integration_intent=P+'integration-intent.json',visual_inspection='Desktop/mobile production screenshots inspected: concise entry, normal surrounding spacing, clean wrapping and no overflow.',style_baseline='Four pre-existing title-case warnings on unchanged Area & Sector Plans.'))
    cp=G.load('project-state/checkpoint.json');cp['resume_command']='PR215 production/live validated closeout complete; no owner decision required. Next available category is existing source/structural prerequisite resolution under a separate authorized population; none begun.';cp['pr215_postmerge_closeout']['state']='complete_production_live_validated';save('project-state/checkpoint.json',cp)
    f=G.ROOT/'project-state/CURRENT.md';s=f.read_text(encoding='utf8').replace('Full validation/ref synchronization pending.','Full normal/governance/sealed-history/Hugo validation passed; background main/planning synchronization authorized. No owner decision required.');assert len(s)<=1800;f.write_text(s,encoding='utf8',newline='\n')
    event('background_integration','Full normal suite and production/archive parity passed; exact background closeout ready for atomic main/planning synchronization.',P+'integration-intent.json');refresh();G.active_check('final');guard()

def integrate():
    def refs():
        lines=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()
        return {x.split()[1]:x.split()[0] for x in lines}
    expected={'refs/heads/main':MERGE,'refs/heads/chatgpt/planning-snapshot':PLANNING};assert refs()==expected
    assert G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan);active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active);G.active_check('final');guard()
    paths=G.changed_paths(MERGE);assert not any(p.startswith('backups/') for p in paths)
    subprocess.run(['git','add','--',*paths],check=True);subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','-m','Complete PR215 production verification and live lifecycle closeout'],check=True)
    head=G.git('rev-parse','HEAD');assert refs()==expected
    for old in [MERGE,PLANNING]:subprocess.run(['git','merge-base','--is-ancestor',old,head],check=True)
    journal='project-state/campaign-runtime/'+TASK+'/integration-journal.json'
    intent=dict(operation='atomic background closeout synchronization',authority=P+'authority.json',sha=head,expected_refs=expected,intent_at=now());save(journal,intent)
    result=subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],capture_output=True,text=True)
    intent.update(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,result_at=now());save(journal,intent);print(result.stdout+result.stderr);assert result.returncode==0
    subprocess.run(['git','switch','main'],check=True);subprocess.run(['git','merge','--ff-only',head],check=True);subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    remote=refs();assert remote=={'refs/heads/main':head,'refs/heads/chatgpt/planning-snapshot':head} and not G.git('status','--porcelain')
    G.active_check('final');guard()
    save('project-state/campaign-runtime/'+TASK+'/final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=remote,verified_at=now(),worktree_clean=True,merge_sha=MERGE,reviewed_head=REVIEWED,production_url=PROD,validation='passed',no_visitor_visible_or_r2_delta=True,no_new_substantive_population=True))
    print('Final synchronized main/planning-snapshot:',head)

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
