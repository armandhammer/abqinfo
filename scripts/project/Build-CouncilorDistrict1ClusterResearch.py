"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\councilor-district-1-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\d1\fetch.log')

STUDIES = 'content/transportation/roadway-projects/studies.md'
SPEED = 'content/transportation/roadway-projects/speed-management.md'
CAPITAL = 'content/city-data/capital-spending.md'

CSR_CLEAN = 'src-23a38383e9fff089'
ENACTED_R1431 = 'src-7bf7341bebf83fe6'   # district-9: enacted R-2014-012, Bill R-14-31

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
 **row("src-1740488e9a78e215", "approved for addition"),
 "title": "Atrisco Drive Lane Modifications, Central Avenue to Iliff Road — Public Meeting Presentation, November 13, 2014",
 "description": ("The City's traffic engineering case for narrowing Atrisco Drive NW to one lane each way sets out "
                 "measured speeds, crash causes, access counts, traffic volumes against roadway capacity, expected "
                 "signal-cycle impacts, and the twelve-month pilot restriping proposed to residents."),
 "date": "2014-11-13",
 "pages": 21,
 "evidence": ("PDF with a thin text layer over image slides; pages were rendered and read. Titled ATRISCO DRIVE / LANE "
              "MODIFICATIONS / CENTRAL AVENUE TO ILIFF ROAD, November 13, 2014, prepared by Parametrix. It carries "
              "existing-conditions speed data from 2009, a crash-cause breakdown (5 following too closely, 4 "
              "excessive speed, 4 improper turn, 3 driver inattention, 3 failure to yield, 3 drugs or alcohol, 3 other "
              "no-error, 2 avoiding a vehicle, 1 passed stop sign), an access inventory of 22 side-street "
              "intersections and over 100 driveways, bikeway conditions, traffic volumes plotted against four-lane and "
              "two-lane level-of-service D capacity, and an expected-traffic-impacts slide giving signal cycles to "
              "clear at Central."),
 "why_retained": ("It is the only record of this project anywhere. The inventory holds nothing else for Atrisco Drive "
                  "NW — every other Atrisco record is Atrisco Vista Boulevard, a different County road on the far west "
                  "side. The condensed-presentation exclusion applied twice in "
                  "councilor-district-7-cluster-research-2026-09-12.json does not reach this file, because that rule "
                  "turns on the full study being archived and here there is no full study to defer to. The site "
                  "already publishes a comparable presentation on the same ground: the GABAC crossing-concept deck at "
                  "content/transportation/bicycling/projects/_index.md line 125."),
 "proposed_canonical_page": STUDIES,
 "cross_listings": [
   {"page": SPEED, "reason": "Its problem statement is speeding on Atrisco Drive and its proposal is a lane conversion to reduce it; that page already carries the Iliff Road and Milne Road speed studies for the same part of the city."},
 ],
 "caution": ("A proposal presented to residents, not a decision. It asks for a twelve-month pilot restriping to one "
             "lane each way with 6.5-foot bike lanes; nothing here records whether that pilot was approved or built."),
 "description_word_count": 0,
}]


def R(i, draft_title, pages, evidence, question, why, extra=None):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages, "evidence": evidence,
              "question_for_human": question, "why_not_decided_here": why})
    if extra:
        r.update(extra)
    return r


rhr = [
 R(CSR_CLEAN,
   "Council Bill C/S R-08-182: Resolution Approving the Programming of Funds and Projects for the 2009-2018 Decade Plan for Capital Improvements Including the 2009 Two-Year Capital Budget",
   14,
   ("Image-only PDF with 14 bytes of extractable text; rendered and read. CITY of ALBUQUERQUE, EIGHTEENTH COUNCIL, "
    "COUNCIL BILL NO. C/S R-08-182, ENACTMENT NO. blank, sponsored by Ken Sanchez. It recites 2-12-2 ROA 1994 "
    "requiring the Mayor to formulate the Decade Plan, the biennial Two-Year Capital Budget requirement, and Council "
    "approval within 60 days of a public hearing, then sets out Section 1's project-and-amount table beginning with "
    "DMD/Streets: Reconstruction of Lead and Coal Avenues $4,000,000, Reconstruction Major Streets $1,600,000, "
    "Reconstruction Major Intersections $1,650,000. It also makes appropriations from Transportation Infrastructure "
    "Tax Fund 340."),
   "Locate the enacted resolution for R-08-182.",
   ("Enactment number blank, under the two standing checkpoint blockers. Applying the standing lesson from "
    "councilor-district-9-cluster-research-2026-09-12.json, this lane searched for the adopted outcome and found the "
    "programme but not the instrument. The 2009 general obligation bond programme this resolution approves is "
    "published in unusual depth: content/city-data/capital-spending.md carries the funding allocation chart, the "
    "department scope tables and the 2009-2017 department summaries for Streets, Storm Drainage, Parks and Recreation, "
    "ABQ RIDE, Community Facilities and more, and at line 141 it publishes the *enacted* criteria resolution R-07-12 "
    "for the same programme. So the Council's enacted instruments for this programme are demonstrably obtainable; the "
    "programming resolution is simply not held. Unlike the district-9 budget case, the outcome here is a programme "
    "rather than a single successor document, so no canonical can be asserted."),
   extra={"note": "This is a complete committee-substitute bill text, not an amendment sheet. The non-self-contained-fragment exclusion recorded in council-documents-cluster-research-2026-09-11.json does not apply to it.",
          "related_outside_this_cluster": ("Two committee amendment sheets to the same bill sit in the District 5 "
                                           "directory, src-a09a7081a2d10b09 and src-652537178b2679cd, both already "
                                           "recommended excluded in "
                                           "councilor-district-5-cluster-research-2026-09-11.json as "
                                           "non-self-contained fragments. Resolving R-08-182 would let those be "
                                           "revisited if desired.")}),

 R("src-f8453bfbac0e5e6f",
   "2009 Capital Implementation Program working table 1: department-by-department comparison of the proposed programme against the proposed floor substitute (Committee Sub R-08-182, Sanchez)",
   8,
   ("Born-digital PDF with a full text layer, 27,494 characters. Headed \"Committee Sub - R-08-182 - Sanchez / 2009 "
    "CIP\" with columns for Proposed Total, Additions, Proposed Floor Sub Subtract, Proposed Total and Comments, "
    "line by line across departments. Example rows: Reconstruct Lead/Coal Avenues $4,000,000 with the comment \"To be "
    "funded from Trans Tax\"; Reconstruct Major Streets $2,900,000 less $1,300,000; Major Paving Rehab $6,000,000."),
   "Decide with C/S R-08-182 above. If the floor substitute these tables analyse was adopted, they document how the programme changed; if it was not, they are working papers for a proposal that failed.",
   ("These are exhibits to a *floor* substitute, a later instrument than the committee substitute above and one that "
    "is not held at all. The amendment-packet rule recorded in council-amendments-cluster-research-2026-09-11.json "
    "says an amendment packet with no enacted parent held is excluded, but that rule was written for amendment "
    "sheets, which are unreadable without the bill. These tables are self-contained and carry figures that exist "
    "nowhere else, so excluding them on a rule written for a different document type would lose real content on a "
    "technicality."),
   extra={"companion": "src-e84ecf5f9ebbee36"}),

 R("src-e84ecf5f9ebbee36",
   "2009 Capital Implementation Program working table 2: district-specific and multiple-district projects by Council district (Committee Sub R-08-182, Sanchez)",
   3,
   ("Born-digital PDF with a full text layer. Headed \"District Specific & Multiple District Projects by Council "
    "District / Committee Sub - R-08-182 - Sanchez\" with columns As Proposed, Proposed Floor Sub and Difference. "
    "Council District One rows include Public Library at Central and Unser $650,000 unchanged, Westgate Community "
    "Center Renovation $1,000,000 rising to $3,000,000, Fortuna Storm Drain $1,500,000 unchanged, SW Arterial "
    "Roadways $1,000,000 unchanged, and West Central MRA / New Neighborhood Park $500,000 rising to $750,000."),
   "Decide with the two rows above.",
   ("Same grounds as its companion table. This one is the more consequential of the two: it is a district-by-district "
    "ledger of what each councillor's area would gain or lose under the floor substitute, which is exactly the kind "
    "of figure a resident would want and which the published departmental summaries do not break out."),
   extra={"companion": "src-f8453bfbac0e5e6f"}),
]

superseded = [
 {**row("src-418a707110a63f41", "superseded"),
  "title_for_reference": "Council Bill C/S R-08-182 — Redline Version",
  "pages": 11,
  "canonical_id": CSR_CLEAN,
  "canonical_url": IDX[CSR_CLEAN].get('direct_file_url'),
  "canonical_state": "requires human review in this batch, under the standing enactment blockers",
  "basis": "The change-marked presentation of the same committee substitute; the clean text is the operative one.",
  "measurement": ("Both are image-only and both were rendered. The pages are identical through line 24 — same council, "
                  "same bill number C/S R-08-182, same blank enactment block, same sponsor, same resolution title and "
                  "recitals — and diverge only in the amount column, where the clean text prints \"$1,600,000\" and the "
                  "redline prints \"[-$2,900,000-][+$1,600,000+]\". The redline also carries the banner \"~ Redline "
                  "Version ~\" above the City name. It runs 11 pages to the clean text's 14 because the markup "
                  "reflows the tables."),
  "hash_found_it": False,
  "what_is_lost": ("The redline is the only record of what the committee changed from the original R-08-182. That is "
                   "worth noting rather than archiving: the same information is recoverable from the two CIP working "
                   "tables held at requires human review above, which give the before and after figures in columns."),
  "precedent": ("Two presentations of one instrument, resolved to the clean text. Same treatment as the R-14-82 and "
                "R-14-113 pairs in councilor-district-9-cluster-research-2026-09-12.json and the FY2011 floor "
                "substitute pair in councilor-district-5-cluster-research-2026-09-11.json.")},
]


def X(i, title, pages, reason, category, date=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "pages": pages, "exclusion_reason": reason, "category": category})
    if date:
        r["date"] = date
    if extra:
        r.update(extra)
    return r


PR = ("A City Council press release on Council letterhead, marked FOR IMMEDIATE RELEASE. Press releases are excluded "
      "on the ground recorded in councilor-district-4-cluster-research-2026-09-12.json: they announce rather than "
      "record, and the instrument or action behind them is the archivable thing.")

excluded = [
 X("src-2bf84750e66b6baf",
   "Press release: Albuquerque City Council amends R-14-31, National Adoption Appreciation Day (corrected issue)", 1,
   PR, "press release", "2014-03-17",
   extra={"version_relationship": ("The corrected issue of src-a208f1c6551241b1, and the correction runs the opposite "
                                   "way from what the filenames suggest: this is copy_of_Harris_Sanchez_Adoption.pdf "
                                   "and it is the later, right one. The earlier file prints the bill number as "
                                   "E-14-31 in both the headline and the body and calls the observance \"National "
                                   "Adoption Day Appreciation\"; this one prints R-14-31 and \"National Adoption "
                                   "Appreciation Day\". Normalized-text ratio 0.99; those two lines are the whole "
                                   "difference."),
          "confirmed_against_another_cluster": ("R-14-31 is right and E-14-31 is a typo. "
                                                "councilor-district-9-cluster-research-2026-09-12.json recommends "
                                                + ENACTED_R1431 + " for addition: the enacted Resolution R-2014-012, "
                                                "Council Bill R-14-31, sponsored by Don Harris and Ken Sanchez, "
                                                "amending R-13-189 on Adoption Appreciation Day. The enacted "
                                                "instrument settles both the number and the name."),
          "but_see": "The enacted resolution itself is the archivable record of this action, and it is already recommended for addition from the District 9 directory."}),

 X("src-a208f1c6551241b1",
   "Press release: Albuquerque City Council amends E-14-31, National Adoption Day Appreciation (first issue, contains a bill-number error)", 1,
   PR, "press release", "2014-03-17",
   extra={"version_relationship": "Superseded in substance by src-2bf84750e66b6baf. Both are excluded, so no canonical_id is asserted; see the status_convention block.",
          "error": "Prints the bill number as E-14-31; the enacted instrument is Council Bill R-14-31, Enactment R-2014-012."}),

 X("src-2cf62271117cfd31",
   "Press release: No one banned from future City Council meetings, May 13, 2014", 2,
   PR, "press release", "2014-05-13",
   extra={"content": ("Council President Ken Sanchez's statement about the 5 May 2014 Council meeting, the special "
                      "meeting he called for 8 May, and the strict interim rules of decorum implemented for it. It "
                      "notes that Council Rules do not permit general public comment at special meetings."),
          "discovery_lead": "The interim rules of decorum themselves, and whatever instrument adopted them, are not held anywhere in the inventory."}),

 X("src-ce4f3ca1b6df8211",
   "Press release: Election of Officers, December 3, 2013", 1,
   PR, "press release", "2013-12-03",
   extra={"content": ("Records that at the 2 December meeting the Council unanimously elected Councillor Ken Sanchez "
                      "President, Councillor Trudy Jones Vice-President and Councillor Dan Lewis Committee of the "
                      "Whole Chair, and summarises the President's duties: presiding, assigning and referring bills, "
                      "preparing the agenda, signing passed bills, and appointing councillors to committees."),
          "why_still_excluded": ("It reports a Council action rather than being one. The minutes of the 2 December "
                                 "2013 meeting are the record, and the run's missing-minutes policy is explicit that "
                                 "an agenda or a notice is never presented as minutes; the same reasoning applies "
                                 "more strongly to a press release.")}),

 X("src-7c3f2ea6bda0d838",
   "Press release: Albuquerque Fire Department pay increase, February 2, 2014", 1,
   PR, "press release", "2014-02-02",
   extra={"content": ("Announces the intention of Council President Sanchez and Councillor Lewis to introduce R-14-22 "
                      "for immediate action on 3 February 2014, reserving $1.8 million in the FY14 General Fund for "
                      "salary increases for firefighters and emergency medical personnel, equivalent to a 3.5% average "
                      "pay increase."),
          "discovery_lead": "R-14-22 is not held in any form, enacted or otherwise."}),

 X("src-161f95b657b74333",
   "Letter from Council President Ken Sanchez to neighbours regarding the Atrisco Drive project, November 5, 2014", 1,
   ("A councillor's letter to constituents inviting them to the 13 November 2014 public meeting. Councillor "
    "communications are excluded throughout this run, most recently for the Councilor's Corner newsletter in "
    "councilor-district-4-cluster-research-2026-09-12.json and the Gibson letter in "
    "councilor-district-7-cluster-research-2026-09-12.json."),
   "councillor communication", "2014-11-05",
   extra={"tested_not_assumed": "Image-only, one byte of extractable text; rendered and read.",
          "discovery_lead": ("It records two things held nowhere else: a Traffic Mitigation Study presented to the "
                             "community in 2010 that proposed a roundabout at Hanover and Atrisco, never built for "
                             "want of funding; and a current two-way volume of approximately 10,800 vehicles per "
                             "weekday on Atrisco Drive NW. It also names the meeting the approved presentation was "
                             "given at, which is how the two files in this directory connect.")}),

 X("src-cefba0fa7ce6abe6",
   "Northwest Area Command, On the Beat, Issue 8, January 2015", 4,
   ("An Albuquerque Police Department area command community newsletter: a commander's column, neighbourhood notices "
    "and seasonal items. A departmental community bulletin, not a record of City action, a standard or a decision."),
   "departmental newsletter", "2015-01"),

 X("src-641e77fab876f4f0",
   "Councilor District 1 documents collection landing page", None,
   "The Plone collection landing page for this directory, not a document.", "collection landing page"),
]

for r in approved:
    r["description_word_count"] = len(r["description"].split())

rows = approved + rhr + superseded + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 13, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "councilor-district-1-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/councilor-district-1-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The District 1 councillor's document collection in the Albuquerque City Council library, covering Council President Ken Sanchez's capital-programme and Atrisco Drive work.",
 "scope": "All 13 pending-review candidates, which is every record in the directory. Nothing here is terminal.",
 "brief": "Apply the now-standard opening sequence: URL group-by, both URL forms, internal and inventory-wide hashing, then a comparison against the published site and R2 before anything is recommended.",
 "brief_finding": ("The sequence found nothing already held, which is itself the result: unlike the last three "
                   "clusters, this directory duplicates nothing in the archive. What it does hold is the 2009 capital "
                   "programming resolution in two presentations plus two working tables — the largest single financial "
                   "instrument found in a councillor directory this run — and a genuinely unheld traffic engineering "
                   "case for a lane conversion on a street the archive knows nothing about."),
 "second_finding": ("A small correction with an unusually clean proof. Two copies of one press release differ in two "
                    "lines: the first prints the bill number E-14-31, the second R-14-31. The Plone filename says the "
                    "second is the copy, but it is the corrected one — and the proof is in another directory. "
                    "councilor-district-9-cluster-research-2026-09-12.json recommends the enacted Resolution "
                    "R-2014-012, Council Bill R-14-31, sponsored by the same two councillors, for exactly this "
                    "subject. Neither press release is worth archiving; the enacted resolution already is."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 13 candidates on both URL forms and measured byte "
            "length and SHA-256 from the raw form. Compared all checksums within the cluster and against the 1,612 "
            "checksummed inventory records: no collisions either way. Extracted text from every PDF; four had no "
            "usable text layer and were rendered and read rather than classified from their filenames. Searched the "
            "inventory and the published site for the adopted outcome of the one legislative instrument and for prior "
            "coverage of the one substantive presentation."),
 "classification_only": True,
 "shared_state_written": [],
 "status_convention": {
  "problem": ("Three clusters in a row have produced version pairs where neither member is retained — the two issues "
              "of a DNA meeting summary, the four copies of a Transition Albuquerque flyer, and now the two issues of "
              "an adoption press release. Marking one superseded by the other asserts an archival ordering for "
              "documents that will not be archived."),
  "rule_used": ("Where the copies are byte-identical, use duplicate: it states a mechanical fact that holds whether or "
                "not anything is retained, which is how the flyer group was handled in "
                "councilor-district-7-cluster-research-2026-09-12.json. Where the copies differ in content and neither "
                "is retained, mark both excluded and record the relationship in prose, which is how the DNA meeting "
                "summaries were handled in dnasdp-cluster-research-2026-09-12.json and how the press releases are "
                "handled here. Reserve superseded for cases where the canonical is itself retained or held for "
                "review, as the redline row in this artifact is."),
  "for_integration": "Stated so the three artifacts read consistently rather than looking like three different judgments.",
 },
 "legislative_package": {
  "instrument": "Council Bill C/S R-08-182, Eighteenth Council, sponsored by Ken Sanchez: approving the programming of funds and projects for the 2009-2018 Decade Plan for Capital Improvements including the 2009 Two-Year Capital Budget, and making appropriations from Transportation Infrastructure Tax Fund 340.",
  "files_here": {
   "clean committee substitute": CSR_CLEAN,
   "redline committee substitute": "src-418a707110a63f41",
   "floor substitute working table, by department": "src-f8453bfbac0e5e6f",
   "floor substitute working table, by Council district": "src-e84ecf5f9ebbee36",
  },
  "outcome_search": ("The programme this resolution approves is published in depth on "
                     "content/city-data/capital-spending.md — the 2009 funding allocation chart, department scope "
                     "tables, and 2009-2017 department summaries — and line 141 of that page publishes the enacted "
                     "criteria resolution R-07-12 for the same bond programme. So enacted instruments from this "
                     "programme are obtainable. The programming resolution itself is not held in any form."),
  "why_it_matters": ("The district-by-district table is the only place in the archive where the 2009 capital programme "
                     "is broken out by Council district with before-and-after figures. The published departmental "
                     "summaries aggregate by department instead."),
  "recommended_action": "Resolve R-08-182 together with the two Don Harris resolutions from district 9 and memorial M-14-5 from district 4. Four Council instruments now sit at requires human review with their adoption evidenced or their programme published, and only the enacted text unlocated.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_rendering": 1,
  "relationships_found_by_text_diff": 1,
  "note": ("Two relationships and hashing found neither. The redline and clean bill texts are both image-only and were "
           "settled by rendering both first pages and reading the amount column. The press release pair was settled by "
           "a two-line diff and then confirmed against an enacted resolution in a different directory."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": ["src-1740488e9a78e215"],
   "finding": "A 21-page City traffic engineering presentation for an Atrisco Drive NW lane conversion, with speed, crash, access, volume and capacity analysis. Nothing else for this street exists in the inventory; every other Atrisco record is Atrisco Vista Boulevard, a different County road.",
   "recommended_action": "Approve and place on the corridor studies page, cross-listed to speed management. Label it a proposal, not a decision."},
  {"severity": "tractable-enactment",
   "affects": [CSR_CLEAN, "src-f8453bfbac0e5e6f", "src-e84ecf5f9ebbee36"],
   "finding": "C/S R-08-182, the 2009 capital programming resolution, plus two floor-substitute working tables. Enactment blocks blank. The programme it approves is published in depth and the enacted criteria resolution for the same bond programme is already on the site.",
   "recommended_action": "Resolve as a package, alongside district 9's R-14-82 and R-14-113 and district 4's M-14-5."},
  {"severity": "cross-cluster-confirmation",
   "affects": ["src-2bf84750e66b6baf", "src-a208f1c6551241b1", ENACTED_R1431],
   "finding": "One of the two adoption press releases misprints the bill number as E-14-31. The enacted Resolution R-2014-012, Council Bill R-14-31, recommended for addition from district 9, settles the number and the observance name.",
   "recommended_action": "None beyond the exclusions. Recorded because it is a worked example of two clusters checking each other."},
  {"severity": "discovery-lead",
   "affects": ["src-161f95b657b74333", "src-7c3f2ea6bda0d838", "src-2cf62271117cfd31"],
   "finding": "Three excluded records each name something the archive does not hold: a 2010 Traffic Mitigation Study for the Atrisco Drive area proposing an unbuilt roundabout at Hanover and Atrisco; Council Bill R-14-22 reserving $1.8 million in FY14 for fire and EMS pay; and the interim rules of decorum adopted for the 8 May 2014 special Council meeting.",
   "recommended_action": "Add all three to the discovery queue. The records that name them are excluded, so these leads exist only here."},
  {"severity": "convention",
   "affects": [],
   "finding": "Version pairs where neither member is retained have now appeared in three consecutive clusters and were handled two different ways.",
   "recommended_action": "Adopt the rule stated in status_convention: duplicate for byte-identical, excluded-with-prose for content-differing, superseded only where the canonical is retained or held for review."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "superseded": counts["superseded"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 13, "http_200": 13, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "method": "Full HTTP GET with a browser user agent on the raw file URL and on the inventoried /view URL, 2026-09-12.",
                "containers_verified": "12 genuine PDFs and one HTML collection page by leading bytes. Four PDFs have no usable text layer and were rendered."},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "superseded": superseded,
 "excluded": excluded,
 "archival_note": (f"The single approved record is a static PDF and is inventory-only until an R2 archive object "
                   f"exists for it and its public download, exact size, SHA-256, and authoritative-source provenance "
                   f"are verified. Archive footprint if authorized: {approved_bytes:,} bytes. Its slides are images "
                   f"with only a thin text layer, so full-text search will reach the slide titles but not the figures; "
                   f"that is a property of the City's original. Three further records are held at requires human "
                   f"review and would add more if resolved."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. The one superseded row carries a canonical_id that "
                      "is itself at requires human review in this batch. Three rows are requires human review and "
                      "belong to one legislative package, described in the legislative_package block. The one "
                      "approved row carries a title, a 20-to-50-word description, a date, a proposed_canonical_page, "
                      "a cross-listing and a caution. No row is a duplicate; this directory duplicates nothing in the "
                      "archive and nothing within itself. Sizes and checksums are first measurements; the inventory "
                      "held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
