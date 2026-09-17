"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\council-documents-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
HASHES = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
          r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\council\hashes.tsv')
BASE = 'https://www.cabq.gov/council/documents/'

PROJECTS = 'content/development-land-use/projects.md'
DEVPROC = 'content/development-land-use/development-process.md'
ZONING = 'content/development-land-use/zoning-ido.md'
SURVEYS = 'content/city-data/city-progress-surveys.md'
OPSDATA = 'content/transportation/operations-data.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

MEASURED = {}
if os.path.exists(HASHES):
    for line in open(HASHES, encoding='utf-8'):
        i, h, m, s = line.rstrip('\n').split('\t')
        MEASURED[i] = {"checksum_sha256": h, "size_bytes": int(s)}


def url_of(i):
    return IDX[i].get('direct_file_url') or IDX[i].get('source_url')


def base(i, status):
    r = {"id": i, "authoritative_url": url_of(i), "recommended_status": status,
         "link_check": "HTTP 200 verified 2026-09-11"}
    if i in MEASURED:
        r.update(MEASURED[i])
        r["link_check"] = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and "
                           "checksum_sha256 measured from the fetched bytes, because the "
                           "inventory record carried neither")
    return r


def A(i, title, desc, page, pages=None, date=None, date_basis=None, why=None,
      evidence=None, cross=None):
    r = base(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "proposed_canonical_page": page, "cross_listings": cross or []})
    if pages:
        r["pages"] = pages
    if date:
        r["date"] = date
    if date_basis:
        r["date_basis"] = date_basis
    if why:
        r["why_retained"] = why
    if evidence:
        r["evidence"] = evidence
    return r


approved = [
 A("src-9f5ac56df8c6cbb8",
   "Albuquerque Rail Yards: Redeveloping the City's Historic Rail Yards, a Urban Land Institute Advisory Services Panel Report (February 2008)",
   "The Urban Land Institute panel report on the Albuquerque Rail Yards sets out market findings, planning and design recommendations, development strategy, and implementation advice for redeveloping the historic Santa Fe Railway shops site south of Downtown.",
   PROJECTS, pages=46, date="2008-02",
   date_basis="The title page reads \"Redeveloping the City's Historic Rail Yards, February 24-29, 2008\".",
   why="The earliest substantive planning study for the Rail Yards and the only copy of it in the inventory. The site already publishes three editions of the Rail Yards Master Plan and two Blacksmith Shop studies under \"Rail Yards Planning and Environmental Records\"; this 2008 panel report is the precursor to all of them and completes that record.",
   evidence="46 pages, produced by ULI, 1025 Thomas Jefferson Street NW, Washington. Its SHA-256 does not match any of the 1,612 checksummed inventory records, so it is not a copy of anything already held."),

 A("src-a3afa3078e7351a7",
   "Neighborhood Task Force Final Report to the City Council (September 2007)",
   "The Council-appointed task force reports on five assigned topics covering the function and role of the Office of Neighborhood Coordination, neighborhood association recognition, notification requirements, and the relationship between neighborhood organisations and the City development review process.",
   DEVPROC, pages=13, date="2007-09",
   date_basis="The report is headed \"Respectfully Submitted To City Council September XX, 2007\"; the day was left as a placeholder in the published file.",
   why="A Council task force report with findings and recommendations, not a meeting record. It documents how Albuquerque's neighborhood notification and recognition rules came to be, which is background the development-process page carries for no other era.",
   evidence="13 pages. Its executive summary cites the Don Harris District 9 Council memorandum of April 25, 2007 that created the task force and lists the five topics it was asked to address."),

 A("src-42032f0eef57807c",
   "Small Business Resource Fair Report: Supporting Albuquerque's Growing Small Business Community (April 2019)",
   "The City Council staff report reviews the Small Business Resource Fair, setting out the local small business context, what the fair delivered, participant and partner feedback, and recommendations for future City support of small businesses.",
   SURVEYS, pages=15, date="2019-04",
   date_basis="The cover reads \"Report Created by City Council Staff April 2019\".",
   why="A Council staff evaluation report with findings and recommendations. It is the substantive half of a two-file package whose other half is the appendices retained below.",
   evidence="15 pages with a table of contents running executive summary, context, and recommendations.",
   cross=[{"page": DEVPROC, "reason": "Its recommendations touch City permitting and business registration steps described there."}]),

 A("src-f164513208041ca0",
   "Appendices to the Small Business Resource Fair Report, Including Enacted Resolution R-2018-081",
   "The appendix volume to the Council small business report opens with enacted Resolution R-2018-081, which directs the Economic Development Department to convene a micro-enterprise development fair with local and state partners, and carries the supporting materials.",
   SURVEYS, pages=20, date="2019-04",
   date_basis="Published as the appendix volume to the April 2019 report; its Appendix 1 transmittal is dated November 15, 2018.",
   why="Not a separate document but the second half of the retained report, and it carries the enacting legislation the report implements. Under the repository canonical-package rule the two belong together.",
   evidence="Image-only PDF with no text layer; page 1 was rendered and read. It is hand-labelled \"APPENDIX 1\" over Enactment No. R-2018-081, a Council Services transmittal to Mayor Timothy M. Keller for Bill No. R-18-82, \"Directing The Economic Development Department To Collaborate With The City Council Office And Other Local And State Government Agencies To Convene A Micro-Enterprise Development Fair (Pena)\", passed at the Special Council meeting of November 5, 2018 by a vote of 9 for and 0 against.",
   cross=[{"page": DEVPROC, "reason": "Same reason as the report it belongs to."}]),

 A("src-baf2db7aea5be0d2",
   "African American Advisory Board Minutes, July 7, 2026",
   "The approved minutes of the City African American Advisory Board record attendance, the business transacted, member reports, and actions taken at the board's July 7, 2026 meeting in the City Council Committee Room.",
   SURVEYS, pages=6, date="2026-07-07",
   date_basis="The minutes are headed \"Tuesday, July 7th, 2026, 11:00 A.M.\" and the filename records a final version of July 16, 2026.",
   why="Approved minutes of a standing City advisory board. Minutes are retained wherever the repository has triaged a board, and the sibling agenda for this same meeting is excluded because these minutes exist.",
   evidence="Six pages opening with the voting members present. See integration_flags: ABQInfo has no existing page for advisory-board minutes, so placement is an open architecture question."),

 A("src-c8618de9cd7384e7",
   "African American Advisory Board Minutes, June 2, 2026",
   "The approved minutes of the City African American Advisory Board record attendance, business transacted, and actions taken at the board's June 2, 2026 meeting, held at the Black Chambers of Commerce New Mexico on Fourth Street SW.",
   SURVEYS, pages=5, date="2026-06-02",
   date_basis="The minutes are headed \"Tuesday, June 2nd, 11:00 A.M.\".",
   why="Approved minutes of a standing City advisory board. Decisive precedent: the agenda for this same meeting, src-0a6bdb5c898342da, is already terminal-excluded in the inventory, which is exactly the treatment the repository missing-minutes policy prescribes when approved minutes exist.",
   evidence="Five pages opening with the voting members present."),

 A("src-f6f982e95a648dd7",
   "African American Advisory Board Minutes, May 5, 2026",
   "The approved minutes of the City African American Advisory Board record attendance, business transacted, and actions taken at the board's May 5, 2026 meeting in the Department of Municipal Development conference room at One Civic Plaza.",
   SURVEYS, pages=4, date="2026-05-05",
   date_basis="The minutes are headed \"May 5, 2026 at 11 am\".",
   why="Approved minutes of a standing City advisory board; the agenda for the same meeting is recommended excluded below on the same ground the June agenda was already excluded.",
   evidence="Four pages listing members present by organisation, including the Black Chambers of Commerce, the New Mexico Black Leadership Council, the African American Museum and Cultural Center, and UNM African American Student Services."),

 A("src-f0c76005377afd83",
   "Albuquerque City Council Services Organizational Chart, April 6, 2026",
   "The chart shows how City Council Services is organised, naming the Director, the deputy directors for policy and operations, general counsel, the Clerk of the Council, and the program evaluation and district associate director roles beneath them.",
   SURVEYS, pages=1, date="2026-04-06",
   date_basis="The filename records 4-6-26 and the chart is current as published.",
   why="A current, dated statement of how the legislative branch staff is structured and who holds each post. It is a reference record rather than a form, and the inventory holds no other organisational chart for Council Services.",
   evidence="One page naming the Director of Council Services and the deputy director, general counsel, operations, and clerk positions."),

 A("src-9642139286c8f411",
   "Stop Sign Reconfiguration Proposal for Raynolds and Barelas, December 2008",
   "The City Municipal Development traffic engineering proposal maps the one-way street grid in the Raynolds and Barelas neighborhoods, marking which existing stop signs would remain, which would be removed, and where new stop signs would be installed.",
   OPSDATA, pages=1, date="2008-12",
   date_basis="The sheet credits \"City of Albuquerque - Department of Municipal Development, Traffic Engineering Division, December 2008\".",
   why="A dated, named traffic-engineering project record for two specific Albuquerque neighborhoods, with a legend that makes it readable on its own. It is the class of neighborhood traffic record the transportation operations page already carries.",
   evidence="One page. The legend distinguishes one-way westbound and eastbound segments, existing stops to remain, existing stops to be removed, and new stops to be installed."),

 A("src-4f28a655d98c8ae3",
   "Old Town Virtual Task Force Summary of Ranking Results, Topic 1: Outdoor Displays",
   "The City task force summary charts how thirty-three participants ranked proposed options for regulating outdoor merchandise displays in Old Town, giving the vote distribution behind the recommendations that fed the Old Town historic protection overlay standards.",
   ZONING, pages=5,
   why="Recorded public-input results with participant counts and per-option vote distributions, which is data rather than a meeting handout. It is the evidence base behind the Old Town sign and display rules that Council later amended by O-19-52, itself in this directory.",
   evidence="Five pages, all headed \"Topic 1: Outdoor Displays, Total Number of Participants: 33\". No black and white counterpart is published for this topic.",
   cross=[{"page": PROJECTS, "reason": "Old Town is a named City redevelopment and planning area."}]),

 A("src-3f866d2089b33926",
   "Old Town Virtual Task Force Summary of Ranking Results, Topic 2: Signs",
   "The City task force summary charts how twelve participants ranked proposed sign rules for Old Town, covering off-premises signs among other categories, and records the vote distribution behind each option the task force considered.",
   ZONING, pages=15,
   why="Same ground as Topic 1. The participant count of twelve is small and should be stated in any published description so the weight of the result is not overstated.",
   evidence="Fifteen pages, all headed \"Topic 2: Signs, Total Number of Participants: 12\", including an Off-Premises Signs block at item 11a. The black and white edition src-388cbd495a6eb4f4 is its greyscale twin.",
   cross=[{"page": PROJECTS, "reason": "Old Town is a named City redevelopment and planning area."}]),

 A("src-d866542fe3372c5e",
   "Old Town Virtual Task Force Summary of Ranking Results, Topic 3: Outdoor Demonstrations",
   "The City task force summary charts how seven participants ranked options for regulating outdoor craft demonstrations in Old Town, testing whether the former zoning code definition at Section 14-16-2-25(o)(1) adequately defined an outdoor demonstration.",
   ZONING, pages=4,
   why="Same ground as the other two topics, and it is the only record in the directory that quotes the superseded zoning code definition of an outdoor demonstration. The seven-participant count must be stated in any description.",
   evidence="Four pages headed \"Topic 3: Outdoor Demonstrations, Total Number of Participants: 7\", quoting the old zoning code language at 14-16-2-25 (o) 1. The black and white edition src-78ba9058dfb576e0 is its greyscale twin.",
   cross=[{"page": PROJECTS, "reason": "Old Town is a named City redevelopment and planning area."}]),
]


def D(i, canonical_id, basis, hash_found, note=None):
    r = base(i, "duplicate")
    r.update({"canonical_id": canonical_id,
              "canonical_url": (IDX[canonical_id].get('direct_file_url')
                                or IDX[canonical_id].get('source_url')),
              "canonical_status": IDX[canonical_id]['status'],
              "basis": basis, "hash_found_it": hash_found})
    if note:
        r["note"] = note
    return r


duplicates = [
 D("src-442d80b03a4e05eb", "src-e8d18ebb99858984",
   "Byte-identical to an already-validated record: same 96,283 bytes and same SHA-256. The City serves the Volcano Trails Environmental Planning Commission Official Notification of Decision of March 3, 2011 from two paths.",
   True),
 D("src-5506a88128e7de17", "src-81c75a7d7a217a68",
   "Byte-identical to the already-validated Volcano Trails Sector Development Plan of August 2011: same 8,903,701 bytes and same SHA-256.",
   True,
   note="At 8.9 MB this is the second largest file in the cluster; recognising it as an exact duplicate avoids a pointless re-archive."),
 D("src-a0095a2e8b524b85", "src-357f0a012444d081",
   "Byte-identical to the already-validated October 2013 Draft Central Avenue Complete Street Plan and Design Toolkit: same 11,759,630 bytes and same SHA-256. A second duplicate of that record, src-4c9e6a583778b007, is already terminal.",
   True,
   note="The inventory title for this pending record, \"Central Avenue Complete Streets Design Toolkit (1st Street to Girard)\", differs from the validated record's title for the same bytes. Use the validated record's title."),
 D("src-f93aa90a07d83d6d", "src-8b120e71c3650349",
   "Byte-identical to the already-validated Volcano Trails Sector Development Plan Adoption Resolution: same 90,762 bytes and same SHA-256. The file is Council Bill C/S R-11-211, Nineteenth Council.",
   True),
 D("src-388cbd495a6eb4f4", "src-3f866d2089b33926",
   "The black and white edition of the Old Town task force Topic 2 ranking results. Same fifteen pages, same twelve participants, same questions; only the chart rendering differs. Normalized-text similarity 0.9271 with token coverage 0.9896 of the colour edition inside it.",
   False,
   note="Published deliberately as an accessibility alternative rather than as a separate result set. Retain the colour edition and record this as its greyscale twin."),
 D("src-78ba9058dfb576e0", "src-d866542fe3372c5e",
   "The black and white edition of the Old Town task force Topic 3 ranking results. Normalized-text similarity 0.9677 with token coverage 0.9620 in both directions.",
   False),
]


def R(i, draft_title, question, why, detail=None, pages=None, date=None):
    r = base(i, "requires human review")
    r.update({"draft_title": draft_title, "question_for_human": question,
              "why_not_decided_here": why})
    if detail:
        r["detail"] = detail
    if pages:
        r["pages"] = pages
    if date:
        r["date"] = date
    return r


PID_Q = ("Does the recorded official-source review below meet the repository's \"exhaustive\" bar "
         "for the missing-minutes agenda policy, and was any of these meetings cancelled or held "
         "without a quorum?")
PID_WHY = (
 "The repository missing-minutes policy permits preserving a verified original official agenda only "
 "\"after a recorded exhaustive official-source review finds no approved minutes for a meeting\", and "
 "forbids archiving an agenda for an officially cancelled or no-quorum meeting. This lane searched "
 "all 872 council/documents records in the inventory, ran the cabq.gov site search for Trails PID "
 "minutes, and fetched and listed the council/documents/meeting-agenda-documents directory, which "
 "holds agendas for the Trails, Mesa del Sol, Saltillo, Winrock and Hunt district boards and no "
 "minutes for any of them. No Trails PID minutes exist anywhere on the City site that this lane could "
 "reach. What this review did not cover is Legistar and the district administrator's own records, and "
 "the agendas themselves prove minutes exist: the May 29, 2013 agenda lists \"Review of minutes of "
 "August 21, 2012 and February 15, 2013\" as a business item. Nothing in an agenda reveals whether the "
 "meeting it announces actually took place, so the cancellation and quorum test cannot be applied from "
 "these files at all. Deciding six agendas on an incomplete review would set the precedent for every "
 "public improvement district agenda in the tree.")

rhr = [
 R("src-bc1dbb930feefaaf", "The Trails Public Improvement District Board of Directors Special Meeting Agenda, May 29, 2013",
   PID_Q, PID_WHY, pages=1, date="2013-05-29"),
 R("src-b657a1bd0d19ffe8", "The Trails Public Improvement District Board of Directors Special Meeting Agenda, August 1, 2013",
   PID_Q, PID_WHY, pages=1, date="2013-08-01"),
 R("src-a6bd9f4f6ae1cb40", "The Trails Public Improvement District Board of Directors Regular Meeting Agenda, May 16, 2025",
   PID_Q, PID_WHY, pages=2, date="2025-05-16"),
 R("src-7e3d417f146c307b", "The Trails Public Improvement District Board of Directors Regular Meeting Agenda, July 25, 2025",
   PID_Q, PID_WHY, pages=2, date="2025-07-25"),
 R("src-c393d59e029b52e9", "The Trails Public Improvement District Board of Directors Regular Meeting Agenda, May 26, 2026",
   PID_Q, PID_WHY, pages=2, date="2026-05-26"),
 R("src-15bd43bb6a15984d", "The Trails Public Improvement District Board of Directors Regular Meeting Agenda, July 24, 2026",
   PID_Q, PID_WHY, pages=2, date="2026-07-24"),
 R("src-9dbe491dce873f71", "Local Government Coordinating Commission Agenda, April 16, 2026",
   "Same missing-minutes question as the Trails PID agendas, for a different body.",
   "The Local Government Coordinating Commission brings together City councilors, County commissioners and APS board members. This is the only LGCC document of any kind in the inventory: no minutes, and no other agenda to establish a series. The same policy bar and the same unresolved cancellation and quorum test apply.",
   pages=3, date="2026-04-16"),

 R("src-be410a77ceab45b2",
   "Council Bill C/S O-24-1: Administrative Demolition of Unsafe Commercial Buildings, Unsafe Accessory Structures, or Dwellings Unfit for Human Habitation (Finance and Government Operations Committee Substitute, January 29, 2024)",
   "Locate the enacted ordinance for each of these bills before any archival or visible use, and decide whether ABQInfo carries pre-enactment bill versions at all.",
   "Every one of these files carries \"ENACTMENT NO. ________________\" blank on its face: they are the version a committee or the Council considered, not the law. The checkpoint already holds an open blocker on exactly this problem for two other records, \"isolated legislative amendment/substitute files; resolve authoritative enacted packages before archival or visible use\", and a second blocker stating that src-0b1642254494f22e \"must not be archived or visibly used as enacted\". Applying that standing instruction is the only defensible answer here. Each of these is a substantial, self-contained bill text, so unlike the one-page amendment sheets they are not excluded as fragments; they are held until their enacted counterparts are located.",
   pages=9, date="2024-01-29"),
 R("src-cb868b1506e51793",
   "Council Bill F/S O-24-4: Authorizing the Issuance and Sale of City of Albuquerque General Obligation Bonds in Two Series Not to Exceed $111,850,000 (Floor Substitute, April 3, 2024)",
   "Same question: locate the enacted ordinance.",
   "Thirty-six pages of bond authorisation with the enactment number blank. The inventory already holds an extensive validated general obligation bond record set, so the enacted counterpart is likely findable and this file should not stand in for it.",
   pages=36, date="2024-04-03"),
 R("src-844d4e3d0227e107",
   "Council Bill C/S O-24-6: Amending the Complete Streets Ordinance to Define Arid Adapted Landscaping (Land Use, Planning and Zoning Committee Substitute, March 13, 2024)",
   "Same question: locate the enacted ordinance.",
   "Enactment number blank. The site already carries Complete Streets material, so an unenacted substitute must not be placed beside it without the enacted text.",
   pages=5, date="2024-03-13"),
 R("src-bc91d8e4f296d80b",
   "Council Bill C/S O-23-96: Adopting a New Part in Chapter 9, Article 5 of the Revised Ordinances to Create an Environmental Justice Air Quality Permit (Finance and Government Operations Committee Substitute, February 12, 2024)",
   "Same question: locate the enacted ordinance.",
   "Enactment number blank. Seventeen pages creating a new permit class; whether it became law is precisely the fact a reader would need and this file does not answer.",
   pages=17, date="2024-02-12"),
 R("src-26cc63bf3b00147d",
   "Council Bill O-19-52: Amending the Integrated Development Ordinance Section 14-16-3-5(J)(3) Old Town HPO 5, Other Development Standards, to Allow Increased Types and Amount of Signage in Old Town",
   "Same question: locate the enacted ordinance.",
   "Enactment number blank. This is the legislative sequel to the Old Town task force ranking results recommended for addition in this same batch, which makes pairing it with its enacted text worth doing rather than skipping.",
   pages=7),
 R("src-3ce96f0fc670867e",
   "Council Bill F/S R-24-17: Authorizing the Giving of Notices for Bids for the Sale of City of Albuquerque General Obligation Bonds Consisting of $102,850,000 (Floor Substitute, April 3, 2024)",
   "Same question: locate the enacted resolution.",
   "Enactment number blank; the companion to F/S O-24-4 above and subject to the same treatment.",
   pages=20, date="2024-04-03"),
 R("src-3cd044acfb1a299f",
   "Council Bill FS R-24-2: Establishing Federal Programming and Policy Priorities for the City of Albuquerque for Federal Fiscal Years 2024/2025 (Floor Substitute, January 22, 2024)",
   "Same question: locate the enacted resolution.",
   "Enactment number blank. A floor amendment to this same bill, src-e0342708393dff1c, is in this directory and records that it failed 1-8, which shows the bill was actively contested on the floor and that this substitute may not be the final text.",
   pages=7, date="2024-01-22"),
]


def X(i, reason, category, extra=None):
    r = base(i, "excluded")
    r.update({"exclusion_reason": reason, "category": category})
    if extra:
        r.update(extra)
    return r


AMEND = ("A one-page City Council floor or committee amendment sheet. It cannot be read on its own: "
         "its content is instructions of the form \"on page 2, line 12, strike 'serious' and insert "
         "'violent'\" against a bill text it does not contain. Whatever it changed is already inside "
         "the enacted ordinance or resolution, which is the record a reader needs. Excluded as a "
         "non-self-contained legislative fragment. See integration_flags: this is a category of at "
         "least 57 files across this directory and its amendments-for-posting-on-council-page "
         "subdirectory, and the exclusion should be revisited as a category if ABQInfo ever carries "
         "Council legislative history as a feature.")

amendments = [
 ("src-73043c0b97d9b011", "Floor Amendment 1 to M-24-1, January 8, 2024, passed 9-0."),
 ("src-c4f048e06b594f03", "Floor Amendment 1 to M-24-2, February 21, 2024, passed 8-1."),
 ("src-fb13b70ee7c4ab0a", "Floor Amendment 1 to C/S O-24-1, March 4, 2024, passed 9-0."),
 ("src-5b892782bc45aa76", "Floor Amendment 1 to O-24-2, March 4, 2024, passed 9-0."),
 ("src-7700b19e3d6bcf84", "Land Use, Planning and Zoning Committee Amendment 1 to O-24-3, March 13, 2024, passed 5-0."),
 ("src-a222307b5ab1a98e", "Floor Amendments 1 and 2 to O-23-87, November 8, 2023, passed 9-0."),
 ("src-66174144ce60e7a3", "Combined floor amendments to O-23-88, November 8, 2023; Amendment 1 was withdrawn by its sponsor."),
 ("src-c94c856a9c4ca66a", "Floor Amendment 1 to P-24-2, May 20, 2024, passed 9-0."),
 ("src-d31eb4e88918a27f", "Floor Amendments 1 and 2 to P-24-3, May 20, 2024, passed 9-0."),
 ("src-9bbb867f1b8e1338", "Floor Amendment 1 to R-23-176, November 8, 2023, passed 9-0."),
 ("src-8379ac4691808eb2", "Floor Amendment 1 to R-23-183, November 20, 2023, passed 9-0."),
 ("src-f5c714195ef5da69", "Combined floor substitute and amendments to R-23-184, December 4, 2023, passed 8-0."),
 ("src-ef40025fc4a31d03", "Amendment packet 1 to 10 for R-23-193, December 4, 2023, with a pass, fail and withdrawn tracking table."),
 ("src-e0342708393dff1c", "Combined floor substitute and Amendments 1 and 2 to R-24-2, January 22, 2024; Amendment 1 failed 1-8."),
 ("src-4e3ee8ab55ea29a0", "Land Use, Planning and Zoning Committee Amendment 1 to R-24-22, March 2024, passed 5-0."),
 ("src-1a9b18d86e47137f", "Floor Amendment 1 to R-24-3, February 21, 2024, passed 9-0."),
 ("src-bc2bf6cdf0c45835", "Floor Amendment 1 to R-24-4, March 4, 2024, passed 9-0; it revises three appropriation figures."),
 ("src-fac05bc1c96112ec", "Floor Amendment 1 to R-24-47, June 3, 2024, passed 8-1."),
 ("src-f0aa9bf5629ada5a", "Floor Amendment 1 to R-24-48, May 20, 2024, passed 9-0."),
 ("src-3e345572c917c940", "Finance and Government Operations Committee Amendments 1 and 2 to R-24-5, January 29, 2024, passed 5-0."),
 ("src-a9b5c9080422b55d", "Floor Amendments 1 and 2 to R-24-50, June 3, 2024, passed 8-1."),
 ("src-8ee8b160a18fce76", "Combined floor amendments to R-24-8, March 4, 2024, passed 9-0, adjusting general obligation bond affordable housing lines."),
 ("src-28a0d2e5c2f2c838", "Finance and Government Operations Committee amendments to R-24-8, February 12, 2024, passed 5-0."),
]

excluded = [X(i, AMEND, "council legislative amendment sheet", {"identifies": d})
            for i, d in amendments]

excluded += [
 X("src-7be54d79de9efd93",
   "African American Advisory Board agenda for May 5, 2026. The approved minutes of that same meeting, src-f6f982e95a648dd7, are recommended for addition in this batch, and the repository missing-minutes policy preserves an agenda only where approved minutes cannot be located.",
   "advisory board agenda superseded by its own minutes",
   {"precedent": "src-0a6bdb5c898342da, the June 2, 2026 agenda for this same board, is already terminal-excluded on this exact ground."}),
 X("src-b3fbcf775c57fa6d",
   "African American Advisory Board agenda for July 7, 2026. The approved minutes of that same meeting, src-baf2db7aea5be0d2, are recommended for addition in this batch.",
   "advisory board agenda superseded by its own minutes",
   {"precedent": "src-0a6bdb5c898342da."}),
 X("src-dc13bd3962e198df",
   "\"Exhibit 2 - Balanced Scorecard\": the rating scale and survey-item description used in the City Attorney's 360-degree feedback assessment. It is the measuring instrument, not the result, so it reports nothing about anyone's performance and has no standalone interpretive value.",
   "evaluation instrument without results",
   {"note": "If the completed scorecard results are ever located they would be a different matter; this file is not them."}),
 X("src-3240234b98d27b27",
   "ABQ NeighborWoods program schedule: a week-by-week outline of what Tree New Mexico and a neighborhood do after joining the tree-planting program. Program-administration guidance published without dates, tied to a third-party delivery partner.",
   "program administration handout"),
 X("src-a7315c04bfa42eb7",
   "Property Owner Agreement to Participate in the ABQ NeighborWoods Tree Program, English. A blank agreement a resident signs. Transactional instrument template.",
   "program form",
   {"translation_pair": "src-9d612c0b224dfb37 is the Spanish edition of this same agreement; both are excluded, and a translation is recorded as a parallel edition rather than a duplicate."}),
 X("src-9d612c0b224dfb37",
   "Acuerdo del Propietario para participar en el programa de arboles de ABQ NeighborWoods: the Spanish edition of the same participation agreement. Same exclusion ground.",
   "program form",
   {"translation_pair": "src-a7315c04bfa42eb7.",
    "encoding_note": "The inventory title for this record is mojibake, \"EspaÃƒÆ'Ã‚Â±ol\", a double-encoded \"Espanol\" from the source page. Any title written for it must come from the document, not the inventory field."}),
 X("src-2390ede0d0136e64",
   "ABQ NeighborWoods program application: a fill-in application asking for coordinator contact details, neighborhood boundaries, and a narrative about existing trees.",
   "program form"),
 X("src-962345dea8ed8430",
   "Civilian Police Oversight Advisory Board application form, 2026 edition. A fill-in application for board membership. Routine even though it recites the Police Oversight Ordinance eligibility rules at Section 9-4-1-5.",
   "board application form",
   {"size_note": "At 11,404,905 bytes across 35 pages this is the third largest file in the cluster, and excluding it keeps a large object out of any future upload batch."}),
 X("src-616ec5b352fd39da",
   "Albuquerque Fire Rescue \"Vial of Life\" medical information form: a blank form a resident completes and keeps at home for emergency responders.",
   "resident form"),
 X("src-6db0397455652054",
   "Public meeting flyer for the Rainbow Boulevard Traffic Calming Study, announcing a single District 5 meeting. An event notice for a meeting long past; the study it announces would be the record worth holding, and it is not in this directory.",
   "event flyer",
   {"follow_up": "The Rainbow Boulevard traffic calming and pedestrian safety study itself, between Paseo del Norte and the southern property line of Volcano Vista High School, is not in the inventory. Worth a targeted search in a later lane."}),
]

# Collection landing pages: everything in the cluster with no document extension.
PAGE_REASON = (
 "A Plone collection landing page inside the Council document library, not a document. Its content is "
 "the list of links to the files it contains, plus site chrome. Excluding it does not touch any file it "
 "lists: those are separate inventory records, most of them in subdirectory clusters this artifact does "
 "not cover.")

landing_ids = []
for x in inv['candidates']:
    if x['status'] != 'pending review':
        continue
    u = x.get('direct_file_url') or x.get('source_url') or ''
    if not u.startswith(BASE):
        continue
    rest = u[len(BASE):]
    rest = rest[:-5] if rest.endswith('/view') else rest
    if '/' in rest:
        continue
    if rest.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
        continue
    landing_ids.append(x['id'])

for i in sorted(landing_ids):
    r = base(i, "excluded")
    r.update({"exclusion_reason": PAGE_REASON,
              "category": "collection landing page",
              "inventory_title": IDX[i].get('title')})
    excluded.append(r)

rows = approved + duplicates + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), "duplicate id"
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "council-documents-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents flat directory",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The flat level of the Albuquerque City Council document library at www.cabq.gov/council/documents: files and collection landing pages published directly under that path, excluding the 48 subdirectories beneath it.",
 "scope": f"All {len(rows)} pending-review candidates at the flat level: {len(rows) - len(landing_ids)} documents and {len(landing_ids)} collection landing pages. The handoff ledger recorded 52 pending for www.cabq.gov/council/documents; the whole tree in fact holds 525 pending across 872 records, and this artifact deliberately scopes to the flat level, which is the coherent unit. The 48 subdirectories, led by 21st-century-transportation-task-force at 57 pending, councilor-district-2-documents at 50, and amendments-for-posting-on-council-page at 34, remain untriaged and are the natural next lanes.",
 "brief": "Separate enacted legislation, adopted plans, and Council reports from routine agendas, notices, and administrative forms.",
 "brief_finding": "The brief's first category turns out to be almost empty and the reason matters: every piece of legislation at this level carries a blank enactment number. Seven are substitute bill texts and twenty-three are one-page amendment sheets, and not one is an enacted ordinance or resolution. The only enacted instrument in the cluster arrives by accident, bound as Appendix 1 inside the appendix volume of a Council staff report. What the directory does hold is a small set of genuinely substantive records buried among fifty-eight forms, fragments, agendas, and landing pages: the 2008 Urban Land Institute Rail Yards panel report, the 2007 Neighborhood Task Force report, a Council staff report with its appendices, three advisory board minutes, and three sets of Old Town task force ranking results.",
 "method": "Scoped the cluster by path depth, separating 65 document files from 42 collection landing pages. Fetched all 65 files without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 65 are genuine PDFs by leading bytes. Extracted text with pdftotext -layout, and rendered the one image-only PDF through pdf.js in a headless browser to identify it. Ran pairwise normalized-text similarity and token coverage across the cluster. Compared all 65 SHA-256 values against the 1,612 checksummed records in master-inventory.json. For the agenda records, searched all 872 council/documents inventory records, ran the cabq.gov site search, and fetched the meeting-agenda-documents directory listing to look for minutes.",
 "classification_only": True,
 "shared_state_written": [],
 "precedent_applied": "Three standing repository rules decide most of this cluster. (1) The missing-minutes agenda policy in AGENTS.md, whose application here is confirmed by an already-terminal record: src-0a6bdb5c898342da, the June 2, 2026 African American Advisory Board agenda, is excluded while the minutes of that same meeting sit pending in this batch. (2) The two open checkpoint blockers on legislative files, which require the authoritative enacted package to be resolved before archival or visible use and forbid presenting a non-enacted version as enacted. (3) The form-versus-substance line applied in the Planning UDD, code-enforcement, construction-documents, and Development Review Services lanes.",
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 4,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 4,
  "relationships_found_by_normalized_text_or_token_coverage": 2,
  "note": "This is the first cluster in this run where hashing did most of the work: four pending files are byte-identical to already-validated records, including an 8.9 MB sector development plan and an 11.8 MB complete streets toolkit. The two relationships hashing missed are the Old Town task force colour and greyscale editions, which are the same result set rendered twice for accessibility and differ in bytes, page images, and extracted chart labels while carrying identical questions and participant counts."
 },
 "integration_flags": [
  {"severity": "category",
   "affects": ["all 23 amendment-sheet records in this artifact"],
   "finding": "The 23 one-page floor and committee amendment sheets here are recommended excluded as non-self-contained fragments, but they are not stray files: they are a deliberate City Council publication series, and a sibling subdirectory named amendments-for-posting-on-council-page holds 34 more. Together that is at least 57 records of the same kind. Each sheet does carry information the enacted text does not, namely the recorded vote with councilors named for and against.",
   "recommended_action": "Treat the exclusion as a category decision that is open to revisiting, not as 23 independent judgements. If ABQInfo ever carries Council legislative history as a feature, revisit all 57 together rather than record by record."},
  {"severity": "blocker-consistent",
   "affects": ["src-be410a77ceab45b2", "src-cb868b1506e51793", "src-844d4e3d0227e107", "src-bc91d8e4f296d80b", "src-26cc63bf3b00147d", "src-3ce96f0fc670867e", "src-3cd044acfb1a299f"],
   "finding": "All seven substitute bill texts carry a blank ENACTMENT NO. on their face. The checkpoint already holds two open blockers on precisely this: isolated legislative amendment and substitute files must have their authoritative enacted packages resolved before archival or visible use, and a non-enacted version must not be archived or presented as enacted.",
   "recommended_action": "Hold all seven at requires human review until each enacted counterpart is located. Two of them, F/S O-24-4 and F/S R-24-17, are general obligation bond instruments, and the inventory already holds an extensive validated GO bond record set, so those two are the most likely to resolve quickly."},
  {"severity": "architecture",
   "affects": ["src-baf2db7aea5be0d2", "src-c8618de9cd7384e7", "src-f6f982e95a648dd7", "src-f0c76005377afd83"],
   "finding": "ABQInfo has no page for City board and commission records. The Development Process Manual Executive Committee minutes were placed on a subject-matter page because the manual has one; the African American Advisory Board and Council Services have no equivalent. The proposed_canonical_page on these four records is the least-bad existing page, not a good fit.",
   "recommended_action": "A new page such as content/about/boards-commissions.md would fit, but that is a material site-architecture change and AGENTS.md reserves those for user direction. Keep these four inventory-only until the user decides. They are approved on the merits; only their placement is open."},
  {"severity": "scope",
   "affects": ["the council/documents tree"],
   "finding": "The handoff ledger recorded 52 pending for www.cabq.gov/council/documents. The real figure is 525 pending across 872 records, spread over 48 subdirectories. This artifact covers the 107 at the flat level.",
   "recommended_action": "Correct the ledger figure and treat the larger subdirectories as separate lanes. By size: 21st-century-transportation-task-force (57), councilor-district-2-documents (50), amendments-for-posting-on-council-page (34), north-fourth-street-plan (23), and then a long tail of 20-record directories."},
  {"severity": "follow-up",
   "affects": ["src-6db0397455652054"],
   "finding": "The excluded public meeting flyer announces a Rainbow Boulevard Traffic Calming and Pedestrian Safety Study between Paseo del Norte and the southern property line of Volcano Vista High School. The study itself is nowhere in the inventory.",
   "recommended_action": "Worth a targeted search in a later lane. A flyer that names a study the archive does not hold is a discovery lead, which is the only reason it is recorded here at all."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "superseded": 0,
  "excluded_breakdown": {
   "council legislative amendment sheet": 23,
   "collection landing page": len(landing_ids),
   "other": counts["excluded"] - 23 - len(landing_ids)
  }
 },
 "link_check": {
  "checked": 65, "http_200": 65, "failed": 0,
  "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 65 document files. The 42 collection landing pages were not individually fetched; they are excluded as pages rather than documents and the parent listing resolved for all of them.",
  "containers_verified": "All 65 files are genuine PDFs by leading bytes (25 50 44 46). No extension mismatch in this cluster, unlike the Municipal Development and Development Review Services libraries."
 },
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": "All 12 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Four of them, the three advisory board minutes and the Council Services organisational chart, additionally have no settled page to go on; see integration_flags.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every duplicate row carries a canonical_id and all four hash-based canonicals are already validated records. The 12 approved rows carry a title, a 20-to-50-word description, a proposed_canonical_page, and cross_listings where a second page applies. Fourteen rows are requires human review and each states its question and what evidence was already gathered, so none of them needs the research repeated. Sizes and checksums for the 65 document files are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != "excluded_breakdown"}}))
