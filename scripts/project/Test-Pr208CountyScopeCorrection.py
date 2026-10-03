"""Exact corrective population, mission exclusions, protected witnesses and final render."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot,git
P='project-state/governance/pr208-county-scope-correction-2026-10-03/'
OLD='project-state/governance/strong-five-review-2026-10-03/'
IDS={'src-5b7146d18ffadd1a','src-dfd205371e4664e5'}
PAGES={'content/public-works/capital-projects.md','content/public-works/parks-recreation.md'}
def guard_current_delta():
    stage=StageSnapshot('pr208-county-scope-correction');base=stage.stage['baseline_commit']
    assert set(stage.load_json(P+'population.json')['candidate_ids'])==IDS
    prior={r['id']:r for r in json.loads(git('show',base+':project-state/master-inventory.json'))['candidates']}
    rows={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert rows.keys()==prior.keys() and {i for i in rows if rows[i]!=prior[i]}==IDS
    review=stage.load_json(P+'review.json');assert {r['id'] for r in review['entries']}==IDS
    for e in review['entries']:
        row=rows[e['id']];old=prior[e['id']]
        assert row['status']=='excluded' and row['scope_assessment']==e['scope_assessment']
        assert row['scope_assessment']['final_scope_decision']=='excluded'
        assert not row['implementation_locations'] and not row['implementation_location'] and not row['proposed_canonical_page']
        assert row['publication_quality_decision']['decision']=='excluded'
        for field in ['source_url','direct_file_url','r2_url','r2_key','r2_etag','r2_last_modified','size_bytes','checksum_sha256','local_path','agency','title','date','file_type','discovery_path','cited_predecessors','cited_successors']:
            assert row.get(field)==old.get(field),(e['id'],field)
        assert row['processing_notes'][:len(old['processing_notes'])]==old['processing_notes']
        assert not any(e['source_url'] in stage.read_text(page) for page in PAGES)
    for path in PAGES:
        assert stage.read_bytes(path).replace(b'\r\n',b'\n')==git('show','9194c21f89d6ef5b711b17d009ed778f75601ce2:'+path).replace(b'\r\n',b'\n')
    changes=set(git('diff',base,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(base))
    assert {p for p in changes if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'}==PAGES
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json','project-state/ordinary-queue-current.json','content/transportation/bicycling/_index.md','content/development-land-use/development-process.md','content/transportation/bicycling/projects/_index.md','content/public-works/city-facilities.md']:
        assert stage.read_bytes(path).replace(b'\r\n',b'\n')==git('show',base+':'+path).replace(b'\r\n',b'\n'),path
    historical=[p for p in git('ls-tree','-r','--name-only',base,'--',OLD,'project-state/governance/pr207-owner-correction-2026-09-30').decode().splitlines()]
    for path in historical:assert (G.ROOT/path).read_bytes().replace(b'\r\n',b'\n')==git('show',base+':'+path).replace(b'\r\n',b'\n'),path
    roots=stage.load_json('project-state/discovery/retained-source-audit-queue.json')
    prev=json.loads(git('show',base+':project-state/discovery/retained-source-audit-queue.json'))
    assert roots['records']==[r for r in prev['records'] if r['candidate_id'] not in IDS]
    for r in stage.load_json(P+'source-retrievals.json')['records']:
        if r['http_status']==200:
            raw=(G.ROOT/r['saved_source']).read_bytes();assert len(raw)==r['size_bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
    assert all(prior[i]==rows[i] for i in ['src-0ce9e0677d08c174','src-0d8b434458a51c1d','src-0a39e768262a9380d69d','src-4db14cde9f1460db','src-e2c19c0b6111c542'])
    return True
def check_rendered(root):
    for route,forbidden in [('public-works/capital-projects','animal-care-and-resource-center-2017'),('public-works/parks-recreation','historical-county-parks-investment')]:
        body=(Path(root)/route/'index.html').read_text(encoding='utf-8');assert forbidden not in body
        for e in G.load(P+'review.json')['entries']:assert e['source_url'] not in body
    for route,anchor in [('transportation/bicycling','facility-types-and-crossings'),('development-land-use/development-process','current-city-review-process')]:
        assert anchor in (Path(root)/route/'index.html').read_text(encoding='utf-8')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rendered-root');args=parser.parse_args();guard_current_delta()
    if args.rendered_root:check_rendered(args.rendered_root)
    print('PASS: only two County scope exclusions/removals; original review, City additions, Sunport, PR207 and provenance preserved.')
