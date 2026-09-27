"""Validate each actual corrected publication candidate and all seven PR pages."""
import argparse
import json
import re
from pathlib import Path
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from QualityCorrectionLifecycle import guard_current_delta
from WorkflowStageLifecycle import ROOT, StageSnapshot
from PublicationQuality import validate_affected_records

class Links(HTMLParser):
    def __init__(self, value):
        super().__init__(); self.links=[]; self.anchors=[]; self.text=''; self.feed(value)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'href' in a: self.links.append(a['href'])
        if 'id' in a: self.anchors.append(a['id'])
    def handle_data(self, data): self.text += data+' '

parser=argparse.ArgumentParser(); parser.add_argument('--rendered-root'); parser.add_argument('--preview'); args=parser.parse_args()
data=guard_current_delta(); stage=StageSnapshot('old-town-quality-correction')
rows={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
validate_affected_records([rows[rid] for rid in data['planning_publication_ids']])
original=stage.load_json('project-state/discovery/planning-documents-root-hugo-implementation-2026-09-26.json')
records=[r for r in original['records'] if r['id'] in data['planning_publication_ids']]
assert len(records)==11
archive=stage.load_json(original['archive_artifact']); verified={r['id']:r for r in archive['results']}
pages={p:stage.read_text(p) for p in data['pr_changed_pages']}
for record in records:
    r=rows[record['id']];v=verified[r['id']];text=pages[record['page']]
    assert r['status']=='implemented' and r['validation_status']=='passed'
    assert r['scope_assessment']['final_scope_decision']=='passes_both_gates'
    assert r['implementation_locations']==[record['page']]
    assert record['archive_url']==r['r2_url']==v['public_url'] and r['r2_url'].startswith('https://files.abqinfo.com/')
    assert record['source_url']==r['direct_file_url']==v['authoritative_source_url']
    assert v['byte_identical'] and v['public_checksum_sha256']==r['checksum_sha256'] and v['public_size_bytes']==r['size_bytes']
    assert text.count(r['r2_url'])==text.count(r['direct_file_url'])==1
    assert sum(t.count(r['r2_url']) for t in pages.values())==1
    assert r['description']==record['description'] and 20<=r['description_word_count']<=50
dem=pages['content/city-data/demographics.md']
assert 'one grouped incomplete component set' in dem and 'do not constitute a complete study' in dem
assert not re.search(r'^### .*Chapter',dem,re.M)
for link in original['cross_links']: assert pages[link['from']].count(link['to'])==1
if (args.rendered_root or args.preview) and not stage.end:
    rendered={}
    for page in data['pr_changed_pages']:
        path=page.removeprefix('content/').removesuffix('.md')+'/'
        if args.preview:
            url=args.preview.rstrip('/')+'/'+path
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 ABQInfo-Preview-Validator'}),timeout=45) as response:
                assert response.status==200;value=response.read().decode()
        else:value=(Path(args.rendered_root)/path/'index.html').read_text(encoding='utf-8')
        rendered[page]=Links(value)
    for record in records:
        parsed=rendered[record['page']]
        anchor=re.sub(r'[^a-z0-9 -]','',record['section'].lower()).replace(' ','-')
        assert anchor in parsed.anchors
        assert parsed.links.count(record['archive_url'])==1 and parsed.links.count(record['source_url'])==1
        if record['id'] not in original['planning_impact_area_family']['component_ids']:
            assert ' '.join(record['description'].split()) in ' '.join(parsed.text.split())
    for rid in data['excluded_ids']:
        for parsed in rendered.values():
            assert all(rows[rid][k] not in parsed.links for k in ('r2_url','direct_file_url','source_url'))
    for page in ('content/development-land-use/projects.md','content/development-land-use/zoning-ido.md'):
        assert 'old-town-regulatory-review' not in rendered[page].anchors and 'old-town-virtual-task-force-records' not in rendered[page].anchors
        assert not any('#old-town-regulatory-review' in u or '#old-town-virtual-task-force-records' in u for u in rendered[page].links)
    for link in original['cross_links']:
        path,anchor=link['to'].split('#');page='content/'+path.strip('/')+'.md'
        assert anchor in rendered[page].anchors
print('PASS: actual-record quality gate on eleven Planning originals; four Old Town exclusions; seven PR pages; immutable provenance/R2; approved hashes, original qualifications, descriptions, archive/source links and Barelas anchors; '+('preview' if args.preview else 'rendered' if args.rendered_root else 'source')+' checks passed.')
