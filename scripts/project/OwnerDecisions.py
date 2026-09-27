"""Durable application of the four explicit September 26 owner decisions."""
import json, hashlib, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TASK='owner-decisions-2026-09-26'
F=ROOT/'project-state/discovery'/TASK
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');t.replace(p)
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,encoding='utf-8').strip()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def start():
 assert not (F/'authorization.json').exists()
 inv=load(ROOT/'project-state/master-inventory.json');packages=load(ROOT/'project-state/discovery/human-review-reassessment-2026-09-26/owner-packages.json')['packages'];ids=[i for p in packages for i in p['affected_record_ids']]
 assert len(ids)==11 and set(ids)=={r['id'] for r in inv['candidates'] if r['status']=='requires human review'}
 save(F/'authorization.json',dict(task='Owner explicitly requested application of four decisions, eligible unchanged-original R2 archives under standing limits, full validation, background integration and branch reconciliation.',baseline_commit=git('rev-parse','HEAD'),content_tree=git('rev-parse','HEAD:content'),allowed_ids=sorted(ids),baseline_row_digests={r['id']:digest(r) for r in inv['candidates']},maximum_object_bytes=150000000,maximum_storage_bytes=13000000000,state='owner_decisions_recorded',decisions={'art-advocacy-primary-sources':'Retain all three as attributed historical evidence; preserve authorship/viewpoint; never official City findings or approved minutes.','dpm-historical-drafts':'Retain all six as historical proposal/draft series; preserve dates, draft/proposed status and relationships to adopted records; never current or enacted standards.','fiber-correspondence':'Exclude from public-facing collection; preserve research/provenance; no original, derivative or summary publication.','wireless-checklist':'Exclude.'}))
 save(F/'baseline-records.json',[r for r in inv['candidates'] if r['id'] in ids]);save(F/'baseline-owner-packages.json',packages);save(F/'baseline-followup-queue.json',load(ROOT/'project-state/discovery/codex-human-review-followup-queue.json'))
def inspect():
 sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
 from PIL import Image,ImageDraw
 ret=load(ROOT/'project-state/discovery/human-review-reassessment-2026-09-26/retrievals.json')['records'];out=[]
 for r in load(F/'baseline-records.json'):
  if r['id'] in ['src-05b68a5758490499','src-333e4b4b3970edc1']:continue
  source=r.get('local_path'); evidence='Saved official/contributed original, prior visual review and preserved source identity.'
  if not source:
   x=next(x for x in ret if x['id']==r['id'] and x.get('page_count'));source=x['saved_source'];evidence='Official-source retrieval in human-review-reassessment-2026-09-26/retrievals.json'
  data=(ROOT/source).read_bytes();sha=hashlib.sha256(data).hexdigest()
  if r.get('checksum_sha256'):assert sha==r['checksum_sha256'] and len(data)==r['size_bytes']
  d=pymupdf.open(stream=data,filetype='pdf');text='\n'.join(p.get_text() for p in d)
  path=ROOT/'tmp/pdfs'/TASK/(r['id']+'.png');path.parent.mkdir(parents=True,exist_ok=True)
  sheet=Image.new('RGB',(1200,((len(d)+3)//4)*420),'white');draw=ImageDraw.Draw(sheet)
  for n,p in enumerate(d):
   pix=p.get_pixmap(matrix=pymupdf.Matrix(min(285/p.rect.width,380/p.rect.height),min(285/p.rect.width,380/p.rect.height)),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);x=(n%4)*300;y=(n//4)*420;sheet.paste(im,(x,y));draw.text((x,y+390),f'Page {n+1}',fill='black')
  sheet.save(path)
  out.append(dict(id=r['id'],source_path=source,size_bytes=len(data),sha256=sha,page_count=len(d),word_count=len(text.split()),text_excerpt=text[:4500],visual_sheet=path.relative_to(ROOT).as_posix(),provenance_evidence=evidence))
 save(F/'inspection.json',out)
 print('Inspected',len(out),'originals')
if __name__=='__main__':globals()[sys.argv[1]]()
