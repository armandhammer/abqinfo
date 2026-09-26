#!/usr/bin/env python3
"""Resumable, immutable authoritative source QA; no inventory or R2 mutation."""
import argparse, hashlib, json, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tmp/pgs-pdf-deps'))
from PIL import Image, ImageDraw
import pymupdf as fitz
import runpy
common = runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,SELECTION,CAMPAIGN = (common[k] for k in ['ROOT','DISC','DATE','SELECTION','CAMPAIGN'])
load,save = common['load'],common['save']
STAGE=ROOT/'research/staging/ordinary-large-campaign-2026-09-26'
QA=ROOT/'tmp/ordinary-large-campaign-qa-2026-09-26'

def now():return datetime.now(timezone.utc).isoformat()
def rel(p):return p.relative_to(ROOT).as_posix()

def source_get(url,path=None):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo authoritative-source identity review)','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as response:
        data=response.read()
        evidence=dict(http_status=response.status,requested_url=url,final_url=response.url,content_type=response.headers.get('Content-Type'),verified_at=now(),size_bytes=len(data),checksum_sha256=hashlib.sha256(data).hexdigest(),leading_bytes=data[:16].hex())
    if path:path.write_bytes(data)
    return data,evidence

def inspect(q):
    r=q['saved_evidence'];rid=q['id'];kind=r['content_kind']
    if kind=='HTML':
        return dict(id=rid,source_qa='saved_full_GET_container_and_content_analysis_reused',saved_evidence=r,source_provenance_artifacts=q['research_artifacts'],disposition='excluded',rationale=r['exclusion_reason'],quality_assessment={'measured_container':'HTML','measured_size_bytes':r['size_bytes'],'saved_sha256':r['checksum_sha256'],'actual_function':r.get('what_it_is'),'standalone_public_value':'No separate static record: the saved review identifies a navigation, contact, directory, general live information or news delivery rather than an original plan, report, regulation or dataset. Retained document links and meaningful live services remain independently reviewable.','intended_publication_form':'none; excluded crawler row','visual_inspection':'not applicable to live HTML candidate; no static original'},mission_scope_assessment={'assessed_at':now(),'geographic_institutional_scope':q['host'],'specific_albuquerque_connection':'City/local agency live information or navigation candidate; origin alone does not establish useful separate archival record.','abqinfo_public_information_value':'The specific candidate function recorded in saved evidence supplies no independent archival public-information value beyond the originating live page.','general_context_exclusion_test':'The source is retained for discovery; no distinct substantive archival document or qualifying interactive public dataset is established by this row.','final_scope_decision':'excluded','substantive_rationale':r['exclusion_reason']},archival_readiness='not eligible: excluded HTML discovery/navigation row',proposed_canonical_page=None)
    ext='jpg' if kind=='JPEG' else 'pdf'
    p=STAGE/(rid+'.'+ext)
    url=r.get('raw_file_url') or r['authoritative_url'].removesuffix('/view')
    data,get=source_get(url,p)
    assert (len(data),hashlib.sha256(data).hexdigest())==(r['size_bytes'],r['checksum_sha256']),'Current authoritative bytes differ from saved identity; preserve historical evidence and defer'
    qa=dict(source_exact_verified=True,source_GET=get,staged_path=rel(p),size_bytes=len(data),checksum_sha256=get['checksum_sha256'])
    if kind=='JPEG':
        im=Image.open(p);im.verify();im=Image.open(p);qa.update(container='JPEG',image_dimensions=list(im.size),representative_images=[rel(p)],page_count=0,rendered_pages=0,full_text='Map image; no invented OCR text',word_count=None)
    else:
        assert data.startswith(b'%PDF-'),'Authoritative GET is not PDF'
        with fitz.open(p) as doc:
            assert not doc.needs_pass and not doc.is_repaired,'Encrypted or repaired container requires separate review'
            texts=[page.get_text() for page in doc]
            text='\n'.join(texts);(STAGE/(rid+'.txt')).write_text(text,encoding='utf-8')
            pages=doc.page_count; selected=sorted({0,pages//2,pages-1})
            render_all=r['recommended_status']=='approved for addition' or pages<=12
            render_indices=range(pages) if render_all else selected
            rendered=[];low=[]
            for i in render_indices:
                pix=doc[i].get_pixmap(matrix=fitz.Matrix(.6,.6),alpha=False)
                img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                # Flag nearly empty pages independently of the text layer.
                small=img.convert('L').resize((100,100));ink=sum(v<235 for v in small.getdata())/10000
                if ink<.002:low.append(i+1)
                thumb=img.copy();thumb.thumbnail((330,460));rendered.append((i+1,thumb))
                if i in selected or ink<.002:
                    img.save(QA/f'{rid}-page-{i+1}.png')
            sheets=[]
            for start in range(0,len(rendered),12):
                batch=rendered[start:start+12];canvas=Image.new('RGB',(3*350,((len(batch)+2)//3)*495),'#e8e8e8');draw=ImageDraw.Draw(canvas)
                for j,(page,img) in enumerate(batch):
                    x=(j%3)*350;y=(j//3)*495;draw.text((x+8,y+5),rid+' p'+str(page),fill='black');canvas.paste(img,(x+8,y+25))
                path=QA/f'{rid}-contact-{start//12+1}.jpg';canvas.save(path,quality=90);sheets.append(rel(path))
            qa.update(container='PDF',structural_result='opens_without_password_or_repair',page_count=pages,word_count=len(text.split()),text_layer_pages=sum(bool(t.strip()) for t in texts),rendered_pages=len(rendered),low_ink_pages=low,contact_sheets=sheets,representative_images=[rel(QA/f'{rid}-page-{i+1}.png') for i in selected],full_text_path=rel(STAGE/(rid+'.txt')),text_excerpts={str(i+1):texts[i][:2000] for i in selected},metadata=doc.metadata)
    qa['representative_visual_qa']='pending_agent_inspection'
    return dict(id=rid,saved_evidence=r,source_provenance_artifacts=q['research_artifacts'],fresh_source_qa=qa,disposition=r['recommended_status'],rationale=r.get('exclusion_reason') or r.get('relationship') or r.get('description'),canonical_candidate_id=r.get('canonical_id'),quality_assessment={'visual_inspection':'pending','actual_function':'pending full text and rendered-page review','measured_page_count':qa['page_count'],'measured_word_count':qa.get('word_count'),'intended_publication_form':'no publication in this campaign; original preserved if approved'},mission_scope_assessment=None,archival_readiness='pending source/content/duplicate/mission review',proposed_canonical_page=r.get('proposed_canonical_page'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--start',type=int,default=1);parser.add_argument('--end',type=int,default=999);parser.add_argument('--families');a=parser.parse_args()
    s=load(SELECTION);qs={q['id']:q for q in s['all_pending_records']};d=load(CAMPAIGN)
    STAGE.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    for f in s['candidate_families']:
        if not a.start<=f['order']<=a.end:continue
        if a.families and f['order'] not in {int(x) for x in a.families.split(',')}:continue
        path=DISC/f"ordinary-large-campaign-{f['family_id']}-{DATE}.json"
        existing=load(path) if path.exists() else dict(schema_version=1,artifact_type='ordinary_large_campaign_family_evidence',family_id=f['family_id'],family=f['family'],scope_ids=f['candidate_ids'],methods='Saved full-document research reused; every static source fresh full GET checked by exact size/hash; PDF text extracted from every page, opening/middle/ending rendered; all pages rendered for approval candidates and short files. HTML uses saved full-GET evidence with current source-health sampling.',records=[],visitor_visible_content_changed=False)
        complete={r['id'] for r in existing['records']}
        for rid in f['candidate_ids']:
            if rid in complete:continue
            try:
                rec=inspect(qs[rid]);existing['records'].append(rec)
            except Exception as e:
                existing['records'].append(dict(id=rid,disposition='deferred',error=str(e),saved_evidence=qs[rid]['saved_evidence'],historical_source_evidence_preserved=True))
            save(path,existing)
        if all(qs[i]['candidate_container_type']=='HTML' for i in f['candidate_ids']) and 'source_health_sample' not in existing:
            try:
                _,health=source_get(qs[f['candidate_ids'][0]]['source_url']);existing['source_health_sample']=health
            except Exception as e:existing['source_health_sample']={'error':str(e),'checked_at':now(),'disposition_basis':'historical measured evidence; source currentness not asserted'}
            save(path,existing)
        existing['state']='source_evidence_prepared_pending_review';save(path,existing)
        print(f['family_id'],len(existing['records']),'sources prepared',flush=True)

if __name__=='__main__':main()
