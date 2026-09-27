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


CATALOG = ROOT / 'project-state/discovery/human-review-reassessment-2026-09-26/owner-packages.json'


def classify(r):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    matches = [p for p in catalog['packages'] if r['id'] in p['affected_record_ids']]
    if len(matches) != 1:
        raise ValueError('Human-review row lacks one concrete owner-decision package: ' + r['id'])
    p = matches[0]
    if r.get('review_reason') != p['decision_kind']:
        raise ValueError('Owner-decision kind differs from current inventory: ' + r['id'])
    result = package(p['package_id'], p['title'], p['decision_question'],
                     [(o['option'], o['consequence']) for o in p['options']])
    result['decision_kind'] = p['decision_kind']
    result['why_owner_judgment_required'] = p['why_owner_judgment_required']
    return result


def build():
    raw = INVENTORY.read_bytes()
    rows = sorted((r for r in json.loads(raw.decode('utf-8-sig'))['candidates'] if r['status'] == 'requires human review'), key=lambda r: r['id'])
    ids = {r['id'] for r in rows}
    evidence = {i: [] for i in ids}
    tracked = subprocess.check_output(['git', 'ls-files', 'project-state', 'research'], cwd=ROOT, text=True).splitlines()
    for name in tracked:
        # This task preserves owner packages; its baseline copies and whole-row
        # digest manifests are bookkeeping, not new owner-decision evidence.
        if name.startswith('project-state/discovery/background-followup-2026-09-26/'):
            continue
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
                  authority='Owner-invoked policy reassessment separated factual research from genuine privacy/editorial choices. Current unresolved choices only; completed owner decisions are recorded in owner-decisions-2026-09-26/authorization.json when present.',
                  link_policy='Saved links only; not live-verified by this task. Null means no link recorded, not proof of absence. R2 availability does not establish official provenance.',
                  refresh_command='python scripts/project/Build-ConsolidatedHumanReviewQueue.py',
                  mission_scope_queue=dict(path='project-state/discovery/mission-scope-borderline-human-review-queue.json', unresolved_count=scope['unresolved_count'], role='Exclusive operational queue for scope-borderline cases; this consolidated view does not replace or populate it.'),
                  excluded_from_this_queue='Pending records, approved archive/architecture blockers and other statuses are not human-review membership. No historical resolved family is reopened.',
                  packages=packages)
    lines = ['# Consolidated ABQInfo human-review decision queue', '', f"Snapshot: 2026-09-26 — **{len(rows)} records in {len(packages)} decision packages**.", '',
             'This queue contains only genuine owner privacy/editorial decisions. Source recovery, family reconciliation, minutes searches and finality prerequisites are Codex work in `codex-human-review-followup-queue.json`. Completed owner choices are preserved in their dated decision artifact; this queue contains only unresolved choices. Visible publication retains manual review.', '',
             'All membership comes from current `requires human review` status and an explicit owner-decision kind/package. The reassessment evidence records research and automatic dispositions separately. Links below retain saved provenance; see retrieval receipts for live checks. R2 identity does not establish authorship or adoption. No visitor-visible content changed.', '',
             f"The exclusive mission-scope borderline queue has {scope['unresolved_count']} unresolved records. Pending live-service prerequisites and approved architecture blockers are outside this queue.", '',
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
