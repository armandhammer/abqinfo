"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. transit/documents, parksandrecreation/open-space,
dot.nm.gov modal, and sustainability/transportation.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\transit-openspace-nmdot-sustainability-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\tx')

TRANSIT = 'content/transportation/transit/abq-ride.md'
TRANSPO = 'content/transportation/_index.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
CLIMATE = 'content/city-data/climate-environment.md'
PARKSREC = 'content/public-works/parks-recreation.md'
MAPS = 'content/maps-data/maps.md'
PROJECTS = 'content/development-land-use/projects.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR_IDS = set()
PRIOR_SHA = {}
for f in glob.glob(os.path.join(DISC, '*.json')):
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
                PRIOR_IDS.add(r['id'])
                if r.get('checksum_sha256'):
                    PRIOR_SHA.setdefault(r['checksum_sha256'], (os.path.basename(f), r['id'], b))
assert not (set(SLICE) & PRIOR_IDS), sorted(set(SLICE) & PRIOR_IDS)

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x)

CONTAINER = {'25504446': 'PDF', '3c21444f': 'HTML', 'd0cf11e0': 'OLE2', '89504e47': 'PNG', '': 'EMPTY'}
LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes - one URL in this lane returns HTTP 200 with no bytes at all.")


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i]))


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i] or "(none: zero bytes returned)",
         "served_filename": fname(i)}
    r.update(M[i])
    return r


HTML = [i for i in SLICE if MAGIC[i] == '3c21444f']
EMPTY = [i for i in SLICE if MAGIC[i] == '']
PNG = [i for i in SLICE if MAGIC[i] == '89504e47']
OLE2 = [i for i in SLICE if MAGIC[i] == 'd0cf11e0']
PDFS = [i for i in SLICE if MAGIC[i] == '25504446']

CROSS_PRIOR = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE if M[i]['checksum_sha256'] in PRIOR_SHA}
CROSS_ARCH = {i: ARCH_BY_SHA[M[i]['checksum_sha256']]['id'] for i in SLICE if M[i]['checksum_sha256'] in ARCH_BY_SHA}

BYHASH = collections.defaultdict(list)
for i in SLICE:
    if M[i]['size_bytes'] == 0:
        continue
    BYHASH[M[i]['checksum_sha256']].append(i)
INTERNAL = {}
for v in BYHASH.values():
    if len(v) == 2 and not any(x in CROSS_PRIOR or x in CROSS_ARCH for x in v):
        a, b = sorted(v, key=lambda x: (len(URL[x]), x))
        INTERNAL[b] = a

EXPIRED = ['src-f81117edb505b024', 'src-36c838882f36a329', 'src-d0b2ba6d737deb99', 'src-720f7e3fe3dd0455']

TITLES = {
 'src-cd76ed2642c5bc5b': ("Para-Transit Advisory Board minutes, 9 September 2009", TRANSIT),
 'src-e42bbc888a2b6931': ("Para-Transit Advisory Board minutes, 9 February 2010", TRANSIT),
 'src-6220c942e21cbc67': ("Para-Transit Advisory Board minutes, 6 May 2009", TRANSIT),
 'src-54391dbd27e5d212': ("Environmental Assessment: New Mexico Rail Runner Montano Station (draft)", TRANSIT),
 'src-ee0aec5b78f6ec86': ("Traffic Assessment: Montano Rail Runner Station", STUDIES),
 'src-e28e38dabfbdb2e2': ("Montano Rail Runner Station Framework Plan, June 2010", TRANSIT),
 'src-4092005fa5d61b38': ("Montano Rail Runner Station certification, NMDOT, 11 August 2010", TRANSIT),
 'src-2dbbf587fead4146': ("Plans for Construction: New Mexico Rail Runner Express Montano Station, Project 559292, 65% submittal", TRANSIT),
 'src-12207bd87008378c': ("Plans for Construction: Montano Station, part II", TRANSIT),
 'src-bd98a6f5ef11e68b': ("Paseo del Bosque Trail map", PARKSREC),
 'src-f0b725eecf05a992': ("Paseo del Bosque Trail guide", PARKSREC),
 'src-62ebf9197c3727ba': ("Electrified Dealer Program: programme overview", CLIMATE),
 'src-bd33f9a55aae6b71': ("ABQ RIDE directions to the Albuquerque Convention Center", TRANSIT),
 'src-3f7f0d0579ad62c0': ("ABQ RIDE Honored Citizen identification card application", TRANSIT),
}

approved, duplicate, excluded = [], [], []

for i, (art, pid, bucket) in sorted(CROSS_PRIOR.items()):
    r = row(i, "duplicate")
    r.update({"canonical_id": pid,
              "title_for_reference": fname(i),
              "relationship": "The same file this run already decided as %s in %s." % (pid, art),
              "how_it_was_established": ("Byte-identical: %s bytes and the same SHA-256 as a row already recorded in "
                                         "a saved artifact. The candidate reaches the file through a resolveuid "
                                         "alias under sustainability/transportation, so its URL shares nothing with "
                                         "the earlier record's." % format(M[i]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "The earlier artifact decided it first and recommended it for addition; recommending it again would tell Codex to archive one file twice.",
              "decided_in": art,
              "group": "already decided in this run"})
    duplicate.append(r)

for copy, canon in sorted(INTERNAL.items()):
    r = row(copy, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": fname(copy) + " (query-string variant)",
              "relationship": "The same page as its canonical, reached with a query string appended.",
              "how_it_was_established": ("Byte-identical: both %s bytes with the same SHA-256. The two URLs differ "
                                         "only by a trailing ?programInfo=overview." % format(M[copy]['size_bytes'], ',')),
              "why_this_one_is_the_copy": "A query string is not a different document.",
              "group": "query-string twins"})
    duplicate.append(r)

DONE = {r['id'] for r in duplicate}

for i in OLE2 + PDFS:
    if i in DONE or i in EXPIRED:
        continue
    t, canon = TITLES.get(i, (fname(i), TRANSIT))
    if 'Para-Transit' in t:
        desc = ("The Para-Transit Advisory Board's own minutes of this meeting, the record of what the board "
                "considered and decided about the City's paratransit service on that date.")
        grp = "Para-Transit Advisory Board minutes"
    elif 'Montano' in t:
        desc = ("Part of the record behind the New Mexico Rail Runner Express station at Montano Road: %s, one of "
                "the studies, assessments, plans and drawings the City and its partners produced for the station."
                % t)
        grp = "Montano Rail Runner Station record"
    elif 'Paseo del Bosque' in t:
        desc = ("The City's public guidance for the Paseo del Bosque Trail, the multi-use trail along the Rio Grande "
                "through Albuquerque, published for people using the trail.")
        grp = "open space and trails"
    else:
        desc = ("The City's %s, part of the public information it publishes about the service or programme it "
                "describes." % t)
        grp = "City service and programme information"
    w = desc.split()
    if len(w) > 50:
        desc = ' '.join(w[:48]).rstrip(',.;') + '.'
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc,
              "evidence": "Published at %s as %s." % (URL[i].split('//')[1].rsplit('/', 1)[0][:70], fname(i)),
              "group": grp, "proposed_canonical_page": canon,
              "cross_listings": ([{"page": TRANSPO, "reason": "Regional rail serving Albuquerque."}]
                                 if grp == "Montano Rail Runner Station record"
                                 else [{"page": MAPS, "reason": "A trail map."}] if grp == "open space and trails"
                                 else []),
              "description_word_count": len(desc.split())})
    if i == 'src-2dbbf587fead4146':
        r["caution"] = ("Its title block reads 65% SUBMITTAL. These are design drawings at a submittal stage, not "
                        "as-built or final construction drawings. Say so wherever they are cited.")
    if i == 'src-54391dbd27e5d212':
        r["caution"] = "Its filename records it as a draft environmental assessment. Label it a draft."
    approved.append(r)
    DONE.add(i)

for i in EXPIRED:
    r = row(i, "excluded")
    r.update({"title_for_reference": fname(i),
              "what_it_is": "A dated transit schedule, detour notice, meeting flier or promotional contest rule.",
              "exclusion_reason": ("Expired service ephemera. It announces a schedule, a detour, a meeting or a "
                                   "contest for a date now years past: a 2013 weekday route schedule, a 2011 state "
                                   "fair detour, a public meeting flier and a promotional contest's rules. Current "
                                   "service information is recommended in this artifact; these are not it."),
              "category": "expired service notice",
              "package": "expired_ephemera"})
    excluded.append(r)
    DONE.add(i)

for i in EMPTY:
    r = row(i, "excluded")
    r.update({"title_for_reference": fname(i),
              "what_it_is": "A URL that returns HTTP 200 and no bytes.",
              "exclusion_reason": ("There is no document at this URL. The request succeeds - HTTP 200, no redirect - "
                                   "and returns zero bytes. Its name suggests a fourth set of Para-Transit Advisory "
                                   "Board minutes, dated 11 November 2011, and if those minutes exist they are not "
                                   "here. Nothing can be archived from an empty response."),
              "category": "empty response",
              "package": "nothing_at_the_url",
              "for_integration": ("Worth a note in the terminal record: HTTP 200 is not evidence that a file exists. "
                                  "This is the second failure of that kind in the run, after three economic-forum "
                                  "URLs that returned 200 while serving a homepage."),
              })
    excluded.append(r)
    DONE.add(i)

for i in PNG:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Image behind a UID alias: " + fname(i),
              "what_it_is": "A PNG image reached through a content management system UID under the sustainability transportation page.",
              "exclusion_reason": ("Site furniture. The URL is a resolveuid alias and the bytes are a small PNG used "
                                   "to illustrate a page, not a record of anything the City did. Same treatment as "
                                   "the councillor portrait images in "
                                   "councilor-district-3-and-6-cluster-research-2026-09-13.json."),
              "category": "page image behind a UID alias",
              "package": "site_furniture"})
    excluded.append(r)
    DONE.add(i)

for i in HTML:
    if i in DONE:
        continue
    r = row(i, "excluded")
    r.update({"title_for_reference": "Web page: " + URL[i].split('//')[1][:90],
              "what_it_is": "A live page on the City's or NMDOT's site.",
              "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f. The archive "
                                   "has already settled this class at these paths, excluding navigation, pagination, "
                                   "contact, or generic interface text captured as a candidate."),
              "category": "live web page",
              "package": "web_pages"})
    excluded.append(r)

rows = approved + duplicate + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "transit-openspace-nmdot-sustainability-cluster-research-2026-09-13",
 "lane": "Claude research lane: transit/documents, parksandrecreation/open-space, dot.nm.gov modal, and sustainability/transportation",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": "Four small directories taken together because none is large enough to be a lane on its own.",
 "scope": "All 58 uncovered candidates across the four sources. The coverage gate is asserted in the generator.",
 "brief": "Check existing dispositions at each source first and run the cross-inventory checksum sweep before writing.",
 "brief_finding": ("The sweep found nothing against the archived set - and then found two collisions against a set I "
                   "had not been sweeping at all. See a_gap_in_my_own_method."),
 "a_gap_in_my_own_method": {
  "what_the_sweep_had_been_doing": ("Comparing every fetched checksum against every checksum carried by a validated, "
                                    "archived, published or implemented inventory record - %d of them. That is what "
                                    "found fifteen already-archived records across the four previous lanes."
                                    % len(ARCH_BY_SHA)),
  "what_it_was_not_doing": ("Comparing against records this run had already decided. Those are still pending review "
                            "in the inventory and carry no checksum there; their checksums exist only inside the "
                            "saved artifacts."),
  "what_that_missed_here": ("Two candidates in this lane are byte-identical to records recommended for addition in "
                            "earlier artifacts of this same run: the Optimized Municipal Electric Vehicle Charging "
                            "Analysis, approved in "
                            "riometro-sustainability-econdev-cluster-research-2026-09-13.json, and the Vision Zero "
                            "executive order, approved in "
                            "municipaldevelopment-flat-remainder-cluster-research-2026-09-13.json. Both reach this "
                            "lane through resolveuid aliases whose URLs share nothing with the earlier records'."),
  "what_would_have_happened": ("Not a wrong fact - both earlier approvals stand - but Codex would have been told to "
                               "archive one file twice under two candidate ids, which is precisely what the sweep "
                               "exists to prevent."),
  "the_fix_applied_here": ("The sweep now runs against two sets: the archived inventory records, and every checksum "
                           "recorded on any row of any saved artifact - %d of them. Both are checked before anything "
                           "is recommended." % len(PRIOR_SHA)),
  "for_every_later_lane": "Sweep against both sets. An artifact is shared state as much as the inventory is.",
 },
 "http_200_is_not_evidence_that_a_file_exists": {
  "the_case": ("transit/documents/copy2_of_Minutes11.15.11.doc returns HTTP 200, no redirect, and zero bytes. The "
               "fetch succeeds and there is nothing in it."),
  "why_it_matters": ("A link check that records status codes would pass this URL. Only measuring the bytes catches "
                     "it - the leading-bytes check has nothing to read."),
  "what_is_probably_missing": ("Its name is the shape of the three Para-Transit Advisory Board minutes recommended "
                               "in this artifact, dated 11 November 2011. If those minutes exist they are not at "
                               "this address."),
  "the_second_of_its_kind": ("economic-forum-cluster-research-2026-09-12.json recorded three URLs that returned HTTP "
                             "200 while serving 4,926 bytes of homepage HTML. Different failure, same lesson."),
 },
 "the_montano_station_record": {
  "count": len([r for r in approved if r['group'] == 'Montano Rail Runner Station record']),
  "what_it_is": ("Six documents covering one station from study to drawings: a draft environmental assessment, a "
                 "traffic assessment, the MRCOG framework plan of June 2010, an NMDOT certification of 11 August "
                 "2010, and two sets of construction plans."),
  "the_caution_on_the_drawings": ("The 46-sheet plan set is titled CITY OF ALBUQUERQUE, DEPARTMENT OF MUNICIPAL "
                                  "DEVELOPMENT, PLANS FOR CONSTRUCTION, NEW MEXICO RAIL RUNNER EXPRESS MONTANO "
                                  "STATION, PROJECT #559292 - and stamped 65% SUBMITTAL. They are design drawings at "
                                  "a submittal stage, not as-built drawings, and the row says so."),
 },
 "three_sets_of_minutes_a_board_the_archive_does_not_cover": {
  "count": len([r for r in approved if r['group'] == 'Para-Transit Advisory Board minutes']),
  "what_they_are": "Para-Transit Advisory Board minutes for 6 May 2009, 9 September 2009 and 9 February 2010, as legacy OLE2 Word documents read with antiword.",
  "why_they_matter": ("They are minutes, not agendas, so no exception is needed to keep them. A fourth set is named "
                      "in this directory and returns nothing; see http_200_is_not_evidence_that_a_file_exists."),
 },
 "method": ("Read the archive's existing dispositions at all four sources before fetching. Fetched all 58 candidates "
            "and measured byte length, SHA-256 and leading bytes from the fetched bytes. Swept every checksum "
            "against the archived inventory records and, after finding the gap described above, against every "
            "checksum recorded on any row of any saved artifact. Grouped by checksum within the slice. Extracted "
            "text with the right reader for each container and rendered the three files with none."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, against anything recommended earlier in the same batch, and - new in this artifact - against every row of every saved artifact.",
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts_in_this_run": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing here duplicates the archive. Two candidates duplicate records this run already recommended, and are recommended duplicate against them.",
 },
 "duplicate_and_supersession_checks": {
  "cross_inventory_byte_collisions": len(CROSS_ARCH),
  "collisions_with_earlier_artifacts": len(CROSS_PRIOR),
  "internal_byte_collisions": len(INTERNAL),
  "relationships_found": len(duplicate),
  "the_query_string_twin": ("An NMDOT motorcycle safety page is registered twice, once plain and once with "
                            "?programInfo=overview appended. Byte-identical. A query string is not a different "
                            "document."),
 },
 "integration_flags": [
  {"severity": "method",
   "affects": sorted(CROSS_PRIOR),
   "finding": "Two candidates are byte-identical to records recommended for addition in earlier artifacts of this same run, reached through resolveuid aliases. The checksum sweep had been comparing only against archived inventory records, not against rows of saved artifacts.",
   "recommended_action": "Sweep against both sets in every later lane. A saved artifact is shared state as much as the inventory is. Detail in a_gap_in_my_own_method."},
  {"severity": "link-check",
   "affects": EMPTY,
   "finding": "transit/documents/copy2_of_Minutes11.15.11.doc returns HTTP 200 with zero bytes. A status-code link check would pass it.",
   "recommended_action": "Exclude, and record in the terminal set that HTTP 200 is not evidence a file exists. If the 11 November 2011 Para-Transit minutes are wanted, they must be sought elsewhere."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'Montano Rail Runner Station record'],
   "finding": "Six documents covering the Montano Rail Runner station from environmental and traffic assessment through the MRCOG framework plan, NMDOT certification and two sets of construction plans.",
   "recommended_action": "Approve as a set. The 46-sheet plan set is stamped 65% SUBMITTAL and its row says so; do not cite it as as-built."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'Para-Transit Advisory Board minutes'],
   "finding": "Three sets of Para-Transit Advisory Board minutes, 2009 and 2010, as legacy OLE2 documents. Minutes, not agendas, so no exception is needed.",
   "recommended_action": "Approve and archive in their original format."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_with_no_bytes": len(EMPTY),
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "rendered": "3 files with no usable text layer.",
                "containers_verified": ("%d HTML pages, %d PDFs, %d legacy OLE2 documents, %d PNG images and %d "
                                        "empty response by leading bytes."
                                        % (bycontainer['HTML'], bycontainer['PDF'], bycontainer['OLE2'],
                                           bycontainer['PNG'], bycontainer['EMPTY']))},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": [],
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. Three approved "
                   f"records are legacy OLE2 documents and should be archived in their original format rather than "
                   f"converted."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Three rows carry a canonical_id: two point at rows "
                     "in earlier artifacts of this run and name the artifact in decided_in, and one at a row in this "
                     "artifact. Every row carries a served_filename and a leading_bytes field; the empty response "
                     "carries a leading_bytes value saying so explicitly. Two approved rows carry a caution about "
                     "their draft or submittal status. Sizes and checksums are first measurements; the inventory "
                     "held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
