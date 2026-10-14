"""Task-local coverage comparison. Recommendations do not alter inventory decisions."""
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).parent
ROOT = OUT.parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name, data): (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def ids(value): return set(re.findall(r'(?i)(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])', str(value).lower()))

inventory = read(ROOT/'project-state/master-inventory.json')['candidates']
catalog = read(OUT/'catalog.json')
configs = read(OUT/'app-configs.json')
pages = read(OUT/'official-pages.json')['pages'] + read(OUT/'catalog-pages.json')
public = {str(p.relative_to(ROOT)).replace('\\','/'): p.read_text(encoding='utf-8') for p in (ROOT/'content').rglob('*.md')}
by_id, by_url = collections.defaultdict(list), collections.defaultdict(list)
for c in inventory:
    for key in ('source_url', 'direct_file_url', 'r2_url'):
        url = c.get(key) or ''
        for i in ids(url):
            if c not in by_id[i]: by_id[i].append(c)
        if url: by_url[url.rstrip('/')].append(c)
linked_ids = collections.defaultdict(set)
for path, text in public.items():
    for i in ids(text): linked_ids[i].add(path)
for page in pages:
    for path, text in public.items():
        if page['url'] in text:
            for i in ids(page.get('body','')+' '+page.get('resolved_url','')): linked_ids[i].add(path+' (official wrapper)')
    for c in by_url.get(page['url'].rstrip('/'),[]):
        for i in ids(page.get('resolved_url','')):
            if c not in by_id[i]: by_id[i].append(c)

deps = {}
for config in configs:
    deps[(config['root'], config['id'])] = ids(json.dumps([config['data'].get('body',{}),config.get('resources_config',{})])) - {config['id']}
components = collections.defaultdict(set)
for (root, app), children in deps.items():
    if app in linked_ids:
        todo, seen = list(children), set()
        while todo:
            child = todo.pop()
            if child in seen: continue
            seen.add(child); components[child].add(app)
            todo.extend(deps.get((root, child),set()) - seen)

items = {}
system = []
for s in catalog['searches'][:2]:
    for item in s['items']:
        if item['owner'].lower().startswith('esri'):
            system.append({'root':s['root'],'id':item['id'],'title':item['title'],'owner':item['owner']}); continue
        item_key = item['id']
        row = items.setdefault(item_key, {'id':item_key,'title':item['title'],'type':item['type'],
                              'deployments':[], 'inventory':[], 'published_pages':sorted(linked_ids[item_key]),
                              'component_of_linked_apps':sorted(components[item_key])})
        row['deployments'].append({'root':s['root'],'url':item.get('url'),'owner':item['owner'],
                                   'title':item['title'],'modified':item['modified']})
        matches = by_id[item_key]
        for match in by_url.get((item.get('url') or '').rstrip('/'),[]):
            if match not in matches: matches = matches + [match]
        row['inventory'] = [{'id':x['id'],'status':x['status'],'title':x['title'],
                             'exclusion_reason':x.get('exclusion_reason'),'r2_key':x.get('r2_key')} for x in matches]
        if matches and all(x['status'] in ('excluded','duplicate','superseded') for x in matches):
            row['coverage'] = 'inventory_' + ','.join(sorted(set(x['status'] for x in matches)))
        elif any('(official wrapper)' not in page for page in row['published_pages']): row['coverage'] = 'directly_linked_live_resource'
        elif row['published_pages']: row['coverage'] = 'reachable_via_linked_official_page'
        elif row['component_of_linked_apps']: row['coverage'] = 'component_of_linked_resource'
        elif matches:
            row['coverage'] = 'inventory_' + ','.join(sorted(set(x['status'] for x in matches)))
        else: row['coverage'] = 'not_directly_cataloged'

r2 = read(ROOT/'project-state/r2-inventory.json')
r2by = {x['key']:x for x in r2['objects']}
static = []
related = []
for c in inventory:
    if not any(t in json.dumps([c.get('agency'),c.get('source_url'),c.get('title')]).lower() for t in ['mrcog','mrmpo','mid-region']): continue
    related.append(c['id'])
    if c.get('r2_key') and re.search(r'\b(maps?|traffic|counts?|forecasts?|xlsx?|csv|geospatial|data)\b', (str(c.get('title'))+' '+str(c.get('file_type'))).lower()):
        o = r2by.get(c['r2_key'])
        static.append({'id':c['id'],'title':c['title'],'status':c['status'],'source_url':c.get('source_url'),
                       'r2_key':c['r2_key'],'checksum_sha256':c.get('checksum_sha256'),
                       'recorded_object_size':o.get('size_bytes') if o else None,
                       'object_present_in_snapshot':bool(o),
                       'published_pages':[path for path,text in public.items() if (c.get('r2_url') or 'NO_MATCH') in text]})

result = {'catalog_retrieved_at':catalog['retrieved_at'],'r2_snapshot_generated_at':r2['generated_at'],
          'r2_snapshot_only':True,'system_item_count':len(system),'system_items':system,
          'unique_local_item_count':len(items),'counts':dict(collections.Counter(x['coverage'] for x in items.values())),
          'items':sorted(items.values(),key=lambda x:(x['type'],x['title'])), 'archived_static_maps_data':static,
          'limitations':['Public item searches include drafts and components; public sharing is not editorial approval.',
                         'Same item ID on two portals is recorded as alternate deployment, not byte-equivalence.',
                         'Metadata/configuration inspected; interactive rendering unavailable.',
                         'Archive reconciliation uses authoritative local R2 snapshot; no live storage listing or upload.']}
save('reconciliation.json',result)

# Freeze exact comparisons before editorial review; retain the initial supplied-item contract.
population = read(OUT/'population.json')
population['candidate_ids'] = sorted(set(related + [x['id'] for x in inventory if any(i in by_id and x in by_id[i] for i in items)] +
                                         ['arcgis-'+i for i in items if not by_id[i]]))
population['pages'] = []  # Report recommends placement only; no public content mutation.
population['artifact_paths'] += [str(OUT.relative_to(ROOT)).replace('\\','/')+'/'+n for n in
                               ['population-v2.json','contract-v2.json','portals.json','official-pages.json','app-configs.json',
                                'groups.json','catalog-pages.json','roadway-service.json','reconcile.py','planning-service.json',
                                'layer-checks.json','static-item-checks.json']]
if '--no-population' not in sys.argv: save('population-v2.json', population)
print(json.dumps({k:result[k] for k in ['system_item_count','unique_local_item_count','counts']}))
print('Archived static map/data records:',len(static),'Population:',len(population['candidate_ids']))
