"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\form-based-code-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\fbc\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/form-based-code/'

AREA = 'content/development-land-use/area-sector-plans.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M = {}
MAGIC = {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")

UNDISC = {
 "fbz_part_a_04_02_09.final.pdf": {
  "url": BASE + "fbz_part_a_04_02_09.final.pdf", "http_status": 200, "size_bytes": 1276278,
  "checksum_sha256": "16275cace1f321813ee742077921a5a833922f95fc01609b1d6af0f45c7112b0", "pages": 59,
  "identity": "Form Based Zones, Section 14-16-3-22 Part A, April 2, 2009 final. The current-generation successor to src-4ce0f7387bab68d1."},
 "fbz_part_c_04_02_09.final.pdf": {
  "url": BASE + "fbz_part_c_04_02_09.final.pdf", "http_status": 200, "size_bytes": 718729,
  "checksum_sha256": "f25c90dd167a7f97c82d40e4f904402c57759c2b14ea2976ce7df1082dc6b7c9", "pages": 28,
  "identity": "Form Based Zones, Section 14-16-3-22 Part C, April 2, 2009 final. The current-generation successor to src-a94103538515dadb."},
}


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    r.update(M[i])
    return r


approved = [
 {**row("src-eb96077b20226b87", "approved for addition"),
  "title": "La Cueva Sector Development Plan, June 2000",
  "description": "The City sector development plan for the La Cueva area in Albuquerque's far Northeast Heights sets the land use, zoning, transportation, and design framework for the foothills neighbourhoods below the Sandia Mountains.",
  "date": "2000-06", "pages": 127,
  "proposed_canonical_page": AREA,
  "cross_listings": [],
  "evidence": "Image-only PDF with essentially no text layer; the cover was rendered and read. It reads \"La Cueva Sector Development Plan, City Of Albuquerque, Contracting Agency; Sites Southwest, Chief or Lead Planners; Resource Technology, Inc., Terry O. Brown, P.E., Civitas, Inc., Team; June 2000\". 127 pages, 13,004,494 bytes.",
  "why_retained": "A complete adopted-era sector development plan, misfiled in the form-based-code directory under the bare filename lacueva.pdf and having nothing to do with form-based code. It is the only copy in the inventory: the six other La Cueva records are all Bernalillo County Upper La Cueva drainage-project material, unrelated to this plan.",
  "misfiling_note": "Nothing in the filename, the inventory title, or the directory it sits in indicates what this document is. It was identified only by rendering the cover."},

 {**row("src-20999f89704896c2", "approved for addition"),
  "title": "Downtown 2010 Plan: Development and Building Process (extract, from printed page 27)",
  "description": "The Downtown 2010 Plan chapter explains its four-step development approach, walking an applicant through the districts map, the district uses matrix, the authorised building types, and the building standards that lead to expedited site plan approval.",
  "date": None, "pages": 44,
  "proposed_canonical_page": REDEV,
  "cross_listings": [{"page": ZONING, "reason": "It is Albuquerque's earliest form-based-style regulatory scheme and the precedent the 2007 to 2009 form-based code drafts in this same directory were built on."}],
  "evidence": "Image-only PDF with no text layer; page 1 was rendered and read. It is headed \"DOWNTOWN 2010, development & building process\" and its first page is printed page 27, so this is an extract rather than the whole plan. It names the five Downtown districts (Housing, Arts and Entertainment, Government, Financial and Hospitality, Warehouse, Mixed-Use) and describes the colour-coded districts map, district uses matrix and building types chart.",
  "why_retained": "The substantive regulatory core of the Downtown 2010 Plan, and the reason it sits in the form-based-code directory: Downtown 2010 is the precedent the later citywide form-based code drafts were modelled on. The site carries the current Downtown 2050 plan and nothing from the 2010 generation.",
  "completeness_caveat": "This is an extract beginning at printed page 27, not the complete Downtown 2010 Plan, and the complete plan is not in the inventory. Any title must say so. See integration_flags.",
  "dating_note": "No printed date on the pages read. The plan is named for 2010 and was adopted well before it; do not assert a date the extract does not carry."},
]
for r in approved:
    r["description_word_count"] = len(r["description"].split())

# Draft generations, established by reading the section number printed in every
# page header and by measuring each generation against the next.
GEN = [
 ("src-24e65271e6797b78", "ABQFBC-finaldraftedits103007ToCdoubleside.pdf", "G1",
  "Form Based Code table of contents, final draft edits, October 30, 2007", 2,
  None, "the June 6, 2008 restructure as a whole",
  "Chapter 14 Article 20 as a standalone Form Based Code article. The June 2008 generation abandoned that structure entirely and folded the code into the Zoning Code at Section 14-16-3-20, so this contents page describes a document that no longer exists in that form."),
 ("src-b5fb627dfff69e54", "ABQFBC-finaldraftedits103007Part1doubleside.pdf", "G1",
  "Form Based Code Part 1, General Provisions, final draft edits, October 30, 2007", 22,
  "src-6c8fb67dc2dacda9", None,
  "Sections numbered 14-20-1-1 in the standalone Article 20 scheme, replaced by Section 14-16-3-20(A) General Provisions in the June 2008 generation."),
 ("src-d837cff6918ede96", "ABQFBC-finaldraftedits103007Part2doubleside.pdf", "G1",
  "Form Based Code Part 2, Building Forms, Materials, Signage, Lot Layout, final draft edits, October 30, 2007", 38,
  "src-41772a036fd8d687", None,
  "Replaced by the June 2008 Section 14-16-3-20(B) material."),
 ("src-ef0083880aa30ca5", "ABQFBC-finaldraftedits103007Part3doubleside.pdf", "G1",
  "Form Based Code Part 3, Form Based Code Zones, final draft edits, October 30, 2007", 44,
  "src-9e517541bd23ff4d", None,
  "Replaced by the June 2008 Section 14-16-3-20(C) components material."),

 ("src-6c8fb67dc2dacda9", "abcfbc_section_a_060608.pdf", "G2",
  "Form Based Code Section 14-16-3-20(A), General Provisions, June 6, 2008", 5,
  "src-4ce0f7387bab68d1", None,
  "Renumbered to Section 14-16-3-22 Form Based Zones in the February 27, 2009 generation; token coverage of this file inside its successor is 0.9464."),
 ("src-41772a036fd8d687", "abcfbc_section_b_060608.pdf", "G2",
  "Form Based Code Section 14-16-3-20(B), Zones, June 6, 2008", 26,
  "src-5157b5d0c02331a6", None,
  "Renumbered and rewritten as Section 14-16-3-22(B); token coverage 0.8593, sequence ratio only 0.0379, so the text was substantially reworked rather than copied."),
 ("src-9e517541bd23ff4d", "abcfbc_section_c_060608.pdf", "G2",
  "Form Based Code Section 14-16-3-20(C), Building Types, Street Design, Parking, Lighting, Signage, Usable Open Space, June 6, 2008", 32,
  "src-a94103538515dadb", None,
  "Renumbered as Section 14-16-3-22(C) Components; token coverage 0.7883."),

 ("src-4ce0f7387bab68d1", "fbz_part_a_02_27_09.pdf", "G3a",
  "Form Based Zones Section 14-16-3-22 Part A, February 27, 2009", 6,
  None, "fbz_part_a_04_02_09.final.pdf",
  "Superseded five weeks later by the April 2, 2009 final Part A, which expanded from 6 pages to 59: token coverage of this file inside the final is 0.9900 while only 0.4454 of the final sits inside this one."),
 ("src-5157b5d0c02331a6", "fbz_part_b_02_27_09-2.rev.pdf", "G3a",
  "Form Based Zones Section 14-16-3-22 Part B, Zones, February 27, 2009 revision", 25,
  "src-05176d26d35effd3", None,
  "Superseded by the April 2, 2009 final Part B, which is in the inventory as src-05176d26d35effd3. Token coverage 0.9345 and 0.9781 with a sequence ratio of 0.0526: the same material comprehensively re-laid-out."),
 ("src-a94103538515dadb", "fbz_part_c_02_27_09-1.pdf", "G3a",
  "Form Based Zones Section 14-16-3-22 Part C, Components, February 27, 2009", 28,
  None, "fbz_part_c_04_02_09.final.pdf",
  "Superseded by the April 2, 2009 final Part C; token coverage 0.9469 and 0.9194, sequence ratio 0.7190."),
]

superseded = []
for i, fname, gen, title, pages, canon_id, canon_external, basis in GEN:
    r = row(i, "superseded")
    r.update({"title_for_reference": title, "pages": pages, "generation": gen, "basis": basis,
              "hash_found_it": False})
    if canon_id:
        r["canonical_id"] = canon_id
        r["canonical_url"] = IDX[canon_id].get('direct_file_url') or IDX[canon_id].get('source_url')
    elif canon_external in UNDISC:
        r["canonical_id"] = None
        r["null_canonical_cause"] = "successor exists on the City server but is not an inventory record"
        r["canonical_not_in_inventory"] = canon_external
        r["canonical_url"] = UNDISC[canon_external]["url"]
        r["canonical_blocker"] = (
         "Add the named file as a candidate before applying this supersession, so the chain does not terminate "
         "outside the inventory. Its URL, size and checksum are in undiscovered_files.")
    else:
        r["canonical_id"] = None
        r["null_canonical_cause"] = "no single successor file exists"
        r["canonical_not_in_inventory"] = canon_external
        r["canonical_blocker"] = (
         "This row has no file-level successor and none can be supplied. The June 2008 restructure published no "
         "table of contents: the probe for abcfbc_toc_060608.pdf returned 404. Apply this row as superseded with "
         "no canonical, or attach it to src-6c8fb67dc2dacda9 as the first file of the generation that replaced "
         "it, which is an editorial choice rather than a measured relationship.")
    superseded.append(r)

duplicates = [
 {**row("src-ca30482593edc4c9", "duplicate"),
  "title_for_reference": "Albuquerque/Bernalillo County Comprehensive Plan (second copy)",
  "pages": 277,
  "canonical_id": "src-2f5e70d5a655369e",
  "canonical_url": "https://www.cabq.gov/council/documents/Volcano%20Heights%20Sector%20Development%20Plan/abq_comp_plan.pdf",
  "basis": "Byte-identical to the copy in the Volcano Heights directory: same 11,872,609 bytes and same SHA-256 344a30caa7a4dc497961386ecfb02ec85f7454459a2ec95482fbad7e6c12e698. The City files the same Comprehensive Plan PDF as reference material in multiple plan directories.",
  "hash_found_it": True,
  "note": "The canonical is recommended for addition in the volcano-heights artifact of the same date, where it is recorded as the only actual copy of the Comprehensive Plan in the archive. Integrate the two artifacts together, and expect further copies of this same file in other plan directories still to be triaged."},
]


def R(i, draft_title, pages, question, why, evidence):
    r = row(i, "requires human review")
    r.update({"draft_title": draft_title, "pages": pages,
              "question_for_human": question, "why_not_decided_here": why, "evidence": evidence})
    return r


ENACT_WHY = (
 "All three carry ENACTMENT NO. blank, so under the two standing checkpoint blockers each is the bill as "
 "considered rather than the law. They must be resolved as one group because they tell a story on their face: "
 "O-07-116 in the Seventeenth Council proposed adopting a form based code outright; F/S O-08-58 in the "
 "Eighteenth Council took a different route, amending the SU-1 Special Use zone to admit Form Based Zones as a "
 "special use; and O-08-58 is explicitly filenamed a reintroduction. Whether any of them passed decides whether "
 "the ten superseded drafts in this directory are the record of an adopted code or of a proposal Albuquerque "
 "spent three years on and did not adopt. That is the single most consequential unresolved question in this "
 "cluster and it cannot be answered from these files.")

rhr = [
 R("src-26cb2e52a14f606e",
   "Council Bill O-07-116: Adopting a Form Based Code Prescribing Building Form, Frontage Type, Parking, Connectivity, Design, Signage and Lighting Standards and Establishing Zones Which Allow Mixed Use",
   2, "Locate the enacted ordinance, or establish that the bill failed. Decide all three together.",
   ENACT_WHY, "2 pages, Seventeenth Council, sponsored by Isaac Benton, enactment number blank."),
 R("src-7bf6d7801a352612",
   "Council Bill F/S O-08-58: Amending Section 14-16-2-22(B) ROA 1994, the SU-1 Special Use Zone, to Include Form Based Zones as a Special Use (floor substitute)",
   3, "Same question; this is the floor substitute of the reintroduced bill below.",
   ENACT_WHY, "3 pages, Eighteenth Council, sponsored by Isaac Benton, enactment number blank."),
 R("src-d6595748f0d531d4",
   "Council Bill O-08-58: Amending Section 14-16-2-22(B) ROA 1994, the SU-1 Special Use Zone, to Include Form Based Code Zones as a Special Use (reintroduction of the form based code)",
   3, "Same question; the filename records this as a reintroduction, which implies an earlier attempt did not carry.",
   ENACT_WHY, "3 pages, Eighteenth Council, sponsored by Isaac Benton, enactment number blank. Its title says Form Based Code Zones where the floor substitute says Form Based Zones, which matches the section renaming visible across the draft generations."),
]

excluded = [
 {**row("src-86ab054ee0977b03", "excluded"),
  "title_for_reference": "Form Based Code collection landing page",
  "exclusion_reason": "The Plone collection landing page for this directory, not a document.",
  "category": "collection landing page",
  "usefulness": "Parsed as part of this lane. It does not list fbz_part_a_04_02_09.final.pdf or fbz_part_c_04_02_09.final.pdf, which is why only Part B of the final generation was ever discovered."},

 {**row("src-f0c757fac463bb4a", "excluded"),
  "title_for_reference": "Basic Principles of the Form Based Code, Councillor Isaac Benton town hall presentation, December 8, 2007",
  "pages": 39,
  "exclusion_reason": "An outreach presentation advocating a proposal, delivered at a councillor's town hall. It argues for the code rather than stating it, and the code text itself is in this directory in four generations.",
  "category": "outreach presentation"},

 {**row("src-740051342d429b2b", "excluded"),
  "title_for_reference": "Myths and Realities about the Form-Based Code, town hall handout, December 8, 2007",
  "pages": 1,
  "exclusion_reason": "A one-page myth-and-rebuttal handout from the same town hall. Advocacy material for a proposal, not a record of a City action or standard.",
  "category": "outreach handout"},

 {**row("src-b3448b2b1a88ceee", "excluded"),
  "title_for_reference": "Summary of the Form-Based Code",
  "pages": 2,
  "exclusion_reason": "A two-page plain-language summary of what the proposed code would do. It is the clearest short explanation in the directory, but it summarises a proposal whose enactment is unresolved and whose every draft is recommended superseded or held, so there is nothing published for it to explain.",
  "category": "proposal summary",
  "revisit_if": "If the enactment question resolves in favour of adoption and the April 2009 final package is published, this summary is the natural explainer to reconsider alongside it."},
]

rows = approved + superseded + duplicates + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)

artifact = {
 "batch_id": "form-based-code-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/form-based-code cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Form Based Code drafting record in the Albuquerque City Council document library at www.cabq.gov/council/documents/form-based-code.",
 "scope": "All 20 pending-review candidates in that directory. The directory also holds one record a prior lane set to requires human review, src-05176d26d35effd3, which this artifact does not reclassify but identifies as the April 2, 2009 final Part B and names as the successor in one supersession chain.",
 "brief": "Separate adopted form-based code text and regulating plans from drafts and meeting handouts, applying the enactment test and the split-package method.",
 "brief_finding": "There is no adopted text here to separate out. Ten of the twenty files are one code drafted four times between October 2007 and April 2009, renumbered twice as it moved from a standalone Chapter 14 Article 20 into the Zoning Code at Section 14-16-3-20 and then Section 14-16-3-22, and every one of them is superseded by a later generation. The three ordinances that would have enacted it all carry blank enactment numbers, and one is filenamed a reintroduction. The two records worth retaining have nothing to do with form-based code at all: a complete 2000 sector development plan filed under the bare name lacueva.pdf, and an extract of the Downtown 2010 Plan.",
 "method": "Fetched all 20 candidates and the prior-lane requires-human-review record without touching shared inventory state, and recorded exact byte length and SHA-256 for each. Read the section number printed in every page header, which is what establishes the four generations and the two renumberings; filenames alone do not show that a 2008 file and a 2009 file regulate under different code sections. Measured each generation against the next by normalized-text similarity and token coverage in both directions. Rendered the two image-only PDFs, which is how both retained records were identified. Probed the filename sequence for parts the City listing does not show. Compared all checksums against the 1,612 checksummed inventory records.",
 "classification_only": True,
 "shared_state_written": [],
 "drafting_chain": {
  "finding": "Four generations of one code, with two renumberings. The generation is readable from the section number printed in every page header, not from the filename.",
  "generations": [
   {"generation": "G1", "date": "2007-10-30", "scheme": "Chapter 14, Article 20, a standalone Form Based Code article with sections numbered 14-20-1-1",
    "files": 4, "ids": ["src-24e65271e6797b78", "src-b5fb627dfff69e54", "src-d837cff6918ede96", "src-ef0083880aa30ca5"]},
   {"generation": "G2", "date": "2008-06-06", "scheme": "Zoning Code Part 3 General Regulations, Section 14-16-3-20 Form Based Code, in three lettered sections A, B and C",
    "files": 3, "ids": ["src-6c8fb67dc2dacda9", "src-41772a036fd8d687", "src-9e517541bd23ff4d"]},
   {"generation": "G3a", "date": "2009-02-27", "scheme": "Section 14-16-3-22 Form Based Zones, renumbered and renamed, in three lettered parts",
    "files": 3, "ids": ["src-4ce0f7387bab68d1", "src-5157b5d0c02331a6", "src-a94103538515dadb"]},
   {"generation": "G3b", "date": "2009-04-02", "scheme": "Section 14-16-3-22 Form Based Zones, final",
    "files": 3, "in_inventory": 1, "ids": ["src-05176d26d35effd3"],
    "not_in_inventory": ["fbz_part_a_04_02_09.final.pdf", "fbz_part_c_04_02_09.final.pdf"],
    "note": "The current generation, and only one of its three parts is in the inventory. Until the other two are added the archive cannot represent the final form of this code at all."}
  ],
  "page_growth_signal": "Part A grew from 5 pages in June 2008 to 6 in February 2009 to 59 in the April 2009 final, absorbing material as the drafters consolidated. That is why coverage of the February Part A inside the April final is 0.9900 while only 0.4454 of the final sits inside February."
 },
 "undiscovered_files": {
  "count": 2,
  "why_this_matters": "Both return HTTP 200 from the City server and neither appears in the City's own collection listing for this directory. They are two of the three parts of the current draft generation. This is the second directory in a row where the City listing is proved incomplete against its own server, after the Planned Growth Strategy cluster of the same date.",
  "files": UNDISC,
  "recommended_action": "Add both as candidates before applying the two supersession rows whose canonical_id is null. This artifact creates no inventory records.",
  "probe_record": "Seven filename-sequence probes were run. Four returned 404: abcfbc_section_d_060608, abcfbc_toc_060608, fbz_part_d_02_27_09, fbz_toc_02_27_09 and ABQFBC-finaldraftedits103007Part4doubleside. Two returned 200 and are listed above. The generations are therefore three parts each after G1, and G1's four-file structure is genuinely four files."
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 1,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 1,
  "relationships_found_by_measurement": 10,
  "note": "Hashing found exactly one relationship, the Comprehensive Plan copy shared with the Volcano Heights directory, and it found it because the City republishes that file unchanged. The ten supersession relationships are invisible to it: each generation was re-typeset, so sequence ratios run as low as 0.0379 between files that token coverage shows are 0.86 the same material. Both measures were needed in every case, and in opposite directions from the Paseo del Volcan cluster, where high coverage with low sequence similarity was a false positive. The difference is that here the page headers independently prove the lineage."
 },
 "integration_flags": [
  {"severity": "unresolved-enactment",
   "affects": ["src-26cb2e52a14f606e", "src-7bf6d7801a352612", "src-d6595748f0d531d4"],
   "finding": "All three form-based code ordinances carry blank enactment numbers, and one is filenamed a reintroduction, which implies an earlier attempt did not carry. Whether any passed determines whether this directory records an adopted code or a three-year proposal that failed.",
   "recommended_action": "Resolve all three together. Note that Section 14-16-3-22 no longer exists: the Integrated Development Ordinance adopted 2017-11-13 replaced Chapter 14 Article 16 entirely, so even an adopted form-based code would now be historic. That does not answer the question, it only bounds it."},
  {"severity": "discovery-gap",
   "affects": ["src-4ce0f7387bab68d1", "src-a94103538515dadb"],
   "finding": "Two supersession rows carry canonical_id null because their successors, the April 2, 2009 final Parts A and C, exist on the City server but are absent from the inventory. A supersession whose canonical lies outside the inventory cannot be applied cleanly.",
   "recommended_action": "Add both files as candidates first, then apply those two rows with their real canonical ids. Their URLs, sizes and checksums are in undiscovered_files."},
  {"severity": "misfiled-record",
   "affects": ["src-eb96077b20226b87"],
   "finding": "lacueva.pdf is the complete La Cueva Sector Development Plan of June 2000, 127 pages, filed in the form-based-code directory and named only for the neighbourhood. Nothing in the filename, the inventory title, or the directory indicates what it is; it was identified by rendering the cover. The inventory's six other La Cueva records are all Bernalillo County drainage-project material.",
   "recommended_action": "Place it on the area and sector plans page. Treat this as a warning that a bare-neighbourhood-name filename in a topic directory may be a whole plan: render before excluding."},
  {"severity": "coverage-gap",
   "affects": ["src-20999f89704896c2"],
   "finding": "process.pdf is an extract of the Downtown 2010 Plan beginning at printed page 27, and the complete Downtown 2010 Plan is nowhere in the inventory. The site carries Downtown 2050 and the 2025 parking study but nothing from the 2010 generation.",
   "recommended_action": "Retain the extract with its partial nature stated in the title, and add the complete Downtown 2010 Plan to the discovery queue. It is a named predecessor of a plan the site already publishes."},
  {"severity": "cross-artifact",
   "affects": ["src-ca30482593edc4c9", "src-2f5e70d5a655369e"],
   "finding": "The Albuquerque/Bernalillo County Comprehensive Plan is byte-identical across the form-based-code and Volcano Heights directories. The volcano-heights artifact recommends the other copy for addition as the archive's only copy of that plan.",
   "recommended_action": "Integrate the two artifacts together. Expect further byte-identical copies of this file in other plan directories still to be triaged; they should all resolve to the single canonical."}
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"]
 },
 "link_check": {"checked": 21, "http_200": 21, "failed": 0,
                "probe_checked": 7, "probe_http_200": 2, "probe_http_404": 5,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11, on the 20 pending candidates and the prior-lane requires-human-review record, plus seven filename-sequence probes.",
                "containers_verified": "20 genuine PDFs and one HTML collection page by leading bytes. Two PDFs have no text layer and were rendered."},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": f"Both approved records are static PDFs and are inventory-only until an R2 archive object exists for each and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. Neither has a text layer, so full-text search will not reach them without optical character recognition; that is a property of the City's originals.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Seven of the ten superseded rows carry a canonical_id resolving to another record in this same cluster, so apply them in generation order G1 then G2 then G3a. Three rows carry canonical_id null and each states its null_canonical_cause. Two of those three, src-4ce0f7387bab68d1 and src-a94103538515dadb, name a successor file that exists on the City server; do not apply them until those files are added as candidates. The third, src-24e65271e6797b78, has no file-level successor at all because the June 2008 restructure published no table of contents, and its canonical_blocker states the editorial choice that remains. The duplicate row's canonical lies in the volcano-heights artifact of the same date. The two approved rows carry a title, a 20-to-50-word description and a proposed_canonical_page; both carry a null or partial date and neither may be given an asserted one. Three rows are requires human review under the standing enactment blockers and must be decided as one group. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write", "no site content change", "no R2 upload", "no commit, merge, or deploy", "no inventory record created for the two undiscovered files"]
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
