"""Governed correction of the existing Central Avenue historical master only."""
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

import TaskGovernance as G
import OwnerResources20261004 as S
from WorkflowStageLifecycle import StageSnapshot, git

TASK = 'central-avenue-master-correction-2026-10-04'
P = 'project-state/governance/' + TASK + '/'
BASE = '26068ab057e95de5e90c8fc98462b3f22e0ca8d8'
REVIEW = 'project-state/governance/central-station-area-family-resolution-2026-10-04/'
PAGE = 'content/development-land-use/area-sector-plans.md'
SCRIPT = 'scripts/project/CentralAvenueMasterCorrection.py'
IDS = G.load(REVIEW + 'receipt.json')['frozen_population']
OPS = ['content_implementation', 'content_removal', 'visitor_visible_change', 'governance_implementation', 'background_integration']

def save(path, value):
    S.save(path, value)

def refresh():
    registry = G.load(G.REGISTRY)
    for row in registry['entries']:
        if row['state'] == 'active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers') == ['/implementation']:
                    a['sha256'] = G.file_hash(a['path'])
    save(G.REGISTRY, registry)
    registered = {a['path'] for r in registry['entries'] for a in r['controlling_artifacts']}
    paths = [f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).glob('*') if f.is_file() and f.name != 'implementation.json' and f.relative_to(G.ROOT).as_posix() not in registered]
    S.audit(paths + [SCRIPT, 'project-state/CURRENT.md', 'project-state/workflow-stage-lifecycle.json'])
    versions = list((G.ROOT/P).glob('contract-v*.json'))
    n = max([int(f.stem.split('-v')[1]) for f in versions], default=0) + 1
    path = P + f'contract-v{n}.json'
    pop=P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json')
    subprocess.run([sys.executable, 'scripts/project/Resolve-TaskGovernance.py', 'resolve', '--population', pop, '--output', path], check=True)
    c = G.load(path)
    assert not c['conflicts'], c['conflicts']
    plan = G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects = {}
    for r in c['resolved_rules']:
        for x in r.get('constraints', []):
            subjects.setdefault(x['subject'], {})[x['field']] = x['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:
        e['governance_ids'] = c['governance_ids']
    if (G.ROOT/(P+'receipt.json')).exists():
        plan['completion_evidence'] = {gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=pop,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',supersession_proposals_path=P+'supersession.json',state='in_progress'))

def freeze():
    assert G.git('rev-parse','HEAD') == BASE
    outputs = ['population.json','authority.json','supersession.json','starting-state.json','implementation.json','receipt.json','public-verification.json','validation.log','local-render.json','preview-render.json','preview.png','preview.json','pr-body.md','review-state.json']
    artifacts = [P+x for x in outputs] + [P+f'contract-v{i}.json' for i in range(1,101)] + [SCRIPT,G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[PAGE],operation_classes=OPS,artifact_paths=artifacts))
    text = ('Current owner authorizes correction of the existing Central Avenue historical master section only, using the completed thirteen-record family review as binding without re-review. Retain eleven continuously paginated September 2017 City-commissioned public-comment report components in one curated historical master; identify the nonbinding draft and 2018 revised completed-study successor, with Route 66 Action Plan, Comprehensive Plan and IDO separate. Label Crabtree Infrastructure as a separate supporting assessment/draft. Remove the unresolved Urban3 scan from public presentation only; preserve its pending status, provenance, object and historical evidence. No R2 mutation or 2018 upload is authorized. The 2018 lead-download presentation remains deferred under the settled review recommendation. Prepare and inspect one Cloudflare nonproduction preview and one unmerged manual-review PR against main; synchronize planning-snapshot to its exact reviewed head. No unrelated content or new substantive disposition is authorized. Inventory implementation statuses remain approved pending manual review. This explicitly releases the previous task-only no-visible-change restrictions for this correction only, while retaining every substantive review finding and restriction outside this scope.')
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction dated 2026-10-04',candidate_ids=IDS,instruction=text,review_artifacts=[dict(path=REVIEW+x,sha256=G.file_hash(REVIEW+x)) for x in ['receipt.json','decisions.json','research.json','accounting.json']]))
    S.bind(P+'authority.json','owner-'+TASK,text,dict(candidate_ids=IDS,pages=[PAGE],task_ids=[TASK]))
    r = G.load(G.REGISTRY)
    proposals = {}
    for gid in ['owner-central-station-area-family-resolution-2026-10-04','decision-central-station-area-family-resolution-2026-10-04']:
        old = next(x for x in r['entries'] if x['governance_id']==gid)
        new = copy.deepcopy(old)
        newgid = gid+'-publication-exception'
        replacement = old['binding_requirement'] + ' Explicit current owner exception: the separately governed '+TASK+' may correct only the existing historical master under owner-'+TASK+'. All completed substantive findings, evidence, pending Urban3 blocker, R2 restrictions and historical task boundaries remain binding; no content merge is authorized.'
        proposals[gid] = dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=old['controlling_artifacts'],new_evidence=P+'authority.json',proposed_replacement=replacement,consequences='Only the existing master correction is authorized; original review evidence and dispositions are unchanged.',authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=newgid,supersession_evidence=P+'authority.json')
        new.update(governance_id=newgid,title=newgid,binding_requirement=replacement,required_actions=[replacement],authority='Explicit current owner narrowly bounded publication exception dated 2026-10-04',supersedes=gid)
        new['controlling_artifacts'] += [dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
        r['entries'].append(new)
    save(G.REGISTRY,r)
    save(P+'supersession.json',dict(proposals=proposals))
    r = G.load(G.REGISTRY)
    owner = next(x for x in r['entries'] if x['governance_id']=='owner-'+TASK)
    owner['controlling_artifacts'].append(dict(path=P+'supersession.json',sha256=G.file_hash(P+'supersession.json'),binding_pointers=['/']))
    save(G.REGISTRY,r)
    stages = G.load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id']=='current-separator-regression-2026-10-04'
    stages['stages'][-1]['end_commit']=BASE
    stages['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='CentralAvenueMasterCorrection',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    save(P+'starting-state.json',dict(baseline_commit=BASE,queue=G.load(REVIEW+'receipt.json')['queue'],review_sha256=G.file_hash(REVIEW+'decisions.json'),inventory_sha256=G.file_hash('project-state/master-inventory.json'),r2_sha256=G.file_hash('project-state/r2-inventory.json')))
    refresh()
    G.active_check('mutation','content_implementation',IDS,[PAGE])

def section(text):
    return text.split('## Central Avenue Station-Area Planning\n',1)[1].split('\n## Near Heights',1)[0]

def amend():
    pop=G.load(P+'population.json')
    pop['artifact_paths'] += [P+'population-v2.json','scripts/project/Invoke-ProjectValidation.ps1']
    G.write_once(P+'population-v2.json',pop)
    refresh()
    G.active_check('mutation','content_implementation',IDS,[PAGE])
    f=G.ROOT/PAGE
    t=f.read_text(encoding='utf8')
    t=t.replace('recording proposals presented before revision.','recording proposals presented before revision. [Archived project public-release page](https://web.archive.org/web/20171008130241id_/http://www.greatercentralave.org/overview/action-plan-report-drafts/).')
    t=t.replace('[City plans and publications](https://www.cabq.gov/planning/plans-publications) lists','The City’s published plan index lists')
    f.write_text(t,encoding='utf8',newline='\n')
    G.active_check('mutation','governance_implementation')
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1'
    t=f.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/CentralAvenueMasterCorrection.py" guard\nif ($LASTEXITCODE) { throw \'Central Avenue historical master correction exact-delta guard failed.\' }\nSet-StrictMode -Version Latest',1)
    f.write_text(t,encoding='utf8',newline='\n')
    refresh()

def implement():
    G.active_check('mutation','content_implementation',IDS,[PAGE])
    G.active_check('mutation','content_removal',[IDS[-1]],[PAGE])
    f=G.ROOT/PAGE
    text=f.read_text(encoding='utf8')
    old=section(text)
    urls=re.findall(r'https://files\.abqinfo\.com/[^)\s]+',old)
    assert len(urls)==13
    names=['Introduction and Action Plan','Station Types','West Central','Old Town','Downtown','East Downtown','University Area','Nob Hill','International District','Equity and Inclusion','Finance']
    links=' · '.join('['+name+']('+url+')' for name,url in zip(names,urls[:11]))
    new=('\n- **Central Avenue Station-Area Planning — September 2017 historical public-comment package**\n\n'
         '  This City-commissioned station-area and corridor strategies report connected ART investment with Central Avenue development, public-realm improvements, equity, financing and implementation priorities. Its eleven continuously paginated sections form one report released for public comment in September 2017. It was a nonbinding draft, not an adopted plan.\n\n'
         '  Official project provenance is established through City grant and procurement records, contemporaneous public-release evidence, and comparison with the revised study later delivered by the City. These eleven preserved originals remain useful together as the historical public-review package, recording proposals presented before revision. [Archived project public-release page](https://web.archive.org/web/20171008130241id_/http://www.greatercentralave.org/overview/action-plan-report-drafts/).\n\n'
         '  The 2018 revised completed study superseded this draft as the completed study; that relationship does not establish adoption of the proposed plan amendment. The adopted 2014 Route 66 Action Plan, Comprehensive Plan and Integrated Development Ordinance (IDO) remained separate governing instruments. The City’s published plan index lists the completed study separately from the adopted Route 66 plan.\n\n'
         '  **Preserved report components (eleven sections):** '+links+'\n\n'
         '  **Separate supporting draft:** [Infrastructure — Crabtree supporting assessment/draft]('+urls[11]+') examines corridor utility capacity and infrastructure assumptions. Released alongside Finance, it is a separate supporting assessment, not section 12 of the continuously paginated report; it is absent from the 2018 combined study.\n')
    f.write_text(text.replace(old,new),encoding='utf8',newline='\n')
    plan=G.load(P+'implementation.json')
    plan['events'].append(dict(operation='content_implementation',candidate_ids=IDS,governance_ids=plan['respected_governance_ids'],action='implements',summary='Implement settled historical master findings; retain twelve original archive links, separate Infrastructure, remove pending Urban3 presentation. No substantive review or inventory/R2 mutation.',evidence=REVIEW+'decisions.json',use_contract_record_rules=True))
    save(P+'implementation.json',plan)
    current=G.ROOT/'project-state/CURRENT.md'
    oldcurrent=current.read_text(encoding='utf8')
    links=oldcurrent[oldcurrent.index('[Receipt]'):]
    current.write_text('# Current project state\n\nCentral Avenue historical master correction prepared for manual PR review: eleven September 2017 City-commissioned public-comment report components grouped together; Crabtree Infrastructure separately labeled; unresolved Urban3 scan removed from presentation only. Binding family review unchanged. Queue: 12 approved / 351 pending. No owner substantive decision pending. No R2 mutations; 2018 lead-download publication remains deferred under the settled review. Do not merge or deploy without owner approval.\n\n[Correction task](governance/'+TASK+'/population.json) · '+links,encoding='utf8',newline='\n')
    save(P+'receipt.json',dict(task_id=TASK,state='prepared_for_manual_review',baseline_commit=BASE,visible_page=PAGE,report_components=IDS[:11],separate_infrastructure=IDS[11],removed_presentation_only=IDS[12],inventory_changes=0,queue=dict(approved=12,pending=351),r2=dict(added=0,deleted=0,overwritten=0,added_bytes=0),review_findings_unchanged=True,completed_study_download_deferred=True,merge_authorized=False))
    refresh()
    guard()

def verify():
    import concurrent.futures
    import urllib.request
    rows=G.load(REVIEW+'accounting.json')['rows'] if 'rows' in G.load(REVIEW+'accounting.json') else G.load(REVIEW+'accounting.json')['records']
    def one(r):
        url='https://files.abqinfo.com/'+r['r2_key']
        h=hashlib.sha256();size=0
        with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'ABQInfo public archive verification'}),timeout=180) as response:
            assert response.status==200
            while chunk:=response.read(1024*1024):
                h.update(chunk);size+=len(chunk)
        assert size==r['original_size_bytes'] and h.hexdigest()==r['original_sha256'],r['id']
        print(r['id'],size,'verified',flush=True)
        return dict(id=r['id'],url=url,size_bytes=size,sha256=h.hexdigest(),verified_at=datetime.now(timezone.utc).isoformat(),byte_identical=True)
    target=P+'public-verification.json'
    results=G.load(target)['retained_links'] if (G.ROOT/target).exists() else []
    for attempt in range(3):
        done={r['id'] for r in results}
        missing=[r for r in rows[:12] if r['id'] not in done]
        if not missing:
            break
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for future in concurrent.futures.as_completed([pool.submit(one,r) for r in missing]):
                try:
                    results.append(future.result())
                    results.sort(key=lambda r:IDS.index(r['id']))
                    save(target,dict(retained_links=results,all_verified=len(results)==12,r2_mutations=0))
                except Exception as error:
                    print('Attempt',attempt+1,'failed:',error,flush=True)
    assert len(results)==12,'Unfinished public-byte verification'
    save(P+'public-verification.json',dict(retained_links=results,all_verified=True,r2_mutations=0))

def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2]
    label='preview' if '.pages.dev' in url else 'local'
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport=dict(width=1440,height=1100))
        response=page.goto(url,wait_until='networkidle',timeout=90000)
        assert response.status==200
        result=page.evaluate(r'''() => {
          const h=document.getElementById('central-avenue-station-area-planning');
          const nodes=[]; let n=h.nextElementSibling;
          while(n && n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}
          return {heading:h.innerText,text:nodes.map(n=>n.innerText).join('\n'),
            links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),
            master_entries:nodes.flatMap(n=>Array.from(n.matches('ul')?n.children:[])).length,
            viewport:{width:innerWidth,height:innerHeight},overflow:document.documentElement.scrollWidth>innerWidth};
        }''')
        assert result['master_entries']==1 and not result['overflow']
        r2=[x['url'] for x in result['links'] if x['url'].startswith('https://files.abqinfo.com/')]
        assert len(r2)==12 and not any('impact-of-transit' in x for x in r2)
        assert 'not section 12' in result['text'] and 'nonbinding draft' in result['text']
        page.locator('#central-avenue-station-area-planning').scroll_into_view_if_needed()
        page.screenshot(path=str(G.ROOT/(P+'preview.png')),full_page=False)
        result.update(url=url,http_status=response.status,rendered_at=datetime.now(timezone.utc).isoformat(),browser='Google Chrome via Playwright',head_sha=G.git('rev-parse','HEAD'))
        save(P+label+'-render.json',result)
        browser.close()
    print(json.dumps(result,ensure_ascii=False))

def guard():
    stage=StageSnapshot(TASK)
    pop=stage.load_json(P+'population-v2.json')
    assert pop['candidate_ids']==IDS and pop['pages']==[PAGE] and pop['baseline_commit']==BASE
    paths=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert paths<=set(pop['artifact_paths'])|{PAGE},paths-set(pop['artifact_paths'])-{PAGE}
    visible={x for x in paths if x.startswith(('content/','layouts/','static/','assets/')) or x=='hugo.toml'}
    assert visible=={PAGE}
    before=git('show',BASE+':'+PAGE).decode('utf8').replace('\r\n','\n')
    after=stage.read_text(PAGE)
    assert before.replace(section(before),'')==after.replace(section(after),''),'Change outside Central section'
    oldurls=re.findall(r'https://files\.abqinfo\.com/[^)\s]+',section(before))
    newurls=re.findall(r'https://files\.abqinfo\.com/[^)\s]+',section(after))
    assert newurls==oldurls[:12] and len(newurls)==12
    assert section(after).count('\n- ')==1
    assert 'City-branded' not in section(after) and 'provenance remains under review' not in section(after)
    for phrase in ['eleven continuously paginated','City-commissioned','nonbinding draft','2018 revised completed study','not section 12','Separate supporting draft']:
        assert phrase in section(after),phrase
    for path in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert stage.read_bytes(path).replace(b'\r\n',b'\n')==git('show',BASE+':'+path).replace(b'\r\n',b'\n'),path
    assert not any(x.startswith(REVIEW) for x in paths),'Completed family evidence changed'
    print('Central Avenue master correction: exact section / thirteen-record scope / unchanged inventory and R2 passed')

if __name__=='__main__':
    globals()[sys.argv[1]]()
