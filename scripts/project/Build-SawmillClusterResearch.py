"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\sawmill-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\sm\fetch.log')

FINAL = 'src-96e192e3bb793470'       # 11.10.08 final release
OCT_A = 'src-4de7fbdd147c8c66'       # 10.29.08 v2 reduced
OCT_B = 'src-e54536e42de9edcc'       # 1-prefixed re-encoding of the same release
FEB = 'src-a02a7c98367d7095'         # February 15 2008 "update"
MRA_PLAN = 'src-6d2bd024ade8862e'    # validated + R2 + published Sawmill/Wells Park MRA plan

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw, v = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    RAW[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


rhr = [{
 **row(FINAL, "requires human review"),
 "priority": 1,
 "draft_title": "Exhibit A to the Sawmill/Wells Park Sector Plan Amendment, October 27, 2008: Land Use and Transportation Section with Master Circulation Plan (final release, November 10, 2008)",
 "pages": 42,
 "evidence": ("Born-digital PDF with a full text layer, 42 pages, 8,448,729 bytes. Headed \"SAWMILL/WELLS PARK SECTOR "
              "PLAN AMENDMENT October 27, 2008 / EXHIBIT A / Sawmill Wells Park Sector Plan Amendment / Master "
              "Circulation Plan (Adopted ___________)\". Its opening clause states that the amendment \"supersedes "
              "conflicting policies, recommendations, or regulations in the Plan\", and specifically Section 2, "
              "Right-of-Way and Street Classification, subsections 2.b, 2.c and 2.d, and Section 3, Street Design, "
              "subsection 3.d. Part I sets out near-term and long-term roadway connectivity plans and streetscape, "
              "roadway and intersection design policies and regulations."),
 "question_for_human": ("Locate the instrument that adopted this amendment, and the Sawmill/Wells Park Sector "
                        "Development Plan it amends. Neither is held."),
 "why_not_decided_here": ("The adoption line is blank on its face — \"Master Circulation Plan (Adopted "
                          "___________)\" — and this is regulation, not description: it states which subsections of "
                          "an adopted sector plan it overrides. Publishing it would present unadopted street "
                          "classification and design regulation as if it governed. That is the same class the two "
                          "standing checkpoint blockers hold back, reached here through an exhibit rather than a bill."),
 "outcome_search": ("Applying the standing lesson, no adopted outcome is held. The inventory contains no Sawmill/Wells "
                    "Park Sector Development Plan, no adopted amendment to it, and no adopting resolution. The only "
                    "Sawmill planning record the archive holds is " + MRA_PLAN + ", the Sawmill/Wells Park Community "
                    "Metropolitan Redevelopment Area Plan of 2005, published at "
                    "content/development-land-use/redevelopment-plans.md line 183 — a different instrument under a "
                    "different statute, not the sector plan."),
 "if_it_resolves": ("It is worth publishing. Forty-two pages of connectivity plans and street design regulation for "
                    "the Sawmill and Wells Park area exist nowhere else in the archive, and the area's redevelopment "
                    "plan is already on the site without them."),
 "related_lead": ("src-385036989b8d1925, \"EPC Notice for Sawmill Wells Park Hearing\", sits pending in the District 2 "
                  "directory. An Environmental Planning Commission hearing notice for this area is the kind of record "
                  "that would date the adoption."),
}]


def S(i, title, pages, basis, measurement, extra=None):
    r = row(i, "superseded")
    r.update({"title_for_reference": title, "pages": pages,
              "canonical_id": FINAL,
              "canonical_url": IDX[FINAL].get('direct_file_url'),
              "canonical_state": "requires human review in this batch, under the standing adoption blockers",
              "basis": basis, "measurement": measurement, "hash_found_it": False})
    if extra:
        r.update(extra)
    return r


superseded = [
 S(OCT_A,
   "Exhibit A to the Sawmill/Wells Park Sector Plan Amendment, October 27, 2008 (October 29 release)",
   42,
   "An earlier release of the same amendment, superseded by the November 10 final.",
   ("Normalized-text ratio 0.9996 against the final, token coverage 0.9994 of the final inside it. The 61-line "
    "difference is not cosmetic throughout: the final fixes garbled typography — \"2.aEstern Gateway\" becomes \"2. "
    "Eastern Gateway\" and \"Center /Corridor - rFontage on Transit Corridor\" becomes \"Center / Corridor - Frontage "
    "on Transit Corridor\" — and it also removes map annotations present in this release, including an \"Interim "
    "Connection Bellamah Ave NW between Aspen Ave and Arbolera de Vida\" and a \"Temporary connection to connect "
    "Sawmill Land Trust property and 12th Street Corridor\"."),
   extra={"why_it_matters": "Those removed annotations describe interim and temporary road connections. A reader taking this release as current would describe connections the City had dropped from the final."}),

 S(OCT_B,
   "Exhibit A to the Sawmill/Wells Park Sector Plan Amendment, October 27, 2008 (re-encoded copy of the October 29 release)",
   42,
   "A re-encoding of the same October release, superseded with it.",
   ("Text-identical to " + OCT_A + ": normalized-text ratio 1.0000, token coverage 1.0000 both ways, and the "
    "normalized strings compare exactly equal. The files differ only in encoding, 14,796,082 bytes here against "
    "10,433,789 — this copy is 4,362,293 bytes larger for the same 42 pages."),
   extra={"filename_note": ("The City distinguishes them only by a leading \"1\" on the filename: "
                            "1sawmill_land_use_transportation_section_2_10.29.08_v2reduced.pdf against "
                            "sawmill_land_use_transportation_section_2_10.29.08_v2reduced.pdf. The same convention "
                            "marked the later EPC draft in dnasdp-cluster-research-2026-09-12.json, where the "
                            "1-prefixed files were the newer package. Here it marks a fatter re-encoding of the same "
                            "release, so the convention is not reliable and the files must be compared."),
          "not_called_a_duplicate": ("Byte-different, so the duplicate status reserved for byte-identical copies in "
                                     "councilor-district-1-cluster-research-2026-09-12.json does not apply. Both are "
                                     "superseded by the same canonical, which states the relationship without "
                                     "asserting byte identity that does not hold.")}),

 S(FEB,
   "Exhibit A to the Sawmill/Wells Park Sector Plan Update, February 15, 2008: Land Use and Transportation Section standalone report",
   39,
   "The February stage of the same work, before it was recast as an amendment.",
   ("Normalized-text ratio 0.9771 against the final, token coverage 0.8387 of this file inside it. Same structure and "
    "the same operative clause listing Section 2 subsections 2.b, 2.c, 2.d and Section 3 subsection 3.d, but the "
    "instrument is named differently: \"SAWMILL/WELLS PARK SECTOR PLAN UPDATE February 15, 2008\" and \"This update to "
    "the Sawmill Wells Park Sector Development Plan supersedes any conflicting policies\", where the October and "
    "November files read AMENDMENT throughout. Three fewer pages."),
   extra={"note": "Its own text slips between the two words — it calls itself an update in the heading and \"this amendment\" two lines later — which is the clearest sign the two are one work at two stages rather than two instruments."}),
]

excluded = [{
 **row("src-915026ad52b7bce2", "excluded"),
 "title_for_reference": "Sawmill documents collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
}]

rows = rhr + superseded + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 5, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
avoided = sum(r["size_bytes"] for r in superseded)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "sawmill-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/sawmill-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The Sawmill/Wells Park sector plan amendment file in the Albuquerque City Council library: one document in four releases.",
 "scope": "All 5 pending-review candidates, which is every record in the directory. Nothing here is terminal.",
 "brief": "Run the standard opening sequence, and apply the new enactment-number method — read later legislation's recitals, not the plans those instruments adopted — to any legislative file found.",
 "brief_finding": ("The method had nothing to work with here and that is itself the answer: this directory contains no "
                   "legislation at all. All four documents are the same exhibit — the Land Use and Transportation "
                   "Section with the Master Circulation Plan — at four release stages between February and November "
                   "2008, and every one of them carries the line \"Master Circulation Plan (Adopted ___________)\" "
                   "with the date left blank. There is no later bill to read recitals from, because the adopting "
                   "instrument is not in the inventory in any form."),
 "second_finding": ("The version chain resolves cleanly and inverts the usual size intuition for the third time in "
                    "this run. The canonical is the smallest file in the directory: the November 10 final is "
                    "8,448,729 bytes, while the superseded October release is 10,433,789 and its re-encoded twin "
                    "14,796,082."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 5 candidates and measured byte length and SHA-256 "
            "from the fetched bytes. Compared all checksums within the cluster and against the 1,612 checksummed "
            "inventory records: no collisions either way, including between the two files that turn out to be "
            "text-identical. Compared all four documents pairwise on normalized text and token coverage, then diffed "
            "the two closest line by line to see whether the differences were cosmetic. Read each cover and operative "
            "clause. Searched the inventory and the published site for the sector plan, for an adopted amendment, and "
            "for an adopting resolution."),
 "classification_only": True,
 "shared_state_written": [],
 "version_chain": {
  "one_document_four_releases": [
   {"stage": 1, "id": FEB, "label": "Sector Plan Update, February 15, 2008", "pages": 39, "bytes": M[FEB]["size_bytes"]},
   {"stage": 2, "id": OCT_A, "label": "Sector Plan Amendment, October 27 2008, October 29 release", "pages": 42, "bytes": M[OCT_A]["size_bytes"]},
   {"stage": 2, "id": OCT_B, "label": "the same October release, re-encoded", "pages": 42, "bytes": M[OCT_B]["size_bytes"]},
   {"stage": 3, "id": FINAL, "label": "final release, November 10 2008", "pages": 42, "bytes": M[FINAL]["size_bytes"]},
  ],
  "measurements": ("February against final: ratio 0.9771, coverage 0.8387. October against final: ratio 0.9996, "
                   "coverage 0.9994. The two October files against each other: ratio 1.0000 and normalized strings "
                   "exactly equal, but 4,362,293 bytes apart."),
  "what_changed_at_the_last_stage": ("Typography fixes — \"2.aEstern Gateway\" to \"2. Eastern Gateway\", "
                                     "\"rFontage\" to \"Frontage\" — and the removal of two map annotations, an "
                                     "interim connection on Bellamah Avenue NW between Aspen Avenue and Arbolera de "
                                     "Vida, and a temporary connection between Sawmill Land Trust property and the "
                                     "12th Street Corridor."),
  "why_the_chain_matters": ("Because the differences are not only cosmetic. Publishing an October release would "
                            "describe road connections the City removed before the final."),
  "filename_convention_is_unreliable": ("The leading \"1\" prefix marks the newer package in the DNASDP directory and "
                                        "a fatter re-encoding of an older release here. It cannot be used as a "
                                        "recency signal; the files have to be compared."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds and against the published site before recommending.",
  "result": "Nothing in this directory is held. The archive's only Sawmill planning record is a different instrument.",
  "what_is_held": (MRA_PLAN + ", the Sawmill/Wells Park Community Metropolitan Redevelopment Area Plan of 2005, "
                   "validated, R2-archived at 23,453,140 bytes and published at "
                   "content/development-land-use/redevelopment-plans.md line 183. A metropolitan redevelopment plan "
                   "under the Metropolitan Redevelopment Code, not the Sector Development Plan this exhibit amends."),
  "what_is_missing": "The Sawmill/Wells Park Sector Development Plan itself, the adopted amendment, and whatever adopted it. None is in the inventory.",
  "cross_inventory_byte_collisions": 0,
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text": 3,
  "note": ("Three relationships in a four-document directory and hashing found none of them — including the pair "
           "whose extracted text is exactly equal, because they are different encodings of one release. That pair is "
           "the clearest demonstration in the run that byte comparison and content comparison answer different "
           "questions."),
 },
 "integration_flags": [
  {"severity": "unadopted-regulation",
   "affects": [FINAL],
   "finding": "The canonical release states which subsections of an adopted sector plan it overrides, and its own adoption line is blank. Forty-two pages of street classification and design regulation for Sawmill and Wells Park exist nowhere else in the archive.",
   "recommended_action": "Hold at requires human review. If the adopting instrument is found, publish it; the area's redevelopment plan is already on the site without any of this."},
  {"severity": "avoid-superseded-archival",
   "affects": [OCT_A, OCT_B, FEB],
   "finding": "Three earlier releases of the same exhibit, one of them a 14.8 MB re-encoding of a 10.4 MB file with identical text.",
   "recommended_action": f"Record all three as superseded by {FINAL}. Together {avoided:,} bytes that need never be uploaded."},
  {"severity": "discovery-lead",
   "affects": [],
   "finding": "The Sawmill/Wells Park Sector Development Plan is not held in any form, and neither is the instrument that adopted this amendment.",
   "recommended_action": "Queue the sector plan. Without it the amendment's supersession clause — Section 2 subsections 2.b, 2.c, 2.d and Section 3 subsection 3.d — cannot be read against anything."},
  {"severity": "related-pending-record",
   "affects": ["src-385036989b8d1925"],
   "finding": "An EPC hearing notice for Sawmill/Wells Park sits pending in the District 2 directory, outside this lane.",
   "recommended_action": "Read it when that directory is revisited; a hearing notice is the kind of record that would date this amendment's adoption."},
  {"severity": "method",
   "affects": [OCT_A, OCT_B],
   "finding": "Two files with exactly equal extracted text and no byte overlap. The City's leading-\"1\" filename prefix marked the newer package in DNASDP and the older release here.",
   "recommended_action": "Do not treat filename prefixes as recency signals, and do not expect hashing to find re-encodings. Compare normalized text."},
 ],
 "counts": {
  "reviewed": len(rows),
  "requires_human_review": counts["requires human review"],
  "superseded": counts["superseded"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 5, "http_200": 5, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "4 genuine PDFs and one HTML collection page by leading bytes. All four PDFs have full text layers; none needed rendering."},
 "requires_human_review": rhr,
 "superseded": superseded,
 "excluded": excluded,
 "archival_note": ("Nothing in this cluster is recommended for addition. The single record held at requires human "
                   f"review is {rhr_bytes:,} bytes and would be worth publishing if its adoption is established; it "
                   "is born-digital with a full text layer. The three superseded releases total "
                   f"{avoided:,} bytes and should never be uploaded."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. All three superseded rows carry the same "
                      "canonical_id, which is itself at requires human review in this batch — the same shape as the "
                      "redline row in councilor-district-1-cluster-research-2026-09-12.json. No row is approved for "
                      "addition. The requires-human-review row is not held under the enactment blockers in the usual "
                      "sense: it is an exhibit with a blank adoption line rather than a bill with a blank enactment "
                      "block, and the reasoning is set out in its why_not_decided_here. Sizes and checksums are first "
                      "measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
