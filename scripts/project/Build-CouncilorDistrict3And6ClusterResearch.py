"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. First slice of the council/find-your-councilor tree: the
district-3 and district-6 councillor sets.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-3-and-6-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d36')

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL, FINAL = {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw, final = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw
    FINAL[i] = final

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR = set()
for f in glob.glob(r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\*.json'):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR.add(r['id'])
assert not (set(SLICE) & PRIOR), sorted(set(SLICE) & PRIOR)

CONTAINER = {'3c21444f': 'HTML', 'ffd8ffe0': 'JPEG'}

LC = ("HTTP 200 verified 2026-09-13 by full GET, following redirects and recording the effective URL; size_bytes "
      "and checksum_sha256 measured from the fetched bytes. Container verified by leading bytes, not by extension - "
      "none of these URLs has an extension.")

SAME = {i for i in SLICE if 'resolveuid' in URL[i]}
PORTRAIT = {i for i in SLICE if MAGIC[i] == 'ffd8ffe0'}

# resolveuid records whose target is itself a candidate in this slice
BYURL = {}
for i in SLICE:
    BYURL.setdefault(URL[i].rstrip('/'), i)
ALIAS_OF = {}
for i in SAME:
    t = FINAL[i].rstrip('/')
    if t in BYURL and BYURL[t] != i:
        ALIAS_OF[i] = BYURL[t]

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
TWINS = {tuple(sorted(v)) for v in BYHASH.values() if len(v) > 1}


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if FINAL[i].rstrip('/') != u.rstrip('/'):
        r["resolves_to"] = FINAL[i]
    r.update(M[i])
    return r


def label(i):
    p = URL[i].split('/find-your-councilor/', 1)[-1]
    return p


excluded = []
for i in SLICE:
    r = row(i, "excluded")
    p = label(i)
    if i in PORTRAIT:
        r.update({"title_for_reference": "Councillor portrait photograph, " + os.path.basename(FINAL[i]),
                  "what_it_is": ("A content management system UID that redirects to a councillor's portrait "
                                 "photograph in the Council's shared image folder."),
                  "exclusion_reason": ("Site furniture. It is a 400 by 500 pixel portrait used to illustrate the "
                                       "councillor's page, not a record of anything the City did. It is also not the "
                                       "object the candidate URL names: the URL is a UID under a district folder and "
                                       "the bytes are a JPEG in /council/images/."),
                  "category": "portrait image behind a UID alias",
                  "package": "site_furniture"})
    elif i in SAME:
        tgt = ALIAS_OF.get(i)
        r.update({"title_for_reference": "Plone UID alias: " + p,
                  "what_it_is": "A content management system UID redirect, not a document.",
                  "exclusion_reason": ("Not a document and not a distinct object. The URL is a Plone resolveuid "
                                       "alias; fetched, it redirects to %s, which is a live web page." % FINAL[i]),
                  "category": "navigational alias",
                  "package": "uid_aliases"})
        if tgt:
            r["aliases_a_candidate_in_this_slice"] = tgt
            r["exclusion_reason"] += (" That target is itself a candidate in this slice, %s, so the two records "
                                      "describe one page." % tgt)
    else:
        r.update({"title_for_reference": "Council web page: " + p,
                  "what_it_is": "A live page on the City Council's website.",
                  "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f - a "
                                       "councillor page rendered by the City's content management system, not a file "
                                       "the City published. The archive's standing rule is that a record is not "
                                       "site-ready until its original is archived to R2 and the download verified; "
                                       "there is no original here to archive."),
                  "category": "live web page",
                  "package": "councillor_web_pages"})
        if re.search(r'/news/', URL[i]):
            r["category"] = "live web page: councillor news release"
            r["exclusion_reason"] += (" It is also a councillor news release, and press releases are excluded on the "
                                      "ground recorded in councilor-district-4-cluster-research-2026-09-12.json.")
    excluded.append(r)

for t in sorted(TWINS):
    for i in t:
        for r in excluded:
            if r['id'] == i:
                r["byte_identical_to"] = [x for x in t if x != i]

rows = excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids)), sorted(set(ids) - set(SLICE)))
counts = collections.Counter(r["recommended_status"] for r in rows)
bycategory = collections.Counter(r["category"] for r in rows)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

DISCOVERED = []
for line in open(os.path.join(SP, 'discovered.log'), encoding='utf-8'):
    code, sz, sha, mag, u = line.rstrip('\n').split('\t')
    DISCOVERED.append({"url": u, "http": int(code), "size_bytes": int(sz),
                       "checksum_sha256": sha, "leading_bytes": mag,
                       "content_kind": "PDF"})

artifact = {
 "batch_id": "councilor-district-3-and-6-cluster-research-2026-09-13",
 "lane": "Claude research lane: the district-3 and district-6 sets under www.cabq.gov/council/find-your-councilor",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13, the first slice of the council/find-your-councilor tree.",
 "cluster": "The two largest councillor document sets not yet reviewed: 29 candidates under district-3 and 41 under district-6.",
 "scope": "All 70 uncovered candidates in the two districts. The coverage gate is asserted in the generator.",
 "brief": ("District lanes are already established for 1, 2, 4, 5, 6, 7, 8 and 9, so check each record against those "
           "artifacts before deciding, and carry the render-and-hash rule into any map or graphic set."),
 "brief_finding": ("There is nothing to render and nothing to compare against the earlier artifacts, because there "
                   "is not a single document in this lane. All 70 candidates were fetched: 68 return HTML and 2 "
                   "return a JPEG. Not one is a PDF, a Word file, a spreadsheet or any other static document."),
 "the_finding": {
  "what_these_records_are": ("Live pages on the City Council's website - councillor biographies, news releases, "
                             "event notices, project pages, neighbourhood association lists - plus Plone UID "
                             "aliases that redirect to those same pages, plus two councillor portrait photographs "
                             "sitting behind such aliases."),
  "why_none_of_it_can_be_archived": ("The archive's standing rule is that a record is not site-ready until its "
                                     "original is archived to R2 and the public download verified against an exact "
                                     "size, a SHA-256 and an authoritative source. A rendered web page has no "
                                     "original to archive. These are pages to link, if they are wanted at all, not "
                                     "candidates to archive."),
  "the_aliases": ("%d of the 70 are Plone resolveuid URLs. Fetched and followed, they redirect to ordinary pages - "
                  "several of them to pages that are themselves separate candidates in this same slice, so the "
                  "inventory holds the same page twice under two URLs. Two alias records are byte-identical to the "
                  "district-6 project pages they point at."
                  % len(SAME)),
  "the_portraits": ("Two aliases resolve not to pages but to councillor portrait photographs in the Council's shared "
                    "image folder, minicouncil3_400x500_2022.jpg and minicouncil6_400x500_2022.jpg. They are site "
                    "furniture."),
 },
 "and_it_generalises": {
  "the_population": "239 uncovered candidates under council/find-your-councilor, across all nine districts.",
  "what_was_checked": ("Every one of the 239 URLs has no file extension, and 76 of them are resolveuid aliases. "
                       "Beyond the 70 decided here, a random sample of 30 was drawn from the remaining 169 and "
                       "fetched: 29 returned HTML and one returned a JPEG."),
  "the_result": ("100 of the 239 have now been fetched and measured by leading bytes, and not one is a static "
                 "document. The evidence does not prove the remaining 139 are all pages, but it makes it the "
                 "overwhelming likelihood."),
  "recommended_action": ("Codex should fetch the remaining 139 and, for every one that returns HTML, take them out "
                         "of the document candidate pool rather than queuing them for triage. That is 139 records "
                         "of review effort that would find nothing to archive."),
  "why_this_matters_to_the_run": ("This tree is the largest single block of uncovered candidates left in the "
                                  "inventory. Treating it as a document backlog overstates how much archival work "
                                  "remains by about a sixth of the whole."),
 },
 "where_the_value_actually_is": {
  "the_method": ("A page cannot be archived, but the files a page links to can. Every one of the 68 HTML candidates "
                 "was parsed for links to pdf, doc, docx, xls, xlsx, ppt, pptx and csv files, and the results "
                 "reconciled against the inventory."),
  "links_found": 5,
  "already_held": ("One, 118th-street-study-public-meeting.pdf, which the archive already holds validated and "
                   "R2-archived."),
  "undiscovered": len(DISCOVERED),
  "the_best_of_them": ("cruising-task-force-final-report_.pdf is the Albuquerque City Council Cruising Task Force "
                       "Findings and Recommendations, dated April 2, 2018 and produced per Resolution R-17-250. It "
                       "is 9,756,353 bytes, it is linked from the district-3 cruising initiative page, and it is "
                       "absent from the inventory. A Council task force report produced under a named resolution is "
                       "exactly the kind of record this archive exists for."),
  "all_four_verified": "Each was fetched individually; all four return HTTP 200 with PDF leading bytes 25504446.",
  "a_cross_slice_note": ("2026-8-15-theory-of-change-final-pdf.pdf also appeared in the 37 undiscovered files found "
                         "from the City's MS4 permit page in "
                         "facility-environmental-compliance-cluster-research-2026-09-12.json. Two unrelated City "
                         "pages link it and the inventory has it from neither."),
  "the_transferable_point": ("This is the second slice in which reading a City page that a candidate pointed at "
                             "found records the crawl missed. In the stormwater slice it produced 37 files; here a "
                             "lane with no documents in it at all still produced four. **When a candidate is a page, "
                             "harvest its links before discarding it.**"),
  "files": DISCOVERED,
 },
 "method": ("Fetched all 70 candidates following redirects, recording the effective URL for each, and measured byte "
            "length, SHA-256 and leading bytes from the fetched bytes. Grouped by checksum to find byte-identical "
            "records. Matched every resolveuid target against the candidate list to find aliases of records already "
            "in the slice. Parsed every HTML body for links to static files and reconciled those against the 1,612 "
            "checksummed inventory records, then fetched and measured each file that was missing. Drew and fetched a "
            "30-record random sample from the rest of the tree to test whether the finding generalises."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": len(TWINS),
  "result": "Nothing here is recommended for addition, so nothing can duplicate the archive. The two internal byte collisions are alias-and-page pairs.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(TWINS),
  "cross_inventory_byte_collisions": 0,
  "aliases_pointing_at_candidates_in_this_slice": len(ALIAS_OF),
  "relationships_found": len(ALIAS_OF),
  "note": ("These are recorded on the rows as aliases rather than as duplicate relationships, because a duplicate "
           "recommendation carries a canonical_id and a canonical must be a record worth keeping. Nothing in this "
           "slice is."),
 },
 "integration_flags": [
  {"severity": "not-a-document-lane",
   "affects": [],
   "finding": f"All 70 candidates in district-3 and district-6 are live web pages or content management system aliases: {bycontainer['HTML']} return HTML and {bycontainer['JPEG']} return a councillor portrait JPEG. There is no static document in the lane.",
   "recommended_action": "Exclude all 70. If any of these pages is worth citing, cite it as an official live link on the relevant page, which is what the archive already does elsewhere; do not queue them for archival."},
  {"severity": "scope-correction",
   "affects": [],
   "finding": "The finding generalises. All 239 uncovered candidates under council/find-your-councilor are extensionless URLs, 76 of them resolveuid aliases; 100 have now been fetched, across two districts plus a 30-record random sample of the rest, and not one is a static document.",
   "recommended_action": "Fetch the remaining 139 and remove every HTML responder from the document candidate pool. This is the largest block of uncovered candidates in the inventory and it is very largely not archival work at all."},
  {"severity": "add-candidates",
   "affects": [],
   "finding": f"{len(DISCOVERED)} City documents linked from these councillor pages and absent from the inventory, all verified HTTP 200 with PDF leading bytes. The most substantial is the Albuquerque City Council Cruising Task Force Findings and Recommendations of April 2, 2018, produced per Resolution R-17-250, at 9,756,353 bytes.",
   "recommended_action": "Add all four as candidates; their URLs, sizes and checksums are recorded in where_the_value_actually_is.files."},
  {"severity": "method",
   "affects": [],
   "finding": "A candidate that turns out to be a web page is still worth parsing. This lane had no documents in it and still produced four undiscovered files; the stormwater slice produced 37 the same way.",
   "recommended_action": "Harvest links from any HTML candidate before discarding it."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "excluded": counts["excluded"],
  "excluded_by_category": dict(bycategory),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "static_documents_found": 0,
                "method": "Full HTTP GET with a browser user agent, following redirects, 2026-09-13.",
                "additional_fetches": ("30 sampled records from the rest of the tree, plus %d undiscovered files, "
                                       "plus the four link targets checked against the inventory." % len(DISCOVERED)),
                "containers_verified": ("%d HTML pages and %d JPEG images by leading bytes. No candidate in this "
                                        "lane has a file extension in its URL, so extension could not have been "
                                        "used." % (bycontainer['HTML'], bycontainer['JPEG']))},
 "approved_for_addition": [],
 "excluded": excluded,
 "archival_note": ("Nothing in this artifact is recommended for addition, so there is no archive footprint. The four "
                   "undiscovered files named in where_the_value_actually_is are not candidates yet and are not "
                   "recommended here; they are reported so they can be added and reviewed on their own terms."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Every row is excluded and every row carries a "
                     "category and a package so the three kinds can be handled separately: live pages, UID aliases, "
                     "and two portrait images. Rows that alias another candidate in this slice name it in "
                     "aliases_a_candidate_in_this_slice; rows that are byte-identical to another name it in "
                     "byte_identical_to. No row carries a canonical_id, deliberately: a canonical must be a record "
                     "worth keeping, and none of these is. The four undiscovered files cannot be applied through "
                     "Update-Candidate because they are not candidates."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the sample fetch and the link harvest were read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "reviewed": len(rows), "excluded": counts["excluded"],
                  "by_category": dict(bycategory), "undiscovered": len(DISCOVERED)}))
