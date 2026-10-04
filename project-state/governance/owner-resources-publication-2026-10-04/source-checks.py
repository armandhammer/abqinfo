"""Fresh official-source retrieval and external checks; metadata does not establish rendered usability."""
import hashlib,json,sys,urllib.request
from pathlib import Path
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
P=S.prefix(S.B);scratch=S.G.ROOT/'research/staging/owner-resources-publication-2026-10-04';scratch.mkdir(parents=True,exist_ok=True)
S.G.active_check('mutation','document_review',S.NEW)
def get(url,label):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=60) as r:
        body=r.read();receipt=dict(requested_url=url,final_url=r.geturl(),http_status=r.status,retrieved_at_utc=S.now(),size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),content_type=r.headers.get('Content-Type'),complete_response=True)
    (scratch/label).write_bytes(body)
    receipt['local_response']=str((scratch/label).relative_to(S.G.ROOT)).replace('\\','/')
    return body,receipt
rows={r['id']:r for r in S.G.load('project-state/master-inventory.json')['candidates']};checks=[]
for rid in S.LIVE+S.NEW:
    body,r=get(rows[rid]['source_url'],rid+'.html');r['candidate_id']=rid;checks.append(r)
    if rid==S.NEW[1]:
        S.save(P+'evidence-1.json',dict(retrieval=r,title='Neighborhood Association Websites',publisher='City Office of Neighborhood Coordination',source_text='NOTE: This list only includes recognized neighborhood associations which have submitted their website to the ONC. It does not include homeowner association (HOA) websites.',visible_listing_evidence=('Academy Estates East' in body.decode('utf-8')),maintained_directory=True,individual_associations_maintain_their_sites=True))
base='https://cabq.maps.arcgis.com/sharing/rest/content/items/1eef18dec8844aecabba439823ff9eb2'
metadata,receipt=get(base+'?f=pjson','app-item.json');data,datareceipt=get(base+'/data?f=pjson','app-data.json')
item=json.loads(metadata);config=json.loads(data);assert 'error' not in item and 'error' not in config
S.save(P+'evidence-2.json',dict(item=item,configuration=config,item_retrieval=receipt,configuration_retrieval=datareceipt,rendered_usability='pending actual desktop Chrome observation'))
S.save(P+'external-checks.json',dict(checked_at_utc=S.now(),checks=checks,all_http_200=all(x['http_status']==200 for x in checks)))
print(json.dumps(dict(title=item.get('title'),owner=item.get('owner'),type=item.get('type'),url=item.get('url'),snippet=item.get('snippet'),description=item.get('description'),config=config),ensure_ascii=False))
