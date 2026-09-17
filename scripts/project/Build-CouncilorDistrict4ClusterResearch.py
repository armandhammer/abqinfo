"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12, the second artifact after the date rollover.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-4-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d4\fetch.log')

PARKS = 'content/public-works/parks-recreation.md'
AREA = 'content/development-land-use/area-sector-plans.md'
CAPITAL = 'content/city-data/capital-spending.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
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
        r["url_form_note"] = ("The inventory URL ends in the Plone /view suffix, which serves an HTML wrapper around "
                              "the file. Both forms return HTTP 200; the bytes were taken from the raw form. Archive "
                              "from the raw form and keep the /view form as the citable official record.")
    r.update(M[i])
    return r


PROCLAMATIONS = [
    ("src-13047a7d2716ba0d", "Proclamation congratulating narcotics detection K-9 Blaze and Sergeant Jeremy Bassett on Blaze's retirement", "2012-03-19", 1, "signed by eight of nine councillors and sealed"),
    ("src-d8e1806ade44a7d8", "Proclamation declaring May 12, 2012 Metro Teen Court Public Safety Day", "2012-04-16", 1, "signed and sealed"),
    ("src-61e7ab3283df2672", "Proclamation declaring August 20, 2012 Eastdale Little League Softball World Series Day", "2012-08-20", 1, "signed by all nine councillors and sealed"),
    ("src-a389da393f30a2c2", "Proclamation recognising Mark Shover of Boy Scout Troop 220 on attaining the rank of Eagle Scout", "2013-02-25", 1, "text layer present"),
    ("src-3cb03ce6dff0bf68", "Proclamation declaring May 20, 2013 Duke City Sound Day", "2013-05-20", 1, "signed and sealed"),
    ("src-48e1c75109ae15b6", "Proclamation honouring Albuquerque Police Department Commander Bonnie Montoya", "2013-12-02", 2, "text layer present"),
    ("src-f36a6a5893844f73", "Proclamation recognising Cyber Hero and the New Mexico Cyber Security Expo", "2014-03-17", 1, "signed and sealed"),
    ("src-a3e64e0383f59b20", "Proclamation welcoming a Kenyan Consulate delegation for Kenya's Golden Jubilee", "2014-04-19", 1, "text layer present"),
    ("src-45d063f61f6316c0", "Proclamation recognising the 2014 NCAA Division I Indoor Track and Field Championships held in Albuquerque", "2014-05-05", 2, "text layer present"),
    ("src-77398afe216df4af", "Proclamation recognising September 2014 as Childhood Cancer Awareness Month", "2014-09-03", 1, "signed and sealed"),
    ("src-24e2c025f0d260ae", "Proclamation declaring October 11, 2014 New Mexico Pageant of Bands Day", "2014-09-15", 1, "signed and sealed"),
    ("src-83f6c3e5c8d373c3", "Proclamation recognising the March of Dimes New Mexico Chapter and declaring November 17, 2014 New Mexico Prematurity Awareness Day", "2014-11-17", 1, "signed and sealed"),
]

PROC_REASON = (
 "A ceremonial Council proclamation on the standard printed form: a dated \"The Council of the City of Albuquerque\" "
 "sheet of WHEREAS recitals ending in a BE IT PROCLAIMED clause, signed by the sitting councillors and embossed with "
 "the City seal. Proclamations carry no legal effect and record no City action beyond the recognition itself. This is "
 "the reasoning councilor-district-5-cluster-research-2026-09-11.json applied to the Donate Life proclamation "
 "(src-61ae66da543b1909); it is applied here to twelve more.")

approved = [{
 **row("src-60a000a59cfbbaaf", "approved for addition"),
 "title": "North Domingo Baca Park Master Development Plan, February 3, 2005",
 "description": ("The City's master development plan for the 32-acre North Domingo Baca Park sets the park program, "
                 "site layout, architectural and landscape design standards, grading and drainage analysis, budget, "
                 "phasing, and the review path each future facility must follow."),
 "date": "2005-02-03",
 "pages": 44,
 "evidence": ("Born-digital PDF with a full text layer, 44 pages. Titled North Domingo Baca Park MASTER DEVELOPMENT "
              "PLAN, City of Albuquerque Department of Municipal Development, February 3, 2005. The park is bounded by "
              "Wyoming Boulevard, Carmel Avenue, Louisiana Boulevard and Corona Avenue, with an adjacent 27-acre AMAFCA "
              "property available for joint use. Eight sections plus a general plant list appendix: executive summary, "
              "site analysis, community issues, master plan, design standards, grading and drainage, project budget, "
              "and phasing."),
 "why_retained": ("It is regulatory, not descriptive. Section 8 sets the future review and approval process: the "
                  "Multi-Generational Center, Library and Pool Complex must be reviewed and approved by the "
                  "Environmental Planning Commission, while all other park features proceed directly to the Design "
                  "Review Committee for a work order. It also fixes design standards for architecture, setbacks, "
                  "building height, parking, lighting, signage, walls and fences, site furniture, landscape, irrigation "
                  "and utilities, and it carries a conceptual grading and drainage report with peak-discharge "
                  "calculations against Kinney Dam. Nothing of this kind for this park is held anywhere in the archive."),
 "proposed_canonical_page": PARKS,
 "cross_listings": [
   {"page": AREA, "reason": "It is a master development plan whose major elements are subject to Environmental Planning Commission approval, which is the class of record that page carries."},
   {"page": CAPITAL, "reason": "That page already schedules North Domingo Baca Park work in three separate bond records without holding the plan those projects build out."},
 ],
 "description_word_count": 0,
 "already_archived_check": ("Searched the inventory and the R2 inventory for North Domingo Baca objects. The archive "
                            "holds nothing for this park: the only Domingo Baca object in R2 is the Paseo del Norte "
                            "and South Domingo Baca Trail Guide, a different place. Three published capital records "
                            "name the park (content/city-data/capital-spending.md lines 314, 466 and 615, and "
                            "content/public-works/parks-recreation.md line 109) but all three are bond schedules that "
                            "fund it, not the plan that governs it."),
 "caution": ("Dated 2005 and explicitly phased against future funding, so its facility list describes intent rather "
             "than what was built. Section 8 records that land acquisition, some drainage, roadway and utility work "
             "and the AFD Station 20 / La Cueva police substation were already complete at the time of writing."),
}]

rhr = [{
 **row("src-227ada9c59279d76", "requires human review"),
 "draft_title": "Council Bill M-14-5: Memorial Calling for the State of New Mexico, the City of Albuquerque and Bernalillo County to Form a Task Force on Mental Health",
 "pages": 3,
 "evidence": ("Born-digital PDF with a full text layer. COUNCIL BILL NO. M-14-5, Twenty-First Council, sponsored by "
              "Brad Winter and Isaac Benton, ENACTMENT NO. blank. The operative clause calls for unanimous support and "
              "action at State, City and County levels by formulating a task force that will seek funding from those "
              "entities and work towards service strategies. Recitals cite the Metropolitan Detention Center, the "
              "2004 Arizona State University Applied Behavioral Health Policy finding that New Mexico had the largest "
              "drug-treatment gap of any state, and the re-traumatising effect of arresting people in mental health "
              "crisis."),
 "question_for_human": "Locate the enacted memorial for M-14-5. As with R-14-82 in the district-9 artifact, the outcome is independently evidenced and only the enactment number is missing.",
 "why_not_decided_here": ("Enactment number blank, under the two standing checkpoint blockers. Applying the standing "
                          "lesson from councilor-district-9-cluster-research-2026-09-12.json, this lane searched for "
                          "the adopted outcome rather than only for the number, and found it twice: "
                          "src-25ffefb6dcf6a735, the joint press release in this same directory dated 27 May 2014, "
                          "announces that the City, Bernalillo County, the State and UNMH have agreed to form exactly "
                          "the Working Group and Task Force the memorial calls for; and src-531fa27913dddde6 is the "
                          "City's own live Task Force on Behavioral Health project page. The task force was formed. "
                          "What is missing is the instrument, and unlike a budget or a plan the outcome here is not "
                          "itself an archivable document, so the memorial cannot simply be marked superseded."),
 "note": ("A memorial is a non-binding expression of Council position, so even enacted it would not be law in the way "
          "an ordinance is. It is still the record of the Council's formal call, and it is the origin of a body the "
          "City still runs."),
}]

excluded = []
for i, title, date, pages, form in PROCLAMATIONS:
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "date": date, "pages": pages,
              "form_evidence": form, "exclusion_reason": PROC_REASON,
              "category": "ceremonial Council proclamation"})
    excluded.append(r)

excluded.append({
 **row("src-25ffefb6dcf6a735", "excluded"),
 "title_for_reference": "Press release: City, County, State and UNMH Partner in Addressing Mental Health, Substance Abuse and Homelessness in Albuquerque",
 "date": "2014-05-27",
 "pages": 1,
 "exclusion_reason": ("A press release. It announces an agreement rather than recording one, and gives no membership, "
                      "charter, budget or schedule. Excluded on the same ground the run has applied to City news "
                      "items throughout."),
 "category": "press release",
 "but_see": "It is the evidence that M-14-5 produced its outcome, and it is cited as such in the requires-human-review row above. Excluding it from the archive does not discard that finding, which is recorded here.",
})

excluded.append({
 **row("src-8e77de0139392161", "excluded"),
 "title_for_reference": "Councilor's Corner, March 2015 edition (Councillor Brad Winter, District 4)",
 "date": "2015-03",
 "pages": 1,
 "exclusion_reason": ("A councillor's constituent newsletter, written in the councillor's voice and explicitly offered "
                      "for reuse in neighbourhood association mailers: \"This is our inaugural edition of the "
                      "bi-monthly Councilor's Corner update. I encourage you to include this in your neighborhood "
                      "association mailer...\". Councillor communications are excluded throughout this run, in "
                      "councilor-district-5-cluster-research-2026-09-11.json and again for eight summary sheets in "
                      "councilor-district-9-cluster-research-2026-09-12.json."),
 "category": "councillor newsletter",
 "but_see": ("It is a usable lead sheet. It reports that the Council had recently passed the Neighborhood Traffic "
             "Management Plan adopting new traffic-calming policy guidelines and treatments, with an amendment "
             "requiring the Department of Municipal Development to report back on the criteria in two years, and that "
             "the 2015 general obligation bonds designate $1 million for design and analysis of an indoor pool at "
             "North Domingo Baca Park. Neither the NTMP nor that report-back is held."),
})

excluded.append({
 **row("src-32776c81a6b4c7e8", "excluded"),
 "title_for_reference": "Councilor District 4 documents collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
})

for r in approved:
    r["description_word_count"] = len(r["description"].split())

rows = approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 17, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "councilor-district-4-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-4-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": ("Dated 2026-09-12, the second artifact after the rollover. Everything before "
               "councilor-district-9-cluster-research-2026-09-12.json is dated 2026-09-11. Cross-references name "
               "artifacts by filename for that reason."),
 "cluster": "The District 4 councillor's document collection in the Albuquerque City Council library, covering the terms of Councillor Brad Winter.",
 "scope": "All 17 pending-review candidates in that directory, which is every record it holds.",
 "count_correction": ("The handoff row claimed this lane at 16 pending. The directory holds 17 records and all 17 are "
                      "pending review, with none terminal. The handoff row has been corrected."),
 "brief": "Apply the district-9 lesson before writing any enactment-blocker row: search the inventory for the adopted outcome, not only for the enactment number.",
 "brief_finding": ("The brief was answerable and it changed what the row says. This directory holds one legislative "
                   "file, memorial M-14-5 with a blank enactment block, and searching for the outcome found it twice: "
                   "a joint press release in this same directory announcing the task force was being formed, and the "
                   "City's own live Task Force on Behavioral Health page. That still leaves the record at requires "
                   "human review rather than superseded, and the reason is worth recording. Unlike a budget or a plan, "
                   "the outcome of a memorial is not itself an archivable document, so there is no canonical to point "
                   "at. The lesson resolves cases where the outcome is a document and sharpens, rather than resolves, "
                   "cases where it is an event."),
 "second_finding": ("The directory is almost entirely ceremonial. Twelve of seventeen records are Council "
                    "proclamations, one is a press release, one a councillor newsletter and one a landing page. The "
                    "single substantive record is a 44-page master development plan for a 32-acre City park that sets "
                    "design standards and the Environmental Planning Commission review path for its major facilities, "
                    "and the archive holds nothing for that park."),
 "method": ("Ran the URL group-by across the directory first; no collisions. Fetched all 17 candidates on both URL "
            "forms and recorded exact byte length and SHA-256 from the raw form. Compared all checksums against the "
            "1,612 checksummed inventory records. Extracted text from every PDF; eight had no usable text layer and "
            "each of those was rendered and read rather than classified from its filename, which is the rule "
            "council-amendments-cluster-research-2026-09-11.json records. Searched the inventory and R2 for the "
            "adopted outcome of the one legislative file, and for prior archival of the one substantive plan."),
 "classification_only": True,
 "shared_state_written": [],
 "url_form_finding": {
  "what": ("Every file record in this directory is inventoried with a Plone /view suffix — "
           ".../ndbp_master_plan.pdf/view — which serves an HTML wrapper page, not the file."),
  "verified": "Both forms return HTTP 200 for all 16 file records. The raw form returns the PDF; the /view form returns HTML.",
  "why_it_matters": ("A fetch of the inventoried URL alone would have measured the size and checksum of a wrapper "
                     "page, and a container check by leading bytes would have called all sixteen HTML. Every row here "
                     "carries both URLs and the measurements are from the raw form."),
  "for_integration": "Archive from raw_file_url; cite authoritative_url. The two are the same object.",
  "scope_of_the_pattern": "This is a Plone convention, not a district-4 one. Other clusters in this run carried it too, including records already marked duplicate in the inventory under /view URLs.",
  "affected_rows": len(raw_differs),
 },
 "empty_directory_resolved": {
  "record": "src-c0433b3c564a14ca, www.cabq.gov/council/documents/task-force-on-mental-health-documents, the only inventory record for that path.",
  "why_it_was_checked": "M-14-5 called for the task force, so a directory of that name looked like where its enacted version and the task force's output would sit.",
  "result": ("Fetched the listing: HTTP 200, and the collection body reads \"There are currently no items in this "
             "folder.\" The directory is genuinely empty on the City's own server, not merely uncrawled."),
  "consequence": ("It does not need a lane. This closes what would otherwise read as an untriaged council/documents "
                  "subdirectory, and it means the enacted M-14-5 is not there. Note that this cuts the opposite way "
                  "from nob-hill-highland-cluster-research-2026-09-11.json, where the City's listing was incomplete "
                  "against its own server: listings can under-report what exists, and they can also correctly report "
                  "nothing. Fetching is what tells them apart."),
 },
 "proclamation_category": {
  "established_by": "councilor-district-5-cluster-research-2026-09-11.json, on src-61ae66da543b1909, the Donate Life proclamation.",
  "applied_here": len(PROCLAMATIONS),
  "tested_not_assumed": ("Eight of the twelve are image-only scans with no text layer. Each was rendered and read "
                         "before being classified, and each proved to be the standard signed and sealed proclamation "
                         "form. The four with text layers were read directly."),
  "inventory_wide": ("Fifteen inventory records carry \"proc\" in the title. Twelve are in this directory, one is the "
                     "district-5 Donate Life proclamation, and one is a Small Business Saturday proclamation on the "
                     "economic development server (src-14be4b3e253f0140), still pending and outside this lane. The "
                     "fifteenth is a false positive: src-567244356665a527, \"IIA Proc C Standard.pdf\", is "
                     "Infrastructure Improvements Agreement Procedure C and is approved for addition in "
                     "development-review-services-cluster-research-2026-09-11.json. Anyone sweeping for proclamations "
                     "by title should exclude it."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 0,
  "note": ("No duplicates and no supersession in this directory, which is the expected result: each proclamation names "
           "a different honouree on a different date, and the one plan and one memorial are unique. The check that "
           "mattered was not between these files but against what the archive already holds, and the park plan "
           "survived it."),
 },
 "integration_flags": [
  {"severity": "archive-from-raw-url",
   "affects": raw_differs,
   "finding": "All 16 file records are inventoried under Plone /view URLs that serve an HTML wrapper rather than the file.",
   "recommended_action": "Archive from raw_file_url and cite authoritative_url. Measurements here are from the raw form."},
  {"severity": "substantive-find",
   "affects": ["src-60a000a59cfbbaaf"],
   "finding": "A 44-page master development plan governing a 32-acre City park, setting design standards and the EPC and DRC review path for its facilities. The archive holds nothing for this park; three published bond records fund it without holding it.",
   "recommended_action": "Approve, archive, and place on the parks page. Cross-list to area and sector plans and to capital spending."},
  {"severity": "tractable-enactment",
   "affects": ["src-227ada9c59279d76"],
   "finding": "Memorial M-14-5 has a blank enactment block, but its outcome is independently evidenced by a joint press release in the same directory and by the City's live Task Force on Behavioral Health page. The enacted instrument is not in the obvious place: the council/documents/task-force-on-mental-health-documents folder is empty on the City's server.",
   "recommended_action": "Resolve alongside the two district-9 resolutions. All three are Twenty-First Council instruments whose adoption is evidenced but whose enacted text is unlocated."},
  {"severity": "discovery-lead",
   "affects": ["src-8e77de0139392161"],
   "finding": "The March 2015 Councilor's Corner reports the Council's adoption of the Neighborhood Traffic Management Plan, with an amendment requiring a Department of Municipal Development report-back on the criteria within two years. Neither the plan nor the report-back is held.",
   "recommended_action": "Add the NTMP to the discovery queue. It is adopted City traffic-calming policy and the newsletter itself is excluded, so the lead lives only here."},
  {"severity": "closes-a-directory",
   "affects": ["src-c0433b3c564a14ca"],
   "finding": "council/documents/task-force-on-mental-health-documents is empty on the City's server and needs no lane.",
   "recommended_action": "Mark the landing-page record terminal when convenient. No research remains."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 17, "http_200": 17, "failed": 0,
                "both_url_forms_checked": 16,
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "16 genuine PDFs and one HTML collection page by leading bytes, taken from the raw form. Eight PDFs have no usable text layer and were rendered."},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"The single approved record is a static PDF and is inventory-only until an R2 archive object "
                   f"exists for it and its public download, exact size, SHA-256, and authoritative-source provenance "
                   f"are verified. Archive footprint if authorized: {approved_bytes:,} bytes. It is born-digital with "
                   f"a full text layer across all 44 pages, so full-text search will reach it without optical "
                   f"character recognition."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id because this directory "
                      "holds no duplicates and no supersession. The one approved row carries a title, a 20-to-50-word "
                      "description, a date, a proposed_canonical_page, two cross-listings, an already_archived_check "
                      "and a caution. One row is requires human review under the standing enactment blockers, with the "
                      "outcome search recorded rather than left implicit. Sixteen rows carry a raw_file_url that "
                      "differs from the inventoried URL; archive from the raw form. Sizes and checksums are first "
                      "measurements; the inventory held neither."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the City listing and R2 inventory were read only"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
