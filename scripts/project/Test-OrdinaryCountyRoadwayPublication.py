"""Check the exact County roadway publication and queue delta."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'project-state/governance/ordinary-county-roadway-2026-09-29/'
BASELINE = '7b28ef1120f7faf7480bdda90a8f0df6a3e31f87'
PAGE = 'content/transportation/roadway-projects/_index.md'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def old(path):
    return json.loads(subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT))


population = load(PREFIX + 'population-v19.json')
selected = set(population['candidate_ids'])
assert len(selected) == 6 and population['pages'] == [PAGE]
before = {r['id']: r for r in old('project-state/master-inventory.json')['candidates']}
after = {r['id']: r for r in load('project-state/master-inventory.json')['candidates']}
changed = {i for i in before.keys() | after.keys() if before.get(i) != after.get(i)}
assert changed == selected, f'Unexpected inventory records changed: {changed ^ selected}'
review = load(PREFIX + 'review-v4.json')
assert {r['id'] for r in review['entries']} == selected
page = (ROOT / PAGE).read_text(encoding='utf-8-sig')
rendered = ROOT / 'tmp/site-build/transportation/roadway-projects/index.html'
assert rendered.is_file(), 'Hugo render required'
html = rendered.read_text(encoding='utf-8')
for entry in review['entries']:
    row = after[entry['id']]
    assert row['status'] == 'implemented'
    assert row['scope_assessment']['final_scope_decision'] == 'passes_both_gates'
    assert row['publication_quality_decision']['decision'] == 'passes'
    assert row['quality_assessment']['visual_inspection_completed']
    assert row['implementation_locations'] == [PAGE]
    assert not row.get('r2_url') and not row.get('direct_file_url')
    assert entry['http_status'] == 200 and entry['content_type'].startswith('text/html')
    assert page.count(entry['final_url']) == 1
    assert html.count(entry['final_url']) == 1
    assert entry['description'] in page
queue = load('project-state/discovery/ordinary-county-roadway-2026-09-29/queue.json')
assert len(queue['newly_approved_backlog']) == 24
assert set(queue['county_roadway_implemented_ids_removed_from_approved']) == selected
assert queue['pending_review_count'] == 372
assert load('project-state/ordinary-queue-current.json')['artifact'] == 'project-state/discovery/ordinary-county-roadway-2026-09-29/queue.json'
assert review['archive_objects_added'] == review['archive_bytes_added'] == 0
for held in ('src-1f9cf39555e7be6f', 'src-ed75a3cb5ecc3b0b'):
    assert after[held] == before[held]
print('PASS: six exact inventory and official-link additions; 24 approved remain; no R2 or held-record change')
