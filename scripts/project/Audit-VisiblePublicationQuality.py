"""Audit every visible implemented/validated record and reconcile the 2026-09-13 audit.

The debt witness never approves publication. It permits only the exact unchanged
legacy failures explicitly enumerated for owner remediation; new failures abort.
"""
import argparse
import collections
import html
import json
import re
from urllib.parse import unquote
from PublicationQuality import ROOT, quality_errors, prior_findings, finding_id
from WorkflowStageLifecycle import digest

QUEUE = ROOT / 'project-state/discovery/publication-quality-remediation-2026-09-26.json'

def normalized(url):
    return unquote(html.unescape(url)).rstrip('/')

def visible_links():
    links = collections.defaultdict(collections.Counter)
    for path in sorted((ROOT / 'content').rglob('*.md')):
        for url in re.findall(r'https?://[^\s<>"\)]+', path.read_text(encoding='utf-8-sig')):
            links[normalized(url)][path.relative_to(ROOT).as_posix()] += 1
    return links

def placements(record, links):
    result = {}
    # A shared directory/hub source is provenance, not evidence that each of its
    # static child records appears publicly. Match original/archive bytes or a
    # record-specific /view wrapper; live services match their actual source.
    fields = ['r2_url', 'direct_file_url']
    source = record.get('source_url') or ''
    direct = record.get('direct_file_url') or ''
    static = bool(record.get('r2_url')) or bool(re.search(r'\b(pdf|docx?|xlsx?|csv|zip)\b', record.get('file_type') or '', re.I))
    if not static or not direct and not record.get('r2_url') or source.rstrip('/').removesuffix('/view') == direct.rstrip('/') or re.search(r'\.(pdf|docx?|xlsx?|csv|zip)(?:/view)?(?:[?#]|$)',source,re.I) or re.search(r'/DocumentCenter/View/\d+',source,re.I):
        fields.append('source_url')
    for field in fields:
        url = record.get(field)
        if url:
            for path, count in links.get(normalized(url), {}).items():
                result[path] = max(result.get(path, 0), count)
    return result

def audit(inventory, links):
    failures, passing, reconciliation = [], [], []
    rows = {r['id']: r for r in inventory['candidates']}
    legacy_visible = {r['id'] for r in json.loads(QUEUE.read_text(encoding='utf-8'))['failures']} if QUEUE.exists() else set()
    for r in inventory['candidates']:
        locations = placements(r, links)
        if not locations or r['status'] not in {'implemented', 'validated'} and not r.get('publication_quality_decision') and r['id'] not in legacy_visible and r['id'] not in prior_findings():
            continue
        errors = quality_errors(r)
        if errors:
            failures.append({'id': r['id'], 'title': r['title'], 'pages': locations,
                             'errors': errors, 'inventory_row_digest': digest(r)})
        else:
            passing.append(r['id'])
    for rid, old in sorted(prior_findings().items()):
        row = rows.get(rid)
        locations = placements(row or old, links)
        # Audit field aliases allow detection even if a row was subsequently removed.
        locations = locations or dict(links.get(normalized(old['r2_url']), {}))
        decision = (row or {}).get('publication_quality_decision', {})
        reversal = decision.get('supersedes_findings', [])
        if locations:
            disposition = 'resolved by explicit evidence-backed reversal' if row and not quality_errors(row) else 'unresolved visible quality finding'
        else:
            disposition = 'no longer directly visitor-visible; original negative finding retained'
        reconciliation.append({'id': rid, 'title': old['title'], 'finding_id': finding_id(rid),
                               'prior_status': old['quality_review']['status'],
                               'proposed_master_record': old['quality_review'].get('proposed_master_record'),
                               'current_inventory_status': (row or {}).get('status'),
                               'current_visible_pages': locations, 'disposition': disposition,
                               'explicit_reversal': reversal})
    return {'failures': sorted(failures, key=lambda r: r['id']), 'passing_ids': sorted(passing),
            'september_13_reconciliation': reconciliation}

def enforce_debt(result, witness):
    old = {r['id']: r for r in witness['failures']}
    for failure in result['failures']:
        assert failure['id'] in old, 'New visible quality debt: ' + failure['id']
        assert failure == old[failure['id']], 'Legacy quality debt changed or grew: ' + failure['id']
    return len(result['failures'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-initial-witness', action='store_true')
    parser.add_argument('--report', default='tmp/visible-publication-quality-audit.json')
    args = parser.parse_args()
    inventory = json.loads((ROOT / 'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
    # Direct inventory writers cannot hide an unreviewed transition by omitting
    # a content link. Both visible statuses require the actual-record gate.
    import subprocess
    baseline = json.loads(subprocess.check_output(['git','show','2588c0c1399351957f140825c50fc485fe5546b1:project-state/master-inventory.json'],cwd=ROOT).decode('utf-8-sig'))
    old = {r['id']:r for r in baseline['candidates']}
    from PublicationQuality import require_publication_quality
    for record in inventory['candidates']:
        if record['status'] in {'implemented','validated'} and record != old.get(record['id']):
            require_publication_quality(record)
    result = audit(inventory, visible_links())
    if args.write_initial_witness:
        assert not QUEUE.exists(), 'Never overwrite the sealed original quality debt witness'
        result['authorization'] = 'Owner requested a durable queue for existing unresolved visible quality failures; no unrelated removals in PR #194.'
        result['policy'] = 'Unresolved debt is not approved. Only exact unchanged listed failures may remain pending owner cleanup; any new or changed failure is fatal. Visible transitions always require the actual-record gate.'
        QUEUE.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    else:
        enforce_debt(result, json.loads(QUEUE.read_text(encoding='utf-8')))
    (ROOT / args.report).write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"PASS: {len(result['passing_ids'])} visible records pass; {len(result['failures'])} explicitly unresolved legacy records remain in the sealed remediation queue; no new or changed quality debt.")
