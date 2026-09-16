"""Claude research lane. Writes one dated decision artifact about documents that
are NOT inventory candidates: files earlier lanes of this run found on City
servers and reported as absent from master-inventory.json.

It never modifies master-inventory.json, checkpoint.json, r2-inventory.json,
site content, or R2. Nothing here can be applied through Update-Candidate,
because none of these files has an inventory id.

Dated 2026-09-14.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\undiscovered-documents-research-2026-09-14.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\und')

STORM = 'content/public-works/stormwater-drainage.md'
CLIMATE = 'content/city-data/climate-environment.md'
FACIL = 'content/public-works/city-facilities.md'
ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'
TRANSPO = 'content/transportation/_index.md'
ZONING = 'content/development-land-use/zoning-ido.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
DEVPROC = 'content/development-land-use/development-process.md'
MAPS = 'content/maps-data/maps.md'

inv = json.load(open(INV, encoding='utf-8'))

M, MAGIC, URL, CODE, GRP = {}, {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], GRP[p[0]], URL[p[0]], CODE[p[0]] = p[4], p[5], p[6], p[1]

SLICE = sorted(M)
REPORTED_IN = {}
for line in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    REPORTED_IN[p[0]] = p[3]

# Both sweep sets, plus every inventory URL: these are proposed ADDITIONS, so a
# collision with any inventory record at all matters, not only an archived one.
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
    return u.lower().replace('https://', '').replace('http://', '').rstrip('/')


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
    for b in ('approved_for_addition', 'duplicate', 'superseded', 'requires_human_review', 'excluded'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('checksum_sha256'):
                PRIOR_SHA.setdefault(r['checksum_sha256'], (os.path.basename(f), r['id'], r.get('recommended_status')))

SHA_HIT = {i: ALL_SHA[M[i]['checksum_sha256']] for i in SLICE if M[i]['checksum_sha256'] in ALL_SHA}
URL_HIT = {i: INV_URL[norm(URL[i])] for i in SLICE if norm(URL[i]) in INV_URL}
ART_HIT = {i: PRIOR_SHA[M[i]['checksum_sha256']] for i in SLICE
           if M[i]['checksum_sha256'] not in ALL_SHA and M[i]['checksum_sha256'] in PRIOR_SHA}
INTERNAL = collections.Counter(M[i]['checksum_sha256'] for i in SLICE)
assert not [k for k, v in INTERNAL.items() if v > 1], 'unexpected internal duplicate'

KIND = {'25504446': 'PDF', '3c21444f': 'HTML'}
LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes and "
      "the container verified by leading bytes. Every PDF was tested for its end-of-file marker.")

MS4 = [{"page": CLIMATE, "reason": "Water-quality monitoring data."}]
A14 = ("Part of the City's 2014 MS4 Annual Report package, submitted to EPA Region 6 under NPDES permit NMS000101 "
       "and certified on 30 March 2015 by the Chief Administrative Officer.")

D = {
 # ---- the annual reports -------------------------------------------------
 'und-004': ("MS4 Annual Report for fiscal year 2021", "annual reports",
   ("The City's stormwater annual report to the federal regulator for July 2020 to June 2021, filed on EPA's MS4 "
    "annual report form under permit NMR04A014 and covering the Middle Rio Grande impairments the City discharges "
    "to."),
   ("20,645,626 bytes, 382 pages. Page 1 has no text layer and was rendered: EPA's MS4 Annual Report Format naming "
    "NMR04A014 City of Albuquerque, reporting period Jul 1, 2020 to Jun 30, 2021, population served 546,000, and "
    "four Middle Rio Grande impairments (E-coli, temperature, PCBs, dissolved oxygen)."), STORM, MS4, None),
 'und-001': ("MS4 Annual Report for fiscal year 2021, draft", "annual reports",
   ("The draft of the City's fiscal 2021 stormwater annual report to the federal regulator, the same 382-page filing "
    "as the final version and published alongside it on the City's stormwater page."),
   ("20,780,456 bytes, 382 pages, no text layer on page 1. Rendered, its page 1 is a PNG byte-identical to the "
    "final report's page 1 - the same 450,584-byte image with the same SHA-256 - and the two files have the same "
    "page count, so the draft and the final are the same report, differing by 134,830 bytes later in the file."),
   STORM, MS4,
   "A draft edition superseded by und-004. Do not archive both as equals; archive the final and keep this only if the archive keeps drafts."),
 'und-002': ("MS4 Annual Report for fiscal year 2020", "annual reports",
   ("The City's stormwater annual report to the federal regulator for July 2019 to June 2020, filed under permit "
    "NMR04A014, the largest single annual filing in this set."),
   ("133,787,450 bytes. Its first six pages are imaged and carry no text; the text from page 7 on opens: Annual "
    "Report for City of Albuquerque, NMR04A014, Reporting Period: July 1, 2019 - June 30, 2020."), STORM, MS4,
   "Too large for the renderer; identified from its own text layer from page 7 on."),
 'und-003': ("MS4 Annual Report for fiscal year 2019", "annual reports",
   ("The City's stormwater annual report to the federal regulator for July 2018 to June 2019, filed under permit "
    "NMR04A014 against the NPDES permit effective December 2014."),
   ("122,657,409 bytes. Identified the same way as the fiscal 2020 report: its first six pages are imaged, and the "
    "text from page 7 on reads Reporting Period: July 1, 2018 - June 30, 2019."), STORM, MS4,
   "Too large for the renderer; identified from its own text layer from page 7 on."),
 'und-035': ("MS4 Annual Report for fiscal year 2017", "annual reports",
   ("The City's stormwater annual report to the federal regulator for July 2016 to June 2017, filed under permit "
    "NMR04A014 and the largest file in this lane."),
   ("138,084,248 bytes, the largest here. Its first six pages are imaged; the text from page 7 on reads Reporting "
    "Period: July 1, 2016 - June 30, 2017."), STORM, MS4,
   "Too large for the renderer; identified from its own text layer from page 7 on."),
 'und-034': ("MS4 Annual Report, signed and compiled, 2016", "annual reports",
   ("The City's signed and compiled stormwater annual report of 2016, submitted on EPA's National Pollutant "
    "Discharge Elimination System MS4 annual report form for the Albuquerque municipal separate storm sewer "
    "system."),
   ("10,027,499 bytes. Its first page reads Annual Report Format / National Pollutant Discharge Elimination System "
    "Stormwater Program / MS4 Annual Report Format. Its filename dates the compilation to 21 November 2016."),
   STORM, MS4, None),
 # ---- the 2014 package ---------------------------------------------------
 'und-005': ("2014 MS4 Annual Report: main body", "the 2014 annual report package",
   ("The body of the City's 2014 stormwater annual report to EPA, the narrative that the package's twenty-seven "
    "lettered attachments support, filed under the NPDES permit effective March 2012."),
   ("703,823 bytes. Opens: CITY OF ALBUQUERQUE 2014 ANNUAL REPORT, DUE APRIL 1, 2015, FOR NPDES PERMIT NMS000101, "
    "EFFECTIVE MARCH 1, 2012."), STORM, MS4, None),
 'und-032': ("2014 MS4 Annual Report: cover letter and certification statement", "the 2014 annual report package",
   ("The City's transmittal letter and signed certification for its 2014 stormwater annual report, the document "
    "that certifies the whole package to EPA under penalty of law."),
   ("58,416 bytes, no text layer, read by rendering: a City of Albuquerque letter of April 1, 2015 to U.S. EPA "
    "Region 6 about permit NMS000101, with a CERTIFICATION STATEMENT signed by Robert J. Perry, Chief "
    "Administrative Officer, dated 3/30/15."), STORM, MS4,
   "This is the document whose printed web address led an earlier lane to the other 36 files."),
 'und-006': ("2014 MS4 Attachment A.1: public outreach outcomes report", "the 2014 annual report package",
   ("The outcomes report for the regional stormwater public-education campaign, prepared for the Mid Rio Grande "
    "Stormwater Quality Team and attached to the City's 2014 annual report as evidence of its outreach."),
   "706,091 bytes. Opens as a February 18, 2015 memorandum TO: The Mid Rio Grande Stormwater Quality Team. " + A14,
   STORM, MS4, None),
 'und-007': ("2014 MS4 Attachment A.1: draft stormwater quality and illicit discharges ordinance",
   "the 2014 annual report package",
   ("The draft City ordinance regulating stormwater quality and prohibiting illicit discharges, attached to the "
    "2014 annual report as the legal instrument the City proposed for its permit obligations."),
   ("207,594 bytes. Opens: ORDINANCE STORMWATER QUALITY AND ILLICIT DISCHARGES, REGULATING STORMWATER QUALITY AND "
    "PROHIBITING ILLICIT DISCHARGES. " + A14), STORM, MS4,
   "A draft ordinance. Do not present it as enacted law; the enacted version is a separate question."),
 'und-008': ("2014 MS4 Attachment A.1: Fleet Management draft spill prevention plan",
   "the 2014 annual report package",
   ("The draft Spill Prevention, Control and Countermeasure plan for the City's Fleet Management Division, attached "
    "to the 2014 annual report as the control measure for fuel and oil at City vehicle facilities."),
   ("13,750,584 bytes, the largest attachment. Opens: City of Albuquerque DRAFT PLAN, Department of Finance and "
    "Administration, Fleet Management Division, Spill Prevention, Control. " + A14), STORM, MS4,
   "Marked DRAFT PLAN on its own first page."),
 'und-009': ("2014 MS4 Attachment A.1: household hazardous waste collection report",
   "the 2014 annual report package",
   ("Monthly figures for the City's household hazardous waste collections from July 2013 to June 2014, counting "
    "participants by city, county and out-of-county, attached as evidence of the pollution-prevention programme."),
   ("223,534 bytes. Opens: Household Hazardous Waste Collection July 2013- June 2014, with columns for Month, "
    "Total, Orphaned, City Participants, County, Out-of-County. " + A14), STORM, MS4, None),
 'und-010': ("2014 MS4 Attachment A.1: industrial and high-risk facility call list",
   "the 2014 annual report package",
   ("The City's contact roster for industrial and high-risk facilities in its stormwater programme, recording which "
    "facility each inspector is responsible for calling and whether the site is in the tracking database."),
   ("225,889 bytes. Column headings read Facility Name, Location, CALL RESPONSIBILITY, FACILITY CONTACT, PHONE2, "
    "EMAIL. " + A14), STORM, MS4,
   ("It is a contact list. The names in it are business contacts at regulated facilities rather than residents, but "
    "a person should confirm that before it is published.")),
 'und-012': ("2014 MS4 Attachment A.1: upstream and downstream water quality results in the Rio Grande",
   "the 2014 annual report package",
   ("Measured water-quality results upstream and downstream of Albuquerque in the Rio Grande, set against the New "
    "Mexico and Pueblo criteria they are judged by, attached to the City's 2014 annual report."),
   ("475,880 bytes. Column headings read NMAC 20.6.4 Water Quality Criterion, Pueblo Water Quality Criterion, Bear "
    "Arroyo at Jefferson, Embudo Arroyo at Monte Largo. " + A14), STORM, MS4, None),
 'und-011': ("2014 MS4 Attachment A.1: supplemental environmental project completion report",
   "the 2014 annual report package",
   ("The completion report for the supplemental environmental project at the Pino Maintenance Yard, carried out "
    "under EPA enforcement docket CWA-06-2014-1740 and attached to the City's 2014 annual report."),
   ("4,079,768 bytes. Its docket number is on its filename; its text from page 2 reads ATTACHMENT A: PROJECT "
    "LOCATION MAP - Pino Maintenance Yard is located in northeast Albuquerque near the intersection of Pino Avenue "
    "and San Pedro Drive, followed by dated construction photographs. " + A14), STORM, MS4, None),
 'und-013': ("2014 MS4 Attachment A.1.a: campaign website analytics report", "the 2014 annual report package",
   ("Web analytics for keeptheriogrand.org, the regional stormwater campaign site, for calendar year 2014, attached "
    "to the City's annual report as a measure of how far its public education reached."),
   ("160,097 bytes. Opens with the report header for http://www.keeptheriogrand.org covering Jan 1, 2014 to Dec 31, "
    "2014. " + A14), STORM, MS4, None),
 'und-014': ("2014 MS4 Attachment A.1.b: public survey card", "the 2014 annual report package",
   ("The two-sided public survey card used by the Mid Rio Grande Stormwater Quality Team, asking residents what "
    "they do about runoff and what they would pay for cleaner water, attached to the City's 2014 annual report."),
   ("126,838 bytes, two pages, no text layer, read by rendering. Both pages are the blank card: Please Tell Us What "
    "You Think, with questions on age, zip code and willingness to pay an additional monthly fee. " + A14),
   STORM, MS4,
   ("Its filename says Survey Card Results, but both of its pages are the blank survey instrument. The file "
    "contains no results. Title it for what it is.")),
 'und-015': ("2014 MS4 Attachment A.14: Flora Vista photographs and plan sheets",
   "the 2014 annual report package",
   ("Before-and-after photographs and plan sheets for the Flora Vista drainage improvement, attached to the City's "
    "2014 annual report as evidence of a completed structural control."),
   ("401,380 bytes, no text layer, read by rendering. Page 1 is captioned Flora Vista - BEFORE, showing standing "
    "water across the roadway, above Flora Vista - AFTER, a rebuilt and drained street photographed 07 03 2014. "
    + A14), STORM, MS4, None),
 'und-016': ("2014 MS4 Attachment A.2: storm event means and annual pollutant loads, 2014",
   "the 2014 annual report package",
   ("Calculated annual pollutant loads and yields by outfall for the 2014 water year, the quantitative core of the "
    "City's monitoring obligation under its stormwater permit."),
   ("217,813 bytes. Opens: Table 1. ANNUAL LOAD (TON) AND YIELD (LB/ACRE) FROM 10/1/13 TO 9/30/14, by outfall "
    "including SAN ANTONIO and SOUTH DIVERSION CHANNEL. " + A14), STORM, MS4, None),
 'und-017': ("2014 MS4 Attachment A.2: total waste diverted and material reuse", "the 2014 annual report package",
   ("Fiscal 2014 figures for waste diverted from landfill and material reused, including household hazardous waste "
    "shipped for destruction, attached to the City's annual report as a pollution-prevention measure."),
   ("261,239 bytes. Column headings read Recycled Waste FY 2014, Total HHW (lbs) Diverted from Landfill, Shipped "
    "Waste for Destruction. " + A14), STORM, MS4, None),
 'und-018': ("2014 MS4 Attachment A.2.a: material removed from arroyos and catch basins in 2014",
   "the 2014 annual report package",
   ("Monthly tonnages of silt, trash, debris and vegetation removed from City arroyos and catch basins during 2014 "
    "and taken to the Cerro Colorado Landfill."),
   ("20,442 bytes, the smallest file in this lane. Opens: Silt/Trash/Debris/Vegetation Removed from Arroyos & Catch "
    "Basins, Cerro Colorado Landfill 2014, by month. " + A14), STORM, MS4, None),
 'und-019': ("2014 MS4 Attachment A.2.a: internal stormwater monitoring memorandum, October 2014",
   "the 2014 annual report package",
   ("The engineer's internal monitoring memorandum to the City's MS4 storm water monitoring team, reporting what "
    "the year's sampling found and attached to the 2014 annual report."),
   ("10,275,726 bytes. Opens: Memorandum To: City of Albuquerque MS4 Storm Water Monitoring Team, From: Sarah C. "
    "Tuite, P.E., Date: October 1, 2014. " + A14), STORM, MS4, None),
 'und-020': ("2014 MS4 Attachment A.2.b: street sweeping materials removed in 2014",
   "the 2014 annual report package",
   ("Materials removed from City streets during 2014 by the Street Maintenance Division, the street-sweeping figures "
    "the City reports as a stormwater control measure."),
   ("155,292 bytes. Opens: City of Albuquerque Department of Municipal Development, Street Maintenance Division. "
    + A14), STORM, MS4, None),
 'und-021': ("2014 MS4 Attachment A.2.b: quarterly visual monitoring results for three City facilities",
   "the 2014 annual report package",
   ("Completed field forms recording quarterly visual inspections of stormwater outfall discharges at three City "
    "facilities, with observed flow, colour, turbidity, sheen and inspector comments."),
   ("470,676 bytes, seven pages, no text layer, read by rendering. Page 1 is a City of Albuquerque, Pino Yards "
    "Complex quarterly visual monitoring form dated 8-22-14 in a steady rain, recording flow at outfalls PY1 to "
    "PY3 and a significant sheen on ponded stormwater at PY3. " + A14), STORM, MS4, None),
 'und-022': ("2014 discharge monitoring reports: cover letter", "the 2014 annual report package",
   ("The City's letter transmitting its 2014 discharge monitoring reports to EPA Region 6, explaining which seasons "
    "produced qualifying storm events and which did not, and attaching the delegation of signatory authority."),
   ("791,483 bytes, eight pages, no text layer, read by rendering. A City letter of March 30, 2015 to the EPA "
    "Region 6 Environmental Protection Specialist about permit NMS0000101, reporting that because of continued "
    "drought no qualifying storm events occurred in the dry season, signed by the Storm Water Management Section. "
    + A14), STORM, MS4, None),
 'und-023': ("2014 discharge monitoring reports: dry season", "the 2014 annual report package",
   ("The City's signed dry-season discharge monitoring reports for 2014 on EPA's NPDES form, recording measured or "
    "absent discharges at each permitted outfall."),
   ("1,741,738 bytes, no text layer, read by rendering. Page 1 is EPA Form 3320-1 for permit NMS000101, discharge "
    "number 001-E, North Floodway Channel, dry season, with No Discharge marked and parameters from temperature to "
    "total suspended solids. " + A14), STORM, MS4, None),
 'und-024': ("2014 discharge monitoring reports: wet season", "the 2014 annual report package",
   ("The City's signed wet-season discharge monitoring reports for 2014 on EPA's NPDES form, the companion set to "
    "the dry-season reports and the larger of the two."),
   ("4,115,866 bytes, no text layer. The same EPA Form 3320-1 series as the dry-season set, distinguished by season "
    "on its filename and by its size. " + A14), STORM, MS4,
   "Identified as the wet-season companion by filename and form series rather than by reading every form."),
 'und-025': ("2014 MS4 Attachment A.4: 311 complaint map and field log", "the 2014 annual report package",
   ("The map and field log of stormwater complaints reported to the City's 311 service during 2014, showing where "
    "residents reported problems and what the City did about them."),
   ("3,155,714 bytes. Its extracted text is a jumble of overlaid map labels and street names, the signature of a "
    "drawn map rather than a document. " + A14), STORM,
   [{"page": CLIMATE, "reason": "Water-quality monitoring data."}, {"page": MAPS, "reason": "A location map."}],
   None),
 'und-026': ("2014 MS4 Attachment A.4: stormwater quality features installed in 2014",
   "the 2014 annual report package",
   ("An inventory of the stormwater quality structures the City installed during 2014, each with its identifier and "
    "location, attached as evidence of new structural controls."),
   ("1,177,706 bytes. Opens: ID 1 structure SWQ STRUCTURE ON SOUTH DOMINGO BACA ARROYO, location SOUTH DOMINGO BACA "
    "ARROYO WEST OF WASHINGTON BRIDGE. " + A14), STORM, MS4, None),
 'und-027': ("2014 MS4 Attachment A.6: impervious area added in 2014", "the 2014 annual report package",
   ("The City's calculation of impervious area added by development during 2014, totalling about 238 acres from "
    "residential, commercial and hydrology-department permit records, with the number of erosion control plans "
    "approved."),
   ("1,311,557 bytes, no text layer, read by rendering. Page 1 is a printed City staff email of 25 March 2015 "
    "summing three permit extracts to Total IA = 237.939 Acres (+/- 238 Acres) and noting 41 Erosion Sediment "
    "Control (ESC) Plans approved in 2014. " + A14), STORM, MS4, None),
 'und-028': ("2014 MS4 Attachment A.6: Rio Grande Valley State Park environmental monitoring baseline report",
   "the 2014 annual report package",
   ("The environmental monitoring plan and baseline data report for the Central to Montano reach of Rio Grande "
    "Valley State Park, attached to the City's 2014 annual report."),
   ("6,103,177 bytes. Opens: RIO GRANDE VALLEY STATE PARK, CENTRAL TO MONTANO PROJECT: ENVIRONMENTAL MONITORING "
    "PLAN AND BASELINE DATA REPORT. " + A14), STORM,
   [{"page": CLIMATE, "reason": "Environmental monitoring data."},
    {"page": 'content/public-works/parks-recreation.md', "reason": "It covers a state park reach inside the city."}],
   None),
 'und-029': ("2014 MS4 Attachment B.5: dry weather screening results", "the 2014 annual report package",
   ("Field results from the City's dry-weather screening for illicit discharges in 2014, recording each location, "
    "the weather, and the suspected source of any flow found."),
   ("616,336 bytes. Opens: Location 01 SAN JOSE DRAIN AT WOODWARD, DATE 12/8/2014, SUSPECTED SOURCE boiler water. "
    + A14), STORM, MS4, None),
 'und-030': ("2014 MS4 Attachment C.1: E. coli loading results for water year 2014",
   "the 2014 annual report package",
   ("The statistical summary of estimated total E. coli load from the Albuquerque storm sewer system for water year "
    "2014, reported against the bacterial total maximum daily load the river is subject to."),
   ("469,827 bytes. Opens: 2013 Bacterial TMDL Loading Report - Albuquerque MS4, STATISTICAL SUMMARY OF THE "
    "ESTIMATED TOTAL E-COLI LOAD. " + A14), STORM, MS4, None),
 'und-031': ("2014 MS4 Attachment C.iv: PCB sediment report, Tijeras Arroyo", "the 2014 annual report package",
   ("The consultant's report on polychlorinated biphenyls in sediment at Tijeras Arroyo, prepared for the City's "
    "storm drainage design section and attached to the 2014 annual report."),
   ("2,349,748 bytes. Opens as a March 12, 2015 letter to the City of Albuquerque Department of Municipal "
    "Development, Storm Drainage Design. " + A14), STORM, MS4, None),
 # ---- the permit and the approval ----------------------------------------
 'und-037': ("Middle Rio Grande watershed-based MS4 general permit", "permit and authorisation",
   ("The federal general permit for municipal separate storm sewer systems in the Middle Rio Grande watershed, the "
    "instrument that imposes every obligation the City's annual reports answer to."),
   ("1,724,506 bytes. Opens: NPDES Permit No. NMR04A000, MIDDLE RIO GRANDE WATERSHED BASED MUNICIPAL SEPARATE STORM "
    "SEWER SYSTEM PERMIT."), STORM, MS4,
   ("Written by the U.S. Environmental Protection Agency, not by the City. Keep it because it is the instrument the "
    "City's own filings are made under, and attribute it to EPA.")),
 'und-036': ("EPA letter authorising the City's MS4 permit coverage, 17 December 2015", "permit and authorisation",
   ("The federal regulator's letter telling the City that its notice of intent was complete and that authorisation "
    "under the Middle Rio Grande storm sewer permit was effective, the document that starts the City's duty to "
    "comply."),
   ("33,429 bytes, no text layer, read by rendering. A U.S. EPA Region 6 letter of December 17, 2015 to the City's "
    "Department of Municipal Development about coverage under NPDES No. NMR04A000, permit tracking number "
    "NMR04A014, signed by the Director of the Water Division."), STORM, MS4,
   "Written by EPA and addressed to the City. Attribute it to EPA; it is kept as part of the City's permit record."),
 # ---- the rest -----------------------------------------------------------
 'und-033': ("Scarcity, Resilience and the Path to Abundance: a theory of change", "city policy",
   ("The Mayor's office statement of the City's theory of change, arguing from scarcity and resilience toward "
    "abundance and setting out how the administration frames the choices facing Albuquerque."),
   ("397,194 bytes. Opens: Scarcity, Resilience and the Path to Abundance: A Theory of Change for the City at the "
    "Crossroads. Two unrelated City pages link this file - the stormwater permit page and a councillor's page - "
    "and the inventory has it from neither."), ABOUT,
   [{"page": CITYDATA, "reason": "It frames how the City reports on itself."}], None),
 'und-038': ("Cruising Task Force findings and recommendations, 2 April 2018", "council records",
   ("The City Council Cruising Task Force's findings and recommendations, produced under Resolution R-17-250, on "
    "what the City should do about cruising in Albuquerque."),
   ("9,756,353 bytes. Its cover reads CRUISING TASK FORCE, APRIL 2, 2018, FINDINGS & CITY COUNCIL RECOMMENDATIONS, "
    "CITY OF ALBUQUERQUE (PER R-17-250)."), TRANSPO,
   [{"page": ABOUT, "reason": "A Council task force record produced under a named resolution."}], None),
 'und-039': ("ABQ Area Resources Quick Guide", "public service guides",
   ("The City's quick-reference guide to Albuquerque social services, listing the organisations residents can turn "
    "to and how to reach them, updated 1 March 2026."),
   "1,608,587 bytes. Opens: ABQ Area Resources Quick Guide, Updated 3/1/26, with a note that the area code is (505) unless indicated.",
   None,
   [{"page": ABOUT, "reason": "A City-published public service document."}],
   ("The site has no health or social-services page, so no canonical placement is proposed. Where it belongs is a "
    "judgment for a person, not for this lane.")),
 'und-040': ("APD resource card, 2026 revision", "public service guides",
   ("The Albuquerque Police Department's folding resource card listing overnight shelters and other services "
    "officers can direct people to, in its February 2026 revision."),
   ("574,917 bytes. Its panels are labelled LEFT PANEL (Side 1) through PANEL 4, and panel content includes "
    "OVERNIGHT SHELTERS, Updated 2/01."), None,
   [{"page": ABOUT, "reason": "A City-published public service document."}],
   ("Print artwork for a folded card rather than a document laid out to be read on screen, and again there is no "
    "page on the site for it. Both questions belong to a person.")),
 'und-041': ("Form Based Zones, Section 14-16-3-22 Part A, 2 April 2009 final", "zoning code",
   ("Part A of the City's Form Based Zones section of the zoning code in its final April 2009 form, the general "
    "regulations establishing the form-based zones and how the section is organised."),
   ("1,276,278 bytes, 59 pages. Opens: PART 3: GENERAL REGULATIONS, Section 14-16-3-22 Form Based Zones, 3-80, "
    "14-16-3-22 FORM BASED ZONES, Section Organization."), ZONING,
   [{"page": DEVPROC, "reason": "Regulations development applications are judged against."}],
   "Named by an earlier lane as the successor to an inventory record whose supersession row has a null canonical."),
 'und-042': ("Form Based Zones, Section 14-16-3-22 Part C, 2 April 2009 final", "zoning code",
   ("Part C of the City's Form Based Zones section of the zoning code in its final April 2009 form, covering the "
    "components of the zones: building types, street design and parking."),
   ("718,729 bytes, 28 pages. Opens: PART 3: GENERAL REGULATIONS, Section 14-16-3-22 Form Based Zones, 3-111, (C) "
    "Components. Building Types, Street Design, Pa."), ZONING,
   [{"page": DEVPROC, "reason": "Regulations development applications are judged against."}],
   "Named by an earlier lane as the successor to an inventory record whose supersession row has a null canonical."),
 'und-043': ("Planned Growth Strategy Part 2, Chapter 4.0: examples of mixed-use redevelopment in other cities",
   "planned growth strategy",
   ("Chapter 4.0 of Part 2 of the City's Planned Growth Strategy, surveying mixed-use redevelopment projects in "
    "other cities as precedent for Albuquerque's own redevelopment approach."),
   ("306,971 bytes, 12 pages, printed pages 157 to 168. Opens: 4.0 Examples of Mixed-Use Redevelopment Projects In "
    "Other Cities. Absent from the City's own collection listing for the directory it sits in."), AREAPLANS,
   [{"page": DEVPROC, "reason": "It informs how redevelopment is handled."}], None),
 'und-044': ("Planned Growth Strategy Part 2, Chapter 6.0: financial implementation of the preferred alternative",
   "planned growth strategy",
   ("Chapter 6.0 of Part 2 of the City's Planned Growth Strategy, setting out how the preferred alternative was to "
    "be paid for and what that implied for City finances."),
   ("241,037 bytes, 16 pages, printed pages 211 to 218. Opens: 6.0 Financial Implementation of the Planned Growth "
    "Strategy Preferred Alternative, 6.1 Executive Summary. Absent from the City's own collection listing."),
   AREAPLANS, [{"page": 'content/city-data/capital-spending.md', "reason": "It is a financing chapter."}], None),
}

DO_NOT_ADD = {
 'und-047': {
  "title_for_reference": "DMDCIPFacParkingScope.pdf",
  "what_it_is": "The Department of Municipal Development's 2013 Community Facilities capital project scope sheet.",
  "why_not": ("It is not undiscovered. It is already inventory record src-047e8956baad212d, status validated, at "
              "exactly this URL and with exactly this checksum."),
  "a_correction_to_an_earlier_artifact": {
   "artifact": "bond-2013-department-set-cluster-research-2026-09-12.json",
   "it_said": ("DMDCIPFacParkingScope.pdf exists on the City server and is absent from the inventory. Only its "
               "copy_of edition was ever crawled. It recommended adding the file as a new candidate."),
   "what_is_actually_the_case": ("The file is in the inventory and validated. The earlier lane probed the City "
                                 "server, found the file, and did not then check the inventory for it."),
   "how_it_was_caught": ("Two ways at once. The checksum sweep matched it to a validated record, and a separate "
                         "URL sweep matched the same record. Either alone would have caught it."),
   "the_rule_it_reinforces": ("Probing a server tells you a file exists. Only a search of the inventory tells you "
                              "the archive lacks it. The earlier lane did the first and reported the second."),
   "a_consequence_for_a_still_open_row": ("That lane left src-dc2bbf43c5bb13f7, the copy_of edition, as requires "
                                          "human review. The question it was held for - whether the original "
                                          "exists - now has an answer: it does, and it is validated."),
  },
  "my_own_error_on_the_way": ("I first requested this file at documents.cabq.gov and got HTTP 404. That host was my "
                              "guess, not the recorded URL; the file is on www.cabq.gov. Refetched at the recorded "
                              "address it returns 200 and 52,980 bytes, matching the earlier lane's measurement "
                              "exactly."),
 },
 'und-048': {
  "title_for_reference": "Sirolli.pdf",
  "what_it_is": "A URL in the Council economic forum directory that returns 4,926 bytes of website HTML, not a document.",
  "why_not": ("It is not undiscovered and it is not a document. It is already inventory record "
              "src-719d61a1047aeb31, and economic-forum-cluster-research-2026-09-12.json already decided it, "
              "excluded. The bytes it serves today are byte-identical to what that lane measured."),
  "a_correction_to_my_own_framing": ("The economic forum lane reported that Sirolli.pdf is missing from the City's "
                                     "own collection listing while still existing as an object. That is a statement "
                                     "about the City's index, not about the inventory. I carried it into this lane "
                                     "as an undiscovered file, which it never was."),
 },
 'und-045': {
  "title_for_reference": "Part2.pdf",
  "what_it_is": ("144 pages of a City and County governmental unification study, sitting in the Planned Growth "
                 "Strategy directory under a filename that suggests it is part of that plan."),
  "why_not": ("Already resolved, and not by me. completed-reports-studies-cluster-research-2026-09-12.json "
              "established that it is 144 of the 276 pages of inventory record src-a5475f489b373f20, Structuring A "
              "New Urban Government: A Report on the Unification of Bernalillo County and the City of Albuquerque, "
              "with token coverage of 1.0000 inside the whole and 0.7239 the other way. Archiving the complete "
              "report covers it."),
  "what_i_verified_here": ("Only that the file is still served and still measures 5,469,413 bytes with the same "
                           "checksum the earlier lane recorded. I did not re-run the containment measurement; the "
                           "recommendation is carried forward from that lane, not re-derived."),
 },
 'und-046': {
  "title_for_reference": "Figure17.pdf",
  "what_it_is": "Figure 17: Conceptual Streetscape Design for Central Avenue, Sierra Dr to Madison St.",
  "why_not": ("nob-hill-highland-cluster-research-2026-09-11.json established that this figure is already inside "
              "the validated R2 archive at printed page 35 of the plan, exactly like its seven siblings, so adding "
              "it as a candidate would create a record whose only possible disposition is duplicate."),
  "what_i_verified_here": ("That the file is still served, measures 634,013 bytes, and is what that lane said it "
                           "is: rendered, its page carries the title Central Avenue Conceptual Streetscape Plan and "
                           "the caption Figure 17: Conceptual Streetscape Design over an aerial of Central between "
                           "Sierra Dr and Madison St. I did not re-verify the containment claim; that is carried "
                           "forward."),
 },
}


def base(i):
    return urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1])


def row(i, rec):
    return {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i], "filename": base(i),
            "recommendation": rec, "reported_in": REPORTED_IN[i], "link_check": LC,
            "content_kind": KIND[MAGIC[i]], "leading_bytes": MAGIC[i], "http_status": CODE[i], **M[i]}


add, skip = [], []
for i in SLICE:
    if i in DO_NOT_ADD:
        r = row(i, "do not add")
        r.update(DO_NOT_ADD[i])
        skip.append(r)
        continue
    t, group, desc, ev, canon, cross, caution = (D[i][0], D[i][1], D[i][2], D[i][3], D[i][4], D[i][5], D[i][6])
    r = row(i, "add to the inventory as a new candidate")
    r.update({"title": t, "group": group, "description": desc, "evidence": ev,
              "description_word_count": len(desc.split()),
              "proposed_canonical_page": canon, "cross_listings": cross or []})
    if canon is None:
        r["no_canonical_page_proposed"] = True
    if caution:
        r["caution"] = caution
    add.append(r)

rows = add + skip
assert len(rows) == len(SLICE), (len(rows), len(SLICE))
assert sorted(r['local_ref'] for r in rows) == SLICE
bygroup = collections.Counter(r.get('group') for r in add)
add_bytes = sum(r['size_bytes'] for r in add)

artifact = {
 "batch_id": "undiscovered-documents-research-2026-09-14",
 "lane": "Claude research lane: the documents this run found on City servers that the inventory does not hold",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": ("Every other artifact in this run decides the status of records that already exist in "
                      "master-inventory.json. This one does not. None of the 48 files below has an inventory id, "
                      "and every row carries inventory_id: null to say so."),
  "so_it_cannot_be_applied_the_usual_way": ("scripts/project/Update-Candidate.ps1 changes the status of an existing "
                                            "candidate. It cannot act on any row here, because there is no "
                                            "candidate to act on. These are proposed additions."),
  "why_the_field_is_called_recommendation": ("Not recommended_status. A status belongs to a record; these files have "
                                             "no record yet. The two values used are add to the inventory as a new "
                                             "candidate, and do not add."),
  "what_should_happen_first": ("The 44 additions should be created as candidates, at which point they become "
                               "ordinary pending-review records and the normal archival gate applies to them - "
                               "inventory-only until an R2 object exists and its download is verified."),
 },
 "cluster": ("Seven earlier lanes each reported files they found on City servers and could not find in the "
             "inventory. Nobody had gone back to them. This lane does."),
 "scope": ("Every undiscovered file reported anywhere in this run, gathered from the artifacts that reported them, "
           "refetched, remeasured, and swept against the inventory and against every saved artifact."),
 "where_they_came_from": {
  "reports_by_artifact": {
   "facility-environmental-compliance-cluster-research-2026-09-12.json": 37,
   "councilor-district-3-and-6-cluster-research-2026-09-13.json": 4,
   "planned-growth-strategy-cluster-research-2026-09-11.json": 3,
   "form-based-code-cluster-research-2026-09-11.json": 2,
   "nob-hill-highland-cluster-research-2026-09-11.json": 1,
   "bond-2013-department-set-cluster-research-2026-09-12.json": 1,
   "economic-forum-cluster-research-2026-09-12.json": 1,
  },
  "total_reports": 49,
  "distinct_files": 48,
  "distinct_files_by_first_reporter": dict(collections.Counter(REPORTED_IN.values())),
  "note": ("49 reports, 48 distinct files: the Mayor's theory-of-change paper was reported twice, once from the "
           "City's stormwater permit page and once from a councillor's page. Two unrelated City pages link it and "
           "the inventory had it from neither. Each row's reported_in names the artifact that reported it first, so "
           "the by-first-reporter tally credits that paper to the stormwater lane and shows 3 for the councillor "
           "lane, not 4."),
 },
 "what_the_sweep_found_this_time": {
  "the_sweep_was_run_differently_here": ("Everywhere else in this run the sweep compared candidates against the "
                                         "1,020 archived inventory records. These are proposed additions, so a "
                                         "collision with any inventory record at all disqualifies them, archived or "
                                         "not. The sweep therefore ran against all %d checksummed inventory "
                                         "records, and then again against all %d inventory URLs."
                                         % (len(ALL_SHA), len(INV_URL))),
  "checksum_collisions_with_the_inventory": len(SHA_HIT),
  "url_collisions_with_the_inventory": len(URL_HIT),
  "collisions_with_saved_artifacts": len(ART_HIT),
  "what_they_were": ("Two files that were never undiscovered: a capital project scope sheet that is already a "
                     "validated inventory record, and an economic-forum URL that is already an inventory record and "
                     "was already excluded. Both were caught twice over, by checksum and by URL."),
  "the_point": ("A URL sweep is not redundant with a checksum sweep. Only 1,460 of the inventory's records carry a "
                "checksum at all, so a file can be in the inventory and invisible to a checksum comparison. Here "
                "both sweeps happened to agree; they need not have."),
 },
 "two_earlier_findings_corrected": {
  "the_capital_project_scope": ("bond-2013-department-set-cluster-research-2026-09-12.json reported "
                                "DMDCIPFacParkingScope.pdf as absent from the inventory and recommended adding it. "
                                "It is inventory record src-047e8956baad212d, validated, at the same URL with the "
                                "same checksum. That lane probed the server and did not then search the inventory."),
  "the_economic_forum_file": ("Sirolli.pdf was reported as missing from the City's own collection listing. That is "
                              "true, and it is a statement about the City's index. I carried it forward as an "
                              "undiscovered file, which it never was: it is an inventory record already excluded."),
  "the_rule": ("Probing a server tells you a file exists. Only a search of the inventory tells you the archive "
               "lacks it. Two of seven reports in this run conflated the two."),
  "a_row_it_unblocks": ("The bond lane held src-dc2bbf43c5bb13f7, the copy_of edition of the same scope sheet, as "
                        "requires human review pending whether the original existed. It exists and is validated."),
 },
 "two_recommendations_carried_forward_rather_than_re_derived": {
  "Part2.pdf": ("Do not add: completed-reports-studies-cluster-research-2026-09-12.json showed it is 144 of the 276 "
                "pages of inventory record src-a5475f489b373f20. I confirmed only that the file is still served at "
                "the same size and checksum."),
  "Figure17.pdf": ("Do not add: nob-hill-highland-cluster-research-2026-09-11.json showed it is already inside the "
                   "validated R2 archive at printed page 35. I confirmed the file's identity by rendering it - it "
                   "is Figure 17, Central Avenue Conceptual Streetscape Design, Sierra Dr to Madison St - but did "
                   "not re-run the containment measurement."),
  "why_this_is_stated": "So that nobody reads a row of this artifact as a second, independent confirmation of something it is not.",
 },
 "the_stormwater_hole_this_closes": {
  "what_the_archive_was_missing": ("A continuous record of the City's federal stormwater compliance. The 37 files "
                                   "from the permit page are the 2014 annual report in full - a main body and 27 "
                                   "lettered attachments - plus the annual reports for fiscal 2017, 2019, 2020 and "
                                   "2021, a signed compiled report for 2016, the EPA letter authorising the City's "
                                   "permit coverage, and the permit itself."),
  "total_bytes": add_bytes,
  "the_three_largest": ("The fiscal 2017, 2020 and 2019 annual reports, at 138,084,248, 133,787,450 and "
                        "122,657,409 bytes. Between them they are four fifths of this lane's footprint."),
  "how_it_was_found_originally": ("Not by crawling. The 2014 certification statement prints the City web page its "
                                  "data would be posted to; an earlier lane read that page and reconciled its links "
                                  "against the inventory."),
 },
 "what_reading_them_changed": {
  "the_renderer_could_not_open_the_three_largest": ("The fiscal 2017, 2019 and 2020 reports defeated the renderer. "
                                                    "They did not need it: the first six pages of each are images, "
                                                    "but the text layer from page 7 on names the reporting period "
                                                    "exactly. A file whose opening pages yield nothing is not a "
                                                    "file without a text layer, and how many pages you look at "
                                                    "decides which of the two you conclude."),
  "a_draft_and_a_final_that_are_the_same_report": ("The fiscal 2021 report exists as a draft and a final, 134,830 "
                                                   "bytes apart. Neither has a text layer on page 1. Rendering both "
                                                   "produced byte-identical page images - the same 450,584-byte PNG "
                                                   "with the same SHA-256 - and both files have 382 pages. The "
                                                   "draft's row says it is superseded by the final."),
  "a_filename_that_promises_results_and_delivers_none": ("Attachment A.1.b is called Survey Card Results. It is two "
                                                         "pages and both of them are the blank survey card. There "
                                                         "are no results in it. Its row is titled for what the file "
                                                         "is, not for what the filename claims."),
  "files_yielding_no_text_in_their_first_six_pages": ("15 of the 47 PDFs. 12 were read by rendering, which is the only "
                                         "way their content could be stated: the certification statement's "
                                         "signature and date, the EPA authorisation letter, the DMR forms, the "
                                         "Flora Vista before-and-after photographs, the handwritten field "
                                         "monitoring forms, the printed staff email totalling 237.939 acres of new "
                                         "impervious area, and the Central Avenue streetscape figure. The other 3 "
                                         "are the oversized annual reports, which the renderer could not open and "
                                         "which did not need it."),
 },
 "one_file_found_and_not_retrievable": {
  "what": "The completed Sandia High School Area Safety and Traffic Calming Study.",
  "why_it_was_looked_for": ("find-your-councilor-cluster-research-2026-09-14.json approved the study's public "
                            "meeting presentation and recorded that the final report its schedule promised for July "
                            "2023 was not in the inventory."),
  "where_it_is": ("Found. The District 7 project page carries a link labelled Sandia High School Safety and Traffic "
                  "Calming Study pointing at https://sfftp.cabq.gov/f/7e1d61fbc4c19830, a City file-transfer host, "
                  "separate from the presentation link labelled Meeting PowerPoint Presentation."),
  "this_confirms_the_earlier_reading": ("The page itself distinguishes the completed study from the meeting "
                                        "presentation, which is exactly how the presentation was labelled."),
  "why_it_is_not_in_this_artifact_as_a_row": ("It cannot be fetched. The share URL returns 1,344 bytes of "
                                              "JavaScript application shell; the file itself is loaded by that "
                                              "application, and the host's REST API answers 401 without "
                                              "credentials. There are no bytes to measure, so there is no size, no "
                                              "checksum and no container - and a row asserting a document without "
                                              "them would be a row asserting something unverified."),
  "what_it_means_for_the_archive": ("A crawler reaches this link and gets 1,344 bytes of shell HTML. Any City "
                                    "document published only through this file-transfer host is invisible to "
                                    "discovery in the same way, and the City uses it for at least one completed "
                                    "study."),
  "recommended_action": ("Retrieve it through a browser and add it, and check whether other sfftp.cabq.gov links "
                         "exist across the City site. I did not attempt to work around the host's authentication."),
  "it_was_retrieved": ("Done on 2026-09-14. The repository owner retrieved it through a browser: it is the Sandia "
                       "High School Area Traffic Calming and Safety Study, final report with appendices, January "
                       "2024 - not July 2023 as the presentation's schedule promised - 10,493,498 bytes and 157 "
                       "pages. Measured and recommended in file-share-retrieval-research-2026-09-14.json. The "
                       "sweep of the City site for other sfftp.cabq.gov links has not been done."),
 },
 "method": ("Read every artifact in project-state/discovery for reported undiscovered files and collected all 49 "
            "reports. Refetched all 48 distinct URLs and measured byte length, SHA-256 and leading bytes from the "
            "fetched bytes; tested every PDF for its end-of-file marker; extracted text from all of them and "
            "rendered the eleven that yielded none and could be rendered; swept every checksum against all "
            "checksummed inventory records and against every row of every saved artifact, and swept every URL "
            "against every inventory URL."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": ("For proposed additions, test against every inventory record rather than only the archived ones, "
                   "and by URL as well as by checksum."),
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "archived_records_compared_against": len(ARCH_SHA),
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Two of the 48 are already inventory records. The other 46 are absent from the inventory by both tests.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "supersession_found": 1,
  "note": ("No two of the 48 files are byte-identical. One supersession: the draft fiscal 2021 annual report is "
           "superseded by the final, established by identical page renders and identical page counts."),
 },
 "integration_flags": [
  {"severity": "not-applicable-through-update-candidate",
   "affects": [r['local_ref'] for r in rows],
   "finding": "No file in this artifact has an inventory id. Update-Candidate.ps1 cannot act on any row.",
   "recommended_action": "Create the 44 additions as candidates first; they then become ordinary pending-review records under the normal archival gate."},
  {"severity": "corrects-an-earlier-artifact",
   "affects": ['und-047', 'und-048'],
   "finding": ("Two files reported as undiscovered are already inventory records - one validated, one already "
               "excluded. The earlier lanes probed the City server and did not search the inventory."),
   "recommended_action": ("Do not add either. Treat src-dc2bbf43c5bb13f7's open human-review question as answered: "
                          "the original exists and is validated.")},
  {"severity": "substantive-find",
   "affects": [r['local_ref'] for r in add if r['group'] in ('annual reports', 'the 2014 annual report package',
                                                             'permit and authorisation')],
   "finding": ("The City's federal stormwater compliance record from 2014 to 2021 - the 2014 annual report in full "
               "with 27 attachments, five later annual reports, the EPA authorisation letter and the permit "
               "itself - none of it in the inventory."),
   "recommended_action": "Add all of it. It is the largest single gap this run found."},
  {"severity": "undiscoverable-by-crawler",
   "affects": [],
   "finding": ("The completed Sandia High School study is published only through sfftp.cabq.gov, a file-transfer "
               "host whose share URL returns 1,344 bytes of JavaScript shell and whose API requires credentials. No "
               "bytes could be measured, so it has no row here."),
   "recommended_action": "Retrieve it through a browser, and sweep the City site for other sfftp.cabq.gov links."},
  {"severity": "title-versus-content",
   "affects": ['und-014'],
   "finding": "Attachment A.1.b is named Survey Card Results and contains two pages, both of them the blank survey card. It holds no results.",
   "recommended_action": "Title it for its content. Its row does."},
  {"severity": "supersession",
   "affects": ['und-001', 'und-004'],
   "finding": "The fiscal 2021 annual report exists as a draft and a final that render identically on page 1 and have the same 382 pages.",
   "recommended_action": "Archive the final. Add the draft only if the archive keeps draft editions."},
  {"severity": "attribution",
   "affects": ['und-036', 'und-037'],
   "finding": "The MS4 general permit and the coverage authorisation letter were written by the U.S. Environmental Protection Agency, not by the City.",
   "recommended_action": ("Keep both - they are the instrument the City's own filings answer to and the letter that "
                          "starts its duty to comply - and attribute them to EPA.")},
  {"severity": "needs-a-person",
   "affects": ['und-039', 'und-040'],
   "finding": ("Two social-services resource guides have no page on the site to sit on; there is no health or "
               "human-services page. One of them is print artwork for a folded card."),
   "recommended_action": "Decide placement before adding, or decide they are out of scope. Neither row proposes a canonical page."},
  {"severity": "contact-list",
   "affects": ['und-010'],
   "finding": "Attachment A.1 is a call list with facility contact names, phone numbers and email addresses.",
   "recommended_action": ("The names appear to be business contacts at regulated facilities rather than residents, "
                          "but confirm that before publishing it.")},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": len(skip),
  "by_group": dict(bygroup),
  "containers": dict(collections.Counter(r['content_kind'] for r in rows)),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if CODE[i] == '200'),
                "failed": sum(1 for i in SLICE if CODE[i] != '200'),
                "method": ("Full HTTP GET with a browser user agent, 2026-09-14, with path segments percent-encoded "
                           "before the request. One URL was published over http on a host that refuses port 80 and "
                           "was refetched over https; one was refetched after I addressed it to the wrong host."),
                "integrity": "Every row rehashed against its file on disk; all 47 PDFs carry their end-of-file marker.",
                "containers_verified": "47 PDF and 1 HTML, by leading bytes."},
 "add_to_inventory": add,
 "do_not_add": skip,
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready. They are not even candidates yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint if all are added and archived: {add_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Each row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes and the artifact "
                      "that originally reported the file, which is everything needed to create a candidate. Every "
                      "row carries inventory_id: null. The two do-not-add rows that correct earlier artifacts name "
                      "the artifact and quote what it said."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('by_group', 'containers')}}))
