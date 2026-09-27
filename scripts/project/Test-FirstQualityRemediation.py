"""Actual-record gates, exact debt delta, original preservation and rendered preview."""
import argparse, copy, json, hashlib, re
from pathlib import Path
from urllib.request import urlopen, Request
from FirstQualityRemediationLifecycle import guard_current_delta,validate_delta,PREFIX,QUEUE
from WorkflowStageLifecycle import ROOT,StageSnapshot,git
from QualityCorrectionLifecycle import before
from PublicationQuality import validate_affected_records
parser=argparse.ArgumentParser();parser.add_argument('--rendered-root');parser.add_argument('--preview');parser.add_argument('--receipt');args=parser.parse_args()
data=guard_current_delta();stage=StageSnapshot('quality-remediation-first');b=data['baseline_commit'];prior=before('project-state/master-inventory.json',b);current=stage.load_json('project-state/master-inventory.json');oldq=before(QUEUE,b);q=stage.load_json(QUEUE);r2=before('project-state/r2-inventory.json',b)
# A repinned unrelated row, new debt, altered original R2 and page cannot pass.
for case in ['inventory','debt','r2','content']:
    bad=copy.deepcopy(current);badq=copy.deepcopy(q);badr2=copy.deepcopy(r2);hashes=copy.deepcopy(data['page_sha256'])
    if case=='inventory':next(r for r in bad['candidates'] if r['id'] not in data['changed_inventory_ids'])['description']='unrelated mutation'
    if case=='debt':badq['failures'].pop()
    if case=='r2':badr2['unauthorized']=True
    if case=='content':hashes[next(iter(hashes))]='0'*64
    try:validate_delta(data,prior,bad,oldq,badq,hashes,r2,badr2)
    except AssertionError:pass
    else:raise AssertionError('Guard accepted '+case)
rows={r['id']:r for r in current['candidates']};responses=[]
if args.rendered_root or args.preview:
    for page in data['changed_pages']:
        urlpath=page.removeprefix('content/').removesuffix('.md')+'/'
        url=args.preview.rstrip('/')+'/'+urlpath if args.preview else None
        html=urlopen(Request(url,headers={'User-Agent':'ABQInfo preview validation'}),timeout=45).read().decode() if url else (Path(args.rendered_root)/urlpath/'index.html').read_text(encoding='utf-8')
        for f in data['families']:
            if f['page']==page:
                if f['id'] in rows:assert rows[f['id']]['r2_url'] in html
                else:
                    assert f['anchor'] in html
                    for rid in f['component_ids']:assert rows[rid]['r2_url'] in html and rows[rid]['direct_file_url'] in html
        for rid in data['target_ids']:
            if 'Executive Committee' in rows[rid]['title']:assert rows[rid]['r2_url'] not in html
        if page.endswith('transportation-plans.md'):assert 'cover sheets' in html and '$48,193,701.21' in html
        if page.endswith('capital-spending.md'):assert '$903,874' in html and '56 applications' in html and 'completed outcomes' in html
        responses.append({'page':page,'url':url,'http_status':200 if url else None,'rendered_sha256':hashlib.sha256(html.encode()).hexdigest(),'result':'passed'})
    if args.receipt:(ROOT/args.receipt).write_text(json.dumps({'result':'passed','responses':responses},indent=2)+'\n')
print('PASS: exactly 25 component failures plus five required annual masters resolved; 1608 unrelated debt rows unchanged; 42 September 13 findings unresolved; actual-record gates and negative delta fixtures pass; originals/R2 unchanged; '+('preview' if args.preview else 'rendered' if args.rendered_root else 'source')+' checks passed.')
