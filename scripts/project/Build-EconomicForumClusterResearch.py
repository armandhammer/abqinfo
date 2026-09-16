"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\economic-forum-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\ef\fetch.log')

IRB1 = 'src-1aecdc742bc5be02'   # completed-reports-studies: Prager analysis, recommended for addition
IRB2 = 'src-2015fa7cf7b66c2e'   # completed-reports-studies: Cordova stakeholder study, recommended for addition
FLORIDA = 'src-0b6ab4d6ffe9f903'  # already terminal excluded

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw, v = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    RAW[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither. Container verified by leading bytes, not by extension.")

SUBSTITUTE_SHA = "129831124c34f7500f460763e399ae95741c4eaa6d6c62762f37781b00c9e318"


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML",
         "leading_bytes": MAGIC[i]}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


duplicates = [
 {**row("src-89db8d6610fb73c7", "duplicate"),
  "title_for_reference": "Analysis of Albuquerque's Industrial Revenue Bond Program, April 2002 (economic-forum copy)",
  "pages": 56,
  "canonical_id": IRB1,
  "canonical_url": IDX[IRB1].get('direct_file_url'),
  "canonical_state": "pending review in the inventory, and recommended for addition in completed-reports-studies-cluster-research-2026-09-12.json",
  "basis": "The City publishes this report twice, in two Council directories, under the same filename.",
  "measurement": ("Byte-identical: 1,082,660 bytes and SHA-256 "
                  "dec4d683e5b0835daf44c446885cf4cf0706b39264cbf3d953fcb0e87e7a787c, measured from both copies in "
                  "this run. The only difference is the directory: council/documents/economic-forum/irbrpt.pdf here "
                  "against council/documents/completed-reports-studies/irbrpt.pdf there."),
  "hash_found_it": True},

 {**row("src-f952903652637ff8", "duplicate"),
  "title_for_reference": "Albuquerque's Industrial Revenue Bond Program: Community Stakeholder Perspectives and Recommendations, May 2002 (economic-forum copy)",
  "pages": 46,
  "canonical_id": IRB2,
  "canonical_url": IDX[IRB2].get('direct_file_url'),
  "canonical_state": "pending review in the inventory, and recommended for addition in completed-reports-studies-cluster-research-2026-09-12.json",
  "basis": "The companion study, likewise published twice under the same filename.",
  "measurement": ("Byte-identical: 448,341 bytes and SHA-256 "
                  "40b90b2f7b64b29073998c1a356c892147c980511cc0d8105cac7b04915aa884."),
  "hash_found_it": True},
]

SUBSTITUTION = (
 "The URL returns HTTP 200 with 4,926 bytes of HTML, not a PDF. The leading bytes are 3c21444f, the start of a "
 "<!DOCTYPE declaration. The content is the homepage of Next Generation Economy, Inc., a private organisation "
 "unrelated to the City, beginning \"Our mission is to create a higher standard of living in New Mexico by nurturing "
 "an entrepreneurial environment powered by human creativity.\" The document the filename promises is gone and "
 "something else is served in its place.")

excluded = [
 {**row("src-719d61a1047aeb31", "excluded"),
  "title_for_reference": "Sirolli.pdf (content no longer present; a third-party homepage is served in its place)",
  "exclusion_reason": SUBSTITUTION,
  "category": "content substitution at the source",
  "substitute_checksum": SUBSTITUTE_SHA,
  "not_in_the_city_listing": ("The City's own collection listing for this directory shows four items — irbrpt.pdf, "
                              "irbrpt2.pdf, Central_New_Mexico_Competitiveness_Summit.pdf and Florida_Summary.pdf — "
                              "and does not list Sirolli.pdf at all. It was reached some other way. That is the third "
                              "directory in this run whose City listing is incomplete against its own server, after "
                              "nob-hill-highland-cluster-research-2026-09-11.json and "
                              "planned-growth-strategy-cluster-research-2026-09-11.json."),
  "what_it_probably_was": "Ernesto Sirolli's enterprise-facilitation approach was a live topic in Albuquerque economic development in this period, and the surrounding files are economic forum papers. Nothing about the actual document survives at this URL."},

 {**row("src-274f7f545f635d66", "excluded"),
  "title_for_reference": "Central_New_Mexico_Competitiveness_Summit.pdf (content no longer present; a third-party homepage is served in its place)",
  "exclusion_reason": SUBSTITUTION,
  "category": "content substitution at the source",
  "substitute_checksum": SUBSTITUTE_SHA,
  "listed_by_the_city": "Unlike Sirolli.pdf, this one is listed in the City's own collection index, so the index advertises a document the server no longer holds."},

 {**row("src-3c44f7d09f2add68", "excluded"),
  "title_for_reference": "Economic Forum collection landing page",
  "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
  "category": "collection landing page"},
]

rows = duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 5, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
avoided = sum(r["size_bytes"] for r in duplicates)
substituted = [r["id"] for r in excluded if r.get("substitute_checksum")]

artifact = {
 "batch_id": "economic-forum-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/economic-forum cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The City Council's Economic Forum file: two industrial revenue bond studies and three papers that are no longer there.",
 "scope": "All 5 pending-review candidates. The directory holds 6 records; the sixth is already excluded and this lane corrects the reason recorded for it.",
 "brief": "Run the standard opening sequence, testing each candidate against the published site as well as the inventory, and comparing normalized text rather than bytes wherever a version chain appears.",
 "brief_finding": ("Three of the five candidates are not documents at all. Sirolli.pdf, "
                   "Central_New_Mexico_Competitiveness_Summit.pdf and Florida_Summary.pdf each return HTTP 200 with "
                   "the same 4,926 bytes of HTML — the homepage of Next Generation Economy, Inc., a private "
                   "organisation — and each carries the identical SHA-256. There is no redirect and the URLs are "
                   "unchanged; a made-up filename in the same directory correctly returns 404, so these are real "
                   "Plone objects whose stored content has been replaced. A status-code link check would call all "
                   "three healthy."),
 "second_finding": ("The other two candidates are byte-identical second copies of the two Industrial Revenue Bond "
                    "studies recommended for addition from completed-reports-studies in this same batch. The City "
                    "publishes both reports twice, in two Council directories, under the same filenames irbrpt.pdf "
                    "and irbrpt2.pdf."),
 "method": ("Ran the URL group-by first; no collisions, because the two IRB copies sit in different directories and "
            "so have different URLs. Fetched all 5 candidates and measured byte length and SHA-256 from the fetched "
            "bytes, and verified every container by leading bytes rather than by extension. Compared the checksums "
            "against the copies fetched earlier in this run and against the 1,612 checksummed inventory records. "
            "Traced redirects on the three suspect URLs and tested a control filename. Parsed the City's own "
            "collection listing. Re-tested the URL behind the directory's one already-terminal record."),
 "classification_only": True,
 "shared_state_written": [],
 "content_substitution": {
  "what_it_is": ("A source URL that returns HTTP 200, at its original address, with no redirect, serving content that "
                 "is not the document it names. Distinct from a 404 and distinct from a redirect to a replacement "
                 "page."),
  "affected": substituted + [FLORIDA],
  "evidence": {
   "status": "HTTP 200 on all three, num_redirects 0, url_effective unchanged.",
   "control": "https://www.cabq.gov/council/documents/economic-forum/ZZZnotreal.pdf returns 404, so the server does distinguish missing objects. These three exist; their content is wrong.",
   "identical_substitute": "All three return the same 4,926 bytes with SHA-256 " + SUBSTITUTE_SHA + ".",
   "container": "Leading bytes 3c21444f, an HTML doctype, where a .pdf URL promises 25504446.",
   "content": "The homepage of Next Generation Economy, Inc., with its navigation and mission statement intact.",
  },
  "what_catches_it": ("Only reading the bytes. The run's standing practice of verifying containers by leading bytes "
                      "rather than by extension catches this on the first fetch; a link check that records status "
                      "codes does not, and neither does a redirect trace."),
  "corrects_a_terminal_record": {
   "record": FLORIDA,
   "recorded_reason": "\"Florida Summary (official City endpoint unavailable)\" — excluded on the basis that the endpoint could not be reached.",
   "what_is_actually_true": ("The endpoint is reachable and returns HTTP 200. What it returns is the same "
                             "substituted third-party homepage. The exclusion is right; the reason is not, and the "
                             "difference matters because a future availability re-check will see 200 and may try to "
                             "recover a document that is not there."),
   "recommended_action": "Update the recorded reason to content substitution rather than unavailability. Claude did not modify the record.",
  },
  "for_future_lanes": ("Treat an HTTP 200 as necessary and not sufficient. Any URL whose leading bytes disagree with "
                       "its extension should be recorded as substitution, with the substitute's checksum, so that "
                       "repeat fetches can be recognised rather than re-investigated."),
 },
 "incomplete_city_listing": {
  "finding": "The City's collection listing for this directory shows four items and omits Sirolli.pdf, which nevertheless exists as an object and returns 200.",
  "listed": ["irbrpt.pdf", "irbrpt2.pdf", "Central_New_Mexico_Competitiveness_Summit.pdf", "Florida_Summary.pdf"],
  "not_listed_but_present": ["Sirolli.pdf"],
  "third_instance": ("After nob-hill-highland-cluster-research-2026-09-11.json, where five files returning 200 were "
                     "absent from the listing, and planned-growth-strategy-cluster-research-2026-09-11.json, where "
                     "three were. The City's own indexes under-report what its server holds often enough that "
                     "filename-sequence probing remains worthwhile."),
  "the_twist_here": "The unlisted file is one of the substituted ones, so probing recovered a name whose content is gone. Completeness of discovery and integrity of content are separate problems.",
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects and published site entries, and against anything recommended earlier in the same batch.",
  "result": ("Two candidates are byte-identical to records recommended for addition hours earlier in this run. "
             "Catching it required comparing against the batch in progress, not only against terminal inventory "
             "state — the canonicals are still marked pending review in master-inventory.json because this run writes "
             "no shared state."),
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue, on top of the six reports already queued from completed-reports-studies.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "internal_byte_collision_group_size": 3,
  "internal_collision_is_not_a_document": "The three-way byte collision in this directory is between the substituted HTML pages, not between documents. Recording it as a duplicate group would be wrong; they are three different missing documents with one replacement page.",
  "cross_inventory_byte_collisions": 0,
  "cross_batch_byte_collisions": 2,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 2,
  "note": ("Hashing found both real relationships here, as it did in district 7 and 4th Street: it works when the same "
           "file is served from two places. It also produced a false-looking three-way collision that a careless pass "
           "would have recorded as a duplicate group of documents rather than as evidence that three documents are "
           "missing."),
 },
 "integration_flags": [
  {"severity": "source-integrity",
   "affects": substituted + [FLORIDA],
   "finding": "Three City URLs return HTTP 200 at their original addresses with a private organisation's homepage instead of the documents they name, all three byte-identical to each other.",
   "recommended_action": "Record all three as content substitution with the substitute checksum, and correct the reason on the already-terminal Florida Summary record from unavailability to substitution."},
  {"severity": "avoid-duplicate-archival",
   "affects": [r["id"] for r in duplicates],
   "finding": "The two 2002 Industrial Revenue Bond studies are published twice, in economic-forum and completed-reports-studies, byte-identical.",
   "recommended_action": f"Record these two as duplicate of the completed-reports-studies copies already recommended for addition. {avoided:,} bytes not uploaded twice."},
  {"severity": "discovery-hygiene",
   "affects": ["src-719d61a1047aeb31"],
   "finding": "Sirolli.pdf is absent from the City's own collection listing yet exists as an object. Third directory in this run where the listing under-reports the server.",
   "recommended_action": "Keep filename-sequence probing in the crawler, but pair it with a container check: probing found this name and its content is gone."},
  {"severity": "method",
   "affects": [],
   "finding": "A status-code link check would have marked all three substituted URLs healthy. The leading-bytes container check caught them on the first fetch.",
   "recommended_action": "Keep verifying containers by leading bytes rather than by extension, everywhere. This cluster is the case that demonstrates why."},
 ],
 "counts": {
  "reviewed": len(rows),
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 5, "http_200": 5, "failed": 0,
                "http_200_but_not_the_document": 2,
                "note": "Two of the five candidates returned 200 while serving substituted content; a third URL outside the pending set, behind the already-terminal Florida Summary record, does the same.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12, plus a redirect trace and a control request for a non-existent filename in the same directory.",
                "containers_verified": "2 genuine PDFs and 3 HTML responses by leading bytes, of which one is a real collection page and two are substituted content at .pdf URLs."},
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": ("Nothing in this cluster is recommended for addition. The two duplicate rows total "
                   f"{avoided:,} bytes and are already covered by the copies recommended from "
                   "completed-reports-studies. Nothing is recoverable from the three substituted URLs."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Both duplicate rows carry a canonical_id pointing "
                      "at a record that is still pending review in master-inventory.json and is recommended for "
                      "addition in completed-reports-studies-cluster-research-2026-09-12.json — apply that artifact "
                      "first, or apply both together, so the canonicals are not left pending behind their duplicates. "
                      "No row is approved for addition and no row requires human review. Every row carries a "
                      "leading_bytes field, which is what distinguishes the two real documents here from the two "
                      "substituted ones."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the already-terminal Florida Summary record was re-tested read-only and left unchanged"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
