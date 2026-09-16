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
OUT = 'project-state/discovery/code-enforcement-cluster-research-2026-09-11.json'

DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'
SAFETY = 'content/city-data/public-safety-data.md'

APPROVED = [
    ('src-07ce09fd200d2d69', 'Compleated  Problem Properties.pdf',
     'Completed Problem Properties Snapshot, Through June 2026', SAFETY,
     'The City cumulative code-enforcement snapshot lists completed problem-property cases from calendar year 2019 through June 2026, identifying each address, the enforcing agency, the enforcement action taken, how compliance was achieved, and the completion date.',
     'Five pages and 17,509 extracted characters covering calendar years 2019 through 2026, ending with a June 2026 entry. This continues the same cumulative series as the validated March 2024 snapshot and extends it by more than two years. See integration_flags.'),
    ('src-f19a78a166008dae', 'CE-WeedHandbook2012.pdf',
     'Weed Identification Handbook, 2012', DEVPROC,
     'The City Planning Department handbook identifies weeds regulated under Albuquerque property-maintenance and nuisance rules, providing photographs and identifying characteristics so property owners and inspectors can recognize the species subject to abatement.',
     'Image-only nineteen-page PDF of 15.98 MB; the cover was rendered and read as "Weed Identification Handbook 2012", Planning Department, under Mayor Richard J. Berry. A published departmental handbook, not a form.'),
    ('src-c5ed372e33966029', 'CodeEnf-ZoningCodeAmendment-O-39.pdf',
     'Zoning Code Amendment Ordinance O-17-39: Garage and Yard Sales', DEVPROC,
     'Amends Albuquerque Zoning Code section 14-16-2-6(A)(2)(c) to increase the permitted number of garage or yard sales in an R-1 zone from one a year to two a year and to clarify the time period during which such sales are allowed.',
     'Enacted ordinance text with bracketed new and strikethrough deleted material, Council Bill O-17-39 sponsored by Don Harris. Legislation rather than an application form.'),
    ('src-d8dd331b50fe7e9a', 'Shared Parking Agreement  Requirements  Sample.pdf',
     'Shared Parking Agreement Requirements and Sample', DEVPROC,
     'Sets what a shared parking agreement submitted to the City Planning Department must contain, citing Integrated Development Ordinance section 5-5(C)(5) on parking reductions, credits and allowances, and supplying a sample agreement for applicants to follow.',
     'Six pages dated 07/18/2024 with citations to the 2024 Integrated Development Ordinance annual update. A current adopted requirements standard, distinct from the blank application forms in this directory.'),
    ('src-092548fef85b887b', 'CodeEnf-Xeriscape101Brochure.pdf',
     'Xeriscape 101 Guide', DEVPROC,
     'The City guide to water-efficient landscaping explains xeriscape principles, planning and design, soil preparation, practical turf areas, efficient irrigation, mulching, plant selection, and maintenance for Albuquerque yards and landscapes.',
     'Three pages but 25,372 extracted characters, an order of magnitude more substantive content than the one-page public handouts excluded elsewhere. A published City guide on water-efficient landscaping, complementing the official plant palette.'),
]

DUPLICATES = [
    ('src-77fc6b8921fe85bb', 'Development_Application.pdf', 'src-7df872bf2933c807',
     'Byte-identical to the Planning UDD copy of the same file, SHA-256 136a1bcce639179a6e1a58ad92b17a99b2a56d3984caa263f79e53f16927feca. The City publishes one development review application in two library folders. The UDD copy is recommended excluded as a routine application form in the Planning UDD artifact, so neither copy is published; this record exists to preserve the cross-directory relationship.'),
    ('src-18709c458f6f7f65', 'code-enforcement-zoning', 'src-849f1acc0cf7fcd3',
     'Byte-identical to the code-enforcement landing page. Both fetches return the same HTML document titled "Code Enforcement - City of Albuquerque"; the two candidate URLs resolve to one navigation page.'),
]

REVIEW = [
    ('src-333e4b4b3970edc1', 'Code-WTF-StaffAppReviewChecklist-May2017.pdf',
     'A hybrid record that the directory precedent does not settle. It runs ten pages and 23,168 characters and states it is "based on section 14-16-3-17 ROA 1994, most recent revision effective December 22, 2014", so it documents how the City applies a named zoning-code section to wireless telecommunications facilities, which reads as a durable enforcement standard. Against that, it is written as an internal staff routing sheet with fill-in blanks such as "Are there any comments from the City Engineer that the applicant needs to address?", and the Planning UDD artifact recommends excluding Form P1 and Form P3 review checklists. Decide whether staff review checklists that interpret a specific code section are retained as standards or excluded with applicant forms.'),
]

EXCLUDED = [
    ('src-849f1acc0cf7fcd3', 'code-enforcement',
     'Not a document. The fetched bytes are an HTML page titled "Code Enforcement - City of Albuquerque", the Plone directory listing for this cluster.'),
    ('src-6eee99e375ac4587', 'Code-ElectronicSignAffidavit.pdf',
     'Blank affidavit and application for an electronic sign permit. A routine application form.'),
    ('src-73d8d1859ed00404', 'Code-IlluminatedSignAffidavit.pdf',
     'Blank affidavit for illuminated sign regulations. A routine application form.'),
    ('src-db9d6c1a5a30718c', 'Code-WTFCollocationApp-2015.pdf',
     'Blank collocation application for wireless telecommunications facilities. A routine application form.'),
    ('src-50ae58d39d230e0c', 'CodeEnf-FamilyDayCareApplication.pdf',
     'Blank application for a family daycare home occupation. A routine application form.'),
    ('src-e55c9574d36c58da', 'CodeEnf-FirearmsAffidavit-May2016.pdf',
     'Agreement of terms and conditions for the sale of firearms from a residential zone. The companion firearms application src-0062e37bac5c9635 was already excluded as unrelated to ABQInfo transportation, land-use, infrastructure, or public-services scope; the same reasoning applies.'),
    ('src-2805e88213942cb1', 'CodeEnf-FormP-6-Rev2017.pdf',
     'Blank intake checklist recording fees collected and case numbers assigned. A routine administrative form.'),
    ('src-448779695384aa97', 'CodeEnf-LiquorApplication-May2016.pdf',
     'Blank zoning application for a liquor license. A routine application form, and 0.9946 identical to CodeEnf-ZoningLiquorLicenseApplication.pdf.'),
    ('src-7cbd36eb38fffc24', 'CodeEnf-LiquorLicenseApplication-2017.PDF',
     'Image-only PDF; rendered and read as a blank "Application for Liquor License" from the Zoning Enforcement Division. A routine application form.'),
    ('src-98913dfff8fe19af', 'CodeEnf-SmallLoanBizApp-Dec2015.pdf',
     'Blank small loan business application. A routine application form.'),
    ('src-365cf43d14814f09', 'CodeEnf-VBRform-July2016.pdf',
     'Blank vacant building registration application. The August 2015 edition of the same form, src-1c9c7fbbc9ccc8a8, was already excluded because users should follow the City current process rather than an archived form.'),
    ('src-ab3c4e31514ec7a7', 'CodeEnf-WallPermitApplication-2017.PDF',
     'Image-only PDF; rendered and read as a blank "Application for Small Wall Permit". A routine application form.'),
    ('src-dabc4e0760fc88c8', 'CodeEnf-ZonalCertificationRequestApplication.pdf',
     'Blank zoning certification request application. One of three near-identical versions of the same form in this directory.'),
    ('src-3bb4a6357e224c42', 'CodeEnf-ZoningLiquorLicenseApplication.pdf',
     'Blank zoning application for a liquor license, 0.9946 identical to CodeEnf-LiquorApplication-May2016.pdf. A routine application form.'),
    ('src-1f1f6270c4b8deb7', 'CodeEnf-ZoningVerificationRequest-2017.pdf',
     'Zoning verification request form with helpful-hints instructions. A routine application form.'),
    ('src-f00d9ac62f70e82a', 'Deviation Application.pdf',
     'Blank Code Enforcement Division deviation application. A routine application form.'),
    ('src-f0a97a7ddde4e74f', 'Housing_Appeal_and_Request_for_Hearing.pdf',
     'Blank housing appeal and hearing request form to be emailed or mailed to named staff. A routine administrative form.'),
    ('src-13cbcd34d22eb3db', 'Public Notice Instructions.pdf',
     'One-page procedural instruction sheet dated 01.17.2025 explaining how to obtain a neighborhood association contact list and send public notice. Operational instructions rather than an adopted standard, matching the treatment of comparable public handouts.'),
    ('src-3662b2e02585d059', 'Request-Zonal Certification-7-21.pdf',
     'Blank zoning certification request application, 0.9295 and 0.9617 similar to the two other versions of the same form in this directory.'),
    ('src-e0628c393a60e09a', 'SIGN POSTING AGREEMENT Site Plan Admin-2024.pdf',
     'Sign posting agreement requirements and acknowledgement for administrative site plan applications. A routine application-stage agreement form.'),
    ('src-fde0f807b3c2eca9', 'UPDATED Zonal Certification Application.pdf',
     'Blank zoning certification request application, 0.9965 identical to CodeEnf-ZonalCertificationRequestApplication.pdf. The newest of three versions of the same form, all routine.'),
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
            'size_bytes': meta[cid]['bytes'],
            'checksum_sha256': meta[cid]['sha'],
            'pages': prof[cid]['pages'],
            'content_kind': prof[cid].get('kind'),
            'link_check': 'HTTP 200 verified 2026-09-11',
        }

    approved = []
    for cid, fn, title, page, desc, ev in APPROVED:
        r = base(cid)
        r.update({'recommended_status': 'approved for addition', 'file': fn, 'title': title,
                  'description': desc, 'description_word_count': len(desc.split()),
                  'proposed_canonical_page': page, 'evidence': ev})
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
        'batch_id': 'code-enforcement-cluster-research-2026-09-11',
        'lane': 'Claude research lane: documents.cabq.gov/planning/code-enforcement cluster',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cluster': 'City of Albuquerque Planning Department code-enforcement document library at documents.cabq.gov/planning/code-enforcement.',
        'scope': 'All 29 pending-review candidates in that directory. The directory already held 2 validated records, 4 excluded, and 1 superseded.',
        'method': ('Fetched every file to a scratch directory without touching shared inventory state and recorded exact byte size and SHA-256. '
                   'Checked the leading bytes of each fetch so HTML pages served under PDF-looking candidate URLs were detected rather than mis-parsed. '
                   'Extracted text, ran normalized-similarity comparison across the cluster, and rendered every file with no extractable text.'),
        'classification_only': True,
        'shared_state_written': [],
        'precedent_applied': ('This directory already draws the line the lane asks for. Regulatory packets and data snapshots are validated: '
                              'src-2d17d01d04c78c38 (Community Residential Program and Emergency Shelter Regulations) and src-6e1166ed8ae8f0e5 (Completed Problem Properties snapshot). '
                              'Registration and application forms are excluded: src-1c9c7fbbc9ccc8a8, src-0062e37bac5c9635, src-4b1eef3fed31d045, src-8ebda64242416f86. '
                              'An earlier cumulative snapshot was superseded by a later one: src-4c0d4f6dbc0c78a1. Those three rules decide almost every record below.'),
        'duplicate_and_supersession_checks': {
            'internal_byte_collisions': 1,
            'cross_directory_byte_collisions': 1,
            'near_identical_form_versions_found': 4,
            'note': ('Two candidate URLs resolve to the same HTML landing page. One pending file is byte-identical to a Planning UDD record reviewed in a separate lane. '
                     'Three versions of the zoning certification request application (0.9295 to 0.9965 similar) and two versions of the liquor licence application (0.9946) sit in this directory; '
                     'all are routine forms, so the version relationships are recorded but do not affect publication.'),
        },
        'integration_flags': [
            {'severity': 'currency',
             'affects': ['src-6e1166ed8ae8f0e5'],
             'finding': ('src-6e1166ed8ae8f0e5 is validated and placed on the public-safety data page as the "Completed Problem Properties Snapshot, March 2024". '
                         'The pending file src-07ce09fd200d2d69 is the same cumulative series carried forward: it covers calendar years 2019 through 2026 and ends with a June 2026 entry, '
                         'so the published snapshot is more than two years out of date. The directory already set this precedent once, superseding the December 2023 snapshot src-4c0d4f6dbc0c78a1 with the March 2024 one.'),
             'recommended_action': ('Treat src-07ce09fd200d2d69 as the current snapshot and supersede src-6e1166ed8ae8f0e5, matching the earlier December 2023 to March 2024 transition. '
                                    'Claude did not modify that terminal validated record. Note the newer file carries no date in its filename, so the title should state the June 2026 coverage explicitly.')},
        ],
        'counts': {
            'reviewed': 29,
            'approved_for_addition': len(approved),
            'duplicate': len(dups),
            'requires_human_review': len(review),
            'excluded': len(excl),
            'superseded': 0,
        },
        'link_check': {'checked': 29, 'http_200': 29, 'failed': 0},
        'approved_for_addition': approved,
        'duplicate': dups,
        'requires_human_review': review,
        'excluded': excl,
        'integration_note': ('Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. '
                            'Every duplicate row carries a canonical_id. R2 archival is not authorized by this artifact. '
                            'src-f19a78a166008dae is 15.98 MB, so any future archival plan must check the size thresholds.'),
        'safeguards': ['no master-inventory.json write', 'no checkpoint.json write', 'no site content change',
                       'no R2 upload', 'no commit, merge, or deploy'],
    }

    total = sum(art['counts'][k] for k in ('approved_for_addition', 'duplicate', 'requires_human_review', 'excluded', 'superseded'))
    assert total == 29, 'classification does not cover all 29 candidates: %d' % total

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(art, indent=1))
    print(json.dumps({'reviewed': 29, 'approved': len(approved), 'duplicate': len(dups),
                      'requires_human_review': len(review), 'excluded': len(excl), 'output': OUT}))


if __name__ == '__main__':
    main()
