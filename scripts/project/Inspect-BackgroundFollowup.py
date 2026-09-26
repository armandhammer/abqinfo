"""Measure unchanged held and recovered PDFs and render comparison pages."""
import hashlib,sys
from pathlib import Path
from BackgroundFollowup import ROOT,F,load,save
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'))
import pymupdf
out=[];dest=ROOT/'tmp/pdfs/background-followup';dest.mkdir(parents=True,exist_ok=True)
for r in load(F/'baseline-records.json'):
 if r['status']!='pending review':continue
 sources=[]
 if r.get('local_path') and (ROOT/r['local_path']).exists():sources.append(('held',ROOT/r['local_path']))
 sources += [('fresh',ROOT/x['saved_source']) for x in load(F/'retrievals.json')['records'] if x.get('id')==r['id'] and x.get('page_count')]
 for label,p in sources:
  with pymupdf.open(p) as d:
   t='\n'.join(p.get_text() for p in d);record=dict(id=r['id'],label=label,path=str(p.relative_to(ROOT)),size_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(d),words=len(t.split()),text_sha256=hashlib.sha256(t.encode()).hexdigest(),opening=t[:4500],ending=t[-2500:]);out.append(record)
   p.with_suffix('.txt').write_text(t,encoding='utf-8')
   for page in sorted(set([0,len(d)//2,len(d)-1])):d[page].get_pixmap(matrix=pymupdf.Matrix(.8,.8)).save(dest/(r['id']+'-'+label+'-'+str(page+1)+'.png'))
  print(r['id'],label,record['pages'],record['words'],record['sha256'][:12],record['opening'][:180].replace('\n',' '))
save(F/'pdf-inspection.json',out)
