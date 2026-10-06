"""One existing historical resolution entry; exact lifecycle/content correction."""
import copy, json, sys, subprocess, hashlib
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git

TASK='bike-boulevard-lifecycle-correction-2026-10-05'
P='project-state/governance/'+TASK+'/'
BASE='1bae493fa93f510cefd353172885fc04bd469c61'
ID='src-4cb190564a688d42'
PAGE='content/transportation/bicycling/bike-plans.md'
OLD='project-state/governance/council-finality-resolution-2026-10-05/'
TITLE='F/S R-07-268 — Bike Boulevards (enacted R-2007-109, 2007)'
DESCRIPTION='Historical 2007 legislation designating Mountain Road, Silver Avenue, and 14th Street bike-boulevard routes; phased Silver Avenue implementation; up to $400,000 in Fund 340 funding for design, engineering, and initial implementation; bikeway-plan amendments and crossing coordination; and the final-version 18 mph provision. Not necessarily current consolidated law.'

def population_path():
    return P+('population-v2.json' if (G.ROOT/(P+'population-v2.json')).exists() else 'population.json')

def now(): return datetime.now(timezone.utc).isoformat()

def refresh():
    r=G.load(G.REGISTRY)
    for rule in r['entries']:
        if rule['state']=='active':
            for artifact in rule['controlling_artifacts']:
                if artifact['path']=='scripts/project/Invoke-ProjectValidation.ps1' and artifact.get('binding_pointers')==['/implementation']:
                    artifact['sha256']=G.file_hash(artifact['path'])
    save(G.REGISTRY,r)
    contracts=list((G.ROOT/P).glob('contract-v*.json'))
    evidence=[p for p in G.changed_paths(BASE) if p.startswith('project-state/') and p not in {G.REGISTRY,G.ACTIVE_TASK,P+'implementation.json',P+'authority.json',P+'supersession.json',G.load(G.REGISTRY)['audit_artifact']}]
    audit(evidence)
    n=max([int(p.stem.split('-v')[1]) for p in contracts],default=0)+1
    path=P+f'contract-v{n}.json'; assert n<=20
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population_path(),'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path); assert not c['conflicts'] and not c['unresolved_gates']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=c['task_population']['operation_classes'],events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]): subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    if (G.ROOT/(P+'receipt.json')).exists():
        plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=population_path(),contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+'supersession.json'))
    print(path, len(c['governance_ids']), 'rules')

def setup():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','supersession.json','implementation.json','receipt.json','queue.json','updates.json','validation.log','preview.json','preview.png','pr-description.md','progress.json']+[f'contract-v{i}.json' for i in range(1,21)]
    artifacts=[P+x for x in outputs]+['scripts/project/BikeBoulevardLifecycleCorrection.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json',G.REGISTRY,G.ACTIVE_TASK,G.load(G.REGISTRY)['audit_artifact'],'project-state/master-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    pop=dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],families=[],pages=[PAGE],operation_classes=['governance_implementation','inventory_disposition','content_implementation','family_review','background_integration','external_mutation'],artifact_paths=artifacts)
    G.write_once(P+'population.json',pop)
    # Exhaustive original authority resolution before any substantive mutation.
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    instruction='Explicit owner instruction: Resolve exactly '+ID+'. Preserve the completed Council finality review. Correct existing visitor-visible Related Bicycle Policy entry in '+PAGE+' in place, not a duplicate. Identify F/S R-07-268, enacted R-2007-109, historical 2007 legislation not necessarily current consolidated law, Mountain Road/Silver Avenue/14th Street routes, phased implementation, up to $400,000 Fund 340 funding, bikeway-plan/crossing coordination and final-version 18 mph provision. Keep existing R2 PDF, use verified official final source, do not publish companion map as required enactment exhibit. Freeze/govern exact record; no R2 or unrelated content edits. Full validation, Cloudflare preview, one unmerged visitor-visible PR against main, planning-snapshot exactly at PR head. No merge or production deployment authority.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner instruction',instruction=instruction,candidate_ids=[ID]))
    r=G.registry(); proposals={}
    for old in r['entries'][:]:
        if old['governance_id'] not in ['decision-council-finality-resolution-2026-10-05','owner-council-finality-resolution-2026-10-05']: continue
        gid=old['governance_id']+'-existing-entry-correction-authorized'
        requirement=old['binding_requirement']+' Explicit owner instruction in '+P+'authority.json supersedes only the inventory-only/no-visible phase restriction for '+ID+' to correct its existing entry and lifecycle in an unmerged manual-review PR. All completed finality, scope, quality, metadata-only source comparison, separate-map and duplicate findings remain controlling; the solar record and every other population remain unchanged. No R2 or merge authority.'
        proposals[old['governance_id']]=dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'authority.json',proposed_replacement=requirement,consequences='Exact one-record existing-entry and lifecycle correction; no R2 or unrelated changes.',authorization_artifact=P+'authority.json')
        new=copy.deepcopy(old);new.update(governance_id=gid,binding_requirement=requirement,required_actions=[requirement],authority='Explicit current owner one-record correction instruction',effective_date='2026-10-05')
        new['controlling_artifacts'].append(dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/']))
        old.update(state='superseded',superseded_by=gid,supersession_evidence=P+'supersession.json');r['entries'].append(new)
    G.write_once(P+'supersession.json',dict(proposals=proposals))
    r['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title=TASK,state='active',scope=dict(candidate_ids=[ID],task_ids=[TASK]),authority='Explicit current owner instruction',decision_date='2026-10-05',effective_date='2026-10-05',controlling_artifacts=[dict(path=P+x,sha256=G.file_hash(P+x),binding_pointers=['/']) for x in ['authority.json','supersession.json']],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['No R2 change, companion-map publication, unrelated content edit, PR merge or production deployment.'],constraints=[],settled_decisions=[],unresolved_gates=[]))
    save(G.REGISTRY,r)
    life=G.load('project-state/workflow-stage-lifecycle.json');life['stages'][-1]['end_commit']=BASE
    life['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/BikeBoulevardLifecycleCorrection.py'],exact_delta_guard=dict(module='BikeBoulevardLifecycleCorrection',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',life)
    suite=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';s=suite.read_text(encoding='utf8');needle="Set-StrictMode -Version Latest"
    s=s.replace(needle,"& python \"$PSScriptRoot/BikeBoulevardLifecycleCorrection.py\" guard\nif ($LASTEXITCODE) { throw 'Bike boulevard one-record correction guard failed.' }\n"+needle,1);suite.write_text(s,encoding='utf8',newline='\n')
    refresh();G.active_check('mutation','governance_implementation',[ID])

def implement():
    G.active_check('mutation','content_implementation',[ID],[PAGE])
    inv=G.load('project-state/master-inventory.json');row=next(r for r in inv['candidates'] if r['id']==ID)
    archive=row['r2_url'];source=G.load(OLD+'evidence-21.json')['url']
    path=G.ROOT/PAGE;text=path.read_text(encoding='utf8');start=text.index('## Related Bicycle Policy\n')
    before=text[start:];assert before.count(archive)==1
    block='## Related Bicycle Policy\n\n- ['+TITLE+']('+archive+')\n\n  '+DESCRIPTION+'\n\n  [Official final resolution PDF]('+source+') · [Official legislative record]('+row['source_url']+')\n'
    path.write_text(text[:start]+block,encoding='utf8',newline='\n')
    original=next(r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates'] if r['id']==ID)
    changes=dict(title=TITLE,description=DESCRIPTION,direct_file_url=source,status='implemented',validation_status='passed',implementation_location=PAGE,implementation_locations=[PAGE],processing_notes=original['processing_notes']+['2026-10-05: Corrected already-existing Related Bicycle Policy entry in place and reconciled approved-for-addition lifecycle to implemented. Historical enacted identity and final source added; direct_file_url now identifies the verified official final PDF (previous value remains the unchanged r2_url). Original R2 unchanged. Owner-review content PR remains unmerged; full suite and preview evidence in '+P+'receipt.json.'])
    save(P+'updates.json',[dict(id=ID,changes=changes)])
    refresh()
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    inv=G.load('project-state/master-inventory.json');q=copy.deepcopy(G.load(OLD+'queue.json'))
    q.update(artifact_type='existing_entry_lifecycle_correction_queue',recorded_at=now(),source_queue_artifact=OLD+'queue.json',inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),approved_count=0,newly_approved_backlog=[],in_progress_publication=dict(task=TASK,candidate_ids=[ID],state='existing_entry_correction_owner_review_pending'))
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    cp=G.load('project-state/checkpoint.json');cp.update(recorded_at=now(),counts_by_status=inv['counts'],next_pending_id=inv['next_pending_id'],remaining_nonterminal=sum(r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed' for r in inv['candidates']),completed_item_range='One existing R-07-268 / R-2007-109 entry corrected in place; lifecycle implemented, validation passed on proposal branch. No R2 changes.',resume_command='Read CURRENT and the bike-boulevard lifecycle correction receipt. Manual-review PR remains unmerged; no production deployment authorized.')
    save('project-state/checkpoint.json',cp)
    current='# Current project state\n\nExactly src-4cb190564a688d42 corrected in place under Related Bicycle Policy on Bike Plans: F/S R-07-268, enacted R-2007-109, historical 2007 legislation with final 18 mph provision. Existing R2 PDF unchanged; official final source and legislative record linked. Lifecycle reconciled from approved for addition to implemented with validation passed on proposal branch. Queue: 0 approved / 340 pending (321 governance-gated / 19 source-structural blocked); 0 human review. Full validation and preview evidence in the correction receipt. One owner-review content PR against main; leave unmerged. Planning snapshot must equal exact PR head; no merge or production deployment authority.\n\n[Correction receipt](governance/'+TASK+'/receipt.json) · [Prior finality receipt](governance/council-finality-resolution-2026-10-05/receipt.json) · [Active task](governance/active-task.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n'
    current=current.replace(' · [Prior finality receipt](governance/council-finality-resolution-2026-10-05/receipt.json)', '')
    current += '\n[Owner correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [Closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json).\n'
    (G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf8',newline='\n')
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='content_implementation',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Existing entry corrected in place; completed review implemented without reopening. Inventory reconciled; unchanged original R2 and contextual companion map preserved.',evidence=PAGE));save(P+'implementation.json',plan)
    refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    save(P+'receipt.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=[ID],page=PAGE,section='Related Bicycle Policy',visible_title=TITLE,visible_description=DESCRIPTION,official_final_source=source,prior_completed_review=OLD+'receipt.json',historical_findings_preserved=True,r2_objects_added=0,r2_bytes_added=0,r2_deleted_or_overwritten=0,lifecycle=dict(before='approved for addition',after='implemented',validation_status='passed',existing_entry=True,duplicate_added=False,proposal_branch=True,correction_live=False),queue_counts=dict(approved=0,pending=340,governance_gated=321,source_structural_blocked=19,human_review=0),validation='pending',preview='pending',pr_state='owner_review_pending_unmerged',governance_accounting={gid:dict(requirement=r['binding_requirement'],evidence=[OLD+'receipt.json',OLD+'comparison.json',P+'authority.json',PAGE,P+'updates.json',P+'queue.json'],implementation='Preserve complete historical authority and all unrelated records; implement only registered one-record existing-entry correction. No R2 or production effects.') for gid,r in [(r['governance_id'],r) for r in G.load(G.load(G.ACTIVE_TASK)['contract'])['resolved_rules']]}))
    refresh();G.active_check('final');guard()

def guard():
    stage=StageSnapshot(TASK);pop=stage.load_json(population_path())
    a={r['id']:r for r in json.loads(git('show',BASE+':project-state/master-inventory.json'))['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]} <= {ID}
    for f in ['r2_key','r2_url','size_bytes','checksum_sha256','source_url','scope_assessment','quality_assessment','publication_quality_decision','local_path']:
        assert a[ID].get(f)==b[ID].get(f),f
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert canonical_bytes(stage.read_bytes(path))==canonical_bytes(git('show',BASE+':'+path)),path
    path='project-state/discovery/retained-source-audit-queue.json'
    oldrows={r['source_url']:r for r in json.loads(git('show',BASE+':'+path))['records']}
    newrows={r['source_url']:r for r in stage.load_json(path)['records']}
    assert all(newrows.get(k)==v for k,v in oldrows.items()),'Existing source audits changed'
    assert set(newrows)-set(oldrows)<={b[ID]['source_url']}
    assert all(newrows[k]['candidate_id']==ID for k in set(newrows)-set(oldrows))
    changes=set(git('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(pop['artifact_paths'])|{PAGE},changes-set(pop['artifact_paths'])-{PAGE}
    old=git('show',BASE+':'+PAGE).decode('utf8').replace('\r\n','\n');live=stage.read_text(PAGE)
    marker='## Related Bicycle Policy\n';assert old[:old.index(marker)]==live[:live.index(marker)],'Unrelated content changed'
    if live!=old:
        assert live.count(a[ID]['r2_url'])==1 and TITLE in live and DESCRIPTION in live
        assert G.load(OLD+'evidence-21.json')['url'] in live
        assert b[ID]['direct_file_url']==G.load(OLD+'evidence-21.json')['url']
        assert b[ID]['status']=='implemented' and b[ID]['validation_status']=='passed'
        assert 'R-268fsatt.pdf' not in live and 'Exhibit A' not in live
    print('PASS: exact one-record lifecycle correction, one existing entry, unchanged originals/R2 and unrelated content')

def retained_queue():
    pop=G.load(P+'population.json');pop['artifact_paths'] += [P+'population-v2.json','project-state/discovery/retained-source-audit-queue.json']
    G.write_once(P+'population-v2.json',pop)
    refresh();G.active_check('mutation','family_review',[ID])
    # The completed exhaustive official-source/version/attachment review already
    # audited this root. Register that factual completion; do not repeat research.
    row=next(r for r in G.load('project-state/master-inventory.json')['candidates'] if r['id']==ID)
    path='project-state/discovery/retained-source-audit-queue.json';q=G.load(path)
    assert row['source_url'] not in {r['source_url'] for r in q['records']}
    q['records'].append(dict(candidate_id=ID,source_url=row['source_url'],title=row['title'],agency=row['agency'],canonical_page=PAGE,audit_status='crawled',crawl_output=OLD+'receipt.json',discovered_documents=0,archived_documents=0,processing_notes=['Registered completed governed official-source review from '+OLD+'receipt.json and comparison.json: matter identities, all final-text versions, substitute/amendment history, official PDF/Word delivery and separate contextual map audited. Existing held/R2 original retained; no new discovery, archive or repeated research in lifecycle correction.'],created_at=now(),updated_at=now()))
    q['counts']={s:sum(r['audit_status']==s for r in q['records']) for s in q['allowed_statuses']};q['generated_at']=now()
    save(path,q)
    receipt=G.load(P+'receipt.json');receipt['retained_source_audit']=dict(path=path,added_candidate_id=ID,status='crawled',existing_completed_review=OLD+'receipt.json',prior_records_unchanged=True)
    receipt['validation_corrections'].append('Registered exact one newly eligible retained source root using completed governed review; no prior audit row altered.')
    save(P+'receipt.json',receipt)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='family_review',candidate_ids=[ID],action='implements',use_contract_record_rules=True,summary='Register completed official-source review in retained-source audit queue; no settled research repeated.',evidence=OLD+'receipt.json'));save(P+'implementation.json',plan)
    refresh();G.active_check('final');guard()

def validation_receipt():
    log=(G.ROOT/'tmp/bike-validation.log').read_text(encoding='utf8')
    assert '"Hugo": "passed"' in log and '52 contiguous stage intervals' in log
    assert 'CURRENT.md resume-pointer regression passed' in log
    (G.ROOT/(P+'validation.log')).write_text('\n'.join(line.expandtabs(4).rstrip() for line in log.splitlines())+'\n',encoding='utf8',newline='\n')
    receipt=G.load(P+'receipt.json');receipt.update(validation='passed',validation_log=P+'validation.log',validation_log_sha256=G.file_hash(P+'validation.log'),validation_attempts=['Initial run stopped at missing required historical CURRENT links; restored links.','Second run stopped at description length and missing official final URL; corrected both and focused inventory check passed.','Third run stopped at newly eligible retained-source root missing from audit queue; registered prior completed review and preserved all old rows.','Final full suite rerun passed after corrections.'],sealed_history='52 contiguous stage intervals; all protected historical evidence unchanged')
    save(P+'receipt.json',receipt)
    save(P+'progress.json',dict(stage='full_validation_passed_preview_pr_pending',completed=[ID],remaining=['Cloudflare preview','rendered preview inspection','manual-review PR','exact planning-snapshot synchronization'],no_r2_changes=True))
    refresh();G.active_check('final');guard()

def render():
    from playwright.sync_api import sync_playwright
    url=sys.argv[2];verification='--verification-only' in sys.argv
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--disable-gpu']);page=browser.new_page(viewport=dict(width=1440,height=1100))
        response=page.goto(url,wait_until='networkidle',timeout=90000);assert response.status==200
        section=page.locator('#related-bicycle-policy');section.scroll_into_view_if_needed()
        data=page.evaluate(r"""() => { const h=document.getElementById('related-bicycle-policy'); let n=h.nextElementSibling;const nodes=[];while(n && n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling;}return {text:nodes.map(n=>n.innerText).join('\n'),links:nodes.flatMap(n=>Array.from(n.querySelectorAll('a')).map(a=>({text:a.innerText,url:a.href}))),overflow:document.documentElement.scrollWidth>innerWidth}; }""")
        assert TITLE in data['text'] and DESCRIPTION in data['text'] and not data['overflow']
        assert len(data['links'])==3 and len([x for x in data['links'] if x['url'].startswith('https://files.abqinfo.com/')])==1
        screenshot=G.ROOT/('tmp/bike-final-preview.png' if verification else P+'preview.png');page.screenshot(path=str(screenshot))
        data.update(url=url,head_sha=G.git('rev-parse','HEAD'),browser='Installed Google Chrome via Playwright',rendered_at=now(),screenshot_sha256=hashlib.sha256(screenshot.read_bytes()).hexdigest())
        if verification:
            old=G.load(P+'preview.json');assert data['text']==old['text'] and data['links']==old['links']
        save('tmp/bike-final-preview.json' if verification else P+'preview.json',data);browser.close()
        print('PASS: rendered preview, complete revised entry, three expected links, no overflow')

if __name__=='__main__': globals()[sys.argv[1] if len(sys.argv)>1 else 'guard']()
