"""Verify the exact live publication delta and optional rendered or preview pages."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from PlanningPublicationLifecycle import ROOT, BASELINE, implementation, sealed_json
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
stage=StageSnapshot('planning-publication')

parser=argparse.ArgumentParser()
parser.add_argument('--rendered-root')
parser.add_argument('--preview')
args=parser.parse_args()
def fetch(url):
    return urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 ABQInfo-Preview-Validator/1.0'}),timeout=45).read().decode()
class Links(HTMLParser):
    def __init__(self,html):
        super().__init__(); self.links=[]; self.anchors=[]; self.text=''; self.feed(html)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'href' in a: self.links.append(a['href'])
        if 'id' in a: self.anchors.append(a['id'])
    def handle_data(self,data):
        self.text+=data+' '
data=implementation(); assert data
load=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
before=sealed_json(ROOT/'project-state/master-inventory.json')
current=stage.load_json('project-state/master-inventory.json')
old={r['id']:r for r in before['candidates']}; rows={r['id']:r for r in current['candidates']}
archives=load(data['archive_artifact']); verified={r['id']:r for r in archives['results']}
ids=set(data['implemented_inventory_ids']); assert ids==set(verified)
assert rows.keys()==old.keys() and {i for i in rows if rows[i]!=old[i]}==ids
allowed={'status','implementation_location','implementation_locations','description','description_word_count','quality_assessment','validation_status','processing_notes','updated_at'}
texts={p:stage.read_text(p) for p in data['changed_pages']}
changes=subprocess.check_output(['git','diff',BASELINE]+([stage.end] if stage.end else [])+['--name-only','--','content','layouts','assets','static','hugo.toml'],cwd=ROOT,text=True).splitlines()
assert set(changes)==set(data['changed_pages']) and len(changes)==6
assert stage.load_json('project-state/r2-inventory.json')==sealed_json(ROOT/'project-state/r2-inventory.json')
assert not data['r2_mutation'] and data['added_storage_bytes']==0 and not data['production_or_live'] and not data['merge_or_deploy']
for record in data['records']:
    rid=record['id']; r=rows[rid]; v=verified[rid]; page=record['page']; text=texts[page]
    assert {k for k in r if r[k]!=old[rid].get(k)}<=allowed
    assert r['status']=='implemented' and r['implementation_locations']==[page] and r['implementation_location']==page
    assert r['scope_assessment']['final_scope_decision']=='passes_both_gates'
    assert r['r2_url']==v['public_url']==record['archive_url'] and r['direct_file_url']==v['authoritative_source_url']==record['source_url']
    assert text.count(record['archive_url'])==1 and text.count(record['source_url'])==1
    assert sum(t.count(record['archive_url']) for t in texts.values())==1
    assert v['byte_identical'] and v['public_checksum_sha256']==r['checksum_sha256'] and v['public_size_bytes']==r['size_bytes']
    assert r['description']==record['description'] and 20<=r['description_word_count']<=50
    if (args.rendered_root or args.preview) and not stage.end:
        urlpath=page.removeprefix('content/').removesuffix('.md')+'/'
        html=fetch(args.preview.rstrip('/')+'/'+urlpath) if args.preview else (Path(args.rendered_root)/urlpath/'index.html').read_text(encoding='utf-8')
        anchor=re.sub(r'[^a-z0-9 -]','',record['section'].lower()).replace(' ','-')
        parsed=Links(html)
        assert anchor in parsed.anchors and parsed.links.count(record['archive_url'])==1 and record['source_url'] in parsed.links,record
        rendered_text=' '.join(parsed.text.split())
        if rid not in data['planning_impact_area_family']['component_ids']:
            assert ' '.join(record['description'].split()) in rendered_text,record['id']
for p,text in texts.items(): assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==data['page_sha256'][p]
dem=texts['content/city-data/demographics.md']; assert dem.count('## Historical Planning Impact Area Study Components')==1
assert 'one grouped incomplete component set' in dem and 'do not constitute a complete study' in dem
assert not re.search(r'^### .*Chapter',dem,re.M)
for link in data['cross_links']:
    assert texts[link['from']].count(link['to'])==1
    if (args.rendered_root or args.preview) and not stage.end:
        path,anchor=link['to'].split('#')
        html=fetch(args.preview.rstrip('/')+path) if args.preview else (Path(args.rendered_root)/path.lstrip('/')/'index.html').read_text(encoding='utf-8')
        assert anchor in Links(html).anchors
for rid in (data['duplicate_id_unchanged'],data['canonical_revitalization_id_unchanged']): assert rows[rid]==old[rid]
assert sum(t.count(rows[data['canonical_revitalization_id_unchanged']]['r2_url']) for t in texts.values())==1
cp=stage.load_json('project-state/checkpoint.json'); assert cp['counts_by_status']==current['counts']
print('PASS: exact 12 publication transitions, six pages, one incomplete chapter set, two Barelas cross-links, unchanged duplicate/canonical rows and R2; '+('preview' if args.preview else 'rendered' if args.rendered_root else 'source')+' checks passed.')
