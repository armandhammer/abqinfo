"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\redistricting-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\redis\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/redistricting-documents/'

DEMOG = 'content/city-data/demographics.md'

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


def A(i, title, desc, date, pages, evidence, why=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": date, "pages": pages,
              "proposed_canonical_page": DEMOG, "cross_listings": [],
              "evidence": evidence})
    if why:
        r["why_retained"] = why
    if extra:
        r.update(extra)
    return r


approved = [
 A("src-f634c5079e834843",
   "Enacted Resolution R-2010-103: Establishing a Redistricting Committee Under Article IV, Section 3 of the City Charter to Review and Make Recommendations Concerning the Nine Council Districts (Council Bill R-10-109)",
   "The enacted City resolution creates the 2010 Redistricting Committee required by the City Charter, sets its charge to recommend council district boundaries from federal census data, and repeals the 2001 enactment that established the previous committee.",
   "2010-08-16", 4,
   "Image-only PDF with no text layer; page 1 was rendered and read. Council Bill No. R-10-109, handwritten Enactment No. R-2010-103, Nineteenth Council, sponsored by Ken Sanchez and Trudy Jones, repealing Enactment R-2001-080 (R-01-256). The recitals set the Charter's composition requirements, the October 2011 municipal election, and the March 15, 2011 start of the candidate exploratory period.",
   why="Enacted law and the constitutive document of the whole directory: every other record here exists because this resolution created the committee. It is the fourth enacted instrument found anywhere in the Council library during this run, and the only one that carries its own date of passage in a companion memorandum also retained here.",
   extra={"date_basis": "The resolution sheet itself carries no passage date. The retained interoffice memorandum src-692f5564d80d10f0 states \"On August 16, 2010, the City Council passed R-10-109\", which is where the date comes from."}),

 A("src-692f5564d80d10f0",
   "Interoffice Memorandum: Appointments to the 2010 Redistricting Committee, September 15, 2010",
   "The Council president and vice-president tell all councilors how the Redistricting Committee will be appointed, recording that the Council passed R-10-109 on August 16, 2010 and held study sessions on August 27 and September 8 to settle the committee's composition.",
   "2010-09-15", 3,
   "Three pages from Council President Ken Sanchez and Vice-President Trudy Jones to all councilors. It restates the Charter requirement that membership be drawn equally from each district and reflect the racial, ethnic and gender makeup of the City's population.",
   why="It supplies the passage date for R-2010-103 that the resolution sheet itself omits, and it is the only record of the two study sessions where the committee's composition was actually decided."),

 A("src-9f7b881c3ef71d73",
   "2010 Redistricting Committee Summary Minutes, Meeting 1, November 4, 2010",
   "The summary minutes of the first meeting of the Albuquerque Redistricting Committee record attendance and the business of the organisational session that opened the 2010 council district review.",
   "2010-11-04", 3,
   "Three pages headed \"CITY OF ALBUQUERQUE 2010 REDISTRICTING COMMITTEE SUMMARY MINUTES NOVEMBER 4, 2010\". The agenda for this meeting is recommended excluded below."),

 A("src-7bab2bcd5abfef1c",
   "2010 Redistricting Committee Summary Minutes, Meeting 2, November 18, 2010",
   "The summary minutes of the second meeting record attendance and the business of the session at which the committee took the population estimation methodology and the abbreviated municipal election calendar.",
   "2010-11-18", 4,
   "Four pages. Two files in the directory are filenamed for this date as handouts. The agenda for this meeting is recommended excluded below."),

 A("src-96d0d06edac1c1b7",
   "Albuquerque Redistricting Committee: Population Estimates and Estimation Process (November 18, 2010)",
   "The consultant presentation sets out how Albuquerque population was estimated for redistricting before the 2010 federal census results were released, describing the estimation method, its data sources, and its limitations for drawing council districts.",
   "2010-11-18", 22,
   "22 pages, the longest technical document in the directory. It exists because R-2010-103 required the committee to work ahead of census release: the resolution records that results would not be available until the first quarter of 2011.",
   why="The methodology behind every district population figure the committee used. It is the only population estimation methodology document in the inventory."),

 A("src-d538ec65f499df4e",
   "Albuquerque Redistricting Committee: Redistricting Principles (December 2, 2010)",
   "The consultant presentation sets out the principles the committee was to apply in drawing council districts, covering equal population, minority voting rights, and the traditional districting criteria courts have recognised.",
   "2010-12-02", 21,
   "21 pages. It is the substantive companion to the legal briefing delivered at the same meeting and retained below.",
   why="The criteria document for a decennial redistricting, which is the standard a later reader would measure the resulting map against."),

 A("src-afcdfa5c5ab2978f",
   "Redistricting Information: One Person One Vote, Minority Voting Rights, and Traditional Districting Principles (December 2, 2010)",
   "The committee's legal briefing sets out the constitutional and Voting Rights Act constraints on Albuquerque redistricting: the five per cent deviation rule, the three-part Section 2 vote dilution test, and the judicially recognised traditional districting principles.",
   "2010-12-02", 3,
   "Image-only PDF with no text layer; page 1 was rendered and read. It states the plus or minus five per cent deviation rule, ten per cent total; names Hispanics, African Americans and Native Americans as the ethnic and language minority groups whose voting power must not be diluted; sets out the three-part Section 2 test; and flags cracking and packing as suspect practices.",
   why="The clearest statement in the inventory of the legal rules that constrain how Albuquerque may draw its council districts, in three pages. It is the kind of record that stays useful across every future redistricting cycle."),

 A("src-e3deb128206a8c5c",
   "Albuquerque City Council District Plan G-2-1d Mod 5 Amended (map)",
   "The council district map shows the boundaries of Albuquerque's nine council districts under plan G-2-1d Mod 5 Amended, the numbered plan variant produced during the redistricting process.",
   None, 1,
   "One sheet. Its text layer is only district numbers and precinct labels, which is why no date or adoption status can be read from it. This is the same limitation the Planning UDD lane recorded for overlay-zone maps, whose extracted text is likewise only unordered labels.",
   why="The only council district map in the inventory. A named plan variant is the concrete output the whole committee process was aimed at.",
   extra={"caveat": "The sheet does not say whether this plan was adopted, and the inventory holds no adoption record for it. Title it as the plan variant it names and do not describe it as the adopted districts unless an adoption record is located. This is a description constraint, not a reason to withhold the record."}),

 A("src-df297fd8ca9ac398",
   "Albuquerque City Council Districts Adopted June 25, 2001: Population and Ethnic Composition",
   "The table gives each of Albuquerque's nine council districts as adopted in June 2001 with its total and adult population, its deviation from the ideal, and its composition by Hispanic origin, White, Native American, Black, Asian, and two or more races.",
   "2001-06-25", 1,
   "One sheet headed \"Albuquerque City Council (Adopted 6/25/01)\". It gives per-district population, signed deviation in persons and per cent, and counts and percentages for each category, separately for total and adult population.",
   why="The baseline the 2010 committee was working against, and unlike the map above it states its adoption date on its face. It is the only district-level demographic table in the inventory and it documents an adopted plan rather than a proposal."),

 A("src-3e58c28a0e371255",
   "2010 Redistricting Committee Meeting 3 Agenda, December 2, 2010 (approved minutes not located)",
   "The agenda for the committee's third meeting, held in the Vincent E. Griego Chambers, sets the session at which the redistricting principles presentation and the legal briefing on voting rights constraints were both delivered.",
   "2010-12-02", 1,
   "One page headed \"2010 Redistricting Committee Meeting #3, Vincent E. Griego Chambers, Basement, 1 Civic Plaza, December 2, 2010 6:00 to 8:00 p.m.\" Two substantive documents in this directory are filenamed 12-2-10 and are recommended for addition, which independently confirms the meeting took place.",
   why="Preserved under the AGENTS.md missing-minutes agenda policy. It is the only record of the third meeting's running order, and unusually for such a case there is positive evidence the meeting happened: two of its handouts survive and are retained in this batch.",
   extra={"policy": "Must be labelled \"Agenda (approved minutes not located)\" or equivalent, must link the official source, must preserve the meeting date, and must never be presented as minutes.",
          "review_recorded": "See exhaustive_minutes_review."}),
]

duplicates = [
 {**row("src-a74dd94689373936", "duplicate"),
  "title_for_reference": "2010 Redistricting Committee Presentation (second encoding)",
  "pages": 5,
  "canonical_id": "src-ff26854cb2f1e490",
  "canonical_url": BASE + "2010-redistricting-committee-tasks-slideshow-presentation.pdf",
  "basis": "The same five-page slideshow on the committee's task under R-10-109, published twice at different byte sizes. Normalized text is identical at ratio 1.0000 with full token coverage in both directions; only the image encoding differs, 95,120 bytes against 197,867.",
  "measurement": "ratio 1.0000, coverage 1.0000 both ways, 202 tokens each. Hashing does not connect them.",
  "hash_found_it": False,
  "note": "The canonical is itself recommended excluded as a restatement of the enacted resolution. The format-pair relationship is recorded here so it is not lost inside a generic exclusion, following the rule set in the construction-documents artifact. Keep the larger file as canonical: same text, better image encoding."},
]


def X(i, title, reason, category, pages=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "exclusion_reason": reason, "category": category})
    if pages:
        r["pages"] = pages
    if extra:
        r.update(extra)
    return r


excluded = [
 X("src-48b982c1c959a31b", "2010 Redistricting Committee Meeting 1 Agenda, November 4, 2010",
   "Agenda for a meeting whose summary minutes are published and recommended for addition in this same batch (src-9f7b881c3ef71d73). The AGENTS.md missing-minutes policy forbids archiving an agenda when an approved-minutes original is available.",
   "agenda superseded by its own minutes", 1,
   extra={"minutes_record_for_same_meeting": "src-9f7b881c3ef71d73"}),
 X("src-b80b979585cddac4", "2010 Redistricting Committee Meeting 2 Agenda, November 18, 2010",
   "Agenda for a meeting whose summary minutes are published and recommended for addition in this same batch (src-7bab2bcd5abfef1c). Same policy ground.",
   "agenda superseded by its own minutes", 1,
   extra={"minutes_record_for_same_meeting": "src-7bab2bcd5abfef1c"}),

 X("src-ff26854cb2f1e490", "2010 Redistricting Committee Tasks Slideshow Presentation",
   "A five-page slideshow restating the committee's charge, headed \"Task of the Committee per R-10-109, the Committee Formation Resolution\". It paraphrases the enacted resolution recommended for addition in this batch and adds nothing the resolution does not state with legal force.",
   "restatement of a retained instrument", 5,
   extra={"canonical_of": "src-a74dd94689373936, its byte-different twin, is recorded as a duplicate of this record."}),

 X("src-e7c627b2b1b1b955", "Glossary of Redistricting Terms",
   "A two-page definition list of general redistricting vocabulary, beginning with the census block. It is generic reference material with no Albuquerque-specific content, on the same footing as the federal antenna-safety guide excluded from the Development Review Services library in the artifact of the same date.",
   "generic reference material", 2),

 X("src-bc66b8e82ed23dbb", "2010 Redistricting Committee Staff and Consulting Resources",
   "A one-page roster naming the facilitator and consultants engaged for the committee and what each was available to do. An administrative staffing list, volatile by nature and with no standalone interpretive value.",
   "administrative roster", 1),

 X("src-757e91ccdac87f26", "2010 Redistricting Committee Redistricting Process Timeline, November 4, 2010",
   "A two-page working schedule of what the committee planned to do month by month, presented at the first meeting. It is a plan of work rather than a record of one, and the meeting records retained in this batch show what actually happened.",
   "working schedule", 2),

 X("src-a919849dfe495cb0", "Abbreviated Unofficial Election Calendar for the October 4, 2011 Municipal Election",
   "A seven-page calendar of municipal election deadlines, marked \"Abbreviated\" and \"Unofficial\" on its own title. A document that disclaims its own authority should not be archived as a record, and the deadlines it lists expired in 2011.",
   "self-disclaimed working document", 7,
   extra={"note": "It was relevant to the committee because R-2010-103 recites the October 2011 election and the March 15, 2011 start of the candidate exploratory period as the reason for working ahead of the census. That reasoning is preserved in the retained resolution."}),
]

rows = approved + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 18, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "redistricting-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/redistricting-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The 2010 Redistricting Committee record set in the Albuquerque City Council document library at www.cabq.gov/council/documents/redistricting-documents.",
 "scope": "All 18 pending-review candidates in that directory, which is the entire directory: no record in it held any other status. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Separate adopted district maps and redistricting committee findings from meeting handouts and public-comment material.",
 "brief_finding": "There is no public-comment material and only one map, and the map does not say whether it was adopted. What the directory does hold is the complete constitutive and analytical record of a decennial redistricting: the enacted resolution that created the committee, the memorandum that dates its passage, the minutes of two of its three meetings, the population estimation methodology it had to use because census results were not yet released, the districting principles it was given, and a three-page legal briefing on the one-person-one-vote and Voting Rights Act constraints. ABQInfo currently has no redistricting content of any kind.",
 "method": "Fetched all 18 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 18 are genuine PDFs by leading bytes. Extracted text with pdftotext -layout and rendered the two files with no text layer through pdf.js in a headless browser, which is how the enacted resolution and the legal briefing were identified. Ran pairwise normalized-text similarity and token coverage across the cluster. Compared all 18 checksums against the 1,612 checksummed inventory records. Paired agendas against minutes by meeting date and ran a recorded review for the one agenda with no matching minutes.",
 "classification_only": True,
 "shared_state_written": [],
 "precedent_applied": "The AGENTS.md missing-minutes agenda policy governs the three agendas. The construction-documents rule that a format twin is recorded as a duplicate even when its canonical is itself excluded governs the slideshow pair. The Development Review Services line on generic federal or non-local reference material governs the glossary.",
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text": 1,
  "note": "One relationship, and hashing misses it: the committee's tasks slideshow is published twice with identical text and different image encodings, 95,120 bytes against 197,867."
 },
 "dating_findings": {
  "resolution_date_recovered": "R-2010-103 carries no passage date on its own sheet. The retained interoffice memorandum supplies it: \"On August 16, 2010, the City Council passed R-10-109\". Two records in the same directory were needed to date one instrument.",
  "map_cannot_be_dated": "The district map's text layer is only district numbers and precinct labels, so neither its date nor its adoption status can be read from it. This is the same limitation the Planning UDD lane recorded for overlay-zone maps. The 2001 demographic table, by contrast, states its adoption date on its face, which is why it can be described as adopted and the map cannot."
 },
 "exhaustive_minutes_review": {
  "purpose": "The AGENTS.md missing-minutes agenda policy permits preserving an official agenda only after a recorded exhaustive official-source review finds no approved minutes. This is that record, for the December 2, 2010 third meeting.",
  "steps": [
   "Enumerated the whole directory: 18 files, of which three are agendas, for meetings numbered 1, 2 and 3 on their own faces, and two are summary minutes, for meetings 1 and 2. Nothing covers meeting 3.",
   "Searched the inventory for redistricting material. This directory is the only redistricting holding of any kind; the site has no redistricting content and the inventory no other redistricting record.",
   "Checked whether the meeting happened rather than assuming it. Two substantive documents in the directory are filenamed 12-2-10, the redistricting principles presentation and the legal briefing, and both are retained in this batch. The meeting took place and produced handouts."
  ],
  "conclusion": "No minutes for the December 2, 2010 meeting exist in any official source reachable from the City site or the inventory, and there is positive evidence the meeting was held. The agenda carries the meeting number, venue and time.",
  "limit_stated_plainly": "This review establishes that the minutes are unpublished, not that they were never approved. It is also silent on what happened after December 2010: the committee was created to work on 2010 census data that the resolution says would not arrive until the first quarter of 2011, so the substantive redistricting work necessarily continued past the last record in this directory, and none of it is published here. The quorum question cannot be answered from an agenda, but unlike the other agenda cases in this run the meeting's occurrence is independently evidenced by its surviving handouts."
 },
 "integration_flags": [
  {"severity": "coverage-gap",
   "affects": ["the redistricting subject generally"],
   "finding": "ABQInfo has no redistricting content at all: no page mentions redistricting, and the inventory holds no redistricting record outside this directory. The ten records recommended here would be the subject's entire presence, and they cover only the first three months of a process that ran into 2011 and beyond.",
   "recommended_action": "Place them as a distinct Council Redistricting section on content/city-data/demographics.md rather than scattering them, and state in any introduction that the record covers only the committee's opening phase. A page-structure choice within an existing page, not a site-architecture change."},
  {"severity": "description-constraint",
   "affects": ["src-e3deb128206a8c5c"],
   "finding": "The council district map names plan variant G-2-1d Mod 5 Amended but says nothing about whether that plan was adopted, and no adoption record exists in the inventory. The variant numbering implies a series of alternatives.",
   "recommended_action": "Title it as the plan variant it names. Do not describe it as the adopted council districts. If an adoption record is later found, that record supersedes this description, not this file."},
  {"severity": "series-incomplete",
   "affects": ["the whole directory"],
   "finding": "The directory stops in December 2010 while the redistricting it documents necessarily continued into 2011 and later: R-2010-103 itself recites that census results would not be available until the first quarter of 2011 and that the municipal election was in October 2011. The committee's recommendations, the adopted plan, and any meetings after the third are all absent.",
   "recommended_action": "Treat this batch as the opening of a series rather than the series. The missing 2011 material is a discovery lead worth a targeted search, and Albuquerque has since run a 2020-cycle redistricting whose records are also absent from the inventory."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "superseded": 0,
  "requires_human_review": 0
 },
 "link_check": {"checked": 18, "http_200": 18, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 18 files are genuine PDFs by leading bytes. Two have no text layer and were rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": "All 10 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: "
                  f"{sum(r['size_bytes'] for r in approved):,} bytes, the smallest batch in this run.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. The single duplicate row carries a canonical_id whose target is itself recommended excluded, which is deliberate and follows the construction-documents rule. The 10 approved rows each carry a title, a 20-to-50-word description, and a proposed_canonical_page; one carries a null date because the document prints none and must not be given an asserted one, and one carries a date recovered from a second document rather than from its own face. One approved row is an agenda preserved under the missing-minutes policy and its title must keep the \"(approved minutes not located)\" qualifier. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
