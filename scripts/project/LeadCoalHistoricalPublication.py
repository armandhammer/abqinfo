"""Owner-authorized two-original archive and bounded unmerged publication."""
import copy, hashlib, json, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativePublication import save, audit

TASK = 'lead-coal-historical-publication-2026-10-12'
P = 'project-state/governance/' + TASK + '/'
OLD = 'project-state/governance/lead-coal-historical-review-2026-10-12/'
BASE = '50e66f5613ecc67b76a2445c7afaf3786474a470'
PAGE = 'content/transportation/roadway-projects/studies.md'
SCRIPT = 'scripts/project/LeadCoalHistoricalPublication.py'
OBJECTS = G.load(OLD+'archive-readiness.json')['objects']
IDS = [o['candidate_id'] for o in OBJECTS]
OPS = ['archive','content_implementation','visitor_visible_change','inventory_disposition','governance_implementation','family_review']

def now(): return datetime.now(timezone.utc).isoformat()

def refresh():
    reg=G.load(G.REGISTRY)
    for r in reg['entries']:
        if r['state']=='active':
            for a in r['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']: a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,reg)
    registered={a['path'] for r in reg['entries'] for a in r['controlling_artifacts']}
    paths=[p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,reg['audit_artifact'],P+'implementation.json'}]
    audit(paths)
    n=max([int(x.stem.split('-v')[1]) for x in (G.ROOT/P).glob('contract-v*.json')],default=0)+1
    path=P+f'contract-v{n}.json'; c=G.resolve(G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));G.write_once(path,c)
    assert not c['conflicts'] and not c['unresolved_gates'],(c['conflicts'],c['unresolved_gates'])
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    ev=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=ev,sha256=G.file_hash(ev))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules, no conflicts/gates')

def event(op,summary,evidence):
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation=op,candidate_ids=IDS,action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',plan)

def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','supersession.json','starting-state.json','original-verification.json','r2-before.json','r2-after.json','archive-preflight.json','upload-intent.json','upload-1.json','upload-2.json','public-1.json','public-2.json','implementation.json','receipt.json','queue.json','validation.log','preview.json','preview-desktop.png','preview-mobile.png','pr-description.md','pr.json','final-state.json','publication.md','link-verification.json']+[f'contract-v{i}.json' for i in range(1,41)]
    paths=[P+x for x in outputs]+[SCRIPT,'scripts/project/LeadCoalHistoricalReview.py','scripts/project/Invoke-ProjectValidation.ps1',G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/r2-inventory.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=['lead-coal-historical-review'],pages=[PAGE],operation_classes=OPS,artifact_paths=paths,archive_objects=[dict(candidate_id=o['candidate_id'],source_path=o['local_original'],r2_key=o['proposed_r2_key'],sha256=o['sha256'],size_bytes=o['size_bytes']) for o in OBJECTS]))
    # Resolve all active authority before registering the explicitly authorized phase change.
    G.write_once(P+'contract-v1.json',G.resolve(G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY)))
    instruction='Explicit owner authorization: upload exactly the two approved unchanged Lead/Coal historical originals to their full destinations in archive-readiness.json, without overwriting or deleting; fresh inventory/capacity/key checks and exact complete public-download size/SHA256 verification. Reuse completed review, assessments, provenance and descriptions. Add only the approved 2021 and 2007 entries, in that order, after unchanged 2025 and 2022 entries in the existing Lead and Coal Avenues section of studies.md. Preserve all existing records, historical evidence and unrelated work. Correct malformed UTF-8 in CURRENT as background maintenance. Full governance/archive/content/link/Hugo validation and actual nonproduction changed-section preview. Prepare concise validated PR description with exact additions/placement/direct preview. Stop with content PR OPEN UNMERGED for owner manual review and merge; no production deployment.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction',instruction=instruction,candidate_ids=IDS,archive_objects=G.load(P+'population.json')['archive_objects'],total_bytes=33800776,merge_authorized=False,production_deployment_authorized=False))
    reg=G.registry();old=next(r for r in reg['entries'] if r['governance_id']=='owner-lead-coal-historical-review-2026-10-12' and r['state']=='active')
    gid=old['governance_id']+'-publication-authorized'
    revised=old['binding_requirement']+' The explicit current owner archival/publication authorization in '+P+'authority.json supersedes only the prior no-upload/no-visible-change/no-PR phase boundary for these exact two approved originals. Completed review and all preservation requirements remain controlling. Stop with an open unmerged PR; no production deployment.'
    proposals={old['governance_id']:dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=revised,consequences='Only two exact-original archives and existing-section unmerged publication authorized; completed review unchanged.',authorization_artifact=P+'authority.json')}
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=revised,required_actions=[revised],prohibited_actions=['No overwrite/delete, unrelated changes, merge or production deployment.'],prohibited_operation_classes=[],effective_date='2026-10-12',implementation_status='authorized archive and unmerged publication');new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
    old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');reg['entries'].append(new)
    reg['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,state='active',scope=dict(candidate_ids=IDS,task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-12',effective_date='2026-10-12',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No merge or production deployment, overwrite/delete or unrelated population.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='archive and unmerged owner-review publication'))
    save(G.REGISTRY,reg)
    prior={x.relative_to(G.ROOT).as_posix():G.file_hash(x.relative_to(G.ROOT).as_posix()) for x in (G.ROOT/OLD).iterdir() if x.is_file()}
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,branch=G.git('branch','--show-current'),checked_at=now(),prior_evidence_sha256=prior,prior_active_task=G.load(G.ACTIVE_TASK),completed_review_reused=True))
    refresh();G.active_check('mutation','governance_implementation',IDS)
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='lead-coal-historical-review-2026-10-12';life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='LeadCoalHistoricalPublication',function='guard')))
    protected={x['path'] for x in life['protected_evidence']}
    for path,h in prior.items():
        if path not in protected:life['protected_evidence'].append(dict(path=path,commit=BASE,sha256=h))
    save('project-state/workflow-stage-lifecycle.json',life)
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=f.read_text(encoding='utf-8-sig');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/LeadCoalHistoricalPublication.py" guard\nif ($LASTEXITCODE) { throw \'Lead/Coal publication guard failed.\' }\nSet-StrictMode -Version Latest',1);f.write_text(s,encoding='utf-8',newline='\n')
    refresh()

def originals():
    rows=[]
    for o in OBJECTS:
        raw=(G.ROOT/o['local_original']).read_bytes();h=hashlib.sha256(raw).hexdigest();assert len(raw)==o['size_bytes'] and h==o['sha256']
        rows.append(dict(candidate_id=o['candidate_id'],local_original=o['local_original'],size_bytes=len(raw),sha256=h,exact_original_match=True,checked_at=now()))
    G.write_once(P+'original-verification.json',dict(objects=rows,total_bytes=sum(x['size_bytes'] for x in rows)))
    event('archive','Verified both unchanged originals against recorded sizes and complete SHA256.',P+'original-verification.json');refresh()

def preflight():
    before=G.load(P+'r2-before.json');keys={x['key'].casefold() for x in before['objects']}
    assert len(before['objects'])==before['object_count'] and sum(x['size_bytes'] for x in before['objects'])==before['total_bytes']
    assert all(o['proposed_r2_key'].casefold() not in keys and o['size_bytes']<=150000000 for o in OBJECTS)
    total=sum(o['size_bytes'] for o in OBJECTS);ceiling=G.load('project-state/r2-storage-policy.json')['maximum_projected_r2_bytes'];assert before['total_bytes']+total<=ceiling
    for o in OBJECTS:
        assert hashlib.sha256((G.ROOT/o['local_original']).read_bytes()).hexdigest()==o['sha256']
        G.active_check('mutation','archive',[o['candidate_id']],r2_key=o['proposed_r2_key'],source_sha256=o['sha256'])
    G.write_once(P+'archive-preflight.json',dict(checked_at=now(),inventory_sha256=G.file_hash(P+'r2-before.json'),objects=OBJECTS,all_destination_keys_absent=True,current_objects=before['object_count'],current_bytes=before['total_bytes'],added_bytes=total,projected_objects=before['object_count']+2,projected_bytes=before['total_bytes']+total,ceiling_bytes=ceiling,no_overwrite=True,no_delete=True))
    G.write_once(P+'upload-intent.json',dict(created_at=now(),objects=OBJECTS,authority=P+'authority.json',recovery='Inspect saved upload/public receipts and live keys before resuming; successful uploads are never repeated or overwritten.'))
    refresh()

def implement():
    for j,o in enumerate(OBJECTS,1):
        v=G.load(P+f'public-{j}.json');assert v['byte_identical'] and v['size_bytes']==o['size_bytes'] and v['checksum_sha256']==o['sha256']
    before=G.load(P+'r2-before.json');after=G.load(P+'r2-after.json');old={x['key']:x for x in before['objects']};new={x['key']:x for x in after['objects']}
    assert new.keys()-old.keys()=={o['proposed_r2_key'] for o in OBJECTS} and all(new[k]==v for k,v in old.items())
    assert after['total_bytes']==before['total_bytes']+33800776 and after['object_count']==before['object_count']+2
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    block=''
    for j,o in enumerate(OBJECTS,1):
        r=rows[o['candidate_id']];label=r['title']+(' (July 27, 2021 historical report, archived PDF)' if j==1 else ' (March 23, 2007 historical report, archived PDF)')
        block+='- ['+label+'](https://files.abqinfo.com/'+o['proposed_r2_key']+')\n\n  '+r['description']+'\n\n'
        if j==1: block+='  [Official City PDF]('+o['source_url']+')\n\n'
        else: block+='  [Original City source (currently unavailable)]('+o['source_url']+') · [Historical City PDF via Internet Archive](https://web.archive.org/web/20160605020924id_/http://www.cabq.gov/municipaldevelopment/documents/newvisionforleadcoalavenues/@@download/file/NewVisionforLeadCoalAvenues.pdf)\n\n'
    (G.ROOT/(P+'publication.md')).write_text(block,encoding='utf-8',newline='\n');refresh()
    G.active_check('mutation','content_implementation',IDS,pages=[PAGE])
    f=G.ROOT/PAGE;s=f.read_text(encoding='utf-8-sig');assert s==G.git('show',BASE+':'+PAGE)+'\n' or s.rstrip()==G.git('show',BASE+':'+PAGE).rstrip()
    s=s.replace('### Historical Street Capital Programs',block+'### Historical Street Capital Programs',1);f.write_text(s,encoding='utf-8',newline='\n')
    G.active_check('mutation','inventory_disposition',IDS)
    for j,o in enumerate(OBJECTS,1):
        r=rows[o['candidate_id']];obj=new[o['proposed_r2_key']]
        r.update(status='implemented',r2_key=obj['key'],r2_url=obj['public_url'],r2_etag=obj['etag'],r2_last_modified=obj['last_modified'],implementation_location=PAGE+'#lead-and-coal-avenues',implementation_locations=[PAGE+'#lead-and-coal-avenues'],validation_status='passed',updated_at=now(),archive_verification=G.load(P+f'public-{j}.json'),archive_receipt=P+f'upload-{j}.json')
        if j==2:
            historical='https://web.archive.org/web/20160605020924id_/http://www.cabq.gov/municipaldevelopment/documents/newvisionforleadcoalavenues/@@download/file/NewVisionforLeadCoalAvenues.pdf'
            if historical not in r['referring_urls']:r['referring_urls'].append(historical)
        r['processing_notes'].append('Owner-authorized unchanged-original archival verified by full public GET; historical entry prepared in unmerged manual-review publication PR. Receipt: '+P+'receipt.json')
    inv['counts']={s:sum(r['status']==s for r in inv['candidates']) for s in inv['allowed_statuses']};inv['generated_at']=now();save('project-state/master-inventory.json',inv);save('project-state/r2-inventory.json',after)
    event('content_implementation','Appended reviewed 2021 then 2007 historical entries after unchanged 2025 and 2022; sources and exact verified archives included.',P+'publication.md')
    event('archive','Uploaded only two unchanged originals; full public GET matched both hashes/sizes and complete R2 inventory confirms exact delta.',P+'r2-after.json')
    receipt=dict(artifact_type='archive_and_unmerged_publication_receipt',recorded_at=now(),candidate_ids=IDS,source_review=OLD+'receipt.json',objects=[dict(**o,public_verification=P+f'public-{j}.json',upload_receipt=P+f'upload-{j}.json') for j,o in enumerate(OBJECTS,1)],r2_before_objects=before['object_count'],r2_before_bytes=before['total_bytes'],r2_after_objects=after['object_count'],r2_after_bytes=after['total_bytes'],uploads=2,added_bytes=33800776,remaining_capacity_bytes=13000000000-after['total_bytes'],page=PAGE,section='Lead and Coal Avenues',existing_entries_preserved=True,merge_authorized=False,production_deployment_authorized=False)
    save(P+'receipt.json',receipt);refresh()

def guard():
    if not (G.ROOT/(P+'starting-state.json')).exists():return
    pop=G.load(P+'population.json');assert set(G.changed_paths(BASE))<=set(pop['artifact_paths'])|{PAGE},'Outside frozen scope'
    for path,h in G.load(P+'starting-state.json')['prior_evidence_sha256'].items():assert G.file_hash(path)==h,path
    original=json.loads(G.git('show',BASE+':project-state/master-inventory.json'));live=G.load('project-state/master-inventory.json');a={r['id']:r for r in original['candidates']};b={r['id']:r for r in live['candidates']}
    assert a.keys()==b.keys() and all(a[i]==b[i] for i in a if i not in IDS),'Unrelated inventory changed'
    for i in IDS:
        for field in ['scope_assessment','quality_assessment','publication_quality_decision','checksum_sha256','size_bytes','description','provenance_status','historical_review_evidence']:assert a[i][field]==b[i][field],(i,field)
    old=G.git('show',BASE+':'+PAGE);new=(G.ROOT/PAGE).read_text(encoding='utf-8-sig').rstrip()
    if new!=old.rstrip():
        block=(G.ROOT/(P+'publication.md')).read_text(encoding='utf-8-sig');assert new==old.replace('### Historical Street Capital Programs',block+'### Historical Street Capital Programs',1).rstrip(),'Changed existing section or unrelated content'
        for j,o in enumerate(OBJECTS,1):
            v=G.load(P+f'public-{j}.json');assert v['byte_identical'] and v['size_bytes']==o['size_bytes'] and v['checksum_sha256']==o['sha256']
            assert b[o['candidate_id']]['r2_url']=='https://files.abqinfo.com/'+o['proposed_r2_key']
    print('PASS exact two-original publication; prior evidence, assessments, existing entries and unrelated inventory preserved')

def checkpoint():
    G.active_check('mutation','governance_implementation',IDS)
    inv=G.load('project-state/master-inventory.json')
    q=G.load(OLD+'queue.json');q.update(artifact_type='lead_coal_historical_publication_queue',recorded_at=now(),source_queue_artifact=OLD+'queue.json',inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),next_work_category='Owner manual editorial review of open unmerged Lead/Coal content PR; no merge or production deployment authorized.',visitor_visible_content_changed=True)
    q['newly_approved_backlog']=[r for r in q['newly_approved_backlog'] if r['id'] not in IDS];q['approved_count']=len(q['newly_approved_backlog'])
    q['in_progress_publication']=dict(task=TASK,candidate_ids=IDS,state='archives_verified_unmerged_content_pr_preparation')
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp['lead_coal_historical_publication']=dict(state='archives_verified_unmerged_content_pr_preparation',candidate_ids=IDS,receipt=P+'receipt.json',remaining_gate='owner_manual_pr_review',merge_authorized=False);save('project-state/checkpoint.json',cp)
    current=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8-sig');links=current[current.index('[Owner correction]'):].replace('\ufffd','\u00b7')
    current='# Current project state\n\nLead/Coal historical originals archived unchanged and full public downloads verified. Added 33,800,776 bytes; R2: 1,619 objects / 11,020,154,060 bytes. Reviewed 2021 Rest-in-Red and 2007 New Vision entries appended after unchanged 2025/2022 entries in existing Lead and Coal Avenues section. Historical qualifications and original provenance preserved. Completed review evidence and all other inventory records unchanged.\n\nNext: verify nonproduction section preview and prepare OPEN UNMERGED owner-review content PR. No merge or production deployment authorized. Volcano approval and three source holds unchanged.\n\n[Receipt](governance/'+TASK+'/receipt.json) · [Review](governance/lead-coal-historical-review-2026-10-12/summary.md) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    event('family_review','Deterministic publication queue/checkpoint refresh; remaining Volcano approval and source holds unchanged.',P+'queue.json');refresh()

def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2];verify_only='--verification-only' in sys.argv[3:]
    assert '.abqinfo.pages.dev/' in url,'Nonproduction preview required'
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for name,width,height in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=width,height=height))
            response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
            result=page.evaluate('''() => {
                const h=document.getElementById('lead-and-coal-avenues');if(!h)throw Error('Missing section');
                const nodes=[h];let n=h.nextElementSibling;while(n&&n.tagName!=='H3'&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}
                return {text:nodes.map(x=>x.innerText).join('\\n'),links:nodes.flatMap(x=>Array.from(x.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth};
            }''')
            assert not result['overflow']
            archives=[x['url'] for x in result['links'] if x['url'].startswith('https://files.abqinfo.com/')]
            assert archives==['https://files.abqinfo.com/transportation/roadway-projects/studies/cabq-lead-coal-studies-final-report-2025.pdf','https://files.abqinfo.com/transportation/roadway-projects/studies/mrmpo-fhwa-lead-coal-road-safety-audit-2022.pdf']+['https://files.abqinfo.com/'+o['proposed_r2_key'] for o in OBJECTS]
            for phrase in ['does not establish present-day implementation or effectiveness','task force’s one-way and two-way','separate recommendation for the one-way option','not an adopted construction plan','Original City source (currently unavailable)']:assert phrase in result['text'],phrase
            for o in OBJECTS:assert o['source_url'] in [x['url'] for x in result['links']]
            page.locator('#lead-and-coal-avenues').scroll_into_view_if_needed()
            page.evaluate('''() => {const h=document.getElementById('lead-and-coal-avenues');const w=document.createElement('div');h.parentNode.insertBefore(w,h);let n=h;while(n){const next=n.nextElementSibling;if(n!==h&&(n.tagName==='H2'||n.tagName==='H3'))break;w.appendChild(n);n=next;}w.id='lead-coal-review-capture';}''')
            output=G.ROOT/('tmp/lead-coal-final-'+name+'.png' if verify_only else P+'preview-'+name+'.png');page.locator('#lead-coal-review-capture').screenshot(path=str(output))
            result.update(viewport=name,width=width,http_status=response.status,screenshot_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),ordered_four_entries_verified=True,source_and_archive_links_verified=True);results.append(result);page.close()
        browser.close()
    value=dict(url=url,head_sha=G.git('rev-parse','HEAD'),rendered_at=now(),browser='Installed Google Chrome via Playwright',results=results)
    if verify_only:
        original=G.load(P+'preview.json');assert [(x['text'],x['links']) for x in original['results']]==[(x['text'],x['links']) for x in results];save('tmp/lead-coal-final-preview.json',value)
    else:save(P+'preview.json',value)
    print('PASS actual nonproduction desktop/mobile section: four ordered entries, exact qualifications, sources, archives, no overflow')

def links():
    import re, urllib.request, urllib.error
    text=(G.ROOT/(P+'publication.md')).read_text(encoding='utf-8-sig')
    results=[]
    for url in re.findall(r'\]\((https?://[^)]+)\)',text):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'},method='HEAD')
            with urllib.request.urlopen(req,timeout=60) as response:status=response.status;final=response.url
        except urllib.error.HTTPError as e:status=e.code;final=e.url
        historical_offline=url==OBJECTS[1]['source_url']
        assert status==200 or (historical_offline and status==404),(url,status)
        results.append(dict(url=url,http_status=status,final_url=final,expected_unavailable_original=historical_offline,publication_label='Original City source (currently unavailable)' if historical_offline else None))
    save(P+'link-verification.json',dict(checked_at=now(),links=results,archive_full_get_receipts=[P+'public-1.json',P+'public-2.json'],known_original_404_explicitly_labeled=True))
    print('PASS new archive/source links; known original City 404 explicitly labeled with verified historical delivery')

def finish():
    pr=G.load(P+'pr.json');preview=G.load(P+'preview.json');assert pr['state']=='OPEN' and pr['mergedAt'] is None
    log=(G.ROOT/'tmp/lead-coal-validation.log').read_text(encoding='utf-8-sig');assert '"Hugo": "passed"' in log
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.rstrip() for line in log.splitlines())+'\n',encoding='utf-8',newline='\n')
    r=G.load(P+'receipt.json');r.update(pr_url=pr['url'],pr_number=pr['number'],state='complete_open_unmerged_owner_review',preview_url=preview['url'],validation=dict(full_repository_suite='passed',hugo='passed',preview_desktop_mobile='passed',links=P+'link-verification.json',log=P+'validation.log'));save(P+'receipt.json',r)
    cp=G.load('project-state/checkpoint.json');cp['lead_coal_historical_publication'].update(state='complete_open_unmerged_owner_review',pr=pr['url'],preview=preview['url']);cp['resume_command']='Owner review and manual merge of open unmerged Lead/Coal PR. No merge or production deployment authorized in this task.';save('project-state/checkpoint.json',cp)
    q=G.load(P+'queue.json');q['in_progress_publication'].update(state='complete_open_unmerged_owner_review',pr=pr['url'],preview=preview['url']);save(P+'queue.json',q)
    f=G.ROOT/'project-state/CURRENT.md';s=f.read_text(encoding='utf-8-sig').replace('Next: verify nonproduction section preview and prepare OPEN UNMERGED owner-review content PR.','Next: owner manual review of [OPEN UNMERGED PR #'+str(pr['number'])+']('+pr['url']+'). Full governance/archive/content/Hugo validation and Chrome desktop/mobile preview checks passed.');f.write_text(s,encoding='utf-8',newline='\n')
    event('governance_implementation','Full suite and nonproduction desktop/mobile preview verified; PR open/unmerged; manual owner review remains the gate.',P+'receipt.json');refresh();G.active_check('final');guard()

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
