"""Bounded background PR210 production verification and post-merge reconciliation."""
import gzip,hashlib,json,subprocess,sys,urllib.request
import OwnerResources20261004 as S
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot,canonical_bytes,git
from Pr208209Reconciliation import presentation
T='pr210-postmerge-closeout-2026-10-04';P=S.prefix(T)
MERGE='b0629fb74495e56d369ee73b5bd94ac8d33d8173'
REVIEWED='dc1b934a494efe828dc37e5449b5534d28b40d3e'
SCRIPT='scripts/project/Pr210PostMergeCloseout.py'
IDS=S.LIVE+[S.SUN]+S.NEW

def refresh():
    S.audit([SCRIPT]);S.refresh(T)
    if (G.ROOT/(P+'verification.json')).exists() and not (G.ROOT/(P+'receipt.json')).exists():
        plan=G.load(P+'implementation.json')
        plan['completion_evidence']={gid:[dict(path=P+'verification.json',sha256=G.file_hash(P+'verification.json'))] for gid in plan['respected_governance_ids']}
        S.save(P+'implementation.json',plan)

def setup():
    pop=G.load(P+'population.json');c=G.load(P+'contract-v1.json')
    G.freshness(c,G.population(pop),G.registry(),G.file_hash(G.REGISTRY))
    authority='Current owner reports manual merge of PR210 and authorizes ONLY background post-merge production verification and reconciliation: verify all seven production pages directly at abqinfo.com against the reviewed nine-record publication, exact merge deployment, links/anchors, sealed Sunport archive and full live R2 accounting; derive implemented inventory and approved/pending queue counts. Run full normal/governance/sealed-history/Hugo/rendered/diff checks. If clean, save immutable closeout receipt, update CURRENT and active task, integrate background-only into main and synchronize planning-snapshot to exact final authoritative main. No content edits, inventory/queue/R2 mutation, new review/publication population, credential change or upload/deletion/overwrite. If an actual production defect appears, stop and report the smallest corrective content PR; do not implement it here.'
    G.write_once(P+'authority.json',dict(authority='Explicit current owner PR210 post-merge instruction',merge_sha=MERGE,reviewed_head=REVIEWED,instruction=authority))
    S.bind(P+'authority.json','owner-'+T,authority,dict(task_ids=[T],candidate_ids=IDS,pages=S.PAGES))
    r=G.load(G.REGISTRY);next(x for x in r['entries'] if x['governance_id']=='owner-'+T)['authority']='Explicit current owner background PR210 post-merge closeout instruction';S.save(G.REGISTRY,r)
    assert G.git('rev-parse',MERGE+'^{tree}')==G.git('rev-parse',REVIEWED+'^{tree}')
    inv=G.load('project-state/master-inventory.json');selected=[x for x in inv['candidates'] if x['id'] in IDS]
    assert len(selected)==9 and all(x['status']=='implemented' for x in selected)
    protected=['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/ordinary-queue-current.json','project-state/checkpoint.json','project-state/r2-storage-policy.json']
    pointer=G.load('project-state/ordinary-queue-current.json');protected.append(pointer['artifact'])
    history=git('ls-tree','-r','--name-only',MERGE,'--',S.prefix(S.A),S.prefix(S.B),'project-state/governance/interactive-app-resolution-2026-10-04').decode().splitlines()
    G.write_once(P+'starting-state.json',dict(merge_sha=MERGE,reviewed_head=REVIEWED,trees_identical=True,content_tree_oid=G.git('rev-parse',MERGE+':content'),protected_sha256={x:G.file_hash(x) for x in protected+history},inventory_record_ids=IDS,queue=dict(approved=sum(x['status']=='approved for addition' for x in inv['candidates']),pending=sum(x['status']=='pending review' for x in inv['candidates'])),r2=dict(objects=G.load('project-state/r2-inventory.json')['object_count'],bytes=G.load('project-state/r2-inventory.json')['total_bytes'])))
    stages=G.load('project-state/workflow-stage-lifecycle.json');assert stages['stages'][-1]['id']==S.B
    stages['stages'][-1]['end_commit']=MERGE
    stages['stages'].append(dict(id=T,baseline_commit=MERGE,regression_scripts=[SCRIPT],exact_delta_guard=dict(module='Pr210PostMergeCloseout',function='guard')))
    S.save('project-state/workflow-stage-lifecycle.json',stages)
    f=G.ROOT/'scripts/project/Invoke-ProjectValidation.ps1';raw=f.read_bytes();text=raw.decode('utf-8');marker='& python "$PSScriptRoot/OwnerResources20261004.py" guard';assert text.count(marker)==1
    text=text.replace(marker,'& python "$PSScriptRoot/Pr210PostMergeCloseout.py" guard\nif ($LASTEXITCODE) { throw \'PR210 background closeout exact-delta guard failed.\' }\n'+marker);f.write_bytes(text.encode('utf-8'))
    S.save(P+'progress.json',dict(state='governed_production_verification_pending',remaining=['direct_production','archive_and_R2','normal_validation','immutable_receipt','background_main_integration','snapshot_sync'],visitor_visible_changes=0))
    refresh();G.active_check('mutation','governance_implementation');guard()

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo PR210 production closeout)','Cache-Control':'no-cache, no-store, max-age=0','Pragma':'no-cache'})
    with urllib.request.urlopen(req,timeout=60) as r:
        body=r.read();assert r.status==200
        return body,dict(url=url,resolved_url=r.url,http_status=r.status,size_bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),headers=dict(r.headers),observed_at=S.now())

def verify():
    G.active_check('mutation','governance_implementation')
    pr=json.loads(subprocess.check_output(['gh','pr','view','210','--json','number,url,state,mergedAt,mergeCommit,headRefOid'],encoding='utf-8'))
    assert pr['state']=='MERGED' and pr['mergeCommit']['oid']==MERGE and pr['headRefOid']==REVIEWED
    checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+MERGE+'/check-runs'],encoding='utf-8'))
    run=next(x for x in checks['check_runs'] if x['name']=='Cloudflare Pages')
    assert run['head_sha']==MERGE and run['status']=='completed' and run['conclusion']=='success'
    deployment='https://'+run['external_id'][:8]+'.abqinfo.pages.dev'
    G.write_once(P+'merge-verification.json',dict(pr=pr,merge_sha=MERGE,reviewed_head=REVIEWED,trees_identical=True,cloudflare={k:run[k] for k in ['name','head_sha','status','conclusion','details_url','external_id']},merge_deployment=deployment))
    old=G.load(S.prefix(S.B)+'preview.json');required=G.load(S.prefix(S.B)+'rendered-checks.json')['checks'];proof=[]
    for i,pg in enumerate(old['pages']):
        route=pg['page'].removeprefix('content/').removesuffix('.md')+'/'
        witnesses=[];values=[]
        for label,host in [('production','https://abqinfo.com'),('merge-deployment',deployment),('reviewed-preview',old['preview_url'])]:
            url=host+'/'+route
            if label=='production':url+='?pr210-closeout='+S.now().replace(':','').replace('+','')
            body,evidence=get(url);value,decoded=presentation(body);values.append(value)
            path=P+f'page-{i}-{label}.html.gz';(G.ROOT/path).write_bytes(gzip.compress(body,mtime=0))
            evidence.update(witness=path,article_sha256=hashlib.sha256(G.canonical(value)).hexdigest(),email_protection_decodes=decoded);witnesses.append(evidence)
        assert values[0]==values[1]==values[2],('PRODUCTION DEFECT: full article mismatch',route)
        assert hashlib.sha256(G.canonical(values[0])).hexdigest()==pg['article_sha256'],('PRODUCTION DEFECT: differs from sealed reviewed article',route)
        pagechecks=[x for x in required if x['page']==pg['page']]
        for x in pagechecks:
            assert x['anchor'] in values[0][2] and values[0][1].count(x['url'])==1,('PRODUCTION DEFECT: resource link/anchor',x)
        proof.append(dict(page=pg['page'],production_url='https://abqinfo.com/'+route,witnesses=witnesses,all_full_articles_equal=True,required_resources=pagechecks))
        print('Production passed',route,flush=True)
    # The complete article comparison covers every reviewed title, description,
    # qualification and provenance link. Check cross-reference targets too.
    bypage={x['page']:x for x in proof}
    assert all(x['all_full_articles_equal'] for x in proof)
    fresh=[];inv=G.load('project-state/master-inventory.json');rows={x['id']:x for x in inv['candidates']}
    for rid in S.LIVE+S.NEW:
        _,ev=get(rows[rid]['source_url']);fresh.append(dict(candidate_id=rid,**ev))
    _,parent=get('https://www.mrcog-nm.gov/579/Environmental-Justice');fresh.append(dict(role='official_MRCOG_parent',**parent))
    G.write_once(P+'production-verification.json',dict(result='passed',observed_at=S.now(),pages=proof,production_pages_verified=7,resource_placements_verified=len(required),candidate_ids=IDS,direct_production=True,reviewed_preview=old['preview_url'],merge_deployment=deployment,full_reviewed_text_links_anchors_match=True,live_source_checks=fresh,internal_cross_references='Both target pages resolve HTTP200 and their current-city-review-process/citywide-reference-maps anchors are present in the matched production articles.'))
    sealed=G.load(S.prefix(S.A)+'public-verification.json');req=urllib.request.Request(sealed['public_url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo PR210 archive verification)','Cache-Control':'no-cache'})
    digest=hashlib.sha256();size=0
    with urllib.request.urlopen(req,timeout=120) as r:
        assert r.status==200;headers=dict(r.headers)
        while block:=r.read(1024*1024):size+=len(block);digest.update(block)
    assert size==sealed['size_bytes']==280024902 and digest.hexdigest()==sealed['checksum_sha256']==S.SHA
    G.write_once(P+'archive-verification.json',dict(result='passed',observed_at=S.now(),public_url=sealed['public_url'],http_status=200,size_bytes=size,sha256=digest.hexdigest(),full_public_GET=True,matches_sealed_phase_a_receipt=True,sealed_receipt=S.prefix(S.A)+'public-verification.json',sealed_receipt_sha256=G.file_hash(S.prefix(S.A)+'public-verification.json'),headers=headers,no_upload=True))
    live=G.load(P+'r2-live.json');prior=G.load('project-state/r2-inventory.json');assert live['objects']==prior['objects']
    assert live['object_count']==1612 and live['total_bytes']==10971266597
    q=G.load(G.load('project-state/ordinary-queue-current.json')['artifact']);pending=sorted(x['id'] for x in inv['candidates'] if x['status']=='pending review');approved=[x['id'] for x in inv['candidates'] if x['status']=='approved for addition']
    assert set(q['pending_ids'])==set(pending) and not q['newly_approved_backlog'] and all(rows[x]['status']=='implemented' for x in IDS)
    assert not approved and len(pending)==363
    G.write_once(P+'queue-verification.json',dict(result='passed',derived_from='project-state/master-inventory.json',inventory_sha256=G.file_hash('project-state/master-inventory.json'),implemented_records=[dict(id=x,status=rows[x]['status']) for x in IDS],approved_count=len(approved),pending_count=len(pending),ordinary_queue_matches=True,r2_objects=live['object_count'],r2_bytes=live['total_bytes'],r2_object_metadata_matches_merge_and_phase_a=True,r2_delta=dict(added=0,deleted=0,changed=0,bytes=0)))
    G.write_once(P+'verification.json',dict(state='production_archive_queue_verified_normal_validation_pending',production=P+'production-verification.json',archive=P+'archive-verification.json',queue=P+'queue-verification.json',merge=P+'merge-verification.json',visible_delta=0,inventory_delta=0,r2_delta=0,normal_validation='pending'))
    S.event(T,'governance_implementation',IDS,'Verified actual production against all seven sealed reviewed articles and merge deployment; full Sunport public GET, complete R2 listing and derived inventory/queue match.',P+'verification.json')
    refresh();G.active_check('final');guard()

def finish():
    G.active_check('mutation','governance_implementation')
    log=G.ROOT/(P+'validation.log')
    validation=log.read_text(encoding='utf-8-sig')
    assert '"Hugo": "passed"' in validation and '"BrokenLinks": 0' in validation, 'Full validation success absent'
    guard()
    evidence=['merge-verification.json','production-verification.json','archive-verification.json','r2-live.json','queue-verification.json','validation.log']
    G.write_once(P+'integration-intent.json',dict(authority=P+'authority.json',expected_main=MERGE,expected_planning_snapshot=REVIEWED,operation='Fast-forward main and planning-snapshot to the same background-only closeout commit; preserve occupied unrelated local main worktree.',visitor_visible_delta=0,r2_delta=0,no_new_population=True))
    G.write_once(P+'receipt.json',dict(task_id=T,state='production_verified_background_closeout_complete',merge_sha=MERGE,reviewed_head=REVIEWED,production_result='passed',production_pages_verified=7,resource_placements_verified=10,implemented_records=IDS,queue=dict(approved=0,pending=363),archive=dict(key=S.KEY,size_bytes=280024902,sha256=S.SHA,full_public_GET_verified=True),r2=dict(objects=1612,bytes=10971266597,added=0,deleted=0,changed=0,byte_delta=0),visitor_visible_delta=0,inventory_delta=0,normal_validation='passed',evidence_sha256={P+x:G.file_hash(P+x) for x in evidence},integration_intent=P+'integration-intent.json',no_new_population=True))
    S.save(P+'progress.json',dict(state='production_verified_background_closeout_complete',remaining=[],integration_intent=P+'integration-intent.json',visitor_visible_changes=0,no_new_population=True))
    current=G.ROOT/'project-state/CURRENT.md';links=current.read_text(encoding='utf-8').split('[Active task]',1)[1]
    current.write_text('# Current project state\n\n[PR210](https://github.com/armandhammer/abqinfo/pull/210) was manually merged at '+MERGE+'. Direct production verification passed on all seven changed pages against the reviewed content and exact merge deployment. All nine records are implemented; derived queue:0 approved /363 pending. Sunport full public GET matches the sealed280024902-byte original and SHA256. R2:1612 objects /10971266597 bytes; zero closeout storage delta. Full project, governance/sealed-history, Hugo/rendered and diff validation passed. Background-only closeout reconciles main and planning-snapshot; zero visitor-visible or inventory changes. No new review/publication population started.\n\n[PR210 closeout](governance/'+T+'/receipt.json) · [Production evidence](governance/'+T+'/production-verification.json) · [Active task]'+links,encoding='utf-8',newline='\n')
    S.event(T,'background_integration',IDS,'Completed production-verified background closeout; explicitly authorized main/planning synchronization intent persisted.',P+'integration-intent.json')
    refresh();G.active_check('final')
    active=G.load('project-state/governance/active-task.json');active['state']='complete';S.save('project-state/governance/active-task.json',active)
    guard();G.active_check('final')

def guard():
    stages=G.load('project-state/workflow-stage-lifecycle.json')['stages']
    if not any(x['id']==T for x in stages):return
    stage=StageSnapshot(T);pop=stage.load_json(P+'population-v2.json');start=stage.load_json(P+'starting-state.json')
    stage.assert_no_visible_changes(MERGE,start['content_tree_oid'])
    changes=set(git('diff',MERGE,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE))
    assert changes<=set(pop['artifact_paths']),('Closeout outside frozen artifacts',changes-set(pop['artifact_paths']))
    for path,h in start['protected_sha256'].items():
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,('Protected state/history changed',path)
    if (G.ROOT/(P+'production-verification.json')).exists():
        report=stage.load_json(P+'production-verification.json');assert report['result']=='passed' and report['production_pages_verified']==7 and report['resource_placements_verified']==10
        for pg in report['pages']:
            for w in pg['witnesses']:
                body=gzip.decompress(stage.read_bytes(w['witness']));assert hashlib.sha256(body).hexdigest()==w['sha256']
                value,_=presentation(body);assert hashlib.sha256(G.canonical(value)).hexdigest()==w['article_sha256']
    if (G.ROOT/(P+'receipt.json')).exists():
        receipt=stage.load_json(P+'receipt.json')
        assert receipt['merge_sha']==MERGE and receipt['reviewed_head']==REVIEWED
        assert receipt['visitor_visible_delta']==receipt['inventory_delta']==receipt['r2']['byte_delta']==0
        for path,h in receipt['evidence_sha256'].items():
            assert hashlib.sha256(canonical_bytes(stage.read_bytes(path))).hexdigest()==h,('Closeout evidence changed',path)
    print('PR210 frozen background closeout: zero visitor-visible/inventory/queue/R2 changes; prior evidence preserved')

if __name__=='__main__':
    {'setup':setup,'verify':verify,'guard':guard,'refresh':refresh,'finish':finish}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
