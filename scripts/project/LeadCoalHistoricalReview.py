"""Bounded local Lead/Coal review; originals, family and publication boundaries preserved."""
import gzip, hashlib, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
import TaskGovernance as G
from PgsLegislativeResolution import save, audit

TASK='lead-coal-historical-review-2026-10-12'
P='project-state/governance/'+TASK+'/'
LOCAL=['research/staging/document-review/lead-coal-rest-in-red-7-28-2021-final-1.pdf','research/staging/document-review/NewVisionforLeadCoalAvenues.pdf']
IDS=['src-'+hashlib.sha256(p.lower().encode()).hexdigest()[:16] for p in LOCAL]
OPS=['document_review','family_review','quality_assessment','inventory_disposition','governance_implementation','background_integration']
def now():return datetime.now(timezone.utc).isoformat()
def freeze():
    base=G.git('rev-parse','HEAD'); inv=G.load('project-state/master-inventory.json')
    family=[r for r in inv['candidates'] if 'lead and coal' in r.get('title','').lower()]
    originals=[dict(candidate_id=i,path=p,size_bytes=(G.ROOT/p).stat().st_size,sha256=hashlib.sha256((G.ROOT/p).read_bytes()).hexdigest()) for i,p in zip(IDS,LOCAL)]
    outputs=['population.json','authority.json','starting-state.json','family-before.json','originals.json','implementation.json','findings.json','summary.md','proposed-entries.md','archive-readiness.json','receipt.json','validation.log','governance-accounting.json','integration.json','queue.json']
    paths=[P+x for x in outputs]+[P+f'contract-v{i}.json' for i in range(1,20)]+[P+f'source-{i}.{ext}' for i in range(1,61) for ext in ['json','gz','txt']]
    paths += [P+f'{kind}-{j}.{ext}' for kind in ['candidate','comparator'] for j in [1,2] for ext in ['json','txt','pdf.gz','renders.json','visual-review.json']]
    paths += [P+f'candidate-{j}-contact-{k}.png' for j in [1,2] for k in range(1,31)]
    paths += ['scripts/project/LeadCoalHistoricalReview.py','project-state/CURRENT.md',G.REGISTRY,G.ACTIVE_TASK,'project-state/governance/audit-2026-09-27/artifact-audit.json','project-state/master-inventory.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json','project-state/workflow-stage-lifecycle.json']
    G.write_once(P+'population.json',dict(task_id=TASK,baseline_commit=base,candidate_ids=IDS,families=['lead-coal-historical-review'],pages=['content/transportation/roadway-projects/studies.md'],operation_classes=OPS,artifact_paths=paths))
    G.write_once(P+'family-before.json',dict(comparator_ids=[r['id'] for r in family],records=family,scope='Read-only complete existing inventory family; no disposition or entry changes authorized.'))
    G.write_once(P+'originals.json',dict(originals=originals,preservation='Exact supplied local originals remain at owner paths; lossless gzip witnesses will be saved.'))
    G.write_once(P+'starting-state.json',dict(baseline_commit=base,checked_at=now(),branch=G.git('branch','--show-current'),content_tree=G.git('rev-parse',base+':content'),protected_sha256={p:G.file_hash(p) for p in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/checkpoint.json','project-state/ordinary-queue-current.json']},prior_active_task=G.load(G.ACTIVE_TASK)))
    instruction='Review exactly the two owner-supplied local PDFs, preserve/hash originals, render and inspect every page, establish metadata/status/provenance, investigate public sources, assess mission/quality/history, compare the unchanged 2022 RSA and 2025 final and complete existing family, check duplicates and prepare independent historical-entry recommendations and concise descriptions under Lead and Coal Avenues in studies.md. Save governed inventory assessments and archive readiness, run normal validation and integrate permissible background-only changes. No R2 upload, visitor-visible content modification or publication PR is authorized by this task. Preserve all existing Lead/Coal records and originals unless a necessary change is separately governed.'
    G.write_once(P+'authority.json',dict(authority='Explicit current user instruction, 2026-10-12',instruction=instruction,candidate_ids=IDS,local_paths=LOCAL))
    reg=G.load(G.REGISTRY)
    reg['entries'].append(dict(governance_id='owner-'+TASK,category='active owner decision',title='Bounded local Lead and Coal historical review',scope=dict(task_ids=[TASK],candidate_ids=IDS),authority='Explicit current user instruction',decision_date='2026-10-12',effective_date='2026-10-12',state='active',controlling_artifacts=[dict(path=P+'authority.json',sha256=G.file_hash(P+'authority.json'),binding_pointers=['/instruction'])],binding_requirement=instruction,required_actions=[instruction],prohibited_actions=['R2 upload, visible content changes and publication PR outside separate owner authorization.'],prohibited_operation_classes=['archive','external_mutation','visitor_visible_change','content_implementation'],constraints=[],settled_decisions=[],unresolved_gates=[],implementation_status='local review and background inventory preparation'))
    save(G.REGISTRY,reg)
    audit([P+x for x in ['starting-state.json','family-before.json','originals.json']])
    refresh()
def refresh():
    old=list((G.ROOT/P).glob('contract-v*.json'))
    if old:audit([x.relative_to(G.ROOT).as_posix() for x in old])
    n=max([int(x.stem.split('-v')[1]) for x in old],default=0)+1;path=P+f'contract-v{n}.json'
    versions=list((G.ROOT/P).glob('population-v*.json'))
    population_path=max(versions,key=lambda x:int(x.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if versions else P+'population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',population_path,'--output',path],check=True,stdout=subprocess.DEVNULL)
    c=G.load(path);assert not c['conflicts'],c['conflicts']
    plan=G.load(P+'implementation.json') if (G.ROOT/(P+'implementation.json')).exists() else dict(artifact_type='task_implementation_plan',actions=OPS,events=[],status='in_progress')
    subjects={}
    for r in c['resolved_rules']:
        for f in r.get('constraints',[]):subjects.setdefault(f['subject'],{})[f['field']]=f['equals']
    ev=P+('receipt.json' if (G.ROOT/(P+'receipt.json')).exists() else 'starting-state.json')
    plan.update(contract=path,contract_sha256=G.file_hash(path),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'],subjects=subjects,completion_evidence={gid:[dict(path=ev,sha256=G.file_hash(ev))] for gid in c['governance_ids']})
    save(P+'implementation.json',plan);save(G.ACTIVE_TASK,dict(population=population_path,contract=path,contract_sha256=G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
    print(path,len(c['governance_ids']),'rules; gates:',c['unresolved_gates'])
def event(summary,evidence,op='document_review',ids=IDS):
    p=G.load(P+'implementation.json');p['events'].append(dict(operation=op,candidate_ids=ids,action='implements',use_contract_record_rules=True,summary=summary,evidence=evidence));save(P+'implementation.json',p)
def guard():
    s=G.load(P+'starting-state.json');before=G.load(P+'family-before.json')['records'];inv=G.load('project-state/master-inventory.json');after={r['id']:r for r in inv['candidates']}
    assert all(after[r['id']]==r for r in before),'Existing family changed'
    assert not G.git('diff',s['baseline_commit'],'--name-only','--','content','layouts','static','assets','hugo.toml'),'Visible change'
    for j,r in enumerate(G.load(P+'originals.json')['originals'],1):
        witness=gzip.decompress((G.ROOT/(P+f'candidate-{j}.pdf.gz')).read_bytes())
        assert len(witness)==r['size_bytes'] and hashlib.sha256(witness).hexdigest()==r['sha256']
        if (G.ROOT/r['path']).exists():assert (G.ROOT/r['path']).read_bytes()==witness
    for p,h in s['protected_sha256'].items():
        if p in ['project-state/checkpoint.json','project-state/ordinary-queue-current.json']:continue
        assert G.file_hash(p)==h,p
    baseline=json.loads(G.git('show',s['baseline_commit']+':project-state/master-inventory.json'));old={r['id']:r for r in baseline['candidates']}
    assert set(after)-set(old)<=set(IDS) and set(old)<=set(after)
    assert all(after[i]==r for i,r in old.items()),'Unrelated or existing inventory changed'
    if set(IDS)<=set(after):
        from PublicationQuality import require_publication_quality
        for j,i in enumerate(IDS,1):
            r=after[i];assert r['status']=='approved for addition' and r['scope_assessment']['final_scope_decision']=='passes_both_gates'
            require_publication_quality(r)
            v=G.load(P+f'candidate-{j}-visual-review.json');assert v['visually_inspected_pages']==list(range(1,v['page_count']+1))
            original=G.load(P+'originals.json')['originals'][j-1];assert r['checksum_sha256']==original['sha256'] and r['size_bytes']==original['size_bytes']
            assert not any(r.get(x) for x in ['r2_url','r2_key','implementation_location','implementation_locations'])
        assert G.load(P+'source-2.json')['exact_supplied_original_match'] and G.load(P+'source-17.json')['exact_supplied_original_match']
        assert G.load(P+'source-18.json')['exact_supplied_original_match']
        assert len(after)==len(old)+2
    pop=G.load(G.load(G.ACTIVE_TASK)['population']);assert set(G.changed_paths(s['baseline_commit']))<=set(pop['artifact_paths'])
    print('PASS exact two additions only; existing inventory, originals, visible content and R2 unchanged')
if __name__=='__main__':globals()[sys.argv[1]]()
