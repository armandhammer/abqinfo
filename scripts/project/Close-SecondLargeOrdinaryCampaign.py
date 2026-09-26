#!/usr/bin/env python3
"""Close the quiescent campaign from receipts, without changing any candidate."""
import collections, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / 'project-state/discovery'
DATE = '2026-09-26'
ART = DISC / f'ordinary-queue-second-large-resolution-campaign-{DATE}.json'
QUEUE = DISC / f'ordinary-queue-next-position-post-second-large-campaign-{DATE}.json'
SEAL = DISC / f'ordinary-second-large-campaign-population-lock-{DATE}.json'

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def save(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def main():
    now = datetime.now(timezone.utc).isoformat()
    campaign = load(ART)
    inv = load(ROOT / 'project-state/master-inventory.json')
    rows = {r['id']: r for r in inv['candidates']}
    r2 = load(ROOT / 'project-state/r2-inventory.json')
    health = load(DISC / f'second-large-campaign-archive-health-{DATE}.json')
    live = load(ROOT / health['live_listing_artifact'])
    assert r2['objects'] == live['objects']
    assert health['summary']['second_campaign'] == len(campaign['archive_objects'])
    assert health['state'] == 'complete_for_recorded_population'
    assert len(campaign['resolved_records']) == 700
    resolved = {r['id']: r for r in campaign['resolved_records']}
    records = {}
    for f in campaign['families_processed']:
        for r in load(ROOT / f['artifact'])['records']:
            if r.get('review_complete'):
                assert r['id'] not in records
                records[r['id']] = r
    assert records.keys() == resolved.keys()
    old_queue = load(DISC / f'ordinary-queue-next-position-post-large-campaign-{DATE}.json')
    selection = load(ROOT / campaign['selection_artifact'])
    pending = {i for i, r in rows.items() if r['status'] == 'pending review'}
    gates = {i: reason for i, reason in old_queue['gated_pending_ids'].items() if i in pending}
    protected_families = {
        'family-043': 'Protected PGS enactment-bill delivery; existing finality/human gate remains authoritative.',
        'family-051': 'Explicitly protected LGCC delivery; do not reopen its completed review.',
        'family-116-12': 'Completed later-MS4 programme components; preservation only, no reopening.',
        'family-116-14': 'Completed Municipal Development Energy Council meeting series; no reopening.',
        'family-127': 'Form Based Zones revision/component family intersects existing human-held src-05176d26d35effd3; bounded version/finality review prerequisite.',
        'family-147': 'Sawmill version family names pending canonical src-96e192e3bb793470, already held by saved adoption/finality recommendation; no automatic application.',
    }
    for f in selection['candidate_families']:
        if f['family_id'] in protected_families:
            for i in f['candidate_ids']:
                if i in pending:
                    gates[i] = protected_families[f['family_id']]
    blocked = {i: 'Existing encrypted/repaired San Pedro source problem; no new decisive evidence.' for i in selection['structural_blocked_ids'] if i in pending}
    blocked['src-2f89e1bc040e1d33'] = 'Fresh preparer stopped on application-shell/saved-evidence mismatch (KeyError exclusion_reason), not a failed PDF. Saved owner retrieval is 321 pages/11940327 bytes; recover its original and independently verify delivery using file-share-retrieval-research-2026-09-14.json. No disposition applied.'
    blocked['src-e63d4ebb9302ec96'] = 'Annual-report landing delivery was NOT RETRIEVED by saved preparation; recover current authoritative original before review.'
    blocked = {i: why for i, why in blocked.items() if i in pending and i not in gates}
    ungated = pending - gates.keys() - blocked.keys()
    family_groups = []
    for f in selection['candidate_families']:
        ids = sorted(set(f['candidate_ids']) & ungated)
        if ids:
            p = DISC / f"ordinary-second-large-campaign-{f['family_id']}-{DATE}.json"
            family_groups.append({'family_id': f['family_id'], 'family': f['family'], 'candidate_ids': ids, 'candidate_count': len(ids), 'saved_preparation_artifact': p.relative_to(ROOT).as_posix() if p.exists() else None, 'selection_is_not_a_disposition': True})
    top_ids = ['family-121', 'family-116-08', 'family-152-08', 'family-116-06', 'family-143', 'family-089']
    priority_reasons = [
        'Thirteen coherent EDAct meeting notices/agendas in Word; full format-specific review and complete minutes/cancellation checks before any retention.',
        'Four on-call design procurement forms/templates, plus related delivery aliases; apply current transactional-form precedent after full-file inspection.',
        'Five MRCOG grant forms/templates plus delivery alias; scope depends on actual contents, never on regional host.',
        'Two local public-works project presentations; inspect complete slides and distinguish project information from promotional photographs.',
        'North Diversion Channel long/brief Word records and one board agenda; verify full content and series before placement.',
        'City map service family; evaluate actual live data/function and documentary value, without visitor-visible implementation.',
    ]
    top = []
    for i, reason in zip(top_ids, priority_reasons):
        group = next((f for f in family_groups if f['family_id'] == i), None)
        if group:
            top.append({**group, 'next_review_requirement': reason})
    archived_ids = {o['id'] for o in campaign['archive_objects']}
    deferrals = []
    for i, x in resolved.items():
        x['current_status'] = rows[i]['status']
        if x['decision'] == 'approved for addition' and i not in archived_ids:
            r = records[i]
            reason = r.get('archive_deferred_reason') or r.get('archive_operation_error')
            assert reason, ('Unattempted approval', i)
            q = r['fresh_source_qa']
            assert q['source_exact_verified'] and r['mission_scope_assessment']['final_scope_decision'] == 'passes_both_gates'
            assert r['r2_key'] and r['proposed_canonical_page']
            deferrals.append({'id': i, 'title': rows[i]['title'], 'reason': reason, 'size_bytes': q['size_bytes'], 'checksum_sha256': q['checksum_sha256'], 'prepared_key': r['r2_key'], 'canonical_page': r['proposed_canonical_page'], 'evidence_artifact': x['evidence_artifact'], 'preparation_complete': True, 'status': rows[i]['status']})
    qa = [r['fresh_source_qa'] for r in records.values()]
    stats = {'resolved_records': 700, 'outcomes': dict(collections.Counter(x['decision'] for x in resolved.values())), 'families_with_applied_dispositions': len(campaign['families_processed']), 'completed_families': sum(f['complete'] for f in campaign['families_processed']), 'partially_completed_families': sum(not f['complete'] for f in campaign['families_processed']), 'source_files_reviewed': len(qa), 'static_source_files_reviewed': sum(q['container'] != 'HTML' for q in qa), 'source_bytes_reviewed': sum(q['size_bytes'] for q in qa), 'pages_analyzed': sum(q.get('page_count') or 0 for q in qa), 'pages_rendered': sum(q.get('rendered_pages') or 0 for q in qa), 'containers': dict(collections.Counter(q['container'] for q in qa)), 'HTML_live_navigation_exclusions': sum(r['disposition'] == 'excluded' and r['fresh_source_qa']['container'] == 'HTML' for r in records.values()), 'mission_scope_exclusions': sum(r['disposition'] == 'excluded' and r['mission_scope_assessment']['final_scope_decision'] == 'excluded' for r in records.values()), 'new_human_review_cases': 0, 'new_mission_borderline_cases': 0, 'archive_objects_added': len(archived_ids), 'archive_bytes_added': sum(o['size_bytes'] for o in campaign['archive_objects']), 'placement_assigned_transitions': len(archived_ids), 'capacity_deferred_approvals': sum('only storage capacity' in r['reason'] for r in deferrals), 'object_size_deferred_approvals': sum('exceeds 150000000' in r['reason'] for r in deferrals), 'other_archive_deferred_approvals': sum('only storage capacity' not in r['reason'] and 'exceeds 150000000' not in r['reason'] for r in deferrals)}
    hard = load(DISC / f'inventory-legacy-relationship-hardening-{DATE}.json')
    campaign.update({'state': 'complete_background_campaign', 'completed_at': now, 'accounting': stats, 'archive_deferrals': deferrals, 'capacity_deferrals': [r for r in deferrals if 'only storage capacity' in r['reason']], 'source_or_structural_failures': blocked, 'deferred_records': [{'id': i, 'reason': gates.get(i) or blocked.get(i) or 'Not selected for additional disposition after the hard cap; independent full-format/live-service/version review remains necessary.'} for i in sorted(pending - set(selection['gated_pending_ids']))], 'legacy_relationship_hardening_artifact': f'project-state/discovery/inventory-legacy-relationship-hardening-{DATE}.json', 'legacy_relationship_results': hard['summary'], 'archive_health_artifact': f'project-state/discovery/second-large-campaign-archive-health-{DATE}.json', 'archive_health_summary': health['summary'], 'final_inventory_counts': inv['counts'], 'latest_r2': {'object_count': r2['object_count'], 'total_bytes': r2['total_bytes'], 'remaining_headroom_bytes': 10000000000 - r2['total_bytes']}, 'final_live_listing_artifact': health['live_listing_artifact'], 'next_queue_artifact': QUEUE.relative_to(ROOT).as_posix(), 'stop_reason': '700 formerly-pending hard cap reached; no additional pending dispositions permitted.', 'zero_content_change': True, 'visitor_visible_content_changed': False, 'live_site_published': False})
    queue = {'schema_version': 1, 'artifact_type': 'ordinary_queue_record_level_post_second_large_campaign', 'recorded_at': now, 'baseline_commit': campaign['baseline_commit'], 'pending_review_count': len(pending), 'pending_ids': sorted(pending), 'gated_pending_count': len(gates), 'gated_pending_ids': gates, 'source_or_structural_blocked_pending_count': len(blocked), 'source_or_structural_blocked_pending_ids': blocked, 'ungated_pending_count': len(ungated), 'ungated_pending_ids': sorted(ungated), 'mission_borderline_queue_size': 0, 'newly_approved_backlog': deferrals, 'archived_placement_backlog': [{'id': i, 'canonical_page': rows[i]['proposed_canonical_page'], 'key': rows[i]['r2_key']} for i in sorted(archived_ids)], 'existing_ia_blocked_approved_ids': old_queue['existing_ia_blocked_approved_ids'], 'background_family_groups': family_groups, 'next_actionable_background_families': top, 'next_actionable_background_family': top[0] if top else None, 'selection_caveat': 'Ungated means eligible for bounded background investigation, not preapproved or all high confidence. Format conversion, live-service evaluation and chronology checks are still required. Do not reopen protected groups or begin visitor-visible implementation. Storage ceiling prevents most additional original archival.', 'visitor_visible_content_changed': False}
    assert len(pending) == len(gates) + len(blocked) + len(ungated) == 412
    population = [{'id': i, 'decision': resolved[i]['decision'], 'family_id': resolved[i]['family_id'], 'source_size_bytes': records[i]['fresh_source_qa']['size_bytes'], 'source_sha256': records[i]['fresh_source_qa']['checksum_sha256'], 'canonical_candidate_id': records[i].get('canonical_candidate_id')} for i in sorted(resolved)]
    lifecycle = [{'id': i, 'status': rows[i]['status'], 'r2_key': rows[i]['r2_key'], 'checksum_sha256': rows[i]['checksum_sha256'], 'size_bytes': rows[i]['size_bytes']} for i in sorted(resolved)]
    lock = {'schema_version': 1, 'population': population, 'population_sha256': digest(population), 'final_lifecycle': lifecycle, 'final_lifecycle_sha256': digest(lifecycle), 'archive_population': [{'id': o['id'], 'key': o['key'], 'sha256': o['checksum_sha256'], 'size_bytes': o['size_bytes']} for o in sorted(campaign['archive_objects'], key=lambda o: o['id'])], 'legacy_changed_ids': hard['changed_ids'], 'content_tree': campaign['content_tree_baseline']}
    campaign['population_lock_artifact'] = SEAL.relative_to(ROOT).as_posix()
    campaign['validation'] = {'state': 'awaiting_full_project_validation', 'required': ['full_project_validation', 'focused_archive_health', 'git_diff_check', 'zero_content_changes']}
    save(QUEUE, queue)
    save(SEAL, lock)
    save(ART, campaign)
    print(json.dumps({'accounting': stats, 'queue': {k: queue[k] for k in ['pending_review_count', 'gated_pending_count', 'source_or_structural_blocked_pending_count', 'ungated_pending_count']}, 'r2': campaign['latest_r2'], 'population_sha256': lock['population_sha256'], 'lifecycle_sha256': lock['final_lifecycle_sha256']}))

if __name__ == '__main__':
    main()
