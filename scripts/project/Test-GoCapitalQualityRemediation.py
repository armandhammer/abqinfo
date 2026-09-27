import argparse,copy,json,hashlib,re
from pathlib import Path
from urllib.request import urlopen,Request
from GoCapitalQualityRemediationLifecycle import guard_current_delta,validate_delta,PREFIX,QUEUE
from WorkflowStageLifecycle import ROOT,StageSnapshot,git
parser=argparse.ArgumentParser();parser.add_argument('--rendered-root');parser.add_argument('--preview');parser.add_argument('--receipt');args=parser.parse_args()
data=guard_current_delta();stage=StageSnapshot('go-capital-quality-remediation');base=data['baseline_commit']
def before(p):return json.loads(git('show',base+':'+p).decode('utf-8-sig'))
prior=before('project-state/master-inventory.json');current=stage.load_json('project-state/master-inventory.json');q=stage.load_json(QUEUE);oldq=before(QUEUE);r2=before('project-state/r2-inventory.json')
for case in ['unrelated_inventory','unrelated_debt','r2','page','wrong_population','negative_finding']:
    bad=copy.deepcopy(current);badq=copy.deepcopy(q);bad_r2=copy.deepcopy(r2);hashes=copy.deepcopy(data['page_sha256']);baddata=copy.deepcopy(data)
    if case=='unrelated_inventory':next(r for r in bad['candidates'] if r['id'] not in data['changed_inventory_ids'])['title']='changed'
    if case=='unrelated_debt':badq['failures'].pop()
    if case=='r2':bad_r2['changed']=True
    if case=='page':hashes[next(iter(hashes))]='0'*64
    if case=='wrong_population':baddata['target_ids'].pop()
    if case=='negative_finding':badq['september_13_reconciliation'][0]['prior_status']='passes'
    try:validate_delta(baddata,prior,bad,oldq,badq,hashes,r2,bad_r2)
    except (AssertionError,ValueError):pass
    else:raise AssertionError('Guard accepted '+case)
rows={r['id']:r for r in current['candidates']};responses=[]
if args.rendered_root or args.preview:
    for page in data['changed_pages']:
        path=page.removeprefix('content/').removesuffix('.md')+'/'
        url=args.preview.rstrip('/')+'/'+path if args.preview else None
        html=urlopen(Request(url,headers={'User-Agent':'ABQInfo remediation preview verification'}),timeout=60).read().decode('utf-8') if url else (Path(args.rendered_root)/path/'index.html').read_text(encoding='utf-8')
        for f in data['families']:
            if page==f['page']:
                assert re.search(r'\bid=["\']?'+re.escape(f['anchor'])+r'["\' >]',html),(page,f['anchor'])
                for i in f['component_ids']:
                    if i=='src-047e8956baad212d':assert rows[i]['r2_url'] not in html and rows[i]['direct_file_url'] not in html
                    else:assert rows[i]['r2_url'] in html and rows[i]['direct_file_url'] in html
                if f['master_id']:assert rows[f['master_id']]['r2_url'] in html and rows[f['master_id']]['direct_file_url'] in html
        if page.endswith('capital-spending.md'):
            assert '$52,514,950' in html and '$727.29 million' in html and '$56.19 million' in html and '$33 million' in html
            assert 'not an enacted or voter-approved final program' in html and 'not proof of ultimate spending' in html and 'Station 13' in html
        else:
            assert '/city-data/capital-spending/#' in html and all(rows[i]['r2_url'] not in html for i in data['target_ids'])
        responses.append({'page':page,'url':url,'http_status':200 if url else None,'rendered_sha256':hashlib.sha256(html.encode()).hexdigest(),'result':'passed'})
    if args.receipt:(ROOT/args.receipt).write_text(json.dumps({'result':'passed','responses':responses},indent=2)+'\n',encoding='utf-8')
print('PASS: 32 queue matches plus two required masters, six pages, four actual-record family gates; 1574/10 remaining; unrelated debt/findings and original R2 preserved; six negative delta fixtures; '+('preview' if args.preview else 'rendered' if args.rendered_root else 'source')+' checks passed.')
