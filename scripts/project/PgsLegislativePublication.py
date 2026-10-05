"""Three exact historical PGS originals and one bounded owner-review publication."""
import copy, json, sys, subprocess, hashlib
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G

TASK='pgs-legislative-publication-2026-10-05'
P='project-state/governance/'+TASK+'/'
BASE='5874a5bbfbe6cbaf7237ef86718a05fe3e6aaefb'
PAGE='content/development-land-use/area-sector-plans.md'
IDS=['src-f7c7bd5b273def22','src-68582bc4fe41fb4f','src-fcbe6a7ebcf916a1']
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value):
    target=G.ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def audit(paths):
    r=G.load(G.REGISTRY);a=G.load(r['audit_artifact']);indexed={x['path']:x for x in a['artifacts']}
    for p in paths:
        indexed[p]=dict(path=p,sha256=G.file_hash(p),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale='Execution evidence and accounting; no independent authority.')
    a['artifacts']=sorted(indexed.values(),key=lambda x:x['path']);save(r['audit_artifact'],a)
    r['audit_sha256']=G.file_hash(r['audit_artifact']);save(G.REGISTRY,r)
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'));audit([p.relative_to(G.ROOT).as_posix() for p in old])
    n=max(int(p.stem.split('-v')[1]) for p in old)+1;path=P+f'contract-v{n}.json'
    pop=G.load(P+'population-v4.json');c=G.resolve(pop,G.registry(),G.file_hash(G.REGISTRY));G.write_once(path,c)
    assert not c['conflicts'] and not c['unresolved_gates']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=pop['operation_classes'],events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population-v4.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path,len(c['governance_ids']),'rules')
def setup():
    pop=G.load(P+'population.json')
    pop['artifact_paths'] += [P+'population-v2.json','scripts/project/Test-PlannedGrowthStrategyHugoImplementation.py','scripts/project/Test-PlannedGrowthStrategyRenderedPage.py']
    G.write_once(P+'population-v2.json',pop)
    pop['operation_classes'].append('family_review')  # Deterministic queue regeneration only.
    pop['artifact_paths'] += [P+'population-v3.json',P+'phase-a-validation.log',P+'preview.png',P+'local-render.json']
    G.write_once(P+'population-v3.json',pop)
    pop['artifact_paths'] += [P+'population-v4.json','project-state/discovery/retained-source-audit-queue.json']
    G.write_once(P+'population-v4.json',pop)
    instruction='Explicit owner instruction 2026-10-05: publish exactly src-f7c7bd5b273def22 / O-2002-034, src-68582bc4fe41fb4f / O-2003-047, src-fcbe6a7ebcf916a1 / O-2004-007. Preserve the completed governed enacted-version review; do not reopen it. This new task replaces only the prior inventory-only stage restrictions for these three records. Phase A: freshly retrieve the specified exact City originals, verify expected bytes/SHA-256, upload without overwrite/delete under development-land-use/area-sector-plans, verify complete public GET, update provenance/accounting and integrate background-only archival into main under current R2 policy. Phase B from that main: add historical Enabling legislation grouping only under existing Citywide Growth Strategy on Area & Sector Plans, one archive/source entry per distinct act; preserve differing 2003/2004 tables, clarify study is historical analysis and only specific policies were enacted. No Word/duplicate variants, R-02-111/R-2002-112 or other records. Full validation, sealed history/governance, Hugo/rendered, public downloads, CURRENT separator and diff checks; inspect exact nonproduction preview; create one content PR with three enacted identities, relationship, section, objects/bytes and section preview link. Synchronize planning-snapshot to reviewed PR head; leave PR unmerged for owner review. No authority to merge/deploy content to production.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction',instruction=instruction,candidate_ids=IDS,expected_total_bytes=133251))
    r=G.registry();proposals={}
    names=['decision-pgs-legislative-resolution-2026-10-05','decision-planned-growth-strategy-decision-2026-09-19-277e4100-three-enacted-holds-resolved-2026-10-05','owner-pgs-legislative-resolution-2026-10-05']
    for old in r['entries'][:]:
        if old['governance_id'] not in names:continue
        replacement=old['binding_requirement']+' New explicit owner archival/publication authority replaces only the prior no-R2/no-visible/inventory-only phase boundary for the exact three IDs in '+P+'authority.json; all finality, quality, family, distinct-table and historical-evidence findings remain controlling. No research reopening or content merge authority.'
        gid=old['governance_id']+'-publication-authorized'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=replacement,consequences='Only exact three-record archival and manual-review content PR stage boundary changes; settled findings and every other population preserved.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=replacement,required_actions=[replacement],authority='Explicit current owner three-record archival and publication instruction',effective_date='2026-10-05')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,state='active',scope={'candidate_ids':IDS,'task_ids':[TASK]},authority='Explicit current owner publication instruction',decision_date='2026-10-05',effective_date='2026-10-05',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No content PR merge or production deployment.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='three-record authorized archival and owner-review PR'))
    save(G.REGISTRY,r)
    life=G.load('project-state/workflow-stage-lifecycle.json');life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/PgsLegislativePublication.py'],exact_delta_guard={'module':'PgsLegislativePublication','function':'guard'}))
    save('project-state/workflow-stage-lifecycle.json',life)
    audit(['project-state/workflow-stage-lifecycle.json']);refresh()
    G.active_check('mutation','archive',IDS)
def guard():
    from WorkflowStageLifecycle import StageSnapshot, git
    stage=StageSnapshot(TASK)
    pop=stage.load_json(P+'population-v4.json')
    a={r['id']:r for r in json.loads(G.git('show',BASE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        for field in ['source_url','direct_file_url','checksum_sha256','size_bytes','scope_assessment','quality_assessment','publication_quality_decision']:
            assert a[i].get(field)==b[i].get(field),(i,field)
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes']
    retained='project-state/discovery/retained-source-audit-queue.json'
    prior=json.loads(G.git('show',BASE+':'+retained));current=stage.load_json(retained)
    oldrows={r['source_url']:r for r in prior['records']};newrows={r['source_url']:r for r in current['records']}
    assert all(newrows.get(k)==v for k,v in oldrows.items()), 'Existing retained-source audits changed'
    additions=set(newrows)-set(oldrows)
    assert additions <= {b[i]['source_url'] for i in IDS}
    assert all(newrows[url]['candidate_id'] in IDS for url in additions)
    changes=git('diff',BASE,stage.end,'--name-only').decode().splitlines() if stage.end else G.changed_paths(BASE)
    assert set(changes)<=set(pop['artifact_paths'])|set(pop['pages']),set(changes)-set(pop['artifact_paths'])-set(pop['pages'])
    old=G.git('show',BASE+':'+PAGE)+'\n';live=stage.read_text(PAGE)
    if '### Enabling legislation\n' in live:
        start=live.index('### Enabling legislation\n');end=live.index('## Downtown Neighborhood Area',start)
        assert live[:start]+live[end:]==old,'Unrelated visible changes'
        block=live[start:end]
        for x in pop['archive_objects']:assert block.count('https://files.abqinfo.com/'+x['r2_key'])==1
        assert all(x in block for x in ['O-2002-034','O-2003-047','O-2004-007','historical','not current consolidated law','did not make the entire study law'])
        assert 'R-02-111' not in block and '.doc' not in block
    else:assert live==old
    if (G.ROOT/(P+'archive-result.json')).exists():
        d=stage.load_json(P+'archive-result.json')
        if d['state']=='complete':
            assert len(d['results'])==3 and d['added_bytes']==133251
            for x in d['results']:assert x['byte_identical'] and x['public_size_bytes']==x['expected_size_bytes'] and x['public_checksum_sha256']==x['expected_checksum_sha256']
    print('PASS: exact three PGS records, original evidence, additive section and archive byte guards')
def implement():
    G.active_check('mutation','content_implementation',IDS,[PAGE])
    assert G.load(P+'archive-result.json')['state']=='complete'
    assert G.git('rev-parse','HEAD')==G.git('rev-parse','origin/main'), 'Phase B starts from post-archive authoritative main'
    block='''### Enabling legislation

The broader Planned Growth Strategy study is historical planning analysis. These three ordinances identify specific measures the City enacted; they did not make the entire study law. The linked originals are historical enactments, not current consolidated law or current forecasts.

- [O-2002-034 — Growth-management framework (F/S O-02-39 (2), 2002)](https://files.abqinfo.com/development-land-use/area-sector-plans/cabq-pgs-ordinance-o-2002-034.pdf)

  Established the City growth-management framework and advisory task force, with impact-fee principles, infrastructure and Capital Improvements Program (CIP) sequencing, a no-net-expense development policy, and intergovernmental coordination. [Official City original](https://www.cabq.gov/council/documents/pgs/o-39fs3.pdf)

- [O-2003-047 — Infrastructure and growth forecasts (O-03-132, 2003)](https://files.abqinfo.com/development-land-use/area-sector-plans/cabq-pgs-ordinance-o-2003-047.pdf)

  Adopted population, housing and employment forecast tables for growth-related capital planning and the land-use assumptions used for development fees. The original includes all three forecast exhibits. [Official City original](https://www.cabq.gov/council/documents/pgs/o-132fin.pdf)

- [O-2004-007 — Development Fees Act land-use assumptions (O-04-9, 2004)](https://files.abqinfo.com/development-land-use/area-sector-plans/cabq-pgs-ordinance-o-2004-007.pdf)

  Adopted the later land-use assumptions and forecast framework under the Development Fees Act for growth capital needs and development impact fees, with a five-year update requirement. Its population, housing and employment tables differ from the 2003 ordinance and are preserved here as a distinct enactment. [Official City original](https://www.cabq.gov/council/documents/pgs/o-9fin.pdf)

'''
    target=G.ROOT/PAGE;s=target.read_text(encoding='utf8');assert '### Enabling legislation' not in s
    target.write_text(s.replace('## Downtown Neighborhood Area',block+'## Downtown Neighborhood Area',1),encoding='utf8',newline='\n')
    descriptions=[line.strip().split(' [Official City original]')[0] for line in block.splitlines() if line.startswith('  ')]
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    requests=[]
    for i,description in zip(IDS,descriptions):
        requests.append(dict(id=i,changes=dict(status='implemented',description=description,implementation_location=PAGE,implementation_locations=[PAGE],validation_status='Historical enactment implemented on owner-review content branch; exact archive public bytes verified. Preview and full validation pending; not live.',processing_notes=rows[i]['processing_notes']+['2026-10-05: Individually identified historical enacted original in Enabling legislation under existing Citywide Growth Strategy; preserves study context and distinct 2003/2004 tables. Owner-review PR, no merge authority.'])))
    save('tmp/pgs-publication-updates.json',requests)
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests','tmp/pgs-publication-updates.json'],check=True)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='content_implementation',candidate_ids=IDS,action='implements',use_contract_record_rules=True,summary='Exactly three historical enactments added under existing Citywide Growth Strategy; study context unchanged; no consolidated-law claim.',evidence=PAGE));save(P+'implementation.json',plan)
    audit(['project-state/master-inventory.json']);refresh();queue();guard()
def queue():
    inv=G.load('project-state/master-inventory.json');q=G.load(P+'queue.json');approved=[r for r in inv['candidates'] if r['status']=='approved for addition']
    q.update(inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),recorded_at=now(),approved_count=len(approved),newly_approved_backlog=[r for r in q['newly_approved_backlog'] if r['id'] in {x['id'] for x in approved}],in_progress_publication={'task':TASK,'candidate_ids':IDS,'state':'content_pr_owner_review_pending'})
    save(P+'queue.json',q)
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],completed_item_range='Three historical PGS enacted originals archived and implemented on the bounded owner-review content branch; PR remains unmerged.',remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),resume_command='Read CURRENT and the PGS legislative publication receipt. Owner-review content PR is the only active publication; do not merge or deploy without subsequent owner approval.')
    save('project-state/checkpoint.json',cp)
    audit([P+'queue.json','project-state/checkpoint.json']);refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    audit(['project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']);refresh()
def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2];preview='.pages.dev' in url
    verification_only='--verification-only' in sys.argv[3:]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu'])
        page=browser.new_page(viewport=dict(width=1440,height=1100))
        response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
        result=page.evaluate('''() => {
          const h=document.getElementById('citywide-growth-strategy');let n=h.nextElementSibling;const nodes=[];
          while(n && n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}
          return {heading:h.innerText,text:nodes.map(n=>n.innerText).join('\\n'),links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth};
        }''')
        assert not result['overflow']
        archives=[x['url'] for x in result['links'] if x['url'].startswith('https://files.abqinfo.com/')];assert len(archives)==16
        pop=G.load(P+'population-v4.json')
        assert archives[-3:]==['https://files.abqinfo.com/'+x['r2_key'] for x in sorted(pop['archive_objects'],key=lambda x:IDS.index(x['candidate_id']))]
        for phrase in ['Enabling legislation','O-2002-034','O-2003-047','O-2004-007','did not make the entire study law','not current consolidated law','tables differ from the 2003 ordinance']:assert phrase in result['text'],phrase
        page.locator('#enabling-legislation').evaluate('(h) => h.scrollIntoView(true)')
        screenshot=G.ROOT/('tmp/pgs-final-head-preview.png' if verification_only else P+'preview.png' if preview else 'tmp/pgs-local.png');page.screenshot(path=str(screenshot),full_page=False)
        result.update(url=url,head_sha=G.git('rev-parse','HEAD'),rendered_at=now(),browser='Installed Google Chrome via Playwright',screenshot_sha256=hashlib.sha256(screenshot.read_bytes()).hexdigest())
        if verification_only:
            original=G.load(P+'preview.json');assert result['text']==original['text']
            normalize=lambda links:[x for x in links if x['text']!='#']
            assert normalize(result['links'])==normalize(original['links']), 'Final-head section differs from inspected preview'
            result['identical_to_inspected_preview']=True
        save('tmp/pgs-final-head-preview.json' if verification_only else P+('preview.json' if preview else 'local-render.json'),result);browser.close()
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':{'setup':setup,'refresh':refresh,'guard':guard,'implement':implement,'queue':queue,'render':render}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
