"""Targeted family and exact-identity evidence; no dispositions are inferred."""
import hashlib,html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
F=ROOT/'project-state/discovery/human-review-reassessment-2026-09-26'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
q=load(F/'baseline-queue.json');base={r['id']:r for r in load(F/'baseline-records.json')}
retrievals=load(F/'retrievals.json')['records'];inventory=load(ROOT/'project-state/master-inventory.json')['candidates']
byhash={}
for r in inventory:
    if r.get('checksum_sha256'):byhash.setdefault(r['checksum_sha256'],[]).append({k:r.get(k) for k in ['id','title','status','source_url','r2_url','size_bytes']})
records=[]
for p in q['packages']:
    for r in p['records']:
        urls={r.get(k) for k in ['direct_file_url','source_url','parent_url'] if r.get(k)}
        fetches=[x for x in retrievals if x['id']==r['id'] or x['url'] in urls]
        texts=[]
        for x in fetches:
            if x.get('saved_source') and 'html' in str(x.get('content_type')).lower():
                body=(ROOT/x['saved_source']).read_text(encoding='utf-8',errors='replace')
                body=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',body,flags=re.I|re.S)
                text=html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',body)))
                pos=text.lower().find('project scope')
                if pos<0:
                    title=html.unescape(x.get('title','').split(' - Public')[0]).strip()
                    pos=text.rfind(title) if title else 0
                if pos<0:pos=0
                texts.append(dict(url=x['url'],main_text=text[pos:pos+15000],title=x.get('title')))
        matches=[]
        hashes={base[r['id']].get('checksum_sha256')}|{x.get('sha256') for x in fetches if not x.get('truncated') and x.get('page_count')}
        for h in hashes:
            for m in byhash.get(h,[]):
                if m['id']!=r['id']:matches.append(m)
        records.append(dict(id=r['id'],package_id=p['package_id'],title=r['title'],retrievals=[{k:v for k,v in x.items() if k!='links'} for x in fetches],main_texts=texts,exact_hash_matches=matches,evidence_artifacts=r['evidence_artifacts']))
save(F/'family-evidence.json',dict(records=records))
print('Summarized',len(records),'records;',len(retrievals),'bounded retrievals')
for r in records:
    if r['exact_hash_matches']:print(r['id'],'MATCH',[(m['id'],m['status']) for m in r['exact_hash_matches']])
