"""Exact five-record deltas, source bytes, owner negatives and rendered links."""
import argparse, hashlib, json
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git
from PublicationQuality import require_publication_quality

P='project-state/governance/strong-five-review-2026-10-03/'
IDS={'src-0a39e768262a9380d69d','src-0ce9e0677d08c174','src-0d8b434458a51c1d','src-5b7146d18ffadd1a','src-dfd205371e4664e5'}
PAGES={'content/transportation/bicycling/_index.md','content/development-land-use/development-process.md','content/public-works/capital-projects.md','content/public-works/parks-recreation.md'}

def guard_current_delta():
    stage=StageSnapshot('strong-five-review-publication');base=stage.stage['baseline_commit']
    pop=stage.load_json(P+'population-v4.json')
    assert set(pop['candidate_ids'])==IDS
    prior={r['id']:r for r in json.loads(git('show',base+':project-state/master-inventory.json'))['candidates']}
    rows={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    assert rows.keys()==prior.keys() and {i for i in rows if rows[i]!=prior[i]}==IDS
    review=stage.load_json(P+'review.json');entries={r['id']:r for r in review['entries']}
    assert set(entries)==IDS
    for rid in IDS:
        row=rows[rid];entry=entries[rid]
        assert row['status']==entry['outcome']
        for field in ['source_url','direct_file_url','r2_url','r2_key','size_bytes','checksum_sha256','discovery_path','cited_predecessors','cited_successors']:
            assert row.get(field)==prior[rid].get(field),(rid,field)
        assert prior[rid]['processing_notes']==row['processing_notes'][:len(prior[rid]['processing_notes'])]
        assert row['scope_assessment']==entry['scope_assessment'] and row['publication_quality_decision']==entry['publication_quality_decision']
        if entry['outcome']=='implemented':
            require_publication_quality(row)
            assert row['implementation_locations']==[entry['page']]
            body=stage.read_text(entry['page']);assert body.count(entry['source_url'])==1
            assert entry['heading'] in body
        else:
            assert not row['implementation_locations'] and not row['proposed_canonical_page']
            assert not any(entry['source_url'] in stage.read_text(page) for page in PAGES)
    for rid in ['src-4db14cde9f1460db','src-e2c19c0b6111c542']:
        assert rows[rid]==prior[rid] and rows[rid]['status']=='excluded'
    changes=set(git('diff',base,stage.end,'--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(base))
    assert {p for p in changes if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'}==PAGES
    assert stage.read_bytes('content/public-works/city-facilities.md').replace(b'\r\n',b'\n')==git('show',base+':content/public-works/city-facilities.md').replace(b'\r\n',b'\n')
    for path in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert stage.read_bytes(path).replace(b'\r\n',b'\n')==git('show',base+':'+path).replace(b'\r\n',b'\n')
    source=stage.load_json(P+'source-retrievals.json')
    for item in stage.load_json(P+'source-rendering.json')['records']:
        assert hashlib.sha256((G.ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    assert {r['id'] for r in source['records']}==IDS
    for row in source['records']:
        body=(G.ROOT/row['saved_source']).read_bytes()
        assert len(body)==row['size_bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
        assert row['extracted_word_count']==len((G.ROOT/row['text_artifact']).read_text(encoding='utf-8').split())
        if row['witness']=='saved_official_200_capture_not_fresh':
            saved=row['prior_retrieval'];assert saved['http_status']==200 and saved['sha256']==row['sha256']
            assert row['http_status']==403
        else:assert row['http_status']==200
    queue=stage.load_json('project-state/discovery/strong-five-review-2026-10-03/queue.json')
    old_queue=json.loads(git('show',base+':project-state/governance/pr207-owner-correction-2026-09-30/receipt.json'))
    assert len(queue['newly_approved_backlog'])==13 and queue['pending_review_count']==372
    for field in ['pending_ids','gated_pending_ids','source_or_structural_blocked_pending_ids','unresolved_ungated_prerequisites']:
        assert queue[field]==old_queue[field]
    roots=stage.load_json('project-state/discovery/retained-source-audit-queue.json')
    previous=json.loads(git('show',base+':project-state/discovery/retained-source-audit-queue.json'))
    assert roots['records'][:len(previous['records'])]==previous['records']
    added=roots['records'][len(previous['records']):]
    assert {r['candidate_id'] for r in added}==IDS-{'src-0a39e768262a9380d69d'}
    assert all(r['audit_status']=='pending descendant crawl' for r in added)
    return True

def check_rendered(root):
    from html.parser import HTMLParser
    class Structure(HTMLParser):
        def __init__(self):super().__init__();self.links=[];self.ids=set();self.text=[]
        def handle_starttag(self,tag,attrs):
            attr=dict(attrs)
            if 'id' in attr:self.ids.add(attr['id'])
            if tag=='a':self.links.append(attr.get('href'))
        def handle_data(self,data):self.text.append(data)
    routes={'src-0ce9e0677d08c174':('transportation/bicycling','facility-types-and-crossings'),
            'src-0d8b434458a51c1d':('development-land-use/development-process','current-city-review-process'),
            'src-5b7146d18ffadd1a':('public-works/capital-projects','animal-care-and-resource-center-2017'),
            'src-dfd205371e4664e5':('public-works/parks-recreation','historical-county-parks-investment')}
    for entry in G.load(P+'review.json')['entries']:
        if entry['id'] not in routes:continue
        # Historical four-entry rendering remains sealed at the stage endpoint.
        # The separate corrective stage checks the two County removals on live output.
        if StageSnapshot('strong-five-review-publication').end and entry['id'] in {'src-5b7146d18ffadd1a','src-dfd205371e4664e5'}:continue
        route,anchor=routes[entry['id']];parser=Structure();parser.feed((Path(root)/route/'index.html').read_text(encoding='utf-8'))
        assert anchor in parser.ids and parser.links.count(entry['source_url'])==1
        words=' '.join(parser.text)
        if 'animal' in route:assert '2017' in words
        if entry['id']=='src-5b7146d18ffadd1a':assert 'not confirmation of present operating capacity or final spending' in words
        if entry['id']=='src-dfd205371e4664e5':assert 'do not confirm that later work was funded or completed' in words

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rendered-root');args=parser.parse_args()
    guard_current_delta()
    if args.rendered_root:check_rendered(args.rendered_root)
    print('PASS: exact five reviewed records; four qualified HTML entries; one redundant summary excluded; source/R2/owner evidence preserved.')
