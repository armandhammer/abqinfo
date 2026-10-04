import hashlib,sys,urllib.request
from pathlib import Path
sys.path.insert(0,'scripts/project')
import OwnerResources20261004 as S
p=S.prefix(S.A); out=S.G.ROOT/'research/staging/sunport-exact-archive-2026-10-04/original.pdf';out.parent.mkdir(parents=True,exist_ok=True)
req=urllib.request.Request(S.SOURCE,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
h=hashlib.sha256();n=0
with urllib.request.urlopen(req,timeout=60) as r,out.open('wb') as f:
    receipt=dict(method='GET',source_url=S.SOURCE,final_url=r.geturl(),http_status=r.status,retrieved_at_utc=S.now(),response_headers={k:v for k,v in r.headers.items() if k.lower()!='set-cookie'})
    while b:=r.read(1024*1024):f.write(b);h.update(b);n+=len(b)
assert n==280024902 and h.hexdigest()==S.SHA,(n,h.hexdigest())
sys.path.insert(0,'tmp/pdfs/pydeps');import fitz
with fitz.open(out) as d:assert len(d)==601;receipt['page_count']=len(d)
receipt.update(size_bytes=n,sha256=h.hexdigest(),complete_response=True,unchanged_exact_original=True,local_path=out.relative_to(S.G.ROOT).as_posix())
S.save(p+'source-verification.json',receipt)
print(receipt)
