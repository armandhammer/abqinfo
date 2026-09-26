#!/usr/bin/env python3
"""Bounded, resumable exact-source preparation. Never uploads or edits content."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, sys, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'))
import pymupdf as fitz
from PIL import Image
DISC=ROOT/'project-state/discovery'
ART=DISC/'approved-backlog-background-archive-campaign-2026-09-26.json'
BASE=ROOT/'tmp/background-campaign-live-baseline-2026-09-26.json'
STAGE=ROOT/'research/staging/approved-background-campaign-2026-09-26'
QA=ROOT/'tmp/approved-background-campaign-qa-2026-09-26'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat()
def save(d):
    d['updated_at']=now(); t=ART.with_suffix('.json.tmp'); t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); t.replace(ART)
def sha(p): return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def nodes(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from nodes(x)
    elif isinstance(v,list):
        for x in v: yield from nodes(x)
def rel(p): return Path(p).relative_to(ROOT).as_posix()
KEYS={
'src-0878bc7d09a7c65b':'development-land-use/projects/cabq-council-answer-downtown-boundary-maps-exhibits-a-b.pdf',
'src-4ac9f8a1fb953e46':'city-data/budget-spending/cabq-council-answer-fy25-non-recurring-items.pdf',
'src-5006deafb03b1f7a':'public-works/capital-projects/cabq-north-domingo-baca-aquatic-center-contract-fee-ledger.xlsx',
'src-9fd0da60e94eb698':'development-land-use/development-process/cabq-code-enforcement-motel-closure-operations-response-2025-06-05.pdf',
'src-a6753953181feb4f':'development-land-use/development-process/cabq-comprehensive-motel-enforcement-history-report-june-2025.pdf',
'src-59a9ee7af1987815':'transportation/cabq-cruising-task-force-final-report-2018.pdf',
'src-b8b28358abc9a2de':'development-land-use/development-process/cabq-final-fiber-right-of-way-excavation-barricading-regulations-2025-06-27.pdf',
'src-07ce09fd200d2d69':'city-data/public-safety/cabq-completed-problem-properties-snapshot-june-2026.pdf',
'src-c5ed372e33966029':'development-land-use/development-process/cabq-zoning-code-amendment-o-17-39-garage-yard-sales.pdf',
'src-092548fef85b887b':'development-land-use/development-process/cabq-xeriscape-101-guide.pdf',
'src-d8dd331b50fe7e9a':'development-land-use/development-process/cabq-shared-parking-agreement-requirements-and-sample-2024.pdf'}
EXCLUDED=['Planning publication','later-MS4','PGS','ABQ RIDE','Municipal Development completed meetings','2014 MS4','Prescription Trails','Notices and Orders','LGCC','fiber correspondence','O-23-96','R-24-17','PGS enactment bills','mission-scope borderlines','NMDOT','pending review']
def initialize():
    assert not ART.exists(),'Existing campaign must be resumed, not overwritten'
    inv=load(ROOT/'project-state/master-inventory.json'); approved=[r for r in inv['candidates'] if r['status']=='approved for addition']
    ranking=load(DISC/'approved-inventory-backlog-prioritization-post-later-ms4-2026-09-25.json')
    units=ranking['ranked_units']; mapping={rid:u for u in units for rid in u['record_ids']}
    assert len(approved)==27 and all(r['id'] in mapping for r in approved)
    live=load(BASE); saved=load(ROOT/'project-state/r2-inventory.json')
    identity=lambda v: {o['key']:(o['size_bytes'],o['etag']) for o in v['objects']}
    assert identity(live)==identity(saved)
    # Store a complete immutable baseline, not just aggregate counters.
    baseline=DISC/'approved-backlog-background-archive-campaign-r2-baseline-2026-09-26.json'
    baseline.write_text(json.dumps(live,indent=2)+'\n',encoding='utf-8')
    for u in units:
        u.setdefault('decision_artifact','project-state/discovery/code-enforcement-cluster-research-2026-09-11.json')
    referenced={u['decision_artifact'] for u in units}
    referenced.update(['project-state/discovery/code-enforcement-cluster-research-2026-09-11.json','project-state/discovery/council-qa-lgcc-news-cluster-research-2026-09-13.json','project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json','project-state/discovery/code-enforcement-snapshot-supersession-2026-09-11.json','project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json'])
    evidence=[(p,load(ROOT/p)) for p in referenced]
    rows=[]
    for r in approved:
        rid=r['id']; u=mapping[rid]; matches=[n for _,d in evidence for n in nodes(d) if n.get('id',n.get('candidate_id'))==rid or n.get('checksum_sha256',n.get('sha256'))==r['checksum_sha256']]
        key=next((n.get('proposed_r2_key') for n in matches if n.get('proposed_r2_key')),KEYS.get(rid))
        page=r['proposed_canonical_page']
        prep=next((n['archive_preparation'] for n in matches if 'archive_preparation' in n),{})
        key=prep.get('proposed_r2_key',key)
        page=prep.get('canonical_page',page)
        if '2011 December' in u['unit']: page='content/city-data/capital-spending.md'
        pages=next((n.get('page_count',n.get('pages',n.get('component_page_count'))) for n in matches if n.get('page_count',n.get('pages',n.get('component_page_count')))),None)
        if rid=='src-59a9ee7af1987815': pages=43
        if rid=='src-06d0fc4cd0abdef6': pages=15
        source=r['direct_file_url'] or next((n['authoritative_url'] for n in matches if n.get('authoritative_url')),r['source_url'])
        assert r['scope_assessment']['final_scope_decision']=='passes_both_gates'
        typ='XLSX' if rid=='src-5006deafb03b1f7a' else 'PDF'
        state='already_prepared_upload_authorized' if prep else 'prepare_then_upload_if_exact'
        if not key: state='prepare_only_unresolved_archive_namespace'
        rows.append(dict(id=rid,family=u['unit'],current_status=r['status'],title=r['title'],governing_decision_artifact=u['decision_artifact'],source_url=r['source_url'],direct_source_url=source,container_type=typ,expected_size_bytes=r['size_bytes'],expected_sha256=r['checksum_sha256'],expected_pages=pages,canonical_page=page,canonical_page_status='settled_existing_topical_home' if page else 'unresolved',source_provenance_confidence='saved_authoritative_exact_evidence_pending_fresh_GET',duplicate_canonical_relationship='pending_complete_inventory_and_live_R2_comparison',archive_preparation_state=state,r2_key=key,r2_key_basis='durable_proposed_key' if key and key not in KEYS.values() else 'existing_topical_namespace_and_accepted_subject' if key else 'no_accepted_namespace_without_new_IA',human_review_requirement=None,size_bytes=r['size_bytes'],within_150mb=r['size_bytes']<=150000000,archival_authorized=True,maximum_safe_stage=state,classification='unchanged_City_original',staged_path=rel(STAGE/(rid+'.'+typ.lower())),outcome='matrix_accounted_pending_preparation'))
    assert len(rows)==27 and len({r['id'] for r in rows})==27
    d=dict(schema_version=1,artifact_type='approved_backlog_background_archive_campaign',recorded_at=now(),baseline_git_sha='c054c9af67f1984051462d75727bd7fb05ea3ed2',authorization='Owner campaign prompt: source preparation, guarded upload <=150000000 bytes, exact public verification, background inventory/integration; zero publication.',project_storage_limit_bytes=10000000000,baseline_r2_artifact=rel(baseline),baseline_r2={'object_count':live['object_count'],'total_bytes':live['total_bytes']},governing_artifact_hashes={p:sha(ROOT/p) for p in sorted(referenced)},records=rows,generated_packages=[],exclusions=EXCLUDED,visitor_visible_content_changed=False,state='matrix_complete_before_R2_mutation')
    save(d); print('Complete matrix: 27 records,',sum(bool(r['r2_key']) for r in rows),'with safe keys')

def inspect(r):
    p=ROOT/r['staged_path']; QA.mkdir(parents=True,exist_ok=True)
    if r['container_type']=='XLSX':
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            for name in z.namelist():
                if name.endswith('.xml') or name.endswith('.rels'): ET.fromstring(z.read(name))
            ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            book=ET.fromstring(z.read('xl/workbook.xml'))
            sheets=[dict(s.attrib) for s in book.findall('x:sheets/x:sheet',ns)]
            dims={name:ET.fromstring(z.read(name)).find('x:dimension',ns).attrib for name in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+.xml',name)}
        return dict(structural_result='ZIP_CRC_and_all_OOXML_XML_valid',sheets=sheets,dimensions=dims,original_unchanged=True,no_conversion=True)
    spec=importlib.util.spec_from_file_location('planning_qa',ROOT/'scripts/project/Build-PlanningDocumentsRootArchivePreparation.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); mod.QA=QA
    with fitz.open(p) as doc: pages=doc.page_count
    if r['expected_pages'] is not None: assert pages==r['expected_pages'],f'Page mismatch {pages}'
    r['page_count']=pages
    qa=mod.inspect(p,pages,r['id']); qa['representative_visual_qa']='pending_agent_visual_inspection'
    with fitz.open(p) as doc:
        selected=sorted({0,pages//2,pages-1,*[i-1 for i in qa['low_ink_pages_1_based']]})
        for i in selected:
            pix=doc[i].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False); pix.save(str(QA/f"{r['id']}-page-{i+1}.png"))
        qa['representative_images']=[rel(QA/f"{r['id']}-page-{i+1}.png") for i in selected]
    return qa

def prepare():
    d=load(ART); inv=load(ROOT/'project-state/master-inventory.json')['candidates']; live=load(BASE); STAGE.mkdir(parents=True,exist_ok=True)
    if d['state']=='complete_background_campaign':
        raise SystemExit('Campaign complete; preserve approved source and archive evidence. No preparation rerun.')
    for r in d['records']:
        if r.get('source_exact_verified'): continue
        try:
            p=ROOT/r['staged_path']; req=urllib.request.Request(r['direct_source_url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo exact archival verification)','Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=120) as response, p.open('wb') as target:
                r['source_GET']={'http_status':response.status,'final_url':response.url,'content_type':response.headers.get('Content-Type'),'verified_at':now()}
                for b in iter(lambda:response.read(1024*1024),b''): target.write(b)
            assert r['source_GET']['http_status']==200
            r['fresh_size_bytes']=p.stat().st_size; r['fresh_sha256']=sha(p)
            assert (r['fresh_size_bytes'],r['fresh_sha256'])==(r['expected_size_bytes'],r['expected_sha256']),'Fresh bytes differ from approved evidence; canonical evidence preserved'
            r['qa']=inspect(r); r['source_exact_verified']=True
            r['source_provenance_confidence']='fresh_authoritative_full_GET_exact_size_SHA256'
            matches=[{'id':x['id'],'status':x['status'],'r2_key':x.get('r2_key'),'source_url':x.get('source_url')} for x in inv if x['id']!=r['id'] and x.get('checksum_sha256')==r['expected_sha256']]
            r['same_sha256_inventory_rows']=matches
            r['same_size_live_objects']=[o['key'] for o in live['objects'] if o['size_bytes']==r['size_bytes']]
            key=r['r2_key']; words=[w for w in Path(key or r['title']).stem.lower().split('-') if len(w)>4 and w not in {'cabq','report','final','historical','program'}]
            r['near_name_live_keys']=[o['key'] for o in live['objects'] if sum(w in o['key'].lower() for w in words)>=min(2,len(words))][:40]
            r['exact_or_casefold_key_collisions']=[o['key'] for o in live['objects'] if key and o['key'].casefold()==key.casefold()]
            r['duplicate_canonical_relationship']='no_exact_inventory_alias_found' if not matches else 'exact_hash_alias_requires_reconciliation'
            r['outcome']='prepared_pending_visual_and_candidate_comparison' if key else 'prepared_unuploaded_unresolved_archive_namespace'
            if matches or r['exact_or_casefold_key_collisions']: r['outcome']='prepared_pending_duplicate_collision_resolution'
        except Exception as e:
            r['outcome']='deferred_source_or_structural_issue'; r['blocker']=str(e)
        save(d); print(r['id'],r['outcome'],r.get('blocker',''),flush=True)
    d['state']='all_27_source_preparation_attempted'; save(d)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['init','prepare']); a=parser.parse_args()
    initialize() if a.action=='init' else prepare()
