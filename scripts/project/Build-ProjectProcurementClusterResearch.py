"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Seventh slice of the municipaldevelopment/documents lane: the
project-specific engineering and procurement records.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\project-procurement-records-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md6')

DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'
CAPITAL = 'content/city-data/capital-spending.md'
TRANSIT = 'content/transportation/transit/abq-ride.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
PARKSREC = 'content/public-works/parks-recreation.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

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

CONTAINER = {'25504446': 'PDF', '504b0304': 'DOCX', '3c21444f': 'HTML'}

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


APPROVED = [
 ('src-bee26bf4c7d2ea17', "2022 Citywide On-Call Engineering Services: Scope of Projects", "2022",
  ("The City's statement of what its 2022 citywide on-call engineering contracts cover, running from roadway, "
   "drainage and traffic evaluations through design, bid documents and construction phase services for the work "
   "called off against them."),
  "Headed CITY OF ALBUQUERQUE, DEPARTMENT OF MUNICIPAL DEVELOPMENT, 2022 CITYWIDE ON-CALL ENGINEERING SERVICES, Project Number: 720600, 720700, 720800, over a SCOPE OF PROJECTS listing.",
  "720600, 720700, 720800", DEVPROC, [{"page": CAPITAL, "reason": "On-call engineering is the delivery mechanism for much of the Capital Implementation Program."}]),
 ('src-dae0e5bc39e97e1a', "Citywide On-Call Engineering Services for Transportation and Storm Drainage: Scope of Projects", None,
  ("The City's scope statement for its transportation and storm drainage on-call engineering contract, covering "
   "green stormwater infrastructure evaluations, roadway and drainage study work, and the design and construction "
   "phase services that follow."),
  "Headed CITY OF ALBUQUERQUE, DEPARTMENT OF MUNICIPAL DEVELOPMENT, CITYWIDE ON-CALL ENGINEERING SERVICES FOR TRANSPORTATION AND STORM DRAINAGE, Project Numbers: 138.02, over a SCOPE OF PROJECTS listing that opens on Green Stormwater Infrastructure evaluations.",
  "138.02", DEVPROC, [{"page": 'content/public-works/stormwater-drainage.md', "reason": "The scope is half stormwater work, including green stormwater infrastructure."}]),
 ('src-1233bd4667df880b', "University Boulevard at Lomas Boulevard Reconstruction: Scope of Project", None,
  ("The City's scope statement for the University at Lomas reconstruction sets out the roadway, drainage and "
   "utility study work required, then the design, bid document and construction phase services the project "
   "needs."),
  "Headed CITY OF ALBUQUERQUE, DEPARTMENT OF MUNICIPAL DEVELOPMENT, UNIVERSITY BOULEVARD AT LOMAS BOULEVARD RECONSTRUCTION, Project Number: 724692, over a SCOPE OF PROJECT listing.",
  "7246.92", ROADWAY, [{"page": DEVPROC, "reason": "The scope is written in the City's standard pre-submittal form."}]),
 ('src-4f03b2e57d8b3737', "98th Street and Benavides Road Intersection Improvements: Pre-Submittal Meeting Presentation", "2020",
  ("The City's presentation on its 98th Street and Benavides Road intersection project sets out the location, the "
   "improvements planned, the schedule through design completion and the funding behind the work."),
  "Titled 98th STREET AND BENAVIDES ROAD INTERSECTION IMPROVEMENTS, CPN 7697.90, Department of Municipal Development Engineering Division, OCTOBER 2, 2020, PRE-SUBMITTAL MEETING. Carries project location, and a PROJECT SCHEDULE & FUNDING slide giving design completion by Spring 2022.",
  "7697.90", ROADWAY, []),
 ('src-d2235c5ab30cf715', "Request for Proposals: A/E Consultant Services for a New General Aviation Terminal at Double Eagle II Airport", "2024",
  ("The City's request for proposals for the design of a new general aviation terminal at Double Eagle II Airport "
   "states the project, the submission deadline, the insurance and format requirements, and where the full request "
   "is published."),
  "Headed City of Albuquerque, Notice of Requests for Proposals from A/E Consultant Services for the Design of a New General Aviation Terminal at the Double Eagle II Airport, Project No: 7223.03, proposals due Wednesday, February 28, 2024 by 3:00pm.",
  "7223.03", PROJECTS, [{"page": CAPITAL, "reason": "A capital project procurement."}]),
 ('src-c1907ae0fa973eb2', "Request for Proposals: Citywide On-Call Traffic Engineering", "2025",
  ("The City's request for proposals for its citywide on-call traffic engineering contract states the project "
   "number, the submission deadline and format, and where the full request for proposals is published."),
  "Headed City of Albuquerque, Notice of Requests for Proposals from CITY WIDE ON-CALL TRAFFIC ENGINEERING, Project No. 183.02, proposals due Wednesday, November 12, 2025. Reaches this slice under the filename mf-3604-10-20-25.pdf.",
  "183.02", DEVPROC, [{"page": ROADWAY, "reason": "Traffic engineering work on the City street network."}]),
 ('src-ff1c069af719b528', "Request for Proposals: Architectural Consultants for Asia at the ABQ BioPark Zoo", "2018",
  ("The City's request for proposals for the Asia exhibit at the BioPark Zoo describes a new multi-level Asian "
   "exhibit with site development, containment perimeter, entry gate and animal holding, at an approximate "
   "construction cost of fifteen million dollars."),
  "Headed CITY OF ALBUQUERQUE, NOTICE OF REQUEST FOR PROPOSALS FROM ARCHITECTURAL CONSULTANTS FOR ASIA AT ABQ BIOPARK ZOO, Project No. 7303.95, proposals due Wednesday, July 11, 2018. A DOCX, leading bytes 504b0304, read from word/document.xml.",
  "7303.95", PARKSREC, [{"page": CAPITAL, "reason": "A fifteen-million-dollar capital project."}]),
 ('src-c40a9e760b69fb42', "Pre-Submittal Conference Information Sheet: ABQ BioPark Children's Fantasy Garden Renovation", None,
  ("The City's information sheet for the Children's Fantasy Garden renovation explains what the BioPark is seeking, "
   "the experience it requires of bidders, the public engagement expected, and the range of renovation it will "
   "consider."),
  "Headed Project No: 6353.93; Abq BioPark Children's Fantasy Garden, Pre-Submittal Conference Information Sheet. Records that the garden opened in 2001, that theme park and family project experience is required, and that the project has potential for CMAR with no animal component anticipated.",
  "6353.93", PARKSREC, [{"page": CAPITAL, "reason": "A capital renovation of a City facility."}]),
 ('src-a717db006dc435fe', "Selection Advisory Committee Process Presentation", "2024",
  ("The City's presentation on how its Selection Advisory Committee chooses design consultants explains the process, "
   "the December 2022 rules update, and the raised expedited design services threshold that lets user departments "
   "select directly."),
  "Titled Selection Advisory Committee (SAC) PowerPoint, April 2024. Records the Updated SAC Rules and Regulations of December 2022 and the rise in the Expedited Design Services limit from $25,000 to $150,000.",
  None, DEVPROC, [{"page": CAPITAL, "reason": "The committee selects the consultants who deliver the capital programme."}]),
 ('src-feceff17d2f6b2cf', "Agreement and Insurance Certification, Capital Implementation Program", None,
  ("The City's certification form has a proposing firm confirm it has reviewed the standard engineering, "
   "architectural or landscape architectural services agreement and will enter into it and meet its insurance "
   "requirements if selected."),
  "Headed City of Albuquerque Capital Implementation Program, Agreement and Insurance Certification, with Project Name, Project Number, Date and Firm Name left blank.",
  None, DEVPROC, [{"page": CAPITAL, "reason": "Required of every firm proposing on a Capital Implementation Program project."}]),
 ('src-3f3ee8935635a62f', "Children's Fantasy Garden Deficiency List, December 9, 2021", "2021",
  ("The City's condition assessment of the Children's Fantasy Garden lists each defect found by area, from the "
   "clogged Doolittle Fountain to walkways that fail accessibility standards, and prices a low, medium and high cost "
   "remedy for each."),
  "Tabulated by CFG Area, Number, Deficiency, and Low, Medium and High Cost Solution. Records the Doolittle Fountain clogged and not running, pedestrian walkways non-compliant for vertical surface discontinuity, drip irrigation not working, and landscape overhanging pathways.",
  "6353.93", PARKSREC, [{"page": CAPITAL, "reason": "The condition record behind a capital renovation."}]),
 ('src-a6cabf80272f6d7d', "Children's Fantasy Garden Accessibility Survey Markup, November 3, 2021", "2021",
  ("The City's accessibility survey marks 28 measured locations on an aerial view of the Children's Fantasy Garden "
   "and gives the longitudinal and cross slope at each, identifying which stretches of path are inaccessible under "
   "accessibility standards."),
  "A single-page aerial markup with 28 numbered extents of measurement and concern and a slope reading for each, from 0.3% to 15.8%, with items 20 and 21 annotated inaccessible for ADA and a note that grades are measured from point of inflection to point of inflection.",
  "6353.93", PARKSREC, [{"page": CAPITAL, "reason": "The survey behind a capital renovation."}]),
 ('src-c11e4d79949d1e86', "ABQ RIDE Yale Maintenance Facility Assessment: Conceptual Estimate of Probable Construction Cost", "2015",
  ("The consultant's conceptual cost estimate for redeveloping the Yale bus facility prices three fleet options and "
   "their sub-options for reusing or replacing the operations and maintenance buildings, with site work, demolition, "
   "equipment and a contingency."),
  ("A letter of June 25, 2015 from a Houston engineering consultancy to Bruce Rizzieri, Director, ABQ Ride, "
   "transmitting the estimate. Prices Option 1 40-foot fixed route plus paratransit, Option 2 40-foot and 60-foot "
   "plus paratransit, and Option 3 paratransit only, each with sub-options A, B and a second-floor operations "
   "variant. Carries a 25% contingency for the conceptual stage."),
  "5798.82", TRANSIT, [{"page": CAPITAL, "reason": "A capital cost estimate for a City facility."}]),
 ('src-5abd331d18df47d5', "Questions and Answers: New General Aviation Terminal at Double Eagle II Airport", "2024",
  ("The City's answers to bidders on the Double Eagle II general aviation terminal record its position on "
   "certification and other requirements of the design, given after the mandatory pre-submittal meeting for the "
   "project."),
  "Dated February 6, 2024, headed Q & A after mandatory Zoom pre-submittal meeting for Project No: 7223.03. Records that City projects are not LEED Certified.",
  "7223.03", PROJECTS, []),
 ('src-9df858c530430f8e', "Questions and Answers: ABQ BioPark Children's Fantasy Garden Renovation", "2024",
  ("The City's answers to bidders on the Children's Fantasy Garden renovation set out the total project budget, how "
   "much of it is soft cost, the maximum allowable construction cost, and how the advertised compensation relates to "
   "them."),
  ("Dated June 17, 2024, headed Questions regarding Project No: 6353.93. Records a total project budget of $5 "
   "million, 20% or $1 million in soft costs, $4 million of potential maximum allowable construction cost, and an "
   "estimated compensation of $750,000, about 18.75% of that construction cost."),
  "6353.93", PARKSREC, [{"page": CAPITAL, "reason": "It states the capital budget for the project."}]),
 ('src-b450bb1e49b889c3', "Questions and Answers: Yale Operations and Maintenance Facility Site Assessment and Design", None,
  ("The City's answers to bidders on the Yale facility project explain how the work is phased, that ABQ RIDE "
   "estimates a year for the first phase, and that later phases depend on the department securing further "
   "funding."),
  "Headed Project No: 5798.82; Architectural Consultant for Site Assessment and Design of the Yale Operations & Maintenance Facility, Questions and Answers.",
  "5798.82", TRANSIT, []),
 ('src-62e38196b34a1e8b', "Questions and Answers: Citywide On-Call Architectural Services, Project 7232.00", "2024",
  ("The City's answers to bidders on its citywide on-call architectural contract confirm that a firm already holding "
   "an on-call architectural agreement with the City is excluded from proposing, whatever department that agreement "
   "sits with."),
  "Dated June 17, 2024, headed Questions regarding: Project No: 7232.00; Architectural Consultants for City Wide On-Call Architectural Services.",
  "7232.00", DEVPROC, []),
 ('src-f1412e3759ceb01d', "Questions and Answers: Citywide On-Call Architectural Services, Project 7303.99", "2023",
  ("The City's answers to bidders on its citywide on-call architectural contract identify who prepared the facility "
   "plan refresh and confirm that firm is not barred from joining a proposing team as a consultant."),
  ("Dated June 5, 2023, headed Questions regarding: Project No: 7303.99; Architectural Consultants for City Wide "
   "On-Call Architectural Services. The filename reads 7373-99; the document reads 7303.99. Title it from the "
   "document."),
  "7303.99", DEVPROC, []),
]

FILENAME_ONLY = {
 'src-3f3ee8935635a62f': (
   "ABQ BioPark Children's Fantasy Garden", '6353.93', ['CFG', 'Doolittle', 'Labyrinth'],
   ("The document never writes the garden's name. It abbreviates it to CFG in its own column heading, and the "
    "features it lists - the Doolittle Fountain, the Labyrinth - are features of the Children's Fantasy Garden, "
    "which the pre-submittal information sheet for 6353.93 describes. The project number itself appears only in "
    "the filename.")),
 'src-a6cabf80272f6d7d': (
   "ABQ BioPark Children's Fantasy Garden", '6353.93', ['Mushroom', 'Labyrinth'],
   ("The weakest attribution in the slice, and it is recorded as such. The text layer is a list of slope readings "
    "and names no site at all; the only identifying words in it are two features, the Mushroom Tunnel and the "
    "Labyrinth, which the deficiency list and the pre-submittal sheet place in the Children's Fantasy Garden. The "
    "rendered page is an aerial of that garden. The project number appears only in the filename.")),
 'src-c11e4d79949d1e86': (
   'ABQ RIDE Yale Maintenance Facility', '5798.82', ['Yale', 'ABQ Ride'],
   ("The document is headed Re: ABQ Ride Yale Maintenance Facility Assessment and is addressed to the Director of "
    "ABQ Ride, so its subject is beyond doubt. It prints no project number; 5798.82 comes from the pre-submittal "
    "documents for the same facility, not from this file, and not from its filename either - the filename is just "
    "cost-estimate.pdf.")),
}

approved = []
for i, title, date, desc, ev, proj, canon, cross in APPROVED:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None,
              "evidence": ev, "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if proj and i in FILENAME_ONLY:
        subject, num, terms, basis = FILENAME_ONLY[i]
        r["project_attribution"] = {
            "project": subject,
            "number": num,
            "number_stated_in_the_document": False,
            "evidence_terms_present_in_the_document": terms,
            "basis": basis,
        }
    elif proj:
        r["city_project_number"] = proj
    approved.append(r)

# ------------------------------------------------------------------ duplicate
dup = [{
 **row('src-348b198176600aa7', "duplicate"),
 "canonical_id": 'src-a6cabf80272f6d7d',
 "title_for_reference": "Children's Fantasy Garden Accessibility Survey Markup, November 3, 2021, second export",
 "relationship": ("The same document as its canonical, published twice under different names. The longer name adds "
                  "percent-grade-extents and amp-003, which reads like an addendum number in the procurement "
                  "package; it describes what the sheet shows and does not make it a different sheet."),
 "how_it_was_established": ("Byte hashing said different: 741,873 against 740,221 bytes, different SHA-256. "
                            "Normalized text is string-equal with a real sequence ratio of 1.0000. The two were then "
                            "rendered to PNG at the same scale and the rendered pages are byte-identical - the same "
                            "5,090,954-byte image with the same SHA-256. The PDF containers differ by 1,652 bytes; "
                            "the documents do not differ at all."),
 "why_this_one_is_the_copy": ("Neither carries a revision stamp and neither filename is a recency signal, so this "
                              "follows the rule already applied to the copy_of editions: the plainer name is the "
                              "primary object and is canonical."),
}]

# ---------------------------------------------------- requires human review
rhr = [{
 **row('src-c2c171a89b600fa8', "requires human review"),
 "draft_title": "Technical Approach: Opportunities for Innovation, proposal evaluation prompt",
 "question_for_human": "Confirm which project this prompt was issued for, or publish it as an undated general selection prompt.",
 "why_not_decided_here": ("Its content is a City evaluation prompt with real substance - it asks proposers how their "
                          "design will empower small, minority and disadvantaged groups, how an under-budget "
                          "construction estimate affects end users, and how the design will support cultural and "
                          "community inclusivity. But the document names no project, no department and no date. The "
                          "only identification is the filename's 7204-00, and this lane has now twice found a "
                          "filename that contradicts its own document."),
 "distinguishing_content": "Technical Approach: Opportunities for Innovation; opens on incorporating new ideas and practices to empower small/minority/disadvantaged groups.",
 "package": "unidentified_procurement_prompt",
 "priority": 1,
}]

# ------------------------------------------------------------------- excluded
ROSTERS = [
 ('src-79863973bfbc7332', "5798.82 pre-submittal sign-in", "A forwarded email containing the Zoom chat roll of a September 2022 pre-submittal meeting."),
 ('src-debad5dae8789593', "Sign-in sheet, February 5, 2024", "The roll of the mandatory Zoom pre-submittal meeting for the Double Eagle II terminal project."),
 ('src-19209afc44e66148', "7700.99 pre-submittal sign-in sheet", "The roll of the May 2, 2024 mandatory pre-submittal for architectural consultants on AIS pre-security fire protection."),
 ('src-ce7b73f98ea2dc28', "5798.82 site walk-through attendance", "The walk-through notice with a thirteen-name attendance list appended."),
]
NOTICES = [
 ('src-a7b4e83d08d2713b', "5798.82 site walk-through notice", "Site Assessment and Design of the Yale Operations & Maintenance Facility; non-mandatory walk-through, Monday, September 12, 2022, 11:00 AM."),
 ('src-8fd77d0f2a7c3eab', "6370.93 site walk-through notice", "Architectural Consultants for Albuquerque Museum Education Center; non-mandatory walkthrough, Monday, July 18, 10:00 AM."),
 ('src-cf3ee217fcc745bb', "6353.93 site walk-through notice", "Abq BioPark Children's Fantasy Garden; non-mandatory walk-through, Friday, June 21, 2024, 9:00 AM."),
 ('src-f92d9eafb7e1a13f', "7011.95 site walk-through notice", "Brillante Explora Early Learning Center; non-mandatory walk-through, Thursday, August 11, 2022, 8:30 AM."),
]

excluded = []
for i, label, what in ROSTERS:
    r = row(i, "excluded")
    r.update({"title_for_reference": label, "what_it_is": what,
              "exclusion_reason": ("A meeting roster. It compiles the names, and in three of the four cases the "
                                   "working email addresses, of named private individuals who attended a City "
                                   "procurement meeting. It records nothing about the project that the project's own "
                                   "documents do not, and republishing a roster of private individuals' contact "
                                   "details carries a cost with no archival return."),
              "category": "procurement meeting roster",
              "package": "the_meeting_rosters"})
    excluded.append(r)
for i, label, what in NOTICES:
    r = row(i, "excluded")
    r.update({"title_for_reference": label, "what_it_is": what,
              "exclusion_reason": ("Expired meeting logistics. A single page announcing where and when to meet for a "
                                   "site visit on a date now years past. It carries no scope, no budget, no "
                                   "schedule and no finding."),
              "category": "expired meeting logistics",
              "package": "the_walk_through_notices"})
    excluded.append(r)
r = row('src-15080d936785b6d8', "excluded")
r.update({"title_for_reference": "selection-advisory-committee-documents, directory listing",
          "what_it_is": "The City's web page for the directory, not a document in it.",
          "exclusion_reason": ("Not a document. The URL returns an HTML page, leading bytes 3c21444f, whose extracted "
                               "text is the City's site navigation. The two files that actually sit in this "
                               "directory are decided in this artifact in their own right."),
          "category": "directory listing, not a document",
          "package": "not_a_document"})
excluded.append(r)

rows = approved + dup + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (set(SLICE) - set(ids), set(ids) - set(SLICE))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
excluded_bytes = sum(r["size_bytes"] for r in excluded)
projects = sorted({r["city_project_number"] for r in approved if r.get("city_project_number")})
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "project-procurement-records-cluster-research-2026-09-12",
 "lane": "Claude research lane: the project-specific engineering and procurement records in www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the seventh slice of the municipaldevelopment/documents lane.",
 "cluster": ("What the City posts while it is hiring a designer for a capital project: scope statements, requests "
             "for proposals, questions and answers, site walk-through notices, sign-in sheets, and the condition "
             "records behind one renovation."),
 "scope": "All 29 uncovered candidates in this group. The coverage gate is asserted in the generator.",
 "brief": ("Tie each file to its City project number and decide whether procurement process papers for a single "
           "project belong in a public archive at all."),
 "brief_finding_on_project_numbers": ("Every file that prints a project number was tied to one, and the numbers are "
                                      "recorded on the rows as city_project_number: " + ", ".join(projects) + ". Two "
                                      "files carry no project number at all - the Selection Advisory Committee "
                                      "presentation and the agreement and insurance certification, both process records "
                                      "rather than project records - and one names none and is held for review. "
                                      "Three more are recorded under project_attribution rather than "
                                      "city_project_number, because their number exists only in their filename; see "
                                      "three_numbers_that_come_from_the_filename_alone."),
 "brief_finding_on_whether_they_belong": {
  "the_answer": ("Not as a class. The question splits cleanly, and the split is not between important and "
                 "unimportant projects but between what a document says and what it merely records having "
                 "happened."),
  "what_is_kept": ("Anything that states scope, budget, schedule, condition or a City position: the on-call scope "
                   "statements, the requests for proposals, the questions and answers - which is where the City "
                   "puts its budget figures and its policy on the record - the Children's Fantasy Garden condition "
                   "survey and deficiency list, the Yale cost estimate, and the presentation explaining how "
                   "consultants are chosen."),
  "what_is_not": ("Meeting rosters and expired meeting logistics. A sign-in sheet records who came; a walk-through "
                  "notice records where to stand on a morning in 2022. Neither says anything about the project that "
                  "the project's own documents do not."),
  "the_privacy_point": ("Three of the four rosters are lists of named private individuals with their working email "
                        "addresses. Republishing those on a public archive has a real cost and no archival return. "
                        "This is the reason the rosters are excluded as a group rather than judged one at a time."),
  "what_this_does_not_say": ("Nothing here is excluded for being procurement. The requests for proposals are "
                             "procurement documents and all three are recommended, because each one states what the "
                             "City wanted built and what it expected it to cost."),
 },
 "method": ("Fetched every candidate and measured byte length and SHA-256 from the fetched bytes, verifying every "
            "container by leading bytes; one is an HTML page and one an OOXML document, and neither was assumed from "
            "its extension. Read each file for its project number, department and date rather than taking them from "
            "the filename. Compared every checksum within the slice and against the 1,612 checksummed inventory "
            "records. Where two files looked alike, compared normalized text with a real sequence ratio and a "
            "string-equality test, then rendered both pages and compared the rendered images."),
 "classification_only": True,
 "shared_state_written": [],
 "a_duplicate_that_hashing_could_not_find_and_rendering_settled": {
  "the_pair": "cfg-survey-markup_2021-11-03-6353-93.pdf and cfg-survey-markup_2021-11-03-percent-grade-extents_amp-003-6353-93.pdf",
  "what_each_method_said": {
   "byte_hashing": "Different. 741,873 against 740,221 bytes, different SHA-256.",
   "normalized_text": "String-equal, real sequence ratio 1.0000, token coverage 1.0000 both directions.",
   "rendering": "Identical. Both rendered to a 5,090,954-byte PNG with the same SHA-256.",
  },
  "why_rendering_was_needed": ("Text equality alone would not have been enough here. This is a single-page aerial "
                               "markup: almost all of its content is one raster image, and its text layer is only "
                               "the annotation list beside it. Two sheets could share every annotation and carry "
                               "different drawings. Rendering compares what a reader actually sees."),
  "the_method_to_keep": ("Render and hash. When two candidates differ in bytes but not in text, and their substance "
                         "is graphical, render both at the same scale and hash the images. It is the only comparison "
                         "in this run that answers the question directly."),
  "and_it_cuts_the_other_way_too": ("The same technique, applied in the previous slice, overturned an exclusion: a "
                                    "file excluded for naming no site names it in large type on page 1, in text that "
                                    "is not in its text layer. Rendering settled a false difference here and a false "
                                    "absence there."),
 },
 "three_numbers_that_come_from_the_filename_alone": {
  "count": len(FILENAME_ONLY),
  "the_files": ["cfg-deficiency-list_2021-12-09-6353-93.pdf", "cfg-survey-markup_2021-11-03-6353-93.pdf",
                "cost-estimate.pdf"],
  "what_is_true": ("None of the three prints a project number anywhere, and their subjects are not equally "
                   "certain either. The Yale cost estimate is headed with its facility and addressed to that "
                   "department's director, so its subject is beyond doubt. The two Children's Fantasy Garden "
                   "files never write the garden's name: the deficiency list abbreviates it to CFG and lists the "
                   "Doolittle Fountain and the Labyrinth, and the survey markup names no site at all - its text "
                   "layer is slope readings, and the only identifying words in it are Mushroom Tunnel and "
                   "Labyrinth. Each row records the evidence terms actually present in its own text."),
  "why_it_is_recorded_separately": ("This lane has found a filename contradicting its own document in four slices "
                                    "running. A number taken from a filename is an attribution and must not be "
                                    "presented as something the document states. These three carry a "
                                    "project_attribution object with its basis written out, rather than a "
                                    "city_project_number field."),
  "how_it_was_caught": ("The validation harness checks that every project number claimed on a row occurs in that "
                        "file's extracted text. It failed on these three, and on a fourth where the document "
                        "prints 720600 and the row had been written 7206.00. It then failed a second time, on a "
                        "first draft of this very block that claimed all three name their subject unmistakably: "
                        "two of them do not, and the check that every asserted evidence term occurs in the text "
                        "is what said so."),
 },
 "filenames_that_contradict_their_documents": {
  "count": 2,
  "cases": [
   "7373-99-informational-sheet.pdf is headed Project No: 7303.99.",
   "mf-3604-10-20-25.pdf is a request for proposals for citywide on-call traffic engineering, Project No. 183.02; its filename records neither.",
  ],
  "the_standing_rule": ("Title from the document. This lane has now found filename errors in four slices - a body "
                        "and a date wrong on an Energy Council file, two misspelled facilities in the stormwater "
                        "set, and these two - and not one of them was visible without opening the file."),
 },
 "the_meeting_rosters": {
  "count": len(ROSTERS),
  "what_they_contain": ("Names of attending architects, engineers and City staff. Three also carry working email "
                        "addresses; the fourth, the Yale walk-through attendance, carries thirteen names without "
                        "addresses."),
  "how_the_fourth_was_identified": ("site-walk-through-attendance.pdf and 5798-82-sitewalkthrough.pdf are the same "
                                    "notice, at a sequence ratio of 0.7755 with the notice fully contained in the "
                                    "attendance file, token coverage 1.0000 one way and 0.7190 the other. Reading "
                                    "the diff shows exactly what the longer file adds: a thirteen-name attendance "
                                    "list."),
  "decision": "Excluded as a group, on the reasoning in brief_finding_on_whether_they_belong.",
 },
 "the_walk_through_notices": {
  "count": len(NOTICES),
  "decision": "Excluded as expired logistics.",
  "what_is_preserved_here_instead": ("Each notice is the only trace in this slice of its project, so the project "
                                     "numbers and titles are recorded on the rows rather than lost with the files: "
                                     "6370.93 Architectural Consultants for Albuquerque Museum Education Center, and "
                                     "7011.95 Brillante Explora Early Learning Center. Neither project appears "
                                     "anywhere else in this slice."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 0,
  "result": "Nothing here duplicates anything the archive holds. The one duplicate in the slice is internal to it.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 2,
  "found_by": "One by text equality confirmed by rendering; one by containment, which established that a notice and an attendance sheet are the same notice with a roster appended.",
  "note": "Neither was findable by hashing. Both files in the duplicate pair are genuine distinct byte sequences of the same document.",
 },
 "integration_flags": [
  {"severity": "method",
   "affects": ['src-348b198176600aa7', 'src-a6cabf80272f6d7d'],
   "finding": "A duplicate that byte hashing called different and that text comparison could not prove: a single-page graphical markup whose text layer is only its annotation list. Rendering both pages produced byte-identical images.",
   "recommended_action": "Adopt render-and-hash for graphical candidates that differ in bytes but not in text. Detail in a_duplicate_that_hashing_could_not_find_and_rendering_settled."},
  {"severity": "substantive-find",
   "affects": ['src-3f3ee8935635a62f', 'src-a6cabf80272f6d7d', 'src-9df858c530430f8e', 'src-c40a9e760b69fb42'],
   "finding": "A complete condition record for the ABQ BioPark Children's Fantasy Garden: a 28-point accessibility slope survey, a priced deficiency list with low, medium and high cost remedies, the renovation's scope, and the City's own statement of its $5 million budget and $4 million maximum allowable construction cost.",
   "recommended_action": "Approve as a set. This is the most complete picture of a single City facility renovation in the slice."},
  {"severity": "substantive-find",
   "affects": ['src-c11e4d79949d1e86'],
   "finding": "A 2015 conceptual construction cost estimate for redeveloping the ABQ RIDE Yale maintenance facility, pricing three fleet options and their sub-options, addressed to the Transit director. It reaches the inventory under the filename cost-estimate.pdf and identifies neither its project nor its subject in that name.",
   "recommended_action": "Approve and title it from the document."},
  {"severity": "privacy",
   "affects": [r['id'] for r in excluded if r.get('package') == 'the_meeting_rosters'],
   "finding": "Four procurement meeting rosters, three of them lists of named private individuals with their working email addresses.",
   "recommended_action": "Exclude. Do not publish; the reasoning is recorded in brief_finding_on_whether_they_belong."},
  {"severity": "title-from-the-document",
   "affects": ['src-f1412e3759ceb01d', 'src-c1907ae0fa973eb2'],
   "finding": "Two filenames that contradict or omit what their document says: 7373-99 for a document headed 7303.99, and mf-3604-10-20-25 for a request for proposals on Project No. 183.02.",
   "recommended_action": "Title both from the document."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": ("%d genuine PDFs, %d OOXML document and %d HTML page by leading bytes. The "
                                        "HTML one is a directory listing and is excluded as not a document."
                                        % (bycontainer['PDF'], bycontainer['DOCX'], bycontainer['HTML']))},
 "approved_for_addition": approved,
 "duplicate": dup,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. One is an OOXML "
                   f"document and should be archived in its original format rather than converted. The "
                   f"{len(excluded)} excluded records, {excluded_bytes:,} bytes, are not to be archived at all."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. One row carries a canonical_id and it is in this "
                     "artifact. Approved rows carry a city_project_number where the document states one, so the "
                     "records can be grouped by project rather than by filename. Two rows must be titled from the "
                     "document rather than the filename and say so. Every row carries a leading_bytes field. Sizes "
                     "and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the excluded rosters were read only to establish what they contain and are not reproduced here"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
