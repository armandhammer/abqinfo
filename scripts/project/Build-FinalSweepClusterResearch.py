"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. The final sweep: every remaining uncovered candidate except
the council/find-your-councilor tree.
"""

import collections
import datetime
import glob
import json
import os
import re
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\final-sweep-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\final')

ZONING = 'content/development-land-use/zoning-ido.md'
DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
BIKEIDX = 'content/transportation/bicycling/_index.md'
BIKEPLANS = 'content/transportation/bicycling/bike-plans.md'
BIKEMAPS = 'content/transportation/bicycling/bike-maps.md'
SAFETY = 'content/transportation/safety-crash-data.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
TRANSPO = 'content/transportation/_index.md'
PARKSREC = 'content/public-works/parks-recreation.md'
FACIL = 'content/public-works/city-facilities.md'
CITYDATA = 'content/city-data/_index.md'
CAPITAL = 'content/city-data/capital-spending.md'
ABOUT = 'content/about/_index.md'
MAPS = 'content/maps-data/maps.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL, CODE = {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    i, c, s, h, mag, raw = p[0], p[1], p[2], p[3], p[4], p[5]
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw
    CODE[i] = c

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

# A lane can only be informed by what existed when it ran. This artifact is
# dated 2026-09-13; artifacts dated after it must not feed its sweep, or
# regenerating it would point its rows at rows that point back at these - the
# later lane already recorded these relationships in the other direction.
OUT_DATE = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(OUT)).group(1)


def later_than_this_artifact(path):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(path))
    return bool(m) and m.group(1) > OUT_DATE


PRIOR_IDS, PRIOR_SHA = set(), {}
for f in glob.glob(os.path.join(DISC, '*.json')):
    if os.path.abspath(f) == os.path.abspath(OUT) or later_than_this_artifact(f):
        continue
    try:
        d = json.load(open(f, encoding='utf-8-sig'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR_IDS.add(r['id'])
                if r.get('checksum_sha256'):
                    PRIOR_SHA.setdefault(r['checksum_sha256'], (os.path.basename(f), r['id']))
assert not (set(SLICE) & PRIOR_IDS), sorted(set(SLICE) & PRIOR_IDS)

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x)

KIND = {'25504446': 'PDF', '3c21444f': 'HTML', '0d0a3c21': 'HTML', '3c68746d': 'HTML', '3c21646f': 'HTML',
        '0d0a0d0a': 'HTML', 'ffd8ffe0': 'JPEG', '89504e47': 'PNG', '7b226375': 'JSON', '496e7661': 'TEXT',
        '(none)': 'NOT RETRIEVED'}

LC = ("HTTP 200 verified 2026-09-13 by full GET unless the row says otherwise; size_bytes and checksum_sha256 "
      "measured from the fetched bytes. Container verified by leading bytes: five distinct byte signatures in this "
      "lane are HTML.")


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i].rstrip('/'))) or URL[i]


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": KIND[MAGIC[i] or '(none)'], "leading_bytes": MAGIC[i] or '(none: nothing retrieved)',
         "http_status": CODE[i], "inventory_title": (IDX[i].get('title') or '').strip()}
    r.update(M[i])
    return r


# ---- relationship resolution, external first, then internal -----------------
CROSS_ARCH, CROSS_PRIOR = {}, {}
for i in SLICE:
    s = M[i]['checksum_sha256']
    if not s or s == '(not retrieved)':
        continue
    if s in ARCH_BY_SHA:
        CROSS_ARCH[i] = ARCH_BY_SHA[s]['id']
    elif s in PRIOR_SHA:
        CROSS_PRIOR[i] = PRIOR_SHA[s]

BYHASH = collections.defaultdict(list)
for i in SLICE:
    s = M[i]['checksum_sha256']
    if s and s != '(not retrieved)':
        BYHASH[s].append(i)
INTERNAL = {}
for v in BYHASH.values():
    if len(v) < 2 or any(x in CROSS_ARCH or x in CROSS_PRIOR for x in v):
        continue
    keep = sorted(v, key=lambda x: (len(URL[x]), x))[0]
    for x in v:
        if x != keep:
            INTERNAL[x] = keep

# ---- the PDFs, decided one at a time ---------------------------------------
# id: (title, description, evidence, canonical page, crosses, optional caution)
PDF = {
 'src-513734e069783a79': (
  "Integrated Development Ordinance, 2019 archive draft (2 November 2020)",
  ("The City's Integrated Development Ordinance in its 2019 form, the single zoning and development code that "
   "replaced Albuquerque's sector plans and zoning ordinances, preserved as the archive draft of that edition."),
  "22,684,755 bytes, published at documents.cabq.gov/planning/IDO as IDO-2019-ArchiveDraft-2020-11-02.pdf.",
  ZONING, [{"page": DEVPROC, "reason": "The code every development application is judged against."}],
  "Its own filename calls it an archive draft. Label it as the 2019 edition's archive draft, not as the code in force."),
 'src-17661dabd6894288': (
  "Integrated Development Ordinance, 2022 NARO update, effective draft (27 May 2022)",
  ("The City's Integrated Development Ordinance as updated in 2022 for the Neighbourhood Association Recognition "
   "Ordinance changes, published as the effective draft of that update."),
  "35,898,335 bytes, the largest IDO file in this lane, published as IDO-2022-NARO-Update-2022-05-27-EffectiveDraft.pdf.",
  ZONING, [{"page": DEVPROC, "reason": "The code every development application is judged against."}],
  "Its filename calls it an effective draft. Say so."),
 'src-a21922f80a2d3421': (
  "Resolution adopting interim Development Review Board procedures, Enactment No. R-2019-035",
  ("The Council resolution adopting interim procedures for the Development Review Board until the first annual "
   "update to the Integrated Development Ordinance was completed, transmitted to the Mayor with its passing vote "
   "recorded."),
  ("Rendered, because the file has no usable text layer. Page 1 is a City Council interoffice memorandum to Mayor "
   "Timothy M. Keller from the Director of Council Services transmitting Bill No. R-19-150, with ENACTMENT NO. "
   "R-2019-035 written on the face, passed at the Council meeting of May 20, 2019 by a vote of 9 FOR AND 0 "
   "AGAINST."),
  ZONING, [{"page": DEVPROC, "reason": "It governs the Development Review Board's procedure."}],
  None),
 'src-1f9cf39555e7be6f': (
  "Albuquerque Sustainable Airport Master Plan",
  ("The City's sustainability-led master plan for the Albuquerque International Sunport, the long-range framework "
   "for how the airport is developed and operated."),
  ("280,024,902 bytes - by a wide margin the largest file in this run. See a_truncation_that_reached_the_log for "
   "how nearly the wrong measurement was recorded for it."),
  FACIL, [{"page": CAPITAL, "reason": "A long-range capital framework."}],
  None),
 'src-28216ed513e1c171': (
  "Police Oversight Ordinance",
  ("The City ordinance establishing independent civilian oversight of the Albuquerque Police Department, setting "
   "out the oversight board and its powers, published alongside the board application material that the ordinance "
   "itself governs."),
  "11,359,271 bytes, published under council/albuquerque-police-oversight-board-application.",
  ABOUT, [{"page": CITYDATA, "reason": "A record of City governance."}],
  None),
 'src-d7ceba23129bb417': (
  "Planning Department General Fee Schedule, 2018",
  ("The Planning Department's schedule of the fees charged for development applications, published alongside the "
   "Integrated Development Ordinance the fees are levied under."),
  "Published at documents.cabq.gov/planning/IDO as Planning-GeneralFeeSchedule-2018-final.pdf.",
  DEVPROC, [{"page": ZONING, "reason": "The fees attach to applications under the code."}],
  None),
 'src-9cfa4cf44d7681c6': (
  "Submittal Form IDO 5-2(D): Climatic and Geographic Responsiveness",
  ("The City's submittal requirement under the Integrated Development Ordinance for showing how a site plan "
   "responds to Albuquerque's climate and geography."),
  ("1,074,551 bytes. The council-projects lane recommended a 1,172,023-byte file of the same subject, the "
   "Albuquerque Site and Building Design Considerations. The two are not byte-identical and the sweep did not "
   "match them; they are two editions or two publications of the same requirement."),
  DEVPROC, [{"page": ZONING, "reason": "A requirement of the code."}],
  "Compare against the 1,172,023-byte file recommended in council-projects-planning-forms-cluster-research-2026-09-13.json before publishing both."),
 'src-edf514ed76f57261': (
  "ADA Accessible Parking Checklist",
  ("The City's checklist for accessible parking in design review, setting out what a plan must show to satisfy the "
   "Americans with Disabilities Act requirements the City applies."),
  "Published at documents.cabq.gov/planning/DesignReviewServices.",
  DEVPROC, [], None),
 'src-b7a829c803af21d4': (
  "How to obtain a New Mexico tax registration certificate online",
  ("The City's step-by-step guide for a business obtaining its New Mexico tax registration certificate through the "
   "State Taxpayer Access Point, published for applicants who need the certificate before the City will process "
   "their business paperwork."),
  ("Headed HOW TO Obtain a Registration Certificate Online, and its steps are Log into the Taxpayer Access Point "
   "(TAP) at https://tap.state.nm.us, then Request a Current Registration Certificate Letter. TAP is the New Mexico "
   "Taxation and Revenue Department's system, so this is the tax registration certificate. The City serves the same "
   "493,169-byte file under a second name; see one_guide_two_names."),
  DEVPROC, [], None),
 'src-c1d97fa6b004e461': (None, None, None, None, None, None),   # archived duplicate, handled by the sweep
 'src-97daa82aa5a3ed2e': (
  "50 Mile Activity Loop map, 6 October 2017",
  ("The City's map of the 50 Mile Activity Loop as it stood in October 2017, showing the route of the multi-use "
   "loop around Albuquerque at that date."),
  "323,407 bytes, dated on its own filename to 6 October 2017.",
  BIKEMAPS, [{"page": PARKSREC, "reason": "A recreational trail route."}], None),
 'src-bcc6b93bf3041388': (
  "50 Mile Activity Loop map, 19 September 2019",
  ("The City's map of the 50 Mile Activity Loop as it stood in September 2019, the middle map of the three dated "
   "editions in this set."),
  "1,145,884 bytes, dated on its own filename to 19 September 2019.",
  BIKEMAPS, [{"page": PARKSREC, "reason": "A recreational trail route."}], None),
 'src-cec8db6ab355c309': (
  "3rd Street flags: 50 Mile Activity Loop",
  ("A City design sheet for the 3rd Street flags on the 50 Mile Activity Loop, the wayfinding element marking the "
   "route through that part of the city."),
  "4,187,192 bytes, published in the 50 Mile Activity Loop document set.",
  PARKSREC, [{"page": BIKEIDX, "reason": "Wayfinding on a multi-use route."}], None),
 'src-b2d1fbbc8714d3d0': (
  "Route 66 summary, version 3",
  ("The City's Route 66 summary, the third version, setting out the corridor work associated with the historic "
   "route through Albuquerque."),
  "8,157,681 bytes, published in the 50 Mile Activity Loop document set as RT66SummaryV3.pdf.",
  ROADWAY, [{"page": PROJECTS, "reason": "A named corridor project."}], None),
 'src-e61dd483047d37b8': (
  "50 Mile Activity Loop: executive summary",
  ("The executive summary of the City's 50 Mile Activity Loop proposal, the short account of what the loop is and "
   "what building it involves."),
  "9,431,282 bytes. Its filename carries a copy_of prefix, which names a content management duplication event rather than a second document.",
  PARKSREC, [{"page": BIKEPLANS, "reason": "A multi-use route plan."}], None),
 'src-3592ef7ced6a0b1b': (
  "ABQ the Plan: book",
  ("The City's ABQ the Plan book, the illustrated account of the capital initiatives gathered under that programme, "
   "of which the 50 Mile Activity Loop is one."),
  "7,357,016 bytes, published in the 50 Mile Activity Loop document set as copy_of_ABQthePlanBook-web.pdf.",
  CAPITAL, [{"page": PROJECTS, "reason": "The programme the projects sit under."}], None),
 'src-d5270aaa7d91d95a': (
  "Rail Corridor and Wells Park mural brochure",
  ("The City's brochure for the murals in the rail corridor and Wells Park, the public art walking guide for that "
   "part of Albuquerque."),
  "6,688,566 bytes, published under artsculture/public-art.",
  PARKSREC, [{"page": MAPS, "reason": "A location guide."}], None),
 'src-dae1d3910f55dc31': (
  "Albuquerque Public Art Bicycle Tour",
  ("The City's guide to touring Albuquerque's public art by bicycle, pairing the public art collection with a "
   "cycling route through the city."),
  "314,662 bytes, published under artsculture/public-art.",
  BIKEIDX, [{"page": PARKSREC, "reason": "A recreational guide."}], None),
 'src-3727c90058932d06': (
  "Downtown street art murals map",
  ("A map of the downtown street art murals, published by the City from an arts organisation's original, showing "
   "where the murals are and how to walk between them."),
  "198,622 bytes. Its inventory title records that the map is from 516 Arts, so the City is the publisher of record here but not the author.",
  PARKSREC, [{"page": MAPS, "reason": "A location map."}],
  "Attributed to 516 Arts on its own title. Credit the originator."),
 'src-7551254e2e0beeb8': (
  "May is Bike Month 2025: bilingual event flyer",
  ("The City's bilingual flyer for its 2025 Bike Month events, listing what was on and when for the month's "
   "programme of rides and activities."),
  "2,244,046 bytes, published under cabq.gov/bikes/documents.",
  BIKEIDX, [], "A dated event flyer for a month now past. Keep only if the archive holds programme ephemera."),
 'src-6ff1ad965c719142': (
  "Esperanza bicycle repair: rear derailleur adjustment",
  ("Printable step-by-step instructions from the City's Esperanza bicycle programme for adjusting a rear "
   "derailleur, one of a set of repair guides the programme publishes."),
  "977,231 bytes, published under parksandrecreation/documents.",
  BIKEIDX, [{"page": PARKSREC, "reason": "A City recreation programme's material."}], None),
 'src-c9805a0121553fb8': (
  "Esperanza bicycle repair: wheel removal, multi-speed",
  ("Printable step-by-step instructions from the City's Esperanza bicycle programme for removing a wheel from a "
   "multi-speed bicycle, the companion to the single-speed guide."),
  "1,108,589 bytes, published under parksandrecreation/documents.",
  BIKEIDX, [{"page": PARKSREC, "reason": "A City recreation programme's material."}], None),
 'src-88b9c4645e13a40c': (
  "Esperanza bicycle repair: wheel removal, single-speed",
  ("Printable step-by-step instructions from the City's Esperanza bicycle programme for removing a wheel from a "
   "single-speed bicycle, the companion to the multi-speed guide."),
  "1,218,675 bytes, published under parksandrecreation/documents.",
  BIKEIDX, [{"page": PARKSREC, "reason": "A City recreation programme's material."}], None),
 'src-39b907a648d42f5e': (
  "Citizens Perception Survey, April 2014",
  ("The City's citizen perception survey of April 2014, the measured account of what Albuquerque residents thought "
   "of City services and conditions at that date."),
  "1,610,029 bytes, published under cabq.gov/progress/documents.",
  CITYDATA, [{"page": ABOUT, "reason": "A measure of how the City is seen to perform."}], None),
 'src-576b1976da61d6d1': (
  "High-speed fibre internet: frequently asked questions",
  ("The City's answers to residents' questions about its high-speed fibre internet programme, published by the "
   "broadband office for people asking when and how service reaches them."),
  "1,807,701 bytes, published under technology-innovation/broadband-office.",
  CITYDATA, [{"page": DEVPROC, "reason": "Fibre installation runs through the public right of way."}], None),
 'src-8a864773236902b1': (
  "City of Espanola Fairview Lane Corridor Safety Plan, 2020",
  ("A New Mexico Department of Transportation corridor safety plan for Fairview Lane in Espanola, one of the "
   "department's local road safety plans for New Mexico communities."),
  "7,200,616 bytes, published at dot.nm.gov.",
  SAFETY, [{"page": ROADWAY, "reason": "A corridor safety study."}],
  "Published by NMDOT for another New Mexico community, not by Albuquerque."),
 'src-aad1bfdd1f3bbf14': (
  "Truth or Consequences Multimodal Transportation Safety Plan, 2021",
  ("A New Mexico Department of Transportation multimodal transportation safety plan for Truth or Consequences, one "
   "of the department's local safety plans."),
  "14,106,041 bytes, published at dot.nm.gov.",
  SAFETY, [{"page": TRANSPO, "reason": "A multimodal safety plan."}],
  "Published by NMDOT for another New Mexico community, not by Albuquerque."),
 'src-76dc6a3d52309621': (
  "Madrid Transportation Safety Plan, 2021",
  ("A New Mexico Department of Transportation transportation safety plan for Madrid, one of the department's local "
   "road safety plans for New Mexico communities."),
  "10,433,668 bytes, published at dot.nm.gov.",
  SAFETY, [{"page": ROADWAY, "reason": "A local road safety plan."}],
  "Published by NMDOT for another New Mexico community, not by Albuquerque."),
 'src-5ac50fc54bafa7f0': (
  "Virtual car seat check education flyer",
  ("A New Mexico Department of Transportation flyer explaining how a virtual child car seat check works and how to "
   "arrange one, part of the department's occupant protection programme."),
  "3,472,760 bytes, published at dot.nm.gov.",
  SAFETY, [], None),
 'src-66506f4f8837131d': (
  "NMDOT Unique Entity Identifier letter, 11 March 2022",
  ("The New Mexico Department of Transportation's letter on the federal Unique Entity Identifier, telling its "
   "subrecipients what the change to the federal identifier required of them."),
  "636,301 bytes, published at dot.nm.gov.",
  DEVPROC, [], None),
}

EXCLUDE_PDF = {
 'src-e69a69949c48b38e': ("Federal Communications Commission rules",
                          "A Federal Communications Commission rules document, posted by the City alongside its fibre programme material.",
                          ("Not a City record. The FCC is the authoritative publisher of its own rules. Same "
                           "treatment as the USDA-NRCS technical note, the NMAC licensing rule, the PNM tariff and "
                           "the IRS form excluded earlier in this run."),
                          "federal rules document", "third_party_authority"),
 'src-b2731ab0d2568c6d': ("terms of service",
                          "A terms-of-service document published under the Council's frequently asked questions page.",
                          ("Interface boilerplate rather than a record of governance. It sets the terms of using a "
                           "website, not anything the City decided."),
                          "website terms of service", "interface_boilerplate"),
}

approved, duplicate, excluded, requires_human_review = [], [], [], []

# external duplicates
for i, canon in sorted(CROSS_ARCH.items()):
    a = IDX[canon]
    r = row(i, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": (IDX[i].get('title') or fname(i)),
              "relationship": "The same file the archive already holds as %s, validated with an r2_url." % (a.get('title') or canon),
              "how_it_was_established": ("Byte-identical to the archived record: %s bytes and the same SHA-256, found "
                                         "by sweeping every fetched checksum against all %d checksummed archived "
                                         "records." % (format(M[i]['size_bytes'], ','), len(ARCH_BY_SHA))),
              "why_this_one_is_the_copy": "The archive already holds it, validated and archived.",
              "group": "already archived"})
    if i == 'src-9a6e43f69e2e059a':
        r["a_title_correction"] = ("This candidate is registered as the 2023 Albuquerque Yearly Survey and the "
                                   "archived record as the 2024 results. The document settles it: it is a Pinion "
                                   "Research memorandum to the City dated April 16, 2024, headed Albuquerque Yearly "
                                   "Survey Results. The archived title is right and the candidate's is wrong.")
    duplicate.append(r)

for i, (art, pid) in sorted(CROSS_PRIOR.items()):
    r = row(i, "duplicate")
    r.update({"canonical_id": pid,
              "title_for_reference": (IDX[i].get('title') or fname(i)),
              "relationship": "The same file this run already decided as %s in %s." % (pid, art),
              "how_it_was_established": ("Byte-identical: %s bytes and the same SHA-256 as a row already recorded in "
                                         "a saved artifact of this run." % format(M[i]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "The earlier artifact decided it first; recommending it again would tell Codex to handle one file twice.",
              "decided_in": art,
              "group": "already decided in this run"})
    duplicate.append(r)

for copy, canon in sorted(INTERNAL.items()):
    r = row(copy, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": (IDX[copy].get('title') or fname(copy)) + ", second URL",
              "relationship": "The same object as its canonical, reached at a second address.",
              "how_it_was_established": ("Byte-identical: both %s bytes with the same SHA-256, at two different "
                                         "URLs." % format(M[copy]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "The shorter URL is taken as canonical; the relationship is what matters.",
              "group": "one object, two addresses"})
    if copy == 'src-67b5bfdf38fd36d7':
        r["why_this_one_is_the_copy"] = ("Not an arbitrary choice between two addresses. The document instructs the "
                                         "reader to use the Taxation and Revenue Department's Taxpayer Access "
                                         "Point, so the Tax-named record describes it correctly and this "
                                         "Business-named one does not.")
        r["a_mislabelled_link"] = ("This is the wrong name for the file behind it, not merely a second name. See "
                                   "one_guide_two_names.")
    duplicate.append(r)

DONE = {r['id'] for r in duplicate}

for i, spec in PDF.items():
    if i in DONE or spec[0] is None:
        continue
    t, desc, ev, canon, cross, caution = spec
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "evidence": ev,
              "group": "documents", "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if caution:
        r["caution"] = caution
    approved.append(r)
    DONE.add(i)

for i, (t, what, why, cat, pkg) in EXCLUDE_PDF.items():
    if i in DONE:
        continue
    r = row(i, "excluded")
    r.update({"title_for_reference": t, "what_it_is": what, "exclusion_reason": why,
              "category": cat, "package": pkg})
    excluded.append(r)
    DONE.add(i)

SHELLS = {
 'src-2f89e1bc040e1d33': {
  "title_for_reference": "Final McDuffie-Twin Parks Traffic Calming Study",
  "what_it_is": ("A City traffic calming study, published through the City's file-transfer host rather than as a "
                 "file on a City web server."),
  "measurement": ("HTTP 200 and 1,344 bytes of JavaScript application shell, leading bytes 3c21646f. The document "
                  "itself is loaded by that application; the host's REST API answers 401 without credentials."),
  "it_was_then_retrieved": ("Resolved on 2026-09-14. The repository owner retrieved it through a browser. It is "
                            "the McDuffie/Twin Parks Neighborhood Traffic Calming Study, final report dated 7 May "
                            "2024, prepared for the City by Wilson & Company, 11,940,327 bytes and 321 pages. See "
                            "file-share-retrieval-research-2026-09-14.json, which carries the full row and the "
                            "provenance note."),
  "the_measurements_on_this_row_are_the_share_page_not_the_document": (
    "1,344 bytes of application shell is what the URL returns and what this lane measured. The document's size and "
    "checksum are on the retrieval artifact's row, and re-fetching this URL will never reproduce them."),
  "package": "published_only_through_a_file_share",
 },
 'src-a9ddff947a4282c9': {
  "title_for_reference": "City of Albuquerque School Crossing Locations",
  "what_it_is": "An ArcGIS Map Journal web application showing school crossing locations.",
  "measurement": "HTTP 200 and 1,228 bytes of JavaScript application shell, leading bytes 3c21444f.",
  "exclusion_reason": ("Not a static document and not a document at all. The URL is an ArcGIS Map Journal "
                       "application (cabq.maps.arcgis.com/apps/MapJournal/index.html?appid=...), whose content is "
                       "assembled in the browser from a map service. There is no original file behind it to "
                       "archive - unlike the other shell in this lane, where there is."),
  "category": "interactive map application",
  "package": "not_a_document",
 },
}

NOT_DOCUMENTS = {
 'JPEG': ("A photograph reached through a content management system UID.",
          "Site furniture. The URL is a resolveuid alias and the bytes are a project photograph, not a record.",
          "page image behind a UID alias", "site_furniture"),
 'PNG': ("An image served from a document repository by numeric identifier.",
         "An image, not a document. Served from MRCOG's ImageRepository by document id.",
         "repository image", "site_furniture"),
 'JSON': ("An ArcGIS vector tile service description.",
          ("Not a document. The URL returns a JSON service descriptor for a map tile layer - currentVersion, "
           "capabilities, tileMap - which is machine configuration for a map, not anything published."),
          "map service endpoint", "not_a_document"),
 'TEXT': ("A Legistar legislation URL that answers Invalid parameters!",
          ("There is no document at this URL. It returns HTTP 200 and nineteen bytes reading Invalid parameters! - "
           "the legislation detail record it addresses is gone. Another case where the status code says success and "
           "the bytes say otherwise."),
          "dead link answering with an error string", "nothing_at_the_url"),
 'NOT RETRIEVED': ("A redirect to a host whose TLS certificate has expired.",
                   ("Could not be retrieved. The URL answers HTTP 302 and following the redirect fails at the TLS "
                    "handshake: the destination's certificate has expired. Nothing was downloaded, so nothing was "
                    "measured, and the row carries no checksum."),
                   "unreachable: expired certificate", "nothing_at_the_url"),
}

for i in SLICE:
    if i in DONE:
        continue
    k = KIND[MAGIC[i] or '(none)']
    if i == 'src-2f89e1bc040e1d33':
        r = row(i, "approved for addition")
        r.update(SHELLS[i])
        r["decided_in"] = "file-share-retrieval-research-2026-09-14.json"
        approved.append(r)
    elif i == 'src-a9ddff947a4282c9':
        r = row(i, "excluded")
        r.update(SHELLS[i])
        excluded.append(r)
    elif k == 'HTML':
        r = row(i, "excluded")
        r.update({"title_for_reference": "Web page: " + URL[i].split('//')[1][:88],
                  "what_it_is": "A live page on a City, NMDOT, MRCOG or Rio Metro website.",
                  "exclusion_reason": ("Not a static document. The URL returns HTML, and there is no original file "
                                       "to archive. The archive has settled this class repeatedly, excluding "
                                       "navigation, pagination, contact, or generic interface text captured as a "
                                       "candidate."),
                  "category": "live web page",
                  "package": "web_pages"})
        excluded.append(r)
    else:
        what, why, cat, pkg = NOT_DOCUMENTS[k]
        r = row(i, "excluded")
        r.update({"title_for_reference": (IDX[i].get('title') or fname(i))[:90],
                  "what_it_is": what, "exclusion_reason": why, "category": cat, "package": pkg})
        excluded.append(r)

rows = approved + duplicate + requires_human_review + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)
byexcl = collections.Counter(r["package"] for r in excluded)

artifact = {
 "batch_id": "final-sweep-cluster-research-2026-09-13",
 "lane": "Claude research lane: every remaining uncovered candidate except the council/find-your-councilor tree",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13. The last lane of this run.",
 "cluster": ("What was left after fourteen lanes: 416 records spread across roughly a hundred directories, none "
             "larger than nine, so one sweep rather than many."),
 "scope": "All 416 remaining uncovered candidates outside the find-your-councilor tree. The coverage gate is asserted in the generator.",
 "brief": ("Fetch and measure every one, classify by container, and run the two-set checksum sweep. This exhausts "
           "the document-bearing pool."),
 "brief_finding": ("Eighty-nine per cent of what remained is web pages. Thirty-eight records are documents, and "
                   "among them are two editions of the Integrated Development Ordinance, an enacted Council "
                   "resolution, the Police Oversight Ordinance and a 280-megabyte airport master plan."),
 "what_the_remainder_actually_was": {
  "total": len(SLICE),
  "html": bycontainer['HTML'],
  "pdf": bycontainer['PDF'],
  "other": len(SLICE) - bycontainer['HTML'] - bycontainer['PDF'],
  "five_byte_signatures_all_meaning_html": ("3c21444f, 0d0a3c21, 3c68746d, 3c21646f and 0d0a0d0a. A check that "
                                            "recognised only the first would have mis-sorted 101 records. Leading "
                                            "bytes have to be read as a family, not matched against one constant."),
  "the_other_six": ("Two JPEG photographs behind UID aliases, one PNG from a document repository, two ArcGIS vector "
                    "tile service descriptors, one Legistar URL that answers Invalid parameters!, and one MRCOG URL "
                    "that could not be retrieved at all."),
 },
 "a_correction_to_this_artifact": {
  "when": "Added 2026-09-14, after the artifact was first written on 2026-09-13.",
  "what_was_wrong": ("Two records in this lane were excluded as live web pages on the strength of their leading "
                     "bytes. Both return HTML, which is true and measured. But both are JavaScript application "
                     "shells, and behind one of them is a document: src-2f89e1bc040e1d33 is titled Final "
                     "McDuffie-Twin Parks Traffic Calming Study and its URL is a share link on the City's "
                     "file-transfer host, sfftp.cabq.gov."),
  "why_the_original_reasoning_failed": ("The exclusion reason said there is no original file to archive. For 336 of "
                                        "the pages in this lane that was correct. For this one it was not: there is "
                                        "a file, the share page just will not hand it to a fetch. A container check "
                                        "answers what the bytes are, and I let it answer a different question - "
                                        "whether a document exists."),
  "what_changed": ("src-2f89e1bc040e1d33 was moved to requires human review for browser retrieval, and after that "
                   "retrieval succeeded on 2026-09-14 it is now approved for addition, decided in "
                   "file-share-retrieval-research-2026-09-14.json. "
                   "src-a9ddff947a4282c9 stays excluded - it is an ArcGIS Map Journal application with no file "
                   "behind it - but its reason now says what it actually is rather than calling it a live web "
                   "page."),
  "how_it_was_found": ("By the method the next lane is built on. Parsing the stored HTML of the pages this lane "
                       "excluded turned up a link to sfftp.cabq.gov/f/licenses.txt, which could only have come from "
                       "a file-share page - and the page it came from was one of this lane's own candidates."),
  "the_rule": ("A small HTML response is worth looking at. Of 371 HTML responses here, exactly two were under 4,000 "
               "bytes, and both were application shells rather than pages. Size is the cheap tell that leading "
               "bytes cannot give you."),
 },
 "a_truncation_that_reached_the_log": {
  "what_happened": ("The bulk fetch ran with a 90-second timeout. The Albuquerque Sustainable Airport Master Plan "
                    "is 280,024,902 bytes and did not finish in 90 seconds. curl wrote what it had - 171,450,880 "
                    "bytes - and the loop recorded that length and its checksum against an HTTP 200."),
  "why_it_was_dangerous": ("Nothing about the recorded row looked wrong. A large plan with a plausible size and a "
                           "valid SHA-256 of the bytes actually on disk. The checksum was correct for a file that "
                           "was not the document."),
  "how_it_was_caught": ("The row was refetched without a timeout and returned a different size. A third complete "
                        "fetch returned 280,024,902 bytes again with a matching SHA-256, so the document is stable "
                        "and the first measurement was the wrong one."),
  "what_was_then_checked": ("Every PDF in the lane was tested for the %%EOF marker in its last two kilobytes. All "
                            "38 are complete; this was the only truncation."),
  "the_rule": ("A timeout on a fetch is not a failure that announces itself. Verify the length of anything large "
               "against a second complete fetch, and test PDFs for their end marker before recording a checksum."),
 },
 "the_two_set_sweep": {
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "already_archived": len(CROSS_ARCH),
  "already_decided_in_this_run": len(CROSS_PRIOR),
  "one_object_two_addresses": len(INTERNAL),
  "total_relationships": len(duplicate),
  "what_the_internal_ones_are": ("Mostly site restructuring. NMDOT serves the same page under both "
                                 "/infrastructure/... and /planning-research-multimodal-and-safety/infrastructure/..., "
                                 "MRCOG serves pages under two numeric ids, and Rio Metro does the same. Neither a "
                                 "URL comparison nor a title comparison would pair them; the bytes do."),
  "artifacts_dated_after_this_one_are_excluded_from_the_sweep": (
   "This artifact is dated %s. Later lanes are skipped, because they recorded their relationship to these rows in "
   "the other direction; feeding them back in would make each point at the other." % OUT_DATE),
  "the_run_total": ("With this lane the sweep has now found 18 already-archived records and 12 already-decided ones "
                    "across six consecutive lanes. It was introduced two thirds of the way through the run; every "
                    "lane before it reported zero cross-inventory collisions, truthfully but only because nothing "
                    "was looking."),
 },
 "one_guide_two_names": {
  "what": ("documents.cabq.gov/planning/BizReg serves one 493,169-byte file under two names: How to Obtain NM "
           "Business Registration Certificate.pdf and How to Obtain NM Tax Registration Certificate.pdf."),
  "the_measurement": "Byte-identical, same SHA-256, and both open on the same heading: HOW TO Obtain a Registration Certificate Online.",
  "why_it_matters": ("A business registration certificate and a tax registration certificate are different things "
                     "obtained through different State processes. One of the two names had to be wrong, and an "
                     "applicant following the wrong one would be reading instructions for the other certificate."),
  "which_name_is_wrong": ("Resolved by reading the document rather than by weighing the two filenames. Its "
                          "instructions are: log into the Taxpayer Access Point at https://tap.state.nm.us, open "
                          "the Letters panel, and Request a Current Registration Certificate Letter. TAP belongs to "
                          "the New Mexico Taxation and Revenue Department. The file is the tax registration "
                          "certificate guide, so the Tax name is right and the Business name is wrong."),
  "the_recommendation": ("Keep the Tax-named record as canonical, record the Business-named one as a duplicate, and "
                         "report the mislabelled link to the City rather than republishing both."),
 },
 "the_substance_that_was_left": {
  "the_code_itself": ("Two editions of the Integrated Development Ordinance - the 2019 archive draft at 22,684,755 "
                      "bytes and the 2022 NARO update effective draft at 35,898,335 - plus the Planning "
                      "Department's 2018 general fee schedule and the IDO 5-2(D) submittal requirement. Both IDO "
                      "files name their own status in their filenames, and both rows say so."),
  "an_enacted_resolution": ("R-150Enacted.pdf is Enactment No. R-2019-035, Bill No. R-19-150, adopting interim "
                            "Development Review Board procedures until the first annual IDO update was completed, "
                            "passed on 20 May 2019 by 9 votes to 0. It has no text layer; the enactment number, the "
                            "vote and the transmittal memorandum were all read by rendering."),
  "the_largest_document_of_the_run": "The Albuquerque Sustainable Airport Master Plan, 280,024,902 bytes.",
  "and_the_police_oversight_ordinance": "11,359,271 bytes, published with the oversight board application material it governs.",
  "the_50_mile_activity_loop_set": ("Six records: dated maps of October 2017 and September 2019, the 3rd Street "
                                    "flags design sheet, the Route 66 summary, the executive summary and the ABQ "
                                    "the Plan book. The May 2020 map is byte-identical to one the archive already "
                                    "holds, which dates the sequence at both ends."),
  "three_NMDOT_local_safety_plans": ("Espanola Fairview Lane, Truth or Consequences and Madrid. Published by NMDOT "
                                     "for other New Mexico communities; each row says so."),
 },
 "method": ("Fetched all 416 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. "
            "Rebuilt the fetch log to one row per candidate after an interrupted run left seventeen ids written "
            "twice, and rehashed every row against the file on disk. Refetched the two records whose status codes "
            "were malformed, which is how the truncation was found. Tested every PDF for its end-of-file marker. "
            "Swept every checksum against the archived inventory records and against every row of every saved "
            "artifact, then grouped by checksum within the lane. Read the 38 documents and rendered the one with no "
            "text layer."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, against anything recommended earlier in the same batch, and against every row of every saved artifact.",
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts_in_this_run": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Thirteen candidates are already held or already decided, and thirty more are one object at two addresses.",
 },
 "duplicate_and_supersession_checks": {
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "relationships_found": len(duplicate),
  "note": "Every relationship in this lane was found by checksum. None would have been found by URL, filename or title.",
 },
 "integration_flags": [
  {"severity": "measurement-integrity",
   "affects": ['src-1f9cf39555e7be6f'],
   "finding": "A 280,024,902-byte master plan was recorded at 171,450,880 bytes with a valid checksum, because a 90-second fetch timeout truncated it and the loop measured what was on disk. Two complete refetches agree on the real size and hash.",
   "recommended_action": "Verify large downloads against a second complete fetch and test PDFs for %%EOF before recording a checksum. Detail in a_truncation_that_reached_the_log."},
  {"severity": "avoids-duplicate-archival",
   "affects": sorted(CROSS_ARCH) + sorted(CROSS_PRIOR),
   "finding": f"{len(CROSS_ARCH)} candidates are byte-identical to records the archive already holds and {len(CROSS_PRIOR)} to records this run already decided. None is reachable by URL or title.",
   "recommended_action": "Apply duplicate. The two-set sweep should be standard practice for every future lane."},
  {"severity": "substantive-find",
   "affects": ['src-513734e069783a79', 'src-17661dabd6894288', 'src-a21922f80a2d3421', 'src-28216ed513e1c171',
               'src-1f9cf39555e7be6f'],
   "finding": "Two editions of the Integrated Development Ordinance, the enacted resolution adopting interim Development Review Board procedures (Enactment R-2019-035, passed 9-0 on 20 May 2019), the Police Oversight Ordinance, and the Albuquerque Sustainable Airport Master Plan.",
   "recommended_action": "Approve. Both IDO files name their own draft status in their filenames and their rows say so; the resolution's enactment number was readable only by rendering."},
  {"severity": "title-from-the-document",
   "affects": ['src-9a6e43f69e2e059a'],
   "finding": "The candidate is registered as the 2023 Albuquerque Yearly Survey and is byte-identical to the archived 2024 results. The document is a Pinion Research memorandum dated April 16, 2024. The archived title is right and the candidate's is wrong.",
   "recommended_action": "Apply duplicate and correct the candidate's title in passing."},
  {"severity": "tell-the-city",
   "affects": ['src-b7a829c803af21d4', 'src-67b5bfdf38fd36d7'],
   "finding": "One 493,169-byte guide is served under two names, one promising a business registration certificate and the other a tax registration certificate. The document itself settles it: its steps run through the Taxation and Revenue Department's Taxpayer Access Point, so it is the tax registration certificate and the Business-named link is mislabelled.",
   "recommended_action": "Approve the Tax-named record, apply duplicate to the Business-named one, and report the mislabelled link rather than republishing both."},
  {"severity": "link-check",
   "affects": [i for i in SLICE if KIND[MAGIC[i] or '(none)'] in ('TEXT', 'NOT RETRIEVED')],
   "finding": "One Legistar legislation URL returns HTTP 200 and the nineteen bytes Invalid parameters!; one MRCOG URL redirects to a host whose TLS certificate has expired and cannot be retrieved at all.",
   "recommended_action": "Record both in the terminal set. Neither is a document and neither failure is visible from a status code alone."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "_note": "Two rows were re-decided on 2026-09-14; see a_correction_to_this_artifact.",
  "excluded": counts["excluded"],
  "containers": dict(bycontainer),
  "excluded_by_package": dict(byexcl),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "http_200_but_not_a_document": 1,
                "unretrievable": 1,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13, with the two anomalous records refetched without a timeout.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": ("%d HTML pages across five byte signatures, %d PDFs, %d JPEG, %d PNG, %d "
                                        "JSON service descriptors, %d error string and %d unretrievable."
                                        % (bycontainer['HTML'], bycontainer['PDF'], bycontainer['JPEG'],
                                           bycontainer['PNG'], bycontainer['JSON'], bycontainer['TEXT'],
                                           bycontainer['NOT RETRIEVED']))},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": requires_human_review,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes - far the largest "
                   f"of any lane in this run, and dominated by one 280,024,902-byte master plan."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Every duplicate row carries a canonical_id; those "
                     "pointing outside this artifact name either an archived inventory record or, in decided_in, "
                     "the saved artifact that decided it. Every row carries the inventory_title, the http_status and "
                     "the leading bytes. One row carries no checksum because nothing could be retrieved from it. "
                     "Sizes and checksums are first measurements; the inventory held none."),
 "what_remains_after_this": ("The 169 candidates under council/find-your-councilor. "
                             "councilor-district-3-and-6-cluster-research-2026-09-13.json established by fetching "
                             "100 of that tree's 239 records that not one is a static document; the remaining 169 "
                             "are a bulk HTML confirmation rather than a research lane."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('containers', 'excluded_by_package')}}))
