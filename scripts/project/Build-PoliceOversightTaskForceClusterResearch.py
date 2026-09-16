"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\police-oversight-task-force-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\potf\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/police-oversight-task-force-documents/'

SAFETY = 'content/city-data/public-safety-data.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")

REPORT = 'src-f4204196f921104e'


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
              "proposed_canonical_page": SAFETY, "cross_listings": [],
              "evidence": evidence})
    if why:
        r["why_retained"] = why
    if extra:
        r.update(extra)
    return r


approved = [
 A(REPORT,
   "Report on the Activities of the Ad Hoc Police Oversight Task Force, Prepared for the City Council in Conformance With Resolution 13-143 (January 31, 2014)",
   "The task force's complete final report to the Albuquerque City Council sets out its statement of principles, its findings on the civilian police oversight process, and its recommendations for amending the Police Oversight Ordinance, with the supporting record appended.",
   "2014-01-31", 238,
   "238 pages and 17,608,309 bytes, by far the largest record in the directory. Measured token coverage establishes it as the canonical package: the standalone statement of principles and the final recommendations are each 1.0000 contained in it, the report draft is 1.0000 contained, the January 15 draft recommendations 0.9776, the Goal 3 substitute 0.9663, the cover memorandum 0.9557, and the cover-letter handout 0.9528.",
   why="The canonical original of nine other files in this directory. Under the AGENTS.md rule, retain one canonical original and document the component relationships rather than archiving every extract separately."),

 A("src-5961fb8a4db0fb4e",
   "United States Department of Justice Civil Rights Division Findings Letter on the Albuquerque Police Department, April 10, 2014",
   "The federal findings letter reports reasonable cause to believe the Albuquerque Police Department engages in a pattern or practice of excessive force including deadly force, identifies structural deficiencies in oversight, training, and policy, and sets out remedial measures.",
   "2014-04-10", 46,
   "46 pages addressed to Mayor Richard J. Berry from the Office of the Assistant Attorney General, Civil Rights Division, under the Violent Crime Control and Law Enforcement Act of 1994, 42 U.S.C. Section 14141.",
   why="A federal publication, but one entirely about Albuquerque: it is the single document that reshaped APD oversight and the reason the ordinance amendments in this directory were written. This is the distinction applied when the Federal Communications Commission antenna-safety guide was excluded from the Development Review Services library in the artifact of the same date: a federal document with no Albuquerque-specific content is out, a federal finding about an Albuquerque department is in.",
   extra={"cross_directory_note": "A second copy exists outside this cluster; see integration_flags."}),

 A("src-8fa6fb11a3c5125b",
   "City of Albuquerque and Albuquerque Police Officers Association Collective Bargaining Agreement, Effective July 16, 2014 to July 16, 2015",
   "The collective bargaining agreement between the City and the police officers' union sets the terms governing Albuquerque police employment for the 2014 to 2015 term, including the disciplinary and investigatory provisions that constrain civilian oversight.",
   "2014-07-16", 50,
   "Image-only PDF with no text layer; the cover was rendered and read. It carries a 2014-2015 tab and the stamp \"CITY OF ALBUQUERQUE OFFICE OF ADMIN HEARINGS JUL 16 2014\".",
   why="The union contract is the document that determines what a civilian oversight body can and cannot do about police discipline, which is why the task force's own library holds it. It is the only copy in the inventory.",
   extra={"currency_warning": "This term expired on July 16, 2015. The title must carry the exact term so no reader takes it as the current agreement, and it must never be presented as in force."}),

 A("src-acac2ea782e05c6d",
   "Police Oversight Task Force Summary Minutes, January 8, 2014",
   "The task force's summary minutes record attendance and the business transacted at its January 8, 2014 meeting as it worked toward recommendations for amending the Albuquerque Police Oversight Ordinance.",
   "2014-01-08", 3,
   "Three pages headed \"Summary Minutes\", listing members present and Council staff present."),

 A("src-eafbf706ed009dcc",
   "Police Oversight Task Force Summary Minutes, January 15, 2014",
   "The task force's summary minutes record attendance and business at its January 15, 2014 meeting, the session that produced the dated draft recommendations work product also held in this directory.",
   "2014-01-15", 2,
   "Two pages headed \"Summary Minutes\". The draft recommendations src-834a319683f40c09 are stamped \"as of 1/15/14\", tying them to this meeting."),

 A("src-d59b9b37da75fde5",
   "Police Oversight Task Force Summary Minutes, January 21, 2014",
   "The task force's summary minutes record attendance and business at its January 21, 2014 meeting, at which a substitute text for Goal 3 on the composition of the civilian oversight board was tabled.",
   "2014-01-21", 2,
   "Two pages headed \"Summary Minutes\". The Goal 3 substitute src-e58c5af13f0ef4e0 is dated 1-21-14, tying it to this meeting. The agenda for the same meeting is recommended excluded below."),

 A("src-1fb997ce90184cb5",
   "Police Oversight Task Force Summary Minutes, January 29, 2014",
   "The task force's summary minutes record attendance and business at its January 29, 2014 meeting, the working session two days before the final report, at which members went through the recommendations line by line.",
   "2014-01-29", 4,
   "Four pages headed \"Summary Minutes\", naming members and Council staff present including Frances Armijo and Stephanie Yara. Three handouts in this directory are filenamed for this date. The agenda for the same meeting is recommended excluded below."),

 A("src-f44c5eec8b947674",
   "Police Oversight Task Force Agenda, August 6, 2014 (approved minutes not located)",
   "The task force's published agenda sets out a final review of seven specific Police Oversight Ordinance amendment recommendations, covering board size, member selection and removal, subject matter experts, access to investigative files, and selection of the independent review officer.",
   "2014-08-06", 1,
   "One page with a substantive numbered business list, not a bare notice. Item 4 enumerates seven lettered topics from the number of oversight board members through the selection, retention and removal of the review officer. The agenda notes that public comment would not be taken at this meeting.",
   why="Preserved under the AGENTS.md missing-minutes agenda policy. It is the only record of the task force's work after January 2014, showing the seven questions still open seven months later.",
   extra={"policy": "Must be labelled \"Agenda (approved minutes not located)\" or equivalent, must link the official source, must preserve the meeting date, and must never be presented as minutes or as a substitute for them.",
          "review_recorded": "See exhaustive_minutes_review."}),
]


def S(i, canonical_id, title, basis, measurement, immediate=None):
    r = row(i, "superseded")
    r.update({"title_for_reference": title, "canonical_id": canonical_id,
              "canonical_url": IDX[canonical_id].get('direct_file_url') or IDX[canonical_id].get('source_url'),
              "basis": basis, "measurement": measurement, "hash_found_it": False})
    if immediate:
        r["immediate_successor"] = immediate
    return r


superseded = [
 S("src-834a319683f40c09", REPORT,
   "Police Oversight Task Force DRAFT Recommendations, Work Product as of January 15, 2014",
   "A dated working draft of the recommendations, marked DRAFT on its face and stamped \"(as of 1/15/14)\". It was superseded twice over within sixteen days, first by the January 31 final recommendations and then by the final report that contains them.",
   "Token coverage 0.9776 inside the retained final report and 0.8590 inside the January 31 final recommendations; normalized-text similarity is low in both cases because the recommendations were substantially rewritten, which is what makes this a version rather than a component.",
   immediate="src-b4b2a26ac036021a"),

 S("src-e58c5af13f0ef4e0", REPORT,
   "Police Oversight Task Force, Substitute for Goal 3, January 21, 2014",
   "A single-goal substitute text tabled at the January 21 meeting, proposing that the oversight board be broadly representative of the community, balanced geographically and across stakeholders, and collectively hold a broad range of skills and experience. It was absorbed into the final recommendations.",
   "Token coverage 0.9663 inside the retained final report and 0.8652 inside the January 31 final recommendations.",
   immediate="src-b4b2a26ac036021a"),

 S("src-ae7ae3ce5e1f23f8", REPORT,
   "Police Oversight Task Force Final Recommendations, Updated",
   "Despite the word \"updated\" in its filename this is the earlier of the two final-recommendations documents, not the later one. It lacks the Statement of Principles that section A of the January 31 document carries, and its text is almost wholly contained in that document.",
   "Against the January 31 recommendations src-b4b2a26ac036021a: normalized-text similarity 0.6234 with token coverage 0.9944 of this file inside it and only 0.8750 the other way, so the January 31 document is the superset. Token coverage inside the retained final report is 1.0000.",
   immediate="src-b4b2a26ac036021a"),

 S("src-eda751586522df88", REPORT,
   "Report on the Activities of the Ad Hoc Police Oversight Task Force, Draft 1 (handout, January 29, 2014)",
   "A fifteen-page draft of the same report, distributed as a handout at the January 29 meeting two days before the final version. Its filename says \"Handout 01292014\" on its face.",
   "Token coverage 1.0000 inside the retained 238-page final report; the final report is roughly ten times longer in normalized characters, 352,150 against 36,009."),

 S("src-7e6495cf09df9304", REPORT,
   "Police Oversight Task Force Cover Letter, final draft (handout, January 29, 2014)",
   "A draft of the transmittal letter to Council President Ken Sanchez, distributed as a handout at the January 29 meeting. The letter actually sent is the interoffice memorandum src-2a426f210dd181dd, which is itself a component of the retained final report.",
   "Against the sent memorandum: normalized-text similarity 0.3008 with token coverage 0.8868 of this draft inside it. Token coverage inside the retained final report is 0.9528.",
   immediate="src-2a426f210dd181dd"),
]


def D(i, title, basis, measurement):
    r = row(i, "duplicate")
    r.update({"title_for_reference": title, "canonical_id": REPORT,
              "canonical_url": IDX[REPORT].get('direct_file_url'),
              "basis": basis, "measurement": measurement, "hash_found_it": False})
    return r


duplicates = [
 D("src-3ead951a710687fa",
   "Police Oversight Task Force Statement of Principles",
   "A one-page extract of the statement of principles, published separately. It is section A of the January 31 final recommendations and appears verbatim inside the retained final report.",
   "Token coverage 1.0000 inside the final recommendations and 1.0000 inside the retained final report."),

 D("src-b4b2a26ac036021a",
   "Police Oversight Task Force Recommendations for Improving the City of Albuquerque Police Oversight Process, January 31, 2014",
   "The complete final recommendations, dated the same day as the final report and published separately from it. It is the substantive core of the retained report rather than a different document, and it is the successor named for three of the superseded rows above.",
   "Token coverage 1.0000 inside the retained final report. It is itself a superset of the statement of principles (1.0000), the \"updated\" recommendations (0.9944), the January 15 draft (0.8590) and the Goal 3 substitute (0.8652)."),

 D("src-2a426f210dd181dd",
   "Police Oversight Task Force Cover Letter Memorandum to City Council President Ken Sanchez",
   "The interoffice memorandum transmitting the recommendations to Council. It is bound into the retained final report.",
   "Token coverage 0.9557 inside the retained final report."),
]


def X(i, title, reason, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "exclusion_reason": reason})
    if extra:
        r.update(extra)
    return r


excluded = [
 X("src-de4e623c20869360",
   "Police Oversight Task Force Items for Discussion, January 29, 2014",
   "A working handout listing individual members' proposed wording changes, such as Mr. Wagman's note that Goal 1 item 2a should read \"policy formulation\" rather than \"policy formation\". It is a line-edit list for a meeting, not a finding or a recommendation, and every change it proposes is settled in the retained final report.",
   {"measurement": "Token coverage 0.8949 inside the retained final report."}),

 X("src-1cdafb9d390b104d",
   "Police Oversight Task Force Agenda, January 21, 2014",
   "Agenda for a meeting whose summary minutes are published and recommended for addition in this same batch (src-d59b9b37da75fde5). The AGENTS.md missing-minutes policy forbids archiving an agenda when an approved-minutes original is available.",
   {"minutes_record_for_same_meeting": "src-d59b9b37da75fde5"}),

 X("src-eaf6dcd1e7d31d5f",
   "Police Oversight Task Force Agenda, January 29, 2014",
   "Agenda for a meeting whose summary minutes are published and recommended for addition in this same batch (src-1fb997ce90184cb5). Same policy ground.",
   {"minutes_record_for_same_meeting": "src-1fb997ce90184cb5"}),
]

rhr = [{
 **row("src-ff9893ec1cd700be", "requires human review"),
 "draft_title": "Albuquerque City Council Study Session Agenda, March 7, 2014",
 "date": "2014-03-07",
 "pages": 1,
 "question_for_human": "City Council study session minutes are a maintained series that this lane cannot reach. Does ABQInfo hold Council study session records at all, and if so is the March 7, 2014 summary retrievable from Legistar?",
 "why_not_decided_here": (
  "This is the one file in the directory that is not a task force record: it is a City Council study "
  "session agenda, filed here because item (b) is \"Police Oversight Task Force Recommendations "
  "(OC-14-2)\". The missing-minutes policy cannot be applied to it the way it was applied to the August 6 "
  "task force agenda, because the agenda itself proves Council keeps study session minutes as a running "
  "series: its item (a) is \"Approval of Study Session Summary Minutes - February 13, 2013\". Approved "
  "minutes for March 7, 2014 therefore almost certainly exist, in Legistar rather than on this page, so "
  "the policy's precondition that an exhaustive review find no approved minutes is not met and preserving "
  "the agenda would be wrong. Excluding it would also be wrong, because it is the only record in the "
  "inventory dating when the task force recommendations reached Council."),
 "evidence": ("One page listing the Twenty-First Council by district under President Ken Sanchez and "
              "Vice-President Trudy E. Jones, with three lettered items: approval of prior study session "
              "minutes, the Police Oversight Task Force Recommendations under file OC-14-2, and the "
              "Indicators Progress Commission."),
}]

rows = approved + superseded + duplicates + excluded + rhr
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

artifact = {
 "batch_id": "police-oversight-task-force-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/police-oversight-task-force-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Ad Hoc Police Oversight Task Force record set in the Albuquerque City Council document library at www.cabq.gov/council/documents/police-oversight-task-force-documents.",
 "scope": "All 20 pending-review candidates in that directory, which is the entire directory: no record in it held any other status, and the City's own listing returns exactly these 20 files. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Separate the task force's findings, recommendations, and adopted ordinance material from meeting handouts, applying the missing-minutes agenda policy as recorded in the Rail Yards artifact.",
 "brief_finding": "The directory's own structure does most of the separating once it is measured. The 238-page final report to Council is the canonical package, and nine of the other nineteen files are extracts from it or drafts of it, a relationship no hash can see and that only token-coverage measurement establishes. Two files are neither task force product nor handout and are the most consequential records present: the United States Department of Justice findings letter on APD of April 10, 2014, and the City's collective bargaining agreement with the Albuquerque Police Officers Association, which is the document that determines what civilian oversight can actually reach.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 20 are genuine PDFs by leading bytes. Extracted text with pdftotext -layout and rendered the one file with no text layer through pdf.js in a headless browser to identify it. Ran pairwise normalized-text similarity and token coverage across the whole cluster, which is how the nine component and version relationships to the final report were found. Compared all 20 checksums against the 1,612 checksummed inventory records. Paired agendas against minutes by meeting date, then ran a recorded exhaustive official-source review for the one task force agenda with no matching minutes. Fetched one out-of-cluster file read-only to settle a cross-directory duplicate question.",
 "classification_only": True,
 "shared_state_written": [],
 "precedent_applied": "The AGENTS.md canonical-package rule governs the report family: where one file's substantive content is wholly contained in another, retain one canonical original and document the relationship. The AGENTS.md missing-minutes agenda policy governs the four agendas. The federal-document line drawn in the Development Review Services artifact of the same date governs the DOJ letter.",
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text_or_token_coverage": 9,
  "note": "Hashing found nothing in this directory, and would not have: the nine relationships are one 238-page report and the extracts, drafts and handouts that were cut from it or grew into it. Every one was found by token coverage. Two of them would also have been mis-called by coverage alone and needed the sequence ratio as well: the January 15 draft recommendations and the Goal 3 substitute sit above 0.85 coverage inside the final recommendations while sharing almost no sequence with them, because the text was rewritten rather than copied."
 },
 "filename_trap": {
  "affects": ["src-ae7ae3ce5e1f23f8", "src-b4b2a26ac036021a"],
  "finding": "POTF Final Recommendations_updated.pdf is the earlier document and POTF Final Recommendations.pdf is the later one. The file called \"updated\" lacks the Statement of Principles that the other carries as section A, and 0.9944 of its tokens sit inside the other while only 0.8750 of the other's sit inside it.",
  "rule": "Do not order these two by filename. This is the fourth directory in this run where a filename asserts a version or a date that the document contradicts."
 },
 "exhaustive_minutes_review": {
  "purpose": "The AGENTS.md missing-minutes agenda policy permits preserving an official agenda only after a recorded exhaustive official-source review finds no approved minutes for that meeting. This is that record, for the August 6, 2014 task force meeting.",
  "steps": [
   "Fetched the City's own directory listing on 2026-09-11. It returns exactly 20 links, matched one for one against the 20 inventory records. The only summary minutes the City publishes for this task force are the four from January 2014.",
   "Searched all 7,074 inventory candidates for police oversight task force material. Nothing outside this directory holds task force minutes.",
   "Read the August 6 agenda itself, whose item 3 is \"Approval of Summary Minutes July 23, 2014\". That proves the task force continued to meet and to keep minutes after January, and that at least one further set of minutes exists unpublished."
  ],
  "conclusion": "No approved minutes for the August 6, 2014 meeting exist in any official source reachable from the City site or the inventory. The agenda carries a substantive seven-part business list.",
  "limit_stated_plainly": "This review establishes that the minutes are unpublished, not that they were never written; the agenda's own reference to July 23 minutes shows the task force kept minutes it did not publish. Nothing in an agenda shows whether the meeting took place, was cancelled, or lacked a quorum, so that half of the policy cannot be affirmatively cleared. If held to a stricter standard this one record moves to requires human review and nothing else in the batch changes."
 },
 "integration_flags": [
  {"severity": "cross-directory duplicate",
   "affects": ["src-5961fb8a4db0fb4e", "src-bdf2981b4899255b"],
   "finding": "The same April 10, 2014 DOJ findings letter is published twice in the Council library under different names in different directories. This cluster's copy is born-digital, 46 pages, 242,627 bytes, with a full text layer. The other, src-bdf2981b4899255b in councilor-district-5-documents, is a scanned image copy, 48 pages, 4,283,835 bytes, with no text layer at all; its first page was rendered and read to confirm it is the same letter to Mayor Richard J. Berry. Different bytes, different hashes, and the other record carries no checksum in the inventory, so nothing automated connects them.",
   "recommended_action": "When councilor-district-5-documents is triaged, make src-bdf2981b4899255b a duplicate of src-5961fb8a4db0fb4e. The born-digital copy is the one to keep: it is text-searchable and one eighteenth the size. This lane did not modify that record, which is outside its cluster."},
  {"severity": "currency",
   "affects": ["src-8fa6fb11a3c5125b"],
   "finding": "The collective bargaining agreement's term ran from July 16, 2014 to July 16, 2015 and expired more than eleven years ago. Its filename, NewUnionContract.pdf, says only \"new\".",
   "recommended_action": "Any title must state the exact term. It must never be presented as the agreement in force, and if a current APOA agreement is later located this record becomes its superseded predecessor rather than a competing copy."},
  {"severity": "placement",
   "affects": ["all 8 approved records"],
   "finding": "content/city-data/public-safety-data.md is the only page that fits this material, and it currently carries data snapshots rather than reports and legal instruments. Eight records including a 238-page report, a federal findings letter and a union contract is a different kind of content from what the page holds today.",
   "recommended_action": "Consider a distinct section on that page, for example Police Oversight Records, rather than appending to the existing data lists. A page-structure choice within an existing page, not a site-architecture change."},
  {"severity": "storage",
   "affects": ["src-f4204196f921104e"],
   "finding": "The final report is 17,608,309 bytes, 83 per cent of this batch's total archive footprint.",
   "recommended_action": "Size it into any upload batch deliberately. The checkpoint already carries an open blocker for 17 originals awaiting separate explicit R2 upload approval."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "requires_human_review": counts["requires human review"]
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 20 files are genuine PDFs by leading bytes. One, the collective bargaining agreement, has no text layer and was rendered."},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicates,
 "excluded": excluded,
 "requires_human_review": rhr,
 "archival_note": "All 8 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: "
                  f"{sum(r['size_bytes'] for r in approved):,} bytes, of which the 238-page final report alone is 17,608,309.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every superseded and duplicate row carries a canonical_id, and all of them resolve to the single retained final report src-f4204196f921104e; the superseded rows additionally name their immediate successor where that is a different file, so the version chain is preserved rather than flattened. The 8 approved rows each carry a title, a 20-to-50-word description, a date, and a proposed_canonical_page. One approved row is an agenda preserved under the missing-minutes policy and its title must keep the \"(approved minutes not located)\" qualifier. One row is requires human review and states its question and the evidence already gathered. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
