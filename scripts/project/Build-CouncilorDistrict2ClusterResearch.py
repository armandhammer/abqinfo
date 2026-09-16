"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-2-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d2\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/councilor-district-2-documents/'

REDEV = 'content/development-land-use/redevelopment-plans.md'
PLANS = 'content/transportation/transportation-plans.md'
ROADS = 'content/transportation/roadway-projects/_index.md'
PARKS = 'content/public-works/parks-recreation.md'
ZONING = 'content/development-land-use/zoning-ido.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC = {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
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
 A("src-d31769eae697e92b",
   "Downtown Albuquerque Walkability Analysis and Recommendations (Jeff Speck)",
   "The consultant walkability study analyses Downtown Albuquerque street by street and recommends changes to make the centre walkable, covering street design, traffic operation, parking, land use, and the sequencing of interventions.",
   None, 302,
   ("302 pages and 31,565,710 bytes, by a wide margin the largest single document triaged in this run. The title page "
    "reads \"DOWNTOWN ALBUQUERQUE WALKABILITY ANALYSIS AND RECOMMENDATIONS\". The directory also holds the announcement "
    "of the author's Albuquerque lecture, src-aa08d71a1dd69370, which names him: \"City Councilor Isaac Benton welcomes "
    "Jeff Speck, urbanist and author, to speak in Albuquerque\"."),
   REDEV,
   why=("A major commissioned analysis of Downtown Albuquerque and the only copy in the inventory. The site already "
        "carries the Downtown 2050 plan and the 2025 Downtown parking study; this is the walkability analysis that sits "
        "between them in subject and predates both."),
   cross=[{"page": PLANS, "reason": "It is a street-design and traffic-operations study as much as a redevelopment one."}],
   extra={"dating_note": "No printed date on the pages read. The surrounding directory material is 2014 and the lecture announcement is undated; do not assert a year the document does not carry.",
          "size_flag": "At 31.5 MB this is a storage decision in its own right; see integration_flags."}),

 A("src-18d68c05c5230e3e",
   "Central Avenue Complete Street Performance Monitoring Summary",
   "The City handout summarises performance monitoring for the Central Avenue complete street work, setting out the background and previous planning efforts and reporting the measures used to judge whether the redesign performed as intended.",
   None, 12,
   "12 pages headed \"PERFORMANCE MONITORING SUMMARY, Background & Previous Planning Efforts\".",
   PLANS,
   why=("Post-implementation measurement is rare in this archive. The inventory holds the Complete Streets ordinance, "
        "its legislation packet and its presentation, all validated, but nothing that reports how the resulting street "
        "actually performed. This does."),
   cross=[{"page": ROADS, "reason": "Central Avenue is a named City corridor project and the monitoring belongs with the corridor record."}],
   extra={"dating_note": "No printed date; the directory context is 2014 to 2015. Do not assert one."}),

 A("src-222f76b6ba5f337e",
   "Comprehensive Plan Central and Established Urban Areas Map",
   "The City map shows the Comprehensive Plan's Central Urban and Established Urban area designations across Albuquerque, the geography that determines where the Complete Streets ordinance and related area policies apply.",
   None, 1,
   ("One large-format sheet, 3,154,645 bytes, labelled \"Comprehensive Plan Central and Established Urban Areas\" with "
    "arterial labels from Westside Boulevard and McMahon to Coors Bypass and NM 528."),
   ZONING,
   why=("The Comprehensive Plan area designations are cited throughout Albuquerque land-use material and the archive "
        "holds no map of them. It pairs directly with the 1988-to-2002 Comprehensive Plan recommended in the "
        "volcano-heights artifact of the same date, which is the text those designations come from."),
   cross=[{"page": PLANS, "reason": "It was published as a Complete Streets supporting map and defines where that ordinance applies."}],
   extra={"dating_note": "No printed date. Do not assert one."}),

 A("src-54ea9bb0628a1a53",
   "Downtown Neighborhood Area Traffic Study: Public Meeting Presentation, June 5, 2014",
   "The City presentation to the June 2014 public meeting sets out the Downtown Neighborhood Area traffic study's findings and options, covering the street network, circulation patterns, and the changes under consideration for the area.",
   "2014-06-05", 50,
   ("50 pages headed \"Downtown Neighborhood Area Traffic Study\". The filename records the meeting date as 6/5/14 and "
    "marks the deck FINAL."),
   ROADS,
   why=("The public-facing half of a study whose technical output the archive already holds. The inventory carries the "
        "DNA Traffic Report final of July 2014 as validated and implemented records (src-ce3c9f54fa83aba9, "
        "src-df8844768db111e4) and its appendix (src-66d6dd3f2f7408bb), but nothing showing what was put to the public "
        "or when. This presentation predates the final report by a month."),
   cross=[{"page": REDEV, "reason": "The Downtown Neighborhood Area is a named planning area with its own plan records."}],
   extra={"relationship": "Companion to the already-validated DNA Traffic Report; not a draft of it. The superseded draft of that report is a separate record, src-959643609168b387."}),

 A("src-6228d26224c6e19f",
   "Highland Park Renovation Record Drawing, City Project 644294 (Sheet LP101)",
   "The City landscape architecture record drawing for the Highland Park renovation keys eight numbered interventions across the park block, covering an accessible pedestrian walk, accessible parking, landscape buffers, play areas, and turf replacing removed parking.",
   None, 1,
   ("One large-format sheet, rendered and read. The title block reads \"CITY OF ALBUQUERQUE, STRATEGIC PLANNING AND "
    "DESIGN, PARKS AND RECREATION DEPARTMENT, HIGHLAND PARK RENOVATION\", City Project No. 644294, Zone Map K-14 and "
    "K-15, Sheet LP101, prepared by Morrow Reardon Wilkinson Miller, Ltd., Landscape Architects. The park block is "
    "bounded by Gold Avenue SE, Locust Street SE, Silver Avenue SE and a public alley."),
   PARKS,
   why=("A named, numbered City park capital project with a keyed site plan, which is the class of record the parks page "
        "already carries under Current Parks and Open Space Projects. It is the only Highland Park record in the inventory."),
   extra={"dating_note": "The record-drawing date block is blank on the sheet. Do not assert a date.",
          "caution": "The sheet is headed RECORD DRAWINGS but its as-built and city-engineer-approval blocks are unsigned, so it should not be described as an as-built."}),
]

superseded = [
 {**row("src-3934eab6ae32efb7", "superseded"),
  "title_for_reference": "Council Bill C/S O-14-27: Complete Streets Ordinance, committee substitute, December 10, 2014 draft",
  "pages": 11,
  "canonical_id": "src-50dbc9e020356e05",
  "canonical_url": BASE + "O27_CompleteStreet_FloorSub_Final_as_amended.pdf",
  "canonical_state": "validated, and titled Adopted Legislation in the inventory",
  "basis": ("A committee-substitute draft superseded by the floor substitute as amended, which the inventory already "
            "holds as a validated record. The bill designation changes on the face of the two documents: this draft is "
            "C/S O-14-27 at 11 pages, the successor is F/S O-14-27 at 12 pages."),
  "measurement": "Normalized-token coverage 0.9819 in both directions with a sequence ratio of 0.4865: the same ordinance re-laid-out and amended on the floor, not a different instrument.",
  "hash_found_it": False,
  "note": ("Two earlier drafts in this directory are already terminal-superseded, src-6705ec42d3bb6d2e for November 7 and "
           "src-dbf42102a1f6ab24. This December 10 draft is the last one before adoption and completes that chain."),
 },
]

LETTERS = [
 ("src-9e03c0a2637b4ea0", "src-e271c19776152b9e", "Greater Albuquerque Chamber of Commerce", "2014PositionSupportingCompleteStreetsOrdinance.pdf", 2),
 ("src-1aad59487828ec12", "src-be8f4bed636a4047", "American Planning Association, New Mexico Chapter", "CompleteStreetsLetterofSupportAPANM.pdf", 1),
 ("src-dac1fb8d66e29479", "src-81fec81c380435d0", "American Society of Landscape Architects, New Mexico", "CompleteStreetsNMASLALetterofSupport.pdf", 2),
 ("src-568151e20e03cfa4", "src-8f7e044375532900", "American Institute of Architects", "CompleteStreets_ABQCityCouncilLtr_12015.pdf", 1),
 ("src-2d4310a701de4e61", "src-bc780b95996af003", "New Mexico Complete Streets Leadership Team", "LetterofSupportforCABQCompleteStreets.pdf", 1),
 ("src-881523bf4e425992", "src-f8188bd262397e5b", "Downtown Albuquerque Millennial Project", "MiABQCompleteStreetsLetterofSupport.pdf", 5),
 ("src-ba088806917968aa", "src-d779aab19483f927", "New Mexico Healthier Weight Council", "NMHWCLetterofSupportCompleteStreetsOrdinance01427.pdf", 2),
]

duplicates = []
for pid, cid, org, fname, pages in LETTERS:
    r = row(pid, "duplicate")
    r.update({
     "title_for_reference": f"Complete Streets Ordinance letter of support from the {org}",
     "pages": pages,
     "canonical_id": cid,
     "canonical_url": BASE + fname,
     "canonical_state": f"already terminal-excluded as \"{(IDX[cid].get('title') or '')}\"",
     "basis": ("Not a similar document but the same URL. The inventory holds two records for this one file: one titled "
               "from the organisation that wrote it and one titled from the link text on the Council page. The "
               "organisation-titled record is still pending; the link-text record is already excluded."),
     "hash_found_it": False,
     "same_url": True,
     "inherits_disposition": ("The canonical is excluded as a stakeholder support letter that adds little policy or "
                             "technical information. That reasoning applies to this record unchanged, because it is the "
                             "same file. Recording it as a duplicate rather than re-excluding it preserves the fact "
                             "that the inventory double-counted one document."),
    })
    duplicates.append(r)

CAL = [
 ("src-bdc2b727531fe546", "May 2014", 17), ("src-b8ce3dac10f06189", "June 2014", 30),
 ("src-d5d5762a61168290", "July 2014", 25), ("src-70612036b0b5dfa4", "August 2014", 18),
 ("src-30428d73a043ced0", "September 2014", 19), ("src-cb7dda40e52ce7cb", "October 2014", 23),
]

excluded = []
for i, month, pages in CAL:
    r = row(i, "excluded")
    r.update({"title_for_reference": f"{month} Master Calendar of Cultural Events and Activities, Cultural Services Department",
              "pages": pages,
              "exclusion_reason": ("A monthly listing of City cultural events. Every entry expired within the month it "
                                   "names, and the series has no interpretive value beyond the events themselves."),
              "category": "monthly event calendar",
              "series": "Six consecutive months, May to October 2014, all excluded on the same ground."})
    excluded.append(r)

OTHER_X = [
 ("src-9bec272a402e22ab", "516 Arts June Events Calendar", 4,
  "An events calendar for a private downtown arts organisation, published on the councilor's page as a courtesy. Not a City record.",
  "third-party event calendar", None),
 ("src-3d558921eed83f30", "Shakespeare on the Plaza event flyer", 1,
  "A flyer for a performance series. An event notice, spent when the performances ended.", "event flyer", None),
 ("src-988e0fb95a74f2c1", "Healthy Aging series flyer, UNM School of Medicine Institute for Ethics", 1,
  "A flyer for a lecture series run by a university institute. Not a City record and not a City event.",
  "third-party event flyer", None),
 ("src-de7de072cc095357", "Rail Yards Market flyer", 1,
  "A season flyer for the Rail Yards Market, \"food. art. music. Sundays 9-3, May 4-Nov 2\". An event notice.",
  "event flyer",
  {"note": "The Rail Yards themselves are well covered: the rail-yards-advisory-board artifact of the same date recommends seventeen records for that site. This flyer adds nothing to them."}),
 ("src-aa08d71a1dd69370", "Jeff Speck lecture announcement", 1,
  "An announcement that Councillor Isaac Benton was hosting the urbanist Jeff Speck to speak in Albuquerque. An event notice.",
  "event announcement",
  {"useful_fact": "It is what identifies the author of the 302-page walkability analysis recommended for addition in this batch, which carries no author on its title page. Recorded here so the attribution is not lost with the flyer."}),
 ("src-711bf07c3fe40d74", "Barelas Pedestrian Bridge ribbon cutting press release", 1,
  "A City Council press release announcing a ribbon cutting. The inventory already carries a terminal exclusion for a Council news item of this kind, src-0b20b31b78ea3865, and five more were excluded in the councilor-district-5 artifact of the same date.",
  "councilor press release", None),
 ("src-385036989b8d1925", "Neighborhood association notification letter, proposed text amendments to the Sawmill/Wells Park Sector Development Plan, August 27, 2014", 1,
  "A hearing notice sent to recognised neighbourhood associations under the Neighborhood Recognition Ordinance. It announces a meeting rather than recording a decision, and the amendments it announces are not in this directory.",
  "hearing notice",
  {"discovery_lead": ("Rendered and read. It gives the details needed to find the substantive record: Project 1000029, "
                      "proposed text amendments to Chapter 6 of the Sawmill/Wells Park Sector Development Plan to update "
                      "the road network and transportation design, Environmental Planning Commission hearing "
                      "October 9, 2014, staff planner Vicente M. Quevedo. Neither the amendments nor the Sawmill/Wells "
                      "Park plan is in the inventory.")}),
]

for i, title, pages, reason, cat, extra in OTHER_X:
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages, "exclusion_reason": reason, "category": cat})
    if extra:
        r.update(extra)
    excluded.append(r)

excluded.append({
 **row("src-42469f4bc1ba2c77", "excluded"),
 "title_for_reference": "Councilor District 2 documents collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
 "note": ("Three paginated views of this same listing are already terminal-excluded as src-7a409f39d2efa5c9, "
          "src-45cbbefa896507d4 and src-7eb126e84c6a8609, titled only \"1\", \"2\" and \"3\"."),
})

rows = approved + superseded + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 27, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "councilor-district-2-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-2-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The District 2 councilor's document collection in the Albuquerque City Council library, covering the terms of Councillor Isaac Benton.",
 "scope": "All 27 pending-review candidates in that directory. The directory holds 51 records in total, 24 of them already terminal, which is unusual: most of the Complete Streets material here was triaged by an earlier pass and this lane had to reconcile against it rather than classify fresh.",
 "brief": "Separate substantive district records from constituent notices and press material, applying the district-5 method: render image-only records, check the enactment number on every legislative file, and check against R2 objects already held.",
 "brief_finding": "The separation is stark: five records carry real content and twenty-two are event calendars, flyers, notices, or the same file counted twice. But the five include the largest document triaged anywhere in this run, a 302-page Downtown Albuquerque walkability analysis, whose author is identifiable only from a flyer in the same directory that is recommended excluded. The reconciliation against existing records also turned up an inventory-hygiene problem the lane brief did not anticipate.",
 "method": "Fetched all 27 pending candidates without touching shared inventory state and recorded exact byte length and SHA-256 for each. Grouped every record in the directory, terminal ones included, by normalised URL, which is what exposed the duplicate-record problem. Rendered the three image-only PDFs. Fetched the already-validated adopted Complete Streets ordinance read-only and measured the pending December draft against it. Compared all checksums against the 1,612 checksummed inventory records.",
 "classification_only": True,
 "shared_state_written": [],
 "inventory_hygiene_finding": {
  "headline": "Twelve URLs in this one directory carry more than one inventory record each: 26 records for 12 files.",
  "how_found": "By grouping every record in the directory on its URL with /view stripped, rather than on its id or title. No content measurement was needed.",
  "cause": ("Two discovery passes titled the same file differently. One pass took the title from the organisation that "
            "wrote the document (\"Greater Albuquerque Chamber of Commerce\"), the other from the link text on the "
            "Council page (\"Complete Streets Letter of Support2\"). Both created records."),
  "pending_half": ("Seven of the extra records are still pending and are recommended duplicate in this artifact. Each "
                   "shares a URL with a twin that is already excluded, so the disposition is settled by the twin."),
  "terminal_half_needs_codex": {
   "severity": "correctness",
   "finding": ("Five URL groups consist entirely of already-terminal records, so this lane cannot touch them, and three "
               "of those groups pair two validated records for one file. The archive is double-counting validated "
               "documents."),
   "groups": [
    {"file": "CompleteStreetsOrdinancePresentation.pdf", "records": ["src-0089b84c33b46e84 (duplicate)", "src-83279794dcb22b7a (validated)", "src-f4de3930a6e04830 (validated)"],
     "note": "Three records for one file, two of them validated."},
    {"file": "CompleteStreetsLegislationPacket.pdf", "records": ["src-439525683f2a5e58 (validated)", "src-8b18827057480dac (validated)"]},
    {"file": "O27_CompleteStreet_FloorSub_Final_as_amended.pdf", "records": ["src-50dbc9e020356e05 (validated)", "src-912bc14c869a79b0 (validated)"],
     "note": "This is the adopted Complete Streets ordinance, and it is the canonical this artifact's one superseded row points at."},
    {"file": "TrafficReportFINALJuly2014.pdf", "records": ["src-ce3c9f54fa83aba9 (validated)", "src-df8844768db111e4 (implemented)"]},
    {"file": "Appendix.pdf", "records": ["src-66d6dd3f2f7408bb (validated)", "src-89f97c6a639700bb (implemented)"]},
   ],
   "recommended_action": ("Codex should reconcile these five groups to one record per file. Claude did not modify any of "
                          "them. Two carry a validated-and-implemented pair, which may be deliberate if the project "
                          "distinguishes an inventory record from a site placement record; the three validated-validated "
                          "and validated-duplicate-validated groups are harder to read as intentional."),
   "wider_question": ("This lane found the pattern by URL-grouping one directory. Whether it recurs across the "
                      "7,074-record inventory is a cheap check worth running before any count of validated records is "
                      "reported: group all records on normalised direct_file_url and list groups with more than one "
                      "terminal record."),
  },
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_url_grouping": 7,
  "relationships_found_by_measurement": 1,
  "note": ("A fourth distinct detection method, and the cheapest yet. The seven duplicate rows here needed no hashing, "
           "no text extraction and no rendering: two records pointing at one URL are one document by definition. The "
           "earlier clusters in this run needed byte hashing, normalized-text coverage, and R2-object inspection "
           "respectively; this one needed only a group-by. Run the URL group-by first in future clusters, before "
           "fetching anything."),
 },
 "integration_flags": [
  {"severity": "correctness",
   "affects": ["src-0089b84c33b46e84", "src-83279794dcb22b7a", "src-f4de3930a6e04830", "src-439525683f2a5e58",
               "src-8b18827057480dac", "src-50dbc9e020356e05", "src-912bc14c869a79b0", "src-ce3c9f54fa83aba9",
               "src-df8844768db111e4", "src-66d6dd3f2f7408bb", "src-89f97c6a639700bb"],
   "finding": "Eleven already-terminal records cover five files. Three groups pair two validated records for a single document and one group has three records for one document.",
   "recommended_action": "Reconcile to one record per file, and run the inventory-wide URL group-by described in inventory_hygiene_finding before any validated-record count is reported. Claude did not modify these records."},
  {"severity": "storage",
   "affects": ["src-d31769eae697e92b"],
   "finding": f"The walkability analysis is 31,565,710 bytes, 80 per cent of this batch's {approved_bytes:,}-byte footprint and the largest single document triaged in this run.",
   "recommended_action": "Size it into the upload queue deliberately rather than folding it into a routine batch, as with the NPDES Manual and the Volcano Heights plan parts."},
  {"severity": "attribution",
   "affects": ["src-d31769eae697e92b", "src-aa08d71a1dd69370"],
   "finding": "The walkability analysis carries no author on its title page. The only thing identifying Jeff Speck as its author is the lecture announcement in the same directory, which is recommended excluded.",
   "recommended_action": "Carry the attribution into the retained record's description and evidence rather than relying on the flyer surviving. It is already recorded in both rows of this artifact."},
  {"severity": "discovery-lead",
   "affects": ["src-385036989b8d1925"],
   "finding": "The excluded hearing notice names a substantive record the archive does not hold: proposed text amendments to Chapter 6 of the Sawmill/Wells Park Sector Development Plan, Project 1000029, heard by the Environmental Planning Commission on October 9, 2014. Neither the amendments nor the Sawmill/Wells Park plan itself is in the inventory.",
   "recommended_action": "Add both to the discovery queue. The Council library has a sawmill-documents subdirectory still untriaged, which is the obvious place to look first."},
  {"severity": "completes-a-record",
   "affects": ["src-54ea9bb0628a1a53"],
   "finding": "The inventory holds the Downtown Neighborhood Area Traffic Report final of July 2014 as validated and implemented records plus its appendix, and a superseded February 2014 draft, but nothing showing what was put to the public. This June 5, 2014 presentation is that.",
   "recommended_action": "Place it with the existing DNA Traffic Report records rather than separately."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "requires_human_review": 0,
 },
 "link_check": {"checked": 28, "http_200": 28, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 27 pending candidates plus a read-only fetch of the already-validated adopted Complete Streets ordinance for the supersession measurement.",
                "containers_verified": "26 genuine PDFs and one HTML collection page by leading bytes. Three PDFs have no text layer and were rendered."},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": f"All 5 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, dominated by the 31,565,710-byte walkability analysis. Three of the five carry a null date because no page prints one, and none may be given an asserted date.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. The single superseded row's canonical is an already-validated record. All seven duplicate rows are same-URL duplicates whose canonicals are already excluded, and each carries same_url true and an inherits_disposition note; they need no content check. The 5 approved rows each carry a title, a 20-to-50-word description, a proposed_canonical_page and cross_listings where a second page applies. This artifact raises no requires-human-review row. Separately, eleven already-terminal records in this directory cover five files and need reconciliation; that is recorded in inventory_hygiene_finding and is outside this lane's classification scope. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
