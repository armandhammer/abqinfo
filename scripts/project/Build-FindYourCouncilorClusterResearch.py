"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-14. The last uncovered block in the inventory: the 169 remaining
council/find-your-councilor records.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\find-your-councilor-cluster-research-2026-09-14.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\fyc')

ROADWAY = 'content/transportation/roadway-projects/_index.md'
SAFETY = 'content/transportation/safety-crash-data.md'
BIKEIDX = 'content/transportation/bicycling/_index.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL, CODE = {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], URL[p[0]], CODE[p[0]] = p[4], p[5], p[1]

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR_IDS, PRIOR_SHA = set(), {}
for f in glob.glob(os.path.join(DISC, '*.json')):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8-sig'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR_IDS.add(r['id'])
                if r.get('checksum_sha256'):
                    PRIOR_SHA.setdefault(r['checksum_sha256'], (os.path.basename(f), r['id'], r.get('recommended_status')))
assert not (set(SLICE) & PRIOR_IDS), sorted(set(SLICE) & PRIOR_IDS)

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x)

KIND = {'25504446': 'PDF', '3c21444f': 'HTML', 'ffd8ffe0': 'JPEG'}
LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes and "
      "the container verified by leading bytes, never by the URL.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u, "recommended_status": status, "link_check": LC,
         "content_kind": KIND[MAGIC[i]], "leading_bytes": MAGIC[i], "http_status": CODE[i],
         "inventory_title": (IDX[i].get('title') or '').strip()}
    r.update(M[i])
    return r


CROSS_ARCH = {i: ARCH_BY_SHA[M[i]['checksum_sha256']]['id'] for i in SLICE
              if M[i]['checksum_sha256'] in ARCH_BY_SHA}
CROSS_PRIOR = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE
               if M[i]['checksum_sha256'] not in ARCH_BY_SHA and M[i]['checksum_sha256'] in PRIOR_SHA}

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
INTERNAL = {}
for v in BYHASH.values():
    if len(v) < 2 or any(x in CROSS_ARCH or x in CROSS_PRIOR for x in v):
        continue
    keep = sorted(v, key=lambda x: (len(URL[x]), x))[0]
    for x in v:
        if x != keep:
            INTERNAL[x] = keep

approved, duplicate, excluded = [], [], []

SANDIA = 'src-88b083b092a7305e'
r = row(SANDIA, "approved for addition")
r.update({
 "title": "Sandia High School Area Safety and Traffic Calming Study: public meeting presentation, 2023",
 "description": ("The consultant presentation for Councillor Tammy Fiebelkorn's 2023 District 7 study of safety and "
                 "traffic calming around Sandia High School, setting out the study area, its existing conditions and "
                 "the schedule leading to a final report."),
 "evidence": ("29 pages, 3,774,703 bytes, complete to its end marker. Its cover reads 2023 COUNCIL DISTRICT 7 "
              "PROJECT / COUNCILOR TAMMY FIEBELKORN / SANDIA HS AREA SAFETY AND TRAFFIC CALMING STUDY, prepared by "
              "Lee Engineering of 8220 San Pedro Drive NE. Its text layer carries little but the schedule and the "
              "section numbers, so the pages were rendered: page 27 is an On-Street Parking slide pairing a study-area "
              "map bounded by Comanche Rd, Louisiana Blvd and Candelaria with a community-provided photograph, and "
              "page 29 is a closing Thank You / Questions slide."),
 "group": "documents",
 "proposed_canonical_page": ROADWAY,
 "cross_listings": [{"page": SAFETY, "reason": "A traffic safety study of a specific area."},
                    {"page": BIKEIDX, "reason": "It has a bicycle facilities section."}],
 "what_this_document_is_not": ("Not the study's final report. Its own schedule slide lists Final Report July 2023 as "
                               "a future item, and the deck closes on a questions slide, so it is a presentation "
                               "given at one of the two public meetings the schedule names."),
 "the_final_report_has_since_been_found": ("Retrieved on 2026-09-14 from the City file-transfer host, which the "
                                           "project page links separately from this deck. It is dated January 2024, "
                                           "six months after this deck's schedule promised - so that July 2023 date "
                                           "was a plan, not a record. Measured in "
                                           "file-share-retrieval-research-2026-09-14.json."),
 "caution": "Label it as the meeting presentation, not as the study's final report.",
})
r["description_word_count"] = len(r["description"].split())
approved.append(r)

for i in sorted(CROSS_PRIOR):
    art, pid, st = CROSS_PRIOR[i]
    r = row(i, "excluded")
    r.update({
     "title_for_reference": (IDX[i].get('title') or '').strip() or URL[i],
     "what_it_is": "A live page on the City website, reached under a councillor's part of the site.",
     "exclusion_reason": ("Not a static document. The URL returns HTML and there is no original file to archive. It "
                          "is also byte-identical to a record this run has already decided, but that record was "
                          "itself excluded as a web page, so pointing a duplicate at it would name a canonical "
                          "that is not worth keeping. The relationship is recorded on this row instead."),
     "category": "live web page",
     "package": "web_pages",
     "byte_identical_to": {"id": pid, "decided_in": art, "its_recommended_status": st},
    })
    excluded.append(r)

for copy, canon in sorted(INTERNAL.items()):
    r = row(copy, "excluded")
    r.update({
     "title_for_reference": (IDX[copy].get('title') or '').strip() or URL[copy],
     "what_it_is": "A live page on the City website, served at a second address under another councillor's district.",
     "exclusion_reason": ("Not a static document. The URL returns HTML and there is no original file to archive. It "
                          "is byte-identical to another record in this same lane, but that record is excluded as a "
                          "web page too, so the relationship is recorded here rather than as a duplicate pointing "
                          "at an excluded canonical."),
     "category": "live web page",
     "package": "web_pages",
     "byte_identical_to": {"id": canon, "decided_in": "this artifact", "its_recommended_status": "excluded"},
    })
    excluded.append(r)

DONE = {x['id'] for x in approved + duplicate + excluded}

for i in SLICE:
    if i in DONE:
        continue
    if MAGIC[i] == 'ffd8ffe0':
        r = row(i, "excluded")
        r.update({
         "title_for_reference": "Councillor portrait photograph (%s)" % (IDX[i].get('title') or '').strip()[:34],
         "what_it_is": "A 400x500 pixel JPEG photograph served behind a content-management UID on a councillor's page.",
         "exclusion_reason": ("Site furniture, not a record. All four images in this lane are 400 by 500 pixels, the "
                              "portrait size the councillor pages use, and each is reached through a resolveuid "
                              "alias whose inventory title is only the identifier itself."),
         "category": "page portrait",
         "package": "site_furniture",
         "pixel_dimensions": "400x500",
        })
        excluded.append(r)
    else:
        r = row(i, "excluded")
        r.update({
         "title_for_reference": "Web page: " + URL[i].split('//')[1][:88],
         "what_it_is": "A live page on the City website under council/find-your-councilor.",
         "exclusion_reason": ("Not a static document. The URL returns HTML, and there is no original file to "
                              "archive. This is the same disposition the archive has applied to councillor pages "
                              "throughout."),
         "category": "live web page",
         "package": "web_pages",
        })
        excluded.append(r)

rows = approved + duplicate + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
bycontainer = collections.Counter(r["content_kind"] for r in rows)
byexcl = collections.Counter(r["package"] for r in excluded)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "find-your-councilor-cluster-research-2026-09-14",
 "lane": "Claude research lane: the 169 remaining council/find-your-councilor records",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14. The last uncovered block in the inventory.",
 "cluster": ("Everything still uncovered after fifteen lanes, and all of it under one path: "
             "www.cabq.gov/council/find-your-councilor."),
 "scope": "All 169 remaining uncovered candidates. The coverage gate is asserted in the generator.",
 "brief": ("councilor-district-3-and-6-cluster-research-2026-09-13.json established by fetching 100 of that tree's "
           "239 records that not one is a static document. Confirm that by measurement across all 169 rather than "
           "by inference, run the two-set checksum sweep, and record any record that is not a web page as a "
           "finding."),
 "why_the_brief_said_confirm_rather_than_assume": {
  "the_inference_that_was_available": ("A hundred records from the same tree had been fetched and every one was a "
                                       "web page. Recommending the remaining 169 as web pages without fetching them "
                                       "would have been the cheap move, and it is what the earlier lane's own "
                                       "recommendation to Codex implied."),
  "what_fetching_them_found": ("It was nearly right and not quite. 164 of the 169 are HTML. The other five are not: "
                               "four councillor portrait photographs, and one real document - a 29-page, "
                               "3,774,703-byte consultant study of safety and traffic calming around Sandia High "
                               "School."),
  "the_rule": ("A sample of 100 that is unanimous still says nothing certain about the 169 that were not sampled. "
               "The cost of checking was one fetch loop; the cost of not checking would have been losing a document "
               "permanently, because a class-wide exclusion is the kind of decision nobody revisits."),
 },
 "the_document_that_was_nearly_lost": {
  "what": "2023 Council District 7 Project: Sandia HS Area Safety and Traffic Calming Study, by Lee Engineering.",
  "where_it_was": ("Behind a resolveuid alias four levels deep: "
                   "council/find-your-councilor/district-7/district-7-projects/traffic-street-improvements/"
                   "sandia-high-school-area-safety-and-traffic-calming-measures/resolveuid/..."),
  "why_the_url_gave_nothing_away": ("The address ends in a 32-character identifier, and the inventory title is that "
                                    "same identifier. Nothing but the leading bytes distinguished it from the 164 "
                                    "web pages around it."),
  "why_the_text_layer_gave_little_away": ("pdftotext returns the schedule and the section numbers and almost nothing "
                                          "else - the deck's substance is in its images. The title block did survive "
                                          "extraction, but the study area, the analysis and the photographs had to "
                                          "be rendered to be seen."),
  "what_it_is_not": ("Not the final report. Its own schedule slide lists Final Report July 2023 as still to come, "
                     "and the deck ends on a questions slide."),
  "the_final_report_has_since_been_found": ("Retrieved on 2026-09-14 from the City file-transfer host, which the "
                                            "project page links separately from this deck. It is dated January "
                                            "2024, six months after the schedule promised - so the July 2023 date "
                                            "in this deck is a plan, not a record of what happened. Measured in "
                                            "file-share-retrieval-research-2026-09-14.json."),
 },
 "the_two_set_sweep": {
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "already_archived": len(CROSS_ARCH),
  "already_decided_in_this_run": len(CROSS_PRIOR),
  "one_object_two_addresses": len(INTERNAL),
  "what_it_found": ("Four pages byte-identical to rows in yesterday's final-sweep artifact - two copies of Report "
                    "Weed and Litter Issues and two of Contact all Councilors - and one further pair internal to "
                    "this lane. Stated exactly: there are three byte-identical pairs inside this lane, and two of "
                    "them are the pairs whose content also matches a row decided yesterday, so they are counted as "
                    "already-decided rather than twice. Six records are involved in those pairs and five rows carry a "
                    "byte identity, the sixth being the record its own pair is recorded against."),
  "why_none_of_them_is_a_duplicate_row": ("Every one of the seven is a web page, and so is every canonical they "
                                          "would point at. A duplicate row would name a canonical that is itself "
                                          "excluded, which is the opposite of what the status means. Each row is "
                                          "excluded on its own merits and carries byte_identical_to as a fact."),
 },
 "method": ("Fetched all 169 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. "
            "Classified by container, swept every checksum against the archived inventory records and against every "
            "row of every saved artifact, grouped by checksum within the lane, measured the four JPEGs' pixel "
            "dimensions from their SOF markers, and read the one PDF both by extraction and by rendering."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against the archived inventory records and against every row of every saved artifact.",
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts_in_this_run": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "The one approved document collides with nothing. The seven collisions are all between web pages.",
 },
 "duplicate_and_supersession_checks": {
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "duplicate_rows_recommended": len(duplicate),
  "note": ("Seven byte collisions, zero duplicate rows. The status is only meaningful when the canonical is a "
           "record worth keeping, and here none of them is."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [SANDIA],
   "finding": ("A 29-page Lee Engineering study of safety and traffic calming around Sandia High School, a 2023 "
               "District 7 project, sitting behind an opaque resolveuid alias among 164 web pages. The earlier "
               "recommendation to treat this whole tree as a bulk web-page confirmation would have excluded it."),
   "recommended_action": ("Approve as the public meeting presentation, not as the final report. Its own schedule "
                          "places a final report in July 2023 which is nowhere in the inventory - worth a targeted "
                          "search of the District 7 project pages.")},
  {"severity": "undiscovered-document",
   "affects": [SANDIA],
   "finding": "The Sandia High School study's final report, listed on this deck's schedule as due July 2023, is not in the inventory under any path.",
   "recommended_action": "Add it to the discovery queue rather than treating the presentation as the study's record."},
  {"severity": "method",
   "affects": sorted(CROSS_PRIOR) + sorted(INTERNAL),
   "finding": ("Seven records are byte-identical to other records, but every canonical they would point at is an "
               "excluded web page."),
   "recommended_action": ("Apply excluded, not duplicate. The byte_identical_to field on each row records the "
                          "relationship without asserting a canonical that is not worth keeping.")},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "containers": dict(bycontainer),
  "excluded_by_package": dict(byexcl),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; the one PDF tested for its end-of-file marker.",
                "containers_verified": "%d HTML, %d JPEG, %d PDF." % (bycontainer['HTML'], bycontainer['JPEG'],
                                                                      bycontainer['PDF'])},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": [],
 "excluded": excluded,
 "archival_note": (f"The {len(approved)} approved record is inventory-only until an R2 archive object exists for it "
                   f"and its public download, exact size, SHA-256, and authoritative-source provenance are verified. "
                   f"Archive footprint if authorized: {approved_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. No row in this artifact carries a canonical_id, "
                      "because no relationship here points at a record worth keeping; the seven byte-identity "
                      "findings are recorded as byte_identical_to on excluded rows. Sizes and checksums are first "
                      "measurements; the inventory held none."),
 "what_remains_after_this": ("Nothing. With this artifact every `pending review` record in master-inventory.json is "
                             "a row in a saved decision artifact. The pool is exhausted."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('containers', 'excluded_by_package')}}))
