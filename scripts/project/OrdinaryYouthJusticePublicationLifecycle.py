"""Guard the frozen two-record family and its complete source/publication delta."""
import hashlib
import io
import json
import tarfile

import TaskGovernance as G
from PublicationQuality import require_publication_quality
from WorkflowStageLifecycle import StageSnapshot, git

PREFIX = 'project-state/governance/ordinary-youth-justice-publication-2026-09-30/'
PAGE = 'content/public-works/city-facilities.md'


def guard_current_delta():
    stage = StageSnapshot('ordinary-youth-justice-publication')
    pop = stage.load_json(PREFIX + 'population.json')
    base = stage.stage['baseline_commit']
    assert base == pop['baseline_commit'] == '07a0485306963f2e485a93030ece81c6a2c01da9'
    paths = (set(git('diff', base, stage.end, '--name-only').decode().splitlines())
             if stage.end else set(G.changed_paths(base)))
    assert paths <= set(pop['artifact_paths'])
    visible = {p for p in paths if p.startswith(('content/', 'layouts/', 'assets/', 'static/')) or p == 'hugo.toml'}
    assert visible == {PAGE}
    assert 'project-state/r2-inventory.json' not in paths
    before = json.loads(git('show', base + ':project-state/master-inventory.json'))
    after = stage.load_json('project-state/master-inventory.json')
    old = {r['id']: r for r in before['candidates']}
    new = {r['id']: r for r in after['candidates']}
    selected = set(pop['candidate_ids'])
    assert len(selected) == 2
    assert {rid for rid in old.keys() | new.keys() if old.get(rid) != new.get(rid)} == selected
    review = stage.load_json(PREFIX + 'review.json')
    page = stage.read_text(PAGE)
    assert {r['id'] for r in review['entries']} == selected
    assert review['group_introduction'] in page and '## ' + review['section_heading'] in page
    for entry in review['entries']:
        row = new[entry['id']]
        assert row['status'] == 'implemented' and row['implementation_locations'] == [PAGE]
        assert not row.get('r2_url') and not row.get('direct_file_url')
        assert row['scope_assessment'] == old[entry['id']]['scope_assessment']
        require_publication_quality(row)
        assert row['quality_assessment']['publication_form'] == 'grouped_component'
        assert page.count(entry['final_url']) == 1 and entry['description'] in page
    queue = stage.load_json('project-state/discovery/ordinary-youth-justice-2026-09-30/queue.json')
    assert len(queue['newly_approved_backlog']) == 18 and queue['pending_review_count'] == 372
    assert set(queue['youth_justice_implemented_ids_removed_from_approved']) == selected
    assert stage.load_json('project-state/ordinary-queue-current.json')['artifact'] == 'project-state/discovery/ordinary-youth-justice-2026-09-30/queue.json'
    audit_path = 'project-state/discovery/retained-source-audit-queue.json'
    old_audit = json.loads(git('show', base + ':' + audit_path))
    new_audit = stage.load_json(audit_path)
    prior_roots = {r['source_url']: r for r in old_audit['records']}
    current_roots = {r['source_url']: r for r in new_audit['records']}
    assert all(current_roots.get(url) == record for url, record in prior_roots.items())
    added_roots = [record for url, record in current_roots.items() if url not in prior_roots]
    assert {r['candidate_id'] for r in added_roots} == selected
    assert all(r['audit_status'] == 'pending descendant crawl' for r in added_roots)
    assert new_audit['next_pending_source_url'] == old_audit['next_pending_source_url']
    rendering = stage.load_json(PREFIX + 'source-rendering.json')
    bundle = stage.read_bytes(rendering['bundle'])
    assert hashlib.sha256(bundle).hexdigest() == rendering['bundle_sha256']
    retrievals = stage.load_json('project-state/discovery/human-review-reassessment-2026-09-26/retrievals.json')['records']
    with tarfile.open(fileobj=io.BytesIO(bundle), mode='r:gz') as archive:
        assert set(archive.getnames()) == {r['member'] for r in rendering['records']}
        for capture in rendering['records']:
            original = next(r for r in retrievals if r.get('id') == capture['id'] and r.get('http_status') == 200)
            for key in ('sha256', 'size_bytes', 'final_url', 'retrieved_at', 'saved_source'):
                assert capture[key] == original[key]
            body = archive.extractfile(capture['member']).read()
            assert len(body) == capture['size_bytes'] and hashlib.sha256(body).hexdigest() == capture['sha256']
            assert hashlib.sha256(stage.read_bytes(capture['render'])).hexdigest() == capture['render_sha256']
    assert review['archive_objects_added'] == review['archive_bytes_added'] == 0
