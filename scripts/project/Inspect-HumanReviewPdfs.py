"""Render bounded review contact sheets; originals remain unchanged."""
import sys,json
from pathlib import Path
sys.path.insert(0,'tmp/pgs-pdf-deps')
import pymupdf
from PIL import Image,ImageDraw
f=Path('project-state/discovery/human-review-reassessment-2026-09-26')
ret=json.loads((f/'retrievals.json').read_text(encoding='utf-8'))['records']
ids=sys.argv[1:] or ['src-4996854ae4e1a349','src-a738fd67bc6abac6','src-c7fcd58b9998999c']
for i in ids:
    r=next(x for x in ret if x['id']==i and x.get('page_count'))
    doc=pymupdf.open(r['saved_source'])
    pages=list(range(len(doc))) if len(doc)<=50 else sorted(set([0,1,2,len(doc)-1]+list(range(10,len(doc),20))))
    sheet=Image.new('RGB',(1200,((len(pages)+3)//4)*420),'white');draw=ImageDraw.Draw(sheet)
    for slot,n in enumerate(pages):
        p=doc[n];factor=min(285/p.rect.width,380/p.rect.height)
        pix=p.get_pixmap(matrix=pymupdf.Matrix(factor,factor),alpha=False)
        im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);x=(slot%4)*300;y=(slot//4)*420
        sheet.paste(im,(x,y));draw.text((x,y+390),f'Page {n+1}',fill='black')
    out=Path('tmp/pdfs/human-review');out.mkdir(parents=True,exist_ok=True)
    sheet.save(out/(i+'.png'))
    print(i,r['page_count'],r['word_count'],r['sha256'],r['text_excerpt'][:800])
