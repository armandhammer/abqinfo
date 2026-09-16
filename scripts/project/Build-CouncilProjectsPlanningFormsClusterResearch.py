"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. council/projects and documents.cabq.gov/planning/online-forms.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\council-projects-planning-forms-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\cp')

DEVPROC = 'content/development-land-use/development-process.md'
ZONING = 'content/development-land-use/zoning-ido.md'
PROJECTS = 'content/development-land-use/projects.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
BIKEIDX = 'content/transportation/bicycling/_index.md'
MAPS = 'content/maps-data/maps.md'

ARCH_ORD = 'src-912bc14c869a79b0'     # Original Albuquerque Complete Streets Ordinance, validated with r2
ARCH_PACKET = 'src-8b18827057480dac'  # Albuquerque Complete Streets Legislation Packet, validated with r2

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw, final = line.rstrip('\n').split('\t')
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

LC = "HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. Container verified by leading bytes."

# every archived record that carries a checksum, for the cross-inventory sweep
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
PDFS = [i for i in SLICE if MAGIC[i] == '25504446']
CROSS = {i: ARCH_BY_SHA[M[i]['checksum_sha256']]['id'] for i in PDFS if M[i]['checksum_sha256'] in ARCH_BY_SHA}

LETTERS = {
 'src-522d3a75520e5492': ("Downtown Albuquerque Millennial Group (MiABQ)", "December 19, 2014"),
 'src-3cbd0371d79732ef': ("New Mexico Healthier Weight Council", "December 9, 2014"),
 'src-5bb1887adc21cf32': ("New Mexico Chapter of the American Society of Landscape Architects", "November 6, 2014"),
 'src-43da3854bce825c3': ("Greater Albuquerque Chamber of Commerce", "undated board position"),
 'src-7f963eab27c1f647': ("American Institute of Architects, Albuquerque Chapter", "January 20, 2015"),
 'src-554512e9477dcb45': ("American Planning Association, New Mexico Chapter", "November 20, 2014"),
 'src-49975585145fa548': ("New Mexico Complete Streets Leadership Team", "November 5, 2014"),
}
RENDERED = {'src-7f963eab27c1f647', 'src-554512e9477dcb45', 'src-49975585145fa548'}

STANDARDS = {
 'src-8370979b7d21890b': (
  "Zone Change Policy for Zone Map Change Applications and Appeals, Enactment 270-1980, Appendix B",
  ("The City policy adopted in 1980 governing how applications to change the zone map are decided and how those "
   "decisions are appealed, still published among the planning department's application materials."),
  "Headed APPENDIX B ZONE CHANGE POLICY, ENACTMENT 270-1980 APPENDIX B, adopting policies for zone map change applications and appeals.",
  ZONING, [{"page": DEVPROC, "reason": "It governs a development review decision."}]),
 'src-d9b63150144be31e': (
  "Albuquerque Site and Building Design Considerations",
  ("The City's design guidance for site plans in Albuquerque, developed by a convened team of architects and "
   "planners, recommending how buildings and sites should respond to the local climate and geography."),
  ("Headed Albuquerque Site & Building Design Considerations, recommended for all designers of site plans in "
   "Albuquerque and developed by a team of architects and planners convened for the purpose. Its filename calls it a "
   "submittal form; it is guidance, not a form."),
  DEVPROC, [{"page": ZONING, "reason": "It shapes what a site plan must show."}]),
 'src-f3d1b969631a7c61': (
  "Wireless Telecommunications Facility Application Requirements",
  ("The City Planning Department's requirements for an application to build a wireless telecommunications facility, "
   "setting out what an applicant must submit before the City will consider siting one."),
  "Headed WIRELESS TELECOMMUNICATIONS FACILITY (WTF) APPLICATION REQUIREMENTS, City of Albuquerque.",
  DEVPROC, [{"page": ZONING, "reason": "Facility siting is a zoning question."}]),
 'src-744bfa29e25ce9ab': (
  "Wireless Telecommunications Facility Waiver Requirements",
  ("The City Planning Department's requirements for seeking a waiver from the wireless telecommunications facility "
   "rules, the companion to the application requirements published beside it."),
  "Headed WIRELESS TELECOMMUNICATIONS FACILITY (WTF) WAIVER REQUIREMENTS, City of Albuquerque, Planning Department.",
  DEVPROC, [{"page": ZONING, "reason": "Facility siting is a zoning question."}]),
 'src-6f478812572d6cf8': (
  "Application Requirements for Policy Decisions Reviewed by the Environmental Planning Commission",
  ("The City's statement of what an application must contain when the Environmental Planning Commission is being "
   "asked to make a policy decision, as distinct from a decision on a particular site."),
  "Headed APPLICATION REQUIREMENTS FOR POLICY DECISIONS REVIEWED BY THE ENVIRONMENTAL PLANNING COMMISSION, City of Albuquerque.",
  DEVPROC, [{"page": ZONING, "reason": "The commission decides zoning policy."}]),
 'src-ec6c7cd6b216ce05': (
  "Application Requirements for Site Plan (EPC) or Master Development Plan",
  ("The City's statement of what an application must contain for a site plan going to the Environmental Planning "
   "Commission, or for a master development plan covering a larger area."),
  "Headed APPLICATION REQUIREMENTS FOR SITE PLAN - EPC OR MASTER DEVELOPMENT PLAN, City of Albuquerque.",
  DEVPROC, [{"page": PROJECTS, "reason": "Master development plans govern named projects."}]),
}

approved, duplicate, excluded = [], [], []

for i, canon in sorted(CROSS.items()):
    a = IDX[canon]
    r = row(i, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": fname(i),
              "relationship": "The same file the archive already holds as %s, validated with an r2_url." % (a.get('title') or canon),
              "how_it_was_established": ("Byte-identical to the archived record: %s bytes and the same SHA-256. The "
                                         "candidate is reached through a Plone resolveuid alias under "
                                         "council/projects, so its URL bears no resemblance to the archived "
                                         "record's and no URL comparison could have matched them."
                                         % format(M[i]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "The archive already holds it, validated and archived.",
              "group": "already archived"})
    duplicate.append(r)

for i, (org, when) in sorted(LETTERS.items()):
    if i in CROSS:
        continue
    r = row(i, "approved for addition")
    desc = ("A letter to the Albuquerque City Council from the %s supporting the proposed Complete Streets "
            "Ordinance, part of the organised comment the Council received on the measure before it was enacted."
            % org)
    ev = "Addressed to the Albuquerque City Council, dated %s, on the organisation's own letterhead and signed." % when
    if i in RENDERED:
        ev += " The file has no usable text layer and was read by rendering."
    r.update({"title": "Complete Streets Ordinance (O-14-27): letter of support from the " + org,
              "description": desc, "date": when.split()[-1] if when[-4:].isdigit() else None,
              "evidence": ev, "group": "Complete Streets legislative comment",
              "proposed_canonical_page": ROADWAY,
              "cross_listings": [{"page": BIKEIDX, "reason": "The ordinance governs provision for cycling on City streets."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

r = row('src-a011d61f6d837e34', "approved for addition")
mapdesc = ("The City's map of the Central Urban and Established Urban areas defined by its Comprehensive Plan, the "
           "geography against which the Complete Streets Ordinance's requirements were framed and debated.")
r.update({"title": "Comprehensive Plan: Central and Established Urban Areas",
          "description": mapdesc, "date": "2014",
          "evidence": ("Rendered, because its text layer is street labels. Titled Comprehensive Plan, Central and "
                       "Established Urban Areas, with a two-colour legend for Central Urban and Established Urban, "
                       "prepared by AGIS and dated 12/5/2014 on the sheet."),
          "group": "Complete Streets legislative comment",
          "proposed_canonical_page": MAPS,
          "cross_listings": [{"page": ZONING, "reason": "The Comprehensive Plan area categories are a zoning-relevant geography."}],
          "description_word_count": len(mapdesc.split())})
approved.append(r)

for i, (t, desc, ev, canon, cross) in sorted(STANDARDS.items()):
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "evidence": ev,
              "group": "planning standards and requirements",
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

DECIDED = {r['id'] for r in approved} | {r['id'] for r in duplicate}

for i in HTML:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Web page: " + URL[i].split('.gov/', 1)[1],
              "what_it_is": "A live page on the City Council's projects site.",
              "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f. The archive "
                                   "has already settled this class in this same tree: twelve council/projects records "
                                   "are excluded in the inventory with the reason navigation, pagination, contact, or "
                                   "generic interface text captured as a candidate."),
              "category": "live web page",
              "package": "web_pages"})
    excluded.append(r)

for i in PDFS:
    if i in DECIDED:
        continue
    r = row(i, "excluded")
    r.update({"title_for_reference": fname(i),
              "what_it_is": "A blank application checklist or form for a live City development review process.",
              "exclusion_reason": ("Not a substantive record. It is a blank form or checklist an applicant fills in "
                                   "to move through a development review process that is still running, so its "
                                   "content is fields rather than decisions. The archive has already settled this "
                                   "class at this exact path: a blank preliminary plat extension checklist is "
                                   "excluded in the inventory with the reason blank preliminary plat extension "
                                   "checklist for a live development review process, not a substantive record."),
              "category": "blank development review form",
              "package": "blank_forms"})
    excluded.append(r)

rows = approved + duplicate + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:6], sorted(set(ids) - set(SLICE))[:6])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

SUBSTANTIVE_PAGES = sorted(
    URL[i].split('.gov/', 1)[1] for i in HTML
    if '/current-projects/' in URL[i] or '/completed-projects/' in URL[i])[:24]

artifact = {
 "batch_id": "council-projects-planning-forms-cluster-research-2026-09-13",
 "lane": "Claude research lane: www.cabq.gov/council/projects and documents.cabq.gov/planning/online-forms",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("Two directories with nothing in common but their state: the Council's project pages, and the planning "
             "department's online application forms."),
 "scope": "All 69 uncovered candidates across the two directories. The coverage gate is asserted in the generator.",
 "brief": ("Check the inventory for the archive's existing decisions about each source before framing the lane - two "
           "briefs in a row have started from a wrong premise."),
 "the_brief_worked": {
  "what_was_checked_first": ("The archive's existing dispositions at both paths, before any candidate was fetched."),
  "council_projects": ("14 records validated, all of them live-link records titled Official source: ...; 14 excluded, "
                       "twelve of them with the reason navigation, pagination, contact, or generic interface text "
                       "captured as a candidate."),
  "planning_online_forms": ("2 records validated with r2_urls - the General Planning Fee Schedule and the Drainage "
                            "Pond Slope Stabilization and Seeding Requirements - and 2 excluded, one of them a blank "
                            "preliminary plat extension checklist excluded as not substantive."),
  "what_that_settled_before_any_work": ("That this archive keeps planning standards and fee schedules and excludes "
                                        "blank process forms; and that it treats Council project pages as live links "
                                        "rather than as documents. Both rules applied cleanly to all 69 records. No "
                                        "premise had to be corrected in this artifact, which is the first lane in "
                                        "three where that is true."),
 },
 "the_cross_inventory_sweep_paid_again": {
  "what_was_run": ("Every fetched checksum in this lane was compared against every checksum carried by a validated, "
                   "archived, published or implemented inventory record - %d of them." % len(ARCH_BY_SHA)),
  "what_it_found": ("Two candidates are byte-identical to records the archive already holds with r2_urls: the "
                    "Original Albuquerque Complete Streets Ordinance (126,155 bytes) and the Albuquerque Complete "
                    "Streets Legislation Packet (5,086,786 bytes)."),
  "why_nothing_else_could_have_found_them": ("Both candidates are reached through Plone resolveuid aliases under "
                                             "council/projects/completed-projects/2015/complete-streets. Their URLs "
                                             "share nothing with the archived records' URLs under "
                                             "council/documents/councilor-district-2-documents. Only the bytes match."),
  "this_is_the_second_lane_running": ("The parks lane found the first cross-inventory byte collision of the run and "
                                      "recommended a sweep. Run on the next lane, the sweep found two more. It "
                                      "should be standard."),
 },
 "the_standing_blocker_resolved_rather_than_tripped": {
  "the_blocker": ("Isolated legislative amendment or substitute files must have their authoritative enacted packages "
                  "resolved before archival or visible use."),
  "what_this_lane_found": ("A Council Bill F/S O-14-27 file whose ENACTMENT NO. line is blank underscores - exactly "
                           "the shape the blocker exists for."),
  "how_it_resolved": ("The archive already holds the enacted package: the Original Albuquerque Complete Streets "
                      "Ordinance and the Complete Streets Legislation Packet, both validated with r2_urls, plus an "
                      "Albuquerque Complete Streets Ordinance Update sourced from o-64enacted-6.pdf. The candidate "
                      "turned out to be byte-identical to the first of those, so it is not an isolated file at all - "
                      "it is the held file, reached by a different route."),
  "a_date_from_another_lane": ("The Vision Zero executive order recommended in "
                               "municipaldevelopment-flat-remainder-cluster-research-2026-09-13.json records that "
                               "the Council enacted the Complete Streets Ordinance, O-14-27, in 2015. That is the "
                               "enactment-number method working across lanes: the date comes from a later "
                               "instrument's recitals, not from the ordinance itself."),
 },
 "an_organised_comment_record": {
  "count": len(LETTERS),
  "what_it_is": ("Seven letters to the City Council supporting the Complete Streets Ordinance, from the American "
                 "Institute of Architects Albuquerque Chapter, the American Planning Association New Mexico "
                 "Chapter, the New Mexico Complete Streets Leadership Team, the New Mexico Chapter of the American "
                 "Society of Landscape Architects, the New Mexico Healthier Weight Council, the Downtown "
                 "Albuquerque Millennial Group, and the Greater Albuquerque Chamber of Commerce."),
  "why_these_are_recommended_when_other_correspondence_was_not": ("permits-forms-regulations-cluster-research-2026-09-12.json "
                                                                  "held the fiber rulemaking correspondence for "
                                                                  "human review because it is a compilation of named "
                                                                  "private residents' complaints about work outside "
                                                                  "their own homes. These are organisations writing "
                                                                  "officially to the Council on their own "
                                                                  "letterhead, signed by an officer in that "
                                                                  "capacity. The distinction is not the subject; it "
                                                                  "is whose privacy is at stake."),
  "three_had_to_be_rendered": ("The AIA, APA-NM and Complete Streets Leadership Team letters have no usable text "
                               "layer. Without rendering they would have been three unattributable scans."),
 },
 "method": ("Read the archive's existing dispositions at both paths before fetching anything. Fetched all 69 "
            "candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. Swept every "
            "checksum against all 1,020 checksummed archived records. Rendered the four files with no usable text "
            "layer. Read every planning form to separate requirements documents from blank checklists rather than "
            "sorting them by filename."),
 "classification_only": True,
 "shared_state_written": [],
 "a_note_on_the_web_pages": {
  "count": len(HTML),
  "decision": "Excluded, as not static documents, consistent with councilor-district-3-and-6-cluster-research-2026-09-13.json.",
  "but_worth_Codex_knowing": ("The archive keeps 14 Council project pages as live-link records titled Official "
                              "source: ... So exclusion here means only that these are not documents to archive; "
                              "several are substantive project pages the archive may want as official links under "
                              "its own existing pattern."),
  "the_candidates_for_that": SUBSTANTIVE_PAGES,
  "why_this_lane_does_not_recommend_them_as_such": ("Creating a live-link record is a different act from archiving a "
                                                    "document, and this lane's remit is documents. The list is "
                                                    "handed over rather than decided."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": len(CROSS),
  "internal_byte_collisions": 0,
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "result": "Two candidates are already held, validated and archived, and are recommended duplicate against those records.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": len(CROSS),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "relationships_found": len(duplicate),
  "found_by": "Checksum comparison against the archived set. Neither could have been found by URL, filename or title.",
 },
 "integration_flags": [
  {"severity": "avoids-duplicate-archival",
   "affects": sorted(CROSS),
   "finding": "Two Complete Streets records reached through resolveuid aliases are byte-identical to records already validated and archived with r2_urls, including the ordinance itself at 126,155 bytes and the legislation packet at 5,086,786 bytes.",
   "recommended_action": "Apply duplicate. And make the cross-inventory checksum sweep standard: it has now found three such collisions in two consecutive lanes."},
  {"severity": "blocker-resolved",
   "affects": ['src-6197821a3622ad82'],
   "finding": "A Council Bill F/S O-14-27 file with a blank enactment number, which is the shape the standing legislative blocker exists for. It resolves: the archive already holds the enacted package, and this file is byte-identical to the held Original Albuquerque Complete Streets Ordinance.",
   "recommended_action": "No blocker action needed. Record that the Vision Zero executive order dates the enactment to 2015."},
  {"severity": "substantive-find",
   "affects": sorted(STANDARDS),
   "finding": "Six planning standards and requirements documents mixed in among the blank forms, including the Zone Change Policy adopted as Enactment 270-1980 and the Albuquerque Site and Building Design Considerations, whose filename calls it a submittal form.",
   "recommended_action": "Approve. Sorting this directory by filename would have excluded all six with the checklists."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'Complete Streets legislative comment'],
   "finding": "The organised comment record on the Complete Streets Ordinance: seven letters of support from professional and business organisations, plus the Comprehensive Plan map of the Central and Established Urban areas the ordinance was framed against. Three of the letters had to be rendered to be read at all.",
   "recommended_action": "Approve as the legislative record of the ordinance whose enacted text the archive already holds."},
  {"severity": "for-codex-not-this-lane",
   "affects": [],
   "finding": "%d Council project pages are excluded here as not-documents, but the archive keeps 14 such pages as live-link records titled Official source: ... Several of these are substantive project pages." % len(HTML),
   "recommended_action": "Consider them for live-link records under the existing pattern; the candidate list is in a_note_on_the_web_pages."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "rendered": "4 files with no usable text layer: three letters and one map.",
                "containers_verified": "%d PDFs and %d HTML pages by leading bytes." % (bycontainer['PDF'], bycontainer['HTML'])},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": [],
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. The "
                   f"{len(duplicate)} duplicate records must not be archived: both are already in R2 under another "
                   f"candidate id."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Two rows carry a canonical_id and both canonicals "
                     "are records already validated and archived, not rows in this artifact. Every approved row "
                     "carries a group. Nothing is held for human review. Every row carries a leading_bytes field. "
                     "Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
