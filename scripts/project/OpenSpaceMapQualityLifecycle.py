"""Bound the Open Space map quality correction to 18 reviewed records and two pages."""
import collections
import hashlib
import html
import json
import re
import runpy
from pathlib import Path
from urllib.parse import unquote

from PublicationQuality import require_publication_quality
from WorkflowStageLifecycle import ROOT, StageSnapshot, canonical_bytes, digest, git

quality_audit = runpy.run_path(str(ROOT / 'scripts/project/Audit-VisiblePublicationQuality.py'))
audit = quality_audit['audit']
visible_links = quality_audit['visible_links']

PREFIX = 'project-state/discovery/open-space-map-quality-2026-09-28/'
QUEUE = 'project-state/discovery/publication-quality-remediation-2026-09-26.json'
PAGES = {'content/maps-data/maps.md', 'content/public-works/parks-recreation.md'}


def baseline_links(commit):
    links = collections.defaultdict(collections.Counter)
    paths = git('ls-tree', '-r', '--name-only', commit, '--', 'content').decode().splitlines()
    for path in paths:
        if not path.endswith('.md'):
            continue
        body = git('show', commit + ':' + path).decode('utf-8-sig')
        for url in re.findall(r'https?://[^\s<>"\)]+', body):
            links[unquote(html.unescape(url)).rstrip('/')][path] += 1
    return links


def guard_current_delta():
    stage = StageSnapshot('open-space-map-quality')
    data = stage.load_json(PREFIX + 'implementation.json')
    baseline = data['baseline_commit']
    assert baseline == stage.stage['baseline_commit']
    before = lambda path: json.loads(git('show', baseline + ':' + path).decode('utf-8-sig'))
    prior = before('project-state/master-inventory.json')
    current = stage.load_json('project-state/master-inventory.json')
    old = {r['id']: r for r in prior['candidates']}
    rows = {r['id']: r for r in current['candidates']}
    targets = set(data['target_ids'])
    assert len(targets) == 18 and old.keys() == rows.keys()
    assert {i for i in old if digest(old[i]) != digest(rows[i])} == targets
    assert {i: digest(rows[i]) for i in targets} == data['expected_row_digests']
    assert {k: v for k, v in prior.items() if k not in {'candidates', 'generated_at'}} == {k: v for k, v in current.items() if k not in {'candidates', 'generated_at'}}
    allowed_fields = {'scope_assessment', 'quality_assessment', 'publication_quality_decision', 'processing_notes', 'updated_at'}
    for rid in targets:
        a, b = old[rid], rows[rid]
        assert a['status'] == b['status'] == 'validated'
        assert {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)} <= allowed_fields
        assert b['processing_notes'][:-1] == a.get('processing_notes', [])
        assert b['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
        require_publication_quality(b)
    assert canonical_bytes(stage.read_bytes(QUEUE)) == canonical_bytes(git('show', baseline + ':' + QUEUE))
    for path in ('project-state/r2-inventory.json', 'project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json'):
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git('show', baseline + ':' + path))
    page_hashes = {p: hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() for p in PAGES}
    assert page_hashes == data['page_sha256']
    visible = set(git('diff', baseline, *([stage.end] if stage.end else []), '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').decode().splitlines())
    if not stage.end:
        visible |= set(git('diff', '--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml').decode().splitlines())
    assert visible == PAGES
    review = stage.load_json(PREFIX + 'review.json')
    assert {r['id'] for r in review['record_observations']} == targets
    receipts = stage.load_json(PREFIX + 'public-byte-measurements.json')['records']
    assert {r['id'] for r in receipts} == targets
    assert sum(bool(r.get('matches_inventory')) for r in receipts) == 16
    assert sum(bool(r.get('supporting_source_only')) for r in receipts) == 2
    for receipt in receipts:
        row = rows[receipt['id']]
        assert receipt.get('source_http_status') == 200
        if row.get('r2_url'):
            assert receipt['matches_inventory'] and receipt['public_sha256'] == row['checksum_sha256'] and receipt['public_size_bytes'] == row['size_bytes']
        else:
            assert receipt['supporting_source_only'] and row['file_type'] == 'Web page or live service'
    old_result = audit(prior, baseline_links(baseline))
    # Historical regression must pair the sealed inventory with that same
    # stage's content. The normal suite independently audits current content.
    result = audit(current, baseline_links(stage.end) if stage.end else visible_links())
    old_fail = {r['id']: r for r in old_result['failures']}
    fail = {r['id']: r for r in result['failures']}
    assert len(old_fail) == data['baseline_actual_failure_count'] == 1517
    assert len(fail) == data['after_actual_failure_count'] == 1499
    assert set(old_fail) - set(fail) == targets and not set(fail) - set(old_fail)
    assert all(fail[i] == old_fail[i] for i in fail)
    assert set(result['passing_ids']) - set(old_result['passing_ids']) == targets
    return data
