import sys,json,pathlib,argparse
ROOT=pathlib.Path.cwd();sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=152);p.add_argument('--end',type=int,default=299);p.add_argument('--label',default='regional');a=p.parse_args()
D=ROOT/'project-state/discovery';Q=ROOT/'tmp/ordinary-second-large-campaign-qa-2026-09-26';sel=json.loads((D/'ordinary-queue-second-large-campaign-selection-2026-09-26.json').read_text(encoding='utf-8-sig'));rr=[]
for f in sel['candidate_families']:
 if not a.start<=f['order']<=a.end:continue
 path=D/f"ordinary-second-large-campaign-{f['family_id']}-2026-09-26.json"
 for r in json.loads(path.read_text(encoding='utf-8-sig'))['records']:
  q=r.get('fresh_source_qa',{});imgs=q.get('representative_images',[])
  if imgs:rr.append((f['family_id'],r,imgs))
manifest=[]
for k in range(0,len(rr),8):
 im=Image.new('RGB',(1200,8*360),'#dddddd');draw=ImageDraw.Draw(im);ids=[]
 for j,(fam,r,imgs) in enumerate(rr[k:k+8]):
  draw.text((4,j*360+2),fam+' '+r['id'],fill='black');ids.append(r['id'])
  for z,ip in enumerate(imgs[:3]):
   page=Image.open(ROOT/ip).convert('RGB');page.thumbnail((395,338));im.paste(page,(z*400+(400-page.width)//2,j*360+20))
 path=Q/f'{a.label}-review-{k//8+1:02}.jpg';im.save(path,quality=88);manifest.append({'sheet':str(path.relative_to(ROOT)).replace('\\','/'),'ids':ids})
(Q/f'{a.label}-review-sheets.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');print(len(rr),'records',len(manifest),'sheets')
