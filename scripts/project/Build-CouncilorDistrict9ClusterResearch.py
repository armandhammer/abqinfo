"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. The sixteen cluster artifacts and the inventory audit that
precede it are dated 2026-09-11; cross-references name them by filename rather
than by "the artifact of the same date".
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-9-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d9\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/councilor-district-9-documents/'

PARKS = 'content/public-works/parks-recreation.md'
AREA = 'content/development-land-use/area-sector-plans.md'
SURVEYS = 'content/city-data/city-progress-surveys.md'

ARCHIVED_RMP = 'src-9696b9222ba27231'      # validated + R2 + published Tijeras Arroyo RMP
ADOPTED_FY2011 = 'src-03b66a5d8f836d44'    # validated + R2 + published FY2011 approved budget
PRECEDENT = 'src-0a2535af77a1ecdc'         # already-excluded Harris/Sanchez floor substitute

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC = {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    r.update(M[i])
    return r


def A(i, title, desc, date, pages, evidence, page, why=None, cross=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": date, "pages": pages,
              "proposed_canonical_page": page, "cross_listings": cross or [],
              "evidence": evidence})
    if why:
        r["why_retained"] = why
    if extra:
        r.update(extra)
    return r


approved = [
 A("src-ed3a4d379473def8",
   "Environmental Planning Commission Record Recommending Adoption of a Rank II Facility Plan for the Tijeras Arroyo Bio-Zone Preserve (Project 1009983, 14EPC-40013)",
   "The Environmental Planning Commission forwards its recommendation of approval to the City Council for adopting a Rank II facility plan over roughly 684 acres of the Tijeras Arroyo Bio-Zone Preserve, with the full staff record behind it.",
   "2014-06-06", 88,
   ("Image-only PDF with almost no text layer; page 1 was rendered and read. It is an interoffice memorandum from Mayor "
    "Richard J. Berry to Council President Ken Sanchez dated June 6 2014, forwarding an EPC recommendation of APPROVAL "
    "for a preserve running about 3.7 miles from the Carnuel Interstate 40 interchange west to the Kirtland Air Force "
    "Base boundary. Staff planner Lorena Patten-Quintana. The background recites the 1986 Facility Plan for Arroyos, "
    "the 1999 Major Public Open Space Facility Plan policy A.2.c calling for this very plan, Resolution R-07-278 of "
    "2007 mandating a Bio-Zone Preserve, and the 2010 East Gateway Sector Development Plan."),
   PARKS,
   why=("The adoption record for a plan the archive already holds. content/public-works/parks-recreation.md publishes "
        "the Tijeras Arroyo Biological Zone Open Space Resource Management Plan under a Tijeras Arroyo Bio-Zone "
        "heading, but nothing showing how it was adopted or on what analysis. This is that, and it is the only copy in "
        "the inventory."),
   cross=[{"page": AREA, "reason": "Its background turns on the East Gateway Sector Development Plan and the Major Public Open Space Facility Plan, both area-plan records."}],
   extra={"relationship": f"Companion to the archived plan {ARCHIVED_RMP}, not a copy of it. See already_archived_check."}),

 A("src-7bf7341bebf83fe6",
   "Enacted Resolution R-2014-012: Amending Resolution R-13-189 on Albuquerque Adoption Appreciation Day and Extending Biopark and Explora Passes to Adoptive and Foster Families (Council Bill R-14-31)",
   "The enacted City resolution widens an earlier one so that annual Zoo, Biopark and Explora passes go to families of all children adopted or placed in foster care in Bernalillo County, removing the sixty-day claim window and the CYFD-only limit.",
   "2014", 2,
   ("Image-only PDF with no text layer; page 1 was rendered and read. Council Bill No. R-14-31 with the handwritten "
    "Enactment No. R-2014-012, Twenty-First Council, sponsored by Don Harris and Ken Sanchez. It amends Section 3 of "
    "Resolution R-13-189, Enactment No. R-2013-054, approved June 17 2013."),
   SURVEYS,
   why=("Enacted law, which is rare in this tree: most Council files posted here are bills as considered with the "
        "enactment block left blank, including the two held at requires human review in this same directory. Unusually "
        "for this tree the filename told the truth: R31Enacted.pdf. It is also the only record in this directory that "
        "changes what a resident is entitled to."),
   extra={"note": "It amends a resolution the archive does not hold, R-13-189 / R-2013-054. That predecessor is a discovery lead."}),

 A("src-5cdf0511f8cc1c98",
   "Four Hills Village Park Design Plan, July 25, 2013",
   "The City park design plan for Four Hills Village Park keys the proposed layout, marking play areas, a half basketball court, walking paths, a bridge, exercise stations, shade structures, fencing, and pedestrian and vehicular entries.",
   "2013-07-25", 2,
   ("Image-only PDF with no text layer; rendered and read. The sheet is titled FOUR HILLS VILLAGE PARK and dated "
    "\"Design 07.25.13\", with about twenty keyed callouts and a noted golf course well site excluded from the park."),
   PARKS,
   why=("A dated design record for a named City park, which is the class of record the parks page already carries under "
        "Current Parks and Open Space Projects. It is the only Four Hills Village Park record in the inventory."),
   extra={"caution": "It is a design plan, not an as-built. Do not describe it as constructed."}),

 A("src-1d8383220acdfcbd",
   "Mile High Little League Schematic Master Plan, June 2014",
   "The City Parks and Recreation schematic master plan for the Mile High Little League site off Juan Tabo Boulevard keys sixteen proposed works, including reoriented fields, relocated batting cages, shade structures over bleachers, parking, and a drainage swale.",
   "2014-06", 1,
   ("Image-only PDF whose only extractable text is two stray characters; rendered and read. The title block reads CITY "
    "OF ALBUQUERQUE, STRATEGIC PLANNING AND DESIGN, PARKS AND RECREATION DEPARTMENT, MILE HIGH LITTLE LEAGUE, "
    "SCHEMATIC MASTER PLAN - JUNE, 2014, prepared by Morrow Reardon Wilkinson Miller, Ltd., Landscape Architects, at "
    "1 inch to 30 feet."),
   PARKS,
   why=("A keyed master plan for a named City recreation site. The same landscape architecture firm prepared the "
        "Highland Park renovation drawing recommended in councilor-district-2-cluster-research-2026-09-11.json, so the "
        "two are part of one Parks and Recreation design programme."),
   extra={"caution": ("Schematic, and unsigned: the City Project No. block reads XXXXXX and the Zone Map block X-XX, so "
                      "no project number can be cited and the design review and city engineer approval blocks are "
                      "empty. Describe it as a schematic master plan and nothing firmer.")}),
]

duplicates = [
 {**row("src-2ea5c8b1ed06eea9", "duplicate"),
  "title_for_reference": "Tijeras Arroyo Biological Zone Open Space Resource Management Plan, February 2014 (Council copy)",
  "pages": 128,
  "canonical_id": ARCHIVED_RMP,
  "canonical_url": IDX[ARCHIVED_RMP].get('r2_url'),
  "canonical_state": "validated, R2-archived, and already published on content/public-works/parks-recreation.md",
  "basis": ("The same 128-page plan the archive already holds. The City publishes it twice: the archived copy came from "
            "www.cabq.gov/parksandrecreation/documents/, this one from the District 9 councilor's page. Normalized text "
            "is identical at ratio 1.0000 with full token coverage in both directions and the same 128 pages; the files "
            "differ by 21,463 bytes of encoding, 5,988,865 here against 5,967,402 archived."),
  "hash_found_it": False,
  "note": ("This was the apparent headline find of the directory and it is not a find. It was caught by checking the "
           "R2 object before recommending, which is the rule "
           "nob-hill-highland-cluster-research-2026-09-11.json records. Recognising it keeps a 6 MB duplicate out of "
           "the upload queue."),
  "cross_directory": True},
]


def S(i, title, canon, pages, basis, measurement, extra=None):
    r = row(i, "superseded")
    r.update({"title_for_reference": title, "pages": pages,
              "canonical_id": canon,
              "canonical_url": IDX[canon].get('r2_url') or IDX[canon].get('direct_file_url') or IDX[canon].get('source_url'),
              "canonical_state": IDX[canon]['status'],
              "basis": basis, "measurement": measurement, "hash_found_it": False})
    if extra:
        r.update(extra)
    return r


superseded = [
 S("src-f1cf917bfeaf11c7",
   "Council Bill R-14-82: Resolution for approximately 684 acres including the Tijeras Arroyo Bio-Zone (earlier version)",
   "src-80dbed6afbf096c3", 6,
   "An earlier layout of the same resolution, superseded by the version the City itself names final.",
   ("Normalized-text similarity 0.9907 with token coverage 1.0000 of this file inside the final. The only substantive "
    "difference found by diff is pagination and a source-file footer: the successor's last page carries the path "
    "x:\\city council\\share\\cl-staff\\_legislative staff\\legislation\\21 council\\r-82final.doc, which is what "
    "establishes which of the two is final rather than the filename alone.")),

 S("src-bbda1951b4676549",
   "Council Bill R-14-113: Resolution recognizing the significance of the historic Rancho de Carnue site adjacent to the Singing Arrow Community Center (earlier version)",
   "src-e90039aa580fda19", 2,
   "An earlier layout of the same resolution, superseded by the version the City names final.",
   "Normalized-text similarity 0.9828 with token coverage 1.0000 of this file inside the final."),

 S("src-a5d1865eee112514",
   "R-10-58 Floor Substitute: Proposed FY2011 Operating Budget, Harris and Sanchez, redline copy",
   ADOPTED_FY2011, 21,
   ("A proposed floor substitute for the Fiscal Year 2011 operating budget, superseded by the budget actually adopted. "
    "The adopted budget is already validated, R2-archived and published on content/city-data/budget-spending.md as "
    "\"City of Albuquerque Approved Budget, Fiscal Year 2011\"."),
   ("Not a text measurement but a status one: this directory's own terminal record src-0a2535af77a1ecdc, the clean copy "
    "of this same floor substitute, is excluded with the reason \"Superseded proposed floor substitute for the FY2011 "
    "budget; the adopted FY2011 operating budget is already preserved and linked on ABQInfo.\""),
   extra={"pair": "src-20c88c17ca7fa831 is its supporting exhibit and takes the same disposition."}),

 S("src-20c88c17ca7fa831",
   "Additional information supporting the Harris and Sanchez R-10-58 floor substitute",
   ADOPTED_FY2011, 5,
   "The supporting exhibit to the floor substitute above, superseded with it by the adopted FY2011 budget.",
   "Same ground as its parent. An exhibit to a superseded proposal has no independent standing.",
   extra={"parent": "src-a5d1865eee112514"}),
]


def R(i, draft_title, pages, question, why, evidence):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why, "evidence": evidence})
    return r


rhr = [
 R("src-80dbed6afbf096c3",
   "Council Bill R-14-82: Resolution for Approximately 684 Acres Including the Tijeras Arroyo Bio-Zone (final version)",
   6,
   "Locate the enacted resolution for R-14-82. Unlike most such cases in this run, the adoption is independently evidenced and only the enactment number is missing.",
   ("Enactment number blank, under the two standing checkpoint blockers. What makes this one tractable is that the "
    "outcome is already visible in the archive: the Environmental Planning Commission record recommending approval is "
    "recommended for addition in this same batch, and the Resource Management Plan the resolution adopts is already "
    "validated, R2-archived and published. The plan exists on the site as adopted policy; the instrument that adopted "
    "it is what is missing."),
   "6 pages, Twenty-First Council, sponsored by Don Harris, enactment number blank. It covers approximately 684 acres, the same acreage the EPC record names."),

 R("src-e90039aa580fda19",
   "Council Bill R-14-113: Resolution Recognizing the Significance of the Historic Rancho de Carnue Site Adjacent to the Singing Arrow Community Center (final version)",
   2,
   "Locate the enacted resolution for R-14-113; decide with R-14-82 above.",
   ("Enactment number blank, same standing blockers. Both resolutions are Don Harris District 9 measures from the "
    "Twenty-First Council and both concern designating or recognising land in that district, so they should be "
    "resolved together. Note that R-14-31 in this same directory does carry its enactment number, which shows the "
    "Council page sometimes posts the enacted version and sometimes does not."),
   "2 pages, Twenty-First Council, sponsored by Don Harris, enactment number blank."),
]

SUMMARIES = [
 ("src-534350482454b96b", "East Gateway Summary", 3),
 ("src-20dfa986309e3216", "Four Hills Park Summary", 1),
 ("src-c74b39a83a00a244", "Jeanne Bellamah Community Center Summary", 1),
 ("src-6d830b446092995c", "Manzano Mesa Multigenerational Center Summary", 1),
 ("src-f6eeb70f0d02621d", "Mile High Little League Summary", 1),
 ("src-160b35307aab600b", "Rancho de Carnue Archeological Site Summary", 1),
 ("src-1e915db242db66a5", "Singing Arrow Community Center Summary", 1),
 ("src-b5a0cbe9aec8027c", "Tijeras Arroyo Biozone Summary", 3),
]

SUMMARY_REASON = (
 "A District 9 councillor's project summary sheet. These are narrative pieces written in the councillor's voice about "
 "what he is doing for the district, not City records of a decision, a study or a standard. The sample text is "
 "characteristic: \"Councilor Harris is working to change that... Elected in 2005, Councilor Harris has...\". The "
 "substantive records behind several of them are held separately, and four are recommended for addition in this same "
 "batch. The inventory already carries terminal exclusions for councillor communications of this kind, and "
 "councilor-district-5-cluster-research-2026-09-11.json excluded five more.")

excluded = []
for i, title, pages in SUMMARIES:
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages,
              "exclusion_reason": SUMMARY_REASON,
              "category": "councillor project summary"})
    excluded.append(r)

excluded.append({
 **row("src-e00b831cfe974916", "excluded"),
 "title_for_reference": "Councilor District 9 documents collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
})

rows = approved + duplicates + superseded + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "councilor-district-9-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-9-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": ("This artifact is dated 2026-09-12. The sixteen cluster artifacts and the inventory URL-collision audit "
               "that precede it are dated 2026-09-11 and were produced in one continuous run; cross-references here "
               "name them by filename rather than by \"the artifact of the same date\", which those artifacts use "
               "among themselves and which remains correct there."),
 "cluster": "The District 9 councillor's document collection in the Albuquerque City Council library, covering the terms of Councillor Don Harris.",
 "scope": "All 20 pending-review candidates in that directory. The directory holds 21 records; the twenty-first is already excluded and it is what corrects an earlier artifact of this run.",
 "brief": "Separate substantive district records from constituent notices, running the URL group-by first and rendering image-only records.",
 "brief_finding": "Four records carry substance and eight are the councillor's own project write-ups. The two things worth reporting beyond that are both about checking rather than classifying: the directory's apparent headline find, a 128-page open space resource management plan, is already validated and archived and was caught before being recommended; and this directory's one terminal record shows that a decision recorded in councilor-district-5-cluster-research-2026-09-11.json was wrong.",
 "method": "Ran the URL group-by across the directory first, per inventory-url-collision-audit-2026-09-11.json; no collisions. Fetched all 20 candidates and recorded exact byte length and SHA-256 for each. Read the already-excluded record's recorded reasoning before classifying anything. Rendered the five files with no usable text layer, which is how both enacted and both plan records were identified. Fetched two R2 objects read-only to test candidates against what the archive already holds. Compared all checksums against the 1,612 checksummed inventory records.",
 "classification_only": True,
 "shared_state_written": [],
 "corrects_an_earlier_artifact": {
  "artifact": "project-state/discovery/councilor-district-5-cluster-research-2026-09-11.json",
  "what_it_said": ("It held three records at requires human review under the standing enactment blockers: "
                   "src-338b0d72594a0aad and src-a9d18b1ea8963cad, the clean and redline copies of Councillor Lewis's "
                   "floor substitute to R-10-58 for the Fiscal Year 2011 operating budget, and src-a4e93912f58bcb5d, "
                   "its graduated wage cut scale exhibit. The stated question was to locate the enacted instrument."),
  "why_that_was_wrong": ("The question was answerable from the inventory and this lane did not check. The adopted "
                         f"outcome is already held: {ADOPTED_FY2011}, \"City of Albuquerque Approved Budget, Fiscal "
                         "Year 2011\", is validated, R2-archived and published on content/city-data/budget-spending.md. "
                         "A proposed floor substitute for a budget that was adopted and is held is superseded, not "
                         "awaiting an enactment number."),
  "how_this_directory_shows_it": ("District 9 holds the competing floor substitute to the same bill, by Councillors "
                                  f"Harris and Sanchez, and it is already terminal: {PRECEDENT} is excluded with the "
                                  "reason \"Superseded proposed floor substitute for the FY2011 budget; the adopted "
                                  "FY2011 operating budget is already preserved and linked on ABQInfo.\" Two "
                                  "councillors offered rival substitutes for one budget; one set was resolved "
                                  "correctly by an earlier pass and the other was left open by this run."),
  "recommended_revision": (f"Resolve all three District 5 records to superseded with canonical {ADOPTED_FY2011}, "
                           "matching the treatment this artifact gives the District 9 redline and exhibit. That closes "
                           "three of the five requires-human-review rows that artifact raised."),
  "claude_did_not_modify": "Those records remain as that artifact left them. This is a recommendation to the integration lane.",
  "lesson": ("Before writing an enactment-blocker row, search the inventory for the adopted outcome, not just for the "
             "enactment number. A budget, a plan or a map that was adopted may already be archived under a completely "
             "different title on a completely different page."),
 },
 "already_archived_check": {
  "rule_applied": "nob-hill-highland-cluster-research-2026-09-11.json established that a candidate must be tested against R2 objects the archive already holds before it is recommended, because an inventory title can understate what an archived object contains.",
  "candidate": "src-2ea5c8b1ed06eea9, the Tijeras Arroyo Biological Zone Open Space Resource Management Plan, February 2014, 128 pages, 5,988,865 bytes.",
  "test": f"Fetched the R2 object for {ARCHIVED_RMP} read-only and compared normalized text and page counts.",
  "result": "Identical: ratio 1.0000, full token coverage both ways, 128 pages each. Different bytes only, 21,463 fewer in the archived copy.",
  "why_it_was_not_obvious": ("The archived record was captured from www.cabq.gov/parksandrecreation/documents/ and this "
                             "copy sits on a councillor's page under a filename beginning R82, so neither the "
                             "directory nor the filename connects them. Hashing does not connect them either."),
  "outcome": "Recommended duplicate rather than approved, keeping a 6 MB re-upload out of the queue.",
  "what_survived_the_check": ("The EPC record src-ed3a4d379473def8 is a different document and is recommended for "
                              "addition: the archive holds the plan but not the record of how it was adopted."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text": 3,
  "relationships_found_by_recorded_status": 2,
  "note": ("Five relationships and hashing finds none. Three are text comparisons: two final-versus-earlier resolution "
           "pairs within the directory and one cross-directory match against an R2 object. The other two were "
           "established from a terminal record's recorded reasoning rather than from any measurement, which is a "
           "reminder that the inventory's own prose carries findings no comparison will reproduce."),
 },
 "integration_flags": [
  {"severity": "corrects-earlier-artifact",
   "affects": ["src-338b0d72594a0aad", "src-a9d18b1ea8963cad", "src-a4e93912f58bcb5d"],
   "finding": "Three District 5 records held at requires human review under an enactment blocker are in fact superseded by an adopted budget the archive already holds and publishes.",
   "recommended_action": f"Resolve all three to superseded with canonical {ADOPTED_FY2011}. Claude did not modify them."},
  {"severity": "avoid-duplicate-archival",
   "affects": ["src-2ea5c8b1ed06eea9"],
   "finding": "A 128-page, 5,988,865-byte plan in this directory is text-identical to an R2 object already published on the parks page.",
   "recommended_action": "Record as duplicate and do not upload. Second cluster in this run where the saving is against an object already in R2."},
  {"severity": "tractable-enactment",
   "affects": ["src-80dbed6afbf096c3", "src-e90039aa580fda19"],
   "finding": "Two Don Harris resolutions with blank enactment numbers. For R-14-82 the adoption is independently evidenced: the EPC approval record is in this batch and the plan it adopts is already published as City policy.",
   "recommended_action": "Resolve the two together. R-14-82 is the more tractable and the more consequential. Note that R-14-31 in this same directory does carry its enactment number, so the Council page posts enacted versions inconsistently rather than never."},
  {"severity": "discovery-lead",
   "affects": ["src-7bf7341bebf83fe6"],
   "finding": "The enacted R-2014-012 amends Resolution R-13-189, Enactment R-2013-054, of June 17 2013, which the archive does not hold.",
   "recommended_action": "Add the predecessor to the discovery queue. An amending resolution is hard to read without the one it amends."},
  {"severity": "editorial",
   "affects": [s[0] for s in SUMMARIES],
   "finding": "Eight councillor project summaries are recommended excluded, but several describe projects whose substantive records are held or recommended: the Tijeras Arroyo plan, Four Hills Village Park, Mile High Little League and Rancho de Carnue.",
   "recommended_action": "The summaries are not the record, but they are a usable index of which District 9 projects have records worth finding. Nothing needs archiving for that."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "superseded": counts["superseded"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "archive_fetches": "Two R2 objects at files.abqinfo.com were fetched read-only for comparison, both HTTP 200.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "19 genuine PDFs and one HTML collection page by leading bytes. Five PDFs have no usable text layer and were rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "superseded": superseded,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": f"All 4 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, dominated by the 5,787,947-byte EPC record. All four are scans with no usable text layer, so full-text search will not reach them without optical character recognition; that is a property of the City's originals.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every duplicate and superseded row carries a canonical_id; two of those canonicals are validated and R2-archived records outside this cluster, and two are final versions held at requires human review inside it. The 4 approved rows each carry a title, a 20-to-50-word description, a date, a proposed_canonical_page, and a caution where the document's own blocks are unsigned or its project number blank. Two rows are requires human review under the standing enactment blockers. Separately, corrects_an_earlier_artifact proposes resolving three records in another artifact of this run that are outside this lane's classification scope. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the two R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
