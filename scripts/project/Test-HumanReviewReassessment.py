"""Independent population, provenance, disposition and archive audit for the owner task."""
import collections
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / 'project-state/discovery/human-review-reassessment-2026-09-26'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(r): return hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)

a = load(F / 'authorization.json')
prior = {r['id']: r for r in json.loads(git('show', a['baseline_commit'] + ':project-state/master-inventory.json').decode('utf-8-sig'))['candidates']}
inv = load(ROOT / 'project-state/master-inventory.json')
rows = {r['id']: r for r in inv['candidates']}
baseline = {r['id']: r for r in load(F / 'baseline-records.json')}
allowed = set(a['allowed_ids'])
assert len(allowed) == 205 and allowed == {i for i,r in prior.items() if r['status'] == 'requires human review'}
assert a['baseline_row_digests'] == {i:digest(r) for i,r in prior.items()}
assert rows.keys() == prior.keys() and baseline == {i:prior[i] for i in allowed}, 'Baseline must preserve exact Unicode and historical evidence'
assert {i for i in rows if rows[i] != prior[i]} <= allowed, 'Unrelated inventory changes'
d = load(F / 'decisions.json'); decisions = {r['id']:r for r in d['records']}
assert len(d['records']) == len(decisions) == 205 and decisions.keys() == allowed
for i in allowed:
    r,p = rows[i],prior[i]
    assert r['status'] == decisions[i]['status'], i
    for f in ['source_url','direct_file_url','discovery_path','cited_predecessors']: assert r.get(f) == p.get(f), (i,f)
    assert set(p['processing_notes']) <= set(r['processing_notes']), i
    if p.get('checksum_sha256'): assert r['checksum_sha256'] == p['checksum_sha256'], ('Historical hash changed',i)
    if r['status'] in ['approved for addition','placement assigned']:
        s = r['scope_assessment']; assert s['final_scope_decision'] == 'passes_both_gates'
        for k in ['geographic_institutional_scope','specific_albuquerque_connection','abqinfo_public_information_value','general_context_exclusion_test','substantive_rationale']: assert s[k], (i,k)
        if r['status'] == 'placement assigned' or str(r.get('direct_file_url') or '').lower().split('?')[0].endswith(('.pdf','.doc','.docx')):
            assert r['quality_assessment'], i
    if r['status'] == 'duplicate':
        c = rows[r['canonical_candidate_id']]
        assert r['checksum_sha256'] and (r['size_bytes'],r['checksum_sha256']) == (c['size_bytes'],c['checksum_sha256'])
owners = load(F / 'owner-packages.json')['packages']
owner_ids = [i for p in owners for i in p['affected_record_ids']]
assert len(owners) == 4 and len(owner_ids) == len(set(owner_ids)) == 11
assert set(owner_ids) == {i for i,r in rows.items() if r['status'] == 'requires human review'}
for p in owners:
    assert p['decision_question'] and p['why_owner_judgment_required'] and len(p['options']) >= 2
    for i in p['affected_record_ids']: assert rows[i]['review_reason'] == p['decision_kind']
follow = load(ROOT / 'project-state/discovery/codex-human-review-followup-queue.json')
work = {r['id'] for r in follow['records']}
assert len(work) == len(follow['records']) == follow['record_count'] == 55
assert work == {i for i,r in decisions.items() if r['outcome_class'] == 'work_prerequisite'}
for r in follow['records']:
    assert rows[r['id']]['status'] == 'pending review' and r['research_authorized'] and not r['owner_decision_required']
    assert r['required_evidence'] and r['recovery_evidence']
summary = load(F / 'summary.json')
assert summary['final_status_counts'] == dict(collections.Counter(rows[i]['status'] for i in allowed))
assert summary['fully_dispositioned_automatically'] == 139 and summary['research_prerequisites'] == 55 and summary['genuine_owner_records'] == 11
assert summary['obsolete_human_gates_removed'] == 194 and 139+55+11 == 205
scope = load(ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json')
assert scope['unresolved_count'] == 1 and rows['src-333e4b4b3970edc1']['review_reason'] == 'mission_scope_borderline'
for r in load(F / 'fbz-comparison.json'):
    assert rows[r['id']]['status'] == 'superseded' and r['old_pages'] == r['new_pages']
    assert r['changes'] and all(x == {'op':'replace','old':'04 02 09 draft','new':'final'} for x in r['changes'])
old = load(F / 'r2-baseline.json'); final = load(F / 'r2-final.json'); current = load(ROOT / 'project-state/r2-inventory.json')
objects = {o['key']:o for o in final['objects']}; original = {o['key']:o for o in old['objects']}
assert {o['key']:o for o in current['objects']} == objects and current['total_bytes'] == final['total_bytes']
for k,o in original.items(): assert (objects[k]['size_bytes'],objects[k]['etag']) == (o['size_bytes'],o['etag']), k
receipts = load(F / 'archive-receipts.json')
assert len(receipts) == 3 and objects.keys()-original.keys() == {r['key'] for r in receipts}
assert sum(r['size_bytes'] for r in receipts) == final['total_bytes']-old['total_bytes'] == summary['r2_added_bytes'] == 381871978
assert final['total_bytes'] == sum(o['size_bytes'] for o in objects.values()) == summary['r2_final_bytes'] == 10670960837 <= a['maximum_storage_bytes'] == 13000000000
assert len(objects) == final['object_count'] == 1588 and len({k.casefold() for k in objects}) == len(objects)
for r in receipts:
    v = r['public_verification']; row = rows[r['id']]
    assert r['key_was_absent'] and r['state'] == 'inventory_reconciled' and v['byte_identical']
    assert 0 < r['size_bytes'] <= a['maximum_object_bytes'] == 150000000
    assert (v['size_bytes'],v['checksum_sha256']) == (r['size_bytes'],r['checksum_sha256']) == (row['size_bytes'],row['checksum_sha256'])
    assert row['r2_key'] == r['key'] and row['status'] == 'placement assigned' and objects[r['key']]['etag'] == r['etag']
    source = ROOT / row['local_path']; assert source.stat().st_size == r['size_bytes']
    with source.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest() == r['checksum_sha256']
assert not git('diff',a['baseline_commit'],'--name-only','--','content').strip()
assert git('rev-parse','HEAD:content').decode().strip() == a['content_tree']
assert not git('ls-files','--others','--exclude-standard','content').strip()
cp = load(ROOT / 'project-state/checkpoint.json'); assert cp['counts_by_status'] == inv['counts']
queue = load(ROOT / load(ROOT / 'project-state/ordinary-queue-current.json')['artifact'])
pending = {i for i,r in rows.items() if r['status'] == 'pending review'}
assert pending == set(queue['pending_ids']) and work <= set(queue['source_or_structural_blocked_pending_ids'])
assert len(pending) == queue['pending_review_count'] == 388 and queue['mission_borderline_queue_size'] == 1
print('PASS: exact 205-record reassessment; 139 dispositions, 55 work prerequisites, 11 owner decisions; unrelated rows/source history/content preserved; three exact archives and 13 GB ceiling.')
