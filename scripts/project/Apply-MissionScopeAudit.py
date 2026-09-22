#!/usr/bin/env python3
"""Apply the 2026-09-22 mission-scope correction to the pre-audit approved set."""
import json
from collections import Counter
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / 'project-state/master-inventory.json'
DISCOVERY = ROOT / 'project-state/discovery'
AUDIT = DISCOVERY / 'approved-inventory-mission-scope-audit-2026-09-22.json'
PRIORITY = DISCOVERY / 'approved-inventory-backlog-prioritization-mission-scope-2026-09-22.json'
POLICY = DISCOVERY / 'mission-scope-review-policy-2026-09-22.json'
TODAY = '2026-09-22'

TRUCK = {
    'src-1f8378fe0d939884', 'src-1ce9fae6e4b2e675', 'src-a5f4c28aefd1ce20',
    'src-57017bee270744dd', 'src-68d5d6b446b98b35', 'src-b07a77c5f6cd79b3',
    'src-84c88a71842b2ed1',
}
NMDOT_GRANTS = {
    'src-087c613a50cf2f77', 'src-1238f81673c19398', 'src-15424a3ed5d9118b',
    'src-3983b9dec570f033', 'src-3d73a376de5f93d7', 'src-3ed48708a5cd8eb4',
    'src-41b913bce3be7d93', 'src-71fa71c632ce4b6a', 'src-7a0927957c7eacfd',
    'src-80a1ba651fd935cd', 'src-9a2d7938040450e4', 'src-b8b65025c4f54a63',
    'src-ba150abfb1b8a847', 'src-d617f438901ade14', 'src-db216e455e924569',
    'src-de1be5126ebdb066', 'src-fa13a1cec10ea9d0', 'src-fe26357deaa58dbb',
}
MUNICIPAL_FORMS = {'src-b3d8dcb56e000437', 'src-4952ea05cd055792'}
WEED_HANDBOOK = {'src-f19a78a166008dae'}

PGS = {
    'src-9aeb5f621800da58', 'src-08b6b68b53336462', 'src-3efa72bc100374a1',
    'src-aee98d2ab382de65', 'src-bc069f52331eb293', 'src-c8e6f10731a478e6',
    'src-cd72192082580abe', 'src-765624191ba169bd', 'src-d15bbc358aeaec4d',
    'src-8188148b0cd6c40d', 'src-0e133db868401e77', 'src-c771ae9e41b9905c',
}
PLANNING_ROOT = {
    'src-16b33375ffbddc62', 'src-1fa6ae851ddf282d', 'src-513fe9056bf9b34c',
    'src-c54e59cd5c25282d', 'src-7de0f5803d442e8f', 'src-8740362a1b751e26',
    'src-99fe2201b73355c4', 'src-afac0cf84867a22f', 'src-c87775c045d8acc4',
    'src-d9bf34830a9467e2', 'src-eb0f4b39798d29df', 'src-f528ec2e0e955690',
    'src-fb6e95610a43c7a4',
}
MS4 = {'src-5cdb4d5491c3a02d', 'src-975528e01439f6df', 'src-fdc66c5b8de48584', 'src-7c1a063b817989bd', 'src-eda3280085776f61', 'src-e531466aed7f5387'}
CLIMATE_AND_TRAFFIC = {'src-114911e49460dc22', 'src-13f6e1487f178196', 'src-88b083b092a7305e'}
CRUISING = {'src-59a9ee7af1987815'}
ENACTMENTS = {'src-31a70a3d6058e31d', 'src-38a3fef570ca8119', 'src-8c4e4715d494b813', 'src-b327afa5a9c059ff', 'src-b7a5fec713a76202', 'src-f6271cb7607a5804'}
GO_BONDS = {'src-20cca95ec6dcbe4f', 'src-832bc2144296aa51', 'src-9e6cb716ac7c28d9', 'src-ca2ae8cb1ef13fdf'}
MISC = {'src-06d0fc4cd0abdef6', 'src-070a763aa9701f86', 'src-07ce09fd200d2d69', 'src-0878bc7d09a7c65b', 'src-092548fef85b887b', 'src-4ac9f8a1fb953e46', 'src-5006deafb03b1f7a', 'src-51fb6dc80b316253', 'src-b8b28358abc9a2de', 'src-9fd0da60e94eb698', 'src-a6753953181feb4f', 'src-c5ed372e33966029', 'src-d8dd331b50fe7e9a'}

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def scope(decision, geographic, connection, value, exclusion_test, rationale):
    return {
        'assessed_at': TODAY,
        'geographic_institutional_scope': geographic,
        'specific_albuquerque_connection': connection,
        'abqinfo_public_information_value': value,
        'general_context_exclusion_test': exclusion_test,
        'final_scope_decision': decision,
        'substantive_rationale': rationale,
    }

def passing_assessment(candidate):
    cid = candidate['id']
    if cid in PGS:
        return scope('passes_both_gates', 'City of Albuquerque planned-growth policy and its component chapters.', 'The complete Part 1 and split Part 2 package directly describe Albuquerque land-use, growth, infrastructure, and regulatory choices.', 'A reader can use the package to understand the City’s historic planned-growth framework and the policy choices behind later land-use work.', 'It is not retained merely as a planning example; each delivery is a documented component of the City’s own adopted planning framework.', 'Saved family research establishes a substantive Albuquerque planning record. The incomplete split package affects future presentation, not mission relevance.')
    if cid in PLANNING_ROOT:
        return scope('passes_both_gates', 'City planning, facilities, redevelopment, open-space, historic-preservation, and land-use policy records.', 'Each record is a City plan, policy, facility program, redevelopment instrument, or Albuquerque-area regulatory decision.', 'These primary records explain concrete Albuquerque public planning, infrastructure, land-use, facilities, and neighborhood decisions.', 'The City subject is not incidental and the records are not being kept simply because a planning page exists.', 'Saved family research and the direct City originals establish a specific public-policy or infrastructure value for Albuquerque.')
    if cid in MS4:
        return scope('passes_both_gates', 'City of Albuquerque MS4 compliance reports and the governing EPA watershed permit.', 'The annual filings identify City permit NMR04A014 and report City stormwater services; the permit governs that City program within the watershed.', 'The series documents how Albuquerque carries out federally required stormwater and water-quality responsibilities.', 'Federal or watershed scope alone would not qualify; these records are retained because the City is a named regulated operator and the filings report its work.', 'The saved decision establishes a coherent City compliance-report series with direct civic and infrastructure value.')
    if cid in CLIMATE_AND_TRAFFIC:
        return scope('passes_both_gates', 'City Climate Action Task Force opening-meeting records or a City traffic-calming public-meeting presentation.', 'The records concern a City climate-policy process or a specific Albuquerque school-area street-safety project.', 'They show public civic decision-making and infrastructure/policy development in Albuquerque.', 'Their value is a specific City process or project, not generic climate or traffic context.', 'The saved decision artifacts identify a concrete Albuquerque policy or safety subject and a useful primary-source form.')
    if cid in CRUISING:
        return scope('passes_both_gates', 'City Council task-force final report under R-17-250.', 'It is a formal Albuquerque City Council report on a locally governed transportation/public-safety issue.', 'The final report records the City’s findings and recommendations for a civic issue.', 'It is not retained as generic car-culture or transportation context; the City Council decision and recommendations are the subject.', 'Saved family research identifies a substantive, standalone City final report with clear public-policy value.')
    if cid in ENACTMENTS:
        return scope('passes_both_gates', 'Enacted City ordinances and resolutions on demolition, historic preservation, sustainability, bonds, federal priorities, and complete streets.', 'Each is an Albuquerque legislative act or formal City policy/expenditure decision.', 'The enactments provide primary evidence of City law, policy, capital finance, and civic decisions.', 'A City enactment is not approved solely because it can sit on a topical page; its formal municipal decision-making content supplies the value.', 'Saved counterpart capture establishes these as final City legislative records with direct civic-information value.')
    if cid in GO_BONDS:
        return scope('passes_both_gates', 'City-edition 2011 parks, cultural-services, and recreation general-obligation-bond scope and schedule records.', 'They concern Albuquerque City capital-program project scopes and schedules.', 'They help explain City spending and capital-program commitments.', 'The unresolved version relationship limits future publication treatment, but City capital-program scope—not generic bond context—satisfies mission scope.', 'Saved research establishes an Albuquerque municipal capital-program subject; finality remains a separate editorial gate.')
    if cid in MISC:
        return scope('passes_both_gates', 'City strategy, Council oversight, public-safety/code-enforcement, water-conservation, budget, facility, regulation, and project records.', 'Each concerns a named City program, Council oversight matter, municipal service, regulation, expenditure, facility, or civic decision.', 'Each can materially inform an Albuquerque reader about a City policy, service, public-safety activity, spending, or regulatory decision.', 'The saved evidence identifies a direct City public-information subject; it is not retained merely for geographic connection or a plausible placement.', 'The documents are City primary records with a substantive municipal-policy, service, infrastructure, finance, or regulatory use.')
    raise AssertionError(f'No passing scope group for {cid}')

def excluded_assessment(candidate):
    cid = candidate['id']
    if cid in TRUCK:
        return scope('excluded_insufficient_albuquerque_relevance', 'Statewide NMDOT freight and interstate truck-parking study series.', 'Saved research does not establish a specific or material Albuquerque focus; any local references would be incidental to a statewide study.', 'Interstate freight-parking analysis is not a core ABQInfo public-information subject even if it contains limited Albuquerque material.', 'Statewide applicability, NMDOT jurisdiction, and I-25/I-40 passing through Albuquerque are expressly insufficient.', 'The prior decision treated statewide highway context and a Roadway Studies placement as enough. Under the corrected two-gate rule, neither establishes an Albuquerque-specific, useful record.')
    if cid in NMDOT_GRANTS:
        return scope('excluded_insufficient_albuquerque_relevance', 'Statewide NMDOT grant-administration, application, reimbursement, and program-template materials.', 'No saved evidence identifies an Albuquerque applicant, project, municipal decision, facility, or material Albuquerque component.', 'Generic state grant-process paperwork does not help a reader understand Albuquerque government, infrastructure, or public policy beyond the originating agency’s materials.', 'NMDOT jurisdiction and possible statewide availability are insufficient; no specific Albuquerque connection is documented.', 'These records are administrative/program templates and forms, not Albuquerque-specific public-information records.')
    if cid in MUNICIPAL_FORMS:
        return scope('excluded_insufficient_abqinfo_usefulness', 'City of Albuquerque unexecuted standard professional-services agreement templates.', 'They are City forms, but do not document a particular Albuquerque project, expenditure, procurement decision, contractor, or public outcome.', 'Blank transactional templates add little durable civic understanding beyond the City’s originating procurement materials.', 'A City agency and a plausible Development Process placement do not turn a generic unexecuted form into a substantive public-information record.', 'The forms pass a narrow institutional connection but fail the independent usefulness gate as generic transactional templates.')
    if cid in WEED_HANDBOOK:
        return scope('excluded_insufficient_abqinfo_usefulness', 'A 2012 Planning Department weed-identification handbook.', 'It has a City source but is a technical reference guide rather than a City policy, service decision, project, or regulatory record.', 'The handbook’s generic operational/identification content does not materially advance understanding of Albuquerque government or public infrastructure.', 'City authorship and a potential landscaping/development page are insufficient where the substantive content is peripheral technical reference material.', 'The document is authoritative but too technical-operational and generic for the site’s public-information purpose.')
    raise AssertionError(f'No excluded scope group for {cid}')

def group(name, ids, ranking, rationale, next_stage):
    return {'family': name, 'candidate_count': len(ids), 'candidate_ids': sorted(ids), 'ranking': ranking, 'scope_status': 'passes_both_gates', 'rationale': rationale, 'next_stage_if_authorized': next_stage}

def main():
    inventory = read(INVENTORY)
    candidates = {c['id']: c for c in inventory['candidates']}
    starting = sorted(c['id'] for c in candidates.values() if c['status'] == 'approved for addition')
    expected = TRUCK | NMDOT_GRANTS | MUNICIPAL_FORMS | WEED_HANDBOOK | PGS | PLANNING_ROOT | MS4 | CLIMATE_AND_TRAFFIC | CRUISING | ENACTMENTS | GO_BONDS | MISC
    assert len(starting) == 86 and set(starting) == expected, 'Pre-audit approved population drifted; do not apply this audit blindly.'

    audit_records = []
    for cid in starting:
        candidate = candidates[cid]
        prior_placement = candidate.get('proposed_canonical_page')
        prior_artifacts = []
        if cid in TRUCK:
            prior_artifacts = ['project-state/discovery/nmdot-statewide-truck-parking-study-decision-2026-09-19.json', 'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json', 'project-state/discovery/nmdot-statewide-truck-parking-study-docx-visual-qa-attestation-2026-09-21.json']
        elif cid in NMDOT_GRANTS:
            prior_artifacts = ['project-state/discovery/nmdot-grant-administration-and-application-decision-2026-09-19.json']
        elif cid in MUNICIPAL_FORMS:
            prior_artifacts = ['project-state/discovery/municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json']
        assessment = excluded_assessment(candidate) if cid in (TRUCK | NMDOT_GRANTS | MUNICIPAL_FORMS | WEED_HANDBOOK) else passing_assessment(candidate)
        resulting_status = 'excluded' if assessment['final_scope_decision'].startswith('excluded_') else 'approved for addition'
        candidate['scope_assessment'] = assessment
        candidate['status'] = resulting_status
        if resulting_status == 'excluded':
            candidate['exclusion_reason'] = assessment['substantive_rationale']
        note = f"Mission-scope audit {TODAY}: {assessment['final_scope_decision']}. {assessment['substantive_rationale']}"
        if prior_placement or prior_artifacts:
            note += ' Prior proposed placement/archive-preparation evidence is preserved as historical evidence and superseded for any excluded record.'
        if note not in candidate['processing_notes']:
            candidate['processing_notes'].append(note)
        audit_records.append({
            'id': cid, 'title': candidate['title'], 'agency': candidate['agency'], 'prior_status': 'approved for addition',
            'scope_assessment': assessment, 'resulting_status': resulting_status,
            'prior_proposed_placement': prior_placement, 'prior_archive_or_review_artifacts': prior_artifacts,
            'prior_work_superseded': bool(resulting_status == 'excluded' and (prior_placement or prior_artifacts)),
        })

    counts = Counter(c['status'] for c in inventory['candidates'])
    inventory['counts'] = {status: counts[status] for status in inventory['allowed_statuses']}
    pending_statuses = {'pending review', 'approved for addition', 'downloaded', 'parsed', 'description drafted', 'placement assigned'}
    pending = sorted(c['id'] for c in inventory['candidates'] if c['status'] in pending_statuses or (c['status'] == 'implemented' and c['validation_status'] != 'passed'))
    inventory['next_pending_id'] = pending[0] if pending else None
    inventory['generated_at'] = f'{TODAY}T00:00:00Z'
    write(INVENTORY, inventory)

    artifacts_to_mark = {
        'nmdot-statewide-truck-parking-study-decision-2026-09-19.json': 'all seven candidates excluded for insufficient Albuquerque relevance',
        'nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json': 'all seven candidates excluded for insufficient Albuquerque relevance; no R2 objects were uploaded',
        'nmdot-statewide-truck-parking-study-docx-visual-qa-attestation-2026-09-21.json': 'all seven candidates excluded for insufficient Albuquerque relevance',
        'nmdot-grant-administration-and-application-decision-2026-09-19.json': 'all 18 statewide grant-administration/application records excluded for insufficient Albuquerque relevance',
        'municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json': 'both City standard-form agreements excluded for insufficient ABQInfo usefulness',
        'approved-inventory-backlog-prioritization-2026-09-21.json': 'replaced by mission-scope audit and scope-gated reprioritization',
        'approved-inventory-backlog-prioritization-post-abq-ride-2026-09-21.json': 'replaced by mission-scope audit and scope-gated reprioritization',
    }
    for filename, reason in artifacts_to_mark.items():
        path = DISCOVERY / filename
        artifact = read(path)
        artifact['superseded_by_mission_scope_audit'] = {
            'artifact': 'project-state/discovery/approved-inventory-mission-scope-audit-2026-09-22.json',
            'recorded_at': TODAY, 'reason': reason,
            'historical_evidence_preserved': True,
            'r2_or_publication_action_authorized': False,
        }
        write(path, artifact)

    audit = {
        'schema_version': 1, 'artifact_type': 'approved_inventory_mission_scope_audit', 'recorded_at': TODAY,
        'purpose': 'Correct the pre-approval mission-scope defect before backlog ranking, archive preparation, or public work.',
        'scope_rule': {
            'albuquerque_relevance': 'Substantial Albuquerque, City-government, or specifically material Albuquerque regional/state/federal component required.',
            'public_information_usefulness': 'Material help understanding a core Albuquerque government, policy, planning, infrastructure, public-service, spending, regulation, project, or civic-decision subject required.',
            'insufficient_by_themselves': ['statewide applicability', 'agency jurisdiction in Albuquerque', 'interstate facility passing through Albuquerque', 'incidental Albuquerque reference/map/statistic/location', 'generic contextual usefulness', 'plausible page placement', 'archive readiness'],
        },
        'starting_population': {'status': 'approved for addition', 'count': 86, 'candidate_ids': starting},
        'records': audit_records,
        'accounting': {'starting_approved': 86, 'remains_approved': 58, 'excluded_insufficient_albuquerque_relevance': 25, 'excluded_insufficient_abqinfo_usefulness': 3, 'requires_human_review': 0, 'reconciled_total': 86},
        'immediate_correction': {'family': 'NMDOT statewide truck-parking study', 'candidate_ids': sorted(TRUCK), 'final_status': 'excluded', 'reason': 'Statewide freight/truck-parking analysis lacks a specific material Albuquerque focus and is not an ABQInfo public-information subject.', 'r2_upload': 'not performed and not authorized', 'public_work': 'not performed and not authorized'},
        'process_correction': {'scope_assessment_required_before_approval': True, 'backlog_ranking_after_scope_gate_only': True, 'archive_readiness_never_establishes_eligibility': True},
    }
    write(AUDIT, audit)

    policy = {
        'schema_version': 1, 'artifact_type': 'mission_scope_review_policy', 'recorded_at': TODAY,
        'applies_before': ['approved for addition', 'archive preparation', 'backlog prioritization', 'visible/static publication'],
        'required_scope_assessment_fields': list(scope('', '', '', '', '', '').keys()),
        'positive_approval_decision': 'passes_both_gates',
        'regression_enforcement': 'Test-MasterInventory.ps1 rejects approved-for-addition candidates without a complete positive assessment; Test-MissionScopeAudit.py validates the 2026-09-22 correction and scope-gated ranking.',
    }
    write(POLICY, policy)

    eligible_groups = [
        group('Planned Growth Strategy', PGS, 1, 'High-significance City land-use and growth-policy family; mission scope passes, but missing Chapter 3.0 must be resolved before truthful preparation or presentation.', 'Bounded authoritative-source recovery for missing Part 2 Chapter 3.0 and a family-level presentation decision; no archive preparation or external action.'),
        group('Later MS4 annual reports and permit', MS4, 2, 'Direct City stormwater-service/compliance value with a coherent chronological form; FY2016 source recovery remains the operational blocker.', 'Recover the authoritative FY2016 City annual-report original and confirm the full chronological family; no archive preparation or external action.'),
        group('Planning documents-root plans and policy instruments', PLANNING_ROOT, 3, 'Substantive City planning/facility/redevelopment records, though the mixed residual needs truthful family-level presentation.', 'Separate coherent subfamilies and record a family presentation plan; no archive preparation or external action.'),
        group('2024 enacted ordinances and resolutions', ENACTMENTS, 4, 'Final City legislative primary records with direct civic, regulatory, and capital-policy value.', 'Confirm coherent topical groupings and public form before any archive-preparation proposal.'),
        group('City strategy, oversight, services, regulation, and facility records', MISC, 5, 'Passing City primary records without a ready common family; do not create an artificial batch.', 'Develop bounded topical family groupings, beginning with a single coherent City oversight or service cluster.'),
        group('City-edition 2011 GO bond records', GO_BONDS, 6, 'Specific City capital-program records whose publication form still depends on version/finality resolution.', 'Resolve the version relationships before proposing archive preparation or a public presentation.'),
        group('Climate Action Task Force and Sandia High safety records', CLIMATE_AND_TRAFFIC, 7, 'Each is specific and useful, but the pair and presentation are distinct small families.', 'Choose one coherent small family and settle its future public form; do not combine unrelated records.'),
        group('Council Cruising Task Force final report', CRUISING, 8, 'Strong standalone City Council report but a singleton with preparatory work still required.', 'Perform only if separately selected as a bounded single-record archival-preparation task.'),
    ]
    assert sum(g['candidate_count'] for g in eligible_groups) == 58
    priority = {
        'schema_version': 1, 'artifact_type': 'approved_inventory_backlog_prioritization_mission_scope_gated', 'recorded_at': TODAY,
        'supersedes': 'project-state/discovery/approved-inventory-backlog-prioritization-post-abq-ride-2026-09-21.json',
        'source_audit': 'project-state/discovery/approved-inventory-mission-scope-audit-2026-09-22.json',
        'eligible_population': {'count': 58, 'scope_decision': 'passes_both_gates'},
        'ranking_order': ['mission/public-information value', 'Albuquerque specificity and significance', 'coherent public presentation', 'source/research completeness', 'placement confidence', 'archive readiness and operational effort'],
        'rule': 'Operational convenience cannot outrank mission relevance; archive readiness ranks only records that already pass scope.',
        'family_groups': eligible_groups,
        'recommended_next_bounded_task': eligible_groups[0],
        'authorization_boundary': 'Decision only. No archive preparation, R2 mutation, Hugo/content edit, PR, merge, deployment, or new-family work was performed or authorized.',
    }
    write(PRIORITY, priority)

if __name__ == '__main__':
    main()
