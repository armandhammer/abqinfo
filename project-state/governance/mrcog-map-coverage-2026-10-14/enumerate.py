"""Task-local public ArcGIS enumeration; GET-only, no inventory or storage mutation."""
import concurrent.futures
import datetime
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent
STAMP = datetime.datetime.now(datetime.timezone.utc).isoformat()
PORTAL = 'https://mrcogmaps.org/portal'
ONLINE = 'https://mrmpo.maps.arcgis.com'
TARGET = '15c077acdfd248aea4d7d15f528f51c1'


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            raw = r.read().decode('utf-8', errors='replace')
            return {'url': url, 'status': r.status, 'resolved_url': r.url,
                    'body': json.loads(raw) if raw.lstrip().startswith(('{', '[')) else raw}
    except Exception as e:
        return {'url': url, 'error': str(e)}


def api(root, path, **params):
    return get(root + '/sharing/rest/' + path + '?' + urllib.parse.urlencode({'f': 'json', **params}))


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def compact_config(response):
    """Retain relationships and concise app text; omit feature geometry and large payloads."""
    body = response.get('body', {})
    raw = json.dumps(body)
    refs = []
    def walk(value):
        if isinstance(value, dict):
            if value.get('url') or value.get('title') or value.get('itemId') or value.get('webmap'):
                refs.append({k:value[k] for k in ('title','url','itemId','webmap','group','name') if k in value})
            for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(body)
    values = body.get('values', {}) if isinstance(body, dict) else {}
    return {k:v for k,v in response.items() if k != 'body'} | {'body': {
        'referenced_item_ids': sorted(set(re.findall(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])', raw))),
        'resource_references': refs, 'values': values if len(json.dumps(values)) < 25000 else 'Large configuration summarized; geometry omitted'}}


def search(root, q):
    pages, items, start, seen = [], [], 1, set()
    while start > 0:
        result = api(root, 'search', q=q, num=100, start=start, sortField='id', sortOrder='asc')
        pages.append(result)
        body = result.get('body', {})
        if 'results' not in body:
            return {'root': root, 'q': q, 'complete': False, 'pages': pages, 'items': items}
        items.extend(body['results'])
        following = body.get('nextStart', -1)
        if following in seen:
            raise ValueError('Repeated pagination cursor')
        seen.add(following)
        start = following
    return {'root': root, 'q': q, 'complete': len(items) == pages[0]['body']['total'],
            'pages': pages, 'items': items}


if __name__ == '__main__':
    if '--groups' in sys.argv:
        groups = []
        for root, q in [(PORTAL, 'owner:portaladmin AND title:"Featured Maps and Apps"'),
                        (ONLINE, 'orgid:i3mLmgyL55IkFf81')]:
            result = api(root, 'community/groups', q=q, num=100)
            groups.append({'root': root, 'search': result, 'contents': [
                {'group': g, 'catalog': search(root, 'group:' + g['id'] + ' AND access:public')}
                for g in result.get('body', {}).get('results', []) if g.get('access') == 'public']})
        save('groups.json', groups)
        urls = ['https://www.mrcog-nm.gov/224/Maps-GIS', 'https://www.mrcog-nm.gov/259/Intelligent-Transportation-Systems',
                'https://www.mrcog-nm.gov/199/Orthophotography', 'https://www.mrcog-nm.gov/227/Socioeconomic-Forecasts',
                'https://www.mrcog-nm.gov/234/Bicycles-and-Pedestrians',
                'https://mrcogmaps.org/Forecast2045', 'https://mrcogmaps.org/taqa',
                PORTAL + '/apps/instant/sidebar/index.html?appid=' + TARGET]
        results = []
        for u in urls:
            r = get(u)
            b = r.get('body', '')
            if isinstance(b, str):
                r['links'] = sorted(set(html.unescape(urllib.parse.urljoin(u, x)) for x in
                                           re.findall(r'(?:href|src)=[\"\']([^\"\']+)', b, re.I)))
            results.append(r)
        save('catalog-pages.json', results)
        print('Groups and official catalog pages saved')
        sys.exit(0)
    target = {'retrieved_at': STAMP, 'metadata': api(PORTAL, 'content/items/' + TARGET),
              'data': api(PORTAL, 'content/items/' + TARGET + '/data')}
    data = target['data'].get('body', {})
    ids = set(re.findall(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])', json.dumps(data))) - {TARGET}
    target['dependencies'] = {i: {'metadata': api(PORTAL, 'content/items/' + i),
                                  'data': api(PORTAL, 'content/items/' + i + '/data')} for i in sorted(ids)}
    save('supplied-map.json', target)
    print('Target dependencies:', sorted(ids), flush=True)
    roots = [PORTAL, ONLINE, 'https://mrcog.maps.arcgis.com']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        portals = list(pool.map(lambda r: api(r, 'portals/self'), roots))
    save('portals.json', portals)
    old_path = OUT / 'catalog.json'
    previous = json.loads(old_path.read_text(encoding='utf-8')) if '--resume' in sys.argv and old_path.exists() else None
    inventories = [search(PORTAL, 'orgid:0123456789ABCDEF AND access:public')]
    for result in portals[1:]:
        b = result.get('body', {})
        if b.get('id'):
            root = result['url'].split('/sharing/')[0]
            inventories.append(next((s for s in previous['searches'] if s['root'] == root), None)
                               if previous else search(root, 'orgid:' + b['id'] + ' AND access:public'))
    # Search organizational names as well, to expose official content in another organization.
    for q in ['(MRCOG OR MRMPO) AND access:public']:
        inventories.append(next((s for s in previous['searches'] if s['root'] == 'https://www.arcgis.com'), None)
                           if previous else search('https://www.arcgis.com', q))
    # Keep one copy of each item; original response pagination totals/cursors remain auditable.
    for s in inventories:
        s['pages'] = [{k: v for k, v in page.items() if k != 'body'} |
                      {'body': {k: v for k, v in page.get('body', {}).items() if k != 'results'}}
                      for page in s['pages']]
    save('catalog.json', {'retrieved_at': STAMP, 'searches': inventories,
         'unscoped_probe': 'access:public includes Esri system templates and hits 10000; not an organizational census. Replaced with explicit orgid filter.'})
    for s in inventories:
        print(s['root'], s['q'], len(s['items']), 'complete=', s['complete'], flush=True)
    urls = ['https://mrcogmaps.org/', 'https://mrcogmaps.org/portal/home/index.html',
            'https://www.mrcog-nm.gov/205/Maps', 'https://www.mrcog-nm.gov/544/Long-Range-System-Maps',
            'https://www.mrcog-nm.gov/623/Traffic-Flow-Maps-and-Busiest-Intersecti',
            'https://www.mrcog-nm.gov/574/Transportation-Analysis-and-Querying-App',
            'https://www.mrcog-nm.gov/579/Environmental-Justice']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(get, urls))
    for page in pages:
        body = page.get('body', '')
        if isinstance(body, str):
            page['links'] = sorted(set(html.unescape(urllib.parse.urljoin(page['url'], u)) for u in
                                       re.findall(r'(?:href|src)=[\"\']([^\"\']+)', body, re.I)))
    save('official-pages.json', {'retrieved_at': STAMP, 'pages': pages})
    # App configurations establish wrapper/web-map relationships without equating similar titles.
    apps = {(s['root'], i['id']) for s in inventories[:2] for i in s['items']
            if i['type'] in ('Web Mapping Application', 'Web Experience', 'Dashboard', 'StoryMap', 'Web Map', 'Hub Site Application')}
    def app_data(pair):
        root, item = pair
        return {'root': root, 'id': item, 'data': compact_config(api(root, 'content/items/' + item + '/data'))}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        configs = list(pool.map(app_data, sorted(apps)))
    save('app-configs.json', configs)
    print('Configurations:', len(configs), flush=True)
