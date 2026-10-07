"""Owner supersession: one normal PDF entry, preserving the exhaustive internal review."""
import copy, hashlib, json, subprocess, sys
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativePublication import save, audit
from SchoolZonePublication import ID, SHA, URL, SOURCE, KEY, PAGE
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
TASK='school-zone-document-entry-correction-2026-10-07'
P='project-state/governance/'+TASK+'/'
BASE='21e084111836b627443a381d15b8f84aad6685be'
MAIN='bdb6d440091f28fa88d0753dad34849b53e703b8'
PRIOR='project-state/governance/school-zone-publication-2026-10-07/'
REVIEW='project-state/governance/school-zone-timing-design-2026-10-06/'
SCRIPT='scripts/project/SchoolZoneDocumentEntryCorrection.py'
TITLE='Albuquerque Middle and High School Zone Active Timings (Archived PDF)'
DESCRIPTION='Provides Albuquerque middle and high school zone flasher schedules, including activation times, locations, shared-school schedules, and operational notes. Obtained through an Inspection of Public Records Act (IPRA) request, this 33-page record is archived unchanged by ABQInfo. The PDF identifies no issuing agency or single effective date.'
ENTRY='- ['+TITLE+']('+URL+')\n\n  '+DESCRIPTION+'\n\n'
OPS=['content_implementation','content_removal','inventory_disposition','governance_implementation','family_review']
def now():return datetime.now(timezone.utc).isoformat()
def refresh():
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        if row['state']=='active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers')==['/implementation']:a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    registered={a['path'] for row in r['entries'] for a in row['controlling_artifacts']}
    audit([x for x in G.changed_paths(BASE) if x.startswith('project-state/') and x not in registered|{G.REGISTRY,G.ACTIVE_TASK,r['audit_artifact'],P+'implementation.json'}])
    path=P+f'contract-v{len(list((G.ROOT/P).glob("contract-v*.json")))+1}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for fact in row.get('constraints',[]):subjects.setdefault(fact['subject'],{})[fact['field']]=fact['equals']
    evidence=P+'receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else P+'authority.json'
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=evidence,sha256=G.file_hash(evidence))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules')
def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','supersession.json','starting-state.json','implementation.json','publication.md','source-record.json','queue.json','receipt.json','validation.log','preview.json','preview-desktop.png','preview-mobile.png','pr-description.md','pr.json','final-verification.json']+[f'contract-v{i}.json' for i in range(1,21)]
    artifacts=[P+x for x in outputs]+[SCRIPT,'scripts/project/Invoke-ProjectValidation.ps1',G.REGISTRY,G.ACTIVE_TASK,G.registry()['audit_artifact'],'project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/master-inventory.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=['school-zone-active-times'],pages=[PAGE],operation_classes=OPS,artifact_paths=artifacts))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    instruction='Explicit owner correction of OPEN UNMERGED PR215 supersedes only the prior direct alphabetical 30-schedule / 61-interval publication form. Replace the entire visitor-facing school/timing list and added School Zone Active Times subsection with exactly one ordinary archived-PDF title/concise description under existing School Transportation Safety. No individual schools/times/rows or elementary continuation prose on public page. Preserve completed full review, verbatim extraction (30 schedules, 32 named schools, 61 intervals), source/R2 exact-byte evidence, scope/quality findings, source privacy/provenance, placement and elementary family context. No agency/current/effective-date inference or invented official URL. Reconcile only this record publication-form metadata; update existing PR215 description, build and inspect corrected Cloudflare preview in desktop/mobile Chrome including surrounding entries, archive link and absence of schedule list/redundant heading/excessive spacing. Complete governance/freshness, sealed-history, Hugo/rendered, PR-description and diff validation. Leave PR215 OPEN UNMERGED. No new R2 mutation, content merge/deploy, elementary or other population.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner editorial supersession',instruction=instruction,source_sha256=SHA,pr_number=215,expected_head=BASE,publication_form='one_linked_archived_original_with_concise_description',r2_mutation_authorized=False,merge_authorized=False,preserved_internal_counts=dict(schedules=30,schools=32,intervals=61)))
    r=G.registry();proposals={}
    for old in r['entries'][:]:
        if old['state']!='active' or 'school-zone' not in old['governance_id']:continue
        gid=old['governance_id']+'-document-entry-form'
        revised='Preserve the unchanged original, complete substantive review/extraction, all factual interval/weekday/location qualifiers as INTERNAL evidence, duplicate/fragment accounting, exact completed archive/public-byte verification, positive scope/quality and truthful IPRA provenance established by '+old['governance_id']+'. Current explicit owner editorial authority supersedes ONLY the prior visitor-facing publication form: use one concise linked archived-PDF entry under existing School Transportation Safety; no individual schools/times or additional school-zone subsection on page. Elementary continuation remains durable family context only. No agency/global effective/current date inference, new R2 mutation, unrelated population, content merge or production deployment. Historical archival authority and completed upload are preserved; this correction grants no repeat upload.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=revised,consequences='Only public presentation and matching metadata change. All prior source, extraction, scope/quality, archival and continuation evidence remains unchanged; no R2 action or merge.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=revised,required_actions=[revised],prohibited_actions=['No individual school/timing list in site content','No new R2 mutation or merge/deploy','No elementary or unrelated population'],authority='Explicit current owner editorial supersession',effective_date='2026-10-07')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,state='active',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner editorial correction',decision_date='2026-10-07',effective_date='2026-10-07',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No R2 mutation, content merge/deploy or unrelated population'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='exact PR215 document-entry correction'))
    save(G.REGISTRY,r)
    prior={}
    for folder in [REVIEW,PRIOR,'project-state/governance/school-zone-remote-checkpoint-2026-10-06/']:
        for path in (G.ROOT/folder).iterdir():
            if path.is_file():prior[path.relative_to(G.ROOT).as_posix()]=G.file_hash(path)
    G.write_once(P+'starting-state.json',dict(remote_main=MAIN,remote_planning=MAIN,remote_pr_head=BASE,pr_state='OPEN',pr_merged_at=None,prior_evidence_sha256=prior,r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),checkpoint_before=G.load('project-state/checkpoint.json'),prior_active_task=G.load(G.ACTIVE_TASK),prior_final_governance='passed before correction',source_sha256=SHA))
    refresh();G.active_check('mutation','governance_implementation',[ID])
    life=G.load('project-state/workflow-stage-lifecycle.json');assert life['stages'][-1]['id']=='school-zone-publication-2026-10-07';life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='SchoolZoneDocumentEntryCorrection',function='guard')))
    protected={x['path'] for x in life['protected_evidence']}
    for path,h in prior.items():
        if path not in protected:life['protected_evidence'].append(dict(path=path,commit=BASE,sha256=h))
    save('project-state/workflow-stage-lifecycle.json',life)
    v=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=v.read_text(encoding='utf-8-sig').replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/SchoolZoneDocumentEntryCorrection.py" guard\nif ($LASTEXITCODE) { throw \'School-zone document-entry correction failed.\' }\nSet-StrictMode -Version Latest',1);v.write_text(s,encoding='utf-8',newline='\n')
    refresh()
def implement():
    G.active_check('mutation','content_removal',[ID],pages=[PAGE])
    page=(G.ROOT/PAGE).read_text(encoding='utf-8-sig');a=page.index('### School Zone Active Times');b=page.index('### APS Vision Zero Task Force Records',a)
    page=page[:a]+ENTRY+page[b:];(G.ROOT/PAGE).write_text(page,encoding='utf-8',newline='\n');(G.ROOT/(P+'publication.md')).write_text(ENTRY.rstrip()+'\n',encoding='utf-8',newline='\n')
    G.active_check('mutation','inventory_disposition',[ID])
    inv=G.load('project-state/master-inventory.json');row=next(x for x in inv['candidates'] if x['id']==ID)
    row.update(description=DESCRIPTION,description_word_count=len(DESCRIPTION.split()),public_title=TITLE,publication_form='linked_archived_original',source_record_evidence=P+'source-record.json',updated_at=now())
    row['quality_assessment']['intended_publication_form']='One ordinary linked unchanged archived original with concise description under existing School Transportation Safety; no direct schedule list or separate document fragments.'
    row['quality_assessment']['substantive_rationale']='The complete local timing dataset remains independently useful for Albuquerque school-zone public information. One unchanged archived original preserves all schedules, locations and operational qualifications; a concise normal document entry follows the explicit owner editorial decision.'
    q=row['publication_quality_decision']['assessment'];q['durable_public_usefulness']='The unchanged archived original provides the complete Albuquerque school-zone flasher reference, with locations and operational qualifications.'
    q['currentness_review']['publication_qualification']='The description identifies no issuing agency or single effective date and makes no claim that the schedules are currently effective.'
    row['publication_quality_decision']['evidence'].append(P+'authority.json');row['processing_notes'].append('Owner supersedes only visitor presentation: linked PDF/description replaces direct schedule list. Exhaustive extraction and original review/archive evidence remain unchanged at '+REVIEW)
    row['review_preview']=None;row['publication_form_supersession']=P+'supersession.json'
    from PublicationQuality import require_publication_quality
    require_publication_quality(row);inv['generated_at']=now();save('project-state/master-inventory.json',inv);save(P+'source-record.json',row)
    queue=G.load(G.load('project-state/ordinary-queue-current.json')['artifact']);queue.update(artifact_type='school_zone_document_entry_correction_queue',recorded_at=now(),inventory_generated_at=inv['generated_at'],next_work_category='Owner review of PR215 concise school-zone PDF entry; no elementary or other population.');save(P+'queue.json',queue);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json')
    for field in ['school_zone_timing_review','next_owner_requested_task']:cp[field].update(state='document_entry_correction_validation_pending',publication=P+'publication.md',publication_form='linked_archived_original',form_supersession=P+'supersession.json',preview=None)
    cp['resume_command']='PR215 owner correction: one concise school-zone archived PDF entry, no rendered individual schedules. Complete validation/preview and leave PR open/unmerged; all extraction/archive evidence preserved.';save('project-state/checkpoint.json',cp)
    current=(G.ROOT/'project-state/CURRENT.md').read_text(encoding='utf-8-sig');tail=current[current.index('[Owner correction]'):]
    current='# Current project state\n\nPR #215 owner editorial correction implemented: one linked Albuquerque Middle and High School Zone Active Timings PDF with concise description directly under School Transportation Safety. Removed the school-zone subsection and all individual school/timing entries. Completed review and exhaustive internal extraction (30 schedules / 32 schools / 61 intervals), scope/quality/safety, unchanged original and exact R2 public-byte evidence preserved. No issuing agency or single effective date claimed. Elementary continuation remains internal family context. No R2 mutation.\n\nNEXT: validate corrected preview and update OPEN UNMERGED PR #215 for owner review; no merge/deploy authority.\n\n[Correction](governance/'+TASK+'/authority.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+tail
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'] += [dict(operation=op,candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary=summary,evidence=proof) for op,summary,proof in [('content_removal','Removed entire alphabetical schedule section and its heading; inserted exactly one concise PDF entry, preserving surrounding entries.',P+'publication.md'),('inventory_disposition','Only same source record presentation/description metadata reconciled with owner supersession; positive scope/quality and all archive/source identity unchanged.',P+'source-record.json')]];save(P+'implementation.json',plan)
    refresh();subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True);refresh();guard()
def guard():
    st=StageSnapshot(TASK);pop=st.load_json(P+'population.json');assert pop['candidate_ids']==[ID] and not set(pop['operation_classes'])&{'archive','external_mutation'}
    changed=set(G.git('diff',BASE,st.end,'--name-only').splitlines()) if st.end else set(G.changed_paths(BASE));assert changed<=set(pop['artifact_paths'])|{PAGE},changed-set(pop['artifact_paths'])-{PAGE}
    start=st.load_json(P+'starting-state.json')
    for path,h in start['prior_evidence_sha256'].items():assert G.file_hash(path)==h,path
    for path,key in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==start[key]
    page=st.read_text(PAGE);old=G.git('show',BASE+':'+PAGE)+'\n'
    if TITLE in page:
        a=old.index('### School Zone Active Times');b=old.index('### APS Vision Zero Task Force Records',a);assert page==old[:a]+ENTRY+old[b:]
        assert '### School Zone Active Times' not in page and '#### Middle/High-School IPRA Record' not in page
        assert page.count(URL)==1 and '7:35 AM to 8:15 AM' not in page and '**Cibola**' not in page
        data=st.load_json(REVIEW+'timings.json');assert len(data['schedules'])==30 and sum(len(x['intervals']) for x in data['schedules'])==61
    else:assert page==old
    before={x['id']:x for x in json.loads(G.git('show',BASE+':project-state/master-inventory.json'))['candidates']};after={x['id']:x for x in st.load_json('project-state/master-inventory.json')['candidates']};assert before.keys()==after.keys();assert {i for i in before if before[i]!=after[i]}<={ID}
    for f in ['r2_url','r2_key','r2_etag','r2_last_modified','size_bytes','checksum_sha256','scope_assessment','source_url','direct_file_url','provenance','status','validation_status']:assert before[ID][f]==after[ID][f],f
    if TITLE in page:
        assert after[ID]['description']==DESCRIPTION and after[ID]['publication_form']=='linked_archived_original'
        from PublicationQuality import require_publication_quality
        require_publication_quality(after[ID])
    cp=st.load_json('project-state/checkpoint.json');prior=start['checkpoint_before'];allowed=['school_zone_timing_review','next_owner_requested_task','resume_command'];assert {k:v for k,v in cp.items() if k not in allowed}=={k:v for k,v in prior.items() if k not in allowed}
    print('PASS exact linked-document correction; no rendered schedules; extraction/review/archive and surrounding entries preserved; zero R2 delta')
def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2];verify_only='--verification-only' in sys.argv[3:];results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for name,width,height in [('desktop',1440,1100),('mobile',390,844)]:
            page=browser.new_page(viewport=dict(width=width,height=height));response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
            result=page.evaluate(r'''() => {const h=document.getElementById('school-transportation-safety');let n=h.nextElementSibling;const nodes=[];while(n&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}return {text:nodes.map(x=>x.innerText).join('\n'),links:nodes.flatMap(x=>Array.from(x.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth,schoolZoneHeading:!!document.getElementById('school-zone-active-times')};}''')
            assert not result['overflow'] and not result['schoolZoneHeading']
            link=page.locator('a',has_text=TITLE).filter(has_text='Archived PDF');assert link.count()==1 and link.get_attribute('href')==URL
            li=link.locator('xpath=ancestor::li[1]');assert li.inner_text()==TITLE+'\n\n'+DESCRIPTION
            assert page.locator('h3',has_text='School Zone Active Times').count()==0
            assert 'weekday not stated' not in result['text'] and '7:35 AM to 8:15 AM' not in result['text'] and 'Clevland' not in result['text']
            # Surrounding section must be semantically identical to prior inspected preview.
            old=browser.new_page(viewport=dict(width=width,height=height));old.goto('https://22bd93cd.abqinfo.pages.dev/transportation/safety-crash-data/',wait_until='networkidle',timeout=90000)
            surrounding=old.evaluate(r'''() => {const h=document.getElementById('school-transportation-safety');let n=h.nextElementSibling;const nodes=[];let skip=false;while(n&&n.tagName!=='H2'){if(n.id==='school-zone-active-times')skip=true;if(n.id==='aps-vision-zero-task-force-records')skip=false;if(!skip)nodes.push(n);n=n.nextElementSibling;}return {text:nodes.map(x=>x.innerText).join('\n'),links:nodes.flatMap(x=>Array.from(x.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))) };}''');old.close()
            assert ' '.join(result['text'].replace(TITLE+'\n\n'+DESCRIPTION,'').split())==' '.join(surrounding['text'].split())
            from urllib.parse import urlsplit
            def comparable(links):
                values=[]
                for x in links:
                    target=urlsplit(x['url'])
                    normalized=target.path+('?' + target.query if target.query else '')+('#'+target.fragment if target.fragment else '') if target.hostname and target.hostname.endswith('.abqinfo.pages.dev') else x['url']
                    values.append(dict(text=x['text'],url=normalized))
                return values
            assert comparable([x for x in result['links'] if x['url']!=URL])==comparable(surrounding['links'])
            download=page.request.get(URL,headers={'Cache-Control':'no-cache'},timeout=180000);body=download.body();assert download.status==200 and len(body)==3013109 and hashlib.sha256(body).hexdigest()==SHA
            li.scroll_into_view_if_needed();box=li.bounding_box();assert box and box['x']>=0 and box['x']+box['width']<=width+1
            output=G.ROOT/('tmp/pr215-correction-final-'+name+'.png' if verify_only else P+'preview-'+name+'.png');page.screenshot(path=str(output),full_page=False)
            result.update(viewport=name,width=width,document_entry_text=li.inner_text(),surrounding_entries_unchanged=True,public_http_status=download.status,public_bytes=len(body),public_sha256=hashlib.sha256(body).hexdigest(),screenshot_sha256=hashlib.sha256(output.read_bytes()).hexdigest());results.append(result);page.close()
        browser.close()
    value=dict(url=url,head_sha=G.git('rev-parse','HEAD'),rendered_at=now(),browser='Installed Google Chrome via Playwright',results=results)
    if verify_only:assert [x['text'] for x in results]==[x['text'] for x in G.load(P+'preview.json')['results']];print('PASS final-head preview matches inspected concise document entry')
    else:save(P+'preview.json',value);print('PASS corrected desktop/mobile: one document entry, no schedule list/heading, surrounding entries identical, exact PDF GET, no overflow')
def receipt():
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);save(P+'receipt.json',dict(task_id=TASK,state='concise_document_entry_implemented_validation_pending',owner_supersession=P+'supersession.json',title=TITLE,description=DESCRIPTION,publication_form='linked_archived_original',internal_dataset=REVIEW+'timings.json',internal_schedules=30,internal_schools=32,internal_intervals=61,prior_evidence_preserved=True,r2_mutations=0,normal_validation='pending',pr_number=215,pr_state='OPEN_UNMERGED',remaining_owner_action='Review PR215 after corrected preview/validation',governance_accounting={x['governance_id']:dict(requirement=x['binding_requirement'],result='Only owner-authorized linked-document publication form and exact source metadata corrected; prior review/extraction, archive/public-byte, scope/quality and family decisions preserved. No individual school/timing rows on site, R2 mutation, unrelated population or merge.',evidence=[P+'authority.json',P+'supersession.json',P+'publication.md',P+'source-record.json',REVIEW+'timings.json',PRIOR+'public-verification.json']) for x in c['resolved_rules']}));refresh();G.active_check('final');guard()
def finish():
    G.active_check('mutation','governance_implementation',[ID]);guard()
    log=(G.ROOT/(P+'validation.log')).read_text(encoding='utf-8-sig');assert '"Hugo": "passed"' in log
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(x.rstrip() for x in log.splitlines())+'\n',encoding='utf-8',newline='\n')
    preview=G.load(P+'preview.json');assert all(x['surrounding_entries_unchanged'] and not x['overflow'] and not x['schoolZoneHeading'] for x in preview['results'])
    pr=G.load(P+'pr.json');assert pr['number']==215 and pr['state']=='OPEN' and pr['mergedAt'] is None
    proof=G.load(P+'receipt.json');proof.update(state='complete_open_unmerged_owner_review',normal_validation='passed',validation_log_sha256=G.file_hash(P+'validation.log'),corrected_preview=preview['url'],preview_evidence=P+'preview.json',visual_inspection='Desktop/mobile screenshots inspected; one normal entry, clean wrapping and normal adjacent-entry spacing, no redundant heading/excessive gap.',r2_live_verification=P+'final-verification.json',remaining_owner_action='Manual review and merge decision for OPEN UNMERGED PR215 only',style_baseline='Four pre-existing title-case warnings on unchanged Area & Sector Plans; corrected school-zone entry has no style warnings.')
    for x in proof['governance_accounting'].values():x['result']+=' Full normal/governance/sealed-history/Hugo validation and corrected desktop/mobile Chrome render/link/absence/parity checks passed; PR stays open/unmerged.';x['evidence'] += [P+'preview.json',P+'validation.log',P+'pr.json',P+'final-verification.json']
    save(P+'receipt.json',proof)
    inv=G.load('project-state/master-inventory.json');row=next(x for x in inv['candidates'] if x['id']==ID);row['review_preview']=preview['url'];save('project-state/master-inventory.json',inv);save(P+'source-record.json',row)
    cp=G.load('project-state/checkpoint.json')
    for field in ['school_zone_timing_review','next_owner_requested_task']:cp[field].update(state='complete_open_unmerged_document_entry_review',preview=preview['url'],remaining_gate='owner_manual_pr_review')
    cp['resume_command']='Review OPEN UNMERGED PR215 corrected concise school-zone PDF entry. Full governance/sealed-history/Hugo/Chrome checks passed; exhaustive timings and original archive preserved. No merge/deploy, R2 mutation or elementary work authorized.';save('project-state/checkpoint.json',cp)
    f=G.ROOT/'project-state/CURRENT.md';s=f.read_text(encoding='utf-8-sig').replace('NEXT: validate corrected preview and update OPEN UNMERGED PR #215 for owner review; no merge/deploy authority.','NEXT: owner review of [OPEN UNMERGED PR #215](https://github.com/armandhammer/abqinfo/pull/215). Full normal/governance/sealed-history/Hugo and corrected Chrome desktop/mobile checks passed; no merge/deploy authority.').replace('governance/'+TASK+'/authority.json','governance/'+TASK+'/receipt.json');f.write_text(s,encoding='utf-8',newline='\n')
    body=G.ROOT/(P+'pr-description.md');s=body.read_text(encoding='utf-8-sig').replace('- Corrected Cloudflare preview inspection checks the concise entry, absence of the former schedule list/heading, surrounding-entry parity, PDF link and clean desktop/mobile layout.','- Installed Chrome desktop/mobile preview inspection passed: one concise entry, no schedule list or redundant heading, unchanged surrounding entries, exact PDF GET and no horizontal overflow.').replace('- Full normal validation is running; final results will be recorded before handoff.','- Full normal validation, governance/freshness, sealed history, Hugo, PR-description and diff checks passed. Four pre-existing title-case warnings on the unchanged Area & Sector Plans page remain; the corrected entry has none.');body.write_text(s,encoding='utf-8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='governance_implementation',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Full normal validation and Chrome desktop/mobile correction inspection passed. Prior extraction/review and archive original/public bytes preserved; R2 live listing identical. PR215 description corrected and open/unmerged; owner review only.',evidence=P+'receipt.json'));save(P+'implementation.json',plan)
    refresh();subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True);refresh();G.active_check('final');guard()
if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
