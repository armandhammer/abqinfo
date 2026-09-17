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
OUT = 'project-state/discovery/planning-udd-cluster-research-2026-09-11.json'

REDEV = 'content/development-land-use/redevelopment-plans.md'
DEVPROC = 'content/development-land-use/development-process.md'
FACIL = 'content/public-works/city-facilities.md'

APPROVED = [
    ('src-6d243844fe259b86', 'AirportMasterPlan-ExSum.pdf',
     'Albuquerque International Sunport Airport Master Plan Executive Summary', FACIL,
     'Summarizes the Albuquerque International Sunport master plan across forty-four pages, covering aviation demand forecasts, airfield and terminal requirements, land use, and the recommended development program for the airport.',
     'Image-only PDF; first page rendered and visually confirmed as the official Sunport Airport Master Plan Executive Summary. Fits the existing Aviation Facilities section.'),
    ('src-28418cab91a745a6', 'MRA-RedevPlan-BarelasNeighborhoodCommercialArea.pdf',
     'Barelas Neighborhood Commercial Area Revitalization Plan', REDEV,
     'Preserves the one-hundred-fifty-page Barelas neighborhood commercial area revitalization plan, documenting existing conditions, redevelopment strategy, land use, design direction, and implementation actions for the metropolitan redevelopment area.',
     'Image-only PDF; cover rendered and visually confirmed. ABQInfo already publishes many sibling metropolitan redevelopment plans from this same planning/UDD/MRA library, so the document class is established.'),
    ('src-33f990150811e7bb', 'UDD-SBroadwaySDP-MRA.pdf',
     'South Broadway Sector Development Plan', REDEV,
     'Preserves the one-hundred-fourteen-page South Broadway sector development plan as adopted and amended, covering land use, zoning, urban design, transportation, housing, and redevelopment policy for the South Broadway area.',
     'Cover text records "Adopted / Amended" with a 1/17/2018 City Planning stamp. A substantive adopted sector plan.'),
    ('src-7a08bd24a1a9dcae', 'UDD-SilverHillHOZGuidelines2017.pdf',
     'Silver Hill Historic Overlay Zone Design Guidelines: Early Automobile Suburbs', DEVPROC,
     'A ninety-six-page City Planning handbook of development guidelines for the Silver Hill historic zone, covering the early automobile suburb context, building types, materials, additions, landscaping, and review expectations for property owners.',
     'Largest document in the cluster at 37.7 MB with 169,791 extracted characters. A substantive published design handbook, not a form.'),
    ('src-bdf76c84223f82be', 'Official Albuquerque Plant Palette and Sizing List-2018-07-03.pdf',
     'Official Albuquerque Plant Palette and Sizing List', DEVPROC,
     'Establishes the City official plant palette and sizing list, rating trees and plants as generally or conditionally recommended, noting vitality issues, and setting the planting sizes accepted in City landscape review.',
     'Thirteen pages with 33,884 extracted characters including the tree ratings legend. An official technical standard used in development review.'),
    ('src-87b92910cd99400d', 'UDD-R-54-1990AnnexationPolicies.pdf',
     'City Annexation Policies Resolution R-54-1990', DEVPROC,
     'Adopts City of Albuquerque policies on annexation and repeals previous annexation policies, setting out the comprehensive-plan area designations, urban-service considerations, and statutory annexation methods the City applies.',
     'Image-only PDF; first page rendered and visually confirmed as Council Bill R-68, Enactment 54-1990, an enacted policy resolution.'),
    ('src-6d08320245cacfbd', 'FacilitatedMeetingsCriteria-IDO-16July2018.PDF',
     'Facilitated Meetings Criteria Under Integrated Development Ordinance Section 14-16-6-4(D)', DEVPROC,
     'Establishes the three criteria the City applies before requiring a City-sponsored facilitated meeting with neighborhood associations under the Integrated Development Ordinance, covering project complexity, decision-making authority, and likelihood of productive negotiation.',
     'Image-only PDF; rendered and visually confirmed as a signed 16 July 2018 interoffice memorandum from Planning Director David Campbell establishing binding administrative criteria.'),
    ('src-6370c534dac0c540', 'HistoricProtectionOverlayZones.pdf',
     'Historic Protection Overlay Zones Citywide Map', DEVPROC,
     'Maps all six Albuquerque historic protection overlay zones citywide as of May 2018, showing Old Town, 8th and Forrester, Fourth Ward, Huning Highland, EDo, and Silver Hill boundaries against the street and parcel network.',
     'Rendered: titled "HISTORIC PROTECTION OVERLAY ZONES", date printed 5/25/2018. The current post-Integrated Development Ordinance citywide map.'),
    ('src-ad7c091a07a0fb3f', 'EighthandForesterHPO.pdf',
     'Eighth and Forrester Historic Protection Overlay Zone Map', DEVPROC,
     'Maps parcel-level boundaries of the Eighth and Forrester historic protection overlay zone as of May 2018, identifying each address within the zone between Mountain Road, Lomas Boulevard, 7th Street, and 11th Street.',
     'Rendered: titled "Eighth & Forrester Historic Protection Overlay Zone", date 5/25/2018. Post-IDO successor to the January 2017 historic overlay zone map.'),
    ('src-ec6e7fdafdab0706', 'FourthWardHPO.pdf',
     'Fourth Ward Historic Protection Overlay Zone Map', DEVPROC,
     'Maps parcel-level boundaries of the Fourth Ward historic protection overlay zone as of May 2018, identifying each address within the zone for Landmarks Commission review of building projects.',
     'Post-IDO 5/25/2018 successor to the January 2017 Fourth Ward historic overlay zone map.'),
    ('src-75755583aa85c00c', 'HuningHighlandandEdoHPO.pdf',
     'Huning Highland and EDo Historic Protection Overlay Zone Map', DEVPROC,
     'Maps parcel-level boundaries of the Huning Highland and EDo historic protection overlay zones as of May 2018, identifying each address subject to Landmarks Commission review within the zones.',
     'Post-IDO 5/25/2018 successor to the January 2017 map. See integration_flags: the January 2017 version is already validated and archived to R2 as src-011ccfd869be15b6.'),
    ('src-c74168a5ee95e044', 'OldTownHPO.pdf',
     'Old Town Historic Protection Overlay Zone Map', DEVPROC,
     'Maps parcel-level boundaries of the Old Town historic protection overlay zone as of May 2018, replacing the former H-1 zone and buffer designation with the HPO-5 overlay boundary.',
     'Rendered: titled "Old Town Historic Protection Overlay Zone", date 5/25/2018, versus the 2017 sheet titled "OLD TOWN H-1 ZONE AND BUFFER".'),
    ('src-7f1e53975e461d43', 'SilverHillHPO.pdf',
     'Silver Hill Historic Protection Overlay Zone Map', DEVPROC,
     'Maps parcel-level boundaries of the Silver Hill historic protection overlay zone as of May 2018, identifying each address subject to Landmarks Commission review within the zone.',
     'Post-IDO 5/25/2018 successor to the January 2017 Silver Hill historic overlay zone map.'),
    ('src-1ee4a0c5133aceda', 'UDD-OldTownDevelopmentGuidelines-May2018.pdf',
     'Historic Old Town Development Standards and Guidelines (HPO-5)', DEVPROC,
     'Sets the Old Town development standards and guidelines effective May 17, 2018, covering the applicability area, Spanish Colonial, Territorial and Western Victorian architectural style standards, building setbacks, and Landmarks Commission review.',
     'States it is "effective as of May 17, 2018" and applies to the HPO-5 overlay "formerly designated H-1", incorporating the design standard amended with the Integrated Development Ordinance on November 13, 2017.'),
    ('src-d42df0916d0d8a2b', 'Assign Amend to Agreement IIA.pdf',
     'Assignment and Amendment to Agreement to Construct Infrastructure Improvements', DEVPROC,
     'Provides the City form for assigning and amending an agreement to construct infrastructure improvements, including the county clerk recording label, assignment terms, and amendment provisions used in development infrastructure agreements.',
     'ABQInfo already publishes six sibling Infrastructure Improvements Agreement forms plus the forms directory, and this assignment-and-amendment variant is not among them, so it completes an established published set rather than being a routine application form.'),
]

SUPERSEDED = [
    ('src-bac4020394541501', 'UDD-CityWideHOZMap-Jan2017.pdf', 'src-6370c534dac0c540',
     'Rendered comparison: this sheet is titled "HISTORIC OVERLAY ZONES AND URBAN CONSERVATION OVERLAY ZONE", date printed 1/17/2017, while its successor is titled "HISTORIC PROTECTION OVERLAY ZONES", date printed 5/25/2018. The Integrated Development Ordinance adopted November 13, 2017 renamed these zones, and the City reissued the citywide map.'),
    ('src-17cc5e45837a40bd', 'UDD-EighthForresterHOZMap-Jan2017.pdf', 'src-ad7c091a07a0fb3f',
     'Rendered comparison: "8TH/FORRESTER HISTORIC OVERLAY ZONE" dated 1/17/2017 versus "Eighth & Forrester Historic Protection Overlay Zone" dated 5/25/2018, covering the same parcels.'),
    ('src-a49aa4a2480d19fa', 'UDD-FourthWardHOZMap-Jan2017.pdf', 'src-ec6e7fdafdab0706',
     'January 2017 historic overlay zone sheet superseded by the May 2018 historic protection overlay zone sheet for the same area.'),
    ('src-a536b6a674de21dd', 'UDD-OldTownHOZMap-Jan2017.pdf', 'src-c74168a5ee95e044',
     'Rendered comparison: "OLD TOWN H-1 ZONE AND BUFFER" dated 1/17/2017 versus "Old Town Historic Protection Overlay Zone" dated 5/25/2018. The H-1 designation and its 300-foot buffer were replaced by the HPO-5 overlay.'),
    ('src-ddd2b59a795fd6dd', 'UDD-SilverhillHOZMap-Jan2017.pdf', 'src-7f1e53975e461d43',
     'January 2017 historic overlay zone sheet superseded by the May 2018 historic protection overlay zone sheet for the same area.'),
    ('src-4c2561ce7ebb4217', 'UDD-OldTownDevelopmentGuidelines-Nov2017.pdf', 'src-1ee4a0c5133aceda',
     'This version states the guidelines apply "in the H-1 Historic Old Town Zone and in the 300 foot buffer zone", the pre-Integrated Development Ordinance designation. The May 2018 version is expressly "effective as of May 17, 2018" and restates the same guidelines for the HPO-5 zone "formerly designated H-1", so it is the current adopted text.'),
]

EXCLUDED = [
    ('src-14031a31fb090a9f', 'BLANK PRT Notes Form Jan2023 SPANISH.pdf',
     'Blank Spanish-language pre-application review notes form with empty fields for project number, date, and site address. A routine application form carrying no plan, policy, or project record.'),
    ('src-fe7cf8a2c849e2a5', 'BLANK PRT Notes Form Sept 2022 fin.pdf',
     'Blank English-language pre-application review notes form with empty fields. A routine application form.'),
    ('src-7df872bf2933c807', 'Development_Application.pdf',
     'The City development review application form effective 4/17/19, consisting of checkboxes and submittal instructions. A routine application form.'),
    ('src-abd5f8981b599450', 'DRT-Application-07-5-16.pdf',
     'Design Review Team application form from July 2016. A routine application form.'),
    ('src-d361615fe43b91c4', 'DRT-ApprovalForm-7-6-16.pdf',
     'Design Review Team approval action form from July 2016, a blank decision sheet with fields for case number, date, and time. A routine administrative form.'),
    ('src-c18e640752df0720', 'DRT-InfoSheet-07-5-16.pdf',
     'Design Review Team informational handout explaining how to obtain feedback on drawings before building permit submittal. Customer-service guidance rather than a durable policy record.'),
    ('src-3021f7eb31b05b17', 'FormP3.pdf',
     'Form P3 application checklist for administrative decisions and minor amendments, listing required submittal materials. A routine application form.'),
    ('src-e3a57019d0552ccb', 'UDD-FormP1-Rev8-2017.pdf',
     'Form P1 application checklist for site development plan review at Environmental Planning Commission public hearing, listing maximum sizes and required submittals. A routine application form.'),
    ('src-eaa340591eafd28a', 'Zone Change PRT handout_3-23 SPANISH.pdf',
     'Spanish-language public handout explaining how to request a zone change and what zoning designations mean. Public-information material rather than an adopted plan or policy.'),
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
            'link_check': 'HTTP 200 verified 2026-09-11',
        }

    approved = []
    for cid, fn, title, page, desc, ev in APPROVED:
        r = base(cid)
        r.update({'recommended_status': 'approved for addition', 'file': fn, 'title': title,
                  'description': desc, 'description_word_count': len(desc.split()),
                  'proposed_canonical_page': page, 'evidence': ev})
        approved.append(r)

    sup = []
    for cid, fn, canon, ev in SUPERSEDED:
        r = base(cid)
        r.update({'recommended_status': 'superseded', 'file': fn, 'canonical_id': canon, 'evidence': ev})
        sup.append(r)

    excl = []
    for cid, fn, ev in EXCLUDED:
        r = base(cid)
        r.update({'recommended_status': 'excluded', 'file': fn, 'reason': ev})
        excl.append(r)

    art = {
        'batch_id': 'planning-udd-cluster-research-2026-09-11',
        'lane': 'Claude research lane: documents.cabq.gov/planning/UDD cluster',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cluster': 'City of Albuquerque Planning Urban Design and Development library at documents.cabq.gov/planning/UDD.',
        'scope': 'All 30 pending-review candidates in that directory.',
        'method': ('Fetched every file to a scratch directory without touching shared inventory state and recorded exact byte size and SHA-256. '
                   'Extracted text and ran normalized-similarity comparison across all 30. '
                   'Because overlay-zone maps extract only unordered parcel-address labels, text similarity is unreliable for them, so every map and every image-only PDF was rendered and read visually.'),
        'classification_only': True,
        'shared_state_written': [],
        'key_finding': ('The Integrated Development Ordinance adopted November 13, 2017 renamed Albuquerque historic overlay zones: the H-1 Old Town zone and the Historic Overlay Zones became Historic Protection Overlay zones. '
                        'The City reissued the whole map series on 5/25/2018 and reissued the Old Town standards effective 5/17/2018. '
                        'Every January 2017 sheet in this directory therefore has a direct post-ordinance successor, which the file names alone do not reveal.'),
        'duplicate_and_supersession_checks': {
            'internal_byte_collisions': 0,
            'cross_inventory_byte_collisions': 0,
            'text_similarity_pairs_over_0_80': 0,
            'supersession_pairs_found_by_rendering': 6,
            'note': ('No byte or text duplicates exist in this cluster. All six supersession relationships were established by rendering and reading the documents, '
                     'because the printed title and date carry the version information while the extracted text does not.'),
        },
        'integration_flags': [
            {'severity': 'consistency',
             'affects': ['src-011ccfd869be15b6'],
             'finding': ('src-011ccfd869be15b6 is already validated and archived to R2 as maps/cabq-huning-highland-edo-historic-overlay-zone-map-2017.pdf. '
                         'It is the January 2017 Huning Highland and EDo historic overlay zone map, which this research finds superseded by the May 2018 historic protection overlay zone map src-75755583aa85c00c recommended above.'),
             'recommended_action': ('Decide the site-wide treatment of the January 2017 sheets. Either publish the 2018 maps as current and relabel the archived 2017 map as a historical pre-ordinance boundary record, '
                                    'or retain both as a labelled version pair. Claude did not modify this terminal validated record. The five other 2017 sheets are recommended superseded on the same reasoning, so the two decisions should be made together.')},
        ],
        'counts': {
            'reviewed': 30,
            'approved_for_addition': len(approved),
            'superseded': len(sup),
            'excluded': len(excl),
            'duplicate': 0,
            'requires_human_review': 0,
        },
        'link_check': {'checked': 30, 'http_200': 30, 'failed': 0},
        'approved_for_addition': approved,
        'superseded': sup,
        'excluded': excl,
        'integration_note': ('Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. '
                            'Every superseded row carries a canonical_id. R2 archival is not authorized by this artifact. '
                            'Note that src-7a08bd24a1a9dcae is 37.7 MB and src-33f990150811e7bb is 14.3 MB, so any future archival plan must check the size thresholds.'),
        'safeguards': ['no master-inventory.json write', 'no checkpoint.json write', 'no site content change',
                       'no R2 upload', 'no commit, merge, or deploy'],
    }

    total = sum(art['counts'][k] for k in ('approved_for_addition', 'superseded', 'excluded', 'duplicate', 'requires_human_review'))
    assert total == 30, 'classification does not cover all 30 candidates: %d' % total

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(art, indent=1))
    print(json.dumps({'reviewed': 30, 'approved': len(approved), 'superseded': len(sup),
                      'excluded': len(excl), 'output': OUT}))


if __name__ == '__main__':
    main()
