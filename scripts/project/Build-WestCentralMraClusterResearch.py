"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\west-central-mra-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\wc\fetch.log')

ADOPTED_PLAN = 'src-56485de565b52365'   # validated + R2 + published, redevelopment-plans.md line 225
ARCHIVED_RMP = 'src-9696b9222ba27231'   # validated + R2 + published Tijeras Arroyo RMP
EG_MRA_PLAN = 'src-42700a168ad3eb38'    # validated + R2 + published East Gateway MRA plan

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

BLOCKER = ("Enactment block blank on the file itself, under the two standing checkpoint blockers: isolated "
           "legislative material must have its authoritative enacted package resolved before archival or visible use.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


superseded = [{
 **row("src-84d8d553f41dc893", "superseded"),
 "title_for_reference": "West Central Metropolitan Redevelopment Area Plan — Final Draft, January 2004 (Bohannan-Huston, Inc. and Research & Polling, Inc.)",
 "pages": 93,
 "canonical_id": ADOPTED_PLAN,
 "canonical_url": IDX[ADOPTED_PLAN].get('r2_url'),
 "canonical_state": "validated, R2-archived, and published at content/development-land-use/redevelopment-plans.md line 225",
 "basis": "The January 2004 final draft of a plan whose June 2004 final the archive already holds.",
 "measurement": ("Fetched the R2 object and compared. The archived copy runs 103 pages to this one's 93, normalized-text "
                 "ratio 0.9949, token coverage 0.9977 and 0.9996. The release states are printed on every page and in "
                 "the source path: this file foots \"Final Draft January 2004\" over "
                 "P:\\03060\\Report\\W CENTRAL MRArpt6-03.doc, and the archived one foots \"June 2004\" over "
                 "P:\\03060\\Report\\Final Report\\W CENTRAL MRArpt-final6-04.doc. The string \"Final Draft\" appears "
                 "87 times here and never in the archived copy."),
 "hash_found_it": False,
 "the_revisions_are_substantive": ("Not just a stamp change. The draft reads \"neighborhood-oriented and Mexican "
                                   "specialty businesses along Old Coors Boulevard\" and \"Mexican and other ethnic "
                                   "specialty retail items\"; the adopted plan reads \"neighborhood-oriented and "
                                   "ethnic specialty businesses\" and \"ethnic specialty retail items\". Anyone "
                                   "quoting the draft would attribute wording to the City that it revised before "
                                   "adoption."),
 "why_it_was_not_obvious": ("The two records share a title and an author. Nothing but the footer and the source "
                            "filename distinguishes them, and the inventory held no checksum for this one. The byte "
                            "sizes point the wrong way: the superseded draft is 21,139,298 bytes against the adopted "
                            "plan's 15,035,247, so the larger file is the older one."),
}]


def R(i, priority, draft_title, pages, evidence, question, why, extra=None):
    r = row(i, "requires human review")
    r.update({"priority": priority, "draft_title": draft_title, "pages": pages,
              "evidence": evidence, "question_for_human": question, "why_not_decided_here": why})
    if extra:
        r.update(extra)
    return r


rhr = [
 R("src-be4df966deebed35", 1,
   "Council Bill F/S R-04-56: Resolution Approving the West Central Metropolitan Redevelopment Plan and Specifically Including the Entire West Central Metropolitan Redevelopment Area for Purposes of Tax Increment Financing",
   4,
   ("Born-digital PDF with a full text layer. CITY OF ALBUQUERQUE, SIXTEENTH COUNCIL, COUNCIL BILL NO. F/S R0456, "
    "ENACTMENT NO. blank, sponsored by Miguel Gomez and Eric Griego. Section 1 adopts the West Central Metropolitan "
    "Redevelopment Plan as attached; Section 2 includes the entire West Central MRA for tax increment financing; "
    "Section 3 appropriates $200,000 from the uncommitted Metropolitan Redevelopment Fund balance and $200,000 from "
    "the Community and Economic Development Reserve Fund to Albuquerque Development Services for land assembly and "
    "public improvements."),
   "Retrieve Enactment 66-2004. The number is known; only the enacted text is missing.",
   (BLOCKER + " But this is the best-evidenced enactment question raised anywhere in this run, because the number is "
    "stated outright rather than inferred. See enactment_numbers_recovered."),
   extra={"stated_enactment_number": "66-2004",
          "stated_by": "src-1564eaa66bce3d8c, in this same directory, whose title line reads \"AMENDING F/S R-04-56, ENACTMENT 66-2004\".",
          "outcome_also_held": ("The plan this resolution adopts is validated, R2-archived and published: "
                                + ADOPTED_PLAN + " at content/development-land-use/redevelopment-plans.md line 225. "
                                "So both kinds of evidence line up — the outcome is held and the enactment number is "
                                "on the record."),
          "it_names_another_missing_instrument": ("Its recitals state that the Council \"has duly passed and adopted "
                                                  "Council Resolution No. F/S R-2-16, Enactment 82-2001, finding, "
                                                  "among other things, that one or more slum areas or blighted "
                                                  "areas\" exist. That is the designating resolution for the West "
                                                  "Central MRA, with its enactment number supplied, and the archive "
                                                  "holds no copy of it.")}),

 R("src-1564eaa66bce3d8c", 2,
   "Council Bill FS-R-04-188 (4): Resolution Amending F/S R-04-56, Enactment 66-2004; Providing an Appropriation to the West Central Metropolitan Redevelopment Project; Establishing Procedures for Management of the Funding by the Alamosa Neighborhood Association; and Accepting a Program of Association Between the Alamosa Neighborhood Association and the West Central Community Development Group",
   13,
   ("Born-digital PDF with a full text layer, the longest legislative file in the directory. CITY OF ALBUQUERQUE, "
    "SIXTEENTH COUNCIL, COUNCIL BILL NO. FS-R-04-188 (4), ENACTMENT NO. blank, sponsor line blank. Its title recites "
    "the enactment number of the resolution it amends."),
   "Decide with F/S R-04-56. This bill is also what makes that one answerable.",
   (BLOCKER + " It is unusual and valuable: it hands over the enactment number of its parent. It also puts City "
    "redevelopment money under a named neighbourhood association's management, which is a governance arrangement the "
    "archive records nowhere."),
   extra={"supplies": "Enactment 66-2004 for F/S R-04-56."}),

 R("src-5924eddac4b3679a", 3,
   "Council Bill R-05-286: Resolution Amending the Adopted Capital Implementation Program by Approving New Projects, Supplementing Current Appropriations and Changing the Scope of Existing Projects, and Amending the General Fund Budget to Clean Up an Approved Appropriation for the West Central MRA Project",
   20,
   ("Born-digital PDF with a full text layer. CITY of ALBUQUERQUE, SIXTEENTH COUNCIL, COUNCIL BILL NO. R05286, "
    "ENACTMENT NO. blank, sponsored by Debbie O'Malley, by request. It is a general Capital Implementation Program "
    "amendment that reaches this directory only because one of its clean-up items concerns the West Central MRA "
    "appropriation made by F/S R-04-188 (4)."),
   "Decide with the two above, and note it belongs to the same CIP series as district 1's C/S R-08-182.",
   (BLOCKER + " No enactment number is stated for it anywhere in the fetched corpus."),
   extra={"related_outside_this_cluster": ("It is a Capital Implementation Program amendment, the same instrument "
                                           "class as C/S R-08-182 in "
                                           "councilor-district-1-cluster-research-2026-09-12.json. Resolving the "
                                           "Council's CIP series once would answer both.")}),
]

excluded = [
 {**row("src-1db703ad807c2e64", "excluded"),
  "title_for_reference": "Floor Amendment No. 1 to R-05-286, June 30, 2005 (Councillors Gomez and Griego)",
  "pages": 2,
  "date": "2005-06-30",
  "exclusion_reason": ("A floor amendment sheet: a numbered list of line edits against a bill text it does not "
                       "contain, of the form \"On page 1, line 5, after the word 'PROJECTS', INSERT THE "
                       "FOLLOWING\". Excluded as a non-self-contained legislative fragment, the category decision "
                       "recorded in council-documents-cluster-research-2026-09-11.json and applied again in "
                       "councilor-district-5-cluster-research-2026-09-11.json."),
  "category": "amendment sheet",
  "parent_is_held": "Its parent R-05-286 is in this directory at requires human review, so unusually for this category the bill it edits is available — but the amendment still adds nothing a reader could use on its own.",
  "content_recorded": ("Its substantive edit inserts into R-05-286 a new Section 4 amending \"Adopted Bill No. F/S "
                       "R04188 (4)\", which is the third confirmation in this directory that F/S R-04-188 (4) was "
                       "adopted.")},

 {**row("src-8eeb755b80a898d9", "excluded"),
  "title_for_reference": "West Central Metropolitan Redevelopment Area collection landing page",
  "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
  "category": "collection landing page"},
]

rows = superseded + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 6, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
avoided = sum(r["size_bytes"] for r in superseded)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "west-central-mra-cluster-research-2026-09-12",
 "lane": "Claude research lane: the West Central Metropolitan Redevelopment Area cluster in the Albuquerque City Council library",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The West Central Metropolitan Redevelopment Area file: the area plan and the four Sixteenth Council instruments that adopted, funded and amended it.",
 "scope": "All 6 pending-review candidates, which is every record in the directory. Nothing here is terminal.",
 "brief": "Run the standard opening sequence and test every candidate against the West Central MRA material already held, before anything is recommended.",
 "brief_finding": ("The test caught the directory's largest file. The 93-page West Central Metropolitan Redevelopment "
                   "Area Plan here is the January 2004 *final draft* of a plan whose June 2004 final is already "
                   "validated, archived and published — and the byte sizes point the wrong way, with the superseded "
                   "draft 6 MB larger than the adopted plan. Nothing in this directory is recommended for addition."),
 "second_finding": ("The directory answers a question the rest of the run has been unable to. Five enactment packages "
                   "now sit at requires human review across these artifacts, every one of them held there because a "
                   "bill's ENACTMENT NO. line is blank. Here a later bill simply states its parent's number in its "
                   "own title — \"AMENDING F/S R-04-56, ENACTMENT 66-2004\" — and F/S R-04-56 in turn states another, "
                   "\"Council Resolution No. F/S R-2-16, Enactment 82-2001\". The recitals of later legislation carry "
                   "enactment numbers that the bills themselves do not. See enactment_numbers_recovered."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 6 candidates and measured byte length and SHA-256 "
            "from the fetched bytes. Compared all checksums within the cluster and against the 1,612 checksummed "
            "inventory records: no collisions either way. Fetched the archived West Central MRA plan read-only and "
            "compared it line by line against the candidate. Read every legislative file's title and operative "
            "sections. Then swept every text fetched across this whole run for stated enactment numbers and for "
            "mentions of the five open enactment packages, which is what produced the finding below."),
 "classification_only": True,
 "shared_state_written": [],
 "enactment_numbers_recovered": {
  "what_was_found": ("Two enactment numbers, both stated as fact inside primary legislative text rather than inferred "
                     "from an outcome."),
  "numbers": [
   {"instrument": "Council Bill F/S R-04-56, approving the West Central Metropolitan Redevelopment Plan",
    "enactment": "66-2004",
    "stated_by": "src-1564eaa66bce3d8c, whose own title line reads \"AMENDING F/S R-04-56, ENACTMENT 66-2004\"",
    "corroborated_by": "src-1db703ad807c2e64, the floor amendment, which refers to \"Adopted Bill No. F/S R04188 (4)\", and by the plan itself being adopted and published"},
   {"instrument": "Council Resolution No. F/S R-2-16, designating the West Central MRA on slum and blight findings",
    "enactment": "82-2001",
    "stated_by": "src-be4df966deebed35, in its recitals",
    "note": "The archive holds no copy of this instrument in any form. It is a discovery lead with its enactment number already attached."},
  ],
  "the_generalisable_method": ("To find an instrument's enactment number, read the recitals and title lines of later "
                              "legislation that amends or cites it. Do not read the plan it produced."),
  "why_the_plan_is_the_wrong_place_to_look": ("Because the City appends the *pre-enactment bill text* to its adopted "
                                              "plans. Two cases are now verified, both inside records that are "
                                              "already validated, R2-archived and live on the site: " + ARCHIVED_RMP
                                              + ", the Tijeras Arroyo Biological Zone Open Space Resource Management "
                                              "Plan, carries \"Appendix A — City Council Resolution\" reproducing "
                                              "C/S R-07-278 with \"ENACTMENT NO. ________________________\" blank; "
                                              "and " + EG_MRA_PLAN + ", the East Gateway Metropolitan Redevelopment "
                                              "Area Plan, reproduces F/S R-07-275 with its block blank in the same "
                                              "way. Both were checked by fetching the R2 objects and reading the "
                                              "appendix."),
  "consequence_for_the_five_open_packages": ("The plan appendices will not resolve them, and two published records "
                                             "carry unenacted bill text of their own. The place to look is the "
                                             "Council's later legislation — amendments, clean-up bills, and "
                                             "resolutions that cite the earlier instrument — or the City Clerk's "
                                             "enacted series directly."),
  "swept_corpus": ("Every text fetched in this run was searched for stated enactment numbers and for the five open "
                   "packages. More than twenty distinct enactment numbers appear across the corpus, but none of them "
                   "attaches to R-07-278, F/S R-07-275, R-14-82, R-14-113, M-14-5, C/S R-08-182 or F/S O-05-98. "
                   "R-14-82 does confirm the fact of adoption for R-07-278 — \"WHEREAS, the Albuquerque City Council "
                   "approved Resolution R-07-278, mandating the City of Albuquerque to develop a Tijeras Arroyo "
                   "Bio-Zone Preserve\" — without giving the number."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds and against the published site before recommending.",
  "candidate": "src-84d8d553f41dc893, West Central Metropolitan Redevelopment Area Plan, 93 pages, 21,139,298 bytes.",
  "result": "Superseded by " + ADOPTED_PLAN + ", the June 2004 final, 103 pages, 15,035,247 bytes, validated and published.",
  "distinguishing_evidence": "Page footers and the embedded source path: \"Final Draft January 2004\" over W CENTRAL MRArpt6-03.doc against \"June 2004\" over Final Report\\W CENTRAL MRArpt-final6-04.doc.",
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue.",
  "size_is_not_a_recency_signal": "Noted because it is counter-intuitive and has now appeared twice: here the superseded draft is larger than the adopted plan, and in councilor-district-7-cluster-research-2026-09-12.json the superseded draft of the Uptown study was larger than the published final.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_comparison_against_r2": 1,
  "note": ("One relationship and hashing did not find it. The four legislative files are four different instruments "
           "in one chain — designate, adopt, amend, clean up — not versions of each other, and the chain is the "
           "reason the enactment numbers surfaced."),
 },
 "integration_flags": [
  {"severity": "method",
   "affects": [],
   "finding": "Enactment numbers are recoverable from the recitals and title lines of later legislation, not from the plans those instruments adopted. Two numbers were recovered here that way; two published, validated archive records were confirmed to carry blank enactment blocks in their own appendices.",
   "recommended_action": "Apply this to the five open enactment packages before any further plan-appendix searching. Search Council legislation that amends or cites each instrument."},
  {"severity": "affects-live-records",
   "affects": [ARCHIVED_RMP, EG_MRA_PLAN],
   "finding": "Two validated, R2-archived, published plans reproduce their adopting resolutions as pre-enactment bill text with the enactment block blank.",
   "recommended_action": "Do not treat a plan appendix as evidence of enactment. When those resolutions are resolved, the appendices remain as published; a note on each page would be more accurate than silence."},
  {"severity": "avoid-superseded-archival",
   "affects": ["src-84d8d553f41dc893"],
   "finding": "The directory's 21 MB plan is the January 2004 final draft of a plan already published in its June 2004 final form, with substantive wording changes between them.",
   "recommended_action": f"Record as superseded. {avoided:,} bytes not uploaded, and a draft kept out of circulation whose text differs from the adopted plan in ways a quoting reader would get wrong."},
  {"severity": "best-evidenced-enactment",
   "affects": ["src-be4df966deebed35"],
   "finding": "F/S R-04-56 has both kinds of evidence: the plan it adopts is published, and its enactment number, 66-2004, is stated outright in a later bill.",
   "recommended_action": "Promote it to the front of the enactment queue, ahead of the five packages whose numbers are still unknown."},
  {"severity": "discovery-lead",
   "affects": [],
   "finding": "Council Resolution F/S R-2-16, Enactment 82-2001, the instrument that designated the West Central MRA on slum and blight findings, is held nowhere in the inventory — and its enactment number is already known.",
   "recommended_action": "Queue it. It is the rare case where a missing document can be requested by its enacted number."},
  {"severity": "governance-record",
   "affects": ["src-1564eaa66bce3d8c"],
   "finding": "FS-R-04-188 (4) places City redevelopment funding under the management of a named neighbourhood association and accepts a program of association between it and the West Central Community Development Group. The archive records no such arrangement anywhere.",
   "recommended_action": "Worth publishing if the package resolves. It is an unusual delegation of City funds."},
 ],
 "counts": {
  "reviewed": len(rows),
  "superseded": counts["superseded"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 6, "http_200": 6, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "archive_fetches": "The archived West Central MRA plan at files.abqinfo.com was fetched read-only for comparison, HTTP 200, 15,035,247 bytes, 103 pages. Two further R2 objects fetched earlier in this run were re-read for the appendix finding.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "5 genuine PDFs and one HTML collection page by leading bytes. All five PDFs have full text layers; none needed rendering."},
 "superseded": superseded,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": ("Nothing in this cluster is recommended for addition. The three records held at requires human "
                   f"review total {rhr_bytes:,} bytes and would add to the queue only if the enactment package is "
                   "resolved; all three are born-digital with full text layers."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. The one superseded row carries a canonical_id "
                      "pointing at a validated, R2-archived, published record. Three rows are requires human review "
                      "under the standing enactment blockers, each with a priority field; the first carries a stated "
                      "enactment number rather than an inference, which no other row in this run does. The largest "
                      "item in this artifact is not a row: enactment_numbers_recovered changes where the other five "
                      "open packages should be searched. Sizes and checksums are first measurements; the inventory "
                      "held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
