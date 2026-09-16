"""Claude research lane. The documents.cabq.gov planning files harvested from
the links of City pages this run had already excluded, and absent from
master-inventory.json.

Like the other harvest lanes, these are NOT inventory candidates: none has an
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
       r'\harvested-planning-documents-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\harv')

AREAPLANS = 'content/development-land-use/area-sector-plans.md'
DEVPROC = 'content/development-land-use/development-process.md'
ZONING = 'content/development-land-use/zoning-ido.md'
PROJECTS = 'content/development-land-use/projects.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
BUDGET = 'content/city-data/budget-spending.md'
ABOUT = 'content/about/_index.md'
STORM = 'content/public-works/stormwater-drainage.md'

inv = json.load(open(INV, encoding='utf-8'))

M, MAGIC, URL, CODE, SRC = {}, {}, {}, {}, {}
ALLF = {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    ALLF[p[0]] = p
    if urllib.parse.urlsplit(p[5]).netloc != 'documents.cabq.gov':
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
# the two Volcano plans were deferred here from the www.cabq.gov lane
DEFERRED_TO_HERE = {i: PRIOR_SHA.get(M[i]['checksum_sha256']) for i in SLICE
                    if M[i]['checksum_sha256'] in PRIOR_SHA}


def container(i):
    if MAGIC[i] != '504b0304':
        return {'25504446': 'PDF'}[MAGIC[i]]
    n = zipfile.ZipFile(os.path.join(SP, 'files', i + '.bin')).namelist()
    return 'DOCX' if any(x.startswith('word/') for x in n) else \
           'XLSX' if any(x.startswith('xl/') for x in n) else \
           'PPTX' if any(x.startswith('ppt/') for x in n) else 'OOXML'


def pages(i):
    if MAGIC[i] != '25504446':
        return None
    return len(re.findall(rb'/Type\s*/Page[^s]', open(os.path.join(SP, 'files', i + '.bin'), 'rb').read()))


LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, and for OOXML by which of word/, xl/ or ppt/ the archive holds. Every "
      "PDF was tested for its end-of-file marker.")

RENDERED = ("has no text layer on any page, so it was read by rendering")

MDS = "mesa del sol"
MDP = "master development plans"
DRV = "development review"
BSF = "building safety"
BIZ = "business licensing"
SWF = "small wireless facilities"
TRY = "treasury policy"
HIS = "historic zones"

D = {
 # ---- Mesa del Sol -------------------------------------------------------
 'hv-211': ("Mesa del Sol Level A Community Master Plan, as amended 2024", MDS,
   ("The community master plan for Mesa del Sol, the roughly 13,000-acre planned community east of Interstate 25, "
    "in its June 2005 form as amended through February 2023, submitted by the developer to the City."),
   ("83,400,243 bytes. Opens: COMMUNITY MASTER PLAN, LEVEL A PLAN: JUNE 2005, AMENDED FEBRUARY 20234, Submitted by "
    "Forest City Covington New Mexico. The date on its own cover reads 20234, which is a typing error in the "
    "document, not in this row."),
   AREAPLANS, [{"page": ZONING, "reason": "A framework plan the code judges applications against."}],
   "Its cover misprints the amendment year as 20234. Quote it as it stands and note the error rather than silently correcting it."),
 'hv-210': ("Mesa del Sol Level B Plan, as amended 2024", MDS,
   ("The Level B plan for Mesa del Sol, which functions as the sector development plan for sub-areas inside the "
    "Level A community master plan, in its amended 2024 form."),
   ("57,751,846 bytes. Its extracted text is the display-font jumble typical of a designed cover, reading in part "
    "MASTER PLAN LEVEL B PLAN AS APPROVED, DEVELOPMENT REVIEW BOARD, FEBRUARY 2008."),
   AREAPLANS, [{"page": ZONING, "reason": "A plan the code judges applications against."}], None),
 'hv-218': ("Mesa del Sol Level B Plan: technical appendices, revised August 2021", MDS,
   ("The technical appendices to the Mesa del Sol Level B plan, the supporting studies behind the plan, in the "
    "October 2006 edition revised in August 2021 and filed under project PR-2021-005684."),
   ("142,963,930 bytes, the largest file in this lane. Opens: TECHNICAL APPENDICES, LEVEL B PLAN: OCTOBER 2006, "
    "REVISED AUGUST 2021, Submitted by Forest City Covington New Mexico."),
   AREAPLANS, [{"page": ZONING, "reason": "Supporting studies behind a framework plan."}], None),
 'hv-209': ("Mesa del Sol Level B Plan, Appendix B: wireless telecommunications facilities", MDS,
   ("The appendix regulating how wireless telecommunication facilities may look and where they may stand inside "
    "Mesa del Sol, written because the Level B plan was silent on wireless while covering every other utility."),
   ("204,347 bytes, one page, " + RENDERED + ". It is headed APPENDIX B TO MESA DEL SOL LEVEL B PLAN, REGULATING "
    "THE APPEARANCE AND LOCATION OF WIRELESS TELECOMMUNICATIONS FACILITIES (WTFs), and sets height limits of 120 "
    "feet for primary and 60 feet for secondary facilities."),
   AREAPLANS, [{"page": ZONING, "reason": "It modifies how the zoning code's wireless section applies."}], None),
 'hv-212': ("Official Notification of Decision: Mesa del Sol Level B wireless amendment, 19 September 2008", MDS,
   ("The City's formal notice that the Environmental Planning Commission approved the Level B master plan amendment "
    "on wireless telecommunications facilities for the roughly 3,100-acre Level B plan area."),
   ("414,476 bytes, " + RENDERED + ". Dated September 19, 2008, file Project# 1004075 / 08EPC-40047, addressed to "
    "Forest City Covington NM LLC, recording that the EPC voted to approve on September 18, 2008."),
   AREAPLANS, [], None),
 'hv-217': ("Applicant's letter on the 2012 Mesa del Sol Level B amendments, 2 October 2012", MDS,
   ("The applicant's letter to the City Planning Department explaining how the proposed 2012 amendments to the Mesa "
    "del Sol Level B community master plan meet the criteria, filed under project 1004075."),
   ("1,639,480 bytes. Opens: October 2, 2012, Ms. Catalina Lehner, City of Albuquerque Planning Department, Re: "
    "Project # 1004075/12EPC-40048 - Amendments to the Level B Community Master Plan."),
   AREAPLANS, [], "Written by the applicant, not by the City. Attribute it to the applicant."),
 'hv-213': ("Official Notification of Decision: Mesa del Sol Level A and B plans, 18 May 2023", MDS,
   ("The City's formal notice of the decision on the 2023 amendments to the Mesa del Sol Level A and Level B plans, "
    "issued to the applicant under project PR-2023-008498."),
   "297,259 bytes. Opens with the Planning Department Urban Design and Development Division letterhead, then OFFICIAL NOTIFICATION OF DECISION, May 18, 2023, addressed to MDS Investments.",
   AREAPLANS, [], None),
 'hv-214': ("Amended Official Notification of Decision: Mesa del Sol 2023 amendments, 21 September 2023", MDS,
   ("The amended notice of decision on the 2023 Mesa del Sol plan amendments, superseding the May 2023 notice "
    "issued under the same project number."),
   ("321,513 bytes. Opens: *AMENDED* OFFICIAL NOTIFICATION OF DECISION, September 21, 2023, under the same project "
    "PR-2023-008498 as the May notice."),
   AREAPLANS, [],
   "Marked AMENDED on its own face and issued under the same project number as the 18 May 2023 notice. Keep both and record which is later."),
 'hv-215': ("Official Notification of Decision: Mesa del Sol Level B, 19 August 2021", MDS,
   ("The City's formal notice of the Environmental Planning Commission and Development Review Board decision on the "
    "2021 Mesa del Sol Level B plan amendment, project PR-2021-005684."),
   "345,977 bytes. Opens with the Planning Department letterhead, then OFFICIAL NOTIFICATION OF DECISION, August 19, 2021, Mesa Del Sol.",
   AREAPLANS, [], None),
 'hv-216': ("Official Notification of Decision: Mesa del Sol Level A and Level B, 17 November 2022", MDS,
   ("The City's formal notice of the decision on the 2022 amendments to both the Level A and Level B Mesa del Sol "
    "plans, issued under project PR-2022-007805."),
   "348,681 bytes. Opens with the Planning Department letterhead, then OFFICIAL NOTIFICATION OF DECISION, November 17, 2022.",
   AREAPLANS, [], None),
 'hv-219': ("Mesa del Sol Level A Development Agreement", MDS,
   ("The development agreement between the City and the Mesa del Sol developer that accompanies the Level A "
    "community master plan, setting out the obligations each side took on."),
   ("1,975,356 bytes. Opens: Level A Development Agreement, LEVEL A DEVELOPMENT AGREEMENT, TABLE OF CONTENTS, 1 "
    "Background Information, 2 Authorization. Filed with the 2006 resolutions."),
   AREAPLANS, [{"page": PROJECTS, "reason": "An agreement governing a named development."}], None),
 'hv-220': ("Council Bill F/S R-05-4: adopting the Mesa del Sol Level A Community Master Plan", MDS,
   ("The Council resolution adopting the Level A community master plan for Mesa del Sol and approving the "
    "development agreement with the developer, sponsored by Isaac Benton."),
   ("73,902 bytes. Opens: CITY of ALBUQUERQUE SEVENTEENTH COUNCIL, COUNCIL BILL NO. F/S R-05-4, ENACTMENT NO. "
    "blank, SPONSORED BY: ISAAC BENTON, RESOLUTION ADOPTING THE LEVEL A COMMUNITY MASTER PLAN FOR MESA DEL SOL."),
   AREAPLANS, [{"page": ABOUT, "reason": "A Council resolution."}],
   ("The enactment number is blank on this copy, so it is the bill as introduced rather than the enacted "
    "instrument. Later resolutions in this set record the enactment as R-2006-005.")),
 'hv-222': ("Council Bill C/S R-12-118: amending the Mesa del Sol Level A plan and development agreement", MDS,
   ("The Council resolution amending the Level A community master plan and the Level A development agreement, and "
    "releasing Tract 8 from land use entitlements on its sale to the Pueblo of Isleta."),
   ("79,394 bytes. Opens: TWENTIETH COUNCIL, COUNCIL BILL NO. C/S R-12-118, ENACTMENT NO. blank, SPONSORED BY: Rey "
    "Garduno."),
   AREAPLANS, [{"page": ABOUT, "reason": "A Council resolution."}],
   "The bill as introduced; the enactment number is blank here and is R-2012-107 on the enacted copy."),
 'hv-221': ("Mesa del Sol Level A amendment, Enactment No. R-2012-107", MDS,
   ("The enacted Council resolution amending the Mesa del Sol Level A master plan and development agreement and "
    "releasing Tract 8 from land use entitlements on its sale to the Pueblo of Isleta."),
   ("111,018 bytes, " + RENDERED + ". Its face reads COUNCIL BILL NO. C/S R-12-118, ENACTMENT NO. R-2012-107 "
    "written by hand, sponsored by Rey Garduno, and the resolution text names Forest City Covington NM, LLC and "
    "the Pueblo of Isleta."),
   AREAPLANS, [{"page": ABOUT, "reason": "An enacted Council resolution."}],
   "The enacted copy of hv-222. The enactment number exists only in the handwriting on this copy."),
 'hv-225': ("Council Bill R-23-98: designating a 500-acre Mesa del Sol employment centre site", MDS,
   ("The Council resolution amending the Mesa del Sol Level A community master plan to designate an approximately "
    "500-acre site as a portion of the employment centre."),
   ("717,883 bytes. Opens: TWENTY-FIFTH COUNCIL, COUNCIL BILL NO. R-23-98, ENACTMENT NO. blank, SPONSORED BY: Pat "
    "Davis by request."),
   AREAPLANS, [{"page": ABOUT, "reason": "A Council resolution."}], "The bill as introduced; the enacted copy carries Enactment R-2023-014."),
 'hv-226': ("Mesa del Sol employment centre designation, Enactment No. R-2023-014", MDS,
   ("The enacted resolution designating roughly 500 acres of Mesa del Sol as part of the employment centre, "
    "recording the Environmental Planning Commission's recommendation of approval behind it."),
   ("64,748 bytes, " + RENDERED + ". Its face reads COUNCIL BILL NO. R-23-98, ENACTMENT NO. R-2023-014 written by "
    "hand, and its recitals record that the EPC heard the case at its November 17, 2022 hearing and voted to "
    "forward a recommendation of approval."),
   AREAPLANS, [{"page": ABOUT, "reason": "An enacted Council resolution."}], None),
 'hv-223': ("Council Bill R-23-158: raising the Mesa del Sol urban centre height limit", MDS,
   ("The Council resolution amending the Mesa del Sol Level A framework plan to raise the maximum building height "
    "in the 92-acre urban centre from 60 feet to 80 feet, and to 128 feet with height bonuses."),
   ("170,328,730 bytes, by far the largest file in this lane and the second largest in the whole harvest, which is "
    "the bill plus its attachments. Opens: TWENTY FIFTH COUNCIL, COUNCIL BILL NO. R-23-158, SPONSORED BY: Pat "
    "Davis, by request."),
   AREAPLANS, [{"page": ZONING, "reason": "It changes a height limit the code enforces."}],
   "The bill package as introduced, at 170 MB. The two-page enacted copy is a separate record."),
 'hv-224': ("Mesa del Sol urban centre height amendment, Enactment No. R-2023-067", MDS,
   ("The enacted resolution raising the allowable maximum building height in the 92-acre Mesa del Sol urban centre "
    "from 60 feet to 80 feet and up to 128 feet with applicable height bonuses."),
   ("76,526 bytes, " + RENDERED + ". Its face reads COUNCIL BILL NO. R-23-158, ENACTMENT NO. R-2023-067 written by "
    "hand, and its recitals record the Level A plan as adopted in January 2006 under Enactment R-2006-005."),
   AREAPLANS, [{"page": ZONING, "reason": "It changes a height limit the code enforces."}],
   "Two pages against the bill package's 170 MB. The enactment number exists only on this copy."),
 'hv-227': ("Council Bill R-23-196: further Mesa del Sol height and land use amendment", MDS,
   ("The Council resolution amending the Mesa del Sol Level A framework plan to raise the maximum building height "
    "from 80 feet to 110 feet and to allow NR-GM land uses on specific employment centre properties case by case."),
   ("39,172,700 bytes, the bill with its attachments. Opens: TWENTY FIFTH COUNCIL, COUNCIL BILL NO. R-23-196, "
    "SPONSORED BY: Pat Davis, by request."),
   AREAPLANS, [{"page": ZONING, "reason": "It changes a height limit the code enforces."}], None),
 'hv-228': ("Mesa del Sol height and land use amendment, Enactment No. R-2024-001", MDS,
   ("The enacted resolution raising the Mesa del Sol maximum building height from 80 feet to 110 feet and allowing "
    "NR-GM land uses on specific employment centre properties as approved case by case."),
   ("9,146,498 bytes, " + RENDERED + ". Its face reads COUNCIL BILL NO. R-23-196, ENACTMENT NO. R-2024-001 written "
    "by hand - and SPONSORED BY: Renee Grout, by request, where the introduced bill reads Pat Davis. See "
    "the_sponsor_that_changed."),
   AREAPLANS, [{"page": ABOUT, "reason": "An enacted Council resolution."}],
   "Its sponsor differs from the introduced bill's. Do not treat the enacted copy as a mere duplicate of the bill."),
 # ---- master development plans -------------------------------------------
 'hv-229': ("Master Development Plan for Alameda Business Park, revised July 1999", MDP,
   ("The approved master development plan for Alameda Business Park off Alameda Boulevard, laying out fifty-nine "
    "lots between the North Diversion Channel and Edith Boulevard with their setbacks and design criteria."),
   ("21,556,898 bytes, six pages, " + RENDERED + ". Sheet 1 of 2 is titled MASTER DEVELOPMENT PLAN FOR ALAMEDA "
    "BUSINESS PARK, ALBUQUERQUE, NEW MEXICO, REVISED MARCH 3, 1999, REVISED JULY 2, 1999, prepared by "
    "Bohannan-Huston under DRB 98-723, and carries City department approval signatures dated 1999."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-230': ("Site Development Plan for Subdivision: Albuquerque West Unit II, 2006", MDP,
   ("The approved site development plan for the Albuquerque West Unit II subdivision, a 9.2-acre site off Paseo del "
    "Norte, setting its lots, access, setbacks and permitted uses."),
   ("19,425,324 bytes, 23 pages, " + RENDERED + ". Its title block reads SITE DEVELOPMENT PLAN FOR SUBDIVISION, "
    "ALBUQUERQUE WEST UNIT II, project 1003272, application 06DRB-00941, with DRB signoff dated 26 July 2006."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   ("Filed under MasterDevelopmentPlans and named AlbuquerqueWestMP.pdf, but its own title block says Site "
    "Development Plan for Subdivision. Title it from the document.")),
 'hv-231': ("Atrisco Business Park Master Development Plan: major amendment for sites over 40 acres", MDP,
   ("The major amendment to the Atrisco Business Park master development plan, setting landscape, signage, "
    "lighting, architectural and utility standards for complexes larger than forty acres."),
   ("24,726,484 bytes, 14 pages, " + RENDERED + ". Titled ATRISCO BUSINESS PARK MASTER DEVELOPMENT PLAN AMENDMENT, "
    "DEVELOPMENT STANDARDS FOR COMPLEXES LARGER THAN 40 ACRES, project 2018-001361."),
   AREAPLANS, [{"page": DEVPROC, "reason": "Standards a development must meet."}],
   ("Its own sheet gives two different EPC approval dates: a handwritten stamp reading September 13, 2018 signed "
    "01 Apr 2019, and a printed block reading EPC APPROVAL - SEPTEMBER 13, 2019. The filename says 2018. Resolve "
    "the year before publishing it.")),
 'hv-232': ("Master Development Plan: Clifford West Business Park, 1997", MDP,
   ("The master development plan for Clifford West Business Park on Unser Boulevard NW, carrying its design "
    "guidelines, site plan and the administrative amendments made to it through 2005."),
   ("6,111,136 bytes, one large sheet, " + RENDERED + ". Titled MASTER DEVELOPMENT PLAN, CLIFFORD WEST BUSINESS "
    "PARK, UNSER BOULEVARD NW, sheet A dated 31 JUL 97, case number Z-97-11, by SLNB Architects, with later DRB "
    "administrative amendments stamped on its face."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-233': ("Site Plan for Subdivision: Fountain Hills Plaza, 2007", MDP,
   ("The approved site plan for the Fountain Hills Plaza subdivision at Paseo del Norte and Eagle Ranch Road, with "
    "its land use summary, tract heights and allowable uses."),
   ("54,013,976 bytes, 28 pages, " + RENDERED + ". Its title block reads Site Plan for Subdivision, Prepared for: "
    "Fountain Hills Plaza, LLC, project 1003445, application 07DRB-70053, with DRB signoff dated June 2007."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   "Named FountainHillsMP.pdf but titled Site Plan for Subdivision on its own sheet."),
 'hv-234': ("Site Plan for Subdivision: Gateway Industrial Park, 2000", MDP,
   ("The approved site plan for Gateway Industrial Park at Broadway and Menaul, dividing the tract into thirteen "
    "lots and carrying the Environmental Planning Commission's conditions of approval and design guidelines."),
   ("11,898,052 bytes, three pages, " + RENDERED + ". Its title block reads GATEWAY INDUSTRIAL PARK, SITE PLAN FOR "
    "SUBDIVISION, project 1000195, case Z-98-116, by Mark Goodwin & Associates, with City approvals dated March to "
    "June 2000."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-235': ("Journal Center 2: Land Development Design Guidelines, revised December 2003", MDP,
   ("The land development design guidelines for Journal Center 2, a supplement to the covenants, sign code, project "
    "standards and park development standards that govern the Journal Center."),
   ("12,895,452 bytes. Opens: JOURNAL CENTER 2, Land Development Design Guidelines, Revised December 2003, A "
    "Supplemental Document to the Covenants, Sign Code, Project Standards, Park Development Standards of the "
    "JOURNAL CENTER, prepared by Sites Southwest and Dekker/Perich."),
   AREAPLANS, [{"page": DEVPROC, "reason": "Design standards a development must meet."}], None),
 'hv-236': ("Journal Center: Park Development Standards", MDP,
   ("The park development standards issued by the Journal Center Corporation for the Journal Center, one of the "
    "four supplementary documents the Journal Center 2 design guidelines are written against."),
   ("3,594,296 bytes, 43 pages, " + RENDERED + ". Its cover reads Park Development Standards over the Journal "
    "Center Corporation mark."),
   AREAPLANS, [{"page": DEVPROC, "reason": "Standards a development must meet."}],
   "Issued by a private corporation and published by the City. Attribute it to Journal Center Corporation."),
 'hv-237': ("Journal Center: Project Standards", MDP,
   ("The project standards issued by the Journal Center Corporation for the Journal Center, the companion document "
    "to its park development standards."),
   ("1,375,643 bytes, 16 pages, " + RENDERED + ". Its cover reads Project Standards over the Journal Center "
    "Corporation mark, in the same series as the park development standards."),
   AREAPLANS, [{"page": DEVPROC, "reason": "Standards a development must meet."}],
   "Issued by a private corporation and published by the City. Attribute it to Journal Center Corporation."),
 'hv-238': ("Site Plan for Subdivision: Ladera Business Park, 2003", MDP,
   ("The approved site plan for Ladera Business Park, a 116.6-acre light industrial site off Unser Boulevard "
    "divided into twenty-nine tracts, with its off-site traffic improvement cost shares."),
   ("14,991,045 bytes, three pages, " + RENDERED + ". Its title block reads LADERA BUSINESS PARK, SITE PLAN FOR "
    "SUBDIVISION, project 1001523, application 03-01458, by Mark Goodwin & Associates, approvals October 2003 to "
    "January 2004."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   "Named LaderaIndustrialParkMP.pdf; the sheet itself says Ladera Business Park."),
 'hv-239': ("Site Plan for Subdivision: Las Lomitas Industrial Park, Vista del Norte, 2004", MDP,
   ("The approved site plan for tracts 1 through 19 of Las Lomitas Industrial Park within Vista del Norte, a "
    "thirty-acre site inside the Elena Gallegos Grant."),
   ("13,186,000 bytes, three pages, " + RENDERED + ". Its title block reads SITE PLAN FOR SUBDIVISION, TRACTS 1 "
    "THRU 19, VISTA DEL NORTE, JUNE 2004, project 1002184, application 04DRB-01804, with EPC approval of July 15, "
    "2004 and City approvals of February 2005."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-240': ("Site Plan for Subdivision and IP Master Development Plan: Luecking Park Office Complex, 2004", MDP,
   ("The approved plan for the Luecking Park Office Complex, a 6.7-acre industrial-park-zoned site between "
    "Pathway Avenue and the North Diversion Channel, with its height, setback and landscape standards."),
   ("8,434,578 bytes, two pages, " + RENDERED + ". Its title block reads SITE PLAN FOR SUBDIVISION / IP MASTER "
    "DEVELOPMENT PLAN, LUECKING PARK OFFICE COMPLEX, project 1000162, dated January 27, 2004, with DRB approvals "
    "of February 2004."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-241': ("NZ Commercial-Office Center: proposed development plan, 1986", MDP,
   ("The development plan for the NZ Commercial-Office Center, an 18-acre thirteen-lot site off University "
    "Boulevard SE, with its street section, jogging path and landscape treatment."),
   ("5,162,368 bytes, two pages, " + RENDERED + ". Titled NZ COMMERCIAL-OFFICE CENTER, PROPOSED DEVELOPMENT PLAN, "
    "TOTAL AREA = 18.01 Ac., file no. Z-75-131 and DRB 86-155, prepared by Andrews, Asbury & Robert Inc., with a "
    "planning director signature dated 10/14/86."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-242': ("Site Plan for Subdivision: North Gateway Industrial Park, March 2007", MDP,
   ("The approved site plan for tracts B-1, C-1-A, C-2-A and C-2-B of North Gateway Industrial Park off Balloon "
    "Fiesta Parkway, covering 22.79 acres inside the Elena Gallegos Grant."),
   ("22,569,277 bytes, six pages, " + RENDERED + ". Its title block reads SITE PLAN FOR SUBDIVISION, NORTH GATEWAY "
    "INDUSTRIAL PARK, March 2007, project 1003790, application 07DRB-00297, with City approvals of April 2007."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-243': ("Ordinance O-2016-019: amended site development plan for the former Indian School property", MDP,
   ("The enacted ordinance approving an amended site development plan for roughly 47 acres on 12th Street NW "
    "between Indian School Road and Menaul Boulevard, and adopting updated design standards and authorized uses "
    "for its commercial and office tracts."),
   ("445,894 bytes, eight pages, " + RENDERED + ". Its face reads COUNCIL BILL NO. C/S O-16-22, ENACTMENT NO. "
    "O-2016-019 written by hand, sponsored by Isaac Benton by request, repealing F/S O-05-98 and naming Indian "
    "Pueblos Marketing, Inc. as successor to the Indian Pueblos Federal Development Corporation."),
   AREAPLANS, [{"page": ZONING, "reason": "It adopts design standards and authorized uses."},
                {"page": ABOUT, "reason": "An enacted ordinance."}], None),
 'hv-244': ("Development design guidelines for the Indian Pueblos Marketing site, Exhibit B-1 to O-16-22", MDP,
   ("The design guidelines exhibit to the 2016 ordinance, supplementing the development design standards for the "
    "former Albuquerque Indian School property on 12th Street NW."),
   ("11,190,288 bytes. Opens: Exhibit B-1. Development Design Guidelines for IPMI, A. General Intent and Goals, "
    "stating that the guidelines supplement the Development Design Standards in Exhibits B-2 and B-3."),
   AREAPLANS, [{"page": ZONING, "reason": "Design standards applications are judged against."}],
   "An exhibit to hv-243. Keep the ordinance and its exhibit together."),
 'hv-245': ("Paradise Hills: a revised master plan, 1963 revised 1985", MDP,
   ("The revised master plan for Paradise Hills within the Alameda Grant, showing the annexation boundary, the "
    "established and developing urban areas and the special-use zoning across the north-west mesa."),
   ("4,959,015 bytes, one blueprint sheet, " + RENDERED + ". Titled PARADISE HILLS, A REVISED MASTER PLAN, ALAMEDA "
    "GRANT, BERNALILLO COUNTY, NEW MEXICO, by Leverton-Denney Engineers, MAY 1963, revised November 1968, November "
    "1974 and 7-8-85, approved by the Albuquerque EPC on 16 January 1975 and the Bernalillo County Commission on "
    "18 February 1975."),
   AREAPLANS, [{"page": PROJECTS, "reason": "A historic plan for a named part of the city."}],
   "The oldest document in this lane, and a joint City and County approval. Date it 1963 with its revisions, not 1985."),
 'hv-246': ("Site Plan for Subdivision and Building Permit: Golf Course Road and Paseo del Norte", MDP,
   ("The approved site plan for the retail development at Golf Course Road and Paseo del Norte, covering the major "
    "retail building and seven pads with their parking, landscape and architectural requirements."),
   ("33,017,961 bytes, three pages, " + RENDERED + ". Its title block reads SITE PLAN FOR SUBDIVISION AND BUILDING "
    "PERMIT, job title GOLF COURSE & PASEO, project manager George Rainhart AIA, DRB case 1097-245, plot date "
    "12/30/94 with updates to 1995 and signatures of October 1997."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   "Named PaseoGolfCourseMP.pdf; the sheet says Site Plan for Subdivision and Building Permit."),
 'hv-247': ("Renaissance: master declaration and rules and regulations", MDP,
   ("The master declaration of covenants and the rules and regulations for the Renaissance development, the private "
    "instrument that binds its lots, published by the City among its master development plans."),
   ("3,877,661 bytes, 92 pages, " + RENDERED + ". Its cover reads PLEASE RETURN TO BOARD SECRETARY above the "
    "Renaissance mark, A master plan for the New Southwest, Master Declaration and Rules and Regulations."),
   AREAPLANS, [{"page": PROJECTS, "reason": "A named development."}],
   ("A private covenant document, not a City instrument, and its cover is stamped PLEASE RETURN TO BOARD "
    "SECRETARY. Attribute it accordingly.")),
 'hv-248': ("Notification of Decision: Richfield Park Subdivision site development plan, 16 May 1986", MDP,
   ("The City's notice that the Environmental Planning Commission approved the site development plan for the "
    "83-acre Richfield Park Subdivision north of Alameda Boulevard, with its findings, conditions and design "
    "criteria."),
   ("5,678,118 bytes, eight pages, " + RENDERED + ". Dated May 16, 1986, file Z-85-70-1, for Lots A-1, B and C, "
    "Richfield Park Subdivision, recording that the EPC voted to approve on May 15, 1986."),
   AREAPLANS, [{"page": DEVPROC, "reason": "A decision applications are judged against."}], None),
 'hv-249': ("Sandia Science and Technology Park Master Development Plan: satellite antenna text amendments", MDP,
   ("The Sandia Science and Technology Park master development plan approved in June 2001, in the clean version "
    "carrying the text amendments on satellite antenna facilities and the notice of decision that approved them."),
   ("29,132,222 bytes. Opens: Master Development Plan Approved June, 2001, SANDIA SCIENCE & TECHNOLOGY PARK, "
    "Project #1001031, Sandia Science & Technology Park (SSTP) Text Amendments regarding Satellite Antenna "
    "Facilities (SAFs), Clean Version with Official Notice of Decision."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}], None),
 'hv-250': ("Site Development Plan amendment: Volcano Business Park Phase II, October 1997", MDP,
   ("The amended site development plan for lots 11 and 12A and five tracts of Volcano Business Park Phase II, "
    "reconfiguring the size, shape and number of tracts to be built in that phase."),
   ("13,577,577 bytes, four pages, " + RENDERED + ". Its title block reads SITE DEVELOPMENT PLAN FOR SP AMENDMENT, "
    "VOLCANO BUSINESS PARK PHASE II, OCTOBER 1997, DRB case 97-450, by Precision Surveys, with City approvals of "
    "early 1998 and a county recording stamp of 04/03/1998."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   "The same file is served at www.cabq.gov/planning/documents; harvested-city-documents-research-2026-09-14.json deferred that copy to this lane."),
 'hv-251': ("Site Plan for Subdivision: Volcano Point, 98th Street and Central Avenue, 2006", MDP,
   ("The approved site plan for the retail development at the north-west corner of 98th Street and Central Avenue, "
    "covering four lots with their building areas, parking and architectural design standards."),
   ("10,586,959 bytes, two pages, " + RENDERED + ". Its title block reads SITE PLAN FOR SUBDIVISION, project title "
    "NORTHWEST CORNER OF 98TH ST. & CENTRAL AVENUE, project 1003794, application 07DRB-00181, by George Rainhart "
    "Architect and Associates, sheet AS1 dated 11-1-2006, with approvals of 2007."),
   AREAPLANS, [{"page": DEVPROC, "reason": "An approved plan applications are judged against."}],
   "The same file is served at www.cabq.gov/planning/documents; that copy was deferred to this lane."),
 # ---- small wireless -----------------------------------------------------
 'hv-269': ("Standards and Regulations for Small Wireless Facilities in the Public Right-of-Way, March 2019", SWF,
   ("The City's published standards for small wireless facilities in the public right of way, setting what a "
    "carrier may install on City poles and in City streets and how it must look."),
   ("7,076,625 bytes. Opens: STANDARDS AND REGULATIONS FOR SMALL WIRELESS FACILITIES IN THE PUBLIC RIGHT-OF WAY, "
    "CITY OF ALBUQUERQUE, NEW MEXICO, Published by: The City of Albuquerque Planning Department, March 2019."),
   ZONING, [{"page": DEVPROC, "reason": "Standards an installation must meet."}], None),
 'hv-253': ("Small cells right-of-way ordinance, Enactment No. O-2018-026", SWF,
   ("The enacted ordinance governing small cell wireless facilities in the public right of way, transmitted with "
    "the City Clerk's certificate recording how it came into effect."),
   ("1,253,800 bytes, 17 pages, " + RENDERED + ". Page 1 is a City Clerk interoffice memorandum of December 4, "
    "2018 certifying BILL NO. F/S O-18-27, ENACTMENT NO. O-2018-026, passed at the November 5, 2018 Council "
    "meeting. See the_ordinance_that_became_law_unsigned."),
   ZONING, [{"page": ABOUT, "reason": "An enacted ordinance."}], None),
 'hv-254': ("Small cell street light and utility pole programme permit and agreement, 2025", SWF,
   ("The City's permit and agreement form for attaching small cell equipment to City street light and utility "
    "poles, the instrument a carrier signs before installing."),
   ("456,536 bytes. Opens: City of Albuquerque, Small Cell Street Light/Utility Pole Program, Planning Dept., "
    "Permit and Agreement, Date Received."),
   DEVPROC, [{"page": ZONING, "reason": "It implements the small wireless standards."}], None),
 # ---- development review -------------------------------------------------
 'hv-203': ("Design Review Committee submittal requirements: privately funded developer projects, July 2026", DRV,
   ("The City's submittal requirements for privately funded developer projects going to the Design Review "
    "Committee, the checklist of what a plan set must contain before review."),
   ("177,854 bytes. Its extracted text is enciphered by a display font and decodes on a uniform 29-character shift "
    "to PrivatelyFundedDeveloperProjects, DesignReviewCommitteeDRC SubmittalRequirements, EffectiveDate July. See "
    "a_second_font_shift."),
   DEVPROC, [], None),
 'hv-204': ("Design Review Committee submittal requirements: capital and other publicly funded projects, July 2026",
   DRV,
   ("The City's submittal requirements for capital improvement and other publicly funded projects going to the "
    "Design Review Committee, the companion sheet to the privately funded requirements."),
   ("198,486 bytes. Its readable text opens CIP and other Publicly Funded Projects; the rest is the same "
    "29-character display-font shift, decoding to DesignReviewCommitteeDRC SubmittalRequirements, EffectiveDate."),
   DEVPROC, [], None),
 'hv-205': ("Stormwater control permit for erosion and sediment control, 2017", DRV,
   ("The City's permit form for erosion and sediment control on a construction site, the stormwater instrument a "
    "project must hold before disturbing ground."),
   ("45,780 bytes. Opens: City of Albuquerque Planning Department, Stormwater Control Permit for Erosion and "
    "Sediment Control, Project Title."),
   DEVPROC, [{"page": STORM, "reason": "A stormwater control instrument."}], None),
 'hv-206': ("Typical components of Design Review Committee construction plan sets", DRV,
   ("The City's checklist of the sheets a private development project's construction plan set must contain for "
    "Design Review Committee review, from the cover sheet through the erosion and sediment control plan."),
   ("14,755 bytes, a Word document. Opens: Typical Components of DRC Construction-Plan Sets (For Private "
    "Development Projects), Cover Sheet with Index to Sheets, General Notes, Final Plat, Approved Grading & "
    "Drainage Plan."),
   DEVPROC, [], None),
 'hv-207': ("Design Review Committee milestone submittal checklist", DRV,
   ("The City's milestone-by-milestone checklist of what a design must show at each study phase through final "
    "submittal, covering survey control, intersection and driveway details and right-of-way sheets."),
   ("40,713 bytes, a spreadsheet. Its shared strings include Study Phase, 100% - FINAL, General Notes, Survey and "
    "Control Points, Intersection Details, Driveway Details, ROW Details."),
   DEVPROC, [], "A workbook, not a document; its container was read from the OOXML archive's xl/ parts."),
 'hv-208': ("Work order close-out submittal requirements, October 2020", DRV,
   ("The City's submittal requirements for closing out a construction work order, including the contractor's "
    "acknowledgement that the work is complete."),
   ("118,367 bytes. Opens: City of Albuquerque Construction Management, Planning Department, Submittal "
    "Requirements for Work Order Close Out, CONTRACTOR ACKNOWLEDGEMENT."),
   DEVPROC, [], None),
 'hv-252': ("Site plan checklist", DRV,
   ("The City's checklist used to verify that a submitted site plan is complete, listing what must be shown before "
    "the plan will be accepted for review."),
   ("420,592 bytes. Opens: SITE PLAN CHECKLIST, Project #, Case #, This checklist will be used to verify the "
    "completeness of site plans submitted."),
   DEVPROC, [], None),
 'hv-255': ("Traffic scoping form, revised July 2020", DRV,
   ("The City's form for scoping the traffic study a development application must produce, completed with the "
    "Development Review Services Division before the study is written."),
   ("247,306 bytes. Opens: City of Albuquerque Planning Department, Development Review Services Division, Traffic "
    "Scoping Form (REV 07/2020)."),
   DEVPROC, [{"page": 'content/transportation/safety-crash-data.md', "reason": "It scopes traffic analysis."}], None),
 'hv-256': ("Development Facilitation Team sign posting agreement", DRV,
   ("The agreement an applicant signs undertaking to post public notice signs for a development application, the "
    "public notice requirement every application must meet."),
   ("137,349 bytes. Opens: DFT SIGN POSTING AGREEMENT - A PUBLIC NOTICE REQUIREMENT, All development applications "
    "are required to complete public notice."),
   DEVPROC, [], None),
 'hv-257': ("Form PLT: pre-approvals and signatures, revised December 2025", DRV,
   ("The Development Hearing Officer's form recording the pre-approvals and signatures a plat application must "
    "collect from each City department before the hearing officer will take it at a public meeting."),
   ("167,444 bytes. Opens: FORM PLT: PRE-APPROVALS/SIGNATURES (Revised 12/2025), Please refer to the DHO public "
    "meeting schedule for meeting dates."),
   DEVPROC, [], None),
 'hv-258': ("Rules of Procedure for the Development Review Board, revised June 2022", DRV,
   ("The procedural rules the Development Review Board runs by, adopted in 1982 and revised in 2003 and again in "
    "June 2022."),
   ("571,707 bytes. Opens with a DocuSign envelope identifier, then CITY OF ALBUQUERQUE, NEW MEXICO, RULES OF "
    "PROCEDURE for the DEVELOPMENT REVIEW BOARD, Adopted March, 1982, Revised July 2003, Revised June 2022."),
   DEVPROC, [{"page": ABOUT, "reason": "The rules of a City board."}], None),
 'hv-259': ("Albuquerque Archaeological Ordinance compliance documentation form", DRV,
   ("The City's blank form for documenting compliance with the Albuquerque Archaeological Ordinance, completed by "
    "an applicant's agent as part of development review."),
   ("1,056,533 bytes. Opens with the Planning Department letterhead naming the director and mayor, then "
    "Albuquerque Archaeological Ordinance - Compliance Documentation, Case Number(s), Agent, Applicant."),
   DEVPROC, [{"page": ZONING, "reason": "A requirement of the code."}], None),
 'hv-260': ("Development Review Board transition meeting: site plan administrative process changes, December 2022",
   DRV,
   ("The Planning Department's briefing on how site plan administration changed under the 2021 Integrated "
    "Development Ordinance amendment cycle, presented at the Development Review Board transition meeting."),
   ("459,842 bytes. Opens: City of Albuquerque Planning Department, DRB Transition Meeting, December 9th, 2022, "
    "2021 IDO Amendment Cycle."),
   DEVPROC, [{"page": ZONING, "reason": "It explains a change to how the code is administered."}], None),
 'hv-261': ("2022 schedule for Development Review Board major cases", DRV,
   ("The published 2022 calendar of application deadlines, agenda posting dates and meeting dates for major cases "
    "before the Development Review Board, the schedule an applicant works backwards from."),
   ("172,798 bytes. Opens: 2022 Schedule for DRB Major Cases, Planning Department, Development Services Division, "
    "Application, Agenda Posted, DRB Meeting."),
   DEVPROC, [], "A past year's calendar. Keep it only if the archive holds scheduling records."),
 'hv-262': ("2022 schedule for Development Review Board minor cases", DRV,
   ("The published 2022 calendar of application, agenda posting and meeting dates for minor cases before the "
    "Development Review Board, the companion to the major case schedule."),
   ("172,942 bytes. Opens: 2022 Schedule for DRB Minor Cases, Planning Department, Development Services Division."),
   DEVPROC, [], "A past year's calendar. Keep it only if the archive holds scheduling records."),
 'hv-263': ("2023 draft schedule for Development Review Board major cases", DRV,
   ("The draft 2023 calendar of application deadlines, agenda posting dates and meeting dates for major cases "
    "before the Development Review Board, published while still marked as a draft."),
   ("148,160 bytes. Opens: 2023 Schedule for DRB Major Cases, Planning Department, Development Services Division. "
    "Its filename says draft."),
   DEVPROC, [], "Marked draft in its own filename, and a past year. Label it a draft schedule."),
 'hv-264': ("2023 draft schedule for Development Review Board minor cases", DRV,
   ("The draft 2023 calendar of application deadlines, agenda posting dates and meeting dates for minor cases "
    "before the Development Review Board, the companion to the major case draft."),
   ("147,177 bytes. Opens: 2023 Schedule for DRB Minor Cases, Planning Department, Development Services Division. "
    "Its filename says draft."),
   DEVPROC, [], "Marked draft in its own filename, and a past year. Label it a draft schedule."),
 'hv-265': ("Sensitive lands analysis form, updated November 2020", DRV,
   ("The City's form for analysing sensitive lands on a development site, the assessment the code requires before "
    "certain land may be developed."),
   ("211,249 bytes. Opens: City of Albuquerque - Planning Department, Updated 11/2/2020, 600 2nd St. NW, Suite 300."),
   DEVPROC, [{"page": ZONING, "reason": "A requirement of the code."}], None),
 'hv-266': ("Environmental Planning Commission Rules of Practice and Procedure, July 2025", DRV,
   ("The procedural rules the Environmental Planning Commission runs by, covering how it is authorised, how cases "
    "reach it and how it hears them, in the edition published with its July 2025 papers."),
   ("316,126 bytes. Opens: RULES OF PRACTICE AND PROCEDURE, ENVIRONMENTAL PLANNING COMMISSION (EPC), TABLE OF "
    "CONTENTS, ARTICLE I - RULES AND GUIDELINES."),
   DEVPROC, [{"page": ABOUT, "reason": "The rules of a City commission."}],
   "The later of two editions here; the 2021 edition is a separate record."),
 'hv-267': ("Environmental Planning Commission Rules of Practice and Procedure, effective 15 April 2021", DRV,
   ("The Environmental Planning Commission's procedural rules as they took effect in April 2021, the edition the "
    "July 2025 rules replace."),
   ("126,925 bytes. Opens: Environmental Planning Commission (EPC) RULES of PRACTICE and PROCEDURE, Effective Date: "
    "April 15, 2021, ARTICLE I - RULES and GUIDELINES, Section 1. Authorization for Rules."),
   DEVPROC, [{"page": ABOUT, "reason": "The rules of a City commission."}],
   "Superseded by the July 2025 edition also in this lane. Record the supersession rather than dropping either."),
 # ---- building safety ----------------------------------------------------
 'hv-198': ("Residential re-roof permit requirements and fee information", BSF,
   ("The City's guidance on the permit a homeowner needs to re-roof a house, what the requirements are and what it "
    "costs."),
   ("132,979 bytes. Opens: CITY OF ALBUQUERQUE, Planning Department, Building Safety, RESIDENTIAL RE-ROOF PERMIT, "
    "Requirements & Fee Information."),
   DEVPROC, [], None),
 'hv-199': ("Retaining walls, garden walls and fences: permit requirements, 2017", BSF,
   ("The City's guidance on permits for retaining walls over twenty-four inches and garden walls and fences over "
    "six feet, and what a plan must show."),
   ("108,339 bytes. Opens: CITY OF ALBUQUERQUE, Planning Department, Building Safety, RETAINING WALLS OVER TWENTY "
    "FOUR INCHES (24), GARDEN WALLS AND FENCES OVER."),
   DEVPROC, [], None),
 'hv-200': ("Tiny Home Guidelines, 2016", BSF,
   ("The City's guidance on tiny homes, setting out how Building Safety treats them and what a builder or owner "
    "must satisfy."),
   ("362,559 bytes, one page whose only extractable text is its title, so it was read by rendering: the sheet is "
    "headed Tiny Home Guidelines and its filename dates it to 2016."),
   DEVPROC, [], None),
 'hv-201': ("Covered patios, porches and carports: plans and permit information", BSF,
   ("The City's guidance on the plans and permits needed to build a covered patio, porch or carport, including how "
    "many sets of drawings to submit."),
   ("136,427 bytes. Opens: CITY OF ALBUQUERQUE, Planning Department, Building Safety, COVERED PATIOS, PORCHES AND "
    "CARPORTS, Plans & Permit Information, Submit two."),
   DEVPROC, [], None),
 'hv-202': ("Sample site plan", BSF,
   ("The City's worked example of a site plan, showing an applicant what must be indicated on the drawing when "
    "submitting for a building permit."),
   ("90,801 bytes. Opens: SAMPLE SITE PLAN, Curb line, The following items must be clearly indicated on the site "
    "plan when submitting drawings."),
   DEVPROC, [], None),
 # ---- business licensing -------------------------------------------------
 'hv-195': ("How to apply for a business licence through ABQ-PLAN", BIZ,
   ("The City's step-by-step guide to applying for a business licence through the ABQ-PLAN self-service portal, "
    "written for an applicant using the system for the first time."),
   ("1,561,434 bytes. Opens: ABQ-PLAN How to apply for a Business License, Website: "
    "cityofalbuquerquenm-energovweb.tylerhost.net/apps/selfservice."),
   DEVPROC, [], None),
 'hv-196': ("How to renew a business licence through ABQ-PLAN", BIZ,
   ("The City's step-by-step guide to renewing an existing business licence through the ABQ-PLAN self-service "
    "portal, the companion to the application guide."),
   ("580,996 bytes. Opens: ABQ-PLAN How to Renew a Business License, Website: "
    "cityofalbuquerquenm-energovweb.tylerhost.net/apps/selfservice."),
   DEVPROC, [], None),
 'hv-197': ("How to apply for a temporary business licence through ABQ-PLAN", BIZ,
   ("The City's step-by-step guide to applying for a temporary business licence through the ABQ-PLAN self-service "
    "portal, the third guide in the series."),
   ("691,679 bytes. Opens: ABQ-PLAN How to apply for Temporary Business License, Website: "
    "cityofalbuquerquenm-energovweb.tylerhost.net/apps/selfservice."),
   DEVPROC, [], None),
 # ---- treasury and historic ----------------------------------------------
 'hv-193': ("Commodity Cost Management Policy, 1 October 2013", TRY,
   ("The City's policy for using commodity cost management transactions to manage price risk, setting out who is "
    "responsible, what the objectives are and what guidelines apply."),
   ("54,422 bytes, a Word document read from its word/document.xml. Opens: The City of Albuquerque, New Mexico, "
    "COMMODITY COST MANAGEMENT POLICY, October 1, 2013."),
   BUDGET, [{"page": ABOUT, "reason": "A City financial policy."}],
   "Published under documents.cabq.gov/investor, the City's bond investor material."),
 'hv-194': ("Post Bond Issuance Compliance Policy, as of 1 January 2014", TRY,
   ("The City's policy for staying compliant after it issues bonds, prepared by the Treasury Division and covering "
    "issuance, bond counsel and the continuing obligations that follow."),
   ("103,372 bytes, a Word document read from its word/document.xml. Opens: CITY OF ALBUQUERQUE, NEW MEXICO, POST "
    "BOND ISSUANCE COMPLIANCE POLICY, As of January 1, 2014, Prepared by: Department of Finance & Administrative "
    "Services, Treasury Division."),
   BUDGET, [{"page": ABOUT, "reason": "A City financial policy."}],
   "Published under documents.cabq.gov/investor, the City's bond investor material."),
 'hv-268': ("Historic Protection Overlays: pros and cons", HIS,
   ("The City's plain summary of what a Historic Protection Overlay does for a neighbourhood and what it asks of "
    "owners, written for residents weighing whether to seek one."),
   ("157,557 bytes. Opens: PROS & CONS OF HPOS, HISTORIC PROTECTION OVERLAYS, PROS, CONS, The historic qualities "
    "of the, Exterior changes to pro."),
   ZONING, [{"page": DEVPROC, "reason": "An overlay changes how applications are reviewed."}], None),
}

add = []
for i in SLICE:
    assert i in D, i
    t, group, desc, ev, canon, cross, caution = D[i]
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i],
         "filename": urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1]),
         "harvested_from": SRC[i], "recommendation": "add to the inventory as a new candidate",
         "link_check": LC, "content_kind": container(i), "leading_bytes": MAGIC[i], "http_status": CODE[i],
         "title": t, "group": group, "description": desc, "evidence": ev,
         "description_word_count": len(desc.split()),
         "proposed_canonical_page": canon, "cross_listings": cross, **M[i]}
    p = pages(i)
    if p:
        r["page_count"] = p
    elif MAGIC[i] == '25504446':
        r["page_count_not_readable"] = ("The page tree is inside a compressed object stream, so the page count "
                                        "cannot be counted from the file structure the way it can for the others "
                                        "here. No page count is asserted.")
    if caution:
        r["caution"] = caution
    add.append(r)

bygroup = collections.Counter(r['group'] for r in add)
add_bytes = sum(r['size_bytes'] for r in add)
containers = collections.Counter(r['content_kind'] for r in add)
notext = [i for i in SLICE if MAGIC[i] == '25504446'
          and len(open(os.path.join(SP, 'txt', i + '.txt'), encoding='utf-8', errors='replace').read().strip()) < 40]

artifact = {
 "batch_id": "harvested-planning-documents-research-2026-09-14",
 "lane": "Claude research lane: the documents.cabq.gov planning files harvested from excluded pages",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": ("None of these files has an inventory id. Every row carries inventory_id: null, the field is "
                      "called recommendation rather than recommended_status, and the only value used is add to the "
                      "inventory as a new candidate."),
  "so_it_cannot_be_applied_the_usual_way": ("Update-Candidate.ps1 changes the status of an existing candidate and "
                                            "cannot act on any row here. These must be created as candidates first, "
                                            "after which the ordinary archival gate applies."),
 },
 "cluster": ("The second slice of the link harvest: everything served from documents.cabq.gov that City pages link "
             "to and the inventory does not hold."),
 "scope": "All %d documents.cabq.gov files in the harvest. Every one is recommended for addition; none collides with anything." % len(SLICE),
 "what_is_in_it": {
  "mesa_del_sol": ("20 files covering the 13,000-acre planned community end to end: the Level A community master "
                   "plan as amended, the Level B plan and its 143 MB technical appendices, the wireless "
                   "telecommunications appendix, six official notifications of decision from 2008 to 2023, the "
                   "Level A development agreement, and eight Council bills and enacted resolutions."),
  "master_development_plans": ("23 files, most of them signed large-format plan sheets for business and industrial "
                               "parks - Alameda, Atrisco, Clifford West, Fountain Hills, Gateway, Ladera, Las "
                               "Lomitas, Luecking, North Gateway, Paradise Hills, Renaissance, Richfield, Sandia "
                               "Science and Technology Park, Volcano Business Park and Volcano Point - plus the "
                               "Journal Center standards and the 2016 ordinance for the former Indian School "
                               "property."),
  "development_review": "20 files: the DRB and EPC rules of procedure, submittal requirements, checklists, forms and case schedules.",
  "building_safety": "5 homeowner permit guides, from re-roofing to tiny homes.",
  "the_rest": "3 ABQ-PLAN business licensing guides, 3 small wireless facility documents, 2 Treasury policies from the bond investor pages, and the historic protection overlay summary.",
 },
 "the_enactment_numbers_that_exist_only_in_handwriting": {
  "what": ("Five Council instruments here appear twice: the bill as introduced, with ENACTMENT NO. left blank, and "
           "an enacted copy with the number written on its face by hand."),
  "the_numbers_read_from_the_renders": {
   "R-23-158": "R-2023-067", "R-23-98": "R-2023-014", "R-23-196": "R-2024-001",
   "C/S R-12-118": "R-2012-107", "C/S O-16-22": "O-2016-019",
  },
  "why_it_matters": ("Every one of the enacted copies is a scan with no text layer. The enactment number, the "
                     "authoritative identifier of the law, is not extractable from any of them - it exists only as "
                     "handwriting in an image. A text-based pipeline would index these five documents without ever "
                     "recording what they enacted."),
  "keep_both_copies": ("The bill package carries the attachments - R-23-158 is 170,328,730 bytes - and the enacted "
                       "copy carries the number and the signature. Neither substitutes for the other."),
 },
 "the_sponsor_that_changed": {
  "what": ("R-23-196 was introduced SPONSORED BY: Pat Davis, by request. The enacted copy, Enactment R-2024-001, "
           "reads SPONSORED BY: Renee Grout, by request."),
  "how_it_was_established": ("The introduced bill has a text layer and the sponsor line was extracted from it. The "
                            "enacted copy has none and the sponsor was read from the render."),
  "why_it_is_recorded": ("It is the clearest possible argument against treating an enacted copy as a duplicate of "
                         "its bill. The two differ in who is recorded as sponsoring the law."),
 },
 "the_ordinance_that_became_law_unsigned": {
  "what": ("The small cells right-of-way ordinance, Enactment O-2018-026, is transmitted with a City Clerk "
           "memorandum of 4 December 2018 certifying that Bill No. F/S O-18-27 passed at the November 5, 2018 "
           "Council meeting, that the Mayor did not sign it within the ten days allowed and did not veto it, and "
           "that under City Charter Article XI, Section 3 it is therefore in full effect without the Mayor's "
           "approval or signature."),
  "why_it_is_worth_recording": ("The certificate is the only thing in the file that says how the ordinance became "
                                "law. Archive the ordinance without it and that fact is lost."),
 },
 "a_second_font_shift": {
  "what": ("Two current Design Review Committee submittal requirement sheets extract as gibberish: "
           "3ULYDWHO\\)XQGHG'HYHORSHU3URMHFWV."),
  "the_decode": ("A uniform shift of 29 character codes recovers PrivatelyFundedDeveloperProjects, "
                 "DesignReviewCommitteeDRC SubmittalRequirements, EffectiveDate July."),
  "why_it_matters": ("This run has now met two different display-font shifts - the MRCOG 2030 MTP elements were "
                     "shifted by one, these by twenty-nine. A search of extracted text would find neither, and "
                     "neither file is an image: the text is there, systematically wrong. Text that extracts as "
                     "gibberish is worth testing for a uniform offset before the file is called unreadable."),
 },
 "filenames_that_do_not_match_their_documents": {
  "the_pattern": ("The MasterDevelopmentPlans directory holds documents that mostly are not called master "
                  "development plans on their own sheets."),
  "examples": {
   "AlbuquerqueWestMP.pdf": "Site Development Plan for Subdivision, Albuquerque West Unit II",
   "FountainHillsMP.pdf": "Site Plan for Subdivision, prepared for Fountain Hills Plaza, LLC",
   "LaderaIndustrialParkMP.pdf": "Ladera Business Park, Site Plan for Subdivision",
   "PaseoGolfCourseMP.pdf": "Site Plan for Subdivision and Building Permit, Golf Course & Paseo",
   "RenaissanceMasterPlan.pdf": "Renaissance: master declaration and rules and regulations - a private covenant document, not a master plan",
  },
  "the_rule": ("Title every one of these from its own title block, not from its filename or its directory. Each row "
               "does, and each row that diverges says so."),
 },
 "what_it_took_to_read_them": {
  "files_with_no_extractable_text_at_all": len(notext),
  "and_no_text_on_any_page": ("Not merely on page 1. pdftotext over the first forty pages of each returns nothing: "
                              "they are wholly scanned - signed plan sheets, blueprints and photocopied "
                              "resolutions. All of them were rendered."),
  "the_oldest": ("Paradise Hills, a blueprint titled MAY 1963 and revised through 7-8-85, approved by the "
                 "Albuquerque EPC in January 1975 and the Bernalillo County Commission in February 1975."),
 },
 "method": ("Fetched and measured every file, verified each container by leading bytes and each OOXML file by its "
            "internal parts, tested every PDF for its end-of-file marker, counted pages from the file structure, "
            "extracted text from all of them, rendered every one that yielded none and read the renders, decoded "
            "the two shifted-font sheets, and swept every checksum against all checksummed inventory records and "
            "every row of every saved artifact, and every URL against every inventory URL."),
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
  "result": "Nothing in this lane is already in the inventory by either test.",
  "the_two_deferred_rows": ("harvested-city-documents-research-2026-09-14.json recorded two www.cabq.gov files as "
                            "do not add because the same bytes are served here: the Volcano Business Park and "
                            "Volcano Point plans. Both are decided in this lane, which is where that artifact said "
                            "they would be."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "bill_and_enacted_pairs": 5,
  "supersession_found": 1,
  "note": ("No two files here are byte-identical. Five Council instruments appear as an introduced bill and an "
           "enacted copy, which are different documents and both kept. The 2021 EPC rules of practice are "
           "superseded by the July 2025 edition, also in this lane."),
 },
 "integration_flags": [
  {"severity": "not-applicable-through-update-candidate",
   "affects": [r['local_ref'] for r in add],
   "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create them as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "identifier-only-in-an-image",
   "affects": ['hv-224', 'hv-226', 'hv-228', 'hv-221', 'hv-243'],
   "finding": ("Five enacted Council instruments carry their enactment number - R-2023-067, R-2023-014, "
               "R-2024-001, R-2012-107, O-2016-019 - only as handwriting on a scan with no text layer."),
   "recommended_action": "Record the enactment number as metadata on each record; it cannot be recovered by searching the file."},
  {"severity": "do-not-collapse",
   "affects": ['hv-227', 'hv-228'],
   "finding": "R-23-196 was introduced sponsored by Pat Davis and enacted under Renee Grout.",
   "recommended_action": "Keep the bill and the enacted copy as separate records. They differ in substance, not only in size."},
  {"severity": "governance-fact",
   "affects": ['hv-253'],
   "finding": ("The small cells right-of-way ordinance became law without the Mayor's signature: the Clerk's "
               "certificate records that he neither signed within ten days nor vetoed, so City Charter Article XI "
               "Section 3 applied."),
   "recommended_action": "Keep the certificate with the ordinance; it is the only record of how the ordinance took effect."},
  {"severity": "extraction",
   "affects": ['hv-203', 'hv-204'],
   "finding": "Two current design review submittal sheets extract as gibberish and decode on a uniform 29-character shift. This run has now met two different shifts.",
   "recommended_action": "Test gibberish extraction for a uniform offset before calling a file unreadable."},
  {"severity": "title-from-the-document",
   "affects": ['hv-230', 'hv-233', 'hv-238', 'hv-246', 'hv-247'],
   "finding": "Five files in the MasterDevelopmentPlans directory are not master development plans on their own title blocks; one is a private covenant document.",
   "recommended_action": "Title each from its title block. Every row does."},
  {"severity": "attribution",
   "affects": ['hv-236', 'hv-237', 'hv-247', 'hv-217'],
   "finding": "Four documents here were written by private parties - Journal Center Corporation, the Renaissance board, and the Mesa del Sol applicant - and are published by the City.",
   "recommended_action": "Attribute them to their authors."},
  {"severity": "date-conflict",
   "affects": ['hv-231', 'hv-211'],
   "finding": ("The Atrisco amendment sheet gives EPC approval as both September 13, 2018 and September 13, 2019 on "
               "the same page; the Mesa del Sol Level A cover misprints its amendment year as 20234."),
   "recommended_action": "Resolve the Atrisco year with the City before publishing; quote the Mesa del Sol cover as it stands and note the misprint."},
 ],
 "counts": {
  "reviewed": len(add),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": 0,
  "by_group": dict(bygroup),
  "containers": dict(containers),
 },
 "link_check": {"checked": len(add), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": ", ".join('%d %s' % (v, k) for k, v in sorted(containers.items()))},
 "add_to_inventory": add,
 "do_not_add": [],
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready, and none is a candidate yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint if all are added and archived: {add_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Each row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes, the container read "
                      "from the file, the page count where the file is a PDF, and harvested_from - the City page "
                      "whose links led to it. Every row carries inventory_id: null."),
 "what_remains_of_this_harvest": ("One lane: the 173 real property flyers from dmdgis.cabq.gov and the 36 files on "
                                  "third-party hosts."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('by_group', 'containers')}}))
