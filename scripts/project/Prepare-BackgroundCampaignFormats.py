#!/usr/bin/env python3
"""Fresh original identity and format-specific inspection; never converts archive bytes."""
import concurrent.futures, hashlib, json, runpy, sys, zipfile
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tmp/pgs-pdf-deps'))
import pymupdf as fitz
from PIL import Image,ImageDraw
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context=(c[k] for k in ['ROOT','load','save','rel','context'])
source=runpy.run_path(str(Path(__file__).with_name('Prepare-LargeOrdinaryCampaign.py')))['source_get']
path,d=context();s=load(ROOT/d['selection_artifact']);qs={q['id']:q for q in s['all_pending_records']}
stage=ROOT/'research/staging'/d['campaign_id'];qa_dir=ROOT/'tmp'/d['campaign_id'];stage.mkdir(parents=True,exist_ok=True);qa_dir.mkdir(parents=True,exist_ok=True)
mode=sys.argv[1] if len(sys.argv)>1 else 'fetch'
def fetch(r):
 rid=r['id'];q=qs[rid];rec=q['saved_evidence'];url=rec.get('raw_file_url') or rec['authoritative_url'].removesuffix('/view')
 ext=Path(urlsplit(url).path).suffix.lower();ext=ext if ext in ['.doc','.docx','.pptx','.rtf','.png','.pdf','.json'] else '.bin'
 p=stage/(rid+ext);data,get=source(url,p)
 if ext=='.bin':
  if data.startswith(b'PK'):
   with zipfile.ZipFile(p) as z:
    ext='.docx' if 'word/document.xml' in z.namelist() else '.pptx' if 'ppt/presentation.xml' in z.namelist() else '.bin'
  elif data.startswith(b'\x89PNG'):ext='.png'
  elif data.startswith(b'%PDF-'):ext='.pdf'
  elif data.startswith(b'\xd0\xcf'):ext='.doc'
  p=stage/(rid+ext);p.write_bytes(data)
 assert (len(data),get['checksum_sha256'])==(rec['size_bytes'],rec['checksum_sha256']),'Saved/current source identity mismatch; preserve historical bytes'
 qa=dict(source_exact_verified=True,source_GET=get,staged_path=rel(p),size_bytes=len(data),checksum_sha256=get['checksum_sha256'],container=ext[1:].upper(),page_count=0,word_count=None,representative_visual_qa='pending_agent_inspection')
 if ext in ['.doc','.docx','.pptx','.rtf']:qa['inspection_pdf']=rel(qa_dir/(rid+'.pdf'))
 elif ext=='.png':
  im=Image.open(p);im.verify();qa['representative_images']=[rel(p)];qa['image_dimensions']=list(Image.open(p).size)
 else:
  text=data.decode('utf-8',errors='replace');t=stage/(rid+'.txt');t.write_text(text,encoding='utf-8');qa.update(full_text_path=rel(t),word_count=len(text.split()))
 r.update(fresh_source_qa=qa,disposition=rec['recommended_status'],rationale=rec.get('description') or rec.get('exclusion_reason'),quality_assessment=dict(visual_inspection='pending',measured_page_count=0,intended_publication_form='none pending review'),canonical_candidate_id=rec.get('canonical_id'),error=None)
 return r
def render_inspection(r):
 qa=r['fresh_source_qa'];p=ROOT/qa['inspection_pdf']
 with fitz.open(p) as doc:
  assert not doc.needs_pass and not doc.is_repaired
  text='\n'.join(page.get_text() for page in doc);tp=stage/(r['id']+'.txt');tp.write_text(text,encoding='utf-8')
  rendered=[];reps=[];selected={0,doc.page_count//2,doc.page_count-1}
  for i,page in enumerate(doc):
   pix=page.get_pixmap(matrix=fitz.Matrix(.7,.7),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
   if i in selected:
    rp=qa_dir/f"{r['id']}-page-{i+1}.png";im.save(rp);reps.append(rel(rp))
   im.thumbnail((330,460));rendered.append((i+1,im))
  sheets=[]
  for start in range(0,len(rendered),12):
   batch=rendered[start:start+12];im=Image.new('RGB',(1050,((len(batch)+2)//3)*495),'#eeeeee');draw=ImageDraw.Draw(im)
   for j,(num,thumb) in enumerate(batch):
    x=(j%3)*350;y=(j//3)*495;draw.text((x+5,y+3),str(num),fill='black');im.paste(thumb,(x+5,y+22))
   sp=qa_dir/f"{r['id']}-contact-{start//12+1}.jpg";im.save(sp,quality=88);sheets.append(rel(sp))
  qa.update(page_count=doc.page_count,word_count=len(text.split()),rendered_pages=doc.page_count,full_text_path=rel(tp),contact_sheets=sheets,representative_images=reps,inspection_only_conversion=True,original_unchanged=True)
  r['quality_assessment'].update(measured_page_count=doc.page_count,measured_word_count=len(text.split()))
for f in s['candidate_families']:
 p=ROOT/f['evidence_artifact'];fam=load(p)
 if mode=='fetch':
  tasks=[r for r in fam['records'] if (not r.get('fresh_source_qa') and r.get('error')) or (r.get('fresh_source_qa') or {}).get('container')=='BIN']
  if not tasks:continue
  def safe(r):
   try:return fetch(r)
   except Exception as e:r['error']=str(e);return r
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   updated={r['id']:r for r in pool.map(safe,tasks)}
  fam['records']=[updated.get(r['id'],r) for r in fam['records']]
 elif mode=='render':
  for r in fam['records']:
   qa=r.get('fresh_source_qa') or {}
   if qa.get('inspection_pdf') and not qa.get('contact_sheets'):
    try:render_inspection(r)
    except Exception as e:r['error']=str(e)
 save(p,fam);print(f['family_id'],mode,flush=True)
requests=[r['fresh_source_qa'] for f in s['candidate_families'] for r in load(ROOT/f['evidence_artifact'])['records'] if (r.get('fresh_source_qa') or {}).get('inspection_pdf')]
save(qa_dir/'office-render-requests.json',requests)
