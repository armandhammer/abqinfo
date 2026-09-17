"""Claude research lane. The last of the link harvest: the real property flyers
served from dmdgis.cabq.gov, and the files on hosts other than the City's own.

As with the other harvest lanes, these are NOT inventory candidates: none has an
inventory id and nothing here can be applied through Update-Candidate.ps1. It
never modifies master-inventory.json, checkpoint.json, r2-inventory.json, site
content, or R2.

Dated 2026-09-14.
"""

import collections
import datetime
import glob
import json
import os
import re
import urllib.parse
import zipfile

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\harvested-remainder-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\harv')

TRANSIT = 'content/transportation/transit/abq-ride.md'
TRANSPO = 'content/transportation/_index.md'
PLANS = 'content/transportation/transportation-plans.md'
DESIGN = 'content/transportation/design-references.md'
CRASH = 'content/transportation/safety-crash-data.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
STORM = 'content/public-works/stormwater-drainage.md'
CLIMATE = 'content/city-data/climate-environment.md'
DEVPROC = 'content/development-land-use/development-process.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
MAPS = 'content/maps-data/maps.md'
ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'
FACIL = 'content/public-works/city-facilities.md'

inv = json.load(open(INV, encoding='utf-8'))

ALLF, M, MAGIC, URL, CODE, SRC = {}, {}, {}, {}, {}, {}
CITY_HOSTS = ('www.cabq.gov', 'documents.cabq.gov')
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    ALLF[p[0]] = p
    if urllib.parse.urlsplit(p[5]).netloc in CITY_HOSTS:
        continue
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], URL[p[0]], CODE[p[0]], SRC[p[0]] = p[4], p[5], p[1], p[6].strip()

SLICE = sorted(M)
FLYERS = [i for i in SLICE if 'dmdgis.cabq.gov' in URL[i]]
OTHER = [i for i in SLICE if i not in FLYERS]

ALL_SHA, ARCH_SHA = {}, {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s:
        ALL_SHA.setdefault(s, (x['id'], x.get('status')))
        if x.get('status') in ('validated', 'published', 'archived', 'implemented'):
            ARCH_SHA.setdefault(s, x['id'])


def norm(u):
    u = urllib.parse.unquote(u or '').strip()
    if u.endswith('/view'):
        u = u[:-5]
    s = urllib.parse.urlsplit(u)
    return (s.netloc.lower().replace('www.', '') + s.path.rstrip('/')).lower()


INV_URL = {}
for x in inv['candidates']:
    for k in ('direct_file_url', 'source_url'):
        if x.get(k):
            INV_URL.setdefault(norm(x[k]), (x['id'], x.get('status')))

PRIOR_SHA = {}
for f in glob.glob(os.path.join(DISC, '*.json')):
    if os.path.abspath(f) == os.path.abspath(OUT):
        continue
    try:
        d = json.load(open(f, encoding='utf-8-sig'))
    except Exception:
        continue
    if not isinstance(d, dict):
        continue
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded',
              'add_to_inventory', 'do_not_add', 'needs_a_decision_from_a_person'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('checksum_sha256'):
                PRIOR_SHA.setdefault(r['checksum_sha256'],
                                     (os.path.basename(f), r.get('id') or r.get('local_ref')))

SHA_HIT = {i: ALL_SHA[M[i]['checksum_sha256']] for i in SLICE if M[i]['checksum_sha256'] in ALL_SHA}
URL_HIT = {i: INV_URL[norm(URL[i])] for i in SLICE if norm(URL[i]) in INV_URL}
ART_HIT = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE
           if M[i]['checksum_sha256'] not in ALL_SHA and M[i]['checksum_sha256'] in PRIOR_SHA}

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
INTERNAL = {}
for v in BYHASH.values():
    if len(v) < 2:
        continue
    keep = sorted(v, key=lambda x: (len(URL[x]), x))[0]
    for x in v:
        if x != keep:
            INTERNAL[x] = keep


def container(i):
    if MAGIC[i] == '25504446':
        return 'PDF'
    if MAGIC[i] == 'd0cf11e0':
        return 'OLE2 (legacy Word)'
    if MAGIC[i] == '3c21646f':
        return 'HTML'
    n = zipfile.ZipFile(os.path.join(SP, 'files', i + '.bin')).namelist()
    return 'DOCX' if any(x.startswith('word/') for x in n) else \
           'XLSX' if any(x.startswith('xl/') for x in n) else \
           'PPTX' if any(x.startswith('ppt/') for x in n) else 'OOXML'


def pages(i):
    if MAGIC[i] != '25504446':
        return None
    n = len(re.findall(rb'/Type\s*/Page[^s]', open(os.path.join(SP, 'files', i + '.bin'), 'rb').read()))
    return n or None


def text(i):
    p = os.path.join(SP, 'txt', i + '.txt')
    return open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''


LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, and for OOXML by which of word/, xl/ or ppt/ the archive holds. Every "
      "PDF was tested for its end-of-file marker.")

NMDOT = "new mexico department of transportation"
NMDOT_NOTE = ("Published by the New Mexico Department of Transportation, not by the City. The archive already holds "
              "62 validated NMDOT records, so the source is in scope; attribute it to NMDOT.")

D = {
 # ---- City transit route maps -------------------------------------------
 'hv-016': ("ABQ RIDE Route 52 weekday schedule, effective 16 May 2026", "transit route schedules",
   ("The weekday timetable and route map for ABQ RIDE route 52, Broadway to Rio Bravo, as it stood from 16 May "
    "2026, listing the timing points along the route in both directions."),
   "204,087 bytes. Opens: Route / Ruta 52, Effective: Broadway / Rio Bravo, May 16, 2026, with the timing points and the wheelchair accessibility notice.",
   TRANSIT, [], "A dated timetable that a later edition will supersede. Date it and expect a successor."),
 'hv-017': ("ABQ RIDE Route 52 weekend schedule, effective 16 May 2026", "transit route schedules",
   ("The weekend timetable and route map for ABQ RIDE route 52, Broadway to Rio Bravo, the companion to the weekday "
    "schedule and effective from the same date."),
   "207,493 bytes. Opens: Route / Ruta 52, Effective: Broadway / Rio Bravo, May 16, 2026, in the weekend edition.",
   TRANSIT, [], "A dated timetable that a later edition will supersede. Date it and expect a successor."),
 'hv-018': ("ABQ RIDE Route 790 weekday schedule, August 2026 to May 2027", "transit route schedules",
   ("The weekday timetable for ABQ RIDE route 790, Coors to University, covering the academic year from August 2026 "
    "to May 2027 and effective from 17 August 2026."),
   "163,423 bytes. Opens: Route/Ruta 790, Effective: August 17, 2026, Coors/University, August 2026 - May 2027, Agosto 2026 - Mayo 2027.",
   TRANSIT, [], "An academic-year timetable with an explicit end date. Date it and expect a successor."),
 'hv-019': ("ABQ RIDE Route 97 weekday schedule, effective 5 April 2025", "transit route schedules",
   ("The weekday timetable for ABQ RIDE route 97 along Zuni Road, westbound and eastbound, as it stood from 5 April "
    "2025."),
   "150,197 bytes. Opens: Route / Ruta 97, Effective: 4/5/2025, Zuni Rd., Westbound / Oeste, Weekday - Dia Laborable.",
   TRANSIT, [], "The oldest of the four route schedules here and the most likely already superseded. Check for a later edition before publishing."),
 # ---- MRCOG ---------------------------------------------------------------
 'hv-270': ("Albuquerque Metropolitan Planning Boundaries map, August 2023", "regional planning",
   ("The regional council's map of the Albuquerque metropolitan planning boundaries, showing the metropolitan "
    "planning area against the regional planning programme boundary, the urban areas, the tribal lands and the "
    "state transportation district."),
   ("4,163,307 bytes, one page with no text layer, read by rendering. Titled Mid Region Council of Governments, "
    "Metropolitan Planning Organization, Albuquerque Metropolitan Planning Boundaries, with a map date of August "
    "2023 and a legend distinguishing the MRCOG/RPP boundary, the MPO/AMPA and NMDOT District 3."),
   MAPS, [{"page": PLANS, "reason": "It defines the area regional transportation plans cover."}],
   "Published by the Mid-Region Council of Governments, not the City. The archive holds 117 validated MRCOG records."),
 'hv-271': ("Transportation Improvement Program amendment schedule, federal fiscal year 2026", "regional planning",
   ("The regional council's calendar of amendment events for the Transportation Improvement Program in federal "
    "fiscal year 2026, quarter by quarter, the schedule a project sponsor must work to."),
   "109,636 bytes. Opens: Transportation Improvement Program (TIP), FFY 2026 Amendment Event, 1st Quarter, 2nd Quarter, 3rd Quarter, 4th Quarter.",
   PLANS, [], "Published by the Mid-Region Council of Governments, not the City."),
 # ---- NMDOT: technical and regulatory -------------------------------------
 'hv-346': ("NMDOT National Pollutant Discharge Elimination System Manual, revision 4, 2023", NMDOT,
   ("The state transportation department's manual of stormwater management guidelines for construction, municipal "
    "separate storm sewer systems and industrial activity, the document its contractors work to."),
   "23,182,208 bytes, the largest file in this lane. Opens: National Pollutant Discharge Elimination System Manual, STORMWATER MANAGEMENT GUIDELINES FOR CONSTRUCTION, MS4, AND INDUSTRIAL.",
   STORM, [{"page": CLIMATE, "reason": "Water-quality guidance."}], NMDOT_NOTE),
 'hv-347': ("NMDOT Erosion and Sediment Control Field Guide, 2024", NMDOT,
   ("The state transportation department's field guide to best management practices for temporary erosion and "
    "sediment control during construction, written for use on site."),
   "13,053,389 bytes. Opens: NMDOT Erosion & Sediment Control Field Guide, Best Management Practices for Construction Phase Temporary Erosion and Sediment control.",
   STORM, [{"page": DESIGN, "reason": "A construction standard."}], NMDOT_NOTE),
 'hv-348': ("NMDOT Green Stormwater Infrastructure Maintenance Field Guide, 2024 edition", NMDOT,
   ("The state transportation department's field guide to maintaining green stormwater infrastructure, the "
    "companion to its erosion and sediment control guide."),
   "12,506,696 bytes. Opens: NMDOT GSI Maintenance Field Guide, Best Management Practices for Green Stormwater Infrastructure, 2024 Edition.",
   STORM, [{"page": CLIMATE, "reason": "Green infrastructure practice."}], NMDOT_NOTE),
 'hv-342': ("NMDOT illicit discharge brochure and report form, revised May 2020", NMDOT,
   ("The state transportation department's public brochure on protecting water from illicit discharges, with the "
    "form on which a member of the public reports one to the Drainage Design Bureau."),
   "2,344,630 bytes. Opens: A-1301 Revised 05/20, HELP PROTECT OUR MOST PRECIOUS RESOURCE: WATER, Drainage Design Bureau Educational Brochure & Report form.",
   STORM, [], NMDOT_NOTE),
 'hv-012': ("NMDOT Infrastructure Design Directives, 1 May 2026", NMDOT,
   ("The state transportation department's current index of infrastructure design directives, the standing "
    "instructions from the Division Chief Engineer that govern how its projects are designed."),
   "29,346,534 bytes, the largest file in this lane after the NPDES manual. Opens: Infrastructure Design Directives, Office of Infrastructure, Division Chief Engineer, May 1, 2026, Index of Current Infrastructure Design Directives.",
   DESIGN, [{"page": ROADWAY, "reason": "Design standards for road projects."}], NMDOT_NOTE),
 'hv-008': ("NMDOT Location Study Procedures, 2015 update", NMDOT,
   ("The state transportation department's guidebook for planning and environmental location studies, setting out "
    "how a corridor or project location is studied before design begins."),
   "2,038,444 bytes. Opens: Post Office Box 1149, Santa Fe, NM 87504, Location Study Procedures Update 2015, A Guidebook for: Planning and Environmental.",
   PLANS, [{"page": DESIGN, "reason": "A procedure projects are designed under."}], NMDOT_NOTE),
 'hv-006': ("NMDOT Digital Delivery Implementation Plan, April 2025", NMDOT,
   ("The state transportation department's plan for moving its project delivery to digital models, setting out what "
    "changes for design, construction and the contractors who work to its plans."),
   "1,932,425 bytes. Opens: New Mexico Department of Transportation, Digital Delivery Implementation Plan, April 2025.",
   DESIGN, [], NMDOT_NOTE),
 'hv-352': ("Draft programmatic agreement among FHWA, NMDOT and the State Historic Preservation Officer, 2027", NMDOT,
   ("The draft agreement among the federal highway agency, the state transportation department and the state "
    "historic preservation officer setting out how historic properties are handled on federally assisted highway "
    "projects in New Mexico."),
   ("91,460 bytes, a Word document read from its word/document.xml. Opens: PROGRAMMATIC AGREEMENT AMONG THE FEDERAL "
    "HIGHWAY ADMINISTRATION, THE NEW MEXICO DEPARTMENT OF TRANSPORTATION, THE. Its filename dates it 25 May 2026 "
    "and marks it a draft for first-round agency review."),
   PLANS, [{"page": ABOUT, "reason": "An intergovernmental agreement."}],
   "A draft circulated for agency review, not an executed agreement. Label it a draft."),
 'hv-353': ("NMDOT contractor located activity request form, July 2026", NMDOT,
   ("The state transportation department's form by which a contractor requests environmental and cultural resources "
    "approval for an activity it has located itself, such as a borrow pit or staging area."),
   "35,973 bytes, a Word document read from its word/document.xml. Opens: Request for Environmental & Cultural Resources Approval, Contractor Located Activity.",
   DEVPROC, [], NMDOT_NOTE),
 'hv-002': ("Tribal and Local Public Agency environmental level of effort form", NMDOT,
   ("The state transportation department's form on which a tribal or local public agency records the environmental "
    "level of effort a federally assisted project requires, completed early in project development."),
   ("344,576 bytes, a legacy OLE2 Word document - the older binary .doc format, not OOXML - read with antiword. Its "
    "text opens: Tribal/Local Public Agency Environmental Level of Effort (LoE) Form."),
   DEVPROC, [], NMDOT_NOTE),
 'hv-013': ("NMDOT bridge number request form, April 2026", NMDOT,
   ("The state transportation department's form for requesting a bridge number, recording the owner, project and "
    "control numbers, the district, county, route and mile post of a new structure."),
   "879,742 bytes. Opens: Bridge Number Request Form, Owner:, Project No.:, Control No.:, District:, LOCATION County:, Route:, Mile Post.",
   ROADWAY, [], NMDOT_NOTE),
 'hv-007': ("NMDOT utilities materials calculator", NMDOT,
   ("The state transportation department's spreadsheet for calculating material quantities on utility work, "
    "covering seed mixes by zone and the material classes used in restoration."),
   ("16,789 bytes, a spreadsheet read from its xl/sharedStrings.xml: Material Quantities, Material, Class A, Class "
    "C, Hand Application, Seed Mix, According to seed zone."),
   DESIGN, [], "A working spreadsheet rather than a published document, and its container was read from the OOXML archive's xl/ parts."),
 'hv-011': ("Right-of-way training for Tribal and Local Public Agencies", NMDOT,
   ("The state transportation department's training deck on acquiring right of way for federally assisted projects, "
    "covering the constitutional limits on eminent domain, the Uniform Act, title, mapping and valuation."),
   ("6,989,303 bytes, a PowerPoint deck of 73 slides read from its ppt/slides parts. Slide 3 quotes the Fifth "
    "Amendment and slide 4 names the Uniform Relocation Assistance and Real Property Acquisition Policies Act of "
    "1970, Public Law 91-646."),
   DEVPROC, [{"page": ROADWAY, "reason": "Right-of-way acquisition for road projects."}], NMDOT_NOTE),
 # ---- NMDOT: programme administration ------------------------------------
 'hv-010': ("NMDOT Disadvantaged Business Enterprise Program Manual", NMDOT,
   ("The state transportation department's manual for its disadvantaged business enterprise programme, the rules "
    "under which firms are certified and contracts are let on federally assisted work."),
   ("2,735,376 bytes. Opens: DISADVANTAGED BUSINESS ENTERPRISE PROGRAM MANUAL, NEW MEXICO DEPARTMENT OF "
    "TRANSPORTATION, CONSTRUCTION AND CIVIL RIGHTS BUREAU. Its own filename says it is currently being revised."),
   DEVPROC, [{"page": ABOUT, "reason": "Contracting policy."}],
   "Its filename states that it is currently being revised. Label it accordingly; a newer edition is expected."),
 'hv-015': ("NMDOT Disadvantaged Business Enterprise Program policy statement, 4 October 2024", NMDOT,
   ("The state transportation department's signed policy statement committing it to the federal disadvantaged "
    "business enterprise rules and naming the officer responsible for the programme."),
   ("388,290 bytes, no text layer, read by rendering. Headed NEW MEXICO DEPARTMENT OF TRANSPORTATION, DISADVANTAGED "
    "BUSINESS ENTERPRISE PROGRAM, POLICY STATEMENT, citing 49 CFR Part 26 and signed by Cabinet Secretary Ricky "
    "Serna, dated 10/04/24."),
   DEVPROC, [{"page": ABOUT, "reason": "Contracting policy."}], NMDOT_NOTE),
 'hv-014': ("NMDOT methodology for formulating highway disadvantaged business enterprise goals, 2024 to 2026",
   NMDOT,
   ("The state transportation department's account of how it calculated its federal disadvantaged business "
    "enterprise participation goals for the 2024, 2025 and 2026 federal fiscal years."),
   ("356,808 bytes, a Word document read from its word/document.xml, whose first word is DRAFT: DRAFT NMDOT "
    "METHODOLOGY USED TO FORMULATE FFY 2024, 2025 AND 2026 HIGHWAY RELATED DBE GOALS."),
   DEVPROC, [], "Its own text begins DRAFT. Label it a draft even though the filename does not say so."),
 'hv-004': ("Interim final rule addendum to the NMDOT disadvantaged business enterprise programme plan, October 2025",
   NMDOT,
   ("The addendum bringing the state transportation department's disadvantaged business enterprise programme plan "
    "into line with a federal interim final rule, effective from 3 October 2025."),
   "84,888 bytes. Opens: Interim Final Rule (IFR) Addendum, Effective October 3, 2025, Applies to: NMDOT DBE Program Plan, 1. Certification - Firms.",
   DEVPROC, [], NMDOT_NOTE),
 'hv-005': ("NMDOT 2028 application guide: Federal Transit Administration sections 5304, 5311 and 5339", NMDOT,
   ("The state transportation department's guide for applicants seeking federal transit funding under sections "
    "5304, 5311 and 5339, setting out eligibility and how an application is made."),
   "419,406 bytes. Opens: 2028 Application Guide, Section 5304/5311/5339, TABLE OF CONTENTS, I. Introduction/Eligibility.",
   TRANSPO, [{"page": TRANSIT, "reason": "Federal transit funding."}], NMDOT_NOTE),
 'hv-009': ("NMDOT 2028 application guide: Federal Transit Administration section 5310", NMDOT,
   ("The state transportation department's guide for applicants seeking federal transit funding under section 5310, "
    "which supports transport for older adults and people with disabilities."),
   "445,399 bytes. Opens: 2028 Application Guide, Section 5310, TABLE OF CONTENTS, I. Introduction/Eligibility.",
   TRANSPO, [{"page": TRANSIT, "reason": "Federal transit funding."}], NMDOT_NOTE),
 'hv-003': ("NMDOT Park and Ride: northern New Mexico routes brochure, revised May 2026", NMDOT,
   ("The state transportation department's Park and Ride brochure for its northern routes, with maps and timetables "
    "for the Red, Purple, Orange, Blue and Green services and the Albuquerque connection."),
   ("3,689,150 bytes, no text layer, read by rendering. It carries route maps and schedules for Santa Fe, Los "
    "Alamos, Espanola, Pojoaque and Las Vegas, and a Purple ABQ route running between Albuquerque and the NM-599 "
    "Station via the Alvarado, Montano and Los Ranchos stops. Marked Rev. 5/26."),
   TRANSIT, [{"page": TRANSPO, "reason": "An intercity service reaching Albuquerque."}],
   "Published by NMDOT. One of its routes serves Albuquerque directly, which is why it is in scope."),
 # ---- NMDOT crash data samples -------------------------------------------
 'hv-349': ("NMDOT crash data request: crash record sample and field list", NMDOT,
   ("The sample file the state transportation department publishes to show what a crash data request returns at the "
    "crash level, and therefore which fields exist in the crash record."),
   ("19,869 bytes, a spreadsheet read from its xl/sharedStrings.xml: CRASH REPORT NUMBER, CRASH DATE, CRASH YEAR, "
    "MONTH, TIME OF CRASH, HOUR OF CRASH, DAY OF WEEK, LAW ENFORCEMENT AGENCY, COUNTY."),
   CRASH, [{"page": 'content/city-data/public-safety-data.md', "reason": "It documents the crash data schema."}],
   "Sample data, not real crash records. Its value is that it documents the fields; label it a sample."),
 'hv-350': ("NMDOT crash data request: occupant record sample and field list", NMDOT,
   ("The sample file showing what a crash data request returns at the occupant level, documenting the fields held "
    "about each person involved in a reported collision."),
   ("18,566 bytes, a spreadsheet read from its xl/sharedStrings.xml: CRASH REPORT NUMBER, VEHICLE NUMBER, PERSON "
    "NUMBER, PASSENGER NUMBER, CRASH DATE, CRASH YEAR."),
   CRASH, [{"page": 'content/city-data/public-safety-data.md', "reason": "It documents the crash data schema."}],
   "Sample data, not real records about real people. Label it a sample."),
 'hv-351': ("NMDOT crash data request: vehicle record sample and field list", NMDOT,
   ("The sample file showing what a crash data request returns at the vehicle level, documenting the fields held "
    "about each vehicle in a reported collision."),
   ("52,767 bytes, a spreadsheet read from its xl/sharedStrings.xml: CRASH REPORT NUMBER, VEHICLE NUMBER, CRASH "
    "DATE, CRASH YEAR, MONTH, TIME OF CRASH, DAY OF WEEK, LAW ENFORCEMENT."),
   CRASH, [{"page": 'content/city-data/public-safety-data.md', "reason": "It documents the crash data schema."}],
   "Sample data, not real records. Label it a sample."),
 # ---- NMDOT history publications -----------------------------------------
 'hv-344': ("Route 66 and Native Americans", NMDOT,
   ("The state transportation department's history of Route 66 and the Native American communities along it, "
    "illustrated from the department's own photographic collection."),
   "6,917,454 bytes. Opens: Introduction, Cover: Laguna Pueblo, 1928, Courtesy of Ron Fernandez, Above: Black and white photo of Bridge 8.",
   AREAPLANS, [{"page": ABOUT, "reason": "A published history of a road through the city."}],
   "A history published by NMDOT. Attribute it to the department and its named contributors."),
 'hv-345': ("The Road to Science: a brief history of highway archaeology in New Mexico", NMDOT,
   ("A history of highway archaeology in New Mexico by Laurel Wallace and Janet Spivey, published by the state "
    "transportation department as part of its cultural resources programme."),
   ("5,787,136 bytes, a legacy OLE2 Word document served with a .doc extension - the older binary format, not "
    "OOXML - read with antiword. Its text opens: The Road to Science: A Brief History of Highway Archaeology in New "
    "Mexico, Laurel Wallace and Janet Spivey."),
   AREAPLANS, [{"page": ABOUT, "reason": "A published history."}],
   "Named authors. Credit them, not only the department."),
 'hv-343': ("The Cambray Overpass and the federal grade-separation program", NMDOT,
   ("A poster on the Cambray overpass and the federal grade-separation programme, drawing on the state "
    "transportation department's historic photographs of the structure."),
   "8,723,999 bytes. Opens: The Cambray Overpass and the Federal Grade-Separation Program, Photo of west approach of Bridge 1705, 1931 (NMDOT Collection).",
   ROADWAY, [{"page": ABOUT, "reason": "A published history."}],
   ("About a structure near Deming, not in Albuquerque. Keep it only if the archive collects NMDOT's statewide "
    "historical series; its subject is outside the city.")),
 'hv-354': ("Stewardship and oversight agreement between FHWA and NMDOT", NMDOT,
   ("The agreement between the federal highway agency and the state transportation department on project "
    "assumption and programme oversight, which decides which federal responsibilities the state carries out."),
   "706,524 bytes. Opens: STEWARDSHIP AND OVERSIGHT AGREEMENT ON PROJECT ASSUMPTION AND PROGRAM OVERSIGHT BY AND BETWEEN THE FEDERAL HIGHWAY ADMINISTRATION.",
   PLANS, [{"page": ABOUT, "reason": "An intergovernmental agreement."}],
   ("A federal agreement, but specific to New Mexico - which is why it is kept where the generic federal "
    "publications in this lane are not.")),
}

EXCLUDE = {
 'hv-273': ("Public Rights-of-Way Accessibility Guidelines with shared use paths, 2013",
            "The United States Access Board's proposed accessibility guidelines for public rights of way.",
            ("A federal agency's own publication of general applicability, linked from an NMDOT page. The Access "
             "Board is the authoritative publisher of its own guidelines. The same treatment this run gave the FCC "
             "rules, the USDA-NRCS technical note, the NMAC licensing rule, the PNM tariff and the IRS form."),
            "federal accessibility guidelines", "third_party_authority"),
 'hv-355': ("Federal Register, volume 83 number 139, 19 July 2018: rules and regulations",
            "A page range from the Federal Register, linked from a regional transit safety resources page.",
            ("A federal publication of general applicability. The Government Publishing Office is its authoritative "
             "source and it is not a New Mexico or Albuquerque instrument. Same reasoning as the accessibility "
             "guidelines above."),
            "federal register extract", "third_party_authority"),
 'hv-272': ("A licence file belonging to the City file-transfer application",
            "The URL sfftp.cabq.gov/f/licenses.txt, which returns 1,344 bytes of JavaScript application shell.",
            ("Not a document and not even the file its name promises. The City's file-transfer host answers every "
             "path under /f/ with the same application shell, which is how this link was found at all: it is the "
             "shell's own reference to its licence file, harvested from a share page that is itself a candidate. "
             "See what_this_link_exposed."),
            "application shell, not a document", "nothing_at_the_url"),
}

FLYER_PKG = "real_property_availability_flyers"


def flyer_facts(i):
    t = re.sub(r'\s+', ' ', text(i))
    out = {}
    m = re.search(r'AVAILABLE\s+(.+?)\s+UPC\s+(\d+)', t)
    if m:
        out['property'] = m.group(1).strip()[:70]
        out['upc'] = m.group(2)
    m = re.search(r'Size\s+([\d.]+)\s*acres', t, re.I)
    if m:
        out['size_acres'] = m.group(1)
    m = re.search(r'Zoning\s+(\S+)', t)
    if m and re.fullmatch(r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*', m.group(1)):
        out['zoning'] = m.group(1)
    else:
        out['zoning_not_stated_on_this_flyer'] = True
    m = re.search(r'Appraisal\s+(.+?)\s+Legal Description', t)
    if m:
        out['appraisal_as_stated'] = m.group(1).strip()[:40]
    return out


add, skip, person = [], [], []


def base_row(i, rec):
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i],
         "filename": urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1]),
         "harvested_from": SRC[i], "recommendation": rec, "link_check": LC,
         "content_kind": container(i), "leading_bytes": MAGIC[i], "http_status": CODE[i], **M[i]}
    p = pages(i)
    if p:
        r["page_count"] = p
    return r


for i in OTHER:
    if i in EXCLUDE:
        t, what, why, cat, pkg = EXCLUDE[i]
        r = base_row(i, "do not add")
        r.update({"title_for_reference": t, "what_it_is": what, "why_not": why, "category": cat, "package": pkg})
        skip.append(r)
        continue
    t, group, desc, ev, canon, cross, caution = D[i]
    r = base_row(i, "add to the inventory as a new candidate")
    r.update({"title": t, "group": group, "description": desc, "evidence": ev,
              "description_word_count": len(desc.split()),
              "proposed_canonical_page": canon, "cross_listings": cross})
    if caution:
        r["caution"] = caution
    add.append(r)

for i in FLYERS:
    r = base_row(i, "put to a person before adding")
    r.update({
     "title_for_reference": "City property availability flyer, UPC %s" % flyer_facts(i).get('upc', '(not read)'),
     "what_it_is": ("A one-page flyer generated from the City Real Property Division's geographic information "
                    "system for a single parcel the City has available, carrying the parcel identifier, address, "
                    "size, zoning, appraisal status, legal description, a locator map and a link to an interest "
                    "form."),
     "package": FLYER_PKG,
     "the_facts_it_states": flyer_facts(i),
     "harvested_from_one_page": SRC[i],
    })
    person.append(r)

rows = add + skip + person
assert len(rows) == len(SLICE), (len(rows), len(SLICE))
assert sorted(r['local_ref'] for r in rows) == SLICE
bygroup = collections.Counter(r['group'] for r in add)
add_bytes = sum(r['size_bytes'] for r in add)
flyer_bytes = sum(r['size_bytes'] for r in person)
containers = collections.Counter(r['content_kind'] for r in rows)
hosts = collections.Counter(urllib.parse.urlsplit(URL[i]).netloc for i in SLICE)
notext = [i for i in SLICE if MAGIC[i] == '25504446' and len(text(i).strip()) < 40]
zoning = collections.Counter(r['the_facts_it_states']['zoning'] for r in person
                             if r['the_facts_it_states'].get('zoning'))
no_zoning = sum(1 for r in person if not r['the_facts_it_states'].get('zoning'))
unappraised = sum(1 for r in person if 'not yet' in (r['the_facts_it_states'].get('appraisal_as_stated') or '').lower())

artifact = {
 "batch_id": "harvested-remainder-research-2026-09-14",
 "lane": "Claude research lane: the last of the link harvest - the property flyers and the files on other hosts",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14. This completes the link harvest.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": ("None of these files has an inventory id. Every row carries inventory_id: null and a "
                      "recommendation rather than a recommended_status."),
  "the_three_values_used": ("add to the inventory as a new candidate; do not add; and put to a person before "
                            "adding, which is used for one package of 173 files and for nothing else."),
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here. These must be created as candidates first.",
 },
 "cluster": ("The third and last slice of the link harvest: everything the harvest found that is not served from "
             "www.cabq.gov or documents.cabq.gov."),
 "scope": "All %d files, across %d hosts." % (len(SLICE), len(hosts)),
 "hosts": dict(hosts),
 "THE_173_FLYERS_ARE_A_SCOPE_QUESTION_NOT_A_RESEARCH_ONE": {
  "what_they_are": ("One page per parcel, generated from the Real Property Division's geographic information "
                    "system, listing the parcel identifier, address, size, zoning, appraisal status and legal "
                    "description over a locator map, ending in a link to submit an interest form. All 173 are "
                    "linked from a single page, www.cabq.gov/available-city-properties."),
  "why_this_lane_will_not_decide_them": {
   "they_carry_no_date_of_issue": ("Not one of them states when it was generated. There is nothing on the face of "
                                   "the file to date the snapshot to."),
   "their_content_is_a_live_state": ("Every one begins with the word AVAILABLE, and %d of the 173 say the parcel is "
                                     "Not yet appraised. Both facts change as parcels are appraised and sold. A "
                                     "flyer archived today will be wrong, silently, at some unknown future date."
                                     % unappraised),
   "and_yet_they_are_real_city_documents": ("They are PDFs the City publishes about publicly owned land, which is "
                                            "exactly the subject an archive of City records exists for. Excluding "
                                            "173 of them on my own judgment would be a scope decision, not a "
                                            "measurement."),
  },
  "what_i_am_asking": ("Does this archive keep a dated snapshot of a live dataset? If yes, these should be taken as "
                       "one batch on one date and labelled as a snapshot of that date. If no, the right object to "
                       "capture is the underlying list rather than 173 generated sheets."),
  "the_precedent_for_asking": ("This run has referred three other class questions to a person rather than deciding "
                               "them: the Prescription Trails guides, the seven code enforcement notices naming "
                               "owners, and this. Each time the question was about what the archive is for, not "
                               "about what the file is."),
  "every_row_carries_what_it_says": ("Each of the 173 rows carries the parcel identifier, the property name, the "
                                     "acreage, the zoning and the appraisal status read from the file itself, so "
                                     "whoever decides can see the class without opening one."),
  "count": len(person),
  "combined_bytes": flyer_bytes,
  "zoning_codes_across_the_set": dict(zoning),
  "flyers_stating_no_zoning": no_zoning,
 },
 "what_the_flyers_themselves_turned_out_to_say": {
  "five_of_them_are_not_in_albuquerque": {
   "what": ("Five flyers are for City-owned land in Farmington: Parcel 1A at 42.5 acres, Parcel 2 at 50 acres, "
            "Parcel 3 at 40 acres, Choke Cherry at 2.5 acres and Hood Mesa at 340 acres - the largest parcel in "
            "the whole set."),
   "why_it_matters": ("The City of Albuquerque holds and is offering land two hundred miles away, and its "
                      "availability page publishes it alongside the city parcels. Whatever is decided about the "
                      "class, these five are a different question from the rest."),
   "and_they_are_laid_out_differently": ("None of the five states a zoning code, where all 168 Albuquerque flyers "
                                         "do. My first parse of these rows read the next token after the word "
                                         "Zoning and recorded a price or the word Not as the zoning. The harness "
                                         "caught it; the parser now reports a zoning only when the value is "
                                         "actually a zoning code, and marks the rest zoning_not_stated_on_this_"
                                         "flyer."),
   "the_rule": ("A field parser that assumes one layout will silently mislabel the records that use another. Check "
                "the shape of what you captured, not only that you captured something."),
  },
  "two_flyers_share_a_parcel_identifier": {
   "what": ("Farmington Parcel 1A (42.5 acres) and Farmington Choke Cherry (2.5 acres) both carry UPC "
            "2074175049476, published as 2074175049476(R003904).pdf and 2074175049476B.pdf."),
   "what_it_is_not": ("Not a duplicate: the two files differ in bytes, in acreage and in the property they name. "
                      "The parcel identifier is simply not unique across this set."),
   "the_consequence": ("If these are ever added, the parcel identifier cannot be the key. It was measured rather "
                       "than assumed: all 173 checksums are distinct, but 172 parcel identifiers cover 173 flyers."),
  },
 },
 "what_this_link_exposed": {
  "the_link": "sfftp.cabq.gov/f/licenses.txt",
  "what_it_is": "The City file-transfer application's reference to its own licence file. It is not a document and the URL returns the application shell.",
  "why_it_is_the_most_useful_row_in_this_lane": ("It could only have come from a file-share page - and the page it "
                                                 "was harvested from was one of the final-sweep lane's own "
                                                 "candidates. That is how src-2f89e1bc040e1d33, the Final "
                                                 "McDuffie-Twin Parks Traffic Calming Study, was found to have been "
                                                 "wrongly excluded as a web page. "
                                                 "final-sweep-cluster-research-2026-09-13.json now carries the "
                                                 "correction and that row is requires human review."),
  "the_general_point": "A harvested link that is not itself worth keeping can still tell you something about the page it came from.",
 },
 "the_federal_publications": {
  "excluded": 2,
  "which": "The Access Board's public rights-of-way accessibility guidelines, and a Federal Register page range.",
  "the_line_applied": ("A federal publication of general applicability is excluded; a federal instrument specific "
                       "to New Mexico is kept. So the FHWA-NMDOT stewardship and oversight agreement is "
                       "recommended and these two are not."),
  "consistent_with": "The FCC rules, the USDA-NRCS technical note, the NMAC licensing rule, the PNM tariff and the IRS form excluded earlier in this run.",
 },
 "containers_that_are_not_what_the_run_has_mostly_seen": {
  "two_legacy_OLE2_Word_documents": ("The Tribal/Local Public Agency level of effort form and The Road to Science, "
                                     "both served as .doc and both in the pre-2007 binary format, leading bytes "
                                     "d0cf11e0. Neither yields to a PDF reader or a ZIP reader; both were read with "
                                     "antiword."),
  "one_PowerPoint_deck": "The right-of-way training, 73 slides, read from its ppt/slides parts rather than assumed from its extension.",
  "four_spreadsheets": "The utilities materials calculator and the three crash data samples, read from xl/sharedStrings.xml.",
  "the_point": ("Eleven of the 36 files on other hosts are not PDFs, and no extension was trusted: every container was "
                "read from the bytes, and for OOXML from which part directory the archive holds."),
 },
 "method": ("Fetched and measured every file, verified each container by leading bytes and each OOXML file by its "
            "internal parts, read the two legacy binary Word documents with antiword and the PowerPoint from its "
            "slide parts, tested every PDF for its end-of-file marker, extracted text from all of them, rendered "
            "those that yielded none, and swept every checksum against all checksummed inventory records and every "
            "row of every saved artifact, and every URL against every inventory URL. For the flyers, parsed the "
            "parcel identifier, property, acreage, zoning and appraisal status out of each file's own text."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "For proposed additions, test against every inventory record rather than only the archived ones, and by URL as well as by checksum.",
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_SHA),
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing here is already in the inventory, and no two files in the lane are byte-identical - not even among 173 flyers generated by the same system.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(INTERNAL),
  "note": ("173 flyers generated from one system on one page, and all 173 checksums are distinct. That is what you "
           "would expect - each carries a different parcel - but it was measured rather than assumed."),
 },
 "integration_flags": [
  {"severity": "needs-a-person",
   "affects": [r['local_ref'] for r in person][:5] + ['... and %d more, one package' % (len(person) - 5)],
   "finding": ("173 real property availability flyers, generated from a live GIS, carrying no date of issue and a "
               "status that changes as parcels are appraised and sold."),
   "recommended_action": ("Decide as one package whether this archive keeps dated snapshots of live data. Do not "
                          "add them piecemeal.")},
  {"severity": "not-applicable-through-update-candidate",
   "affects": [],
   "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create the additions as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "substantive-find",
   "affects": ['hv-346', 'hv-012', 'hv-347', 'hv-348', 'hv-270'],
   "finding": ("The NMDOT NPDES stormwater manual, its Infrastructure Design Directives, two 2024 field guides, and "
               "the regional council's metropolitan planning boundaries map - all reachable from City pages and "
               "none in the inventory."),
   "recommended_action": "Add them, attributed to NMDOT and MRCOG."},
  {"severity": "label-as-draft",
   "affects": ['hv-014', 'hv-352', 'hv-010'],
   "finding": ("Three files announce their own provisional status: the DBE goal methodology begins DRAFT, the "
               "programmatic agreement is a draft for agency review, and the DBE program manual's filename says it "
               "is currently being revised."),
   "recommended_action": "Label each as provisional; do not present any of them as settled policy."},
  {"severity": "sample-not-data",
   "affects": ['hv-349', 'hv-350', 'hv-351'],
   "finding": "Three crash data files are sample data published to document the request schema, not real crash records.",
   "recommended_action": "Keep them for the schema and label them samples, so nobody reads them as crash statistics."},
  {"severity": "out-of-area",
   "affects": ['hv-343'],
   "finding": "The Cambray overpass poster is about a structure near Deming, not in Albuquerque.",
   "recommended_action": "Keep it only if the archive collects NMDOT's statewide historical series."},
  {"severity": "third-party-authority",
   "affects": ['hv-273', 'hv-355'],
   "finding": "Two federal publications of general applicability, linked from transport pages.",
   "recommended_action": "Do not add. Their publishers are the authoritative source, and the run has excluded five others on the same reasoning."},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": len(skip),
  "put_to_a_person_before_adding": len(person),
  "by_group": dict(bygroup),
  "containers": dict(containers),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": ", ".join('%d %s' % (v, k) for k, v in sorted(containers.items()))},
 "add_to_inventory": add,
 "do_not_add": skip,
 "needs_a_decision_from_a_person": person,
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready, and none is a candidate yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint of the additions: {add_bytes:,} bytes. The 173 flyers would add a further "
                   f"{flyer_bytes:,} bytes if a person decides to keep them."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes, the container read "
                      "from the file, and harvested_from. Every row carries inventory_id: null. The 173 flyer rows "
                      "are one package and must be decided together; each carries the parcel facts read from the "
                      "file so the class can be judged without opening them."),
 "the_harvest_is_now_complete": {
  "pages_parsed": 535,
  "document_links_found": 610,
  "already_inventory_records": 254,
  "already_decided_as_an_undiscovered_file": 1,
  "absent_from_the_inventory": 355,
  "decided_across_three_lanes": {
   "harvested-city-documents-research-2026-09-14.json": 69,
   "harvested-planning-documents-research-2026-09-14.json": 77,
   "harvested-remainder-research-2026-09-14.json": len(SLICE),
  },
  "and_it_corrected_an_earlier_artifact": ("final-sweep-cluster-research-2026-09-13.json, whose exclusion of the "
                                           "Final McDuffie-Twin Parks Traffic Calming Study was wrong."),
  "what_would_extend_it": ("Only 535 of the roughly 900 HTML pages this run excluded were still on disk to parse. "
                           "The rest were fetched in earlier lanes whose scratch files are gone. Re-fetching them "
                           "and harvesting their links is the obvious next move, and on this lane's yield it would "
                           "be worth it."),
 },
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('by_group', 'containers')}}))
