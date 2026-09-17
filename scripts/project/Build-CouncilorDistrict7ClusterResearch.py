"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-7-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d7\fetch.log')

STUDIES = 'content/transportation/roadway-projects/studies.md'
BIKE = 'content/transportation/bicycling/projects/_index.md'
DESIGN = 'content/transportation/design-references.md'

UPTOWN_FINAL = 'src-967112fbf63ba98f'   # validated + R2 + published: the FINAL report
UPTOWN_R2DUP = 'src-468a382736e4056e'
BIKE_ASSESS = 'src-a42856962290497a'    # validated + R2 + published
FLYER_CANON = 'src-8cb66c7833f15fd7'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw, v = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    RAW[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET on both URL forms; size_bytes and checksum_sha256 measured "
      "from the bytes returned by the raw file URL, because the inventory record carried neither")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


approved = [{
 **row("src-c8b06367d22b8e24", "approved for addition"),
 "title": "Observations and Recommendations: The Built Environment, Albuquerque, New Mexico — Walkable and Livable Communities Institute, June 2014 (Draft)",
 "description": ("A consultant memo prepared for the City records what a walkability review of Albuquerque's built "
                 "environment found and recommends changes to street design, crossings, block structure, parking, and "
                 "land use to improve health and walkability."),
 "date": "2014-06",
 "pages": 10,
 "evidence": ("Born-digital PDF with a full text layer, headed DRAFT. \"Prepared by the Walkable and Livable "
              "Communities Institute for the City of Albuquerque, June 2014\". Its opening paragraph states that it "
              "summarises the Institute's observations during a May visit \"on behalf of the Complete Streets "
              "Leadership Team, led by the Healthier Weights Council\", and warns that the recommendations rest on a "
              "short visit and should not be considered exhaustive."),
 "why_retained": ("It is City-commissioned advice on citywide street design, and the archive holds nothing from the "
                  "WALC Institute. The inventory-wide search for walkable, livable or WALC returns exactly one record: "
                  "this one. The site already carries a family of complete-streets material on "
                  "content/transportation/roadway-projects/studies.md and "
                  "content/transportation/design-references.md, and this is the review that sat behind the Complete "
                  "Streets Leadership Team's work."),
 "proposed_canonical_page": DESIGN,
 "cross_listings": [
   {"page": STUDIES, "reason": "Its recommendations are corridor and intersection design advice of the kind that page collects, and it names specific Albuquerque locations."},
 ],
 "caution": ("Marked DRAFT on its face and self-limiting: a short-visit review, not an adopted standard. Describe it as "
             "consultant observations and recommendations, never as City policy."),
 "description_word_count": 0,
}]

superseded = [
 {**row("src-4d101bf92cb3992f", "superseded"),
  "title_for_reference": "Uptown Pedestrian Study, MRCOG On-Call Professional Services Task #8, October 27, 2014 — FINAL DRAFT",
  "pages": 66,
  "canonical_id": UPTOWN_FINAL,
  "canonical_url": IDX[UPTOWN_FINAL].get('r2_url'),
  "canonical_state": "validated, R2-archived, and already published at content/transportation/roadway-projects/studies.md line 321",
  "basis": ("The final-draft state of a report whose final state the archive already holds. Both carry the same cover "
            "date of October 27, 2014; the difference is the release marking."),
  "measurement": ("Fetched the R2 object and compared. 66 pages each, token coverage 1.0000 in both directions, "
                  "normalized-text ratio 0.9964. The complete line-level diff is 149 lines, of which 67 are the "
                  "running footer: the archived copy reads FINAL on every page and this one reads FINAL DRAFT. The "
                  "only other difference is a dropped caption line, \"Figure 5. Weekday Peak Hour Pedestrian Counts\", "
                  "plus whitespace. Bytes differ — 6,852,988 here against 6,318,521 archived — because the City's "
                  "published copy is its own downsized file, named "
                  "2014-uptown-ped-study-final-report-oct-28-2014-small.pdf on the transit server."),
  "hash_found_it": False,
  "why_it_was_not_obvious": ("Nothing connects the two records. This copy sits on a councillor's page under "
                             "UptownStudyDRAFTFinalReportOct282014.pdf; the archived one came from "
                             "www.cabq.gov/transit/documents/. Different servers, different filenames, different "
                             "bytes, and the inventory held no checksum for this record."),
  "note_for_integration": ("This file is 534,467 bytes larger than the archived one because it is not downsampled. If "
                           "figure legibility in the published copy is ever a problem, the fuller-resolution file is "
                           "this one — but it is the draft state, so a better fix would be the City's own full-size "
                           "final if one exists. " + UPTOWN_R2DUP + " is the archive-URL alias of the same final report.")},

 {**row("src-2251877ee3dc73ba", "superseded"),
  "title_for_reference": "San Pedro Drive Streetscape Concept between Constitution Avenue and Lomas Boulevard, University of New Mexico Community and Regional Planning Studio, Summer 2011",
  "pages": 58,
  "canonical_id": BIKE_ASSESS,
  "canonical_url": IDX[BIKE_ASSESS].get('r2_url'),
  "canonical_state": "validated, R2-archived, and already published at content/transportation/bicycling/projects/_index.md line 115",
  "basis": ("A student studio's road-diet concept for a segment of San Pedro Drive, overtaken by the City's own "
            "engineering assessment of the same question across a larger segment."),
  "measurement": ("Not a text comparison; the two are different works and share little vocabulary. The grounds are "
                  "authority, scope and date. This document is CRP 420/520, Summer 2011, written by three graduate "
                  "and ten undergraduate students \"on behalf of the Fair Heights Neighborhood Association\", and its "
                  "Chapter 3 Recommended Alternative 1 is a road diet between Lomas Boulevard and Constitution "
                  "Avenue. The City's San Pedro Drive Bike Facility Assessment of 18 July 2014 is a City-commissioned "
                  "engineering study under City Wide On-Call Engineering Services Task 10, CoA Project 5015.00, whose "
                  "project area runs one mile from Marble Avenue to Indian School Road and therefore contains the "
                  "studio's segment, and it evaluates the same road diet with traffic volumes, intersection "
                  "operations, crash history, parking, transit and public feedback. That assessment is already "
                  "archived and published."),
  "hash_found_it": False,
  "checked_for_citation": ("Fetched the archived assessment and searched it: it does not cite the studio work, the "
                           "University of New Mexico planning studio, or the Fair Heights Neighborhood Association. "
                           "Its only UNM reference is a traffic data source. So this is not the City's antecedent "
                           "document, which removes the one argument for keeping it alongside the assessment."),
  "provenance_caveat": ("It is also not a City record. It was produced by a university studio for a private "
                        "neighbourhood association and published on a councillor's page. Even setting supersession "
                        "aside, it would not carry City authority."),
  "footprint_avoided": "45,323,369 bytes, the largest single candidate seen in any cluster this run."},
]

FLYER_REASON = ("A byte-identical copy of " + FLYER_CANON + ", the Transition Albuquerque workshop flyer. Four "
                "records, one file, 425,770 bytes and the same SHA-256 across all four — the Plone filenames say so "
                "plainly: TransitionAlbuqueruqe.pdf, copy_of_, copy2_of_ and copy3_of_. This is the first four-way "
                "exact-hash group found in the Council library this run, and unlike most relationships in these "
                "clusters, plain hashing found it.")

duplicates = []
for i in ("src-4f112d9ff2a63a58", "src-8279121801007f16", "src-b1d8491309abf640"):
    r = row(i, "duplicate")
    r.update({"title_for_reference": "Transition Albuquerque: Training for Transition, April 10-11 2015 (Plone copy)",
              "pages": 1, "canonical_id": FLYER_CANON,
              "canonical_url": IDX[FLYER_CANON].get('direct_file_url'),
              "canonical_state": "recommended excluded in this batch",
              "basis": FLYER_REASON, "hash_found_it": True})
    duplicates.append(r)


def X(i, title, pages, reason, category, date=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages, "exclusion_reason": reason, "category": category})
    if date:
        r["date"] = date
    if extra:
        r.update(extra)
    return r


CONDENSED = ("A public-meeting slide deck condensing a study the archive holds in full. This is the reasoning the "
             "inventory already records on src-03f5d07ef881a5bb, the 17 September 2014 San Pedro presentation, which "
             "is terminal with the note that its \"crash, capacity, bike-lane, and crossing content is substantively "
             "contained in\" the canonical 2014 assessment.")

excluded = [
 X(FLYER_CANON, "Transition Albuquerque: Training for Transition, April 10-11 2015", 1,
   ("A flyer for a paid two-day workshop run by Transition Albuquerque, a private organisation, at the First "
    "Unitarian Church, at $150 per person. Not a City record, not a City event, and not a City decision. Its partner "
    "logos are non-profits and a university programme."),
   "third-party event flyer", "2015-04-10",
   extra={"note": "The canonical of a four-way byte-identical group; the other three are recommended duplicate."}),

 X("src-f166cc39d1779bed", "Uptown Pedestrian Study presentation, November 12, 2014", 34,
   CONDENSED, "public meeting presentation", "2014-11-12",
   extra={"relationship": ("Condenses the Uptown Pedestrian Study. The full report's final state is already archived "
                           "and published; its final draft is recommended superseded in this batch."),
          "tested_not_assumed": ("The deck is image-heavy — 34 pages, 33,403,329 bytes, and only 326 distinct text "
                                 "tokens — so a text comparison alone would prove little. Pages were rendered. Its "
                                 "substantive slides are Parametrix conceptual exhibits stamped CONCEPTUAL DRAFT "
                                 "ONLY, for locations the report covers in Section IV, Potential Improvements for "
                                 "Pedestrian Safety, where the report also carries the supporting counts, crash data "
                                 "and appendices A to C that the deck does not.")}),

 X("src-63d57c5e18152b08", "San Pedro Drive Lane Conversion informational meeting presentation, August 26, 2014", 19,
   CONDENSED, "public meeting presentation", "2014-08-26",
   extra={"relationship": ("The earlier of the two San Pedro meeting decks. The later one, src-03f5d07ef881a5bb of 17 "
                           "September 2014, is already terminal for exactly this reason, so excluding this one "
                           "follows a decision already made rather than making a new one."),
          "content": "Its existing-conditions slides report 160 crashes in three years between Marble and Indian School, 50% rear-end, 18% left-turn, 13% sideswipe — figures the archived assessment carries with their full derivation."}),

 X("src-f8431695e913e837", "Mile-Hi District identity study, Fair Heights Neighborhood Association", 13,
   ("A branding deck proposing a visual identity for the San Pedro corridor: an MHD logo, a signpost mock-up, and "
    "scanned 1960s newspaper clippings used as historical colour. It proposes a name and a look, not a City standard, "
    "a study or a decision."),
   "neighbourhood association branding proposal",
   extra={"tested_not_assumed": "Image-only, 45 bytes of extractable text across 13 pages. Pages were rendered and read."}),

 X("src-89045c7614ba9811", "Mile-Hi District brochure (San Pedro from Lomas to Haines)", 5,
   ("A promotional narrative about the corridor's history as \"a quintessential island of 'Main Street USA'\" since "
    "the 1950s and its revitalisation prospects. Descriptive marketing copy, not a record of City action."),
   "promotional brochure"),

 X("src-dd2c3303527546c5", "San Pedro project letter and flyer", 2,
   ("A two-page project summary handout listing the restriping, the left-turn lane, the bike lanes, the Mile-Hi "
    "identity signage and a project timeline. A summary of work the archived assessment specifies in full."),
   "project summary handout"),

 X("src-db0778071f53f05c", "Letter from Councillor Diane Gibson to neighbours regarding the Mile-Hi District", 2,
   ("A councillor's letter to constituents, opening \"Greeting Neighbors\" and written throughout in the first person. "
    "Councillor communications are excluded throughout this run, in "
    "councilor-district-5-cluster-research-2026-09-11.json, for eight summary sheets in "
    "councilor-district-9-cluster-research-2026-09-12.json, and for the Councilor's Corner newsletter in "
    "councilor-district-4-cluster-research-2026-09-12.json."),
   "councillor communication"),

 X("src-61314122c639ccfc", "Press release: Near Heights commercial corridor rebranded as the \"Mile High District\"", 2,
   ("A City Council press release of 17 November 2014 announcing that Councillor Gibson had named the San Pedro "
    "corridor between Lomas and I-40 the Mile High District. Press releases are excluded on the same ground applied "
    "in councilor-district-4-cluster-research-2026-09-12.json: it announces rather than records."),
   "press release", "2014-11-17"),

 X("src-83ca98bec5b47279", "Comment sheet, San Pedro Drive Lane Conversion Project public meeting, September 17, 2014", 2,
   ("A blank comment form: ruled lines, a name, address and email block, and a return-by date of 26 September 2014. "
    "Blank forms are excluded throughout this run, the split established in "
    "planning-udd-cluster-research-2026-09-11.json between an adopted standard and a submittal form."),
   "blank form", "2014-09-17",
   extra={"tested_not_assumed": "Two bytes of extractable text; rendered and read rather than inferred from the filename."}),

 X("src-7f560a60734c0eb5", "Councilor District 7 documents collection landing page", None,
   "The Plone collection landing page for this directory, not a document.", "collection landing page"),
]

for r in approved:
    r["description_word_count"] = len(r["description"].split())

rows = approved + superseded + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 16, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
avoided = sum(r["size_bytes"] for r in superseded) + sum(r["size_bytes"] for r in duplicates)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "councilor-district-7-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-7-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The District 7 councillor's document collection in the Albuquerque City Council library, covering Councillor Diane Gibson's San Pedro Drive and Uptown work.",
 "scope": "All 16 pending-review candidates. The directory holds 19 records; the other three are already terminal and two of them are what this lane's findings rest on.",
 "brief": "Check every candidate against the published site as well as the inventory, per the dnasdp finding that a published record can be the superseded one.",
 "brief_finding": ("Checking against the published site was the whole lane. Both of the directory's apparently "
                   "substantial studies turned out to be second copies of work ABQInfo already publishes, and neither "
                   "was reachable any other way. The 66-page Uptown Pedestrian Study here is the FINAL DRAFT of a "
                   "report whose FINAL state is already archived at studies.md line 321 — same cover date, same 66 "
                   "pages, full token coverage both ways, and the entire difference is the word DRAFT in a running "
                   "footer. The 58-page, 45 MB San Pedro streetscape concept is a university studio's road-diet "
                   "proposal for a segment inside the project area of the City's own assessment, which is archived at "
                   "the bicycling projects page. One genuine find survived: a WALC Institute walkability memo "
                   "prepared for the City, of which the inventory holds exactly one copy and the archive none."),
 "method": ("Ran the URL group-by first; one collision, already resolved in the inventory. Fetched all 16 candidates "
            "on both URL forms and measured byte length and SHA-256 from the raw form. Compared all checksums against "
            "the 1,612 checksummed inventory records and within the cluster. Fetched two R2 objects read-only and "
            "compared them line by line against candidates. Searched the archived assessment for citations of the "
            "studio work. Rendered every image-only or thin-text file rather than classifying it from its filename."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "nob-hill-highland-cluster-research-2026-09-11.json requires testing a candidate against R2 objects the archive already holds; dnasdp-cluster-research-2026-09-12.json extended it to the published site entry.",
  "candidates_tested": 2,
  "both_failed_the_test": True,
  "uptown": ("src-4d101bf92cb3992f against " + UPTOWN_FINAL + ". Identical 66 pages, coverage 1.0000 both ways, ratio "
             "0.9964; 67 of the 149 diff lines are the FINAL versus FINAL DRAFT footer. Recommended superseded."),
  "san_pedro": ("src-2251877ee3dc73ba against " + BIKE_ASSESS + ". Different authors and different text, but the City "
                "assessment's one-mile project area from Marble Avenue to Indian School Road contains the studio's "
                "Lomas-to-Constitution segment and answers the same road-diet question with engineering data. "
                "Recommended superseded."),
  "what_survived": "src-c8b06367d22b8e24, the WALC Institute memo. No inventory record and no R2 object matches it on any search for walkable, livable or WALC.",
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue by these checks and the flyer hash group, against {approved_bytes:,} bytes added.",
 },
 "url_collision_already_resolved": {
  "group": "https://www.cabq.gov/council/documents/councilor-district-7-documents/SanPedroDriveBikeFacilityAssessment.pdf",
  "records": ["src-842f1c8cdfa8fc1f", BIKE_ASSESS],
  "state": "Already handled: src-842f1c8cdfa8fc1f is duplicate with the reason \"Direct-file URL alias for canonical archive candidate " + BIKE_ASSESS + "\", and the canonical is validated and archived.",
  "why_recorded": ("inventory-url-collision-audit-2026-09-11.json counted 79 groups as actionable_now. This is one "
                   "that has since been actioned, and it is worth recording that the audit's actionable set is being "
                   "drawn down rather than growing."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "internal_byte_collision_group_size": 4,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 1,
  "url_collisions_already_terminal": 1,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 3,
  "relationships_found_by_comparison_against_r2": 2,
  "note": ("Six relationships, and for once hashing found half of them — four identical copies of one flyer, which "
           "Plone's own copy_of_ filenames also announced. The two that mattered were invisible to hashing, to "
           "filenames and to titles, and were only reachable by fetching what the archive already publishes."),
 },
 "integration_flags": [
  {"severity": "avoid-duplicate-archival",
   "affects": ["src-4d101bf92cb3992f", "src-2251877ee3dc73ba"],
   "finding": "Both of this directory's major studies are already covered by published archive objects: one is the draft state of a published final report, the other is superseded by the City's own assessment of the same corridor question.",
   "recommended_action": f"Record both as superseded. Together they are {sum(r['size_bytes'] for r in superseded):,} bytes that do not need uploading."},
  {"severity": "substantive-find",
   "affects": ["src-c8b06367d22b8e24"],
   "finding": "A Walkable and Livable Communities Institute memo prepared for the City in June 2014 for the Complete Streets Leadership Team. The inventory holds one copy and the archive holds none.",
   "recommended_action": "Approve and place on the transportation design references page, cross-listed to corridor studies. It is marked DRAFT and self-limiting; label it as consultant observations."},
  {"severity": "figure-resolution",
   "affects": ["src-4d101bf92cb3992f"],
   "finding": "The published Uptown study is the City's own downsized file; the councillor-page copy is 534,467 bytes larger and not downsampled, but is the draft state.",
   "recommended_action": "No action unless figure legibility in the published copy proves inadequate. If it does, look for the City's full-size final rather than substituting this draft."},
  {"severity": "hash-group",
   "affects": ["src-4f112d9ff2a63a58", "src-8279121801007f16", "src-b1d8491309abf640", FLYER_CANON],
   "finding": "Four inventory records, one 425,770-byte file, distinguished only by Plone copy_of_ prefixes. The file itself is a third-party paid-workshop flyer.",
   "recommended_action": "Resolve three as duplicate of the canonical and exclude the canonical. Nothing is archived either way."},
  {"severity": "audit-followthrough",
   "affects": ["src-842f1c8cdfa8fc1f"],
   "finding": "The one URL collision in this directory is already terminal, resolved against the validated archived assessment.",
   "recommended_action": "None. Recorded as evidence that the URL-collision audit's actionable set is being worked down."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 16, "http_200": 16, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "archive_fetches": "Two R2 objects at files.abqinfo.com were fetched read-only for comparison, both HTTP 200; the bike assessment's bytes and SHA-256 match its inventory record exactly.",
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "15 genuine PDFs and one HTML collection page by leading bytes."},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": (f"The single approved record is a static PDF and is inventory-only until an R2 archive object "
                   f"exists for it and its public download, exact size, SHA-256, and authoritative-source provenance "
                   f"are verified. Archive footprint if authorized: {approved_bytes:,} bytes. It is born-digital with "
                   f"a full text layer, so full-text search reaches it without optical character recognition."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Every duplicate and superseded row carries a "
                      "canonical_id: the two superseded rows point at validated, R2-archived, already-published "
                      "records outside this cluster, and the three duplicate rows point at a canonical inside it that "
                      "is itself recommended excluded. The one approved row carries a title, a 20-to-50-word "
                      "description, a date, a proposed_canonical_page, a cross-listing and a caution. No row is "
                      "requires human review; this directory contains no legislation. Sizes and checksums are first "
                      "measurements; the inventory held none for any pending record here."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the two R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
