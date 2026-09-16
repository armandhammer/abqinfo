"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\east-central-sector-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\ec\fetch.log')

MRA_PLAN = 'src-42700a168ad3eb38'      # validated + R2 + published, redevelopment-plans.md line 99
BIOZONE_RMP = 'src-9696b9222ba27231'   # validated + R2 + published, parks-recreation.md line 139
EPC_RECORD = 'src-ed3a4d379473def8'    # district-9, recommended for addition

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

BLOCKER = ("Enactment number blank, under the two standing checkpoint blockers: isolated legislative material must "
           "have its authoritative enacted package resolved before archival or visible use. Claude is research-only "
           "and cannot decide that.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


def R(i, priority, draft_title, pages, evidence, question, why, extra=None):
    r = row(i, "requires human review")
    r.update({"priority": priority, "draft_title": draft_title, "pages": pages,
              "evidence": evidence, "question_for_human": question, "why_not_decided_here": why})
    if extra:
        r.update(extra)
    return r


rhr = [
 R("src-1a09b0a2a4e8fcbd", 1,
   "Council Bill C/S R-07-278: Resolution Requiring the City to Develop a Master Plan for a Bio-Zone Preserve Within and Adjacent to the Tijeras Arroyo Between the Juan Tabo Boulevard Right-of-Way and the Eastern City Limit",
   3,
   ("Born-digital PDF with a full text layer. CITY of ALBUQUERQUE, SEVENTEENTH COUNCIL, COUNCIL BILL NO. C/S R07278, "
    "ENACTMENT NO. blank, sponsored by Don Harris. Section 1 formally invites a joint effort; Section 2 addresses the "
    "City and Bernalillo County; Section 3 provides for the City acting alone in the absence of a joint City/County "
    "planning effort. It extends a moratorium \"until October 1st, 2008\"."),
   "Locate the enacted resolution for R-07-278. This is the most tractable enactment question found anywhere in this run.",
   (BLOCKER + " What makes it tractable is that two independent records in the archive already treat it as enacted "
    "law. " + EPC_RECORD + ", the Environmental Planning Commission record recommended for addition in "
    "councilor-district-9-cluster-research-2026-09-12.json, cites \"Resolution R-07-278 of 2007\" in its background as "
    "the instrument mandating a Bio-Zone Preserve. And the master plan this resolution requires exists, is finished, "
    "and is published: " + BIOZONE_RMP + ", the Tijeras Arroyo Biological Zone Open Space Resource Management Plan of "
    "February 2014, is validated, R2-archived and live at content/public-works/parks-recreation.md line 139. The "
    "mandate was carried out. Only the enactment number is missing."),
   extra={"relationship": "This is the authority behind a plan the site already publishes, and nothing on that page currently says where the plan came from.",
          "cross_cluster": "Found because the district-9 EPC record was read closely enough to capture its citations. That reading is what made this row answerable."}),

 R("src-b8dad566165e2a17", 2,
   "Council Bill R-07-275: Resolution Designating the East Gateway Metropolitan Redevelopment Area, Making Findings and Determinations Pursuant to the Metropolitan Redevelopment Code, and Directing the Metropolitan Redevelopment Agency to Prepare a Plan",
   7,
   ("Born-digital PDF with a full text layer, the longest bill in the directory. COUNCIL BILL NO. R07275, ENACTMENT "
    "NO. blank, Don Harris, Seventeenth Council. Sections 1 and 2 find the area appropriate for a metropolitan "
    "redevelopment project under Section 3-60A-8 NMSA 1978 and describe the boundary from a centerline point; Section "
    "3 lists an area under review for inclusion; Section 4 lists lands excluded; Sections 5 and 6 make the blight and "
    "rehabilitation findings; Section 7 authorises the Metropolitan Redevelopment Agency."),
   "Locate the enacted floor substitute F/S R-07-275. Note that the archive is missing the enactment number twice over, not once.",
   (BLOCKER + " The outcome is held and published: " + MRA_PLAN + ", the East Gateway Metropolitan Redevelopment Area "
    "Plan of 2014, is validated, R2-archived and live at content/development-land-use/redevelopment-plans.md line 99. "
    "That plan is the document this resolution directed the Agency to prepare."),
   extra={"the_archive_is_missing_it_twice": ("Fetched the archived plan and read it. Its page 2 reproduces the "
                                              "designating resolution as \"COUNCIL BILL NO. F/S R-07-275 ENACTMENT NO. "
                                              "________________________\" — also blank. So the published, validated "
                                              "record carries an unenacted bill text in its own appendix. Resolving "
                                              "this question improves a page that is already live."),
          "this_text_is_not_redundant": ("The candidate is the original bill; the archived plan carries the floor "
                                         "substitute. Token coverage of the candidate inside the archived plan is "
                                         "0.6976, and the tokens that appear only in the candidate are street numbers "
                                         "— 10415, 10501, 12817, 12821, 12825 and dozens more. The standalone "
                                         "resolution carries the parcel-level boundary description in Sections 2, 3 "
                                         "and 4 that the published plan does not reproduce in text. Do not treat it as "
                                         "a duplicate of the archived plan.")}),

 R("src-208b33695082ab06", 3,
   "Exhibit A to F/S R-06-172: Amended Interim Development Management Area Design Regulations, East Gateway",
   4,
   ("Born-digital PDF with a full text layer. Headed \"Exhibit A: FS/R06172 Amended Interim Development Management "
    "Area Design Regulations\". Part A on applicability states the regulations are in addition to existing City "
    "Ordinance and Development Process Manual requirements and that the Planning Director rules on conflicts. Part B1 "
    "sets densities, intensities and height within one block of the arterials — Central Avenue from Moon Street to "
    "Tramway Road, and Eubank, Juan Tabo and Tramway Boulevards."),
   "Decide with the package below. This is the only file in the directory that is regulatory text rather than an instrument or a map.",
   (BLOCKER + " It is an exhibit and its parent's enactment status is exactly what is unresolved. It is also expired "
    "on its face: see interim_regime_expired.")),

 R("src-19270229907c2c5b", 4,
   "Council Bill R-07-276: Resolution Establishing the East Gateway Interim Design Regulations Area, Setting a Moratorium for Specified Uses in the C-2 and C-3 Zones, and Setting a Time Period for the Applicability of Interim Design Regulations",
   2,
   ("Born-digital PDF with a full text layer. COUNCIL BILL NO. R07276, ENACTMENT NO. blank, Don Harris. Section 1 "
    "carries forward the Interim Design Regulations adopted in R-06-172; Section 2 runs from the effective date "
    "\"until October 31, 2008 or until the final consideration by the City\" Council of the sector plan; Section 3 "
    "declares an emergency."),
   "Decide with the package.",
   BLOCKER + " Expired on its face: see interim_regime_expired."),

 R("src-c9c828803603e6d3", 5,
   "Council Bill F/S(2) R-06-18: Resolution Requiring a Metropolitan Redevelopment Plan / Sector Development Plan for an Interim Development Management Area, Defining That Area and Declaring an Interim Period",
   3,
   ("Born-digital PDF with a full text layer. COUNCIL BILL NO. F/S(2) R0618, ENACTMENT NO. blank, Don Harris. Section "
    "1 requires the City to develop a Metropolitan Redevelopment Area Plan; Section 2 directs the administration upon "
    "enactment; Section 3 establishes the Interim Development Management Area and runs \"until June 1st, 2006, for any "
    "property that is\" within it. This is the origin instrument of the whole package: the two later resolutions name "
    "and amend the area it creates."),
   "Decide with the package. Resolve this one first within the package, since the others define themselves by reference to it.",
   BLOCKER + " Expired on its face: see interim_regime_expired.",
   extra={"exhibit": "src-1a52f943f87c3eb4"}),

 R("src-51ac987d9e9d59d5", 6,
   "Council Bill C/S R-06-172: Resolution Naming the Sector Planning Area Established in F/S(2) R-06-18 and the Interim Development Management Area Established in F/S(2) R-06-67 the \"East Gateway Sector Planning and Interim Development Management Area\"",
   3,
   ("Born-digital PDF with a full text layer. COUNCIL BILL NO. CSR06172, ENACTMENT NO. blank, sponsored by Harris. "
    "Section 3 carries forward the provisions adopted in sections one through three of F/S(2) R-06-18. It is the "
    "naming instrument and the parent of the design regulations exhibit above."),
   "Decide with the package.",
   BLOCKER + " Expired on its face: see interim_regime_expired.",
   extra={"exhibit": "src-cd4af1b973f2c583",
          "names_an_instrument_not_in_this_directory": "It also names an area established in F/S(2) R-06-67, which is held nowhere in the inventory. That is a discovery lead."}),

 R("src-cd4af1b973f2c583", 7,
   "Attachment 1 to F/S R-06-172: East Gateway Sector Plan and Interim Development Management Area boundary map, June 15, 2007",
   1,
   ("Image-only PDF with one byte of extractable text; rendered and read. Titled \"Attachment 1: F/S R-06-172 East "
    "Gateway Sector Plan and Interim Development Management Area\". A parcel-level AGIS map with two shaded classes in "
    "the legend — East Gateway Sector Plan and IDMA, and Near Heights Metropolitan Redevelopment Area — at 0.25 mile "
    "scale, footed \"Map prepared June 15, 2007. Data provided by City of Albuquerque AGIS and City of Albuquerque "
    "Council Services\" and \"See legislation for properties excluded from Design Regulations\"."),
   "Decide with its parent, C/S R-06-172.",
   (BLOCKER + " A boundary map is more self-contained than the bill it belongs to, and this one is the clearest single "
    "picture of the regulated area anywhere in the cluster. But its own legend defers to the legislation for excluded "
    "properties, so it cannot stand alone, and its parent's status is unresolved."),
   extra={"if_the_package_resolves": "This is the file most worth publishing from this directory. It shows the East Gateway area against the Near Heights MRA, which the site already covers on the redevelopment plans page."}),

 R("src-1a52f943f87c3eb4", 8,
   "Exhibit A to F/S R-06-18: Interim Development Management Area map",
   1,
   ("Single-sheet PDF, 17,569,920 bytes, the largest file in the directory. It carries a text layer consisting almost "
    "entirely of street labels — I-40 ramps, Tomasita, Marcella, Grace, Shirley, Nambe, Copper, Claudine, Monarch, La "
    "Cueva, Chelwood Park, Eubank, Central, Tramway and several hundred more — headed \"Exhibit A: FS-R-06-18\"."),
   "Decide with its parent, F/S(2) R-06-18.",
   (BLOCKER + " It is an exhibit to an instrument whose enactment status is unresolved."),
   extra={"caution": "At 17.5 MB for a single sheet it is by far the heaviest archival cost in the cluster, and its content overlaps the June 2007 Attachment 1 map above, which is 5.8 MB and better labelled. If only one map is ever archived, prefer src-cd4af1b973f2c583."}),
]

excluded = [{
 **row("src-7615be91eb93e1e0", "excluded"),
 "title_for_reference": "East Central Sector collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
}]

rows = rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 9, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "east-central-sector-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/east-central-sector cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The East Gateway sector planning legislation in the Albuquerque City Council library, filed under the directory name east-central-sector.",
 "scope": "All 9 pending-review candidates, which is every record in the directory. Nothing here is terminal.",
 "brief": "Run the standard opening sequence and reconcile any multi-file sector-plan package by printed page ranges, per the PGS and DNASDP method.",
 "brief_finding": ("There is no multi-file plan package here to reconcile. The directory is not a plan library at all: "
                   "it is a single legislative package of six Seventeenth Council resolutions sponsored by Don Harris "
                   "plus two exhibit maps, every one of them carrying a blank ENACTMENT NO. block. Under the two "
                   "standing checkpoint blockers nothing in it can be approved by a research lane, so every "
                   "substantive file is recommended for human review. The lane's value is in what it can tell a human "
                   "before they start: two of the eight are answerable almost immediately, the other six describe an "
                   "interim regime that expired by its own terms between 2006 and 2008, and the successor document "
                   "that closed it is named in the archive but held nowhere."),
 "why_nothing_is_approved": ("Not a judgment about importance. Every file is either a bill with an unfilled enactment "
                            "block or an exhibit to one, which is precisely the class the checkpoint holds back from "
                            "archival or visible use. The directory is unusual in having no ceremonial material, no "
                            "press releases, no meeting handouts and no duplicates — 8 of its 9 records are primary "
                            "legislative material and the ninth is the landing page."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 9 candidates on both URL forms and measured byte "
            "length and SHA-256 from the raw form. Compared all checksums within the cluster and against the 1,612 "
            "checksummed inventory records: no collisions either way. Extracted text from every PDF and read the "
            "operative sections; rendered the one image-only sheet. Fetched the archived East Gateway MRA plan "
            "read-only and searched it for the designating resolution. Searched the inventory and the published site "
            "for each instrument's outcome, per the standing lesson."),
 "classification_only": True,
 "shared_state_written": [],
 "two_answerable_now": {
  "R-07-278": {
   "record": "src-1a09b0a2a4e8fcbd",
   "evidence_it_was_enacted": ("Two independent archive records treat it as law. " + EPC_RECORD + ", the EPC record "
                               "recommended for addition from district 9, cites \"Resolution R-07-278 of 2007\" as "
                               "the instrument mandating a Bio-Zone Preserve. And the master plan it requires is "
                               "finished and published: " + BIOZONE_RMP + " at "
                               "content/public-works/parks-recreation.md line 139."),
   "what_is_missing": "The enactment number and the enacted text.",
   "why_it_is_worth_doing": "The site publishes the plan with no statement of the authority that required it. This resolution is that authority.",
  },
  "R-07-275": {
   "record": "src-b8dad566165e2a17",
   "evidence_it_was_enacted": ("The plan it directed the Metropolitan Redevelopment Agency to prepare exists and is "
                               "published: " + MRA_PLAN + " at content/development-land-use/redevelopment-plans.md "
                               "line 99."),
   "what_is_missing": ("The enactment number — and the archive is missing it twice. The published plan reproduces the "
                       "designating resolution in its own appendix as \"COUNCIL BILL NO. F/S R-07-275 ENACTMENT NO. "
                       "________________________\", also blank."),
   "why_it_is_worth_doing": "Resolving it corrects a gap inside a record that is already validated and live, not only in a pending one.",
  },
  "note": "Both were reachable only because earlier clusters were read closely enough to capture their citations, and because the published site was checked rather than just the inventory.",
 },
 "interim_regime_expired": {
  "finding": ("The remaining six files describe a temporary control regime that has lapsed. Each instrument sets its "
              "own end date in its own text: F/S(2) R-06-18's Interim Development Management Area runs \"until June "
              "1st, 2006\"; C/S R-07-278's moratorium \"shall be imposed until October 1st, 2008\"; R-07-276 runs "
              "\"until October 31, 2008 or until the final consideration by the City\" Council of the sector plan."),
  "what_closed_it": ("The East Gateway Sector Development Plan. " + EPC_RECORD + " names \"the 2010 East Gateway "
                     "Sector Development Plan\" in its background, so the plan exists and was adopted. The inventory "
                     "holds no copy of it under any search for East Gateway."),
  "consequence": ("These are historical-record questions, not live-regulation questions. Nobody is relying on these "
                  "interim design regulations today. That should lower their priority against the two answerable rows "
                  "above, and it means that if the 2010 sector development plan is found, the right move may be to "
                  "publish that and record this package as its superseded predecessor."),
 },
 "discovery_leads": [
  {"what": "East Gateway Sector Development Plan, 2010", "named_by": EPC_RECORD,
   "why": "The adopted successor that closed the interim regime in this directory. Not held anywhere in the inventory. The single most useful document this cluster points at."},
  {"what": "Council Bill F/S(2) R-06-67", "named_by": "src-51ac987d9e9d59d5",
   "why": "C/S R-06-172 names the Interim Development Management Area \"established in F/S(2) R-06-67\". That instrument is in neither this directory nor the inventory, so the package as filed is incomplete."},
  {"what": "The Staff Report attached to R-07-275 as Exhibit A", "named_by": "src-b8dad566165e2a17",
   "why": "Sections 5 and 6 of the designating resolution rest on blight findings \"set forth in the Staff Report attached to this resolution as Exhibit A\". That staff report is not in the directory and not in the inventory."},
 ],
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 1,
  "note": ("One relationship, and it is a partial-containment rather than a duplicate: the standalone R-07-275 is "
           "0.6976 contained in the archived MRA plan, which carries the floor substitute instead. The tokens outside "
           "that overlap are the street numbers of the parcel-level boundary description, which is why the candidate "
           "is not recommended as a duplicate. Every other file in the directory is unique in content and in bytes."),
 },
 "integration_flags": [
  {"severity": "tractable-enactment",
   "affects": ["src-1a09b0a2a4e8fcbd"],
   "finding": "R-07-278 is cited as law by an EPC record in the district-9 batch, and the Bio-Zone master plan it required is validated, archived and published. Only the enactment number is missing.",
   "recommended_action": "Resolve first. It is the most tractable enactment question in the run and it would let the parks page state where its Tijeras Arroyo plan came from."},
  {"severity": "affects-a-live-record",
   "affects": ["src-b8dad566165e2a17", MRA_PLAN],
   "finding": "The published East Gateway MRA Plan reproduces its own designating resolution with a blank enactment block. The gap is inside a validated, live record, not only in a pending one.",
   "recommended_action": "Resolve F/S R-07-275 alongside R-07-278. Do not treat the pending standalone bill as a duplicate of the plan: it carries a parcel-level boundary description the plan does not reproduce."},
  {"severity": "lowered-priority",
   "affects": ["src-19270229907c2c5b", "src-c9c828803603e6d3", "src-51ac987d9e9d59d5", "src-208b33695082ab06", "src-cd4af1b973f2c583", "src-1a52f943f87c3eb4"],
   "finding": "Six files describe an interim control regime that expired by its own terms between June 2006 and October 2008, closed by a 2010 sector development plan the archive does not hold.",
   "recommended_action": "Hold as a package at lower priority than the two above. If the 2010 plan is found, publish that and record this package as its superseded predecessor."},
  {"severity": "discovery-lead",
   "affects": [],
   "finding": "Three named documents are missing from the inventory entirely: the 2010 East Gateway Sector Development Plan, Council Bill F/S(2) R-06-67, and the staff report that is Exhibit A to R-07-275.",
   "recommended_action": "Queue all three. The sector development plan is the one that matters."},
  {"severity": "archival-cost",
   "affects": ["src-1a52f943f87c3eb4", "src-cd4af1b973f2c583"],
   "finding": "Two overlapping boundary maps, 17,569,920 bytes and 5,796,235 bytes. The smaller one is better labelled and dated.",
   "recommended_action": "If the package ever resolves and only one map is archived, take src-cd4af1b973f2c583."},
 ],
 "counts": {
  "reviewed": len(rows),
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 9, "http_200": 9, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "archive_fetches": "The archived East Gateway MRA plan at files.abqinfo.com was fetched read-only for comparison, HTTP 200, 2,788,694 bytes, 38 pages.",
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "8 genuine PDFs and one HTML collection page by leading bytes. One PDF has no usable text layer and was rendered."},
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"Nothing in this cluster is recommended for archival. If the package were resolved in full it "
                   f"would add {rhr_bytes:,} bytes, of which 23,366,155 is the two overlapping boundary maps; taking "
                   f"only the better of the two would cut that to {rhr_bytes - 17569920:,}. Seven of the eight "
                   f"substantive files are born-digital with full text layers."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Every substantive row is requires human review under "
                      "the standing enactment blockers, and each carries a priority field, an outcome search, and the "
                      "evidence found for or against enactment. No row carries a canonical_id, because nothing here "
                      "duplicates or is superseded by anything held — the one partial containment found is documented "
                      "in the R-07-275 row rather than asserted as a relationship. Sizes and checksums are first "
                      "measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the archived MRA plan was fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
