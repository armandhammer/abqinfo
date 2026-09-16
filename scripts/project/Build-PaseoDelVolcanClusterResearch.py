"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\paseo-del-volcan-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\pdv\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/paseo-del-volcan-documents/'

PLANS = 'content/transportation/transportation-plans.md'
ROADS = 'content/transportation/roadway-projects/_index.md'
PARKS = 'content/public-works/parks-recreation.md'

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


def A(i, title, desc, date, pages, evidence, page, why=None, cross=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": date, "pages": pages,
              "proposed_canonical_page": page, "cross_listings": cross or [],
              "evidence": evidence})
    if why:
        r["why_retained"] = why
    if extra:
        r.update(extra)
    return r


approved = [
 A("src-8043e1de7031af50",
   "Paseo del Volcan Corridor: Analysis of Economic Development Opportunities, With Technical Appendices (September 2014)",
   "The corridor study analyses the economic development opportunities a completed Paseo del Volcan would open on Albuquerque's west side, assessing land, market, and infrastructure conditions and the return on investment from building the road, with full technical appendices.",
   "2014-09", 86,
   "86 pages and 4,563,767 bytes, the substantive deliverable the whole directory was assembled to produce. Its procurement history is visible in the same directory: a draft scope of work, a findings memorandum feeding the request for proposals, and the steering committee minutes that commissioned it.",
   PLANS,
   why="The only full corridor economic study in the inventory. The site currently mentions Paseo del Volcan exactly once, inside an MRCOG appendix listing regional projects of special interest; this is the primary document behind that line.",
   cross=[{"page": ROADS, "reason": "Paseo del Volcan is a named west side corridor project and belongs in the roadway projects index alongside Unser Boulevard and Paseo del Norte."}]),

 A("src-e04cf778f5a04ae9",
   "Paseo del Volcan Economic Opportunity Analyses and Implementation Strategy, Steering Committee Summary Presentation (November 7, 2014)",
   "The summary presentation to the steering committee sets out the corridor background, the economic opportunity findings from the September 2014 analysis, and the implementation strategy proposed for carrying those findings forward.",
   "2014-11-07", 30,
   "30 pages. It post-dates the study by two months and carries the implementation strategy the study itself does not.",
   PLANS,
   why="Not a duplicate of the study, despite a coverage measurement that looks like one. See measurement_trap: its extracted text is only slide headings, so 0.9055 of its 582 tokens sit inside the study's 3,027 while the sequence ratio is 0.106. The two documents answer different questions.",
   extra={"relationship": "Companion to src-8043e1de7031af50; present them together."}),

 A("src-4aaa2a918146e21c",
   "Paseo del Volcan Right-of-Way Acquisition Status Map, December 2013",
   "The New Mexico Department of Transportation map shows right-of-way acquisition progress along the Paseo del Volcan alignment from Interstate 40 to US 550, tabulating parcels and acres acquired against those outstanding and naming the major landholders.",
   "2013-12", 1,
   "One large-format sheet prepared for NMDOT by Parsons Brinckerhoff. The table reads 403 parcels and 419 acres acquired (28 and 23 per cent) against 1,050 parcels and 1,443 acres not acquired, out of a project total of 1,453 parcels and 1,862 acres, with 672 acres in land dedications from Ranch Joint Venture, the City of Albuquerque and Western Albuquerque Land Holding LLC. It marks Phase 1 and Phase 2 as acquired and Phase 3 private parcels as outstanding, and tabulates 2014 and 2015 funding of $1,000,000 a year from state match and STP-FLEX.",
   ROADS,
   why="A dated, quantified public record of how much of a major corridor the state had actually bought, naming the private landholders involved. It is the only right-of-way status record in the inventory for this corridor.",
   extra={"date_trap": "The inventory titles the other copy of this map \"Map of Acquisition Status 4/4/2014\" and both filenames carry meeting dates. The map's own printed date is DECEMBER 2013; the 2014 dates are the meetings it was handed out at. Date it from the sheet."}),

 A("src-b1816c40babc0546",
   "Paseo del Volcan Funding and Financing Workshop Presentation (April 4, 2014)",
   "The consultant workshop presentation to the steering committee sets out the funding and financing mechanisms available for building the Paseo del Volcan corridor, prepared by the highway financing practice advising the Mid-Region Council of Governments.",
   "2014-04-04", 13,
   "13 pages headed \"Strategic Consulting Services, Paseo del Volcan, Funding and Financing Workshop\". The April 4, 2014 minutes record Nick Amrhein of Parsons Brinckerhoff presenting financing strategies for 45 minutes, the longest item on that agenda.",
   PLANS,
   why="The financing half of the corridor question, which the economic study does not cover. Together with the study and the right-of-way map it gives the three things a reader needs: what the road would be worth, what it would cost to buy, and how it could be paid for."),

 A("src-625f2a5f3f04d910",
   "Paseo del Volcan: Long Term Perspective (project brochure)",
   "The public brochure makes the case for Paseo del Volcan, describing how the Sandia Mountains, the Petroglyph National Monument, and surrounding tribal lands constrain Albuquerque's growth, and stating the corridor's cost at roughly $96.2 million with a $26.0 million first phase.",
   None, 2,
   "Two pages. It carries the headline cost figures, $96.2 million total and $26.0 million for Phase 1, and the constraint argument in the form the project's promoters put to the public.",
   PLANS,
   why="The public-facing summary of the corridor case, and the only document in the directory that states the total project cost. Its 0.9091 token coverage inside the study is the same sparse-text artefact described in measurement_trap, not duplication.",
   extra={"dating_note": "No printed date. It belongs to the 2013 to 2014 steering committee period; do not assert a date it does not carry."}),

 A("src-2f75875ce1c5cf27",
   "Long Range Development Plans for Double Eagle II Airport, Steering Committee Presentation (June 27, 2014)",
   "The presentation to the Paseo del Volcan steering committee sets out long range development plans for Double Eagle II Airport, the City's west side general aviation field, and the aviation economy context for corridor development around it.",
   "2014-06-27", 5,
   "Five pages, opening with the state of the Albuquerque aviation economy. Double Eagle II is a City-owned airport and the corridor's main existing public asset.",
   PLANS,
   why="The only Double Eagle II development planning record in the inventory. The airport is City property, which makes this a City asset record rather than a corridor advocacy document.",
   cross=[{"page": ROADS, "reason": "The airport is the anchor land use on the corridor the roadway index would describe."}]),

 A("src-bdb03a2b53786b9a",
   "Major Public Open Space on the City's West Side, Steering Committee Presentation",
   "The City Open Space presentation inventories major public open space lands and facilities west of Coors Boulevard, illustrating each with photographs, as context for what the Paseo del Volcan corridor would run through and alongside.",
   None, 25,
   "25 pages and 9,053,886 bytes, the largest file in the directory, headed \"Major Public Open Space On the City's West Side\" with photographs credited to Bill Pentler and the subtitle \"City Open Space Lands and Facilities West of Coors\".",
   PARKS,
   why="A City Open Space inventory of the west side in its own right, useful well beyond the corridor question. The parks page already carries an Arroyo and Open Space Planning History section.",
   cross=[{"page": PLANS, "reason": "It was prepared for the corridor steering committee and belongs beside the other corridor records."}],
   extra={"dating_note": "No printed date; it belongs to the 2013 to 2014 steering committee period."}),

 A("src-189c0a45bb72113c",
   "Paseo del Volcan Steering Committee Minutes, Second Meeting, January 15, 2014",
   "The minutes of the second Paseo del Volcan steering committee meeting, convened by the Mid-Region Council of Governments as the Albuquerque metropolitan planning organisation, record attendance and the right-of-way acquisition discussion.",
   "2014-01-15", 3,
   "Three pages headed \"Mid-Region Council of Governments / Albuquerque Metropolitan Planning Organization (MPO), Paseo del Volcan (PDV) Steering Committee, Second Meeting\". The agenda for this meeting is recommended excluded below.",
   PLANS),

 A("src-3924fb39a476b0a7",
   "Paseo del Volcan Steering Committee Minutes, April 4, 2014",
   "The minutes of the April 2014 steering committee meeting record the right-of-way acquisition update, the economic development discussion that shaped the corridor study's scope, and the financing strategies workshop.",
   "2014-04-04", 3,
   "Three pages, chaired by Dewey Cave, Executive Director of the Mid-Region Council of Governments. Two other files in the directory are handouts from this meeting. The agenda is recommended excluded below.",
   PLANS),

 A("src-fd2c4ff2f2681189",
   "Paseo del Volcan Steering Committee Meeting Notes, Fourth Meeting, June 27, 2014",
   "The notes of the fourth steering committee meeting, the longest meeting record in the directory, cover the right-of-way acquisition update and the presentations on Double Eagle II Airport development and private landholder plans for the corridor.",
   "2014-06-27", 8,
   "Eight pages, the fullest meeting record in the directory. It is headed \"Meeting Notes\" rather than Minutes, so title it that way. The agenda is recommended excluded below.",
   PLANS,
   extra={"naming_rule": "The committee headed this record \"PDV Steering Committee Meeting Notes\". Title it notes, not minutes, on the same principle applied to the Rail Yards facilitated meeting notes in the artifact of the same date."}),

 A("src-05705d25113d3f2e",
   "Paseo del Volcan Steering Committee Agenda, First Meeting, November 20, 2013 (approved minutes not located)",
   "The agenda for the first Paseo del Volcan steering committee meeting sets out the overview presentation by Councilor Dan Lewis and the New Mexico Department of Transportation, followed by strategy discussion and next steps for the corridor.",
   "2013-11-20", 1,
   "One page. It is the founding meeting of the committee whose later minutes make up much of this directory, and it names who convened it: Dewey Cave of MRCOG, Councilor Dan Lewis, and Tony Abbo of NMDOT.",
   PLANS,
   why="Preserved under the AGENTS.md missing-minutes agenda policy. It is the only record of the committee's first meeting and the only place the corridor effort's originators are named together.",
   extra={"policy": "Must be labelled \"Agenda (approved minutes not located)\" or equivalent, must link the official source, must preserve the meeting date, and must never be presented as minutes.",
          "date_trap": "The filename and the inventory title both say 11/12/2013. The sheet itself says Wednesday, November 20, 2013. Date it from the sheet.",
          "review_recorded": "See exhaustive_minutes_review."}),
]

duplicates = [
 {**row("src-a467fcc659644b8c", "duplicate"),
  "title_for_reference": "PDV ROW Acquisition Status map, April 4 2014 handout copy",
  "pages": 1,
  "canonical_id": "src-4aaa2a918146e21c",
  "canonical_url": BASE + "PDV%20STATUS%20OF%20ACQUISITION%2012-13%20011514%20Final.pdf",
  "basis": "The same December 2013 NMDOT right-of-way acquisition status map, re-handed out at the April 4, 2014 meeting. This copy is a scan with no text layer; the canonical carries a text layer. Every figure matches: 403 parcels and 419 acres acquired at 28 and 23 per cent, 1,050 and 1,443 not acquired at 72 and 77 per cent, 1,453 parcels and 1,862 acres project total, 672 acres of land dedication from Ranch Joint Venture, the City and Western Albuquerque Land Holding.",
  "measurement": "Not findable by hash (different bytes) and not findable by text comparison (this copy yields one character). Confirmed by rendering page 1 and reading the table against the canonical's text layer.",
  "hash_found_it": False,
  "note": "Keep the text-layer copy even though it is the larger file, 1,272,699 bytes against 588,183: it is searchable and its filename records the December 2013 data period rather than a meeting date."},
]

rhr = []


def X(i, title, reason, category, pages=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "exclusion_reason": reason, "category": category})
    if pages:
        r["pages"] = pages
    if extra:
        r.update(extra)
    return r


excluded = [
 X("src-20065a59506917f2", "Paseo del Volcan Steering Committee Agenda, January 15, 2014",
   "Agenda for a meeting whose minutes are published and recommended for addition in this same batch (src-189c0a45bb72113c). The AGENTS.md missing-minutes policy forbids archiving an agenda when an approved-minutes original is available.",
   "agenda superseded by its own minutes", 1,
   extra={"minutes_record_for_same_meeting": "src-189c0a45bb72113c"}),
 X("src-d75d2e3ee14b488b", "Paseo del Volcan Steering Committee Agenda, April 4, 2014",
   "Agenda for a meeting whose minutes are published and recommended for addition in this same batch (src-3924fb39a476b0a7). Same policy ground.",
   "agenda superseded by its own minutes", 1,
   extra={"minutes_record_for_same_meeting": "src-3924fb39a476b0a7",
          "note": "Image-only; rendered and read to confirm the meeting date and the five-item running order."}),
 X("src-8915599f6312f3dc", "Paseo del Volcan Steering Committee Agenda, June 27, 2014",
   "Agenda for a meeting whose notes are published and recommended for addition in this same batch (src-fd2c4ff2f2681189). Same policy ground.",
   "agenda superseded by its own meeting record", 1,
   extra={"minutes_record_for_same_meeting": "src-fd2c4ff2f2681189"}),

 X("src-54ca295d8b264ed2", "Paseo del Volcan Draft Scope of Work for a Site Selection Assessment",
   "A draft procurement scope circulated to the steering committee before the economic development analysis was commissioned. It is superseded in substance by the study that was actually produced, src-8043e1de7031af50, and as a draft scope it records no finding of its own.",
   "draft procurement scope", 4,
   extra={"note": "Image-only; rendered. Recorded as excluded rather than superseded because a scope of work and the study it produced are different kinds of document, not two versions of one."}),

 X("src-cea0004bcdaac447", "Findings for the Paseo del Volcan Economic Development Analysis Draft RFP, April 4, 2014",
   "A two-page working memorandum of preliminary findings assembled while drafting the request for proposals, listing best uses for the corridor and sampling a consultant's competitiveness talking points. Every question it raises is answered by the September 2014 study.",
   "working memorandum", 2,
   extra={"note": "Image-only; rendered and read. It cites the Santolina Fiscal Impact Analysis of May 14, 2013 and a projected net taxable value of $3,213,295,892 at full build-out, figures that belong to that separate Bernalillo County analysis rather than to this corridor record."}),

 X("src-b0262b506bbf6683", "Corporate Site Selection Trends: New Mexico's Competitiveness for Business, Remarks by Dennis J. Donovan, January 13, 2014",
   "A consultant's speech handouts to an economic development audience on New Mexico's general business competitiveness. It is not a Paseo del Volcan document, not a City record, and contains no Albuquerque corridor content; it was filed here because the findings memorandum quotes it.",
   "third-party speech handout", 18,
   extra={"encoding_note": "The inventory title for this record is mojibake. Any title must come from the document."}),

 X("src-5b435ce5abe5a4c5", "Paseo del Volcan: The Road to Economic Development, WALH and Ranch Joint Ventures Presentation, June 2014",
   "A presentation to the steering committee by the two private landholding companies with the largest interests along the alignment, Western Albuquerque Land Holding and Ranch Joint Venture. It is landowner advocacy for the corridor rather than a public planning record, and the public analysis of the same question is the September 2014 study retained above.",
   "private landholder presentation", 21,
   extra={"context": "Both companies appear on the retained right-of-way map as land dedicators: Western Albuquerque Land Holding at 315 acres and Ranch Joint Venture at 178 acres. Their interest in the corridor is direct, which is the reason to keep their advocacy out of the archive while keeping the map that names them in it.",
          "measurement_note": "Its 0.8396 token coverage inside the study is the sparse-text artefact described in measurement_trap, not evidence of duplication."}),

 X("src-c0477552efe412a1", "Paseo del Volcan Sample Resolution, December 12, 2013",
   "A model resolution drafted for other local governments to adopt, stating the regional importance of the corridor and asking that it be made a high priority for local, state or federal funding. Its resolution number is blank and no adopting body is named: it is a template for advocacy, not an enacted instrument.",
   "model resolution template", 4,
   extra={"note": "If an adopted version by any named jurisdiction is later located, that adopted resolution would be a retainable record and this template would remain excluded."}),
]

rows = approved + duplicates + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "paseo-del-volcan-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/paseo-del-volcan-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Paseo del Volcan corridor record set in the Albuquerque City Council document library at www.cabq.gov/council/documents/paseo-del-volcan-documents, covering the 2013 to 2014 steering committee convened by the Mid-Region Council of Governments.",
 "scope": "All 20 pending-review candidates in that directory, which is the entire directory: no record in it held any other status. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Separate corridor studies, alignment records, and adopted plans from meeting handouts and correspondence.",
 "brief_finding": "There are no adopted plans here; the corridor never got one. What the directory holds is the evidence base that would have supported one, and it is unusually complete: an 86-page economic development study with technical appendices, a quantified state right-of-way acquisition map, a financing workshop, and the minutes of the committee that commissioned all three. The site currently mentions Paseo del Volcan exactly once, inside an MRCOG appendix line listing it among regional projects of special interest. This directory is the primary record behind that line.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 20 are genuine PDFs by leading bytes. Extracted text with pdftotext -layout and rendered the four files with no text layer through pdf.js in a headless browser, which is how the right-of-way map duplicate, the RFP findings memorandum, the draft scope and one agenda were identified. Ran pairwise normalized-text similarity and token coverage across the cluster, then discarded three coverage results as artefacts after checking them against the sequence ratio. Compared all 20 checksums against the 1,612 checksummed inventory records. Paired agendas against meeting records by date and ran a recorded review for the one agenda with no matching record.",
 "classification_only": True,
 "shared_state_written": [],
 "measurement_trap": {
  "finding": "Token coverage badly over-calls duplication in a directory of slide presentations. Three files sit above 0.83 coverage inside the retained 86-page study while sharing almost no sequence with it: the November 2014 summary presentation at 0.9055 coverage and 0.106 sequence ratio, the project brochure at 0.9091 and 0.087, and the private landholder presentation at 0.8396 and 0.047.",
  "cause": "A slide deck's extracted text is only its headings. The November presentation yields 582 distinct tokens and the brochure 506, against the study's 3,027. A small corridor vocabulary sits almost entirely inside a large one about the same corridor without the documents being related at all.",
  "rule": "Never call a duplicate from coverage alone when the covered file's token count is an order of magnitude smaller than the container's. Check the sequence ratio, and where the file is visual, render it. This is the mirror image of the 2011 GO-bond finding, where coverage caught what hashing missed: coverage and sequence similarity each fail in opposite directions and both are needed."
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_only_by_rendering": 1,
  "false_positives_discarded": 3,
  "note": "The directory's one real duplicate is a scanned re-handout of a map whose other copy carries a text layer. Hashing cannot see it and text comparison cannot either, because the scan yields a single character. It was found by rendering. The three relationships that measurement did suggest were all false and are documented in measurement_trap."
 },
 "date_traps": {
  "count": 2,
  "detail": [
   "src-05705d25113d3f2e is filed as 11/12/2013 by both its filename and its inventory title. The sheet says Wednesday, November 20, 2013.",
   "The right-of-way map is dated by both copies' filenames to the meetings it was handed out at, 011514 and 04042014. The map's own printed date is DECEMBER 2013."
  ],
  "note": "This is the fifth directory in this run where a filename asserts a date the document contradicts. In this directory the pattern has a specific cause worth naming: handout filenames record the meeting, not the document."
 },
 "exhaustive_minutes_review": {
  "purpose": "The AGENTS.md missing-minutes agenda policy permits preserving an official agenda only after a recorded exhaustive official-source review finds no approved minutes. This is that record, for the November 20, 2013 first meeting.",
  "steps": [
   "Enumerated the whole directory: 20 files, of which four are agendas and three are meeting records. The three meeting records cover January 15, April 4 and June 27, 2014. Nothing covers November 2013.",
   "The January 15, 2014 record is headed \"Second Meeting\" and the June 27 record \"Fourth Meeting\", which fixes the November 20, 2013 meeting as the first and shows the committee numbered its meetings consecutively. A third meeting record is also absent from this directory.",
   "Searched the inventory for Paseo del Volcan steering committee material. Nothing outside this directory holds meeting records for this committee."
  ],
  "conclusion": "No minutes for the November 20, 2013 first meeting exist in any official source reachable from the City site or the inventory. The agenda carries a substantive running order naming the presenters.",
  "limit_stated_plainly": "The committee was convened by the Mid-Region Council of Governments, not by the City, so its authoritative minute book is MRCOG's rather than cabq.gov's and was not reached by this review. The numbering gap also shows at least one further meeting record is unpublished here. Nothing in an agenda shows whether the meeting took place or had a quorum. If held to a stricter standard this one record moves to requires human review and nothing else in the batch changes."
 },
 "integration_flags": [
  {"severity": "coverage-gap",
   "affects": ["the Paseo del Volcan corridor generally"],
   "finding": "Paseo del Volcan appears in the site's content exactly once, inside a description of an MRCOG appendix listing regional projects of special interest. Eleven records recommended here would be the corridor's first substantive presence, including the only corridor economic study, the only right-of-way status record, and the only Double Eagle II Airport development planning record in the inventory.",
   "recommended_action": "Consider a Paseo del Volcan Corridor subsection rather than scattering eleven records across three pages. A page-structure choice within existing pages, not a site-architecture change."},
  {"severity": "provenance",
   "affects": ["src-189c0a45bb72113c", "src-3924fb39a476b0a7", "src-fd2c4ff2f2681189", "src-05705d25113d3f2e", "src-4aaa2a918146e21c"],
   "finding": "Much of this directory is not City-authored. The steering committee was convened and minuted by the Mid-Region Council of Governments as the metropolitan planning organisation, and the right-of-way map was prepared for the New Mexico Department of Transportation by Parsons Brinckerhoff. The City published them; it did not write them.",
   "recommended_action": "Attribute each record to its actual author in any published description. The City page is the source location, not the provenance."},
  {"severity": "interest-disclosure",
   "affects": ["src-5b435ce5abe5a4c5", "src-4aaa2a918146e21c"],
   "finding": "The private landholder presentation recommended excluded was made by Western Albuquerque Land Holding and Ranch Joint Venture, and the right-of-way map recommended for addition names those same two companies as land dedicators at 315 and 178 acres. The parties advocating for the corridor are among the parties whose land it crosses.",
   "recommended_action": "That is a reason to retain the map, which records the interest, and to leave out the advocacy, which asserts a position. If the presentation is ever revisited, the interest must be stated alongside it."},
  {"severity": "follow-up",
   "affects": ["src-cea0004bcdaac447"],
   "finding": "The excluded RFP findings memorandum cites a Santolina Fiscal Impact Analysis dated May 14, 2013 with a projected net taxable value of $3,213,295,892 at full build-out. Santolina is a major Bernalillo County master plan and that analysis is not in the inventory.",
   "recommended_action": "Worth a targeted search in a later lane, as a County rather than City record."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "superseded": 0,
  "requires_human_review": 0
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 20 files are genuine PDFs by leading bytes. Four have no text layer and were rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": "All 11 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: "
                  f"{sum(r['size_bytes'] for r in approved):,} bytes. Two records dominate it: the west side open space presentation at 9,053,886 bytes and the corridor study at 4,563,767.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. The single duplicate row carries a canonical_id. The 11 approved rows each carry a title, a 20-to-50-word description, a proposed_canonical_page, and cross_listings where a second page applies; two carry a null date because the document prints none, and those must not be given an asserted date. One approved row is an agenda preserved under the missing-minutes policy and its title must keep the \"(approved minutes not located)\" qualifier; one is headed Meeting Notes by the committee and must not be titled minutes. Two records carry date traps recorded in date_traps and must be dated from the document rather than the filename or the inventory title. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
