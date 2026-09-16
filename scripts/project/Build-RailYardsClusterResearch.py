"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\rail-yards-advisory-board-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\railyard\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/rail-yard/'

PROJECTS = 'content/development-land-use/projects.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC, "content_kind": "PDF"}
    r.update(M[i])
    return r


def A(i, title, desc, date, pages, kind, evidence, page=PROJECTS, cross=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": date, "pages": pages, "record_kind": kind,
              "proposed_canonical_page": page, "cross_listings": cross or [],
              "evidence": evidence})
    if extra:
        r.update(extra)
    return r


MIN = "approved minutes"
NOTES = "facilitated meeting notes"

approved = [
 A("src-31f04c0a05ce9464",
   "Rail Yards Advisory Board Minutes, July 23, 2009",
   "The board's first recorded meeting takes a presentation on the Santa Fe Railyard redevelopment from Richard Czoski, then reviews tax increment development districts, public improvement districts, and New Market Tax Credits as financing tools for the Albuquerque Rail Yards site.",
   "2009-07-23", 10, MIN,
   "Ten pages, the longest record in the cluster. Numbered items 2 through 6 cover the Santa Fe Railyard presentation, TIDDs and PIDs, New Market Tax Credits presented by Marquita Russel, and next steps."),

 A("src-28d44d49f4e5bb96",
   "Rail Yards Advisory Board Minutes, September 15, 2009",
   "The board takes an update from Rail Yards Coordinator Lawrence Kline and a presentation from Leba Freed, president of the WHEELS Museum, on the museum's role and interests at the Albuquerque Rail Yards site.",
   "2009-09-15", 5, MIN,
   "Five pages. Numbered items 2 and 3 are the coordinator update and the WHEELS Museum presentation."),

 A("src-2235f2459a6f25f5",
   "Rail Yards Advisory Board Minutes, November 9, 2009",
   "The board works on designing a vision for the Albuquerque Rail Yards and sets its own agenda through mid-2010, shaping the sequence of work that led to the master developer request for proposals.",
   "2009-11-09", 6, MIN,
   "Six pages. Numbered items 2 and 3 are \"Designing a Vision for the Rail Yards\" and \"Designing the Advisory Board's Agenda Through Mid-2010\"; the meeting adjourned at 1:00 PM."),

 A("src-9e487819a23af012",
   "Rail Yards Advisory Board Minutes, December 14, 2009",
   "The board hears workforce housing data from Marti Luick and market housing data from Todd Clarke, discusses perspectives on housing within a future Rail Yards development, and takes up advisory board ground rules as new business.",
   "2009-12-14", 5, MIN,
   "Five pages. Numbered items 2 through 5 are the two housing data presentations, the housing discussion, and the ground rules item; the meeting adjourned at 1:00 PM."),

 A("src-629bcb5615c018f0",
   "Rail Yards Advisory Board Facilitated Meeting Notes, January 11, 2010",
   "The facilitator reframes the board's charge, which is at minimum to develop a request for qualifications for a master developer of the Rail Yards, and the board works through the competing demands built into the authorizing legislation.",
   "2010-01-11", 7, NOTES,
   "Seven pages, headed FACILITATED MEETING NOTES rather than MINUTES. Facilitator Tim Karpoff opens by restating the charge and naming the authorizing legislation's requirements, including a minimum number of workforce housing units and the WHEELS Museum.",
   extra={"naming_rule": "Title this a facilitated meeting notes record, never minutes. The board titled four 2010 records this way and titled every other meeting record MINUTES, so the distinction is the board's own."}),

 A("src-912c7bc4e5bd5a67",
   "Rail Yards Advisory Board Facilitated Meeting Notes, March 8, 2010",
   "With the City purchasing officer and purchasing attorney present, the board works through what a master developer solicitation should ask for and what minimum commitments proposers should be required to return.",
   "2010-03-08", 7, NOTES,
   "Seven pages. The staff list is unusually procurement-heavy: John Vigil, Purchasing Officer, and Paula West, Purchasing attorney, alongside the facilitator and consultant Lawrence Kline.",
   extra={"naming_rule": "Facilitated meeting notes, not minutes."}),

 A("src-1c09de804a8080ee",
   "Rail Yards Advisory Board Facilitated Meeting Notes, April 12, 2010",
   "The board works line by line through a draft solicitation document, with members debating how much neighborhood history to include, how the Urban Land Institute report should be referenced, and which state incentives to list.",
   "2010-04-12", 6, NOTES,
   "Six pages recorded as numbered line comments attributed to individual members, including Senator Griego on section length and the history of the neighborhood, and Leba Freed asking whether the ULI report would be provided in full or in part.",
   extra={"naming_rule": "Facilitated meeting notes, not minutes.",
          "links_to": "The ULI report the members are discussing is src-9f5ac56df8c6cbb8, recommended for addition in the council-documents artifact of the same date."}),

 A("src-a6e79304cfd046df",
   "Rail Yards Advisory Board Facilitated Meeting Notes, May 10, 2010",
   "Described by the facilitator as the final meeting before the request for proposals is issued, the board settles remaining details and Councilor Benton frames the selection as the start of an ongoing interactive process with whichever master developer is chosen.",
   "2010-05-10", 4, NOTES,
   "Four pages. Tim Karpoff states \"This is intended to be the final meeting before we issue the RFP\"; Councilor Benton and Leba Freed open the meeting.",
   extra={"naming_rule": "Facilitated meeting notes, not minutes."}),

 A("src-cb1c03423c8c69eb",
   "Rail Yards Advisory Board RFP Selection Committee Minutes, September 21, 2010",
   "The selection committee receives the three proposals submitted for the Rail Yards master developer contract and is briefed by purchasing staff on confidentiality, non-disclosure forms, and the ten-day protest period after which evaluation score sheets become public record.",
   "2010-09-21", 2, MIN,
   "Two pages. Joe Rael distributes the three proposals and answers members' questions about what discussions are permitted; the record is a verbatim exchange."),

 A("src-280c30eafa8548d7",
   "Rail Yards Advisory Board RFP Selection Committee Minutes, October 19, 2010",
   "The committee shortlists the Rail Yards master developer field, voting unanimously to interview the Samitaur and City View/Paradigm teams and voting nine to one to reject the Albuquerque Station Consortium proposal as non-responsive to the request for proposals.",
   "2010-10-19", 1, MIN,
   "One page, and the single most consequential record in the cluster: it carries both recorded votes, including the 9-1 vote with Campbell dissenting, and directs staff to draft interview questions."),

 A("src-87bcd16c28c3bf01",
   "Rail Yards Advisory Board RFP Selection Committee Minutes, December 14, 2010",
   "At the selection committee's final meeting the members score the two remaining Rail Yards master developer proposals and debate each team's financing capacity, with Samitaur's banking relationships and ability to carry upfront costs weighed against uncertainty over City View's funding.",
   "2010-12-14", 3, MIN,
   "Three pages. Councilor Benton calls the meeting to order; the facilitator states \"This is the final meeting of the Selection Committee. Tonight, we are going to score the proposals and determine if there is a recommendation\"."),

 A("src-30a65e69acc80582",
   "Rail Yards Advisory Board Agenda, May 4, 2011 (approved minutes not located)",
   "The board's published agenda sets out discussion of the draft predevelopment agreement, a WHEELS Museum presentation on its Blacksmith Shop proposal, and next steps covering continued agreement negotiations and City legal review.",
   "2011-05-04", 1, "official agenda, approved minutes not located",
   "One page with a substantive business list, not a bare notice. Its Blacksmith Shop item is the origin of the Rail Yards Blacksmith Shop Feasibility Study the site already archives for 2012.",
   extra={"policy": "Preserved under the AGENTS.md missing-minutes agenda policy. It must be labelled \"Agenda (approved minutes not located)\" or equivalent, must link the official source, must preserve the meeting date, and must never be presented as minutes or as a substitute for them.",
          "review_recorded": "See exhaustive_minutes_review."}),

 A("src-a4873560a2bfda21",
   "Rail Yards Advisory Board Agenda, June 20, 2011 (approved minutes not located)",
   "The board's published agenda sets out a welcome and overview followed by discussion of the draft predevelopment agreement, covering issues requiring board guidance, other issues of note, and questions and comments before adjournment.",
   "2011-06-20", 1, "official agenda, approved minutes not located",
   "One page. The predevelopment agreement it discusses is the same negotiation the November 14, 2011 minutes later report on in detail.",
   extra={"policy": "Preserved under the AGENTS.md missing-minutes agenda policy, with the same labelling requirement as the May 4, 2011 agenda.",
          "review_recorded": "See exhaustive_minutes_review."}),

 A("src-7e42cac096e8fc1f",
   "Rail Yards Advisory Board Minutes, November 14, 2011",
   "City staff report that master development agreement negotiations with Samitaur Constructs have stalled over a requested three million dollar loan to fund master planning and over how fair value of parcels would be defined, and ask the board for direction.",
   "2011-11-14", 2, MIN,
   "Two pages. Suzie Lubar, Manager of the Real Property Division, gives the negotiations update; Leba Freed reads a WHEELS Museum statement recommending that negotiations with Samitaur cease altogether. Samitaur's representatives attended.",
   extra={"approval_evidence": "These minutes were formally approved: the March 14, 2012 minutes record \"The minutes from the 11-14-11 RYAB meeting were approved by a unanimous vote of the Board.\""}),

 A("src-a817856a169fdddb",
   "Rail Yards Advisory Board Minutes, March 14, 2012",
   "The Council chief finance officer tells the board that the thirty required workforce housing units cannot be built off site, quoting Council bill R-07-332 on the creation of affordable housing on the railyard property, and members question Samitaur's capacity to deliver permanently affordable housing.",
   "2012-03-14", 6, MIN,
   "Six pages. Item 1 approves the November 14, 2011 minutes unanimously. The record also notes mid-meeting loss of quorum after Senator Griego left, after which members stated positions instead of voting formally; the meeting adjourned at 4:20 PM.",
   extra={"quorum_note": "The quorum loss is recorded mid-meeting and the meeting continued and produced minutes. It does not engage the AGENTS.md rule against archiving agendas for no-quorum meetings, which concerns agendas rather than minutes, but any description should not imply formal votes were taken after that point."}),

 A("src-1ff81de0bfe295ef",
   "Rail Yards Advisory Board Minutes, October 8, 2012",
   "Staff report on the Rail Yards master planning process, which opened with three public meetings attended by more than two hundred people and continued through small-group sessions with a dozen key stakeholders before Samitaur's first draft plan.",
   "2012-10-08", 5, MIN,
   "Five pages. Item 1 approves the March 14, 2012 minutes unanimously. Item 2 names the stakeholders consulted, including the Barelas and South Broadway neighborhoods, the WHEELS Museum, the New Mexico Steam Locomotive and Railroad Historic Society, MRCOG, the Downtown Action Team, and affordable housing providers, and sets the October 25 public meeting for the first draft."),

 A("src-ef81b015dafabc60",
   "Rail Yards Master Plan Frequently Asked Questions, December 1, 2012",
   "The City question-and-answer document explains the Rail Yards master planning process to the public, covering the site's history and ownership, the role of the master developer, the planning timeline, and how residents could take part.",
   "2012-12-01", 9, "public information document",
   "Nine pages opening \"This document is intended to provide background information to help the public\". It is the only non-meeting record in the directory and the public-facing companion to the master plan the site already archives in three editions.",
   page=PROJECTS,
   cross=[{"page": REDEV, "reason": "The Rail Yards are a named City redevelopment area and the page already carries related redevelopment records."}]),
]


def X(i, canonical_id, title, reason):
    r = row(i, "excluded")
    r.update({"title_for_reference": title,
              "exclusion_reason": reason,
              "minutes_record_for_same_meeting": canonical_id})
    return r


excluded = [
 X("src-1c2854ed333f643c", "src-cb1c03423c8c69eb",
   "Rail Yards Advisory Board RFP Selection Committee Meeting 1 Agenda, September 21, 2010",
   "Agenda for a meeting whose minutes are published and recommended for addition in this same batch (src-cb1c03423c8c69eb). The AGENTS.md missing-minutes policy preserves an agenda only where approved minutes cannot be located, and forbids archiving one when an approved-minutes original is available."),
 X("src-258d0666cbbe5a58", "src-87bcd16c28c3bf01",
   "Rail Yards Advisory Board RFP Selection Committee Final Meeting Agenda, December 14, 2010",
   "Agenda for a meeting whose minutes are published and recommended for addition in this same batch (src-87bcd16c28c3bf01). Same policy ground."),
 X("src-4e714d712aa9adc8", "src-7e42cac096e8fc1f",
   "Rail Yards Advisory Board Agenda, November 14, 2011",
   "Agenda for a meeting whose minutes are published, recommended for addition in this same batch (src-7e42cac096e8fc1f), and demonstrably approved: the March 14, 2012 minutes record their unanimous approval. Same policy ground, and the strongest case of the three because the approval is documented."),
]

rows = approved + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "rail-yards-advisory-board-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/rail-yard cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Rail Yards Advisory Board record set in the Albuquerque City Council document library at www.cabq.gov/council/documents/rail-yard.",
 "scope": "All 20 pending-review candidates in that directory, which is the entire directory: no record in it held any other status, and the City's own listing returns exactly these 20 files. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Separate Rail Yards planning, environmental, and redevelopment records from meeting handouts, extending the placement already established under Rail Yards Planning and Environmental Records.",
 "brief_finding": "The separation the brief asks for turns out to be the wrong cut for this directory. Nineteen of the twenty files are meeting records, and they are not handouts: they are the minute book of the board that ran the Rail Yards master developer competition from 2009 to 2012, including the one-page October 19, 2010 selection committee minutes that record the votes shortlisting Samitaur and rejecting the Albuquerque Station Consortium as non-responsive. The site already archives the master plan those decisions produced in three editions. What was missing was how the developer was chosen, and this directory is that record.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 20 are genuine PDFs by leading bytes and all have extractable text. Compared every checksum against the 1,612 checksummed inventory records and against each other. Read every meeting record to identify its business, its date, and whether the board titled it minutes or notes. Paired agendas against minutes by meeting date, then ran a recorded exhaustive official-source review for the two agendas with no matching minutes.",
 "classification_only": True,
 "shared_state_written": [],
 "precedent_applied": "The AGENTS.md missing-minutes agenda policy governs this cluster end to end: preserve a verified original official agenda only after a recorded exhaustive official-source review finds no approved minutes, label it so it is never presented as minutes, and never archive an agenda when an approved-minutes original is available. The council-documents artifact of the same date applied the same rule with an in-inventory precedent, src-0a6bdb5c898342da.",
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "note": "No duplicate or supersession relationship exists in this directory. Every file is a distinct dated record of a distinct meeting, which is unusual for this project and follows from the directory being a minute book rather than a forms library."
 },
 "record_kind_distinction": {
  "finding": "The board titled four early 2010 records FACILITATED MEETING NOTES and every other meeting record MINUTES, on the face of each document. That is the board's own distinction, not an inference from filenames.",
  "rule": "Title the four 2010 records as facilitated meeting notes and never as minutes. They are full meeting records of comparable depth, four to seven pages with attendance and attributed discussion, so they are retained on the same footing; only the label differs.",
  "ids": ["src-629bcb5615c018f0", "src-912c7bc4e5bd5a67", "src-1c09de804a8080ee", "src-a6e79304cfd046df"]
 },
 "exhaustive_minutes_review": {
  "purpose": "The AGENTS.md missing-minutes agenda policy permits preserving an official agenda only after a recorded exhaustive official-source review finds no approved minutes for that meeting. This is that record, for the May 4, 2011 and June 20, 2011 meetings.",
  "steps": [
   "Fetched the City's own directory listing at https://www.cabq.gov/council/documents/rail-yard on 2026-09-11. It returns exactly 20 links, enumerated and matched one for one against the 20 inventory records. The City publishes nothing else for this board.",
   "Searched all 7,074 inventory candidates for RYAB and for \"rail yards advisory\" in title, direct_file_url and source_url. The result is exactly these 20 records plus src-9f5ac56df8c6cbb8, the 2008 Urban Land Institute panel report, which is not a meeting record.",
   "Read the minutes of the next recorded meeting, November 14, 2011, for a minutes-approval item covering either date. It has none: those minutes open directly with the negotiations update.",
   "Established that the board did approve minutes as a matter of practice, so silence is meaningful rather than merely absent: the March 14, 2012 minutes approve the November 14, 2011 minutes unanimously, and the October 8, 2012 minutes approve the March 14, 2012 minutes unanimously."
  ],
  "conclusion": "No approved minutes for the May 4, 2011 or June 20, 2011 meetings exist in any official source reachable from the City site or the inventory. Both agendas carry substantive business lists rather than bare notices.",
  "limit_stated_plainly": "Two things this review cannot establish from these files. First, whether minutes for those two meetings were ever produced and simply never published, as opposed to never produced. Second, whether either meeting was held at all: nothing in an agenda shows whether the meeting it announces took place, was cancelled, or lacked a quorum, and the AGENTS.md rule against archiving agendas for cancelled or no-quorum meetings therefore cannot be affirmatively cleared from the agenda alone. Nothing found indicates cancellation, and the surrounding record shows an active board negotiating a predevelopment agreement throughout 2011, but that is inference rather than proof. If Codex or the user holds this to a stricter standard, these two records should move to requires human review; the rest of the batch does not depend on them."
 },
 "integration_flags": [
  {"severity": "placement",
   "affects": ["all 17 approved records"],
   "finding": "content/development-land-use/projects.md already carries a \"Rail Yards Planning and Environmental Records\" section holding the Blacksmith Shop feasibility and environmental sampling studies, and the page above it carries three editions of the Rail Yards Master Plan. Seventeen meeting records is a large addition to a section currently holding two items.",
   "recommended_action": "Consider a distinct subsection, for example Rail Yards Advisory Board Records, rather than appending seventeen entries to the existing list. That is a page-structure choice within an existing page rather than a site-architecture change, but it should be made deliberately."},
  {"severity": "coherence",
   "affects": ["src-9f5ac56df8c6cbb8", "src-1c09de804a8080ee"],
   "finding": "The 2008 Urban Land Institute Rail Yards panel report is recommended for addition in the council-documents artifact of the same date, from a different directory. The April 12, 2010 facilitated meeting notes in this batch record the board debating how that report should be used in the developer solicitation.",
   "recommended_action": "Integrate the two artifacts together so the report and the board record that uses it land on the same page in the same batch."},
  {"severity": "precision",
   "affects": ["src-a817856a169fdddb"],
   "finding": "The March 14, 2012 minutes record that quorum was lost mid-meeting when Senator Griego left, after which members stated positions instead of voting formally.",
   "recommended_action": "Any published description must not imply formal votes were taken after that point. The record remains approved minutes of a meeting that took place; this is a description-accuracy note, not a status question."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "excluded": counts["excluded"],
  "duplicate": 0, "superseded": 0, "requires_human_review": 0,
  "approved_breakdown": {
   "approved minutes": sum(1 for r in approved if r["record_kind"] == MIN),
   "facilitated meeting notes": sum(1 for r in approved if r["record_kind"] == NOTES),
   "official agenda, approved minutes not located": 2,
   "public information document": 1
  }
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 20 files are genuine PDFs by leading bytes and all yield extractable text; no rendering was needed."},
 "approved_for_addition": approved,
 "excluded": excluded,
 "archival_note": "All 17 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: "
                  f"{sum(r['size_bytes'] for r in approved):,} bytes, under two megabytes for all seventeen, so this batch poses no storage question.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id because the directory holds no duplicate or supersession relationship at all. The 17 approved rows each carry a title, a 20-to-50-word description, a date, a record_kind, and a proposed_canonical_page. Two of them are agendas preserved under the missing-minutes policy and their titles must keep the \"(approved minutes not located)\" qualifier. Four are facilitated meeting notes and must never be titled minutes. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != "approved_breakdown"}}))
