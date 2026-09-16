"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

This artifact also addresses the open checkpoint blocker naming
src-0f4496e4073a5e06 as an isolated legislative amendment file.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\nob-hill-highland-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\nhh\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/nob-hill-highland/'

AREA = 'content/development-land-use/area-sector-plans.md'
PLANS = 'content/transportation/transportation-plans.md'

ARCHIVED = 'src-6916bbd03258654b'   # validated, R2-archived transportation section

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


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    r.update(M[i])
    return r


FIGURES = [
 ("src-8160a61f7c83c971", "Figure13-reportmaps5pedestriancirculationrev.pdf", "Figure 13: Pedestrian Circulation Recommendations", 29),
 ("src-90652ae3635e9ae5", "Figure14.pdf", "Figure 14: Conceptual Streetscape Design (Girard Blvd. to Wellesley Dr.)", 32),
 ("src-f0f9ee71b7918da0", "Figure15.pdf", "Figure 15: Conceptual Streetscape Design (Wellesley Dr. to Hermosa Dr.)", 33),
 ("src-fc770208932ab76a", "Figure16.pdf", "Figure 16: Conceptual Streetscape Design (Hermosa Dr. to Sierra Dr.)", 34),
 ("src-a28d98368f0e0c64", "Figure18.pdf", "Figure 18: Conceptual Streetscape Design (Madison St. to San Mateo Blvd.)", 36),
 ("src-672aaf4ba581ee4a", "Figure19-reportmaps6bicyclecirculationrev.pdf", "Figure 19: Bicycle Circulation Recommendations", 43),
 ("src-f9164381b5372306", "FigureD6-TurningMovementExhibitGIRARDTOALISO1.pdf", "Figure D6: Intersection Turn Movements", 135),
]

duplicates = []
for i, fname, figtitle, printed in FIGURES:
    r = row(i, "duplicate")
    r.update({
     "title_for_reference": f"Nob Hill Highland Sector Development Plan, {figtitle}",
     "pages": 1,
     "canonical_id": ARCHIVED,
     "canonical_url": IDX[ARCHIVED].get('r2_url') or IDX[ARCHIVED].get('direct_file_url'),
     "canonical_state": "validated and already archived to R2",
     "basis": (f"This figure is already inside the validated, R2-archived Nob Hill Highland Sector Development "
               f"Plan record, on its own printed page {printed}. Publishing the loose sheet would add a second "
               f"copy of a page the archive already holds."),
     "hash_found_it": False,
     "printed_page_in_canonical": printed,
    })
    duplicates.append(r)

approved = [
 {**row("src-eee3ae1f6b6df008", "approved for addition"),
  "title": "Nob Hill Highland Sector Development Plan, September 2006 Draft — Front Matter and Introduction (printed pages i to 23)",
  "description": "The draft sector development plan's opening sections introduce the Nob Hill and Highland planning area, list the steering committee and participants, and set out the contents, figures, and introductory context for the 770-acre plan area.",
  "date": "2006-09", "pages": 31,
  "proposed_canonical_page": AREA,
  "cross_listings": [{"page": PLANS, "reason": "The plan's adopted movement-systems chapter is already published there; the draft's introduction gives that chapter its context."}],
  "evidence": ("31 PDF pages. Every page footer reads \"Nob Hill Highland Sector Development Plan - September 2006 Draft\" "
               "with printed page numbers running i through 23. Acknowledgements name Mayor Martin J. Chavez and a "
               "steering committee including the Nob Hill Neighborhood Association, Bernalillo County and APS."),
  "why_retained": ("The archive holds no introduction to this plan in any form. The validated R2 copy covers only printed "
                   "pages 3 and 28 to 53 and 129 to 140, so pages i to 23 exist nowhere else in the inventory."),
  "labelling_constraint": ("It is a DRAFT and must be titled one. The plan was adopted in 2007 by R-07-185, amended "
                           "through August 2014, and then repealed by R-17-213. Never present this as the adopted plan."),
  "completeness_caveat": "Printed pages 24 to 98 of the draft are not published in this directory and are not in the inventory."},

 {**row("src-da5e395c4284e4b8", "approved for addition"),
  "title": "Nob Hill Highland Sector Development Plan, September 2006 Draft — Appendices A to C (printed pages 99 to 117)",
  "description": "The draft plan's appendices carry a vision for the Hiland Theatre and Highland neighbourhood, recommended transit-oriented development references, and excerpts from the Revitalization Through Design guidelines for the Nob Hill business district.",
  "date": "2006-09", "pages": 20,
  "proposed_canonical_page": AREA,
  "cross_listings": [],
  "evidence": ("20 PDF pages, printed 99 to 117, headed \"VI. APPENDICES\". Appendix A is a vision for the future of the "
               "Hiland Theatre and Highland neighbourhood presented to the City; Appendix B carries excerpts from "
               "Revitalization through Design Guidelines for Nob Hill Business District."),
  "why_retained": ("Appendices A to C are not in the validated R2 copy, which jumps from printed page 53 to Appendix D at "
                   "printed page 129. This is the only copy of that material in the inventory."),
  "labelling_constraint": "Draft, same constraint as the front matter above.",
  "complements": "src-eee3ae1f6b6df008 and the validated src-6916bbd03258654b together give printed pages i-23, 28-53, 99-117 and 129-140 of a roughly 140-page plan."},
]
for r in approved:
    r["description_word_count"] = len(r["description"].split())


def R(i, draft_title, pages, question, why, evidence):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why, "evidence": evidence})
    return r


rhr = [
 R("src-3b98e92fa018bda2",
   "Council Bill R-07-185: Repeal of the Nob Hill Sector Development Plan and Adoption of the Nob Hill Highland Sector Development Plan, With Change of Zoning Within the Plan Boundary",
   10,
   "Locate the enacted resolution R-07-185. This is the instrument that adopted the plan and rezoned roughly 770 acres.",
   ("This copy is an unsigned working version: COUNCIL BILL NO., ENACTMENT NO. and SPONSORED BY are all three blank on "
    "its face, which is worse than the usual case in this run where only the enactment number is missing. It cannot be "
    "cited for its own bill number. The adoption is not in doubt, because the validated R2 copy of the plan states on "
    "its first page that the plan was \"Repealed - R-17-213\" and was in force \"As Amended Through August 2014\", but "
    "the enacted text of R-07-185 is what a reader would need and this is not it."),
   "10 pages, Seventeenth Council. The title repeals the earlier Nob Hill Sector Development Plan, adopts the Nob Hill Highland plan, and changes zoning within an area bounded by Girard Boulevard, Lomas Boulevard, San Mateo and Zuni Boulevard/Garfield Street containing approximately 770 acres."),

 R("src-99b19f7854667dca",
   "Council Bill R-04-189: Authorizing a Community Based Update of the Nob Hill Sector Plan to Pursue Consistency With the Central/Highland Metropolitan Redevelopment Area Plan",
   4,
   "Locate the enacted resolution R-04-189; decide together with R-07-185.",
   ("Enactment number blank, under the two standing checkpoint blockers. It is the instrument that started the process "
    "R-07-185 finished, so the two belong together. Its sponsor, Martin Heinrich, is recorded on the face of this copy, "
    "unlike R-07-185."),
   "4 pages, Sixteenth Council, sponsored by Martin Heinrich, enactment number blank."),
]

AMENDMENTS = [
 ("src-2f170ed5e1945f6f", "far-07-185amndtoresolution3.pdf", "Amendment to the resolution text itself", 2),
 ("src-f3c81bea3f2a7bc0", "far-07-185bldgarticulation4.pdf", "Building articulation standards", 1),
 ("src-ff1e0ecbec5d0b95", "far-07-185epccondit_clnup5.pdf", "Environmental Planning Commission conditions cleanup", 4),
 ("src-78e98fcba1ebf030", "far-07-185epcrecs_3.pdf", "Environmental Planning Commission recommendations", 1),
 ("src-f5381196eb22253a", "far-07-185nhna1.pdf", "Nob Hill Neighborhood Association amendment", 1),
 ("src-53b2664596e094e9", "far-07-185nhna3prkgstruc3.pdf", "Nob Hill Neighborhood Association, parking structures", 1),
 ("src-198bd816c0d22058", "far-07-185Amendmisc5.pdf", "Miscellaneous amendments", 2),
 ("src-90eec340c83f0544", "far07-185plnngresptocommnts.pdf", "Planning response to comments", 1),
]

AMEND_REASON = (
 "A City Council floor amendment sheet to R-07-185. It cannot be read on its own: it instructs a change at a stated "
 "page and column of a plan it does not contain, and the plan pages it operates on are not published in this "
 "directory either. Excluded as a non-self-contained legislative fragment, the category decision recorded in the "
 "council-documents artifact of the same date, which covers at least 57 such files across this tree and is "
 "explicitly open to revisiting as one category rather than record by record.")

excluded = []
for i, fname, subject, pages in AMENDMENTS:
    r = row(i, "excluded")
    r.update({"title_for_reference": f"Floor Amendment to R-07-185: {subject}",
              "pages": pages, "exclusion_reason": AMEND_REASON,
              "category": "council legislative amendment sheet",
              "amendment_set": "R-07-185 Nob Hill Highland, nine sheets including src-0f4496e4073a5e06"})
    excluded.append(r)

excluded.append({
 **row("src-880db422c2320123", "excluded"),
 "title_for_reference": "Nob Hill Highland collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
 "usefulness": ("Parsed as part of this lane. It does not list Figure17.pdf, which exists on the City server. That file "
                "needs no action: see undiscovered_files."),
})

rows = duplicates + approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "nob-hill-highland-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/nob-hill-highland cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Nob Hill Highland Sector Development Plan record set in the Albuquerque City Council document library.",
 "scope": "All 20 pending-review candidates in that directory. The directory also holds src-0f4496e4073a5e06, which a prior lane set to requires human review and which the checkpoint names in an open blocker; this artifact does not reclassify it but corrects the blocker's premise and recommends a disposition.",
 "brief": "Separate adopted sector plan text and regulating material from drafts and meeting handouts, rendering image-only records and probing the filename sequence against the City listing.",
 "brief_finding": "The separation came out differently than expected because a validated record already in the archive turned out to contain a third of the directory. Seven of the twenty files are single plan figures that are already inside the R2-archived Nob Hill Highland plan copy, each on its own printed page; publishing them would duplicate pages the archive holds. Nine are floor amendment sheets to R-07-185. Only two files carry material the archive does not have in any form, and both are marked September 2006 Draft on every page.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each. Read the printed page footer on every page of the two plan files to recover their page ranges. Fetched the already-validated R2 archive object for this plan and mapped it page by page, which is what established that all eight figures and two of the four page ranges are already held. Probed the figure filename sequence against the City listing. Compared all checksums against the 1,612 checksummed inventory records.",
 "classification_only": True,
 "shared_state_written": [],
 "blocker_correction": {
  "blocker_text": "src-0f4496e4073a5e06 and src-0feec7ebf6650e27 are isolated legislative amendment/substitute files; resolve authoritative enacted packages before archival or visible use.",
  "source": "project-state/checkpoint.json, blockers array",
  "finding": ("The premise is wrong for src-0f4496e4073a5e06: it is not isolated. It is one of nine floor amendment "
              "sheets to R-07-185 sitting in this directory, and the resolution they amend, R07185.pdf, is in the same "
              "directory as src-3b98e92fa018bda2. The amendment states its own target on its face: \"The Nob Hill "
              "Highland Sector Development Plan attached to and incorporated by R-07-185 is amended as follows\", dated "
              "August 6, 2007, inserting a solar-access section for R-1 properties west of Washington Street citing "
              "Zoning Code Section 14-16-3-3(A)(7)."),
  "what_is_actually_missing": ("Not the amendment's context but the plan pages it operates on. This sheet amends page 96 "
                               "of the plan; the directory publishes printed pages i to 23 and 99 to 117 only, and the "
                               "validated R2 copy covers 3, 28 to 53 and 129 to 140. Page 96 is in none of them."),
  "recommended_action_for_src_0f4496e4073a5e06": ("Resolve to excluded with the other eight amendment sheets, on the "
                                                  "non-self-contained-fragment ground recorded in the council-documents "
                                                  "artifact. An excluded record needs no enacted package, which closes "
                                                  "this half of the blocker without further research. Claude did not "
                                                  "modify the record."),
  "note_on_the_other_named_record": ("src-0feec7ebf6650e27 is not in this directory and is untouched by this artifact. "
                                     "The blocker should be narrowed to that record alone once this half is applied."),
 },
 "already_archived_finding": {
  "canonical_id": ARCHIVED,
  "canonical_state": "validated, R2-archived, and published on content/transportation/transportation-plans.md",
  "what_it_actually_contains": ("The inventory titles it a Transportation Section, but it is 42 PDF pages spanning "
                                "printed pages 3, 28 to 53, and 129 to 140: the whole Plan Components / Movement "
                                "Systems chapter plus Appendix D. Its first page states \"Repealed - R-17-213\" and "
                                "\"As Amended Through August 2014\"."),
  "consequence": ("All eight plan figures in this directory are inside it, each on its own printed page: Figure 13 at "
                  "29, Figure 14 at 32, Figure 15 at 33, Figure 16 at 34, Figure 17 at 35, Figure 18 at 36, Figure 19 "
                  "at 43, Figure D6 at 135. Seven of those eight are pending candidates and are recommended duplicate."),
  "method_note": ("This was settled by fetching the R2 object and mapping it page by page, not by reasoning from its "
                  "inventory title. A record titled as one section of a plan may hold considerably more than that; "
                  "check the object before classifying anything against it."),
 },
 "undiscovered_files": {
  "count": 1,
  "files": {"Figure17.pdf": {"url": BASE + "Figure17.pdf", "http_status": 200, "size_bytes": 634013,
                             "identity": "Figure 17: Conceptual Streetscape Design (Sierra Dr. to Madison St.), the one figure in the series absent from the City's collection listing and from the inventory."}},
  "recommended_action": ("No action. Unlike the Planned Growth Strategy and Form Based Code clusters of the same date, "
                         "this undiscovered file does not need adding: Figure 17 is already inside the validated R2 "
                         "archive at printed page 35, exactly like its seven siblings. Adding it as a candidate would "
                         "create a record whose only possible disposition is duplicate."),
  "generalisation": ("Third consecutive directory in which the City's own collection listing is incomplete against its "
                     "own server, after pgs and form-based-code. But this one also shows the corrective: check whether "
                     "an undiscovered file is already held before queuing it for addition. Probe the sequence, then "
                     "check the archive."),
  "probe_record": "Nine probes run. Figure17 returned 200; nhplan2, nhplan1, nhplanpart2, Figure1, Figure12, Figure20, nhplanbody and nhtext returned 404, which bounds the figure series and shows no further plan-body file is published.",
 },
 "plan_completeness": {
  "plan": "Nob Hill Highland Sector Development Plan",
  "adopted": "2007 by R-07-185, amended through August 2014, repealed by R-17-213",
  "approximate_length_pages": 140,
  "held_or_recommended": [
   {"printed_pages": "i-23", "source": "src-eee3ae1f6b6df008, September 2006 draft", "state": "recommended for addition here"},
   {"printed_pages": "3, 28-53", "source": ARCHIVED, "state": "validated and R2-archived, adopted text as amended through 2014"},
   {"printed_pages": "99-117", "source": "src-da5e395c4284e4b8, September 2006 draft", "state": "recommended for addition here"},
   {"printed_pages": "129-140", "source": ARCHIVED, "state": "validated and R2-archived, adopted text as amended through 2014"},
  ],
  "not_held": "Printed pages 24 to 27 and 54 to 98 are in no inventory record and are published nowhere in this directory. Page 96, which one floor amendment operates on, falls in that gap.",
  "mixed_generation_warning": ("What the archive would hold after this batch is two page ranges of a September 2006 draft "
                               "and two page ranges of the adopted text as amended through 2014. Those are different "
                               "documents. Any page presenting them together must say so plainly rather than implying "
                               "one continuous plan."),
  "lead": ("The validated R2 copy names its source for the complete plan: http://www.cabq.gov/planning/plans-publications/"
           "area-sector-development-plans. That is a library index rather than a file link, but it is the place to look "
           "for a complete adopted copy."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_archive_inspection": 7,
  "note": ("Hashing finds nothing here and could not: a loose one-page figure sheet shares no bytes with the 42-page "
           "archive object that contains the same figure on a numbered page. Text comparison also fails, because six of "
           "the seven figure sheets have no text layer at all. The relationships were established by fetching the "
           "archive object and locating each figure by its printed page. That is a third distinct method, after byte "
           "hashing and normalized-text measurement, and it is the only one that works for image-only extracts of a "
           "document the archive already holds."),
 },
 "integration_flags": [
  {"severity": "blocker-correction",
   "affects": ["src-0f4496e4073a5e06"],
   "finding": "The checkpoint describes this record as an isolated legislative amendment file. It is not isolated: it is one of nine amendment sheets to R-07-185 and the resolution they amend is in the same directory.",
   "recommended_action": "Resolve it to excluded with its eight siblings and narrow the blocker to src-0feec7ebf6650e27 alone."},
  {"severity": "avoid-duplicate-archival",
   "affects": [f[0] for f in FIGURES],
   "finding": f"Seven pending figure sheets totalling {sum(M[f[0]]['size_bytes'] for f in FIGURES):,} bytes are already inside the R2-archived plan object, each on its own printed page.",
   "recommended_action": "Record them as duplicates and do not upload. This is the first cluster in this run where the saving is against an object already in R2 rather than against another candidate."},
  {"severity": "mixed-generation",
   "affects": ["src-eee3ae1f6b6df008", "src-da5e395c4284e4b8", ARCHIVED],
   "finding": "The two recommended records are September 2006 draft pages; the validated archive object is adopted text as amended through 2014. Placed on one page they would look like a single plan and are not.",
   "recommended_action": "Title both new records with September 2006 Draft, and if they are listed alongside the archived adopted chapter, state the difference in the surrounding text. Neither may be presented as adopted."},
  {"severity": "inventory-title-misleading",
   "affects": [ARCHIVED],
   "finding": "The validated record is titled a Transportation Section but contains the whole Movement Systems chapter and Appendix D, spanning printed pages 3, 28 to 53 and 129 to 140, and is the archive's only copy of any adopted text from this plan.",
   "recommended_action": "Consider retitling it to reflect what it holds. A future lane that reasons from the current title will underestimate what the archive already has, which is exactly the error this lane nearly made."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "superseded": 0,
 },
 "link_check": {"checked": 21, "http_200": 21, "failed": 0,
                "probe_checked": 9, "probe_http_200": 1, "probe_http_404": 8,
                "archive_fetch": "The validated R2 object at files.abqinfo.com was fetched read-only, HTTP 200, 8,234,679 bytes.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 20 pending candidates and the prior-lane requires-human-review record, plus nine filename-sequence probes.",
                "containers_verified": "20 genuine PDFs and one HTML collection page by leading bytes."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": f"Both approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, a small batch. Recognising the seven figures as duplicates keeps a further {sum(M[f[0]]['size_bytes'] for f in FIGURES):,} bytes of already-archived content out of the upload queue.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. All seven duplicate rows carry a canonical_id pointing at src-6916bbd03258654b, which is already validated and R2-archived, and each records the printed page in that object where the figure sits. The two approved rows carry a title, a 20-to-50-word description and a proposed_canonical_page, and both carry a labelling_constraint that must survive into any published title. Two rows are requires human review under the standing enactment blockers. Nine amendment sheets are recommended excluded, eight here and one, src-0f4496e4073a5e06, by recommendation in blocker_correction. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy", "no inventory record created for the undiscovered file", "the R2 object was fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
