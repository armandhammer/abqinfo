"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-6-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d6\fetch.log')

PART1 = 'src-e7442b03ed708de4'     # validated, published: Zuni Road Study Part I
PART1_R2 = 'src-f57d18c0f4a7b682'
PART2 = 'src-257a9d7a9cd2784a'     # validated, published: Zuni Road Study Part II
PART2_COUNCIL = 'src-41dd0953c79a9816'   # already terminal duplicate: the Council copy of Part II
AGENDA = 'src-0ec812a6e3e76aee'    # already terminal excluded: the one-page 19 Aug 2014 agenda
GEOM = 'src-66553f9534aa579f'      # validated, published: Central/Zuni cross-section analysis

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


NOTES = [
 ("src-172795dd78e6c4eb", "Meeting Notes from Zuni Road Study Public Meeting #1, February 9, 2011", "2011-02-09",
  "attended by approximately 22 people including area residents city of albuquerque staff", 22,
  "Highland High School"),
 ("src-5276d66ddb02d3d3", "Meeting Notes from Zuni Road Study Public Meeting #2, May 4, 2011", "2011-05-04",
  "attended by approximately 13 people including area residents city of albuquerque staff", 13,
  "Highland High School"),
 ("src-e5cd3740284d3faa", "Meeting Notes from Zuni Road Study Public Meeting #3, July 20, 2011", "2011-07-20",
  "attended by approximately 45 people including area residents city of albuquerque staff", 45,
  "Cesar Chavez Community Center"),
]

duplicates = [{
 **row("src-b303d3b21a520dc0", "duplicate"),
 "title_for_reference": "Zuni Road Study Report Part I (City Council copy)",
 "pages": 133,
 "canonical_id": PART1,
 "canonical_url": IDX[PART1_R2].get('r2_url'),
 "canonical_state": "validated, R2-archived, and already published at content/transportation/roadway-projects/studies.md line 329",
 "basis": ("The same 133-page study the archive already holds. The City publishes it twice: the archived copy came "
           "from www.cabq.gov/planning/documents/ZuniRoadStudyPart11111.pdf, this one from the District 6 councillor's "
           "page under a different filename."),
 "measurement": ("Fetched the R2 object and compared. 133 pages each, normalized-text ratio 1.0000, token coverage "
                 "1.0000 in both directions, and a line-level unified diff of the two extracted texts returns zero "
                 "differing lines. The files differ by 1,485 bytes of encoding, 8,461,336 here against 8,459,851 "
                 "archived."),
 "hash_found_it": False,
 "mirrors_a_decision_already_made": ("This is the Part I counterpart of a decision already in the inventory. "
                                     + PART2_COUNCIL + ", the Council copy of Part II, is already terminal with the "
                                     "reason \"Alternate official City Council copy of Zuni Road Study Part II; the "
                                     "same collected-data report is already preserved and validated as " + PART2
                                     + ".\" The byte gaps are even the same shape: Part II differs by 1,230 bytes, "
                                     "Part I by 1,485. Part I was left pending; this closes it the same way."),
}]

for i, title, date, phrase, attend, venue in NOTES:
    r = row(i, "duplicate")
    r.update({
     "title_for_reference": title, "pages": 1, "date": date,
     "canonical_id": PART1,
     "canonical_url": IDX[PART1_R2].get('r2_url'),
     "canonical_state": "validated, R2-archived, and already published at content/transportation/roadway-projects/studies.md line 329",
     "basis": "Not a separate document but a page lifted out of the study the archive already holds. The study incorporates its public-involvement record in its own narrative and in Appendix A.",
     "measurement": (f"Token coverage 1.0000 inside the archived Part I, and the containment is verbatim, not merely "
                     f"lexical: the phrase \"{phrase}\" appears literally in the archived study's extracted text and "
                     f"nowhere in Part II. The notes record a meeting at {venue} attended by roughly {attend} people "
                     f"including District 6 Councillor Rey Garduño."),
     "hash_found_it": False,
     "the_file_says_so_itself": ("These sheets state their own redundancy. Meeting #1's notes read \"A flyer and other "
                                 "materials from this meeting are included in Appendix A of the Zuni Road Study "
                                 "report\", and Meeting #3's read \"A flyer and other materials from this meeting, "
                                 "including the presentation slides, are included in Appendix A.\" Reading the file "
                                 "before comparing it is what pointed at the comparison to run."),
    })
    duplicates.append(r)

CROSS = [
 ("src-e0c7da753dfe1665", "Zuni Road cross-section handout: Washington Street to San Mateo Boulevard", "existing six-lane divided section against a proposed four-lane divided section with 5-6 foot bicycle lanes"),
 ("src-22948160e479a442", "Zuni Road cross-section handout: San Mateo Boulevard to Wyoming Boulevard", "existing four-lane undivided section against Alternative 1B, a three-lane road diet with a striped centre two-way left-turn lane"),
 ("src-299a355e83b9ca82", "Zuni Road cross-section handout: Wyoming Boulevard to Central Avenue", "existing four-lane asymmetric section against a three-lane section with bicycle lanes"),
]

CROSS_REASON = (
 "A one-page public-information handout sheet pairing a street-level photograph with an engineering typical-section "
 "diagram lifted from the Zuni Road Study. The diagrams are the study's own figures: the study carries the existing "
 "typical sections for these three segments as Figures 5, 6 and 7 and the proposed sections as Figures 14 onward, "
 "with full dimensioning and the alternatives analysis behind them, and it names Alternative 1B, Road Diet by "
 "Reconstructing Curb and Sidewalk, thirty times. The handout adds a photograph and a five-line caption and drops "
 "everything else.")

excluded = []
for i, title, what in CROSS:
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": 1, "exclusion_reason": CROSS_REASON,
              "category": "public information handout",
              "content": what,
              "tested_not_assumed": ("Rendered and read. The San Mateo to Wyoming sheet's diagram is captioned "
                                     "ALTERNATIVE 1B - ROAD DIET BY RECONSTRUCTING CURB AND SIDEWALK over a 60-foot "
                                     "nominal right-of-way, which is how the sheets were tied back to the study "
                                     "rather than guessed at from their titles."),
              "canonical_for_reference": PART1})
    excluded.append(r)

excluded.append({
 **row("src-32a617f4e28735ba", "excluded"),
 "title_for_reference": "Zuni Road Improvements Project public information meeting packet, August 19, 2014 (Project #592691, CN A300655)",
 "pages": 4,
 "date": "2014-08-19",
 "exclusion_reason": ("A four-page meeting packet: the agenda sheet, a project area map, a blank comment form and the "
                      "form's postage-paid reverse. Meeting handouts and blank forms are both excluded throughout this "
                      "run, and the packet's own first page is already terminal in the inventory."),
 "category": "meeting packet",
 "contains_an_already_excluded_record": (AGENDA + " is the one-page \"Zuni Road Improvements Public Meeting Agenda, "
                                         "August 19, 2014\", excluded with the reason that it is a \"One-page "
                                         "public-information meeting schedule with no substantive project "
                                         "presentation or findings\". That page is page 1 of this packet. The "
                                         "inventory holds the sheet and the packet as separate records; excluding "
                                         "both keeps them consistent."),
 "tested_not_assumed": ("Image-only, four bytes of extractable text across four pages. All four were rendered and "
                        "read. Page 1 is the agenda and project summary, page 2 is Figure 1 Project Area Map by "
                        "Marron and Associates at 1:26,843, page 3 is the comment form, page 4 is its mailer reverse "
                        "addressed to the Department of Municipal Development."),
 "discovery_lead": ("The packet identifies a later, separate project from the 2011 study: Zuni Road Improvements, "
                    "Washington Street SE to Central Avenue NE, approximately 2.9 miles, Project #592691, CN A300655, "
                    "sponsored by the City with the New Mexico Department of Transportation and the Federal Highway "
                    "Administration. The federal control number and the Marron and Associates figure numbering point "
                    "at an environmental document for that project. Nothing for CN A300655 is held anywhere in the "
                    "inventory."),
})

excluded.append({
 **row("src-4981e2d1057203fb", "excluded"),
 "title_for_reference": "Councilor District 6 documents collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
})

rows = duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 9, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
avoided = sum(r["size_bytes"] for r in duplicates)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "councilor-district-6-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-6-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The District 6 councillor's document collection in the Albuquerque City Council library, which is entirely Zuni Road corridor material from Councillor Rey Garduño's terms.",
 "scope": "All 9 pending-review candidates. The directory holds 13 records; the other four are already terminal and three of them are what this lane's findings rest on.",
 "brief": "Run the standard opening sequence, reading each record's citations closely enough to answer other clusters' open questions the way the district-9 EPC record answered R-07-278.",
 "brief_finding": ("Reading the records closely answered this cluster's own questions rather than another's, and it "
                   "emptied the directory. Every substantive file here is either the Zuni Road Study itself or "
                   "material lifted out of it, and the study is already validated, R2-archived and published in both "
                   "its parts. Nothing is recommended for addition and nothing needs human review: four records are "
                   "duplicates of a published archive object and five are handouts and forms."),
 "the_reading_that_did_it": ("The three meeting-notes sheets say their own redundancy out loud. Meeting #1's notes "
                             "read \"A flyer and other materials from this meeting are included in Appendix A of the "
                             "Zuni Road Study report.\" That sentence is what prompted fetching the archived study "
                             "and testing containment, which came back verbatim at token coverage 1.0000. A lane that "
                             "classified these from their titles would have called them public-meeting records and "
                             "either archived three redundant sheets or excluded them for the wrong reason."),
 "method": ("Ran the URL group-by first; one collision, already resolved in the inventory. Fetched all 9 candidates "
            "on both URL forms and measured byte length and SHA-256 from the raw form. Compared all checksums within "
            "the cluster and against the 1,612 checksummed inventory records: no collisions either way, which is the "
            "point — every relationship in this cluster is invisible to hashing. Fetched both archived study parts "
            "read-only and tested each candidate against them by token coverage and then by literal phrase match. "
            "Rendered every image-only sheet. Read the terminal records' recorded reasoning before classifying "
            "anything."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "nob-hill-highland-cluster-research-2026-09-11.json requires testing a candidate against R2 objects the archive already holds; dnasdp-cluster-research-2026-09-12.json extended it to the published site entry.",
  "candidates_tested": 7,
  "result": "Four are contained in the archived Zuni Road Study Part I and three are derived from its figures.",
  "part_1": ("src-b303d3b21a520dc0 against " + PART1 + ": 133 pages each, ratio 1.0000, coverage 1.0000 both ways, "
             "zero differing lines in a full line-level diff, 1,485 bytes apart."),
  "meeting_notes": ("Three sheets, each at token coverage 1.0000 inside the archived Part I, each confirmed by a "
                    "literal phrase match present in Part I and absent from Part II."),
  "cross_sections": ("Token coverage 0.9268 to 0.9750, which on 33 to 41 tokens proves nothing on its own — the "
                     "caution recorded in the earliest artifacts of this run is that sparse text over-calls. They "
                     "were settled by rendering instead: the diagrams are the study's own typical sections, one of "
                     "them captioned with the study's Alternative 1B by name."),
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue, and nothing added.",
 },
 "closes_a_pair": {
  "what": ("The inventory already held a terminal decision for the Council copy of Zuni Road Study Part II — "
           + PART2_COUNCIL + ", duplicate, \"the same collected-data report is already preserved and validated as "
           + PART2 + "\" — while the Council copy of Part I sat pending. This artifact closes Part I the same way."),
  "why_it_was_left_open": ("Nothing in the record connected them. The two Council copies have different filenames from "
                           "their archived counterparts, sit on a different server, and carry no checksum in the "
                           "inventory. Part II happened to be reached by an earlier pass and Part I was not."),
  "shape_of_the_evidence": "Both Council copies are slightly larger than their archived counterparts and text-identical to them: Part II by 1,230 bytes, Part I by 1,485.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 1,
  "url_collisions_already_terminal": 1,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_comparison_against_r2": 7,
  "note": ("Seven relationships and hashing found none of them, in a directory where every single substantive file "
           "turns out to be derived from one archived report. This is the clearest case yet for the rule that a "
           "candidate must be tested against what the archive already holds rather than against its neighbours."),
 },
 "url_collision_already_resolved": {
  "group": "https://www.cabq.gov/council/documents/councilor-district-6-documents/ZuniGeometricAnalysis.pdf",
  "records": ["src-5a3c0c601f75c4a9", GEOM],
  "state": "Already handled: the implemented record is the official-PDF link carried on the published page and the canonical is validated and archived at content/transportation/roadway-projects/studies.md line 341.",
  "why_recorded": "Second consecutive councillor directory whose single URL collision was already actioned, after councilor-district-7-cluster-research-2026-09-12.json. The audit's actionable set continues to draw down.",
 },
 "integration_flags": [
  {"severity": "avoid-duplicate-archival",
   "affects": [r["id"] for r in duplicates],
   "finding": "All four are contained in the archived Zuni Road Study Part I: the full 133-page Council copy and three meeting-notes sheets lifted from its public-involvement record.",
   "recommended_action": f"Record all four as duplicate of {PART1}. Together {avoided:,} bytes that do not need uploading."},
  {"severity": "closes-a-pair",
   "affects": ["src-b303d3b21a520dc0"],
   "finding": "The Council copy of Part II was already terminal as a duplicate; the Council copy of Part I was still pending. Same relationship, same shape of evidence.",
   "recommended_action": "Apply the same decision. No new judgment is required."},
  {"severity": "discovery-lead",
   "affects": ["src-32a617f4e28735ba"],
   "finding": "The 2014 meeting packet identifies a distinct later project — Zuni Road Improvements, Washington Street SE to Central Avenue NE, 2.9 miles, Project #592691, CN A300655, with NMDOT and FHWA — and reproduces Figure 1 of a Marron and Associates document for it. Nothing for CN A300655 is held.",
   "recommended_action": "Queue the environmental document for CN A300655. The 2011 study is the planning record; this is the project that followed it, and the archive has the first and not the second."},
  {"severity": "empty-result",
   "affects": [],
   "finding": "Nothing in this directory is recommended for addition and nothing needs human review. The directory is fully derived from records already published.",
   "recommended_action": "None. Recorded so the zero is legible as a finding rather than as an incomplete lane."},
 ],
 "counts": {
  "reviewed": len(rows),
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 9, "http_200": 9, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "archive_fetches": "Both archived Zuni Road Study parts at files.abqinfo.com were fetched read-only for comparison, both HTTP 200; Part I's bytes match its inventory record exactly.",
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "8 genuine PDFs and one HTML collection page by leading bytes. Four PDFs have no usable text layer and were rendered."},
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": ("Nothing in this cluster is recommended for archival, and nothing here is inventory-only pending "
                   f"R2 work. The {avoided:,} bytes in the duplicate rows are already preserved in the two published "
                   "Zuni Road Study objects, whose downloads, sizes, checksums and provenance were verified when they "
                   "were validated."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Every duplicate row carries a canonical_id pointing "
                      "at one validated, R2-archived, already-published record outside this cluster, and each states "
                      "whether the relationship is whole-document identity or containment. No row is approved for "
                      "addition and no row requires human review, so this artifact adds nothing to either queue. "
                      "Sizes and checksums are first measurements; the inventory held none for any pending record "
                      "here."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the two R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
