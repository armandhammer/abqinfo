"""Read-only Council source delivery witnesses and measured/rendered PDF inspection."""
import json, gzip, urllib.request, hashlib, sys, re
from concurrent.futures import ThreadPoolExecutor
import CouncilFinalityResolution as S
from PIL import Image,ImageDraw
sys.path.insert(0,str(S.G.ROOT/'tmp/pgs-pdf-deps'))
import pymupdf
def fetch(item):
    n,url=item;row=dict(url=url,method='GET')
    from datetime import datetime,timezone
    row['retrieved_at']=datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ABQInfo Council finality research'}),timeout=45) as res:
            data=res.read();row.update(status=res.status,final_url=res.url,content_type=res.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),complete=True)
        (S.G.ROOT/(S.P+f'evidence-{n}.bin.gz')).write_bytes(gzip.compress(data,mtime=0))
        if data[:1] in [b'{',b'[']:row['response_json']=json.loads(data)
        elif data.startswith(b'%PDF'):inspect(n,data,row)
        else:
            from bs4 import BeautifulSoup
            if 'html' in row['content_type']:
                soup=BeautifulSoup(data,'html.parser');row['links']=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in soup.select('a[href]')];(S.G.ROOT/(S.P+f'evidence-{n}.txt')).write_text(soup.get_text('\n',strip=True),encoding='utf-8',newline='\n')
    except Exception as e:row.update(error=str(e),complete=False)
    S.save(S.P+f'evidence-{n}.json',row);return n,row.get('status'),row.get('size_bytes'),row.get('error')
def inspect(n,data,row):
    with pymupdf.open(stream=data,filetype='pdf') as d:
        t='\n'.join(p.get_text() for p in d);row.update(page_count=len(d),word_count=len(t.split()),metadata=d.metadata,embedded_files=d.embfile_names())
        (S.G.ROOT/(S.P+f'evidence-{n}.txt')).write_text(t,encoding='utf8',newline='\n')
        tiles=[]
        for p in d:
            pix=p.get_pixmap(matrix=pymupdf.Matrix(.85,.85));tiles.append(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))
        w=max(x.width for x in tiles);h=max(x.height for x in tiles)+22;cols=min(2,len(tiles))
        sheet=Image.new('RGB',(w*cols,h*((len(tiles)+cols-1)//cols)),'#ddd');draw=ImageDraw.Draw(sheet)
        for i,im in enumerate(tiles):sheet.paste(im,((i%cols)*w,(i//cols)*h+22));draw.text(((i%cols)*w+5,(i//cols)*h+3),str(i+1),fill='black')
        sheet.save(S.G.ROOT/(S.P+f'evidence-{n}.png'));row['contact_sheet']=S.P+f'evidence-{n}.png'
def existing():
    paths=['project-state/discovery/nob-hill-highland-cluster-research-2026-09-11.json','project-state/discovery/human-review-reassessment-2026-09-26/family-evidence.json','project-state/discovery/human-review-reassessment-2026-09-26/decisions.json','project-state/discovery/background-followup-2026-09-26/comparisons.json','project-state/discovery/background-followup-2026-09-26/decisions.json','project-state/contributed-document-review-2026-08-14.json','project-state/contributed-document-decisions-2026-08-14.json']
    findings=[]
    for path in paths:
        d=S.G.load(path);matches=[]
        def walk(x):
            if isinstance(x,dict):
                if any(x.get(k) in S.IDS for k in ['id','candidate_id','matching_inventory_id']):matches.append(x)
                else:
                    for v in x.values():walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
        walk(d)
        findings.append(dict(path=path,sha256=S.G.file_hash(path),matches=matches,cluster_summary={k:d[k] for k in ['blocker_correction','brief_finding','method','plan_completeness'] if k in d}))
    S.save(S.P+'historical-evidence.json',dict(artifacts=findings))
    for n,row in enumerate(S.G.load(S.P+'prior-records.json')['records'],30):
        path=S.G.ROOT/row['local_path'];data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==row['checksum_sha256']
        m=dict(id=row['id'],source=str(path),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest());inspect(n,data,m);S.save(S.P+f'evidence-{n}.json',m);print(n,m['page_count'],m['word_count'])
def initial():
    jobs=[(1,'https://webapi.legistar.com/v1/cabq/matters/5227'),(2,'https://webapi.legistar.com/v1/cabq/matters/5227/attachments'),(3,'https://webapi.legistar.com/v1/cabq/matters/5227/histories'),(4,'https://webapi.legistar.com/v1/cabq/matters/5227/versions'),(5,S.G.load(S.P+'prior-records.json')['records'][1]['r2_url'])]
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch,jobs):print(result,flush=True)
def versions():
    jobs=[(6,'https://webapi.legistar.com/v1/cabq/matters/5227/texts/6628'),(7,'https://webapi.legistar.com/v1/cabq/matters/5227/texts/6577'),(8,'https://webapi.legistar.com/v1/cabq/matters/5227/texts/6549'),(9,'https://webapi.legistar.com/v1/cabq/matters/5227/texts/6408'),(10,'https://legistar.granicus.com/cabq/attachments/6143.pdf'),(11,'https://legistar.granicus.com/cabq/attachments/6204.doc'),(12,'https://legistar.granicus.com/cabq/attachments/6142.doc'),(13,'https://webapi.legistar.com/v1/cabq/events/1170/attachments'),(14,'https://cabq.legistar.com/LegislationDetail.aspx?ID=5227&GUID=575ED4A3-9FC8-4E83-8C5F-074E09157313&Options=ID|Text|&Search=R-07-268')]
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch,jobs):print(result,flush=True)
def compare():
    import difflib
    def data(n):return gzip.decompress((S.G.ROOT/(S.P+f'evidence-{n}.bin.gz')).read_bytes())
    held,current=data(5),data(21)
    def container(b):
        # Only two explicit non-content metadata fields differ; preserve every other byte.
        b=re.sub(rb'/ID\[<([0-9A-F]+)><[0-9A-F]+>\]',rb'/ID[<\1><METADATA-ID>]',b)
        return re.sub(rb'/ModDate \(D:[^)]*\)',b'/ModDate (METADATA-DATE)',b)
    assert container(held)==container(current),'Unexplained official/held byte difference'
    def clean(t,pdf=False):
        t=re.sub(r'\.\.t\s*.*?\.\.b\s*','',t,flags=re.S)
        t=re.sub(r'\[\+Bracketed/Underscored Material\+\]\s*-\s*New\s*\[-Bracketed/Strikethrough Material-\]\s*-\s*Deletion','',t)
        if pdf:t=re.sub(r'^\s*\d{1,2}\s*$','',t,flags=re.M)
        return re.sub(r'[^a-z0-9]','',t.lower())
    texts={}
    for n in [6,7,8,9]:
        d=S.G.load(S.P+f'evidence-{n}.json')['response_json'];assert d['MatterTextMatterId']==5227
        texts[d['MatterTextVersion']]=d
    h=(S.G.ROOT/(S.P+'evidence-5.txt')).read_text(encoding='utf8')
    assert clean(h,True)==clean(texts['4']['MatterTextPlain'])
    assert (S.G.ROOT/(S.P+'evidence-5.txt')).read_bytes()==(S.G.ROOT/(S.P+'evidence-21.txt')).read_bytes()
    pixels=[]
    with pymupdf.open(stream=held,filetype='pdf') as a,pymupdf.open(stream=current,filetype='pdf') as b:
        assert len(a)==len(b)==4
        for i in range(4):
            pa,pb=a[i].get_pixmap(matrix=pymupdf.Matrix(1,1)),b[i].get_pixmap(matrix=pymupdf.Matrix(1,1))
            assert pa.width==pb.width and pa.height==pb.height and pa.samples==pb.samples
            pixels.append(dict(page=i+1,width=pa.width,height=pa.height,pixel_sha256=hashlib.sha256(pa.samples).hexdigest(),equal=True))
    prior=S.G.ROOT/'research/staging/background-followup-2026-09-26/bill-R-07-268-final-587d887acadb.doc'
    assert prior.read_bytes()==data(11)
    assert not re.search(r'\bexhibit|\battach(?:ed|ment)|incorporat\w*\s+(?:by\s+reference|the\s+(?:plan|map|exhibit|attachment))',texts['4']['MatterTextPlain'],re.I),'Reassess incorporated package'
    record=S.G.load(S.P+'prior-records.json')['records'][1];assert hashlib.sha256(held).hexdigest()==record['checksum_sha256'] and len(held)==record['size_bytes']
    S.save(S.P+'comparison.json',dict(matter_id=5227,final_text_id=6628,final_version='4',enactment='R-2007-109',correct_matter_identity_all_versions=True,held_r2_exact=True,held_size_bytes=len(held),held_sha256=hashlib.sha256(held).hexdigest(),current_official_size_bytes=len(current),current_official_sha256=hashlib.sha256(current).hexdigest(),held_current_official_exact_bytes=False,only_container_differences=['PDF trailer second document ID, twice','PDF ModDate:20250224173152 to20260122185501'],all_remaining_bytes_equal=True,all_four_rendered_pages_pixel_equal=pixels,full_held_text_equals_correct_final_version=True,official_final_word_equals_september_witness=True,final_text_references_or_incorporates_exhibits=False,companion_exhibit=dict(legacy_attachment=6143,current_attachment=2251888,title='Exhibit A: F/S-07-268 Bike Boulevards',pages=1,role='Illustrative route/phasing and proposed-crossing study-area map. Separately delivered with the floor substitute; final version4 contains all route endpoints/phases/crossing instructions in its own sections and neither references nor incorporates this exhibit. Preserve contextual relationship; not an omitted required enacted exhibit.'),version_differences={f'{a}-to-{b}':list(difflib.unified_diff(texts[a]['MatterTextPlain'].splitlines(),texts[b]['MatterTextPlain'].splitlines(),n=1)) for a,b in [('1','2'),('2','3'),('3','4')]},delivery_qualification='Complete final resolution in official bill format; blank printed enactment line also appears in the authoritative final PDF and final text. Not a signed/certified enactment facsimile; identity verified independently by matter/public report.',rejected_evidence=['Historical /texts/{version} mismatched MatterTextMatterId','API/legacy matter IDs used as modern public page IDs returned Invalid parameters','Meeting minutes endpoint returns image/png2912 bytes, not minutes; not used for text or adoption completeness']))
    print('Correct final text, all non-metadata PDF bytes and all rendered pixels equal; exact held/R2 verified')
if __name__=='__main__':
    if sys.argv[1]=='fetch':print(fetch((int(sys.argv[2]),sys.argv[3])))
    else:globals()[sys.argv[1]]()
