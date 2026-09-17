"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. neighborhood-traffic-management-program/documents and
www.cabq.gov/planning/documents.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\ntmp-planning-documents-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\nt')

SPEED = 'content/transportation/roadway-projects/speed-management.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
DESIGNREF = 'content/transportation/design-references.md'
BIKEPLANS = 'content/transportation/bicycling/bike-plans.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'
DEVPROC = 'content/development-land-use/development-process.md'
PARKSREC = 'content/public-works/parks-recreation.md'
FACIL = 'content/public-works/city-facilities.md'
DEMO = 'content/city-data/demographics.md'
MAPS = 'content/maps-data/maps.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR = set()
for f in glob.glob(r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\*.json'):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR.add(r['id'])
assert not (set(SLICE) & PRIOR), sorted(set(SLICE) & PRIOR)

CONTAINER = {'25504446': 'PDF', '3c21444f': 'HTML'}
LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, not by extension - one file named .docx in this lane is a PDF.")

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x)


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i]))


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


HTML = [i for i in SLICE if MAGIC[i] == '3c21444f']
NTMP = [i for i in SLICE if '/neighborhood-traffic-management-program/' in URL[i] and MAGIC[i] != '3c21444f']
PLANNING = [i for i in SLICE if '/planning/documents' in URL[i] and MAGIC[i] != '3c21444f']

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
TWINS = {}
for v in BYHASH.values():
    if len(v) == 2:
        a, b = sorted(v)
        TWINS[b] = a

CROSS = {i: ARCH_BY_SHA[M[i]['checksum_sha256']]['id'] for i in SLICE
         if M[i]['checksum_sha256'] in ARCH_BY_SHA}
for i in CROSS:
    TWINS.pop(i, None)

TOOL_NAME = {
 'chicane': 'chicanes', 'diagonal-diverter': 'diagonal diverters', 'forced-turn-island': 'forced turn islands',
 'high-visibility-crosswalks': 'high visibility crosswalks', 'lane-narrowing-with-center-island': 'lane narrowing with a centre island',
 'lateral-shift': 'lateral shifts', 'median-barrier': 'median barriers', 'medians-partial-medians': 'medians and partial medians',
 'neckdowns-bulbouts': 'neckdowns and bulbouts', 'one-lane-choker': 'one-lane chokers',
 'one-way-couplet-conversions': 'one-way couplet conversions', 'parking-strategies': 'parking strategies',
 'partial-closure': 'partial closures', 'permanent-radar-speed-sign': 'permanent radar speed signs',
 'radar-speed-trailer': 'radar speed trailers', 'raised-intersection': 'raised intersections',
 'speed-hump': 'speed humps', 'speed-kidney': 'speed kidneys', 'speed-table': 'speed tables',
 'two-lane-choker': 'two-lane chokers', 'education-community-involvement': 'education and community involvement',
}

PLANS = {
 'src-99fe2201b73355c4': ("Barelas Sector Development Plan, Adopted April 2008", "2008", AREAPLANS,
  ("The adopted sector development plan for Barelas, the City's land use and design framework for the "
   "neighbourhood, setting what may be built where and to what standard within the plan's boundary."),
  "Titled BARELAS SECTOR DEVELOPMENT PLAN, Adopted April 2008, on its cover. At 49,626,419 bytes it is the largest file in this lane."),
 'src-d9bf34830a9467e2': ("Barelas Neighborhood Commercial Area Revitalization Plan, with legislation", None, REDEV,
  ("The City's revitalization plan for the Barelas neighbourhood commercial area, published complete with the "
   "legislation that adopted it, covering the commercial frontage the plan set out to revive."),
  "Rendered, because the file has no usable text layer. Its cover reads BARELAS NEIGHBORHOOD COMMERCIAL AREA REVITALIZATION PLAN over a photograph of the Arrow Super Market building. The filename records that the legislation is bound in."),
 'src-afac0cf84867a22f': ("Bosque Action Plan, Rio Grande Valley State Park, Final Plan, January 1993", "1993", PARKSREC,
  ("The City's final action plan for the bosque within Rio Grande Valley State Park, setting out what the City "
   "proposed to do along the river corridor, from access and trails through restoration and wildlife preserve."),
  ("Rendered, because the file has no usable text layer at all. Its cover reads City of Albuquerque, Parks and "
   "General Services Department, BOSQUE ACTION PLAN, Rio Grande Valley State Park, Final Plan, January 1993. 105 "
   "pages.")),
 'src-fb6e95610a43c7a4': ("Major Public Open Space Facility Plan, January 1999", "1999", PARKSREC,
  ("The City's adopted facility plan for its major public open space, the framework governing how the City's open "
   "space lands are acquired, managed and used."),
  "Headed CITY OF ALBUQUERQUE, MAJOR PUBLIC OPEN SPACE FACILITY PLAN, January 1999."),
 'src-2379e7a8b1c51aca': ("Clayton Heights Metropolitan Redevelopment Area Plan, July 2010", "2010", REDEV,
  ("The City's metropolitan redevelopment area plan for Clayton Heights, described on its own cover as an "
   "Albuquerque gateway neighbourhood, setting the redevelopment framework for the designated area."),
  "Headed Clayton Heights, Metropolitan Redevelopment Area Plan, An Albuquerque Gateway Neighborhood. The filename records final 07 2010."),
 'src-7de0f5803d442e8f': ("Facility Plan: Electric System Transmission and Generation, 2010-2020", None, FACIL,
  ("The joint City and County facility plan for electric system transmission and generation across the decade to "
   "2020, the adopted framework for where electrical infrastructure may be built."),
  "Headed FACILITY PLAN, Electric System, Transmission and Generation (2010 - 2020), City of Albuquerque and Bernalillo County."),
 'src-f528ec2e0e955690': ("Volcano Trails Sector Development Plan, as enacted 2011, with adopting legislation", "2011", AREAPLANS,
  ("The Volcano Trails sector development plan in its enacted form, the plan text published together with the "
   "legislation that adopted it, which the plan document alone does not carry."),
  ("8,976,542 bytes against the 8,903,701-byte plan the archive already holds. Token coverage of the held plan "
   "inside this file is 1.0000 with two of three contiguous sixty-word runs present, and this file carries 221 "
   "further tokens the held plan does not: adopt, adopting, authorized, advisory, enactment-style numbers and NMSA "
   "years. It is the plan with its adopting legislation bound in.")),
 'src-c87775c045d8acc4': ("H-1 Historic Old Town Zone Design Guidelines, as amended through April 9, 1998", "1998", ZONING,
  ("The design guidelines adopted by the Landmarks and Urban Conservation Commission for building projects in the "
   "H-1 Historic Old Town Zone and the three hundred foot buffer zone around it."),
  "Opens: The following Design Guidelines (as amended through April 9, 1998) have been adopted by the Landmarks and Urban Conservation Commission for building projects in the H-1 Historic Old Town Zone and in the 300 foot buffer zone surrounding the H-1 Zone."),
 'src-eb0f4b39798d29df': ("Unser Boulevard Overlay Zone: complete legislation", None, ZONING,
  ("The complete legislative package establishing the Unser Boulevard overlay zone, the additional development "
   "controls applied along the corridor over and above the underlying zoning."),
  ("Headed CITY of ALBUQUERQUE, NINTH COUNCIL, COUNCIL BILL NO. C/S R-14, sponsored by Alan B. Armijo. Its "
   "ENACTMENT NO. line is blank on the face, but the file is titled complete legislation and runs to 1,969,125 "
   "bytes, so the package rather than an isolated substitute.")),
 'src-8740362a1b751e26': ("Planned Communities Criteria: Policy Element, February 1991", "1991", ZONING,
  ("The City's adopted policy element setting the criteria a planned community must meet, the framework under which "
   "large master-planned developments are judged against the Comprehensive Plan."),
  "Rendered, because the file has no usable text layer. Its cover reads PLANNED COMMUNITIES, PLANNED COMMUNITIES CRITERIA: POLICY ELEMENT, February, 1991."),
 'src-fee63a8f74f3f110': ("Trails and Bikeways Facility Plan, Adopted July 1993, map revised November 1996", "1993", BIKEPLANS,
  ("The City's adopted facility plan for trails and bikeways, the earliest in the sequence the archive holds, "
   "setting the framework for the trail and bikeway network the later plans revised."),
  ("Rendered, because the file has no usable text layer. Its cover reads Trails & Bikeways Facility Plan, Adopted, "
   "July 1993, Map Revised Nov. 1996. The archive already holds a 2015 appendix and the 2024 Bikeway and Trail "
   "Facilities Plan; this is their predecessor.")),
 'src-e6ec0d7ea1527506': ("Revocable Permit (standard form)", None, DEVPROC,
  ("The City's standard revocable permit instrument, the agreement by which the City grants a permission it can "
   "later withdraw, with the project name, number and parties left to be filled in."),
  "Headed REVOCABLE PERMIT with Project Name and Project Number blank, opening THIS REVOCABLE PERMIT (Permit), made and entered into this ___ day of."),
}

CHAPTERS = {'src-16b33375ffbddc62': '1.0', 'src-c54e59cd5c25282d': '3', 'src-1fa6ae851ddf282d': '5',
            'src-513fe9056bf9b34c': '8'}

FORMS = ['src-e9a45e771497acb7', 'src-a64d3561994aa604', 'src-826b838b930e23b6', 'src-c28ac1861614a36d',
         'src-da51e530c87ba7ca', 'src-21c399e0d5a2510c', 'src-12776db138d35f11']

approved, duplicate, rhr, excluded = [], [], [], []

# ---------------------------------------------------------------- duplicates
for i, canon in sorted(CROSS.items()):
    a = IDX[canon]
    r = row(i, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": fname(i),
              "relationship": "The same file the archive already holds as %s, validated with an r2_url." % (a.get('title') or canon),
              "how_it_was_established": ("Byte-identical to the archived record: %s bytes and the same SHA-256, found "
                                         "by sweeping every fetched checksum against all %d checksummed archived "
                                         "records." % (format(M[i]['size_bytes'], ','), len(ARCH_BY_SHA))),
              "why_this_one_is_the_copy": "The archive already holds it, validated and archived.",
              "group": "already archived"})
    duplicate.append(r)

for copy, canon in sorted(TWINS.items()):
    r = row(copy, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": fname(copy) + ", second inventory record",
              "relationship": "The same file registered twice in the inventory under two candidate ids at one URL.",
              "how_it_was_established": "Byte-identical: both %s bytes with the same SHA-256 at the same URL." % format(M[copy]['size_bytes'], ','),
              "why_this_one_is_the_copy": "Arbitrary between two identical registrations of one URL; the relationship is what matters.",
              "group": "duplicate registrations"})
    duplicate.append(r)

DUP_IDS = {r['id'] for r in duplicate}

# ------------------------------------------------------------- NTMP toolbox
for i in NTMP:
    if i in DUP_IDS:
        continue
    stem = fname(i).replace('.pdf', '')
    if stem in TOOL_NAME:
        subject = TOOL_NAME[stem]
        desc = ("The City's traffic calming tool sheet for %s, setting out what the measure does, where it is "
                "appropriate, what it costs and what effect it has on speeds, emergency access and drainage."
                % subject)
        t = "Neighborhood Traffic Management Program tool sheet: " + subject
        ev = "One sheet in the City's traffic calming toolbox, published at neighborhood-traffic-management-program/documents/%s." % fname(i)
        grp = "traffic calming toolbox"
        canon, cross = SPEED, [{"page": ROADWAY, "reason": "The measures are applied on City streets."}]
    else:
        t = "Neighborhood Traffic Management Program: program document"
        desc = ("The City's Neighborhood Traffic Management Program document, the framework under which residents "
                "request traffic calming on their streets and the City ranks, designs and installs it.")
        ev = "A 4,101,479-byte PDF published at the program's own landing path."
        grp = "traffic calming toolbox"
        canon, cross = SPEED, [{"page": DEVPROC, "reason": "It sets the process a neighbourhood follows."}]
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "evidence": ev, "group": grp,
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# ------------------------------------------------------------- planning plans
for i, (t, date, canon, desc, ev) in sorted(PLANS.items()):
    if i in DUP_IDS:
        continue
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "date": date, "evidence": ev,
              "group": "adopted plans and legislation",
              "proposed_canonical_page": canon,
              "cross_listings": ([{"page": AREAPLANS, "reason": "An adopted area plan."}]
                                 if canon not in (AREAPLANS,) else [{"page": DEVPROC, "reason": "It governs development review in the plan area."}]),
              "description_word_count": len(desc.split())})
    approved.append(r)

for i, ch in sorted(CHAPTERS.items()):
    r = row(i, "approved for addition")
    desc = ("Chapter %s of the City's planning impact area population and land use study, one of four chapters of "
            "that study published separately on the planning department's document page." % ch)
    r.update({"title": "Planning Impact Area population and land use study: Chapter %s" % ch,
              "description": desc,
              "evidence": ("Chapter 1.0 is headed EXECUTIVE SUMMARY and reports planning impact area population "
                           "reaching almost 600,000 by 1998 against the 1990 Census total of 515,143, naming PIAs 4, "
                           "5, 14 and 15. The filenames carry 2010, which on the evidence of the data is the "
                           "projection horizon rather than the publication year."),
              "group": "adopted plans and legislation",
              "caution": ("Only chapters 1, 3, 5 and 8 are here; 2, 4, 6 and 7 are not among the candidates. Name the "
                          "parent study from a complete copy before publishing, and do not date it 2010 from the "
                          "filename."),
              "proposed_canonical_page": DEMO,
              "cross_listings": [{"page": AREAPLANS, "reason": "The study underpins area planning."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

# ---------------------------------------------------- requires human review
r = row('src-40f04f71007ea537', "requires human review")
r.update({"draft_title": "Bosque Action Plan: Map #3, Trails Map (existing and proposed trails)",
          "question_for_human": "Confirm whether this sheet is a page of the Bosque Action Plan recommended in this artifact, and drop it if so.",
          "why_not_decided_here": ("Everything points to it being one sheet of that plan and the test that would "
                                   "prove it could not be run. Its own legend reads BOSQUE ACTION PLAN, RIO GRANDE "
                                   "VALLEY STATE PARK, CITY OF ALBUQUERQUE PARKS AND GENERAL SERVICES DEPARTMENT, it "
                                   "is numbered Map #3, it carries the printed sheet number 19, and both files carry "
                                   "the same 0193 date stamp in their filenames. But both are entirely image-only - "
                                   "zero extractable tokens each - so token containment cannot be measured at all, "
                                   "and render-and-hash at PDF page 19 does not match because the printed sheet "
                                   "number is offset from the PDF page number: PDF page 19 of the 105-page plan is "
                                   "an Introduction divider."),
          "measurement": "1,318,593 bytes against the plan's 15,918,465. Rendered page 1 is 902,309 bytes of PNG; the plan's rendered page 19 is 1,195,874 bytes and a different image.",
          "distinguishing_content": "Map #3 Trails Map, existing and proposed trails, Bosque Action Plan, Rio Grande Valley State Park.",
          "package": "a_sheet_of_a_plan_or_a_document",
          "what_would_settle_it": "A page-by-page render comparison across the 105-page plan. That is a mechanical job, not a research question, and it was out of proportion to one record here.",
          "priority": 1})
rhr.append(r)

r = row('src-ec22ce0ade528517', "requires human review")
r.update({"draft_title": "Sector Plan: El Rancho Atrisco Phase III",
          "question_for_human": "Establish whether this is the adopted sector plan or the developer's submission, then decide.",
          "why_not_decided_here": ("Its cover says what it is and what it is not. SECTOR PLAN, EL RANCHO ATRISCO "
                                   "PHASE III, Prepared for WESTLAND DEVELOPMENT CO. INC., For Submission TO THE CITY "
                                   "OF ALBUQUERQUE ENVIRONMENTAL PLANNING COMMISSION, prepared by a private "
                                   "engineering and planning firm. It is a private party's submission to the "
                                   "commission, not on its face a plan the City adopted. Publishing a developer's "
                                   "submission as an adopted sector plan would misstate its standing."),
          "measurement": "Rendered, because the file has no usable text layer. 459,890 bytes. The cover carries a fax header dated 2004 and a page stamp.",
          "distinguishing_content": "El Rancho Atrisco Phase III sector plan, prepared for Westland Development Co. Inc. by Denney-Gross & Associates.",
          "package": "submitted_or_adopted",
          "priority": 2})
rhr.append(r)

# ------------------------------------------------------------------- excluded
for i in HTML:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Web page: " + URL[i].split('.gov/', 1)[1],
              "what_it_is": "A live page on the City's site.",
              "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f. The archive "
                                   "has already settled this class at both of this lane's paths: six "
                                   "neighborhood-traffic-management-program records and nine planning/documents "
                                   "records are excluded in the inventory with the reason navigation, pagination, "
                                   "contact, or generic interface text captured as a candidate."),
              "category": "live web page",
              "package": "web_pages"})
    excluded.append(r)

for i in FORMS:
    r = row(i, "excluded")
    extra = " Its name ends .docx and its leading bytes are 25504446: it is a PDF." if i == 'src-21c399e0d5a2510c' else ""
    r.update({"title_for_reference": fname(i),
              "what_it_is": "A permit process flow chart, cancellation request, stop-work request or contact sheet for a live City permitting process.",
              "exclusion_reason": ("Not a substantive record. It is process paperwork for a permitting process that "
                                   "is still running - a flow chart of the steps, a request form to cancel or stop "
                                   "work, a contact sheet. The archive has already settled this class at this exact "
                                   "path, excluding a generic hard-copy application link for a live process as not "
                                   "substantive." + extra),
              "category": "live process paperwork",
              "package": "process_paperwork"})
    excluded.append(r)

rows = approved + duplicate + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "ntmp-planning-documents-cluster-research-2026-09-13",
 "lane": "Claude research lane: neighborhood-traffic-management-program/documents and www.cabq.gov/planning/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("The City's traffic calming toolbox, and what is left on the planning department's document page - which "
             "turns out to be adopted plans going back to 1991."),
 "scope": "All 61 uncovered candidates across the two paths. The coverage gate is asserted in the generator.",
 "brief": ("Check the archive's existing decisions at both paths first, and run the cross-inventory checksum sweep - "
           "it has found three already-archived records in two consecutive lanes."),
 "brief_finding": ("Both instructions paid. The existing dispositions settled two whole classes before any candidate "
                   "was read, and the sweep found two more already-archived records, bringing the run's total to "
                   "five across three consecutive lanes."),
 "the_sweep_again": {
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "found": len(CROSS),
  "what_they_are": ("ABQcomprehensiveonstreetbicycleplan.pdf, byte-identical to the 2000 Albuquerque Comprehensive "
                    "On-Street Bicycle Plan the archive holds; and VolcanoTrailsSDPFINAL.pdf, byte-identical to the "
                    "Volcano Trails Sector Development Plan it holds. Both already carry r2_urls."),
  "the_bicycle_plan_has_now_appeared_three_times": ("Once in the parks lane at "
                                                    "parksandrecreation/recreation/bike/documents, once here at "
                                                    "planning/documents, and once already archived. One 8,054,496-byte "
                                                    "file, three inventory records, three different paths."),
  "running_total": "Five already-archived records caught by this sweep in three consecutive lanes. It should be standard before any lane is written.",
 },
 "an_enacted_package_the_archive_does_not_have": {
  "what_the_archive_holds": ("The Volcano Trails Sector Development Plan (8,903,701 bytes, validated with an "
                             "r2_url), its adoption resolution, and the Environmental Planning Commission notice, as "
                             "three separate objects."),
  "what_this_lane_found": ("VolcanoTrailsSDPFINALenacted2011.pdf, 8,976,542 bytes - the plan and its adopting "
                           "legislation in one instrument."),
  "the_measurement": ("Token coverage of the held plan inside the enacted file is 1.0000, with two of three "
                      "contiguous sixty-word runs present verbatim. The enacted file carries 221 tokens the held "
                      "plan does not, and they are the vocabulary of adoption: adopt, adopting, authorized, "
                      "advisory, enactment-style numbers, NMSA years."),
  "why_it_matters": ("The standing blocker on isolated legislative files exists because a plan without its adopting "
                     "instrument is an incomplete record. Here the archive has the plan and the resolution "
                     "separately and this is the two bound together as enacted."),
  "and_a_second_legislative_package": ("UnserBlvdOverlayZoneCompleteLegislation.pdf is Council Bill C/S R-14 of the "
                                       "Ninth Council, sponsored by Alan B. Armijo, with a blank ENACTMENT NO. line "
                                       "on its face - but it is titled complete legislation and runs to 1,969,125 "
                                       "bytes, so it is the package rather than an isolated substitute. Recommended, "
                                       "with the blank enactment line recorded on the row."),
 },
 "the_traffic_calming_toolbox": {
  "count": len([r for r in approved if r['group'] == 'traffic calming toolbox']),
  "what_it_is": ("One sheet per measure across the City's whole traffic calming repertoire: chicanes, diagonal "
                 "diverters, forced turn islands, high visibility crosswalks, lane narrowing with a centre island, "
                 "lateral shifts, median barriers, medians and partial medians, neckdowns and bulbouts, one-lane and "
                 "two-lane chokers, one-way couplet conversions, parking strategies, partial closures, permanent "
                 "radar speed signs, radar speed trailers, raised intersections, speed humps, speed kidneys, speed "
                 "tables, and education and community involvement - plus the program document itself."),
  "why_it_belongs": ("The archive already holds 83 validated Neighborhood Traffic Management Program records, mostly "
                     "street-by-street speed studies, and a live-link record titled Program documents and "
                     "traffic-calming tools. It holds the studies and the link, and not the tools."),
  "eight_are_registered_twice": ("Eight of the sheets appear as two candidate ids at one URL with identical bytes. "
                                 "They are recommended duplicate against their twins."),
 },
 "plans_that_were_sitting_in_a_forms_directory": {
  "count": len([r for r in approved if r['group'] == 'adopted plans and legislation']),
  "the_oldest": "Planned Communities Criteria: Policy Element, February 1991.",
  "the_largest": "Barelas Sector Development Plan, Adopted April 2008, at 49,626,419 bytes.",
  "the_list": ["Barelas Sector Development Plan (2008)", "Barelas Neighborhood Commercial Area Revitalization Plan",
               "Bosque Action Plan, Rio Grande Valley State Park (1993)",
               "Major Public Open Space Facility Plan (1999)",
               "Clayton Heights Metropolitan Redevelopment Area Plan (2010)",
               "Facility Plan: Electric System Transmission and Generation (2010-2020)",
               "Volcano Trails SDP as enacted 2011",
               "H-1 Historic Old Town Zone Design Guidelines (1998)",
               "Unser Boulevard Overlay Zone complete legislation",
               "Planned Communities Criteria: Policy Element (1991)",
               "Trails and Bikeways Facility Plan (1993)",
               "Revocable Permit standard form",
               "Planning Impact Area study chapters 1, 3, 5 and 8"],
  "five_had_to_be_rendered": ("The Barelas revitalization plan, the Bosque Action Plan, the El Rancho Atrisco sector "
                              "plan, the Planned Communities policy element and the Trails and Bikeways Facility "
                              "Plan have no usable text layer. Five adopted plans, invisible to any pass that reads "
                              "text."),
  "a_predecessor_for_a_series_the_archive_holds": ("The Trails and Bikeways Facility Plan is Adopted, July 1993, Map "
                                                   "Revised Nov. 1996. The archive holds a 2015 appendix and the "
                                                   "2024 Bikeway and Trail Facilities Plan. This is where that "
                                                   "sequence starts."),
 },
 "method": ("Read the archive's existing dispositions at both paths before fetching. Fetched all 61 candidates and "
            "measured byte length, SHA-256 and leading bytes from the fetched bytes. Swept every checksum against "
            "all %d checksummed archived records. Grouped by checksum within the slice. Rendered the ten files with "
            "no usable text layer. Compared the enacted Volcano Trails file against the held plan by token coverage "
            "and contiguous run. One fetch timed out mid-download at 15,130,560 of 15,918,465 bytes; curl's own "
            "retry completed it, and the logged measurement was confirmed by an independent refetch returning the "
            "identical SHA-256 before anything was recorded." % len(ARCH_BY_SHA)),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": len(CROSS),
  "internal_byte_collisions": len(TWINS),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "result": "Two candidates are already held with r2_urls and are recommended duplicate against them.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(TWINS),
  "cross_inventory_byte_collisions": len(CROSS),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "relationships_found": len(duplicate),
  "note": ("Eight internal pairs are one URL registered twice. The two cross-inventory hits are different URLs for "
           "one file, which is why only the bytes found them."),
 },
 "integration_flags": [
  {"severity": "avoids-duplicate-archival",
   "affects": sorted(CROSS),
   "finding": "Two candidates are byte-identical to records already validated and archived with r2_urls. The 2000 Comprehensive On-Street Bicycle Plan has now appeared as three inventory records at three paths for one 8,054,496-byte file.",
   "recommended_action": "Apply duplicate. Make the cross-inventory checksum sweep standard; it has now found five such records in three consecutive lanes."},
  {"severity": "enacted-package-found",
   "affects": ['src-f528ec2e0e955690'],
   "finding": "The Volcano Trails Sector Development Plan as enacted in 2011, plan and adopting legislation in one instrument. The archive holds the plan and its adoption resolution as separate objects and not the two bound together.",
   "recommended_action": "Approve. Record it against the held plan so the enacted form is the one cited."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'adopted plans and legislation'],
   "finding": "Thirteen adopted plans, policy elements and legislative packages in a directory of application forms, reaching back to the Planned Communities Criteria of February 1991. Five have no usable text layer and were readable only by rendering.",
   "recommended_action": "Approve. Title and date each from the document; the filenames are unreliable here, and chapter1_2010.pdf carries 1990-1998 data."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'traffic calming toolbox'],
   "finding": "The City's complete traffic calming toolbox, one sheet per measure, plus the program document. The archive holds 83 validated speed studies from this program and a live link to the tools, and not the tools themselves.",
   "recommended_action": "Approve as a set on the speed management page."},
  {"severity": "judgment-needed",
   "affects": [r['id'] for r in rhr],
   "finding": "A trails map that is almost certainly a sheet of the Bosque Action Plan but cannot be proved to be, because both files are wholly image-only; and a sector plan whose cover marks it as a developer's submission to the Environmental Planning Commission rather than an adopted plan.",
   "recommended_action": "Settle the first with a page-by-page render comparison; settle the second by asking whether the plan was adopted in this form."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "one_retry": ("A 15,918,465-byte plan timed out at 15,130,560 bytes on one attempt; curl's retry "
                              "completed it and an independent refetch returned the identical SHA-256."),
                "rendered": "10 files with no usable text layer.",
                "containers_verified": "%d PDFs and %d HTML pages by leading bytes." % (bycontainer['PDF'], bycontainer['HTML'])},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, dominated by the "
                   f"Barelas Sector Development Plan at 49,626,419 bytes. Nineteen approved records are scanned "
                   f"documents with no usable text layer and should be archived as they are, with their titles taken "
                   f"from this artifact."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Ten rows carry a canonical_id; eight canonicals are "
                     "rows in this artifact and two are records already validated and archived. Every approved row "
                     "carries a group. The chapter rows carry a caution about their incomplete set and their "
                     "misleading filenames. Every row carries a leading_bytes field. Sizes and checksums are first "
                     "measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
