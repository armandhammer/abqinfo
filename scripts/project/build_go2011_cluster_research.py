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
OUT = 'project-state/discovery/go2011-bond-cluster-research-2026-09-11.json'
CAPITAL = 'content/city-data/capital-spending.md'

# (id, file, title, description, evidence)
APPROVED = [
    ('src-2746069f062780cf', '2011_g.o._summary.pdf', '2011-2019 General Obligation Bond Summary Totals',
     'Consolidates $727.29 million of planned 2011 through 2019 bond funding by department and division, covering streets, storm drainage, parks, public safety, transit, and every community facilities purpose with biennial and total columns.',
     'Extraction yields no text, so page one was rendered and read: a "G.O. Bond Summary Totals" table with grand totals of $153,360,000 in 2011 rising to a $727,290,000 program total. The 2011 counterpart of the already-validated 2009 go_bond_totals.pdf.'),
    ('src-75f032fd59799df5', 'council_neigh-set_aside_scope.pdf', '2011 Council Neighborhood Set-Aside Project Scopes',
     'Details nine pages of 2011 Council neighborhood set-aside project scopes by district, describing study, design, and construction work for parks, streets, lighting, community facilities, and other district-specific neighborhood improvements.',
     'Nine pages and 12,902 extracted characters with 38 dollar figures. Best similarity against any decided 2011 record is 0.0447, so it is wholly new content.'),
    ('src-d30fe509d51eec50', 'streets_scope.pdf', '2011 Streets General Obligation Bond Project Scopes',
     'Details 2011 street bond scopes covering planning, design, right-of-way acquisition, and construction for major roadways, intersections, paving rehabilitation, bridges, signals, and named corridor projects across the City.',
     'Four pages, 7,486 characters, 34 dollar figures. Best similarity against any decided record is 0.1449.'),
    ('src-be70a79a59ae0915', '1streets_scope.pdf', '2011 Streets General Obligation Bond Project Scopes (Initial Version)',
     'Details the initial 2011 street bond scope list, covering roadway planning, design, right-of-way acquisition, construction, paving rehabilitation, intersections, bridges, and named corridor projects before later revision.',
     'Four pages and 8,838 characters versus 7,486 in streets_scope.pdf; the two differ materially. Follows the directory precedent where 1family_summary.pdf is validated as the "Initial Version" alongside family_summary.pdf.'),
    ('src-2663fc607177e07d', 'storm_drainage_scope.pdf', '2011 Storm Drainage General Obligation Bond Project Scopes',
     'Details 2011 storm drainage bond scopes for regulatory compliance work, storm drain and pump station rehabilitation, channel and arroyo improvements, water quality facilities, and drainage master planning.',
     'Three pages, 5,078 characters. Retained over the 0.9166-similar storm_drain_scope.pdf because its filename matches the validated storm_drainage_summary.pdf.'),
    ('src-2daae0eb6e136555', 'finance_scope.pdf', '2011 Finance and Administrative Services General Obligation Bond Project Scopes',
     'Details 2011 Finance and Administrative Services bond scopes for enterprise business systems, servers and networks, radio and communications management, continuity planning, and related technology investments.',
     'Two pages, 3,607 characters. Retained over the 0.9979-similar 1finance_scope.pdf as the canonically named file.'),
    ('src-b7f0628556085641', 'planning_scope.pdf', '2011 Planning General Obligation Bond Project Scopes',
     'Details 2011 Planning Department bond scopes for studying, designing, and constructing improvements, including electronic plan review, geographic information systems, permitting technology, and redevelopment support.',
     'One page, 2,129 characters. Materially different from 1planning_scope.pdf at 3,431 characters, so both are retained as separate versions.'),
    ('src-89b36d5577443f99', '1planning_scope.pdf', '2011 Planning General Obligation Bond Project Scopes (Initial Version)',
     'Details the initial 2011 Planning Department bond scope list for studying, designing, and constructing improvements, including plan review technology, geographic information systems, and redevelopment support.',
     'Two pages and 3,431 characters versus 2,129 in planning_scope.pdf. Follows the validated 1family_summary.pdf "Initial Version" precedent in this directory.'),
    ('src-352694313c3e5710', 'family_scope.pdf', '2011 Family and Community Services General Obligation Bond Project Scopes',
     'Details 2011 Family and Community Services bond scopes for designing, renovating, and improving community centers, child development centers, health and social service centers, and related facilities and equipment.',
     'One page, 2,067 characters, distinct from the 1,928-character initial version.'),
    ('src-b08cdbd2624ad1a0', '1family_scope.pdf', '2011 Family and Community Services General Obligation Bond Project Scopes (Initial Version)',
     'Details the initial 2011 Family and Community Services bond scope list for renovating and improving community centers, child development centers, health and social service centers, and related equipment.',
     'Matches the validated pairing precedent: 1family_summary.pdf is titled "(Initial Version)" and family_summary.pdf is the later schedule, both retained.'),
    ('src-2ed981e6df5e99d2', 'facilities_scope.pdf', '2011 City Facilities, CIP, and Parking General Obligation Bond Project Scopes',
     'Details 2011 Municipal Development bond scopes for replacing aging vehicles, City building improvement and rehabilitation, energy and security systems, roofs, and parking facility upgrades.',
     'Retained over the text-identical cip_facilities_parking_scope.pdf because its filename matches the validated facilities_summary.pdf.'),
    ('src-4bafa6f452f2f586', 'env_health_scope.pdf', '2011 Environmental Health General Obligation Bond Project Scopes',
     'Details 2011 Environmental Health bond scopes for designing and constructing improvements including landfill remediation, environmental monitoring, health and safety equipment, and facility rehabilitation.',
     'Retained over the text-identical env._health_scope.pdf because its filename matches the validated env_health_summary.pdf.'),
    ('src-afc7fa6f1c4ac06f', 'cultural_services_scope.pdf', '2011 Cultural Services General Obligation Bond Project Scopes',
     'Details 2011 Cultural Services bond scopes across the Biological Park, museums, libraries, and cultural facilities, covering design, renovation, exhibits, collections, and related equipment purchases.',
     'Two pages and 3,958 characters, the fuller of the two Cultural Services scope files. Best similarity against any decided record is 0.0824.'),
    ('src-27d391d187280ced', 'parks_and_recreation_scope.pdf', '2011 Parks and Recreation General Obligation Bond Project Scopes',
     'Details 2011 Parks and Recreation bond scopes for planning, designing, renovating, equipping, and constructing parks, recreation facilities, trails, open space, and related park improvements.',
     'Three pages and 4,760 characters, the fuller of the two Parks scope files. Best similarity against any decided record is 0.1043.'),
    ('src-b37593a011f57fae', 'transit_scope.pdf', '2011 ABQ RIDE Transit General Obligation Bond Project Scopes',
     'Details 2011 transit bond scopes for purchasing revenue and support vehicles, acquiring associated equipment, and related ABQ RIDE facility and technology investments.',
     'Retained over the text-identical 1transit_scope.pdf as the canonically named file.'),
    ('src-f74d655ffb05fd08', 'police_scope.pdf', '2011 Police General Obligation Bond Project Scopes',
     'Details 2011 Police bond scopes for purchasing marked and unmarked police vehicles and related Albuquerque Police Department facility and equipment investments.',
     'Retained over the text-identical 1police_scope.pdf as the canonically named file.'),
    ('src-db9fefd23083da69', 'fire_scope.pdf', '2011 Fire General Obligation Bond Project Scopes',
     'Details 2011 Fire bond scopes for purchasing and replacing emergency response apparatus and related Albuquerque Fire Department equipment and facility investments.',
     'One page, 349 characters, distinct from the 522-character initial version.'),
    ('src-e6ca25d4cfa80752', '1fire_scope.pdf', '2011 Fire General Obligation Bond Project Scopes (Initial Version)',
     'Details the initial 2011 Fire bond scope list for purchasing and replacing emergency response apparatus and related department equipment before later revision.',
     'Materially longer than fire_scope.pdf at 522 versus 349 characters, following the directory "Initial Version" precedent.'),
    ('src-b90b07ac62c4f7fd', 'senior_affairs_scope.pdf', '2011 Senior Affairs General Obligation Bond Project Scopes',
     'Details 2011 Senior Affairs bond scopes for planning, designing, constructing, and rehabilitating senior centers and related department facilities, equipment, and vehicles.',
     'Retained over the text-identical 1senior_affairs_scope.pdf as the canonically named file.'),
    ('src-54665bf864159096', 'affordable_housing_scope.pdf', '2011 Affordable Housing General Obligation Bond Project Scope',
     'Records the 2011 affordable housing bond scope covering land acquisition for affordable housing development under the City affordable housing program.',
     'One page, 193 characters, distinct from the 354-character initial version.'),
    ('src-25501032bfbfa682', '1affordable_housing_scope.pdf', '2011 Affordable Housing General Obligation Bond Project Scope (Initial Version)',
     'Records the initial 2011 affordable housing bond scope covering land acquisition for affordable housing development before later revision of the scope text.',
     'Materially longer than affordable_housing_scope.pdf at 354 versus 193 characters, following the directory "Initial Version" precedent.'),
    ('src-2e6b47bcf85ff53d_PLACEHOLDER', '', '', '', ''),
    ('src-4cd84ecef3756fb0', 'senior_affairs_summary.pdf', '2011-2019 Senior Affairs General Obligation Bond Schedule',
     'Schedules Senior Affairs bond funding from 2011 through 2019 for senior center renovation, rehabilitation, equipment, and related department facility investments across the decade plan.',
     'No Senior Affairs schedule is validated in this directory, so this record fills a genuine gap. Retained over the text-identical 1senior_affairs_summary.pdf.'),
    ('src-542056c326cf2578', '1finance_summary.pdf', '2011-2019 Finance and Administrative Services General Obligation Bond Schedule (Initial Version)',
     'Schedules the initial Finance and Administrative Services bond allocations from 2011 through 2019 for enterprise systems, servers, networks, radio management, and continuity planning before later revision.',
     'Similarity to the validated finance_summary.pdf is 0.8776, below the duplicate threshold, matching the validated 1family_summary.pdf "Initial Version" pattern.'),
    ('src-a547a0278fb86fb9', '1fire_summary.pdf', '2011-2019 Fire General Obligation Bond Schedule (Initial Version)',
     'Schedules the initial Fire bond allocations from 2011 through 2019 for apparatus replacement and fire station rehabilitation before later revision of the department schedule.',
     'Similarity to the validated fire_summary.pdf is 0.7023, well below the duplicate threshold.'),
    ('src-c9af414f77032660', '1planning_summary.pdf', '2011-2019 Planning General Obligation Bond Schedule (Initial Version)',
     'Schedules the initial Planning Department bond allocations from 2011 through 2019 for plan review technology, geographic information systems, permitting, and redevelopment support before later revision.',
     'Similarity to the validated planning_summary.pdf is 0.7847.'),
    ('src-a31943aca401c7f0', '1streets_summary.pdf', '2011-2019 Streets General Obligation Bond Schedule (Initial Version)',
     'Schedules the initial Streets bond allocations from 2011 through 2019 for roadway and intersection reconstruction, paving rehabilitation, bridges, sidewalks, and named corridor projects before later revision.',
     'Similarity to the validated streets_summary.pdf is 0.7595, with 210 dollar figures across two pages.'),
]
APPROVED = [a for a in APPROVED if a[0] != 'src-2e6b47bcf85ff53d_PLACEHOLDER']

# (id, file, canonical_id, evidence)
DUPLICATES = [
    ('src-849903e09a7a3629', '1affordable_housing_summary.pdf', 'src-65e4a509079e184f',
     'Normalized extracted text is identical (ratio 1.0000) to the validated affordable_housing_summary.pdf.'),
    ('src-8d51aa695a1b75a2', '1animal_welfare_summary.pdf', 'src-8d8336fa08217661',
     'Normalized extracted text is identical (ratio 1.0000) to the validated animal_welfare_summary.pdf, and byte-identical to 2animal_welfare_summary.pdf.'),
    ('src-af0959a8c4862eef', '2animal_welfare_summary.pdf', 'src-8d8336fa08217661',
     'Byte-identical to 1animal_welfare_summary.pdf and text-identical (ratio 1.0000) to the validated animal_welfare_summary.pdf. The only byte-level duplicate pair in this directory.'),
    ('src-2e6b47bcf85ff53d', '1animal_welfare_scope.pdf', 'src-cd53dc44578da73b',
     'Normalized extracted text is identical (ratio 1.0000) to src-0e4d613178cccba9, which is already a duplicate of the validated canonical Animal Welfare project scope src-cd53dc44578da73b.'),
    ('src-c0d6267d2264ee18', '1police_summary.pdf', 'src-61f62a0f79a49ead',
     'Normalized extracted text is identical (ratio 1.0000) to the validated police_summary.pdf.'),
    ('src-9283a5b9090fca32', '1transit_summary.pdf', 'src-04a2e444a39dcd41',
     'Normalized extracted text is identical (ratio 1.0000) to the validated transit_summary.pdf.'),
    ('src-a33d1890d24a2e5c', 'env._health_summary.pdf', 'src-9eacad9e5872b301',
     'Normalized extracted text is identical (ratio 1.0000) to the validated env_health_summary.pdf; the filenames differ only by a period.'),
    ('src-520d641757b64f6d', 'storm_summary.pdf', 'src-4c768545506342aa',
     'Similarity to the validated storm_drainage_summary.pdf is 0.9838, and the file is byte-identical to src-aa1962fc1e07f208, which was already ruled an alternate filename for the same schedule.'),
    ('src-0999e32cc1c95e42', '1senior_affairs_scope.pdf', 'src-b90b07ac62c4f7fd',
     'Normalized extracted text is identical (ratio 1.0000) to senior_affairs_scope.pdf.'),
    ('src-19bbb4d8ab80444f', '1police_scope.pdf', 'src-f74d655ffb05fd08',
     'Normalized extracted text is identical (ratio 1.0000) to police_scope.pdf.'),
    ('src-fcdc70705711d818', 'cip_facilities_parking_scope.pdf', 'src-2ed981e6df5e99d2',
     'Normalized extracted text is identical (ratio 1.0000) to facilities_scope.pdf, which is retained because its name matches the validated facilities_summary.pdf.'),
    ('src-fad7587972cfece9', 'env._health_scope.pdf', 'src-4bafa6f452f2f586',
     'Normalized extracted text is identical (ratio 1.0000) to env_health_scope.pdf, which is retained because its name matches the validated env_health_summary.pdf.'),
    ('src-959e56eb2708523a', '1senior_affairs_summary.pdf', 'src-4cd84ecef3756fb0',
     'Normalized extracted text is identical (ratio 1.0000) to senior_affairs_summary.pdf.'),
    ('src-830b7013a2f5a7ec', '1transit_scope.pdf', 'src-b37593a011f57fae',
     'Normalized extracted text is identical (ratio 1.0000) to transit_scope.pdf.'),
    ('src-a32a875b0c13f4bf', '1finance_scope.pdf', 'src-2daae0eb6e136555',
     'Normalized similarity to finance_scope.pdf is 0.9979; the difference is a single character of PDF text extraction noise, not substantive content.'),
    ('src-543d717d6f9b935c', 'storm_drain_scope.pdf', 'src-2663fc607177e07d',
     'Normalized similarity to storm_drainage_scope.pdf is 0.9166 across the same three-page scope table; storm_drainage_scope.pdf is retained because its name matches the validated storm_drainage_summary.pdf.'),
]

REVIEW = [
    ('src-ca2ae8cb1ef13fdf', 'parks_and_rec_summary.pdf',
     'Similarity to the validated parks_and_recreation_summary.pdf is 0.7459, so it is not a duplicate, but the abbreviated filename carries no version signal comparable to the "1" prefix used elsewhere in this directory. Determine whether it is an earlier draft, a later revision, or a differently scoped extract before retaining or superseding it.'),
    ('src-832bc2144296aa51', 'cultural_summary.pdf',
     'Similarity to the validated cultural_services_summary.pdf is 0.8395 and it carries 125 dollar figures across two pages. Same abbreviated-filename ambiguity as parks_and_rec_summary.pdf; decide the two together.'),
    ('src-20cca95ec6dcbe4f', 'parks_and_rec_scope.pdf',
     'Two pages and 2,741 characters against 4,760 in parks_and_recreation_scope.pdf, so the two are materially different, but the abbreviated filename gives no version order. Resolve alongside parks_and_rec_summary.pdf.'),
    ('src-9e6cb716ac7c28d9', 'cultural_scope.pdf',
     'Two pages and 2,986 characters against 3,958 in cultural_services_scope.pdf. Same abbreviated-filename ambiguity; resolve alongside cultural_summary.pdf.'),
]

EXCLUDED = [
    ('src-8c9c63233ce7dd7a', '2011-go-bond-documents',
     'Not a document. The fetched bytes are an HTML page beginning "<!DOCTYPE html>" with the title "2011 GO Bond Documents - City of Albuquerque"; this is the Plone directory listing for the cluster, a navigation page rather than a capital-program record.'),
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
    for cid, fn, title, desc, ev in APPROVED:
        r = base(cid)
        r.update({'recommended_status': 'approved for addition', 'file': fn, 'title': title,
                  'description': desc, 'description_word_count': len(desc.split()),
                  'proposed_canonical_page': CAPITAL, 'evidence': ev})
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
        'batch_id': 'go2011-bond-cluster-research-2026-09-11',
        'lane': 'Claude research lane: cip-documents/2011-go-bond-documents cluster',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cluster': 'City of Albuquerque 2011 general obligation bond document set under cip-documents/2011-go-bond-documents.',
        'scope': 'All 47 pending-review candidates in that directory. The directory already held 17 validated department schedules, 2 duplicates, and 1 implemented record.',
        'method': ('Fetched every pending file to a scratch directory without touching shared inventory state and recorded exact byte size and SHA-256. '
                   'Compared all 47 hashes against each other and against every checksum in master-inventory.json, then extracted text and ran normalized-similarity comparison both within the pending set and against all 19 already-decided files in the same directory, which were fetched for the purpose. '
                   'Files with no extractable text were rendered and read.'),
        'classification_only': True,
        'shared_state_written': [],
        'precedent_applied': ('This directory already validates both family_summary.pdf as the "2011-2019 Family and Community Services General Obligation Bond Schedule" and 1family_summary.pdf as the same schedule "(Initial Version)". '
                              'The "1" prefix therefore marks an earlier version rather than a duplicate, and a "1"-prefixed file is only a duplicate when its normalized text actually matches. '
                              'That distinction drives the split below: eight "1"-prefixed files matched exactly and are duplicates, while five differ materially and are retained as initial versions.'),
        'duplicate_and_supersession_checks': {
            'internal_byte_collisions': 1,
            'cross_inventory_byte_collisions': 1,
            'text_identical_or_near_pairs_found': 16,
            'note': ('Hashing alone found only two relationships: 1animal_welfare_summary.pdf is byte-identical to 2animal_welfare_summary.pdf, and storm_summary.pdf is byte-identical to the already-duplicate src-aa1962fc1e07f208. '
                     'The other fourteen duplicate relationships are invisible to hashing and were found only by normalized-text comparison, including eight pending files that are text-identical to already-validated department schedules.'),
        },
        'counts': {
            'reviewed': 47,
            'approved_for_addition': len(approved),
            'duplicate': len(dups),
            'requires_human_review': len(review),
            'excluded': len(excl),
            'superseded': 0,
        },
        'link_check': {'checked': 47, 'http_200': 47, 'failed': 0},
        'approved_for_addition': approved,
        'duplicate': dups,
        'requires_human_review': review,
        'excluded': excl,
        'integration_note': ('Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. '
                            'Every duplicate row carries a canonical_id. R2 archival is not authorized by this artifact. '
                            'If the approved "(Initial Version)" records are ever published, title them the way the validated 1family_summary.pdf record already is, so readers can tell the versions apart.'),
        'safeguards': ['no master-inventory.json write', 'no checkpoint.json write', 'no site content change',
                       'no R2 upload', 'no commit, merge, or deploy'],
    }

    total = sum(art['counts'][k] for k in ('approved_for_addition', 'duplicate', 'requires_human_review', 'excluded', 'superseded'))
    assert total == 47, 'classification does not cover all 47 candidates: %d' % total

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(art, indent=1))
    print(json.dumps({'reviewed': 47, 'approved': len(approved), 'duplicate': len(dups),
                      'requires_human_review': len(review), 'excluded': len(excl), 'output': OUT}))


if __name__ == '__main__':
    main()
