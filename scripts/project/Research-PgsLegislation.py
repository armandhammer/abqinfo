"""Read-only authoritative retrieval and exact PGS legislative comparisons."""
import hashlib,json,re,sys,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import PgsLegislativeResolution as S
sys.path.insert(0,str(S.G.ROOT/'tmp/pgs-pdf-deps'))
import pymupdf
OUT=S.G.ROOT/'research'/'staging'/S.TASK
OUT.mkdir(parents=True,exist_ok=True)
def fetch(item):
    n,url=item; path=OUT/f'source-{n}.bin'
    receipt=dict(url=url,retrieved_at=S.now(),request_method='GET',complete_response=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ABQInfo source/finality research'}),timeout=60) as r:
            data=r.read();receipt.update(http_status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        path.write_bytes(data);receipt['local_source']=path.relative_to(S.G.ROOT).as_posix()
        if data[:1] in [b'{',b'[']:
            try:receipt['response_json']=json.loads(data)
            except ValueError:pass
        elif data.startswith(b'%PDF'):
            with pymupdf.open(stream=data,filetype='pdf') as d:
                t='\n'.join(p.get_text() for p in d);receipt.update(page_count=len(d),word_count=len(t.split()),text_sha256=hashlib.sha256(t.encode()).hexdigest())
                (S.G.ROOT/(S.P+f'evidence-{n}.txt')).write_text(t,encoding='utf8',newline='\n')
    except Exception as e:receipt.update(error=str(e),complete_response=False)
    S.save(S.P+f'evidence-{n}.json',receipt)
    return n,receipt.get('http_status'),receipt.get('size_bytes'),receipt.get('error')
def initial():
    jobs=[];n=1
    for mid in [1463,2609,2802]:
        for suffix in ['', '/attachments','/histories','/texts']:
            jobs.append((n,f'https://webapi.legistar.com/v1/cabq/matters/{mid}'+suffix));n+=1
    for url in ['https://www.cabq.gov/council/documents/pgs/o-39fs3.pdf','https://www.cabq.gov/council/documents/pgs/o-132fin.pdf','https://www.cabq.gov/council/documents/pgs/o-9fin.pdf','https://legistar.granicus.com/cabq/attachments/292.doc','https://legistar.granicus.com/cabq/attachments/1354.doc','https://legistar.granicus.com/cabq/attachments/1589.doc','https://www.cabq.gov/council/projects/completed-projects/2004/planned-growth-strategy']:
        jobs.append((n,url));n+=1
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(fetch,jobs):print(result,flush=True)
def inspect_existing():
    records=[]
    for n,(rid,label,p) in enumerate([(S.IDS[0],'held','src-f7c7bd5b273def22-60c0e7c0162c.bin'),(S.IDS[1],'held','src-68582bc4fe41fb4f-57e21a6b26da.bin'),(S.IDS[2],'held','src-fcbe6a7ebcf916a1-32ada83e3c46.bin'),(S.IDS[0],'word-render','pgs-doc-o39-8e8ba678277c.pdf'),(S.IDS[1],'word-render','pgs-doc-o132-90de549cc251.pdf'),(S.IDS[2],'word-render','pgs-doc-o9-32f27e6cc283.pdf')],30):
        path=S.G.ROOT/'research/staging/background-followup-2026-09-26'/p
        with pymupdf.open(path) as d:
            t='\n'.join(page.get_text() for page in d)
            text_path=S.P+f'evidence-{n}.txt';(S.G.ROOT/text_path).write_text(t,encoding='utf8',newline='\n')
            record=dict(id=rid,label=label,source=path.relative_to(S.G.ROOT).as_posix(),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=len(d),words=len(t.split()),text_path=text_path)
            tiles=[]
            from PIL import Image,ImageDraw
            for i,page in enumerate(d):
                pix=page.get_pixmap(matrix=pymupdf.Matrix(.38,.38));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                tiles.append(im)
            w=max(im.width for im in tiles);h=max(im.height for im in tiles)+22
            sheet=Image.new('RGB',(w*4,h*((len(tiles)+3)//4)),'#ddd');draw=ImageDraw.Draw(sheet)
            for i,im in enumerate(tiles):sheet.paste(im,((i%4)*w,(i//4)*h+22));draw.text(((i%4)*w+5,(i//4)*h+3),str(i+1),fill='black')
            sheet.save(S.G.ROOT/(S.P+f'evidence-{n}.png'));record['contact_sheet']=S.P+f'evidence-{n}.png'
            records.append(record);print(record)
    S.save(S.P+'comparison.json',dict(existing_measurements=records))
def compare():
    import difflib
    c=S.G.load(S.P+'comparison.json');results=[]
    def clean(t,pdf=False):
        t=re.sub(r'\.\.t\s*.*?\.\.b\s*','',t,flags=re.S)
        t=re.sub(r'\[\+Bracketed/Underscored Material\+\]\s*-\s*New\s*\[-Bracketed/Strikethrough Material-\]\s*-\s*Deletion','',t)
        t=re.sub(r'^.*X:\\SHARE.*$','',t,flags=re.M|re.I)
        if pdf:t=re.sub(r'^\s*\d{1,2}\s*$','',t,flags=re.M)
        t=re.sub(r'(\w)-\s*\n\s*(\w)',r'\1-\2',t)
        # Hyphenation, apostrophe glyphs and punctuation differ by converter; preserve every letter and number.
        return re.sub(r'[^a-z0-9]','',t.lower())
    for held,word,final,original,mid in [(30,33,54,57,1463),(31,34,60,61,2609),(32,35,62,63,2802)]:
        finalrow=S.G.load(S.P+f'evidence-{final}.json')['response_json']
        assert finalrow['MatterTextMatterId']==mid
        finaltext=finalrow['MatterTextPlain'];heldtext=(S.G.ROOT/(S.P+f'evidence-{held}.txt')).read_text(encoding='utf8');wordtext=(S.G.ROOT/(S.P+f'evidence-{word}.txt')).read_text(encoding='utf8')
        # Split prose from the standalone EXHIBIT 1 heading, not the prose reference to that exhibit.
        def parts(t):return re.split(r'(?im)^\s*EXHIBIT\s+[123]\s*$',t)
        hp,wp,fp=parts(heldtext),parts(wordtext),parts(finaltext)
        def clauses(t):return t[re.search(r'Section\s+1\.',t,re.I).start():]
        result=dict(matter_id=mid,text_id=finalrow['MatterTextId'],version=finalrow['MatterTextVersion'],matter_identity_verified=True,held_prose_equal=clean(clauses(hp[0]),True)==clean(clauses(fp[0])),word_prose_equal=clean(clauses(wp[0]),True)==clean(clauses(fp[0])),held_exhibit_count=len(hp)-1,word_exhibit_count=len(wp)-1,final_exhibit_count=len(fp)-1,exhibits=[])
        if not result['held_prose_equal']:
            a,b=clean(hp[0],True),clean(fp[0]);sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
            result['prose_differences']=[dict(op=op,held=a[max(0,i-2):j+2],final=b[max(0,k-2):l+2]) for op,i,j,k,l in sm.get_opcodes() if op!='equal']
        for i in range(1,len(fp)):
            # The identical ordered numeric sequence compares every cell, including negative values; row labels compared separately.
            def nums(t):return re.findall(r'(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?',t)
            def table(t,pdf):
                if pdf:t=re.sub(r'\n\s*\d{1,2}\s*\Z','',t)
                return nums(re.sub(r'1960\s*-\s*1979','1960 1979',t))
            ha,wa,fa=table(hp[i],True),table(wp[i],True),table(fp[i],False)
            def labels(t):return re.sub(r'[^a-z]','',re.sub(r'\bSubarea\b','',t,flags=re.I).lower())
            result['exhibits'].append(dict(exhibit=i,numeric_tokens=len(fa),held_numeric_sequence_equal=ha==fa,word_numeric_sequence_equal=wa==fa,held_labels_equal=labels(hp[i])==labels(fp[i]),word_labels_equal=labels(wp[i])==labels(fp[i]),held_numeric_sequence=ha,final_numeric_sequence=fa))
        a=S.G.load(S.P+f'evidence-{original}.json')['response_json'];assert a['MatterTextMatterId']==mid
        result['version_changes']=list(difflib.unified_diff(a['MatterTextPlain'].splitlines(),finaltext.splitlines(),fromfile='prior legislative version',tofile='final legislative version',n=1))
        results.append(result);print({k:v for k,v in result.items() if k not in ['version_changes','exhibits','prose_differences']});print('diffs',result.get('prose_differences',[]));print('tables',[(e['exhibit'],e['held_numeric_sequence_equal'],e['word_numeric_sequence_equal']) for e in result['exhibits']])
    c['substantive_comparisons']=results;S.save(S.P+'comparison.json',c)
if __name__=='__main__':
    if sys.argv[1]=='initial':initial()
    elif sys.argv[1]=='existing':inspect_existing()
    elif sys.argv[1]=='compare':compare()
    elif sys.argv[1]=='fetch':print(fetch((int(sys.argv[2]),sys.argv[3])))
