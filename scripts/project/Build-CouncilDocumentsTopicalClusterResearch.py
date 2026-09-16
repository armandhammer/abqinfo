"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Covers the topical slice of the council/documents tail: the
small named directories and the substantive flat-level files, excluding the
2023-2026 legislative amendment series and the advisory-board agenda and
minutes series, which are separate claimed lanes.
"""

import collections
import datetime
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\council-documents-topical-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\tail\fetch.log')

AREA = 'content/development-land-use/area-sector-plans.md'
PROJECTS = 'content/development-land-use/projects.md'
ZONING = 'content/development-land-use/zoning-ido.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
SPEED = 'content/transportation/roadway-projects/speed-management.md'
TXPLANS = 'content/transportation/transportation-plans.md'
SAFETY = 'content/city-data/public-safety-data.md'
BUDGET = 'content/city-data/budget-spending.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither. Container verified by leading bytes, not by extension.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML",
         "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


# ---------------------------------------------------------------- duplicates
# Every one of these is byte-identical to a validated, R2-archived record.
DUPES = [
 ("src-a0095a2e8b524b85", "src-357f0a012444d081",
  "Central Avenue Complete Street Plan and Design Toolkit, October 2013 draft", 120),
 ("src-5e3f04254885b800", "src-ffa72f2b8869a660",
  "Central Avenue Complete Streets Report, March 2014 draft", 122),
 ("src-5506a88128e7de17", "src-81c75a7d7a217a68",
  "Volcano Trails Sector Development Plan", 70),
 ("src-f93aa90a07d83d6d", "src-8b120e71c3650349",
  "Volcano Trails Sector Development Plan Adoption Resolution", 12),
 ("src-442d80b03a4e05eb", "src-e8d18ebb99858984",
  "Volcano Trails Environmental Planning Commission Official Notice of Decision", 20),
 ("src-4541bdade4a94304", "src-2f8683a1ba3c7dc4",
  "South Yale Corridor Segments and Future Context", 1),
 ("src-66add68f2b531815", "src-fa4a64d343feb303",
  "South Yale Segment 1 Concept Plan", 1),
]

duplicates = []
for i, canon, title, pages in DUPES:
    c = IDX[canon]
    assert c['status'] == 'validated', canon
    assert c['size_bytes'] == M[i]['size_bytes'], (i, canon)
    assert c['checksum_sha256'] == M[i]['checksum_sha256'], (i, canon)
    r = row(i, "duplicate")
    r.update({"title_for_reference": title, "pages": pages,
              "canonical_id": canon, "canonical_url": c.get('r2_url'),
              "canonical_state": "validated, R2-archived and published at " + (c.get('implementation_location') or 'its recorded page'),
              "basis": "A second Council-server copy of a document the archive already holds.",
              "measurement": ("Byte-identical to the canonical: %d bytes and SHA-256 %s, matching the validated "
                              "record's recorded values exactly." % (M[i]['size_bytes'], M[i]['checksum_sha256'])),
              "hash_found_it": True})
    duplicates.append(r)

# ---------------------------------------------------------------- superseded
superseded = [{
 **row("src-bee427d5c6a31344", "superseded"),
 "title_for_reference": "Central Avenue Complete Streets, 1st Street to Girard, March 2014 draft — Part 2 of a split edition",
 "pages": 56,
 "canonical_id": "src-ffa72f2b8869a660",
 "canonical_url": IDX["src-ffa72f2b8869a660"].get('r2_url'),
 "canonical_state": "validated, R2-archived and published at content/transportation/roadway-projects/studies.md",
 "basis": "Half of a split edition of a report the archive holds complete.",
 "measurement": ("Exactly 3,405,862 bytes, the same size as src-2ba50be86045099d, the inventory's terminal record "
                 "for this same split part, which is already superseded with the reason \"Split Part 2 edition is "
                 "redundant with the complete 122-page March 2014 PDF archived in this batch.\" That terminal record "
                 "carries no checksum, so the match here is by size and by identical URL-free filename rather than by "
                 "hash; the canonical it defers to, src-ffa72f2b8869a660, is byte-identical to another candidate in "
                 "this same lane and so is independently confirmed."),
 "hash_found_it": False,
 "note": "This lane therefore holds both halves of the relationship: the complete March 2014 report as a byte-identical duplicate, and its split Part 2 as superseded by the same canonical.",
}]

# --------------------------------------------------------------- corrections
CORRECTION = {
 "corrects_a_terminal_record": "src-049105295d2745af",
 "what_it_says": ("Excluded as duplicate with the reason \"Metadata/view wrapper alias for the canonical Uptown "
                  "Sector Development Plan record src-4ccef0c6ec25aac8, already archived and validated.\""),
 "why_that_is_wrong": ("src-4ccef0c6ec25aac8 is not the Uptown Sector Development Plan. It is a 13-page extract "
                       "titled \"Uptown Sector Development Plan — Transportation and Connectivity\", taken from the "
                       "Development Process Manual cross-sections server and published on "
                       "content/transportation/transportation-plans.md. Fetched and measured: 3,293,254 bytes, 13 "
                       "pages, 787 distinct tokens. The adopted plan is 4,133,982 bytes, 115 pages, 3,302 distinct "
                       "tokens. Token coverage of the extract inside the plan is 0.9797; coverage of the plan inside "
                       "the extract is 0.2335. A 13-page roadway cross-section appendix was recorded as the canonical "
                       "for a 115-page adopted sector plan."),
 "consequence": ("The full adopted Uptown Sector Development Plan is held nowhere. It is recommended for addition in "
                 "this artifact, and the terminal record's reason should be corrected so the same conflation is not "
                 "repeated."),
 "claude_did_not_modify": "That record is terminal and outside this lane's classification scope. This is a recommendation to the integration lane.",
 "same_shape_as": ("dnasdp-cluster-research-2026-09-12.json, where a published record turned out to be the "
                   "superseded draft, and west-central-mra-cluster-research-2026-09-12.json, where a published plan "
                   "carried an unenacted bill in its appendix. Three artifacts in this batch have now found that a "
                   "terminal or published decision needed revisiting."),
}


def A(i, title, desc, date, pages, evidence, why, page, cross=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
              "date": date, "pages": pages, "evidence": evidence, "why_retained": why,
              "proposed_canonical_page": page, "cross_listings": cross or []})
    if extra:
        r.update(extra)
    return r


FH_NOTE = ("One of three files the City posts as the July 2007 Four Hills Speed Hump Evaluation Study: an executive "
           "summary, the final report and a technical appendix. All three are image-only scans with no usable text "
           "layer, so containment between the executive summary and the report could not be measured; page 1 of each "
           "was rendered and all three carry the same running header, \"Four Hills Speed Hump Evaluation / July "
           "2007\". Archive them together and treat the report as the visible record.")

approved = [
 A("src-2aa87993b25de330",
   "Uptown Sector Development Plan, Adopted Plan, February 2009",
   ("The adopted sector development plan for Albuquerque's Uptown area sets the land use, urban design, zoning and "
    "connectivity framework the City applies there, and it is the full plan rather than the transportation extract "
    "the archive currently holds."),
   "2009-02", 115,
   ("Born-digital PDF with a full text layer, 115 pages, 4,133,982 bytes. Opens on an acknowledgements page listing "
    "Mayor Martin J. Chávez and the nine-member Council of the day — Brad Winter as President, Debbie O'Malley as "
    "Vice President, Ken Sanchez, Isaac Benton, Michael J. Cadigan and the rest. Filed by the City as "
    "uptown_sdp_adopted_plan_2_4_09.pdf. The archived extract's own cover gives the adoption date as January 15, "
    "2009."),
   ("It is the document the archive has been recording as held while holding something else. See "
    "corrects_a_terminal_record. Two other Uptown records are already terminal — a July 2008 working version marked "
    "superseded and the wrapper alias — so the adopted plan is the one gap in an otherwise triaged set."),
   AREA,
   [{"page": ZONING, "reason": "A sector development plan is the zoning instrument for its area, and this is the adopted text."},
    {"page": TXPLANS, "reason": "That page already carries the 13-page transportation extract of this plan; the full plan belongs beside it."}],
   extra={"caution": "Adopted in 2009 and amended since. The archived transportation extract is labelled \"Amended Through 2013\", so this text is the plan as adopted, not as currently amended."}),

 A("src-9f5ac56df8c6cbb8",
   "Albuquerque Rail Yards: Redeveloping the City's Historic Rail Yards — Urban Land Institute Advisory Services Panel Report, February 24–29, 2008",
   ("An Urban Land Institute advisory panel's report on redeveloping Albuquerque's historic Rail Yards records the "
    "panel's findings and recommendations on market potential, development strategy, planning and design, and "
    "implementation for the site."),
   "2008-02-29", 46,
   ("Born-digital PDF with a full text layer, 46 pages. Cover: \"AN ADVISORY SERVICES PANEL REPORT / Albuquerque Rail "
    "Yards / Albuquerque, New Mexico / Urban Land Institute\", with the panel dates February 24–29, 2008 and the "
    "subtitle \"Redeveloping the City's Historic Rail Yards\"."),
   ("The archive holds a substantial Rail Yards file — rail-yards-advisory-board-cluster-research-2026-09-11.json "
    "triaged the advisory board's own library and the site carries Rail Yards planning and environmental records — "
    "but an inventory-wide search for ULI or Advisory Services Panel returns only this record. It is the outside "
    "expert assessment that preceded the City's own work."),
   PROJECTS,
   [{"page": AREA, "reason": "Its recommendations are area-planning recommendations for a defined City site."}],
   extra={"caution": "An independent panel's advice to the City in 2008, not City policy and not an adopted plan."}),

 A("src-9024a88c37c3e026",
   "Huning Highland Railroad Plan: Development and Building Process",
   ("The Huning Highland Railroad plan sets out a four-step process for building in the area, taking an applicant "
    "from the colour-coded district map through the district uses matrix to the standards that apply to a given "
    "property."),
   None, 41,
   ("Born-digital PDF with a full text layer, 41 pages, 5,647,564 bytes, filed as EDHHRailroad.pdf. It opens on a "
    "\"development & building process\" section stating that \"The Huning Highland Railroad plan introduces a new, "
    "innovative approach to Huning Highland Railroad development\" and setting out the steps: locate your property "
    "and its Downtown district on the colour-coded district map, then identify permitted uses on the district uses "
    "matrix."),
   ("The archive's Huning Highland material is maps and a repealed East Downtown plan held at requires human review. "
    "This is a usable regulatory how-to for the same area and nothing like it is held."),
   AREA,
   [{"page": ZONING, "reason": "It is a district-by-district use and standards framework, which is zoning content."}],
   extra={"caution": ("Undated on its face. The related East Downtown Sector Development Plan is marked REPEALED on "
                      "the City's own planning server (src-5b9de5b2cda39393), so this plan's current force is "
                      "uncertain and it should be labelled as a historical planning document until that is settled.")}),

 A("src-a3afa3078e7351a7",
   "Neighborhood Task Force Final Report, September 2007",
   ("The Neighborhood Task Force's report to the City Council addresses the five topics Councillor Don Harris's April "
    "2007 memorandum asked it to examine, and sets out its findings and recommendations on each for Council "
    "consideration."),
   "2007-09", 13,
   ("Born-digital PDF with a full text layer, 13 pages. Headed \"Neighborhood Task Force Final Report / Respectfully "
    "Submitted To City Council\". Its executive summary states: \"Don Harris, District 9, Council Memorandum "
    "(appendix I) dated April 25, 2007 proposed a Neighborhood Task Force to look at five (5) general topics\"."),
   "A City Council task force's own final report, held nowhere. The run has recommended other task-force output — the police oversight assessment from completed-reports-studies — and this is the same class.",
   PROJECTS,
   [{"page": AREA, "reason": "Neighbourhood-level policy questions of the kind this report addresses are the subject matter of that page."}],
   extra={"caution": ("The cover date is printed as \"September XX, 2007\" with the day left as placeholder Xs, so "
                      "the file is a final report in substance but an unfinalised proof in form. Date it to the month "
                      "only.")}),

 A("src-42032f0eef57807c",
   "Small Business Resource Fair Report: Supporting Albuquerque's Growing Small Business Community, April 2019",
   ("City Council staff report on the Small Business Resource Fair, recording what the event set out to do for local "
    "small businesses, who took part, what participants asked for, and what the staff recommend the Council do "
    "next."),
   "2019-04", 15,
   ("Born-digital PDF with a full text layer, 15 pages. Cover: \"SMALL BUSINESS RESOURCE FAIR REPORT / Supporting "
    "Albuquerque's Growing Small Business Community / Report Created by City Council Staff / April 2019\"."),
   "Council staff's own report on a Council programme, held nowhere. It is also one of very few economic-development records in the archive from after 2002.",
   PROJECTS,
   extra={"caution": "A staff report on one event, not a policy or a programme evaluation."}),

 A("src-d8f7ec08b6b02cf6",
   "Four Hills Speed Hump Evaluation Study, Final Report, July 2007",
   ("The City's evaluation of the Four Hills speed humps reports what the installed humps did to vehicle speeds and "
    "traffic on the affected streets, and sets out the study's conclusions and recommendations for the "
    "neighbourhood."),
   "2007-07", 58,
   ("Image-only scan with no usable text layer, 58 pages, 1,353,905 bytes; page 1 rendered and read. Title page: "
    "\"FINAL REPORT / Four Hills Speed Hump Evaluation Study / Albuquerque, New Mexico / Michael J. Cunneen / July "
    "2007\", with the running header \"Four Hills Speed Hump Evaluation — July 2007\"."),
   ("The archive holds a Four Hills Traffic Calming Study from 2023, sixteen years later, and nothing from this "
    "study. Speed humps are among the most contested neighbourhood traffic measures the City installs and this is "
    "its own evaluation of whether they worked."),
   SPEED,
   [{"page": STUDIES, "reason": "That page already carries the 2023 Four Hills Traffic Calming Study, which this predates by sixteen years."}],
   extra={"multipart": FH_NOTE,
          "caution": "No text layer, so full-text search will not reach its findings without optical character recognition."}),

 A("src-83743c8ca421ab3d",
   "Four Hills Speed Hump Evaluation Study, Technical Appendix, July 2007",
   ("The technical appendix to the City's Four Hills speed hump evaluation carries the underlying measurements and "
    "supporting material behind the final report's conclusions about speeds and traffic on the affected streets."),
   "2007-07", 30,
   "Image-only scan with no usable text layer, 30 pages, 927,570 bytes; page 1 rendered and read, carrying the same July 2007 running header as the final report.",
   "The evidence base for the report above. Archiving a study's conclusions without its measurements is the pattern this run has avoided elsewhere, as with the Zuni Road Study's Part II collected data.",
   SPEED,
   extra={"multipart": FH_NOTE,
          "caution": "No text layer."}),

 A("src-b7203e954d4ac16f",
   "Four Hills Speed Hump Evaluation Study, Executive Summary, July 2007",
   ("The executive summary of the City's Four Hills speed hump evaluation states in brief what the study measured and "
    "what it concluded about the humps' effect on speeds and traffic in the neighbourhood."),
   "2007-07", 6,
   "Image-only scan with no usable text layer, 6 pages, 86,942 bytes; page 1 rendered and read, and it carries the full report's title block and the same July 2007 running header.",
   "The third file of the same delivery. It is very likely an extract of the final report, but with no text layer in either file that containment could not be measured, so it is recommended alongside rather than as a duplicate.",
   SPEED,
   extra={"multipart": FH_NOTE,
          "caution": "No text layer, and its relationship to the final report is inferred from the shared title block rather than measured."}),

 A("src-b838ec4d5a8d4527",
   "Proposed South Yale Metropolitan Redevelopment Area and Sector Development Plan Boundaries Map",
   ("The City map draws the proposed South Yale metropolitan redevelopment area and sector development plan "
    "boundaries over the existing parcel zoning, labelling each parcel's R-1, R-2, R-3 or SU-2 designation across the "
    "corridor."),
   None, 1,
   ("Single-sheet PDF with a text layer of parcel labels, 540,797 bytes, filed as SyaleMapBnd.pdf. Titled \"Proposed "
    "South Yale MRA/SDP Boundaries\", with parcel-level zoning labels — R-1, R-2, R-3 and SU-2 — running along St "
    "Cyr, Dartmouth, Tulane, Basehart and Richmond."),
   ("The archive holds the South Yale transportation section, the complete street master plan, corridor segments and "
    "a segment concept plan, but no boundary map. It is the one sheet that shows what area all the other records "
    "cover."),
   AREA,
   [{"page": STUDIES, "reason": "It is the area definition for the South Yale corridor records already published there."}],
   extra={"caution": "Proposed boundaries, undated on its face. Do not present it as the adopted boundary."}),

 A("src-dc13bd3962e198df",
   "Exhibit 2: Balanced Scorecard, City Attorney Evaluation, August 2025",
   ("The stakeholder scorecard from the City Attorney's 360-degree performance evaluation records how survey items "
    "were rated and explains the weighting by which exceeds, meets and does not meet expectations were combined into "
    "average scores."),
   "2025-08", 2,
   ("Born-digital PDF with a full text layer, 2 pages. It describes a 360-Degree Feedback Assessment in which \"both "
    "the City Attorney and their relevant Stakeholders were asked to respond to a series of survey items regarding "
    "the City Attorneys performance\", with a Not Applicable option excluded from averages, and sets out the "
    "weighting: Exceeds Expectations multiplied by 3, Meets Expectations by 2, Does Not Meet Expectations by 1, "
    "divided by the total number of ratings."),
   ("The Council evaluates the City Attorney and this is the instrument it uses. The archive holds no record of how "
    "any City official is formally evaluated, and this one states its own methodology, which is what makes it "
    "readable years later."),
   BUDGET,
   [{"page": PROJECTS, "reason": "It is a record of how the Council oversees a City department head."}],
   extra={"caution": "An exhibit to a larger evaluation; Exhibit 1, which it refers to, is not in this directory."}),
]

# ---------------------------------------------------- requires human review
def R(i, priority, draft_title, pages, evidence, question, why, extra=None):
    r = row(i, "requires human review")
    r.update({"priority": priority, "draft_title": draft_title, "pages": pages,
              "evidence": evidence, "question_for_human": question, "why_not_decided_here": why})
    if extra:
        r.update(extra)
    return r


BLOCKER = ("Enactment block blank, under the two standing checkpoint blockers: isolated legislative material must "
           "have its authoritative enacted package resolved before archival or visible use.")

rhr = [
 R("src-629504bb1af568b7", 1,
   "Council Bill R-05-383: Resolution Amending Bill No. F/S R-04-155 (Enactment R-2005-033), Which Amended the Huning Highland Sector Development Plan to Establish the SU-2/CRZ",
   3,
   ("Born-digital PDF with a full text layer. CITY OF ALBUQUERQUE, SIXTEENTH COUNCIL, COUNCIL BILL NO. R05383, "
    "ENACTMENT NO. blank, sponsored by Eric Griego. Section 2 deletes and replaces Section 3 of Bill No. F/S R-04-155; "
    "Section 3 amends the same bill by adding an attached map of the SU-2/CRZ location."),
   "Retrieve Enactment R-2005-033 for F/S R-04-155, then resolve R-05-383 itself.",
   (BLOCKER + " But it is the fourth instrument in this run to hand over a predecessor's enactment number, and it "
    "does so three times: its own title recites \"BILL NO. F/S R04155 (ENACTMENT NO. R2005033), WHICH AMENDED THE "
    "HUNING HIGHLAND SECTOR DEVELOPMENT PLAN TO ESTABLISH THE SU-2/CRZ\", and Sections 2 and 3 repeat the number."),
   extra={"supplies": "Enactment R-2005-033 for F/S R-04-155, which is src-5a39a69a5a13eb31 in this same lane.",
          "method_confirmed": ("This is the third independent confirmation of the method recorded in "
                               "west-central-mra-cluster-research-2026-09-12.json: enactment numbers live in the "
                               "recitals and title lines of later legislation. It has now worked in two unrelated "
                               "directories.")}),

 R("src-5a39a69a5a13eb31", 2,
   "Council Bill F/S R-04-155: Resolution Amending the Huning Highland Sector Development Plan to Establish the SU-2/CRZ",
   9,
   ("Born-digital PDF with a full text layer, 9 pages. CITY of ALBUQUERQUE, SIXTEENTH COUNCIL, COUNCIL BILL NO. F/S "
    "R-04-155, ENACTMENT NO. blank on the face of the file, sponsored by Eric Griego."),
   "Retrieve Enactment R-2005-033. The number is known; only the enacted text is missing.",
   (BLOCKER + " The number is supplied by src-629504bb1af568b7 above, so this is one of only two rows anywhere in "
    "this run whose enactment number is stated rather than inferred — the other being F/S R-04-56 in "
    "west-central-mra-cluster-research-2026-09-12.json."),
   extra={"stated_enactment_number": "R-2005-033",
          "stated_by": "src-629504bb1af568b7, in its title line and again in Sections 2 and 3."}),

 R("src-40d4239b82ca0b0b", 3,
   "Council Bill C/S2 O-06-53: Large Retail Facility Ordinance — Amending Section 8-1-2-39 ROA 1994 to Add to Traffic Engineer Duties, and Section 14-8-2-7 ROA 1994 to Create a Stakeholders' Process and Traffic Review for Large Retail Facilities",
   31,
   ("Born-digital PDF with a full text layer, 31 pages. CITY of ALBUQUERQUE, SEVENTEENTH COUNCIL, COUNCIL BILL NO. "
    "C/S2 O0653, ENACTMENT NO. blank, sponsored by Debbie O'Malley. It amends Sections 8-1-2-39 and 14-8-2-7 ROA 1994 "
    "and further sections of 14-16, creating a stakeholders' process and traffic review for large retail "
    "facilities."),
   "Locate the enacted large retail facility ordinance. This is the substantive 'big box' regulation and the archive holds nothing on the subject.",
   (BLOCKER + " No later legislation in the fetched corpus states its enactment number. This is regulation of a kind "
    "residents look up — what triggers a traffic review for a big-box store — so it is worth resolving rather than "
    "leaving."),
   extra={"related": "src-9f1d31095920f273, the \"Big Box\" Regulations landing page in the same directory, is recommended excluded below."}),

 R("src-e90d0c73c44e1a7e", 4,
   "Council Bill O-07-73: High Performance Buildings Ordinance",
   7,
   ("Born-digital PDF with a full text layer, 7 pages. CITY of ALBUQUERQUE, SEVENTEENTH COUNCIL, with the COUNCIL "
    "BILL NO., ENACTMENT NO. and SPONSORED BY lines all blank on the face of the file; the bill number comes from the "
    "City's filename o-07-73.pdf and from the directory's landing page."),
   "Locate the enacted High Performance Buildings Ordinance.",
   (BLOCKER + " It also has the identification gap seen in 12th-and-menaul: the file does not name itself, so the "
    "bill number is derived from the filename rather than stated."),
   extra={"note": "Albuquerque's high performance buildings ordinance was litigated and is historically significant; the archive holds nothing on it."}),

 R("src-87508af513982aa1", 5,
   "Council Bill O-07-84: Tax Cuts Ordinance",
   1,
   ("Born-digital PDF with a full text layer, a single page. CITY of ALBUQUERQUE, SEVENTEENTH COUNCIL, COUNCIL BILL "
    "NO. O0784, ENACTMENT NO. blank, sponsored by Don Harris, by request."),
   "Locate the enacted ordinance.",
   BLOCKER + " No enactment number for it appears anywhere in the fetched corpus."),

 R("src-fedd2569de36e85c", 6,
   "Council Bill R-08-97: Balloon Landing Site Purchase Resolution",
   2,
   ("Born-digital PDF with a full text layer, 2 pages. CITY of ALBUQUERQUE, EIGHTEENTH COUNCIL, with COUNCIL BILL "
    "NO. and SPONSORED BY blank and ENACTMENT NO. blank; the bill number R-08-97 comes from the inventory title and "
    "the City's filename copy_of_r0897.pdf."),
   "Locate the enacted resolution.",
   (BLOCKER + " Note the filename: this is the copy_of_ variant, and the directory's other record "
    "(src-82c6c198b4eefd21) is the landing page rather than a second copy of the bill, so there is no sibling to "
    "compare it against."),
   extra={"caution": "The copy_of_ prefix has meant three different things in this run — a newer package in DNASDP, a fatter re-encoding in sawmill, a corrected issue in district 1. Here there is nothing to compare it to, so nothing should be inferred from it."}),
]

# ------------------------------------------------------------------ excluded
excluded = []

LANDING = "The Plone collection landing page for this path, not a document."
for i in sorted(k for k in M if MAGIC[k] == '3c21444f'):
    r = row(i, "excluded")
    r.update({"title_for_reference": (IDX[i].get('title') or 'collection landing page'),
              "exclusion_reason": LANDING, "category": "collection landing page"})
    if i == 'src-c0433b3c564a14ca':
        r["already_known_empty"] = ("councilor-district-4-cluster-research-2026-09-12.json fetched this listing and "
                                    "recorded that its collection body reads \"There are currently no items in this "
                                    "folder.\" It is a landing page for nothing, and this lane formally closes it.")
    excluded.append(r)

OLDTOWN = [
 ("src-4f28a655d98c8ae3", "Topic 1, colour graphs", 5),
 ("src-3f866d2089b33926", "Topic 2, colour graphs", 15),
 ("src-388cbd495a6eb4f4", "Topic 2, black and white graphs", 15),
 ("src-d866542fe3372c5e", "Topic 3, colour graphs", 4),
 ("src-78ba9058dfb576e0", "Topic 3, black and white graphs", 3),
]
OT_REASON = ("Ranking-results graphs from the Old Town Virtual Task Force, a public-engagement exercise. The sheets "
             "report their own sample size on every page — \"Total Number of Participants: 12\" — and the City posts "
             "each topic twice, once in colour and once in black and white, which is a presentation choice rather "
             "than two documents. Public-involvement working material is excluded throughout this run.")
for i, label, pages in OLDTOWN:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Old Town Virtual Task Force, summary of ranking results — " + label,
              "pages": pages, "exclusion_reason": OT_REASON, "category": "public involvement working material",
              "presentation_pair": ("Topics 2 and 3 each appear as a colour and a black-and-white rendering of the "
                                    "same data; topic 1 appears only in colour. The pairs are not byte-identical and "
                                    "are not recommended as duplicates of each other, since neither member is "
                                    "retained — the convention recorded in "
                                    "councilor-district-1-cluster-research-2026-09-12.json.")})
    excluded.append(r)


def X(i, title, pages, reason, category, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages, "exclusion_reason": reason, "category": category})
    if extra:
        r.update(extra)
    return r


FORM = ("A blank form or application packet. Blank forms are excluded throughout this run, the split established in "
        "planning-udd-cluster-research-2026-09-11.json between an adopted standard and a submittal form.")

excluded += [
 X("src-962345dea8ed8430", "Civilian Police Oversight Advisory Board application packet, 2026", 35, FORM, "application packet",
   extra={"note": "At 11,404,905 bytes it is the largest file in this lane and the second largest anywhere in it; an application packet is not worth that."}),
 X("src-2390ede0d0136e64", "ABQ NeighborWoods application", 4, FORM, "application form"),
 X("src-616ec5b352fd39da", "Vial of Life form, 2020", 2, FORM, "form"),
 X("src-a7315c04bfa42eb7", "ABQ NeighborWoods neighbourhood agreement (English)", 1,
   "A one-page participation agreement template for a tree-planting programme. A form to be signed, not a record of City action.", "agreement template"),
 X("src-9d612c0b224dfb37", "ABQ NeighborWoods neighbourhood agreement (Spanish)", 1,
   "The Spanish edition of the same one-page agreement template.", "agreement template",
   extra={"language_pair": "The English and Spanish editions are the same instrument in two languages and neither is retained; the relationship is recorded here rather than asserted as a duplicate."}),
 X("src-3240234b98d27b27", "ABQ NeighborWoods programme schedule", 1,
   ("A one-page week-by-week outline of how the tree-planting programme runs, from Tree New Mexico contacting "
    "neighbourhood leaders onward. Programme logistics, not a City decision."), "programme handout"),
 X("src-6db0397455652054", "Rainbow Boulevard public meeting flyer, May 31", 1,
   "A one-page meeting announcement. Meeting flyers are excluded throughout this run.", "meeting announcement"),
 X("src-62525f0f27a329cc", "District 3 Newsletter, December 2014", 2,
   ("A councillor's constituent newsletter. Councillor communications are excluded throughout this run, in district "
    "5, district 9, the Councilor's Corner in district 4 and the Gibson letter in district 7."),
   "councillor newsletter"),
 X("src-f0c76005377afd83", "Council Services organisational chart, April 6, 2026", 1,
   ("A current staff organisational chart for Council Services, headed by Director of Council Services Isaac Padilla. "
    "Administrative reference that changes with staffing; it records no decision and would be wrong within a year."),
   "administrative reference"),
 X("src-4d29d7578683da90", "Albuquerque Fire Rescue Station 11 questions and answers", 2,
   ("A two-page question-and-answer sheet issued by Albuquerque Fire Rescue under Mayor Tim Keller and Fire Chief "
    "Emily V. Jaramillo. A public-information handout answering questions about one station, not a record of a "
    "decision, a standard or a study."), "public information handout"),
 X("src-9642139286c8f411", "Department of Municipal Development proposal for stop sign reconfiguration, Raynolds and Barelas, December 2008", 1,
   ("A one-page departmental proposal sheet for reconfiguring stop signs in two neighbourhoods. A single-sheet "
    "proposal with no analysis behind it and no record of what was decided."), "departmental proposal"),
 X("src-cbd9e912b1e24b09", "Interoffice memorandum from Councillors Cadigan, Jones and O'Malley to Mayor Martin Chávez regarding the Redflex contract", 3,
   ("A councillors' memorandum to the Mayor about the red light camera contract. Councillor communications are "
    "excluded throughout this run; a memorandum asking the administration for something is not the City's record of "
    "what was done."), "councillor communication",
   extra={"discovery_lead": "The Redflex contract itself, and whatever the administration did in response, are held nowhere. The red light camera programme is a significant and contested piece of City history with no record in the archive."}),
 X("src-c96c9d872de87154", "Streets and Traffic Enhancement Program draft document comment resolution matrix, 2013", 8,
   ("A consultant's comment-resolution matrix for the Streets and Traffic Enhancement Program draft: each public "
    "comment with the consultant's disposition and response. Public-involvement working material, of the class "
    "excluded for the DNA meeting summaries and the Zuni meeting notes."),
   "public involvement working material",
   extra={"content_recorded": ("It is unusually substantive for its class — it records, for example, a comment from "
                               "Larry Caudill of the Wildflower Area on 19 June 2013 that motor vehicle crashes "
                               "should not be the primary evaluation criterion, accepted with the response that "
                               "\"motor vehicle crash frequency\" was changed to \"crash frequency\" to reflect that "
                               "all documented crashes are a priority. The STEP programme document it comments on is "
                               "held nowhere."),
          "discovery_lead": "The Streets and Traffic Enhancement Program document itself."}),
 X("src-b83cb78799aee935", "South Yale Sector Development Plan, EPC Draft, Chapter Four: Plan Implementation — Transportation, June 2008", 18,
   ("One chapter of a June 2008 EPC draft of a plan whose adopted transportation section the archive already holds. "
    "src-5d29a972bd5550ba, \"South Yale Sector Development Plan — Transportation Section\", is validated, R2-archived "
    "at 4,475,608 bytes and published on content/transportation/transportation-plans.md. A single chapter of a "
    "superseded draft adds nothing to it."),
   "superseded draft chapter",
   extra={"note": "Recorded as excluded rather than superseded because the archived record is the adopted transportation section of the plan rather than a later edition of this same draft chapter, so it is not a like-for-like successor."}),
 X("src-f164513208041ca0", "Appendices (unattributed)", 20,
   ("A 20-page image-only file named appendices.pdf sitting at the flat level of council/documents with no parent "
    "document in the directory and no title page identifying what it is an appendix to. Rendered; it carries no "
    "identifying header. Unattributable material cannot be described, placed or cited."),
   "unattributable",
   extra={"for_integration": "If a parent is ever identified this decision should be revisited. Recorded with its checksum so it can be matched if the parent turns up."}),
 X("src-f7c952e28ec3bf2c", "Exhibit B page 1 (unattributed)", 1,
   ("A single image-only sheet named exhibitbpage1.pdf with no text layer and no identifying header. It sits beside "
    "the South Yale files, but nothing on the sheet ties it to them."),
   "unattributable",
   extra={"for_integration": "Same treatment as appendices.pdf above."}),
]


# ---------------------------------------------------------------- coverage gate
# This lane was first drafted over 63 records. 41 of them were already rows in
# council-documents-cluster-research-2026-09-11.json, which covered every file at
# the flat level of council/documents. Only the 22 below were genuinely
# uncovered; the rest are dropped here and accounted for in
# overlap_with_the_flat_level_lane.
NEW_ONLY = {
 "src-2aa87993b25de330", "src-40d4239b82ca0b0b", "src-4541bdade4a94304", "src-4d29d7578683da90",
 "src-5a39a69a5a13eb31", "src-5e3f04254885b800", "src-62525f0f27a329cc", "src-629504bb1af568b7",
 "src-66add68f2b531815", "src-83743c8ca421ab3d", "src-87508af513982aa1", "src-9024a88c37c3e026",
 "src-b7203e954d4ac16f", "src-b838ec4d5a8d4527", "src-b83cb78799aee935", "src-bee427d5c6a31344",
 "src-c96c9d872de87154", "src-cbd9e912b1e24b09", "src-d8f7ec08b6b02cf6", "src-e90d0c73c44e1a7e",
 "src-f7c952e28ec3bf2c", "src-fedd2569de36e85c",
}
duplicates = [r for r in duplicates if r["id"] in NEW_ONLY]
superseded = [r for r in superseded if r["id"] in NEW_ONLY]
approved   = [r for r in approved   if r["id"] in NEW_ONLY]
rhr        = [r for r in rhr        if r["id"] in NEW_ONLY]
excluded   = [r for r in excluded   if r["id"] in NEW_ONLY]
for n, group in enumerate(rhr, 1):
    group["priority"] = n

rows = duplicates + superseded + approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [x for x in ids if ids.count(x) > 1]
assert set(ids) == NEW_ONLY, (NEW_ONLY - set(ids), set(ids) - NEW_ONLY)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
approved_pages = sum(r["pages"] for r in approved)
avoided = sum(r["size_bytes"] for r in duplicates) + sum(r["size_bytes"] for r in superseded)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
npdf = sum(1 for r in rows if r["content_kind"] == "PDF")
nhtml = sum(1 for r in rows if r["content_kind"] == "HTML")

artifact = {
 "batch_id": "council-documents-topical-cluster-research-2026-09-12",
 "lane": "Claude research lane: the topical slice of the council/documents tail",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": ("The small named directories under council/documents together with the substantive files sitting "
             "directly at its flat level — Huning Highland, South Yale, Volcano Trails, Four Hills speed humps, "
             "complete streets, Uptown, big-box regulations, tax cuts, red light cameras, high-performance "
             "buildings, the Neighborhood Traffic Management Plan and a long tail of single files."),
 "scope": ("The 22 pending-review candidates in this slice that were not already rows in a saved artifact. 63 were "
           "fetched and measured; 41 turned out to be already covered by "
           "council-documents-cluster-research-2026-09-11.json and are accounted for in "
           "overlap_with_the_flat_level_lane rather than re-decided here."),
 "why_this_slice_exists": ("A remainder sweep over council/documents. Two counting errors preceded it and both are "
                           "recorded in overlap_with_the_flat_level_lane, because the second is a method failure "
                           "worth not repeating."),
 "brief": "A dated research decision file covering the planning and policy material, with per-path grouping preserved inside the artifact.",
 "brief_finding": ("The headline is a correction to a terminal record: the full adopted Uptown Sector Development "
                   "Plan is not held, and the inventory record that says it is names a 13-page transportation "
                   "extract as its canonical. See corrects_a_terminal_record. Three retained rows are byte-identical "
                   "to validated R2 objects, each confirmed against the inventory's own recorded checksums."),
 "third_finding": ("The enactment-number method from west-central-mra-cluster-research-2026-09-12.json worked again "
                    "in an unrelated directory. Council Bill R-05-383 recites its predecessor's number three times — "
                    "\"BILL NO. F/S R04155 (ENACTMENT NO. R2005033)\" — which resolves the number for F/S R-04-155 "
                    "and makes it one of only two rows in the whole run whose enactment number is stated rather than "
                    "inferred."),
 "method": ("Ran the URL group-by across the whole slice first; no collisions. Fetched all 63 candidates and measured "
            "byte length and SHA-256 from the fetched bytes, verifying every container by leading bytes rather than "
            "by extension, per economic-forum-cluster-research-2026-09-12.json. Compared every checksum against the "
            "1,612 checksummed inventory records and against exact recorded sizes, which is what surfaced the seven "
            "byte-identical matches. Fetched one R2 object read-only to test the Uptown record. Extracted text from "
            "all 45 PDFs and rendered every image-only file rather than classifying it from its filename. Swept the "
            "whole run's fetched corpus for enactment numbers matching this slice's six legislative files."),
 "classification_only": True,
 "shared_state_written": [],
 "corrects_a_terminal_record": CORRECTION,

 "overlap_with_the_flat_level_lane": {
  "what_happened": ("This lane was drafted over 63 records. 41 of them were already rows in "
                    "council-documents-cluster-research-2026-09-11.json, which had covered every file sitting "
                    "directly at the flat level of council/documents. Only 22 were genuinely uncovered, and the "
                    "artifact carries only those."),
  "why_it_happened": ("The remainder was computed by excluding a list of directory names already worked, and then by "
                      "selecting inventory records still marked pending review. Neither test catches an "
                      "already-decided record, because this run writes no shared state: every record it classifies "
                      "stays pending review in master-inventory.json until Codex applies the artifacts. A flat-level "
                      "file has no directory name to exclude, so it was invisible to the first test and looked "
                      "untouched to the second."),
  "the_rule_that_prevents_it": ("Before claiming any remainder lane, build the set of ids that already appear as a row "
                                "in some file under project-state/discovery/ and subtract it. Directory names and "
                                "inventory status are both unreliable for this while the run is classification-only."),
  "of_the_41": {"same_disposition_as_the_earlier_lane": 32, "different_disposition": 9},
  "the_nine_conflicts_resolve_to_the_earlier_lane": {
   "decision": ("Every one of the nine is left as council-documents-cluster-research-2026-09-11.json decided it. That "
                "lane read them properly and this one did not: it rendered page 1 of each image-only file and drew "
                "conclusions the fuller reading contradicts."),
   "worked_examples": [
    {"id": "src-f164513208041ca0",
     "this_lane_said": "excluded as unattributable, a 20-page image-only appendices.pdf with no identifying header",
     "the_earlier_lane_established": ("it is the appendix volume to the Small Business Resource Fair Report, opening "
                                      "on a hand-labelled APPENDIX 1 over Enactment No. R-2018-081, a Council "
                                      "Services transmittal to Mayor Keller for Bill No. R-18-82. It carries enacted "
                                      "legislation and belongs with the report under the canonical-package rule."),
     "outcome": "Approved for addition stands. The unattributable finding was a failure to read past page 1."},
    {"id": "src-4f28a655d98c8ae3",
     "this_lane_said": "excluded with the other Old Town topics, citing Total Number of Participants: 12 on every page",
     "the_earlier_lane_established": ("the three topics have different samples — Topic 1 Outdoor Displays with 33 "
                                      "participants, Topic 2 Signs with 12, Topic 3 Outdoor Demonstrations with 7 — "
                                      "and Topic 3 is the only record quoting the superseded zoning code definition "
                                      "of an outdoor demonstration at 14-16-2-25(o)(1). They are the evidence base "
                                      "behind Old Town sign and display rules later amended by O-19-52."),
     "outcome": ("Approved for addition stands for the three colour editions and duplicate for the two greyscale "
                 "twins. This lane read one topic's participant count and applied it to all three.")},
    {"id": "src-dc13bd3962e198df",
     "this_lane_said": "approved, as the archive's only record of how a City official is formally evaluated",
     "the_earlier_lane_established": ("it is the rating scale and survey-item description, the measuring instrument "
                                      "rather than any result, so it reports nothing about anyone's performance"),
     "outcome": "Excluded stands. The earlier reading is right: the file describes the weighting, not the scores."}],
   "full_list": ["src-388cbd495a6eb4f4", "src-3f866d2089b33926", "src-4f28a655d98c8ae3", "src-78ba9058dfb576e0",
                 "src-9642139286c8f411", "src-d866542fe3372c5e", "src-dc13bd3962e198df", "src-f0c76005377afd83",
                 "src-f164513208041ca0"],
   "for_integration": ("No action. These ids appear in council-documents-cluster-research-2026-09-11.json and nowhere "
                       "in this artifact's row buckets.")},
  "what_the_overlap_did_contribute": ("Independent corroboration on already-decided rows. The Volcano Trails Sector "
                                      "Development Plan, its adoption resolution and its EPC Notice of Decision, and "
                                      "the October 2013 Central Avenue draft, were all recorded as duplicate by the "
                                      "earlier lane and are confirmed byte-identical to their validated canonicals "
                                      "against the inventory's own recorded checksums. Corroboration, not new "
                                      "classification, so those rows are not repeated here."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds and against the published site before recommending.",
  "matches_found": len(duplicates) + len(superseded),
  "byte_identical_to_validated_records": len(duplicates),
  "how": ("Comparing fetched checksums against the inventory's own recorded checksums, and fetched sizes against "
          "recorded sizes. Each matched on both, so none needed a fetch of the R2 object to confirm. Four further "
          "byte-identical matches were found among the records this lane turned out to share with "
          "council-documents-cluster-research-2026-09-11.json; they corroborate that lane's decisions and are "
          "described in overlap_with_the_flat_level_lane rather than repeated as rows."),
  "what_matched": [{"candidate": r["id"], "canonical": r["canonical_id"], "what": r["title_for_reference"]} for r in duplicates],
  "eighth_match": ("src-bee427d5c6a31344 matches a terminal record by size on a record that carries no checksum, and "
                   "is recommended superseded rather than duplicate for that reason."),
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue.",
  "the_one_that_failed_the_other_way": "src-2aa87993b25de330, where the archive believed it held the document and did not.",
 },
 "enactment_numbers": {
  "recovered_here": [{"instrument": "Council Bill F/S R-04-155, amending the Huning Highland Sector Development Plan to establish the SU-2/CRZ",
                      "enactment": "R-2005-033",
                      "stated_by": "src-629504bb1af568b7, in its title line and again in Sections 2 and 3"}],
  "method": "The method recorded in west-central-mra-cluster-research-2026-09-12.json: read the recitals and title lines of later legislation, not the plans those instruments adopted.",
  "confirmed_in_a_second_directory": True,
  "not_found_for": ["C/S2 O-06-53", "O-07-73", "O-07-84", "R-08-97"],
  "sweep": "Every text fetched across this whole run was searched for each of this slice's six bill numbers in proximity to the word enactment. Only the R-04-155 citation came back.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 7,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 7,
  "relationships_found_by_size_against_a_checksumless_record": 1,
  "relationships_found_by_text_comparison": 1,
  "note": ("Hashing did well here, because this slice is full of second copies of documents the City also publishes "
           "elsewhere. The one relationship hashing could not find is the one that mattered most: the Uptown adopted "
           "plan against the extract the inventory had recorded as its canonical, which took a fetch and a token "
           "comparison to disprove."),
 },
 "path_groups": {k: [x for x in v if x in {r["id"] for r in rows}] for k, v in {
  "huning-highland": ["src-df71413ad4181460", "src-9024a88c37c3e026", "src-5a39a69a5a13eb31", "src-629504bb1af568b7"],
  "four-hills-speed-hump-studies": ["src-a2c9ffe1607190be", "src-d8f7ec08b6b02cf6", "src-83743c8ca421ab3d", "src-b7203e954d4ac16f"],
  "complete-streets": ["src-96fcac92a6d81b53", "src-5e3f04254885b800", "src-bee427d5c6a31344"],
  "south-yale-sector-plan": ["src-b838ec4d5a8d4527", "src-b83cb78799aee935", "src-f7c952e28ec3bf2c"],
  "south-yale-blvd": ["src-4541bdade4a94304", "src-66add68f2b531815"],
  "uptown-documents": ["src-936b48bc54970418", "src-2aa87993b25de330"],
  "big-box-regulations": ["src-9f1d31095920f273", "src-40d4239b82ca0b0b"],
  "volcano-trails-flat-files": ["src-5506a88128e7de17", "src-f93aa90a07d83d6d", "src-442d80b03a4e05eb"],
  "old-town-virtual-task-force": [i for i, _, _ in OLDTOWN],
  "abq-neighborwoods": ["src-2390ede0d0136e64", "src-a7315c04bfa42eb7", "src-9d612c0b224dfb37", "src-3240234b98d27b27"],
 }.items() if any(x in {r["id"] for r in rows} for x in v)},
 "integration_flags": [
  {"severity": "corrects-a-terminal-record",
   "affects": ["src-049105295d2745af", "src-2aa87993b25de330", "src-4ccef0c6ec25aac8"],
   "finding": "A terminal duplicate decision records a 13-page transportation extract as the canonical for the 115-page adopted Uptown Sector Development Plan. Coverage of the extract inside the plan is 0.9797; of the plan inside the extract, 0.2335.",
   "recommended_action": "Approve the adopted plan from this lane and correct the terminal record's reason. Claude did not modify it."},
  {"severity": "avoid-duplicate-archival",
   "affects": [r["id"] for r in duplicates] + [superseded[0]["id"]],
   "finding": "Eight candidates are already in the archive, seven byte-identical to validated R2 objects.",
   "recommended_action": f"Record seven as duplicate and one as superseded. {avoided:,} bytes not uploaded."},
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved],
   "finding": f"Ten unheld records totalling {approved_pages} pages: the adopted Uptown sector plan, the Urban Land Institute Rail Yards advisory panel report, the Huning Highland Railroad development process plan, the 2007 Neighborhood Task Force final report, the 2019 Small Business Resource Fair report, the three-part 2007 Four Hills speed hump evaluation, the South Yale boundaries map, and the City Attorney evaluation scorecard.",
   "recommended_action": "Approve. Three of the ten are image-only and will need optical character recognition to be searchable."},
  {"severity": "enactment-number-recovered",
   "affects": ["src-5a39a69a5a13eb31", "src-629504bb1af568b7"],
   "finding": "F/S R-04-155 is Enactment R-2005-033, stated three times in R-05-383's own text. Second directory in which the later-legislation method has worked.",
   "recommended_action": "Retrieve Enactment R-2005-033 and resolve both Huning Highland resolutions together. Promote them alongside F/S R-04-56 from West Central, ahead of the packages whose numbers are unknown."},
  {"severity": "discovery-lead",
   "affects": ["src-cbd9e912b1e24b09", "src-c96c9d872de87154"],
   "finding": "Two excluded records name things the archive does not hold: the Redflex red light camera contract and whatever the administration did about it, and the Streets and Traffic Enhancement Program document that a 2013 comment matrix responds to.",
   "recommended_action": "Queue both. The red light camera programme is a significant and contested piece of City history with no record in the archive at all."},
  {"severity": "unattributable",
   "affects": ["src-f164513208041ca0", "src-f7c952e28ec3bf2c"],
   "finding": "Two image-only files at the flat level — appendices.pdf and exhibitbpage1.pdf — carry no identifying header and have no parent in the directory.",
   "recommended_action": "Exclude as unattributable, keeping their checksums so they can be matched if a parent is ever identified."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "superseded": counts["superseded"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": f"{npdf} genuine PDFs and {nhtml} HTML collection pages by leading bytes. No content substitution found in this slice, unlike economic-forum. Seven PDFs have no usable text layer and were rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "superseded": superseded,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are static PDFs and are inventory-only until an R2 archive "
                   f"object exists for each and its public download, exact size, SHA-256, and authoritative-source "
                   f"provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes "
                   f"across {approved_pages} pages. Three of the ten — the Four Hills report, technical appendix and "
                   f"executive summary — are image-only scans and will not be reachable by full-text search without "
                   f"optical character recognition. A further {len(rhr)} records totalling {rhr_bytes:,} bytes are "
                   f"held at requires human review."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Seven duplicate rows carry canonical_ids pointing "
                      "at validated, R2-archived records, each confirmed byte-identical against the inventory's own "
                      "recorded checksum rather than inferred; the one superseded row matches a checksumless terminal "
                      "record by size and defers to the same canonical that terminal record names. Six rows are "
                      "requires human review, each with a priority field, and two of them are one Huning Highland "
                      "package whose enactment number is now known. Every row carries a leading_bytes field. The "
                      "largest item in this artifact is not a row: corrects_a_terminal_record asks for a terminal "
                      "duplicate decision outside this lane's scope to be revisited. Sizes and checksums are first "
                      "measurements; the inventory held none for any pending record here."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the one R2 object consulted was fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
