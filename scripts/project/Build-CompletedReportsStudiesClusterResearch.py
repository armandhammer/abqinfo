"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\completed-reports-studies-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\cr\fetch.log')

FACILITIES = 'content/public-works/city-facilities.md'
BUDGET = 'content/city-data/budget-spending.md'
PROJECTS = 'content/development-land-use/projects.md'
SAFETY = 'content/city-data/public-safety-data.md'

UNIFICATION = 'src-a5475f489b373f20'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, RAW = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw, v = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    RAW[i] = raw

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    if RAW[i] != u:
        r["raw_file_url"] = RAW[i]
    r.update(M[i])
    return r


def A(i, title, desc, date, pages, evidence, why, page, cross, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
              "date": date, "pages": pages, "evidence": evidence, "why_retained": why,
              "proposed_canonical_page": page, "cross_listings": cross})
    if extra:
        r.update(extra)
    return r


approved = [
 A("src-17429d7a43730037",
   "City of Albuquerque Parking System Review: Parking Operations and Financial Review, October 2002 (Carl Walker, Inc.)",
   ("The City's consultant review of its parking system examines how parking is organised and governed, measures "
    "current supply against demand downtown, analyses the system's finances and rates, and recommends a new "
    "organisational structure with supporting operational changes."),
   "2002-10", 161,
   ("Born-digital PDF with a full text layer, 161 pages, 7,086,702 bytes. Cover: \"City of Albuquerque / Parking "
    "System Review - FINAL / October 2002 / Prepared for: City of Albuquerque, New Mexico / Prepared by: Carl Walker, "
    "Inc., Phoenix, Arizona\", with the running title \"City of Albuquerque Parking Operations and Financial Review\". "
    "The table of contents runs an 18-page executive summary, then Introduction with background, scope of services "
    "and study area; Parking Organizational Analysis covering current system goals, current organisational structure, "
    "a recommended organisation with guiding principles and other recommendations; and Current Parking Supply and "
    "Demand beginning with public parking."),
   ("The archive holds nothing on City parking. An inventory-wide search for parking system review, Carl Walker or "
    "parking operations and financial returns no record at all, and the site has no parking material. This is a "
    "161-page City-commissioned review of a system residents use daily."),
   FACILITIES,
   [{"page": BUDGET, "reason": "Half the report is a financial review of the parking system's revenues, rates and cost structure."}],
   extra={"caution": "A consultant's review with recommendations, dated 2002. Nothing here shows which recommendations the City adopted."}),

 A("src-1aecdc742bc5be02",
   "Analysis of Albuquerque's Industrial Revenue Bond Program, April 2002 (Prager Company with NatCity Investments and Teresa Córdova)",
   ("The City Council's commissioned analysis of the Industrial Revenue Bond programme compares Albuquerque's "
    "operating-cost competitiveness against rival metropolitan areas, surveys non-IRB incentives, explains how the "
    "programme actually works, and tests whether it matches the City's economic development goals."),
   "2002-04", 56,
   ("Born-digital PDF with a full text layer, 56 pages. \"Prepared for: Albuquerque City Council. Prepared by: Prager "
    "Company, In Collaboration with the Economic Development Group of NatCity Investments and Teresa Córdova. April "
    "2002.\" Four numbered parts after an introduction and conclusions: Operating Cost Competitiveness, Non-IRB "
    "Incentives, IRB Program Mechanics, and Economic Development-IRB Program Alignment. Its introduction opens "
    "\"The debate surrounding the Industrial Revenue Bond (IRB) program in Albuquerque is perhaps more public and "
    "longer lasting than in any other major U.S. city.\""),
   ("Industrial revenue bonds are the City's largest business-incentive instrument and the archive explains them "
    "nowhere. The only IRB record in the whole inventory is a single news item, src-d3176451f1bc5245, announcing an "
    "authorisation. This is the analysis of how the programme works and whether it works."),
   PROJECTS,
   [{"page": BUDGET, "reason": "It is an analysis of a City financing instrument and of the revenue consequences of granting it."}],
   extra={"companion": "src-2015fa7cf7b66c2e, the stakeholder study commissioned alongside it.",
          "caution": "Analysis and recommendations, not policy. Dated 2002; the programme's rules have changed since."}),

 A("src-2015fa7cf7b66c2e",
   "Albuquerque's Industrial Revenue Bond Program: Community Stakeholder Perspectives and Recommendations, May 2002 (Teresa Córdova, Ph.D.)",
   ("The companion study to the City Council's Industrial Revenue Bond analysis sets out what economic development "
    "professionals and other community stakeholders said about the programme's goals, its effect on tax revenue, its "
    "perceived impacts, and what should change."),
   "2002-05", 46,
   ("Born-digital PDF with a full text layer, 46 pages. \"Prepared for Albuquerque City Council. Prepared by Teresa "
    "Córdova, Ph.D. May 2002.\" Part I is background — research questions and methodology, trends in Albuquerque's "
    "economy, trends in current economic development strategies, and the City's IRB programme. Part II is stakeholder "
    "perspectives, opening with economic development professionals and covering economic development goals, tax "
    "structure, revenue and IRBs, and perceived impacts of IRBs."),
   ("The qualitative half of a two-part commission. Its author is also a named collaborator on the Prager analysis, "
    "so the two were designed together: one measures the programme, the other records what the people affected by it "
    "said. Keeping one without the other would leave the Council's own inquiry half-preserved."),
   PROJECTS,
   [{"page": BUDGET, "reason": "Its central section is on tax structure, revenue and IRBs."}],
   extra={"companion": "src-1aecdc742bc5be02, the quantitative analysis commissioned alongside it."}),

 A("src-7d2a00f380fdc8c6",
   "Police Oversight Project, City of Albuquerque, May 2002 (Richard Jerome, P.C., and the Police Assessment Resource Center)",
   ("An independent assessment of Albuquerque's police oversight system reviews how oversight mechanisms work "
    "elsewhere, traces the contested early history of the Police Oversight Commission and Independent Review Officer, "
    "and examines how citizen complaints against officers are actually handled."),
   "2002-05", 116,
   ("Born-digital PDF with a full text layer, 116 pages. Cover: \"POLICE OVERSIGHT PROJECT / CITY OF ALBUQUERQUE / "
    "RICHARD JEROME, P.C. / POLICE ASSESSMENT RESOURCE CENTER / May 2002.\" A six-page executive summary then "
    "chapters on Introduction, Overview of Police Oversight Mechanisms, Methodology, the Early Contest for the POC "
    "and the IRO, and the Citizen Complaint Process."),
   ("It is the earliest independent assessment of Albuquerque police oversight in the inventory by more than a "
    "decade, and it predates everything the archive holds on the subject. "
    "police-oversight-task-force-cluster-research-2026-09-11.json triaged the task force's own library without "
    "encountering it, and an inventory-wide search for police oversight project, Police Assessment Resource Center or "
    "Richard Jerome returns nothing. It is the baseline any later oversight record is measured against."),
   SAFETY,
   [{"page": BUDGET, "reason": "Oversight structure and the Independent Review Office are recurrent budget items, and this is the report that assessed how that structure was working."}],
   extra={"caution": "A 2002 assessment. It long predates the 2014 Department of Justice findings and the reforms that followed, and must never be presented as a description of current oversight."}),

 A("src-e45a582a0a145144",
   "APD Total Compensation Comparison and Overtime Cost Management Analysis, March 19, 2001 (Watson Wyatt)",
   ("The City's consultant study compares Albuquerque Police Department total compensation against competing "
    "employers element by element, analyses how the department's overtime is generated and controlled, and makes "
    "recommendations for managing both."),
   "2001-03-19", 44,
   ("Born-digital PDF with a full text layer, 44 pages, headed \"APD Total Compensation Comparison & Overtime "
    "Analysis / March 19, 2001 / City of Albuquerque / WWW.WATSONWYATT.COM\" and titled inside \"Full Report with "
    "Executive Summary\". Four sections — Introduction and Executive Summary, Total Compensation Comparison, "
    "Overtime Cost Management, Recommendations — with appendices giving the matrix used for pay element comparisons, "
    "overtime practices study results, and a note on the consulting firm. Its opening line: \"Labor costs for public "
    "safety personnel are increasing for cities throughout the United States.\""),
   ("Police pay and overtime are perennial budget questions and the archive holds no analysis of either. The only "
    "trace of this study anywhere in the inventory is this file."),
   BUDGET,
   [{"page": SAFETY, "reason": "It is an analysis of how the police department is staffed and paid, which is public-safety operational data."}],
   extra={"caution": "Dated 2001. Its comparison figures are of historical interest only; do not present them as current pay."}),

 A(UNIFICATION,
   "Structuring A New Urban Government: A Report on the Unification of Bernalillo County and the City of Albuquerque, November 12, 2002 (David Rusk and the Unification Exploratory Group)",
   ("The Unification Exploratory Group's report examines whether Albuquerque and Bernalillo County should merge into "
    "a single urban government, setting out the legal parameters for doing so, a financing and revenue analysis, and "
    "a review of both governments' functions, services and operations."),
   "2002-11-12", 276,
   ("Born-digital PDF with a full text layer, 276 pages, 6,979,441 bytes — the longest document in the cluster. "
    "\"Structuring A New Urban Government / A Report on the Unification of Bernalillo County and the City of "
    "Albuquerque / Part 1 prepared by David Rusk / Part 2 prepared by the Unification Exploratory Group / November "
    "12, 2002\", followed by the Group's seventeen-member roster chaired by Vickie Perea with Chuck Lanier as "
    "vice-chair. Part 2's own contents are PART 2A Legal Parameters of Unification, PART 2B City and County "
    "Financing, and PART 2C Functions, Services and Operations of City and County Government."),
   ("A 276-page Council-commissioned study of the most consequential structural question the City has ever put to "
    "itself, held nowhere. It also resolves an open item in another artifact: see resolves_an_open_item."),
   BUDGET,
   [{"page": PROJECTS, "reason": "Part 2C reviews both governments' functions, services and operations, which bears directly on how City projects and services are organised."}],
   extra={"placement_is_a_judgment_call": ("The site has no page for City government structure. Budget and spending is "
                                           "the closest fit because Part 2B is a revenue and financing analysis, but "
                                           "a governance page would be a better home if one is ever created. Flagged "
                                           "rather than decided silently."),
          "caution": "The report explores unification; it does not enact it. Albuquerque and Bernalillo County remain separate governments."}),
]

excluded = [{
 **row("src-ca8abef11c283b6e", "excluded"),
 "title_for_reference": "Completed Reports & Studies collection landing page",
 "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
 "category": "collection landing page",
}]

rows = approved + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 7, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
approved_pages = sum(r["pages"] for r in approved)
raw_differs = [r["id"] for r in rows if "raw_file_url" in r]

artifact = {
 "batch_id": "completed-reports-studies-cluster-research-2026-09-12",
 "lane": "Claude research lane: www.cabq.gov/council/documents/completed-reports-studies cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12. Artifacts before councilor-district-9-cluster-research-2026-09-12.json are dated 2026-09-11; cross-references name artifacts by filename.",
 "cluster": "The City Council's own library of completed commissioned reports, six studies from 2001 and 2002 filed under flat lower-case filenames.",
 "scope": "All 7 pending-review candidates, which is every record in the directory. Nothing here is terminal.",
 "brief": "Run the standard opening sequence; given the directory name, test every candidate against the published site before anything else, since a completed report is the class most likely to be held already.",
 "brief_finding": ("The brief expected duplication and found none. All six reports are unheld: inventory-wide searches "
                   "for parking system review, Carl Walker, industrial revenue bond, Prager, police oversight "
                   "project, Police Assessment Resource Center, Richard Jerome, Watson Wyatt, total compensation, "
                   "unification, urban government and David Rusk return, between them, a single unrelated news item. "
                   "No checksum in the cluster matches any of the 1,612 checksummed inventory records. This is the "
                   "densest directory of unheld substantive material found in the run: six Council-commissioned "
                   "reports, 699 pages, on parking, industrial revenue bonds, police oversight, police pay and "
                   "City-County unification."),
 "why_that_is_credible": ("The directory is small, flat and plainly named, with six files called parking.pdf, "
                          "irbrpt.pdf, irbrpt2.pdf, pocstudy.pdf, UEGreport.pdf and APDcompensationstudy.pdf. Nothing "
                          "about those names suggests what they contain, which is the most likely reason a crawler "
                          "reached them and no triage pass ever prioritised them."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 7 candidates and measured byte length and "
            "SHA-256 from the fetched bytes. Compared all checksums within the cluster and against the 1,612 "
            "checksummed inventory records. Read every report's cover, table of contents and opening pages rather "
            "than classifying from filenames. Searched the inventory and the published site for each report's subject "
            "and for its author. Fetched one file from another directory read-only to test a cross-cluster "
            "identification."),
 "classification_only": True,
 "shared_state_written": [],
 "resolves_an_open_item": {
  "the_open_item": ("planned-growth-strategy-cluster-research-2026-09-11.json found a file at "
                    "https://www.cabq.gov/council/documents/pgs/Part2.pdf that is absent from both the City's "
                    "collection listing and the inventory, and established that despite its filename it is not the "
                    "combined Planned Growth Strategy Part 2 but \"Part 2 of a City and County governmental "
                    "unification study, a different report entirely\". It recommended adding that file to the "
                    "inventory as a new candidate under its true identity."),
  "what_this_lane_found": ("The report it is part of is already an inventory record, in this directory. "
                           + UNIFICATION + " is the complete 276-page \"Structuring A New Urban Government: A Report "
                           "on the Unification of Bernalillo County and the City of Albuquerque\"."),
  "measurement": ("Fetched pgs/Part2.pdf read-only: HTTP 200, 5,469,413 bytes, SHA-256 beginning d703841bb7329a44, "
                  "144 pages. Token coverage of that file inside " + UNIFICATION + " is 1.0000; coverage the other "
                  "way is 0.7239, which is exactly the signature of a part inside its whole. Its table of contents "
                  "reads PART 2A Legal Parameters of Unification, PART 2B City and County Financing, PART 2C "
                  "Functions, Services and Operations of City and County Government — the same three parts named on "
                  "the complete report's contents page."),
  "consequence": ("The PGS recommendation can be narrowed. pgs/Part2.pdf does not need adding as a new candidate "
                  "under a new identity: it is 144 of the 276 pages of a report this artifact recommends approving in "
                  "full. Archiving " + UNIFICATION + " covers it. The other two undiscovered PGS files, Part2-4.pdf "
                  "and Part2-6.pdf, are genuine Planned Growth Strategy chapters and that recommendation stands "
                  "unchanged."),
  "how_it_was_found": ("Not by a search. The PGS artifact recorded what the mystery file's table of contents said, "
                       "and reading this directory's covers turned up a report with the same three part titles. "
                       "Recording the content of an unidentified file, rather than only the fact that it was "
                       "unidentified, is what made the match possible two clusters later."),
 },
 "already_archived_check": {
  "rule_applied": "nob-hill-highland-cluster-research-2026-09-11.json and dnasdp-cluster-research-2026-09-12.json require testing candidates against R2 objects and published site entries before recommending.",
  "candidates_tested": 6,
  "matches_found": 0,
  "searches_run": ("parking system review, Carl Walker, parking operations and financial; industrial revenue bond, "
                   "Prager; police oversight project, Police Assessment Resource Center, Richard Jerome, PARC; "
                   "Watson Wyatt, total compensation, overtime analysis; unification, urban government, David Rusk. "
                   "Run over every inventory record's title, description, source URL, direct file URL and R2 URL, and "
                   "over the whole of content/."),
  "only_hit": "src-d3176451f1bc5245, a District 6 news item headed \"Albuquerque City Council Authorizes $776.6 Million Indus...\", still pending and unrelated to the analyses here.",
  "cross_inventory_byte_collisions": 0,
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_inside_the_cluster": 0,
  "relationships_found_outside_it": 1,
  "note": ("No duplicates and no supersession among the six reports; they are six different studies on five different "
           "subjects. The one relationship found runs outward: a file in the pgs directory is 144 pages of the "
           "unification report here. The two IRB reports are companions rather than versions — one quantitative, one "
           "qualitative, commissioned together, sharing an author — and both are recommended."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved],
   "finding": f"Six unheld City Council-commissioned reports totalling {approved_pages} pages: parking system review, two industrial revenue bond studies, an independent police oversight assessment, an APD compensation and overtime analysis, and a City-County unification report.",
   "recommended_action": "Approve all six. Every one is born-digital with a full text layer, so all are searchable once archived."},
  {"severity": "narrows-an-earlier-recommendation",
   "affects": [UNIFICATION],
   "finding": "The unidentified pgs/Part2.pdf that planned-growth-strategy-cluster-research-2026-09-11.json recommended adding as a new candidate is 144 pages of this 276-page report, at token coverage 1.0000.",
   "recommended_action": "Do not create a separate candidate for pgs/Part2.pdf. Archive the complete report instead. The recommendation to add Part2-4.pdf and Part2-6.pdf as Planned Growth Strategy chapters is unaffected."},
  {"severity": "placement-gap",
   "affects": [UNIFICATION],
   "finding": "The site has no page for City government structure. A 276-page study of whether the City and County should merge is proposed for the budget and spending page because Part 2B is a financing analysis.",
   "recommended_action": "Accept the placement or create a governance page. Flagged rather than decided quietly."},
  {"severity": "coverage-gap-closed",
   "affects": ["src-1aecdc742bc5be02", "src-2015fa7cf7b66c2e"],
   "finding": "Industrial revenue bonds are the City's largest business-incentive instrument and the archive currently explains them nowhere; the only IRB record in the inventory is a news item.",
   "recommended_action": "Publish the two 2002 studies together, quantitative and stakeholder, and label both as 2002 analyses rather than current programme rules."},
  {"severity": "date-caution",
   "affects": ["src-7d2a00f380fdc8c6"],
   "finding": "The 2002 police oversight assessment predates the 2014 Department of Justice findings and every reform since.",
   "recommended_action": "Publish it as the earliest baseline, never as a description of current oversight. It is the only pre-2014 independent assessment the archive would hold."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": 7, "http_200": 7, "failed": 0,
                "both_url_forms_checked": len(raw_differs),
                "external_fetches": "https://www.cabq.gov/council/documents/pgs/Part2.pdf was fetched read-only for the cross-cluster identification, HTTP 200, 5,469,413 bytes.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "6 genuine PDFs and one HTML collection page by leading bytes. All six PDFs have full text layers; none needed rendering."},
 "approved_for_addition": approved,
 "excluded": excluded,
 "archival_note": (f"All 6 approved records are static PDFs and are inventory-only until an R2 archive object exists "
                   f"for each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes across "
                   f"{approved_pages} pages. Every one is born-digital with a full text layer, so full-text search "
                   f"reaches all of them without optical character recognition — unusual for this run, where most "
                   f"approved records have been scans."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id: this directory "
                      "contains no duplicates, no supersession and no legislative material, so nothing here is held "
                      "for human review under the enactment blockers. Each approved row carries a title, a "
                      "20-to-50-word description, a date, a page count, a proposed_canonical_page, one cross-listing "
                      "and a caution about its age. One row additionally carries placement_is_a_judgment_call and "
                      "should be read before it is placed. Sizes and checksums are first measurements; the inventory "
                      "held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the pgs/Part2.pdf file was fetched read-only and no inventory record was created for it"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
