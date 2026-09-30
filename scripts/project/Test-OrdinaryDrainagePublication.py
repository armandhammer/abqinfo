"""Check source bytes, publication form, and exact four-record queue accounting."""

import hashlib
import json
import tarfile
from pathlib import Path

from OrdinaryDrainagePublicationLifecycle import guard_current_delta

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'project-state/governance/ordinary-drainage-projects-2026-09-29/review.json'
PAGE = ROOT / 'content/public-works/stormwater-drainage.md'
EVIDENCE = ROOT / 'project-state/governance/pr206-review-correction-2026-09-29/review.json'

guard_current_delta()
review = json.loads(REVIEW.read_text(encoding='utf-8'))
evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
bundle = ROOT / evidence['bundle']
assert hashlib.sha256(bundle.read_bytes()).hexdigest() == evidence['bundle_sha256']
assert bundle.stat().st_size == evidence['bundle_size_bytes']
captures = {record['id']: record for record in evidence['records']}
assert set(captures) == {entry['id'] for entry in review['entries']}
retrievals = json.loads((ROOT / evidence['prior_retrieval_manifest']).read_text(encoding='utf-8'))['records']
official = {record['id']: record for record in retrievals
            if record.get('id') in captures and record.get('http_status') == 200}
assert set(official) == set(captures)
inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8'))
rows = {row['id']: row for row in inventory['candidates']}
page = PAGE.read_text(encoding='utf-8')
assert '## County Drainage Projects' in page
with tarfile.open(bundle, 'r:gz') as archive:
    assert set(archive.getnames()) == {capture['member'] for capture in captures.values()}
    for entry in review['entries']:
        capture = captures[entry['id']]
        assert capture['original_staging_path'] == entry['saved_source']
        assert capture['official_url'] == entry['final_url']
        assert capture['http_status'] == 200
        assert capture['sha256'] == entry['source_sha256']
        retrieval = official[entry['id']]
        assert retrieval['saved_source'] == capture['original_staging_path']
        assert retrieval['final_url'] == capture['official_url']
        assert retrieval['retrieved_at'] == capture['retrieved_at']
        assert retrieval['size_bytes'] == capture['size_bytes']
        assert retrieval['sha256'] == capture['sha256']
        member = archive.getmember(capture['member'])
        assert member.isfile() and member.size == capture['size_bytes']
        source = archive.extractfile(member)
        assert source is not None
        assert hashlib.sha256(source.read()).hexdigest() == entry['source_sha256']
        row = rows[entry['id']]
        assert row['source_url'] == entry['final_url']
        assert row['implementation_locations'] == ['content/public-works/stormwater-drainage.md']
        assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
        assert row['publication_quality_decision']['decision'] == 'passes'
        assert row['quality_assessment']['publication_form'] == 'live_service'
        assert row['direct_file_url'] is None and row['r2_url'] is None
        status = row['validation_status']
        assert 'nonproduction preview verified' in status
        assert 'HTTP 403' in status
        assert 'owner review and production verification pending' in status
        assert entry['title'] in page and page.count(entry['final_url']) == 1
print('PASS: four exact County drainage links, source hashes, quality decisions, inventory rows, and queue delta')
