"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. Ninth and final slice of the municipaldevelopment/documents
lane: everything left at the flat level.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\municipaldevelopment-flat-remainder-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md8')

CLIMATE = 'content/city-data/climate-environment.md'
CAPITAL = 'content/city-data/capital-spending.md'
DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
SPEED = 'content/transportation/roadway-projects/speed-management.md'
BIKE = 'content/transportation/bicycling/bike-plans.md'
BIKEIDX = 'content/transportation/bicycling/_index.md'
TRANSIT = 'content/transportation/transit/abq-ride.md'
STORM = 'content/public-works/stormwater-drainage.md'
FACIL = 'content/public-works/city-facilities.md'
CAPPROJ = 'content/public-works/capital-projects.md'
PARKSREC = 'content/public-works/parks-recreation.md'
MAPS = 'content/maps-data/maps.md'

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

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML', '3c21444f': 'HTML'}

LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
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


SOLAR_WHY = ("A design record for a photovoltaic installation on a named City building. The site, address, rated "
             "capacity and modelled output are printed at the top of page 1 in text that is not in the PDF text "
             "layer, so every one of these was read by rendering.")
SOLAR_CAUTION = ("Consultant modelling, not metered generation. Describe the figures as designed and modelled "
                 "output, never as what the array produced.")

# id, title, date, kw, site, evidence, canonical, crosses
SOLAR = [
 ('src-365f0d791febb5b5', "Solar Photovoltaic Annual Production Report: Barelas Senior Center", "2022", "76.5",
  "COA Senior Center, 714 7th Street SW",
  ("Titled COA Barelas Senior Center 76.5 kW over COA SENIOR CENTER, 714 7th street SW Albuquerque, NM. Module DC "
   "nameplate 76.5 kW, inverter AC nameplate 86.4 kW, annual production 124.3 MWh, performance ratio 78.7%. "
   "Prepared by Zach Johnson of Solluna Solar. Folsom Labs HelioScope, May 24, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-5e848474ee9ec258', "Solar Photovoltaic Annual Production Report: Cherry Hills Library", "2022", "102.5",
  "COA Cherry Hills Library, 6901 Barstow Street NE",
  ("Titled COA Cherry Hills 102.3 kW over COA Cherry Hills Library, 6901 Barstow St NE. Module DC nameplate 102.5 "
   "kW, inverter AC nameplate 86.4 kW, annual production 168.1 MWh, performance ratio 77.8%. Prepared by Zach "
   "Johnson of Solluna Solar. Folsom Labs HelioScope, May 24, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-75d2d39430666298', "Solar Photovoltaic Annual Production Report: Fire Station 5", "2022", "100.5",
  "Fire Station #5, 123 Dallas Street NE",
  ("Titled 100.5 kW Roof Mount and Carport over Fire Station #5, 123 Dallas St NE. Module DC nameplate 100.5 kW, "
   "inverter AC nameplate 86.4 kW, annual production 162.4 MWh, performance ratio 77.3%. Prepared by Zach Johnson "
   "of Solluna Solar. Folsom Labs HelioScope, May 24, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-8c3b3a07716c9aba', "Solar Photovoltaic Annual Production Report: Fire Station 11", "2022", "35.5",
  "Fire Station #11, 5403 Southern Avenue",
  ("Titled 35.5 kW Roof Mount RM 5 over Fire Station #11, 5403 Southern Ave. Module DC nameplate 35.5 kW, inverter "
   "AC nameplate 28.8 kW, annual production 57.71 MWh, performance ratio 78.7%. Prepared by Zach Johnson of Solluna "
   "Solar. Folsom Labs HelioScope, May 24, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-bcad87d152beeed3', "Solar Photovoltaic Annual Production Report: Fire Station 18", "2022", "29.1",
  "Fire Station #18, 6100 Taylor Ranch NW",
  ("Titled 29.1 kW Roof Mount and Carports over Fire Station #18, 6100 Taylor Ranch NW. Module DC nameplate 29.1 "
   "kW, inverter AC nameplate 28.8 kW, annual production 47.90 MWh, performance ratio 74.7%. Prepared by Zach "
   "Johnson of Solluna Solar. Folsom Labs HelioScope, May 24, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-4c7c531cc2ea2092', "Solar Photovoltaic Annual Production Report: Daytona Transit Facility Carport and Shade Structures", "2022", "471.2",
  "COA ABQ City Transit, 8001 Daytona Road NE",
  ("Titled 471 kW Carport and Shade Structures over COA ABQ CITY TRANSIT, 8001 Daytona Rd NE. Module DC nameplate "
   "471.2 kW, inverter AC nameplate 399.6 kW, annual production 840.7 MWh, performance ratio 84.2%. The largest "
   "array in the series. Prepared by Zach Johnson of Solluna Solar. Folsom Labs HelioScope, May 24, 2022."),
  TRANSIT, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-679f8fb7755e21b3', "Solar Shade Structure Proposal: Daytona Transit Facility", "2019", None,
  "City of Albuquerque (Daytona Transit)",
  ("A Solluna Solar proposal dated 3/5/2019, Prepared For City of Albuquerque (Daytona Transit) with a named City "
   "contact, for Shade Structures (City Transit) using CS3U-375-MB-AG bifacial modules, over an aerial of the "
   "facility with the proposed arrays overlaid. Three years earlier than the production report for the same site "
   "and a different document entirely."),
  TRANSIT, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-ee3fa4b12b013f20', "Solar Photovoltaic Annual Production Report: Cerro Colorado Landfill", "2022", "78.8",
  "Cerro Colorado, 18000 Cerro Colorado Road SW",
  ("Titled Design 1 over C | Cerro Colorado, 18000 Cerro Colorado Rd SW. Module DC nameplate 78.8 kW, inverter AC "
   "nameplate 72.0 kW, annual production 135.8 MWh, performance ratio 84.3%. Prepared by OE Solar. Folsom Labs "
   "HelioScope, May 27, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."},
          {"page": STORM, "reason": "The same landfill whose stormwater plan is recommended in the facility environmental slice."}]),
 ('src-d7f6d2d4ab91ee23', "Solar Photovoltaic Annual Production Report: Los Altos Swimming Pool", "2022", "71.8",
  "Los Altos Swimming Pool, 10300 Lomas Boulevard NE",
  ("Titled Roof Only over Los Altos Swimming Pool, 10300 Lomas Blvd NE. Module DC nameplate 71.8 kW, inverter AC "
   "nameplate 69.0 kW, annual production 126.7 MWh, performance ratio 81.8%. Prepared by OE Solar. Folsom Labs "
   "HelioScope, May 27, 2022."),
  PARKSREC, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-698baaa3ade9ac32', "Solar Photovoltaic Annual Production Report: City Yards, Pino Avenue", "2022", "319.6",
  "City of Albuquerque City Yards, 5501 Pino Avenue NE",
  ("Titled RM5 (copy)1 over City of Albuquerque City Yards, 5501 Pino Ave NE. Module DC nameplate 319.6 kW, "
   "inverter AC nameplate 300.0 kW, annual production 562.7 MWh, performance ratio 82.5%. Prepared by OE Solar. "
   "Folsom Labs HelioScope, May 27, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."},
          {"page": STORM, "reason": "The Pino Yards complex whose three stormwater plans are recommended in the facility environmental slice."}]),
 ('src-83c14ed85d745707', "Solar Photovoltaic Annual Production Report: Albuquerque International Sunport", "2022", "609.8",
  "Sunport, 2200 Sunport Boulevard SE",
  ("Titled Design 1 over C | Sunport, 2200 Sunport Blvd SE. Module DC nameplate 609.8 kW, inverter AC nameplate "
   "600.0 kW, annual production 1.026 GWh, performance ratio 85.0%. The only array in either slice whose modelled "
   "output is measured in gigawatt hours. Prepared by OE Solar. Folsom Labs HelioScope, May 27, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
 ('src-eeaa18493adbc117', "Solar Photovoltaic Annual Production Report: Foothills Area Command", "2022", "72.0",
  "5th Command Center, 12800 Lomas Boulevard NE",
  ("Titled Carport & roof (copy) over 5th Command Center, 12800 lomas blvd NE. Module DC nameplate 72.0 kW, "
   "inverter AC nameplate 75.0 kW, annual production 128.9 MWh, performance ratio 83.9%. The filename calls the "
   "site the Foot Hills APD Substation; the document calls it the 5th Command Center. Prepared by OE Solar. Folsom "
   "Labs HelioScope, May 27, 2022."),
  FACIL, [{"page": CLIMATE, "reason": "Part of the City's renewable generation."}]),
]

approved = []
for i, title, date, kw, site, ev, canon, cross in SOLAR:
    r = row(i, "approved for addition")
    desc = ("The consultant's model for the %s solar array gives its rated size, its expected annual output, its "
            "month by month generation and the losses expected from shading, inverters, temperature, soiling and "
            "wiring." % site.split(',')[0]) if kw else (
           "The consultant's 2019 proposal for solar shade structures at the City's Daytona transit facility sets "
           "out the modules proposed and shows the arrays laid over an aerial view of the site as they would be "
           "built.")
    r.update({"title": title, "description": desc, "date": date, "pages": None,
              "site": site, "evidence": ev, "why_retained": SOLAR_WHY, "caution": SOLAR_CAUTION,
              "group": "city facility solar", "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if kw:
        r["designed_dc_kw"] = float(kw)
    approved.append(r)

# ------------------------------------------------------------ moratorium set
MORATORIUM = [
 ('src-2266ca3b89ee09f0', "2018 Construction Moratorium Map: Balloon Fiesta, State Fair and Holiday Shopping", "2018",
  ("The City's combined 2018 moratorium map shows all three periods in which street excavation is restricted - "
   "Balloon Fiesta, the State Fair and the holiday shopping season - with the affected areas and streets for "
   "each."),
  "Carries three legends on one sheet: 2018 BALLOON FIESTA, 2018 NM STATE FAIR and 2018 HOLIDAY SHOPPING, each with its own moratorium area and moratorium street symbology."),
 ('src-1cc61b8a27655a35', "2018 Balloon Fiesta Construction Moratorium Map", "2018",
  ("The City's map of the streets and areas closed to construction during the 2018 Balloon Fiesta, showing the "
   "arterial and collector routes on which excavation permits will not be issued for the duration."),
  "Titled 2018 BALLOON FIESTA Construction Moratorium, October 1st - October 14th, City of Albuquerque DMD Construction Services Division."),
 ('src-e312b8e6c7c8b733', "2018 New Mexico State Fair Construction Moratorium Map", "2018",
  ("The City's map of the streets and areas closed to construction during the 2018 New Mexico State Fair, showing "
   "where excavation permits will not be issued while the fair is running."),
  "Titled 2018 NM STATE FAIR Construction Moratorium, September 3rd - 16th, City of Albuquerque DMD Construction Services Division."),
 ('src-a27cb77f73d4642a', "2018 Holiday Shopping Construction Moratorium Map", "2018",
  ("The City's map of the streets and areas closed to construction for the 2018 holiday shopping season, marking "
   "the moratorium areas around the shopping districts and the arterial routes serving them."),
  "Titled 2018 HOLIDAY SHOPPING Construction Moratorium, November 21st - January 1st, City of Albuquerque DMD Construction Services Division."),
 ('src-d271ba5b038d8770', "2020 Holiday Shopping Construction Moratorium Map", "2020",
  ("The City's map of the streets and areas closed to construction for the 2020 holiday shopping season, the map "
   "the City's moratorium letter of that year tells contractors to consult for the detail."),
  "Titled 2020 HOLIDAY SHOPPING Construction Moratorium, November 25th - January 1st."),
 ('src-d53579bf075c2b93', "Construction Moratorium Notice to Contractors, Excavators and Plumbers, August 7, 2020", "2020",
  ("The City's letter to contractors announces the 2020 holiday shopping moratorium, cites the ordinance section "
   "it rests on, defines the four restricted areas, and explains how a waiver for an emergency or ongoing project "
   "may be obtained."),
  ("A letter of August 7, 2020 on City letterhead under Mayor Timothy M. Keller, addressed to Contractors, "
   "Excavators, and Plumbers Excavating within the Public Right-of-Way. Cites Section 6-5-2-4 of the Ordinance, "
   "gives effective dates Wednesday, November 25th, 2020 to Monday, January 1st, 2021, and defines the Old Town, "
   "Uptown, Northwest and Downtown areas. Waivers require the concurrence of the Director of Municipal "
   "Development.")),
 ('src-db6729572f9b4184', "2022 Balloon Fiesta Construction Moratorium Map", "2022",
  ("The City's map of the streets and areas closed to construction during the 2022 Balloon Fiesta, the most recent "
   "moratorium map in the set."),
  "Titled 2022 BALLOON FIESTA Construction Moratorium."),
]
for i, title, date, desc, ev in MORATORIUM:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "construction moratorium",
              "why_retained": ("The City restricts street excavation during major events, and these are the only "
                               "record of where and when. The letter states the rule; the maps show its extent."),
              "proposed_canonical_page": ROADWAY,
              "cross_listings": [{"page": DEVPROC, "reason": "It governs when a right-of-way excavation permit will not be issued."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

# ------------------------------------------------------------- bond programme
BOND = [
 ('src-9d7dc19099e4f7d3', "2025 General Obligation Bond Program Instruction Book", "2025", CAPITAL, [],
  ("The City's instruction book for its 2025 general obligation bond programme sets out how departments prepare "
   "and submit capital projects for the programme, including how a project's operating and maintenance "
   "consequences must be analysed."),
  "Titled G.O. BOND 2025 Program INSTRUCTION BOOK, City of Albuquerque. The largest bond document in the slice at 179,434 characters of extracted text."),
 ('src-1bd6e0aa7b78c29c', "Election Bond Questions: $12,900,000 public safety programme", None, CAPITAL, [],
  ("The City's ballot questions for a general obligation bond election, set out purpose by purpose in the words "
   "voters were asked to approve, beginning with a public safety question of twelve million nine hundred thousand "
   "dollars."),
  "Headed Election Bond Questions over Public Safety Bonds, Shall the City of Albuquerque issue $12,900,000 of its general obligation bonds to design, develop..."),
 ('src-724000b87a9f5e1b', "Election Bond Questions: $16,271,000 public safety programme", None, CAPITAL, [],
  ("The City's ballot questions for a different general obligation bond election, again purpose by purpose, with a "
   "public safety question of sixteen million two hundred and seventy one thousand dollars."),
  "Headed Election Bond Questions over Public Safety Bonds, Shall the City of Albuquerque issue $16,271,000 of its general obligation bonds to design, develop... Measured against its sibling at a real sequence ratio of 0.1341, so the two are different programmes, not editions."),
 ('src-bf022ba83b6456a9', "General Obligation Bond Programme: Dollar Amounts and Percentages by Purpose", None, CAPITAL, [],
  ("The City's summary chart divides a general obligation bond programme by purpose, giving the dollar amount and "
   "the share of the programme each purpose received, from affordable housing and metropolitan redevelopment "
   "onward."),
  "Headed Dollar Amounts and Percentages by Purpose, opening on Affordable Housing Bonds $4,495,000 and Metropolitan Redevelopment Bonds $2,375,000."),
 ('src-6b54b933b6974ddf', "General Obligation Bond Programme: Dollar Amounts and Percentages by Purpose, second programme", None, CAPITAL, [],
  ("A second City summary chart dividing a different bond programme by purpose, with its own dollar amounts and "
   "shares for each purpose of the programme."),
  "Headed Dollar Amounts and Percentages by Purpose, opening on Affordable Housing Bonds $3,788,000 - a different figure from its sibling, which is what establishes it as a different programme."),
 ('src-1dd2db219b1b7612', "General Obligation Bond Funding: how the City's bonds work", None, CAPITAL, [],
  ("The City's explanation of general obligation bond funding sets out that the bonds may finance any capital "
   "improvement the voters approve and that the City's general income from all sources is pledged to their "
   "repayment."),
  "Headed GENERAL OBLIGATION BOND FUNDING, explaining that the bonds are called General Obligation because the City's general income from all sources is pledged to the payment of the bonds."),
 ('src-c0b19c51ada746cb', "General Obligation Bonds: Frequently Asked Questions and Answers", None, CAPITAL, [],
  ("The City's questions and answers on its general obligation bonds explain what the bonds are, what backs them, "
   "and how the programme works, written for residents rather than for departments."),
  "Headed Frequently Asked Questions and Answers, question 1 What are General Obligation Bonds, answered as bonds backed by the full faith and credit of the City."),
 ('src-b8564a950074fabe', "Public Transportation Bonds: purpose sheet", None, TRANSIT,
  [{"page": CAPITAL, "reason": "A general obligation bond purpose sheet."}],
  ("The City's public transportation bond sheet lists each transit project the purpose funds with its allocation, "
   "from bus stop and facility rehabilitation through the equipment the funds may be used to buy."),
  "Headed Public Transportation Bonds, opening on Bus Stops Facility Rehabilitation $100,000 to rehabilitate and repair bus shelters and bus stations and purchase associated equipment."),
 ('src-e32027cc45bd73b3', "Capital Implementation Program: Presentation to the Council Committee of the Whole, 2015", "2015", CAPITAL,
  [{"page": CAPPROJ, "reason": "It presents the capital programme to the Council."}],
  ("The Municipal Development director's presentation of the Capital Implementation Program to the City Council "
   "sitting as a Committee of the Whole, setting out the programme as it stood under the administration of the "
   "day."),
  "Titled Capital Implementation Program, Department of Municipal Development, Wilfred Gallegos, P.E. Director, under Mayor Richard J. Berry."),
]
for i, title, date, canon, cross, desc, ev in BOND:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "bond programme", "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# -------------------------------------------------- enacted law and City policy
POLICY = [
 ('src-47786043ceaa7956', "Storm Water Quality Ordinance, Enactment No. O-2016-016", "2016", STORM,
  [{"page": DEVPROC, "reason": "It creates obligations in the development process."}],
  ("The City ordinance creating its storm water quality article records why the City legislated - the Clean Water "
   "Act, its municipal storm sewer permit since 2003, and the watershed based permit of December 2014 - and what "
   "the new article requires."),
  ("Rendered, because the file has twelve pages and twelve bytes of extractable text. Headed CITY of ALBUQUERQUE, "
   "TWENTY SECOND COUNCIL, COUNCIL BILL NO. C/S O-16-16, ENACTMENT NO. O-2016-016 handwritten on the face, "
   "sponsored by Trudy E. Jones by request. Adopts a stormwater quality ordinance creating a new Article 11 to "
   "Chapter 6 of the Albuquerque Code of Ordinances, section 6-11-1 Short Title, the Storm Water Quality "
   "Ordinance.")),
 ('src-af1446ca7eb32215', "Ordinance Governing the Naming and Changing of Names of Streets, Enactment No. 99-1983", "1983", ROADWAY,
  [{"page": MAPS, "reason": "Street names are the basis of the City's addressing and mapping."}],
  ("The City ordinance governing how streets are named and renamed sets out the four methods of official naming, "
   "the policy for cooperating with neighbouring governments on names that cross jurisdictions, and the policy for "
   "naming new streets."),
  ("Rendered, because the file has five pages and five bytes of extractable text. Headed CITY of ALBUQUERQUE, "
   "FIFTH COUNCIL, COUNCIL BILL NO. O-198, ENACTMENT NO. 99-1983 handwritten on the face, sponsored by Nadyne C. "
   "Bicknell and Thomas W. Hoover. Section 1 Method of Naming, Section 2 Inter-Governmental Cooperation Policy, "
   "Section 3 Policy on Naming New Streets.")),
 ('src-af3e21b6afd5f99b', "Executive Order: Vision Zero Pledge to End Traffic Fatalities and Severe Injuries", "2019", SPEED,
  [{"page": ROADWAY, "reason": "The pledge governs how City streets are designed and operated."}],
  ("The Mayor's executive order commits the City to Vision Zero, records the sixty nine people killed on "
   "Albuquerque roadways in 2018, names the departments and partner agencies joining the effort, and pledges the "
   "City to the framework."),
  ("Rendered, because the file has two pages and two bytes of extractable text. Headed EXECUTIVE ORDER, "
   "PROCLAIMING THE CITY'S COMMITMENT TO END ALL TRAFFIC FATALITIES AND SEVERE INJURY ACCIDENTS IN ALBUQUERQUE "
   "THROUGH PARTICIPATION IN THE VISION ZERO PLEDGE, signed by Timothy M. Keller. Records sixty nine individuals "
   "killed on Albuquerque roadways in 2018 and cites the Complete Streets Ordinance, O-14-27, enacted in 2015. "
   "The filename dates it 2019-09-04.")),
 ('src-95a1b652b2da3385', "Pedestrian Sidewalk, Drive Pad, and Curb and Gutter Required: Section 6-5-5-3", None, DEVPROC,
  [{"page": ROADWAY, "reason": "The requirement applies to every property along a City street."}],
  ("The City ordinance section requiring every property in the city to have sidewalk, drive pad, curb ramps and "
   "curb and gutter to the City's standards, unless a variance from those standards has been granted."),
  "Headed 6-5-5-3 PEDESTRIAN SIDEWALK, DRIVE PAD, AND CURB AND GUTTER REQUIRED, requiring all properties within the city to have sidewalk, drive pad, curb ramps, curb and gutter in accordance with the standards set forth by 6-5-5-1 et seq."),
 ('src-b5cab5a2a135aec0', "Streets and Traffic Enhancement Program (STEP): A Summary of Traffic Calming Policy, Council Draft, January 2014", "2014", SPEED,
  [{"page": ROADWAY, "reason": "The programme governs traffic calming on City streets."}],
  ("The City's summary of its traffic calming policy under the Streets and Traffic Enhancement Program explains how "
   "residents request calming measures, what measures are available, and how the City ranks and delivers them."),
  ("Titled Streets and Traffic Enhancement Program - STEP, A Summary of Traffic Calming Policy, City of "
   "Albuquerque. The cover carries COUNCIL DRAFT overprinted on the City name, which is why the extracted text "
   "reads COUNCICLiDtyRAoFfT. The filename records Updated Jan 2014.")),
 ('src-e2a168a9bf594838', "Albuquerque Street Lighting: Operation and Maintenance, December 2014", "2014", ROADWAY,
  [{"page": CAPITAL, "reason": "It addresses a recurring cost on the City's operating budget."}],
  ("The City's paper on street lighting examines the two costs that fall on its operating budget, the cost of "
   "operating and maintaining the lights and the cost of the electricity they use, and what drives each."),
  ("Headed ALBUQUERQUE STREET LIGHTING, Operation and Maintenance, December 2014, stating that the two issues of "
   "interest for street lighting on the City's operating budget are cost of operation and maintenance and cost of "
   "electricity. Its filename carries a copy_of_ prefix, but the plain name ALBUQUERQUESTREETLIGHTING.pdf was "
   "probed in both cases and returns 404: there is no second edition, and the prefix is a content management "
   "system artefact only.")),
 ('src-6fc42dafe71b89b1', "Automated Speed Enforcement: Radar Certificates of Calibration, May 2022", "2022", SPEED, [],
  ("Certificates of calibration for the radar units used in the City's automated speed enforcement programme, each "
   "recording the unit tested, the speeds read against simulated speeds, the standard used and the technician who "
   "performed the test."),
  ("Rendered, because the file has nine pages and nine bytes of extractable text. Each page is a ComSonics Repair "
   "Services Certificate of Calibration issued to NovoaGlobal, Inc. for a UMRR-11 Type 44 unit, dated May 5, 2022, "
   "certifying accuracy within plus or minus 1 mph, with simulated speeds of 25, 35 and 45 mph read as 25.5, 35.5 "
   "and 45.4, against a Sensys America simulator traceable to the National Institute of Standards and "
   "Technology.")),
]
for i, title, date, canon, cross, desc, ev in POLICY:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "enacted law and City policy", "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# --------------------------------------------------- Albuquerque Energy Council
AEC = [
 ('src-41dc50cfe28f0da7', "Albuquerque Energy Council Meeting Minutes, March 16, 2022", "2022", "Mayane Barudin"),
 ('src-74a90609f656aa53', "Albuquerque Energy Council Meeting Minutes, August 18, 2021", "2021", "Alex Montano"),
]
for i, title, date, chair in AEC:
    r = row(i, "approved for addition")
    desc = ("The Albuquerque Energy Council's own record of what it discussed and decided at this meeting, held at "
            "the Department of Municipal Development offices and by video, chaired by %s." % chair)
    r.update({"title": title, "description": desc, "date": date, "pages": None,
              "evidence": ("Headed Albuquerque Energy Council, Meeting Minutes, Department of Municipal Development "
                           "1801 4th Street Bldg. B, with the meeting date and the 8:00 am to 10:00 am slot, In "
                           "office and Zoom, and the chair named on the face."),
              "group": "Albuquerque Energy Council",
              "why_retained": ("The agenda and minutes slice recorded that this body has no presence on cabq.gov at "
                               "all and preserved ten of its agendas under the missing-minutes exception. These are "
                               "minutes, not agendas, and they extend a series that artifact could only partly "
                               "assemble."),
              "cross_artifact": "municipaldevelopment-agenda-minutes-cluster-research-2026-09-12.json",
              "proposed_canonical_page": CLIMATE,
              "cross_listings": [{"page": CAPITAL, "reason": "The council advises on City energy spending."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

# ------------------------------------------------------ bicycle and pedestrian
BIKEPED = [
 ('src-2f5da96c42d54fa8', "No Parking in Bicycle Lanes: parking locations poster, English", None,
  ("The City's education poster shows, lane arrangement by lane arrangement, where a vehicle may and may not park "
   "where a bicycle lane is present, so that drivers can tell a legal parking location from an obstruction of the "
   "bike lane."),
  "Headed Parking Locations - No Parking in Bicycle Lanes, over a series of labelled cross sections of vehicle lane, bicycle lane, shared lane and parking arrangements."),
 ('src-cc44b06a2deb4a51', "No Parking in Bicycle Lanes: parking locations poster, Spanish", None,
  ("The Spanish edition of the City's bicycle lane parking poster, showing the same lane arrangements and the same "
   "rule about where a vehicle may and may not park where a bicycle lane is present."),
  "Headed Zonas de Estacionamiento - No Estacionarse en los Carriles de Bicicletas, over the same labelled cross sections as the English edition. Not a translation stub: it is a separately typeset sheet, 349,256 bytes against the English edition's 349,018."),
 ('src-b31976802bec1a91', "Bike Safety Skills Class Flyer, 2026", "2026",
  ("The City's flyer for its free bicycle safety skills class gives the schedule, the location and how to sign up, "
   "and states what participants earn for completing it."),
  "Headed Bike Safety Skills Class, recording that sign ups are open over the phone or online, that the free class is offered every Wednesday in May at 4:30 pm at the City's McKinley location, and that participants earn a reward for attending."),
 ('src-f68d3b814d3fb873', "Dr. Martin Luther King Jr. Avenue Bike Facility Enhancements: project trifold", None,
  ("The City's project leaflet for bicycle facility enhancements on Dr. Martin Luther King Jr. Avenue explains why "
   "the City is working on this roadway, what the enhancements are, and who to contact with questions about the "
   "project."),
  "A trifold headed Why Dr. Martin Luther King Jr. Ave.? over Bike Facility Enhancements, naming the project manager and recording that the roadway is one of the main entry ways to downtown for many commuters."),
]
for i, title, date, desc, ev in BIKEPED:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "bicycle and pedestrian", "proposed_canonical_page": BIKEIDX,
              "cross_listings": [{"page": BIKE, "reason": "It implements the City's bicycle network planning."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

# ------------------------------------------------ presentations and open houses
PRESENT = [
 ('src-96224aad72485bf6', "CIP Bidding and Contract Book Overview: Building Albuquerque presentation", "2022", DEVPROC,
  ("The City's presentation on how its capital projects are bid explains the contract book, the bidding process "
   "and what a contractor must do to bid on City work, given at a contractors' event."),
  "Titled Department of Municipal Development, CIP Bidding and Contract Book Overview, June 14, 2022. An OOXML presentation, leading bytes 504b0304, read slide by slide from ppt/slides."),
 ('src-d6c487f305a5153a', "Designing Albuquerque: An Open House for Architects, Landscape Architects and Engineers, projects presentation", "2022", DEVPROC,
  ("The City's open house presentation for design professionals sets out the projects it expects to commission, "
   "given to architects, landscape architects and engineers at a single event."),
  "Titled Designing Albuquerque: An Open House for Architects, Landscape Architects & Engineers, Projects, June 15, 2022. An OOXML presentation read from ppt/slides."),
 ('src-fdcc45f96bed54e8', "Economic Development at the Contractors' Open House", None, DEVPROC,
  ("The City's Economic Development Department presentation to a contractors' open house sets out what the "
   "department does and how contractors encounter it, alongside the design and bidding material presented at the "
   "same event."),
  "Titled City of Albuquerque Economic Development, Contractor's Open House, over an Economic Development Department slide. An OOXML presentation read from ppt/slides."),
 ('src-9b6e88ac820f9e90', "Coors Boulevard Public Information Meetings, February 2011", "2011", ROADWAY,
  ("The City's public information presentation on its Coors Boulevard study sets out the project background, the "
   "study area and the objectives, as given at two public meetings held two days apart."),
  "Headed Public Information Meetings, February 22 and 24, 2011, over Project Background, Study Area, and Objectives."),
 ('src-1917803690500070', "Street Maintenance and Rehabilitation in the Twenty First Century: District 8 Coalition presentation, August 3", None, ROADWAY,
  ("The City's presentation to a district coalition on street maintenance and rehabilitation sets out the "
   "condition of the street network, what maintaining it costs, and the additional revenue the City has received "
   "and appropriated for the work."),
  "Titled Street Maintenance and Rehabilitation in Twenty First Century, prepared for the District 8 coalition. Records $54 million in additional revenue received by the City and appropriated recently by City Council."),
 ('src-26da8f3f818b9014', "Before and After: City construction projects showcase, October 2025", "2025", CAPPROJ,
  ("The City's before and after showcase presents completed construction projects across Albuquerque, from new "
   "community centres on the west side to new public safety facilities, with the finished result set against what "
   "was there before."),
  "Headed CABQ Before and After, opening on the statement that the City of Albuquerque is busy building, from new community centers on the Westside to new public safety facilities and 100-foot-long slides off Juan Tabo. The filename records 10-21-25."),
]
for i, title, date, canon, desc, ev in PRESENT:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "presentations and open houses", "proposed_canonical_page": canon,
              "cross_listings": [{"page": CAPITAL, "reason": "It concerns the delivery of the capital programme."}]
              if canon != CAPITAL else [],
              "description_word_count": len(desc.split())})
    approved.append(r)

# ----------------------------------------------------- maps, projects, the rest
REST = [
 ('src-afa324837918e7b9', "Land Grants within Bernalillo County, New Mexico", None, MAPS,
  [{"page": DEVPROC, "reason": "Land grant boundaries bear on land use and title across the county."}],
  ("A map of the Spanish and Pueblo land grants within Bernalillo County, drawn over the public land survey "
   "township and range grid so that each grant's extent can be read against the section numbering."),
  ("Rendered, because the file has one page and one byte of extractable text. Titled Land Grants within Bernalillo "
   "County New Mexico, with a PLSS land grant and township corner legend, and the grants shaded and labelled: "
   "Sandia Pueblo, Elena Gallegos, Alameda, Town of Atrisco, Pajarito, Isleta Pueblo, Town of Alburquerque and "
   "Canyon. The annotations are hand-drawn.")),
 ('src-3d2d149de98b33f7', "Completed Construction Projects from 2010 to Current", None, CAPPROJ,
  [{"page": MAPS, "reason": "It is a map of where the work happened."}],
  ("The City's map of construction projects completed from 2010 onward, plotting each project by its number "
   "against the street network so that the work done in any part of the city can be located."),
  "A map plotting numbered projects across the Albuquerque street grid, its extracted text the project numbers and street names together: 9934, 4695 Westside, 3958, 3906, 3917 Unser, 11579 NM, 4th, 7892 McMahon, 528, 4661 Roy, Irving."),
 ('src-f020ff71081d2224', "Brillante STEAM Early Learning Center: concept board", None, PROJECTS,
  [{"page": CAPITAL, "reason": "A City capital project."}],
  ("The architects' concept board for the Brillante early learning centre sets out the key concepts of the design "
   "and what the centre is intended to be: a museum-based STEAM early learning centre serving more than a hundred "
   "children."),
  ("Rendered, because the file has one page and one byte of extractable text. Headed BRILLANTE, STEAM EARLY "
   "LEARNING CENTER, by Henry Architects LLC of Taos, with the Brillante and Explora identities on it. Key "
   "concepts listed as Piazza, Atelier, Classrooms, Resource Library, Learning Kitchen & Garden, Courtyards, "
   "Reflecting, Observing, Illuminating. Records that Brillante will be the state's only full-time museum-based "
   "STEAM early learning center, inspired by the Reggio Emilia method, serving over 100 infants, toddlers and "
   "young children, and will act as a lab school for local higher education institutions.")),
 ('src-a659323fdbfc0d8a', "Questions and Answers: On-Call Architectural Services, Project 137.02", "2025", DEVPROC, [],
  ("The City's answers to bidders on an on-call architectural services contract tell them where the full request "
   "for proposals is published and address the questions raised about the Transit Department's share of the "
   "work."),
  "Dated June 26, 2025, headed Questions Regarding On-Call Architectural Services, Project No: 137.02. The filename reads 127-02-additions; the document reads 137.02. An OOXML document read from word/document.xml."),
 ('src-8cc352afd205c7ee', "Request for Proposals: Western Trails Triangle, Real Property Division", "2022", REDEV,
  [{"page": PROJECTS, "reason": "A City land disposition."}],
  ("The City's request for sealed proposals for land it acquired at the Western Trails Triangle, giving the "
   "proposal number, the deadline, the statutory basis for the disposition and the division handling it."),
  ("Rendered, because the file has seven pages and seven bytes of extractable text. Headed REQUEST FOR PROPOSALS, "
   "RFP# RPD-WTT-BCS, proposals due Wednesday, August 24, 2022 by 3:00 pm. The City through the Real Property "
   "Division will accept sealed proposals for land acquired through acquisition and in accordance with Section "
   "5-2-1 et seq. R.O.A. 1994, handled by the Planning Department Real Property Division.")),
]
for i, title, date, canon, cross, desc, ev in REST:
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "maps, projects and the rest", "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# ----------------------------------------------------------------- superseded
superseded = [{
 **row('src-b2f10ed06a3359a3', "superseded"),
 "canonical_id": 'src-1917803690500070',
 "title_for_reference": "Street Maintenance and Rehabilitation in Twenty First Century: District 8 Coalition presentation, earlier version",
 "relationship": "An earlier version of the same presentation.",
 "how_it_was_established": ("A line-level diff over the two extractions returns exactly one differing block in a "
                            "166-line and 167-line document. The successor rewrites a single revenue bullet from "
                            "'$54 million in additional revenue' and '$42 appropriated recently by City Council' to "
                            "'$54 million in additional revenue received by City' and 'Has been appropriated "
                            "recently by City Council including'. Everything else is identical."),
 "a_caveat_worth_carrying": ("Neither document carries a date on its face. The ordering rests on two things: the "
                             "successor's filename records aug_3, and its wording is the fuller, corrected one - a "
                             "bullet that read '$42 appropriated' now reads as a sentence. Given that nine filenames "
                             "in this tree have contradicted their own documents, the filename alone would not be "
                             "enough; the wording is what carries it. If the City can date either version, confirm "
                             "the order."),
 "recommended_treatment": "Retain. The difference is one bullet, but it is a bullet about public money.",
}]

# ------------------------------------------------------------------ duplicate
duplicate = [
 {**row('src-b1e0a1643b2e820c', "duplicate"),
  "canonical_id": 'src-2f5da96c42d54fa8',
  "title_for_reference": "bike-lane-ed-poster-final-eng.pdf/view",
  "relationship": "The Plone /view wrapper URL of the English bicycle lane poster, recorded as a separate candidate.",
  "how_it_was_established": ("The /view URL was fetched in both forms. Stripped of the suffix it returns the same "
                             "349,018 bytes with the same SHA-256 as its plain twin. Fetched with the suffix intact "
                             "it returns 110,513 bytes of HTML, leading bytes 3c21444f - the content management "
                             "system's viewer page, not the document."),
  "why_this_one_is_the_copy": "A /view URL is a wrapper around the object, not an object. Archive the raw form.",
  "precedent": "The inventory already records the /view twin of gabac-mountain-road-bike-blvd-crossing.pdf as a duplicate; this follows it."},
 {**row('src-7f40f4a3c910becd', "duplicate"),
  "canonical_id": 'src-cc44b06a2deb4a51',
  "title_for_reference": "bike-lane-ed-poster-final-esp.pdf/view",
  "relationship": "The Plone /view wrapper URL of the Spanish bicycle lane poster.",
  "how_it_was_established": "Same test, same result: 349,256 bytes and an identical SHA-256 when the suffix is stripped, 110,513 bytes of HTML when it is not.",
  "why_this_one_is_the_copy": "A /view URL is a wrapper around the object, not an object."},
 {**row('src-4ead432e376c6c29', "duplicate"),
  "canonical_id": 'src-9d7dc19099e4f7d3',
  "title_for_reference": "pages-40-44-from-g-o-book-smm-1.pdf",
  "relationship": "Pages 40 to 44 of the 2025 general obligation bond instruction book, published separately.",
  "how_it_was_established": ("Token coverage of the extract inside the full book is 1.0000; coverage of the book "
                             "inside the extract is 0.1028. Every word of the extract is in the book and the book is "
                             "roughly ten times its length. It is a section of the book, not a separate document."),
  "a_cross_slice_finding": ("The same five pages appear again as o-m-instructions-2027.pdf, recommended in "
                            "permits-forms-regulations-cluster-research-2026-09-12.json. Those two are NOT the same: "
                            "token coverage between them is 0.8722 and 0.9856, but the real sequence ratio is 0.4528 "
                            "and they are not string-equal. The 2027 instructions are a revision of the 2025 book's "
                            "section, with the fiscal years moved on. Both should be kept; only this extract is "
                            "redundant."),
  "why_this_one_is_the_copy": "The full book is present and recommended. An extract adds nothing the book does not hold."},
]

# ---------------------------------------------------- requires human review
rhr = [
 {**row('src-3b8d91e803255804', "requires human review"),
  "draft_title": "Balloon Fiesta Construction Moratorium Map, year not stated",
  "question_for_human": "Establish which Balloon Fiesta this map covers, then approve it.",
  "why_not_decided_here": ("Its title block reads BALLOON FIESTA Construction Moratorium with no year and no dates, "
                           "unlike the 2018 and 2022 maps in the same set which carry both. Publishing a moratorium "
                           "map under the wrong year would tell a contractor the wrong streets were closed."),
  "measurement": "Rendered and hashed against every other map in the set; its rendered page is distinct from all of them. Real sequence ratio 0.9637 against the 2022 map and 0.9957 against the undated holiday map, which is a measure of the street labels, not of the moratorium drawn on them.",
  "distinguishing_content": "BALLOON FIESTA Construction Moratorium, with moratorium area and moratorium street symbology and no date line.",
  "package": "the_undated_moratorium_maps", "priority": 1},
 {**row('src-7c96ca757c40af55', "requires human review"),
  "draft_title": "Holiday Construction Moratorium Map, year not stated",
  "question_for_human": "Establish which holiday season this map covers, then approve it.",
  "why_not_decided_here": ("Its title block reads HOLIDAY Construction Moratorium with no year and no effective "
                           "dates. The 2018 and 2020 holiday maps both carry theirs."),
  "measurement": "Rendered and confirmed distinct from every other map in the set. Its title block was only legible after rendering; the extracted text gives street names and the word Moratorium.",
  "distinguishing_content": "HOLIDAY Construction Moratorium, no date line, moratorium area shown at Uptown and Old Town.",
  "package": "the_undated_moratorium_maps", "priority": 2},
 {**row('src-d7ed8b7315a5e12d', "requires human review"),
  "draft_title": "Paseo del Norte Construction Moratorium Map",
  "question_for_human": "Confirm the year and the occasion of the Paseo del Norte moratorium, then approve it.",
  "why_not_decided_here": ("The filename says 2013 and the document does not. Its extracted text is street labels "
                           "and the word Moratorium; no year appears anywhere on it. This lane has found nine "
                           "filenames in this tree that contradict their own documents, so a year that exists only "
                           "in a filename is an attribution, not a fact."),
  "measurement": "Rendered and confirmed distinct. It is the outlier of the map set: real sequence ratios against the others run 0.0148 to 0.0645, an order of magnitude below every other pair, so it is drawn on a different base map.",
  "distinguishing_content": "Paseo del Norte moratorium, covering a different and smaller area than the event moratoria.",
  "package": "the_undated_moratorium_maps", "priority": 3},
 {**row('src-f1c90b2d48b85069', "requires human review"),
  "draft_title": "501 Tijeras NW Ground Floor As-Built Drawing",
  "question_for_human": "Establish the City's interest in this building before publishing a private client's drawing of it.",
  "why_not_decided_here": ("The drawing's own title block names its client as a private limited liability company, "
                           "not the City. A handwritten annotation reading MRA-$4000 suggests a Metropolitan "
                           "Redevelopment Agency grant, which would explain why the City holds it, but that is an "
                           "inference from a handwritten note. The document states no City role."),
  "measurement": ("Rendered, because the file has one page and one byte of extractable text. Title block: PROJECT "
                  "501 TIJERAS NW GROUND FLOOR, DESCRIPTION AS-BUILT DRAWING, CLIENT Duke City Commercial LLC, "
                  "sheet 01 of 03, scale 3/16 inch to the foot, dated 10/27/22. Usable area 8,182.16 sq ft, common "
                  "area 2,583.56 sq ft, out-building gross area 305.62 sq ft."),
  "distinguishing_content": "As-built floor plan of 501 Tijeras NW, ground floor, with BOMA usable area calculations.",
  "package": "a_private_clients_drawing_on_a_City_page", "priority": 4},
]

# ------------------------------------------------------------------- excluded
excluded = [
 {**row('src-09592fba403c1e2f', "excluded"),
  "title_for_reference": "Shawn's Meeting Notes, June 5, 2025",
  "what_it_is": "An automatically generated transcript and summary of a one-hour meeting, produced by a third-party AI notetaking service.",
  "exclusion_reason": ("Machine transcription, not a City record. It is headed with a personal first name and a "
                       "timestamp, runs to forty three thousand characters of unreviewed automatic transcript, and "
                       "carries no City authorship, no adoption and no indication that anyone checked it. A "
                       "transcript nobody has verified is not a minute."),
  "category": "unreviewed machine transcript", "package": "meeting_exhaust"},
 {**row('src-400bbca73dd43239', "excluded"),
  "title_for_reference": "Advertising order confirmation and ad proof",
  "what_it_is": "A newspaper advertising order confirmation addressed to the City's accounts payable section.",
  "exclusion_reason": ("Billing paperwork. It is an Ad Proof/Order Confirmation carrying an account number, an ad "
                       "order number and a payable address. Whatever the City advertised is a City record; the "
                       "invoice for placing it is not."),
  "category": "accounts payable paperwork", "package": "administrative_exhaust"},
 {**row('src-e5b8c25b8896c902', "excluded"),
  "title_for_reference": "streets-documents, directory listing",
  "what_it_is": "The City's web page for the directory, not a document in it.",
  "exclusion_reason": ("Not a document. The URL returns an HTML page, leading bytes 3c21444f, whose extracted text "
                       "is the City's site navigation. The one file that sits in this directory, the sidewalk "
                       "ordinance section, is recommended in this artifact in its own right."),
  "category": "directory listing, not a document", "package": "not_a_document"},
 {**row('src-48c77cfd3533626b', "excluded"),
  "title_for_reference": "mountain-road-bike-blvd-crossing-at-san-pedro-drive.pdf/view",
  "what_it_is": "The Plone /view wrapper URL of a record the inventory already carries, and already excluded.",
  "exclusion_reason": ("A wrapper around an excluded object. Its plain twin, src-350f1b4d381f1b7e, is already "
                       "excluded in the inventory, and the same crossing document is already held as "
                       "src-438b3ebcc3f671e2, validated with an r2_url under the name "
                       "gabac-mountain-road-bike-blvd-crossing.pdf. Excluding the wrapper matches what its own plain "
                       "twin already is."),
  "category": "view wrapper of an excluded record", "package": "not_a_document"},
 {**row('src-142c353eae3b8211', "excluded"),
  "title_for_reference": "PNM 14th Revised Rate No. 20: Integrated System Streetlighting and Floodlighting Service",
  "what_it_is": "A Public Service Company of New Mexico electricity tariff for streetlighting service, effective October 28, 2013.",
  "exclusion_reason": ("Not a City record, and superseded on its own face. It is a utility tariff filed with the "
                       "New Mexico Public Regulation Commission - 14th Revised Rate No. 20 cancelling 13th Revised "
                       "Rate No. 20 - stamped EFFECTIVE OCT 28 2013 and, beside it, REPLACED BY NMPRC Operation of "
                       "Law. The authoritative publisher is the Commission."),
  "category": "third-party utility tariff, superseded",
  "if_reconsidered": "If the City's streetlighting electricity cost needs a source, cite the current tariff at the Commission rather than archiving a rate that has been replaced.",
  "package": "third_party_authority"},
]

rows = approved + superseded + duplicate + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), ("missing: %s" % sorted(set(SLICE) - set(ids)), "extra: %s" % sorted(set(ids) - set(SLICE)))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)
solar_kw = round(sum(r["designed_dc_kw"] for r in approved if r.get("designed_dc_kw")), 1)
n_rendered = 31

artifact = {
 "batch_id": "municipaldevelopment-flat-remainder-cluster-research-2026-09-13",
 "lane": "Claude research lane: the remainder of the flat level of www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13, the ninth and last slice of the municipaldevelopment/documents lane.",
 "cluster": ("Everything left at the flat level once the bond sheets, the agendas, the procurement paper, the "
             "environmental plans and the forms have been taken out: moratorium maps, a second solar series, two "
             "sets of council minutes, three pieces of enacted law, and a long tail of presentations and maps."),
 "scope": "All 65 remaining uncovered candidates in the tree. The coverage gate is asserted in the generator.",
 "brief": ("This is the heterogeneous remainder, so group it by what each document is before deciding, and expect "
           "filenames to be unreliable - eight in this tree have now contradicted their own documents."),
 "brief_finding": ("Grouped, it is not heterogeneous at all: eight groups account for all 65, and three of them are "
                   "substantial runs the archive does not hold. The filename warning was worth carrying - a ninth "
                   "case turned up, and three more records carry a year that exists only in a filename."),
 "this_completes_the_tree": ("With this artifact every candidate under www.cabq.gov/municipaldevelopment/documents "
                             "is decided. Nine slices, 384 records."),
 "method": ("Fetched every candidate and measured byte length and SHA-256 from the fetched bytes, verifying every "
            "container by leading bytes: 60 PDFs, 4 OOXML files and one HTML page. Extracted text with the right "
            "reader for each container. Ran a pairwise screen across the whole slice at token coverage 0.75 and "
            "above, then measured every surviving pair with a real sequence ratio. Rendered 31 files: ten with no "
            "usable text layer, twelve solar reports, and the whole map set. Rendered and hashed the entire map "
            "set, because text comparison cannot distinguish two maps of the same city."),
 "classification_only": True,
 "shared_state_written": [],
 "the_map_problem_and_how_it_was_solved": {
  "what_the_text_said": ("The moratorium maps score 0.9980, 0.9957, 0.9637, 0.9593, 0.9475 and 0.9459 against each "
                         "other on real sequence ratio, with token coverage up to 0.9944. On text alone most of "
                         "them read as copies."),
  "why_the_text_says_that": ("Their extracted text is street labels. They are maps of the same city, so they carry "
                             "almost the same labels whatever is drawn on top. The moratorium itself - the shaded "
                             "areas and the coloured streets - is not text at all."),
  "what_was_done": ("Every map was rendered to PNG at the same scale and the rendered pages hashed. Nine maps, nine "
                    "distinct SHA-256 values. Not one pair is the same drawing."),
  "the_rule_this_confirms": ("Render and hash, established one slice earlier on a pair of survey markups. That case "
                             "proved a duplicate the text could not prove; this case refuses six duplicates the text "
                             "appeared to show. The technique answers both directions of the question."),
  "a_second_thing_rendering_gave": ("The titles. holiday-shopping-map.pdf carries 2018 HOLIDAY SHOPPING "
                                    "Construction Moratorium, November 21st - January 1st in its title block, and "
                                    "2018-moratorium.pdf turns out to be a combined sheet showing all three 2018 "
                                    "moratoria at once. Three maps state no year anywhere and are held for review."),
 },
 "the_second_solar_series": {
  "count": len(SOLAR),
  "what_it_is": ("Eleven annual production reports and one 2019 proposal, covering eleven City buildings: the "
                 "Barelas Senior Center, Cherry Hills Library, Fire Stations 5, 11 and 18, the Daytona transit "
                 "facility, Cerro Colorado landfill, Los Altos swimming pool, the Pino Avenue City Yards, the "
                 "Sunport and the Foothills area command."),
  "designed_capacity": ("%s kW DC across the eleven 2022 reports. The Sunport array alone is 609.8 kW and models "
                        "1.026 GWh a year, the only one in either slice measured in gigawatt hours." % f"{solar_kw:,}"),
  "who_prepared_them": ("Two consultants neither of which appears in the first series: Solluna Solar, credited to "
                        "Zach Johnson, for six of them, and OE Solar for five. The first series, in "
                        "facility-environmental-compliance-cluster-research-2026-09-12.json, was Rio Grande "
                        "Renewables."),
  "the_series_as_a_whole": ("With the six records in that artifact the City facility solar series now runs to "
                            "eighteen documents across sixteen sites and three consultants. The archive publishes "
                            "the City's climate plans and greenhouse gas inventories and held no record of what "
                            "solar was actually installed on City roofs."),
  "every_one_had_to_be_rendered": ("The site name, address and capacity are printed at the top of page 1 in text "
                                   "that is not in the PDF text layer. Searching the extracted text of any of these "
                                   "for a site returns the consultant's name and the word Folsom. This is the exact "
                                   "failure that produced a wrong exclusion two slices ago, and the reason all "
                                   "twelve were rendered rather than three."),
  "the_caution_on_every_row": SOLAR_CAUTION,
 },
 "three_pieces_of_enacted_law_that_no_text_search_would_have_found": {
  "count": 3,
  "the_ordinance": ("cs-o-16enacted.pdf is the Storm Water Quality Ordinance, Council Bill C/S O-16-16, Enactment "
                    "No. O-2016-016, sponsored by Trudy E. Jones by request, creating Article 11 of Chapter 6 of "
                    "the Albuquerque Code of Ordinances. Twelve pages, twelve bytes of extractable text."),
  "the_older_ordinance": ("streetnaming_coa5thcouncil.pdf is the ordinance governing the naming and changing of "
                          "names of streets, Council Bill O-198, Enactment No. 99-1983, sponsored by Nadyne C. "
                          "Bicknell and Thomas W. Hoover, of the Fifth Council. Five pages, five bytes of "
                          "extractable text."),
  "the_executive_order": ("dmd-20190904-executiveorder-vz.pdf is the Mayor's Vision Zero executive order, recording "
                          "sixty nine people killed on Albuquerque roadways in 2018 and citing the Complete Streets "
                          "Ordinance O-14-27. Two pages, two bytes of extractable text."),
  "the_point": ("All three are scanned. Every one of them would be invisible to any pass that reads text, searches "
                "filenames, or trusts inventory titles. They were found by rendering the ten files whose text layer "
                "was empty, which took one command."),
  "the_enactment_numbers_matter": ("Both ordinances carry their enactment number handwritten on the face - "
                                   "O-2016-016 and 99-1983 - which is exactly the evidence the west-central lane "
                                   "had to reconstruct from later legislation when the adopting resolutions came "
                                   "back blank."),
 },
 "two_more_energy_council_minutes": {
  "count": 2,
  "the_finding": ("Minutes of 18 August 2021, chaired by Alex Montano, and 16 March 2022, chaired by Mayane "
                  "Barudin. municipaldevelopment-agenda-minutes-cluster-research-2026-09-12.json recorded that the "
                  "Albuquerque Energy Council has no presence on cabq.gov at all - three candidate page URLs 404 "
                  "and the City's own site search returns zero items for the exact phrase - and preserved ten of "
                  "its agendas under the missing-minutes exception because no minutes could be found for them."),
  "what_it_changes": ("Two of that body's meetings now have minutes after all, and the March 2022 meeting is later "
                      "than any record that artifact held. The agendas it preserved stand; this adds to the series "
                      "rather than displacing anything."),
  "a_dating_note": ("august-18-min.pdf carries no year in its filename. The document gives Wednesday, August 18th "
                    "2021 on its face. Dated from the document, as the Energy Council record in the earlier "
                    "artifact established."),
 },
 "a_ninth_filename_that_contradicts_its_document": {
  "the_case": "127-02-additions.docx is headed Questions Regarding On-Call Architectural Services, Project No: 137.02.",
  "the_running_count": ("Nine now, across five slices: a body and a date wrong on an Energy Council file, two "
                        "misspelled facilities in the stormwater set, a project number and an unrecorded project in "
                        "the procurement slice, three wrong years on parking and vehicle forms, and this."),
  "and_three_more_of_a_different_kind": ("Three records carry a year that exists only in a filename and nowhere on "
                                         "the document: the Paseo del Norte moratorium map, held for review for "
                                         "exactly that reason, and the two undated event moratorium maps beside it. "
                                         "A year in a filename is an attribution, not a fact."),
  "and_one_that_is_merely_different": ("foot-hills-apd-substation.pdf is headed 5th Command Center, 12800 lomas "
                                       "blvd NE. Both names describe the same police facility, so this is a naming "
                                       "difference rather than an error, but the row is titled from the document "
                                       "and records both."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 2,
  "one_candidate_already_held_under_another_name": ("The /view wrapper of the Mountain Road bike boulevard crossing "
                                                    "resolves to a document the archive already holds as "
                                                    "src-438b3ebcc3f671e2, validated with an r2_url under the name "
                                                    "gabac-mountain-road-bike-blvd-crossing.pdf. Excluded."),
  "result": "Nothing recommended here duplicates anything the archive holds.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 2,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 2,
  "checksums_compared_against": 1612,
  "relationships_found": 4,
  "relationships_tested_and_rejected": 6,
  "found_by": ("Two by byte hashing once the /view suffix was stripped, one by containment inside a larger book, "
               "one by a line-level diff that returned a single differing bullet."),
  "rejected_by": "Rendering and hashing six map pairs whose text similarity ran from 0.9459 to 0.9980.",
  "note": ("The six rejections matter as much as the four findings. Every one of those pairs would have been "
           "recommended as a duplicate by any process that stopped at text."),
 },
 "integration_flags": [
  {"severity": "method",
   "affects": [],
   "finding": "Render and hash settles map comparison. Nine moratorium maps score up to 0.9980 on text similarity because their extracted text is street labels; rendered and hashed, all nine are distinct drawings. Six apparent duplicates were refused this way.",
   "recommended_action": "Apply render-and-hash to any graphical candidate set before accepting or refusing a duplicate on text similarity."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'enacted law and City policy'][:3],
   "finding": "Three pieces of enacted City law and mayoral policy found only by rendering: the Storm Water Quality Ordinance (Enactment O-2016-016), the street naming ordinance (Enactment 99-1983, Fifth Council), and the Vision Zero executive order. All three are scanned and carry between two and twelve bytes of extractable text.",
   "recommended_action": "Approve. Both ordinances carry their enactment number handwritten on the face."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'city facility solar'],
   "finding": f"A second City facility solar series: twelve documents covering eleven buildings, {solar_kw:,} kW DC designed, prepared by Solluna Solar and OE Solar. With the first series the run now totals eighteen documents across sixteen sites and three consultants.",
   "recommended_action": "Approve, describing every figure as designed and modelled rather than generated. Every one of these had to be rendered; the site names are not in the text layer."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'Albuquerque Energy Council'],
   "finding": "Two more sets of Albuquerque Energy Council minutes, 18 August 2021 and 16 March 2022, for a body the agenda and minutes slice recorded as having no presence on cabq.gov at all.",
   "recommended_action": "Approve and fold into the series that artifact began. The agendas it preserved under the missing-minutes exception still stand."},
  {"severity": "date-before-publishing",
   "affects": [r['id'] for r in rhr if r.get('package') == 'the_undated_moratorium_maps'],
   "finding": "Three construction moratorium maps with no year on their faces. Publishing one under the wrong year would tell a contractor the wrong streets were closed.",
   "recommended_action": "Date each from a City source, then approve. Their rendered pages are distinct from every dated map in the set, so none of them is a copy of one."},
  {"severity": "judgment-needed",
   "affects": ['src-f1c90b2d48b85069'],
   "finding": "An as-built drawing whose title block names a private limited liability company as the client, posted on a City page, with a handwritten MRA-$4000 annotation that suggests a Metropolitan Redevelopment Agency grant.",
   "recommended_action": "Establish the City's interest before publishing a private client's drawing of a private building."},
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
                "http_200_but_not_the_document": 2,
                "the_two": "Both bicycle lane poster /view URLs return 110,513 bytes of HTML rather than the poster. Fetched without the suffix they return the poster.",
                "probes": "ALBUQUERQUESTREETLIGHTING.pdf was probed in two cases for a plain twin of the copy_of_ file; both 404.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "containers_verified": ("%d PDFs, %d OOXML files and %d HTML page by leading bytes."
                                        % (bycontainer['PDF'], bycontainer['OOXML'], bycontainer['HTML'])),
                "rendered": ("%d files rendered to PNG: ten with no usable text layer, nine maps whose "
                             "differences are not text at all, and twelve solar reports whose site names are not "
                             "in their text layer." % n_rendered)},
 "approved_for_addition": approved,
 "superseded": superseded,
 "duplicate": duplicate,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, dominated by the "
                   f"solar series and the 2025 bond instruction book. Four approved records are OOXML and should be "
                   f"archived in their original format rather than converted. Nineteen are scanned documents with no "
                   f"usable text layer; they should be archived as they are, and their titles taken from this "
                   f"artifact rather than from their filenames or their empty text."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. One row carries a canonical_id for supersession and "
                     "three for duplication; all four canonicals are approved rows in this artifact. Every approved "
                     "row carries a group field. Solar rows carry a site and, where the document states one, a "
                     "designed_dc_kw. Two rows name another artifact they extend. Every row carries a "
                     "leading_bytes field. Sizes and checksums are first measurements; the inventory held none. "
                     "This artifact completes the municipaldevelopment/documents tree."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the probe for a plain street-lighting twin was read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != 'approved_by_group'}}))
