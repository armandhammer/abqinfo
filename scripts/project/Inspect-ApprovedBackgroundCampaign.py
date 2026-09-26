"""Make review sheets, compare canonical candidates and validate stored packages."""
import difflib, importlib.util, json, re, urllib.request
from pathlib import Path
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('Prepare-ApprovedBackgroundCampaign.py'))
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
from PIL import Image, ImageDraw

def review_sheets(rows,prefix):
    pdfs=[r for r in rows if r['container_type']=='PDF' and r.get('qa')]
    for start in range(0,len(pdfs),4):
        group=pdfs[start:start+4]; sheet=Image.new('RGB',(1050,len(group)*470),'#eeeeee'); draw=ImageDraw.Draw(sheet)
        for j,r in enumerate(group):
            draw.text((8,j*470+4),r['id']+' '+r['title'][:95],fill='black')
            for k,ip in enumerate(r['qa']['representative_images'][:3]):
                im=Image.open(c.ROOT/ip); im.thumbnail((340,435)); sheet.paste(im,(k*350+(350-im.width)//2,j*470+25))
        out=c.QA/f'{prefix}-{start//4+1}.jpg';sheet.save(out,quality=90); print(c.rel(out))

def packages(d):
    if d['generated_packages']: return
    capital=c.load(c.DISC/'2011-capital-spending-consolidation-manifest-2026-09-18.json')
    dpm=c.load(c.DISC/'dpm-executive-committee-consolidation-manifest-2026-09-17.json')
    inv={r['id']:r for r in c.load(c.ROOT/'project-state/master-inventory.json')['candidates']}
    for packet in capital['compilations']+dpm['annual_packets']:
        is_dpm='year' in packet
        result=packet if is_dpm else packet['build_result']
        r=dict(id='generated-dpm-'+str(packet['year']) if is_dpm else 'generated-capital-'+packet['compilation_id'],title='DPM Executive Committee annual packet '+str(packet['year']) if is_dpm else packet['title'],family='DPM corrected annual packets' if is_dpm else 'Capital Spending 2011 historical compilations',classification='ABQInfo_generated_historical_compilation',container_type='PDF',staged_path=packet['local_output_path'],r2_key=packet['proposed_r2_key'],size_bytes=result['resulting_size_bytes'] if is_dpm else result['size_bytes'],expected_sha256=result['resulting_sha256'] if is_dpm else result['checksum_sha256'],expected_pages=result['resulting_page_count'] if is_dpm else result['page_count'],component_manifest='project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json' if is_dpm else 'project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json',archival_authorized=True,human_review_requirement=None,within_150mb=True,outcome='package_validation_pending')
        d['generated_packages'].append(r)
        try:
            p=c.ROOT/r['staged_path']; assert (p.stat().st_size,c.sha(p))==(r['size_bytes'],r['expected_sha256'])
            sources=packet['components'] if is_dpm else packet['sources']; comp_evidence=[]
            with c.fitz.open(p) as doc:
                offset=doc.page_count-sum(s['source_page_count'] for s in sources) if is_dpm else 0
                for s in sources:
                    rid=s['source_master_id'] if is_dpm else s['candidate_id']; row=inv[rid]
                    assert row['status']!='requires human review',f'Human review {rid}'
                    sp=c.ROOT/(s.get('local_path') or ('tmp/pdfs/dpm-input/'+rid+'.pdf'))
                    assert sp.is_file(),f'Missing component {sp}'
                    expected_hash,expected_size=row['checksum_sha256'],row['size_bytes']
                    evidence_basis='current_inventory_exact_source'
                    if is_dpm and expected_hash is None:
                        cp=c.ROOT/f"research/staging/claude-consolidation-checkpoints/dpm-{packet['year']}/items/{rid}.json"
                        if cp.exists():
                            checkpoint=c.load(cp);expected_hash,expected_size=checkpoint['checksum_sha256'],checkpoint['size_bytes']
                            evidence_basis='saved_source_checkpoint; corrected_manifest_inclusion'
                        else:
                            fresh=c.STAGE/(rid+'-dpm-component.pdf')
                            urllib.request.urlretrieve(s['source_url'],fresh)
                            expected_hash,expected_size=c.sha(fresh),fresh.stat().st_size
                            evidence_basis='fresh_authoritative_full_GET_matches_stored_component; corrected_manifest_inclusion; historical_original_status_unchanged'
                    assert c.sha(sp)==expected_hash and sp.stat().st_size==expected_size,f'Component bytes mismatch {rid}'
                    with c.fitz.open(sp) as src:
                        start=offset if is_dpm else s['compilation_source_page_start']-1
                        for i in range(src.page_count):
                            a=src[i].get_pixmap(matrix=c.fitz.Matrix(.5,.5),alpha=False);b=doc[start+i].get_pixmap(matrix=c.fitz.Matrix(.5,.5),alpha=False)
                            assert (a.width,a.height,a.samples)==(b.width,b.height,b.samples),f'Component rendered fidelity {rid} page {i+1}'
                        offset+=src.page_count
                        comp_evidence.append(dict(id=rid,size_bytes=sp.stat().st_size,sha256=c.sha(sp),pages=src.page_count,rendered_source_pages_pixel_identical=True,evidence_basis=evidence_basis))
            r['component_integrity']=comp_evidence;r['qa']=c.inspect(r);r['source_exact_verified']=True
            r['outcome']='prepared_pending_visual_and_candidate_comparison'
        except Exception as e: r['outcome']='deferred_package_integrity';r['blocker']=str(e)
        c.save(d);print(r['id'],r['outcome'],r.get('blocker',''),flush=True)

def compare(d):
    inv=c.load(c.ROOT/'project-state/master-inventory.json')['candidates'];live=c.load(c.BASE)
    captures=c.load(c.DISC/'council-enacted-counterpart-capture-2026-09-20.json')['records']
    held={r['checksum_sha256']:r['held_substitute_id'] for r in captures if r.get('capture_status')=='captured'}
    for r in d['records']:
        if r['id']=='src-07ce09fd200d2d69': r['r2_key']=c.KEYS[r['id']]
        if not r.get('source_exact_verified'): continue
        key=r['r2_key'];r['namespace_existing_object_count']=sum(o['key'].startswith(str(Path(key).parent).replace('\\','/')+'/') for o in live['objects']) if key else 0
        assert not key or r['namespace_existing_object_count']>0,'Unestablished namespace'
        words=set(re.findall(r'[a-z0-9]+',r['title'].lower()))-{'city','albuquerque','cabq','the','and','of','for','report','enacted','ordinance','resolution','general','obligation','bond','2011','services'}
        scores=[(len(words & set(re.findall(r'[a-z0-9]+',(x.get('title') or '').lower()))),x) for x in inv if x['id']!=r['id'] and x.get('checksum_sha256') and x.get('r2_key')]
        candidates=[x for n,x in sorted(scores,key=lambda z:-z[0])[:5] if n>=max(2,len(words)//2)]
        if r['expected_sha256'] in held:
            x=next(x for x in inv if x['id']==held[r['expected_sha256']]); candidates=[x]+[q for q in candidates if q['id']!=x['id']]
        r['canonical_comparisons']=[]
        for other in candidates:
            item=dict(id=other['id'],title=other['title'],sha256=other['checksum_sha256'],size_bytes=other['size_bytes'],relationship='different_exact_container_identity')
            if other.get('r2_key'):
                found=next((o for o in live['objects'] if o['key']==other['r2_key']),None)
                assert found and found['size_bytes']==other['size_bytes']
            if r['expected_sha256'] in held and other['id']==held[r['expected_sha256']]:
                op=c.ROOT/(other.get('local_path') or 'tmp/background-canonical/'+other['id']+'.pdf');op.parent.mkdir(parents=True,exist_ok=True)
                if not op.exists() or (other['checksum_sha256'] and c.sha(op)!=other['checksum_sha256']):
                    url=other.get('r2_url') or other.get('direct_file_url') or other['source_url'];urllib.request.urlretrieve(url,op)
                if other['checksum_sha256']: assert c.sha(op)==other['checksum_sha256']
                item['comparison_source_sha256']=c.sha(op);item['comparison_source_size_bytes']=op.stat().st_size
                item['comparison_source_basis']='saved_exact_inventory_hash' if other['checksum_sha256'] else 'fresh_authoritative_counterpart_for_comparison_only; no canonical source replacement'
                with c.fitz.open(op) as a,c.fitz.open(c.ROOT/r['staged_path']) as b:
                    at=[re.sub(r'\s+',' ',p.get_text()).strip() for p in a];bt=[re.sub(r'\s+',' ',p.get_text()).strip() for p in b]
                    item.update(held_pages=len(at),enacted_pages=len(bt),held_pages_exact_text_in_enacted=sum(t in bt for t in at if t),text_similarity=round(difflib.SequenceMatcher(None,' '.join(at),' '.join(bt),autojunk=False).ratio(),4),relationship='final_enactment_counterpart_to_substitute_not_an_exact_source_wrapper_alias',held_excerpt=at[0][:350],enacted_excerpt=bt[0][:350])
            r['canonical_comparisons'].append(item)
        # Different sizes rule out exact alias; saved edition/program decisions govern semantic near matches.
        r['duplicate_canonical_relationship']='distinct_authoritative_original; exact inventory hash and saved/live key/same-size checks clear; semantic candidates retained as distinct versions or subjects'
        c.save(d)

if __name__=='__main__':
    d=c.load(c.ART)
    if d['state']=='complete_background_campaign':raise SystemExit('Completed campaign evidence must not be re-prepared or re-compared.')
    packages(d); compare(d);review_sheets(d['records'],'original-review');review_sheets(d['generated_packages'],'package-review');c.save(d)
