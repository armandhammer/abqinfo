"""GET-only verification of public wrappers, supplied layers and catalog PDF fingerprints."""
import concurrent.futures
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from enumerate import OUT, get, save, api

inventory = json.loads(Path('project-state/master-inventory.json').read_text(encoding='utf-8-sig'))['candidates']
pages = json.loads((OUT/'catalog-pages.json').read_text(encoding='utf-8'))
urls = set()
for file in Path('content').rglob('*.md'):
    text = file.read_text(encoding='utf-8')
    urls.update(re.findall(r'https://www\.mrcog-nm\.gov/\d+/[^\s)\"<>]+',text))
urls -= {p['url'] for p in pages}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for r in pool.map(get,sorted(urls)):
        b = r.get('body','')
        if isinstance(b,str):
            r['links'] = sorted(set(html.unescape(urllib.parse.urljoin(r['url'], x)) for x in
                                   re.findall(r'(?:href|src)=[\"\']([^\"\']+)', b,re.I)))
        pages.append(r)
save('catalog-pages.json',pages)

target = json.loads((OUT/'supplied-map.json').read_text(encoding='utf-8'))
webmap = target['dependencies']['8854cd813777456db84f616efa3bc5a3']['data']['body']
def layers(rows):
    for row in rows:
        if row.get('url'): yield row
        yield from layers(row.get('layers',[]))
def check(row):
    root = row['url']
    metadata = get(root+'?f=json')
    count = get(root+'/query?'+urllib.parse.urlencode({'f':'json','where':'1=1','returnCountOnly':'true'}))
    return {'title':row['title'],'url':root,'metadata':metadata,'count':count}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    checks = list(pool.map(check,list(layers(webmap['operationalLayers']))))
save('layer-checks.json',checks)
configs = json.loads((OUT/'app-configs.json').read_text(encoding='utf-8'))
for x in configs:
    if x['id'] in ('7b8a980f1eeb423ab181c40bc2d1732b','71f76312d8ce4b83bca87a475170a3a0','eeee7544fd0c4951895aef450a797493'):
        x['resources_config'] = api(x['root'],'content/items/'+x['id']+'/resources/config/config.json')
save('app-configs.json',configs)
static=[]
catalog=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
for item in catalog['searches'][1]['items']:
    if item['type'] != 'PDF': continue
    u='https://mrmpo.maps.arcgis.com/sharing/rest/content/items/'+item['id']+'/data'
    try:
        with urllib.request.urlopen(u,timeout=60) as response: data=response.read()
        sha=hashlib.sha256(data).hexdigest()
        static.append({'id':item['id'],'title':item['title'],'url':u,'size':len(data),'sha256':sha,
                       'pdf_signature':data.startswith(b'%PDF'),
                       'exact_inventory_hash_matches':[c['id'] for c in inventory if c.get('checksum_sha256')==sha]})
    except Exception as e: static.append({'id':item['id'],'error':str(e)})
save('static-item-checks.json',static)
print('Official wrappers:',len(pages),'layer checks:',len(checks),'static PDF fingerprints:',len(static))
