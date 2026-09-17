"""Research lane only.

Reads master-inventory.json plus scratch measurement files and writes one dated
decision artifact under project-state/discovery/. It never modifies
master-inventory.json, checkpoint.json, site content, or R2 state.
"""

import datetime
import io
import json
import sys

INVENTORY = 'project-state/master-inventory.json'
OUT = 'project-state/discovery/go2009-bond-cluster-research-2026-09-11.json'

CF_SUM = 'src-b3d0cd2df96d0bc6'      # validated community_facilities_-_summary.pdf
CF_SCOPE = 'src-00d75ea75ac5c12a'    # validated community_facilities_-_scopes.pdf
TOTALS = 'src-fea1d0aef6dc4569'      # validated go_bond_totals.pdf
STORM_BONDS = 'src-ec2498a018d22816'  # validated storm_sewer_system_bonds.pdf
PARKS_BONDS = 'src-60615a9cae3d68d4'  # validated parks_recreation_bonds.pdf
PARKS_SUM = 'src-2b015205e93852b3'    # validated parks_rec_-_summary.pdf

APPROVED = [
    ('src-e69e9150b150bc1a', 'fire_-_scope.pdf', '2009 Fire General Obligation Bond Project Scopes',
     'Details the 2009 Fire bond scopes for replacing outdated emergency response apparatus, rehabilitating fire stations, acquiring land for Station 9 expansion, and renovating Fire Station 2.',
     'Token coverage against the canonical Community Facilities scopes is only 0.633, and Apparatus, emergency, and Public Safety terms are absent from it. This is a separate Public Safety bond purpose, not a Community Facilities component.'),
    ('src-b7ef66c741b8a886', 'fire_-_summary.pdf', '2009-2017 Fire General Obligation Bond Summary',
     'Schedules $22.9 million of Fire bond funding through 2017 for apparatus replacement, fire station rehabilitation, land acquisition for the Station 9 expansion, and renovation of Fire Station 2.',
     'Token coverage against the canonical Community Facilities summary is 0.625. The two-page file is the complete record and strictly contains the one-page variants src-cd538ab91b9dcb63 and src-9c44f81e1b767084. Note that page two carries a Council neighborhood set-aside table, so an integrator may prefer to describe it as a combined sheet.'),
    ('src-5603714dac7351ba', 'police_-_scope.pdf', '2009 Police General Obligation Bond Project Scopes',
     'Details the 2009 Police bond scopes, including the Sixth Area Command Phase II, marked police vehicle replacement, Cibola and Ellison facility work, and headquarters improvements.',
     'Token coverage against the canonical Community Facilities scopes is only 0.569, with Command, Marked, Police, and Cibola absent. A separate Public Safety purpose.'),
    ('src-535234f371b3922c', 'police_-_summary.pdf', '2009-2017 Police General Obligation Bond Summary',
     'Schedules Police bond funding through 2017 for the Sixth Area Command Phase II, marked police vehicles, facility renovation, and related public safety capital investments.',
     'Token coverage against the canonical Community Facilities summary is 0.629. The two-page file strictly contains the one-page variant src-d530a6667e691129.'),
    ('src-999d681b4e75a4c1', 'cultural_services_-_scope.pdf', '2009 Cultural Services General Obligation Bond Project Scopes',
     'Details 2009 Cultural Services bond scopes across the Biological Park, museums, libraries, and cultural facilities, including paving, exhibits, a bonsai facility, International District work, and feasibility studies.',
     'Token coverage against the canonical Community Facilities scopes is 0.798, and distinctive content including Bonsai, International, District, and Feasibility is absent from the canonical. Materially more detailed than the consolidated sheet, so it is not a contained component.'),
    ('src-e12c77bb460b9c8f', 'council_sas_-_scopes.pdf', '2009 Council Neighborhood Set-Aside Project Scopes',
     'Details nine pages of 2009 Council neighborhood set-aside project scopes by district, covering parks, alleys, beautification, amenities, economic development, and other district-specific neighborhood improvements.',
     'Token coverage against the canonical Community Facilities summary is only 0.146. A distinct Council set-aside purpose with no consolidated equivalent retained.'),
    ('src-cb27c408e8c26a66', 'council_sas_-_summary.pdf', '2009-2017 Council Neighborhood Set-Aside General Obligation Bond Summary',
     'Schedules Council neighborhood set-aside bond funding through 2017 by district, covering park, alley, beautification, amenity, and neighborhood enhancement allocations across all Council districts.',
     'Token coverage against the canonical Community Facilities summary is 0.545, with Alley, Amenities, Beautification, and Set-Aside terms absent.'),
    ('src-768a6855fcfaf443', 'library_bonds.pdf', '2009 Library General Obligation Bond Authorization',
     'Preserves the 2009 library bond authorization sheet, covering design, equipping, and construction of library facilities, feasibility work, and the purchase of library materials and collections.',
     'Token coverage against the canonical Community Facilities summary is only 0.111. A distinct purpose-level authorization sheet of the same class as the retained parks_recreation_bonds and storm_sewer_system_bonds records.'),
    ('src-7567c5f27fceba0a', 'senior_family_community_center_community_enhancement_project_bonds.pdf',
     '2009 Senior, Family, Community Center, and Community Enhancement Project Bond Authorization',
     'Preserves the 2009 authorization sheet for senior, family, and community center bonds and community enhancement projects, covering acquisition, design, construction, and equipping of community facilities.',
     'Token coverage against the canonical Community Facilities summary is only 0.248. A distinct purpose-level authorization sheet.'),
    ('src-b049c4df2812749b', 'public_safety_bonds.pdf', '2009 Public Safety General Obligation Bond Authorization',
     'Preserves the 2009 Public Safety bond authorization sheet, covering fire apparatus, the Sixth Area Command, Cibola facilities, and related police and fire capital purposes.',
     'Token coverage against the canonical Community Facilities summary is only 0.121, with Apparatus, Cibola, and Command absent. See integration_flags: its byte-identical twin src-4204206743b66c6c was previously ruled a duplicate of the Community Facilities summary, which verification does not support.'),
    ('src-f70c337140899545', 'uetf_2010-2011.pdf', 'Urban Enhancement Trust Fund 2010-2011 Program Overview',
     'Describes the Urban Enhancement Trust Fund program for 2010 and 2011, including the committee, selection criteria, decade-plan relationship, and the process for awarding community enhancement funding.',
     'A separate City funding program rather than a general obligation bond purpose; token coverage against the Community Facilities summary is 0.054.'),
    ('src-b9402ce7e2e6c22f', 'uetf_2010-2011_summary.pdf', 'Urban Enhancement Trust Fund 2010-2011 Funding Summary',
     'Summarizes Urban Enhancement Trust Fund allocations for the 2010 and 2011 cycle, recording the total program amount available for community enhancement awards.',
     'Companion summary sheet to the Urban Enhancement Trust Fund overview; not a bond-purpose component.'),
    ('src-10edc718610865b0', 'uetf_2010-2011projects.pdf', 'Urban Enhancement Trust Fund 2010-2011 Funded Projects',
     'Lists the Urban Enhancement Trust Fund projects funded for 2010 and 2011 across fourteen pages, naming each organization, project, and award amount for community, cultural, and educational enhancement work.',
     'Fourteen-page project register with 42 dollar figures; token coverage against the Community Facilities summary is 0.026. A substantive standalone funding record.'),
]

DUPLICATES = [
    ('src-5be1347ebf4771ed', '1community_facilities_-_summary.pdf', CF_SUM,
     'Byte-identical to the validated community_facilities_-_summary.pdf (same SHA-256). A Plone re-upload of the same file under a "1" prefix.'),
    ('src-723dd5410eb8cbcc', '1go_bond_totals.pdf', TOTALS,
     'Byte-identical to the validated go_bond_totals.pdf (same SHA-256).'),
    ('src-c8cd11329c890ea9', '1dmd_storm_drainage_-_scopes.pdf', STORM_BONDS,
     'Normalized extracted text is identical (ratio 1.0000) to src-958736f6bd1e54ad, which was already ruled a duplicate because the storm drainage project scopes are fully represented by the retained 2009 Storm Sewer System Bonds authorization sheet.'),
    ('src-44acef2b42bfa08e', 'public_safety-fire_-_scopes.pdf', 'src-e69e9150b150bc1a',
     'Normalized extracted text is identical (ratio 1.0000) to fire_-_scope.pdf; the files differ by three bytes of PDF encoding only. The directory convention already retains the non-prefixed name and rules the public_safety- variant duplicate.'),
    ('src-c715f52202528605', 'public_safety-police_-_scopes.pdf', 'src-5603714dac7351ba',
     'Normalized extracted text is identical (ratio 1.0000) to police_-_scope.pdf, differing by two bytes of PDF encoding.'),
    ('src-9c44f81e1b767084', 'public_safety-fire_-_summary.pdf', 'src-b7ef66c741b8a886',
     'Normalized extracted text is identical (ratio 1.0000) to 1fire_-_summary.pdf, and both are strictly contained within the complete two-page fire_-_summary.pdf.'),
    ('src-cd538ab91b9dcb63', '1fire_-_summary.pdf', 'src-b7ef66c741b8a886',
     'The 548-character single-page text is contained verbatim within the 947-character two-page fire_-_summary.pdf, which is the complete record.'),
    ('src-d530a6667e691129', '1police_-_summary.pdf', 'src-535234f371b3922c',
     'The 547-character single-page text is contained verbatim within the 1,039-character two-page police_-_summary.pdf.'),
    ('src-c7acbcbdac7f5a84', 'animal_welfare_-_scope.pdf', CF_SCOPE,
     'Token coverage against the canonical Community Facilities scopes is 1.000 with no missing terms; the Animal Welfare scope is fully represented there.'),
    ('src-5f5c7f6cd632557b', 'animal_welfare_-_summary.pdf', CF_SUM,
     'Token coverage against the canonical Community Facilities summary is 1.000 with no missing terms.'),
    ('src-78ad201f6197b420', 'env._health_-_scope.pdf', CF_SCOPE,
     'Token coverage against the canonical Community Facilities scopes is 1.000, and the Environmental Health scope text appears verbatim inside it.'),
    ('src-7919b04bed94d619', 'finance_admin._-_scope.pdf', CF_SCOPE,
     'Token coverage against the canonical Community Facilities scopes is 0.988; the only unmatched token is the generic word "total".'),
    ('src-70e5acbb5ec868bc', 'dmd_-_cip_facilities_and_parking_-_scope.pdf', CF_SCOPE,
     'Token coverage against the canonical Community Facilities scopes is 0.954; the only unmatched tokens are generic words. This mirrors the existing ruling for the matching summary sheet src-1101044bb84eb3f3.'),
    ('src-d1a8a47dfa508dc1', '1parks_rec_-_scopes.pdf', PARKS_BONDS,
     'Parks and Recreation project-scope component. The directory already rules parks_rec_-_scopes.pdf (src-168dd1a36287a42d) a duplicate because the scopes are fully represented by the retained Parks and Recreation Bonds authorization sheet; the distinctive rows in this file, including Recreation Facility Development, Open Space, and Bosque work, are present there.'),
    ('src-3bce8c490338291d', 'dmd_park_design_-_scopes.pdf', PARKS_BONDS,
     'Park Design project-scope component, matching the existing ruling for its variant src-0a45f76cb5f7d922, whose recorded canonical is the Parks and Recreation project-scope record.'),
    ('src-b62e758d6186d260', 'dmd_park_design_-_summary.pdf', PARKS_SUM,
     'Park Design schedule component, matching the existing ruling for its variant src-26a9b4b80270cc43, whose recorded canonical is the Parks and Recreation schedule.'),
]

REVIEW = [
    ('src-5de108fb850c221f', 'senior_affairs_-_scope.pdf',
     'Token coverage against the canonical Community Facilities scopes is 0.912, but the unmatched tokens are specific project names: Bear Canyon and North Domingo Baca Multigenerational. Decide whether those rows make the standalone Senior Affairs scope independently useful or whether the consolidated sheet is sufficient.'),
    ('src-6fe3ca04cbe476d5', 'senior_affairs_-_summary.pdf',
     'Token coverage against the canonical Community Facilities summary is 0.952, with "Canyon" unmatched. Same borderline question as the Senior Affairs scope sheet; the two should be decided together.'),
    ('src-d2d3b593d77a2885', 'family_and_community_services_-_summary.pdf',
     'Token coverage against the canonical Community Facilities summary is 0.917, but Holiday Park Community Center, Pat Hurley Community Center, and Storehouse Facility rows are absent from the canonical. Its byte-identical twin src-3ef781d4a038852a was already ruled a duplicate on the stated ground that the schedule is "contained within the canonical 2009 Community Facilities schedule", which this measurement does not fully support. Re-adjudicate both together.'),
    ('src-5cea73d2df70dabb', '1dmd_streets_-_summary.pdf',
     'Not a duplicate of the validated dmd_streets_-_summary.pdf: normalized similarity is 0.7679 and the two carry materially different rows, including a Reconstruction Major Streets block totalling $16.9 million that appears only in the validated file. These are two different revisions of the Streets schedule and the version order is unresolved. Determine which revision the City treats as current before retaining or superseding either.'),
]

EXCLUDED = [
    ('src-9a95b64100b0b931', 'pie_chart.pdf',
     'A single-page percentage-and-dollar pie chart of the 2009 program by purpose, with no project lists, locations, schedules, or scopes. This is the same document class as src-7405cfc41e5500c4 in the 2003 directory, which was excluded for exactly this reason.'),
    ('src-bb8d1282621d598e', 'frequently_asked_questions_and_answers.pdf',
     'Seven-page voter-education question-and-answer sheet on general obligation bond mechanics, carrying no capital-program detail. Consistent with the FAQ exclusions recommended for the 2003 and 2004 directories.'),
]


def main():
    scratch = sys.argv[1]
    inv = json.load(io.open(INVENTORY, encoding='utf-8'))
    idx = {c['id']: c for c in inv['candidates']}
    meta = {m['id']: m for m in json.load(io.open(scratch + '/meta.json', encoding='utf-8'))}
    prof = json.load(io.open(scratch + '/profile.json', encoding='utf-8'))

    def base(cid):
        c = idx[cid]
        return {
            'id': cid,
            'authoritative_url': c.get('direct_file_url') or c.get('source_url'),
            'size_bytes': meta[cid]['bytes'] if cid in meta else None,
            'checksum_sha256': meta[cid]['sha'] if cid in meta else None,
            'pages': prof[cid]['pages'] if cid in prof else None,
            'link_check': 'HTTP 200 verified 2026-09-11',
        }

    approved = []
    for cid, fn, title, desc, ev in APPROVED:
        r = base(cid)
        r.update({'recommended_status': 'approved for addition', 'file': fn, 'title': title,
                  'description': desc, 'description_word_count': len(desc.split()),
                  'proposed_canonical_page': 'content/city-data/capital-spending.md', 'evidence': ev})
        approved.append(r)

    dups = []
    for cid, fn, canon, ev in DUPLICATES:
        r = base(cid)
        r.update({'recommended_status': 'duplicate', 'file': fn, 'canonical_id': canon, 'evidence': ev})
        dups.append(r)

    review = []
    for cid, fn, ev in REVIEW:
        r = base(cid)
        r.update({'recommended_status': 'requires human review', 'file': fn, 'reason': ev})
        review.append(r)

    excl = []
    for cid, fn, ev in EXCLUDED:
        r = base(cid)
        r.update({'recommended_status': 'excluded', 'file': fn, 'reason': ev})
        excl.append(r)

    art = {
        'batch_id': 'go2009-bond-cluster-research-2026-09-11',
        'lane': 'Claude research lane: a further substantive pending-review cluster',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cluster': 'City of Albuquerque 2009 general obligation bond document set under cip-documents/2009-go-bond-documents.',
        'scope': 'All 35 pending-review candidates in that directory. The directory already held 16 validated, 26 duplicate, and 1 implemented record before this review.',
        'method': ('Fetched every pending file directly to a scratch directory without touching shared inventory state and recorded exact byte size and SHA-256. '
                   'Compared all 35 hashes against each other and against every checksum in master-inventory.json. '
                   'Extracted text and ran normalized similarity plus a five-or-more-letter token-coverage test against the canonical Community Facilities scope and summary sheets, and fetched twelve already-decided counterpart files to test the "1"-prefixed variants directly.'),
        'classification_only': True,
        'shared_state_written': [],
        'canonical_anchors': {
            'community_facilities_summary': CF_SUM,
            'community_facilities_scopes': CF_SCOPE,
            'go_bond_totals': TOTALS,
            'storm_sewer_system_bonds': STORM_BONDS,
            'parks_recreation_bonds': PARKS_BONDS,
            'parks_rec_summary': PARKS_SUM,
        },
        'duplicate_and_supersession_checks': {
            'byte_identical_to_already_decided_records': 4,
            'text_identical_pairs_found': 3,
            'containment_relationships_found': 2,
            'internal_byte_collisions_among_the_35': 0,
            'note': ('Four files are byte-identical to already-decided records. Three further pairs are identical in normalized text while differing by two or three bytes of PDF encoding, so a hash-only check would have missed them. '
                     'Two single-page summaries are contained verbatim within their two-page counterparts.'),
        },
        'integration_flags': [
            {'severity': 'correctness',
             'affects': ['src-4204206743b66c6c', 'src-5c9206c81408ce50', 'src-3ef781d4a038852a'],
             'finding': ('These three records are already terminal as duplicates whose recorded canonical is src-b3d0cd2df96d0bc6, the 2009 Community Facilities summary, on the stated ground that the Public Safety, Police, and Family and Community Services schedules are contained within it. '
                         'Direct measurement does not support that: the Community Facilities summary contains zero occurrences of "Fire" and zero of "Police", and its three "Public Safety" mentions are an EDACS and microwave communications sub-block, not the fire or police schedules. '
                         'For Family and Community Services, the Holiday Park, Pat Hurley, and Storehouse rows are absent from the canonical.'),
             'recommended_action': 'The Codex integration lane should re-examine these three terminal rulings. This research lane did not modify them.'},
            {'severity': 'advisory',
             'affects': ['src-b7ef66c741b8a886'],
             'finding': 'The complete two-page fire_-_summary.pdf appends a Council neighborhood set-aside table as its second page, so its title should not imply the file is exclusively a Fire schedule.',
             'recommended_action': 'Describe it accurately if it is published, or prefer the pure one-page schedule if a clean Fire-only record is wanted.'},
        ],
        'counts': {
            'reviewed': 35,
            'approved_for_addition': len(approved),
            'duplicate': len(dups),
            'requires_human_review': len(review),
            'excluded': len(excl),
            'superseded': 0,
        },
        'link_check': {'checked': 35, 'http_200': 35, 'failed': 0},
        'approved_for_addition': approved,
        'duplicate': dups,
        'requires_human_review': review,
        'excluded': excl,
        'integration_note': ('Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. '
                            'Every duplicate row carries a canonical_id. R2 archival is not authorized by this artifact.'),
        'safeguards': ['no master-inventory.json write', 'no checkpoint.json write', 'no site content change',
                       'no R2 upload', 'no commit, merge, or deploy'],
    }

    total = sum(art['counts'][k] for k in ('approved_for_addition', 'duplicate', 'requires_human_review', 'excluded', 'superseded'))
    assert total == 35, 'classification does not cover all 35 candidates: %d' % total

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(art, indent=1))
    print(json.dumps({'reviewed': 35, 'approved': len(approved), 'duplicate': len(dups),
                      'requires_human_review': len(review), 'excluded': len(excl), 'output': OUT}))


if __name__ == '__main__':
    main()
