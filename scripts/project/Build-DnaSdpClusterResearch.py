"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\dnasdp-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\dn\fetch.log')

AREA = 'content/development-land-use/area-sector-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'

OLD1 = 'src-1c078f889adede14'   # validated + published: the 9.17.2010 draft, Part 1
OLD2 = 'src-0a1c11a9bce94067'
OLD3 = 'src-1794e14599b5ed91'
OLD4 = 'src-86c15e73ab9895c6'

NEW1 = 'src-9f4896d16e30c694'
NEW2 = 'src-7231803ce1ad2ff6'
NEW3 = 'src-52dc90346e567ac1'
NEW4 = 'src-380ac9326e0001af'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw, v = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    RAW[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET on both URL forms; size_bytes and checksum_sha256 measured "
      "from the bytes returned by the raw file URL, because the inventory record carried neither")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


PKG_NOTE = ("One of the four non-overlapping files the City publishes as the EPC draft. The four join without gap or "
            "overlap and total 165 pages, exactly matching the 165 pages of the four-file September draft they "
            "replace. Part 1 is the canonical visible record; Parts 2 to 4 are required components of the same "
            "delivery and must be archived with it.")


def part(i, n, title, pages, desc, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": "2010-10-28", "pages": pages,
              "multipart": {"package": "Downtown Neighborhood Area Sector Development Plan Update, EPC Draft 10.28.2010",
                            "part": n, "of": 4, "canonical_visible_record": NEW1,
                            "package_pages": 165, "note": PKG_NOTE},
              "proposed_canonical_page": AREA})
    if extra:
        r.update(extra)
    return r


approved = [
 part(NEW1, 1,
      "Downtown Neighborhood Area Sector Development Plan Update, EPC Draft, October 28, 2010 — Part 1 of 4: front matter through Section 3, Community Issues",
      66,
      ("The version of the Downtown Neighborhood Area sector plan that went to the Environmental Planning Commission "
       "covers the area's history, assets, existing conditions, and the public involvement that shaped it, and it "
       "opens the four-file package the Commission reviewed."),
      extra={
       "evidence": ("Born-digital PDF with a full text layer. The cover reads \"Downtown Neighborhood Area Sector "
                    "Development Plan Update / epc DRAFT 10.28.2010\" and every page footer carries \"EPC DRAFT "
                    "10.28.10\", where the September package reads \"DRAFT 9.17.2010\" and \"DRAFT 9.17.10\". Prepared "
                    "for the City of Albuquerque by Consensus Planning, Inc. with Harwick Transportation Group and "
                    "Christopher Wilson. Its own Section 3 states: \"The draft Sector Plan was submitted to the "
                    "Environmental Planning Commission (EPC) on October 28, 2010.\""),
       "why_retained": ("It is the plan as the Commission actually considered it, and the Commission's decision on it "
                        "is in this same batch. The archive currently publishes the working draft from six weeks "
                        "earlier instead. See supersedes_a_published_record."),
       "cross_listings": [
         {"page": ZONING, "reason": "Sections 5 and 6 of the package are implementation policies and zoning regulations for roughly 280 acres, which is zoning content."},
       ],
      }),
 part(NEW2, 2,
      "Downtown Neighborhood Area Sector Development Plan Update, EPC Draft, October 28, 2010 — Part 2 of 4: Section 4 Goals and Objectives through Section 6 Zoning Regulations",
      70,
      ("The substantive middle of the plan states the goals and objectives drawn from the public meetings, the "
       "implementation policies and strategies built on them, and the opening zoning regulations and development "
       "standards for the plan area."),
      extra={"evidence": "Born-digital PDF, full text layer, every page footed \"EPC DRAFT 10.28.10\". Opens at SECTION 4: GOALS & OBJECTIVES.",
             "cross_listings": [{"page": ZONING, "reason": "It is where the plan's development standards begin."}]}),
 part(NEW3, 3,
      "Downtown Neighborhood Area Sector Development Plan Update, EPC Draft, October 28, 2010 — Part 3 of 4: Proposed Zoning map",
      1,
      ("A single large-format sheet maps the zoning proposed for every parcel in the Downtown Neighborhood Area, "
       "keyed by SU-2 category, and is the map the sector plan's zoning regulations operate on."),
      extra={"evidence": "Single-sheet born-digital PDF titled \"Proposed Zoning / Downtown Neighborhood Area SDP\", parcel-level, SU-2 categories keyed across the plan area.",
             "cross_listings": [{"page": ZONING, "reason": "It is a parcel-level proposed-zoning map."}],
             "caution": "Proposed, not adopted. Label it as the map the EPC reviewed, never as current zoning."}),
 part(NEW4, 4,
      "Downtown Neighborhood Area Sector Development Plan Update, EPC Draft, October 28, 2010 — Part 4 of 4: remaining Section 6 Zoning Regulations and the Action Agenda",
      28,
      ("The closing file carries the rest of the zoning regulations, including the special use zones and "
       "non-conforming use rules, and the action agenda that assigns the plan's recommendations to responsible "
       "parties and timeframes."),
      extra={"evidence": ("Born-digital PDF, full text layer, footed \"EPC DRAFT 10.28.10\". Its first page differs "
                          "from the September file's first page: the September Part 4 opens on NON-CONFORMING USES, "
                          "the October one opens on SPECIAL USE ZONE - SU-2/SU-1 at printed page 129, which is how the "
                          "two packages can be told apart from their first sheet alone."),
             "cross_listings": [{"page": ZONING, "reason": "Non-conforming use rules and special use zones are zoning code content."}]}),

 {**row("src-7472d7fda76be8bb", "approved for addition"),
  "title": "Official Notice of Decision: Environmental Planning Commission Recommendation of Approval, Downtown Neighborhood Area Sector Development Plan (Project 1008570, 10EPC-40063), April 7, 2011",
  "description": ("The Environmental Planning Commission's formal decision recommends that the City Council adopt the "
                  "Downtown Neighborhood Area Sector Development Plan, and sets out the findings supporting it and the "
                  "numbered conditions that change specific pages of the plan."),
  "date": "2011-04-07",
  "pages": 18,
  "evidence": ("Born-digital PDF with a full text layer, headed OFFICIAL NOTIFICATION OF DECISION, City of Albuquerque "
               "Planning Department, Current Planning Division, dated April 7, 2011, File Project #1008570 / "
               "10EPC-40063 SEC DEV PLAN PHSE 2, DOWNTOWN NEIGHBORHOOD AREA. Staff planner Petra Morris. Zone Atlas "
               "Maps J-13, J-14, K-13 and K-14. Boundaries: Mountain Road north, Central Avenue south, 19th Street "
               "west, and 4th, 5th, 7th and 8th Streets east, approximately 280 acres. It records that the Commission "
               "voted that a RECOMMENDATION OF APPROVAL be forwarded to City Council."),
  "why_retained": ("It is the decision, and it is also the errata. The conditions are page-specific edits to the plan "
                   "text — for example condition 10, \"P.101 F1 shall read 30% instead of 50%. Add the following "
                   "sentence 'Garage doors shall not be counted towards this requirement.'\", and condition 8 setting "
                   "usable open space at 360 square feet per dwelling unit, or 500 where garages have no alley access. "
                   "Anyone reading the EPC draft without this document will read superseded numbers. It also names the "
                   "old and proposed zoning categories across the whole plan area."),
  "proposed_canonical_page": AREA,
  "cross_listings": [{"page": ZONING, "reason": "Its conditions are the operative amendments to the plan's zoning regulations and development standards."}],
  "caution": ("A recommendation to the Council, not the Council's adoption. Pages 15 to 18 are the notification list "
              "and carry the names and street addresses of individual residents, as published by the City."),
  "description_word_count": 0},

 {**row("src-3e18d918097011be", "approved for addition"),
  "title": "Downtown Neighborhoods Area Boundary and Historic Districts Map, September 17, 2010",
  "description": ("The City AGIS map draws the sector plan boundary against Old Town, the Downtown 2010 plan area, "
                  "City historic overlay zones and six National or State historic districts, and marks the boundary "
                  "adjustment proposed at Central and 9th."),
  "date": "2010-09-17",
  "pages": 1,
  "evidence": ("Single-sheet PDF with a thin text layer; rendered and read. Titled DOWNTOWN NEIGHBORHOODS AREA, "
               "produced by AGIS at 1 inch to roughly 500 feet. Legend: Downtown Neighborhoods SDP, City Historic "
               "Overlay Zones, Downtown 2010 SDP, and the Eighth Street/Forrester, Fourth Ward, Manzano Court, Old "
               "Albuquerque, Orilla de la Acequia and Watson historic districts. A callout at the southeast corner "
               "reads PROPOSED BOUNDARY ADJUSTMENT."),
  "why_retained": ("It is the only sheet in the cluster that shows the plan boundary against the neighbouring "
                   "regulatory geographies, and the only one that shows what was proposed to change about that "
                   "boundary. The proposed-zoning map in Part 3 shows zoning, not this."),
  "proposed_canonical_page": AREA,
  "cross_listings": [{"page": ZONING, "reason": "It is the clearest single map of the City historic overlay zones inside the plan area, which are zoning overlays."}],
  "description_word_count": 0},
]

superseded = [
 {**row("src-5ba380f7478082d6", "superseded"),
  "title_for_reference": "Downtown Neighborhoods Area map, October 2009 printing",
  "pages": 1,
  "canonical_id": "src-3e18d918097011be",
  "canonical_url": IDX["src-3e18d918097011be"].get('direct_file_url'),
  "canonical_state": "recommended for addition in this batch",
  "basis": "The same AGIS map, one revision earlier, before the boundary adjustment was drawn.",
  "measurement": ("Normalized-text ratio 0.9648 with token coverage 0.9892 of this file inside the successor. The "
                  "difference is exactly five tokens present only in the successor — proposed, boundary, adjustment, "
                  "park and 9thcentral — and one present only here, parkcentral. Rendering both confirms it: the "
                  "successor adds the PROPOSED BOUNDARY ADJUSTMENT callout and redraws the southeast corner. Both "
                  "sheets carry the identical AGIS source footer "
                  "Q:\\AGISFILE\\PROJECTS\\DebbieStover\\MAG-Oct09-DowntownNeighborhood\\AREAMAP8X11.mxd, which is what "
                  "proves they are one map and not two."),
  "hash_found_it": False},
]


def X(i, title, pages, reason, category, date=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages,
              "exclusion_reason": reason, "category": category})
    if date:
        r["date"] = date
    if extra:
        r.update(extra)
    return r


FLYER = ("A one-page public meeting announcement: date, time, venue, a two-line description of the topic, and a "
         "contact. It records an invitation, not a proceeding. Meeting handouts are excluded throughout this run, in "
         "rail-yards-advisory-board-cluster-research-2026-09-11.json and "
         "police-oversight-task-force-cluster-research-2026-09-11.json.")

SUMMARY = ("A consultant's summary of one public meeting in the plan's outreach programme. The plan itself carries "
           "this ground in Section 3, Community Issues, which states the process and the dates and which is retained "
           "in this batch. These summaries are the working papers behind that section, not City decisions.")

excluded = [
 X("src-f6cb8022c9bad856", "Flyer: first public meeting, January 16, 2010, Hotel Blue", 1, FLYER, "meeting announcement", "2010-01-16",
   extra={"note": "Issued by the Downtown Neighborhood Association and City Councillor Debbie O'Malley; City contact Petra Morris, Planning."}),
 X("src-5cb612ddbcbe92db", "Flyer: second public meeting, February 20, 2010, Manzano Day School", 1, FLYER, "meeting announcement", "2010-02-20"),
 X("src-3106004a467b8963", "Flyer: open house, September 25, 2010", 1, FLYER, "meeting announcement", "2010-09-25"),
 X("src-caab00f4b2622ae4", "Meeting summary: first public meeting, Hotel Blue", 3, SUMMARY, "public meeting summary",
   extra={"date_conflict": ("This file dates the first public meeting to December 16, 2009. The flyer for that meeting "
                            "(src-f6cb8022c9bad856) gives January 16, 2010 at Hotel Blue, 10:00 a.m., and Section 3 of "
                            "the plan itself lists the three general public meetings as January 16, 2010, February 20, "
                            "2010 and September 25, 2010. Same venue, same start time, same described content. Two "
                            "independent records say January 16, 2010 and one says December 16, 2009, so the summary "
                            "sheet carries a date error. Recorded because the file is excluded and the error would "
                            "otherwise travel uncorrected if anyone cites it.")}),
 X("src-d52b47891442f405", "Meeting summary: second public meeting, February 20, 2010, Manzano Day School", 1, SUMMARY, "public meeting summary", "2010-02-20"),
 X("src-34b6b231754ced73", "Meeting summary: third public meeting, September 25, 2010, MRCOG office (first issue)", 4, SUMMARY, "public meeting summary", "2010-09-25",
   extra={"version_relationship": ("Superseded in substance by src-d41b1b924b7714b1, the revised issue, at normalized "
                                   "ratio 0.9933. The revisions are not cosmetic: the attendance line is corrected to "
                                   "\"51 attendees signed in\", a sentence is added stating that residential density "
                                   "in the Central zone follows the R-3 zone in the Code, and \"outdoor patio dining\" "
                                   "is changed throughout to \"outdoor restaurant seating\" in the passage setting the "
                                   "Central Avenue front setback at 10 feet, or 15 with seating in front. Both files "
                                   "are excluded, so no canonical_id is asserted; the relationship is recorded here "
                                   "rather than lost."),
          "if_reinstated": "Should either ever be wanted, take src-d41b1b924b7714b1 and not this one."}),
 X("src-d41b1b924b7714b1", "Meeting summary: third public meeting, September 25, 2010, MRCOG office (revised issue)", 4, SUMMARY, "public meeting summary", "2010-09-25",
   extra={"version_relationship": "The revised issue of src-34b6b231754ced73. See that row for what changed.",
          "but_see": ("Its revised passages are the clearest short statement of what changed between the September "
                      "and October drafts of the plan, in particular the Central Avenue front setback and the "
                      "treatment of outdoor restaurant seating.")}),
 X("src-fc32f636bdb143c2", "Key observations from the Downtown Neighborhood Area tours, October 15, 16 and 19, 2009", 3,
   ("The project team's working notes from three neighbourhood walking tours, explicitly \"a follow-up to the more "
    "detailed tour notes taken by the project team\". Early-stage observations that the plan's own existing-conditions "
    "and community-issues sections carry forward."),
   "planning process working notes", "2009-10-19"),
 X("src-e892793e1773f333", "DNA Tour Map: walking tour routes for October 15, 16 and 19, 2009", 1,
   ("A route handout for the three walking tours, colour-coded by date with start and end points. It organises an "
    "event; it records nothing about the plan area that the boundary map and the proposed-zoning map do not."),
   "meeting handout", "2009-10-19"),
 X("src-dd1a8f9f37ef2db0", "DNASDP documents collection landing page", None,
   "The Plone collection landing page for this directory, not a document.", "collection landing page"),
]

for r in approved:
    if not r.get("description_word_count"):
        r["description_word_count"] = len(r["description"].split())

rows = approved + superseded + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 17, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
pkg_bytes = sum(M[i]["size_bytes"] for i in (NEW1, NEW2, NEW3, NEW4))
old_pkg_bytes = sum(IDX[i]["size_bytes"] for i in (OLD1, OLD2, OLD3, OLD4))
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "dnasdp-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/dnasdp-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The Downtown Neighborhood Area Sector Development Plan Update collection in the Albuquerque City Council library.",
 "scope": "All 17 pending-review candidates. The directory holds 21 records; the other four are the September 2010 draft package, and they are the subject of this lane's main finding rather than of its classification.",
 "brief": "Fetch both URL forms per the district-4 Plone /view finding, and test each candidate against R2 objects already held before recommending anything.",
 "brief_finding": ("The test against what is already held produced the opposite of the usual result. In every prior "
                   "cluster the check has kept something out of the queue; here it establishes that the record "
                   "ABQInfo currently publishes is the superseded one. The four pending files named "
                   "1dna_sector_plan_-_part_1..4.pdf are the EPC Draft of 28 October 2010. The four files already in "
                   "the inventory, one validated and published and three consolidated under it, are the working draft "
                   "of 17 September 2010. See supersedes_a_published_record."),
 "second_finding": ("The Commission's decision on that plan is also in this directory and was never connected to it: "
                   "an 18-page Official Notice of Decision of 7 April 2011 recommending Council adoption, whose "
                   "numbered conditions are page-specific edits to the plan text. The plan and its errata have sat in "
                   "the same folder untriaged."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 17 candidates on both URL forms and measured byte "
            "length and SHA-256 from the raw form. Compared all checksums against the 1,612 checksummed inventory "
            "records. Fetched the four September package files read-only for comparison and confirmed their bytes "
            "match the inventory exactly. Compared the two packages part by part on normalized text and token "
            "coverage, and read the running footers, which is the split-package method recorded in "
            "planned-growth-strategy-cluster-research-2026-09-11.json. Rendered every image-only or thin-text sheet "
            "rather than classifying it from its filename."),
 "classification_only": True,
 "shared_state_written": [],
 "supersedes_a_published_record": {
  "what_is_published": (f"content/development-land-use/area-sector-plans.md line 13 publishes \"Downtown Neighborhood "
                        f"Area Sector Development Plan Update (Draft, September 17, 2010; multipart)\", inventory "
                        f"record {OLD1}, status validated. Its Parts 2, 3 and 4 ({OLD2}, {OLD3}, {OLD4}) are marked "
                        f"duplicate with the note \"Consolidated into multipart canonical record {OLD1}\", which was a "
                        f"consolidation marker rather than a duplicate finding."),
  "what_this_lane_found": (f"The same four-part package exists one revision later as the EPC Draft of 28 October 2010: "
                           f"{NEW1}, {NEW2}, {NEW3} and {NEW4}, all pending review, all sitting in the same directory "
                           f"under filenames prefixed with a 1."),
  "evidence": [
   "Cover: the September Part 1 reads \"DRAFT 9.17.2010\"; the October Part 1 reads \"epc DRAFT 10.28.2010\".",
   "Running footer on every page: \"DRAFT 9.17.10\" against \"EPC DRAFT 10.28.10\".",
   ("The October Part 1 says so itself, in Section 3: \"The draft Sector Plan was submitted to the Environmental "
    "Planning Commission (EPC) on October 28, 2010. The EPC is tasked with reviewing the Plan and providing "
    "recommendations to the City Council for its consideration.\""),
   ("Structure is identical and content is close but not equal, which is what a revision looks like: part-by-part "
    "page counts 66, 70, 1 and 28 in both packages, 165 pages either way; normalized-text quick ratios 0.9828, "
    "0.9875, 0.9934 and 0.9895; token coverage of the September text inside the October text 0.9209, 0.9764, 0.9495 "
    "and 1.0000."),
   ("The revisions are substantive, not cosmetic. The October Part 4 opens on SPECIAL USE ZONE - SU-2/SU-1 at printed "
    "page 129 where the September Part 4 opens on NON-CONFORMING USES, so the section order changed. The revised "
    "third-meeting summary in this directory independently describes plan changes made in that window, including the "
    "Central Avenue front setback and the treatment of outdoor restaurant seating."),
   ("Byte sizes differ in both directions — October Parts 1, 2 and 4 are larger and Part 3 is smaller — so nothing "
    "here is a re-encoding of the same file. No checksum in this cluster collides with any of the 1,612 checksummed "
    "inventory records."),
  ],
  "recommended_action": (f"Resolve {OLD1} to superseded with canonical {NEW1}, and {OLD2}, {OLD3} and {OLD4} to "
                         f"superseded with canonicals {NEW2}, {NEW3} and {NEW4} respectively. Replace the site entry "
                         f"at content/development-land-use/area-sector-plans.md with the October package, and pair it "
                         f"with the Notice of Decision recommended in this batch."),
  "claude_did_not_modify": ("Those four records are terminal and out of this lane's classification scope, and the site "
                            "was not touched. They are named here as a recommendation to the integration lane, in the "
                            "same form as the district-5 correction in "
                            "councilor-district-9-cluster-research-2026-09-12.json."),
  "the_published_entry_is_not_wrong_about_status": ("The site text already says \"This four-file draft was published "
                                                    "for review and should not be read as an adopted plan\", which is "
                                                    "correct for either package. Neither is adopted. The issue is "
                                                    "which draft, not whether it is a draft."),
  "also_not_site_ready": (f"{OLD1} carries no r2_url and its validation_status records \"R2 archival follow-up pending "
                          f"explicit approval\", so the published entry links the live City file only. Under the "
                          f"standing rule a static document is not site-ready until its original is archived and the "
                          f"archive download verified. Whichever package is published, that step is still outstanding."),
  "footprint_note": (f"The October package is {pkg_bytes:,} bytes against {old_pkg_bytes:,} for the September package. "
                     f"Archiving the successor and not the predecessor is roughly a wash in storage and a clear gain "
                     f"in accuracy."),
 },
 "multipart_convention_conflict": {
  "observation": (f"Two conventions for multi-file packages are in use. In this directory a prior pass marked Parts 2 "
                  f"to 4 duplicate and consolidated them under Part 1. In "
                  f"planned-growth-strategy-cluster-research-2026-09-11.json each component was approved on its own "
                  f"row with a multipart block naming the canonical visible record."),
  "what_this_artifact_does": ("Follows the Planned Growth Strategy convention: all four October parts are approved for "
                             "addition, each carrying a multipart block that names Part 1 as the canonical visible "
                             "record. Marking a non-overlapping component duplicate is not wrong as bookkeeping but it "
                             "reads as a duplicate finding, and this cluster now contains real duplicate and "
                             "supersession findings that would be confused with it."),
  "for_integration": "Whichever convention Codex settles on, the four October parts must be archived together; one visible record should present the package.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text": 3,
  "relationships_found_by_rendering": 1,
  "note": ("Four relationships, none of them reachable by hashing: the package supersession across eight files, the "
           "two AGIS printings of one map, and the two issues of the third meeting summary. The map pair was settled "
           "by rendering both sheets and by the identical AGIS source path in their footers; the token difference is "
           "five words."),
 },
 "integration_flags": [
  {"severity": "published-record-superseded",
   "affects": [OLD1, OLD2, OLD3, OLD4],
   "finding": "ABQInfo publishes the 17 September 2010 working draft of the Downtown Neighborhood Area sector plan. The 28 October 2010 EPC draft of the same package sits pending in the same City directory.",
   "recommended_action": f"Resolve the four September records to superseded against their October counterparts and republish the page entry. Claude did not modify them."},
  {"severity": "decision-record-found",
   "affects": ["src-7472d7fda76be8bb"],
   "finding": "The EPC Official Notice of Decision of 7 April 2011 recommends Council adoption and carries numbered conditions that edit specific pages of the plan.",
   "recommended_action": "Approve and publish alongside the plan. Reading the draft without it yields superseded figures."},
  {"severity": "archive-from-raw-url",
   "affects": raw_differs,
   "finding": "Records in this directory are inventoried under Plone /view URLs that serve an HTML wrapper rather than the file. Same pattern as councilor-district-4.",
   "recommended_action": "Archive from raw_file_url and cite authoritative_url."},
  {"severity": "not-site-ready",
   "affects": [OLD1],
   "finding": "The published sector-plan entry links the live City file only; the record carries no r2_url and its own validation note defers archival.",
   "recommended_action": "Whichever package is published, complete the R2 archival and download verification."},
  {"severity": "discovery-lead",
   "affects": ["src-7472d7fda76be8bb"],
   "finding": "The Notice of Decision recommends adoption to the City Council; the Council's adopting instrument is not held anywhere in the inventory, and no adopted Downtown Neighborhood Area sector plan is held.",
   "recommended_action": "Queue the Council enactment for Project 1008570 / 10EPC-40063. It is the only thing that would let the site drop the draft caveat."},
  {"severity": "editorial",
   "affects": ["src-caab00f4b2622ae4"],
   "finding": "An excluded meeting summary misdates the first public meeting as December 16, 2009; the flyer and the plan's own Section 3 both give January 16, 2010.",
   "recommended_action": "None needed, the file is excluded. Recorded so the error does not travel if anyone cites it."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 17, "http_200": 17, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "reference_fetches": "The four September package files were fetched read-only for comparison, all HTTP 200, and their bytes and SHA-256 match the inventory exactly.",
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "16 genuine PDFs and one HTML collection page by leading bytes."},
 "approved_for_addition": approved,
 "superseded": superseded,
 "excluded": excluded,
 "archival_note": (f"All 6 approved records are static PDFs and are inventory-only until an R2 archive object exists "
                   f"for each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, of which "
                   f"{pkg_bytes:,} is the four-part plan package. Every one is born-digital with a text layer, so "
                   f"full-text search reaches all of them without optical character recognition."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Four of the six approved rows are components of one "
                      "package and carry a multipart block naming src-9f4896d16e30c694 as the canonical visible "
                      "record; they must be archived together. One superseded row carries a canonical_id that is "
                      "itself approved in this batch. The largest recommendation in this artifact is not a row at all: "
                      "supersedes_a_published_record asks for four terminal records outside this lane's scope to be "
                      "resolved and for a live site entry to be repointed. Sizes and checksums are first "
                      "measurements; the inventory held neither for any pending record here."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the four September package files were fetched read-only"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
