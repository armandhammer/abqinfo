#!/usr/bin/env python3
"""Create first/middle/last PDF inspection sheets without modifying originals."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

root=Path('research/staging/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21')
out=root/'pdf-visual-qa'; out.mkdir(exist_ok=True)
for file in sorted(root.glob('*.pdf')):
    pdf=pdfium.PdfDocument(str(file)); tiles=[]
    for page_no in sorted({0,len(pdf)//2,len(pdf)-1}):
        image=pdf[page_no].render(scale=.7).to_pil().convert('RGB'); image.thumbnail((700,900))
        tile=Image.new('RGB',(720,940),'white'); tile.paste(image,((720-image.width)//2,30))
        ImageDraw.Draw(tile).text((10,8),f'{file.name}: page {page_no+1}/{len(pdf)}',fill='black'); tiles.append(tile)
    sheet=Image.new('RGB',(720,len(tiles)*940),'#d8d8d8')
    for n,tile in enumerate(tiles): sheet.paste(tile,(0,n*940))
    sheet.save(out/(file.stem+'-first-middle-last.png'))
