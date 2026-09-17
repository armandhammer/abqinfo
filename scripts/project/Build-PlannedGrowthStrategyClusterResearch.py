"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

This artifact also discharges the open checkpoint blocker on the split Planned
Growth Strategy package, using the reconciliation method recorded in the Volcano
Heights artifact of the same date.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\planned-growth-strategy-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\pgs\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/pgs/'

PLANS = 'content/development-land-use/area-sector-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'
CAPITAL = 'content/city-data/capital-spending.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")

P1_COMBINED = 'src-9aeb5f621800da58'

P1_CHAPTERS = [
 ("src-1779ba516b4d2c3f", "Part1-1.pdf", 1, "Acknowledgements, introduction and study framing", 20),
 ("src-544756098ac12660", "Part1-2.pdf", 2, "Development Trends", 51),
 ("src-cd7c886fe1c0e6f7", "Part1-3.pdf", 3, "Alternative Scenarios", 11),
 ("src-a7dd815a1ea2937e", "Part1-4.pdf", 4, "Infrastructure Costs", 86),
 ("src-415952dd1d905cf7", "Part1-5.pdf", 5, "Policy, Regulatory and Plan Review", 72),
 ("src-0bd664780961f148", "Part1-6.pdf", 6, "Section 2, Economic Impact of Growth", 31),
 ("src-f1990b741c73ce09", "Part1-7.pdf", 7, "Section 3, Other Consequences", 15),
]

# Part 2 chapter map, page ranges read from the Part 2 table of contents printed
# inside Part2-1a.pdf, not inferred from filenames.
P2_MAP = [
 ("src-08b6b68b53336462", "Part2-1a.pdf", "1.0a", "Section 1 Preferred Alternative: front matter, table of contents, and Introduction and Rationale, first half", "1-51", 56, "pending review"),
 ("src-3efa72bc100374a1", "Part2-1b.pdf", "1.0b", "Introduction and Rationale, second half, through the establishment of the Preferred Alternative", "52-82", 22, "pending review"),
 ("src-aee98d2ab382de65", "Part2-2.pdf", "2.0", "Preferred Alternative: Subarea Descriptions", "83-130", 48, "pending review"),
 (None, "Part2-3.pdf", "3.0", "Preferred Alternative Summary", "131-156", None, "ABSENT FROM SOURCE"),
 ("UNDISCOVERED-Part2-4", "Part2-4.pdf", "4.0", "Examples of Mixed-Use Redevelopment Projects in Other Cities", "157-168", 12, "not in inventory"),
 ("src-c8e6f10731a478e6", "Part2-5.pdf", "5.0", "Section 2 Implementation: Level of Service Standards and the Planned Growth Strategy", "169-210", 35, "pending review"),
 ("UNDISCOVERED-Part2-6", "Part2-6.pdf", "6.0", "Financial Implementation of the Planned Growth Strategy Preferred Alternative", "211-218", 16, "not in inventory"),
 ("src-765624191ba169bd", "Part2-7.pdf", "7.0", "Planned Growth Regulatory Structure Approaches", "219-244", 26, "pending review"),
 ("src-d15bbc358aeaec4d", "Part2-8.pdf", "8.0", "Combining the Level of Service Standards with the Management Committee material", "245-264", 20, "pending review"),
 ("src-8188148b0cd6c40d", "Part2-9.pdf", "9.0", "City and County Financial and Planning Requirements", "265-280", 16, "pending review"),
 ("src-0e133db868401e77", "Part2-10.pdf", "10.0", "Section 3 Urban Growth Management: Growth Strategy Techniques Used in Other Locations", "281-", 63, "requires human review (already set by a prior lane)"),
 ("src-c771ae9e41b9905c", "Part2-11.pdf", "11.0", "Section 4 Legal and Regulatory Outline: Planned Growth Regulatory structure", "-345", 33, "pending review"),
]

P2_PENDING = [m for m in P2_MAP if m[6] == "pending review"]

UNDISCOVERED = {
 "Part2-4.pdf": {"url": BASE + "Part2-4.pdf", "size_bytes": 306971,
                 "checksum_sha256": "7d40a07b77cf1b821cc2656b47c8205c6eec0355a5a72edb92e94746bc242036",
                 "pages": 12, "http_status": 200,
                 "identity": "Planned Growth Strategy Part 2, Chapter 4.0, Examples of Mixed-Use Redevelopment Projects in Other Cities, printed pages 157 to 168."},
 "Part2-6.pdf": {"url": BASE + "Part2-6.pdf", "size_bytes": 241037,
                 "checksum_sha256": "41f9b0e7f4b2171b1640ab6788ad62c087c90bbb47438449182d3f46adf25e00",
                 "pages": 16, "http_status": 200,
                 "identity": "Planned Growth Strategy Part 2, Chapter 6.0, Financial Implementation of the Planned Growth Strategy Preferred Alternative, printed pages 211 to 218."},
 "Part2.pdf": {"url": BASE + "Part2.pdf", "size_bytes": 5469413,
               "checksum_sha256": "d703841bb7329a4431f85fef58044be200137a42d4b41339fad3388bfd006393",
               "pages": 144, "http_status": 200,
               "identity": "NOT the combined Planned Growth Strategy Part 2. Despite sitting in the pgs directory under the obvious combined-file name, its table of contents reads PART 2A Legal Parameters of Unification, PART 2B City and County Financing, PART 2C Functions, Services and Operations of City and County Government. It is Part 2 of a City and County governmental unification study, a different report entirely.",
               "measurement": "144 pages against the 347 pages of the eleven Preferred Alternative chapter files. Token coverage of four sampled Part 2 chapters inside it is only 0.5600 to 0.6132, which is shared municipal-finance vocabulary, not containment. Compare Part1.pdf, where every chapter measures 1.0000."},
}


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC, "content_kind": "PDF"}
    r.update(M[i])
    return r


approved = [
 {**row(P1_COMBINED, "approved for addition"),
  "title": "Planned Growth Strategy, Part 1: Existing Conditions, Development Trends, Alternative Scenarios, Infrastructure Costs, and Economic Impact (complete, 286 pages)",
  "description": "The City and County growth study's first volume documents Albuquerque development trends, tests alternative growth scenarios, prices the infrastructure each would require, reviews the policy and regulatory framework, and assesses the economic impact of growth.",
  "date": None,
  "pages": 286,
  "proposed_canonical_page": ZONING,
  "cross_listings": [
   {"page": PLANS, "reason": "The Planned Growth Strategy is the growth-management framework the sector and area plans were written under; it belongs beside them."},
   {"page": CAPITAL, "reason": "Part 1 Chapter 4 prices infrastructure capital costs by utility and is a capital-planning record as much as a land-use one."},
  ],
  "evidence": "286 pages and 47,215,522 bytes. Measured to be the exact concatenation of the seven Part 1 chapter files: their PDF page counts sum to 286 and each chapter's normalized token coverage inside this file is 1.0000. Prepared for the County of Bernalillo under County Manager Juan Vigil and the City of Albuquerque under Mayor Jim Baca.",
  "why_retained": "The canonical complete original of Part 1, which makes the seven chapter files components rather than separate documents. Retaining one 286-page original instead of seven fragments is the AGENTS.md canonical rule applied exactly.",
  "dating_note": "No printed date on the pages read. The enabling ordinances in this same directory run from Council Bill F/S O-02-39(2) through O-04-9, placing the study in the 2001 to 2004 period under Mayor Jim Baca. Do not assert a specific date the document does not carry.",
  "package_id": "pgs-part1"},
]

for i, fname, ch, covers, pages, status in [(m[0], m[1], m[2], m[3], m[5], m[6]) for m in P2_PENDING]:
    r = row(i, "approved for addition")
    r.update({
     "title": f"Planned Growth Strategy, Part 2 (Preferred Alternative) — Chapter {ch}: {covers.split(': ')[-1]}",
     "description": (f"Chapter {ch} of the City and County growth study's second volume sets out "
                     f"{covers.split(': ')[-1].lower()}, one of eleven chapters establishing and implementing "
                     "the Preferred Alternative for Albuquerque's future growth and its infrastructure."),
     "date": None,
     "pages": pages,
     "chapter": ch,
     "printed_pages": [m[4] for m in P2_MAP if m[0] == i][0],
     "package_id": "pgs-part2-preferred-alternative",
     "proposed_canonical_page": ZONING,
     "cross_listings": [{"page": PLANS, "reason": "Part of the growth-management framework the sector and area plans were written under."}],
     "evidence": f"{pages} pages. Printed page range read from the Part 2 table of contents inside Part2-1a.pdf, not inferred from the filename; see split_package_reconciliation.",
    })
    r["description_word_count"] = len(r["description"].split())
    approved.append(r)

approved[1]["contains_table_of_contents"] = (
 "This chapter file carries the Part 2 table of contents, which is the authority for every page range in "
 "split_package_reconciliation and the evidence that Chapter 3.0 exists and is missing.")

for r in approved:
    r.setdefault("description_word_count", len(r["description"].split()))

duplicates = []
for i, fname, n, covers, pages in P1_CHAPTERS:
    if IDX[i]['status'] != 'pending review':
        continue
    r = row(i, "duplicate")
    r.update({
     "title_for_reference": f"Planned Growth Strategy Part 1, chapter file {n} of 7 ({covers})",
     "pages": pages,
     "canonical_id": P1_COMBINED,
     "canonical_url": BASE + "Part1.pdf",
     "basis": (f"A chapter extract of the complete Part 1. Its normalized token coverage inside Part1.pdf is 1.0000, "
               f"and the seven chapter files' PDF page counts sum to exactly the 286 pages of Part1.pdf."),
     "hash_found_it": False,
    })
    duplicates.append(r)


def R(i, draft_title, pages, question, why, evidence):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why, "evidence": evidence})
    return r


ENACT_WHY = (
 "The sheet carries ENACTMENT NO. blank, so under the two standing checkpoint blockers it is the bill as "
 "considered rather than the law and must not be archived or presented as enacted. These three are the most "
 "consequential such files found anywhere in this run: they are the instruments that would have given the "
 "Planned Growth Strategy legal force, and whether they passed is precisely the question a reader of the study "
 "would need answered. They should be resolved as one group.")

rhr = [
 R("src-f7c7bd5b273def22",
   "Council Bill F/S O-02-39 (2): Adopting Elements of a Planned Growth Strategy to Guide the Management of City of Albuquerque Urban Growth; Identifying and Defining Certain Implementation Elements",
   14,
   "Locate the enacted ordinance. This is the instrument that would have adopted the Planned Growth Strategy itself.",
   ENACT_WHY,
   "14 pages, Fifteenth Council, sponsored by Michael Cadigan, enactment number blank."),
 R("src-68582bc4fe41fb4f",
   "Council Bill O-03-132: Adopting an Infrastructure and Growth Plan Pursuant to Section 14-13-2-3(B) ROA 1994",
   5,
   "Locate the enacted ordinance; decide together with F/S O-02-39(2) and O-04-9.",
   ENACT_WHY,
   "5 pages, Fifteenth Council, sponsored by Michael Cadigan, enactment number blank."),
 R("src-fcbe6a7ebcf916a1",
   "Council Bill O-04-9: Adopting Land Use Assumptions Pursuant to the State Development Fees Act and Section 14-13-1-4 ROA 1994",
   5,
   "Locate the enacted ordinance; decide together with the other two.",
   ENACT_WHY + " This one also connects to material already triaged: the land use assumptions it adopts under the State Development Fees Act are the same assumptions the Component Capital Improvements Plan resolutions R-2012-100 and R-2013-115, recommended for addition in the Development Review Services artifact of the same date, later amend.",
   "5 pages, Sixteenth Council, sponsored by Michael Cadigan, enactment number blank."),
]

excluded = [
 {**row("src-b443cbb28db8106b", "excluded"),
  "content_kind": "HTML; leading bytes are 3c 21 44 4f",
  "title_for_reference": "Planned Growth Strategy collection landing page",
  "exclusion_reason": ("The Plone collection landing page for this directory, not a document. Its only content is the "
                       "list of links to the files it contains plus site chrome."),
  "category": "collection landing page",
  "usefulness": ("It was fetched and parsed as part of this lane. Notably it does not list Part2-4.pdf, Part2-6.pdf or "
                 "Part2.pdf either, which is why those three were never discovered: the crawler followed the City's own "
                 "listing and the listing is incomplete. They were found by probing the filename sequence directly."),
 },
]

rows = approved + duplicates + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 19, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "planned-growth-strategy-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/pgs Planned Growth Strategy cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Planned Growth Strategy record set in the Albuquerque City Council document library at www.cabq.gov/council/documents/pgs.",
 "scope": "All 19 pending-review candidates in that directory. The directory also holds two records a prior lane already set to requires human review, src-0bd664780961f148 and src-0e133db868401e77; this artifact does not reclassify them but resolves the factual question the checkpoint blocker raises about the second, and recommends a disposition for both. It further records three files that exist on the City server and are absent from the inventory entirely.",
 "brief": "Discharge the checkpoint's open PGS split-package blocker by reconciling the complete package with the method recorded in the Volcano Heights artifact, and classify the directory.",
 "brief_finding": "The blocker is discharged with a hard answer, and it is not the answer the blocker anticipated. Part 1 is complete and a combined 286-page original exists, which makes its seven chapter files duplicates rather than a package to assemble. Part 2 is a genuine eleven-chapter package with no combined original, it is missing one chapter outright, and two of its chapters were never discovered into the inventory at all. The file that looks like the combined Part 2 is a different report about City and County unification.",
 "method": "Fetched all 19 candidates and the two prior-lane requires-human-review records without touching shared inventory state, and recorded exact byte length and SHA-256 for each. Extracted text with pdftotext -layout. Located and read the Part 2 table of contents printed inside Part2-1a.pdf and used it, rather than filenames, as the authority for every chapter page range. Verified Part 1 by two independent measures: PDF page-count arithmetic and per-chapter token coverage. Probed the filename sequence directly for chapters the City's own listing does not show, which is how three undiscovered files were found. Compared all checksums against the 1,612 checksummed inventory records.",
 "classification_only": True,
 "shared_state_written": [],
 "blocker_resolution": {
  "blocker_text": "src-0e133db868401e77 is PGS Part 2 Chapter 10; reconcile the complete split PGS package before any archival or visible use.",
  "source": "project-state/checkpoint.json, blockers array",
  "status": "RESOLVED as a factual question. The package is reconciled and mapped below. Two decisions remain and both are stated explicitly.",
  "part_1": {
   "finding": "COMPLETE, and a combined original exists. Part1.pdf (src-9aeb5f621800da58) is 286 PDF pages; the seven chapter files Part1-1 through Part1-7 have PDF page counts summing to exactly 286, and each chapter's normalized token coverage inside Part1.pdf is 1.0000.",
   "consequence": "There is nothing to assemble for Part 1. Retain the combined original and record the seven chapter files as duplicates of it. Six of the seven are pending and are classified that way in this artifact; the seventh, src-0bd664780961f148 (Part1-6), was set to requires human review by a prior lane and is recommended for the same duplicate treatment.",
   "recommended_action_for_src_0bd664780961f148": "Resolve to duplicate, canonical src-9aeb5f621800da58. Its coverage inside Part1.pdf is 1.0000, identical to its six siblings. Claude did not modify this record."
  },
  "part_2": {
   "finding": "INCOMPLETE, and no combined original exists. The Part 2 table of contents lists eleven numbered chapters. Ten are obtainable; Chapter 3.0, Preferred Alternative Summary, printed pages 131 to 156, returns HTTP 404 with body {\"error_type\": \"NotFound\"} and exists nowhere else in the inventory.",
   "aggravating_detail": "The missing chapter is the summary chapter. Of the eleven, 3.0 is the one a general reader would most likely want.",
   "second_finding": "Two of the ten obtainable chapters, 4.0 and 6.0, are not in the inventory at all. They return HTTP 200 from the City server but do not appear in the City's own collection listing, which is why the crawler never saw them.",
   "third_finding": "Part2.pdf exists at the obvious combined-file URL and is NOT the combined Part 2. See undiscovered_files. Anyone reconciling this package by assuming that file is the whole of Part 2 would be wrong.",
   "recommended_action_for_src_0e133db868401e77": "Resolve to approved for addition as Chapter 10.0 of the Part 2 package, on the same footing as the eight pending chapters recommended here. The reconciliation the blocker required is now done and nothing about this record is uncertain any more. Claude did not modify it.",
   "decisions_that_remain": [
    "Add Part2-4.pdf and Part2-6.pdf to the inventory as new candidates before any Part 2 archival. Without them the package is missing three chapters rather than one.",
    "Decide how to present a package with a permanently missing chapter. The Volcano Heights artifact set the rule that a partial archive of a split plan must not present an incomplete document as complete. Here completeness is not achievable, so the answer cannot be to withhold: it must be to publish the ten obtainable chapters with an explicit note that Chapter 3.0, Preferred Alternative Summary, pages 131 to 156, is not available from the City."
   ]
  },
  "method_note": "The method is the one recorded in the Volcano Heights artifact: read each part's printed page range from the document itself, never from the filename, then check the ranges join. Applied here it also exposed the gap, which filename inspection alone would have shown as a missing number without proving a chapter existed to fill it. The Part 2 table of contents is what proves Chapter 3.0 exists."
 },
 "split_package_reconciliation": {
  "pgs_part_1": {
   "result": "COMPLETE with a combined original",
   "combined_id": P1_COMBINED, "combined_pages": 286,
   "combined_size_bytes": M[P1_COMBINED]["size_bytes"],
   "combined_checksum_sha256": M[P1_COMBINED]["checksum_sha256"],
   "chapter_manifest": [{"chapter": n, "id": i, "file": f, "covers": c, "pdf_pages": p,
                         "size_bytes": M[i]["size_bytes"], "checksum_sha256": M[i]["checksum_sha256"],
                         "coverage_in_combined": 1.0,
                         "inventory_status_before": IDX[i]['status']}
                        for i, f, n, c, p in P1_CHAPTERS],
   "page_arithmetic": "20 + 51 + 11 + 86 + 72 + 31 + 15 = 286, equal to the combined file's page count.",
   "chapter_bytes_total": sum(M[i]["size_bytes"] for i, _, _, _, _ in P1_CHAPTERS)
  },
  "pgs_part_2_preferred_alternative": {
   "result": "INCOMPLETE, no combined original",
   "authority_for_page_ranges": "The Part 2 table of contents printed on PDF pages 5 to 7 of Part2-1a.pdf.",
   "chapter_manifest": [
    {"chapter": ch, "id": i, "file": f, "title": covers, "printed_pages": pr, "pdf_pages": pp,
     "state": st,
     **({"size_bytes": M[i]["size_bytes"], "checksum_sha256": M[i]["checksum_sha256"]} if i in M else {}),
     **({"size_bytes": UNDISCOVERED[f]["size_bytes"], "checksum_sha256": UNDISCOVERED[f]["checksum_sha256"]} if f in UNDISCOVERED and i and i.startswith("UNDISCOVERED") else {})}
    for i, f, ch, covers, pr, pp, st in P2_MAP],
   "gap": {"chapter": "3.0", "title": "Preferred Alternative Summary", "printed_pages": "131-156",
           "estimated_length_pages": 26,
           "http_status": 404,
           "response_body": "{\"error_type\": \"NotFound\"}",
           "searched": "The inventory holds no copy under any name; the City's collection listing does not offer it; the filename sequence probe returns 404."},
   "obtainable_chapters": 10, "total_chapters": 11,
   "manifest_entry_count": 12,
   "counting_note": ("The manifest has twelve file entries for eleven chapters because Chapter 1.0 is itself split "
                     "across two files, Part2-1a.pdf and Part2-1b.pdf. Of the twelve entries: eight are pending "
                     "candidates recommended for addition here, one is the prior-lane requires-human-review record "
                     "src-0e133db868401e77 recommended for the same treatment, two are files that exist on the City "
                     "server but are absent from the inventory, and one is the chapter that does not exist at all."),
   "entry_states": {"pending review, recommended for addition": 8,
                    "prior-lane requires human review, recommended for addition": 1,
                    "exists on server, not in inventory": 2,
                    "absent from source": 1}
  }
 },
 "undiscovered_files": {
  "count": 3,
  "why_this_matters": "All three return HTTP 200 from the City server and none appears in the City's own Plone collection listing for this directory. A crawler that follows the published listing cannot find them. They were found by probing the chapter filename sequence directly.",
  "files": UNDISCOVERED,
  "recommended_action": "Add Part2-4.pdf and Part2-6.pdf to the inventory as new candidates; they are chapters of a package this artifact recommends retaining. Add Part2.pdf as a new candidate under its true identity, a City and County unification study, not as a Planned Growth Strategy file. This artifact does not create inventory records.",
  "generalisation": "This is the first cluster in this run where a City collection listing was proved incomplete against its own server. Where a directory's files are numbered, probe the sequence rather than trusting the listing."
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_measurement": 7,
  "note": "Seven relationships, all between the Part 1 chapter files and the combined Part 1, and hashing finds none of them: a chapter extract shares no bytes with the volume it came from. They were established by token coverage at 1.0000 and corroborated by exact page arithmetic. The same measurement applied to the file named Part2.pdf returns 0.56 to 0.61 and correctly refuses to call it a container."
 },
 "integration_flags": [
  {"severity": "blocker-discharge",
   "affects": ["src-0e133db868401e77", "src-0bd664780961f148"],
   "finding": "The checkpoint blocker requiring reconciliation of the split PGS package is discharged above. Both prior-lane requires-human-review records in this directory now have a clear disposition: src-0bd664780961f148 is a duplicate of the combined Part 1, and src-0e133db868401e77 is Chapter 10.0 of the Part 2 package and should be approved with its ten siblings.",
   "recommended_action": "Apply both dispositions and close the blocker, recording the two remaining decisions from blocker_resolution.part_2.decisions_that_remain rather than leaving the blocker open for them."},
  {"severity": "discovery-gap",
   "affects": ["the crawl method generally"],
   "finding": "Part2-4.pdf, Part2-6.pdf and Part2.pdf exist on the City server, return HTTP 200, and are absent from both the City's collection listing and the inventory. Two of them are chapters of a document this artifact recommends retaining.",
   "recommended_action": "Add the two chapters as candidates before any Part 2 archival, add Part2.pdf under its true identity, and consider a sequence-probe pass over other numbered City directories. This is a crawler finding, not a classification one."},
  {"severity": "permanent-gap",
   "affects": ["the PGS Part 2 package"],
   "finding": "Chapter 3.0, Preferred Alternative Summary, pages 131 to 156, is not obtainable from the City. It is the summary chapter of the volume.",
   "recommended_action": "Publish the ten obtainable chapters with an explicit, visible note naming the missing chapter and its page range. Do not present the package as complete, and do not withhold ten chapters because the eleventh is lost."},
  {"severity": "filename-trap",
   "affects": ["Part2.pdf"],
   "finding": "A file named Part2.pdf sits in the pgs directory and is a City and County unification study, not the combined Planned Growth Strategy Part 2. Its sibling Part1.pdf, by contrast, genuinely is the combined Part 1. The same naming convention means two different things in one directory.",
   "recommended_action": "Never infer a combined-volume relationship from a filename. Part1.pdf earned that description by measuring 1.0000 coverage and exact page arithmetic; Part2.pdf fails both tests."},
  {"severity": "storage",
   "affects": [P1_COMBINED] + [m[0] for m in P2_PENDING],
   "finding": f"The nine approved records total {approved_bytes:,} bytes, about 98 mebibytes, dominated by the 47,215,522-byte combined Part 1 and the two 23-megabyte Part 2 chapter-1 files. Retaining the combined Part 1 instead of its seven chapter files saves nothing on storage, {sum(M[i]['size_bytes'] for i, _, _, _, _ in P1_CHAPTERS):,} bytes against {M[P1_COMBINED]['size_bytes']:,}, but it is still right on document-integrity grounds.",
   "recommended_action": "Size this into the upload queue deliberately. Together with the Volcano Heights batch the two artifacts now account for roughly 240 megabytes of proposed archival, against the 67,526,043 bytes already awaiting approval in the checkpoint's existing blocker."},
  {"severity": "coverage-gap",
   "affects": ["the Planned Growth Strategy subject"],
   "finding": "The Planned Growth Strategy is the growth-management framework Albuquerque adopted elements of in the early 2000s, and the site carries nothing about it. Part 1's Chapter 4 prices infrastructure capital costs by utility, which is capital-planning material the site does cover elsewhere.",
   "recommended_action": "Consider a Growth Management section rather than filing eleven records into an existing list. The three enabling ordinances, once their enactment status is resolved, belong with the study."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "superseded": 0
 },
 "link_check": {"checked": 21, "http_200": 21, "failed": 0,
                "probe_checked": 7, "probe_http_200": 3, "probe_http_404": 4,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 19 pending candidates and the 2 prior-lane requires-human-review records. A further seven filename-sequence probes were run for chapters the listing does not show: Part2-3, Part2-4, Part2-6, Part2, Part2-1, Part2-12 and Part1-8.",
                "containers_verified": "20 genuine PDFs and one HTML collection page by leading bytes."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": f"All 9 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, and that figure will rise once Part2-4.pdf and Part2-6.pdf are added as candidates and Part2-10 is resolved. The Part 2 chapters must be archived as a set: a partial archive of an already-incomplete package would compound the gap.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every duplicate row carries a canonical_id resolving to the retained combined Part 1. The 9 approved rows each carry a title, a 20-to-50-word description, a proposed_canonical_page and cross_listings; all carry a null date because no file in this directory prints one, and none may be given an asserted date. The eight Part 2 chapter rows share a package_id and carry their printed page ranges. Three rows are requires human review under the standing enactment blockers and should be decided as one group. Two records outside this artifact's classification scope have explicit recommended dispositions in blocker_resolution. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy", "no inventory record created for the three undiscovered files"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
