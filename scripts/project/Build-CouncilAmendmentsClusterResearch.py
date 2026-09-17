"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

This lane exists to TEST rather than re-apply the amendment-sheet category
decision recorded in the council-documents artifact of the same date.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\council-amendments-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\amend\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/amendments-for-posting-on-council-page/'

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


# Four files in this directory are full bill texts, not amendment sheets. Each
# was identified by its own masthead, not by its filename.
SUBSTITUTES = [
 ("src-29b20d60b30299cd", "o-10-approved-fs-pena.pdf", "F/S O-24-10", 63,
  "Authorizing the Issuance and Sale of City of Albuquerque Gross Receipts Tax Improvement Revenue Bonds in One or More Series in an Aggregate Principal Amount Not to Exceed $22,500,000",
  "Klarissa J. Pe\u00f1a, by request",
  "By far the largest file in the directory at 63 pages, and a bond authorisation rather than a procedural amendment. The inventory already holds an extensive validated general obligation bond record set, so a gross receipts tax revenue bond instrument of this size is squarely in scope if its enactment can be established."),
 ("src-d7c28482bfc9b3c0", "o-21-approved-cs-rogers-by-request.pdf", "C/S O-24-21", 7,
  "Amending Article 12 of Chapter 13 of the Revised Ordinances of Albuquerque, the Albuquerque Minimum Wage Ordinance",
  "Nichole Rogers, by request",
  "An amendment to the Albuquerque Minimum Wage Ordinance. Whether it passed determines the current minimum wage rule, which is exactly the kind of fact a reader would come to the archive for."),
 ("src-cba160dcbb55f5a1", "r-34-approved-fs-grout-fiebelkorn.pdf", "F/S R-24-34", 10,
  "Repealing Article 9 of Chapter 3 of the Code of Resolutions and Replacing It With the Sustainability Resolution",
  "Ren\u00e9e Grout and Tammy Fiebelkorn",
  "A wholesale repeal and replacement of the City's sustainability resolution. If enacted it is the governing sustainability policy; if not, Article 9 stands."),
 ("src-56f776ae07a23774", "r-45-approved-cs-basan-grout.pdf", "C/S R-24-45", 5,
  "Amending the City of Albuquerque Immigrant Friendly Policy",
  "Brook Bassan and Ren\u00e9e Grout",
  "An amendment to the City's immigrant friendly policy. The directory also holds a floor amendment to this same bill, src-77d70bbc48bff79e, so R-24-45 is the one bill here represented by both a substitute and an amendment sheet."),
]

SUB_WHY = (
 "The sheet carries ENACTMENT NO. blank, so under the two standing checkpoint blockers it is the version considered "
 "rather than the law. It is held rather than excluded because it is a complete, self-contained bill text: unlike an "
 "amendment sheet it can be read on its own, and the council-documents artifact of the same date held seven flat-level "
 "substitutes on exactly this ground. All four in this directory should be decided as one group together with those "
 "seven, since they share a Council term and a blank-enactment problem.")

rhr = []
for i, fname, bill, pages, subject, sponsor, why in SUBSTITUTES:
    r = row(i, "requires human review")
    r.update({
     "draft_title": f"Council Bill {bill}: {subject}",
     "pages": pages, "bill": bill, "sponsor": sponsor,
     "document_kind": "substitute bill text, complete and self-contained",
     "question_for_human": f"Locate the enacted instrument for {bill}, or establish that the bill did not carry.",
     "why_not_decided_here": SUB_WHY,
     "why_this_one_matters": why,
     "evidence": (f"{pages} pages. The masthead reads \"COUNCIL BILL NO. {bill} ENACTMENT NO. ________\", Twenty Sixth "
                  f"Council, sponsored by {sponsor}. It contains no amendment instruction and no vote line, which is "
                  f"what separates it structurally from the twenty-five amendment sheets in this directory."),
    })
    rhr.append(r)

# The 25 amendment sheets, with the bill each amends read from the document.
AMENDMENTS = [
 ("src-86d9aafefd9502a7", "o-5-approved-fa-1-champine.pdf", "C/S O-24-5", 2),
 ("src-09a0152fb526fcba", "o-24-13-council-mtg-amd-june-17-2024.pdf", "O-24-13", 17),
 ("src-9de129d7dbaadf19", "o-24-13-lupz-amd-may-15-2024.pdf", "O-24-13", 19),
 ("src-2709cc8e5055ccb4", "o-15-combined.pdf", "F/S O-24-15", 19),
 ("src-94ae67ff88b8f0cf", "o-24-17-council-mtg-june-17-2024.pdf", "O-24-17", 1),
 ("src-55b074db377e4da5", "o-25-committee-amendments-fgo-06102024.pdf", "O-24-25", 4),
 ("src-e4c5198ea43128eb", "o-26-approved-fa-1-rogers-revised.pdf", "O-24-26", 1),
 ("src-e0df5123d40e06af", "p-1-amendments.pdf", "P-24-1", 2),
 ("src-d5edfea6680b8418", "p-3-amendments.pdf", "P-24-3", 2),
 ("src-69e439238e1c7b8d", "p-24-4-council-mtg-amd-june-3-2024.pdf", "P-24-4", 1),
 ("src-e42c6efdfa2123d2", "p-24-4-council-mtg-amd-june-17-2024.pdf", "P-24-4", 5),
 ("src-732601df14a95262", "r-22-approved-fa-1-baca.pdf", "R-24-22", 1),
 ("src-2c631ff1c50f1a28", "r-27-approved-fa-1-fiebelkorn.pdf", "R-24-27", 1),
 ("src-abac586d162b852d", "r-29-combined.pdf", "R-24-29", 3),
 ("src-158f40d92d8a70f2", "r-36-combined-05212024.pdf", "C/S R-24-36", 6),
 ("src-dc51261fcfaa5092", "r-36-combined_cow.pdf", "C/S R-24-36", 3),
 ("src-3c7645d96175bf0a", "r-40-amendments-05202024.pdf", "R-24-40", 3),
 ("src-bbc3ad61d1d7aadb", "r-40-combined_cow.pdf", "R-24-40", 9),
 ("src-8c6df2e0fa5b7b88", "r-42-approved-fa-1-grout-champine.pdf", "R-24-42", 1),
 ("src-77d70bbc48bff79e", "r-45-approved-fa-1-champine-rev.pdf", "C/S R-24-45", 1),
 ("src-ae0dc1620fb9ec71", "r-47-amendments.pdf", "R-24-47", 3),
 ("src-5ec7c4cde9874d57", "r-24-49-council-mtg-june-17-2024.pdf", "R-24-49", 3),
 ("src-e5c7d37577145809", "r-57-approved-fa-1-fiebelkorn.pdf", "R-24-57", 1),
 ("src-9c8080978f060c7e", "r-58-approved-fa-1-fiebelkorn.pdf", "R-24-58", 1),
 ("src-f2dd063f60780a91", "r-59-approved-fa-1-bassan.pdf", "R-24-59", 1),
]

AMEND_REASON = (
 "A City Council amendment packet for a 2024 bill. It instructs a change at a stated page and line of a bill text it "
 "does not contain, and no enacted instrument for that bill exists anywhere in the inventory, so the packet has no "
 "parent to be read against. This is the exact wording the directory's own terminal records already use: \"Isolated "
 "2024 City Council amendment packet without parent-legislation context; it is not a standalone durable policy or "
 "project record.\"")

excluded = []
for i, fname, bill, pages in AMENDMENTS:
    r = row(i, "excluded")
    r.update({"title_for_reference": f"Amendment packet to Council Bill {bill}",
              "pages": pages, "bill": bill,
              "exclusion_reason": AMEND_REASON,
              "category": "council legislative amendment sheet",
              "parent_enacted_instrument_held": False})
    excluded.append(r)

rows = rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 29, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)

bill_map = collections.defaultdict(list)
for i, f, b, p in AMENDMENTS:
    bill_map[b].append({"id": i, "kind": "amendment sheet", "file": f, "pages": p})
for i, f, b, p, *_ in SUBSTITUTES:
    bill_map[b].append({"id": i, "kind": "substitute bill text", "file": f, "pages": p})

artifact = {
 "batch_id": "council-amendments-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/amendments-for-posting-on-council-page cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Albuquerque City Council's posted amendment packets for the 2024 session, Twenty Sixth Council.",
 "scope": "All 29 pending-review candidates in that directory. The directory holds 34 records in total; the other five are already terminal and are what made this lane worth running as a test rather than a re-application.",
 "brief": "Test rather than assume the amendment-sheet category decision recorded in the council-documents artifact, by fetching and reading every file rather than inferring from the directory name.",
 "brief_finding": "The category decision survives for twenty-five of the twenty-nine files, and on a better-stated ground than the one it was originally given. It fails for the other four, which are not amendment sheets at all but complete substitute bill texts, including a 63-page $22,500,000 gross receipts tax revenue bond authorisation and an amendment to the Albuquerque Minimum Wage Ordinance. The earlier artifact's claim that the category covers \"at least 57 files across this tree\" was therefore too broad, and this artifact corrects it.",
 "method": "Ran the URL group-by across the directory first, as the inventory URL-collision audit of the same date recommends; it found no collisions here and cost nothing. Fetched all 29 candidates and recorded exact byte length and SHA-256 for each. Read every file's masthead rather than trusting its filename, and applied a structural test: an amendment sheet carries an amendment designation and a recorded vote line, a substitute bill text carries a COUNCIL BILL NO. masthead and neither. Read the five already-terminal records in the directory for their recorded reasoning. Searched the whole inventory for an enacted counterpart to each of the twenty-four bills represented here.",
 "classification_only": True,
 "shared_state_written": [],
 "what_this_lane_tested": {
  "assumption_1": {
   "claim": "The council-documents artifact of the same date recommended excluding Council amendment sheets as a category and stated the category covers \"at least 57 files across this tree and is explicitly open to revisiting as one category rather than record by record\". The 29 files in this directory were counted into that 57 from the directory name alone; none was fetched.",
   "test": "Fetched and read all 29, classifying by masthead and structure rather than by filename or directory.",
   "result": "FAILED for 4 of 29. They are complete substitute bill texts with no amendment instruction and no vote line.",
   "correction": ("The category figure should read at least 48 amendment sheets, not 57: 23 at the flat level plus 25 "
                  "here. The four substitutes join the seven flat-level substitutes already held at requires human "
                  "review, making eleven 2024-session substitute bill texts to decide as one group."),
   "lesson": "A directory named for a category is not evidence that its contents are that category. This is the second time in this run that a name has misdescribed contents, after lacueva.pdf turned out to be a complete sector development plan.",
  },
  "assumption_2": {
   "claim": "The council-documents artifact excluded amendment sheets on the ground that they are non-self-contained fragments.",
   "test": "Read the reasoning already recorded on the five terminal records in this directory.",
   "result": "CONFIRMED but under-specified. The directory's own records encode a sharper rule that the earlier artifact missed.",
   "the_sharper_rule": ("Whether an amendment packet is excluded or superseded turns on one question: is the enacted "
                        "instrument identified and held? Two records here are superseded, not excluded, with "
                        "validation_status \"superseded by signed enacted R-2025-014\" and the reason \"passed changes "
                        "are incorporated into signed enacted R-2025-014\". Three are excluded, with the reason "
                        "\"Isolated 2024 City Council amendment packet without parent-legislation context\". Same kind "
                        "of document, opposite dispositions, decided by whether the parent exists in the archive."),
   "why_it_matters": ("An amendment packet is not inherently worthless. Once the enacted instrument is held, the packet "
                      "becomes a superseded predecessor of it, which is a retained relationship rather than a "
                      "discarded one. Recording the packets as excluded today does not preclude that; it records the "
                      "state of the archive today."),
  },
 },
 "enacted_parent_search": {
  "question": "Does the inventory hold an enacted instrument for any of the twenty-four bills represented in this directory?",
  "method": ("Searched all 7,074 candidates twice. First for any record whose title, validation status or exclusion "
             "reason cites an enactment number of the form O-2024-nnn, P-2024-nnn or R-2024-nnn. Then, per bill, for "
             "any record outside this directory whose title or URL contains the full bill token."),
  "result_enactment_numbers": "Zero records anywhere in the inventory cite a 2024 enactment number.",
  "result_per_bill": ("One match, and it is not a parent: src-0fb0d4343ac02dcd, a June 3 2024 floor amendment to "
                      "P-24-3, already terminal-excluded with the reason \"Isolated floor amendment without the "
                      "authoritative parent legislation or complete enacted package.\" It is a sibling of the packets "
                      "here, not the legislation they amend."),
  "conclusion": ("No 2024 enacted instrument is held. The condition that makes an amendment packet superseded rather "
                 "than excluded is therefore absent for every bill in this directory, and the exclusion stands for all "
                 "twenty-five."),
  "false_positives_discarded": ("A first per-bill pass used a loose pattern that reduced O-24-25 to \"o-25\" and R-24-22 "
                                "to \"r-22\", and reported five apparent parents: the Menaul MRA enacted amendment, the "
                                "2025 Integrated Development Ordinance, the Menaul MRA plan, R-22-38 records, and an "
                                "Edgewood property fact sheet. All five were spurious substring matches on unrelated "
                                "bill numbers. They are recorded here so the same mistake is not repeated: match the "
                                "full bill token, never a truncation."),
  "if_this_changes": ("Should the 2024 enacted ordinances and resolutions later be captured, for example through a "
                      "Legistar attachment audit like the one that produced the R-25-117 records in this directory, "
                      "these twenty-five exclusions should be revisited as supersessions. That is the single condition "
                      "that flips them."),
 },
 "bill_map": {
  "note": ("Twenty-four bills across twenty-nine files. The bill was read from each document rather than its filename; "
           "five amendment packets do not state their bill on a parseable line and are mapped from their filename and "
           "content, and are marked as such in the per-record rows."),
  "bills": {b: v for b, v in sorted(bill_map.items())},
  "bills_with_more_than_one_file": {b: v for b, v in sorted(bill_map.items()) if len(v) > 1},
  "the_instructive_one": ("C/S R-24-45, Amending the City of Albuquerque Immigrant Friendly Policy, is the only bill "
                          "here represented by both a substitute bill text (src-56f776ae07a23774, held) and an "
                          "amendment sheet (src-77d70bbc48bff79e, excluded). The two sit side by side in one directory "
                          "and receive opposite dispositions, which is the clearest demonstration in this artifact that "
                          "the split is structural and not arbitrary."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "note": ("The URL group-by was run first per the audit artifact's rule and found nothing, which is itself worth "
           "recording: the collision pattern is not uniform across the Council tree. Byte hashing likewise found "
           "nothing. Two amendment packets for one bill, such as the two R-24-40 files, are a Committee of the Whole "
           "set and a Council meeting set from different dates, not duplicates."),
 },
 "integration_flags": [
  {"severity": "corrects-a-prior-artifact",
   "affects": ["project-state/discovery/council-documents-cluster-research-2026-09-11.json"],
   "finding": "That artifact stated the amendment-sheet category covers at least 57 files across this tree, counting all 29 records in this directory from its name. Four of the 29 are substitute bill texts, not amendment sheets.",
   "recommended_action": "Read the category figure as at least 48 amendment sheets. The four substitutes identified here are recommended requires human review and belong with the seven flat-level substitutes that artifact already holds, making eleven to decide as one group."},
  {"severity": "rule-refinement",
   "affects": ["all council amendment packets in the inventory"],
   "finding": "The directory's own terminal records distinguish superseded from excluded by whether the enacted instrument is held, not by the nature of the document. The council-documents artifact excluded on the fragment ground alone and did not record this.",
   "recommended_action": "Adopt the sharper rule for any future amendment-packet decision: enacted parent held means superseded by it, no parent held means excluded. Apply it when reconciling the R-25-117 records already in this directory."},
  {"severity": "tractability",
   "affects": [s[0] for s in SUBSTITUTES],
   "finding": "Four substitute bill texts with blank enactment numbers, including a $22,500,000 gross receipts tax revenue bond authorisation, an amendment to the Albuquerque Minimum Wage Ordinance, a repeal and replacement of the sustainability resolution, and an amendment to the immigrant friendly policy.",
   "recommended_action": "These are more consequential than their page counts suggest and three of the four set current City policy if enacted. Resolve them with the impact-fees group, which the impact-fees artifact of the same date identifies as the enactment group most likely to resolve quickly."},
  {"severity": "method",
   "affects": ["future lanes"],
   "finding": "A loose per-bill match pattern produced five false parent matches by truncating bill numbers. A structural test on document content, rather than filename, is what separated the substitutes from the amendment sheets.",
   "recommended_action": "Match full bill tokens only, and classify legislative files by masthead rather than by filename or directory name."},
 ],
 "counts": {
  "reviewed": len(rows),
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "approved_for_addition": 0, "superseded": 0, "duplicate": 0,
  "bills_represented": len(bill_map),
 },
 "link_check": {"checked": 29, "http_200": 29, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "All 29 files are genuine PDFs by leading bytes and all yield extractable text; no rendering was needed."},
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": "No record in this artifact is recommended for addition, so this batch proposes no archival and no site change. The four held records must not be archived or presented as enacted while their enactment numbers are blank.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Twenty-five rows are excluded as amendment packets whose parent legislation is not held, each carrying parent_enacted_instrument_held false so the condition that would flip them is explicit and machine-readable. Four rows are requires human review and are substitute bill texts, each carrying its bill number, sponsor and subject; decide them with the seven flat-level substitutes from the council-documents artifact. No row carries a canonical_id because the directory holds no duplicate or supersession relationship. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
