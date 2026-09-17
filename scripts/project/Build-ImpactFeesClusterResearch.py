"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\impact-fees-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\impf\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/if/'

CAPITAL = 'content/city-data/capital-spending.md'
DEVPROC = 'content/development-land-use/development-process.md'

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


def A(i, title, desc, date, pages, evidence, why=None, extra=None, cross=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "description_word_count": len(desc.split()),
              "date": date, "pages": pages,
              "proposed_canonical_page": CAPITAL,
              "cross_listings": cross if cross is not None else [
                  {"page": DEVPROC, "reason": "Impact fees are charged through the development-review process and that page already carries the City fee schedules."}],
              "evidence": evidence})
    if why:
        r["why_retained"] = why
    if extra:
        r.update(extra)
    return r


approved = [
 A("src-f1d84e049627a759",
   "City of Albuquerque Impact Fees: Service Areas Composite Map and Fee Examples (printed March 15, 2005)",
   "The single-sheet City reference maps all four impact fee service-area systems, overlays them into a composite map, tabulates the total fee for sample residential, retail, office and industrial buildings by area, and states every reduction and waiver.",
   "2005-03-15", 1,
   ("One large-format sheet, rendered and read. It shows Public Safety Facilities in two service areas, Drainage "
    "Facilities in five, Park, Recreation, Trails and Open Space in seven, and Roadway Facilities in eight, then a "
    "composite overlay. The example table runs from $1,332 to $8,751 for a 2,000 square foot residence depending on "
    "area, and gives retail, office and industrial figures alongside. The footer reads \"Map Printed March 15, 2005\"."),
   why=("The most useful single document in the directory and the only one a non-specialist could read on its own. It "
        "makes the whole scheme legible in one sheet: which fee applies where, what it costs, and who pays nothing. "
        "The reductions panel records the jobs-housing balance adjustments, the Metropolitan Redevelopment Area "
        "exemption, the economic-development waivers under the Local Economic Development Act, and the complete "
        "affordable-housing waiver in Planned Village Development and Infill Development Zones."),
   extra={"caution": "The fee figures are 2005 and have been superseded many times. Any title must carry the March 2005 date so no reader takes the amounts as current."}),

 A("src-87a9372507474dbf",
   "Drainage Impact Fee Study, City of Albuquerque, Amended November 10, 2004",
   "The consultant study calculates the drainage facility costs of accommodating new development in Albuquerque and derives the recommended drainage impact fee for each service area, with the land use assumptions and cost basis behind the figures.",
   "2004-11-10", 33,
   "33 pages headed \"AMENDED 11/10/04, CITY OF ALBUQUERQUE, NEW MEXICO, Drainage Impact Fee Study\".",
   why="One of the three technical studies that justify the fees. Under the New Mexico Development Fees Act a fee must rest on a study of this kind, so these reports are the legal foundation of the charge, not background reading."),

 A("src-6a516acc2759d33c",
   "Park, Recreation, Trail and Open Space Costs of Accommodating New Development and Recommended Impact Fees, Amended November 12, 2004",
   "The consultant study calculates the park, recreation, trail and open space costs of accommodating new development across the seven service areas and derives the recommended impact fee for each, with the cost basis behind the figures.",
   "2004-11-12", 20,
   "20 pages headed \"AMENDED 11/12/04\".",
   why="The park and open space half of the fee justification; see the drainage study above."),

 A("src-24319f0b447bf4a2",
   "Public Safety Costs of Accommodating New Development and Recommended Public Safety Impact Fees, Amended November 10, 2004",
   "The consultant study calculates the police and fire facility costs of accommodating new development across the two public safety service areas and derives the recommended public safety impact fee for each.",
   "2004-11-10", 14,
   "14 pages headed \"AMENDED 11/10/04, PUBLIC SAFETY COSTS OF ACCOMMODATING NEW DEVELOPMENT AND RECOMMENDED PUBLIC SAFETY [IMPACT FEES]\".",
   why="The public safety third of the fee justification. See integration_flags: the matching roadway facilities study is missing from the directory even though the committee's comments on it survive."),

 A("src-9aaa5d2d38dc619f",
   "Proposed Impact Fees: Impact Fees Consultant Methodology Summaries",
   "The City Council document summarises the methodology each consultant used to derive Albuquerque's proposed impact fees, giving the common framework behind the four separate facility studies in plain summary form.",
   None, 8,
   "8 pages headed \"City of Albuquerque, City Council, Proposed Impact Fees, Impact Fees Consultant Methodology Summaries\".",
   why=("The bridge between the four technical studies. It is the one document that explains how the fees were "
        "calculated without requiring the reader to work through any individual study, and it covers roadway "
        "facilities, whose own study is missing from this directory."),
   extra={"dating_note": "No printed date. It belongs to the 2004 fee-adoption sequence; do not assert a date it does not carry."}),

 A("src-34b99a71ddc876f3",
   "Albuquerque Impact Fee Committee Comments on the Park, Recreation, Trails and Open Space Impact Fee Study, October 5, 2004",
   "The City Impact Fee Committee sets out its formal comments on the proposed park, recreation, trails and open space impact fee study, recording where the appointed committee agreed with the consultant's approach and where it did not.",
   "2004-10-05", 11,
   "11 pages headed \"City of Albuquerque Impact Fee Committee 10/05/04\".",
   why=("The statutory review body's own words on a fee it was appointed to scrutinise. A fee record that carries only "
        "the consultant's case is weaker than one that carries the committee's response to it.")),

 A("src-afc895972cb92c6b",
   "Albuquerque Impact Fee Committee Comments on the Public Safety Impact Fee Study",
   "The City Impact Fee Committee sets out its formal comments on the proposed public safety impact fee study, recording the appointed committee's response to the consultant's cost basis and recommended fee levels.",
   "2004-10", 8,
   ("8 pages headed \"City of Albuquerque Impact Fee Committee 10/05/04\". The filename records 10.18.04 while the "
    "page header reads 10/05/04, so the precise date is ambiguous on the document's own face."),
   why="Same ground as the parks comments above.",
   extra={"dating_caution": "Filename and page header disagree: 10.18.04 against 10/05/04. Date it to October 2004 and no more precisely unless the discrepancy is resolved."}),

 A("src-e483853343a12296",
   "Albuquerque Impact Fee Committee Comments on the Roadway Facilities Impact Fee Study, September 29, 2004",
   "The City Impact Fee Committee sets out its formal comments on the proposed roadway facilities impact fee study, the largest of the four fee systems at eight service areas, recording the appointed committee's response.",
   "2004-09-29", 8,
   "8 pages headed \"City of Albuquerque Impact Fee Committee 9/29/04\".",
   why=("Same ground as the other committee comments, with added weight: the roadway study these comments respond to is "
        "not in the directory, so this is the only surviving record in the inventory of what that study said and how "
        "the committee received it.")),
]


def R(i, draft_title, pages, question, why, evidence, extra=None):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why, "evidence": evidence})
    if extra:
        r.update(extra)
    return r


ORD_WHY = (
 "Enactment number blank, under the two standing checkpoint blockers. What distinguishes these four from the "
 "form-based code ordinances triaged in the artifact of the same date is that adoption here is not in doubt, only "
 "the enactment numbers are: Albuquerque demonstrably operates an impact fee programme, and the inventory already "
 "holds the evidence. The Development Review Services artifact of the same date recommends for addition the enacted "
 "Resolutions R-2012-100 and R-2013-115 amending the Component Capital Improvements Plan that governs impact fee "
 "spending, and the Impact Fee Credit Holder Summary of February 18, 2020 showing live credit balances up to "
 "$1,972,877. The question is which enactment numbers to cite, not whether the fees exist.")

ORDS = [
 ("src-783d52b1391b5633", "o-69fs2fin.pdf", "F/S(2) O-04-69", "Park, Recreation, Trails and Open Space Facilities Impact Fees", 30,
  "src-5595744160ab5aaf", "o-69fs2finappendix.pdf", 6),
 ("src-ffeaf7c21fd42639", "o-70fs2fin.pdf", "F/S(2) O-04-70", "Public Safety Facilities Impact Fees", 30,
  "src-c010f5feed1a9cf4", "o-70fs2finappendix.pdf", 4),
 ("src-5b42b0f430f5e999", "o-71fs2fin.pdf", "F/S(2) O-04-71", "Roadway Facilities Impact Fees", 29,
  "src-97720ceaf5b69931", "o-71fs2finappendix.pdf", 3),
 ("src-aceef0eda40266f9", "o-72fs2fin.pdf", "F/S(2) O-04-72", "Drainage Facilities Impact Fees", 29,
  "src-fb54d0a9b4bcb537", "o-72fs2finappendix.pdf", 4),
]

rhr = []
for oid, ofile, bill, subject, opages, aid, afile, apages in ORDS:
    rhr.append(R(oid,
      f"Council Bill {bill}: {subject} (floor substitute 2, final)",
      opages,
      f"Locate the enacted ordinance for {bill}. Decide all four together with their appendices.",
      ORD_WHY,
      f"{opages} pages, Sixteenth Council, sponsored by Michael Cadigan, enactment number blank.",
      extra={"appendix_record": aid,
             "pair_rule": "This ordinance and its appendix are one instrument. Decide and apply them together; the appendix is meaningless alone and the ordinance is incomplete without its fee schedule."}))
    rhr.append(R(aid,
      f"Appendices A and B to Council Bill {bill}: {subject} Cost Schedule",
      apages,
      f"Decide with {bill} above.",
      ("This is the fee schedule itself, the table of dollar amounts the ordinance would impose. It is held with its "
       "parent ordinance rather than separately: a published fee schedule detached from the instrument that sets it, "
       "and whose enactment is unconfirmed, would be the most misleading thing this directory could produce."),
      f"{apages} pages headed \"Appendix A, {bill}\" and \"Appendix B, {subject.upper()} IMPACT FEES COST SCHEDULE\".",
      extra={"parent_record": oid}))

rhr.append(R("src-c623d7f1fe27648d",
  "Council Bill F/S R-04-159: Establishing Interim Council Policy on Lower Impact Fees for Service Efficiencies, Reductions and Offsets Based on City Planning Policies, and Impact Fee Waivers for Affordable Housing",
  5,
  "Locate the enacted resolution F/S R-04-159; decide with the four fee ordinances.",
  ORD_WHY + (" This resolution matters more than its five pages suggest: the reductions and waivers it establishes are "
             "the ones printed on the retained 2005 service-area map, so the map already publishes the policy this "
             "instrument sets. If the resolution is never resolved the map still stands, but the two belong together."),
  "5 pages, Sixteenth Council, sponsored by Michael Cadigan, enactment number blank."))

duplicates = [
 {**row("src-3878d42af1890e08", "duplicate"),
  "title_for_reference": "Council Bill O-03-132: Adopting an Infrastructure and Growth Plan (second copy)",
  "pages": 5,
  "canonical_id": "src-68582bc4fe41fb4f",
  "canonical_url": "https://www.cabq.gov/council/documents/pgs/o-132fin.pdf",
  "canonical_state": "recommended requires human review in the planned-growth-strategy artifact of the same date, for its blank enactment number",
  "basis": ("The same Council Bill O-03-132, Fifteenth Council, sponsored by Michael Cadigan, published in both the "
            "impact-fees and Planned Growth Strategy directories. Normalized-token coverage is 1.0000 of this copy "
            "inside the other and 0.9916 the other way; the sequence ratio of 0.6964 and the fivefold size difference, "
            "126,466 bytes against 25,029, reflect different scan settings for the same five pages."),
  "hash_found_it": False,
  "note": ("The canonical is itself held at requires human review, which is deliberate: recording the copy relationship "
           "keeps it from being triaged twice, and the enactment question is answered once rather than in two "
           "directories. Integrate this artifact with the planned-growth-strategy artifact."),
  "cross_directory": True},
]

excluded = [
 {**row("src-3d2bc0752190c539", "excluded"),
  "title_for_reference": "Impact Fees Documents collection landing page",
  "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
  "category": "collection landing page",
  "usefulness": ("Parsed as part of this lane. It lists no roadway facilities impact fee study, which corroborates the "
                 "filename probes: that study is genuinely absent rather than merely unlinked.")},
]

rows = approved + rhr + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 19, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "impact-fees-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/if impact-fees cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The 2004 impact fee adoption record in the Albuquerque City Council document library at www.cabq.gov/council/documents/if.",
 "scope": "All 19 pending-review candidates in that directory. The directory also holds two records a prior lane set to requires human review, src-0e84cb9afce66afc and src-0d81ec5c9bdeb726; this artifact does not reclassify them but recommends a disposition for both.",
 "brief": "Check each candidate against the already-triaged CCIP resolutions and the O-04-9 land use assumptions ordinance, and against R2 objects already held.",
 "brief_finding": "The directory is a single coherent legislative package: four facility-specific impact fee ordinances each with its fee-schedule appendix, the consultant studies justifying three of the four fees, the appointed Impact Fee Committee's comments on all four, a methodology summary, and a service-area map. It connects directly to material triaged earlier in this run, which settles the usual enactment doubt in an unusual direction: adoption is certain and only the enactment numbers are missing. One thing is genuinely absent: the roadway facilities study, the largest of the four systems.",
 "method": "Fetched all 19 candidates and the two prior-lane requires-human-review records without touching shared inventory state, and recorded exact byte length and SHA-256 for each. Extracted text and read every document's masthead and title block. Rendered the one image-only file. Ran filename probes for a roadway facilities study under several plausible names. Compared the O-03-132 copy here against the copy in the Planned Growth Strategy directory by normalized text. Compared all checksums against the 1,612 checksummed inventory records, and checked the findings against the impact-fee records already recommended in the Development Review Services artifact.",
 "classification_only": True,
 "shared_state_written": [],
 "package_structure": {
  "four_fee_systems": [
   {"system": "Park, Recreation, Trails and Open Space", "service_areas": 7, "ordinance": "F/S(2) O-04-69",
    "ordinance_id": "src-783d52b1391b5633", "appendix_id": "src-5595744160ab5aaf",
    "study_id": "src-6a516acc2759d33c", "committee_comments_id": "src-34b99a71ddc876f3"},
   {"system": "Public Safety Facilities", "service_areas": 2, "ordinance": "F/S(2) O-04-70",
    "ordinance_id": "src-ffeaf7c21fd42639", "appendix_id": "src-c010f5feed1a9cf4",
    "study_id": "src-24319f0b447bf4a2", "committee_comments_id": "src-afc895972cb92c6b"},
   {"system": "Roadway Facilities", "service_areas": 8, "ordinance": "F/S(2) O-04-71",
    "ordinance_id": "src-5b42b0f430f5e999", "appendix_id": "src-97720ceaf5b69931",
    "study_id": None, "study_state": "ABSENT from the directory and from the inventory",
    "committee_comments_id": "src-e483853343a12296"},
   {"system": "Drainage Facilities", "service_areas": 5, "ordinance": "F/S(2) O-04-72",
    "ordinance_id": "src-aceef0eda40266f9", "appendix_id": "src-fb54d0a9b4bcb537",
    "study_id": "src-87a9372507474dbf", "committee_comments_id": "src-0e84cb9afce66afc"},
  ],
  "service_area_counts_source": "Read from the retained service-area map src-f1d84e049627a759, which shows each system's areas side by side.",
  "cross_cutting": {"methodology_summary": "src-9aaa5d2d38dc619f", "service_area_map": "src-f1d84e049627a759",
                    "interim_policy_resolution": "src-c623d7f1fe27648d",
                    "infrastructure_and_growth_plan_ordinance": "src-3878d42af1890e08, a second copy of the Planned Growth Strategy directory's O-03-132",
                    "committee_comments_on_component_cip": "src-0d81ec5c9bdeb726"},
 },
 "missing_study": {
  "what": "The roadway facilities impact fee study, the technical justification for the largest of the four systems at eight service areas.",
  "evidence_it_existed": ("The Impact Fee Committee's formal comments on it survive as src-e483853343a12296, dated "
                          "9/29/04 and eight pages long. A committee does not comment on a study that was never "
                          "written, and the other three systems each have a study in this directory."),
  "searched": ("Probed AmendedRoadwayImpactFeeReport.pdf and AmendedRoadwayFacilitiesImpactFeeReport.pdf, both 404. The "
               "City's own collection listing for this directory shows no roadway study either, so it is absent rather "
               "than merely unlinked. Nothing in the inventory holds it under any name."),
  "consequence": ("The archive would hold three of four fee justifications. Any published presentation must say which "
                  "one is missing rather than implying a complete set, and the retained methodology summary "
                  "src-9aaa5d2d38dc619f is the only document in the inventory that covers the roadway calculation at all."),
 },
 "enactment_question": {
  "finding": ("Nine records in this directory carry a blank enactment number, but unlike every other such group in this "
              "run the underlying adoption is not in doubt. Albuquerque operates an impact fee programme now."),
  "corroboration_already_in_the_inventory": [
   "The Development Review Services artifact of the same date recommends for addition enacted Resolution R-2012-100, which adopts the Component Capital Improvements Plan governing impact fee spending for 2012 to 2022.",
   "The same artifact recommends enacted Resolution R-2013-115, which amends that plan to restore two projects' impact fee credits.",
   "The same artifact recommends the Impact Fee Credit Holder Summary of February 18, 2020, which lists live credit balances of up to $1,972,877 against named holders.",
   "The Planned Growth Strategy artifact holds Council Bill O-04-9, adopting land use assumptions under the State Development Fees Act, which is the statutory precondition for charging the fees these four ordinances impose.",
  ],
  "consequence": ("The question for the human is which enactment numbers to cite, not whether the fees were adopted. "
                  "That makes this group the most tractable of the enactment-blocker groups raised in this run and a "
                  "good candidate to resolve first: four ordinances, one resolution, and a known-good outcome to "
                  "confirm against."),
 },
 "prior_lane_records": [
  {"id": "src-0e84cb9afce66afc",
   "what_it_is": "Albuquerque Impact Fee Committee comments on the drainage impact fee study, 10/05/04, 9 pages.",
   "recommended_disposition": ("approved for addition, on exactly the same ground as the three other committee comment "
                               "sets recommended here. It completes the set: comments survive for all four systems, and "
                               "holding three while leaving the fourth at requires human review would be arbitrary."),
   "note": "Claude did not modify this record."},
  {"id": "src-0d81ec5c9bdeb726",
   "what_it_is": "Impact Fee Committee memorandum to the Environmental Planning Commission on the Component Capital Improvement Program, dated 3.1.05, 2 pages.",
   "recommended_disposition": ("approved for addition. It is the committee's formal position on the Component Capital "
                               "Improvements Plan, and the Development Review Services artifact of the same date "
                               "recommends the two enacted resolutions that later amended that same plan. Retaining the "
                               "committee's 2005 comments alongside the 2012 and 2013 amendments gives the plan a "
                               "continuous record."),
   "note": "Claude did not modify this record."},
 ],
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_measurement": 1,
  "note": ("One relationship and hashing misses it. O-03-132 is published in this directory and in the Planned Growth "
           "Strategy directory under near-identical filenames, o132fin.pdf and o-132fin.pdf, at 126,466 and 25,029 "
           "bytes. Same five pages, same bill, different scan settings: coverage 1.0000 and 0.9916 with a sequence "
           "ratio of 0.6964. A fivefold size difference between two copies of one five-page bill is worth noting as a "
           "pattern: size is not evidence of difference in this archive."),
 },
 "integration_flags": [
  {"severity": "tractable-enactment-group",
   "affects": [r["id"] for r in rhr],
   "finding": "Nine requires-human-review rows, all blank enactment numbers, but with the adoption independently corroborated by four records already recommended elsewhere in this run.",
   "recommended_action": "Resolve this group before the form-based code or Planned Growth Strategy groups. Here the answer is known to exist; there it is not."},
  {"severity": "incomplete-set",
   "affects": ["src-e483853343a12296"],
   "finding": "The roadway facilities impact fee study is absent from the directory, the listing and the inventory, while the committee's comments on it survive.",
   "recommended_action": "Add it to the discovery queue and, if the three retained studies are ever published together, name the missing one."},
  {"severity": "currency",
   "affects": ["src-f1d84e049627a759"],
   "finding": "The service-area map prints fee amounts from March 2005 that have been superseded many times over.",
   "recommended_action": "Carry the March 2005 date in the title. The map's service-area geography and its reductions and waivers policy are the durable content; the dollar figures are historic."},
  {"severity": "pair-integrity",
   "affects": [o[0] for o in ORDS] + [o[5] for o in ORDS],
   "finding": "Each of the four ordinances and its appendix is one instrument. The appendix carries the fee schedule and the ordinance carries the legal text.",
   "recommended_action": "Apply each pair together and never publish an appendix alone. A fee schedule detached from an instrument whose enactment is unconfirmed is the most misleading output this directory could produce."},
  {"severity": "cross-artifact",
   "affects": ["src-3878d42af1890e08", "src-68582bc4fe41fb4f"],
   "finding": "O-03-132 is the same bill in this directory and in the Planned Growth Strategy directory; the canonical is held at requires human review there.",
   "recommended_action": "Integrate this artifact with the planned-growth-strategy artifact so the enactment question for O-03-132 is answered once."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "superseded": 0,
 },
 "link_check": {"checked": 21, "http_200": 21, "failed": 0,
                "probe_checked": 4, "probe_http_200": 0, "probe_http_404": 4,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 19 pending candidates and the two prior-lane requires-human-review records, plus four filename probes for a roadway facilities study.",
                "containers_verified": "20 genuine PDFs and one HTML collection page by leading bytes. One PDF has no text layer and was rendered."},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": f"All 8 approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, a small batch dominated by the 2,229,905-byte service-area map.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. The 8 approved rows each carry a title, a 20-to-50-word description, a proposed_canonical_page and a cross_listing; two carry a null or imprecise date with the reason stated, and neither may be given an asserted one. Nine rows are requires human review, and they form four ordinance-and-appendix pairs plus one resolution: each pair carries appendix_record and parent_record fields and must be applied together. The single duplicate row's canonical lies in the planned-growth-strategy artifact of the same date. Two records outside this artifact's classification scope have explicit recommended dispositions in prior_lane_records. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
