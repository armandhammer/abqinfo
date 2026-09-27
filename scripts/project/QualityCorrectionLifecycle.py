"""Exact owner-authorized Old Town correction after the sealed Planning stage."""
import json
import hashlib
import subprocess
from collections import Counter
from WorkflowStageLifecycle import ROOT, StageSnapshot, digest, canonical_bytes
from PublicationQuality import validate_affected_records

BASELINE = '2588c0c1399351957f140825c50fc485fe5546b1'
ARTIFACT = 'project-state/discovery/old-town-quality-correction-2026-09-26/implementation.json'

def before(path, baseline):
    return json.loads(subprocess.check_output(['git', 'show', baseline + ':' + path], cwd=ROOT).decode('utf-8-sig'))

def validate_delta(data, prior, current, paths, hashes, r2_before, r2_after):
    old = {r['id']: r for r in prior['candidates']}
    rows = {r['id']: r for r in current['candidates']}
    assert len(rows) == len(current['candidates']) == len(old) == len(prior['candidates'])
    assert rows.keys() == old.keys() and prior.keys() == current.keys()
    assert {i for i in rows if rows[i] != old[i]} == set(data['changed_inventory_ids'])
    assert all(prior[k] == current[k] for k in prior if k not in {'candidates', 'counts', 'generated_at', 'next_pending_id'})
    assert {i: digest(rows[i]) for i in data['changed_inventory_ids']} == data['expected_row_digests']
    allowed = {'publication_quality_decision', 'updated_at', 'status', 'implementation_location', 'implementation_locations', 'cross_listing_approved', 'exclusion_reason', 'validation_status', 'processing_notes'}
    for rid in data['changed_inventory_ids']:
        assert {k for k in rows[rid] if rows[rid][k] != old[rid].get(k)} <= allowed, 'Source/provenance mutation'
    validate_affected_records([rows[i] for i in data['planning_publication_ids']])
    for rid in data['excluded_ids']:
        r = rows[rid]
        assert r['status'] == 'excluded' and not r['implementation_locations'] and r['implementation_location'] is None
        assert r['publication_quality_decision']['decision'] == 'excluded_from_publication'
        assert all(r[k] == old[rid][k] for k in ('source_url', 'direct_file_url', 'r2_url', 'checksum_sha256', 'size_bytes'))
    counts = Counter(r['status'] for r in rows.values())
    assert current['counts'] == {s: counts[s] for s in current['allowed_statuses']}
    pending = [r['id'] for r in rows.values() if r['status'] in {'pending review', 'approved for addition', 'downloaded', 'parsed', 'description drafted', 'placement assigned'} or r['status'] == 'implemented' and r.get('validation_status') != 'passed']
    assert current['next_pending_id'] == (min(pending) if pending else None)
    assert set(paths) == set(data['correction_pages']) and hashes == data['correction_page_sha256']
    assert r2_before == r2_after, 'R2 mutation is not authorized'

def guard_current_delta():
    stage = StageSnapshot('old-town-quality-correction')
    data = stage.load_json(ARTIFACT)
    assert data['baseline_commit'] == stage.stage['baseline_commit']
    baseline = data['baseline_commit']
    current = stage.load_json('project-state/master-inventory.json')
    args = ['git', 'diff', baseline] + ([stage.end] if stage.end else []) + ['--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml']
    paths = subprocess.check_output(args, cwd=ROOT, text=True).splitlines()
    if not stage.end:
        assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml'], cwd=ROOT).strip()
    hashes = {p: hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() for p in data['correction_pages']}
    validate_delta(data, before('project-state/master-inventory.json', baseline), current, paths, hashes, before('project-state/r2-inventory.json', baseline), stage.load_json('project-state/r2-inventory.json'))
    # The original twelve archive/public-byte witnesses remain complete and untouched.
    original = before('project-state/discovery/planning-documents-root-hugo-implementation-2026-09-26.json', baseline)
    assert set(data['planning_publication_ids']) == set(original['implemented_inventory_ids']) - {data['excluded_ids'][0]}
    assert len(data['planning_publication_ids']) == 11 and len(data['excluded_ids']) == 4
    assert set(data['pr_changed_pages']) == set(original['changed_pages']) | {'content/development-land-use/projects.md'}
    cumulative = subprocess.check_output(['git', 'diff', original['baseline_commit']] + ([stage.end] if stage.end else []) + ['--name-only', '--', 'content', 'layouts', 'assets', 'static', 'hugo.toml'], cwd=ROOT, text=True).splitlines()
    assert set(cumulative) == set(data['pr_changed_pages'])
    assert {p: hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() for p in data['pr_changed_pages']} == data['pr_page_sha256']
    old_queue = before('project-state/discovery/retained-source-audit-queue.json', baseline)
    new_queue = stage.load_json('project-state/discovery/retained-source-audit-queue.json')
    old = {r['source_url']: r for r in old_queue['records']}; new = {r['source_url']: r for r in new_queue['records']}
    h1_url = before('project-state/master-inventory.json', baseline)
    h1_url = next(r['source_url'] for r in h1_url['candidates'] if r['id'] == data['excluded_ids'][0])
    assert old.keys() - new.keys() == {h1_url} and not new.keys() - old.keys()
    assert all(new[u] == old[u] for u in new)
    assert all(new_queue[k] == old_queue[k] for k in old_queue if k not in {'records','counts','generated_at','next_pending_source_url'})
    counts = Counter(r['audit_status'] for r in new.values())
    assert new_queue['counts'] == {s: counts[s] for s in new_queue['allowed_statuses']}
    prior_review = before('project-state/discovery/consolidated-human-review-queue.json', baseline)
    current_review = stage.load_json('project-state/discovery/consolidated-human-review-queue.json')
    assert all(current_review[k] == prior_review[k] for k in prior_review if k != 'inventory_sha256')
    # Historical queue hashes were measured on Windows checkout bytes (CRLF).
    # Git snapshots store LF; reconstruct only those two checkout representations.
    inventory_bytes = canonical_bytes(stage.read_bytes('project-state/master-inventory.json'))
    assert current_review['inventory_sha256'] in {
        hashlib.sha256(inventory_bytes).hexdigest(),
        hashlib.sha256(inventory_bytes.replace(b'\n', b'\r\n')).hexdigest(),
    }
    assert stage.read_bytes('project-state/discovery/consolidated-human-review-queue.md') == subprocess.check_output(['git','show',baseline+':project-state/discovery/consolidated-human-review-queue.md'],cwd=ROOT)
    for p, expected in data['protected_correction_evidence'].items():
        assert hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() == expected, 'Quality evidence/debt witness changed'
    receipts = stage.load_json('project-state/discovery/old-town-quality-correction-2026-09-26/currentness-evidence.json')
    pdf = next(r for r in receipts['sources'] if r['saved_path'].endswith('.pdf'))
    actual_pdf = stage.read_bytes(pdf['saved_path'])
    assert len(actual_pdf) == pdf['size_bytes'] and hashlib.sha256(actual_pdf).hexdigest() == pdf['sha256'], 'Currentness PDF original bytes changed'
    rows = {r['id']: r for r in current['candidates']}
    texts = {p: stage.read_text(p) for p in data['pr_changed_pages']}
    for rid in data['excluded_ids']:
        assert all(rows[rid][k] not in t for t in texts.values() for k in ('r2_url', 'direct_file_url', 'source_url'))
    assert all('#old-town-regulatory-review' not in t and '#old-town-virtual-task-force-records' not in t for t in texts.values())
    return data
