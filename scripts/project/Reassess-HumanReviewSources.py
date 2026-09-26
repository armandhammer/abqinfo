"""Bounded, resumable read-only recovery for the locked September 26 review."""
import concurrent.futures, hashlib, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / 'project-state/discovery/human-review-reassessment-2026-09-26'
STAGING = ROOT / 'research/staging/human-review-reassessment-2026-09-26'
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.active=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'): self.active=[a['href'],'']
    def handle_data(self, data):
        if self.active: self.active[1]+=data
    def handle_endtag(self, tag):
        if tag=='a' and self.active: self.links.append(self.active); self.active=None
def fetch(task):
    result=dict(task, retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        request=urllib.request.Request(task['url'], headers={'User-Agent':'Mozilla/5.0 (ABQInfo bounded official-source review)'})
        with urllib.request.urlopen(request, timeout=25) as response:
            maximum=150000001 if task['id'] in ['src-4996854ae4e1a349','src-a738fd67bc6abac6','src-c7fcd58b9998999c'] else 30000001
            data=response.read(maximum)
            result.update(http_status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'),size_bytes=len(data), truncated=len(data)==maximum, sha256=hashlib.sha256(data).hexdigest())
        name=task['id']+'-'+hashlib.sha256(task['url'].encode()).hexdigest()[:8]+'.bin'
        STAGING.mkdir(parents=True,exist_ok=True); dest=STAGING/name; dest.write_bytes(data)
        result['saved_source']=dest.relative_to(ROOT).as_posix()
        if data.startswith(b'%PDF') and not result['truncated']:
            import sys
            sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'))
            import pymupdf
            with pymupdf.open(stream=data,filetype='pdf') as doc:
                text='\n'.join(p.get_text() for p in doc)
                result.update(page_count=doc.page_count,word_count=len(text.split()),is_repaired=doc.is_repaired,text_excerpt=text[:10000])
                dest.with_suffix('.txt').write_text(text,encoding='utf-8')
        elif 'html' in str(result['content_type']).lower():
            body=data.decode('utf-8',errors='replace'); parser=Links();parser.feed(body)
            result['title']=(re.findall(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)+[''])[0]
            result['links']=[dict(url=urljoin(result['final_url'],u),label=t.strip()) for u,t in parser.links if urlparse(urljoin(result['final_url'],u)).scheme in ['http','https']]
            body=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',body,flags=re.I|re.S)
            result['text_excerpt']=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',body))[:22000]
    except Exception as e: result['error']=str(e)
    return result
def main():
    baseline=json.loads((FOLDER/'baseline-queue.json').read_text(encoding='utf-8'))
    output=FOLDER/'retrievals.json'; evidence=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {'records':[]}
    done={r['url'] for r in evidence['records']}; tasks=[]
    for package in baseline['packages']:
        for row in package['records']:
            urls=[]
            for key in ['direct_file_url','source_url','parent_url']:
                u=row.get(key)
                if u and u.startswith(('http://','https://')) and 'files.abqinfo.com' not in u and u not in done and u not in urls:
                    urls.append(u);done.add(u)
                    tasks.append(dict(id=row['id'],package_id=package['package_id'],url=u))
    followups=FOLDER/'followup-tasks.json'
    if followups.exists():
        for t in json.loads(followups.read_text(encoding='utf-8')):
            if t['url'] not in done:tasks.append(t);done.add(t['url'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for future in concurrent.futures.as_completed([pool.submit(fetch,t) for t in tasks]):
            result=future.result()
            evidence['records'].append(result);save(output,evidence)
            print(result['id'],result.get('http_status'),result.get('size_bytes'),result.get('error',''),flush=True)
if __name__=='__main__':main()
