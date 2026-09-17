"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Second slice of the municipaldevelopment/documents lane: the
bid and procurement series.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\municipaldevelopment-procurement-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\proc\fetch.log')

DEVPROC = 'content/development-land-use/development-process.md'
CAPITAL = 'content/city-data/capital-spending.md'

RULES = 'src-230753126ba3bbf7'   # validated + R2 + published consultant compensation rules

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

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
        v = d.get(b)
        if isinstance(v, list):
            for r in v:
                if isinstance(r, dict) and r.get('id'):
                    PRIOR.add(r['id'])
assert not (set(M) & PRIOR), sorted(set(M) & PRIOR)

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML', '7b5c7274': 'RTF', 'd0cf11e0': 'DOC'}

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither. Container verified by leading bytes, not by extension.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


approved = [
 {**row("src-b3d8dcb56e000437", "approved for addition"),
  "title": "City of Albuquerque On-Call Engineering Services Agreement (standard form, revision 10-04-17)",
  "description": ("The City's standard professional services contract for citywide on-call engineering sets out in "
                  "fourteen articles what the engineer must do, how work is authorised and paid, who holds "
                  "responsible charge, and the terms the City contracts on."),
  "date": "2017-10-04", "pages": 16,
  "evidence": ("Born-digital PDF with a full text layer, 16 pages, footed \"Engineering Services; Proj No: XXXX ... "
               "Rev. 10-04-17\". The parties block is filled with placeholders — \"Your Firm Name Here, Inc.\", \"123 "
               "ABC Street\", \"Jane Engineer, PE\" — which is what identifies it as the blank standard form rather "
               "than an executed contract. Its recitals require Council approval of the Mayor's recommendation, "
               "record that funding is appropriated to the Capital Implementation Program, cite Section 61-23-21B "
               "NMSA 1978 for signing authority, and require a named registered Project Engineer in responsible "
               "charge under the Engineering and Surveying Practice Act, Sections 61-23-1 et seq. Fourteen numbered "
               "articles, I to XIV."),
  "why_retained": ("It is a standard, not a solicitation. The archive already publishes exactly this class of record: "
                   + RULES + ", the Rules and Regulations Governing Compensation for Consulting Engineers, Architects "
                   "and Landscape Architects, is validated, R2-archived and live on "
                   "content/development-land-use/development-process.md. That record sets how consultants are paid; "
                   "this one sets what they sign. The archive has the first half and not the second."),
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": CAPITAL, "reason": "Its recitals tie the funding for every such engagement to the Capital Implementation Program, whose bond records that page publishes."}],
  "caution": ("A blank template, not a contract anyone signed, and dated by its own revision stamp rather than by "
              "adoption. Describe it as the City's standard form as posted, and note that later revisions may exist."),
  "description_word_count": 0},

 {**row("src-4952ea05cd055792", "approved for addition"),
  "title": "City of Albuquerque On-Call Landscape Architectural Services Agreement (standard form)",
  "description": ("The City's standard professional services contract for citywide on-call landscape architectural "
                  "work, carrying the same fourteen-article structure as the engineering form with the obligations "
                  "and professional requirements specific to landscape architects."),
  "date": None, "pages": 17,
  "evidence": ("Born-digital PDF with a full text layer, 17 pages, headed \"CITY OF ALBUQUERQUE / ON-CALL LANDSCAPE "
               "ARCHITECTURAL SERVICES AGREEMENT\" over \"City Clerk Contract No. ____________\" and \"Project "
               "Number 7859\". Fourteen numbered articles, I to XIV."),
  "why_retained": ("The companion standard form for the other profession the City retains on call. The published "
                   "compensation rules cover engineers, architects and landscape architects together, so keeping one "
                   "contract form and not the other would leave that rule half-illustrated."),
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": CAPITAL, "reason": "Same Capital Implementation Program funding recital as the engineering form."}],
  "relationship": ("Not a duplicate of the engineering form: normalized-text ratio 0.9597 with token coverage 0.9767 "
                   "and 0.9691. They share boilerplate and differ in the professional-practice provisions and the "
                   "scope of services, which is what makes them two instruments rather than two copies."),
  "caution": "A blank template. It carries no revision stamp, so it cannot be dated from its face.",
  "description_word_count": 0},
]
for r in approved:
    r["description_word_count"] = len(r["description"].split())

# ------------------------------------------------------------------ excluded
SOLICIT = ("Transactional solicitation paperwork for one procurement: it advertises, clarifies or closes a single "
           "competition and records no City standard, decision, study or programme. Once the competition is over it "
           "documents nothing a resident or a later reader can use.")

CLASS = {
 "legal advertisement": SOLICIT + " These are the newspaper notices of a Request for Proposals, headed \"City of "
                                  "Albuquerque / Notice of Requests for Proposals\" and giving the due date and the "
                                  "Selection Advisory Committee office address.",
 "Selection Advisory Committee request for proposals": SOLICIT + " These are the full RFP notices issued by the "
                                                                 "Selection Advisory Committee for a named project "
                                                                 "number.",
 "solicitation addendum": SOLICIT + " An addendum modifies the contract documents mid-competition and is meaningless "
                                    "without the solicitation it amends.",
 "solicitation questions and answers": SOLICIT + " A question-and-answer sheet closing out bidder queries for one "
                                                 "solicitation.",
 "bid package": SOLICIT + " A bid package is the instructions-to-bidders volume for one competition.",
 "procurement system guide": ("An access and data-entry guide for the City's ProCore capital project management "
                              "system: how to request a login, set a password and file a project request form. "
                              "Internal system instructions, superseded whenever the system changes."),
 "procurement training deck": ("A slide deck used to train City staff or vendors on a procurement process. "
                               "Presentations are excluded throughout this run; the process itself is recorded in the "
                               "Public Purchases Ordinance and the standard forms."),
 "on-call scope sheet": ("An informational sheet listing the scope of work covered by a group of on-call project "
                         "numbers, issued to prospective proposers alongside a solicitation."),
}

ROWS = [
 # legal advertisements
 ("src-44fcb8867fda3754", "Legal advertisement, Project 5001.07: hydrology consultants", "legal advertisement"),
 ("src-7cd1458740cafd26", "Legal advertisement, Project 6353.93 (not federally funded)", "legal advertisement"),
 ("src-1f29a11262609ad0", "Legal advertisement, Project 7232", "legal advertisement"),
 ("src-a52b9b8fa41d9b7f", "Legal advertisement, Project 7260.82: in-line baggage system", "legal advertisement"),
 ("src-4d5aa34eba1972cd", "Legal advertisement, Project 7303.99 (not federally funded)", "legal advertisement"),
 ("src-22f0955ecab55307", "Legal advertisement, Project 7600.00 (federally funded)", "legal advertisement"),
 ("src-138081a63a9c5c60", "Legal advertisement, Project 7650.00: citywide on-call environmental engineering services (federally funded)", "legal advertisement"),
 ("src-67d1fd2ed0d1370e", "Legal advertisement, Project 7680.92 (federally funded)", "legal advertisement"),
 ("src-4c87d4d2e526a5f5", "Legal advertisement, Project 7782.92 (not federally funded)", "legal advertisement"),
 ("src-1e8a3e177f1b8c3c", "Legal advertisement, Project 8028.02 (not federally funded)", "legal advertisement"),
 ("src-6b5efb04b2ac55db", "Legal advertisement, September 6, 2023 (not federally funded)", "legal advertisement"),
 ("src-56d271177d8644f1", "Legal advertisement, Project 7700.99 (not federally funded)", "legal advertisement"),
 ("src-b48e6f5b559b448d", "Legal advertisement, corrected amount", "legal advertisement"),
 ("src-43d31c1641b70425", "Legal advertisement with legal markups, June 16, 2020 (not federally funded)", "legal advertisement"),
 ("src-8abf13d97c97fa56", "Legal advertisement with legal markups, June 16, 2020 (federally funded)", "legal advertisement"),
 ("src-4a2800924218bb64", "Legal advertisement, Project 150.02, revised June 30, 2025", "legal advertisement"),
 # SAC RFPs
 ("src-7e766274088552f2", "Request for proposals 4383.91: engineering consultants for Unser Boulevard improvements", "Selection Advisory Committee request for proposals"),
 ("src-d9de6b7a86e9f5dd", "Request for proposals 6135.82: engineering services for regional transportation management", "Selection Advisory Committee request for proposals"),
 ("src-269e817ec3e07a00", "Request for proposals 6588.92: engineering consultants for Ladera Drive improvements", "Selection Advisory Committee request for proposals"),
 ("src-11786528ccb1a960", "Request for proposals 7006.92: architectural consultants for the Edith transfer station", "Selection Advisory Committee request for proposals"),
 ("src-eed7d21ed0756088", "Request for proposals 7023.02: architectural consultants for the Westside multigenerational centre", "Selection Advisory Committee request for proposals"),
 ("src-1ecbfbd102bb54df", "Request for proposals 7222.00: engineering services for the Aviation Department", "Selection Advisory Committee request for proposals"),
 ("src-724a07fd7a5ae48b", "Request for proposals 7616.94: architectural consultants for ABQ RIDE Central and Unser transit facilities", "Selection Advisory Committee request for proposals"),
 ("src-6407b96c9c391226", "Request for proposals 7700.91: architectural services for design consultant services", "Selection Advisory Committee request for proposals"),
 ("src-1cf31a5ef4b3ee2d", "Request for proposals 7852: engineering consultants for citywide on-call engineering services", "Selection Advisory Committee request for proposals"),
 ("src-e67766e4b3c596b7", "Request for proposals 7853.00: landscape architectural consultants for citywide on-call landscape services", "Selection Advisory Committee request for proposals"),
 ("src-762a80b52c1351f4", "Request for proposals 7854.00: engineering consultants for citywide on-call engineering", "Selection Advisory Committee request for proposals"),
 ("src-99a3dfa74f6094b0", "Request for proposals 7909.00: engineering consultants for traffic signal expansion projects", "Selection Advisory Committee request for proposals"),
 ("src-6f3556bc08a66437", "Request for proposals 6200: engineering consultants for citywide engineering services", "Selection Advisory Committee request for proposals"),
 ("src-4cb4d028b6c8902c", "Request for proposals 7525: citywide on-call engineering services, transportation", "Selection Advisory Committee request for proposals"),
 ("src-0880f378bceeef60", "Request for proposals 7703.92: Bellamah extension", "Selection Advisory Committee request for proposals"),
 ("src-df1d20d7cb45b2cb", "Request for proposals 7580.91: Rail Yards", "Selection Advisory Committee request for proposals"),
 ("src-e3c045d87e4ad0b3", "Request for proposals: City and County escalator modernisation, final, November 1, 2012", "Selection Advisory Committee request for proposals"),
 ("src-3783e58f9cc98436", "Request for proposals: City and County escalators, due December 4", "Selection Advisory Committee request for proposals"),
 ("src-26c831b7fa9ce71a", "Notice of requests for proposals: citywide on-call architectural services, Project 0137.02, due July 2, 2025", "Selection Advisory Committee request for proposals"),
 ("src-a234e825f99c57c2", "On-call architectural services, DEII, January 24, 2024", "Selection Advisory Committee request for proposals"),
 ("src-503b2193335553d0", "On-call architectural services request for proposals for the Aviation Department, MF-3600", "Selection Advisory Committee request for proposals"),
 ("src-de22d63276c9444b", "Request for proposals: Choke Cherry Trail, Farmington, February 22, 2023", "Selection Advisory Committee request for proposals"),
 ("src-af00716d1a23515e", "Request for proposals: additional information", "Selection Advisory Committee request for proposals"),
 # addenda, Q&A, bid packages
 ("src-598b98e539779b39", "Addendum No. 1, Project 7580.91, November 30, 2012: City and County escalators", "solicitation addendum"),
 ("src-f88ccd57854268b2", "Questions and answers for solicitation 7260.82, April 22, 2024: architectural consultants for the in-line baggage system at the Albuquerque Sunport", "solicitation questions and answers"),
 ("src-7b8344b252999ea6", "Request for proposals questions, Project 150.02: traffic engineering on-call for Neighborhood Traffic Management Program traffic calming", "solicitation questions and answers"),
 ("src-8cf867d1266f19b3", "Bid package, 1009 Edith: RFP RPD-EDITH24-GGB, proposals due March 6, 2024", "bid package"),
 ("src-822807e73efdf2c7", "Bid package: Hood Mesa, Farmington", "bid package"),
 # guides, training, scope sheets
 ("src-2cd754000890e4d3", "2025 general obligation bond project request form job aid (ProCore access)", "procurement system guide"),
 ("src-bc6e6f5afa6e0401", "2027 general obligation bond project request form creation guide (ProCore)", "procurement system guide"),
 ("src-9195bc96ec027a98", "2027 project request form training, full deck", "procurement training deck"),
 ("src-ed212e95885cb4b3", "2027 project request form training, update deck", "procurement training deck"),
 ("src-7455b688bae320f4", "Doing business with the City's Central Purchasing Division", "procurement training deck"),
 ("src-51808dace3a91a14", "2022 citywide on-call engineering services informational sheet, Projects 7225.00, 7216.00 and 7217.00", "on-call scope sheet"),
]

excluded = []
for i, what, cat in ROWS:
    r = row(i, "excluded")
    r.update({"title_for_reference": what, "exclusion_reason": CLASS[cat], "category": cat})
    excluded.append(r)

EXTRA = {
 "src-598b98e539779b39": {"tested_not_assumed": ("Image-only with three bytes of extractable text; page 1 was rendered "
                                                 "and read. Headed CITY OF ALBUQUERQUE / DEPARTMENT OF MUNICIPAL "
                                                 "DEVELOPMENT, ADDENDUM NO. 1, dated November 30, 2012, Project No. "
                                                 "7580.91, addressed TO: ALL BIDDERS OF RECORD, and stating that it "
                                                 "\"forms a part of the contract Documents and modifies or supplements "
                                                 "the Project Manual or the Drawings\"."),
                          "note": "Its one clarification asks for the load weight capacity at the top and bottom of the escalator and records that the City will provide structural drawings S1 through S37."},
 "src-44fcb8867fda3754": {"tested_not_assumed": ("An RTF, not a PDF — leading bytes 7b5c7274. Extracted by stripping "
                                                 "RTF control words rather than with pdftotext. The body is a "
                                                 "Selection Advisory Committee notice seeking \"Proposals from "
                                                 "professional\" consultants for HYDROLOGY work, with a Project "
                                                 "Description and the Capital Implementation Program Division office "
                                                 "at Civic Plaza as the delivery address.")},
 "src-7455b688bae320f4": {"content": ("It explains that the Purchasing Division \"serves as the Central Purchasing "
                                      "Office for the City of Albuquerque\" for all departments' goods, services and "
                                      "professional or technical needs, and that the City is \"home rule\" and "
                                      "governed by the Public Purchases Ordinance, 5-5-1 et seq."),
                          "discovery_lead": "The Public Purchases Ordinance, 5-5-1 et seq., is the statute behind this whole directory and is held nowhere in the inventory."},
 "src-51808dace3a91a14": {"content": "Headed 2022 CITYWIDE ON-CALL ENGINEERING SERVICES, Project Number 722500, 721600, 721700, over a SCOPE OF PROJECTS section."},
}
for r in excluded:
    if r["id"] in EXTRA:
        r.update(EXTRA[r["id"]])

rows = approved + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(M), (set(M) - set(ids), set(ids) - set(M))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bycat = collections.Counter(r["category"] for r in excluded)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "municipaldevelopment-procurement-cluster-research-2026-09-12",
 "lane": "Claude research lane: the bid and procurement series of www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the second slice of the municipaldevelopment/documents lane.",
 "cluster": "The Department of Municipal Development's procurement paperwork: legal advertisements, Selection Advisory Committee requests for proposals, addenda, bidder questions, bid packages, ProCore guides, training decks and the standard on-call contract forms.",
 "scope": "All 52 pending-review candidates in this series that are not already rows in a saved artifact. The coverage gate is asserted in the generator.",
 "brief": "Test whether any of these are substantive City records rather than transactional solicitation paperwork, rather than assuming the whole class is excluded.",
 "brief_finding": ("The test was worth running and it found two. Fifty of the fifty-two are transactional — they "
                   "advertise, clarify or close a single competition — but two are the City's standard professional "
                   "services contract forms for citywide on-call engineering and on-call landscape architectural "
                   "work. Those are standards, not solicitations, and the archive already publishes their companion: "
                   "the Rules and Regulations Governing Compensation for Consulting Engineers, Architects and "
                   "Landscape Architects is validated, archived and live. The archive has the rule that says how such "
                   "consultants are paid and not the contract that says what they sign."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 52 candidates and measured byte length and "
            "SHA-256 from the fetched bytes, verifying every container by leading bytes. One fetch failed with a "
            "connection reset and was retried to a clean HTTP 200 before any measurement was recorded. Compared every "
            "checksum within the slice and against the 1,612 checksummed inventory records. Extracted text from every "
            "file, which required four different readers because the series is not all PDFs, and rendered the one "
            "image-only file rather than classifying it from its filename."),
 "classification_only": True,
 "shared_state_written": [],
 "container_mix": {
  "counts": dict(bycontainer),
  "why_it_matters": ("This is the most format-mixed slice in the run. Six of the fifty-two are not PDFs: two "
                     "PowerPoint decks and a Word document in OOXML zip containers, a further two legacy OLE2 Word "
                     "documents, and one RTF. Extension alone would have mislabelled none of them here, but leading "
                     "bytes are what determined which reader to use, and pdftotext would have returned nothing for "
                     "six records that do have readable content."),
  "readers_used": ["pdftotext -layout for the 46 PDFs",
                   "a ZIP reader over word/document.xml and ppt/slides/slideN.xml for the OOXML files",
                   "an RTF control-word stripper for the 5001.07 legal advertisement",
                   "antiword for the two legacy OLE2 Word documents",
                   "pdf.js rendering for the one image-only PDF"],
  "a_size_coincidence_that_is_not_a_relationship": ("src-4a2800924218bb64 and src-503b2193335553d0 are both exactly "
                                                    "46,080 bytes and both OLE2. Their checksums differ and their "
                                                    "content differs. OLE2 files are block-padded, so equal sizes are "
                                                    "common and mean nothing; only the hash settles it."),
 },
 "the_two_that_survived": {
  "what_they_are": "The City's blank standard-form professional services agreements for citywide on-call engineering and on-call landscape architectural services.",
  "why_they_are_not_solicitations": ("A solicitation invites proposals for one project and expires when it closes. "
                                     "These are the terms every such engagement is executed on: fourteen articles "
                                     "covering scope, authorisation, payment, responsible charge and the rest, with "
                                     "the parties block left as placeholders."),
  "how_they_were_identified": ("By reading rather than by filename. \"boilerplate\" in a procurement directory reads "
                               "like throwaway paperwork; the files are 16 and 17 pages of contract text citing "
                               "Section 61-23-21B NMSA 1978 and the Engineering and Surveying Practice Act."),
  "the_archive_gap_they_fill": (RULES + " on content/development-land-use/development-process.md sets how consulting "
                                "engineers, architects and landscape architects are compensated. Nothing in the "
                                "archive shows what those consultants actually sign."),
  "they_are_two_instruments_not_two_copies": "Normalized-text ratio 0.9597, token coverage 0.9767 and 0.9691. Shared boilerplate, different professional-practice provisions and scope.",
 },
 "excluded_by_category": dict(bycat),
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 0,
  "result": "Nothing in this slice duplicates anything, inside the inventory or inside this batch.",
  "note": ("Unlike cip-documents, where the same file was posted at several paths, this series has no repetition at "
           "all: fifty-two distinct competitions and documents, no two alike."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 0,
  "note": "No duplicates and no supersession. The nearest thing to a relationship is the pair of standard forms, which are companions rather than versions and are both recommended.",
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved],
   "finding": "Two standard-form City professional services contracts, 16 and 17 pages, for citywide on-call engineering and on-call landscape architectural services. The archive publishes the compensation rules for these professions and nothing about the agreement itself.",
   "recommended_action": "Approve and place on the development process page beside the compensation rules, cross-listed to capital spending. Label both as blank standard forms as posted, not executed contracts."},
  {"severity": "category-confirmed",
   "affects": [],
   "finding": "Fifty of fifty-two are transactional solicitation paperwork. The brief asked for this to be tested rather than assumed; it was, by reading every file, and the category holds.",
   "recommended_action": "Exclude the fifty. The two exceptions are recorded above so the exclusion is not read as covering the whole directory by default."},
  {"severity": "discovery-lead",
   "affects": ["src-7455b688bae320f4"],
   "finding": "The Central Purchasing outreach deck names the Public Purchases Ordinance, 5-5-1 et seq., as the statute the City procures under. It is held nowhere in the inventory.",
   "recommended_action": "Queue the Public Purchases Ordinance. It is the legal basis for this entire directory, and the run has already recommended the parallel Article 12 capital improvements ordinance from cip-documents."},
  {"severity": "format-caution",
   "affects": [r["id"] for r in rows if r["content_kind"] != "PDF"],
   "finding": "Six records in this slice are not PDFs — two OOXML presentations, one OOXML document, two legacy OLE2 Word files and one RTF. pdftotext returns nothing for all six.",
   "recommended_action": "None here, since all six are excluded. Recorded because any future pass over this directory that assumes PDF will silently read nothing from these."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "retries": "One candidate, src-1ecbfbd102bb54df, failed first with a connection reset and was retried to HTTP 200 before measurement.",
                "http_200_but_not_the_document": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": ("%d genuine PDFs, %d OOXML zip containers, %d legacy OLE2 Word documents and "
                                        "%d RTF by leading bytes. No content substitution in this slice."
                                        % (bycontainer['PDF'], bycontainer['OOXML'], bycontainer['DOC'], bycontainer['RTF']))},
 "approved_for_addition": approved,
 "excluded": excluded,
 "archival_note": (f"Both approved records are static PDFs and are inventory-only until an R2 archive object exists "
                   f"for each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. Both are "
                   f"born-digital with full text layers."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id; this slice contains "
                      "no duplicates and no supersession. No row requires human review; procurement paperwork raises "
                      "no enactment question. Each approved row carries a title, a 20-to-50-word description, a page "
                      "count, a proposed_canonical_page, a cross-listing and a caution that it is a blank template. "
                      "Every row carries a leading_bytes field, which matters more here than anywhere else in the run "
                      "because six records are not PDFs. Sizes and checksums are first measurements; the inventory "
                      "held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
