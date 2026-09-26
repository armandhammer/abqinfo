"""Build a read-only decision queue from current inventory and tracked evidence.

No source retrieval, disposition changes, storage operations, or content edits.
Run with --check to verify exact regeneration and complete, exclusive coverage.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'project-state/discovery/consolidated-human-review-queue.json'
REPORT = OUT.with_suffix('.md')
INVENTORY = ROOT / 'project-state/master-inventory.json'


def package(key, title, question, options):
    return dict(package_id=key, title=title, decision_question=question,
                options=[dict(option=a, consequence=b) for a, b in options], records=[])


RESEARCH = [('Authorize targeted research', 'Recover exact official evidence, then reassess scope, quality and family relationships; no approval or publication is implied.'),
            ('Keep on hold', 'Preserve the unresolved gate and existing evidence.'),
            ('Request exclusion review', 'Evaluate a documented exclusion through the normal inventory workflow; this queue changes no disposition.')]


def classify(r):
    t = r['title'].lower()
    s = r.get('validation_status') or ''
    url = (r.get('source_url') or '') + ' ' + (r.get('parent_url') or '')
    ids = r['id']
    if ids == 'src-05b68a5758490499':
        return package('fiber-correspondence', 'Fiber rulemaking correspondence: privacy and presentation',
                       'Should resident correspondence be retained in full, redacted, or represented by a summary?',
                       [('Full original', 'Requires an explicit owner privacy decision and separate archive/publication authorization.'),
                        ('Redacted derivative or summary', 'Requires an authorized redaction/editorial stage, provenance and clear distinction from the original.'),
                        ('Keep on hold', 'No new archive or visible entry; public-record value and privacy remain unresolved.')])
    if 'form based' in t or 'fbz part' in t:
        return package('form-based-zones', 'Form Based Zones: complete historical legal package', 'Authorize resolution of all three final parts and enactment evidence, or retain the hold? Parts must not be published independently as a complete enacted code.', RESEARCH)
    if 'enacted ordinance not located' in s:
        return package('pgs-enactments', 'Planned Growth Strategy: three enactment instruments', 'How should the three blank-enactment bills be handled pending authoritative final ordinances? Resolve together; do not infer passage from the published strategy.', RESEARCH)
    if 'station-area planning draft' in t:
        return package('central-station-drafts', 'Central Avenue station-area drafts: provenance and complete family', 'Authorize exact official-source reconciliation for the complete draft family, or keep it held? Existing archive verification does not establish government provenance or adoption.', RESEARCH)
    if any(w in t for w in ['art design comments', 'coalition response', 'summary of art meeting', 'impact of transit', 'scale of the prize', 'art corridor building']):
        return package('art-supporting-records', 'ART supporting studies and engagement records', 'Authorize provenance and authorship review of this supporting ART family, with separate treatment of advocacy/commentary and official studies?', RESEARCH)
    if 'published archive placement' in s:
        if 'data dictionary' in t:
            return package('regional-data-provenance', 'Regional data dictionary: exact source and public value', 'Authorize exact government-source recovery and a separate assessment of the data dictionary\'s substantive Albuquerque public-information value?', RESEARCH)
        return package('regional-archived-provenance', 'Regional climate and data PDFs: exact source provenance', 'Authorize recovery of exact government-hosted originals for the three archived regional records, followed by a material Albuquerque scope review?', RESEARCH)
    if any(w in t for w in ['girard streetscape', 'buena vista bike', '2014 bikeways', '2024 bikeway', 'bike boulevards']):
        return package('contributed-bike-provenance', 'Contributed bicycle plans and designs: official original identity', 'Authorize exact-source recovery and comparison for these contributed bicycle records? Preserve draft/annotated labels and do not equate R2 identity with official provenance.', RESEARCH)
    if any(w in t for w in ['development process manual', 'dpm ', 'chapter 7 dpm', 'draft construction stormwater', 'section-3-9-7', 'development-process-manual']):
        return package('dpm-drafts-meetings', 'DPM amendments, drafts and committee records', 'Authorize a family review of adoption evidence and minutes availability? Preserve proposed text as draft; agenda retention requires exhaustive approved-minutes search and cancellation/no-quorum checks.', RESEARCH)
    if 'trails' in t and ('agenda' in t or 'pid' in t):
        return package('trails-pid-agendas', 'Trails PID agenda series', 'Should this agenda series undergo the missing-minutes policy review as a coherent meeting family before any retention decision?', RESEARCH)
    if any(w in t for w in ['lewis ', 'o0835', 'r-09-1']):
        return package('district-five-legislation', 'District 5 pre-enactment legislation and supporting exhibit', 'Resolve the five held District 5 files together, treating the three F/S R-10-58 deliveries as one instrument. Authorize final-enactment recovery, or retain the hold?', RESEARCH)
    if 'legislative reconciliation: final disposition unresolved' in s:
        return package('final-action-' + ids, r['title'] + ': final action', 'Authorize further final-action recovery after the documented deep review, or leave this substitute held? No adoption may be inferred from postponements or later related activity.', RESEARCH)
    if any(w in t for w in ['floor substitute', 'committee substitute', 'floor amendment', 'f/s r-', 'regulatory plan', 'huning highland railroad']):
        return package('council-legal-versions', 'Council substitutes, amendments and enacted package relationships', 'Authorize final-action and canonical-package reconciliation? Judge final legal status and standalone value separately; blank enactment fields and partial exhibits cannot prove enactment.', RESEARCH)
    if any(w in t for w in ['streets summary', 'senior affairs', 'family and community services summary', 'bond scopes', 'impact fee committee']):
        return package('capital-components', 'Capital program excerpts and impact-fee recommendations', 'Should these excerpts and recommendations be retained within complete program records, reviewed for independent historical value, or left held?', [('Review complete program families', 'Compare full bond/CIP and impact-fee records; avoid fragmentary standalone entries.'), *RESEARCH[1:]])
    if ids in ['src-a738fd67bc6abac6', 'src-c7fcd58b9998999c', 'src-4996854ae4e1a349']:
        return package('archive-authority-' + ids, r['title'] + ': archive authorization', 'Authorize a new bounded archive stage for this protected record, or retain the hold? The later 150 MB campaign limit did not admit protected human-review records or resolve their historical authorization gate.', [('Authorize bounded preflight', 'Recheck mission scope, quality, exact original size, storage ceiling and current explicit upload authority before any upload; publication remains separate.'), ('Keep on hold', 'No storage added and no public-content change.')])
    if 'bernco.gov' in url or 'Bernalillo County provenance' in s:
        if 'technical standards' in t:
            return package('bernco-standards-page', 'County technical standards landing page: canonical relationship', 'Authorize recovery and comparison of this held landing page with the already archived complete standards, before deciding whether it adds independent value?', RESEARCH)
        if 'luna properties' in t:
            return package('luna-environmental-family', 'Luna Properties environmental evaluation: draft and parent family', 'Authorize official-source recovery and comparison of the draft evaluation with its project page, preserving draft/finality uncertainty?', RESEARCH)
        if 'public information requests' in t:
            return package('county-records-service', 'County public-information request service', 'Authorize current-service recovery and usefulness review of this request portal?', RESEARCH)
        if '/wp-content/' in url or 'gantt' in t or 'gannt' in t or 'traffic ' in t:
            return package('bernco-project-attachments', 'County construction notices, maps and schedules: recovery policy', 'Authorize recovery and parent-project comparison of County attachments, or keep them held? Review as project components, not a bulk standalone publication batch.', RESEARCH)
        return package('bernco-project-pages', 'County public-works project pages: access and historical curation', 'Authorize targeted official-source recovery for blocked County project pages and review of project-level public value? Failed access alone is neither exclusion nor approval.', RESEARCH)
    if any(w in t for w in ['accessible agenda', 'minutes']) or t == 'agenda' or t == 'april 16, 2026':
        return package('council-meeting-recovery', 'Council meeting records: broken delivery links', 'Authorize exact meeting-ID/GUID recovery and duplicate comparison? Agendas require the standing missing-minutes and cancellation checks.', RESEARCH)
    if 'dot.nm.gov' in url or 'realfile' in url or 'nmdot' in t or 'web map' in t:
        return package('nmdot-recovery-scope', 'NMDOT links, forms, maps and shuttle records', 'Authorize a targeted recovery and substantive Albuquerque relevance review? Statewide tools, forms, phone-link artifacts and Santa Fe services must not gain eligibility merely through recovery.', RESEARCH)
    if 'riometro' in url or any(w in t for w in ['rail runner', 'train service', 'bus operations']):
        return package('regional-transit-recovery', 'Regional transit pages, service notices and FAQs', 'Authorize successor/current-service and Albuquerque-value review, or retain these failed-link gates? Expired notices and isolated FAQs may not deserve separate entries.', RESEARCH)
    if ids in ['src-0eb2bcba2848b4dd', 'src-ea9839282b301e5f']:
        return package('unreconciled-staging', 'Unreconciled staged documents', 'Authorize provenance recovery for the staged transportation-process document and missing EC-175 file? EC-175 must not be conflated with the distinct validated parking study.', RESEARCH)
    # Individually material issues should remain discrete decision packages.
    questions = {
        'lin-2f6fbe4ffb0b6564': 'Authorize recovery of the referenced Bike Gap Closure study, or retain the unavailable-source hold?',
        'lin-7bdbcdc09efe2035': 'Authorize reconciliation of conflicting adopted/draft references and recovery of the San Antonio Arroyo plan?',
        'src-352d880cb11386d3': 'Authorize recovery of the original 2004 Progress Report beyond the saved sign-in redirect?',
        'src-395957636cb2fed0': 'Authorize recovery of the authoritative 1993 plan original while preserving its documented 2015 repeal?',
        'src-158f843cc102a40f': 'Authorize title/source reconciliation for Volcano Park versus the recorded Huning Castle/Raynolds plan path?',
        'src-1f0f860a2332e181': 'Authorize comparison of the broken Sign Posting Agreement with the newer 2024 form rather than infer replacement?',
    }
    if ids in questions:
        return package('recovery-' + ids, r['title'] + ': source/status recovery', questions[ids], RESEARCH)
    if ids == 'src-333e4b4b3970edc1':
        return package('wireless-checklist', 'Wireless facility checklist: version and independent value', 'Authorize version comparison with the final wireless rules and application materials before deciding whether this staff checklist has independent public value?', RESEARCH)
    if s == 'not run':
        return package('frozen-editorial-' + ids, r['title'] + ': renewed editorial review', 'Authorize renewed review of this record formerly held outside the frozen batch? Saved potential usefulness is not a current positive mission-scope or publication decision.', RESEARCH)
    if 'autonomous campaign' in s:
        if 'ahymo' in t:
            return package('ahymo-model', 'AHYMO model: recovery and technical public value', 'Authorize source recovery and review of whether this hydrology model delivery materially informs Albuquerque public infrastructure rather than merely technical operations?', RESEARCH)
        return package('city-service-link-recovery', 'City service and institutional links: recovery and usefulness', 'Authorize recovery and current-service comparison for failed City/institutional links? Decide whether each is a substantive public-information source rather than an incidental service or event link.', RESEARCH)
    raise ValueError('Unclassified human gate: ' + ids + ' ' + t)


def build():
    raw = INVENTORY.read_bytes()
    rows = sorted((r for r in json.loads(raw.decode('utf-8-sig'))['candidates'] if r['status'] == 'requires human review'), key=lambda r: r['id'])
    ids = {r['id'] for r in rows}
    evidence = {i: [] for i in ids}
    tracked = subprocess.check_output(['git', 'ls-files', 'project-state', 'research'], cwd=ROOT, text=True).splitlines()
    for name in tracked:
        if name == 'project-state/master-inventory.json' or 'consolidated-human-review' in name or '/campaigns/' in name or not name.endswith(('.json', '.md')):
            continue
        # Evidence lookup only; never derive membership from historical artifacts.
        body = (ROOT / name).read_text(encoding='utf-8-sig', errors='replace')
        hits = set(re.findall(r'(?:src|lin)-[0-9a-f]{16,20}', body)) & ids
        for i in hits:
            evidence[i].append(name)
    groups = {}
    for r in rows:
        p = classify(r)
        p = groups.setdefault(p['package_id'], p)
        e = sorted(evidence[r['id']], key=lambda n: (not any(w in n for w in ['research', 'decision', 'reconciliation', 'review']), len(n), n))
        notes = r.get('processing_notes', [])
        record = {k: r.get(k) for k in ['id', 'title', 'status', 'source_url', 'direct_file_url', 'parent_url', 'r2_url', 'r2_key', 'size_bytes', 'checksum_sha256', 'local_path', 'implementation_locations', 'scope_assessment', 'quality_assessment']}
        stop = r.get('exclusion_reason') or r.get('validation_status') or 'See saved processing notes'
        if stop == 'not run':
            stop = next((n for n in notes if any(w in n.lower() for w in ['frozen batch', 'held outside', 'future review', 'future human review', 'retain for future'])), 'Saved review remains incomplete; see processing notes and research artifact.')
        record.update(saved_validation_status=r.get('validation_status'), saved_exclusion_reason=r.get('exclusion_reason'), saved_processing_notes=notes,
                      evidence_artifacts=e, automation_stop=stop,
                      evidence_gap=None if e else 'No separate tracked ID-bearing research artifact located; authoritative inventory notes and discovery paths are the saved evidence.',
                      discovery_path=r.get('discovery_path', []))
        p['records'].append(record)
    packages = sorted(groups.values(), key=lambda p: p['package_id'])
    for p in packages:
        p['record_count'] = len(p['records'])
        p['affected_record_ids'] = [r['id'] for r in p['records']]
        p['why_automation_stopped'] = sorted({r['automation_stop'] for r in p['records']})
        p['evidence_artifacts'] = sorted({e for r in p['records'] for e in r['evidence_artifacts']})
        p['decision_state'] = 'awaiting_owner_decision'
    scope = json.loads((ROOT / 'project-state/discovery/mission-scope-borderline-human-review-queue.json').read_text(encoding='utf-8-sig'))
    result = dict(schema_version=1, artifact_type='consolidated_human_review_decision_queue', recorded_at='2026-09-26',
                  inventory_sha256=hashlib.sha256(raw).hexdigest(), record_count=len(rows), package_count=len(packages),
                  membership_rule='All and only current inventory candidates with status requires human review, exactly once.',
                  authority='Owner requested queue construction and normal background integration only. Options are proposals, not decisions or external-action authority.',
                  link_policy='Saved links only; not live-verified by this task. Null means no link recorded, not proof of absence. R2 availability does not establish official provenance.',
                  refresh_command='python scripts/project/Build-ConsolidatedHumanReviewQueue.py',
                  mission_scope_queue=dict(path='project-state/discovery/mission-scope-borderline-human-review-queue.json', unresolved_count=scope['unresolved_count'], role='Exclusive operational queue for scope-borderline cases; this consolidated view does not replace or populate it.'),
                  excluded_from_this_queue='Pending records, approved archive/architecture blockers and other statuses are not human-review membership. No historical resolved family is reopened.',
                  packages=packages)
    lines = ['# Consolidated ABQInfo human-review decision queue', '', f"Snapshot: 2026-09-26 — **{len(rows)} records in {len(packages)} decision packages**.", '',
             'Choose a package and an option; identify exceptions by record ID. These are proposed decisions only. Applying a decision requires a separately authorized, validated inventory stage. Archival and visible publication retain their own gates.', '',
             'All membership comes from current `requires human review` status. Historical evidence explains holds and may be superseded. Links are saved references, not fresh reachability checks. R2 verification does not resolve official provenance. No inventory, R2 or content changes were made.', '',
             f"The exclusive mission-scope borderline queue has {scope['unresolved_count']} unresolved records; it remains unchanged. Pending live-service prerequisites and approved architecture blockers are outside this queue.", '',
             'Regenerate with `python scripts/project/Build-ConsolidatedHumanReviewQueue.py`; validate freshness and coverage with `--check`.', '', '## Decision index', '', '| Package | Records |', '| --- | ---: |']
    for p in packages:
        lines.append(f"| [{p['title']}](#{p['package_id']}) | {p['record_count']} |")
    for p in packages:
        lines += ['', f"<a id=\"{p['package_id']}\"></a>", '', '## ' + p['title'], '', '**Decision:** ' + p['decision_question'], '', '**Options and consequences:**', '']
        lines += [f"- **{o['option']}:** {o['consequence']}" for o in p['options']]
        lines += ['', '**Affected records and saved evidence:**', '']
        for r in p['records']:
            lines += [f"### {r['title']} — `{r['id']}`", '', '**Automation stopped:** ' + str(r['automation_stop']), '']
            # Show meaningful saved research notes without hiding the machine-readable full record.
            substantive = [n for n in r['saved_processing_notes'] if not any(n.startswith(w) for w in ['Discovered by', 'Downloaded exact', 'Exact metadata', 'Enumerated without', 'Original source file uploaded', 'Parallel verification', 'Public R2 download'])]
            lines += [f'- Saved finding: {n}' for n in substantive[-3:]]
            links = [(k, r[k]) for k in ['source_url', 'direct_file_url', 'parent_url', 'r2_url'] if r[k]]
            lines += [f"- {k.replace('_', ' ')}: [saved link](<{u}>)" for k, u in links]
            if not links:
                lines += ['- No source/archive link recorded; see saved lineage and provenance evidence.']
            lines += [f'- Evidence: [{e}](../../{e})' for e in r['evidence_artifacts'][:6]]
            if len(r['evidence_artifacts']) > 6:
                lines += ['- Additional ID-bearing evidence references are listed in the JSON queue.']
            if r['evidence_gap']:
                lines += ['- Evidence gap: ' + r['evidence_gap']]
            lines += ['']
    return result, '\n'.join(lines).rstrip() + '\n'


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--check', action='store_true')
    opts = args.parse_args()
    result, report = build()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    flat = [i for p in result['packages'] for i in p['affected_record_ids']]
    assert len(flat) == len(set(flat)) == result['record_count']
    if opts.check:
        assert OUT.read_text(encoding='utf-8') == payload, 'JSON queue is stale'
        assert REPORT.read_text(encoding='utf-8') == report, 'Markdown queue is stale'
    else:
        OUT.write_text(payload, encoding='utf-8', newline='\n')
        REPORT.write_text(report, encoding='utf-8', newline='\n')
    print(json.dumps(dict(result='passed', records=result['record_count'], packages=result['package_count'], mode='check' if opts.check else 'build')))


if __name__ == '__main__':
    main()
