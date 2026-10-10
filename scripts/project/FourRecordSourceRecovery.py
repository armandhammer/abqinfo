"""Exact four-record recovery; source evidence only unless a governed inventory update is recorded."""
import copy, gzip, hashlib, json, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from PgsLegislativeResolution import save, audit
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes
import Progress2004Recovery as Prior
TASK='four-record-source-recovery-2026-10-10'
P='project-state/governance/'+TASK+'/'
BASE='d63f04918d2437de176a4cbeb30d4a59c4348eb2'
REMOTE='349a6ca93a5df42fa8a332deb16f93ffb58d5580'
IDS=['lin-2f6fbe4ffb0b6564','lin-7bdbcdc09efe2035','src-158f843cc102a40f','src-352d880cb11386d3']
SCRIPT='scripts/project/FourRecordSourceRecovery.py'
RUNNER='scripts/project/Invoke-ProjectValidation.ps1'
OPS=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration']
def now():return datetime.now(timezone.utc).isoformat()
def rows():
    out=[]
    for i in IDS:Prior.ID=i;out.append(Prior.target())
    return out
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    outputs=['population.json','authority.json','starting-state.json','implementation.json','progress.json','receipt.json','summary.md','validation.log','prior-research.json','research-journal.json','accounting.json','supersession.json','integration-intent.json','remote-final.json','governance-review.json','updates.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,61)]+[P+f'evidence-{i}.{ext}' for i in range(1,161) for ext in ['json','gz','txt','png','pdf']]
    paths += [SCRIPT,RUNNER,G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md',P+'queue.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=['content/city-data/city-progress-surveys.md'],operation_classes=OPS,artifact_paths=paths))
    protected=['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']
    priorpaths=G.git('ls-files','project-state/governance/progress-2004-source-recovery-2026-10-09','project-state/governance/progress-2004-remote-checkpoint-2026-10-10').splitlines()
    G.write_once(P+'starting-state.json',dict(observed_at=now(),selected_records=rows(),baseline_commit=BASE,remote_refs={'main':REMOTE,'chatgpt/planning-snapshot':REMOTE,'codex/progress-2004-source-recovery-2026-10-10':BASE},protected_sha256={x:G.file_hash(x) for x in protected},prior_recovery_sha256={x:G.file_hash(x) for x in priorpaths},content_tree=G.git('rev-parse',BASE+':content'),queue_pointer=G.load('project-state/ordinary-queue-current.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True)
    c=G.load(P+'contract-v1.json');assert not c['conflicts'],c['conflicts']
    print('Frozen exact four records; initial immutable contract:',P+'contract-v1.json')
def refresh():
    r=G.load(G.REGISTRY)
    actual=(G.ROOT/RUNNER).read_text(encoding='utf-8').strip();base=G.git('show',BASE+':'+RUNNER)
    addition='& python "$PSScriptRoot/FourRecordSourceRecovery.py" guard\nif ($LASTEXITCODE) { throw "Four-record recovery boundary failed" }\n'
    expected=base.replace('Set-StrictMode -Version Latest',addition+'Set-StrictMode -Version Latest',1)
    assert actual in (base,expected)
    if actual==expected:
        a=next(a for x in r['entries'] if x['governance_id']=='policy-durable-task-governance' for a in x['controlling_artifacts'] if a['path']==RUNNER);a['sha256']=G.file_hash(RUNNER);save(G.REGISTRY,r)
    audit([x.relative_to(G.ROOT).as_posix() for x in (G.ROOT/P).glob('*') if x.is_file() and x.name not in ['authority.json','supersession.json','implementation.json','governance-review.json']])
    n=max(int(x.stem.split('-v')[1]) for x in (G.ROOT/P).glob('contract-v*.json'))+1;assert n<=60
    path=P+f'contract-v{n}.json';subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='research_in_progress')
    subjects={}
    for row in c['resolved_rules']:
        for f in row.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    ev=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=ev,sha256=G.file_hash(ev))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+('governance-review.json' if (G.ROOT/(P+'governance-review.json')).exists() else 'supersession.json')))
    print(path,len(c['governance_ids']),'rules; gates:',c['unresolved_gates'])
def event(summary,evidence,ids=IDS,op='document_review',action='implements'):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=ids,action=action,use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)
def guard():
    st=StageSnapshot(TASK);v=st.load_json(P+'starting-state.json');pop=st.load_json(P+'population.json');assert pop['candidate_ids']==IDS and pop['baseline_commit']==BASE
    st.assert_no_visible_changes(REMOTE,v['content_tree'])
    for path,h in {**v['protected_sha256'],**v['prior_recovery_sha256']}.items():
        if path in ['project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']:continue
        assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==h,'Protected evidence/state changed: '+path
    baseline=json.loads(G.git('show',BASE+':project-state/master-inventory.json'));inv=st.load_json('project-state/master-inventory.json')
    before={r['id']:r for r in baseline['candidates']};after={r['id']:r for r in inv['candidates']};assert before.keys()==after.keys()
    delta={i for i in before if before[i]!=after[i]};assert delta<=set([IDS[2]]),delta
    if delta:
        u=st.load_json(P+'updates.json')['approved_updates'];assert len(u)==1 and u[0]['id']==IDS[2]
        expected={**before[IDS[2]],**u[0]['changes'], 'updated_at':after[IDS[2]]['updated_at']};assert expected==after[IDS[2]],'Inventory differs from exact approved update'
        assert after[IDS[2]]['status']=='approved for addition'
        for n in [1,24]:
            src=st.load_json(P+f'evidence-{n}.json');raw=gzip.decompress(st.read_bytes(src['preserved_response']))
            assert len(raw)==3896692 and raw.startswith(b'%PDF-') and hashlib.sha256(raw).hexdigest()==after[IDS[2]]['checksum_sha256']
        assert st.load_json(P+'evidence-3.json')['page_count']==76 and st.load_json(P+'evidence-3.json')['all_76_pages_rendered_and_visually_inspected'] is True
        from PublicationQuality import require_publication_quality
        require_publication_quality(after[IDS[2]])
        assert before[IDS[2]]['source_url'] in after[IDS[2]]['processing_notes'][-1]
        assert after[IDS[2]]['processing_notes'][:len(before[IDS[2]]['processing_notes'])]==before[IDS[2]]['processing_notes']
        for field in ['r2_url','r2_key','implementation_location','implementation_locations']:assert before[IDS[2]][field]==after[IDS[2]][field]
        q=st.load_json(P+'queue.json');pending={i for i,r in after.items() if r['status']=='pending review'};approved={i for i,r in after.items() if r['status']=='approved for addition'}
        assert set(q['pending_ids'])==pending and {r['id'] for r in q['newly_approved_backlog']}==approved=={IDS[2]}
        assert (len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(332,321,11)
        assert st.load_json('project-state/checkpoint.json')['remaining_nonterminal']==884
        assert st.load_json('project-state/discovery/consolidated-human-review-queue.json')['record_count']==0
    else:
        for path in ['project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json']:
            assert hashlib.sha256(canonical_bytes(st.read_bytes(path))).hexdigest()==v['protected_sha256'][path]
    changes=set(G.git('diff',BASE,st.end,'--name-only').splitlines()) if st.end else set(G.changed_paths(BASE));assert changes<=set(pop['artifact_paths']),changes-set(pop['artifact_paths'])
    print('PASS exact four-record recovery: at most conclusive Volcano update; other rows, prior evidence, R2 and visitor-visible state preserved')

def get(url,label,ids=IDS,body=None):
    G.active_check('mutation','document_review',ids)
    n=max([int(x.stem.split('-')[1]) for x in (G.ROOT/P).glob('evidence-*.json')],default=0)+1
    rec=dict(requested_url=url,label=label,candidate_ids=ids,requested_at=now(),method=('POST read-only query' if body else 'GET'),query_body=body,state='request_intent');save(P+f'evidence-{n}.json',rec)
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,headers={'User-Agent':'Mozilla/5.0 (ABQInfo public source recovery)',**({'Content-Type':'application/json'} if body else {})})
        try:resp=urllib.request.urlopen(req,timeout=25)
        except urllib.error.HTTPError as e:resp=e
        with resp:data=resp.read(150000001);rec.update(final_url=resp.geturl(),http_status=resp.status,content_type=resp.headers.get('Content-Type'))
        assert len(data)<=150000000
        (G.ROOT/(P+f'evidence-{n}.gz')).write_bytes(gzip.compress(data,mtime=0))
        scratch=G.ROOT/'research/staging'/TASK;scratch.mkdir(parents=True,exist_ok=True);(scratch/f'{n}.bin').write_bytes(data)
        rec.update(state='response_saved',size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),preserved_response=P+f'evidence-{n}.gz',pdf_header=data.startswith(b'%PDF-'))
    except Exception as e:rec.update(state='request_failed',error=str(e))
    save(P+f'evidence-{n}.json',rec)
    print(json.dumps(rec));return rec
def assess():
    assert not (G.ROOT/(P+'governance-review.json')).exists(), 'Binding assessment already registered; reuse its immutable findings rather than rerun.'
    G.active_check('mutation','quality_assessment',[IDS[2]])
    original=G.load(P+'starting-state.json')['selected_records'][2]
    evidence=[P+f'evidence-{n}.json' for n in [1,2,3,6,9,24]]
    scope=dict(assessed_at='2026-10-10',geographic_institutional_scope='City of Albuquerque Volcano Park and West Mesa public open space, planned by the City Open Space Task Force West Mesa Committee.',specific_albuquerque_connection='This adopted City master plan directly governs the conceptual development and preservation of the Albuquerque volcano park: named local sites, City access and trail routes, five facility areas and implementation priorities.',abqinfo_public_information_value='Explains the historical public land, conservation, recreation and access decisions that shaped a major Albuquerque open-space facility, with adopted goals, resource analysis and mapped proposals.',general_context_exclusion_test='Eligibility follows substantial place-specific City park policy, design and implementation content, rather than volcanic geology as generic context or an incidental Albuquerque reference.',final_scope_decision='passes_both_gates',substantive_rationale='The complete adopted original supplies a durable account of City choices about park land, resource protection, public recreation and infrastructure investment. Maps and facility designs tie those choices to specific Albuquerque sites, and the signed adoption pages establish a concrete municipal decision with meaningful historical public-information value.')
    quality=dict(assessed_at='2026-10-10',document_function='Complete historical City park master plan adopted by R-216-80 with signed mayoral approval.',substantive_content='Thirty-one numbered body pages analyze physical/cultural resources, goals and compatible uses; context and master-plan maps locate five intensive-use areas, access/trail concepts and facilities, design criteria and implementation priorities. Original appendices A-H provide supporting history, geology, biology, archaeology and interagency/public correspondence.',durable_public_usefulness='Readers can understand the origins and tradeoffs of Albuquerque volcano-park conservation, recreation and access policy and the specific facilities proposed in the adopted plan.',information_density='76 scan pages including title/adoption/frontmatter, 31 body pages, eight appendix openers and 29 numbered supporting pages. Substantial readable narrative, maps and conceptual designs; no machine text layer does not mean absent substantive content.',unique_information='Site-specific adopted1980 goals, original master-plan map, five facility-area proposals and phased implementation are not supplied by the incorrect Huning Castle sector-plan link or the broader1999 MPOS plan bibliography.',rationale='The original is a complete adopted program-level planning record, with resource analysis and mapped public-facility choices supported by appendices. Its substantive body has coherent standalone historical value for Albuquerque open-space policy; the appendices and adoption frontmatter remain inside one canonical original, avoiding separate low-value fragments or a misleading current-guidance claim.',reviewed_document_content=True,visual_inspection_completed=True,visual_inspection='All76 original pages rendered and inspected through seven contact sheets; durable title, resolution, approval, master-map and final-page images retained in evidence-3.png through evidence-7.png.',page_count=76,extracted_word_count=0,standalone_public_value='substantial',publication_form='standalone',series_relationship='standalone',family_review='Original complete master plan includes all supporting appendices. Huning Castle/Raynolds2002 is a different document;1999 MPOS is a broader contextual successor, not an alternate edition. No competing inventory canonical located. Do not split appendices into separate entries.',currentness_review_required=True,currentness_review=dict(status='historical_status_uncertain',authoritative_sources=evidence,finding='AdoptedSeptember22 1980 and mayorapprovedSeptember24. Current index still lists it but misdates1984/mislinks Huning Castle. Current legal/operational force is not established by this recovery. Scan packaging date2000 is not issue date.',publication_qualification='Historical1980 plan, not an assertion of current governing design or operational guidance; any later publication requires its own authorization and clear historical qualification.'))
    pq=dict(decision='passes',finding_id=TASK+':'+IDS[2],assessment=quality,evidence=evidence)
    changes=dict(status='approved for addition',date='1980-08-21',file_type='PDF',source_url='https://www.cabq.gov/planning/documents/volcano.pdf/view',direct_file_url='https://www.cabq.gov/planning/documents/volcano.pdf/@@download/file/volcano.pdf',size_bytes=3896692,checksum_sha256='1ca7c8e156ee434f3f52e83be0c137ba18e967b5c3d4b643746468e135c9a46e',local_path=None,scope_assessment=scope,quality_assessment=quality,publication_quality_decision=pq,review_reason=None,exclusion_reason=None,provenance_status='Complete original City PDF recovered; live official download and20150910232543 City historical capture are identical full3896692bytes/SHA256. TitleAugust21 1980 and signed R-216-80 reconcile incorrect1984/Huning index metadata. Preserved response is gzip storage of exact original bytes, not a new document.',proposed_canonical_page='content/public-works/parks-recreation.md',validation_status='Governed source/family/scope/quality approval inventory-only; no R2/archive/publication authorized. See '+P+'governance-review.json',processing_notes=original['processing_notes']+['2026-10-10 '+TASK+': complete1980 original recovered and all76 pages reviewed; full City/2015historical bytes identical. DateAugust21 1980; CounciladoptionSeptember22 and mayorapprovalSeptember24. Incorrect prior authored index URL preserved: '+original['source_url']+'. Index1984label rejected as unsupported; no1984edition inferred. One historical standalone plan, appendices retained together. Scope/quality pass. No R2, visitor-visible work or publication PR; separate archive authorization and verified public bytes remain future prerequisites. Evidence: '+P+'governance-review.json'])
    from PublicationQuality import require_publication_quality
    require_publication_quality({**original,**changes})
    updates=dict(approved_updates=[dict(id=IDS[2],changes=changes)])
    save(P+'updates.json',updates)
    exception=' Explicit current owner source-recovery exception solely for src-158f843cc102a40f under '+TASK+': conclusive newly recovered complete1980 City original, signed R-216-80 and exact historical byte parity satisfy the preserved title/incorrect-link/original prerequisite. Apply the recorded positive actual-file source/family/scope/quality assessment and inventory-only approval. Preserve original1984/Huning index evidence, historical notes and every unrelated decision. Bike Gap, San Antonio and2004 remain pending with unchanged holds. No R2, visible changes or publication PR; current operational/legal force is not asserted.'
    registry=G.registry();oldids=['decision-bikeway-2014-draft-resolution-2026-10-08-exception-'+str(n)+'-pr218-postmerge' for n in [1,2,4]]
    replacements=[]
    for gid in oldids:
        old=next(r for r in registry['entries'] if r['governance_id']==gid);assert old['state']=='active'
        replacements.append(dict(existing_governance_id=gid,new_governance_id=gid+'-volcano-recovery',authorized=True,authority=P+'authority.json',conclusive_evidence=evidence,prior_requirement=old['binding_requirement'],proposed_replacement=old['binding_requirement']+exception,consequences='Resolve only Volcano factual source hold and inventory eligibility; all historical/other dispositions preserved.'))
    save(P+'governance-review.json',dict(artifact_type='binding_source_family_scope_quality_decision',task_id=TASK,authority=P+'authority.json',exact_population=IDS,mutable_inventory_ids=[IDS[2]],decision='Approve Volcano original inventory-only; other three pending unchanged.',source=evidence,scope_assessment=scope,quality_assessment=quality,updates=P+'updates.json',supersession_proposals=replacements,binding_requirement=exception,remaining_archive_publication_gate='No R2/visible publication in this task. Separate authorization, exact public-byte verification and owner-review content PR would be required for publication.'))
    supersession=G.load(P+'supersession.json')
    for rr in replacements:
        old=next(r for r in registry['entries'] if r['governance_id']==rr['existing_governance_id']);new=copy.deepcopy(old)
        new.update(governance_id=rr['new_governance_id'],authority='Explicit current user conclusive source-recovery reconciliation instruction',binding_requirement=rr['proposed_replacement'],decision_date='2026-10-10',effective_date='2026-10-10')
        new['required_actions'] += [exception]
        new['controlling_artifacts'] += [dict(path=P+'governance-review.json',sha256=G.file_hash(P+'governance-review.json'),binding_pointers=['/']),dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
        old.update(state='superseded',superseded_by=new['governance_id'],supersession_evidence=P+'governance-review.json');registry['entries'].append(new)
        supersession['proposals'][old['governance_id']]={**rr,'authorization_artifact':P+'authority.json','current_decision':rr['prior_requirement'],'controlling_evidence':old['controlling_artifacts'],'new_evidence':P+'governance-review.json'}
    review=G.load(P+'governance-review.json');review['proposals']=supersession['proposals'];save(P+'governance-review.json',review)
    for row in registry['entries']:
        if row['governance_id'].endswith('-volcano-recovery'):
            for artifact in row['controlling_artifacts']:
                if artifact['path']==P+'governance-review.json':artifact['sha256']=G.file_hash(artifact['path'])
    save(G.REGISTRY,registry) # Preserve initial registered supersession receipt; combined proposals are in the replacement decision receipt.
    event('Complete Volcano original, family identity, two scope gates and substantive visual quality reviewed; explicit narrow factual-hold reconciliation registered. No other settled decision changed.',P+'governance-review.json',[IDS[2]],'quality_assessment')
    refresh()

def apply():
    G.active_check('mutation','inventory_disposition',[IDS[2]])
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    invpath=G.ROOT/'project-state/master-inventory.json';invpath.write_bytes(invpath.read_bytes().replace(b'\r\n',b'\n'))
    audit(['project-state/master-inventory.json']);refresh();queue()
    event('Only Volcano Park becomes approved for addition with exact official identity and complete scope/quality. Other three pending originals and all unrelated rows unchanged.',P+'updates.json',[IDS[2]],'inventory_disposition')
    save(P+'progress.json',dict(state='four_recovery_outcomes_and_inventory_accounting_complete_validation_pending',completed=IDS,approved_inventory_only=[IDS[2]],unresolved_originals=[IDS[0],IDS[1],IDS[3]],remaining=['full validation','authorized background integration and ref synchronization'],r2_delta_bytes=0,visitor_visible_delta=0))
    refresh();guard()

def queue():
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};prior=G.load(G.load(P+'starting-state.json')['queue_pointer']['artifact']);q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'};approved={i for i,r in rows.items() if r['status']=='approved for addition'}
    q.update(artifact_type='four_record_source_recovery_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['queue_pointer']['artifact'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),in_progress_publication=None)
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']=[i for i in prior[kind+'_pending_ids'] if i in pending];q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q['ungated_pending_ids']=sorted(ungated);q['ungated_pending_count']=len(ungated)
    q['unresolved_ungated_prerequisites']=[r for r in prior['unresolved_ungated_prerequisites'] if r['id'] in ungated];q['actionable_ungated_pending_ids']=[i for i in prior['actionable_ungated_pending_ids'] if i in ungated];q['genuinely_actionable_ungated_pending_count']=len(q['actionable_ungated_pending_ids'])
    q['background_family_groups']=[dict(f,candidate_ids=[i for i in f['candidate_ids'] if i in pending],candidate_count=len(set(f['candidate_ids'])&pending)) for f in prior['background_family_groups'] if set(f['candidate_ids'])&pending]
    q['newly_approved_backlog']=[dict(id=i,title=rows[i]['title'],reason='Complete historical original independently recovered and scoped/quality reviewed. No archival authorization in current task; separate R2 authorization/public-byte verification and owner-review publication required.',canonical_page=rows[i]['proposed_canonical_page'],evidence=P+'governance-review.json') for i in sorted(approved)]
    q['source_recovery']=dict(population=P+'population.json',research=P+'research-journal.json',blockers_cleared=[IDS[2]],preserved_pending=[IDS[0],IDS[1],IDS[3]])
    q['next_work_category']='Separately authorize archive-only preparation for recovered Volcano original, or pursue targeted custodian recovery for three missing originals. No publication population authorized.'
    assert set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|ungated==pending
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    remaining=sorted(r['id'] for r in rows.values() if r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed')
    checkpoint=G.load('project-state/checkpoint.json');checkpoint.update(recorded_at=inv['generated_at'],completed_item_range='Four existing source holds reviewed with new approaches; complete1980 Volcano original approved inventory-only, three holds preserved.',counts_by_status=inv['counts'],next_pending_id=remaining[0] if remaining else None,remaining_nonterminal=len(remaining),resume_command='Read CURRENT and four-record recovery receipt. No R2/visible publication or new population authorized. Next productive work: separate Volcano archive authorization, or narrowly identified study/report custodians for three missing originals.')
    save('project-state/checkpoint.json',checkpoint)
    audit([P+'queue.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json']);refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
    audit(['project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md'])

if __name__=='__main__':
    if sys.argv[1]=='get':get(sys.argv[2],sys.argv[3],sys.argv[4:] or IDS)
    else:globals()[sys.argv[1]]()
