"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-5-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d5\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/councilor-district-5-documents/'

ROADS = 'content/transportation/roadway-projects/_index.md'
SAFETY = 'content/transportation/safety-crash-data.md'
BUDGET = 'content/city-data/budget-spending.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
MAGIC = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")


def kind(i):
    return "PDF" if MAGIC[i] == '25504446' else "OLE2 Word document"


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC, "content_kind": kind(i)}
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
 A("src-fc250f15df2ab028",
   "Enacted Ordinance O-2014-005: Approving a Project Involving Eclipse Aerospace, Inc. Under the Local Economic Development Act (Council Bill O-14-4)",
   "The enacted City ordinance approves a Local Economic Development Act project with Eclipse Aerospace to support continued aircraft assembly and administrative operations in Albuquerque, authorising a project participation agreement and making the findings the Act requires.",
   "2014", 7,
   "Image-only PDF with no text layer; page 1 was rendered and read. It carries Council Bill No. O-14-4 and the handwritten Enactment No. O-2014-005, Twenty-First Council, sponsored by Rey Garduno and Dan Lewis, and recites Sections 5-10-1 through 5-10-13 NMSA 1978 and the City's implementing LEDA ordinance F/S O-04-10.",
   BUDGET,
   why="Enacted law, and the only copy in the inventory. It is a rare find in this tree. Across the Council library triaged in this run, thirty-five legislative files carry a blank enactment number, and only three carry a real one: this ordinance, R-2010-056 below, and R-2018-081, which survives only because it was bound as Appendix 1 inside a Council staff report rather than published on its own.",
   extra={"companion": "src-26ac11ece2bef98d is Councilor Lewis's press release announcing support for the same bill. The press release is recommended excluded; the ordinance is the record."}),

 A("src-77ded92dfd05478c",
   "Enacted Resolution R-2010-056: Creating a Traffic and Pedestrian Safety Project on Rainbow Boulevard and Universe Boulevard (Council Bill C/S R-10-44)",
   "The enacted City resolution creates a traffic and pedestrian safety project on Rainbow and Universe Boulevards, directing lighting, safety, and street improvements and appropriating funds from the Transportation Infrastructure Tax Fund 340 for the school corridor.",
   "2010", 3,
   "Image-only PDF with no text layer; page 1 was rendered and read. Council Bill No. C/S R-10-44, handwritten Enactment No. R-2010-056, Nineteenth Council, sponsored by Dan Lewis. The recitals name Tierra Antigua Elementary, Tony Hillerman Middle School, Volcano Vista High School and the APS sports complex as the traffic generators, and cite unsignalized crossings and a lack of roadway lighting.",
   ROADS,
   why="Enacted law creating a named, funded City project. It also closes a loop opened by the council-documents artifact of the same date, which flagged that a public meeting flyer announced a Rainbow Boulevard Traffic Calming and Pedestrian Safety Study the archive did not hold. This resolution is that project's legislative origin.",
   cross=[{"page": SAFETY, "section": "School Transportation Safety", "reason": "The resolution's entire justification is student pedestrian and driver safety at three named schools, which is what that section covers."}]),

 A("src-4347bb9af15c89ba",
   "Councilor Dan Lewis Request for Investigation into the Redflex Traffic Systems Contract With the City of Albuquerque, January 24, 2014",
   "The District 5 councilor formally asks the City Inspector General and the Director of Internal Audit to investigate the procurement process behind Albuquerque's original Redflex red-light camera contract, following press reports of alleged misconduct in the company's municipal contracting.",
   "2014-01-24", 1,
   "Image-only PDF with no text layer; rendered and read. Addressed to Peter Pacheco, Office of Inspector General, and Deborah Yoshimura, Director of Internal Audit, copied to City Councilors. It cites a Chicago Tribune report of January 23, 2014 and dates the City's Redflex contract to approximately 2005.",
   SAFETY,
   why="A formal oversight request to two named City accountability offices, not constituent correspondence or an announcement. It is a dated primary record of how Albuquerque's red-light camera programme came under scrutiny, and the inventory holds nothing else on the Redflex procurement.",
   extra={"related": "The Council library has a separate red_light_cameras collection page, src-c846ef71accb706a, which is excluded as a landing page in the council-documents artifact of the same date. This letter is the substantive record behind that topic."}),
]

duplicates = [
 {**row("src-bdf2981b4899255b", "duplicate"),
  "title_for_reference": "DOJ Findings and Recommendations (scanned copy)",
  "canonical_id": "src-5961fb8a4db0fb4e",
  "canonical_url": "https://www.cabq.gov/council/documents/police-oversight-task-force-documents/140410DOJAPDFindingsLetter.pdf",
  "pages": 48,
  "basis": "The same United States Department of Justice Civil Rights Division findings letter on the Albuquerque Police Department of April 10, 2014, published a second time in a different Council directory. This copy is a 48-page scan with no text layer at 4,283,835 bytes; the canonical is born-digital, 46 pages, 242,627 bytes, with a full text layer. Keep the born-digital copy: it is searchable and one eighteenth the size.",
  "measurement": "Neither hashing nor text comparison could connect these: the bytes differ completely and this copy yields no extractable text at all. Page 1 was rendered and read, confirming the identical letter to Mayor Richard J. Berry under 42 U.S.C. Section 14141.",
  "hash_found_it": False,
  "note": "This relationship was predicted by the police-oversight-task-force artifact of the same date and is confirmed here."},

 {**row("src-7ca564066d19954f", "duplicate"),
  "title_for_reference": "Lewis additional info.pdf (second copy)",
  "canonical_id": "src-a4e93912f58bcb5d",
  "canonical_url": BASE + "1lewis_additional_info.pdf",
  "pages": 4,
  "basis": "Byte-identical to the copy published one directory entry above it under a leading-1 filename: same 4 pages, same size, same SHA-256. The City published the same file twice.",
  "measurement": "Identical SHA-256 a4c50c85f6943150ac27040a75cc9ed95673c44e0e2c7c7db228d2d4f12efbd3. The only byte collision in this cluster.",
  "hash_found_it": True,
  "note": "The leading-1 convention here marks a duplicate upload, not an earlier version. That is the opposite of the 2011 GO-bond directory, where a leading 1 marked an earlier version of a materially different document. Do not generalise the convention across City libraries."},
]


def R(i, draft_title, pages, question, why, evidence, date=None):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why,
              "evidence": evidence})
    if date:
        r["date"] = date
    return r


ENACT_Q = "Locate the enacted instrument for this bill before any archival or visible use, and decide whether ABQInfo carries pre-enactment bill versions at all."
ENACT_WHY = ("The document carries ENACTMENT NO. blank on its face, so it is the version considered "
             "rather than the law. The checkpoint holds two standing blockers on exactly this: isolated "
             "legislative amendment and substitute files must have their authoritative enacted packages "
             "resolved before archival or visible use, and a non-enacted version must not be archived or "
             "presented as enacted. The council-documents artifact of the same date held seven substitute "
             "bill texts on the same ground. This directory makes the point sharply: two of its legislative "
             "files do carry enactment numbers and are recommended for addition, and these do not.")

rhr = [
 R("src-1288d4b8b7490606",
   "Council Bill R-09-1: Creating an Unser Boulevard Extension Project, Compass Drive to Lyons Boulevard, Appropriating Funds in the Transportation Infrastructure Tax Fund 340",
   None, ENACT_Q,
   ENACT_WHY + " This one is worth resolving first: the site already carries an Unser Boulevard and Paseo del Norte project section on content/transportation/roadway-projects/_index.md, so an enacted version would have an immediate home.",
   "Word document, not a PDF. Nineteenth Council, sponsored by Dan Lewis, enactment number blank. The recitals argue that Coors Boulevard is the only north-south arterial alternative to Interstate 25 for west side residents and that completing the Unser corridor would relieve pressure on both and on the Interstate 25 and Paseo del Norte interchange."),

 R("src-16da4791a0edb197",
   "Council Bill F/S O-08-35: Amending Section 14-14-5-3 ROA 1994, a Portion of the Subdivision Ordinance, to Require Certain Notice and Approval",
   None, ENACT_Q, ENACT_WHY,
   "Eighteenth Council, sponsored by Cadigan, enactment number blank. A floor substitute amending the Subdivision Ordinance notice and approval requirements."),

 R("src-338b0d72594a0aad",
   "Council Bill F/S R-10-58: Appropriating Funds for Operating the Government of the City of Albuquerque for Fiscal Year 2011 (Lewis floor substitute, clean copy)",
   20, ENACT_Q,
   ENACT_WHY + " This is also the largest single piece of legislation in the directory, a whole fiscal-year operating budget, so the gap between the substitute and whatever passed could be substantial.",
   "Image-only PDF with no text layer; identified by rendering its redline twin. Twenty pages, Nineteenth Council, sponsored by Dan Lewis, enactment number blank.",
   date="2010"),

 R("src-a9d18b1ea8963cad",
   "Council Bill F/S R-10-58: Fiscal Year 2011 Operating Budget (Lewis floor substitute, redline copy)",
   21, ENACT_Q,
   ENACT_WHY + " The redline and clean copies are the same instrument in two presentations, one page apart, and must be decided together: if the substitute is retained at all, the redline is the more informative of the two because it shows what Councilor Lewis proposed to change.",
   "Image-only PDF; page 1 was rendered and read. Twenty-one pages. The title line carries the bracketed insertion \"[+STATING THE CITY COUNCIL'S INTENT WITH REGARD TO THE WAGE DECREASES+]\", and Section 1 shows the operating reserve changing from $37,926,000 to $37,935,000. Enactment number blank.",
   date="2010"),

 R("src-a4e93912f58bcb5d",
   "Graduated Wage Cut Scale, Lewis Budget Substitute (supporting exhibit to F/S R-10-58)",
   4, "Decide with the two floor-substitute copies above; this exhibit has no meaning apart from them.",
   "A supporting exhibit to a bill whose enacted status is unresolved. It cannot be retained if the substitute it supports is not, and it should not be excluded separately if the substitute is retained.",
   "Image-only PDF; page 1 was rendered and read. It tabulates a graduated municipal pay cut by salary band, from no cut below $30,000 up to 6.5 per cent above $125,001, with a stated weighted average effective cut of 2.14 per cent. src-7ca564066d19954f is a byte-identical second copy and is recorded as a duplicate of this record.",
   date="2010"),
]


def X(i, title, reason, category, pages=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "exclusion_reason": reason, "category": category})
    if pages:
        r["pages"] = pages
    if extra:
        r.update(extra)
    return r


AMEND = ("A committee amendment sheet: a numbered list of line edits against a bill text it does not "
         "contain, of the form \"On page 4, line 1, replace $1,500,000 with $3,000,000\". Excluded as a "
         "non-self-contained legislative fragment, the category decision recorded in the council-documents "
         "artifact of the same date, which covers at least 57 such files across this tree.")

PRESS = ("A District 5 councilor's press release. It announces a position or an event rather than "
         "recording a City action, and the record of the action, where one exists, is held separately. "
         "The inventory already carries a terminal exclusion for a Council news item of this kind, "
         "src-0b20b31b78ea3865.")

excluded = [
 X("src-a09a7081a2d10b09", "Committee Amendment 1 to C/S R-08-182 (Cadigan), March 12, 2009",
   AMEND, "council legislative amendment sheet", 2,
   extra={"identifies": "Committee of the Whole, March 12, 2009. Fourteen numbered edits rewriting capital appropriation figures, ending \"Recalculate and change all subtotals and totals accordingly\"."}),
 X("src-652537178b2679cd", "Committee Amendment 2 to C/S R-08-182 (Cadigan), Storehouse",
   AMEND, "council legislative amendment sheet", 1),

 X("src-26ac11ece2bef98d", "Press Release: Councilor Dan Lewis Announces Support for O-14-4, Eclipse Aerospace, February 19, 2014",
   PRESS, "councilor press release",
   extra={"note": "The bill it supports, enacted as O-2014-005, is recommended for addition in this batch. The ordinance is the record; the announcement is not."}),
 X("src-38a1243f852e6b87", "Press Release: Councilor Dan Lewis Responds to the Department of Justice Findings, April 11, 2014",
   PRESS, "councilor press release",
   extra={"note": "The findings it responds to are the DOJ letter recommended for addition in the police-oversight artifact of the same date. This is the closest call in the batch: it is a same-day reaction by the chair of the Council Committee of the Whole to the most consequential document in the archive. It is still an announcement rather than a City action, and the Council's actual response is the ordinance amendment work recorded in the task force directory."}),
 X("src-ab90bbed4d6998b9", "Press Release: Paradise Hills Little League Fields Dedication, March 28, 2014",
   PRESS, "councilor press release"),
 X("src-fbd917f968b7e407", "Press Release: Hailey Ratliff Trails Park Dedication, February 14, 2014",
   PRESS, "councilor press release",
   extra={"note": "It records that a City park was named for a Tony Hillerman Middle School student killed while riding her bicycle to school. That naming is a durable fact worth carrying as editorial context on a parks or school-safety page; the press release is not the record of it."}),
 X("src-3f3e90ba56e359ca", "Press Release: Legislation to Restructure the Albuquerque Downtown Business Improvement District, February 28, 2014",
   PRESS, "councilor press release",
   extra={"note": "It announces a bill to be introduced at the March 3, 2014 Council meeting tying the Downtown BID's five-year review to service delivery. The bill itself is not in this directory."}),

 X("src-10f0d9df6be21453", "Film Notice for Tony Hillerman Elementary School, February 27, 2014",
   "A commercial production company's neighborhood notice that filming would occur near a school, published on the councilor's page as a courtesy. Not a City record, not a plan, project record, or adopted standard, and spent the moment the shoot ended.",
   "third-party notice"),

 X("src-47bf834e27b251e6", "Letter to the Ventana Ranch Neighborhood Association Regarding Stop Signs at Ventana Road and Universe Boulevard, March 7, 2014",
   "Constituent correspondence answering a neighborhood association about stop signs. It is a councilor's reply rather than a City decision record, and the decisions it relays are recorded elsewhere.",
   "constituent correspondence",
   extra={"facts_worth_keeping": "It states two concrete commitments that are useful as editorial context even though the letter is not archived: the Department of Municipal Development agreed to reinstall the removed stop signs at Ventana Road and Universe Boulevard until a new signal was in place, and the 2013 General Obligation Bond cycle funded a fully signalized intersection at Irving and Universe. The inventory already holds an extensive validated 2013 GO bond record set against which that second claim can be checked."}),

 X("src-61ae66da543b1909", "Donate Life Proclamation, May 3, 2010",
   "A ceremonial Council proclamation recognising organ and tissue donation. Proclamations carry no legal effect and record no City action beyond the recognition itself.",
   "ceremonial proclamation",
   extra={"note": "Word document, not a PDF."}),
]

rows = approved + duplicates + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "councilor-district-5-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-5-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The District 5 councilor's document collection in the Albuquerque City Council library at www.cabq.gov/council/documents/councilor-district-5-documents, covering the terms of Councilor Dan Lewis.",
 "scope": "All 20 pending-review candidates in that directory, which is the entire directory: no record in it held any other status. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Resolve the cross-directory DOJ findings-letter duplicate flagged by the police-oversight artifact, and separate substantive district records from constituent notices.",
 "brief_finding": "The duplicate is confirmed and the separation holds, but the directory's real value turned out to be legislative rather than constituent. Two of its files carry an actual enactment number, which almost nothing else triaged in this tree does: Ordinance O-2014-005 on the Eclipse Aerospace economic development project, and Resolution R-2010-056 creating the Rainbow and Universe Boulevard traffic and pedestrian safety project. The second one closes a loop the council-documents artifact opened hours earlier, when a public meeting flyer was found announcing a Rainbow Boulevard study the archive did not hold.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each. Checked leading bytes: 18 PDFs and 2 Word documents. Eleven of the eighteen PDFs carry no text layer at all, so nine were rendered page by page through pdf.js in a headless browser and read, which is how both enacted instruments, the Redflex investigation request, the budget substitute and its wage-cut exhibit were identified. Extracted text with pdftotext -layout and antiword for the rest. Compared all 20 checksums against the 1,612 checksummed inventory records and against each other. Fetched nothing outside the cluster: the cross-directory duplicate was settled against measurements already taken in the police-oversight lane.",
 "classification_only": True,
 "shared_state_written": [],
 "image_only_records": {
  "count": 11,
  "share_of_cluster": "55 per cent",
  "note": "More than half this directory is scanned paper with no text layer, the highest proportion of any cluster triaged in this run. Every record recommended for addition here is one of them. A pipeline that triages on extracted text would have classified this directory as almost empty and left its two enacted instruments pending indefinitely.",
  "ids": ["src-338b0d72594a0aad", "src-4347bb9af15c89ba", "src-47bf834e27b251e6", "src-652537178b2679cd",
          "src-77ded92dfd05478c", "src-7ca564066d19954f", "src-a09a7081a2d10b09", "src-a4e93912f58bcb5d",
          "src-a9d18b1ea8963cad", "src-bdf2981b4899255b", "src-fc250f15df2ab028"]
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 1,
  "relationships_found_only_by_rendering": 1,
  "note": "The cross-directory DOJ duplicate is invisible to every automated method available in this project. The two copies share no bytes, so hashing fails; this copy yields no extractable text at all, so normalized-text and token-coverage comparison fail too. It was settled by rendering page 1 and reading it. Any future claim that a directory holds no duplicates should state whether its image-only records were rendered."
 },
 "integration_flags": [
  {"severity": "closes-a-lead",
   "affects": ["src-77ded92dfd05478c", "src-6db0397455652054"],
   "finding": "The council-documents artifact of the same date excluded a public meeting flyer for a Rainbow Boulevard Traffic Calming and Pedestrian Safety Study and recorded that the study itself was nowhere in the inventory. Enacted Resolution R-2010-056 in this directory is that project's legislative origin: it creates the traffic and pedestrian safety project on Rainbow and Universe Boulevards and appropriates the Transportation Infrastructure Tax Fund 340 money for it.",
   "recommended_action": "The study document is still missing and remains worth a targeted search. The resolution supplies the project name, the funding source and the date to search on."},
  {"severity": "convention",
   "affects": ["src-a4e93912f58bcb5d", "src-7ca564066d19954f"],
   "finding": "A leading 1 on a filename means a duplicate upload in this directory (1lewis_additional_info.pdf is byte-identical to lewis_additional_info.pdf), where in the 2011 general obligation bond directory the same convention marked a materially different earlier version.",
   "recommended_action": "Do not carry a filename convention across City libraries. Measure each directory."},
  {"severity": "blocker-consistent",
   "affects": ["src-1288d4b8b7490606", "src-16da4791a0edb197", "src-338b0d72594a0aad", "src-a9d18b1ea8963cad", "src-a4e93912f58bcb5d"],
   "finding": "Five files are pre-enactment legislation or its supporting exhibit, all with the enactment number blank, held under the two standing checkpoint blockers. They should be decided as one group, and the three F/S R-10-58 records as one instrument.",
   "recommended_action": "Resolve R-09-1 first: the site already has an Unser Boulevard and Paseo del Norte section on the roadway projects page, so an enacted version has an immediate home. Note that the enacted-versus-not question is now answerable in this tree, because this directory proves the City does publish enacted instruments with their enactment numbers written on them."},
  {"severity": "editorial",
   "affects": ["src-fbd917f968b7e407", "src-47bf834e27b251e6"],
   "finding": "Two excluded records carry durable facts worth keeping as editorial context even though the documents themselves are not archived: a City park was named for Hailey Ratliff, a Tony Hillerman Middle School student killed riding her bicycle to school; and the 2013 General Obligation Bond cycle funded a fully signalized intersection at Irving and Universe Boulevards.",
   "recommended_action": "Neither needs an inventory record. Both are checkable against the validated 2013 GO bond set already held."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "superseded": 0
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "18 PDFs and 2 OLE2 Word documents by leading bytes; both Word files are published with a .doc extension that matches."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": "All 3 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: "
                  f"{sum(r['size_bytes'] for r in approved):,} bytes, a small batch. All three are scans with no text layer, so any future full-text search over the archive will not reach them without optical character recognition; that is a property of the City's originals, not something archiving changes.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Both duplicate rows carry a canonical_id; one resolves outside this cluster to src-5961fb8a4db0fb4e in the police-oversight directory, so integrate the two artifacts together. The 3 approved rows each carry a title, a 20-to-50-word description, a date, a proposed_canonical_page, and a cross_listing where a second page applies. Five rows are requires human review under the standing enactment blockers and three of those are one instrument in two presentations plus its exhibit. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
