"""Durable exact-population setup for Central Avenue provenance research."""
import json
import sys
from pathlib import Path
import subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent))
from TaskGovernance import digest, file_hash, load, write_once

ROOT = Path(__file__).resolve().parents[2]
TASK = 'central-station-area-family-resolution-2026-10-04'
BASE = 'project-state/governance/' + TASK
IDS = ['src-c1d5a2b0b33b331a','src-5f3ea18d2262dd4e','src-80ee860e3cfa60bf','src-bad7cd0818045625','src-2641b5b13214d7ee','src-5ade756c56baac45','src-ed916e54f80ece6f','src-863e82803d9e7cac','src-c070ab7e5a4a2622','src-2bbfb64ecf6455b3','src-d7b006f3aceaa405','src-61107c696c0e35b5','src-e0748ccf7ebc1a77']

def save(path, value):
    (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def refresh():
    import OwnerResources20261004 as S
    paths=[p.relative_to(ROOT).as_posix() for p in (ROOT/BASE).rglob('*') if p.is_file() and p.name!='implementation.json']
    S.audit(paths)
    n=max(int(p.stem.split('-v')[1]) for p in (ROOT/BASE).glob('contract-v*.json'))+1
    contract=BASE+f'/contract-v{n}.json'
    versions=list((ROOT/BASE).glob('population-v*.json'))
    pop=max(versions,key=lambda p:int(p.stem.split('-v')[1])).relative_to(ROOT).as_posix() if versions else BASE+'/population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',pop,'--output',contract],check=True,stdout=subprocess.DEVNULL)
    c=load(contract); p=load(BASE+'/implementation.json')
    p.update(contract=contract,contract_sha256=file_hash(contract),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'])
    for e in p['events']:e['governance_ids']=c['governance_ids']
    save(BASE+'/implementation.json',p)
    save('project-state/governance/active-task.json',dict(population=pop,contract=contract,contract_sha256=file_hash(contract),implementation=BASE+'/implementation.json',state='in_progress'))
    print(contract)

def history():
    sources=['project-state/near-complete-review-decisions-2026-08-20.json','project-state/near-complete-review-archive-plan-2026-08-20.json','project-state/near-complete-review-public-validation-2026-08-20.json','project-state/discovery/codex-human-review-followup-queue.json']
    sources += [p.relative_to(ROOT).as_posix() for p in (ROOT/'project-state/discovery/background-followup-2026-09-26').glob('*.json')]
    sources += [a[0] for a in load(BASE+'/contract-v1.json')['controlling_artifacts'] if a[0].startswith('project-state/discovery/')]
    out=[]
    def selected(v):
        result=[]
        if isinstance(v,dict):
            if any(i in json.dumps(v,ensure_ascii=False) for i in IDS) and (any(v.get(k) in IDS for k in ['id','candidate_id','document_id']) or any(k in v for k in ['family_id','family'])):
                return [v]
            for x in v.values():result+=selected(x)
        elif isinstance(v,list):
            for x in v:result+=selected(x)
        return result
    for path in sorted(set(sources)):
        v=load(path); matches=selected(v)
        out.append(dict(path=path,sha256=file_hash(path),matches=matches))
    save(BASE+'/existing-evidence.json',out)
    for x in out:
        if x['matches']:print(x['path'],json.dumps(x['matches'],ensure_ascii=False)[:12000])

def inspect():
    import hashlib
    sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'))
    import pymupdf
    evidence=[]
    for x in load(BASE+'/starting-state.json')['rows']:
        r=x['row'];p=ROOT/r['local_path'];data=p.read_bytes()
        assert len(data)==r['size_bytes'] and hashlib.sha256(data).hexdigest()==r['checksum_sha256']
        with pymupdf.open(p) as d:
            texts=[page.get_text() for page in d]
            e=dict(id=r['id'],sha256=r['checksum_sha256'],size_bytes=len(data),pages=len(d),words=len(' '.join(texts).split()),metadata=d.metadata,first_pages=texts[:3],last_pages=texts[-2:],uri_links=[link['uri'] for page in d for link in page.get_links() if 'uri' in link])
            (ROOT/BASE/(r['id']+'.txt')).write_text('\n\f\n'.join(texts),encoding='utf8')
            d[0].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(ROOT/BASE/(r['id']+'.png'))
            evidence.append(e)
            print(json.dumps(e,ensure_ascii=False))
    save(BASE+'/pdf-inspection.json',evidence)

def fetch():
    import hashlib, urllib.request, concurrent.futures
    from datetime import datetime, timezone
    from html.parser import HTMLParser
    from urllib.parse import urljoin
    tasks=load(BASE+'/'+sys.argv[2])
    def one(t):
        e=dict(t,retrieved_at=datetime.now(timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(urllib.request.Request(t['url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo provenance research)'}),timeout=40) as r:
                data=r.read(150000001); assert len(data)<150000001
                e.update(http_status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            suffix='pdf' if data.startswith(b'%PDF') else 'html'
            path=BASE+f"/evidence-{t['n']}.{suffix}"
            (ROOT/path).write_bytes(data);e['witness']=path
            if suffix=='pdf':
                sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
                with pymupdf.open(stream=data,filetype='pdf') as d:
                    text='\n\f\n'.join(p.get_text() for p in d);e.update(pages=len(d),words=len(text.split()),metadata=d.metadata)
                    (ROOT/BASE/f"evidence-{t['n']}.txt").write_text(text,encoding='utf8')
                    d[0].get_pixmap().save(ROOT/BASE/f"evidence-{t['n']}.png")
            else:
                class Links(HTMLParser):
                    def __init__(self): super().__init__();self.links=[]
                    def handle_starttag(self,tag,attrs):
                        if tag=='a':
                            a=dict(attrs)
                            if 'href' in a:self.links.append(urljoin(e['final_url'],a['href']))
                p=Links();p.feed(data.decode('utf8',errors='replace'));e['links']=p.links
        except Exception as error:e['error']=str(error)
        return e
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for e in pool.map(one,tasks):
            out.append(e);save(BASE+'/'+sys.argv[3],out);print(e['n'],e.get('http_status'),e.get('pages'),e.get('size_bytes'),e.get('error'),flush=True)

def compare():
    import re,difflib,hashlib
    sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
    combined=pymupdf.open(ROOT/BASE/'evidence-3.pdf')
    rows={x['id']:x['row'] for x in load(BASE+'/starting-state.json')['rows']}
    def norm(text):
        text=text.replace('DRAFT FOR PUBLIC COMMENT','').replace('DRAFT FOR COMMENT','').replace('\u00ad','')
        return re.findall(r'\w+|[^\w\s]',text)
    offset=0;out=[]
    for rid in IDS[:11]:
        with pymupdf.open(ROOT/rows[rid]['local_path']) as d:
            pages=[]
            for i,p in enumerate(d):
                old=norm(p.get_text());new=norm(combined[offset+i].get_text())
                changes=[]
                for tag,a,b,c,e in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
                    if tag!='equal':changes.append(dict(kind=tag,old=' '.join(old[a:b]),new=' '.join(new[c:e])))
                pages.append(dict(local_page=i+1,official_2018_page=offset+i+1,equal_after_draft_label_normalization=old==new,changes=changes))
            out.append(dict(id=rid,pages=len(d),official_page_start=offset+1,official_page_end=offset+len(d),unchanged_text_pages=sum(p['equal_after_draft_label_normalization'] for p in pages),page_comparisons=pages))
            offset+=len(d)
    assert offset==len(combined)==237
    save(BASE+'/evidence-52.json',dict(method='Every page compared in original order; remove public-comment labels, soft hyphens and whitespace only; retain all substantive wording, numbers and punctuation.',official_document=load(BASE+'/evidence-42.json'),records=out,infrastructure_absent_from_combined=True))
    for r in out:
        print(r['id'],r['unchanged_text_pages'],'/',r['pages'])
        for p in r['page_comparisons']:
            if p['changes']:print('PAGE',p['local_page'],json.dumps(p['changes'],ensure_ascii=False)[:4000])

def setup_authority():
    import OwnerResources20261004 as S
    pop=load(BASE+'/population-v2.json')
    text='Current user authorizes a new governed background provenance/family-resolution review for exactly the thirteen Central Avenue IDs in this population: deep original-PDF and authoritative-source research, family/finality and current mission/quality findings, evidence-based background inventory dispositions, deterministic accounting and complete validation. No visitor-visible changes, new population, R2 upload/deletion/overwrite/replacement, or owner preference as proof of provenance. Clean background-only integration into main and synchronization of chatgpt/planning-snapshot are explicitly authorized. Preserve all original bytes, provenance, prior source/R2 history and settled governance; register any new binding decision with exact evidence.'
    write_once(BASE+'/authority.json',dict(authority='Explicit current user instruction dated 2026-10-04',candidate_ids=IDS,instruction=text))
    S.bind(BASE+'/authority.json','owner-'+TASK,text,dict(candidate_ids=IDS,task_ids=[TASK]))
    r=load('project-state/governance-registry.json')
    row=next(x for x in r['entries'] if x['governance_id']=='owner-'+TASK)
    row['authority']='Explicit current user Central Avenue family-resolution instruction dated 2026-10-04'
    save('project-state/governance-registry.json',r)
    stages=load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id']=='pr210-postmerge-closeout-2026-10-04'
    stages['stages'][-1]['end_commit']=pop['baseline_commit']
    stages['stages'].append(dict(id=TASK,baseline_commit=pop['baseline_commit'],regression_scripts=['scripts/project/CentralStationAreaFamilyResolution.py'],exact_delta_guard=dict(module='CentralStationAreaFamilyResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    path=ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=path.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/CentralStationAreaFamilyResolution.py" guard\nif ($LASTEXITCODE) { throw \'Central Avenue exact-population background guard failed.\' }\nSet-StrictMode -Version Latest',1)
    path.write_text(t,encoding='utf8',newline='\n')
    # Refresh only the validation runner implementation hash changed by this stage.
    for row in r['entries']:
        for a in row['controlling_artifacts']:
            if a['path']=='scripts/project/Invoke-ProjectValidation.ps1' and a.get('binding_pointers')==['/implementation']:a['sha256']=file_hash(a['path'])
    save('project-state/governance-registry.json',r)
    S.audit(['project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1'])
    refresh()

def guard():
    from WorkflowStageLifecycle import StageSnapshot,git
    from TaskGovernance import changed_paths
    stage=StageSnapshot(TASK)
    pop=stage.load_json(BASE+'/population-v3.json'); baseline=pop['baseline_commit']
    assert pop['candidate_ids']==IDS and len(set(IDS))==13
    stage.assert_no_visible_changes(baseline, subprocess.check_output(['git','rev-parse',baseline+':content'],text=True).strip())
    for p in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert stage.read_bytes(p).replace(b'\r\n',b'\n')==git('show',baseline+':'+p).replace(b'\r\n',b'\n'),p
    before=json.loads(git('show',baseline+':project-state/master-inventory.json'))
    after=stage.load_json('project-state/master-inventory.json')
    a={x['id']:x for x in before['candidates']};b={x['id']:x for x in after['candidates']}
    assert a.keys()==b.keys()
    assert {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        for k in ['checksum_sha256','size_bytes','local_path','r2_key','r2_url','r2_etag','r2_last_modified']:
            assert a[i].get(k)==b[i].get(k),(i,k)
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes']
    paths=set(git('diff',baseline,stage.end,'--name-only').decode().splitlines()) if stage.end else set(changed_paths(baseline))
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    print('Central Avenue exact 13-record boundary: passed; zero visible/R2 delta')

if __name__ == '__main__' and len(sys.argv)>1:
    {'refresh':refresh,'history':history,'inspect':inspect,'fetch':fetch,'compare':compare,'setup-authority':setup_authority,'guard':guard}[sys.argv[1]]()
elif __name__ == '__main__' and (ROOT/(BASE+'/authority.json')).exists():
    guard()
elif __name__ == '__main__':
    inventory = load('project-state/master-inventory.json')
    rows = inventory['documents'] if 'documents' in inventory else inventory['candidates']
    selected = [r for r in rows if r['id'] in IDS]
    assert len(selected) == 13
    outputs = ['population.json','starting-state.json','authority.json','implementation.json','progress.json','existing-evidence.json','research.json','decisions.json','accounting.json','receipt.json','validation.log']
    pop = dict(task_id=TASK, baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','consolidation','governance_implementation','background_integration'],artifact_paths=[BASE+'/'+p for p in outputs]+[BASE+f'/contract-v{i}.json' for i in range(1,21)]+['scripts/project/CentralStationAreaFamilyResolution.py','project-state/master-inventory.json','project-state/governance/active-task.json','project-state/governance-registry.json','project-state/governance/audit-2026-09-27/artifact-audit.json','project-state/CURRENT.md'])
    write_once(BASE+'/population.json',pop)
    write_once(BASE+'/starting-state.json',dict(baseline_commit=pop['baseline_commit'],remote_refs={'main':pop['baseline_commit'],'chatgpt/planning-snapshot':pop['baseline_commit']},remote_verified_by='git ls-remote origin refs/heads/main refs/heads/chatgpt/planning-snapshot',rows=[{'id':r['id'],'row_sha256':digest(r),'row':r} for r in selected],inventory_sha256=file_hash('project-state/master-inventory.json'),active_task=load('project-state/governance/active-task.json')))
    print(json.dumps(selected,ensure_ascii=False,indent=2))
