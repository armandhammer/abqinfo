"""Exact one-record factual source recovery; no publication or storage effects."""
import copy, gzip, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, git, canonical_bytes

TASK='mcduffie-source-recovery-2026-10-06'
P='project-state/governance/'+TASK+'/'
BASE='3fa18db2ab70856fdee58cf4dbb602a5be280c82'
ID='src-2f89e1bc040e1d33'
SCRIPT='scripts/project/McDuffieSourceRecovery.py'

def now(): return datetime.now(timezone.utc).isoformat()

def refresh():
    registry=G.load(G.REGISTRY)
    for row in registry['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,registry)
    registered={a['path'] for r in G.registry()['entries'] for a in r['controlling_artifacts']}
    paths=[p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in registered|{G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],P+'implementation.json'}]
    audit(paths)
    versions=list((G.ROOT/P).glob('contract-v*.json'))
    n=max(int(p.stem.split('-v')[1]) for p in versions)+1
    assert n<=30
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'] and not c['unresolved_gates']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(actions=G.load(P+'population.json')['operation_classes'],events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    evidence=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan['completion_evidence']={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
    print(path,len(c['governance_ids']),'rules; no gates/conflicts')

def event(op,summary,evidence):
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',plan)

def setup():
    assert G.git('rev-parse','HEAD')==BASE
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    instruction='Current explicit owner instruction: exactly '+ID+' factual City source/provenance recovery. Independently visit parent and share using installed Chrome/Playwright; inspect actual public download behavior and measure PDF against owner-retrieved 11940327 bytes / SHA256 48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15 / 321 pages. Save immutable evidence. Resolve former factual inability to attest URL-to-bytes only if conclusive. Preserve historical evidence and all settled unrelated decisions. No new scope/quality/publication approval inferred from retrieval. Only authorized factual background inventory/queue changes; regenerate accounting and full validation. Background-only main/planning integration authorized after fresh governance and validation. No visitor-visible or R2 mutation, publication PR, Sandia record or other population.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',instruction=instruction,candidate_ids=[ID]))
    r=G.registry();r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='One-record McDuffie factual source recovery',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-06',effective_date='2026-10-06',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No R2 or visitor-visible changes; no automatic publication eligibility.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='factual source recovery'))
    save(G.REGISTRY,r)
    row=next(x for x in G.load('project-state/master-inventory.json')['candidates'] if x['id']==ID)
    prior='project-state/governance/pr213-postmerge-closeout-2026-10-06/'
    protected=git('ls-tree','-r','--name-only',BASE,'--',prior).decode().splitlines()+['project-state/discovery/file-share-retrieval-research-2026-09-14.json','project-state/discovery/owner-decisions-2026-09-26/next-ordinary-queue.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json']
    G.write_once(P+'starting-state.json',dict(observed_at=now(),remote_refs=dict(main=BASE,planning_snapshot=BASE),remote_verification='Independent git ls-remote origin refs/heads/main refs/heads/chatgpt/planning-snapshot; both matched clean local HEAD.',selected_row=row,source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],content_tree_oid=G.git('rev-parse',BASE+':content'),protected_sha256={p:G.file_hash(p) for p in protected}))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='pr213-postmerge-closeout-2026-10-06'
    life['stages'][-1]['end_commit']=BASE
    existing={s['path'] for s in life['protected_evidence']}
    for p in protected:
        if p.startswith(prior) and p not in existing:life['protected_evidence'].append(dict(path=p,commit=BASE,sha256=G.file_hash(p)))
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='McDuffieSourceRecovery',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',life)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf8');s=s.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/McDuffieSourceRecovery.py" guard\nif ($LASTEXITCODE) { throw \'McDuffie exact one-record source recovery guard failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(s,encoding='utf8',newline='\n')
    event('governance_implementation','Exact population and complete registry resolved; preceding completed PR213 stage sealed at authoritative synchronized commit.',P+'starting-state.json')
    save(P+'progress.json',dict(state='governed_source_recovery_ready',remaining=['Chrome source retrieval','factual disposition','full validation','background integration'],r2_delta=0,visitor_visible_delta=0))
    refresh();G.active_check('mutation','document_review',[ID]);guard()

def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,start['content_tree_oid'])
    for p,h in start['protected_sha256'].items():assert G.file_hash(p)==h,'Protected prior evidence/storage changed: '+p
    a={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']}
    b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<={ID}
    allowed={'direct_file_url','file_type','size_bytes','checksum_sha256','provenance_status','processing_notes','local_path','updated_at'}
    assert {k for k in a[ID].keys()|b[ID].keys() if a[ID].get(k)!=b[ID].get(k)}<=allowed
    assert b[ID]['status']=='pending review','Source recovery does not authorize publication eligibility'
    assert b[ID]['processing_notes'][:len(a[ID]['processing_notes'])]==a[ID]['processing_notes']
    if (G.ROOT/(P+'record-updates.json')).exists():
        ev=stage.load_json(P+'retrieval.json');raw=stage.read_bytes(P+'download.pdf')
        assert len(raw)==11940327 and hashlib.sha256(raw).hexdigest()=='48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15'
        assert ev['download']['matches_owner_retrieved_original'] and ev['download']['page_count']==321 and ev['provenance_blocker']=='conclusively_resolved'
        net=stage.load_json(P+'network.json')
        deliveries=[n for n in net if '/api/rest/v1/files/' in n['url'] and n['status']==200]
        assert any(n.get('response',{}).get('download_uri')==ev['download']['url'] for n in deliveries),'Observed public API delivery must match browser download'
        assert ev['parent']['share_links']==[dict(text='McDuffie/Twin Parks Traffic Calming Study',url=a[ID]['source_url'])]
        expected=stage.load_json(P+'record-updates.json')[0]['changes']
        assert all(b[ID].get(k)==v for k,v in expected.items())
        q=stage.load_json(P+'queue.json');prior=stage.load_json(start['source_queue'])
        blocked=copy.deepcopy(prior['source_or_structural_blocked_pending_ids']);del blocked[ID]
        assert q['source_or_structural_blocked_pending_ids']==blocked and q['gated_pending_ids']==prior['gated_pending_ids']
        assert q['ungated_pending_ids']==q['actionable_ungated_pending_ids']==[ID]
        assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,340,321,18)
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
    print('McDuffie exact one-record factual recovery; sealed PR213/history, pending status, zero visible/R2 guard passed')

def retrieve():
    from playwright.sync_api import sync_playwright
    G.active_check('mutation','document_review',[ID])
    row=G.load(P+'starting-state.json')['selected_row'];network=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        context=browser.new_context(accept_downloads=True,viewport=dict(width=1440,height=1100))
        page=context.new_page()
        def capture(response):
            if 'sfftp.cabq.gov' in response.url:
                entry=dict(url=response.url,status=response.status,method=response.request.method,resource_type=response.request.resource_type,content_type=response.headers.get('content-type'))
                if 'json' in (entry['content_type'] or ''):
                    try:entry['response']=response.json()
                    except Exception:pass
                network.append(entry)
        page.on('response',capture)
        response=page.goto(row['parent_url'],wait_until='networkidle',timeout=90000)
        parent=dict(url=page.url,status=response.status,title=page.title(),share_links=page.locator('a[href*="cf8779d97e34c92c"]').evaluate_all('(as)=>as.map(a=>({text:a.innerText,url:a.href}))'),observed_at=now())
        (G.ROOT/(P+'parent.html.gz')).write_bytes(gzip.compress(page.content().encode(),mtime=0));page.screenshot(path=str(G.ROOT/(P+'parent.png')))
        response=page.goto(row['source_url'],wait_until='networkidle',timeout=90000)
        page.get_by_text('COA Final McDuffie_Traffic Calming Study 052024.pdf',exact=False).first.wait_for(timeout=60000)
        share=dict(url=page.url,status=response.status,title=page.title(),text=page.locator('body').inner_text(),links=page.locator('a').evaluate_all('(as)=>as.map(a=>({text:a.innerText,url:a.href}))'),buttons=page.get_by_role('button').all_text_contents(),observed_at=now())
        page.get_by_role('button',name='COA Final McDuffie_Traffic Calming Study 052024.pdf',exact=True).click()
        page.get_by_role('button',name='Download',exact=True).wait_for(timeout=30000)
        share['after_file_click']=dict(url=page.url,text=page.locator('body').inner_text(),buttons=page.get_by_role('button').evaluate_all('(bs)=>bs.map(b=>({text:b.innerText,label:b.getAttribute("aria-label"),title:b.getAttribute("title")}))'))
        with page.expect_download(timeout=90000) as pending:
            page.get_by_role('button',name='Download',exact=True).click()
        download=pending.value
        download.save_as(str(G.ROOT/(P+'download.pdf')))
        data=(G.ROOT/(P+'download.pdf')).read_bytes()
        sys.path.insert(0,str(G.ROOT/'tmp/pgs-pdf-deps'))
        import pymupdf as fitz
        doc=fitz.open(stream=data,filetype='pdf');cover=doc[0].get_text()
        (G.ROOT/(P+'cover.txt')).write_text(cover,encoding='utf8',newline='\n')
        doc[0].get_pixmap(matrix=fitz.Matrix(1,1)).save(str(G.ROOT/(P+'cover.png')))
        actual=dict(url=download.url,filename=download.suggested_filename,failure=download.failure(),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),pdf_header=data[:8].decode('ascii'),page_count=len(doc),is_encrypted=doc.is_encrypted,eof_present=b'%%EOF' in data[-1024:],cover=cover,observed_at=now())
        actual['matches_owner_retrieved_original']=actual['size_bytes']==11940327 and actual['sha256']=='48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15' and actual['page_count']==321
        (G.ROOT/(P+'share.html.gz')).write_bytes(gzip.compress(page.content().encode(),mtime=0));page.screenshot(path=str(G.ROOT/(P+'share.png')))
        save(P+'network.json',network)
        save(P+'retrieval.json',dict(state='actual_pdf_independently_retrieved',browser='Installed Google Chrome via Playwright',method='Fresh anonymous browser context: City parent link -> public share -> named file -> visible Download control -> Playwright download event -> saved exact original bytes; no login or credentials.',parent=parent,share=share,download=actual))
        print(json.dumps(dict(download=actual,network=[n for n in network if '/bundles/' in n['url'] or n['resource_type']=='document']),indent=2))
        browser.close()

def disposition():
    sys.path.insert(0,str(G.ROOT/'tmp/pgs-pdf-deps'));import pymupdf
    ev=G.load(P+'retrieval.json');actual=ev['download'];assert actual['matches_owner_retrieved_original']
    data=(G.ROOT/(P+'download.pdf')).read_bytes();assert hashlib.sha256(data).hexdigest()==actual['sha256']
    with pymupdf.open(stream=data,filetype='pdf') as d:
        text='\n'.join('PAGE '+str(n+1)+'\n'+d[n].get_text() for n in range(3))
        assert len(d)==321 and 'City of Albuquerque' in text and 'Wilson & Company' in text and '5/7/2024' in text
        # Parse each page to establish a valid complete page tree without making a publication-quality judgment.
        assert all(d[n].rect.width>0 and d[n].rect.height>0 for n in range(len(d)))
    (G.ROOT/(P+'cover.txt')).write_text('\n'.join(line.rstrip() for line in text.splitlines())+'\n',encoding='utf8',newline='\n')
    ev['identity']=dict(title='McDuffie/Twin Parks Neighborhood Traffic Calming Study',report_date='2024-05-07',prepared_for='City of Albuquerque',prepared_by='Wilson & Company, Inc., Engineers & Architects',opening_pages=P+'cover.txt',cover_visual_inspection='Confirmed title, City, neighborhood and 5/7/2024 on rendered cover.',all_321_pages_parse=True)
    ev['provenance_blocker']='conclusively_resolved'
    ev['download_relationship']='Public share metadata identifies read-only/no-password/no-registration share; named-file Download control issues a signed S3 original-PDF URL valid for 60 seconds. Durable official source is the City share URL; signed URL is a delivery witness, not a stable direct_file_url.'
    save(P+'retrieval.json',ev)
    event('document_review','Independent anonymous Chrome parent/share/download reproduces exact preserved owner file. Valid 321-page PDF and May7 2024 City/Wilson identity confirmed; factual URL-to-bytes provenance blocker conclusively resolved.',P+'retrieval.json')
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    row=G.load(P+'starting-state.json')['selected_row']
    note='2026-10-06 independent source recovery: installed Chrome/Playwright visited current official City parent and its public share, then downloaded COA Final McDuffie_Traffic Calming Study 052024.pdf using the visible Download control. Exact 11,940,327 bytes / SHA-256 48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15 / valid 321 pages match the preserved owner-retrieved original. May 7, 2024 City of Albuquerque McDuffie/Twin Parks study prepared by Wilson & Company confirmed. Former inability to independently attest URL-to-bytes provenance conclusively resolved. Share generates a 60-second signed download URL, so durable source remains the official share and direct_file_url remains null. Pending review retained: scope/quality/archival/publication eligibility not assessed or authorized by this factual task. Evidence: '+P+'retrieval.json.'
    changes=dict(file_type='PDF',size_bytes=actual['size_bytes'],checksum_sha256=actual['sha256'],provenance_status='Independently retrieved exact original from official City parent-linked public share; preserved owner-file SHA-256 reproduced; former URL-to-bytes blocker resolved.',processing_notes=row['processing_notes']+[note],local_path=P+'download.pdf')
    G.write_once(P+'record-updates.json',[dict(id=ID,changes=changes)])
    refresh();G.active_check('mutation','inventory_disposition',[ID])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    inv=G.load('project-state/master-inventory.json');start=G.load(P+'starting-state.json');q=copy.deepcopy(G.load(start['source_queue']))
    assert ID in q['source_or_structural_blocked_pending_ids']
    del q['source_or_structural_blocked_pending_ids'][ID]
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'}
    q.update(artifact_type='mcduffie_factual_source_recovery_queue',recorded_at=now(),source_queue_artifact=start['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_ids=sorted(pending),pending_review_count=len(pending))
    for kind in ['gated','source_or_structural_blocked']:q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated))
    q['actionable_ungated_pending_ids']=sorted(set(q['actionable_ungated_pending_ids'])|{ID})
    q['genuinely_actionable_ungated_pending_count']=len(q['actionable_ungated_pending_ids'])
    q['resolved_source_provenance']={ID:dict(evidence=P+'retrieval.json',result='Exact owner-file bytes independently reproduced; source blocker cleared, ordinary scope/quality review remains.')}
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],completed_item_range='Exactly one McDuffie source/provenance blocker conclusively resolved by independent exact-byte Chrome retrieval; pending review retained. Zero R2/visitor-visible delta.',resume_command='Read CURRENT and McDuffie source recovery receipt. Factual task complete; no next population begun. Ordinary scope/quality review is separate governed work.')
    save('project-state/checkpoint.json',cp)
    accounting=dict(approved=q['approved_count'],pending=q['pending_review_count'],gated=q['gated_pending_count'],source_structural_blocked=q['source_or_structural_blocked_pending_count'],ungated=q['ungated_pending_count'],actionable=q['genuinely_actionable_ungated_pending_count'],human_review=sum(r['status']=='requires human review' for r in inv['candidates']),changed_record_ids=[ID],status='pending review',r2_delta=0,visitor_visible_delta=0)
    save(P+'accounting.json',accounting)
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,retrieval=P+'retrieval.json',matches_owner_original=True,provenance_blocker='conclusively_resolved',final_status='pending review',remaining_work='Separate governed mission-scope and publication-quality eligibility review; no source/provenance blocker remains.',owner_decision_required=False,accounting=accounting,r2_delta=0,visitor_visible_delta=0,normal_validation='pending',background_integration='pending',next_population_started=False))
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf8');links=old[old.index('[Owner correction]'):]
    current.write_text('# Current project state\n\nExactly src-2f89e1bc040e1d33 McDuffie/Twin Parks source/provenance blocker conclusively resolved. Anonymous installed Chrome retrieved the City parent-linked PDF: 11,940,327 bytes, 321 pages, SHA-256 48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15, identical to preserved owner file. May 7, 2024 City/Wilson study confirmed. Pending review retained; retrieval grants no eligibility, archive or publication authority. Queue: 0 approved / 340 pending (321 governance-gated / 18 source-structural blocked / 1 actionable ungated), 0 human review. Zero R2/visitor-visible delta; no owner decision or next population. Full validation/background integration pending.\n\n[Source receipt](governance/'+TASK+'/receipt.json) | [Active task](governance/active-task.json) | [Queue](ordinary-queue-current.json) | [Workflow](governance-workflow.md) | [Registry](governance-registry.json).\n\n'+links,encoding='utf8',newline='\n')
    event('inventory_disposition','Exact factual fields updated; pending review retained, former source blocker removed and one record becomes actionable for separate scope/quality review. Deterministic accounting/checkpoint updated; no storage/content delta.',P+'accounting.json')
    save(P+'progress.json',dict(state='factual_recovery_complete',remaining=['full validation','background integration'],r2_delta=0,visitor_visible_delta=0))
    refresh();G.active_check('final');guard()

def regenerate():
    G.active_check('mutation','governance_implementation',[ID])
    q=G.load(P+'queue.json')
    q['actionability_basis']='Historical follow-up and unrelated decisions preserved. Independent exact-byte McDuffie retrieval cleared only its source/provenance blocker; exactly one ungated pending record is actionable for separate scope/quality investigation, not preapproved or ranked for archiving/publication.'
    q['background_family_groups']=[dict(family_id='mcduffie-source-recovered',family='McDuffie/Twin Parks study',candidate_ids=[ID],candidate_count=1,evidence_artifact=P+'retrieval.json',selection_is_not_a_disposition=True)]
    q['next_work_category']='Separate governed mission-scope and publication-quality review; no next population launched or archive authorization.'
    save(P+'queue.json',q)
    # Same deterministic-only API as PR213: rebuilding zero-case accounting
    # does not launch a substantive family review or broaden this population.
    import importlib.util
    spec=importlib.util.spec_from_file_location('mcduffie_queue_builder',G.ROOT/'scripts/project/Build-ConsolidatedHumanReviewQueue.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    payload,report=module.build();assert payload['record_count']==0 and payload['packages']==[]
    save('project-state/discovery/consolidated-human-review-queue.json',payload)
    (G.ROOT/'project-state/discovery/consolidated-human-review-queue.md').write_text(report,encoding='utf8',newline='\n')
    event('governance_implementation','Regenerated empty consolidated human-review queue after inventory hash update; exact one-record ordinary grouping/accountability refreshed. No human decision added.',P+'queue.json')
    save(P+'progress.json',dict(state='validation_retry_after_derived_queue_regeneration',remaining=['full normal validation','background integration'],initial_validation_issue='Consolidated human-review queue inventory hash stale; deterministic regeneration applied, unresolved cases remain zero.'))
    refresh();G.active_check('final');guard()

def finish():
    log=(G.ROOT/'tmp/mcduffie-validation.log').read_text(encoding='utf8')
    assert '"Hugo": "passed"' in log and 'CURRENT.md resume-pointer regression passed.' in log
    assert 'contiguous stage intervals' in log and 'unchanged historical evidence files' in log
    assert 'Traceback (most recent call last)' not in log
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in log.splitlines())+'\n',encoding='utf8',newline='\n')
    page=G.ROOT/'tmp/site-build/transportation/roadway-projects/studies/index.html';html=page.read_text(encoding='utf8')
    assert 'cabq-mcduffie-twin-parks-traffic-calming-public-meeting-2-2023.pdf' in html
    assert 'cf8779d97e34c92c' not in html and 'mcduffie-source-recovery-2026-10-06/download.pdf' not in html
    save(P+'rendered-check.json',dict(result='passed',hugo_rendered_page=str(page.relative_to(G.ROOT)),sha256=hashlib.sha256(page.read_bytes()).hexdigest(),existing_2023_public_meeting_entry_preserved=True,final_report_not_added=True,unchanged_full_visitor_visible_tree=True,source_and_historical_rendered_checks='Full normal project suite passed; no live publication task.'))
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);r=G.load(P+'receipt.json')
    r.update(state='factual_recovery_complete_validation_passed',research_checkpoint_commit=G.git('rev-parse','HEAD'),normal_validation='passed',validation_log=P+'validation.log',rendered_checks=P+'rendered-check.json',initial_validation_issue='Derived empty consolidated human-review queue stale after inventory hash changed; regenerated deterministically, then complete normal suite passed.',background_integration='authorized atomic synchronization of final commit; independently verify remote refs after push',integration_intent=P+'integration-intent.json',governance_accounting={row['governance_id']:dict(requirement=row['binding_requirement'],implementation='Exact factual one-record source recovery under current owner authority; complete registry resolved, fresh contract at mutation points, original evidence and settled unrelated decisions preserved. No eligibility/quality/publication approval, campaign, owner question, R2 or visitor-visible change inferred. Former factual inability resolved by exact current public download, not by historical recommendation.',evidence=[P+'retrieval.json',P+'accounting.json',P+'validation.log'],controlling_artifacts_preserved=row['controlling_artifacts']) for row in c['resolved_rules']})
    save(P+'receipt.json',r)
    save(P+'integration-intent.json',dict(authority='owner-'+TASK,candidate_ids=[ID],remote_baseline=dict(main=BASE,planning_snapshot=BASE),operation='Fast-forward-only atomic push of final background commit to main and chatgpt/planning-snapshot, after independent remote ref and fresh governance verification.',prohibited=['visitor-visible changes','R2 effects','unrelated record changes','new population'],validation='Complete normal project suite passed',r2_delta=0,visitor_visible_delta=0))
    current=G.ROOT/'project-state/CURRENT.md';s=current.read_text(encoding='utf8').replace('Full validation/background integration pending.','Full normal validation passed (governance, sealed history, Hugo/rendered, CURRENT/checkpoint and diff checks). Final background commit synchronizes main/planning-snapshot.')
    assert len(s)<=1800;current.write_text(s,encoding='utf8',newline='\n')
    save(P+'progress.json',dict(state='complete_integration_ready',remaining=['guarded atomic remote synchronization'],owner_decision_required=False,next_population_started=False))
    event('background_integration','Complete normal validation passed after deterministic derived-queue regeneration; background-only integration authorized by current registered owner instruction.',P+'integration-intent.json')
    refresh();G.active_check('final');guard()

def integrate():
    refs=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()
    assert {line.split()[1]:line.split()[0] for line in refs}=={'refs/heads/main':BASE,'refs/heads/chatgpt/planning-snapshot':BASE}
    assert G.load(P+'receipt.json')['normal_validation']=='passed'
    G.active_check('mutation','background_integration',[ID]);guard()
    save(P+'progress.json',dict(state='complete',remaining=[],owner_decision_required=False,next_population_started=False,integration='Final commit carrying this receipt is synchronized atomically to main/planning-snapshot; concrete remote refs independently verified after push.'))
    refresh();G.active_check('mutation','background_integration',[ID])
    plan=G.load(P+'implementation.json');plan['status']='complete';save(P+'implementation.json',plan)
    active=G.load(G.ACTIVE_TASK);active['state']='complete';save(G.ACTIVE_TASK,active)
    G.active_check('final');guard()
    paths=[p for p in G.changed_paths(BASE) if not p.startswith('backups/')]
    subprocess.run(['git','add','--',*paths],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    subprocess.run(['git','commit','-m','Validate and integrate McDuffie factual source recovery'],check=True)
    subprocess.run(['git','push','--atomic','origin','HEAD:main','HEAD:chatgpt/planning-snapshot'],check=True)
    head=G.git('rev-parse','HEAD')
    subprocess.run(['git','branch','-f','chatgpt/planning-snapshot',head],check=True)
    final=subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot'],encoding='utf8').splitlines()
    assert len(final)==2 and all(line.split()[0]==head for line in final)
    assert not G.git('status','--porcelain')
    assert hashlib.sha256(git('show',head+':'+P+'download.pdf')).hexdigest()=='48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15'
    save('tmp/mcduffie-final-refs.json',dict(main=head,planning_snapshot=head,remote_refs=final,verified_at=now(),clean_worktree=True,committed_original_pdf_hash_verified=True,validation='passed'))
    print('Final main/planning-snapshot:',head)

if __name__=='__main__':globals()[sys.argv[1]]()
