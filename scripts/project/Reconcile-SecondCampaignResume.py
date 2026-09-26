#!/usr/bin/env python3
"""Read-only live reconciliation before resumed second-campaign mutations."""
import concurrent.futures, hashlib, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'project-state/discovery'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
c = load(D / 'ordinary-queue-second-large-resolution-campaign-2026-09-26.json')
live = load(D / 'second-large-campaign-resume-live-2026-09-26.json')
baseline = load(ROOT / c['baseline_r2_artifact'])
objects = {o['key']: o for o in live['objects']}
assert len(objects) == len({k.casefold() for k in objects}) == live['object_count']
assert live['total_bytes'] == sum(o['size_bytes'] for o in objects.values()) <= 10000000000
for o in baseline['objects']:
    assert all(objects[o['key']][f] == o[f] for f in ['size_bytes', 'etag']), ('Baseline collision', o['key'])
records = {r['id']: r for f in c['families_processed'] for r in load(ROOT / f['artifact'])['records'] if r.get('review_complete')}
intents = {}
for r in records.values():
    if r.get('upload_intent'):
        key = r['r2_key']
        assert key not in intents, ('Duplicate intent', key)
        q, i = r['fresh_source_qa'], r['upload_intent']
        assert (i['key'], i['size_bytes'], i['sha256']) == (key, q['size_bytes'], q['checksum_sha256'])
        intents[key] = r
new_keys = objects.keys() - {o['key'] for o in baseline['objects']}
assert new_keys <= intents.keys(), ('Unknown live objects', new_keys - intents.keys())
saved = {o['key']: o for o in c['archive_objects']}
assert saved.keys() <= new_keys
def verify(key):
    r, o = intents[key], objects[key]
    q = r['fresh_source_qa']
    assert o['size_bytes'] == q['size_bytes'], ('Non-identical collision', key)
    p = ROOT / q['staged_path']
    assert p.stat().st_size == q['size_bytes'] and hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() == q['checksum_sha256']
    req = urllib.request.Request('https://files.abqinfo.com/' + key, headers={'Cache-Control': 'no-cache', 'User-Agent': 'ABQInfo resume reconciliation'})
    with urllib.request.urlopen(req, timeout=60) as response:
        h, size = hashlib.sha256(), 0
        while block := response.read(1024 * 1024): h.update(block); size += len(block)
        assert response.status == 200 and (size, h.hexdigest()) == (q['size_bytes'], q['checksum_sha256']), ('Non-identical collision', key)
    if key in saved:
        assert saved[key]['etag'] == o['etag'] and saved[key]['checksum_sha256'] == h.hexdigest()
    return {'id': r['id'], 'key': key, 'size_bytes': size, 'checksum_sha256': h.hexdigest(), 'etag': o['etag'], 'byte_identical': True, 'already_recorded_complete': key in saved, 'verified_at': datetime.now(timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    receipts = list(pool.map(verify, sorted(new_keys)))
report = {'schema_version': 1, 'state': 'complete_pre_mutation_reconciliation', 'recorded_at': datetime.now(timezone.utc).isoformat(), 'live_listing_artifact': 'project-state/discovery/second-large-campaign-resume-live-2026-09-26.json', 'baseline_objects_unchanged': len(baseline['objects']), 'live_object_count': live['object_count'], 'live_total_bytes': live['total_bytes'], 'campaign_objects_exact_verified': len(receipts), 'unrecorded_completed_keys': sorted(new_keys - saved.keys()), 'receipts': receipts, 'visitor_visible_content_changed': False}
(D / 'second-large-campaign-resume-reconciliation-2026-09-26.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'receipts'}))
