import json, hashlib, concurrent.futures, subprocess, re
from pathlib import Path
from urllib.request import Request, urlopen
from pypdf import PdfReader
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
TMP=ROOT/'tmp/go-capital-quality'; TMP.mkdir(exist_ok=True,parents=True)
POPLER=Path('C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
ids=set(json.loads((OUT/'preparation.json').read_text(encoding='utf-8'))['capital_candidate_ids'])|{'src-cb8cd727e3ca1fde','src-8c5d2888cc22b991'}
rows=[r for r in json.loads((ROOT/'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))['candidates'] if r['id'] in ids]
def measure(row):
    rid=row['id'];path=TMP/(rid+'.pdf')
    data=urlopen(Request(row['r2_url'],headers={'User-Agent':'ABQInfo quality remediation original byte review'}),timeout=90).read()
    sha=hashlib.sha256(data).hexdigest()
    assert sha==row['checksum_sha256'] and len(data)==row['size_bytes'],rid
    path.write_bytes(data)
    reader=PdfReader(path);texts=[p.extract_text() or '' for p in reader.pages]
    (TMP/(rid+'.txt')).write_text('\n\f\n'.join(texts),encoding='utf-8')
    result={'id':rid,'title':row['title'],'url':row['r2_url'],'source_url':row['direct_file_url'],'size_bytes':len(data),'sha256':sha,'verified':True,'page_count':len(texts),'extracted_word_count':len(re.findall(r'\S+', '\n'.join(texts))),'page_text_sha256':[hashlib.sha256(t.encode()).hexdigest() for t in texts],'pdf_metadata':{str(k):str(v) for k,v in (reader.metadata or {}).items()}}
    if len(texts)<25:
        pages=list(range(1,len(texts)+1))
    else:
        pages=[1,2,3]+[n+1 for n,t in enumerate(texts) if any(s in t.lower() for s in ['plaza del sol stucco','replacement vehicles (dmd)','parking facilities rehabilitation','city building improvement'])]
        pages=sorted(set(pages))
    result['rendered_pages']=pages
    for n in pages:
        subprocess.run([str(POPLER),'-f',str(n),'-l',str(n),'-scale-to','1000','-png','-singlefile',str(path),str(TMP/(rid+'-'+str(n)))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(measure,rows))
(OUT/'public-byte-measurements.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
images=[]
for r in results:
    for n in r['rendered_pages']:
        im=Image.open(TMP/(r['id']+'-'+str(n)+'.png')).convert('RGB');im.thumbnail((360,470))
        tile=Image.new('RGB',(380,515),'#eeeeee');tile.paste(im,((380-im.width)//2,35));d=ImageDraw.Draw(tile);d.text((8,5),r['id']+' p'+str(n),fill='black');images.append(tile)
for offset in range(0,len(images),16):
    batch=images[offset:offset+16];sheet=Image.new('RGB',(1520,515*((len(batch)+3)//4)),'white')
    for n,im in enumerate(batch):sheet.paste(im,((n%4)*380,(n//4)*515))
    sheet.save(TMP/('sheet-'+str(offset//16)+'.png'))
print(json.dumps({'records':len(results),'rendered_pages':len(images),'sheets':(len(images)+15)//16,'measurements':str(OUT/'public-byte-measurements.json')}))
