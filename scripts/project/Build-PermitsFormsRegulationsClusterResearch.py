"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Eighth slice of the municipaldevelopment/documents lane: the
permits, forms, applications and regulations group.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\permits-forms-regulations-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md7')

DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'
CAPITAL = 'content/city-data/capital-spending.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
SPEED = 'content/transportation/roadway-projects/speed-management.md'
STORM = 'content/public-works/stormwater-drainage.md'
BIKE = 'content/transportation/bicycling/bike-plans.md'
FACIL = 'content/public-works/city-facilities.md'

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
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('id'):
                PRIOR.add(r['id'])
assert not (set(SLICE) & PRIOR), sorted(set(SLICE) & PRIOR)

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML', 'd0cf11e0': 'DOC'}

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


# id, title, date, group, description, evidence, canonical, crosses
APPROVED = [
 ('src-ef4ac437d38d7d61',
  "Regulation Governing the Award and Rejection of Bids and Offers and Debarment of Contractors for Public Works Projects",
  "2021", "regulations",
  ("The City's rule for awarding public works contracts governs advertising, the receipt and opening of bids, "
   "grounds for rejection, qualification of the apparent low bidder, contract execution, emergency procurement and "
   "the debarment of contractors."),
  ("A forty-page regulation whose table of contents runs from Authority and Purpose and Policy through Emergency "
   "Procurement at section 15.0. It carries no cover page; every page is footer-dated 1/22/21."),
  DEVPROC, [{"page": CAPITAL, "reason": "It governs the award of the City's public works contracts."}]),
 ('src-b8b28358abc9a2de',
  "Regulations Governing Public Right of Way Excavation and Barricading for Fiber Infrastructure Purposes",
  "2025", "regulations",
  ("The City's rules for fiber installation in the public right of way set out how excavation and barricading for "
   "fiber infrastructure is authorised and controlled, citing them by their own short title and stating their "
   "authority and scope."),
  ("Headed CITY OF ALBUQUERQUE, REGULATIONS GOVERNING PUBLIC RIGHT OF WAY EXCAVATION AND BARRICADING FOR FIBER "
   "INFRASTRUCTURE PURPOSES, with section 1 TITLE giving the short citation and section 2 AUTHORITY AND SCOPE. The "
   "filename records final fiber rules dated 6-27-25."),
  DEVPROC, [{"page": ROADWAY, "reason": "The rules govern work in the City street right of way."}]),
 ('src-6076ae4aeac6bc39',
  "Regulation Governing Requests for the City of Albuquerque to Serve as Fiscal Agent of a State Capital Outlay Project",
  "2023", "regulations",
  ("The City's rule for state capital outlay awards sets out how an outside entity asks the City to act as fiscal "
   "agent for a project the Legislature has funded, and what the City requires before it will accept that role."),
  ("Titled City of Albuquerque, Regulation Governing Requests for the City of Albuquerque to Serve as Fiscal Agent "
   "of a State Capital Outlay Project, promulgated by the Department of Municipal Development, Effective Date "
   "1/30/2023. Signed through DocuSign; the envelope ID appears on the cover."),
  CAPITAL, [{"page": DEVPROC, "reason": "It is a promulgated departmental regulation."}]),
 ('src-9c4d003600899fac',
  "Residential Parking Permit Regulation, with the transmitting inter-office memorandum",
  "2022", "regulations",
  ("The City's residential parking permit rule, sent to the Chief Administrative Officer by the Municipal "
   "Development director, governs how on-street permit zones are established and how residents obtain and use "
   "permits within them."),
  ("Opens on a City of Albuquerque, Department of Municipal Development inter-office memorandum dated October 18, "
   "2022, from Patrick Montoya, Director, to Lawrence Rael, Chief Administrative Officer. Signed through DocuSign."),
  ROADWAY, [{"page": DEVPROC, "reason": "A promulgated departmental regulation."}]),
 ('src-268a2054bd39dc7b',
  "2027-2036 Decade Plan for Capital Improvements: General Obligation Bond Program Instruction Book",
  "2027", "capital programme",
  ("The City's instruction book for its 2027 general obligation bond programme sets out the decade plan for capital "
   "improvements through 2036 and the process departments follow to get a project into it."),
  ("Titled G.O. BOND PROGRAM, City of Albuquerque, CAPITAL IMPLEMENTATION PROGRAM, 2027-2036 DECADE PLAN FOR "
   "CAPITAL IMPROVEMENTS, with project imagery including the Conway Wood Northwest Multi-Generational Center and "
   "the Paseo Expansion."),
  CAPITAL, [{"page": PROJECTS, "reason": "The decade plan is where City capital projects begin."}]),
 ('src-dbd1f5327b59e1ee',
  "2023 General Obligation Bond Program Instruction Booklet",
  "2023", "capital programme",
  ("The City's instruction booklet for its 2023 general obligation bond programme opens on the mayor, the "
   "administration and the councillors of the day and sets out how departments prepare and submit projects for the "
   "programme."),
  ("Opens on the Mayor and City Councillors of the time, with Timothy M. Keller as mayor, Isaac Benton as council "
   "president for District 2, Dan Lewis as vice-president for District 5, Sarita Nair as Chief Administrative "
   "Officer and Lawrence Rael as Chief Operations Officer."),
  CAPITAL, [{"page": PROJECTS, "reason": "The programme that funds City capital projects."}]),
 ('src-ed393fa3ad5dd15c',
  "Operating and Maintenance Expense Analysis: Project Request Form Instructions, 2027 Programme",
  "2027", "capital programme",
  ("The City's instructions tell departments how to state the operating and maintenance consequences of a requested "
   "capital project, identifying new personnel, recurring and non-recurring costs, and revenue changes from the "
   "2028 fiscal year forward."),
  ("Headed Instructions, Operating & Maintenance Expense Analysis, explaining the purpose of this section of the "
   "PRF and requiring costs to be identified starting in FY 2028 and looking forward through FY 2032."),
  CAPITAL, []),
 ('src-29e0c2c5bba9cf59',
  "Guidelines for Consultants and Contractors on the Preparation of Contract Documents",
  None, "process guidance",
  ("The City's contract services guidance tells consultants and contractors how to prepare the documents a City "
   "contract requires, issued as a memorandum from the Municipal Development contract specialist to the consultant "
   "on a project."),
  "Headed Department of Municipal Development, Contract Services, Memorandum, To: Consultant, From: Samantha A. Sanchez, Contract Specialist.",
  DEVPROC, []),
 ('src-5f4d0d85d6c85eaf',
  "City of Albuquerque Project Labor Agreement",
  "2025", "process guidance",
  ("The City's project labor agreement sets the terms under which construction work on a covered City project is "
   "performed, taking effect on the owner's notice to proceed, with articles running from purpose through the "
   "administration of the agreement."),
  ("Headed CITY OF ALBUQUERQUE PROJECT LABOR AGREEMENT, Effective on Date of Owner's Notice to Proceed, over an "
   "index beginning at Article 1 Purpose. An OOXML document, leading bytes 504b0304, read from word/document.xml. "
   "The filename records 4-3-25."),
  DEVPROC, [{"page": CAPITAL, "reason": "It governs labour on City capital construction."}]),
 ('src-44905a6eda9d90af',
  "Excavation and Temporary Traffic Control Permit Application",
  None, "permits and forms",
  ("The City's application for permission to excavate in the street and control traffic around the work, to be sent "
   "to the Construction Coordination Section at least fourteen days ahead, with incomplete forms and early start "
   "dates rejected."),
  ("Headed Department of Municipal Development, Construction Coordination Section, Excavation and Temporary Traffic "
   "Control Permit Application, requiring submission to dmdccs@cabq.gov at least fourteen calendar days in advance."),
  DEVPROC, [{"page": ROADWAY, "reason": "The permit governs work in the street."}]),
 ('src-5b1d9f19e92709b1',
  "Public Right-of-Way Excavation and Temporary Traffic Control Permit Application, 2024",
  "2024", "permits and forms",
  ("The City's right-of-way excavation permit application, a fuller form than the older excavation and barricade "
   "application, requires submission at least ten days ahead rather than fourteen and asks for more about the work "
   "proposed."),
  ("Headed Department of Municipal Development, Construction Coordination Section, Public Right-of-Way Excavation "
   "and Temporary Traffic Control Permit Application, requiring submission at least ten calendar days in advance. "
   "The filename records updated 2024."),
  DEVPROC, [{"page": ROADWAY, "reason": "The permit governs work in the street."}]),
 ('src-d4584254b73fcfdf',
  "Oversize and Overweight Vehicle Permit Application",
  None, "permits and forms",
  ("The City's permit application for moving an oversize or overweight load through Albuquerque, issued under the "
   "Traffic Code, collecting the mover's details and the route and dimensions of the move for City approval."),
  "Headed Traffic Code Subsection 4.67, CITY OF ALBUQUERQUE, OVERSIZE OVERWEIGHT PERMIT, returnable to coaoversizepermits@cabq.gov.",
  ROADWAY, [{"page": DEVPROC, "reason": "A City permit application."}]),
 ('src-78e5d98cb0f1016b',
  "Final Plat Checklist",
  None, "permits and forms",
  ("The City Surveyor's checklist must be completed by the surveyor preparing a subdivision plat and submitted with "
   "the plat for final review and approval, recording the subdivision, the subdivider, the surveyor and the agent."),
  "Headed FINAL PLAT CHECKLIST, requiring completion in black or blue ink by the Surveyor preparing the Plat and submission with a copy of the Plat to the City Surveyor.",
  DEVPROC, []),
 ('src-a55097ba6908d863',
  "Damage Waiver Form, Street Maintenance Division",
  None, "permits and forms",
  ("The City's waiver has a property owner acknowledge, before signing, the risk of damage from street maintenance "
   "work adjacent to their property, and release the City accordingly."),
  ("Headed CITY OF ALBUQUERQUE, Department of Municipal Development, Street Maintenance Division, Damage Waiver "
   "Form, Please Read Before Signing. The letterhead names Richard J. Berry as mayor and Michael J. Riordan as "
   "director, which places it in the 2009 to 2017 administration."),
  DEVPROC, [{"page": FACIL, "reason": "It concerns City street maintenance work at private property."}]),
 ('src-d58df86766b3e791',
  "Capital Implementation Program Application for Payment",
  "2022", "permits and forms",
  ("The City's payment application form is completed by the architect or engineer on a capital project to certify "
   "work done and request payment against the contract, recording the contract date and the amounts claimed."),
  "Headed CITY OF ALBUQUERQUE, Capital Implementation Program, Application for Payment, with fields for Architect/Engineer, Date Prepared and Contract Dated. The filename records updated 3-16-2022.",
  CAPITAL, [{"page": DEVPROC, "reason": "Part of the City's contract administration."}]),
 ('src-792abbefaf7e2364',
  "Excavation Inspector Boundaries, January 1, 2025",
  "2025", "permits and forms",
  ("The City's map divides Albuquerque into excavation inspector areas so that anyone working in the right of way "
   "can identify which inspector covers the location, bounded by the major streets named across the map."),
  "A map headed EXCAVATION INSPECTOR BOUNDARIES with the boundary streets labelled, including Westside Blvd NW, McMahon Blvd, Golf Course Rd NW, Tramway Rd NE and Calle Cuervo. The filename records 1-1-25.",
  ROADWAY, [{"page": DEVPROC, "reason": "It tells right-of-way permit holders who inspects their work."}]),
 ('src-ea8b6759979b82f7',
  "Green Vehicle Registration, 2026",
  "2026", "parking",
  ("The City Parking Division's registration form for the green vehicle programme, which must be presented in "
   "person at the Parking Division office along with the vehicle registration in order to obtain the benefit."),
  ("Headed City of Albuquerque, Parking Division, Green Vehicle Registration, over the year 2026, requiring "
   "applications and vehicle registration to be presented in person at the Parking Division office. The filename "
   "reads gvp-application-2025; the document reads 2026."),
  ROADWAY, []),
 ('src-b9caab22c1981252',
  "Application for On-Street Parking Permit, 2026",
  "2026", "parking",
  ("The City's residential on-street parking permit application collects the resident's name, address and contact "
   "details and the permit and visitor permit numbers being requested or renewed for the year."),
  "Headed 2026 APPLICATION FOR ON-STREET PARKING with fields for resident name, home address, permit numbers and visitor permits. The filename reads on-street-parking-application-2025; the document reads 2026.",
  ROADWAY, []),
 ('src-2e1072f410179f61',
  "Request for On-Street Parking Permits: Block Petition",
  None, "parking",
  ("The City's petition form is used by residents of a block to request that on-street parking permits be "
   "established there, naming the block and collecting the signatures of the households supporting the request."),
  "Headed City of Albuquerque, Parking Division, Request For On-Street Parking Permits, Permits for the block of, with the example given as the 100 Block of Rio Grande Blvd SW.",
  ROADWAY, []),
 ('src-e9a43accf712d8d1',
  "On-Street Parking Permit Zones: Streets and Blocks",
  None, "parking",
  ("The City's schedule of residential parking permit zones lists each lettered zone with the streets in it and the "
   "block numbers on each street that the zone covers."),
  "Tabulated as Zone, Street, Block, opening on Zone A with Alvarado, Cagua, La Guayra and Marquette and the block numbers covered on each.",
  ROADWAY, []),
 ('src-a6a0f32bd01b08e9',
  "Automated Speed Enforcement: Request for a Payment Plan",
  None, "automated speed enforcement",
  ("The City form by which someone issued an automated speed enforcement penalty asks the Office of Administrative "
   "Hearings to let them pay it over time, with the outcome notified by email or post."),
  "Headed City of Albuquerque, Office of Administrative Hearings, Request for Payment Plan, Automated Speed Enforcement.",
  SPEED, []),
 ('src-d9a21f26465c95f9',
  "Automated Speed Enforcement: Request for Hearing",
  None, "automated speed enforcement",
  ("The City form by which someone issued an automated speed enforcement penalty appeals it to the Independent "
   "Hearing Office, with the online alternative named on the form itself."),
  "Headed City of Albuquerque, Independent Hearing Office, AUTOMATED SPEED ENFORCEMENT (ASE), REQUEST FOR HEARING, noting that appeals may also be made at cabq.gov/appeals.",
  SPEED, []),
 ('src-da782a8496860fd5',
  "Request for Proposals: Architectural Consultants for a Hangar Facility at the Sunport and Double Eagle II Airport",
  "2018", "requests for proposals",
  ("The City's request for proposals for hangar facilities at its two airports names the project number, the "
   "professions invited, and the deadline by which proposals had to reach the Selection Advisory Committee office."),
  "Headed CITY OF ALBUQUERQUE, NOTICE OF REQUEST FOR PROPOSALS FROM ARCHITECTURAL CONSULTANTS FOR CONSTRUCTION OF A HANGAR FACILITY AT THE ALBUQUERQUE INTERNATIONAL SUNPORT AND THE DOUBLE EAGLE II AIRPORT, PROJECT NO. 6564.93, proposals due Wednesday, August 8, 2018.",
  PROJECTS, [{"page": CAPITAL, "reason": "A capital project procurement."}]),
 ('src-4c1b7ae34207fd2f',
  "Request for Proposals: Citywide On-Call Engineering Services for Hydrology, Hydraulics and Storm Drainage Work",
  "2018", "requests for proposals",
  ("The City's request for proposals for its hydrology, hydraulics and storm drainage on-call engineering contract "
   "names the project number, the firms invited, and where and by when proposals had to be delivered."),
  "Headed CITY OF ALBUQUERQUE, NOTICE OF REQUEST FOR PROPOSALS FOR CITYWIDE ON-CALL ENGINEERING SERVICES FOR HYDROLOGY, HYDRAULICS AND STORM DRAINAGE WORK, PROJECT NO. 5001.07, proposals due Wednesday, September 19, 2018.",
  STORM, [{"page": DEVPROC, "reason": "An on-call engineering procurement."}]),
 ('src-e0b517a974bfdc14',
  "Request for Proposals: Engineering for On-Street Bicycle Facility Design On-Call",
  "2018", "requests for proposals",
  ("The City's request for proposals for on-call engineering of on-street bicycle facilities names the project "
   "number, the firms invited, and the deadline by which proposals had to reach the Selection Advisory Committee "
   "office."),
  "Headed CITY OF ALBUQUERQUE, NOTICE OF REQUEST FOR PROPOSALS FOR ENGINEERING FOR ON-STREET BICYCLE FACILITY DESIGN ON-CALL, PROJECT NO. 7589.00, proposals due Wednesday, October 17, 2018.",
  BIKE, [{"page": DEVPROC, "reason": "An on-call engineering procurement."}]),
]

approved = []
for i, title, date, group, desc, ev, canon, cross in APPROVED:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None,
              "evidence": ev, "group": group,
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# ----------------------------------------------------------------- superseded
superseded = [
 {**row('src-d611348f13f18054', "superseded"),
  "canonical_id": 'src-ef4ac437d38d7d61',
  "title_for_reference": "Regulation Governing the Award and Rejection of Bids/Offers and Debarment of Contractors for Public Works Projects, effective July 25, 2008",
  "relationship": "The 2008 edition of the regulation recommended above, which carries the same title word for word.",
  "how_it_was_established": ("The file has no usable text layer - 36 bytes for 36 pages - so it was rendered. Its "
                             "cover reads REGULATION GOVERNING THE AWARD AND REJECTION OF BIDS/OFFERS AND DEBARMENT "
                             "OF CONTRACTORS FOR PUBLIC WORKS PROJECTS OF THE CITY OF ALBUQUERQUE, Effective JULY "
                             "25, 2008. The later edition has no cover at all and is footer-dated 1/22/21 on every "
                             "page, 40 pages against 36."),
  "a_caveat_worth_carrying": ("The 2021 edition states no effective date on its face; its date is a page footer. "
                              "The supersession rests on the identical title and the later footer date, which is "
                              "sound, but if the City can confirm an adoption date for the 2021 edition it should be "
                              "recorded rather than the footer."),
  "recommended_treatment": "Retain as the superseded edition; it is the only record of what the rule said before 2021.",
 },
 {**row('src-5091be606b6614ab', "superseded"),
  "canonical_id": 'src-ea8b6759979b82f7',
  "title_for_reference": "Green Vehicle Registration, 2024",
  "relationship": "The 2024 edition of the Parking Division's green vehicle registration form.",
  "how_it_was_established": ("Normalized-text sequence ratio 0.9994 against the later edition, token coverage 0.9938 "
                             "both directions. A line-level diff returns exactly one differing block in the whole "
                             "document: the year, 2024 against 2026. Nothing else on the form changed."),
  "recommended_treatment": "Retain as the earlier edition. Note that its successor's filename says 2025 and its face says 2026.",
 },
]

# ------------------------------------------------------------------ duplicate
duplicate = [
 {**row('src-8dfa6da27a05f4f1', "duplicate"),
  "canonical_id": 'src-4c1b7ae34207fd2f',
  "title_for_reference": "mf-3334-1.docx",
  "relationship": "The same file as mf-3334.docx, published twice.",
  "how_it_was_established": ("Byte-identical: both 20,309 bytes with the same SHA-256. This is the only "
                             "byte-identical pair found in eight slices of this tree, and the only one the URL "
                             "group-by and hashing pass would have caught on its own."),
  "why_this_one_is_the_copy": "The -1 suffix is the content management system's collision suffix; the plain name is the primary object.",
 },
 {**row('src-6924f5ef7f391100', "duplicate"),
  "canonical_id": 'src-44905a6eda9d90af',
  "title_for_reference": "excavationbarricadeform.doc",
  "relationship": "The same form as excavationbarricadeform.pdf, in the editable format it was authored in.",
  "how_it_was_established": ("Token coverage 1.0000 in both directions with a real sequence ratio of 0.9868; not "
                             "text-equal, and it could not be, because the two extractions come from different "
                             "readers - antiword over a legacy OLE2 document and pdftotext over a PDF. Every "
                             "substantive string matches, including the fourteen calendar day notice period."),
  "why_this_one_is_the_copy": ("The PDF is the fixed rendering the City means applicants to print and fill; the DOC "
                               "is the source. Standing practice in this archive is to keep one canonical original "
                               "and document the relationship rather than archive both."),
  "a_reason_to_revisit": ("If the archive wants the editable form available as well, this is the file to archive, "
                          "not a second copy of the PDF. Flagged rather than decided."),
 },
]

# ---------------------------------------------------- requires human review
rhr = [
 {**row('src-05b68a5758490499', "requires human review"),
  "draft_title": "Fiber Infrastructure Rulemaking: Public Hearing Correspondence and Complaints, June 2025",
  "question_for_human": "Decide whether the City's fiber rulemaking correspondence is published in full, redacted, or summarised.",
  "why_not_decided_here": ("It is genuinely two things at once. It is the public comment record of a City rulemaking "
                           "- the correspondence that fed the June 2025 fiber regulations recommended above - and "
                           "public comment on a rulemaking is ordinarily a public record. It is also seventy-four "
                           "thousand characters of emails from named residents about work outside their own homes. "
                           "This lane excludes rosters of private individuals' contact details on its own judgment; "
                           "it should not decide on its own judgment to publish residents' complaints in full."),
  "measurement": "Born-digital PDF. Opens on an email of Sunday, June 8, 2025 from a named resident with the subject Cable Installation.",
  "distinguishing_content": "Correspondence and email complaints gathered for the 6-5-25 fiber regulations hearing.",
  "package": "the_fiber_rulemaking_record",
  "priority": 1},
 {**row('src-24475ae69d0950da', "requires human review"),
  "draft_title": "Portable and Fixed System Maintenance Instructions, automated speed enforcement equipment",
  "question_for_human": "Decide whether a vendor's equipment maintenance manual, posted by the City, is archived as a City record.",
  "why_not_decided_here": ("The authorship is a vendor's, not the City's: the document is NOVOAGLOBAL, Inc.'s, with "
                           "that company's document control header. On this lane's own precedent - the USDA soil "
                           "loss note in the previous slice, the NMAC licensing rule excluded here - that is "
                           "grounds to exclude. But those two have authoritative publishers who publish them; this "
                           "one does not appear to be published anywhere except on the City's page, and it documents "
                           "how the City's speed enforcement cameras are maintained, which is exactly the kind of "
                           "thing an accountability archive exists to hold."),
  "measurement": "Born-digital PDF with a document control header reading Tec-18020, Rev E, 11/23/2021, and the vendor strapline Creating Safer Communities.",
  "distinguishing_content": "Portable and Fixed Systems Maintenance Instructions, NOVOAGLOBAL, Inc.",
  "package": "vendor_documentation_the_city_posts",
  "priority": 2},
 {**row('src-a5e67a171e101912', "requires human review"),
  "draft_title": "Other Funding Sources Worksheet",
  "question_for_human": "Confirm this belongs to the project request form set, or drop it.",
  "why_not_decided_here": ("There is almost nothing on it. The workbook's entire shared string table is two words, "
                           "Source and Amount, and the sheet itself is empty. It carries no City name, no title, no "
                           "form number and no date. Its only connection to the City is its URL and its neighbours: "
                           "it sits beside the project request form instructions recommended above, and a capital "
                           "request does ask what other funding a project has."),
  "measurement": "OOXML workbook, leading bytes 504b0304, read from xl/sharedStrings.xml and xl/worksheets/sheet1.xml. The shared string table holds two entries.",
  "distinguishing_content": "A two-column blank worksheet headed Source and Amount.",
  "package": "unidentified_blank_template",
  "priority": 3},
]

# ------------------------------------------------------------------- excluded
excluded = [
 {**row('src-3e365c42a31693fa', "excluded"),
  "title_for_reference": "NMAC Title 14, Chapter 6, Part 6: Construction Industries Licensing, Classifications and Scopes",
  "what_it_is": "A State of New Mexico administrative rule, issued by the Construction Industries Division of the Regulation and Licensing Department.",
  "exclusion_reason": ("Not a City record. It is codified state law - 14.6.6.1 NMAC, reissued 3/10/2022 - applying "
                       "to anyone contracting under the Construction Industries Licensing Act, Section 60-13-3 NMSA "
                       "1978. The City posts it because its contractors are licensed under it; the authoritative "
                       "publisher is the New Mexico Administrative Code."),
  "category": "state administrative rule",
  "if_reconsidered": "Cite it to NMAC rather than archiving the City's copy as though the City issued it. Same treatment as the USDA-NRCS technical note in the previous slice.",
  "package": "third_party_authority"},
 {**row('src-2883388452797b58', "excluded"),
  "title_for_reference": "Chat log from the public meeting on the fiber optic hearing",
  "what_it_is": "The chat transcript of a video meeting, including the opening advertisement of an AI notetaking bot that joined the call.",
  "exclusion_reason": ("Meeting exhaust. It records who typed what into a chat window during a hearing, opening with "
                       "a third-party notetaking service's help text rather than anything about fiber. The hearing's "
                       "substance is in the regulations recommended above and in the correspondence record held for "
                       "review; this adds nothing and names participants."),
  "category": "meeting chat transcript",
  "package": "meeting_exhaust"},
]

rows = approved + superseded + duplicate + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (set(SLICE) - set(ids), set(ids) - set(SLICE))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
superseded_bytes = sum(r["size_bytes"] for r in superseded)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "permits-forms-regulations-cluster-research-2026-09-12",
 "lane": "Claude research lane: the permits, forms, applications and regulations group in www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the eighth slice of the municipaldevelopment/documents lane.",
 "cluster": ("The rules the City makes and the paper it hands out: promulgated regulations, capital programme "
             "instruction books, permit and parking applications, automated speed enforcement forms, and the "
             "numbered requests for proposals filed among them."),
 "scope": "All 34 uncovered candidates in this group. The coverage gate is asserted in the generator.",
 "brief": ("Separate adopted regulations from the application forms that implement them, and date every form from "
           "its own face rather than from a version number in its filename."),
 "brief_finding_on_the_separation": ("Four promulgated regulations, and they are recommended as regulations rather "
                                     "than as paperwork: the bids and debarment rule, the fiber right-of-way rules, "
                                     "the state capital outlay fiscal agent rule and the residential parking rule. "
                                     "Three of the four carry a promulgation trail on their face - two DocuSign "
                                     "envelopes and an inter-office memorandum from the department director to the "
                                     "Chief Administrative Officer - which is what distinguishes them from the forms "
                                     "underneath them."),
 "brief_finding_on_dating": ("The instruction to date from the face rather than the filename was the right one, and "
                            "it changed three records. See three_filenames_with_the_wrong_year."),
 "method": ("Fetched every candidate and measured byte length and SHA-256 from the fetched bytes, verifying every "
            "container by leading bytes: 27 PDFs, 6 OOXML documents and one legacy OLE2 document, each read with "
            "the right reader - pdftotext, a ZIP reader over word/document.xml or xl/sharedStrings.xml, and antiword. "
            "Read each file for its own title, year and effective date. Rendered the one file with no usable text "
            "layer, which is how its 2008 effective date was found. Compared every checksum within the slice and "
            "against the 1,612 checksummed inventory records, then compared the look-alike pairs with real sequence "
            "ratios, token coverage and line-level diffs."),
 "classification_only": True,
 "shared_state_written": [],
 "three_filenames_with_the_wrong_year": {
  "count": 3,
  "cases": [
   "gvp-application-2025.pdf is headed Green Vehicle Registration 2026.",
   "on-street-parking-application-2025.pdf is headed 2026 APPLICATION FOR ON-STREET PARKING.",
   "gvp-applicaiton-2024.pdf is headed 2024 and is correct, but its filename also misspells application.",
  ],
  "what_would_have_happened": ("Taking the filenames at face value would have published the current parking permit "
                               "and green vehicle forms a year stale, told residents the wrong registration year, "
                               "and made the 2024 green vehicle form look current rather than superseded."),
  "the_running_count": ("Eight filenames in this tree now contradict their own documents: a body and a date wrong on "
                        "an Energy Council file, two misspelled facilities in the stormwater set, a project number "
                        "and an unrecorded project in the procurement slice, and these three years."),
 },
 "the_two_supersessions": {
  "count": len(superseded),
  "the_bids_regulation": ("The 2008 edition is 36 pages with a cover reading Effective JULY 25, 2008; the 2021 "
                          "edition is 40 pages with no cover, footer-dated 1/22/21. The 2008 file has 36 bytes of "
                          "extractable text for 36 pages and had to be rendered before any of this was visible."),
  "the_green_vehicle_form": ("Sequence ratio 0.9994 and exactly one differing block in a line-level diff: the year. "
                             "The cleanest supersession in the whole run - two documents identical but for four "
                             "characters."),
  "why_both_are_retained": ("A superseded regulation is the only record of what the rule said before it changed, and "
                            "a superseded form is the only record of what the City asked for in an earlier year."),
 },
 "a_supersession_that_was_not": {
  "the_hypothesis": ("excavationbarricadeform.pdf requires fourteen days' notice; "
                     "row-permit-application-updated-2024.pdf requires ten, has a longer title, and is dated 2024. "
                     "It looked like the same form in a later edition with a shortened notice period."),
  "the_measurement": "Real sequence ratio 0.2268, token coverage 0.4560 and 0.7634. Not the same form.",
  "what_they_are": ("Two different permits from the same section. The older, shorter form covers excavation with "
                    "temporary traffic control; the 2024 form is the fuller public right-of-way permit application "
                    "and asks for considerably more. Both are recommended."),
  "why_it_is_recorded": ("A plausible supersession that the measurement refused. The notice period difference, which "
                         "looked like the strongest evidence for the hypothesis, is simply a difference between two "
                         "permits."),
 },
 "the_duplicates": {
  "count": len(duplicate),
  "the_byte_identical_one": ("mf-3334.docx and mf-3334-1.docx are the same 20,309 bytes with the same SHA-256. This "
                             "is the only byte-identical pair in eight slices of this tree, and the only "
                             "relationship in any of them that plain hashing would have found unaided."),
  "the_format_pair": ("excavationbarricadeform.doc and .pdf are the same form in two formats, at token coverage "
                      "1.0000 both directions and a real sequence ratio of 0.9868. They cannot be text-equal: the "
                      "two extractions come from different readers over different containers. The PDF is canonical "
                      "under the standing rule that one canonical original is kept and the relationship documented."),
  "the_contrast_worth_keeping": ("Across eight slices, hashing found one relationship. Text comparison, containment, "
                                 "date mapping and rendering found every other one. Hashing answers only whether two "
                                 "files are the same bytes, and in a City document tree they almost never are."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 1,
  "result": "Nothing here duplicates anything the archive holds. The one byte collision is internal to this slice.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found": 4,
  "found_by": "One by byte hashing, one by rendering an image-only cover, one by a line-level diff over near-identical text, one by token coverage across two container formats.",
  "relationships_tested_and_rejected": 1,
 },
 "integration_flags": [
  {"severity": "date-from-the-document",
   "affects": ['src-ea8b6759979b82f7', 'src-b9caab22c1981252', 'src-5091be606b6614ab'],
   "finding": "Three parking forms whose filenames carry the wrong year. Two files named 2025 are headed 2026; taking the filenames at face value would publish the current forms a year stale and tell residents the wrong registration year.",
   "recommended_action": "Title and date all three from the document."},
  {"severity": "supersession",
   "affects": [r['id'] for r in superseded],
   "finding": "The 2008 bids and debarment regulation, superseded by the 1/22/21 edition, and the 2024 green vehicle registration form, superseded by the 2026 edition. The 2008 file had to be rendered before its effective date was visible; the green vehicle pair differ by exactly one line.",
   "recommended_action": "Apply the canonical_id values. Retain both superseded records; each is the only account of what the rule or the form said before it changed."},
  {"severity": "substantive-find",
   "affects": ['src-268a2054bd39dc7b', 'src-dbd1f5327b59e1ee', 'src-ed393fa3ad5dd15c'],
   "finding": "The 2027-2036 Decade Plan for Capital Improvements instruction book, the 2023 bond programme instruction booklet, and the project request form instructions for operating and maintenance analysis. The archive holds a 2007 decade plan and nothing later.",
   "recommended_action": "Approve. Together they show how a project gets into the capital programme and what it must say about its running costs."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'regulations'],
   "finding": "Four promulgated City regulations: the award, rejection and debarment rule for public works; the June 2025 fiber right-of-way rules; the state capital outlay fiscal agent rule effective 1/30/2023; and the October 2022 residential parking rule.",
   "recommended_action": "Approve as regulations, distinct from the application forms that implement them."},
  {"severity": "judgment-needed",
   "affects": [r['id'] for r in rhr],
   "finding": "Three that this lane should not decide alone: the fiber rulemaking correspondence, which is both a public comment record and a compilation of residents' complaints; a vendor's maintenance manual for the City's speed enforcement equipment, which is not a City record but may be the only public copy; and a blank two-word worksheet with no identification on it.",
   "recommended_action": "Decide each on the reasoning recorded in its row."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "superseded": counts["superseded"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": ("%d PDFs, %d OOXML documents and %d legacy OLE2 document by leading bytes. "
                                        "The OOXML set is five Word documents and one Excel workbook, which needed "
                                        "different readers."
                                        % (bycontainer['PDF'], bycontainer['OOXML'], bycontainer['DOC']))},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicate,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, dominated by the "
                   f"two bond instruction books. The {len(superseded)} superseded records add {superseded_bytes:,} "
                   f"bytes and should be archived too; a superseded rule is the only record of what the rule used to "
                   f"say. Four approved records are OOXML and should be archived in their original format rather "
                   f"than converted."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Two rows carry a canonical_id for supersession and "
                     "two for duplication; all four canonicals are approved rows in this artifact. Three approved "
                     "rows must be dated from the document rather than the filename and say so. Every approved row "
                     "carries a group field so the regulations can be listed apart from the forms. Every row carries "
                     "a leading_bytes field. Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the correspondence file was read only to establish what it contains and is not reproduced here"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != 'approved_by_group'}}))
