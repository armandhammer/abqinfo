"""Exact two-record 2024 Bikeway edition/provenance resolution."""
import copy, hashlib, json, subprocess, sys
import TaskGovernance as G
import Trails1993CanonicalReconciliation as Shared
from SourceHoldResolution import audit

TASK='bikeway-2024-edition-resolution-2026-10-07'
BASE='ed3160e0d91f5e9ccd0598622555c16935ef6882'
P='project-state/governance/'+TASK+'/'
IDS=['src-907f4de342216f97','src-0b1dfe6e620d7fe0']
PAGE='content/transportation/bicycling/bike-plans.md'
SCRIPT='scripts/project/Bikeway2024EditionResolution.py'
save=Shared.save

def refresh():
    Shared.TASK=TASK;Shared.BASE=BASE;Shared.P=P;Shared.ID=IDS[0]
    Shared.refresh()

def event(operation,summary,evidence):
    plan=G.load(P+'implementation.json')
    plan['events'].append(dict(operation=operation,candidate_ids=IDS,governance_ids=plan['respected_governance_ids'],action='implements',summary=summary,evidence=evidence,use_contract_record_rules=True))
    save(P+'implementation.json',plan)

def bind(path,gid,requirement):
    r=G.load(G.REGISTRY)
    r['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope={'candidate_ids':IDS,'task_ids':[TASK]},authority='Explicit current owner two-record edition/provenance resolution instruction',decision_date='2026-10-07',effective_date='2026-10-07',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded edition review'))
    save(G.REGISTRY,r)

def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    names=['population.json','authority.json','baseline-records.json','baseline-page.md','starting-state.json','implementation.json','supersession.json','historical-evidence.json','retrievals.json','comparison.json','comparison.txt','research-findings.json','quality-decision.json','governance-reconciliation.json','record-updates.json','queue.json','accounting.json','receipt.json','progress.json','rendered-check.json','integration-intent.json','remote-final.json','summary.md','pr-description.md','pr.json','preview-verification.json','preserved.txt','city.txt','desktop.png','mobile.png']
    paths=[P+n for n in names]+[P+f'contract-v{i}.json' for i in range(1,61)]+[P+f'response-{i:03d}.bin.gz' for i in range(1,151)]+[P+f'visual-{i:03d}.png' for i in range(1,151)]+[P+f'validation-attempt-{i}.log' for i in range(1,8)]
    paths += [SCRIPT,'scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md','project-state/discovery/retained-source-audit-queue.json',PAGE]
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[PAGE],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','content_implementation','content_removal','visitor_visible_change'],artifact_paths=paths))
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id'] in IDS}
    G.write_once(P+'baseline-records.json',rows)
    (G.ROOT/(P+'baseline-page.md')).write_bytes((G.ROOT/PAGE).read_bytes())
    qp=G.load('project-state/ordinary-queue-current.json')['artifact'];q=G.load(qp)
    G.write_once(P+'starting-state.json',dict(baseline_commit=BASE,remote_main=BASE,remote_planning_snapshot=BASE,source_queue=qp,queue_counts={k:q[k] for k in ['approved_count','pending_review_count','gated_pending_count','source_or_structural_blocked_pending_count']},r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),page_sha256=G.file_hash(PAGE)))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    save(P+'progress.json',dict(stage='exact_two_records_and_existing_presentation_frozen',inventory_mutation=False))

def bootstrap():
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals={}))
    refresh();a=G.load(G.ACTIVE_TASK);a.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,a)
    G.active_check('mutation','governance_implementation',IDS)
    save(P+'authority.json',dict(artifact_type='owner_authorization',authority='Explicit current user instruction',candidate_ids=IDS,instruction='Reconstruct current ABQInfo state from repository and Project instructions. Resolve the 2024 Bikeway and Trail Facilities Plan edition/provenance issue involving exactly src-907f4de342216f97 (unresolved 144-page edition currently primary current-plan link) and src-0b1dfe6e620d7fe0 (513-page Combined Authoritative Edition matching current City delivery). Freeze exactly these records and existing presentation on content/transportation/bicycling/bike-plans.md; normal governed workflow. Determine exactly what 144-page edition is, its relationship to 513-page City edition, and appropriateness as primary current plan. Complete version comparison and authoritative-source research, including 31 differing extracted-text pages in addition to absent appendices; do not assume equivalence. Ultimately make current official plan unambiguous and avoid duplicative/confusing main plan versus combined edition terminology. Do not overwrite/delete R2 objects or broaden into 2014/2015 family. If visible correction required, one owner-review PR with verified Cloudflare preview and synchronize chatgpt/planning-snapshot to reviewed PR head; do not merge. If no visible correction, only authorized background reconciliation. Full validation; report conclusion, dispositions, correction, queues, R2 delta, validation, final refs.'))
    bind(P+'authority.json','owner-'+TASK,'Complete exact two-record edition/provenance comparison and reconciliation; make current official plan unambiguous via one unmerged owner-review PR if required, verify Cloudflare preview and synchronize planning-snapshot to PR head. No content merge, R2 mutation or 2014/2015 population expansion.')
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json')
    assert lifecycle['stages'][-1]['id']=='pr216-postmerge-closeout-2026-10-07'
    lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Bikeway2024EditionResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=runner.read_text(encoding='utf-8-sig');i=s.index('Set-StrictMode')
    s=s[:i]+'& python "$PSScriptRoot/Bikeway2024EditionResolution.py" guard\nif ($LASTEXITCODE -ne 0) { throw "2024 Bikeway edition resolution regression failed" }\n\n'+s[i:];runner.write_text(s,encoding='utf-8',newline='\n')
    refresh();G.active_check('review','document_review',IDS)

def guard():
    from WorkflowStageLifecycle import StageSnapshot
    stage=StageSnapshot(TASK)
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert stage.load_json(path)==json.loads(subprocess.check_output(['git','show',BASE+':'+path])),path
    before=json.loads(subprocess.check_output(['git','show',BASE+':project-state/master-inventory.json']));after=stage.load_json('project-state/master-inventory.json')
    b={r['id']:r for r in before['candidates']};a={r['id']:r for r in after['candidates']}
    assert set(a)==set(b)
    assert all(a[i]==b[i] for i in a if i not in IDS),'Outside frozen inventory population'
    old=subprocess.check_output(['git','show',BASE+':'+PAGE]).decode('utf-8');new=stage.read_text(PAGE)
    assert old[old.index('  - [Bicycle and Trail Crossings Guide]'):]==new[new.index('  - [Bicycle and Trail Crossings Guide]'):],'Outside frozen presentation'
    print('Exact two-record inventory/presentation and zero R2 delta guard passed')

def fetch(url,label):
    import urllib.request,gzip
    from datetime import datetime,timezone
    G.active_check('review','document_review',IDS)
    records=G.load(P+'retrievals.json') if (G.ROOT/(P+'retrievals.json')).exists() else dict(records=[])
    r=dict(label=label,requested_url=url,retrieved_at=datetime.now(timezone.utc).isoformat())
    raw=None
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 ABQInfo version comparison'}),timeout=60) as response:
            raw=response.read();r.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if len(raw)<10000000:
                r['response_artifact']=P+f'response-{len(records["records"])+1:03d}.bin.gz';(G.ROOT/r['response_artifact']).write_bytes(gzip.compress(raw,mtime=0))
            else:
                row=next((v for v in G.load(P+'baseline-records.json').values() if v['checksum_sha256']==r['sha256']),None)
                if row:
                    assert (G.ROOT/row['local_path']).read_bytes()==raw;r['identical_retained_original']=row['local_path']
                else:
                    target=G.ROOT/'tmp'/('bikeway-source-'+r['sha256']+'.pdf');target.write_bytes(raw);r['temporary_source_path']=target.relative_to(G.ROOT).as_posix()
    except Exception as e:r['error']=str(e)
    records['records'].append(r);save(P+'retrievals.json',records);print(json.dumps(r));return raw,r

def obtain():
    refresh();G.active_check('review','document_review',IDS)
    for row in G.load(P+'baseline-records.json').values():
        raw=(G.ROOT/row['local_path']).read_bytes();assert len(raw)==row['size_bytes'] and hashlib.sha256(raw).hexdigest()==row['checksum_sha256']
        _,r=fetch(row['r2_url'],'fresh full public GET '+row['id']);assert r['sha256']==row['checksum_sha256'] and r['size_bytes']==row['size_bytes']
    _,r=fetch('https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf','current City original');assert r['sha256']==G.load(P+'baseline-records.json')[IDS[1]]['checksum_sha256']
    _,r=fetch('https://onbase.cabq.gov/PublicAccess/api/Document/12246818/','Planning adopted-plan delivery');assert r['sha256']==G.load(P+'baseline-records.json')[IDS[1]]['checksum_sha256']
    for url,label in [('https://www.cabq.gov/planning/plans-publications','Planning adopted plan index'),('https://www.cabq.gov/municipaldevelopment/our-department/engineering/bicycle-pedestrian-amenities','DMD plan index'),('https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf/view','City file listing')]:fetch(url,label)
    event('document_review','Fresh public GETs verify both existing originals; current City and Planning adopted-plan OnBase delivery match exact 513-page original.',P+'retrievals.json')

def compare():
    import pymupdf as fitz,difflib,re
    from PIL import Image,ImageDraw
    refresh();G.active_check('review','document_review',IDS)
    baseline=G.load(P+'baseline-records.json');docs={n:fitz.open(G.ROOT/baseline[i]['local_path']) for n,i in zip(['preserved','city'],IDS)}
    assert len(docs['preserved'])==144 and len(docs['city'])==513
    def words(s):return re.findall(r'\S+',s)
    def delta(a,b):return [dict(kind=k,preserved=' '.join(a[i:j]),city=' '.join(b[m:n])) for k,i,j,m,n in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if k!='equal']
    def images(p):return [dict(rect=list(i['bbox']),width=i['width'],height=i['height'],digest=i['digest'].hex()) for i in p.get_image_info(hashes=True)]
    texts={n:[p.get_text() for p in d] for n,d in docs.items()}
    for n,t in texts.items():(G.ROOT/(P+n+'.txt')).write_text('\n\f\n'.join(t),encoding='utf-8')
    rows=[];report=[]
    for i in range(144):
        a,b=docs['preserved'][i],docs['city'][i];at,bt=texts['preserved'][i],texts['city'][i]
        ap=a.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False);bp=b.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
        row=dict(pdf_page=i+1,preserved_dimensions=list(a.rect),city_dimensions=list(b.rect),preserved_word_count=len(words(at)),city_word_count=len(words(bt)),text_equal=at.strip()==bt.strip(),token_delta=delta(words(at),words(bt)),render_equal=ap.samples==bp.samples,preserved_render_sha256=hashlib.sha256(ap.samples).hexdigest(),city_render_sha256=hashlib.sha256(bp.samples).hexdigest(),preserved_images=images(a),city_images=images(b),drawings_equal=str(a.get_drawings())==str(b.get_drawings()))
        if not row['render_equal']:
            left=Image.frombytes('RGB',[ap.width,ap.height],ap.samples);right=Image.frombytes('RGB',[bp.width,bp.height],bp.samples)
            canvas=Image.new('RGB',(ap.width+bp.width+12,max(ap.height,bp.height)+25),'white');canvas.paste(left,(0,25));canvas.paste(right,(ap.width+12,25));ImageDraw.Draw(canvas).text((10,5),f'PDF {i+1}: PRESERVED 144-PAGE | CURRENT CITY 513-PAGE',fill='black')
            path=P+f'visual-{i+1:03d}.png';canvas.save(G.ROOT/path);row['paired_visual']=path
        rows.append(row)
        if not row['text_equal']:report.append(f'PDF PAGE {i+1}\n'+json.dumps(row['token_delta'],ensure_ascii=False,indent=2))
    appended=[]
    for i in range(144,513):
        p=docs['city'][i];pix=p.get_pixmap(matrix=fitz.Matrix(.3,.3),alpha=False)
        appended.append(dict(pdf_page=i+1,words=len(words(texts['city'][i])),opening=texts['city'][i][:240],dimensions=list(p.rect),images=images(p),render_sha256=hashlib.sha256(pix.samples).hexdigest()))
    (G.ROOT/(P+'comparison.txt')).write_text('\n\n'.join(report),encoding='utf-8')
    save(P+'comparison.json',dict(artifact_type='complete_edition_version_comparison',originals={n:dict(candidate_id=i,path=baseline[i]['local_path'],size_bytes=baseline[i]['size_bytes'],sha256=baseline[i]['checksum_sha256'],pages=len(docs[n]),words=sum(len(words(t)) for t in texts[n]),metadata=docs[n].metadata) for n,i in zip(['preserved','city'],IDS)},alignment=rows,appended_city_pages=appended,different_extracted_text_pages=[r['pdf_page'] for r in rows if not r['text_equal']],different_render_pages=[r['pdf_page'] for r in rows if not r['render_equal']],whole_core_token_delta=delta(words('\n'.join(texts['preserved'])),words('\n'.join(texts['city'][:144]))),visual_inspection_completed=False))
    event('document_review','All 657 pages extracted and measured; all 144 core pages compared in text, rendered pixels, raster images and vector drawings; all 369 additional City pages inventoried and rendered successfully. Full deltas saved.',P+'comparison.json')
    print('Different text pages:',[r['pdf_page'] for r in rows if not r['text_equal']]);print('Different render pages:',[r['pdf_page'] for r in rows if not r['render_equal']])

def legislative():
    import pymupdf as fitz,re,unicodedata
    refresh();G.active_check('review','document_review',IDS)
    source=next(r for r in G.load(P+'retrievals.json')['records'] if r['label']=='R-94 original legislative attachment')
    wrapper=fitz.open(G.ROOT/source['temporary_source_path'])
    held=fitz.open(G.ROOT/G.load(P+'baseline-records.json')[IDS[0]]['local_path'])
    assert len(wrapper)==754 and len(held)==144
    rows=[]
    def normalized(t):
        return unicodedata.normalize('NFKC',t.replace('\u00ad','-').replace('\ufffd','').replace(' ','').replace('\n','').replace('\t',''))
    for i in range(144):
        a=held[i];b=wrapper[193+i]
        at=a.get_text().strip();bt=b.get_text().strip()
        clean=lambda t:re.sub(r'\s+\d+\s*$','',t).strip()
        numbered=bt.removesuffix(str(i+168)).strip()
        rows.append(dict(held_pdf_page=i+1,council_attachment_pdf_page=194+i,council_added_page_number=i+168,exact_text=at==bt,text_equal_after_wrapper_page_number=clean(at)==clean(bt),normalized_body_text_equal=normalized(at)==normalized(numbered),held_words=len(at.split()),attachment_words=len(bt.split()),held_excerpt=at[:120] if at!=bt else None,attachment_excerpt=bt[:120] if at!=bt else None,held_images=[x['digest'].hex() for x in a.get_image_info(hashes=True)],attachment_images=[x['digest'].hex() for x in b.get_image_info(hashes=True)]))
    assert all(r['normalized_body_text_equal'] for r in rows)
    save(P+'historical-evidence.json',dict(artifact_type='official_legislative_exhibit_relationship',source_url=source['final_url'],source_size_bytes=source['size_bytes'],source_sha256=source['sha256'],source_pages=754,legislative_context='Original R-24-94 attachment transmits July 18 2024 EPC recommendation and labels its attached plan PROPOSED 2024 BIKEWAY & TRAIL FACILITIES PLAN. The proposed plan core occupies attachment PDF pages 194-337; appendices follow. All 144 preserved core pages match its extracted text after removing only the Council page number and normalizing soft hyphen/replacement glyph and whitespace extraction. This establishes a proposed-edition textual relationship, not exact PDF byte identity or proof of the preserved PDF delivery route.',alignment=rows,exact_text_pages=[r['held_pdf_page'] for r in rows if r['exact_text']],wrapper_page_number_only_pages=[r['held_pdf_page'] for r in rows if not r['exact_text'] and r['text_equal_after_wrapper_page_number']],normalized_body_text_equal_pages=[r['held_pdf_page'] for r in rows if r['normalized_body_text_equal']],differing_pages=[r['held_pdf_page'] for r in rows if not r['text_equal_after_wrapper_page_number']]))
    event('document_review','Aligned all 144 preserved pages against the original official R-24-94 attachment proposed-plan pages 194-337, distinguishing Council wrapper pagination.',P+'historical-evidence.json')
    print('Exact text:',sum(r['exact_text'] for r in rows),'wrapper-only:',sum(r['text_equal_after_wrapper_page_number'] and not r['exact_text'] for r in rows),'different:',[r['held_pdf_page'] for r in rows if not r['text_equal_after_wrapper_page_number']])

if __name__=='__main__':globals()[sys.argv[1]]()
