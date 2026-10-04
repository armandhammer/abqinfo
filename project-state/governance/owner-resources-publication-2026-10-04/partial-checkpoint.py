"""Persist an honest incomplete publication checkpoint; no PR or reviewed-head sync."""
import copy,sys,subprocess
from html.parser import HTMLParser
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
P=S.prefix(S.B)
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if a.get('id'):self.ids.append(a['id'])
    def handle_data(self,data):self.text.append(data)
locations=S.G.load(P+'evidence-3.json')['locations'];rows={r['id']:r for r in S.G.load('project-state/master-inventory.json')['candidates']};proof=[]
for rid,locs in locations.items():
    for loc in locs:
        page,anchor=loc.split('#');route=page.removeprefix('content/').removesuffix('.md')+'/'
        f=S.G.ROOT/('tmp/site-build/'+route+'index.html');v=Page();v.feed(f.read_text(encoding='utf-8'))
        url=rows[rid]['r2_url'] if rid==S.SUN else rows[rid]['source_url']
        assert v.links.count(url)==1 and anchor in v.ids,(rid,page,anchor)
        if rid==S.SUN:
            assert S.SOURCE in v.links
            source_text=(S.G.ROOT/page).read_text(encoding='utf-8')
            sunport_entry=source_text[source_text.index('- [Albuquerque International Sunport'):source_text.index('- [Double Eagle II Airport',source_text.index('- [Albuquerque International Sunport'))]
            assert 'exceeds ABQInfo' not in sunport_entry
            assert sum('Sunport Sustainable Airport Master Plan' in t for t in v.text)==1
            assert any('LegislationDetail.aspx?ID=3980533' in x for x in v.links)
        proof.append(dict(candidate_id=rid,page=page,route=route,anchor=anchor,url=url,exact_link_count=1,section_anchor_present=True))
S.save(P+'rendered-checks.json',dict(state='partial_local_rendered_checks_passed',checks=proof,new_neighborhood_resources='Not published; actual desktop Chrome render and visual quality remain pending.',not_nonproduction_preview=True))
pointer=S.G.load('project-state/ordinary-queue-current.json');q=copy.deepcopy(S.G.load(pointer['artifact']));inv=S.G.load('project-state/master-inventory.json')
pending=sorted(r['id'] for r in inv['candidates'] if r['status']=='pending review')
q.update(artifact_type='in_progress_owner_publication_queue',recorded_at=S.now(),inventory_generated_at=inv['generated_at'],inventory_sha256=S.G.file_hash('project-state/master-inventory.json'),pending_ids=pending,pending_review_count=len(pending))
q['source_or_structural_blocked_pending_ids'][S.NEW[0]]='Current owner publication prerequisite: actual desktop Chrome rendering of exact supplied app is pending; metadata is not usability evidence.'
q['source_or_structural_blocked_pending_count']=len(q['source_or_structural_blocked_pending_ids'])
q['newly_approved_backlog']=[dict(id=S.NEW[1],title=rows[S.NEW[1]]['title'],reason='Owner-supplied maintained ONC live directory passes scope/value; actual visual quality and publication remain pending.',review=P+'review.json')]
q['in_progress_publication']=dict(task=S.B,implemented_ids=S.LIVE+[S.SUN],pending_app=S.NEW[0],approved_directory=S.NEW[1],not_live=True)
assert set(pending)==set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|set(q['ungated_pending_ids'])
S.save(P+'queue.json',q);S.save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=P+'queue.json',task=S.B))
S.refresh(S.B)
subprocess.run([sys.executable,'scripts/project/Build-ConsolidatedHumanReviewQueue.py'],check=True)
progress=dict(state='in_progress_waiting_for_desktop_chrome_access',phase_a_integration_sha='1e56540c199d26384989074d497a9bffac60e3f4',completed=['phase_a_main_integration','two_stable_source_ids','full_publication_population_and_contract','six_settled_resources_implemented','Sunport_archive_link_implemented','fresh_external_GET_checks','ONC_directory_scope_value_review','official_ArcGIS_title_identity','content_style','actual_visible_quality_audit','Hugo','partial_local_rendered_semantics','diff_check'],remaining=['actual_desktop_Chrome_render_of_owner_ArcGIS_app','actual_visual_quality_of_directory','publish_two_neighborhood_resources_and_internal_cross_reference_if_warranted','full_final_project_validation','nonproduction_Cloudflare_preview','inspect_every_final_changed_section','one_unmerged_content_PR','planning_snapshot_to_reviewed_PR_head'],blocker=dict(browser_inventory=dict(apps=[],browsers=[]),chrome_create_error='Browser is not available: chrome',pending_owner_choice='Enable desktop Chrome connector or explicitly authorize installed Chrome through Playwright.',required_by='Current owner Phase B instruction requires actual desktop Chrome rendering; computer-use tool permits only cua_repl unless another technology is explicitly requested.'),r2_objects=1612,r2_bytes=10971266597,additional_phase_b_r2_mutations=0,main_queue=dict(approved=7,pending=363),branch_queue=dict(approved=1,pending=364),pr_created=False,preview_created=False,planning_snapshot_unchanged_at_phase_a=True,normal_final_validation='pending')
S.save(P+'progress.json',progress)
current='# Current project state\n\nPhase A integrated on main at1e56540c199d26384989074d497a9bffac60e3f4: exact Sunport original archived, full public GET verified; complete validation passed. R2:1612 objects /10971266597 bytes; standing150000000 object and13000000000 project ceilings unchanged. Phase B branch has six reviewed resources and one Sunport archive-link update; title identified as Recognized Neighborhood Associations and Coalitions; ONC directory scope approved. Actual desktop Chrome access pending for new-resource and preview visual review. No PR/preview yet. Main queue7 approved /363 pending; branch1 approved /364 pending. Planning-snapshot remains at Phase A main.\n\n[Publication progress](governance/'+S.B+'/progress.json) · [Sunport receipt](governance/'+S.A+'/receipt.json) · [Active task](governance/active-task.json) · [Owner correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [Closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).\n'
(S.G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
S.refresh(S.B);S.G.active_check('mutation','content_implementation');S.guard()
print('Partial publication checkpoint saved; final review and PR requirements remain incomplete.')
