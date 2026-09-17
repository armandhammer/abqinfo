"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\4th-street-montano-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\fm\fetch.log')

VISIONING = 'src-173ce250cdac7c01'   # validated + R2 + published
DRAFT_TWIN = 'src-48a9681a27727130'  # terminal superseded twin of the draft plan
FINAL_PLAN = 'src-6479e8efc5bcc2b6'  # validated + R2: the City Council draft Rank III corridor plan
BACKGROUND = 'src-925265ba30c142c1'  # validated + R2: Background & Resource Materials

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


duplicates = [
 {**row("src-4d604937d6910980", "duplicate"),
  "title_for_reference": "Fourth Street and Montaño Community Visioning Report, November 6, 2004",
  "pages": 13,
  "canonical_id": VISIONING,
  "canonical_url": IDX[VISIONING].get('r2_url'),
  "canonical_state": "validated, R2-archived, and published at content/development-land-use/area-sector-plans.md",
  "basis": "A second inventory record for one file. Same URL, same bytes, same document.",
  "measurement": ("Byte-identical to the canonical: 1,246,032 bytes and SHA-256 "
                  "6a50f38bb6836736e29628722e42943aff09ac0fcebc3352e170372b15d2371c, matching the validated record "
                  "exactly. Both records carry the same direct file URL once the Plone /view suffix is normalised."),
  "hash_found_it": True,
  "audit_class": ("This is the actionable_now class defined in inventory-url-collision-audit-2026-09-11.json: a "
                  "pending record whose URL twin is already terminal. It needs no judgment, only the twin's "
                  "disposition.")},

 {**row("src-f90f45e9692ffc1a", "duplicate"),
  "title_for_reference": "Draft North Fourth Street Rank III Corridor Plan (filed under the coalition's 4th Street and Montaño improvements filename)",
  "pages": 31,
  "canonical_id": DRAFT_TWIN,
  "canonical_url": IDX[DRAFT_TWIN].get('direct_file_url'),
  "canonical_state": "already terminal as superseded",
  "basis": "A second inventory record for one file, whose twin is already resolved.",
  "measurement": ("Byte-identical to the terminal twin: 34,703,589 bytes and SHA-256 "
                  "558ce8f2b72821da0d5ba2b0a4ade70c38a11409c2e033488a76afa280561738. The largest file in the "
                  "directory and the second-largest single candidate seen in this run."),
  "hash_found_it": True,
  "audit_class": "Second actionable_now URL twin in one directory.",
  "what_the_twin_records": ("The twin's own reasoning, already in the inventory: \"PDF title and content show this is "
                            "a draft North Fourth Street Rank III Corridor Plan, despite the referring link label; "
                            "the final 2010 plan is already archived\", and \"The authoritative final 2010 North "
                            "Fourth Street Corridor Plan is already archived and implemented; this larger draft is "
                            "retained in local staging for research but is not duplicated in production R2 or site "
                            "content.\" The final plan it defers to is " + FINAL_PLAN + ", validated and R2-archived "
                            "at 13,960,760 bytes."),
  "note_on_the_filename": ("The City files a 34.7 MB corridor plan draft under "
                           "4th_street_and_montano_area_improvements_draft_plan.pdf inside a coalition directory. "
                           "Neither the filename nor the directory says what the document is. This is the same trap "
                           "as pgs/Part2.pdf in planned-growth-strategy-cluster-research-2026-09-11.json: the "
                           "identity has to come from the file, never from where it sits.")},
]


def X(i, title, pages, reason, category, date=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages, "exclusion_reason": reason, "category": category})
    if date:
        r["date"] = date
    if extra:
        r.update(extra)
    return r


PROCESS = ("Public-involvement working material from the 4th Street Corridor Master Plan process. The plan that came "
           "out of that process is archived and published, and it carries the process in its own narrative: \"This "
           "corridor plan is the result of extensive public involvement including mediated negotiations, design "
           "charrettes, open houses, public hearings\", with the two open houses and the workshop participation "
           "described in the pages that follow. This is the same reasoning dnasdp-cluster-research-2026-09-12.json "
           "applied to the DNA meeting summaries and councilor-district-6-cluster-research-2026-09-12.json applied to "
           "the Zuni meeting notes.")

excluded = [
 X("src-a7e8a65f2a77cbaa", "Survey results, 4th Street and Montaño area improvements", 5,
   PROCESS, "public involvement working material",
   extra={"content": ("Five pages of bar charts reporting responses to the outreach survey. Question 1 asks \"What "
                      "are my major concerns about 4th Street and its relationship with my neighborhood?\" and charts "
                      "responses up to about 45 across categories including pedestrian conditions, commercial "
                      "development, transients, unsafe turns, neighborhood character, labor finder and tattoo "
                      "businesses, and rural character."),
          "tested_not_assumed": ("This is the one file in the directory carrying primary quantitative data, so "
                                 "containment was tested rather than assumed. It is not inside either archived "
                                 "object: token coverage 0.8750 in the Background and Resource Materials and 0.7969 "
                                 "in the corridor plan, which on 128 tokens is the sparse-text over-call the earliest "
                                 "artifacts of this run warn about, and the literal question text appears in neither. "
                                 "It is excluded as process material, not as a duplicate."),
          "recorded_because_it_is_excluded": ("The concern categories above are the only quantified statement of what "
                                              "residents said about this corridor anywhere in the archive. Recorded "
                                              "here so the finding survives the exclusion.")}),

 X("src-f479e43c3d324796", "Values and issues exercise: 4th Street and Montaño Area Improvements Corridor Master Plan, stakeholder workshop summary, August 12-13, 2008", 3,
   PROCESS, "public involvement working material", "2008-08-13",
   extra={"content": ("The consultant's summary of the August 2008 stakeholder workshop, stating that \"The values and "
                      "issues identified by the public and the information derived from focus group and individual "
                      "stakeholder meetings and interviews will help to guide the process for the 4th Street Corridor "
                      "Master Plan\", and describing the 13 August values exercise in which aerial maps of the study "
                      "area were provided at each table with three sticky notes."),
          "containment": "Token coverage 0.7383 in the Background and Resource Materials and 0.7047 in the corridor plan; no literal phrase match in either. Not contained, and not recommended."}),

 X("src-c3dca05b7c5c94a7", "Open house handout, July 29, 2009: \"As We Go Forward\"", 1,
   PROCESS, "meeting handout", "2009-07-29",
   extra={"content": ("A one-page next-steps sheet: the draft plan for 4th Street between Douglas MacArthur and the "
                      "northern City boundary will be developed by the consultant, Sites Southwest, with City Council "
                      "staff, posted online before a further community-wide meeting, with hard copies at the City "
                      "Council offices."),
          "discovery_lead": "It names the consultant, Sites Southwest, and the corridor limits, neither of which the archived plan's title states."}),

 X("src-b8301725a4474ca5", "Meeting flyer: 4th Street and Montaño, \"The Blueprints Are Underway\"", 1,
   ("A one-page meeting announcement thanking residents for turning out at the design meetings and asking them to "
    "attend the next ones. It records an invitation, not a proceeding. Meeting flyers are excluded throughout this "
    "run."),
   "meeting announcement",
   extra={"content": "States that the City is conducting a study to improve Fourth Street near Montaño from Douglas MacArthur north to Solar Road."}),
]

rows = duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 6, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
avoided = sum(r["size_bytes"] for r in duplicates)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "4th-street-montano-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/4th-street-montano-area-improvement-coalition cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The 4th Street and Montaño Area Improvement Coalition file in the Albuquerque City Council library.",
 "scope": "All 6 pending-review candidates. The directory holds 10 records; the other four are already terminal and two of them are exact twins of candidates here.",
 "brief": "Run the standard opening sequence, checking every candidate against the Fourth Street and Montaño material the site already publishes.",
 "brief_finding": ("The directory adds nothing. Two of its six pending records are byte-identical twins of records "
                   "already terminal in the inventory, and the other four are public-involvement working material "
                   "from a corridor-plan process whose plan, background appendices, zoning maps and metropolitan "
                   "redevelopment plan are all already archived. Nothing is recommended for addition and nothing "
                   "needs human review — the second directory in this run to come back empty for both queues, after "
                   "councilor-district-6-cluster-research-2026-09-12.json."),
 "second_finding": ("Both URL twins are the actionable_now class from "
                    "inventory-url-collision-audit-2026-09-11.json, and having two in one six-record directory is the "
                    "densest concentration seen. Neither needed judgment: hashing matched them to their twins "
                    "exactly, and the twins already carry the reasoning."),
 "method": ("Ran the URL group-by first; two collisions, each pairing a pending record with a terminal one. Fetched "
            "all 6 candidates and measured byte length and SHA-256 from the fetched bytes, then compared those "
            "against the terminal twins' recorded checksums. Compared all checksums against the 1,612 checksummed "
            "inventory records. Fetched two archived R2 objects read-only — the City Council draft corridor plan and "
            "the Background and Resource Materials — and tested the four remaining candidates against both by token "
            "coverage and then by literal phrase match. Read each file rather than classifying it from its filename, "
            "which in this directory is necessary: one file named for area improvements is a 31-page corridor plan "
            "draft."),
 "classification_only": True,
 "shared_state_written": [],
 "url_twins_resolved": {
  "count": 2,
  "twin_1": {
   "pending": "src-4d604937d6910980", "terminal": VISIONING, "terminal_status": "validated",
   "url": "https://www.cabq.gov/council/documents/4th-street-montano-area-improvement-coalition/4thstcommunityvisioningreport11.06.04.pdf",
   "confirmed_by": "Byte-identical: 1,246,032 bytes, SHA-256 6a50f38bb6836736e29628722e42943aff09ac0fcebc3352e170372b15d2371c.",
  },
  "twin_2": {
   "pending": "src-f90f45e9692ffc1a", "terminal": DRAFT_TWIN, "terminal_status": "superseded",
   "url": "https://www.cabq.gov/council/documents/4th-street-montano-area-improvement-coalition/4th_street_and_montano_area_improvements_draft_plan.pdf",
   "confirmed_by": "Byte-identical: 34,703,589 bytes, SHA-256 558ce8f2b72821da0d5ba2b0a4ade70c38a11409c2e033488a76afa280561738.",
  },
  "why_it_matters": ("The audit counted 79 groups as actionable_now. Three consecutive councillor and coalition "
                     "directories have now each contributed at least one resolved group — district 7 and district 6 "
                     "had one apiece already actioned, and this one has two closed here. The set is being worked "
                     "down, not accumulating."),
  "measurement_note": "These are the only relationships in this run that plain hashing found on its own without a prior URL or filename hint, alongside the Transition Albuquerque group in district 7.",
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds and against the published site before recommending.",
  "objects_fetched": [
   {"id": FINAL_PLAN, "what": "North Fourth Street Rank III Corridor Plan, City Council draft 2010", "bytes": 13960760, "pages": 133},
   {"id": BACKGROUND, "what": "North Fourth Street Background and Resource Materials 2009", "bytes": 12912123, "pages": 100},
  ],
  "result_for_the_four_process_files": ("None is contained. Token coverage ran 0.6349 to 0.8750 against either object "
                                        "on token sets of 126 to 298, and no literal phrase from any of the four "
                                        "appears in either. They are excluded as process material, not called "
                                        "duplicates on a coverage number that would not support it."),
  "why_the_distinction_matters": ("Three clusters in a row have now produced coverage figures in the 0.6 to 0.9 band "
                                  "on sparse text, and in every case rendering or phrase-matching decided the "
                                  "question. Coverage alone has still never settled a case in this run."),
  "what_the_archive_already_holds_for_this_corridor": ("The corridor is unusually well covered: the 2004 community "
                                                       "visioning report, the Rank III corridor plan, its background "
                                                       "and resource materials, existing zoning and form-based "
                                                       "overlay zone maps, the North Fourth Street Metropolitan "
                                                       "Redevelopment Plan, and enacted Resolution R-17-160 held at "
                                                       "requires human review. That is why this directory adds "
                                                       "nothing."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 2,
  "url_collisions_in_this_directory": 2,
  "url_collisions_resolved_here": 2,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 2,
  "relationships_found_by_other_means": 0,
  "note": ("Two relationships and hashing found both, which is unusual for this run — in most clusters hashing has "
           "found nothing. It worked here because the twins are the same file served from the same URL, which is the "
           "one case byte comparison is built for."),
 },
 "integration_flags": [
  {"severity": "url-twin-resolution",
   "affects": ["src-4d604937d6910980", "src-f90f45e9692ffc1a"],
   "finding": "Two pending records are byte-identical twins of terminal records at the same URLs: one validated and published, one already superseded.",
   "recommended_action": f"Record both as duplicate of their twins. Together {avoided:,} bytes that do not need uploading and two actionable_now groups closed."},
  {"severity": "empty-result",
   "affects": [],
   "finding": "Nothing in this directory is recommended for addition and nothing needs human review. The corridor is already covered by seven archived or held records.",
   "recommended_action": "None. Recorded so the zero is legible as a finding rather than as an incomplete lane."},
  {"severity": "editorial",
   "affects": ["src-a7e8a65f2a77cbaa"],
   "finding": "The excluded survey results are the only quantified statement in the archive of what residents said about this corridor, charting concerns about pedestrian conditions, commercial development, transients, unsafe turns, neighborhood character, labor finder and tattoo businesses, and rural character.",
   "recommended_action": "No archival action. The categories are recorded in the row so the content is not lost with the file."},
  {"severity": "naming-trap",
   "affects": ["src-f90f45e9692ffc1a", DRAFT_TWIN],
   "finding": "A 34.7 MB draft of the North Fourth Street Rank III Corridor Plan is filed as 4th_street_and_montano_area_improvements_draft_plan.pdf inside a neighbourhood coalition directory. Neither name nor location identifies it.",
   "recommended_action": "None here; the twin already records it. Noted as a second instance of the pgs/Part2.pdf pattern — identity comes from the file, never from where it sits."},
 ],
 "counts": {
  "reviewed": len(rows),
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 6, "http_200": 6, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "archive_fetches": "Two R2 objects at files.abqinfo.com were fetched read-only for comparison, both HTTP 200 at their recorded byte sizes.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "6 genuine PDFs by leading bytes. All six have text layers; none needed rendering."},
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": ("Nothing in this cluster is recommended for archival. The two duplicate rows total "
                   f"{avoided:,} bytes, of which 34,703,589 is a corridor-plan draft whose terminal twin already "
                   "records that the final plan is archived and implemented instead."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Both duplicate rows carry a canonical_id pointing "
                      "at a terminal record at the same URL, confirmed byte-identical rather than inferred from the "
                      "URL match. No row is approved for addition and no row requires human review, so this artifact "
                      "adds nothing to either queue. Sizes and checksums are first measurements for the pending "
                      "records; the inventory held none for them, though it held both twins' checksums, which is what "
                      "made the confirmation possible."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the two R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
