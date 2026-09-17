"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. First slice of the municipaldevelopment/documents lane: the
cip-documents subtree.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\cip-documents-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md\fetch.log')

CAPITAL = 'content/city-data/capital-spending.md'
PARKS = 'content/public-works/parks-recreation.md'
TXPLANS = 'content/transportation/transportation-plans.md'
ABQRIDE = 'content/transportation/transit/abq-ride.md'
STORM = 'content/public-works/stormwater-drainage.md'
SAFETY = 'content/city-data/public-safety-data.md'
PROJECTS = 'content/development-land-use/projects.md'
FACILITIES = 'content/public-works/city-facilities.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

# Coverage gate: no record already decided in a saved artifact may appear here.
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
assert not (set(M) & PRIOR), sorted(set(M) & PRIOR)

LC = ("HTTP 200 verified 2026-09-12 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "because the inventory record carried neither. Container verified by leading bytes, not by extension.")


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML",
         "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


SET_2007 = ("One sheet of the City's 2007 general obligation bond election package, published under "
            "cip-documents/2007-bond-documents and cip-documents/2007-election-documents. The package's own dating is "
            "evidenced on its face: the ballot questions are headed \"2007 G.O. BOND QUESTIONS\", the bond issue "
            "table \"2007 G.O. BOND ISSUE\", and the planning schedule runs through 2006 naming the R-06-21 criteria "
            "resolution.")

SET_2013 = ("One sheet of a complete set of general obligation bond project scope tables sitting at the flat root of "
            "cip-documents. See the_undated_set for how it is dated and why the year must be confirmed before "
            "publication.")


def A(i, title, desc, date, pages, evidence, page, cross=None, extra=None, setnote=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
              "date": date, "pages": pages, "evidence": evidence,
              "proposed_canonical_page": page, "cross_listings": cross or []})
    if setnote:
        r["set"] = setnote
    if extra:
        r.update(extra)
    return r


# ---------------------------------------------------- 2007 bond election package
approved = [
 A("src-b55b2e3b16fbce5b",
   "2007 General Obligation Bond Election Questions",
   ("The ballot questions put to Albuquerque voters in the 2007 general obligation bond election, each stating the "
    "amount to be issued and the purposes the money may be spent on, purpose by purpose across the whole programme."),
   "2007", 3,
   ("Born-digital PDF with a full text layer, headed \"2007 G.O. BOND QUESTIONS\". The first question reads \"Shall "
    "the City of Albuquerque issue $12,184,000 of its general obligation bonds to design, develop, study, construct, "
    "modernize, automate, renovate, rehabilitate, recondition, landscape, furnish, enhance and otherwise improve, and "
    "to acquire land, vehicles, apparatus, and equipment for, police and fire department facilities?\""),
   CAPITAL,
   [{"page": SAFETY, "reason": "The first ballot question is the public safety bond and names police and fire facilities, vehicles and apparatus."}],
   extra={"canonical_of_group": "Three byte-identical copies of this file exist in the directory; the other two are recommended duplicate.",
          "why_retained": "The ballot question is the legal text voters actually approved, and it states each purpose's dollar figure. The archive holds bond scope tables for several programmes but no ballot questions for any of them."},
   setnote=SET_2007),

 A("src-1ecfc67085793132",
   "2007 General Obligation Bond Issue: Taxable and Non-Taxable Balance Table",
   ("The City's accounting table for the 2007 bond issue sets out proposed taxable and non-taxable amounts against "
    "prior balances, page by page across the programme, showing how each purpose's authorisation was composed."),
   "2007", 2,
   ("Born-digital PDF with a full text layer, headed \"2007 G.O. BOND ISSUE\" over a lettered column grid running A "
    "to J with headings Page, Proposed, Balance, Taxable, Non-Taxable, Proposed Non-Taxable and Balance."),
   CAPITAL, None,
   extra={"why_retained": "It is the financial reconciliation behind the ballot questions, and nothing of its kind is held for any bond programme.",
          "caution": "A dense numeric table with no narrative. It should be described as the issue's balance accounting rather than as a project list."},
   setnote=SET_2007),

 A("src-3d9162c12630506a",
   "2007 General Obligation Bond Summary Chart: Dollar Amounts and Percentages by Purpose",
   ("The summary chart apportions the 2007 general obligation bond programme across its purposes, giving each a "
    "dollar amount and a share of the whole, from affordable housing through zoo, biological park, museum and public "
    "safety bonds."),
   "2007", 1,
   ("Born-digital PDF with a full text layer, headed \"DOLLAR AMOUNTS AND PERCENTAGES BY PURPOSE\". Affordable "
    "Housing Bonds is shown at $10,100,000 and 6 per cent, followed by Zoo, Biological Park, Museum and Public Safety "
    "Bonds."),
   CAPITAL, None,
   extra={"why_retained": "The one page that shows the whole 2007 programme's shape at a glance. The archive holds a comparable funding allocation chart for 2009 and nothing for 2007."},
   setnote=SET_2007),

 A("src-8deb41aa3918bdb7",
   "Schedule of the Planning Process for the 2007 General Obligation Bond Programme",
   ("The dated schedule of the City's capital planning process leading to the 2007 bond election, listing each "
    "statutory and administrative step from the criteria resolution onward with the ordinance-mandated deadlines "
    "that govern them."),
   "2006", 2,
   ("Born-digital PDF with a full text layer, headed \"SCHEDULE OF THE PLANNING PROCESS\" and opening on 2006: \"Jan "
    "18 Introduction of Criteria Resolution (Ordinance mandated deadline)\" and \"R-06-21 Criteria Resolution passed "
    "by City Council\"."),
   CAPITAL, None,
   extra={"why_retained": ("It is the only record in the archive that shows the statutory rhythm of a bond cycle with "
                           "its deadlines. It also names R-06-21, the criteria resolution for this programme, which "
                           "is held nowhere — the archive does hold the equivalent enacted criteria resolution R-07-12 "
                           "for the 2009 programme, published at content/city-data/capital-spending.md."),
          "discovery_lead": "Criteria Resolution R-06-21."},
   setnote=SET_2007),

 A("src-3d99f4eec334285b",
   "Frequently Asked Questions and Answers: 2007 General Obligation Bond Programme",
   ("The City's explainer for voters answers what general obligation bonds are, how they are backed and redeemed, and "
    "how the capital programme that spends them is planned, selected and adopted."),
   "2007", 4,
   ("Born-digital PDF with a full text layer, headed \"FREQUENTLY ASKED QUESTIONS AND ANSWERS\". Its first answer "
    "reads: \"General Obligation Bonds (G.O. Bonds) are bonds backed by the full faith and credit of the City of "
    "Albuquerque. They may be redeemed by any regular source of City funding, but as a policy matter are generally "
    "redeemed by property taxes paid to the City.\""),
   CAPITAL, None,
   extra={"why_retained": "Plain-language explanation of the instrument behind most of what the capital spending page publishes. The archive has the tables and not the explanation.",
          "edition_note": "src-6e1fadf40a815ca1 is a differently typeset edition of the same explainer belonging to the later set; both are recommended and the relationship is recorded on each."},
   setnote=SET_2007),

 A("src-959009fa3fe01cd9",
   "Summary of the Planning Process: Capital Implementation Program",
   ("The City's summary of how the Capital Implementation Program works describes the division that administers it "
    "and the process by which capital projects are planned, selected and proposed to the City Council over the "
    "ten-year capital plan."),
   "2007", 2,
   ("Born-digital PDF with a full text layer, headed \"SUMMARY OF PLANNING PROCESS / Capital Implementation "
    "Program\". It states that the division \"administers the process by which capital improvement projects are "
    "planned, selected and proposed for adoption by the City Council. The capital plan covers a ten-year period\"."),
   CAPITAL, None,
   extra={"canonical_of_group": "Two byte-identical copies exist in the directory; the other is recommended duplicate.",
          "why_retained": "The narrative counterpart to the schedule above, and the only description in the archive of how the capital programme is actually assembled."},
   setnote=SET_2007),

 A("src-277e53d39ccd32af",
   "Revised Ordinances of Albuquerque, Article 12: Capital Improvements",
   ("The City ordinance governing capital improvements sets out the programme's intent and scope, how it is adopted "
    "and published, the City Council's role in it, and the rest of the statutory framework the bond cycle runs "
    "under."),
   None, 6,
   ("Born-digital PDF with a full text layer, headed \"ARTICLE 12: CAPITAL IMPROVEMENTS\" and listing sections 2-12-1 "
    "capital improvements program intent and scope, 2-12-2 adopting the capital improvements program and publication, "
    "and 2-12-3 city council participation. Internal references span 2000 to 2007."),
   CAPITAL, None,
   extra={"why_retained": ("It is the law the whole capital programme runs on, and the archive holds none of it. Every "
                           "bond record already published on the capital spending page is produced under these "
                           "sections."),
          "caution": ("An extract of the Revised Ordinances as they stood when this file was posted, not a current "
                      "codification. Label it with the posting context and point readers to the current code for "
                      "force.")},
   setnote=SET_2007),
]

SHEETS_2007 = [
 ("src-1ef3942c3d4cb415", "Affordable Housing Bonds", 1, PROJECTS,
  ("The 2007 affordable housing bond sheet assigns ten million dollars to citywide land acquisition for affordable "
   "housing under Council Bill F/S(3) O-06-8, with one per cent set aside for public art under the City's Art in "
   "Municipal Places ordinance."),
  ("Headed AFFORDABLE HOUSING BONDS. Affordable Housing Landbanking $10,000,000 for \"Land acquisition for affordable "
   "housing City-Wide, as provided in F/S(3) O-06-8\"; 1% for Public Art $100,000; Total $10,100,000."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-9b4cd97fc2be099b", "Energy Conservation, Public Facilities, and System Modernization Bonds", 2, FACILITIES,
  ("The 2007 energy conservation and public facilities bond sheet funds rehabilitation of City buildings for "
   "structural value and energy efficiency, replacement vehicles for Municipal Development, new roofs and security "
   "improvements at City facilities."),
  ("Headed ENERGY CONSERVATION, PUBLIC FACILITIES, AND SYSTEM MODERNIZATION BONDS. City Building Improvement and "
   "Rehabilitation $600,000; Replacement Vehicles; New Roofs for City Facilities $100,000; Security Improvements. "
   "References 2006."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet in the 2007 programme."}]),
 ("src-8933cccca7b7c3ff", "Parks and Recreation Bonds", 2, PARKS,
  ("The 2007 parks and recreation bond sheet funds community and neighbourhood park development — land, design and "
   "construction with buildings, storage and water features — and records a Council amendment expanding the project "
   "description, including Pat Hurley Park."),
  ("Headed PARKS AND RECREATION BONDS. Community Park Development $3,000,000; Neighborhood Park Development; Pat "
   "Hurley Park. It carries an explicit \"COUNCIL AMENDMENT: The Project Description attached hereto is expanded by "
   "adding the following\". References 2007."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet in the 2007 programme."}]),
 ("src-a9913e4be707e219", "Public Safety Bonds", 2, SAFETY,
  ("The 2007 public safety bond sheet funds fire station rehabilitation to maintain living and working conditions for "
   "emergency response personnel, fire apparatus replacement, work at Fire Station 2, and a second phase of radio "
   "frequency infrastructure."),
  ("Headed PUBLIC SAFETY BONDS. Fire Station Rehabilitation $750,000, naming stations 6, 7 and 17 \"or other "
   "facilities as the need may arise\"; Fire Apparatus Replacement; Fire Station 2 Rehabilitation; Radio Frequency "
   "Infrastructure, Phase II."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet in the 2007 programme."}]),
 ("src-51d8d424c326104e", "Public Transportation Bonds", 2, ABQRIDE,
  ("The 2007 public transportation bond sheet funds replacement and expansion of revenue vehicles to obtain the "
   "federal match, and improvements to the West Side Park and Ride facility at Central and Unser including pavement "
   "and sidewalks."),
  ("Headed PUBLIC TRANSPORTATION BONDS. Revenue Vehicles Replacement / Expansion (Transit) $2,750,000, noting the "
   "funds \"are required to obtain the federal match\"; West Side Park & Ride Improvements $1,250,000 at Central and "
   "Unser."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet in the 2007 programme."}]),
 ("src-eb26d8bc05ea810f", "Senior, Family, Community Center, and Community Enhancement Project Bonds", 2, CAPITAL,
  ("The 2007 senior, family and community centre bond sheet funds renovations, additions and security improvements at "
   "existing Family and Community Services facilities, with the whole allocation spent inside the 1980 City "
   "boundaries, and the North Domingo Baca multigenerational centre."),
  ("Headed SENIOR, FAMILY, COMMUNITY CENTER, AND COMMUNITY ENHANCEMENT PROJECT BONDS. Renovations, Additions and "
   "Security Improvements: Existing FCSD Facilities $500,000, with the condition that \"100% of funding will be spent "
   "within the 1980 boundaries\"; North Domingo Baca Park Multigenerational Center."),
  [{"page": PARKS, "reason": "It funds the North Domingo Baca multigenerational centre, and that park's master development plan is recommended for addition in councilor-district-4-cluster-research-2026-09-12.json."}]),
 ("src-d3efe770119ba686", "Zoo, Biological Park, Museum, and Cultural Facility Bonds", 2, CAPITAL,
  ("The 2007 zoo, biological park and museum bond sheet funds the second phase of the aquarium expansion with its "
   "three-storey Indo-Pacific reef tank, the Asian Experience and tiger habitat, and the Japanese Garden and Sasebo "
   "exhibition."),
  ("Headed ZOO, BIOLOGICAL PARK, MUSEUM, AND CULTURAL FACILITY BONDS. Aquarium Expansion, Phase II $1,800,000 for a "
   "\"three-story 500,000 gallon Indo-Pacific Reef Tank exhibit\" with an elevator to the top of the tank, noting "
   "\"Construction is expected to begin in 2009\"; Asian Experience / Tiger Habitat; Japanese Garden / Sasebo "
   "Exhibition."),
  None),
]
for i, title, pages, page, desc, ev, cross in SHEETS_2007:
    approved.append(A(i, "2007 " + title, desc, "2007", pages,
                      "Born-digital PDF with a full text layer. " + ev, page, cross, setnote=SET_2007))

SHEETS_LATER = [
 ("src-f87c2b7ead021f67", "Affordable Housing Bonds", 1, PROJECTS,
  ("The affordable housing bond sheet assigns ten million dollars to citywide land acquisition under Council Bill "
   "F/S(3) O-06-8, and records a Council amendment broadening the project to designate up to two million dollars for "
   "a further purpose."),
  ("Headed Affordable Housing Bonds. Affordable Housing $10,000,000 \"Land acquisition for affordable housing city "
   "wide, as provided in F/S(3) O-06-8\", with \"Council Amendment: The scope of this project is broadened to "
   "designate up to $2,000,000\"; 1% for Public Art."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-cf8de7cdd1e33ab5", "Library Bonds", 2, CAPITAL,
  ("The library bond sheet allocates funds by Council district for studying, designing, constructing, modernising, "
   "automating and furnishing libraries and for acquiring land for them, listing each district's share separately."),
  ("Headed Library Bonds, with entries District 1, Library Projects $350,000, District 6 and District 7, each "
   "described as \"Study, plan, design, develop, construct, rehabilitate, modernize, preserve, automate, upgrade, "
   "furnish, landscape and otherwise improve libraries and acquire land for libraries that benefit\" the district."),
  None),
 ("src-454e7b6319a9b1bd", "Museum and Cultural Facility Bonds", 2, CAPITAL,
  ("The museum and cultural facility bond sheet funds repairs and renovation at the South Broadway Cultural Center, "
   "replacing inefficient HVAC units serving the auditorium and gallery, addressing skylight inefficiencies, and "
   "replacing an ageing fire alarm system."),
  ("Headed Museum and Cultural Facility Bonds. South Broadway Cultural Center - Repairs and Renovation $350,000, "
   "covering HVAC for auditorium and gallery, sky lights, fire alarm replacement and audio and lighting systems. "
   "References 2013."),
  None),
 ("src-7f2c021eb265318b", "Parks and Recreation Bonds", 2, PARKS,
  ("The parks and recreation bond sheet funds park renovation across the City including all park amenities, and the "
   "renovation and development of swimming pools with their associated site improvements."),
  ("Headed Parks and Recreation Bonds. Park Renovation $2,500,000 to \"Plan, design, renovate, equip and construct "
   "park improvements, including all park amenities\"; Swimming Pool Renovation & Development $1,000,000."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-5d250f83bc10d354", "Public Safety Bonds", 2, SAFETY,
  ("The public safety bond sheet funds replacement of emergency response apparatus — fire engines, ladder trucks, "
   "hazmat rescue vehicles and brush trucks — together with renovations at Fire Station 13."),
  ("Headed Public Safety Bonds. Fire Apparatus Replacement $3,875,000 for \"Fire Engines, Ladder Trucks, Hazmat "
   "Rescue Vehicles and Brush Trucks\"; Fire Station 13 Renovations."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-b115ed6fef212714", "Public Transportation Bonds", 2, ABQRIDE,
  ("The public transportation bond sheet funds replacement and expansion of revenue and support vehicles with their "
   "associated equipment, stating that the local bond money is required to draw down federal funds and reach "
   "sufficient combined funding."),
  ("Headed Public Transportation Bonds. Revenue and Support Vehicle Replacement / Expansion $5,200,000, noting "
   "\"These local GO Bond funds are required to obtain federal funds and provide sufficient combined funding\"."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-fbea59110f9af935", "Senior, Family, Community Center, and Community Enhancement Project Bonds", 2, CAPITAL,
  ("The senior, family and community centre bond sheet funds remediation, renovations, additions and security "
   "improvements at existing Family and Community Services facilities and sites, covering design, demolition, "
   "construction, equipment and furnishing."),
  ("Headed Senior, Family, Community Center, and Community Enhancement Project Bonds. Remediation, Renovations, "
   "Additions and Security Improvements: Existing FCSD Facilities $500,000."),
  None),
 ("src-45b2bd5570996347", "Storm Sewer System Bonds", 2, STORM,
  ("The storm sewer bond sheet funds work to comply with the City's federal municipal separate storm sewer permit, "
   "covering public education, public involvement, best management practices and stormwater quality activities under "
   "the NPDES programme."),
  ("Headed Storm Sewer System Bonds. NPDES Stormwater Quality $1,200,000 for \"work activities to achieve compliance "
   "with our EPA Municipal Separate Storm Sewer (MS4) permit\", listing Public Education, Public Involvement and Best "
   "Management Practices."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-189ef27f66da7fef", "Street Bonds", 3, TXPLANS,
  ("The street bond sheet funds the Osuna Road widening between Edith and Interstate 25, Lead and Coal improvements "
   "from Interstate 25 to Broadway, major street and intersection reconstruction, and replacement of regulatory and "
   "informational signs to federal specifications."),
  ("Headed Street Bonds. Osuna Road Widening $500,000 for Osuna between Edith and I-25; Lead and Coal Improvements, "
   "I-25 to Broadway; Reconstruction Major Streets $500,000. A sign entry records that regulatory replacements are "
   "required by 12/31/2014 and informational sign replacements by 12/31/2017, at a total estimated cost of "
   "$11,300,000."),
  [{"page": CAPITAL, "reason": "It is a bond purpose sheet and belongs with the programme's other purposes."}]),
 ("src-72def9da3ba1d799", "Zoo and Biological Park Bonds", 2, CAPITAL,
  ("The zoo and biological park bond sheet funds renovation and repair of outdated BioPark facilities, covering "
   "utilities, life support systems, animal enclosures, public amenities, electronic equipment and landscaping, and "
   "remodelling of existing buildings."),
  ("Headed Zoo and Biological Park Bonds. Renovation & Repair (BioPark) $1,500,000 to \"Design, construct, equip, "
   "furnish and renovate current outdated facilities, to include utilities, life support, animal enclosures, public "
   "amenities, electronic equipment, and landscaping\"."),
  None),
]
for i, title, pages, page, desc, ev, cross in SHEETS_LATER:
    approved.append(A(i, title + " (General Obligation Bond Project Scopes, undated set)", desc, None, pages,
                      "Born-digital PDF with a full text layer. " + ev, page, cross, setnote=SET_2013,
                      extra={"caution": "The year is not printed on this sheet. See the_undated_set; it must be established before publication."}))

approved.append(A("src-6e1fadf40a815ca1",
 "Frequently Asked Questions and Answers: General Obligation Bonds (undated set)",
 ("The City's explainer for voters answers what general obligation bonds are, how they are backed and redeemed, and "
  "how the capital programme that spends them is planned, in a later and differently typeset edition of the same "
  "questions."),
 None, 4,
 ("Born-digital PDF with a full text layer, headed \"Frequently Asked Questions and Answers\" in mixed case where the "
  "2007 edition uses full capitals. The first answer is materially the same text about full faith and credit and "
  "redemption from property taxes."),
 CAPITAL, None,
 extra={"edition_note": "A differently typeset edition of src-3d99f4eec334285b. Both are recommended: they belong to different programme packages and neither contains the other.",
        "caution": "Undated, like the rest of the flat set."},
 setnote=SET_2013))

# ------------------------------------------------------------------- duplicates
duplicates = []
for i, canon, what, basis in [
 ("src-69e0f8d7f13b52c5", "src-b55b2e3b16fbce5b", "2007 bond election questions (2007-election-documents copy)",
  "internal"),
 ("src-8d49558bccd018a6", "src-b55b2e3b16fbce5b", "2007 bond election questions (bond-election.pdf copy)",
  "internal"),
 ("src-c35e132701113c4d", "src-959009fa3fe01cd9", "Summary of the planning process (2007-election-documents copy)",
  "internal"),
 ("src-c8891cd2a4655f74", "src-888427a6abc5edf0", "Library bond project scopes", "archived"),
 ("src-573991b6788eb8cb", "src-6fc996f849849028", "Street bond project scopes", "archived"),
 ("src-8198e95c6a898c26", "src-b17fb11a9e63c180", "2011 Streets general obligation bond project scope", "archived"),
 ("src-2b2fc5cb64d08910", "src-230753126ba3bbf7",
  "Rules and Regulations Governing Compensation for Consulting Engineers, Architects, and Landscape Architects",
  "archived"),
]:
    c = IDX[canon]
    r = row(i, "duplicate")
    r.update({"title_for_reference": what, "canonical_id": canon, "hash_found_it": True})
    if basis == "internal":
        r.update({"canonical_url": IDX[canon].get('direct_file_url'),
                  "canonical_state": "recommended for addition in this batch",
                  "basis": "The City posts the same file at more than one path inside this directory.",
                  "measurement": "Byte-identical to the canonical: %d bytes, SHA-256 %s." % (M[i]['size_bytes'], M[i]['checksum_sha256'])})
    else:
        assert c['status'] == 'validated', canon
        assert c['checksum_sha256'] == M[i]['checksum_sha256'], (i, canon)
        r.update({"canonical_url": c.get('r2_url'),
                  "canonical_state": "validated, R2-archived and published at " + (c.get('implementation_location') or 'its recorded page'),
                  "basis": "A second Council-server path for a document the archive already holds.",
                  "measurement": ("Byte-identical to the canonical: %d bytes and SHA-256 %s, matching the validated "
                                  "record's recorded values exactly." % (M[i]['size_bytes'], M[i]['checksum_sha256'])),
                  "canonical_recorded_title": c.get('title'),
                  "canonical_recorded_date": c.get('date')})
    duplicates.append(r)

# --------------------------------------------------------------------- excluded
FORM = ("A blank administrative form used to transact capital-programme business. Blank forms are excluded throughout "
        "this run, the split established in planning-udd-cluster-research-2026-09-11.json between an adopted standard "
        "and a submittal form.")
excluded = []
for i, what in [("src-cf6ea129deaacd75", "Additional services request form"),
                ("src-7db522c233d09f76", "Application for payment form"),
                ("src-c5a719e610edf283", "Change order form"),
                ("src-9b8823612d4eae10", "Request for payment for services form")]:
    r = row(i, "excluded")
    r.update({"title_for_reference": what + " (cip-forms-documents)", "exclusion_reason": FORM, "category": "blank form"})
    excluded.append(r)

for i in sorted(k for k in M if MAGIC[k] == '3c21444f'):
    r = row(i, "excluded")
    r.update({"title_for_reference": (IDX[i].get('title') or 'collection landing page'),
              "exclusion_reason": "The Plone collection landing page for this path, not a document.",
              "category": "collection landing page"})
    excluded.append(r)

rows = approved + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(M), (set(M) - set(ids), set(ids) - set(M))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
avoided = sum(r["size_bytes"] for r in duplicates)
npdf = sum(1 for r in rows if r["content_kind"] == "PDF")
nhtml = sum(1 for r in rows if r["content_kind"] == "HTML")
n2007 = sum(1 for r in approved if r.get("set") == SET_2007)
nlater = sum(1 for r in approved if r.get("set") == SET_2013)

artifact = {
 "batch_id": "cip-documents-cluster-research-2026-09-12",
 "lane": "Claude research lane: the cip-documents subtree of www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the first slice of the municipaldevelopment/documents lane.",
 "cluster": "The City's Capital Implementation Program document library: the 2007 general obligation bond election package, a second undated set of bond scope sheets, the CIP forms, and the capital improvements ordinance.",
 "scope": ("All 42 pending-review candidates in cip-documents that are not already rows in a saved artifact. The "
           "subtree's 2003, 2007 decade plan, 2009, 2011 and 2017 folders were triaged in earlier runs and are "
           "untouched here; the coverage gate in this generator asserts no overlap."),
 "brief": "A dated research decision file for the first slice of the municipaldevelopment/documents lane, claimed against the artifact-coverage set.",
 "brief_finding": ("Two complete general obligation bond programme packages that the archive does not hold. The "
                   "first is the 2007 bond election package — ballot questions, issue table, summary chart, planning "
                   "schedule, voter FAQ, process summary, the capital improvements ordinance and seven purpose "
                   "sheets. The second is an undated set of ten purpose sheets at the flat root that matches none of "
                   "the archived programmes. The archive already publishes bond scope tables for 2003, 2009, 2011 and "
                   "2017 and a 2007 decade plan; it holds no ballot questions for any programme and no ordinance."),
 "method": ("Ran the URL group-by first; no collisions. Fetched all 42 candidates and measured byte length and "
            "SHA-256 from the fetched bytes, verifying every container by leading bytes. Compared every checksum "
            "within the slice and against the 1,612 checksummed inventory records, and every size against recorded "
            "sizes. Fetched three archived 2009 R2 objects read-only to test whether the flat set is a second edition "
            "of the 2009 scopes. Read every PDF's header and opening entries rather than classifying from filenames, "
            "and searched each purpose sheet for a printed year."),
 "classification_only": True,
 "shared_state_written": [],
 "the_undated_set": {
  "what_it_is": ("Ten general obligation bond purpose sheets plus a voter FAQ, sitting at the flat root of "
                 "cip-documents under underscore filenames — affordable_housing_bonds.pdf, library_bonds.pdf, "
                 "museum_and_cultural_facility_bonds.pdf and so on."),
  "the_problem": "No programme year is printed on nine of the eleven sheets.",
  "what_was_ruled_out": {
   "2009": ("The 2009 folder contains files with exactly the same names. Three were fetched from R2 and compared: "
            "parks ratio 0.8222 with coverage 0.5338 and 0.5657; street ratio 0.9492 with coverage 0.7089 and 0.6857; "
            "storm ratio 0.9430 with coverage 0.6609 and 0.6337. Similar subject matter, different documents — not "
            "editions of one another."),
   "2003, 2007, 2011, 2017": ("No checksum in the flat set matches any record in those folders, and the 2017 sheets "
                              "are 110,000 to 160,000 bytes against this set's 33,000 to 59,000."),
  },
  "what_points_to_2013": [
   "museum_and_cultural_facility_bonds.pdf references 2013 in its text.",
   ("street_bonds.pdf cites federal sign-replacement deadlines of 12/31/2014 for regulatory signs and 12/31/2017 for "
    "informational signs, which are forward-looking from a programme of about this date."),
   ("The archive already holds one validated record dated 2013 sitting in this same flat directory rather than in a "
    "year folder: src-3cc1912d7ac89cf9, \"2013 Energy and Water Conservation, Public Facilities, and System "
    "Modernization Bonds\". The flat directory is where 2013 material lives."),
   "The archive holds no 2013 bond scope set, so a complete set with no year folder fits the gap.",
  ],
  "why_it_is_not_asserted": ("None of that is the year printed on the sheets. Publishing a bond table under the wrong "
                             "programme year would misstate what voters authorised, and every comparable entry on "
                             "content/city-data/capital-spending.md carries a year."),
  "recommended_action": ("Approve the sheets and establish the year before publication — the City's bond ordinance "
                         "series or the Council's criteria resolution for the cycle will settle it. Each row carries "
                         "the caution."),
 },
 "a_dating_conflict_in_the_2007_folder": {
  "finding": ("Two files inside cip-documents/2007-election-documents are byte-identical to records the archive has "
              "validated, archived and published as 2003: library-bonds.pdf matches src-888427a6abc5edf0, \"2003 "
              "Library General Obligation Bond Project Scopes\", and street-bonds.pdf matches src-6fc996f849849028, "
              "\"2003 Street General Obligation Bond Project Scopes\". Both archived records were captured from "
              "cip-documents/2003-bond-doc/."),
  "the_tension": ("Their sibling sheets in the same 2007 folder reference 2006, 2007 and 2009 on their faces — the "
                  "zoo sheet says construction of the aquarium phase is \"expected to begin in 2009\" — so the folder "
                  "reads as a genuine 2007 package. Either the City reused two 2003 sheets in its 2007 folder, or the "
                  "2003 attribution on those two archived records is wrong."),
  "what_this_lane_does": ("Recommends both as duplicate, because the bytes are identical and only one copy needs "
                          "archiving either way, and flags the year question rather than resolving it. The canonical "
                          "records' recorded titles and dates are carried on each duplicate row so the conflict is "
                          "visible at the point of application."),
  "for_integration": "Confirm the year on those two archived records before relying on their published dates. Claude did not modify them.",
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "byte_identical_to_validated_records": 4,
  "internal_byte_duplicate_groups": 2,
  "r2_objects_fetched": 3,
  "result": ("Four candidates are already held. The three R2 fetches were spent disproving a hypothesis rather than "
             "confirming one, which is what kept the flat set from being recorded as a second edition of the 2009 "
             "scopes."),
  "footprint_effect": f"{avoided:,} bytes kept out of the upload queue.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 2,
  "internal_collision_group_sizes": [3, 2],
  "cross_inventory_byte_collisions": 4,
  "url_collisions_in_this_slice": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 6,
  "relationships_ruled_out_by_text": 3,
  "note": ("Hashing found all six real relationships here, because this directory is full of the same file posted at "
           "more than one path. Text comparison earned its place the other way round: it ruled out three "
           "same-filename pairs against the 2009 set that hashing could not have distinguished from unrelated files."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved if r.get("set") == SET_2007],
   "finding": f"The complete 2007 general obligation bond election package, {n2007} records: ballot questions, issue table, summary chart, planning schedule, voter FAQ, process summary, the capital improvements ordinance and seven purpose sheets. The archive holds no ballot questions for any bond programme and no capital improvements ordinance.",
   "recommended_action": "Approve and place on the capital spending page with subject cross-listings. The ballot questions and the ordinance are the two that fill genuine category gaps."},
  {"severity": "date-before-publishing",
   "affects": [r["id"] for r in approved if r.get("set") == SET_2013],
   "finding": f"A complete set of {nlater} bond purpose sheets and a voter FAQ with no programme year printed on nine of them. Evidence points to 2013 but does not establish it.",
   "recommended_action": "Approve, then establish the year from the City's bond ordinance series before publishing. Do not infer it from the directory."},
  {"severity": "dating-conflict",
   "affects": ["src-c8891cd2a4655f74", "src-573991b6788eb8cb", "src-888427a6abc5edf0", "src-6fc996f849849028"],
   "finding": "Two files in the 2007 election folder are byte-identical to records published as 2003 bond scopes, while their sibling sheets reference 2006 to 2009.",
   "recommended_action": "Record the two candidates as duplicate and confirm the year on the two archived records. Claude did not modify them."},
  {"severity": "discovery-lead",
   "affects": ["src-8deb41aa3918bdb7"],
   "finding": "The 2007 planning schedule names Criteria Resolution R-06-21, passed by the City Council, which the archive does not hold. The equivalent for the 2009 programme, enacted resolution R-07-12, is already published on the capital spending page.",
   "recommended_action": "Queue R-06-21. The archive has one criteria resolution and the schedule that names the other."},
  {"severity": "category-gap",
   "affects": ["src-277e53d39ccd32af"],
   "finding": "Revised Ordinances Article 12, Capital Improvements, is the statutory basis for every bond record already published on the capital spending page, and none of it is held.",
   "recommended_action": "Approve, labelled as the ordinance text as posted rather than a current codification."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "archive_fetches": "Three R2 objects at files.abqinfo.com were fetched read-only for comparison, all HTTP 200 at their recorded byte sizes.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": f"{npdf} genuine PDFs and {nhtml} HTML collection pages by leading bytes. No content substitution in this slice. Every PDF has a full text layer; none needed rendering."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are static PDFs and are inventory-only until an R2 archive "
                   f"object exists for each and its public download, exact size, SHA-256, and authoritative-source "
                   f"provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, "
                   f"small for the number of records because bond purpose sheets are short tables. Every one is "
                   f"born-digital with a full text layer, so all are searchable once archived."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Seven duplicate rows carry canonical_ids: four "
                      "point at validated, R2-archived records and are confirmed byte-identical against the "
                      "inventory's own recorded checksums, and three point at canonicals recommended for addition in "
                      "this same batch. No row requires human review; this slice contains no unenacted legislation, "
                      "and the capital improvements ordinance is codified law rather than a bill. Every row carries a "
                      "leading_bytes field and every approved row carries a set field naming which programme package "
                      "it belongs to. The undated set must be dated before publication. Sizes and checksums are first "
                      "measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the three R2 objects were fetched read-only and not modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
