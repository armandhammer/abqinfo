import json,hashlib,concurrent.futures
from pathlib import Path
from urllib.request import Request,urlopen
p=Path('project-state/discovery/go-capital-quality-remediation-2026-09-27');rows=json.loads((p/'public-byte-measurements.json').read_text(encoding='utf-8'))
def verify(r):
    try:
        with urlopen(Request(r['source_url'],headers={'User-Agent':'ABQInfo original source verification'}),timeout=75) as response:
            b=response.read();return {'id':r['id'],'url':r['source_url'],'http_status':response.status,'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'matches_preserved_archive':len(b)==r['size_bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']}
    except Exception as e:return {'id':r['id'],'url':r['source_url'],'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(verify,rows))
(p/'official-link-verification.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');print('Official exact matches',sum(r.get('matches_preserved_archive',False) for r in results),'/',len(results));print([r for r in results if not r.get('matches_preserved_archive')])
