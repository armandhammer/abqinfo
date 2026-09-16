"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\volcano-heights-sdp-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\vh\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/Volcano%20Heights%20Sector%20Development%20Plan/'

AREA = 'content/development-land-use/area-sector-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")

PARTS = [
 ("src-32dd217ff7b0f446", "01_a-bi-viii.pdf", "cover, credits, contents a to bi, and Purpose and Authority at viii", 10),
 ("src-cfc70e1dc6c64444", "02_ix1-8.pdf", "ix and 1-8: Section One Planning Framework, plan area, natural and cultural features", 9),
 ("src-7baaf8b0bd32bd1f", "03_9-15.pdf", "9-15: geological and soil conditions, treatment of natural features", 7),
 ("src-f4d73106bafbe0b5", "04_16-24.pdf", "16-24: platting and zoning, Comprehensive Plan relationship", 9),
 ("src-61f42195cca58f3d", "05_25-37.pdf", "25-37: Section II land use plans and policies", 13),
 ("src-83a16b999f89c788", "06_38-43.pdf", "38-43: Section Two Plan Elements opening", 6),
 ("src-9c2f60d4cf5ff230", "07_44-57.pdf", "44-57: Section II continued", 14),
 ("src-71e61e77151ea323", "08_58-64.pdf", "58-64: transit network", 7),
 ("src-d17257eb10d8932e", "09_65-75.pdf", "65-75: Section III", 11),
 ("src-32e7c0fe9f8fd5ff", "10_76-87.pdf", "76-87: permitted and limited uses", 12),
 ("src-5347e9957ec0b1ea", "11_88-103.pdf", "88-103: Section IV", 16),
 ("src-5576e14822e38925", "12_104-114.pdf", "104-114: Section V", 11),
 ("src-e4cc1044a7aaeef4", "13_115-128.pdf", "115-128: Section VI", 14),
 ("src-f278bf4efaeb6563", "14_129-147.pdf", "129-147: Section VII", 19),
 ("src-1a310c59c9947664", "15_148-161.pdf", "148-161: Appendix", 14),
 ("src-34471105d1864d8c", "16_162-182.pdf", "162-182: Appendix G and remaining appendices", 21),
]
PART_IDS = [p[0] for p in PARTS]
PART_BYTES = sum(M[i]["size_bytes"] for i in PART_IDS)
ANCHOR = PARTS[0][0]


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC, "content_kind": "PDF"}
    r.update(M[i])
    return r


approved = []
for n, (i, fname, covers, pages) in enumerate(PARTS, start=1):
    r = row(i, "approved for addition")
    r.update({
     "title": f"Volcano Heights Sector Development Plan, Final, October 2006 — Part {n:02d} of 16 ({covers.split(':')[0]})",
     "description": ("Part " + f"{n:02d}" + " of the sixteen-part City sector development plan for Volcano Heights on the Northwest Mesa, "
                     "covering " + covers.split(': ', 1)[-1] + ", within the plan's land use, zoning, transportation, and urban design framework."),
     "date": "2006-10",
     "pages": pages,
     "covers": covers,
     "part_number": n,
     "package_id": "volcano-heights-sdp-2006",
     "package_anchor": ANCHOR,
     "proposed_canonical_page": AREA,
     "proposed_canonical_section": "Southwest Mesa and Volcano Area",
     "cross_listings": [],
     "evidence": f"{pages} pages. Part of a contiguous sixteen-part split verified page by page; see split_package_reconciliation.",
    })
    r["description_word_count"] = len(r["description"].split())
    approved.append(r)

approved[0]["date_basis"] = ("The title page reads \"VOLCANO HEIGHTS SECTOR DEVELOPMENT PLAN, FINAL, October 2006\". "
                             "It names the planning team: Matt Taecker of Taecker Urban Design & Planning as principal, "
                             "Signe Rich, Jolene Wolfley, William Dennis, Mark White of Freilich Leitner & Carlisle, "
                             "Louis J. Colombo of City Council Services, and Joel Wooldridge of the Planning Department.")
approved[0]["why_retained"] = (
 "The anchor part of the only complete copy of this plan anywhere in the inventory, and it fills a gap the site "
 "already names: content/development-land-use/area-sector-plans.md carries the Volcano Trails plan and a 2014 "
 "transportation-amendment presentation whose own description says it amends \"the Volcano Cliffs, Volcano Heights, "
 "Volcano Trails, and West Side plans\". The Volcano Heights plan itself was missing.")

approved += [
 {**row("src-90d9a2983c0bb697", "approved for addition"),
  "title": "Environmental Planning Commission Staff Report on the Volcano Heights Sector Development Plan (Projects 06EPC00697 and 06EPC00698)",
  "description": "The City staff report analyses the proposed Volcano Heights Sector Development Plan against the applicable criteria and recommends approval based upon conditions, giving the professional planning assessment behind the plan's adoption.",
  "date": "2006",
  "pages": 89,
  "proposed_canonical_page": AREA,
  "proposed_canonical_section": "Southwest Mesa and Volcano Area",
  "cross_listings": [],
  "evidence": "89 pages, Planning Project Numbers 06EPC00697 and 06EPC00698, Case 1004905, staff planner Louis Colombo, Deputy Director of City Council Services. The recommendation line reads APPROVAL BASED UPON CONDITIONS.",
  "why_retained": "The reasoning behind the plan, which the plan itself does not contain. The site already treats this class of record as retainable: it publishes the Volcano Trails Environmental Planning Commission Official Notice of Decision alongside the Volcano Trails plan."},

 {**row("src-26909d4cd89806d4", "approved for addition"),
  "title": "Response to Protests Regarding the Volcano Heights Sector Development Plan",
  "description": "The City response document answers the formal protests lodged against the Volcano Heights Sector Development Plan, setting out each objection raised and the planning response to it before the plan went to Council.",
  "date": "2006",
  "pages": 13,
  "proposed_canonical_page": AREA,
  "proposed_canonical_section": "Southwest Mesa and Volcano Area",
  "cross_listings": [],
  "evidence": "13 pages headed \"Response to Protests regarding Volcano Heights Sector Development Plan, Overview\".",
  "why_retained": "The only record in the cluster of what was argued against the plan and how the City answered. A plan record that carries only the proponent's case is a weaker archive than one that carries the objections too."},

 {**row("src-2f5e70d5a655369e", "approved for addition"),
  "title": "Albuquerque/Bernalillo County Comprehensive Plan, As Adopted 1988 and Amended Through January 2002",
  "description": "The joint City and County comprehensive plan is the Rank I policy document that governed Albuquerque land use for three decades, consolidated here as adopted in August 1988 and amended through the January 2002 County resolutions.",
  "date": "2002-01-22",
  "pages": 277,
  "proposed_canonical_page": ZONING,
  "cross_listings": [{"page": AREA, "reason": "Every sector development plan in that page's collection, including Volcano Heights, was written to conform to this Rank I plan and is unreadable without it."}],
  "evidence": "277 pages. The title page records City Enactment No. 138-1988 of August 30, 1988 and Bernalillo County Resolution No. 103-88 of August 23, 1988, then lists twelve amendments through Bernalillo County Resolutions 2, 3, 6 and 7 of 2002, all dated January 22, 2002. Published under Mayor Martin J. Chavez with Brad Winter as Council President.",
  "why_retained": "The most significant find in this cluster and the reason it should not be treated as a single-plan directory. The Albuquerque/Bernalillo County Comprehensive Plan appears in the inventory only as twelve lineage stubs, all terminal, none carrying a URL or any bytes: lin-13291f6314d11937, lin-56d8cb0454ac470d, lin-5bde064f99c9f470, lin-719dd1a871998539, lin-a015dff846665c02, lin-a5ac6e5320f82ddb, lin-a848983617f571aa, lin-b514d37381919aea, lin-b6984a912acaa6b9, lin-c0f031ceb3a62c28, lin-fbae987aedf73234 and lin-fbc11f5ed0807d12. Documents across the archive cite this plan and the archive does not hold it. This copy is the actual document.",
  "currency_warning": "This edition was superseded by the 2017 Albuquerque/Bernalillo County Comprehensive Plan adopted alongside the Integrated Development Ordinance on 2017-11-13, the ordinance the Planning UDD lane recorded as renaming the historic overlay zones. The title must carry the 1988-to-2002 span so no reader takes it as current policy.",
  "package_note": "This is a reference copy filed with the sector plan, not part of the sixteen-part split. It is a separate document with its own identity."},
]

rhr = [{
 **row("src-e9b93dd7ac244a12", "requires human review"),
 "draft_title": "Council Bill R-06-86: Adopting the Volcano Heights Sector Development Plan as a Rank 3 Sector Development Plan and Amending the Zone Map",
 "pages": 29,
 "question_for_human": "Locate the enacted resolution adopting the Volcano Heights Sector Development Plan. Unlike the other pre-enactment files held in this run, here the adoption is independently evidenced, so the question is which enactment number to cite rather than whether adoption happened.",
 "why_not_decided_here": (
  "The sheet carries ENACTMENT NO. blank, so under the two standing checkpoint blockers it is the bill as considered "
  "rather than the law and must not be archived or presented as enacted. What makes this case different from the seven "
  "substitutes held in the council-documents artifact is that the plan it adopts demonstrably was adopted: the plan "
  "itself is marked FINAL and dated October 2006, the Environmental Planning Commission staff report recommends "
  "approval based upon conditions, and a formal response to protests was prepared, which only happens on the way to a "
  "Council vote. Withholding the sixteen plan parts over this would be wrong; withholding the resolution until its "
  "enactment number is found is exactly right."),
 "evidence": "29 pages, Seventeenth Council, Council Bill No. R-06-86, sponsored by Michael Cadigan. The title adopts the plan as a Rank 3 Sector Development Plan, amends the zone map as specified in the plan, approves changes to identified plans, and provides guidance, a work program, and potential funding sources.",
 "does_not_block": "The sixteen plan parts, the staff report, the response to protests, and the Comprehensive Plan are all recommended for addition and none depends on this record.",
}]

for r in approved:
    r["description_word_count"] = len(r["description"].split())

rows = approved + rhr
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
total_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "volcano-heights-sdp-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/Volcano Heights Sector Development Plan cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Volcano Heights Sector Development Plan record set in the Albuquerque City Council document library.",
 "scope": "All 20 pending-review candidates in that directory, which is the entire pending set. One record in the directory, src-fd25896c3bbded91, is a paginated listing URL already terminal-excluded. Completing this artifact leaves the directory with no non-terminal records.",
 "brief": "Separate the adopted sector development plan and its supporting studies from meeting handouts, checking against the already-validated Volcano Trails records.",
 "brief_finding": "There are no meeting handouts here at all. Sixteen of the twenty files are one 182-page plan cut into contiguous page ranges, and the other four are its staff report, its response to protests, its adopting bill, and a full copy of the 1988 Albuquerque/Bernalillo County Comprehensive Plan. That last file is the find: the Rank I plan that governed Albuquerque land use for three decades exists in the inventory only as twelve lineage stubs with no bytes and no URL, and this directory holds the actual document.",
 "method": "Fetched all 20 candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each; all 20 are genuine PDFs by leading bytes and all yield extractable text. Read the running header of every plan part to recover its printed page range, then verified the sixteen ranges join end to end with no gap and no overlap. Compared all 20 checksums against the 1,612 checksummed inventory records and against each other. Checked the plan's relationship to the already-validated Volcano Trails and Volcano cross-section records, and searched the inventory for existing Comprehensive Plan holdings.",
 "classification_only": True,
 "shared_state_written": [],
 "split_package_reconciliation": {
  "why_this_matters": "The checkpoint carries an open blocker requiring exactly this work for a different document: \"src-0e133db868401e77 is PGS Part 2 Chapter 10; reconcile the complete split PGS package before any archival or visible use.\" This is that reconciliation, done for Volcano Heights.",
  "result": "COMPLETE AND CONTIGUOUS. The sixteen parts carry printed page ranges that join end to end from page 1 through page 182 with no gap and no overlap, plus front matter a to bi and viii in part 01. Nothing is missing.",
  "verification": "Page ranges were read from each part's own running header, which prints \"Volcano Heights Sector Development Plan - <page>\" on every page, not inferred from filenames. Checked programmatically: zero gaps, last page 182.",
  "manifest": [{"part": n, "id": i, "file": f, "covers": c, "pages": p,
                "size_bytes": M[i]["size_bytes"], "checksum_sha256": M[i]["checksum_sha256"]}
               for n, (i, f, c, p) in enumerate(PARTS, start=1)],
  "package_total_bytes": PART_BYTES,
  "package_total_pages": 182,
  "anchor_id": ANCHOR,
  "integration_rule": "These sixteen records are one document. They must be added to a page as a single plan entry with its parts listed beneath it, never as sixteen separate plan entries, and no part may be published without the others."
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "note": "No duplicate or supersession relationship exists inside this directory: every part is a distinct page range of one document. The two existing Volcano Heights records in the inventory are unrelated to these: src-428c2b8d791a054f and src-e83d30ce68171820 are roadway cross-section drawings from the Development Process Manual XSections directory, not plan text."
 },
 "integration_flags": [
  {"severity": "storage",
   "affects": PART_IDS,
   "finding": f"The sixteen plan parts total {PART_BYTES:,} bytes, roughly 123 mebibytes, for a single 182-page document. Individual parts run to 16.5 megabytes for nineteen pages, which means the scans are very high resolution. Adding the Comprehensive Plan and the staff report brings the batch to {total_bytes:,} bytes.",
   "recommended_action": "This is the largest single archive decision raised by any artifact in this run and it needs an explicit answer before upload. The checkpoint already carries an open blocker for 17 originals totalling 67,526,043 bytes awaiting separate R2 upload approval; this batch is more than twice that on its own."},
  {"severity": "provenance-question",
   "affects": PART_IDS,
   "finding": "The City publishes this plan only as sixteen separate files. There is no single-file original anywhere in the inventory or at this source. Recombining the parts into one PDF would produce a document whose bytes and checksum match nothing the City ever published.",
   "recommended_action": "Archive the sixteen originals as they are, each with its own verified checksum, and present them as one plan with sixteen parts. Do not create a recombined file and archive that as the original: the archival standard in AGENTS.md requires the archived object's size and SHA-256 to be verifiable against the authoritative source, and a recombination is a derived work. If a combined reading copy is ever wanted it must be labelled as a derived convenience copy, separately from the archived originals."},
  {"severity": "coverage-gap",
   "affects": ["src-2f5e70d5a655369e"],
   "finding": "The Albuquerque/Bernalillo County Comprehensive Plan is cited throughout the archive and held nowhere in it. The inventory carries twelve lineage stubs for it, all terminal, none with a URL or bytes. This 277-page copy as adopted 1988 and amended through January 2002 is the document those stubs point at.",
   "recommended_action": "Treat it as a find in its own right rather than as supporting material for a sector plan. It should also prompt a targeted search for the 2017 Albuquerque/Bernalillo County Comprehensive Plan that superseded it, which is likewise absent."},
  {"severity": "placement",
   "affects": PART_IDS + ["src-90d9a2983c0bb697", "src-26909d4cd89806d4"],
   "finding": "content/development-land-use/area-sector-plans.md already has a Southwest Mesa and Volcano Area section holding the Volcano Trails plan, its EPC notice of decision, and a 2014 transportation-amendment presentation whose description explicitly names the Volcano Heights plan among those it amends. The plan that description refers to has been missing from the site.",
   "recommended_action": "Add Volcano Heights beside Volcano Trails in that section, matching the existing pattern of plan plus decision record. The 2014 amendment entry already there should then be cross-referenced to it."},
  {"severity": "blocker-consistent",
   "affects": ["src-e9b93dd7ac244a12"],
   "finding": "The adopting bill R-06-86 carries a blank enactment number, so it is held under the standing blockers. Unlike every other such case in this run, the adoption itself is independently evidenced by the plan's FINAL marking, the staff report's approval recommendation, and the existence of a formal response to protests.",
   "recommended_action": "Find the enactment number rather than the fact. Nothing else in the batch depends on it, and the plan parts should not wait for it."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "duplicate": 0, "superseded": 0, "excluded": 0,
  "approved_breakdown": {"plan parts of one 182-page document": 16, "supporting records": 2, "comprehensive plan": 1}
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 20 files are genuine PDFs by leading bytes and all yield extractable text; no rendering was needed."},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "archival_note": f"All 19 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {total_bytes:,} bytes. That is by far the largest of any batch in this run and must not be folded into a routine upload; see integration_flags. Sixteen of the nineteen are parts of one document and either all sixteen are archived or none is: a partial archive of a split plan would present an incomplete document as complete.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id because the directory holds no duplicate or supersession relationship. The sixteen plan parts share a package_id, a package_anchor and a part_number, and split_package_reconciliation carries the verified manifest with per-part page ranges and checksums; treat them as one document. The one requires-human-review row states its question and explicitly does not block the rest of the batch. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != "approved_breakdown"}}))
