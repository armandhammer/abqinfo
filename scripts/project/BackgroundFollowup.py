"""Durable owner-authorized follow-up evidence and exact population guard."""
import argparse, concurrent.futures, hashlib, json, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TASK='background-followup-2026-09-26'
F=ROOT/'project-state/discovery'/TASK
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');t.replace(p)
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,encoding='utf-8').strip()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def fetch(t):
 r=dict(t,retrieved_at=datetime.now(timezone.utc).isoformat())
 try:
  with urllib.request.urlopen(urllib.request.Request(t['url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo official-source verification)'}),timeout=45) as q:
   data=q.read(150000001);r.update(http_status=q.status,final_url=q.url,content_type=q.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),truncated=len(data)==150000001)
  p=ROOT/'research/staging'/TASK/(t.get('id','source')+'-'+hashlib.sha256(t['url'].encode()).hexdigest()[:12]+'.bin');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);r['saved_source']=p.relative_to(ROOT).as_posix()
  if data.startswith(b'%PDF') and not r['truncated']:
   sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
   with pymupdf.open(stream=data,filetype='pdf') as d:
    text='\n'.join(p.get_text() for p in d);r.update(page_count=len(d),word_count=len(text.split()),text_excerpt=text[:16000]);p.with_suffix('.txt').write_text(text,encoding='utf-8')
  elif 'html' in str(r['content_type']):
   import importlib.util
   s=importlib.util.spec_from_file_location('recover',ROOT/'scripts/project/Reassess-HumanReviewSources.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
   from urllib.parse import urljoin
   h=data.decode('utf-8',errors='replace');parser=m.Links();parser.feed(h);r['links']=[dict(url=urljoin(r['final_url'],u),label=l.strip()) for u,l in parser.links]
  elif 'json' in str(r['content_type']):r['payload']=json.loads(data)
 except Exception as e:r['error']=str(e)
 return r
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['start','fetch']);p.add_argument('--tasks');a=p.parse_args()
 if a.action=='start':
  assert not (F/'authorization.json').exists(),'Do not reset a task'
  inv=load(ROOT/'project-state/master-inventory.json');q=load(ROOT/'project-state/discovery/codex-human-review-followup-queue.json');approved=[r for r in inv['candidates'] if r['status']=='approved for addition'];allowed={r['id'] for r in q['records']}|{r['id'] for r in approved}
  save(F/'authorization.json',dict(task='Owner requested deterministic Codex follow-up exhaustion, eligible approved-original archives under standing R2 policy, full validation, background integration and branch reconciliation. Four owner packages unchanged; no inferred legal outcomes or visible changes.',baseline_commit=git('rev-parse','HEAD'),content_tree=git('rev-parse','HEAD:content'),allowed_ids=sorted(allowed),followup_ids=[r['id'] for r in q['records']],approved_ids=[r['id'] for r in approved],baseline_row_digests={r['id']:digest(r) for r in inv['candidates']},maximum_object_bytes=150000000,maximum_storage_bytes=13000000000,state='evidence_in_progress'))
  save(F/'baseline-records.json',[r for r in inv['candidates'] if r['id'] in allowed]);save(F/'baseline-followup-queue.json',q);save(F/'owner-packages-baseline.json',load(ROOT/'project-state/discovery/consolidated-human-review-queue.json')['packages']);print('Locked',len(q['records']),'follow-ups and',len(approved),'approvals')
 else:
  out=F/'retrievals.json';e=load(out) if out.exists() else dict(records=[]);done={r['url'] for r in e['records'] if r.get('http_status')==200};tasks=[t for t in load(ROOT/a.tasks) if t['url'] not in done]
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
   for r in pool.map(fetch,tasks):e['records'].append(r);save(out,e);print(r.get('id'),r.get('http_status'),r.get('size_bytes'),r.get('error',''),flush=True)
if __name__=='__main__':main()
