"""Claude research lane. Documents harvested from the links of City web pages
this run had already excluded, and absent from master-inventory.json.

Like undiscovered-documents-research-2026-09-14.json, these are NOT inventory
candidates: none has an inventory id, and nothing here can be applied through
Update-Candidate.ps1. It never modifies master-inventory.json, checkpoint.json,
r2-inventory.json, site content, or R2.

This lane covers the www.cabq.gov department documents. Dated 2026-09-14.
"""

import collections
import datetime
import glob
import json
import os
import re
import urllib.parse
import zipfile

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\harvested-city-documents-research-2026-09-14.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\harv')

ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'
BUDGET = 'content/city-data/budget-spending.md'
SAFETYDATA = 'content/city-data/public-safety-data.md'
PWORKS = 'content/public-works/_index.md'
PARKS = 'content/public-works/parks-recreation.md'
STORM = 'content/public-works/stormwater-drainage.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
DEVPROC = 'content/development-land-use/development-process.md'
CRASH = 'content/transportation/safety-crash-data.md'
TRANSPO = 'content/transportation/_index.md'
BIKE = 'content/transportation/bicycling/_index.md'

inv = json.load(open(INV, encoding='utf-8'))

M, MAGIC, URL, CODE, SRC = {}, {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if urllib.parse.urlsplit(p[5]).netloc != 'www.cabq.gov':
        continue
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], URL[p[0]], CODE[p[0]], SRC[p[0]] = p[4], p[5], p[1], p[6].strip()

SLICE = sorted(M)

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
              'add_to_inventory', 'do_not_add'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('checksum_sha256'):
                PRIOR_SHA.setdefault(r['checksum_sha256'],
                                     (os.path.basename(f), r.get('id') or r.get('local_ref')))

SHA_HIT = {i: ALL_SHA[M[i]['checksum_sha256']] for i in SLICE if M[i]['checksum_sha256'] in ALL_SHA}
URL_HIT = {i: INV_URL[norm(URL[i])] for i in SLICE if norm(URL[i]) in INV_URL}
ART_HIT = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE
           if M[i]['checksum_sha256'] not in ALL_SHA and M[i]['checksum_sha256'] in PRIOR_SHA}

KIND = {'25504446': 'PDF', '504b0304': 'OOXML'}


def container(i):
    if MAGIC[i] != '504b0304':
        return KIND[MAGIC[i]]
    n = zipfile.ZipFile(os.path.join(SP, 'files', i + '.bin')).namelist()
    return 'DOCX' if any(x.startswith('word/') for x in n) else \
           'XLSX' if any(x.startswith('xl/') for x in n) else \
           'PPTX' if any(x.startswith('ppt/') for x in n) else 'OOXML'


LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, and for OOXML by which of word/, xl/ or ppt/ the archive holds.")

LIQUOR = [i for i in SLICE if 'liquor-hearing' in URL[i] or 'notice-of-public-hearing-on' in URL[i]]

DOCS = {
 'hv-339': ("Third Amended Court Approved Settlement Agreement, United States v. City of Albuquerque",
   "police oversight and reform",
   ("The third amended settlement agreement between the United States and the City governing reform of the "
    "Albuquerque Police Department, filed in the federal case and approved on 2 June 2023."),
   ("524,507 bytes. Its first page is the court filing header: Case 1:14-cv-01025-JB-JFR, Document 988-2, Filed "
    "04/12/23, Page 2 of 107, IN THE UNITED STATES DISTRICT COURT FOR THE DISTRICT OF NEW MEXICO, UNITED STATES OF "
    "AMERICA, Plaintiff, vs. THE CITY OF ALBUQUERQUE."),
   ABOUT, [{"page": SAFETYDATA, "reason": "It governs how the police department is measured and reformed."}],
   ("A federal court document that the City publishes, not a City-authored one. Attribute it to the court "
    "proceeding; its filename records approval on 2 June 2023 while the filing stamp reads 12 April 2023.")),
 'hv-332': ("Downtown 2050 Redevelopment Plan, May 2025", "redevelopment plans",
   ("The City's Metropolitan Redevelopment Agency plan for downtown Albuquerque to 2050, prepared with an advisory "
    "committee and setting the redevelopment framework for the city centre."),
   ("10,265,747 bytes. Opens: DOWNTOWN 2050 ALBUQUERQUE REDEVELOPMENT PLAN, May 2025, ACKNOWLEDGMENTS, Advisory "
    "Committee, Metropolitan Redevelopment Agency (MRA) Staff, Terry Brunner, Director."),
   REDEV, [{"page": DEVPROC, "reason": "A framework development applications downtown are judged against."}], None),
 'hv-335': ("Parks and Recreation Department Design Guidelines", "design standards",
   ("The City's design guidelines for parks, setting out what a park design must address from general site "
    "considerations through demolition and preservation to document requirements."),
   ("2,499,178 bytes. Opens: CITY OF ALBUQUERQUE PARKS AND RECREATION DEPARTMENT DESIGN GUIDELINES, with sections "
    "for General Park Considerations, General Document Requirements, and Demolition and Preservation."),
   PARKS, [{"page": DEVPROC, "reason": "Standards a design must meet."}], None),
 'hv-269': (None,) * 7,
 'hv-274': ("Ethics and Code of Conduct training module, 2016", "city governance",
   ("The City's public-service ethics training module, the material City employees are taught on standards of "
    "conduct and the code they work under."),
   ("1,188,351 bytes. Opens: ETHICS & CODE OF CONDUCT TRAINING MODULE, City of Albuquerque, New Mexico, Public "
    "Service Ethics."),
   ABOUT, [], None),
 'hv-275': ("Citizens' Independent Salary Commission report, 29 March 2023", "salary commission",
   ("The commission's 2023 report to the City on the salaries of elected officials, delivered as an interoffice "
    "memorandum from the independent body that reviews what the City pays them."),
   ("1,145,820 bytes. Opens with a DocuSign envelope identifier, then: City of Albuquerque Citizens' Independent "
    "Salary Commission, Interoffice Memorandum, March 29, 2023."),
   BUDGET, [{"page": ABOUT, "reason": "A record of how the City sets elected officials' pay."}], None),
 'hv-276': ("Citizens' Independent Salary Commission final memorandum, 7 March 2025", "salary commission",
   ("The commission's final memorandum of March 2025 on the salaries of the City's elected officials, one of two "
    "final memoranda the commission issued during 2025."),
   ("2,296,507 bytes. Opens with a Docusign envelope identifier, then: Citizens' Independent Salary Commission, "
    "City of Albuquerque, Final Memorandum, March 7, 2025."),
   BUDGET, [{"page": ABOUT, "reason": "A record of how the City sets elected officials' pay."}],
   "Two 2025 final memoranda exist, dated 7 March and 31 December. Keep both and date them; neither supersedes the other on its face."),
 'hv-277': ("Citizens' Independent Salary Commission final memorandum, 31 December 2025", "salary commission",
   ("The commission's final memorandum of December 2025 on the salaries of the City's elected officials, the later "
    "of the two final memoranda issued that year."),
   ("1,495,614 bytes. Opens with a Docusign envelope identifier, then: Citizens' Independent Salary Commission, "
    "City of Albuquerque, Final Memorandum, December 31, 2025."),
   BUDGET, [{"page": ABOUT, "reason": "A record of how the City sets elected officials' pay."}],
   "The companion to the 7 March 2025 memorandum. Date both."),
 'hv-278': ("Citizens' Independent Salary Commission agenda, 25 November 2025", "salary commission",
   ("The agenda for the commission's meeting of 25 November 2025, listing the business the independent salary "
    "commission took and naming the members who sat."),
   ("526,476 bytes. Opens: Citizens' Independent Salary Commission, Office of Internal Audit, Teleconference Via "
    "Zoom, with the chairperson and members named."),
   BUDGET, [{"page": ABOUT, "reason": "A record of a City commission's proceedings."}],
   ("An agenda, not minutes. The missing-minutes rule applies: keep it only if a recorded exhaustive search finds "
    "no approved minutes for this commission, and label it Agenda (approved minutes not located). That search has "
    "not been run for this body.")),
 'hv-280': ("Inspection of Public Records Act annual report, fiscal year 2025", "public records reporting",
   ("The City Clerk's annual account of how the City handled public records requests in fiscal 2025, with the "
    "statistical breakdown of volume, closure and backlog."),
   ("7,501,862 bytes. Opens: FISCAL YEAR ANNUAL REPORT 2025, OFFICE OF THE CITY CLERK, with a contents list running "
    "Intro, Statistical Breakdown, Message from the Clerk, Our Team, A Broken Law, Closure."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-281': ("Inspection of Public Records Act backlog reduction report, first quarter fiscal 2025",
   "public records reporting",
   ("The City Clerk's first-quarter report on reducing the public records request backlog, covering July to "
    "September 2024 and by far the largest file in this lane."),
   ("43,098,667 bytes. Opens: CITY PROGRESS AMID SURGING REQUESTS, FIRST QUARTER IPRA BACKLOG REDUCTION REPORT 2024 "
    "(JULY 1ST - SEPTEMBER 30)."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-282': ("Inspection of Public Records Act backlog reduction report, second quarter fiscal 2025",
   "public records reporting",
   ("The City Clerk's second-quarter report on the public records request backlog, covering October to December "
    "2024 in the same series as the first-quarter report."),
   ("10,029,120 bytes. Opens: DRIVING CHANGE, REDUCING BACKLOG, Second Quarter IPRA Backlog Reduction Report FY2025 "
    "(OCTOBER 1ST - DECEMBER 31)."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-283': ("Inspection of Public Records Act report, third quarter fiscal 2025", "public records reporting",
   ("The City Clerk's third-quarter summary of public records request activity, covering January to March 2025 and "
    "presented as figures rather than narrative."),
   ("3,917,390 bytes. Opens: IPRA BY THE NUMBERS: Third Quarter Fiscal Year 2025, FY2025 (JANUARY 1 - MARCH 31)."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-284': ("Inspection of Public Records Act report, first quarter fiscal 2026", "public records reporting",
   ("The City Clerk's first-quarter report on public records requests for fiscal 2026, continuing the quarterly "
    "series and reporting how video requests are reshaping the workload."),
   ("9,277,008 bytes. Opens: FIRST QUARTER IPRA REPORT FY26, OFFICE OF THE CITY CLERK, with contents including Our "
    "Team, Video is Reshaping IPRA, Comparing Quarterly Growth."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-285': ("Inspection of Public Records Act report, second and third quarters fiscal 2026",
   "public records reporting",
   ("The City Clerk's combined report on public records requests for the second and third quarters of fiscal 2026, "
    "the most recent in the quarterly series."),
   ("5,471,356 bytes. Opens: SECOND AND THIRD QUARTERS IPRA REPORT FY26, OFFICE OF THE CITY CLERK, and its opening "
    "pages name the requesting organisations by city."),
   ABOUT, [{"page": CITYDATA, "reason": "Reported City performance data."}], None),
 'hv-286': ("Inspection of Public Records Act fee and cost schedule, 2026", "public records reporting",
   ("The City Clerk's schedule of the fees and costs charged for inspecting and copying public records in 2026, and "
    "how the City invoices a requester."),
   ("196,380 bytes. Opens with a Docusign envelope identifier, then: 2026 INSPECTION OF PUBLIC RECORD ACT (IPRA) "
    "FEE AND COST SCHEDULE, ALBUQUERQUE CITY CLERK."),
   ABOUT, [], None),
 'hv-287': ("Local Government Coordinating Commission agenda, 20 August 2026", "council records",
   ("The agenda for the joint City and County coordinating commission's meeting of 20 August 2026, naming the chair "
    "and vice-chair and listing the business before it."),
   ("174,668 bytes. Opens: City of Albuquerque Government Center, Agenda, Local Government Coordinating Commission, "
    "One Civic Plaza, Chair Nichole Rogers, Councilor, District 6."),
   ABOUT, [{"page": CITYDATA, "reason": "A record of City and County coordination."}],
   ("An agenda kept under the missing-minutes exception, on the review recorded in "
    "council-qa-lgcc-news-cluster-research-2026-09-13.json. That review found no approved LGCC minutes on the City "
    "side, and the County side could not be checked because www.bernco.gov returned HTTP 403. Label it Agenda "
    "(approved minutes not located), and note the review was not exhaustive.")),
 'hv-288': ("Albuquerque City Council: Council Services organisation chart, August 2026", "city governance",
   ("The organisation chart for the City Council's own staff office, naming the Director of Council Services and "
    "the deputy directors and showing how Council Services is structured."),
   ("90,275 bytes. Opens: Albuquerque City Council, Director of Council Services, Deputy Director, Council Policy, "
    "General Counsel. Its filename dates it 24 August 2026."),
   ABOUT, [], None),
 'hv-326': ("Lodgers' Tax Ordinance, Article 4", "city ordinances",
   ("Article 4 of the City's code of ordinances imposing the lodgers' tax, setting out the authority for the tax, "
    "who owes it, the exemptions, and how the proceeds may be used."),
   ("63,450 bytes. Opens with the article's own contents: ARTICLE 4: LODGERS' TAX, 4-4-1 Short title, 4-4-2 "
    "Authority, 4-4-3 Purpose, 4-4-4 Definitions, 4-4-6 Imposition of tax, use of proceeds, 4-4-7 Exemptions."),
   BUDGET, [{"page": ABOUT, "reason": "A City ordinance."}], None),
 'hv-327': ("Notice of the 2026 Albuquerque minimum wage rate", "minimum wage",
   ("The City's published notice of the minimum wage and tipped minimum wage that apply in Albuquerque during 2026, "
    "issued in English and Spanish as the ordinance requires."),
   ("150,646 bytes. Opens: NOTICE REGARDING 2026 MINIMUM WAGE RATE IN THE CITY OF ALBUQUERQUE, and states that the "
    "Minimum Wage Ordinance requires the City to post the adjusted rates."),
   ABOUT, [{"page": CITYDATA, "reason": "A published City rate."}], None),
 'hv-328': ("Minimum Wage Ordinance as amended, Article 12", "minimum wage",
   ("Article 12 of the City's code of ordinances setting the Albuquerque minimum wage, in its amended form, "
    "including the notice, posting, record-keeping and enforcement provisions."),
   ("199,048 bytes. Opens with the article's contents: ARTICLE 12: MINIMUM WAGE, 13-12-1 Short title, 13-12-2 "
    "Definitions, 13-12-3 Minimum wage, 13-12-4 Notice, posting and records, 13-12-5 Implementation and "
    "enforcement."),
   ABOUT, [], None),
 'hv-329': ("Rule regarding enforcement of the Albuquerque Minimum Wage Ordinance", "minimum wage",
   ("The City's administrative rule for enforcing its minimum wage ordinance, setting out how an employee complains, "
    "how the Legal Department demands compliance, and what happens if an employer does not comply."),
   ("362,322 bytes, no text layer, read by rendering. Page 1 is headed Rule Regarding Enforcement of the "
    "Albuquerque Minimum Wage Ordinance and states it is an administrative rule required by the ordinance, ROA "
    "1994 section 13-12-1 et seq., with sections on Contact Information, Initial Demand Letter and Civil "
    "Litigation."),
   ABOUT, [],
   "Its filename says english-spanish; only the English text was read. Confirm whether a Spanish version follows in the same file."),
 'hv-330': ("City of Albuquerque organisation chart, accessible version", "city governance",
   ("The City's organisation chart in its accessible form, running from the people of Albuquerque through the Mayor "
    "and Council to the Chief Administrative Officer, and naming the councillors by district."),
   ("227,594 bytes. Opens: The People of Albuquerque, City of Albuquerque, Mayor, City Council, Chief "
    "Administrative Officer, with councillors listed by district."),
   ABOUT, [], "The accessible companion to the graphical chart; keep the pair together."),
 'hv-331': ("City of Albuquerque organisation chart", "city governance",
   ("The City's organisation chart as a designed graphic, the visual companion to the accessible version published "
    "beside it on the Mayor's pages."),
   ("922,752 bytes with no text layer at all, four times the size of the accessible version, which is what an "
    "image-set chart against a tagged one looks like."),
   ABOUT, [],
   "No text layer, so nothing in it is searchable or screen-readable. The accessible version is the one to cite."),
 'hv-334': ("Mid Rio Grande Stormwater Quality Team: public information sheet", "stormwater",
   ("The public information sheet for the regional stormwater quality partnership between the City, the flood "
    "control authority, the state transportation department and the other Middle Rio Grande members."),
   ("704,215 bytes. Opens: The Mid Rio Grande Stormwater Quality Team is a joint effort of the City of Albuquerque, "
    "Albuquerque Metropolitan Arroyo and Flood Control Authority (AMAFCA), New Mexico Department of "
    "Transportation."),
   STORM, [], None),
 'hv-338': ("New Mexico Uniform Crash Report: station report form", "crash reporting",
   ("The Albuquerque Police Department's version of the state uniform crash report form, the instrument on which "
    "every reported collision in the city is recorded."),
   ("462,921 bytes. Opens: CRASH, Albuquerque Police Department, STATE OF NEW MEXICO UNIFORM CRASH REPORT "
    "INVESTIGATION, SH 10074, Rev July 2018."),
   CRASH, [{"page": SAFETYDATA, "reason": "The instrument behind the City's crash statistics."}],
   "The form is a State of New Mexico instrument that the police department publishes; attribute it accordingly."),
 'hv-340': ("New Mexico Uniform Crash Report, fillable, Spanish", "crash reporting",
   ("The Spanish-language fillable version of the state uniform crash report form as published by the Albuquerque "
    "Police Department, the companion to the English station report."),
   ("8,992,730 bytes. Opens: CRASH, STATE OF NEW MEXICO UNIFORM CRASH REPORT INVESTIGATION, Departamento de Policia "
    "de Albuquerque, SH 10074, Rev July 2018."),
   CRASH, [{"page": SAFETYDATA, "reason": "The instrument behind the City's crash statistics."}],
   "Nineteen times the size of the English station report, which is what an embedded fillable form layer costs."),
 'hv-341': ("Manzano Mesa Multigenerational Center newsletter, September 2026", "centre newsletters",
   ("The monthly newsletter for the City's Manzano Mesa Multigenerational Center, listing centre hours, staff and "
    "the programme of activities for September 2026."),
   ("5,058,218 bytes. Opens with the centre's address at 501 Elizabeth St SE, its hours, and its 2026 Newsletter "
    "masthead with the centre staff named."),
   PARKS, [],
   ("A dated monthly newsletter. Keep it only if the archive holds programme ephemera, the same question raised by "
    "the Bike Month flyer in the final-sweep lane.")),
 'hv-001': ("Solid Waste Management residential disability form", "service forms",
   ("The City form by which an elderly or disabled resident who cannot move their carts to the kerb asks the Solid "
    "Waste Management Department for assisted collection."),
   ("151,474 bytes. Opens: SOLID WASTE MANAGEMENT DEPARTMENT, CITY OF ALBUQUERQUE, Residential Disability Form, "
    "addressed to an individual who is elderly or disabled and unable to place their garbage carts at the kerb."),
   PWORKS, [],
   "Reached over http; the City server answers on https and the row records the https URL actually fetched."),
}

EXCLUDE = {
 'hv-279': ("Citizens' Independent Salary Commission public notice, 25 November 2025",
            "A notice that the commission would meet, giving the date and the Zoom details.",
            ("A notice of a meeting, not a record of one. This run excluded nine notices of meeting in the EDAct "
             "lane on the same reasoning: the missing-minutes exception covers agendas, which state the business, "
             "not bare notices that a meeting will happen. The agenda for this same meeting is recommended above."),
            "notice of meeting", "meeting_notices"),
 'hv-333': ("Greater Albuquerque Active Transportation Committee: notice of meeting cancellation, 14 September 2026",
            "A notice from the Department of Municipal Development that a GAATC meeting would not take place.",
            ("A cancellation notice. The archive's rule is explicit that nothing is preserved for a cancelled or "
             "no-quorum meeting, and a notice that a meeting did not happen is the clearest case of it."),
            "notice of cancellation", "meeting_notices"),
}

DO_NOT_ADD = {
 'hv-325': {
  "title_for_reference": "Civilian Police Oversight Ordinance",
  "what_it_is": "The City ordinance establishing civilian oversight of the police department.",
  "why_not": ("Already decided. It is byte-identical - 11,359,271 bytes and the same SHA-256 - to a candidate "
              "already recommended for addition in final-sweep-cluster-research-2026-09-13.json as "
              "src-28216ed513e1c171, reached there through a resolveuid alias under the oversight board application "
              "page. Adding it again would tell Codex to archive one file twice."),
  "the_relationship": ("Two City pages publish the same ordinance at two addresses, one an opaque alias and one a "
                       "plain path under cpoa/documents. The plain path is the better citation."),
 },
 'hv-336': {
  "title_for_reference": "Volcano Business Park Master Development Plan",
  "what_it_is": "A master development plan for the Volcano Business Park.",
  "why_not": ("The same file, byte for byte, is served at "
              "documents.cabq.gov/planning/MasterDevelopmentPlans/VolcanoBusinessParkMP.pdf and belongs to the "
              "master development plan set, which is a separate lane. Deciding it here would create a second "
              "candidate for one file and split the set."),
  "where_it_will_be_decided": "The documents.cabq.gov planning tree, 77 files, claimed as the next lane.",
 },
 'hv-337': {
  "title_for_reference": "Volcano Point Master Development Plan",
  "what_it_is": "A master development plan for Volcano Point.",
  "why_not": ("The same file, byte for byte, is served at "
              "documents.cabq.gov/planning/MasterDevelopmentPlans/VolcanoPointMP.pdf and belongs to the master "
              "development plan set. Same reasoning as the Volcano Business Park plan."),
  "where_it_will_be_decided": "The documents.cabq.gov planning tree, 77 files, claimed as the next lane.",
 },
}

MONTHS = ('january february march april may june july august september october november december').split()


def hearing_date(i):
    m = re.search(r'on-(' + '|'.join(MONTHS) + r')-(\d{1,2})-(20\d\d)', urllib.parse.unquote(URL[i]).lower())
    if not m:
        return None
    return '%s %s %s' % (m.group(2), m.group(1).capitalize(), m.group(3))


def text(i):
    p = os.path.join(SP, 'txt', i + '.txt')
    if os.path.exists(p):
        return open(p, encoding='utf-8', errors='replace').read()
    if MAGIC[i] == '504b0304':
        z = zipfile.ZipFile(os.path.join(SP, 'files', i + '.bin'))
        if 'word/document.xml' in z.namelist():
            return re.sub(r'<[^>]+>', ' ', z.read('word/document.xml').decode('utf-8', 'replace'))
    return ''


def row(i, rec):
    return {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i],
            "filename": urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1]),
            "harvested_from": SRC[i], "recommendation": rec, "link_check": LC,
            "content_kind": container(i), "leading_bytes": MAGIC[i], "http_status": CODE[i], **M[i]}


add, skip, excluded = [], [], []

for i, spec in DOCS.items():
    if spec[0] is None:
        continue
    t, group, desc, ev, canon, cross, caution = spec
    r = row(i, "add to the inventory as a new candidate")
    r.update({"title": t, "group": group, "description": desc, "evidence": ev,
              "description_word_count": len(desc.split()),
              "proposed_canonical_page": canon, "cross_listings": cross})
    if caution:
        r["caution"] = caution
    add.append(r)

for i, spec in DO_NOT_ADD.items():
    r = row(i, "do not add")
    r.update(spec)
    skip.append(r)

for i, (t, what, why, cat, pkg) in EXCLUDE.items():
    r = row(i, "do not add")
    r.update({"title_for_reference": t, "what_it_is": what, "why_not": why, "category": cat, "package": pkg})
    skip.append(r)

for i in LIQUOR:
    d = hearing_date(i)
    tx = re.sub(r'\s+', ' ', text(i))
    r = row(i, "do not add")
    r.update({
     "title_for_reference": "Notice of public liquor hearing, %s" % (d or "date not in the filename"),
     "what_it_is": ("A statutory notice that the City's Liquor Hearing Officer will hold a public hearing on liquor "
                    "licence applications, listing each application number, the applicant, the trading name, the "
                    "proposed address and the licence sought."),
     "why_not": ("A notice that a hearing will be held, not a record of what was decided at it. This run has "
                 "excluded notices of meeting on exactly this reasoning; the archival value in liquor licensing is "
                 "in the hearing officer's decisions, and those are not published at this path. Thirty-six of these "
                 "notices are published here as a rolling series, most of them for hearings still in the future."),
     "category": "statutory hearing notice",
     "package": "liquor_hearing_notices",
     "hearing_date": d,
     "the_officer_named": "Steven M. Chavez, Esq., City of Albuquerque Liquor Hearing Officer",
     "statutory_basis": "Section 60-6B-4D(1) NMSA 1978 as amended, and Section 13-2-1 Revised Ordinances of Albuquerque 1994 as amended",
     "applicants_are_businesses": ("The applications name licence holders - companies and trading names - rather "
                                   "than private individuals, so this exclusion is about record type, not about "
                                   "anyone's privacy."),
     "date_confirmed_in_the_text": bool(d and re.search(re.escape(d.split()[1]) + r'\s+' + d.split()[0] + r',?\s+' + d.split()[2], tx, re.I)),
    })
    skip.append(r)

DONE = {x['local_ref'] for x in add + skip + excluded}
missing = [i for i in SLICE if i not in DONE]
assert not missing, missing

rows = add + skip
assert len(rows) == len(SLICE), (len(rows), len(SLICE))
bygroup = collections.Counter(r.get('group') for r in add)
bypkg = collections.Counter(r.get('package') for r in skip if r.get('package'))
add_bytes = sum(r['size_bytes'] for r in add)
containers = collections.Counter(r['content_kind'] for r in rows)

artifact = {
 "batch_id": "harvested-city-documents-research-2026-09-14",
 "lane": "Claude research lane: documents harvested from the links of pages this run had already excluded (www.cabq.gov)",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": ("None of these files has an inventory id. Every row carries inventory_id: null, the field is "
                      "called recommendation rather than recommended_status, and the values are add to the "
                      "inventory as a new candidate, and do not add."),
  "so_it_cannot_be_applied_the_usual_way": ("Update-Candidate.ps1 changes the status of an existing candidate and "
                                            "cannot act on any row here. These are proposed additions; they must be "
                                            "created as candidates first, after which the ordinary archival gate "
                                            "applies."),
 },
 "where_this_lane_came_from": {
  "the_method": ("Two earlier lanes parsed City pages for document links before discarding the pages, and found 41 "
                 "files the crawl had missed. That method had been applied to two pages. This lane applies it to "
                 "every HTML page this run excluded and still had on disk."),
  "what_was_parsed": ("535 stored HTML pages from the final-sweep and find-your-councilor lanes, for links ending "
                      "in pdf, doc, docx, xls, xlsx, ppt, pptx, csv, rtf or txt."),
  "what_came_out": ("610 distinct document links. 254 are already inventory records, 1 had already been decided as "
                    "an undiscovered file, and 355 were absent from the inventory by URL."),
  "all_355_were_fetched": ("Every one returned HTTP 200 and real document bytes: 336 PDF, 16 OOXML, 2 legacy OLE2, "
                           "and 1 that is the file-share application's own licence file. 1,326,543,013 bytes in "
                           "total. No PDF among them is truncated."),
  "this_lane_is_the_first_slice_of_that": ("The %d files served from www.cabq.gov. The 77 from documents.cabq.gov, "
                                           "the 173 real property flyers from dmdgis.cabq.gov and the 36 on "
                                           "third-party hosts are separate lanes." % len(SLICE)),
 },
 "the_correction_this_method_forced": {
  "what": ("Parsing these pages turned up a link to sfftp.cabq.gov/f/licenses.txt - a file that could only come "
           "from the City's file-transfer application. The page it came from was one of the final-sweep lane's own "
           "candidates."),
  "the_consequence": ("final-sweep-cluster-research-2026-09-13.json had excluded src-2f89e1bc040e1d33 as a live web "
                      "page. It is titled Final McDuffie-Twin Parks Traffic Calming Study, and its 1,344 bytes are "
                      "a JavaScript file-share shell with a document behind it. That artifact has been corrected: "
                      "the row is now requires human review, for retrieval through a browser."),
  "why_it_matters_here": ("The method does not only find documents the crawl missed. It finds mistakes in the "
                          "decisions already made about the pages it parses."),
 },
 "what_the_sweep_found": {
  "checksum_collisions_with_the_inventory": len(SHA_HIT),
  "url_collisions_with_the_inventory": len(URL_HIT),
  "collisions_with_saved_artifacts": len(ART_HIT),
  "sets_compared_against": {"all_checksummed_inventory_records": len(ALL_SHA),
                            "archived_inventory_records": len(ARCH_SHA),
                            "inventory_urls": len(INV_URL),
                            "saved_artifact_rows": len(PRIOR_SHA)},
  "what_it_caught": ("One file in this lane is byte-identical to a candidate this run has already recommended: the "
                     "Civilian Police Oversight Ordinance, approved yesterday under a resolveuid alias and served "
                     "here at a plain path. Without the sweep it would have been proposed as a new candidate for a "
                     "file already queued for archival."),
 },
 "the_substance": {
  "the_settlement_agreement": ("The Third Amended Court Approved Settlement Agreement in United States v. City of "
                              "Albuquerque, the federal agreement governing police reform, approved 2 June 2023 and "
                              "filed as Document 988-2 in case 1:14-cv-01025. It is a court document the City "
                              "publishes, and its row says so."),
  "the_public_records_series": ("Six City Clerk reports on public records requests - the fiscal 2025 annual report "
                                "and quarterly reports through the second and third quarters of fiscal 2026 - a "
                                "complete recent series, none of it in the inventory."),
  "the_salary_commission": ("Three Citizens' Independent Salary Commission reports and one agenda. Two of the three "
                           "are final memoranda dated within the same year, 7 March and 31 December 2025; neither "
                           "supersedes the other on its face and both rows say to date them."),
  "the_wage_and_tax_instruments": ("The Minimum Wage Ordinance as amended, the administrative rule for enforcing "
                                  "it, the 2026 rate notice, and the Lodgers' Tax ordinance."),
  "and_downtown_2050": "The Metropolitan Redevelopment Agency's Downtown 2050 Redevelopment Plan of May 2025.",
 },
 "the_liquor_notices": {
  "count": len(LIQUOR),
  "what_they_are": ("A rolling series of statutory notices that the City's Liquor Hearing Officer will hear liquor "
                    "licence applications, each listing the application number, applicant, trading name, proposed "
                    "address and licence sought."),
  "why_all_of_them_are_excluded": ("They announce hearings; they do not record them. This run excluded nine notices "
                                   "of meeting in the EDAct lane on the same distinction - the missing-minutes "
                                   "exception covers agendas, which state business, not bare notices. The archival "
                                   "value in liquor licensing is the hearing officer's decisions, and those are not "
                                   "published at this path."),
  "most_are_for_hearings_that_have_not_happened": ("Their dates run from August 2025 to October 2026, so the "
                                                   "majority are notices of future hearings - live announcements "
                                                   "rather than records."),
  "four_of_them_are_Word_documents": ("The series is published mostly as PDF but four are .docx, and their "
                                      "container was read from the OOXML archive's word/ parts rather than assumed "
                                      "from the extension. Their URLs end .docx, so the extension is honest here - "
                                      "which is worth stating, because this run has met several cases where it was "
                                      "not."),
  "no_private_individuals_are_named": ("The applicants are licence holders and trading names. The exclusion is "
                                       "about record type, not privacy - unlike the code enforcement notices this "
                                       "run referred to a person."),
 },
 "method": ("Parsed 535 stored HTML pages for document links, reconciled them against every inventory URL, fetched "
            "and measured the remainder, verified each container by leading bytes and each OOXML file by its "
            "internal parts, tested every PDF for its end-of-file marker, extracted text from all of them and "
            "rendered the ones that yielded none, and swept every checksum against all checksummed inventory "
            "records and every row of every saved artifact."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "For proposed additions, test against every inventory record rather than only the archived ones, and by URL as well as by checksum.",
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "archived_records_compared_against": len(ARCH_SHA),
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "One collision, with a candidate this run recommended yesterday. Nothing here is already in the inventory.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "collisions_with_earlier_artifacts": len(ART_HIT),
  "collisions_with_the_next_lane": 2,
  "note": ("Two files here are byte-identical to files in the documents.cabq.gov planning tree, which is the next "
           "lane. They are recorded as do not add and point at where they will be decided, rather than being "
           "proposed twice."),
 },
 "integration_flags": [
  {"severity": "not-applicable-through-update-candidate",
   "affects": [r['local_ref'] for r in rows],
   "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create the additions as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "substantive-find",
   "affects": ['hv-339', 'hv-332', 'hv-280', 'hv-281', 'hv-328'],
   "finding": ("The federal police reform settlement agreement, the Downtown 2050 Redevelopment Plan, a complete "
               "recent series of City Clerk public records reports, and the Minimum Wage Ordinance as amended - "
               "none of it in the inventory, all of it reachable from pages this run had already excluded."),
   "recommended_action": "Add them."},
  {"severity": "method",
   "affects": [],
   "finding": ("Harvesting links from excluded pages produced %d documents from www.cabq.gov alone, and corrected a "
               "decision in an earlier artifact." % len(add)),
   "recommended_action": "Harvest links from any HTML candidate before discarding it, and re-check the pages already discarded."},
  {"severity": "attribution",
   "affects": ['hv-339', 'hv-338', 'hv-340'],
   "finding": "The settlement agreement is a federal court document and the crash report forms are State of New Mexico instruments; the City publishes all three.",
   "recommended_action": "Keep them and attribute them to their authors."},
  {"severity": "missing-minutes-rule",
   "affects": ['hv-287', 'hv-278'],
   "finding": ("Two agendas. The LGCC agenda rests on the review recorded yesterday, which could not check the "
               "County side because bernco.gov returned 403. The salary commission agenda rests on no review at "
               "all."),
   "recommended_action": ("Label the LGCC agenda Agenda (approved minutes not located) and record that its review "
                          "was not exhaustive. Run a minutes search for the Citizens' Independent Salary Commission "
                          "before keeping its agenda.")},
  {"severity": "accessibility",
   "affects": ['hv-331', 'hv-330'],
   "finding": "The City publishes its organisation chart twice: a 922,752-byte graphic with no text layer at all, and a 227,594-byte accessible version.",
   "recommended_action": "Keep both, cite the accessible one."},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": len(skip),
  "by_group": dict(bygroup),
  "do_not_add_by_package": dict(bypkg),
  "containers": dict(containers),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": ", ".join('%d %s' % (v, k) for k, v in sorted(containers.items()))},
 "add_to_inventory": add,
 "do_not_add": skip,
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready, and none is a candidate yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint if all are added and archived: {add_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Each row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes, the container read "
                      "from the file, and harvested_from - the City page whose links led to it. Every row carries "
                      "inventory_id: null."),
 "what_remains_of_this_harvest": ("Three lanes: the 77 documents.cabq.gov planning files (master development plans, "
                                  "framework plans, development review board and form material), the 173 real "
                                  "property flyers from dmdgis.cabq.gov, and the 36 files on third-party hosts "
                                  "(NMDOT, MRCOG, federal agencies, and the City transit and file-share hosts)."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('by_group', 'containers', 'do_not_add_by_package')}}))
