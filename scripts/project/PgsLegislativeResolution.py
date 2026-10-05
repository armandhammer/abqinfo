"""Exactly three PGS legislative records; background only, historical evidence sealed."""
import copy, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, git as git_bytes

TASK='pgs-legislative-resolution-2026-10-05'
P='project-state/governance/'+TASK+'/'
BASE='483bde8f1e660614417d7f7ab5b4e7a484b4d8be'
IDS=['src-f7c7bd5b273def22','src-68582bc4fe41fb4f','src-fcbe6a7ebcf916a1']
def now(): return datetime.now(timezone.utc).isoformat()
def save(path,value):
    p=G.ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def audit(paths):
    r=G.load(G.REGISTRY);a=G.load(r['audit_artifact']);indexed={x['path']:x for x in a['artifacts']}
    for p in paths:
        indexed[p]=dict(path=p,sha256=G.file_hash(p),hash_kind='normalized-file-bytes',classification='historical evidence only / non-binding',governance_ids=[],rationale='Exact research, source retrieval, comparison, accounting or execution evidence; no independent authority.')
    a['artifacts']=sorted(indexed.values(),key=lambda x:x['path']);save(r['audit_artifact'],a)
    r['audit_sha256']=G.file_hash(r['audit_artifact']);save(G.REGISTRY,r)
def bind(path,gid,requirement,scope,category='active owner decision'):
    r=G.load(G.REGISTRY);assert not any(x['governance_id']==gid for x in r['entries'])
    r['entries'].append(dict(governance_id=gid,category=category,title=gid,scope=scope,authority='Explicit current user three-record PGS legislative resolution instruction',decision_date='2026-10-05',effective_date='2026-10-05',state='active',controlling_artifacts=[dict(path=path,sha256=G.file_hash(path),binding_pointers=['/'])],binding_requirement=requirement,required_actions=[requirement],prohibited_actions=[],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='bounded background legislative research'))
    save(G.REGISTRY,r)
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:audit([p.relative_to(G.ROOT).as_posix() for p in old])
    n=max([int(p.stem.split('-v')[1]) for p in old],default=0)+1;path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=G.load(P+'population.json')['operation_classes'],events=[],status='research_in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects)
    for e in plan['events']:e['use_contract_record_rules']=True
    if (G.ROOT/(P+'receipt.json')).exists():plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    save(P+'implementation.json',plan)
    save(G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress',supersession_proposals_path=P+('decisions.json' if (G.ROOT/(P+'decisions.json')).exists() else 'supersession.json')))
    print(path,len(c['governance_ids']),'rules; gates:',c['unresolved_gates'])
def freeze():
    assert G.git('rev-parse','HEAD')==BASE
    inv=G.load('project-state/master-inventory.json');rows={x['id']:x for x in inv['candidates']}
    assert all(rows[i]['status']=='pending review' for i in IDS)
    outputs=['population.json','authority.json','starting-state.json','prior-records.json','implementation.json','supersession.json','progress.json','receipt.json','accounting.json','summary.md','owner-decisions-needed.json','validation.log','queue.json','remote-final.json','decisions.json','updates.json','research-journal.json','comparison.json','integration-intent.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,101)]
    paths += [P+f'evidence-{i}.{ext}' for i in range(1,201) for ext in ['json','txt','png']]
    paths += ['scripts/project/PgsLegislativeResolution.py','scripts/project/Research-PgsLegislation.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md',G.REGISTRY,G.registry()['audit_artifact'],G.ACTIVE_TASK,'project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=BASE,candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration'],artifact_paths=paths))
    G.write_once(P+'prior-records.json',dict(records=[rows[i] for i in IDS]))
    priorq=G.load(G.load('project-state/ordinary-queue-current.json')['artifact'])
    G.write_once(P+'starting-state.json',dict(checked_at_utc=now(),refs={x:G.git('rev-parse',x) for x in ['HEAD','origin/main','origin/chatgpt/planning-snapshot']},queue_counts={s:sum(x['status']==s for x in inv['candidates']) for s in ['approved for addition','pending review']},source_blocked_count=priorq['source_or_structural_blocked_pending_count'],source_queue=G.load('project-state/ordinary-queue-current.json')['artifact'],r2_inventory_sha256=G.file_hash('project-state/r2-inventory.json'),r2_policy_sha256=G.file_hash('project-state/r2-storage-policy.json')))
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',P+'population.json','--output',P+'contract-v1.json'],check=True,stdout=subprocess.DEVNULL)
    c=G.load(P+'contract-v1.json');G.freshness(c,G.load(P+'population.json'),G.registry(),G.file_hash(G.REGISTRY));assert not c['conflicts']
    instruction='Resolve exactly src-f7c7bd5b273def22 F/S O-02-39 (2), src-68582bc4fe41fb4f O-03-132 and src-fcbe6a7ebcf916a1 O-04-9 together using existing durable PGS research and current authoritative Council/Legistar final files, variants, actions, amendments/substitutes, enactment numbers and required exhibits/incorporated plans. Do not reopen settled PGS chapters/package. Bill metadata alone cannot prove incomplete held PDF enacted completeness; reject MatterTextMatterId mismatches. Apply background inventory dispositions only on conclusive evidence; preserve historical originals/provenance. No visitor-visible or R2 mutation. Regenerate accounting, run full validation/governance/sealed-history/Hugo/rendered and diff checks; integrate clean background work into main and synchronize planning-snapshot. No other population. Current instruction authorizes resolution of factual holds, not arbitrary editorial supersession.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction',candidate_ids=IDS,instruction=instruction))
    bind(P+'authority.json','owner-'+TASK,instruction,{'candidate_ids':IDS,'task_ids':[TASK]})
    save(P+'supersession.json',dict(proposals={}))
    bind(P+'supersession.json','supersessions-'+TASK,'Only conclusive current evidence may resolve the exact three factual enacted-package holds; no settled PGS chapter/package decisions are replaced. Preserve all historical evidence.',{'task_ids':[TASK]})
    save(P+'progress.json',dict(state='population_frozen_governed_research_ready',completed=[],remaining=IDS,r2_mutations=0,visitor_visible_mutations=0))
    audit([P+'starting-state.json',P+'prior-records.json',P+'progress.json']);refresh()
    print(G.active_check('mutation','document_review',IDS))
def guard():
    stage=StageSnapshot(TASK);start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(BASE,G.git('rev-parse',BASE+':content'))
    for p,k in [('project-state/r2-inventory.json','r2_inventory_sha256'),('project-state/r2-storage-policy.json','r2_policy_sha256')]:
        import hashlib
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest()==start[k],p
    baseline=json.loads(git_bytes('show',BASE+':project-state/master-inventory.json'));a={r['id']:r for r in baseline['candidates']};b={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert a.keys()==b.keys() and {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes'],'Historical notes lost: '+i
        for field in ['source_url','local_path','sha256','file_size_bytes','r2_key','r2_url']:
            if field in a[i]:assert b[i].get(field)==a[i][field],(i,field)
        for field in ['direct_file_url','checksum_sha256','size_bytes']:
            assert b[i].get(field)==a[i].get(field),(i,field)
    changes=set(git_bytes('diff',BASE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(BASE))
    assert changes<=set(stage.load_json(P+'population.json')['artifact_paths']),changes-set(stage.load_json(P+'population.json')['artifact_paths'])
    if (G.ROOT/(P+'decisions.json')).exists():
        from PublicationQuality import require_publication_quality
        d=stage.load_json(P+'decisions.json');assert {r['id'] for r in d['records']}==set(IDS)
        for r in d['records']:
            assert b[r['id']]['status']=='approved for addition'
            require_publication_quality(b[r['id']])
            text=G.load(P+f"evidence-{r['final']}.json")['response_json']
            assert text['MatterTextId']==r['text'] and text['MatterTextMatterId']==r['matter'] and text['MatterTextVersion']==r['version']
        comparison=G.load(P+'comparison.json')
        assert all(r['held_prose_equal'] and r['word_prose_equal'] and all(e['held_numeric_sequence_equal'] and e['word_numeric_sequence_equal'] and e['held_labels_equal'] and e['word_labels_equal'] for e in r['exhibits']) for r in comparison['substantive_comparisons'])
    if (G.ROOT/(P+'queue.json')).exists():
        q=stage.load_json(P+'queue.json');pending={i for i,r in b.items() if r['status']=='pending review'};approved={i for i,r in b.items() if r['status']=='approved for addition'}
        assert set(q['pending_ids'])==pending and {r['id'] for r in q['newly_approved_backlog']}==approved==set(IDS)
        assert (len(pending),q['gated_pending_count'],q['source_or_structural_blocked_pending_count'])==(348,321,27)
    print('Exact three-record PGS / historical originals / zero visitor-visible / zero R2 guard passed')
def research_checkpoint():
    c=G.load(P+'comparison.json')
    assert all(r['held_prose_equal'] and r['word_prose_equal'] and all(e['held_numeric_sequence_equal'] and e['word_numeric_sequence_equal'] and e['held_labels_equal'] and e['word_labels_equal'] for e in r['exhibits']) for r in c['substantive_comparisons'])
    stages=G.load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id']=='pr211-postmerge-closeout-2026-10-05'
    stages['stages'][-1]['end_commit']=BASE
    stages['stages'].append(dict(id=TASK,baseline_commit=BASE,regression_scripts=['scripts/project/PgsLegislativeResolution.py'],exact_delta_guard=dict(module='PgsLegislativeResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    runner=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=runner.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/PgsLegislativeResolution.py" guard\nif ($LASTEXITCODE) { throw \'Three-record PGS legislative background boundary failed.\' }\nSet-StrictMode -Version Latest',1);runner.write_text(t,encoding='utf8',newline='\n')
    r=G.load(G.REGISTRY)
    for row in r['entries']:
        for a in row['controlling_artifacts']:
            if a['path']=='scripts/project/Invoke-ProjectValidation.ps1':a['sha256']=G.file_hash(a['path'])
    save(G.REGISTRY,r)
    journal=dict(recorded_at=now(),state='research_complete_dispositions_not_yet_applied',population=IDS,existing_evidence_used=['project-state/discovery/planned-growth-strategy-cluster-research-2026-09-11.json','project-state/discovery/planned-growth-strategy-decision-2026-09-19.json','project-state/discovery/background-followup-2026-09-26/decisions.json','project-state/discovery/background-followup-2026-09-26/comparisons.json','project-state/discovery/human-review-reassessment-2026-09-26/family-evidence.json','project-state/discovery/codex-human-review-followup-queue.json'],critical_discovery='The /versions endpoint maps Key to MatterTextId and Value to MatterTextVersion. Old /texts/1 etc selected unrelated global text IDs. Correct IDs 2191/3192/3419 were checked against MatterTextMatterId 1463/2609/2802. Complete final operative clauses, headers, row labels and numeric exhibit sequences agree with held PDFs and exact listed Word attachments.',accepted_final_texts=[dict(matter_id=1463,text_id=2191,version='4',enactment='O-2002-034'),dict(matter_id=2609,text_id=3192,version='2',enactment='O-2003-047'),dict(matter_id=2802,text_id=3419,version='2',enactment='O-2004-007')],comparison=P+'comparison.json',visual_inspection='All 14/5/5 held PDF pages and 16/6/6 prior Word render pages inspected through contact sheets. Blank converter pages in the 6-page Word renders are pagination, not omitted exhibits. Both later original PDFs contain three legible forecast tables. Referenced R-02-111 Exhibit A water/wastewater/hydrology service tier and street traffic shed maps are present on pages30-31 of the separate official 32-page resolution; page32 is blank. No need to append the PGS study to these self-contained enactments.',invalid_routes_rejected=['/texts/{version} with mismatched MatterTextMatterId, retained only in historical evidence','/texts collection GET405','LegislationDetail legacy/API IDs return Invalid parameters!','ViewReport API matter ID1463 produces empty bill header; no legislative evidence'],next_action='Register conclusive three-record dispositions and narrow factual-hold resolution; preserve all settled study work.',r2_mutations=0,visitor_visible_mutations=0)
    save(P+'research-journal.json',journal)
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='document_review',candidate_ids=IDS,action='research_unsettled',use_contract_record_rules=True,summary=journal['critical_discovery'],evidence=P+'research-journal.json'));save(P+'implementation.json',plan)
    save(P+'progress.json',dict(state=journal['state'],completed=['complete_source_and_version_comparison'],remaining=IDS,r2_mutations=0,visitor_visible_mutations=0))
    audit([p.relative_to(G.ROOT).as_posix() for p in (G.ROOT/P).glob('*') if p.is_file() and p.name not in ['authority.json','supersession.json','implementation.json'] and not p.name.startswith('contract-v')])
    refresh();G.active_check('mutation','governance_implementation',IDS);guard()
def decisions():
    G.active_check('mutation','quality_assessment',IDS)
    before={r['id']:r for r in G.load(P+'prior-records.json')['records']}
    evidence=[P+'comparison.json',P+'research-journal.json']
    details=[
        dict(id=IDS[0],bill='F/S O-02-39 (2)',matter=1463,version='4',text=2191,enactment='O-2002-034',passed='2002-09-23',signed='2002-09-25',published='2002-10-01',pages=14,words=4579,held=30,word=33,final=54,
             value='Establishes the City growth-management framework, advisory task force, impact-fee principles, infrastructure/CIP sequencing, no-net-expense development policy and intergovernmental coordination.',
             finality='Final legislative version4, text2191, is the second floor substitute F/S O-02-39(2) after September23 successful amendments. Council passed version3 as substituted/as amended; final4 contains the resulting changes and agrees with the expressly labelled Final Version attachment292.doc and the held City PDF. September23 substitute and amendment motions1,2,6,7 passed; motions3,4,5 failed. Final3-to4 changes include fiscal consequences to impact, three to five task-force nominees, and recognition of existing private water service companies. The attachment version0 field is a delivery selector, not the enacted version.',
             package='Complete 14-page final ordinance; no own attached exhibit is absent. Final-file Word reflows to16 pages but has the same operative clauses. The 2001 PGS study is background analysis, not blanket enacted law: only policies specifically adopted have binding force. Section6(B)(2) references Part2 Chapters1-3 and preferences1.3.1-1.3.4; use the already-settled complete PGS family as context. R-02-111, enacted R-2002-112, supplies companion implementation policies and Exhibit A water/wastewater/hydrology tier and street traffic-shed maps on pages30-31 of its separate32-page City original. This contextual resolution is evidence only, not an added task candidate. R-02-112 is recorded Died on Expiration with no enactment number; its conditional as-adopted reference cannot be treated as enacted plan amendments.'),
        dict(id=IDS[1],bill='O-03-132',matter=2609,version='2',text=3192,enactment='O-2003-047',passed='2003-10-20',signed='2003-11-03',published='2003-11-03',pages=5,words=1127,held=31,word=34,final=60,
             value='Adopts the City/County population, housing and employment forecast tables used for growth-related capital planning and the basis of development-fee land-use assumptions.',
             finality='Final legislative version2, text3192. Council passed version1 as amended on October20 after successful Cadigan amendments1/2 (meeting exhibits35/36); final2 was signed and published November3. Original1 population Exhibit1 says To be provided by MRCOG; final2 replaces it with the complete population table and adds the sentence connecting the Infrastructure and Growth Plan to Land Use Assumptions under the New Mexico Development Fees Act. Final attachment1354.doc, City PDF and correctly keyed final text agree in all clauses and every table cell.',
             package='Complete five-page enacted delivery: two pages of ordinance plus required Exhibit1 population, Exhibit2 housing and Exhibit3 employment, each with16 subareas and Grand Total, base2000 and both Vacant Land/Centers & Corridors scenarios for2010/2025. All three incorporated tables are present. The six-page Word inspection has a reflow blank page and the same three tables. No missing MRCOG population exhibit remains in this final delivery. This implements the 2002 PGS framework, rather than republishing the settled research chapters.'),
        dict(id=IDS[2],bill='O-04-9',matter=2802,version='2',text=3419,enactment='O-2004-007',passed='2004-02-02',signed='2004-02-13',published='2004-02-17',pages=5,words=1113,held=32,word=35,final=62,
             value='Adopts the particular land-use projections used to calculate growth capital needs and development impact fees, with a statutory five-year update requirement.',
             finality='Final legislative version2, text3419. Introduced January5, postponed January21, passed unamended February2 (meeting exhibit19), sent to Mayor as version2 February6, signed February13 and published February17. Original1-to-final2 changes fill the sponsor and correct duplicate section numbering; there is no recorded floor amendment. Final attachment1589.doc, City PDF and final text agree in all clauses and every exhibit table cell.',
             package='Complete five-page final ordinance with required Exhibits1-3 for population, housing and employment:16 subareas plus Grand Total and both growth scenarios. Insert Exhibits1,2and3 is a drafting instruction retained in the prose; the actual tables are present on pages3-5. These2004 forecasts are related to, but not identical to, the2003 Infrastructure and Growth Plan: e.g. total2025 population729363/729719 vs729763/729731; total housing328790/328800 vs328795/328805; employment466594/466582 vs466593/466582. Do not collapse these two ordinances or substitute the2003 exhibits. The2012/2013 impact-fee/CCIP instruments are later family history, outside this task; neither is a replacement for the2004 original.')]
    records=[];updates=[]
    for d in details:
        scope=dict(assessed_at='2026-10-05',geographic_institutional_scope='City of Albuquerque growth-management legislation and its Albuquerque/Bernalillo urban-area implementation.',specific_albuquerque_connection=d['value'],abqinfo_public_information_value='Records a consequential adopted local land-use, infrastructure, capital-financing or impact-fee decision and its exact legal/forecast content.',general_context_exclusion_test='This is operative Albuquerque legislation with identifiable local implementation and adopted numerical/policy content; it is not statewide applicability, generic context, transactional paperwork or a report merely hosted by the City.',final_scope_decision='passes_both_gates',substantive_rationale=d['value']+' Its complete final legislative delivery materially explains City development policy beyond provenance or institutional jurisdiction.')
        quality=dict(document_function='Complete historical enacted local growth-management ordinance with its own required exhibits.',substantive_content=d['value']+' '+d['package'],durable_public_usefulness='Supports historical understanding of what Albuquerque actually adopted, rather than mistaking the larger PGS study for law or assuming one forecast delivery replaces another.',information_density=f"{d['pages']} original pages / {d['words']} extractable words; dense operative clauses and, for the later ordinances, three substantive numerical tables.",unique_information=d['value']+' This legislative act has a distinct adoption purpose, date and enacted content within the family.',rationale='Each complete ordinance has independently meaningful legal and infrastructure information. Retain one exact official PDF per act, with its own incorporated tables and linked family context, rather than create duplicate Word entries or repeat already-published PGS report chapters.',standalone_public_value='high',publication_form='standalone',series_relationship='component',aggregation_decision=dict(form='standalone',rationale='These are three complete separate legislative acts, not serial administrative fragments. Their distinct operative powers and forecast tables merit individually identified original entries within one coherent historical PGS legislative grouping.',standalone_unique_value=d['value'],evidence=evidence),reviewed_document_content=True,visual_inspection_completed=True,visual_inspection=f"All held pages and bit-verified Word-render pages visually inspected in evidence-{d['held']}.png / evidence-{d['word']}.png; dense exhibit rows, headings and page ends reviewed. No clipped or missing substantive pages.",page_count=d['pages'],extracted_word_count=d['words'],measured_page_count=d['pages'],measured_word_count=d['words'],intended_publication_form='One historical official PDF per enacted ordinance, together in the existing Citywide Growth Strategy family context; no separate Word/attachment entry.',currentness_review_required=True,currentness_review=dict(status='historical_status_uncertain',authoritative_sources=[P+f"evidence-{d['final']}.json",P+'evidence-19.json'],finding='Finality is established for this dated enactment. This task does not certify all intervening legal amendments or that2000/2010/2025 forecasts represent current law or present-day conditions.',publication_qualification='Label as historical legislation with its adoption/enactment identity. Present enacted original, not a current consolidated code or current forecast.'))
        conclusion='Conclusive complete final enacted delivery; blank printed enactment field is not a missing-text blocker after verified correct-matter final-text comparison. Approve inventory-only for one historical original per act; exact R2 archival/public-byte verification and a separately authorized manual-review content PR remain future publication prerequisites.'
        records.append(dict(**d,scope_assessment=scope,quality_assessment=quality,held_record_classification='complete final legislative delivery; uncertified bill-format official original',disposition='approved for addition',binding_requirement=conclusion,owner_decision_required=False,evidence=evidence+[P+f"evidence-{d['final']}.json"]))
        updates.append(dict(id=d['id'],changes=dict(status='approved for addition',file_type='PDF',date=d['passed'],scope_assessment=scope,quality_assessment=quality,publication_quality_decision=dict(decision='passes',finding_id=TASK+':'+d['id'],assessment=quality,evidence=evidence),provenance_status=f"Exact official City PDF and listed Legistar Word bytes reverified; correct-matter final text{d['text']} version{d['version']} confirms all clauses and exhibits; {d['enactment']}.",proposed_canonical_page='content/development-land-use/area-sector-plans.md',review_reason=None,exclusion_reason=None,validation_status='Governed enacted-package/source-quality review complete; inventory-only approval, no R2 archival or visitor-visible implementation. '+P+'decisions.json',processing_notes=before[d['id']]['processing_notes']+['2026-10-05 PGS three-ordinance resolution: '+d['finality']+' '+d['package']+' '+conclusion+' Evidence: '+P+'decisions.json'])))
    registry=G.load(G.REGISTRY);old=next(r for r in registry['entries'] if r['governance_id']=='decision-planned-growth-strategy-decision-2026-09-19-277e4100')
    replacement=old['binding_requirement']+' Explicit current-user, conclusive-source exception for exactly '+', '.join(IDS)+': their enacted-finality holds are resolved and replaced by the inventory-only approvals in '+P+'decisions.json. Preserve the historical holds unchanged as evidence and every other settled chapter/package, canonical and family decision. No R2 or visitor-visible action is authorized.'
    new_id=old['governance_id']+'-three-enacted-holds-resolved-2026-10-05'
    proposals={old['governance_id']:dict(authorized=True,existing_governance_id=old['governance_id'],current_decision=old['binding_requirement'],controlling_evidence=copy.deepcopy(old['controlling_artifacts']),new_evidence=P+'comparison.json',proposed_replacement=replacement,consequences='Only the three factual enacted-package prerequisites become resolved eligible inventory records; all13 settled research deliveries and all historical originals/decisions remain unchanged.',authorization_artifact=P+'authority.json')}
    G.write_once(P+'decisions.json',dict(artifact_type='pgs_three_record_enacted_package_resolution',authority=P+'authority.json',proposals=proposals,records=records,family_relationship='Three independently substantive legal instruments implement the already-settled PGS study family. Preserve one complete City PDF per act and their differing forecast tables; companion R-02-111 with Exhibit A maps provides context, not a fourth task candidate.',publication_gate='No active publication population. No R2/archive mutation or visitor-visible change authorized; future archive and visible PR require their own authorization.'))
    G.write_once(P+'updates.json',dict(approved_updates=updates))
    # Conclusive findings and explicit current authority replace only the factual hold.
    new=copy.deepcopy(old);new.update(governance_id=new_id,binding_requirement=replacement,authority='Explicit current user conclusive background-disposition instruction; preserved prior family authority',decision_date='2026-10-05',effective_date='2026-10-05')
    new['controlling_artifacts'] += [dict(path=P+'decisions.json',sha256=G.file_hash(P+'decisions.json'),binding_pointers=['/']),dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/'])]
    old.update(state='superseded',superseded_by=new_id,supersession_evidence=P+'decisions.json');registry['entries'].append(new);save(G.REGISTRY,registry)
    bind(P+'decisions.json','decision-'+TASK,'Apply exactly the three conclusive inventory-only approvals, complete-package relationships and source/finality resolutions recorded here. Preserve all other inventory rows, settled PGS study decisions and original evidence; no R2/visitor-visible action.',{'candidate_ids':IDS,'task_ids':[TASK]},'active family decision')
    audit([P+'updates.json']);refresh();apply_records()
def apply_records():
    from PublicationQuality import require_publication_quality
    prior={r['id']:r for r in G.load(P+'prior-records.json')['records']}
    for u in G.load(P+'updates.json')['approved_updates']:require_publication_quality({**prior[u['id']],**u['changes']})
    G.active_check('mutation','inventory_disposition',IDS)
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'updates.json'],check=True)
    inventory=G.ROOT/'project-state/master-inventory.json'
    inventory.write_bytes(inventory.read_bytes().replace(b'\r\n',b'\n'))
    audit(['project-state/master-inventory.json']);refresh();queue()
    plan=G.load(P+'implementation.json');plan['events'].append(dict(operation='inventory_disposition',candidate_ids=IDS,action='implements',use_contract_record_rules=True,summary='Exactly three conclusive complete enacted-delivery approvals; historical provenance and study family preserved.',evidence=P+'decisions.json'));save(P+'implementation.json',plan)
    save(P+'progress.json',dict(state='three_records_resolved_validation_pending',completed=IDS,remaining=[],r2_mutations=0,visitor_visible_mutations=0,next_population_authorized=False))
    audit([P+'progress.json',P+'queue.json','project-state/checkpoint.json']);refresh();guard()
def queue():
    inv=G.load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};prior=G.load(G.load(P+'starting-state.json')['source_queue']);q=copy.deepcopy(prior)
    pending={i for i,r in rows.items() if r['status']=='pending review'};approved={i for i,r in rows.items() if r['status']=='approved for addition'}
    q.update(artifact_type='pgs_legislative_resolution_queue',recorded_at=inv['generated_at'],source_queue_artifact=G.load(P+'starting-state.json')['source_queue'],inventory_generated_at=inv['generated_at'],inventory_sha256=G.file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending),approved_count=len(approved),in_progress_publication=None)
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending};q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids']);q['ungated_pending_ids']=sorted(ungated);q['ungated_pending_count']=len(ungated)
    q['unresolved_ungated_prerequisites']=[r for r in prior['unresolved_ungated_prerequisites'] if r['id'] in ungated];q['actionable_ungated_pending_ids']=[i for i in prior['actionable_ungated_pending_ids'] if i in ungated];q['genuinely_actionable_ungated_pending_count']=len(q['actionable_ungated_pending_ids'])
    q['background_family_groups']=[dict(f,candidate_ids=[i for i in f['candidate_ids'] if i in pending],candidate_count=len(set(f['candidate_ids'])&pending)) for f in prior['background_family_groups'] if set(f['candidate_ids'])&pending]
    q['newly_approved_backlog']=[dict(id=i,title=rows[i]['title'],reason='Complete final historical enacted ordinance and required exhibits proved; separately authorized archival/public-byte verification and reviewed content PR remain future prerequisites.',canonical_page=rows[i]['proposed_canonical_page'],evidence=P+'decisions.json') for i in sorted(approved)]
    q['pgs_resolution']=dict(population=P+'population.json',decisions=P+'decisions.json',blockers_cleared=IDS)
    assert set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|ungated==pending
    save(P+'queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=TASK))
    remaining_statuses={'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'}
    remaining=sorted(r['id'] for r in rows.values() if r['status'] in remaining_statuses or (r['status']=='implemented' and r.get('validation_status')!='passed'))
    checkpoint=G.load('project-state/checkpoint.json');checkpoint.update(recorded_at=inv['generated_at'],completed_item_range='Exactly three PGS enacted legislative deliveries resolved; complete originals approved inventory-only; no archive/publication task.',counts_by_status=inv['counts'],next_pending_id=remaining[0] if remaining else None,remaining_nonterminal=len(remaining),resume_command='Read CURRENT and the PGS legislative resolution receipt. This three-record task is complete after validation/integration; no follow-on population is authorized. Three archival/publication prerequisites remain future work, not an owner decision in this task.')
    save('project-state/checkpoint.json',checkpoint)
    audit([P+'queue.json','project-state/checkpoint.json']);refresh()
    subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
def prepare_validation():
    guard();G.active_check('mutation','background_integration',IDS)
    q=G.load(P+'queue.json')
    accounting=dict(recorded_at=now(),population=IDS,completed=IDS,remaining=[],blockers_cleared=3,approved=q['approved_count'],pending=q['pending_review_count'],source_or_structural_blocked=q['source_or_structural_blocked_pending_count'],governance_gated=q['gated_pending_count'],owner_pending=0,active_publication_population=None,r2_objects_added=0,r2_bytes_added=0,r2_deleted_or_overwritten=0,visitor_visible_paths_changed=[])
    save(P+'accounting.json',accounting)
    save(P+'owner-decisions-needed.json',dict(record_count=0,records=[],rationale='All three enacted-finality questions were factual and are conclusively resolved. Future archive/publication authorization is a separate stage, not a current editorial ambiguity.'))
    save(P+'receipt.json',dict(artifact_type='pgs_legislative_resolution_receipt',recorded_at=now(),baseline_commit=BASE,population=P+'population.json',authority=P+'authority.json',research_checkpoint_commit=G.git('rev-parse','HEAD'),research=P+'research-journal.json',comparison=P+'comparison.json',dispositions=P+'decisions.json',accounting=P+'accounting.json',validation_log=P+'validation.log',validation_result=P+'evidence-73.json',state='enacted_finality_dispositions_and_accounting_complete',r2_delta_bytes=0,r2_delta_objects=0,visitor_visible_delta=0,owner_pending=0,settled_study_population_unchanged=True,followon_population_started=False))
    text='# Current project state\n\nExactly three PGS legislative blockers resolved together: O-02-39 / O-2002-034 final v4, O-03-132 / O-2003-047 final v2, O-04-9 / O-2004-007 final v2. Correctly keyed Legistar final text, exact Word/PDF clauses and all required forecast exhibits agree. Three complete historical originals approved inventory-only; settled PGS study/chapter work preserved. Queue: 3 approved / 348 pending (321 governance-gated / 27 source-structural blocked). No active publication population or owner decision. Zero visitor-visible/R2 delta. Validation/integration evidence is in the receipt and its linked result; no follow-on population authorized.\n\n[PGS receipt](governance/'+TASK+'/receipt.json) · [Finality and packages](governance/'+TASK+'/decisions.json) · [Active task](governance/active-task.json) · [Owner correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [Closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n'
    (G.ROOT/'project-state/CURRENT.md').write_text(text,encoding='utf8',newline='\n')
    report='# PGS legislative resolution\n\nAll three held City PDFs are complete final legislative deliveries. Their printed blank enactment fields remain unchanged; conclusive correctly keyed Legistar final text and action history establish their enacted identities. Each ordinance is independently substantive and eligible as one dated historical original in the existing PGS family, pending separately authorized archive/publication work.\n\n| Record | Final identity | Complete delivery | Disposition |\n|---|---|---|---|\n'
    for r in G.load(P+'decisions.json')['records']:report+=f"| {r['id']} / {r['bill']} | {r['enactment']} / v{r['version']} / text{r['text']} | {r['pages']} pages; "+('no own exhibit' if r['pages']==14 else 'Exhibits1-3 included')+' | approved, inventory-only |\n'
    report+='\nThe2003 and2004 table sets differ and are retained separately. R-02-111 / R-2002-112 contains companion service-tier maps; R-02-112 has no enactment. No other family record was reassessed or changed. Historical study publication remains unchanged.\n\nAccounting:3 approved /348 pending /27 source-structural blocked /321 governance-gated. Three blockers cleared. No genuine owner choice, active publication, R2 object/byte mutation or visitor-visible delta. See validation.log and evidence-73.json for full validation and integration-intent.json for ref synchronization evidence.\n'
    (G.ROOT/(P+'summary.md')).write_text(report,encoding='utf8',newline='\n')
    audit([P+'accounting.json',P+'owner-decisions-needed.json',P+'receipt.json',P+'summary.md','project-state/CURRENT.md','project-state/checkpoint.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md'])
    refresh();print(G.active_check('final')['task_id']);guard()
if __name__=='__main__':
    {'freeze':freeze,'refresh':refresh,'guard':guard,'research-checkpoint':research_checkpoint,'decisions':decisions,'apply':apply_records,'queue':queue,'prepare-validation':prepare_validation}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
