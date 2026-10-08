"""Exact one-record BRT report version/finality review and bounded correction."""
import copy, hashlib, json, subprocess, sys
import TaskGovernance as G
import Trails1993CanonicalReconciliation as Shared

TASK='brt-prize-version-resolution-2026-10-07'
BASE='86dc4adcd30401d4077f6e7f0190edb3d7910a40'
P='project-state/governance/'+TASK+'/'
ID='src-e80e0b49a4723c9a'
PAGE='content/transportation/transit/abq-ride.md'
SHA='49fbec4922fdb0c8963f7ab421a6f4b9fe6269197a907cbec652ef4290c478a6'
def save(path,value):Shared.save(path,value)
def refresh():
    Shared.TASK=TASK;Shared.BASE=BASE;Shared.P=P;Shared.ID=ID
    Shared.refresh()
def event(operation,summary,evidence):
    Shared.P=P;Shared.ID=ID;Shared.event(operation,summary,evidence)
def bind(path,gid,requirement):
    Shared.TASK=TASK;Shared.P=P;Shared.ID=ID;Shared.bind(path,gid,requirement)
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    names=['population.json','population-v2.json','authority.json','baseline-record.json','starting-state.json','implementation.json','supersession.json','historical-evidence.json','retrievals.json','comparison.json','comparison.txt','research-findings.json','quality-decision.json','governance-reconciliation.json','record-updates.json','queue.json','accounting.json','receipt.json','progress.json','rendered-check.json','integration-intent.json','remote-final.json','summary.md','pr-description.md','pr.json','preview-verification.json','preserved.pdf','city.pdf','preserved.txt','city.txt','desktop.png','mobile.png']
    paths=[P+n for n in names]+[P+f'contract-v{i}.json' for i in range(1,51)]+[P+f'response-{i:03d}.bin.gz' for i in range(1,101)]+[P+f'visual-{i:03d}.png' for i in range(1,101)]+[P+f'validation-attempt-{i}.log' for i in range(1,6)]
    paths+=['scripts/project/BrtPrizeVersionResolution.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md','project-state/discovery/retained-source-audit-queue.json',PAGE]
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=[PAGE],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','content_implementation','content_removal','visitor_visible_change'],artifact_paths=paths))
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID);G.write_once(P+'baseline-record.json',row)
    qp=G.load('project-state/ordinary-queue-current.json')['artifact'];q=G.load(qp)
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,remote_main=BASE,remote_planning_snapshot=BASE,source_queue=qp,queue_counts={k:q[k] for k in ['approved_count','pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count']},r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),page_sha256=G.file_hash(PAGE)))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    save(P+'progress.json',dict(stage='exact_record_frozen_initial_contract_saved',inventory_mutation=False))
def bootstrap():
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals={}))
    refresh();active=G.load(G.ACTIVE_TASK);active.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,active);G.active_check('mutation','governance_implementation',[ID])
    save(P+'authority.json',dict(artifact_type='owner_authorization',authority='Explicit current user instruction',candidate_ids=[ID],instruction='Resolve exactly src-e80e0b49a4723c9a, The Scale of the Prize: Community Benefits of Bus Rapid Transit. Freeze exact record, resolve complete registry and immutable contracts; freshness-check before substantive work or mutation. Existing evidence first; exact preserved42-page and City41-page bytes required. Align every page and compare all substantive text/tables/graphics/dates/title/status/header/footer/ending matter, distinguish PDF metadata/container differences and explain extra page. Research authoritative City/project/archived City/directory/first-party delivery or final citation; no filename/use/branding inference of finality. Independently apply current quality/currentness after provenance analysis. Conclusive final provenance permits canonical reconciliation/hold release and unchanged existing R2 retention. If finality is not established, remove unsupported Final Report wording through the smallest accurate owner-review content PR; do not merge. If not publication-worthy or superseded, apply resolved governance and preserve originals. This instruction authorizes exact evidence-driven governance reconciliation/supersession of stale record holds and unsupported finality representations, preserving unrelated decisions and all historical evidence. No destructive R2, overwrite with City version, silent version replacement, unrelated population or unauthorized upload. Visitor-visible changes require unmerged owner-review PR. Only if conclusive with no visible change, clean background integration/main-planning synchronization is authorized. Full normal/governance/sealed-history/Hugo/rendered/CURRENT/diff validation required.'))
    bind(P+'authority.json','owner-'+TASK,'Exact one-record complete version/provenance/quality review. Correct unsupported finality if needed only in an unmerged owner-review content PR. Explicit evidence-backed record-scoped replacements may reconcile prior stale holds. No destructive R2, upload, version overwrite, unrelated population or content merge.')
    bind(P+'supersession.json','authorization-'+TASK+'-supersession','Only the explicit evidence-backed record-scoped replacements recorded in this task are authorized; preserve all unrelated governance and original historical artifacts.')
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json');assert lifecycle['stages'][-1]['id']=='trails-1993-canonical-reconciliation-2026-10-07';lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/BrtPrizeVersionResolution.py'],exact_delta_guard=dict(module='BrtPrizeVersionResolution',function='guard')));save('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf-8-sig');i=s.index('Set-StrictMode');s=s[:i]+'& python "$PSScriptRoot/BrtPrizeVersionResolution.py" guard\nif ($LASTEXITCODE -ne 0) { throw "BRT prize version resolution regression failed" }\n\n'+s[i:];runner.write_text(s,encoding='utf-8',newline='\n')
    refresh();G.active_check('review','document_review',[ID])
def historical():
    refresh();G.active_check('review','document_review',[ID])
    paths=['project-state/near-complete-review-decisions-2026-08-20.json','project-state/near-complete-review-public-validation-2026-08-20.json']+['project-state/discovery/background-followup-2026-09-26/'+n for n in ['decisions.json','retrievals.json','pdf-inspection.json','next-ordinary-queue.json']]
    evidence={}
    for p in paths:
        raw=(G.ROOT/p).read_bytes();old=subprocess.check_output(['git','show',BASE+':'+p],cwd=G.ROOT);assert raw.replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n');evidence[p]=G.file_hash(p)
    row=G.load(P+'baseline-record.json');raw=(G.ROOT/row['local_path']).read_bytes();assert len(raw)==2766304 and hashlib.sha256(raw).hexdigest()==SHA
    city=next(r for r in G.load(paths[3])['retrievals'] if r.get('id')==ID and r.get('page_count')==41) if 'retrievals' in G.load(paths[3]) else None
    save(P+'historical-evidence.json',dict(artifact_type='preserved_version_history_verification',artifact_sha256=evidence,local_preserved=dict(path=row['local_path'],size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),old_assertion='August20 called the supplied copy final while acknowledging unreconciled exact final-file origin; September26 deferred pending complete version comparison. Neither filename nor prior status establishes finality.',preserved_history_unchanged=True))
    (G.ROOT/(P+'preserved.pdf')).write_bytes(raw)
    event('document_review','Existing exact original and historical provenance/finality holds verified intact; no previous finality assertion adopted as proof.',P+'historical-evidence.json')
def fetch(url,label,output=None):
    import urllib.request,gzip
    from datetime import datetime,timezone
    path=P+'retrievals.json';r=G.load(path) if (G.ROOT/path).exists() else dict(records=[])
    n=len(r['records'])+1;record=dict(label=label,requested_url=url,retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 ABQInfo source verification','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=60) as response:
            raw=response.read();record.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),response_artifact=P+f'response-{n:03d}.bin.gz')
            (G.ROOT/record['response_artifact']).write_bytes(gzip.compress(raw,mtime=0))
            if output:(G.ROOT/(P+output)).write_bytes(raw);record['original_path']=P+output
    except Exception as error:record['error']=str(error)
    r['records'].append(record);save(path,r);print(json.dumps({k:v for k,v in record.items() if k!='response_artifact'}));return record
def obtain():
    refresh();G.active_check('review','document_review',[ID])
    row=G.load(P+'baseline-record.json')
    pub=fetch(row['r2_url'],'fresh_existing_public_42_page_object');assert pub['size_bytes']==2766304 and pub['sha256']==SHA
    city=fetch('https://www.cabq.gov/economicdevelopment/documents/f-scale-of-the-prize.pdf','current_city_41_page_original','city.pdf');assert city['size_bytes']==2724654 and city['sha256']=='397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995'
    fetch(row['source_url'],'current_city_landing_page')
    event('document_review','Fresh full public preserved GET and current City-linked original obtained and hashed, matching durable 42/41-page identities.',P+'retrievals.json')
def compare():
    import pymupdf as fitz,difflib,re
    from PIL import Image,ImageDraw
    refresh();G.active_check('review','document_review',[ID])
    docs={n:fitz.open(G.ROOT/(P+n+'.pdf')) for n in ['preserved','city']}
    def body(page):return re.sub(r'^(?:DRAFT: )?The Scale of the Prize\s+\d+\s+','',page.get_text()).strip()
    def words(text):return re.findall(r'\S+',text)
    def diff(a,b):
        aa=words(a);bb=words(b);return [dict(kind=k,preserved=' '.join(aa[i:j]),city=' '.join(bb[m:n])) for k,i,j,m,n in difflib.SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes() if k!='equal']
    def images(page):
        return [dict(rect=list(info['bbox']),width=info['width'],height=info['height'],pixel_digest=info['digest'].hex(),colorspace=info['colorspace']) for info in page.get_image_info(hashes=True)]
    def drawings(page):
        return hashlib.sha256(str(page.get_drawings()).encode()).hexdigest()
    rows=[];global_images={};fonts={};report=[]
    for name,d in docs.items():
        text='\n\f\n'.join(p.get_text() for p in d);(G.ROOT/(P+name+'.txt')).write_text(text,encoding='utf-8')
        global_images[name]=[dict(page=i+1,images=images(p)) for i,p in enumerate(d) if images(p)]
        fonts[name]=sorted({str(f[1:]) for p in d for f in p.get_fonts(full=True)})
    for h in range(1,43):
        c=h if h<=5 else None if h==6 else h-1
        hp=docs['preserved'][h-1];cp=docs['city'][c-1] if c else None
        row=dict(preserved_pdf_page=h,city_pdf_page=c,preserved_printed_page=h-2 if h>=3 else None,city_printed_page=c-2 if c and c>=3 else None,preserved_size=list(hp.rect),city_size=list(cp.rect) if cp else None,preserved_words=len(words(hp.get_text())),city_words=len(words(cp.get_text())) if cp else None,
            full_text_delta=diff(hp.get_text(),cp.get_text()) if cp else [dict(kind='only_preserved',preserved=hp.get_text())],body_text_delta=diff(body(hp),body(cp)) if cp else [],preserved_images=images(hp),city_images=images(cp) if cp else [],preserved_drawings_digest=drawings(hp),city_drawings_digest=drawings(cp) if cp else None)
        pix=hp.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False);left=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        right=None
        if cp:
            pix=cp.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False);right=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        canvas=Image.new('RGB',(left.width*2+20,left.height+34),'white');canvas.paste(left,(0,34))
        if right:canvas.paste(right,(left.width+20,34))
        ImageDraw.Draw(canvas).text((10,8),f'PRESERVED PDF {h}   |   CITY PDF {c if c else "NO CORRESPONDING PAGE"}',fill='black')
        path=P+f'visual-{h:03d}.png';canvas.save(G.ROOT/path);row['paired_visual']=path;rows.append(row)
        report.append(f'\nPRESERVED PDF {h} / CITY PDF {c}\n'+json.dumps(row['body_text_delta'],ensure_ascii=False,indent=2))
    report.insert(0,'WHOLE BODY TOKEN DELTAS (headers/page numbers excluded; preserved to City)\n'+json.dumps(diff('\n'.join(body(p) for p in docs['preserved'][2:]),'\n'.join(body(p) for p in docs['city'][2:])),ensure_ascii=False,indent=2))
    (G.ROOT/(P+'comparison.txt')).write_text('\n'.join(report),encoding='utf-8')
    save(P+'comparison.json',dict(artifact_type='complete_document_version_comparison',exact_originals={n:dict(path=P+n+'.pdf',size_bytes=(G.ROOT/(P+n+'.pdf')).stat().st_size,sha256=hashlib.sha256((G.ROOT/(P+n+'.pdf')).read_bytes()).hexdigest(),pages=len(d),metadata=d.metadata,fonts=fonts[n]) for n,d in docs.items()},alignment=rows,whole_body_delta=diff('\n'.join(body(p) for p in docs['preserved'][2:]),'\n'.join(body(p) for p in docs['city'][2:])),all_raster_images=global_images,visual_inspection_completed=False))
    event('document_review','All 83 pages extracted/measured; complete 42-row alignment and side-by-side rendering saved, with exhaustive body token edits, header/status differences and decoded image/vector inventories.',P+'comparison.json')
def inspection_checkpoint():
    """Persist completed visual work without pre-empting final provenance research."""
    refresh();G.active_check('review','document_review',[ID])
    d=G.load(P+'comparison.json')
    assert len(d['alignment'])==42
    assert all([x['pixel_digest'] for x in r['preserved_images']]==[x['pixel_digest'] for x in r['city_images']] for r in d['alignment'])
    d['visual_inspection_completed']=True
    d['visual_review']=dict(paired_images_inspected=[r['paired_visual'] for r in d['alignment']],actual_pages_inspected=83,extra_page='Preserved PDF page6, printed page4, has only running report title and page number. It is blank report body between Executive Summary and Section I; not an appendix or additional substantive ending page.',alignment='Preserved1-5 = City1-5; preserved6 has no City counterpart; preserved7-42 = City6-41. Reflow moves paragraphs and table rows across adjacent corresponding pages, all tracked by whole-body and per-page deltas.',status='Preserved cover/body have no final marking and no DRAFT marking. City cover says DRAFT NOT FOR RELEASE and alternating running headers include DRAFT:. Neither cover states a publication date.',graphics='Every decoded raster image matches its aligned counterpart exactly: maps, image-based tables, source symbols and legends. Vector tables retain the same numerical data; the station classification table changes 15th Street to16th Street. City Table I.9 abbreviates its first-column heading to BRT Line, retaining the opening-year/rating data in rows. City printed23 has visible revision bars absent from preserved24.',ending='Both end with the same recommendations, no approval/signature/final-delivery or extra appendix. Final paragraph changes possibly to potentially for displacement risk.',layout='Cover position/case, body spacing, line/table wrapping, split table rows, table placements, font resource subsets, contents references and footer page numbers differ; blank-page removal shifts Section I onward by one printed page.',dates='Visible source dates, access dates, forecast horizons and report-body years remain the same. PDF metadata differs: preserved Word2016 export March3 2016, City Word2010 export March10 2016. Export timestamps do not independently establish delivery, issue date, finality or authoritative version succession.',comparison_scope='Full original bytes; all83 pages visually inspected using42 paired renders; exhaustive text edits retained separately, including paragraph/table moves and non-substantive punctuation/wrapping edits. No inference of finality from filename, metadata, commissioning or lack of draft watermark.')
    save(P+'comparison.json',d)
    save(P+'research-findings.json',dict(artifact_type='incomplete_provenance_research_checkpoint',candidate_ids=[ID],comparison_completed=True,finality_established=False,finding='Document comparison cannot demonstrate the preserved42-page copy is final. It contains unresolved editorial questions and distinct text; its export predates the City marked draft. Exact42-page authoritative delivery/final citation still requires the requested first-party/archive/directory research.',completed_first_party_evidence=['Fresh complete City-linked41-page PDF and landing page recorded in retrievals.json; both match September26 retained identities.'],remaining=['Authoritative City/project publication history and directories','Archived City captures and final-delivery/final-report citations','Independent resolved-governance publication-quality/currentness decision','Explicit governance reconciliation and bounded inventory/content correction','Full validation and unmerged owner-review PR/preview if unsupported label remains'],interruption='Automatic approval review authentication failed after account change; web tool also returned401 token_revoked. No bypass of approval review attempted. User asked to restore sign-in.'))
    event('document_review','Complete83-page direct visual inspection saved, including every aligned graphic/table/status/end page. Comparison does not establish finality; authoritative version-delivery research remains incomplete.',P+'comparison.json')
    save(P+'progress.json',dict(stage='full_version_comparison_saved_authoritative_trace_pending',inventory_mutation=False,visitor_visible_mutation=False,r2_mutation=False,completed=['Exact one-record population/complete governance/immutable contracts','Historical evidence intact','Fresh exact full public42 and City41 GET identities','All83 pages extracted/aligned/rendered/visually inspected'],remaining=G.load(P+'research-findings.json')['remaining'],execution_issue='Account sign-in must be restored for automatic approval review and web authentication.'))
    refresh();guard()

def interruption_checkpoint():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    path=G.ROOT/'project-state/CURRENT.md';old=path.read_text(encoding='utf-8-sig');links=old[old.index('[Owner correction]'):]
    path.write_text('# Current project state\n\nActive exact one-record BRT report version review: src-e80e0b49a4723c9a, The Scale of the Prize. Baseline main/planning 86dc4adcd30401d4077f6e7f0190edb3d7910a40. Immutable population and complete52-rule contracts saved. Existing evidence intact; fresh public42-page and City41-page GETs match durable size/SHA. 83-page comparison and visual inspection saved. Extra page is blank-body preserved PDF6/printed4; substantive editorial/status/layout differences exist. Finality is not established by comparison. City/project/archive delivery research remains incomplete.\n\nAutomatic approval review and web authentication failed after account change (token refresh failure /401 token_revoked). Restore app sign-in before remaining authenticated research/PR work. No inventory/content/R2/ref mutation; task evidence uncommitted. Queue unchanged:0 approved/335 pending,321 gated/14 source-structural blocked; no publication population or owner decision. Task/governance/CURRENT tests and64-stage/810-file sealed history pass. Full project/Hugo/rendered validation and final disposition remain pending. Prior decisions unchanged.\n\n[Progress](governance/brt-prize-version-resolution-2026-10-07/progress.json) · [Comparison](governance/brt-prize-version-resolution-2026-10-07/comparison.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links,encoding='utf-8',newline='\n')
    (G.ROOT/(P+'summary.md')).write_text('BRT prize report version review: incomplete provenance-trace checkpoint\n\nExact record: '+ID+'; baseline '+BASE+'. No inventory, public-content, R2 or ref mutation.\n\nPreserved copy:42 pages,2766304 bytes,SHA256 '+SHA+'. City-linked draft:41 pages,2724654 bytes,SHA256397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995. Full originals and fresh fullGET receipts are retained locally; PDF files are ignored by the general repository rule and must be explicitly retained/staged if a later reviewed commit is prepared.\n\nAll83 pages were visually inspected. Extra page is PDF6/printed4, blank except running title/footer. First5 pages align one-to-one; preserved7-42 align City6-41, with paragraphs/table rows reflowing across adjacent pages. Every decoded raster image matches exactly. Numeric table data match, but station table15th Street becomes16th Street and TableI.9 first-column heading loses opening-year/rating words; row data remain. Status cover/running header markings differ. City includes revision bars on printed23. Exhaustive raw text/body edits, metadata/font inventories, positions and42 paired renders are saved in comparison.json/comparison.txt.\n\nMeaningful wording changes include NobHill participation, unfinished executive-summary editorial questions, updated-zoning dependency, regional planning wording, Central Avenue/Street, adopted/recent MRA, IDO activity centers/downtown concentration, transit dependability/speed, lower/greater speed, floor-area-ratio explanatory language and possible/potential displacement. All forecasts, numerical projections, mapped graphics and visible source/access dates remain equivalent. Some token edits are paragraph/table extraction movement or hyphenation, distinguished by full visual inspection.\n\nNeither cover/ending establishes final delivery or approval. Preserved unmarked version retains editorial questions; its Word2016 PDF export is March3 2016 versus City marked-draft Word2010 March10 2016. Metadata is export evidence, not authoritative issue/finality evidence. A final42-page City delivery/citation has not been established. Requested first-party/directory/archive search is incomplete due authentication failure. No quality/currentness disposition or governance supersession has been applied.\n\nGovernance regression, exact task guard, CURRENT regression and64 contiguous stages/810 sealed historical files pass; git diff --check passes for tracked changes. Full project validation and Hugo/rendered work remain pending. Hugo default installed path was unavailable inside the restricted execution surface. No PR/preview/commit created. Queue remains0 approved/335 pending,321 gated/14 source-structural blocked. Resume from progress.json after app authentication is restored.\n',encoding='utf-8',newline='\n')
    progress=G.load(P+'progress.json');progress['partial_validation']=dict(task_guard='passed',governance_regression='passed',sealed_history='passed:64 contiguous stages,810 historical evidence files unchanged',current_separator='passed',git_diff_check='passed tracked changes',full_suite='pending',hugo='pending:configured executable unavailable in restricted surface',rendered='pending');save(P+'progress.json',progress)
    refresh();guard()

def guard():
    from WorkflowStageLifecycle import StageSnapshot,git,canonical_bytes
    stage=StageSnapshot(TASK);state=stage.load_json(P+'starting-state.json');pop_path=next(P+n for n in ['population-v2.json','population.json'] if (G.ROOT/(P+n)).exists());pop=stage.load_json(pop_path)
    assert pop['candidate_ids']==[ID] and pop['pages']==[PAGE]
    for path,key in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==state[key]
    before={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']};after={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert before.keys()==after.keys() and {i for i in before if before[i]!=after[i]}<={ID}
    # During research no disposition or visible correction has yet been applied.
    # A completed decision adds a separately frozen exact mutation request.
    requests=G.ROOT/(P+'record-updates.json')
    if requests.exists():
        changes=stage.load_json(P+'record-updates.json')['approved_updates'][0]['changes'];expected=copy.deepcopy(before[ID]);expected.update(changes);expected['updated_at']=after[ID]['updated_at'];expected['description_word_count']=len(expected['description'].split());assert after[ID]==expected
        assert after[ID]['status']=='pending review' and after[ID]['review_reason']=='source_provenance_unresolved' and after[ID]['date'] is None and after[ID]['direct_file_url'] is None
        for k in ['r2_url','r2_key','r2_etag','r2_last_modified','size_bytes','checksum_sha256','local_path','implementation_location','implementation_locations']:assert after[ID][k]==before[ID][k]
        assert after[ID]['processing_notes'][:len(before[ID]['processing_notes'])]==before[ID]['processing_notes']
        from PublicationQuality import require_publication_quality
        require_publication_quality(after[ID])
        v=stage.load_json(P+'quality-decision.json')['visible_change'];source=git('show',BASE+':'+PAGE).decode('utf-8').replace('\r\n','\n');assert source.count(v['old_entry'])==1 and stage.read_text(PAGE)==source.replace(v['old_entry'],v['new_entry'])
        assert stage.read_text(PAGE).count(after[ID]['r2_url'])==source.count(after[ID]['r2_url'])==1
        assert '(Final Report)' not in v['new_entry'] and 'final status are unverified' in v['new_entry']
        visible=set(git('diff',BASE,stage.end or 'HEAD','--name-only','--','content','layouts','assets','static','hugo.toml').decode().splitlines())
        if not stage.end:visible |= set(git('diff','HEAD','--name-only','--','content','layouts','assets','static','hugo.toml').decode().splitlines())
        assert visible<={PAGE},visible
        if (G.ROOT/(P+'queue.json')).exists():
            q=stage.load_json(P+'queue.json');assert (q['approved_count'],q['pending_review_count'],q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(0,335,321,14)
            assert ID in q['pending_ids'] and ID in q['source_or_structural_blocked_pending_ids']
    else:
        assert after==before
        stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for path in stage.load_json(P+'historical-evidence.json')['artifact_sha256']:
        assert canonical_bytes(stage.read_bytes(path))==canonical_bytes(git('show',BASE+':'+path))
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    d=stage.load_json(P+'comparison.json');assert d['exact_originals']['preserved']['sha256']==SHA and d['exact_originals']['city']['sha256']=='397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995'
    assert len(d['alignment'])==42 and [r['city_pdf_page'] for r in d['alignment']]==[1,2,3,4,5,None]+list(range(6,42))
    for name,original in d['exact_originals'].items():
        raw=stage.read_bytes(original['path']);assert len(raw)==original['size_bytes'] and hashlib.sha256(raw).hexdigest()==original['sha256']
    print('Exact BRT report population, byte identities, alignment and historical/R2 preservation passed')

def resume():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    pop=copy.deepcopy(G.load(P+'population.json'));pop['artifact_paths'] += [P+'authority-resumption.json']
    G.write_once(P+'population-v2.json',pop)
    G.write_once(P+'authority-resumption.json',dict(artifact_type='owner_authorization',candidate_ids=[ID],authority='Repeated current user task instruction after authentication recovery',instruction='Resume same exact one-record task under immutable population/contracts and complete registry resolution. Finish full version/finality and authoritative-source research and current publication quality/currentness. If unsupported Final Report wording requires correction, create normal unmerged owner-review content PR, create and verify nonproduction preview, and synchronize chatgpt/planning-snapshot to the reviewed PR head. Never merge content PR. No destructive R2, overwriting42 with41, unrelated population or unsupported finality. Full validation and exact ref/count receipts required.'))
    bind(P+'authority-resumption.json','owner-'+TASK+'-resumption','Finish this same exact-record version/finality correction. A visible correction requires an unmerged owner-review PR with verified nonproduction preview and planning-snapshot synchronized to its reviewed head; main stays unchanged. No R2 mutation or unrelated population.')
    refresh();G.active_check('review','document_review',[ID])
    event('governance_implementation','Resumed same exact population after authentication recovery; explicit current authority includes verified unmerged content PR and planning-snapshot synchronization.',P+'authority-resumption.json')

def research():
    refresh();G.active_check('review','document_review',[ID])
    urls=[
      ('https://www.cabq.gov/economicdevelopment/documents/f-scale-of-the-prize.pdf/view','City exact file listing'),
      ('https://www.cabq.gov/economicdevelopment/documents','City economic development document directory'),
      ('https://www.cabq.gov/search?SearchableText=scale%20of%20the%20prize','City site publication search'),
      ('https://www.cabq.gov/transit/services/art','Current official ART project resources'),
      ('https://www.cnt.org/publications','Commissioned author publication directory'),
      ('https://www.cnt.org/search?search_api_fulltext=Albuquerque','Commissioned author Albuquerque search'),
      ('https://web.archive.org/cdx/search/cdx?url=*.cabq.gov/*scale*prize*&output=json&filter=statuscode:200&collapse=urlkey','Archive City title/file family CDX index'),
      ('https://archive.org/wayback/available?url=www.cabq.gov/economicdevelopment/the-scale-of-the-prize-community-benefits-of-transit-oriented-development&timestamp=20161231','Archived City page availability2016'),
      ('https://archive.org/wayback/available?url=www.cabq.gov/economicdevelopment/documents/f-scale-of-the-prize.pdf&timestamp=20161231','Archived City file availability2016'),
      ('https://web.archive.org/cdx/search/cdx?url=abqbrt.org/*&output=json&filter=urlkey:.*(scale|prize|cnt|report|resource).*&filter=statuscode:200&collapse=urlkey','Archive original ART project report/resource directory'),
      ('https://documents.cabq.gov/planning/environmental-planning-commission/December%2014_2023/Agenda%203_PR-2018-001843_RZ-2023-00040_Citywide%20Amendments.pdf','City-hosted2023 EPC packet citing42-page report'),
      ('https://web.archive.org/cdx/search/cdx?url=cnt.org/*scale*prize*&output=json&filter=statuscode:200&collapse=urlkey','Archive commissioned author report family index')]
    for url,label in urls:fetch(url,label)
    event('document_review','Bounded exact-report first-party publication/directory and archive queries preserved as full response bytes or explicit errors; no new inventory population or publication begun.',P+'retrievals.json')
    refresh()

def research_followup():
    import gzip,re,html
    refresh();G.active_check('review','document_review',[ID])
    for url,label in [
      ('https://web.archive.org/web/20170109075907id_/http://www.cabq.gov/economicdevelopment/the-scale-of-the-prize-community-benefits-of-transit-oriented-development','Archived City landing original20170109'),
      ('https://web.archive.org/web/20170201000114id_/http://www.cabq.gov/economicdevelopment/documents/f-scale-of-the-prize.pdf','Archived City report original20170201'),
      ('https://cnt.org/publications','Commissioned author publication directory canonical domain'),
      ('https://cnt.org/search?search_api_fulltext=Albuquerque','Commissioned author Albuquerque search canonical domain'),
      ('https://www.cabq.gov/transit/services/art-information','City ART information resources'),
      ('https://web.archive.org/cdx/search/cdx?url=www.cabq.gov/economicdevelopment/documents/*&output=json&filter=urlkey:.*(scale|prize|cnt).*&filter=statuscode:200&collapse=urlkey','Exact archived City economic-development document family index'),
      ('https://www.cabq.gov/economicdevelopment/documents/@@search?SearchableText=scale','City exact document-folder report search'),
      ('https://web.archive.org/cdx/search/cdx?url=abqbrt.blob.core.windows.net/resources/*&output=json&filter=urlkey:.*(scale|prize|cnt).*&filter=statuscode:200&collapse=urlkey','Archived official ART project resource-delivery directory')]:fetch(url,label)
    review=[]
    for r in G.load(P+'retrievals.json')['records']:
        if 'response_artifact' not in r:continue
        raw=gzip.decompress((G.ROOT/r['response_artifact']).read_bytes())
        if raw.startswith(b'%PDF'):
            import pymupdf as fitz
            d=fitz.open(stream=raw,filetype='pdf');value='\n'.join(p.get_text() for p in d)
            excerpts=[value[max(0,m.start()-300):m.end()+650] for m in re.finditer('Scale of the Prize|42.page|Center for Neighborhood Technology',value,re.I)]
            review.append(dict(label=r['label'],pages=len(d),sha256=r['sha256'],matched_preserved=r['sha256']==SHA,matched_city=r['sha256']=='397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995',excerpts=excerpts[:12]))
        elif 'html' in str(r.get('content_type')):
            value=raw.decode('utf-8',errors='replace');main=re.search(r'<(?:article|main)[^>]*>(.*?)</(?:article|main)>',value,re.S)
            text=html.unescape(re.sub('<[^>]+>',' ',main.group(1) if main else value));text=re.sub(r'\s+',' ',text)
            excerpts=[text[max(0,m.start()-180):m.end()+500] for m in re.finditer('Scale of the Prize|final report|Albuquerque|no results|No items',text,re.I)]
            links=[html.unescape(u) for u in re.findall(r'href=[\"\x27]([^\"\x27]+)',value) if re.search('scale|prize|cnt|art-information',u,re.I)]
            review.append(dict(label=r['label'],url=r['requested_url'],excerpts=excerpts[:15],relevant_links=links))
        else:review.append(dict(label=r['label'],index_or_availability_response=raw.decode('utf-8',errors='replace')[:10000]))
    findings=G.load(P+'research-findings.json');findings['retrieved_response_review']=review;save(P+'research-findings.json',findings)
    event('document_review','Reviewed retrieved City directory/search/page material and available archive replays/indices. Exact original digests distinguish a City-hosted variant from unsupported final filename assertions.',P+'research-findings.json')
    refresh()

def author_directory():
    import gzip,re,html
    refresh();G.active_check('review','document_review',[ID]);results=[]
    urls=[('https://cnt.org/publications?page='+str(n),'Author publication library page'+str(n+1)) for n in range(1,14)]
    urls += [('https://cnt.org/search/content/Scale%20of%20the%20Prize','Author exact title search'),('https://cnt.org/search/content/Albuquerque','Author actual Albuquerque search'),('https://www.cabq.gov/economicdevelopment/documents/f-scale-of-the-prize.pdf/@@download/file/F%20Scale%20of%20the%20Prize.pdf','City file-listing explicit download delivery')]
    for url,label in urls:
        r=fetch(url,label)
        if r.get('response_artifact'):
            raw=gzip.decompress((G.ROOT/r['response_artifact']).read_bytes());value=html.unescape(re.sub('<[^>]*>',' ',raw.decode('utf-8',errors='replace')));value=re.sub(r'\s+',' ',value)
            results.append(dict(label=label,url=url,sha256=r['sha256'],title_match='scale of the prize' in value.lower(),albuquerque_match='albuquerque' in value.lower(),excerpts=[value[max(0,m.start()-150):m.end()+450] for m in re.finditer('scale of the prize|albuquerque|no results|no search results',value,re.I)][:8],exact_preserved=r['sha256']==SHA,exact_city=r['sha256']=='397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995'))
    f=G.load(P+'research-findings.json');f['complete_author_library_and_search']=results;save(P+'research-findings.json',f)
    event('document_review','All14 available author publication-library pages and actual title/Albuquerque searches checked; explicit City file-listing delivery hash checked. No finality inference from later citations.',P+'research-findings.json');refresh()

def finish_research():
    import gzip,re
    from bs4 import BeautifulSoup
    refresh();G.active_check('review','document_review',[ID])
    records=G.load(P+'retrievals.json')['records'];r=next(r for r in records if r['label']=='Author actual Albuquerque search')
    soup=BeautifulSoup(gzip.decompress((G.ROOT/r['response_artifact']).read_bytes()),'html.parser');links=[]
    for a in soup.select('.search-results h3 a'):
        title=a.get_text(' ',strip=True);url=a.get('href','')
        if re.search('transit|central avenue',title,re.I):
            if url.startswith('/'):url='https://cnt.org'+url
            links.append(dict(title=title,url=url));fetch(url,'Author search followup: '+title)
    f=G.load(P+'research-findings.json');f['author_report_reference_followups']=links
    f.update(artifact_type='complete_bounded_report_version_provenance_research',status='complete_bounded_research_no_final_delivery_established',remaining=[],interruption_history=f.pop('interruption',None),finality_established=False,exact_preserved_official_delivery_established=False,
      final_conclusion='Preserved42-page unmarked, draft-like editorial/export variant remains provenance-uncertain. It is not demonstrably a later/final version, nor merely a container-only export of the City41-page draft. The executive-summary editorial questions and textual/table-label revisions establish substantive version differences. Never describe it as a proven final or as a proven officially released42-page draft.',
      authoritative_positive_evidence=['Current City landing links only f-scale-of-the-prize.pdf; current file listing and explicit download yield the same41-page marked draft.','Archived official City page20170109 links the same URL without a final claim; archived City original20170201 is byte-identical to today41-page draft:2724654 bytes, SHA256397930c361fef4255459b20d533e9cc12a198e8a63ad1482afc55a1a08286995.','Complete14-page commissioned-author publication directory and actual exact-title/Albuquerque site searches supplied no42-page authoritative delivery or final-status statement. Relevant author-indexed press references discuss the prospective/being-compiled study; they do not authenticate this42-page delivery.'],
      secondary_citation_review=dict(url='https://documents.cabq.gov/planning/environmental-planning-commission/December%2014_2023/Agenda%203_PR-2018-001843_RZ-2023-00040_Citywide%20Amendments.pdf',finding='Indexed September5 2023 citizen submission mentions a42-page report and quotes a characterization of the CNT study as a draft. The submission is public comment hosted in an EPC packet, not a City/author final-delivery attestation; page count does not authenticate exact bytes. Direct fresh packet retrieval404, so this lead is not treated as verified full original or final proof.'),
      archive_limitations='Successful exact City2017 landing/PDF replays establish actual historical publication. Several broader CDX family/directory queries returned503; original ART report/resource filter query returned empty[]. No claim of exhaustive access to every historical capture or privately delivered City/author file. These limits do not support Final Report language.',
      report_date_conclusion='Neither original states an issue date. Prior2014 canonical date is unsupported and is corrected to undated;2014 refers to cited NAIOP work, while body references2015/2016 and PDF export metadata is March2016. Export date is retained separately in comparison, not converted into an authoritative report publication date.',
      supersession_conclusion='City41-page file is demonstrably official publication of a marked draft, historically unchanged since2017. No authoritative final/adopted/supersession finding for either version; preserve both originals and do not replace archived42 with41.',
      search_queries=['exact title/Albuquerque/author','exact filename','site:cabq.gov exact title/final','site:documents.cabq.gov exact title','site:cnt.org exact title','site:cabq.legistar.com exact title','City site and document-folder searches','Wayback exact City page/PDF availability and replays','CDX City/CNT/ART project/resource family filters','CNT complete publication library and actual site search'])
    save(P+'research-findings.json',f);event('document_review','Authoritative live/listing/download and exact archived2017 City originals establish only the41-page marked draft. No defensible42-page final delivery established by bounded first-party/archive/directory research; limitations explicit.',P+'research-findings.json');refresh()

def quality():
    import re
    refresh();G.active_check('review','quality_assessment',[ID]);d=G.load(P+'comparison.json');f=G.load(P+'research-findings.json');assert d['visual_inspection_completed'] and not f['finality_established']
    scope=dict(assessed_at=Shared.now(),geographic_institutional_scope='Albuquerque Rapid Transit Central Avenue corridor; study attributed to CNT for the City of Albuquerque.',specific_albuquerque_connection='The actual report maps25 proposed Albuquerque stations and Downtown, Urban Neighborhood and Town Center districts, using2015 Bernalillo Assessor parcels and local zoning/ART assumptions.',abqinfo_public_information_value='Substantial historical ART investment rationale, redevelopment assumptions, housing/employment/value forecasts and local zoning/service recommendations permit scrutiny of the original planning case.',general_context_exclusion_test='Eligibility of the substance rests on named Albuquerque station districts, local parcel calculations and City policy recommendations, not commissioning, branding, generic BRT literature or a filename. General national comparisons are supporting analysis within the material local report.',final_scope_decision='passes_both_gates',substantive_rationale='This complete local analysis explains how forecast Central Avenue redevelopment, station accessibility, housing, jobs and zoning were linked to the proposed ART investment. It materially helps readers understand a consequential Albuquerque infrastructure/policy decision; its unproved version/finality must be separately qualified and cannot be approved as official final evidence.')
    q=dict(document_function='Historical prospective economic/development and land-use analysis for the proposed Albuquerque Rapid Transit corridor, with calculations and implementation recommendations.',substantive_content='Local station typologies, assessor values, vacancy/utilization and FAR assumptions; district calculation tables, maps, national comparisons, limitations and forecast findings/recommendations.',durable_public_usefulness='Enables scrutiny of the original ART economic and zoning rationale and comparison of assumptions/forecasts with later outcomes; not a present-day evaluation or promise.',information_density='42 PDF pages including one blank numbered body page, cover and contents; '+str(sum(r['preserved_words'] for r in d['alignment']))+' extractable words; detailed maps, measured/calculated tables and substantive analysis throughout.',unique_information='A complete, distinct42-page unmarked editorial version with the same numerical forecast framework as the official41-page marked draft, including identifiable text/station-label differences. Useful historical version evidence when described accurately; not a new or duplicate entry.',rationale='The full document gives meaningful Albuquerque-specific public infrastructure and land-use information beyond identifying business or repeating administrative material. Its maps, explicit assumptions, detailed calculation tables and recommendations merit a historical report entry. Unfinished editorial notes, uncertain exact official delivery and unproved final status require an explicit public qualifier and continued factual source hold. A passing independent substance/quality assessment does not approve finality, provenance or a new publication lifecycle.',reviewed_document_content=True,visual_inspection_completed=True,page_count=42,extracted_word_count=sum(r['preserved_words'] for r in d['alignment']),standalone_public_value='substantive',publication_form='standalone',series_relationship='standalone',currentness_review_required=True,currentness_review=dict(status='historical_status_uncertain',authoritative_sources=[P+'comparison.json',P+'research-findings.json',P+'retrievals.json'],finding='2016 export-era prospective ART study; official2017 and current City delivery remains a marked draft. No established final publication date/version succession. Historical planning analysis, not current project status, measured realized outcomes or current zoning/service policy.',publication_qualification='Keep under ART Planning and Development History as a preserved42-page copy; explicitly state exact official delivery and final status unverified, distinguishing the City-linked41-page draft.'),version_relationship=dict(official_comparator_pages=41,same_numerical_forecasts=True,all_raster_graphics_identical=True,substantive_editorial_variant=True,supersession_established=False,one_entry_only=True),provenance_gate='unresolved; maintain pending review and source/structural blocker',owner_review_gate='unmerged normal content PR only; no implementation/validated transition or production content merge')
    label='The Scale of the Prize: Community Benefits of Bus Rapid Transit (Preserved Copy)'
    description='Historical analysis of potential development, housing, employment, and zoning around proposed ART stations along Central Avenue. The preserved 42-page copy differs from the City-linked 41-page draft; its exact official delivery and final status are unverified.'
    baseline=G.load(P+'baseline-record.json');old='- ['+baseline['title']+' (Final Report)]('+baseline['r2_url']+')\n\n  '+baseline['description']+' [Official City project page and marked draft]('+baseline['source_url']+')'
    new='- ['+label+']('+baseline['r2_url']+')\n\n  '+description+' [Official City report page and marked draft]('+baseline['source_url']+')'
    source=subprocess.check_output(['git','show',BASE+':'+PAGE],cwd=G.ROOT).decode('utf-8').replace('\r\n','\n');assert source.count(old)==1
    save(P+'quality-decision.json',dict(artifact_type='actual_record_scope_quality_currentness_decision',candidate_id=ID,scope_assessment=scope,quality_assessment=q,decision='passes independent substance and historical-quality gates with explicit version qualifier; provenance hold remains',visible_change=dict(page=PAGE,old_entry=old,new_entry=new,new_label=label,new_description=description,section='ART Planning and Development History'),publication_quality_decision=dict(decision='passes',finding_id=TASK+':historical-qualified-report-quality',assessment=q,evidence=[P+'comparison.json',P+'research-findings.json',P+'quality-decision.json'])))
    event('quality_assessment','Full actual report passes independent scope/substantive historical-quality assessment with explicit uncertain-version qualification; source-finality is unresolved and lifecycle remains pending. No standalone fragment or current-project claim.',P+'quality-decision.json');refresh()

def reconcile():
    refresh();G.active_check('mutation','governance_implementation',[ID]);f=G.load(P+'research-findings.json');q=G.load(P+'quality-decision.json');assert not f['finality_established']
    r=G.load(G.REGISTRY);old_id='decision-near-complete-review-decisions-2026-08-20-55b5f92e';old=next(e for e in r['entries'] if e['governance_id']==old_id);assert old['state']=='active'
    exception=' Explicit owner-authorized exception solely for src-e80e0b49a4723c9a: complete comparison and authoritative live/archive research establish no final42-page delivery. Replace prior provisional final-report assertion/approval only with preserved unmarked editorial variant, exact official delivery/final status unverified. Keep existing42-page original/R2 and one existing historical entry; prepare accurate label/description correction solely in an unmerged owner-review PR. Preserve pending source-provenance hold; a positive substantive historical-quality assessment is independent and does not release it. Preserve every unrelated decision and all original evidence.'
    new_id='decision-'+TASK+'-august-finality-exception';proposal=dict(existing_governance_id=old_id,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=[P+'comparison.json',P+'research-findings.json',P+'quality-decision.json'],proposed_replacement=old['binding_requirement']+exception,consequences='Only this existing record provisional finality representation is corrected; September26 factual source prerequisite remains. No new eligibility/lifecycle approval, no original-byte replacement, unrelated disposition or public merge.',authorization_artifact=P+'authority-resumption.json',authorized=True)
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals={old_id:proposal}))
    save(P+'governance-reconciliation.json',dict(artifact_type='record_scoped_version_and_public_wording_decision',candidate_id=ID,explicit_scoped_replacements={old_id:proposal},finality_established=False,finality_label_supported=False,canonical_source_prerequisite_cleared=False,final_lifecycle_status='pending review',independent_quality='passes as qualified historical analysis; does not prove official42-page delivery',visible_correction='One existing entry only: replace Final Report label with Preserved Copy and qualify42/41 distinction/exact delivery and final status uncertainty.',historical_evidence_unchanged=True,owner_decision='Owner review/merge decision for the correction PR; factual source/finality cannot be established by owner preference.',r2_delta=0))
    new=copy.deepcopy(old);new.update(governance_id=new_id,title=old['title']+' with exact BRT uncertain-finality correction',authority='Explicit repeated current owner exact-record correction instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],supersedes=[old_id],implementation_status='Unmerged bounded historical-entry correction; factual source hold retained')
    new['controlling_artifacts'].append(dict(path=P+'governance-reconciliation.json',sha256=G.file_hash(P+'governance-reconciliation.json'),binding_pointers=['/']))
    new['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in old['settled_decisions']]
    old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    for e in r['entries']:
        for a in e['controlling_artifacts']:
            if a['path']==P+'supersession.json':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    bind(P+'governance-reconciliation.json','decision-'+TASK,'Preserve42-page original and pending factual source hold. Correct unsupported Final Report wording in exactly one existing historical entry via unmerged owner-review PR and verified preview; positive quality is independent of provenance. Keep all unrelated decisions and R2 unchanged.')
    bind(P+'quality-decision.json','quality-'+TASK,'Apply actual-report positive material Albuquerque and substantive historical-quality assessment with explicit unverified version/finality qualifier. No new entry, finality approval, current-outcome claim or source-hold release.')
    b=G.load(P+'baseline-record.json');changes=dict(status='pending review',date=None,direct_file_url=None,description=q['visible_change']['new_description'],provenance_status='Preserved42-page unmarked editorial report variant; exact archived/local/public bytes verified. City official current and archived2017 delivery is a distinct41-page marked draft. Exact official-source42-page delivery and final status remain unverified.',review_reason='source_provenance_unresolved',validation_status='Exact public/local size/SHA passed; complete83-page comparison passed. Independent historical scope/quality passes with version qualification. Official42-page delivery/finality unresolved; accurate visible correction awaiting owner PR review, no validated lifecycle.',scope_assessment=q['scope_assessment'],quality_assessment=q['quality_assessment'],publication_quality_decision=q['publication_quality_decision'],processing_notes=b['processing_notes']+['2026-10-07 '+TASK+': complete83-page version comparison and direct visuals; extra preserved PDF6/printed4 is blank report body. Body text/station label edits, absent/present draft markings, pagination/layout and PDF export metadata differ; all decoded raster images and numerical forecasts match. No proven later/final42-page delivery. City live and archived2017 PDFs exactly match41-page marked draft. Prior final filename/2014 date and provisional finality language do not establish fact; date now undated and exact42-page source/finality remains pending. Owner-authorized scoped replacement corrects only provisional finality representation; all historical source evidence and September26 factual hold preserved. One existing public entry correction is prepared in an unmerged owner-review PR; no R2/version replacement or new population.'])
    save(P+'record-updates.json',dict(approved_updates=[dict(id=ID,changes=changes)]));event('governance_implementation','Explicit exact-record supersession corrects August provisional finality representation; preserves September26 factual prerequisite and every unrelated historical decision. Registers current actual-record quality independently.',P+'governance-reconciliation.json');refresh()

def queue():
    inv=G.load('project-state/master-inventory.json');prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved={r['id'] for r in inv['candidates'] if r['status']=='approved for addition'}
    q.update(artifact_type='brt_version_qualification_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for k in ['gated','source_or_structural_blocked']:
        values=prior[k+'_pending_ids'];q[k+'_pending_ids']=({i:v for i,v in values.items() if i in pending} if isinstance(values,dict) else sorted(i for i in values if i in pending));q[k+'_pending_count']=len(q[k+'_pending_ids'])
    if isinstance(q['source_or_structural_blocked_pending_ids'],dict):q['source_or_structural_blocked_pending_ids'][ID]='Exact42-page official delivery/final status unverified after complete version comparison and bounded first-party/archive research; qualified-wording correction in owner-review PR does not release factual prerequisite.'
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated),brt_prize_resolution=dict(candidate_id=ID,finality_established=False,source_blocker_cleared=False,visible_correction_owner_review=True))
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,335,321,14,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))

def apply():
    refresh();G.active_check('mutation','inventory_disposition',[ID]);subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
    refresh();G.active_check('mutation','content_implementation',[ID]);q=G.load(P+'quality-decision.json');v=q['visible_change'];path=G.ROOT/PAGE;s=path.read_text(encoding='utf-8-sig');assert s.count(v['old_entry'])==1;path.write_text(s.replace(v['old_entry'],v['new_entry']),encoding='utf-8',newline='\n')
    queue();refresh();G.active_check('mutation','inventory_disposition',[ID]);subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True,stdout=subprocess.DEVNULL)
    refresh();G.active_check('mutation','family_review',[ID]);subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    save(P+'accounting.json',dict(candidate_ids=[ID],final_status='pending review',source_blocker_cleared=False,counts=dict(approved=0,pending=335,governance_gated=321,source_structural_blocked=14,actionable=0,owner_source_decisions=0),owner_content_review_required=True,r2_delta=dict(uploads=0,overwrites=0,deletions=0,added_bytes=0),visitor_visible_proposed_delta='One existing historical entry label and description/source-link label; same archive and official landing URLs, no new entry/placement.',production_visible_delta=0))
    event('inventory_disposition','Exactly one pending record reconciled to accurate unknown finality/undated provenance and independent positive historical quality; factual source hold retained and queue regenerated without count change.',P+'accounting.json');event('content_implementation','Prepared exact single-entry factual correction; same public42-page bytes and source landing remain, no substitute41-page object or new placement. Owner-review PR only, not merged.',P+'quality-decision.json')
    save(P+'progress.json',dict(stage='bounded_correction_prepared_validation_pr_preview_pending',remaining=['full validation','rendered inspection','unmerged PR and verified preview','planning synchronization'],inventory_updated=[ID],content_changes=[PAGE],r2_mutation=False))
    current('Correction prepared; full validation/preview/PR pending.');refresh();guard()

def current(state):
    path=G.ROOT/'project-state/CURRENT.md';old=path.read_text(encoding='utf-8-sig');tail=old[old.index('[Owner correction]'):]
    path.write_text('# Current project state\n\nExact BRT report src-e80e0b49a4723c9a reviewed. Complete83-page alignment/direct visual comparison saved: extra preserved PDF6/printed4 blank body; text/status/layout differences, same raster graphics/numerical forecasts. City current and archived2017 originals match41-page marked draft. Preserved42-page official delivery/finality unproved; Final Report unsupported. Historical substantive-quality passes with explicit qualifier; source hold remains pending, not validated. Registered exact exception preserves history/unrelated decisions.\n\nOne existing ABQ RIDE history entry correction: Preserved Copy label and uncertain-finality description; same42-page R2 object/source page. '+state+' Main unchanged; content merge not authorized. Queue0 approved/335 pending (321 gated/14 source-structural blocked), no new population/source owner decision. R2 delta0; production visible delta0.\n\n[Receipt](governance/'+TASK+'/receipt.json) · [Comparison](governance/'+TASK+'/comparison.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+tail,encoding='utf-8',newline='\n')

def receipt():
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);evidence=[P+n for n in ['historical-evidence.json','retrievals.json','comparison.json','research-findings.json','quality-decision.json','governance-reconciliation.json','accounting.json','queue.json']]
    old=G.load(P+'receipt.json') if (G.ROOT/(P+'receipt.json')).exists() else {}
    old.update(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],state='correction_prepared_unmerged_owner_review',finality_established=False,source_blocker_cleared=False,canonical_status='pending review',accounting=G.load(P+'accounting.json'),normal_validation=old.get('normal_validation','pending'),content_merge_authorized=False,evidence_sha256={p:G.file_hash(p) for p in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Exact one existing BRT report only. Complete bytes/83-page aligned visual/text/graphic/table/date/status review and live/historical first-party evidence establish no final42-page delivery. Preserve pending factual source prerequisite; independently evaluate material Albuquerque/substantive historical value with explicit uncertain-version qualification. Register bounded current authority/quality and explicit August provisional-finality exception; preserve all unrelated architecture, settled decisions, original histories and R2. One existing entry correction is unmerged for owner review; no campaign, substitute object, new entry/placement or content merge.',evidence=evidence) for r in c['resolved_rules']})
    save(P+'receipt.json',old);refresh();G.active_check('final');guard()

def render():
    from playwright.sync_api import sync_playwright
    from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
    from functools import partial
    from urllib.parse import urlparse
    import threading
    preview=sys.argv[2] if len(sys.argv)>2 else None;verify_only=len(sys.argv)>3 and sys.argv[3]=='verify'
    server=None
    if preview:assert urlparse(preview).scheme=='https' and urlparse(preview).hostname.endswith('.abqinfo.pages.dev')
    else:
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(G.ROOT/'tmp/site-build')));threading.Thread(target=server.serve_forever,daemon=True).start()
    base=preview.rstrip('/') if preview else 'http://127.0.0.1:'+str(server.server_port);url=base+'/transportation/transit/abq-ride/#art-planning-and-development-history'
    results=[];row=G.load(P+'baseline-record.json');v=G.load(P+'quality-decision.json')['visible_change']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        for n,(label,w,h) in enumerate([('desktop',1440,1100),('mobile',390,844)],43):
            page=browser.new_page(viewport=dict(width=w,height=h));response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
            link=page.locator('a[href="'+row['r2_url']+'"]');assert link.count()==1 and link.inner_text()==v['new_label']
            item=link.locator('xpath=ancestor::li[1]');text=item.inner_text();assert v['new_description'] in ' '.join(text.split()) and '(Final Report)' not in text
            assert item.locator('a[href="'+row['source_url']+'"]').count()==1 and page.locator('#art-planning-and-development-history').count()==1
            assert 'Albuquerque Rapid Transit Design Reconfiguration Conditions' in page.inner_text('body') and 'ART Corridor Building Permits, October 2022' in page.inner_text('body')
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            item.scroll_into_view_if_needed();page.evaluate('window.scrollBy(0,-65)')
            path='tmp/brt-prize-final-'+label+'.png' if verify_only else P+(f'visual-{n:03d}.png' if preview else label+'.png');page.screenshot(path=str(G.ROOT/path))
            results.append(dict(viewport=label,width=w,height=h,screenshot=path,http_status=response.status,entry_text=text,archive_link_count=1,same_existing_archive=True,official_marked_draft_page_link_count=1,anchor_passed=True,no_horizontal_overflow=True,unsupported_final_label_absent=True));page.close()
        browser.close()
    if server:server.shutdown();server.server_close()
    data=dict(browser='Google Chrome via Playwright',url=url,nonproduction=True,checked_head=G.git('rev-parse','HEAD'),results=results,exact_single_entry_source_delta_guard='passed',publication_quality_gate='passed independently; factual source hold remains')
    if verify_only:
        previous=G.load(P+'preview-verification.json');assert [r['entry_text'] for r in results]==[r['entry_text'] for r in previous['results']];print('Final-head preview exactly matches reviewed entry in desktop/mobile')
    else:save(P+('preview-verification.json' if preview else 'rendered-check.json'),data);print('Verified complete qualified report entry, existing archive/source/anchor and desktop/mobile layout')

def normalize_derived():
    refresh();G.active_check('mutation','governance_implementation',[ID])
    for name in ['city.txt','preserved.txt','comparison.txt']:
        path=G.ROOT/(P+name);path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').split('\n')).rstrip()+'\n',encoding='utf-8',newline='\n')
    # Exact PDF originals and gzip response evidence are never normalized.
    for path in (G.ROOT/P).glob('validation-attempt-*.log'):
        import re
        value=path.read_text(encoding='utf-8-sig',errors='replace');value=re.sub(r'\x1b\[[0-9;]*m','',value);path.write_text('\n'.join(line.rstrip() for line in value.splitlines())+'\n',encoding='utf-8',newline='\n')
    refresh()

if __name__=='__main__':globals()[sys.argv[1]]()
