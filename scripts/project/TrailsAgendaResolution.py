"""Exactly scoped Trails PID agenda factual review and background accounting."""
import json
import sys
import subprocess
import copy
import gzip
import hashlib
import urllib.request
import urllib.error
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/project'))
from TaskGovernance import load, file_hash, population, digest
import TaskGovernance as G
from SourceHoldResolution import audit, bind

TASK = 'trails-pid-agenda-resolution-2026-10-05'
BASE = 'd63bba40f30e6c3265e86a737be0bacbdaf1b0f4'
DIR = 'project-state/governance/' + TASK
IDS = ['src-bc1dbb930feefaaf', 'src-b657a1bd0d19ffe8', 'src-a6bd9f4f6ae1cb40',
       'src-7e3d417f146c307b', 'src-c393d59e029b52e9', 'src-15bd43bb6a15984d']

def now(): return datetime.now(timezone.utc).isoformat()

def write(path, obj):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def freeze():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
    records = {r['id']: r for r in load('project-state/master-inventory.json')['candidates'] if r['id'] in IDS}
    assert set(records) == set(IDS) and all(r['status'] == 'pending review' for r in records.values())
    paths = ['population.json','authority.json','starting-state.json','baseline-records.json',
             'implementation.json','historical-evidence.json','governance-reconciliation.json',
             'retrievals.json','source-links.json','pdf-inspection.json','meeting-findings.json',
             'record-updates.json','queue.json','accounting.json','receipt.json','progress.json',
             'validation.log','rendered-check.json','integration-intent.json','summary.md']
    paths += ['contract-v%d.json' % n for n in range(1, 31)]
    paths += ['sources.json','fetch-tasks.json','research-searches.json']
    artifacts = [DIR + '/' + p for p in paths]
    artifacts += ['scripts/project/TrailsAgendaResolution.py', 'project-state/governance/active-task.json',
                  'project-state/master-inventory.json','project-state/checkpoint.json',
                  'project-state/CURRENT.md','project-state/ordinary-queue-current.json',
                  'project-state/governance-registry.json','project-state/governance/audit-2026-09-27/artifact-audit.json',
                  'project-state/discovery/consolidated-human-review-queue.json',
                  'project-state/discovery/consolidated-human-review-queue.md']
    write(DIR + '/population.json', dict(task_id=TASK, baseline_commit=BASE, candidate_ids=IDS,
          families=[], pages=[], operation_classes=['document_review','family_review','quality_assessment',
          'inventory_disposition','governance_implementation','background_integration'],artifact_paths=artifacts))
    write(DIR + '/baseline-records.json', records)
    write(DIR + '/starting-state.json', {'baseline_commit':BASE,'remote_main':BASE,'remote_planning_snapshot':BASE,
          'approved':0,'pending':348,'source_structural_blockers':27,'active_publication':False,'owner_decision_pending':False})
    write(DIR + '/progress.json', {'stage':'population_frozen','candidate_ids':IDS,'inventory_mutation':False})
    print(DIR)

def refresh():
    registry = load(G.REGISTRY)
    for row in registry['entries']:
        if row['state'] == 'active':
            for a in row['controlling_artifacts']:
                if a.get('binding_pointers') == ['/implementation']:
                    a['sha256'] = file_hash(a['path'])
    write(G.REGISTRY, registry)
    registered = {a['path'] for r in registry['entries'] for a in r['controlling_artifacts']}
    paths = [p.relative_to(ROOT).as_posix() for p in (ROOT / DIR).glob('*')
             if p.is_file() and p.name != 'implementation.json' and p.relative_to(ROOT).as_posix() not in registered]
    paths += [p for p in G.changed_paths(BASE) if p not in registered and p not in [G.REGISTRY,registry['audit_artifact'],DIR+'/implementation.json'] and not p.startswith('backups/')]
    audit(sorted(set(paths)))
    versions = list((ROOT/DIR).glob('contract-v*.json'))
    n = max([int(p.stem.split('-v')[1]) for p in versions],default=0) + 1
    contract = DIR + '/contract-v%d.json' % n
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',
                    DIR+'/population.json','--output',contract],check=True,stdout=subprocess.DEVNULL)
    c = load(contract)
    assert not c['conflicts'] and not c['unresolved_gates'], (c['conflicts'],c['unresolved_gates'])
    p = load(DIR+'/implementation.json') if (ROOT/DIR/'implementation.json').exists() else {
        'artifact_type':'task_implementation_plan','actions':load(DIR+'/population.json')['operation_classes'],
        'events':[], 'status':'research_in_progress'}
    subjects = {}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]): subjects.setdefault(f['subject'],{})[f['field']] = f['equals']
    p.update(contract=contract,contract_sha256=file_hash(contract),population_sha256=c['population_sha256'],
             respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in p['events']: e['governance_ids'] = c['governance_ids']
    receipt = DIR + '/receipt.json'
    if (ROOT/receipt).exists(): p['completion_evidence'] = {gid:[{'path':receipt,'sha256':file_hash(receipt)}] for gid in c['governance_ids']}
    write(DIR+'/implementation.json',p)
    write(G.ACTIVE_TASK,dict(population=DIR+'/population.json',contract=contract,contract_sha256=file_hash(contract),
                           implementation=DIR+'/implementation.json',state='in_progress'))
    print(contract,len(c['governance_ids']),'rules; no conflicts/gates')

def event(operation,summary,evidence,action='implements'):
    p=load(DIR+'/implementation.json')
    p['events'].append(dict(operation=operation,candidate_ids=IDS,governance_ids=p['respected_governance_ids'],
                           action=action,summary=summary,evidence=evidence,use_contract_record_rules=True))
    write(DIR+'/implementation.json',p)

def setup():
    pop=load(DIR+'/population.json')
    pop['artifact_paths'] += ['project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1']
    pop['artifact_paths'] += [DIR+'/response-%03d.bin.gz' % i for i in range(1,251)]
    pop['artifact_paths'] += [DIR+'/visual-%02d.png' % i for i in range(1,41)]
    write(DIR+'/population.json',pop)
    authority = ('Resolve exactly the six frozen Trails PID agenda blockers as one governed family. '
        'Use existing evidence first and exhaustive active registry resolution; perform factual meeting occurrence, '
        'approved minutes, subsequent approvals, cancellation/quorum and incorporated substantive attachment review. '
        'Apply current mission/publication-quality policy independently. Possible conclusive background dispositions '
        'are exclude, qualified missing-minutes retention, duplicate/superseded, or factual hold. '
        'The current user authorizes evidence-driven inventory dispositions, deterministic accounting, full validation, '
        'and clean background-only integration into main with synchronized chatgpt/planning-snapshot. '
        'No visitor-visible change, R2 mutation or another population is authorized. '
        'Historical recommendations cannot be manually ranked; genuine conflicting authority requires explicit reconciliation.')
    write(DIR+'/authority.json',dict(authority='Explicit current user instruction',candidate_ids=IDS,instruction=authority))
    bind(DIR+'/authority.json','owner-'+TASK,authority,{'candidate_ids':IDS,'task_ids':[TASK]})
    state=load(DIR+'/starting-state.json')
    state.update(source_queue=load('project-state/ordinary-queue-current.json')['artifact'],
                 r2_inventory_sha256=file_hash('project-state/r2-inventory.json'),
                 r2_policy_sha256=file_hash('project-state/r2-storage-policy.json'))
    write(DIR+'/starting-state.json',state)
    lifecycle=load('project-state/workflow-stage-lifecycle.json')
    assert lifecycle['stages'][-1]['id']=='pr212-postmerge-closeout-2026-10-05'
    lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/TrailsAgendaResolution.py'],
        exact_delta_guard={'module':'TrailsAgendaResolution','function':'guard'}))
    write('project-state/workflow-stage-lifecycle.json',lifecycle)
    runner=ROOT/'scripts/project/Invoke-ProjectValidation.ps1'
    t=runner.read_text(encoding='utf-8')
    t=t.replace('Set-StrictMode -Version Latest', '& python "$PSScriptRoot/TrailsAgendaResolution.py" guard\nif ($LASTEXITCODE) { throw \'Trails six-record background boundary failed.\' }\nSet-StrictMode -Version Latest',1)
    runner.write_text(t,encoding='utf-8',newline='\n')
    refresh()
    print(G.active_check('mutation','document_review'))

def guard():
    from WorkflowStageLifecycle import StageSnapshot,git,canonical_bytes
    stage=StageSnapshot(TASK)
    state=stage.load_json(DIR+'/starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for path,key in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==state[key],path
    before={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']}
    after={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert before.keys()==after.keys()
    assert {i for i in before if before[i]!=after[i]}<=set(IDS),'Population widened'
    for i in IDS:
        assert after[i]['processing_notes'][:len(before[i]['processing_notes'])]==before[i]['processing_notes'],'History lost'
        assert all(after[i][k]==before[i][k] for k in ['r2_key','r2_url','source_url','direct_file_url']),'Source/archive fields changed'
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(stage.load_json(DIR+'/population.json')['artifact_paths']),changes-set(stage.load_json(DIR+'/population.json')['artifact_paths'])
    for path in ['project-state/discovery/meeting-agenda-documents-cluster-research-2026-09-11.json',
                 'project-state/discovery/council-public-body-missing-minutes-matrix-2026-09-20.json',
                 'project-state/discovery/council-documents-cluster-research-2026-09-11.json',
                 'project-state/discovery/background-followup-2026-09-26/decisions.json']:
        assert canonical_bytes((ROOT/path).read_bytes())==canonical_bytes(git('show',BASE+':'+path)),'Historical evidence edited'
    print('Trails exact six-record, original history, zero visible/R2 guard passed')

def retrieve(tasks):
    from concurrent.futures import ThreadPoolExecutor
    from bs4 import BeautifulSoup
    existing=load(DIR+'/retrievals.json') if (ROOT/DIR/'retrievals.json').exists() else {'records':[]}
    start=len(existing['records'])+1
    def get(pair):
        n,task=pair;url=task['url'];p=DIR+'/response-%03d.bin.gz'%n
        r=dict(task,requested_at=now(),method='GET',response_artifact=p)
        try:
            try:res=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo official records review)'}),timeout=40)
            except urllib.error.HTTPError as e:res=e
            with res:body=res.read(12000001)
            assert len(body)<=12000000
            r.update(status=res.status,final_url=res.geturl(),content_type=res.headers.get('Content-Type'),size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),complete=True)
            (ROOT/p).write_bytes(gzip.compress(body,mtime=0))
            if body.startswith(b'%PDF-'):
                sys.path.insert(0,str(ROOT/'tmp/pdfs/pydeps'));import fitz
                doc=fitz.open(stream=body,filetype='pdf')
                page_links=[{k:(list(v) if k in ['from','to'] else v) for k,v in l.items()} for page in doc for l in page.get_links()]
                r.update(page_count=len(doc),text='\n'.join(page.get_text() for page in doc),attachments=doc.embfile_names(),page_links=page_links)
                r['word_count']=len(r['text'].split())
            elif 'html' in (r['content_type'] or ''):
                soup=BeautifulSoup(body,'html.parser')
                main=soup.find(id='content') or soup.find('main') or soup
                r['text']=main.get_text(' ',strip=True)
                from urllib.parse import urljoin
                r['links']=[{'label':a.get_text(' ',strip=True),'url':urljoin(res.geturl(),a['href'])} for a in main.find_all('a',href=True)]
        except Exception as e:r.update(error=str(e),complete=False)
        return r
    with ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(get,enumerate(tasks,start)))
    existing['records']+=results;write(DIR+'/retrievals.json',existing)
    for r in results:print(r.get('label'),r.get('status'),r.get('page_count'),r.get('size_bytes'),r.get('error',''))

def historical():
    paths=['project-state/discovery/meeting-agenda-documents-cluster-research-2026-09-11.json',
           'project-state/discovery/council-public-body-missing-minutes-matrix-2026-09-20.json',
           'project-state/discovery/council-documents-cluster-research-2026-09-11.json',
           'project-state/discovery/background-followup-2026-09-26/decisions.json',
           'project-state/discovery/background-followup-2026-09-26/retrievals.json',
           'project-state/discovery/human-review-reassessment-2026-09-26/family-evidence.json']
    extracted=[]
    def walk(x,p):
        if isinstance(x,dict):
            if any(v in IDS for v in x.values() if isinstance(v,str)) or any('Trails Public Improvement' in v for v in x.values() if isinstance(v,str)):
                extracted.append({'pointer':p,'evidence':x});return
            for k,v in x.items():walk(v,p+'/'+k)
        elif isinstance(x,list):
            for n,v in enumerate(x):walk(v,p+'/'+str(n))
    for p in paths:walk(load(p),p)
    write(DIR+'/historical-evidence.json',dict(artifacts=[{'path':p,'sha256':file_hash(p)} for p in paths],extracted=extracted))
    event('family_review','Read existing exact-family research, source receipts and minutes matrix; preserve recommendations and factual limitations.',DIR+'/historical-evidence.json','research_unsettled')

def fetch_initial():
    rows=load(DIR+'/baseline-records.json')
    tasks=[{'label':i,'url':rows[i]['direct_file_url']} for i in IDS]
    tasks += [{'label':'pid-index','url':'https://www.cabq.gov/council/public-improvement-districts'},
              {'label':'trails-former-index','url':'https://www.cabq.gov/council/public-improvement-districts/the-trails-public-improvement-district'},
              {'label':'city-trails-search','url':'https://www.cabq.gov/search?SearchableText=%22Trails%22&b_size:int=100'},
              {'label':'city-exact-search','url':'https://www.cabq.gov/search?SearchableText=%22Trails+Public+Improvement+District%22&b_size:int=100'},
              {'label':'city-minutes-search','url':'https://www.cabq.gov/search?SearchableText=%22Trails%22+minutes&b_size:int=100'}]
    write(DIR+'/fetch-tasks.json',tasks);retrieve(tasks)

def findings():
    inspections=load(DIR+'/pdf-inspection.json')
    for r in inspections:
        r.update(visual_inspection_completed=True,visual_finding='All pages visually inspected. Numbered meeting business and accessibility notices only; no substantive resolutions, budgets, financial tables, report narratives or minutes appended.')
    write(DIR+'/pdf-inspection.json',inspections)
    dates=['2013-05-29','2013-08-01','2025-05-16','2025-07-25','2026-05-26','2026-07-24']
    occurrence=[
        'August 1, 2013 agenda item 3 schedules review of May 29 minutes. This is retrospective corroboration of a meeting/minutes record, not a roll call or executed minutes; occurrence with a quorum is not independently established.',
        'February 4, 2014 agenda item 3 schedules review of August 1, 2013 minutes. This corroborates a prior meeting/minutes record, but supplies no roll call, approved minutes or approval result.',
        'July 25, 2025 agenda item 3 schedules approval of May 16 minutes. Item 6 records a no-quorum Board gathering on May 17 and lists actions matching May 16 business. The connection is plausible but the conflicting dates prevent a conclusive no-quorum assignment to May 16; no executed minutes or resolution resolves it.',
        'May 26, 2026 agenda item 3 schedules approval of July 25, 2025 minutes. This retrospectively corroborates a prior meeting/minutes record but establishes neither its quorum nor the approval vote.',
        'July 24, 2026 agenda item 3 schedules approval of May 26, 2026 minutes. This retrospectively corroborates a prior meeting/minutes record but establishes neither quorum nor approved-minute status.',
        'The original notice establishes a scheduled July 24 meeting. Complete current directory and subsequent published records supply no later Trails agenda, minutes, roll call or completed resolution establishing occurrence. Actual occurrence remains unverified.'
    ]
    substantive=[
        'Lists consideration of open-meetings, preliminary FY2014 budget and quarterly-report resolutions, disclosure/delinquencies, foreclosure status and legislative updates. Contains none of the resolutions, financial figures, foreclosure findings or legislative analysis.',
        'Lists final FY2014 budget and quarterly-report resolutions and a foreclosure-status report. Contains no budget, quarterly data, resolution terms or foreclosure findings.',
        'Lists audit/consultant ratifications, an omitted prior audit adoption, open-meetings policy, financial statements, quarterly reports and a preliminary budget. The historical audit-adoption aside is a research lead, not the audit, decision or policy text; no financial amounts or analysis are supplied.',
        'Lists ratification of a prior no-quorum gathering, consulting and retention-policy resolutions, quarterly report and final budget. The no-quorum statement is a specific historical lead, but its May16/17 ambiguity, absence of executed Resolution2025-03, roll call or action results, and business-list remainder do not provide sufficient standalone public value.',
        'Lists audit/portal authorizations, budget-approval letters and resolutions for open-meetings policy, audit, quarterly reports, budget adjustment and preliminary budget. Contains no letter, audit finding, policy terms, report data, budget numbers or adopted action.',
        'Lists quarterly report, budget adjustment and final-budget resolutions plus the debt-service/non-debt-service hearing topic. Contains no report, budget, assessment amounts, resolution text, hearing findings or adopted action.'
    ]
    rows=[]
    for n,(rid,date,ins) in enumerate(zip(IDS,dates,inspections)):
        rationale=('The exact official agenda substantially concerns an Albuquerque district, so the geographic/institutional gate passes. '
            +substantive[n]+' Its limited content identifies proposed business rather than explaining the underlying public expenditure, infrastructure, policy or decisions. '
            'The agenda fails the independent substantive public-information gate and actual-record publication-quality test. Missing approved minutes cannot cure that failure. '
            'The whole publicly available agenda family was considered; combining these notices would still omit the substantive records and would not justify a master or standalone entry.')
        scope=dict(assessed_at=now(),geographic_institutional_scope='The Trails PID, a City-approved district wholly within Albuquerque financing residential infrastructure.',
            specific_albuquerque_connection='Exact dated governing-board agenda for Albuquerque Trails PID; material institutional/geographic connection is present.',
            abqinfo_public_information_value=substantive[n],general_context_exclusion_test='Specific geography and an official publisher do not make a proposed-business list a substantive account of Albuquerque policy, spending or infrastructure. Named records belong in their own factual review; none is incorporated here.',
            final_scope_decision='excluded_insufficient_public_information_value',substantive_rationale=rationale)
        quality=dict(reviewed_document_content=True,visual_inspection_completed=True,page_count=ins['page_count'],extracted_word_count=ins['word_count'],
            document_function='Official proposed meeting agenda, not minutes or a decision instrument.',substantive_content=substantive[n],
            standalone_public_value='low',durable_public_usefulness='Useful as a source-research pointer to proposed business; insufficient to independently explain actual policy, expenditure or outcomes.',
            information_density='Sparse numbered business list and notice boilerplate; no substantive tables, incorporated reports or decision text.',
            unique_information='Date, location, proposed items and limited historical asides. These do not supply the underlying decisions or substantive reports.',
            series_relationship='serial',publication_form='excluded',rationale=rationale,
            aggregation_decision=dict(form='excluded',rationale='Review of complete published Trails agenda family shows repetitive notices; a combined agenda master would not create missing substantive content.',evidence=[DIR+'/sources.json',DIR+'/retrievals.json']),
            limited_content=ins['word_count']<250,limited_content_exception='No exception: short business notices contain no distinct map, legal instrument or dense financial/tabular information.',
            evidence=[DIR+'/pdf-inspection.json',DIR+'/retrievals.json'])
        rows.append(dict(id=rid,date=date,title='The Trails Public Improvement District Board of Directors '+('Special' if n<2 else 'Regular')+' Meeting Agenda, '+date,
            occurrence_state='unverified_notice_only' if n==5 else 'retrospectively_corroborated_not_independently_verified',meeting_occurrence=occurrence[n],
            minutes_state='referenced_not_located_approval_unverified' if n<5 else 'not_located_existence_unverified',
            approved_minutes_conclusion='No approved minutes original or completed vote approving these minutes was located. A proposed review/approval item is not evidence of completed approval. This is not proof that no minutes exist.',
            cancellation_quorum='No affirmative cancellation evidence located; no affirmative quorum record located.' if n!=2 else 'Date-conflicting no-quorum evidence: July25 item6 expressly says May17, while item3 and the selected notice say May16. Do not silently correct May17 or claim May16 definitively lacked a quorum.',
            substantive_value=substantive[n],incorporated_reports_resolutions=False,scope_assessment=scope,quality_assessment=quality,
            final_disposition='excluded',disposition_basis='Conclusive independent public-information/quality failure; meeting-occurrence and minute-approval uncertainty preserved, not misrepresented as resolved.',
            qualified_missing_minutes_retention=False,owner_decision_required=False))
    searches=['site:cabq.gov Trails minutes 2013','site:cabq.gov Trails 2025 minutes','Trails Public Improvement District minutes',
        'Trails Public Improvement District Albuquerque administrator minutes','Trails Public Improvement District May17 2025',
        'site:financedta.com Trails Albuquerque','Brescia Consulting Albuquerque website','site:reports.saonm.org The Trails FY2013/FY2014/FY2025']
    write(DIR+'/research-searches.json',dict(method='Supplementary web search; conclusions use preserved official originals and directory responses.',queries=searches,
        authoritative_results=['https://www.cabq.gov/council/documents/8113TrailsAgenda.pdf','https://www.cabq.gov/council/documents/meeting-agenda-documents/2414TrailsPIDBoardAgendaFINAL.pdf',
        'https://www.cabq.gov/council/documents/7-25-25-trails-pid-agenda.pdf'],negative_result_limit='Search misses are not proof of nonexistent records. No confirmed independent Brescia board-record portal was identified. The attempted bresciaconsulting.com domain is unconfirmed, not treated as official evidence.'))
    evidence=load(DIR+'/retrievals.json')['records']
    directories=[r for r in evidence if r['label']=='council-documents-current' or r['label'].startswith('council-full-directory-')]
    assert len(directories)==30 and all(r.get('status')==200 for r in directories)
    index_links={l['url'] for r in directories for l in r.get('links',[]) if '/council/documents/' in l['url'] and '/view' in l['url']}
    method=dict(official_city_directory_pages=30,official_city_directory_item_links=len(index_links),meeting_agenda_directory_pages=2,
        broad_trails_search_pages=46,minutes_search_pages=6,subsequent_family_documents='All Trails meeting/agenda files discovered in complete Council directory, City search and original inventory; evidence only, no additional mutation population.',
        legistar='Complete active body index has no Trails PID body; title-filtered matters and PID attachment indexes checked. Council legislation/appointments are distinct from PID minutes.',
        administrator='DTA public site, Trails search and district-administration page reviewed; no Trails board minutes delivery identified. No confirmed public Brescia archive located. District Clerk is the official records contact named by the agendas.',
        unavailable='State Auditor public index and two identified district audits timed out after elevated read-only attempts; supplementary web reader exposed historical financial report text but no exact selected meeting minutes.',
        exhaustion_limit='Reasonably available published official records exhausted for these agenda decisions. Private/nonpublished Clerk records, confirmed approved minutes and the May16/17 discrepancy remain factually unresolved. No records request or message to an official was sent or authorized.',
        retention_test='No record is approved under the missing-minutes exception. Exclusion is conclusive on independent substance and needs no unsupported assertion of meeting occurrence or absence of minutes.')
    write(DIR+'/meeting-findings.json',dict(task_id=TASK,completed_at=now(),population=IDS,method=method,records=rows,
        binding_requirement='Exclude exactly the six frozen agenda notices for insufficient substantive public-information/publication value. Preserve exact originals, historical research and the stated unresolved occurrence/minutes/quorum limits. No missing-minutes label, archive action, visible entry or new population is authorized.'))
    audit_rows=load(load(G.REGISTRY)['audit_artifact'])['artifacts']
    historical_paths=[x['path'] for x in load(DIR+'/historical-evidence.json')['artifacts']]
    reconciliation=dict(task_id=TASK,classification_evidence=[x for x in audit_rows if x['path'] in historical_paths],
        active_contract=load(G.ACTIVE_TASK)['contract'],resolver_conflicts=[],
        earlier_recommendation='September11 agenda-cluster recommendation explicitly says it did not modify the six records; the audit classifies it and Council research/matrix as historical evidence only / non-binding.',
        later_control='Registered September26 follow-up retains a factual prerequisite for agenda preservation/archiving, expressly says references to earlier minutes do not supply them, and asks for no owner policy choice. This is a conditional unresolved-evidence state, not a settled positive scope/quality decision or permanent requirement to publish/preserve notices.',
        reconciliation='The two artifacts are a nonbinding substance recommendation and subsequent controlling factual hold, not two contradictory active settled decisions. Implement the current owner-authorized factual and actual-record review; retain the historical facts and archival prohibition. Resolve current inventory eligibility through independent conclusive substance exclusions without claiming the retention prerequisites were established.',
        supersession_required=False,why_no_authority_superseded='No prior positive eligibility/publication or terminal disposition for these six is reversed. Existing registered historical hold evidence and its continuing no-archive consequence remain unchanged. The new registered scoped family decision completes the authorized review; all unrelated decisions stay active.',
        factual_uncertainties_preserved=True,owner_decisions_needed=0)
    write(DIR+'/governance-reconciliation.json',reconciliation)
    # Saved review outputs are proposals until their explicit registry registration.
    # Re-pin the complete contract before the governance registration entry point.
    refresh()
    G.active_check('mutation','governance_implementation')
    gid='decision-'+TASK
    registry=load(G.REGISTRY)
    registry['entries'].append(dict(governance_id=gid,category='active family decision',title='Six Trails PID agenda substance exclusions with factual limits preserved',
        scope={'candidate_ids':IDS,'task_ids':[TASK]},authority='Explicit current owner-authorized six-record background resolution under mission/publication-quality policies',
        decision_date='2026-10-05',effective_date='2026-10-05',state='active',
        controlling_artifacts=[{'path':DIR+'/meeting-findings.json','sha256':file_hash(DIR+'/meeting-findings.json'),'binding_pointers':['/binding_requirement','/records']},
                              {'path':DIR+'/governance-reconciliation.json','sha256':file_hash(DIR+'/governance-reconciliation.json'),'binding_pointers':['/reconciliation']}],
        binding_requirement=load(DIR+'/meeting-findings.json')['binding_requirement'],required_actions=['Preserve the exact six negative substance assessments and original evidence; occurrence/minutes uncertainty is not a retention approval.'],
        prohibited_actions=['No automatic reversal from missing minutes, official provenance or title-only substantive references.'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='Evidence-based family exclusions ready for authorized inventory application'))
    write(G.REGISTRY,registry)
    authority_audit=load(registry['audit_artifact'])
    for a in authority_audit['artifacts']:
        if a['path'] in [DIR+'/meeting-findings.json',DIR+'/governance-reconciliation.json']:
            a.update(classification='active family decision',governance_ids=[gid],rationale='Registered final six-record exclusions and reconciliation; original historical evidence and no-retention limits preserved.')
    write(registry['audit_artifact'],authority_audit)
    registry['audit_sha256']=file_hash(registry['audit_artifact']);write(G.REGISTRY,registry)
    event('quality_assessment','All ten original pages visually inspected; exact hashes, family contents and independent negative scope/quality determinations complete.',DIR+'/meeting-findings.json')
    event('family_review','Exhaust current public City/Council directories, subsequent Trails agendas, Legistar and public administrator routes; preserve factual limits and reconcile recommendation/hold through registry classifications.',DIR+'/governance-reconciliation.json')
    updates=[]
    before=load(DIR+'/baseline-records.json')
    for r in rows:
        rid=r['id']
        changes=dict(status='excluded',title=r['title'],date=r['date'],file_type='PDF',review_reason='publication_quality_exclusion',exclusion_reason=r['scope_assessment']['substantive_rationale'],
            scope_assessment=r['scope_assessment'],quality_assessment=r['quality_assessment'],
            publication_quality_decision={'decision':'excluded','finding_id':TASK+':'+rid,'rationale':r['scope_assessment']['substantive_rationale'],'evidence':[DIR+'/meeting-findings.json',DIR+'/pdf-inspection.json']},
            validation_status='Governed exact-family exclusion; source/visual/whole-family review complete. Factual occurrence/minutes limits preserved in '+DIR+'/meeting-findings.json',
            processing_notes=before[rid]['processing_notes']+['2026-10-05 '+TASK+': conclusive public-information/quality exclusion; no substantive attachments. '+r['meeting_occurrence']+' No approved minutes located; no absence or approval inferred. Earlier recommendation/later factual hold reconciled in '+DIR+'/governance-reconciliation.json'])
        updates.append({'id':rid,'changes':changes})
    write(DIR+'/record-updates.json',{'approved_updates':updates})
    write(DIR+'/progress.json',{'stage':'factual_and_quality_review_complete','candidate_ids':IDS,'inventory_mutation':False,'next_population_authorized':False})
    refresh()

def queue():
    inv=load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    prior=load(load(DIR+'/starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'}
    approved={i for i,r in rows.items() if r['status']=='approved for addition'}
    q.update(artifact_type='trails_pid_agenda_resolution_queue',recorded_at=inv['generated_at'],
        source_queue_artifact=load(DIR+'/starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],
        inventory_sha256=file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),newly_approved_backlog=[],in_progress_publication=None)
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending}
        q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),genuinely_actionable_ungated_pending_count=len(ungated))
    q['trails_agenda_resolution']={'task':TASK,'excluded_ids':IDS,'cleared_blockers':6,'factual_limits_retained':True}
    assert (len(approved),len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'],len(ungated))==(0,342,321,21,0)
    write(DIR+'/queue.json',q)
    write('project-state/ordinary-queue-current.json',{'schema_version':1,'artifact':DIR+'/queue.json','task':TASK})
    return q

def apply():
    refresh();G.active_check('mutation','inventory_disposition',IDS)
    current={r['id']:r for r in load('project-state/master-inventory.json')['candidates']}
    requests=load(DIR+'/record-updates.json')['approved_updates']
    if all(current[i]['status']=='excluded' for i in IDS):
        assert all(all(current[x['id']].get(k)==v for k,v in x['changes'].items()) for x in requests),'Interrupted inventory state differs from final requests'
        print('Six saved dispositions already complete; resume derived accounting only')
    else:
        assert all(current[i]['status']=='pending review' for i in IDS),'Unexpected partially applied family'
        subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',DIR+'/record-updates.json'],check=True)
    inventory=ROOT/'project-state/master-inventory.json'
    inventory.write_bytes(inventory.read_bytes().replace(b'\r\n',b'\n'))
    queue()
    refresh()
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Update-ArchiveReconciliationCheckpointCounts.ps1'],check=True)
    refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    inv=load('project-state/master-inventory.json');after={r['id']:r for r in inv['candidates']};before=load(DIR+'/baseline-records.json')
    q=load(DIR+'/queue.json')
    write(DIR+'/accounting.json',dict(task_id=TASK,result='six_conclusive_exclusions',records=[{'id':i,'before_status':before[i]['status'],'after_status':after[i]['status'],
        'before_row_sha256':digest(before[i]),'after_row_sha256':digest(after[i])} for i in IDS],
        blockers_cleared=6,queue={'approved':0,'pending':342,'governance_gated':321,'source_blocked':21,'ungated':0},
        genuine_owner_decisions=0,r2={'uploads':0,'added_bytes':0,'deleted_objects':0,'overwritten_objects':0,'delta':0},visitor_visible_delta=0,
        factual_uncertainties_are_nonblocking_for_exclusion=True,next_population_authorized=False))
    event('inventory_disposition','Apply exactly six conclusive exclusions; preserve earlier notes/source/archive fields and all other inventory records; regenerate queue/checkpoint/owner accounting.',DIR+'/accounting.json')
    write(DIR+'/progress.json',{'stage':'six_dispositions_saved_validation_pending','completed':IDS,'remaining':['full_validation','background_integration'],'next_population_authorized':False})
    current=ROOT/'project-state/CURRENT.md';old=current.read_text(encoding='utf-8');links=old[old.index('[Owner correction]'):]
    text='# Current project state\n\nExactly six Trails PID agendas excluded after official-source and complete-page/family review: proposed business lists lack substantive attachments or independent public-information value. Prior-minute references corroborate five dates without approved minutes or quorum proof; May16/17 2025 discrepancy and July24 2026 occurrence remain unverified. Missing minutes do not establish retention. Earlier recommendation/later factual hold reconciled without conflicting settled authority. Queue: 0 approved / 342 pending (321 governance-gated / 21 source-structural blocked); six blockers cleared. No active publication or owner decision. Zero visitor-visible/R2 delta. Full validation and authorized background main/planning synchronization pending; no next population.\n\n[Trails review](governance/'+TASK+'/meeting-findings.json) \u00b7 [Reconciliation](governance/'+TASK+'/governance-reconciliation.json) \u00b7 '+links
    current.write_text(text,encoding='utf-8',newline='\n')
    refresh();guard()

def review_receipt():
    pop=load(DIR+'/population.json')
    pop['artifact_paths'] += [DIR+'/validation-attempt-1.log',DIR+'/validation-attempt-2.log']
    write(DIR+'/population.json',pop)
    receipt=dict(task_id=TASK,stage='six_exclusions_complete_validation_pending',candidate_ids=IDS,
        authoritative_baseline=BASE,accounting=load(DIR+'/accounting.json'),
        review_evidence_sha256={DIR+'/'+p:file_hash(DIR+'/'+p) for p in ['meeting-findings.json','pdf-inspection.json',
            'historical-evidence.json','governance-reconciliation.json','retrievals.json','sources.json','record-updates.json','queue.json','accounting.json']},
        governance_accounting={},normal_validation='pending',no_new_population=True,
        factual_limits='No approved minutes or completed approval vote located; five dates have subsequent-agenda corroboration only; May16/17 date discrepancy and July24 2026 occurrence remain unresolved. No retention exception invoked.',
        owner_decision_required=False,visitor_visible_delta=0,r2_delta=0)
    c=load(load(G.ACTIVE_TASK)['contract'])
    for r in c['resolved_rules']:
        gid=r['governance_id']
        if gid=='decision-'+TASK: finding='Exactly six excluded under the registered final findings; actual original pages and complete family assessed; factual uncertainty and originals preserved.'
        elif gid=='owner-'+TASK: finding='Exact requested six-record family only. Public factual work and conclusive background dispositions saved; authorized integration awaits full validation; no other population or external archival action.'
        elif gid=='policy-mission-scope': finding='All six have a material Albuquerque institution connection but fail the substantive public-information gate; complete negative assessments saved, no eligible status or borderline owner referral.'
        elif gid=='policy-publication-quality': finding='All ten pages visually inspected and measured; original hashes verified; attachments/links absent; series independently assessed and no limited-content or aggregation exception invented.'
        elif gid.startswith('decision-'): finding='Preserved controlling artifacts and unrelated record decisions unchanged. The Trails predecessor entries recorded conditional factual holds for retention, with no positive scope/quality or permanent eligibility decision. Current explicit review completes eligibility as exclusions while preserving prior evidence and archival restrictions.'
        elif gid in ['policy-agents','policy-project-state','policy-durable-task-governance']: finding='Six-record population, full registry contracts, per-record events, pre-mutation freshness, immediate inventory save and deterministic queue/checkpoint accounting; no source/provenance history rewritten.'
        elif gid.startswith('workflow-') or gid.startswith('authorization-'): finding='No background campaign or parallel invocation inferred. Previous stage sealed at exact baseline; exact current delta guarded; recovery receipts saved. No protected owner/publication/R2 operation initiated.'
        else: finding='No regulated operation or settled subject reopened. Negative eligibility determinations do not confer publication/archive authority. Historical exclusions, currentness and original source/storage boundaries preserved.'
        receipt['governance_accounting'][gid]=dict(requirement=r['binding_requirement'],implementation=finding,
            controlling_evidence_preserved=[{'path':a['path'],'sha256':file_hash(a['path'])} for a in r['controlling_artifacts']],
            evidence=[DIR+'/meeting-findings.json',DIR+'/governance-reconciliation.json',DIR+'/accounting.json'])
    write(DIR+'/receipt.json',receipt)
    refresh();G.active_check('final');guard()

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1] == 'freeze': freeze()
    elif sys.argv[1]=='setup':setup()
    elif sys.argv[1]=='refresh':refresh()
    elif sys.argv[1]=='guard':guard()
    elif sys.argv[1]=='historical':historical()
    elif sys.argv[1]=='initial':fetch_initial()
    elif sys.argv[1]=='fetch':retrieve(load(DIR+'/fetch-tasks.json'))
    elif sys.argv[1]=='findings':findings()
    elif sys.argv[1]=='apply':apply()
    elif sys.argv[1]=='review-receipt':review_receipt()
