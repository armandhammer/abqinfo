"""Resume-safe isolated thirteen-record background review; no storage or site mutation."""
import copy, hashlib, json, subprocess, sys, runpy
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G

P='project-state/governance/remaining-approved-review-2026-10-03/'
TASK='remaining-approved-review-2026-10-03'
OWNER='owner-'+TASK
BASE='78327bed8cdc2cc25e540d1737cde22096ec8e83'
IDS=['src-ed75a3cb5ecc3b0b','src-1f9cf39555e7be6f','src-0e0cd2037365e977','src-751926439273bc52','src-255c53cabfcc83d6','src-93ef5bb0e94bfa97','src-28184729e8cc1326','src-3a4c39611a00e0a3','src-143f58c34ccb049a','src-93024cc660045c22','src-2c5c4a2267988a30','src-2aba4fa7ad3e22e2','src-ab94ccbf5e75b5d0']
def save(path,data):
    target=G.ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def audit(paths,rationale):
    registry=G.load(G.REGISTRY);data=G.load(registry['audit_artifact']);indexed={r['path']:r for r in data['artifacts']}
    for path in paths: indexed[path]=dict(path=path,sha256=G.file_hash(path),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale=rationale)
    data['artifacts']=sorted(indexed.values(),key=lambda r:r['path']);save(registry['audit_artifact'],data)
    registry['audit_sha256']=G.file_hash(registry['audit_artifact']);save(G.REGISTRY,registry)
def bind(path,gid,requirement,scope,authority='Explicit owner instruction 2026-10-03'):
    registry=G.load(G.REGISTRY)
    if any(r['governance_id']==gid for r in registry['entries']):
        existing=next(r for r in registry['entries'] if r['governance_id']==gid)
        assert existing['binding_requirement']==requirement and existing['controlling_artifacts'][0]['sha256']==G.file_hash(path)
        return
    registry['entries'].append(dict(governance_id=gid,category='active owner decision',title=gid,scope=scope,authority=authority,decision_date='2026-10-03',effective_date='2026-10-03',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='in progress'))
    save(G.REGISTRY,registry)
def now(): return datetime.now(timezone.utc).isoformat()
def git(*args): return subprocess.check_output(['git',*args],cwd=G.ROOT).decode().strip()
def freeze():
    assert git('rev-parse','HEAD')==BASE
    inventory=G.load('project-state/master-inventory.json')
    rows={r['id']:r for r in inventory['candidates']}
    assert all(rows[i]['status']=='approved for addition' for i in IDS)
    paths=[P+n for n in ['population.json','authority.json','starting-remote-state.json','progress.json','prior-records.json','implementation.json','supersession.json','owner-decisions-needed.json','receipt.json','summary.md','pr-body.md','remote-check.json','validation.log','bootstrap-validation.json','accounting.json','family-analysis.json']]
    paths += [P+f'contract-v{i}.json' for i in range(1,101)]
    paths += [P+f'milestone-{i}.json' for i in [3,6,9,13]]
    for rid in IDS:
        paths += [P+f'records/{rid}/{n}' for n in ['review.json','retrievals.json','research.json','family.json','publication-plan.json','validation.json','source.html','article.html','article.txt','article.png','current.html','current.txt','supplement.html','supplement.txt']]
    paths += ['scripts/project/Review-RemainingApproved.py','project-state/governance/active-task.json',G.REGISTRY,G.registry()['audit_artifact'],'project-state/master-inventory.json','project-state/ordinary-queue-current.json',P+'queue.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','external_mutation'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    pr=json.loads(subprocess.check_output(['gh','pr','view','208','--json','number,state,title,body,headRefName,headRefOid,baseRefName,url,updatedAt'],cwd=G.ROOT))
    assert pr['state']=='OPEN' and pr['headRefOid']==BASE
    refs={r:git('rev-parse',r) for r in ['origin/main','origin/codex/strong-five-review-2026-10-03','origin/chatgpt/planning-snapshot','origin/codex/remaining-approved-review-2026-10-03']}
    assert refs['origin/chatgpt/planning-snapshot']==BASE
    G.write_once(P+'starting-remote-state.json',dict(timestamp=now(),refs=refs,pr208=pr,protected_tree=git('ls-tree',BASE,'content','layouts','assets','static'),r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json'),production_baseline=refs['origin/main']))
    save(P+'progress.json',dict(task_id=TASK,baseline_commit=BASE,branch='codex/'+TASK,records=[dict(id=i,title=rows[i]['title'],state='not_started',research_evidence_paths=[],review_artifact_path=None,resulting_disposition=None,inventory_mutation_applied=False,validation_passed=False,checkpoint_commit_sha=None,unresolved_blocker=None,owner_decision_required=False) for i in IDS],last_pushed_commit=BASE,next_unfinished=IDS[0]))
    save(P+'owner-decisions-needed.json',dict(items=[]))
    save(P+'supersession.json',dict(proposals={}))
    c=G.resolve(G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));G.write_once(P+'contract-v1.json',c)
    print('Frozen',len(IDS),'records;',len(c['governance_ids']),'rules; gates',c['unresolved_gates'],'conflicts',c['conflicts'])
def refresh():
    old=[f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).glob('contract-v*.json')]
    audit(old,'Immutable prior resolver snapshots; historical evidence only after replacement.')
    population_path=P+('population-v3.json' if (G.ROOT/(P+'population-v3.json')).exists() else 'population.json')
    c=G.resolve(G.load(population_path),G.registry(),G.file_hash(G.REGISTRY))
    n=max([int(Path(p).stem.split('-v')[1]) for p in old],default=0)+1
    path=P+f'contract-v{n}.json';G.write_once(path,c)
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration','external_mutation'],events=[],status='background_review_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for fact in r.get('constraints',[]): subjects.setdefault(fact['subject'],{})[fact['field']]=fact['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']: e['governance_ids']=c['governance_ids']
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print('Contract',path,'rules',len(c['governance_ids']),'conflicts',c['conflicts'],'gates',c['unresolved_gates'])
def setup():
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY))
    G.write_once(P+'authority.json',dict(governance_metadata={'governance_id':OWNER},authority='Explicit current owner campaign instruction',candidate_ids=IDS,baseline_commit=BASE,instruction='Independently reassess exactly these thirteen remaining approved records under complete durable governance. September30 triage and existing approval are nonbinding for this review. Apply evidence-based scope/quality exclusions or strengthened candidate/blocked outcomes, explicitly superseding only population-specific prior approvals where needed; preserve historical evidence, all out-of-population rows, PR207 exclusions and settled family consolidation. Research provenance, currentness, family identity and quality; save implementation-ready future publication plans for survivors. No visitor-visible change, R2 upload/overwrite/delete/transform, merge, deployment, PR208 modification or planning-snapshot movement. Isolated branch starts at reviewed PR208 head. Commit/push bootstrap, then every completed individual record. Genuine unavailable owner choices are recorded and do not stop other reviews. Draft stacked PR is authorized with PR208 branch as base. Freshness checks precede each record and mutation. Validate exact population and protected trees, normal suite at milestones and completion.'))
    bind(P+'authority.json',OWNER,'Execute exactly the isolated thirteen-record background reassessment described in this current owner authority; previous population-specific approval/triage is nonbinding. Preserve every other settled decision. No site or R2 mutation, merge, PR208 change, or planning-snapshot movement. Push every completed review separately.',{'candidate_ids':IDS,'task_ids':[TASK]})
    audit([P+'prior-records.json',P+'starting-remote-state.json',P+'progress.json'],'Frozen input/progress/remote evidence; no independent binding instruction.')
    refresh()
    result=G.active_check('mutation','document_review')
    save(P+'bootstrap-validation.json',dict(timestamp=now(),result=result,review_started=False))
    print('Bootstrap validated')
def complete_bootstrap():
    # Owner expressly reopens only this population's approvals; other decisions survive.
    registry=G.load(G.REGISTRY);proposals={}
    prefixes=['decision-decisions-b8452592-five-review-exception-2026-10-03-two-county-correction','decision-next-ordinary-queue-b8bb5c70-five-review-exception-2026-10-03-two-county-correction','decision-decision-updates-b04354f2','decision-decisions-2c491c71']
    for gid in prefixes:
        old=next(r for r in registry['entries'] if r['governance_id']==gid)
        new_id=gid+'-remaining-thirteen-exception'
        new=copy.deepcopy(old)
        requirement=old['binding_requirement']+' Explicit current owner exception: prior eligibility/approval and triage for exactly the thirteen IDs in '+P+'population.json are nonbinding for independent reassessment under '+OWNER+'. All other record decisions, PR207 owner exclusions, five resolved PR208 records, settled consolidation, original provenance and size/storage gates are preserved.'
        new.update(governance_id=new_id,effective_date='2026-10-03',authority='Explicit current owner thirteen-record background review instruction',binding_requirement=requirement,required_actions=[requirement],settled_decisions=[])
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        proposals[gid]=dict(authorized=True,existing_governance_id=gid,current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Reassess only exact thirteen population approvals; preserve all other scope, provenance, consolidation, archive and owner decisions.',authorization_artifact=P+'authority.json')
        old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'authority.json');registry['entries'].append(new)
    save(G.REGISTRY,registry);save(P+'supersession.json',dict(proposals=proposals))
    bind(P+'supersession.json','supersession-'+TASK,'Apply only the exact authorized approval exceptions recorded here. All other settled decisions and historical evidence remain controlling.',{'task_ids':[TASK]})
    pop=G.load(P+'population.json');pop['artifact_paths']+=['project-state/workflow-stage-lifecycle.json']
    # No review has begun; replacing the bootstrap population preserves the same 13 IDs.
    G.write_once(P+'population-v2.json',pop)
    pop['artifact_paths'] += [P+'population-v2.json']
    # Freeze the complete anticipated output list in a new immutable population.
    pop['artifact_paths'] += [P+'population-v3.json']
    G.write_once(P+'population-v3.json',pop)
    lifecycle=G.load('project-state/workflow-stage-lifecycle.json')
    assert lifecycle['stages'][-1]['id']=='pr208-county-scope-correction'
    lifecycle['stages'][-1]['end_commit']=BASE
    lifecycle['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/Review-RemainingApproved.py'],exact_delta_guard=dict(module='Review-RemainingApproved',function='guard_current_delta')))
    save('project-state/workflow-stage-lifecycle.json',lifecycle)
    audit([P+'prior-records.json',P+'starting-remote-state.json',P+'progress.json'],'Frozen input/progress/remote evidence; no independent authority.')
    refresh()
    result=G.active_check('mutation','document_review')
    guard_current_delta()
    save(P+'bootstrap-validation.json',dict(timestamp=now(),result=result,review_started=False,protected_trees_unchanged=True,r2_changes=0))
def guard_current_delta():
    pop=G.load(G.load(G.ACTIVE_TASK)['population']); assert pop['candidate_ids']==IDS and pop['baseline_commit']==BASE
    assert not git('diff',BASE,'--name-only','--','content','layouts','assets','static','hugo.toml')
    assert not git('ls-files','--others','--exclude-standard','--','content','layouts','assets','static')
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert not git('diff',BASE,'--name-only','--',path)
    prior=json.loads(git('show',BASE+':project-state/master-inventory.json'));current=G.load('project-state/master-inventory.json')
    a={r['id']:r for r in prior['candidates']};b={r['id']:r for r in current['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for path in git('ls-tree','-r','--name-only',BASE,'--','project-state/governance/strong-five-review-2026-10-03','project-state/governance/pr208-county-scope-correction-2026-10-03','project-state/governance/pr207-owner-correction-2026-09-30').splitlines():
        assert not git('diff',BASE,'--name-only','--',path),path
    return True
def begin():
    rid=sys.argv[2];assert rid in IDS
    G.active_check('mutation','document_review',[rid]);guard_current_delta()
    ledger=G.load(P+'progress.json');row=next(r for r in ledger['records'] if r['id']==rid)
    assert row['state'] in ['not_started','in_progress']
    row['state']='in_progress';row['started_at']=now();ledger['last_pushed_commit']=git('rev-parse','origin/codex/'+TASK)
    for prior in ledger['records']:
        if prior['state']=='complete' and not prior['checkpoint_commit_sha']:
            prior['checkpoint_commit_sha']=git('log','-1','--format=%H','--',prior['review_artifact_path'])
    save(P+'progress.json',ledger)
    print(rid,'in_progress; current contract',G.load(G.ACTIVE_TASK)['contract'])
def retrieve():
    import urllib.request, urllib.error
    from bs4 import BeautifulSoup
    rid,label,url=sys.argv[2:5];assert rid in IDS and label in ['source','current','supplement']
    G.active_check('mutation','document_review',[rid])
    root=P+'records/'+rid+'/'
    receipts=G.load(root+'retrievals.json') if (G.ROOT/(root+'retrievals.json')).exists() else dict(records=[])
    receipt=dict(url=url,label=label,attempted_at=now(),fresh=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ABQInfo official-source review'}),timeout=35) as response:
            receipt.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),content_length=response.headers.get('Content-Length'))
            if 'pdf' in response.headers.get('Content-Type','').lower() or url.lower().split('?')[0].endswith('.pdf'):
                receipt['body_read']=False;body=None
            else:
                body=response.read(4000001); assert len(body)<=4000000,'Oversize HTML'
                path=root+label+'.html';(G.ROOT/path).parent.mkdir(parents=True,exist_ok=True);(G.ROOT/path).write_bytes(body)
                receipt.update(saved_source=path,size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    except Exception as e:
        receipt.update(http_status=getattr(e,'code',None),error=str(e));body=None
    receipts['records'].append(receipt);save(root+'retrievals.json',receipts)
    print(json.dumps(receipt))
    if body:
        soup=BeautifulSoup(body,'html.parser'); core=soup.select_one('#content-core') or soup.select_one('main') or soup
        if 'bernco.gov' in url:
            elements=soup.select('.et_pb_text_inner')
            core=next((x for x in elements if 'Project Scope' in x.get_text()),None) or (max(elements,key=lambda x:len(x.get_text())) if elements else core)
        text=core.get_text(' ',strip=True)
        target=root+('article.txt' if label=='source' else label+'.txt');(G.ROOT/target).write_text(text,encoding='utf-8')
        print(text[:18000])
def witness():
    from bs4 import BeautifulSoup
    rid=sys.argv[2];G.active_check('mutation','document_review',[rid]);root=P+'records/'+rid+'/'
    old=G.load('project-state/discovery/human-review-reassessment-2026-09-26/retrievals.json')['records']
    old += G.load('project-state/discovery/background-followup-2026-09-26/retrievals.json')['records']
    hits=[r for r in old if r.get('id')==rid and r.get('http_status')==200]
    for item in hits:
        data=(G.ROOT/item['saved_source']).read_bytes();assert len(data)==item['size_bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
        soup=BeautifulSoup(data,'html.parser');elements=soup.select('.et_pb_text_inner')
        core=next((x for x in elements if 'Project Scope' in x.get_text()),None) or soup.select_one('#content-core') or (max(elements,key=lambda x:len(x.get_text())) if elements else soup)
        text=core.get_text(' ',strip=True)
        (G.ROOT/root).mkdir(parents=True,exist_ok=True)
        (G.ROOT/(root+'article.txt')).write_text(text,encoding='utf-8')
        (G.ROOT/(root+'article.html')).write_text('<html><meta charset="utf-8"><body>'+str(core)+'</body></html>',encoding='utf-8')
        receipt={k:v for k,v in item.items() if k not in ['text_excerpt','links_artifact','links_artifact_sha256','link_count']}
        receipt.update(witness='historical_official_capture_not_fresh',exact_bytes_reverified=True,article_text=root+'article.txt',article_html=root+'article.html',article_word_count=len(text.split()))
        receipts=G.load(root+'retrievals.json') if (G.ROOT/(root+'retrievals.json')).exists() else dict(records=[])
        receipts['records'].append(receipt);save(root+'retrievals.json',receipts)
        print(json.dumps(receipt));print(text[:16000])
def finish():
    rid=sys.argv[2];root=P+'records/'+rid+'/';review=G.load(root+'review.json')
    task=G.load(G.ACTIVE_TASK);contract=G.load(task['contract'])
    G.freshness(contract,G.load(task['population']),G.registry(),G.file_hash(G.REGISTRY))
    G.validate_plan(contract,{**G.load(task['implementation']),'actions':['inventory_disposition']},'mutation');guard_current_delta()
    bind(root+'review.json','decision-'+TASK+'-'+rid,review['binding_requirement'],{'candidate_ids':[rid],'task_ids':[TASK]},'Record-specific independent review under explicit owner campaign authority')
    registered={a['path'] for r in G.load(G.REGISTRY)['entries'] for a in r['controlling_artifacts']}
    paths=[f.relative_to(G.ROOT).as_posix() for f in (G.ROOT/P).rglob('*') if f.is_file() and f.suffix in ['.json','.txt','.md','.html'] and f.relative_to(G.ROOT).as_posix() not in registered and f.name!='implementation.json' and not f.name.startswith('contract-v')]
    audit(paths+['project-state/master-inventory.json'],'Research, source extracts, progress, accounting and existing materialized inventory evidence; active decisions are separately registered.')
    refresh();G.active_check('mutation','inventory_disposition',[rid])
    if review.get('approved_updates'):
        subprocess.run(['py','-3.13','scripts/project/Update-CandidatesBatch.py','--requests',root+'review.json'],cwd=G.ROOT,check=True)
    queue_pointer=G.load('project-state/ordinary-queue-current.json');queue=G.load(queue_pointer['artifact'])
    rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
    queue['newly_approved_backlog']=[r for r in queue['newly_approved_backlog'] if rows[r['id']]['status']=='approved for addition']
    queue['campaign_review']=dict(task=TASK,progress=P+'progress.json',population=P+'population-v3.json')
    save(P+'queue.json',queue);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    plan=G.load(P+'implementation.json');plan['events']=[e for e in plan['events'] if e.get('candidate_ids')!=[rid]];plan['events'].append(dict(operation='document_review',candidate_ids=[rid],governance_ids=plan['respected_governance_ids'],action='implements',summary=review['rationale'],evidence=root+'review.json'));save(P+'implementation.json',plan)
    ledger=G.load(P+'progress.json');row=next(r for r in ledger['records'] if r['id']==rid)
    row.update(state='complete',completed_at=now(),research_evidence_paths=review['evidence'],review_artifact_path=root+'review.json',resulting_disposition=review['outcome'],inventory_mutation_applied=bool(review.get('approved_updates')),unresolved_blocker=review.get('blocker'),owner_decision_required=review.get('owner_decision_required',False))
    ledger['next_unfinished']=next((r['id'] for r in ledger['records'] if r['state']!='complete'),None);save(P+'progress.json',ledger)
    # Update mutable nonbinding receipts, then pin a replacement immutable contract.
    audit([P+'queue.json',P+'progress.json','project-state/master-inventory.json'],'Generated queue, progress and inventory materialization of separately registered exact record decisions; no independent authority.')
    refresh();G.active_check('mutation','inventory_disposition',[rid]);guard_current_delta()
    subprocess.run(['git','diff','--check'],cwd=G.ROOT,check=True)
    row['validation_passed']=True;save(P+'progress.json',ledger)
    save(root+'validation.json',dict(timestamp=now(),candidate=rid,governance_contract=G.load(G.ACTIVE_TASK)['contract'],population_fresh=True,inventory_delta_within_exact_population=True,protected_tree_unchanged=True,r2_changes=0,diff_check='passed'))
    print('Completed',rid,review['outcome'],'; validate/commit/push before next record')
def prepare_review():
    rid=sys.argv[2];root=P+'records/'+rid+'/';review=G.load(root+'review.json')
    before=next(r for r in G.load(P+'prior-records.json')['records'] if r['id']==rid)
    scope=review['scope_assessment'];quality=review['quality_assessment']
    status='excluded' if review['outcome'].startswith('excluded') else 'approved for addition'
    changes=dict(status=status,scope_assessment=scope,quality_assessment=quality,validation_status='Independent background scope/quality/family/currentness review complete; see '+root+'review.json',review_reason='mission_scope_exclusion' if status=='excluded' and scope['final_scope_decision']=='excluded' else ('publication_quality_exclusion' if status=='excluded' else None),exclusion_reason=review['rationale'] if status=='excluded' else None,publication_quality_decision=dict(decision='excluded' if status=='excluded' else 'passes',finding_id=TASK+':'+rid,rationale=review['rationale'],evidence=review['evidence'],assessment=quality))
    if status=='excluded':changes.update(proposed_canonical_page=None,implementation_location=None,implementation_locations=[],cross_listing_approved=False)
    else: changes['proposed_canonical_page']=review['publication_plan']['canonical_page']
    changes['processing_notes']=before['processing_notes']+['2026-10-03 independent thirteen-record background review: '+review['rationale']+' Evidence: '+root+'review.json']
    review['approved_updates']=[dict(id=rid,changes=changes)];save(root+'review.json',review)
    if 'publication_plan' in review:save(root+'publication-plan.json',dict(id=rid,**review['publication_plan'],evidence=review['evidence']))
if __name__=='__main__': globals()[sys.argv[1] if len(sys.argv)>1 else 'guard_current_delta']()
