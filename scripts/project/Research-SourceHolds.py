"""Read-only streamed source retrieval with exact response receipts."""
import argparse, hashlib, json, re, sys, urllib.request, urllib.error, gzip, collections, difflib, math
from pathlib import Path
import SourceHoldResolution as S

SCRATCH=S.G.ROOT/'research/staging/source-hold-resolution-2026-10-04'
def retrieve(url,label,headers=None):
    SCRATCH.mkdir(parents=True,exist_ok=True)
    prior=list((S.G.ROOT/S.P).glob('retrieval-*.json'))
    n=max([int(p.stem.split('-')[1]) for p in prior],default=0)+1
    receipt=dict(requested_url=url,requested_at_utc=S.now(),label=label,method='GET',request_headers=headers or {},historical_archive_evidence=('web.archive.org' in url or 'archive.org/wayback' in url))
    while True:
        try:
            S.G.write_once(S.P+f'retrieval-{n}.json',dict(receipt,state='request_intent'))
            break
        except FileExistsError:n+=1
    path=SCRATCH/label; h=hashlib.sha256();size=0
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo provenance research)',**(headers or {})})
        redirects=[]
        class Redirects(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,req,fp,code,msg,headers,newurl):
                redirects.append(dict(from_url=req.full_url,status=code,to_url=newurl))
                return super().redirect_request(req,fp,code,msg,headers,newurl)
        try: response=urllib.request.build_opener(Redirects()).open(req,timeout=60)
        except urllib.error.HTTPError as e: response=e
        receipt.update(final_url=response.geturl(),http_status=response.status,content_type=response.headers.get('Content-Type'),response_headers={k:v for k,v in response.headers.items() if k.lower()!='set-cookie'},redirect_chain=redirects)
        with response, path.open('wb') as f:
            while b:=response.read(1024*1024):
                size+=len(b)
                if size>350000000:raise ValueError('Read-only response safety ceiling exceeded')
                f.write(b);h.update(b)
        receipt.update(exact_byte_length=size,sha256=h.hexdigest(),local_path=path.relative_to(S.G.ROOT).as_posix(),complete_response=True)
        if size and ('pdf' in (receipt['content_type'] or '') or path.read_bytes()[:5]==b'%PDF-'):
            try:
                sys.path.insert(0,str(S.G.ROOT/'tmp/pdfs/pydeps')); import fitz
                with fitz.open(path) as doc:
                    receipt.update(pdf_valid=True,pdf_pages=len(doc),pdf_metadata=doc.metadata,pdf_repaired=doc.is_repaired,pdf_encrypted=doc.is_encrypted)
            except Exception as e:receipt.update(pdf_valid=False,pdf_error=str(e))
        elif size<5000000:
            body=path.read_bytes().decode('utf-8',errors='replace')
            out=S.P+f'evidence-{n}.txt';(S.G.ROOT/out).write_text(body,encoding='utf-8',newline='\n');receipt['preserved_response_text']=out
    except Exception as e:receipt.update(error=str(e),complete_response=False,partial_byte_length=size)
    S.save(S.P+f'retrieval-{n}.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))
    return receipt
def compare():
    sys.path.insert(0,str(S.G.ROOT/'tmp/pdfs/pydeps'));import pymupdf as fitz
    paths={'printing':'research/staging/ordinary-second-large-campaign-2026-09-26/src-1f9cf39555e7be6f.pdf','onbase':'research/staging/source-hold-resolution-2026-10-04/onbase-12246971.pdf','summary':'research/staging/source-hold-resolution-2026-10-04/onbase-12246972.pdf','legistar':'research/staging/source-hold-resolution-2026-10-04/legistar-8032966.pdf'}
    docs={k:fitz.open(S.G.ROOT/p) for k,p in paths.items() if (S.G.ROOT/p).is_file()}
    texts={k:[p.get_text() for p in d] for k,d in docs.items()}
    def norm(t):return re.sub(r'\s+',' ',t).strip()
    def tokens(t):return re.findall(r'[a-z0-9]+',t.lower())
    result=dict(created_at_utc=S.now(),method='Full page text extraction, per-page dimensions and text hashes; exact token page matches and weighted token-overlap candidate alignment with sequence comparison. All pages raster-rendered for validity; representative pages visually compared. No PDF modification.',documents={})
    for k,d in docs.items():
        p=S.G.ROOT/paths[k];rows=[]
        for i,page in enumerate(d):
            pix=page.get_pixmap(matrix=fitz.Matrix(0.35,0.35),alpha=False)
            t=texts[k][i]
            rows.append(dict(page=i+1,width=page.rect.width,height=page.rect.height,word_count=len(t.split()),text_sha256=hashlib.sha256(norm(t).encode()).hexdigest(),raster_sha256=hashlib.sha256(pix.samples).hexdigest(),text_opening=norm(t)[:100],text_ending=norm(t)[-100:]))
        result['documents'][k]=dict(path=paths[k],bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),page_count=len(d),metadata=d.metadata,word_count=sum(r['word_count'] for r in rows),all_pages_rendered=True,pages=rows)
        print(k,len(d),result['documents'][k]['word_count'],flush=True)
    def align(a,b):
        aa=[tokens(t) for t in texts[a]];bb=[tokens(t) for t in texts[b]]
        sets=[set(t) for t in bb];df=collections.Counter(w for ss in sets for w in ss)
        weights={w:math.log(1+len(bb)/(n+1)) for w,n in df.items()}
        rows=[]
        exact={norm(t):i for i,t in enumerate(texts[b]) if len(tokens(t))>8}
        for i,t in enumerate(aa):
            if len(t)<9:rows.append(dict(source_page=i+1,kind='sparse_or_blank',tokens=len(t)));continue
            if norm(texts[a][i]) in exact:
                j=exact[norm(texts[a][i])];rows.append(dict(source_page=i+1,target_page=j+1,kind='exact_normalized_text',sequence_ratio=1.0,source_coverage=1.0));continue
            ss=set(t)
            scores=[sum(weights.get(w,1) for w in ss&s)/max(1,sum(weights.get(w,1) for w in ss|s)) for s in sets]
            top=sorted(range(len(bb)),key=lambda j:scores[j],reverse=True)[:4]
            options=[]
            for j in top:
                sm=difflib.SequenceMatcher(None,t,bb[j],autojunk=False);blocks=sm.get_matching_blocks();match=sum(x.size for x in blocks)
                options.append((match/max(len(t),len(bb[j]),1),j,sm.ratio(),match/len(t)))
            _,j,ratio,coverage=max(options)
            sm=difflib.SequenceMatcher(None,t,bb[j],autojunk=False)
            differences=[dict(kind=tag,source=' '.join(t[x:y])[:180],target=' '.join(bb[j][u:v])[:180]) for tag,x,y,u,v in sm.get_opcodes() if tag!='equal']
            rows.append(dict(source_page=i+1,target_page=j+1,kind='best_content_match',sequence_ratio=round(ratio,6),source_coverage=round(coverage,6),source_tokens=len(t),target_tokens=len(bb[j]),differences=differences[:8]))
        return dict(source=a,target=b,source_pages=len(aa),target_pages=len(bb),exact_pages=sum(x.get('kind')=='exact_normalized_text' for x in rows),pages_at_least_95_percent_coverage=sum(x.get('source_coverage',0)>=.95 for x in rows),page_alignment=rows)
    result['comparisons']=[align('printing','onbase')]
    if 'legistar' in docs:result['comparisons'].append(align('printing','legistar'));result['comparisons'].append(align('onbase','legistar'))
    S.save(S.P+'sunport-comparison.json',result)
    render_samples(docs)
    print('Comparison saved',flush=True)
def render_samples(docs=None):
    sys.path.insert(0,str(S.G.ROOT/'tmp/pdfs/pydeps'));import pymupdf as fitz
    if docs is None:docs={k:fitz.open(S.G.ROOT/p) for k,p in {'printing':'research/staging/ordinary-second-large-campaign-2026-09-26/src-1f9cf39555e7be6f.pdf','onbase':'research/staging/source-hold-resolution-2026-10-04/onbase-12246971.pdf'}.items()}
    # Preserve individual source page renders without image alteration.
    pairs=[(1,1),(2,2),(3,3),(18,18),(150,150),(301,301),(450,450),(560,560),(600,606),(601,607)]
    for n,(a,b) in enumerate(pairs,1):
        for offset,(key,page) in enumerate([('printing',a),('onbase',b)]):
            pix=docs[key][page-1].get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False)
            pix.save(S.G.ROOT/(S.P+f'visual-{2*n-1+offset}.png'))
def global_compare():
    sys.path.insert(0,str(S.G.ROOT/'tmp/pdfs/pydeps'));import pymupdf as fitz
    docs={k:fitz.open(S.G.ROOT/p) for k,p in {'printing':'research/staging/ordinary-second-large-campaign-2026-09-26/src-1f9cf39555e7be6f.pdf','onbase':'research/staging/source-hold-resolution-2026-10-04/onbase-12246971.pdf'}.items()}
    def clean(t):
        t=re.sub(r'[-\u2010-\u2015]\s*\n\s*(?=[a-z])','',t)
        t=t.replace('\ufffd',' ')
        return re.findall(r'[a-z0-9]+',t.lower())
    ts={k:[clean(p.get_text()) for p in d] for k,d in docs.items()}
    # Whole-volume matching tolerates page reflow. autojunk suppresses extremely
    # common words as anchors, but they still match within anchored blocks.
    a=[w for p in ts['printing'] for w in p];b=[w for p in ts['onbase'] for w in p]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=True)
    blocks=sm.get_matching_blocks();match=sum(x.size for x in blocks)
    diffs=[]
    for tag,x,y,u,v in sm.get_opcodes():
        if tag!='equal':diffs.append(dict(kind=tag,printing_start_token=x,printing_end_token=y,onbase_start_token=u,onbase_end_token=v,printing=' '.join(a[x:y])[:800],onbase=' '.join(b[u:v])[:800]))
    c=S.G.load(S.P+'sunport-comparison.json');c['whole_volume_sequence_comparison']=dict(normalization='lowercase alphanumeric tokens; rejoin explicit line-end hyphenation; page boundaries ignored, headers/page numbers retained',printing_tokens=len(a),onbase_tokens=len(b),matching_tokens=match,printing_coverage=match/len(a),onbase_coverage=match/len(b),sequence_ratio=sm.ratio(),difference_ranges=diffs)
    # True aligned samples rather than same physical page number.
    S.save(S.P+'sunport-comparison.json',c)
    samples=[150,301,450,560,601]
    mapping={x['source_page']:x.get('target_page') for x in c['comparisons'][0]['page_alignment']}
    c['aligned_visual_samples']=[]
    for n,p in enumerate(samples):
        q=mapping[p]
        for offset,(key,page) in enumerate([('printing',p),('onbase',q)]):
            docs[key][page-1].get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False).save(S.G.ROOT/(S.P+f'visual-{21+2*n+offset}.png'))
        c['aligned_visual_samples'].append(dict(printing_page=p,onbase_page=q,printing_render=S.P+f'visual-{21+2*n}.png',onbase_render=S.P+f'visual-{22+2*n}.png'))
    S.save(S.P+'sunport-comparison.json',c)
    print(json.dumps({k:v for k,v in c['whole_volume_sequence_comparison'].items() if k!='difference_ranges'}),flush=True)
if __name__=='__main__' and len(sys.argv)==2 and sys.argv[1]=='compare':compare()
elif __name__=='__main__' and len(sys.argv)==2 and sys.argv[1]=='render':render_samples()
elif __name__=='__main__' and len(sys.argv)==2 and sys.argv[1]=='global':global_compare()
elif __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('label');p.add_argument('--headers');a=p.parse_args()
    retrieve(a.url,a.label,json.loads(a.headers) if a.headers else None)
