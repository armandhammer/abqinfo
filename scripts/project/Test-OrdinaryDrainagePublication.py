"""Check source bytes, publication form, and exact four-record queue accounting."""

import hashlib
import json
from pathlib import Path

from OrdinaryDrainagePublicationLifecycle import guard_current_delta

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'project-state/governance/ordinary-drainage-projects-2026-09-29/review.json'
PAGE = ROOT / 'content/public-works/stormwater-drainage.md'

guard_current_delta()
review = json.loads(REVIEW.read_text(encoding='utf-8'))
inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8'))
rows = {row['id']: row for row in inventory['candidates']}
page = PAGE.read_text(encoding='utf-8')
assert '## County Drainage Projects' in page
for entry in review['entries']:
    source = ROOT / entry['saved_source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['source_sha256']
    row = rows[entry['id']]
    assert row['source_url'] == entry['final_url']
    assert row['implementation_locations'] == ['content/public-works/stormwater-drainage.md']
    assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
    assert row['publication_quality_decision']['decision'] == 'passes'
    assert row['quality_assessment']['publication_form'] == 'live_service'
    assert row['direct_file_url'] is None and row['r2_url'] is None
    assert entry['title'] in page and page.count(entry['final_url']) == 1
print('PASS: four exact County drainage links, source hashes, quality decisions, inventory rows, and queue delta')
