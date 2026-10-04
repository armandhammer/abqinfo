"""Final local semantics, exact frozen queue and interruption-safe validation checkpoint."""
import copy,hashlib,json,re,subprocess,sys,urllib.request
from html.parser import HTMLParser
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
P=S.prefix(S.B)
S.G.active_check('mutation','governance_implementation')
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if a.get('id'):self.ids.append(a['id'])
    def handle_data(self,data):self.text.append(data)
rows={r['id']:r for r in S.G.load('project-state/master-inventory.json')['candidates']}
locations=S.G.load(P+'evidence-3.json')['locations']
for rid,r in S.G.load(P+'review-final.json')['records'].items():locations[rid]=[r['placement']]
proof=[]
for rid,locs in locations.items():
    for loc in locs:
        page,anchor=loc.split('#');route=page.removeprefix('content/').removesuffix('.md')+'/'
        body=(S.G.ROOT/('tmp/site-build/'+route+'index.html')).read_bytes();v=Page();v.feed(body.decode('utf-8'))
        url=rows[rid]['r2_url'] if rid==S.SUN else rows[rid]['source_url']
        assert v.links.count(url)==1 and anchor in v.ids,(rid,page,anchor)
        if rid==S.SUN:
            assert S.SOURCE in v.links and any('LegislationDetail.aspx?ID=3980533' in x for x in v.links)
            assert sum('Sunport Sustainable Airport Master Plan' in t for t in v.text)==1
            text=(S.G.ROOT/page).read_text(encoding='utf-8');entry=text[text.index('- [Albuquerque International Sunport'):text.index('- [Double Eagle II Airport',text.index('- [Albuquerque International Sunport'))]
            assert 'exceeds ABQInfo' not in entry
        proof.append(dict(candidate_id=rid,page=page,route=route,anchor=anchor,url=url,exact_link_count=1,section_anchor_present=True,local_html_sha256=hashlib.sha256(body).hexdigest()))
S.save(P+'rendered-checks.json',dict(state='all_local_rendered_semantics_passed',checks=proof,all_nine_records=True,visible_pages=7,not_nonproduction_preview=True))
checks=[]
urls=[(rid,rows[rid]['source_url']) for rid in S.LIVE+S.NEW]+[('official_MRCOG_parent','https://www.mrcog-nm.gov/579/Environmental-Justice')]
for rid,url in urls:
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (ABQInfo external link verification)','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=60) as response:
        data=response.read();assert response.status==200
        checks.append(dict(candidate_id=rid,requested_url=url,final_url=response.url,http_status=response.status,complete_response=True,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),retrieved_at_utc=S.now()))
S.save(P+'external-checks.json',dict(checked_at_utc=S.now(),checks=checks,all_http_200=True))
updates=[dict(id=rid,changes=dict(validation_status='passed')) for rid in S.LIVE+[S.SUN]+S.NEW]
S.save(P+'record-updates.json',updates);S.refresh(S.B)
if not all(rows[rid]['validation_status']=='passed' for rid in S.LIVE+[S.SUN]+S.NEW):
    subprocess.run([sys.executable,'scripts/project/Update-CandidatesBatch.py','--requests',P+'record-updates.json'],check=True)
S.refresh(S.B);inv=S.G.load('project-state/master-inventory.json')
q=copy.deepcopy(S.G.load(P+'queue.json'));pending=sorted(r['id'] for r in inv['candidates'] if r['status']=='pending review')
q.update(artifact_type='owner_publication_queue',recorded_at=S.now(),inventory_generated_at=inv['generated_at'],inventory_sha256=S.G.file_hash('project-state/master-inventory.json'),pending_ids=pending,pending_review_count=len(pending),newly_approved_backlog=[])
q['source_or_structural_blocked_pending_ids'].pop(S.NEW[0],None);q['source_or_structural_blocked_pending_count']=len(q['source_or_structural_blocked_pending_ids'])
q['in_progress_publication']=dict(task=S.B,implemented_ids=S.LIVE+[S.SUN]+S.NEW,not_live=True)
assert len(pending)==363 and not any(r['status']=='approved for addition' for r in inv['candidates'])
assert set(pending)==set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|set(q['ungated_pending_ids'])
S.save(P+'queue.json',q)
# Update only top-level current fields; preserve all historical checkpoint bytes.
f=S.G.ROOT/'project-state/checkpoint.json';raw=f.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8')
remaining=sorted([r for r in inv['candidates'] if r['status'] in ['pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'] or (r['status']=='implemented' and r['validation_status']!='passed')],key=lambda r:r['id'])
values=dict(recorded_at=S.now(),completed_item_range='Frozen nine-record owner publication implemented; local rendered and external checks passed; full validation and preview pending',total_candidates=len(inv['candidates']),counts_by_status=inv['counts'],remaining_nonterminal=len(remaining),next_pending_id=remaining[0]['id'] if remaining else None,resume_command='Complete final project validation, inspect the nonproduction Cloudflare preview, open one unmerged content PR and synchronize planning-snapshot to its reviewed head. Do not merge or deploy production.')
for k,v in values.items():
    pattern=r'("'+k+r'"\s*:\s*)(?:'+(r'\{[^}]*\}' if isinstance(v,dict) else r'"(?:[^"\\]|\\.)*"|\d+|null')+')'
    if isinstance(v,dict):replacement=json.dumps(v,ensure_ascii=False,indent=2).replace('\n','\n  ').replace('\n',nl)
    else:replacement=json.dumps(v,ensure_ascii=False)
    text,n=re.subn(pattern,lambda m:m.group(1)+replacement,text,count=1);assert n==1,k
f.write_bytes(text.encode('utf-8'))
links='[Active task](governance/active-task.json) · [Owner correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [Closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).'
current='# Current project state\n\nPhase A integrated on main at1e56540c199d26384989074d497a9bffac60e3f4; exact Sunport archive full public GET verified. R2:1612 objects /10971266597 bytes; standing ceilings unchanged. Phase B implements all nine frozen resources on seven existing pages, including Recognized Neighborhood Associations and Coalitions and ONC Neighborhood Association Websites. Installed Chrome review, local rendered and fresh external checks passed. Full project validation, final Cloudflare preview inspection, one unmerged content PR and exact planning-snapshot sync remain. Branch queue:0 approved /363 pending; no additional R2 actions.\n\n[Publication progress](governance/'+S.B+'/progress.json) · [Sunport receipt](governance/'+S.A+'/receipt.json) · '+links+'\n'
(S.G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
S.save(P+'progress.json',dict(state='all_content_implemented_final_validation_pending',completed=['Phase A integrated','all nine resources implemented','Chrome new-source scope/quality review','all local Hugo link/anchor semantics','nine external URLs HTTP200'],remaining=['complete_project_validation','nonproduction_preview_inspection','unmerged_content_PR','exact_planning_snapshot_sync'],r2_objects=1612,r2_bytes=10971266597,branch_queue=dict(approved=0,pending=363),pr_created=False,preview_created=False))
S.save(P+'receipt.json',dict(task_id=S.B,state='content_complete_final_validation_pending',phase_a_integration_sha='1e56540c199d26384989074d497a9bffac60e3f4',candidate_ids=S.LIVE+[S.SUN]+S.NEW,pages=S.PAGES,new_resource_review=P+'review-final.json',settled_six_reviews_unchanged=True,local_rendered_checks=P+'rendered-checks.json',external_checks=P+'external-checks.json',normal_validation='pending',preview='pending',pr='pending',r2_objects=1612,r2_bytes=10971266597,phase_a_added_objects=1,phase_a_added_bytes=280024902,phase_b_r2_mutations=0,content_unmerged=True))
S.refresh(S.B)
subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
S.refresh(S.B);S.G.active_check('final');S.guard()
print('Complete content checkpoint passed; full normal validation and preview/PR remain.')
