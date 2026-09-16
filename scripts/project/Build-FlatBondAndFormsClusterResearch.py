"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Fifth slice of the municipaldevelopment/documents lane: the
remaining flat-level general obligation bond material and the standard-form
services agreements.
"""

import collections
import datetime
import difflib
import glob
import json
import os
import pathlib
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\flat-bond-and-standard-forms-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md4')

CAPITAL = 'content/city-data/capital-spending.md'
DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'

ENG_FORM = 'src-b3d8dcb56e000437'   # on-call engineering agreement, approved in the procurement slice
LAND_FORM = 'src-4952ea05cd055792'  # on-call landscape agreement, approved in the procurement slice

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls5.tsv'), encoding='utf-8')]
MOVED = 'src-feaefc4c87a06768'   # corrected out; decided in facility-environmental-compliance-cluster-research-2026-09-12.json
SLICE = [i for i in SLICE if i != MOVED]
NAME = {i: os.path.basename(URL[i]) for i in SLICE}

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
assert not (set(SLICE) & PRIOR), sorted(set(SLICE) & PRIOR)

CONTAINER = {'25504446': 'PDF', 'd0cf11e0': 'DOC'}

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither. Container verified by leading bytes, not by extension.")


def norm(i):
    f = pathlib.Path(SP, 'txt', '%s.txt' % i)
    return re.sub(r'[^a-z0-9]+', ' ', f.read_text(encoding='utf-8', errors='replace').lower()).strip() if f.exists() else ''


def lead(i, n=2):
    t = pathlib.Path(SP, 'txt', '%s.txt' % i)
    if not t.exists():
        return ''
    lines = [re.sub(r'\s+', ' ', l).strip() for l in t.read_text(encoding='utf-8', errors='replace').split('\n') if l.strip()]
    return ' '.join(lines[1:1 + n])[:200]


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


# ------------------------------------------------------------------ approved
approved = [
 {**row('src-a246ab1fcdb14d3d', "approved for addition"),
  "title": "Summary of the 2015 General Obligation Bond Program",
  "description": ("The City's summary of its 2015 general obligation bond programme sets out what each purpose was "
                  "allocated across the programme, from public safety onward, giving the shape of the whole bond "
                  "package in one document."),
  "date": "2015", "pages": None,
  "evidence": "Born-digital PDF with a full text layer, headed \"Summary of 2015 G.O. Bond Program\" over the purpose listing, beginning with Public Safety.",
  "why_retained": ("Dated on its own face, which almost nothing else at this level of the directory is. The archive "
                   "holds bond department sets for 2003, 2009, 2011 and 2017, a 2007 decade plan, and — from "
                   "bond-2013-department-set-cluster-research-2026-09-12.json — a 2013 set. It holds nothing for "
                   "2015."),
  "proposed_canonical_page": CAPITAL, "cross_listings": [],
  "description_word_count": 0},

 {**row('src-f17b0733dab9b327', "approved for addition"),
  "title": "2015-2023 General Obligation Bond Summary Totals by Department and Division",
  "description": ("The City's decade summary schedules every department and division's general obligation bond "
                  "funding across the 2015, 2017, 2019, 2021 and 2023 cycles, with the totals for each line across "
                  "the whole period."),
  "date": "2015", "pages": None,
  "evidence": ("Born-digital PDF with a full text layer, headed \"G.O. Bond Summary Totals\" over the column set "
               "\"Department / Division  2015 2017 2019 2021 2023  Totals\"."),
  "why_retained": ("The 2015 counterpart of the five-cycle schedules the archive already publishes for other "
                   "programmes, and the schedule that the undated purpose sheets held for review below would each "
                   "have to be matched against."),
  "proposed_canonical_page": CAPITAL, "cross_listings": [],
  "description_word_count": 0},

 {**row('src-4abc31e10a698871', "approved for addition"),
  "title": "City of Albuquerque Services Agreement: generic standard-form template",
  "description": ("The City's blank professional services agreement template leaves the profession, project and "
                  "parties unfilled, and is the master form from which the profession-specific on-call agreements "
                  "for engineers, architects and landscape architects are drawn."),
  "date": None, "pages": None,
  "evidence": ("Legacy OLE2 Word document, leading bytes d0cf11e0, extracted with antiword. It opens \"City Clerk "
               "Contract No. _________________ / Project Number _______________________ / CITY OF ALBUQUERQUE / "
               "____________________ SERVICES AGREEMENT / (Name of Project):\" — the profession itself left blank, "
               "which is what distinguishes it from the filled-in professional forms."),
  "why_retained": ("It is the root of the standard-form family. "
                   "municipaldevelopment-procurement-cluster-research-2026-09-12.json recommended the on-call "
                   "engineering and on-call landscape forms; this is the template behind them and the three further "
                   "forms in this batch."),
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": CAPITAL, "reason": "Every agreement drawn from it is funded through the Capital Implementation Program."}],
  "caution": "A blank template with no revision stamp and no date on its face. Describe it as the generic form as posted.",
  "description_word_count": 0},

 {**row('src-ff4a164039280baf', "approved for addition"),
  "title": "City of Albuquerque Architectural Services Agreement (standard form)",
  "description": ("The City's standard professional services contract for architectural work sets out the "
                  "architect's obligations, how the work is authorised and paid, and the terms the City contracts "
                  "on, in the same article structure as its engineering and landscape counterparts."),
  "date": None, "pages": None,
  "evidence": "Born-digital PDF with a full text layer, opening on \"City Clerk Contract No. ____________ / Project Number\" over the City of Albuquerque architectural services agreement heading.",
  "why_retained": "The third profession in the standard-form family and the one the archive lacked entirely.",
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": CAPITAL, "reason": "Architectural engagements are funded through the Capital Implementation Program."}],
  "caution": "A blank template, not an executed contract.",
  "description_word_count": 0},

 {**row('src-7c0cbd9f16e7534b', "approved for addition"),
  "title": "City of Albuquerque Landscape Architectural Services Agreement (standard form, non-on-call)",
  "description": ("The City's standard landscape architectural services contract, distinct from the on-call form: "
                  "same family of terms, but written for a single named project rather than for work called off "
                  "against a standing engagement."),
  "date": "2017", "pages": None,
  "evidence": ("Born-digital PDF with a full text layer, opening on \"City Clerk Contract No. ____________ / Project "
               "Number\", and referencing 2017."),
  "why_retained": ("Not a copy of the on-call landscape form already recommended. Measured against " + LAND_FORM +
                   ": token coverage 0.9946 both directions and a real sequence ratio of 0.4745. Nearly the same vocabulary, a "
                   "different instrument."),
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": PROJECTS, "reason": "Landscape architectural engagements attach to named City projects."}],
  "caution": "A blank template.",
  "description_word_count": 0},

 {**row('src-eea8e27da0993211', "approved for addition"),
  "title": "City of Albuquerque Services Agreement for Federally Assisted Projects: HUD standard form",
  "description": ("The City's standard services agreement for projects assisted with federal Housing and Urban "
                  "Development funds, carrying the federal terms and certifications such an engagement must include "
                  "alongside the City's own contract provisions."),
  "date": None, "pages": None,
  "evidence": ("Born-digital PDF with a full text layer, opening \"Proj. No. XXX.XX / City Clerk Contract No.\" with "
               "the project number left as placeholder characters."),
  "why_retained": ("The most distinct member of the standard-form family: measured against the on-call engineering "
                   "form " + ENG_FORM + " it returns a real sequence ratio of 0.0256, so the federal provisions "
                   "dominate it. Nothing in the archive records how the City contracts when federal money is "
                   "involved."),
  "proposed_canonical_page": DEVPROC,
  "cross_listings": [{"page": PROJECTS, "reason": "Federally assisted projects are the City projects this form governs."}],
  "caution": "A blank template with no revision stamp.",
  "description_word_count": 0},
]
for r in approved:
    r["description_word_count"] = len(r["description"].split())

APPROVED_IDS = {r['id'] for r in approved}

# ------------ the record corrected out of this artifact (see a_correction_carried_forward)
excluded = []

# ------------------------------------------------- requires human review rows
rhr = []

# (a) the third edition of a 2013 sheet, belonging to the earlier package
r = row('src-f6c1a087135ceff4', "requires human review")
r.update({"draft_title": "2013-2021 General Obligation Bond Summary: Family and Community Services (third edition)",
          "question_for_human": ("Resolve with the two editions of this sheet already held for review in "
                                 "bond-2013-department-set-cluster-research-2026-09-12.json. There are three, not "
                                 "two."),
          "why_not_decided_here": ("Dated on its face to the same 2013, 2015, 2017, 2019 and 2021 cycles as the "
                                   "plain and copy_of editions of the Family and Community Services summary, and "
                                   "distinguished from them only by a copy2_of prefix. The edition question that "
                                   "artifact raises for twenty-nine sheets has a third answer for this one."),
          "measurement": "Headed \"G.O. Bond Summary\" over \"Department / Division /\" with the 2013 to 2021 column set. %d bytes." % M['src-f6c1a087135ceff4']['size_bytes'],
          "distinguishing_content": "Headed G.O. Bond Summary over the 2013 2015 2017 2019 2021 column set, Family and Community Services, third edition by filename prefix copy2_of.",
          "package": "the_two_editions, extended to three for this department",
          "cross_artifact": "bond-2013-department-set-cluster-research-2026-09-12.json"})
rhr.append(r)

# (b) the election bond question
r = row('src-88fd4897987bc078', "requires human review")
r.update({"draft_title": "Election Bond Question: Affordable Housing Bonds, $10,150,000 in support of the Workforce Housing Act",
          "question_for_human": "Establish which bond election this question was put at, then approve it.",
          "why_not_decided_here": ("It is a ballot question and the archive holds very few — "
                                   "cip-documents-cluster-research-2026-09-12.json recommended the 2007 set precisely "
                                   "because no programme's questions were held. This one is worth the same treatment, "
                                   "but its programme year is not printed on it. The body references 2022 and 2024 "
                                   "and bond elections fall in odd years, which points at 2023 without establishing "
                                   "it, and publishing a ballot question under the wrong election would misstate what "
                                   "voters were asked."),
          "measurement": ("Born-digital PDF, 811,883 bytes, the largest file in this slice. It reads \"Shall the City "
                          "of Albuquerque issue $10,150,000 of its general obligation bonds in support of the "
                          "Workforce Housing Act to provide resources for the construction and rehabilitation of high "
                          "quality, permanently affordable housing for low to moderate income working families, "
                          "including affordable senior rental?\" and its scope page cites the Health, Housing and "
                          "Homelessness Workforce Housing Trust Fund at $10,000,000 under F/S(3) O-06-9."),
          "distinguishing_content": "Workforce Housing Trust Fund $10,000,000, under F/S(3) O-06-9. Sole entry; this is a ballot question, not a purpose table.",
          "package": "the_undated_purpose_sheets",
          "note": "The only ballot question in this slice; everything else in the package is a department purpose sheet."})
rhr.append(r)

# (c) the undated purpose sheets
SHEETS = [i for i in SLICE
          if i not in APPROVED_IDS
          and i not in {'src-f6c1a087135ceff4', 'src-88fd4897987bc078'}]
for i in sorted(SHEETS, key=lambda x: NAME[x]):
    r = row(i, "requires human review")
    r.update({"draft_title": "General obligation bond purpose sheet, programme year not stated: " + NAME[i],
              "question_for_human": "Match this sheet to its bond programme year, then approve it.",
              "why_not_decided_here": ("No programme year is printed on it, and the flat level of this directory "
                                       "mixes purpose sheets from several programmes under near-identical names. "
                                       "Publishing a bond table under the wrong programme year would misstate what "
                                       "voters authorised."),
              "distinguishing_content": lead(i),
              "package": "the_undated_purpose_sheets"})
    rhr.append(r)

for n, r in enumerate(rhr, 1):
    r["priority"] = n

rows = approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (set(SLICE) - set(ids), set(ids) - set(SLICE))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
bycontainer = collections.Counter(r["content_kind"] for r in rows)
n_sheets = len(SHEETS)

artifact = {
 "batch_id": "flat-bond-and-standard-forms-cluster-research-2026-09-12",
 "lane": "Claude research lane: the remaining flat-level bond material and standard-form services agreements in www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the fifth slice of the municipaldevelopment/documents lane.",
 "cluster": "What remains of the flat level's general obligation bond material once the 2013 department set is taken out, together with four standard-form City services agreements.",
 "scope": ("The 44 pending-review candidates in this group that are decided here. One further candidate was drafted into this artifact and corrected out of it; see a_correction_carried_forward. The coverage gate is asserted in the generator."),
 "brief": "Date each group from the face of the documents, and compare the lowercase and CamelCase sheets before assuming either is a copy.",
 "brief_finding": ("The comparison was the point and it came back negative: the lowercase and CamelCase sheets are "
                   "not copies of each other, and neither are the numbered ones. Every purpose sheet in this group "
                   "carries different figures for the same department — affordable housing alone appears at "
                   "$2,500,000, $3,400,000, $4,300,000 and $5,000,000 across four files. They are sheets from several "
                   "different bond programmes filed side by side under near-identical names, and almost none of them "
                   "prints its programme year. Across all 41 within-family pairs the highest real sequence ratio is "
                   "0.6155 and not one pair is string-equal."),
 "second_finding": ("Four more standard-form City services agreements, including the generic template the "
                    "profession-specific ones are drawn from and the form used when federal Housing and Urban "
                    "Development money is involved. With the two recommended in "
                    "municipaldevelopment-procurement-cluster-research-2026-09-12.json that makes six, and the "
                    "archive held none of them."),
 "method": ("Fetched every candidate and measured byte length and SHA-256 from the fetched bytes, verifying every "
            "container by leading bytes; one is a legacy OLE2 Word document and was read with antiword rather than "
            "pdftotext. Compared every checksum within the slice and against the 1,612 checksummed inventory records. "
            "Read the year columns and headings off the face of each file rather than inferring from filenames. "
            "Extracted the leading project entry and dollar figure from every purpose sheet, which is what "
            "established that they are different programmes rather than copies. Compared each standard form against "
            "the two already recommended, using real sequence ratios rather than token coverage. Probed the server "
            "for the missing numbered sheets 3, 4, 7 and 12 across six plausible names."),
 "classification_only": True,
 "shared_state_written": [],
 "the_undated_purpose_sheets": {
  "count": n_sheets,
  "the_problem": ("Three naming conventions for the same material sit side by side at the flat level — a numbered "
                  "series (1-public-safety-bonds.pdf through 11-metropolitan-redevelopment-bonds.pdf), a CamelCase "
                  "series (PublicSafetyBonds.pdf), and a lowercase hyphenated series with and without a -1 suffix "
                  "(public-safety-bonds.pdf, public-safety-bonds-1.pdf). Almost none carries a programme year."),
  "why_they_are_not_copies": ("Their figures differ. Affordable housing appears at $2,500,000 in "
                              "AffordableHousingBonds.pdf, $3,400,000 in affordable-housing-bonds-1.pdf, $4,300,000 "
                              "in affordable-housing-bonds.pdf and $5,000,000 in 10-affordable-housing-bonds.pdf. "
                              "Storm sewer NPDES compliance appears at $1,500,000 and $2,000,000. Public "
                              "transportation vehicle replacement at $3,790,500, $4,000,000 and $4,500,000. These are "
                              "different programmes, not editions."),
  "what_can_be_dated": ("Only fragments, and none of them a programme year for the sheets themselves. "
                        "museum-zoo-and-biological-park-and-cultural-facility-bonds.pdf references 2017 and 2022; "
                        "street-bonds.pdf and street-bonds-1.pdf reference 2009 and 2015; library-bonds.pdf "
                        "references 2017; SeniorFamilyCommunityCenter...Bonds.pdf references 2010. Those are project "
                        "references inside scope text, not programme years."),
  "what_would_settle_it": ("The two summaries approved in this batch. The 2015 decade summary schedules every "
                           "department across 2015 to 2023 and the 2015 programme summary gives each purpose's "
                           "allocation; matching a sheet's lead figure against those tables would place it. That is a "
                           "reading task against a document this artifact is recommending, not a research question."),
  "the_pairwise_comparison": {
   "pairs_measured": 41,
   "method": "Every within-family pair, compared with a real difflib sequence ratio over normalized extracted text plus a direct string-equality test. Token coverage was not used, for the reason recorded in the_standard_form_family.",
   "highest_ratio": "0.6155, AffordableHousingBonds.pdf against affordable-housing-bonds.pdf.",
   "lowest_ratio": "0.0157, street-bonds-1.pdf against street-bonds.pdf, two sheets whose filenames differ by one character.",
   "string_equal_pairs": 0,
   "conclusion": "Not one pair in the set is the same document, and most are barely related. The naming convention carries no information about content.",
  },
  "a_caution_on_the_matching": ("A single lead figure is not always enough to separate two sheets. Three of the four storm sewer sheets carry $2,000,000 on the NPDES Stormwater Quality MS4 line, yet their pairwise ratios are 0.1612, 0.1940 and 0.2036 - the rest of each table is different. Match on the full line set, not on the first entry."),
  "each_row_carries": "A distinguishing_content field holding its lead project entry and dollar figure, so the matching can be done from the artifact without refetching.",
  "the_missing_numbers": ("The numbered series runs 1, 2, 5, 6, 8, 9, 10, 11. Numbers 3, 4, 7 and 12 were probed "
                          "directly against six plausible names each — parks and recreation, public transportation, "
                          "street, library, energy and community facilities — and none returned HTTP 200. The gaps "
                          "are real, not a crawl failure."),
 },
 "a_correction_carried_forward": {
  "the_record": "src-feaefc4c87a06768, albuquerque-m-helioscope_shading_1870012_summary.pdf",
  "what_this_artifact_first_said": "Excluded as unattributable third-party software output, on the ground that searches of its extracted text returned no identification of the site it models.",
  "what_is_true": "Page 1 carries, in large type, Museum of Albuquerque (COA#2), 2000 Mountain Rd. NW, Albuquerque, NM 87104. It is the May 17, 2018 shading study for a 714-module City array.",
  "why_the_check_failed": "Its title block is not in the text layer. pdftotext returns 1,561 bytes for three pages, header and footer only, so searching that text for a site name could only return nothing.",
  "the_lesson": "The absence of an expected string in extracted text is evidence about the extraction, not about the document. Render before excluding anything for what it does not say.",
  "where_it_is_decided": "facility-environmental-compliance-cluster-research-2026-09-12.json, approved for addition, alongside the five sibling reports that identified it.",
  "effect_on_this_artifact": "This artifact covers 44 records rather than 45, and has no excluded rows.",
 },
 "the_standard_form_family": {
  "now_six": ("Two were recommended in municipaldevelopment-procurement-cluster-research-2026-09-12.json — on-call "
              "engineering and on-call landscape architectural. Four more are recommended here: the generic template, "
              "architectural, landscape architectural for a named project, and the HUD federally assisted form."),
  "they_are_six_instruments_not_six_copies": ("Measured against the on-call engineering form: architectural returns a "
                                              "real sequence ratio of 0.1919, the HUD form 0.0256. The two landscape "
                                              "forms return 0.4745 against each other. Every pair shares almost all "
                                              "of its vocabulary because they are all City professional services "
                                              "contracts."),
  "the_trap_this_avoided": ("Across all fifteen pairs of the six forms, token coverage runs 0.7658 to 0.9946, and "
                            "eleven of the fifteen pairs sit above 0.95. On coverage alone every one of "
                            "them would read as a duplicate of the others. Real sequence ratios over the same fifteen "
                            "pairs run 0.0256 to 0.6825, and not one pair is string-equal. This is the second slice "
                            "running in which coverage near 1.0 accompanied a real ratio far below it, after the "
                            "Animal Welfare scope pair "
                            "in bond-2013-department-set-cluster-research-2026-09-12.json, and it is the reason that "
                            "artifact's measurement rule was written down."),
  "the_gap_they_close": ("The archive publishes the Rules and Regulations Governing Compensation for Consulting "
                         "Engineers, Architects and Landscape Architects. It records how these consultants are paid "
                         "and, until this batch, nothing about what they sign."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 0,
  "cross_batch_comparisons": "Four standard forms compared against the two recommended from the procurement slice; one summary sheet compared against the 2013 department set.",
  "result": "Nothing in this slice duplicates anything, in the archive or in this batch.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 0,
  "note": ("No duplicates, no supersession, and that is the finding. Forty-five files whose names imply heavy "
           "repetition — four affordable housing sheets, three public transportation sheets, two of several others — "
           "and not one pair is the same document. Forty-one pairs measured, highest ratio 0.6155."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved if 'Agreement' in r['title'] or 'Services Agreement' in r['title']],
   "finding": "Four more standard-form City services agreements: the generic template, architectural, landscape architectural for a named project, and the HUD federally assisted form. With the two from the procurement slice that completes a family of six the archive held none of. Fifteen pairs measured; highest real ratio 0.6825, none string-equal.",
   "recommended_action": "Approve and place on the development process page beside the compensation rules. Label each a blank standard form as posted."},
  {"severity": "substantive-find",
   "affects": ['src-a246ab1fcdb14d3d', 'src-f17b0733dab9b327'],
   "finding": "The 2015 general obligation bond programme summary and the 2015 to 2023 decade schedule, both dated on their own faces. The archive holds 2003, 2007, 2009, 2011, 2013 and 2017 and had nothing for 2015.",
   "recommended_action": "Approve. These two are also the key to the undated sheets held for review below."},
  {"severity": "date-before-publishing",
   "affects": [r["id"] for r in rhr if r.get('package') == 'the_undated_purpose_sheets'],
   "finding": f"{n_sheets + 1} bond purpose sheets and one ballot question with no programme year on their faces, from several different programmes filed under near-identical names. Their figures differ department by department, so they are not copies.",
   "recommended_action": "Match each against the two 2015 summaries approved here and against the archived 2009, 2011, 2013 and 2017 sets. Each row carries its lead entry and figure so the matching needs no refetching."},
  {"severity": "extends-an-earlier-package",
   "affects": ['src-f6c1a087135ceff4'],
   "finding": "The Family and Community Services 2013 summary exists in a third edition, copy2_of, alongside the plain and copy_of editions held for review in the 2013 department set artifact.",
   "recommended_action": "Fold it into that package. The edition question has three answers for this department, not two."},
  {"severity": "corrected-out-of-this-artifact",
   "affects": [],
   "finding": "albuquerque-m-helioscope_shading_1870012_summary.pdf was drafted here as excluded for naming no site. That was wrong: the site is printed on page 1 in text absent from the PDF text layer. It is the 2018 Albuquerque Museum solar shading study.",
   "recommended_action": "It is decided in facility-environmental-compliance-cluster-research-2026-09-12.json and is not a row here. See a_correction_carried_forward."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "probes": "Twenty-four direct probes for the missing numbered sheets 3, 4, 7 and 12; none returned HTTP 200.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": ("%d genuine PDFs and %d legacy OLE2 Word document by leading bytes."
                                        % (bycontainer['PDF'], bycontainer['DOC']))},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. Five are "
                   f"born-digital PDFs with full text layers; the sixth is a legacy Word document, which should be "
                   f"archived in its original format rather than converted. A further {len(rhr)} records totalling "
                   f"{rhr_bytes:,} bytes are held at requires human review pending a programme year."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id; this slice contains "
                      "no duplicates and no supersession, which is itself the finding given how repetitive the "
                      "filenames look. Every requires-human-review row carries a priority and a package name, and "
                      "every purpose sheet carries a distinguishing_content field holding its lead project and dollar "
                      "figure so the programme matching can be done from this artifact alone. One row belongs to a "
                      "package opened in another artifact and names it. Every row carries a leading_bytes field. "
                      "Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the numbered-sheet probes were read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
