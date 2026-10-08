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

def quality():
    refresh();G.active_check('review','quality_assessment',IDS)
    f=G.load(P+'research-findings.json');c=G.load(P+'comparison.json');assert c['visual_inspection_completed'] and len(c['different_extracted_text_pages'])==31
    scope=dict(assessed_at=Shared.now(),geographic_institutional_scope='Adopted City of Albuquerque Rank 2 bikeway and trail facilities plan for the Albuquerque street and trail network.',specific_albuquerque_connection='Maps and evaluates Albuquerque bikeways, trails and crossings; names local projects and implementation responsibilities and records the City Council adopting resolution R-24-94.',abqinfo_public_information_value='The full plan lets residents examine the City network vision, project priorities, facility designs, public input, evaluation method and implementation commitments in one official file.',general_context_exclusion_test='The basis is the specific City adoption, named Albuquerque corridors and locally actionable network/project recommendations, not generic cycling guidance or incidental City references.',final_scope_decision='passes_both_gates',substantive_rationale='This adopted facility plan directly governs consequential Albuquerque active-transportation infrastructure policy and priorities. Its maps, project tables, policy actions, crossings guide and public-input appendices materially help readers understand and scrutinize the City network and future investments.')
    q=dict(document_function='Complete adopted Albuquerque bikeway and trail facilities plan with integrated implementation and supporting appendices.',substantive_content='Network analysis, mapped facility recommendations, prioritized local projects, design and crossing guidance, policy actions, evaluation methods, public-input analysis and detailed project profiles.',durable_public_usefulness='One complete official reference for residents to inspect City bicycle and trail priorities, implementation commitments and supporting methods over time.',information_density='513 PDF pages and '+str(c['originals']['city']['words'])+' extracted words, including 144 plan-body pages and 369 pages of substantive appendices and crossings guidance; maps, tables and diagrams were visually reviewed.',unique_information='Exact current City Planning and adopted-plan OnBase delivery, with later plan-body revisions and complete appendices absent from the preserved July 2024 proposed-edition body.',rationale='The official complete file has clear standalone value because it combines the adopted Albuquerque network plan with its project methodology, priority tables, local maps, public-input record, profiles and crossing guidance. Component convenience links on the existing page supplement this single canonical original; they do not make a second primary plan entry. The proposal-only body is retained as historical evidence and cannot substitute for the current edition.',reviewed_document_content=True,visual_inspection_completed=True,page_count=513,extracted_word_count=c['originals']['city']['words'],standalone_public_value='substantive',publication_form='standalone',series_relationship='standalone',currentness_review_required=True,currentness_review=dict(status='current',authoritative_sources=[P+'retrievals.json',P+'historical-evidence.json','https://www.cabq.gov/planning/plans-publications'],finding='City Planning lists the 2024 plan as an adopted Rank 2 facility plan, with the current PDF and adopted-plan OnBase delivery exact to this 513-page original. The earlier proposed-plan body is a separate prior edition.',publication_qualification='Single current plan entry links the complete 513-page archived original and official City PDF; supporting component links remain subordinate.'))
    decision=dict(artifact_type='current_plan_scope_quality_and_presentation_decision',candidate_ids=IDS,canonical_id=IDS[1],superseded_proposal_id=IDS[0],scope_assessment=scope,quality_assessment=q,publication_quality_decision=dict(decision='passes',finding_id=TASK+':complete-city-edition',assessment=q,evidence=[P+'comparison.json',P+'historical-evidence.json',P+'research-findings.json',P+'retrievals.json']),visible_change=dict(page=PAGE,section='Current Bike Plan',old_current_plan_link=G.load(P+'baseline-records.json')[IDS[0]]['r2_url'],new_current_plan_link=G.load(P+'baseline-records.json')[IDS[1]]['r2_url'],official_city_pdf='https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf',retain_component_links=True),decision='Complete City edition passes both mission-scope gates and substantive standalone publication quality; proposed-only body is superseded for current-plan presentation.')
    save(P+'quality-decision.json',decision);event('quality_assessment','The actual complete City file passes positive Albuquerque mission scope, full-document visual and substantive quality, family-component and currentness review; one canonical current-plan entry is appropriate.',P+'quality-decision.json');refresh()

def reconcile():
    refresh();G.active_check('mutation','governance_implementation',IDS)
    f=G.load(P+'research-findings.json');q=G.load(P+'quality-decision.json');assert f['complete_comparison']['text_equivalent_to_official_proposal_pages']==144
    old_ids=['decision-trails-1993-canonical-reconciliation-2026-10-07-exception-'+str(i) for i in range(1,5)]
    registry=G.load(G.REGISTRY);proposals={};replacements=[]
    exception=' Explicit current owner exception solely for src-907f4de342216f97 and src-0b1dfe6e620d7fe0: the 144-page preserved PDF is text-equivalent throughout to the proposed-plan body in the original R-24-94 exhibit, but its exact former City-delivered bytes remain unproved. Complete comparison establishes 31 changed extracted-text core pages and 369 absent appendix pages versus the 513-page currently delivered adopted City file. Reconcile the former as a superseded proposed-edition body and the latter as the validated single current complete-plan entry, with positive actual-file scope/quality. Replace only the Current Bike Plan presentation through one unmerged owner-review PR with verified preview. Preserve both R2 originals, all historical evidence, unrelated decisions and the 2014/2015 family.'
    for n,old_id in enumerate(old_ids,1):
        old=next(x for x in registry['entries'] if x['governance_id']==old_id);assert old['state']=='active'
        new_id='decision-'+TASK+'-exception-'+str(n)
        proposal=dict(existing_governance_id=old_id,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=[P+'historical-evidence.json',P+'comparison.json',P+'research-findings.json',P+'quality-decision.json',P+'retrievals.json'],proposed_replacement=old['binding_requirement']+exception,consequences='Only the exact two frozen candidate dispositions and existing Current Bike Plan presentation change. Old evidence, all other records and page sections, and R2 bytes remain unchanged.',authorization_artifact=P+'authority.json',authorized=True)
        proposals[old_id]=proposal
        new=copy.deepcopy(old);new.update(governance_id=new_id,title=old['title']+' with exact 2024 Bikeway edition exception',state='active',authority='Explicit current owner exact-two-record edition/provenance instruction',decision_date='2026-10-07',effective_date='2026-10-07',binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],supersedes=[old_id],implementation_status='Evidence-backed proposed/current edition reconciliation and owner-review presentation')
        new['controlling_artifacts'].append(dict(path=P+'governance-reconciliation.json',sha256='',binding_pointers=['/']))
        new['settled_decisions']=[dict(question_id=x['question_id'],decision=x['decision']+exception) for x in old.get('settled_decisions',[])]+[dict(question_id=TASK+':version-identity',decision='The 144-page file is the proposed body and the 513-page City delivery is the current complete adopted edition; one current entry only, with no R2 replacement.')]
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'supersession.json');replacements.append(new)
    save(P+'supersession.json',dict(artifact_type='explicit_scope_supersession_proposals',proposals=proposals))
    save(P+'governance-reconciliation.json',dict(artifact_type='exact_two_record_edition_disposition',candidate_ids=IDS,explicit_scoped_replacements=proposals,proposed_edition_id=IDS[0],current_official_complete_edition_id=IDS[1],proposed_status='superseded',current_status='validated',exact_proposed_pdf_city_delivery_unproved=True,proposal_text_relationship_established=True,complete_current_city_byte_identity_established=True,visible_change='Replace the proposed-body primary link and duplicative combined entry with one complete City current-plan link under Current Bike Plan.',owner_review='One unmerged review PR with verified Cloudflare preview; planning-snapshot at reviewed PR head.',r2_delta=0,historical_evidence_unchanged=True,unrelated_records_unchanged=True))
    for new in replacements:new['controlling_artifacts'][-1]['sha256']=G.file_hash(P+'governance-reconciliation.json')
    registry['entries']+=replacements
    for x in registry['entries']:
        for a in x['controlling_artifacts']:
            if a['path']==P+'supersession.json':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,registry)
    bind(P+'governance-reconciliation.json','decision-'+TASK,'Disposition only the two frozen 2024 Bikeway editions; 144-page proposed body is superseded for the current-plan slot and the byte-verified 513-page City edition is the single validated current plan. One owner-review visible correction, no merge or R2 mutation.')
    bind(P+'quality-decision.json','quality-'+TASK,'Apply actual complete City edition positive mission-scope, standalone document-quality and currentness assessment; component convenience links remain subordinate and unchanged.')
    b=G.load(P+'baseline-records.json');a=b[IDS[0]];z=b[IDS[1]]
    proposal_changes=dict(status='superseded',title='2024 Bikeway and Trail Facilities Plan — Proposed Plan Body (July 2024)',date='2024-07',source_url=G.load(P+'historical-evidence.json')['source_url'],direct_file_url=None,canonical_candidate_id=IDS[1],review_reason=None,exclusion_reason='Superseded proposed-plan body; not the complete currently delivered adopted City edition.',provenance_status='Text-equivalent on all 144 pages to the City R-24-94 proposed-plan exhibit after Council page numbers/PDF extraction normalization; exact former City delivery of this PDF hash remains unproved. Existing archived/local/public bytes verified and preserved.',validation_status='Proposed-edition relationship and complete 513-page current-edition comparison passed; exact City delivery of the preserved proposed-body PDF hash remains unverified. Not a current-plan publication.',processing_notes=a['processing_notes']+['2026-10-07 '+TASK+': full 144/513-page comparison and all 144 pages aligned to original R-24-94 PROPOSED exhibit; 31 core pages differ in extracted text, 369 current City appendix pages absent. This proposed-edition body is superseded as the current-plan entry. Original R2 bytes retained; exact former City delivery of its hash remains unproved.'])
    current_changes=dict(status='validated',title='2024 Bikeway and Trail Facilities Plan',date='2024-12',scope_assessment=q['scope_assessment'],quality_assessment=q['quality_assessment'],publication_quality_decision=q['publication_quality_decision'],review_reason=None,exclusion_reason=None,provenance_status='Exact retained/local/R2 public SHA256 and size match the current City Planning PDF and adopted-plan OnBase delivery: complete 513-page 2024 plan.',validation_status='passed',description='The complete adopted City plan sets Albuquerque bicycle and trail network priorities, facility recommendations, policies and implementation guidance, with supporting project, public-input and crossing materials.',description_word_count=25,processing_notes=z['processing_notes']+['2026-10-07 '+TASK+': exact current City PDF and Planning adopted-plan OnBase GETs match existing 513-page R2 original. Complete proposed/current page comparison finds 31 extracted-text core page differences and 369 additional appendix pages. This is the single canonical current-plan entry; both existing R2 originals remain unchanged.'])
    save(P+'record-updates.json',dict(approved_updates=[dict(id=IDS[0],changes=proposal_changes),dict(id=IDS[1],changes=current_changes)]))
    event('governance_implementation','Four exact-record explicit authority replacements reconcile prior proposed/current uncertainty while preserving all other decisions; scoped inventory changes staged but not yet applied.',P+'governance-reconciliation.json')
    refresh();G.active_check('mutation','inventory_disposition',IDS)

def repair_authorization_supersession():
    """Register the changed controlling proposal receipt after the research checkpoint."""
    active=G.load(G.ACTIVE_TASK);active.pop('supersession_proposals_path',None);save(G.ACTIVE_TASK,active)
    registry=G.load(G.REGISTRY);old_id='authorization-'+TASK+'-supersession'
    old=next(x for x in registry['entries'] if x['governance_id']==old_id);assert old['state']=='active'
    baseline=json.loads(subprocess.check_output(['git','show','HEAD:'+G.REGISTRY],cwd=G.ROOT))
    prior=next(x for x in baseline['entries'] if x['governance_id']==old_id)
    proposal=dict(existing_governance_id=old_id,current_decision=prior['binding_requirement'],controlling_evidence=copy.deepcopy(prior['controlling_artifacts']),new_evidence=[P+'historical-evidence.json',P+'comparison.json',P+'research-findings.json',P+'quality-decision.json'],proposed_replacement=prior['binding_requirement']+' The completed exact-two-record proposals in the updated receipt replace the initially empty proposal placeholder; this does not expand the frozen scope or add an external action.',consequences='Register the evidence-backed receipt change after the research checkpoint while preserving the earlier empty receipt and its authority history.',authorization_artifact=P+'authority.json',authorized=True)
    data=G.load(P+'supersession.json');data['proposals'][old_id]=proposal;save(P+'supersession.json',data)
    new=copy.deepcopy(old);new.update(governance_id=old_id+'-v2',title='Completed exact-two-record supersession receipt authority',state='active',authority='Explicit current owner exact-two-record resolution instruction',decision_date='2026-10-07',effective_date='2026-10-07',binding_requirement=proposal['proposed_replacement'],required_actions=[proposal['proposed_replacement']],supersedes=[old_id],implementation_status='Registered completed scoped proposals')
    new['settled_decisions']=[dict(question_id=TASK+':proposal-receipt',decision='Completed four scoped source/queue/override replacements; no other authority changed.')]
    old.update(state='superseded',superseded_by=new['governance_id'],supersession_evidence=P+'supersession.json');registry['entries'].append(new)
    for x in registry['entries']:
        for a in x['controlling_artifacts']:
            if a['path']==P+'supersession.json':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,registry);refresh();G.active_check('mutation','inventory_disposition',IDS)

def queue():
    inv=G.load('project-state/master-inventory.json');prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={r['id'] for r in inv['candidates'] if r['status']=='pending review'};approved={r['id'] for r in inv['candidates'] if r['status']=='approved for addition'}
    q.update(artifact_type='bikeway_2024_edition_resolution_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for k in ['gated','source_or_structural_blocked']:
        original=prior[k+'_pending_ids'];q[k+'_pending_ids']=({i:why for i,why in original.items() if i in pending} if isinstance(original,dict) else sorted(i for i in original if i in pending));q[k+'_pending_count']=len(q[k+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated),bikeway_2024_edition_resolution=dict(proposed_body_id=IDS[0],current_complete_id=IDS[1],source_blocker_cleared=1,owner_review_pr_required=True))
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,334,321,13,0)
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))

def apply_presentation():
    refresh();G.active_check('mutation','content_implementation',IDS)
    path=G.ROOT/PAGE;s=path.read_text(encoding='utf-8-sig');old=(G.ROOT/(P+'baseline-page.md')).read_text(encoding='utf-8-sig')
    assert s==old
    start=s.index('## Current Bike Plan\n');end=s.index('  - [Bicycle and Trail Crossings Guide]',start)
    new='## Current Bike Plan\n\n- [2024 Bikeway and Trail Facilities Plan](https://files.abqinfo.com/transportation/bicycling/bike-plans/2024-albuquerque-bikeway-trail-facilities-plan-combined.pdf)\n\n  The City\'s complete adopted 513-page plan sets Albuquerque\'s bicycle and trail network vision, facility recommendations, project priorities, and implementation guidance, with its supporting appendices and crossings guide. [Official City PDF](https://www.cabq.gov/planning/documents/2024-bikeway-and-trail-facilities-plan.pdf)\n\n'
    path.write_text(s[:start]+new+s[end:],encoding='utf-8',newline='\n')
    queue();save(P+'progress.json',dict(stage='two_inventory_dispositions_and_single_current_plan_presentation_applied',completed=IDS,remaining=['derived_checkpoint_and_human_queue','full_validation','owner_review_PR_and_verified_Cloudflare_preview','planning_snapshot_sync']))
    event('content_implementation','Current Bike Plan now has one primary link to the exact complete City edition, with its official PDF beside it; old proposed-body main link and duplicative combined entry removed, all existing component links untouched.',PAGE)
    refresh();guard()

def local_receipt():
    refresh();G.active_check('mutation','inventory_disposition',IDS);guard()
    baseline=G.load(P+'baseline-records.json');inventory=G.load('project-state/master-inventory.json');after={r['id']:r for r in inventory['candidates'] if r['id'] in IDS}
    assert after[IDS[0]]['status']=='superseded' and after[IDS[1]]['status']=='validated'
    q=G.load(P+'queue.json');assert q['pending_review_count']==334 and q['source_or_structural_blocked_pending_count']==13
    human=G.load('project-state/discovery/consolidated-human-review-queue.json');checkpoint=G.load('project-state/checkpoint.json')
    save(P+'accounting.json',dict(task_id=TASK,candidate_ids=IDS,before_status={i:baseline[i]['status'] for i in IDS},after_status={i:after[i]['status'] for i in IDS},before_row_sha256={i:G.digest(baseline[i]) for i in IDS},after_row_sha256={i:G.digest(after[i]) for i in IDS},queue=dict(approved=0,pending=334,governance_gated=321,source_structural_blocked=13,actionable=0,human_review=len(human.get('records',[]))),checkpoint_remaining_nonterminal=checkpoint['remaining_nonterminal'],visitor_visible_change='One Current Bike Plan entry now links the 513-page complete City edition; proposed-body main link and duplicate combined item removed.',r2_delta=dict(objects=0,bytes=0,uploads=0,overwrites=0,deletions=0),historical_evidence_preserved=True,other_inventory_rows_unchanged=True,other_page_content_unchanged=True))
    current=G.ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8-sig');links=old[old.index('[Owner correction]'):]
    current.write_text('# Current project state\n\n2024 Bikeway and Trail Facilities Plan exact two-record edition resolution is in an unmerged owner-review PR. The 144-page July 2024 proposed-plan body src-907f4de342216f97 is superseded for the current-plan presentation: all 144 pages text-align with the original R-24-94 PROPOSED exhibit after Council pagination/extraction normalization, but exact former City delivery of its PDF hash remains unproved. The 513-page src-0b1dfe6e620d7fe0 is the complete adopted City delivery, exact to both current Planning PDF and adopted-plan OnBase public bytes; its first 144 pages differ on 31 extracted-text pages and 369 appendix pages follow.\n\nThe Current Bike Plan section now has one primary complete City plan link and an official City PDF link. The existing 144-page R2 original remains intact but is no longer presented as current; component links and 2014/2015 family remain unchanged. Full validation and Cloudflare preview/PR review are pending; do not merge or deploy. No R2 write.\n\nQueue: 0 approved / 334 pending (321 governance-gated / 13 source-structural blocked), 0 actionable / human review. Checkpoint remaining nonterminal 885.\n\n[Receipt](governance/bikeway-2024-edition-resolution-2026-10-07/receipt.json) · [Research](governance/bikeway-2024-edition-resolution-2026-10-07/research-findings.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n\n'+links,encoding='utf-8',newline='\n')
    event('inventory_disposition','Exactly the two frozen inventory rows reconciled, derived 334/321/13 queue and checkpoint regenerated, zero human queue and R2 delta verified; visible change remains owner-review-only.',P+'accounting.json')
    c=G.load(G.load(G.ACTIVE_TASK)['contract']);evidence=[P+n for n in ['comparison.json','historical-evidence.json','research-findings.json','quality-decision.json','governance-reconciliation.json','record-updates.json','accounting.json','queue.json','retrievals.json']]
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,status='visible_correction_implemented_validation_and_owner_PR_pending',accounting=G.load(P+'accounting.json'),normal_validation='pending',owner_review_required=True,visitor_visible_delta='one corrected Current Bike Plan entry',r2_delta=0,evidence_sha256={p:G.file_hash(p) for p in evidence},governance_accounting={r['governance_id']:dict(requirement=r['binding_requirement'],implementation='Complete exact-two-record review verifies the older proposed body against the Council exhibit and exact current City bytes for the complete later edition. Four registered scoped exceptions and the owner authorization receipt preserve all other authority. Independent current City scope/quality passed; two inventory dispositions and single existing-page presentation are applied. No R2 write, 2014/2015 family action, merge or production deployment.',evidence=evidence) for r in c['resolved_rules']}))
    save(P+'progress.json',dict(stage='local_disposition_and_accounting_complete',completed=IDS,remaining=['full_validation','owner_review_PR_and_verified_Cloudflare_preview','planning_snapshot_sync']))
    refresh();G.active_check('final');guard()

if __name__=='__main__':globals()[sys.argv[1]]()
