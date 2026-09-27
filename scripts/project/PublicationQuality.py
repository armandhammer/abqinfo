"""Publication value is independent of scope, provenance, archiving and rendering.

No legacy status is proof of quality. The explicit debt registry is only a bounded
remediation queue; it is never consulted by the actual-record transition gate.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = 'project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json'
DECISION_FIELD = 'publication_quality_decision'
REGULATORY = re.compile(r'guideline|checklist|\bfees?\b|procedur|operational|regulat|criteria|overlay zone|ordinance|standards', re.I)
ENGAGEMENT = re.compile(r'ranking|workshop|task.force|survey|engagement|feedback', re.I)

@lru_cache(maxsize=1)
def prior_findings():
    data = json.loads((ROOT / AUDIT).read_text(encoding='utf-8-sig'))
    return {r['candidate_id']: r for r in data['documents']
            if r['quality_review']['status'] != 'meets standard on renewed review'}

def finding_id(rid):
    return 'post-pr132-2026-09-13:' + rid

def text(value):
    return isinstance(value, str) and len(value.strip()) >= 35

def evidence(values):
    return isinstance(values, list) and bool(values) and all(
        isinstance(v, str) and (v.startswith('https://') or (ROOT / v.split('#')[0]).is_file()) for v in values)

def quality_errors(record, findings=None):
    """Evaluate this actual record; no status or debt exemption can approve it."""
    errors = []
    d = record.get(DECISION_FIELD) or {}
    if d.get('decision') != 'passes':
        errors.append('missing or negative durable publication-quality decision')
    if not evidence(d.get('evidence')):
        errors.append('missing publication-value evidence')
    q = d.get('assessment') or {}
    for field in ('document_function', 'substantive_content', 'durable_public_usefulness',
                  'information_density', 'unique_information', 'rationale'):
        if not text(q.get(field)):
            errors.append('missing substantive ' + field)
    if len(str(q.get('rationale', '')).split()) < 20:
        errors.append('public-value rationale lacks substantive detail (20 words minimum)')
    if q.get('standalone_public_value') == 'low' and q.get('publication_form') == 'standalone':
        errors.append('low standalone public value')
    if q.get('reviewed_document_content') is not True or q.get('visual_inspection_completed') is not True:
        errors.append('document-content/visual review not established')
    form = q.get('publication_form')
    if form not in {'standalone', 'grouped_component', 'consolidated_master', 'live_service'}:
        errors.append('nonpublic or unspecified publication form')
    relationship = q.get('series_relationship')
    if relationship not in {'standalone', 'component', 'serial'}:
        errors.append('missing series/component review')
    if relationship in {'component', 'serial'}:
        a = q.get('aggregation_decision') or {}
        if not text(a.get('rationale')) or not evidence(a.get('evidence')) or a.get('form') != form:
            errors.append('series/component ignores aggregation decision')
        if form == 'standalone' and not text(a.get('standalone_unique_value')):
            errors.append('component standalone exception lacks unique value')
    pages = q.get('page_count')
    words = q.get('extracted_word_count')
    if not isinstance(pages, int) or pages < 0 or not isinstance(words, int) or words < 0:
        errors.append('missing measured content')
    thin = isinstance(pages, int) and 0 < pages <= 2 or q.get('limited_content') is True
    if thin and form == 'standalone':
        a = q.get('limited_content_assessment') or {}
        for field in ('specific_substance', 'unique_durable_use', 'why_shortness_is_sufficient'):
            if not text(a.get(field)):
                errors.append('limited content lacks concrete ' + field)
        if not evidence(a.get('evidence')):
            errors.append('unsupported limited-content exception')
    title = record.get('title', '')
    if REGULATORY.search(title) or q.get('currentness_review_required') is True:
        c = q.get('currentness_review') or {}
        if c.get('status') not in {'current', 'historical_superseded', 'historical_status_uncertain'} or not evidence(c.get('authoritative_sources')) or not text(c.get('finding')) or not text(c.get('publication_qualification')):
            errors.append('missing authoritative currentness/supersession review')
    if ENGAGEMENT.search(title) or q.get('public_engagement') is True:
        e = q.get('engagement_assessment') or {}
        if not text(e.get('function')) or not text(e.get('durable_unique_information')) or not evidence(e.get('evidence')):
            errors.append('missing substantive public-engagement review')
        if form == 'standalone' and e.get('substantive_basis') not in {'analysis', 'formal_findings', 'formal_action', 'durable_unique_information'}:
            errors.append('raw engagement data does not establish standalone value')
    negatives = []
    negative = (prior_findings() if findings is None else findings).get(record.get('id'))
    if negative: negatives.append(finding_id(record['id']))
    prior_quality = record.get('quality_assessment') or {}
    if prior_quality.get('publication_form') == 'archive_only' or prior_quality.get('standalone_public_value') == 'low':
        negatives.append('inventory-quality:' + record.get('id', '?'))
    owner_path = ROOT / 'project-state/discovery/old-town-quality-correction-2026-09-26/record-decisions.json'
    if findings is None and owner_path.exists():
        owner = json.loads(owner_path.read_text(encoding='utf-8'))
        if record.get('id') in owner['excluded_ids']:
            negatives.append('owner-old-town-2026-09-26:' + record['id'])
    for negative_id in negatives:
        reversal = d.get('supersedes_findings') or []
        matching = [r for r in reversal if r.get('finding_id') == negative_id]
        if not any(text(r.get('new_evidence_rationale')) and evidence(r.get('new_evidence')) for r in matching):
            errors.append('unresolved contradiction with prior negative/questionable quality finding')
    return sorted(set(errors))

def require_publication_quality(record):
    errors = quality_errors(record)
    if errors:
        raise ValueError(record.get('id', '?') + ': ' + '; '.join(errors))
    return True

def require_quality_transition(before, after):
    require_publication_quality(after)
    old_decision = before.get(DECISION_FIELD) or {}
    if old_decision and old_decision.get('decision') != 'passes':
        from WorkflowStageLifecycle import digest
        stable_id = old_decision.get('finding_id') or 'inventory-decision:' + before['id'] + ':' + digest(old_decision)
        owner_path = ROOT / 'project-state/discovery/old-town-quality-correction-2026-09-26/record-decisions.json'
        if owner_path.exists() and before['id'] in json.loads(owner_path.read_text(encoding='utf-8'))['excluded_ids']:
            stable_id = 'owner-old-town-2026-09-26:' + before['id']
        reversals = after[DECISION_FIELD].get('supersedes_findings', [])
        if not stable_id or not any(r.get('finding_id') == stable_id and text(r.get('new_evidence_rationale')) and evidence(r.get('new_evidence')) for r in reversals):
            raise ValueError(after['id'] + ': negative decision must be preserved and explicitly superseded with new evidence')

def validate_affected_records(records):
    """Implementation validators call this before allowing any visible transition."""
    for record in records:
        require_publication_quality(record)

def validate_completed_implementation(records, closeout):
    """A completed deployment audit reports debt; it never permits a transition.

    If this is a new implementation without a completed production closeout,
    every affected actual record must pass. Completed live records are still
    evaluated, with any failure required to match the sealed remediation debt.
    """
    if not closeout:
        return validate_affected_records(records)
    assert closeout.get('production_verification_result') == 'passed'
    from WorkflowStageLifecycle import digest
    debt = json.loads((ROOT / 'project-state/discovery/publication-quality-remediation-2026-09-26.json').read_text())
    pending = {r['id']: r for r in debt['failures']}
    for record in records:
        errors = quality_errors(record)
        if errors:
            assert record['id'] in pending and pending[record['id']]['inventory_row_digest'] == digest(record)
        else:
            require_publication_quality(record)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--record-file', required=True)
    parser.add_argument('--previous-record-file')
    args = parser.parse_args()
    record = json.loads(Path(args.record_file).read_text(encoding='utf-8-sig'))
    if args.previous_record_file:
        require_quality_transition(json.loads(Path(args.previous_record_file).read_text(encoding='utf-8-sig')), record)
    else:
        require_publication_quality(record)
    print('Actual-record publication quality passed.')
