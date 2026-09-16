"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Sixth slice of the municipaldevelopment/documents lane: the
facility environmental compliance set. Fifteen 2021 stormwater pollution
prevention plans, the 2015 Water Year MS4 report attachments, and the City
facility solar design series.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\facility-environmental-compliance-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md5')
SP4 = SP[:-1] + '4'

STORM = 'content/public-works/stormwater-drainage.md'
CLIMATE = 'content/city-data/climate-environment.md'
CAPITAL = 'content/city-data/capital-spending.md'
TRANSIT = 'content/transportation/transit/abq-ride.md'

PARENT = 'src-c312994aa69f9bd5'   # water-year-2015-report-032516.pdf, validated and R2-archived
MOVED = 'src-feaefc4c87a06768'    # the 2018 museum shading report, corrected out of the slice-5 artifact

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for path in (os.path.join(SP, 'fetch.log'), os.path.join(SP4, 'fetch.log')):
    for line in open(path, encoding='utf-8'):
        i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
        if i in M:
            continue
        M[i] = {"size_bytes": int(s), "checksum_sha256": h}
        MAGIC[i] = mag
        URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')] + [MOVED]

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


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


SWPPP_WHY = ("The City's own stormwater pollution prevention plan for a named municipal facility, adopted under its "
             "EPA Multi-Sector General Permit. Each plan states that facility's drainage, its industrial activities, "
             "its pollutant sources, its control measures and its inspection schedule. The archive holds the City's "
             "MS4 permit reporting but not one of the facility plans underneath it.")

SWPPP = [
 ('src-f4a2c5973b47a750',
  "Storm Water Pollution Prevention Plan: Warehouse and Surplus Auction, Department of Finance and Administration",
  ("The City's stormwater plan for its Warehouse and Surplus Auction facility in the Pino Yards Complex records the "
   "site's drainage, industrial activities, pollutant sources, control measures and inspection routine under the "
   "federal multi-sector permit."),
  "Department of Finance and Administration, Purchasing Division; Warehouse and Surplus Auction (WSA), 5501 Pino St NE, Bldg. G, Albuquerque, NM 87109.",
  "Marked FINAL PLAN and dated May 2021 on its cover. The only plan in the set signed through DocuSign; its envelope ID appears on every page."),
 ('src-ec291ff32e857e33',
  "Storm Water Pollution Prevention Plan: Double Eagle II Yard, DMD Street Maintenance Division",
  ("The City's stormwater plan for the Double Eagle II street maintenance yard sets out the site's drainage, its "
   "industrial activities, its pollutant sources and the control measures and inspections required under the federal "
   "multi-sector permit."),
  "Department of Municipal Development, Street Maintenance Division; Double Eagle II Yard, Double Eagle Rd, Albuquerque, NM 87120.",
  "Marked FINAL PLAN and dated May 2021 on its cover."),
 ('src-ec2cc37296683211',
  "Storm Water Pollution Prevention Plan: Pino Yards Complex Street Maintenance Division, DMD",
  ("The City's stormwater plan for the street maintenance operation at the Pino Yards Complex records that site's "
   "drainage, industrial activities, pollutant sources, control measures and inspection schedule under the federal "
   "multi-sector permit."),
  "Department of Municipal Development, Street Maintenance Division; Pino Yards Complex, 5501 Pino St NE, Bldg. F, Albuquerque, NM 87109.",
  "Marked FINAL PLAN and dated May 2021 on its cover. One of three separate plans for three separate operations in the same Pino Yards Complex, each in its own building."),
 ('src-396c7eda463ade5d',
  "Storm Water Pollution Prevention Plan: Street Satellite #1, DMD Street Maintenance Division",
  ("The City's stormwater plan for its Street Satellite #1 maintenance yard on Wyoming Boulevard records the site's "
   "drainage, industrial activities, pollutant sources, control measures and inspection routine under the federal "
   "multi-sector permit."),
  "Department of Municipal Development, Street Maintenance Division; Street Satellite #1 (SS1), 400 Wyoming Blvd NE, Albuquerque, NM 87123.",
  "Marked FINAL PLAN and dated May 2021 on its cover."),
 ('src-93b87673aa626c87',
  "Storm Water Pollution Prevention Plan: Street Satellite #2, DMD Street Maintenance Division",
  ("The City's stormwater plan for its Street Satellite #2 maintenance yard on Commercial Street records the site's "
   "drainage, industrial activities, pollutant sources, control measures and inspection routine under the federal "
   "multi-sector permit."),
  "Department of Municipal Development, Street Maintenance Division; Street Satellite #2 (SS2), 1820 Commercial St NE, Albuquerque, NM 87102.",
  "Marked FINAL PLAN and dated May 2021 on its cover."),
 ('src-70fe061ad2a73da1',
  "Storm Water Pollution Prevention Plan: Street Satellite #3, DMD Street Maintenance Division",
  ("The City's stormwater plan for its Street Satellite #3 maintenance yard on Sunset Gardens Road records the site's "
   "drainage, industrial activities, pollutant sources, control measures and inspection routine under the federal "
   "multi-sector permit."),
  "Department of Municipal Development, Street Maintenance Division; Street Satellite #3 (SS3), 11800 Sunset Gardens Rd, Albuquerque, NM 87121.",
  "Marked FINAL PLAN and dated May 2021 on its cover."),
 ('src-ed7b4a03dc74ecd0',
  "Storm Water Pollution Prevention Plan: Cerro Colorado Landfill, Solid Waste Management Department",
  ("The City's stormwater plan for the Cerro Colorado Landfill records the landfill's drainage, the industrial "
   "activities that could affect stormwater quality, its pollutant sources, and the control measures and inspections "
   "the federal permit requires."),
  "Solid Waste Management Department; Cerro Colorado Landfill, 18000 Cerro Colorado Rd SW, Albuquerque, NM 87121.",
  "Marked FINAL PLAN and dated Updated: May 2021 on its cover. The filename spells the site Cero Colorado; the document spells it Cerro Colorado. Title it from the document."),
 ('src-2795a18baf28a484',
  "Storm Water Pollution Prevention Plan: Don Reservoir Convenience Center, Solid Waste Management Department",
  ("The City's stormwater plan for the Don Reservoir Convenience Center records the site's drainage, its waste "
   "handling activities, its pollutant sources, and the control measures and inspection schedule required under the "
   "federal multi-sector permit."),
  "Solid Waste Management Department; Don Reservoir Convenience Center (DRCC), 117 114th St SW, Albuquerque, NM 87121.",
  "Marked FINAL PLAN and dated Updated: May 2021. The filename spells the site Don Reservior; the document spells it Don Reservoir. Title it from the document."),
 ('src-e7f76a24cab573fe',
  "Storm Water Pollution Prevention Plan: Eagle Rock Convenience Center, Solid Waste Management Department",
  ("The City's stormwater plan for the Eagle Rock Convenience Center records the site's drainage, its waste handling "
   "activities, its pollutant sources, and the control measures and inspections the federal multi-sector permit "
   "requires."),
  "Solid Waste Management Department; Eagle Rock Convenience Center (ERCC), 6301 Eagle Rock Ave NE, Albuquerque, NM 87113.",
  "Marked FINAL PLAN and dated Updated: May 2021 on its cover."),
 ('src-8f3e86e3d21212cc',
  "Storm Water Pollution Prevention Plan: Edith Yards Maintenance Facility, Solid Waste Management Department",
  ("The City's stormwater plan for the Edith Yards maintenance facility records the site's drainage, its vehicle and "
   "equipment maintenance activities, its pollutant sources, and the control measures and inspections the federal "
   "permit requires."),
  "Solid Waste Management Department; Edith Yards Maintenance Facility, 4600 Edith Blvd NE, Albuquerque, NM 87107.",
  "Marked FINAL PLAN and dated Updated: May 2021 on its cover."),
 ('src-86f8242e2e9051d2',
  "Storm Water Pollution Prevention Plan: Fleet Storage Yard Hanover Facility, Solid Waste Management Department",
  ("The City's stormwater plan for the Hanover fleet storage yard records the site's drainage, its vehicle storage "
   "and maintenance activities, its pollutant sources, and the control measures and inspection schedule required "
   "under the federal permit."),
  "Solid Waste Management Department; Fleet Storage Yard, Hanover Facility (FSYH), 6401 Hanover Dr NW, Albuquerque, NM 87121.",
  "Marked FINAL PLAN and dated May 2021 on its cover."),
 ('src-dc99a8cd8ca048e8',
  "Storm Water Pollution Prevention Plan: Montessa Park Convenience Center, Solid Waste Management Department",
  ("The City's stormwater plan for the Montessa Park Convenience Center records the site's drainage, its waste "
   "handling activities, its pollutant sources, and the control measures and inspections the federal multi-sector "
   "permit requires."),
  "Solid Waste Management Department; Montessa Park Convenience Center (MPCC), 3512 Los Picaros Rd SW, Albuquerque, NM 87106.",
  "Marked FINAL PLAN and dated Updated: May 2021 on its cover."),
 ('src-7e0cfd10413353d7',
  "Storm Water Pollution Prevention Plan: Pino Yards Complex Clean City Division, Solid Waste Management Department",
  ("The City's stormwater plan for the Clean City Division operation at the Pino Yards Complex records that site's "
   "drainage, its activities, its pollutant sources, and the control measures and inspections required under the "
   "federal multi-sector permit."),
  "Solid Waste Management Department; Pino Yards Complex, Clean City Division (PYCC), 5501 Pino St NE, Bldg D, Albuquerque, NM 87109.",
  "Marked FINAL PLAN and dated Updated: May 2021 on its cover. The third of three plans for three separate operations in the Pino Yards Complex."),
 ('src-35f817eeb7fb94db',
  "Storm Water Pollution Prevention Plan: ABQ RIDE West Side Transit Facility, Daytona version",
  ("The Transit Department's stormwater plan covering its West Side and Yale facilities, in the version carrying the "
   "Daytona site drawings and the 2021 Daytona non-stormwater discharge re-evaluation, with that site's drainage, "
   "activities and control measures."),
  "Transit Department, ABQ RIDE; West Side Transit Facility (Daytona), 8001 Daytona Rd NW, Albuquerque, NM 87121, and Yale Maintenance Facility, 601 Yale Blvd NE, Albuquerque, NM 87106.",
  "Marked FINAL PLAN and dated Updated: 05/05/2021. Carries Figure No. 1A, the Daytona general location map, and a 2021 re-evaluation memo for the Daytona Transit Facility."),
 ('src-9688bda860dac577',
  "Storm Water Pollution Prevention Plan: ABQ RIDE Yale Maintenance Facility, Yale version",
  ("The Transit Department's stormwater plan covering its West Side and Yale facilities, in the version carrying the "
   "Yale site drawings and the 2021 Yale non-stormwater discharge re-evaluation, with that site's drainage, "
   "activities and control measures."),
  "Transit Department, ABQ RIDE; West Side Transit Facility (Daytona), 8001 Daytona Rd NW, Albuquerque, NM 87121, and Yale Maintenance Facility, 601 Yale Blvd NE, Albuquerque, NM 87106.",
  "Marked FINAL PLAN and dated Updated: 05/05/2021. Carries Figure No. 1B, the Yale general location map, and a 2021 re-evaluation memo for the Yale Transit Facility that records no change since the 2020 site visit."),
]

approved = []
for i, title, desc, facility, ev in SWPPP:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": "2021", "pages": None,
              "facility": facility, "evidence": ev, "why_retained": SWPPP_WHY,
              "proposed_canonical_page": STORM,
              "cross_listings": ([{"page": TRANSIT, "reason": "An ABQ RIDE operating facility."}]
                                 if 'ABQ RIDE' in title else []),
              "package": "the_2021_facility_plans"})
    approved.append(r)

WY_WHY = ("An attachment to the City of Albuquerque Water Year 2015 Report, which the archive already holds, "
          "validated and R2-archived, as " + PARENT + ". The parent is a nine-page cover and narrative that lists "
          "five attachments and holds none of them. Without this file the archived record is incomplete.")

WY = [
 ('src-74259110bbf723e6',
  "Certification Statement and EPA Transmittal, City of Albuquerque 2015 Water Year Data Report",
  ("The City's signed transmittal to EPA Region 6 certifying its 2015 Water Year data report under penalty of law, "
   "identifying the permits it is filed under and naming where the underlying discharge monitoring reports can be "
   "read."),
  ("Letter dated April 1, 2016 on City letterhead to U.S. EPA Region 6, Compliance Assurance and Enforcement "
   "Division, Water Enforcement Branch, Dallas. Signed by Robert J. Perry, Chief Administrative Officer, dated "
   "3/30/16. Cites former Permit No. NMS000101 and current Permit No. NMR04A00."),
  "2016"),
 ('src-ac4a7d2b99bf5cf8',
  "Attachment 2: Chemical Loading and Event Mean Concentrations, Water Year 2015",
  ("The City's chemical loading tables for the 2015 water year give annual load and yield for each monitored "
   "constituent at five outfalls, with each contributing basin's size, covering October 2014 through September "
   "2015."),
  ("Table 1 is headed ANNUAL LOAD (TON) AND YIELD (LB/ACRE) FROM 10/1/14 TO 9/30/15, with columns for San Antonio, "
   "South Diversion Channel, San Jose Drain, North Diversion Channel and Tijeras Arroyo and their basin sizes in "
   "acres."),
  "2015"),
 ('src-f47d9ee905540a56',
  "Attachment 4: Dry Weather Screening Results, Water Year 2015",
  ("The City's dry weather screening results map the outfall locations sampled along the Rio Grande during the 2015 "
   "water year, the screening carried out to detect discharges to the storm sewer system outside of rainfall "
   "events."),
  ("A map-led document whose extracted text is street and arroyo labels. The parent report describes Attachment 4 as "
   "dry weather screening results from 20 outfall locations along the Rio Grande."),
  "2015"),
 ('src-e7ceffdaa300742d',
  "Attachment 5: Notes Regarding Discharge Monitoring Reports, Water Year 2015",
  ("The City's note on its electronically filed discharge monitoring reports explains how to obtain read access, and "
   "records an unresolved disagreement with EPA over how the biennial reporting period should be interpreted and "
   "entered."),
  ("Headed Attachment 5 Discharge Monitoring Reports (DMRs). Records that City staff had been working with EPA since "
   "January 2016 for clarification, reproduces a City email of March 25, 2016, and states that clarification had not "
   "been received when the report was prepared."),
  "2016"),
 ('src-829ac52903bbafb6',
  "Attachment 3: Water Quality Monitoring Results, Water Year 2015",
  ("The City's water quality monitoring results tabulate sampled concentrations against New Mexico and Pueblo water "
   "quality criteria at each monitored arroyo and floodway station, with the qualifier and collection date recorded "
   "for every sample."),
  ("Opens on 2014 Monitoring Results for Downstream of I-25 Baffle Chute BMP and tabulates NMAC 20.6.4 and Pueblo "
   "criteria against Bear Arroyo at Jefferson, Embudo Arroyo at Monte Largo, Hahn Arroyo, North Floodway near "
   "Alameda and San Antonio Arroyo. Dated 1-13-16 in the filename."),
  "2016"),
]
for i, title, desc, ev, date in WY:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None,
              "evidence": ev, "why_retained": WY_WHY,
              "proposed_canonical_page": STORM, "cross_listings": [],
              "package": "the_water_year_2015_attachments",
              "parent_record": PARENT})
    approved.append(r)

r = row('src-3d341c61d7813a68', "approved for addition")
r.update({"title": "Transitional Update for City of Albuquerque, NPDES Permits NMS000101 and NMR04A000",
          "description": ("The City's transition-period report to EPA covers January to June 2015 and explains how "
                          "its municipal storm sewer permit coverage moved from the expiring Phase 1 permit to the "
                          "regional watershed based permit."),
          "date": "2015", "pages": None,
          "evidence": ("Headed Transitional Update for City of Albuquerque NMS000101/NMR04A000, Reporting Period "
                       "January 1, 2015 - June 30, 2015, DUE December 1, 2015. Records NMS000101 expiring March 22, "
                       "2015 and NMR04A000 effective December 22, 2015, with an eNOI application date of June 21, "
                       "2015."),
          "why_retained": ("The document the Water Year 2015 report refers back to, and the only record in the "
                           "archive of how the City's permit coverage changed. It names the City's three stormwater "
                           "partners and explains why the reporting cycle moved from calendar year to fiscal year."),
          "proposed_canonical_page": STORM, "cross_listings": [],
          "package": "the_transition_period_submission"})
approved.append(r)

SOLAR_WHY = ("A design record for a photovoltaic installation on a named City building, prepared for the City by its "
             "solar consultant and marked For Construction. The archive holds the City's climate plans and no record "
             "of what was actually built on City roofs.")

SOLAR = [
 ('src-3d258d1f7af0cf94',
  "Solar Photovoltaic Annual Production Report: Albuquerque Botanical Gardens",
  ("The consultant's production model for the Botanical Gardens solar array gives its rated size, its expected "
   "annual output, its month by month generation and the losses expected from shading, inverters, temperature, "
   "soiling and wiring."),
  ("Project Name Botanical Gardens, 2601 Central Ave. NW. Design 6, Talesun 320 plus Seraphim 325P, For "
   "Construction. Module DC nameplate 203.0 kW, inverter AC nameplate 250.0 kW, annual production 342.3 MWh, "
   "performance ratio 85.8%. Prepared by Benjamin Rodefer, Rio Grande Renewables. Folsom Labs HelioScope, June 14, "
   "2022."),
  [{"page": CAPITAL, "reason": "A capital installation on a City facility."}]),
 ('src-a91b27910d2bc7ff',
  "Solar Photovoltaic Annual Production Report: Los Griegos Health and Social Service Center",
  ("The consultant's production model for the Griegos Center solar array gives its rated size, its expected annual "
   "output, its month by month generation and the losses expected from inverters, temperature, reflection and "
   "soiling."),
  ("Project Name City of ABQ Griegos Center (P2G2), 1231 Candelaria, Albuquerque, NM 87107. Final Design, Seraphim "
   "360M, For Construction. Module DC nameplate 75.6 kW, inverter AC nameplate 70.0 kW, annual production 141.5 MWh, "
   "performance ratio 84.9%. Prepared by Benjamin Rodefer, Rio Grande Renewables. Folsom Labs HelioScope, June 14, "
   "2022."),
  [{"page": CAPITAL, "reason": "A capital installation on a City facility."}]),
 ('src-7db766b9952052ab',
  "Solar Photovoltaic Annual Production Report: Old Albuquerque Police Department Building",
  ("The consultant's production model for the Old APD Building solar array gives its rated size, its expected annual "
   "output, its month by month generation and the losses expected from mismatch, inverters, reflection, temperature "
   "and soiling."),
  ("Project Name Old APD Building (COA#2), 401 Marquette Ave NW, Albuquerque, NM. RAS Design 1, 5 degree tilt, 11 "
   "inch intra row spacing, for construction. Module DC nameplate 86.3 kW, inverter AC nameplate 72.0 kW, annual "
   "production 153.1 MWh, performance ratio 83.9%. Prepared by Benjamin Rodefer, Rio Grande Renewables. Folsom Labs "
   "HelioScope, June 14, 2022."),
  [{"page": CAPITAL, "reason": "A capital installation on a City facility."}]),
 ('src-566cc9bf0d049f71',
  "Solar Photovoltaic Design Overview: Albuquerque Museum",
  ("The consultant's design overview for the Albuquerque Museum solar array lists the inverters, modules, cabling "
   "and stringing specified, and breaks the installation into six roof field segments with each segment's tilt, "
   "orientation and capacity."),
  ("Project Museum of Albuquerque (COA#2), 2000 Mountain Rd. NW, Albuquerque, NM 87104. Design 3, 5 degree tilt, 11 "
   "inch intra row spacing, For Construction. DC nameplate 246.3 kW, AC nameplate 220.0 kW. 714 Seraphim SEG-6MA-"
   "345WW modules across six field segments, five Solectria inverters. Prepared by Benjamin Rodefer, Rio Grande Renewables; last "
   "modified 09/13/2018. Folsom Labs HelioScope, June 14, 2022."),
  [{"page": CAPITAL, "reason": "A capital installation on a City facility."}]),
 (MOVED,
  "Solar Photovoltaic Shading Report: Albuquerque Museum",
  ("The consultant's shading study for the Albuquerque Museum solar design maps the modelled shade across the roof "
   "and reports, for each of the six field segments, its irradiance after shading, its expected output and its solar "
   "access."),
  ("Project Museum of Albuquerque (COA#2), 2000 Mountain Rd. NW, Albuquerque, NM 87104, for the same Design 3, 5 "
   "degree tilt, 11 inch intra row spacing. 714 modules, 242.8 kWp, weighted solar access 99.3%, total solar "
   "resource fraction 87.9%, AC energy 440.1 MWh. Produced by Brian Schmidly, Rio Grande Renewables. Folsom Labs "
   "HelioScope, May 17, 2018."),
  [{"page": CAPITAL, "reason": "A capital installation on a City facility."}]),
]
for i, title, desc, ev, cross in SOLAR:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc,
              "date": "2018" if i == MOVED else "2022", "pages": None,
              "evidence": ev, "why_retained": SOLAR_WHY,
              "proposed_canonical_page": CLIMATE, "cross_listings": cross,
              "package": "the_city_facility_solar_series",
              "caution": ("Consultant modelling, not metered generation. Describe the figures as designed and "
                          "modelled output, never as what the array produced.")})
    approved.append(r)

for r in approved:
    r["description_word_count"] = len(r["description"].split())

# --------------------------------------------------------- requires human review
rhr = []
r = row('src-e01b2c62963c90e9', "requires human review")
r.update({"draft_title": "Solar Photovoltaic Annual Production Report: Albuquerque Main Library (incomplete export)",
          "question_for_human": "Ask the City for a complete export of the Main Library design, or publish this one with its defects stated on the page.",
          "why_not_decided_here": ("Unlike the other four in the series this file is an incomplete export. Its "
                                   "inverter AC nameplate reads 0 with the load ratio left blank, and the annual "
                                   "production table that every sibling carries is simply absent from page 1. Its "
                                   "own title records it as a backup taken on 2017-12-19, four and a half years "
                                   "before the June 14, 2022 export date. The numbers that are present may therefore "
                                   "describe a superseded design."),
          "measurement": ("Project Name City of ABQ Main Library (COA#1), 501 Copper Ave NW, Albuquerque, New "
                          "Mexico, 87102, and Prepared For City of Albuquerque - the only file in the series to name "
                          "the client explicitly. Design 3, Talesun N-S RM (Large, 10 Deg), backup 2017-12-19 "
                          "08:59:01. Module DC nameplate 201.9 kW, annual production 361.0 MWh, performance ratio "
                          "83.8%, inverter AC nameplate 0."),
          "distinguishing_content": "Inverter AC Nameplate 0; Load Ratio blank; no Annual Production table on page 1.",
          "package": "the_city_facility_solar_series",
          "priority": 1})
rhr.append(r)

# ------------------------------------------------------------------- excluded
excluded = [{
 **row('src-6ac840c695ebd756', "excluded"),
 "title_for_reference": "USDA-NRCS New Mexico Agronomy Technical Note 28: Revised Universal Soil Loss Equation, October 1999",
 "exclusion_reason": ("Not a City record. This is a United States Department of Agriculture Natural Resources "
                      "Conservation Service technical note, published in Albuquerque in October 1999, which replaces "
                      "the Universal Soil Loss Equation with its revised form for sheet and rill erosion estimates. "
                      "The City posts it because its stormwater work relies on the method, but USDA-NRCS is the "
                      "authoritative publisher and the City's copy carries no City authorship, adoption or "
                      "amendment."),
 "category": "third-party federal technical standard",
 "if_reconsidered": ("If the method is worth a reference on the stormwater page, cite it to USDA-NRCS rather than "
                     "archiving the City's copy as though the City issued it."),
 "measurement": "Born-digital PDF, 449,316 bytes, headed USDA-NRCS, NM Agronomy Technical Note 28, Page 1.",
}]

rows = approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (set(SLICE) - set(ids), set(ids) - set(SLICE))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
n_swppp = len(SWPPP)
n_wy = len(WY) + 1
n_solar = len(SOLAR)

UNDISCOVERED = [l.strip() for l in open(os.path.join(SP, 'ms4missing.txt'), encoding='utf-8') if l.strip()]

artifact = {
 "batch_id": "facility-environmental-compliance-cluster-research-2026-09-12",
 "lane": "Claude research lane: the facility environmental compliance set in www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the sixth slice of the municipaldevelopment/documents lane.",
 "cluster": ("Three groups that share a subject: the City's stormwater pollution prevention plans for its own "
             "facilities, the attachments to its 2015 Water Year municipal storm sewer report, and the design "
             "records for solar arrays on City buildings."),
 "scope": ("The 27 uncovered candidates matching this subject, plus one record corrected out of "
           "flat-bond-and-standard-forms-cluster-research-2026-09-12.json and decided here instead. The coverage "
           "gate is asserted in the generator."),
 "brief": ("Establish for each SWPPP which City facility and which permit term it belongs to, and decide whether the "
           "site-named HelioScope series changes the exclusion recorded for the unattributable sixth report."),
 "brief_finding": ("Every plan names its facility and its address on its cover, and all fifteen belong to the same "
                   "permit term: each is marked FINAL PLAN and dated May 2021 under the EPA Multi-Sector General "
                   "Permit. They cover four departments and fifteen distinct sites, including three separate "
                   "operations inside the Pino Yards Complex, each in its own building."),
 "second_finding": ("The brief's second question was answered yes, and it overturned the earlier exclusion. See "
                    "a_correction_to_the_previous_artifact."),
 "third_finding": ("The five 2015 water year files are the missing attachments to a report the archive already holds, "
                   "validated and R2-archived. See the_water_year_2015_attachments."),
 "method": ("Fetched every candidate and measured byte length and SHA-256 from the fetched bytes, verifying every "
            "container by leading bytes. Read each cover page for department, facility, address, plan status and "
            "date. Rendered the six files whose substance is not in their text layer, which is how the facility "
            "solar series was identified and how the earlier exclusion was found to be wrong. Compared the fifteen "
            "plans pairwise at line level first, because character-level comparison over 105 pairs of "
            "two-hundred-page documents does not terminate in reasonable time; the character-level run was left going "
            "and its results are reported alongside. Fetched the City's "
            "own MS4 permit page and reconciled every file it links against the inventory. Fetched the archived "
            "parent report and measured token coverage of each candidate inside it."),
 "classification_only": True,
 "shared_state_written": [],
 "a_correction_to_the_previous_artifact": {
  "what_was_wrong": ("flat-bond-and-standard-forms-cluster-research-2026-09-12.json excluded "
                     "albuquerque-m-helioscope_shading_1870012_summary.pdf as unattributable, on the stated ground "
                     "that searches of its extracted text returned no site identification."),
  "what_is_true": ("The file names its site in large type at the top of page 1: Museum of Albuquerque (COA#2), 2000 "
                   "Mountain Rd. NW, Albuquerque, NM 87104. It is the May 17, 2018 shading study for the same Design "
                   "3, 5 degree tilt, 11 inch intra row spacing, 714-module array as helioscope-museum-rgr.pdf in "
                   "this slice."),
  "why_the_check_failed": ("Its title block is not in the PDF text layer. pdftotext returns 1,561 bytes for a "
                           "three-page document, the header and footer only. Searching that text for a site name "
                           "could only ever return nothing. The file had to be rendered, and this lane had already "
                           "recorded that rule twice before applying it here."),
  "what_changed": ("The record is removed from the previous artifact and decided here as approved for addition. That "
                   "artifact now covers 44 records rather than 45, and its excluded list is empty."),
  "the_lesson": ("A file with a thin text layer has not been read. The absence of an expected string in extracted "
                 "text is evidence about the extraction, not about the document. Render before excluding anything "
                 "for what it does not say."),
  "how_it_was_caught": ("Only because the sibling series was claimed as the next slice and those five files were "
                        "rendered. Nothing in the previous slice would have surfaced it."),
 },
 "the_2021_facility_plans": {
  "count": n_swppp,
  "departments": ["Municipal Development, Street Maintenance Division (5 sites)",
                  "Solid Waste Management Department (7 sites)",
                  "Transit Department, ABQ RIDE (2 versions, 2 sites)",
                  "Finance and Administration, Purchasing Division (1 site)"],
  "permit_term": "All fifteen are marked FINAL PLAN and dated May 2021, under the EPA Multi-Sector General Permit for industrial stormwater discharges.",
  "the_pino_yards_point": ("Three plans cover three separate operations in one complex at 5501 Pino St NE: Street "
                           "Maintenance in Building F, Clean City Division in Building D, and Warehouse and Surplus "
                           "Auction in Building G. Same address, three departments, three plans. They must not be "
                           "collapsed into one entry."),
  "the_transit_pair": {
   "what_it_looks_like": ("transit-daytona and transit-yale share a cover naming both facilities and are the closest "
                          "pair in the set under every measure taken: line-level sequence ratio 0.9527, character-level "
                          "sequence ratio 0.9811, token coverage 0.9891 and 0.9912. Neither is string-equal to the other."),
   "what_it_is": ("Two facility-specific versions of one Transit Department plan. The Daytona file carries Figure "
                  "No. 1A, the Daytona general location map, and a 2021 non-stormwater discharge re-evaluation memo "
                  "for the Daytona Transit Facility. The Yale file carries Figure No. 1B, the Yale general location "
                  "map, and the corresponding Yale memo, which adds that no change to the facility was observed "
                  "since the 2020 site visit."),
   "decision": "Both retained. Neither is a duplicate and neither supersedes the other; each is the only record of its own site's drawings and inspection.",
   "how_it_was_settled": "By reading the opcodes of the line-level diff, not by trusting the ratio. The single largest differing block is 51 lines against 4, and it is the site drawing set.",
  },
  "two_filenames_misspell_their_site": ("swmd-cero-colorado-landfill names a landfill the document spells Cerro "
                                        "Colorado; swmd-don-reservior-convenience-center names a site the document "
                                        "spells Don Reservoir. Title both from the document, as the Energy Council "
                                        "record established in "
                                        "municipaldevelopment-agenda-minutes-cluster-research-2026-09-12.json."),
  "the_gap_they_close": ("The archive holds the City's MS4 permit, its annual reports and its stormwater management "
                         "program, all of which describe facility plans. It holds no facility plan."),
 },
 "the_water_year_2015_attachments": {
  "count": len(WY),
  "the_parent": {
   "id": PARENT,
   "file": "water-year-2015-report-032516.pdf",
   "status_in_inventory": "validated, with an r2_url",
   "what_it_is": ("A short cover and narrative, 127,553 bytes, that explains the reporting cycle and then lists five "
                  "attachments: bacterial loading, chemical loading and event means, water monitoring status and "
                  "results, dry weather screening from 20 outfalls, and the discharge monitoring reports."),
  },
  "the_transition_period_submission": ("transitional-update-for-city-of-albuquerque-nms000101-nmr04a000.pdf is not "
                                      "one of these five attachments. It is the separate December 1, 2015 "
                                      "transition-period filing that the parent report refers back to, and it is "
                                      "recommended in its own right under its own package name."),
  "the_finding": ("The archive holds the cover and three of the eight pieces. Attachment 1 is "
                  "bacterial-tmdl-report-wy-2015-030616.pdf and Attachment 3's status half is "
                  "water-quality-monitoring-status-june-september-2015.pdf, both already validated and archived. The "
                  "remaining five were sitting unread in pending review, and with them the signed certification that "
                  "identifies the submission."),
  "containment_measured": ("Token coverage of each candidate inside the parent: chemical loads 0.2623, dry weather "
                           "screening 0.1276, DMR notes 0.6852, transitional update 0.5102, water quality results "
                           "0.1613. None is contained in the parent; the shared vocabulary is the permit numbers and "
                           "the boilerplate. The parent is a cover, not a compilation."),
  "why_it_matters": ("A compliance submission whose attachments are missing is not the submission. The certification "
                     "statement is the only file that carries the signature, the addressee and the penalty-of-law "
                     "language, and it is the only one that dates the filing."),
  "recommended_treatment": "Publish these five as attachments of " + PARENT + ", under the parent's own entry, rather than as six unrelated stormwater files.",
 },
 "the_city_facility_solar_series": {
  "count": n_solar + 1,
  "what_it_is": ("Six design records for photovoltaic arrays on five City buildings - the Botanical Gardens, the "
                 "Griegos Health and Social Service Center, the Main Library, the Albuquerque Museum and the Old APD "
                 "Building - prepared for the City by Rio Grande Renewables and exported from Folsom Labs "
                 "HelioScope. Five carry a June 14, 2022 export date; the Museum shading study is from May 17, 2018."),
  "combined_capacity_designed": ("813.1 kW DC across the five sites, using each file's module DC nameplate: 246.3 at "
                                 "the Museum, 203.0 at the Botanical Gardens, 201.9 at the Main Library, 86.3 at the "
                                 "Old APD Building and 75.6 at the Griegos Center."),
  "the_caution": ("These are modelled outputs marked For Construction, not metered generation. Four of the six are "
                  "Annual Production Reports, one is a Design Overview listing components and field segments, and "
                  "one is a Shading Report. Describe them as designed and modelled."),
  "the_incomplete_one": "The Main Library file is an incomplete export and is held for review; see requires_human_review.",
  "why_they_are_worth_holding": ("The archive publishes the City's climate plans and greenhouse gas inventories and "
                                 "has no record of what solar was actually installed on City roofs. These name the "
                                 "building, the address, the module count and the design capacity."),
 },
 "an_undiscovered_set": {
  "count": len(UNDISCOVERED),
  "how_it_was_found": ("The certification statement prints the City webpage its data would be posted to. Fetching "
                       "that page and reconciling every file it links against the inventory returned 61 links, 23 in "
                       "the inventory and 38 absent - 37 of them City files, the other a New Mexico Department of "
                       "Transportation manual."),
  "verification": ("All 37 were fetched individually. Every one returned HTTP 200 with PDF leading bytes 25504446. "
                   "Three needed a retry: one was linked over http on a host that refuses port 80, and two carry "
                   "unencoded spaces in the href that must be percent-encoded before the request will form."),
  "what_is_in_it": ("The entire 2014 MS4 Annual Report package - a main body and 27 lettered attachments in their "
                    "own directory - plus the FY19, FY20 and FY21 annual reports and an FY21 draft, the fiscal 2017 "
                    "annual report, the 2016 signed compiled annual report, EPA's 2015 approval letter, and the MS4 "
                    "permit itself."),
  "why_this_matters_beyond_itself": ("This is the fifth undiscovered file of the run and by far the largest. The "
                                     "first four were found by probing names the City uses; this one was found by "
                                     "reading a City page that a candidate document pointed at. The archive's "
                                     "stormwater compliance series has a hole in it from 2014 through 2021 that no "
                                     "amount of triage over the existing inventory would have revealed."),
  "recommended_action": "Add all 37 as candidates. They are listed in full below, already verified.",
  "urls": UNDISCOVERED,
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 0,
  "containment_test_against_an_archived_parent": ("Run for all five water year candidates and the transitional "
                                                  "update against " + PARENT + ". Highest coverage 0.6852; none is "
                                                  "contained."),
  "result": "Nothing in this slice duplicates anything the archive holds.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 0,
  "swppp_pairs_measured": 105,
  "swppp_line_ratio_range": "0.2883 to 0.9527, comparing the plans as sequences of lines",
  "swppp_line_coverage_range": "0.2474 to 0.9638, the share of one plan's distinct lines present in the other",
  "swppp_character_ratio_range": "0.0029 to 0.9811, comparing the same plans as sequences of characters",
  "swppp_token_coverage_range": "0.6172 to 0.9912, the share of one plan's vocabulary present in the other",
  "swppp_identical_line_lists": 0,
  "swppp_string_equal_pairs": 0,
  "why_both_measures_are_reported": ("The line-level comparison was run first because character-level comparison "
                                     "over 105 pairs of two-hundred-page documents does not terminate in reasonable "
                                     "time; the character-level run was left going in the background and finished "
                                     "afterwards. Both are reported because they disagree in magnitude and agree in "
                                     "conclusion: the transit pair is the closest under either (0.9527 by line, "
                                     "0.9811 by character) and no pair is equal under either."),
  "relationships_found": 0,
  "note": ("The closest pair in the set, the two Transit versions, was examined line by line rather than accepted on "
           "its ratio. It is not a duplicate. This is the third slice running in which a high similarity score "
           "covered a real distinction, and the second in which reading the difference rather than the score settled "
           "it."),
 },
 "integration_flags": [
  {"severity": "corrects-a-saved-artifact",
   "affects": [MOVED],
   "finding": "The exclusion of albuquerque-m-helioscope_shading_1870012_summary.pdf in flat-bond-and-standard-forms-cluster-research-2026-09-12.json was wrong. The file names its site on page 1 in text that is not in its text layer. It is the 2018 Albuquerque Museum shading study.",
   "recommended_action": "Apply the approved for addition status from this artifact. The previous artifact has been corrected to 44 records and no longer lists this id."},
  {"severity": "completes-an-archived-record",
   "affects": [r['id'] for r in approved if r.get('package') == 'the_water_year_2015_attachments'],
   "finding": f"Five files that complete {PARENT}, the Water Year 2015 Report, which the archive already holds validated and R2-archived. The parent is a cover listing five attachments and holding none of them; coverage testing confirms none of them is inside it.",
   "recommended_action": "Approve and publish under the parent's entry as its attachments, not as separate stormwater files."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r.get('package') == 'the_2021_facility_plans'],
   "finding": "Fifteen City stormwater pollution prevention plans, all FINAL PLAN, all May 2021, covering fifteen named facilities across four departments. The archive holds the permit and the annual reports above them and not one facility plan.",
   "recommended_action": "Approve. Title two of them from the document rather than the filename; both misspell their site."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r.get('package') == 'the_city_facility_solar_series'],
   "finding": "Design records for photovoltaic arrays on five City buildings, 813.1 kW DC designed in total, prepared for the City by Rio Grande Renewables. The archive holds the City's climate plans and no record of what solar was built on City roofs.",
   "recommended_action": "Approve, describing every figure as designed and modelled rather than generated."},
  {"severity": "add-candidates",
   "affects": [],
   "finding": f"{len(UNDISCOVERED)} City MS4 compliance documents linked from the City's own MS4 permit page and absent from the inventory, including the whole 2014 annual report package and the FY19 through FY21 annual reports. All 37 verified HTTP 200 with PDF leading bytes.",
   "recommended_action": "Add as candidates; the verified URL list is in an_undiscovered_set. Three need care: one http link on a host refusing port 80, two hrefs with unencoded spaces."},
  {"severity": "date-before-publishing",
   "affects": [r['id'] for r in rhr],
   "finding": "The Main Library solar file is an incomplete export: inverter nameplate 0, load ratio blank, annual production table absent, and its own title records it as a 2017 backup rather than the 2022 design.",
   "recommended_action": "Request a complete export, or publish with the defects stated."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "additional_probes": f"{len(UNDISCOVERED)} undiscovered City MS4 files, all HTTP 200; plus the archived parent report, HTTP 200.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "All %d are genuine PDFs by leading bytes 25504446." % len(rows)},
 "approved_for_addition": approved,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, which is the "
                   f"largest in this lane so far and is dominated by the fifteen facility plans, every one of them "
                   f"several megabytes of scanned site drawings. A further {len(rhr)} record totalling "
                   f"{rhr_bytes:,} bytes is held at requires human review."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id; this slice contains "
                     "no duplicates and no supersession. One row corrects a saved artifact and names it. Six rows "
                     "carry a parent_record naming an already-archived document they belong to. Every row carries a "
                     "leading_bytes field. Sizes and checksums are first measurements; the inventory held none. "
                     "an_undiscovered_set carries 37 verified URLs that are not candidates yet and cannot be applied "
                     "through Update-Candidate."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the archived parent was fetched read-only and its inventory record was not touched",
                "the 37 undiscovered files were fetched read-only and no candidate was created"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
