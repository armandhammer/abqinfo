#!/usr/bin/env python3
"""Bounded public retrieval evidence for live deliveries, meeting checks and blockers."""
import concurrent.futures, hashlib, json, re, runpy, sys, urllib.request
from pathlib import Path
from urllib.parse import urljoin
from html.parser import HTMLParser
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context,now=(c[k] for k in ['ROOT','load','save','rel','context','now'])
path,d=context();s=load(ROOT/d['selection_artifact']);folder=path.parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a' and a.get('href'):self.current=[a['href'],'']
  if tag in ['iframe','embed'] and a.get('src'):self.links.append([a['src'],'EMBED'])
 def handle_data(self,data):
  if self.current:self.current[1]+=data
 def handle_endtag(self,tag):
  if tag=='a' and self.current:self.links.append(self.current);self.current=None
tasks=[dict(id=q['id'],url=q['saved_evidence'].get('raw_file_url') or q['source_url']) for q in s['all_pending_records'] if q['saved_evidence']['content_kind']=='HTML']
rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
q=load(ROOT/d['source_queue_artifact'])
tasks += [dict(id=i,url=rows[i]['source_url'].removesuffix('/view')) for i in q['source_or_structural_blocked_pending_ids']]
tasks += [dict(id='official-edact-meeting-index',url='https://www.cabq.gov/economicdevelopment/economic-development-action-account-edact'),dict(id='official-climate-meeting-index',url='https://www.cabq.gov/sustainability/sustainability-resources'),dict(id='official-mprab-index',url='https://www.cabq.gov/parksandrecreation/our-department/boards-commissions/metropolitan-parks-recreation-advisory-board')]
def fetch(task):
 try:
  request=urllib.request.Request(task['url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo bounded source review)'})
  with urllib.request.urlopen(request,timeout=35) as response:
   data=response.read();out=dict(task,http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),retrieved_at=now())
  p=ROOT/'research/staging'/d['campaign_id']/(task['id']+'-current-source.bin');p.write_bytes(data);out['saved_source']=rel(p)
  if data.startswith(b'%PDF'):
   sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
   with pymupdf.open(stream=data,filetype='pdf') as doc:out.update(pages=doc.page_count,needs_password=doc.needs_pass,is_repaired=doc.is_repaired)
  else:
   text=data.decode('utf-8',errors='replace');parser=Links();parser.feed(text);out['links']=[dict(url=urljoin(out['final_url'],u),label=t.strip()) for u,t in parser.links]
   out['title']=(re.findall(r'<title[^>]*>(.*?)</title>',text,re.S|re.I)+[''])[0]
   out['text_excerpt']=re.sub(r'<[^>]+>',' ',text)[-14000:]
  return out
 except Exception as e:return dict(task,error=str(e),retrieved_at=now())
evidence=folder/'bounded-source-investigation.json';existing=load(evidence) if evidence.exists() else dict(schema_version=1,records=[])
done={r['id'] for r in existing['records']}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for r in pool.map(fetch,[t for t in tasks if t['id'] not in done]):
  existing['records'].append(r);save(evidence,existing);print(r['id'],r.get('http_status'),r.get('error',''),flush=True)
