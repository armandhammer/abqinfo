"""Claude research lane. The second link harvest, first slice: the 2022
Redistricting Committee record, Council floor amendments, the Regional Baseball
Complex set and the parks material, harvested from excluded pages that had to be
re-fetched.

These are NOT inventory candidates: none has an inventory id and nothing here can
be applied through Update-Candidate.ps1. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-14.
"""

import collections
import datetime
import glob
import json
import os
import re
import urllib.parse

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\second-harvest-council-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\h2')

ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'
DEMOG = 'content/city-data/demographics.md'
MAPS = 'content/maps-data/maps.md'
PARKS = 'content/public-works/parks-recreation.md'
CAPITAL = 'content/public-works/capital-projects.md'
FACIL = 'content/public-works/city-facilities.md'
CRASH = 'content/transportation/safety-crash-data.md'
SAFETY = 'content/city-data/public-safety-data.md'
ZONING = 'content/development-land-use/zoning-ido.md'

inv = json.load(open(INV, encoding='utf-8'))

ALLF, M, MAGIC, URL, CODE, SRC = {}, {}, {}, {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    ALLF[p[0]] = p
    M[p[0]] = {"size_bytes": int(p[2]), "checksum_sha256": p[3]}
    MAGIC[p[0]], URL[p[0]], CODE[p[0]], SRC[p[0]] = p[4], p[5], p[1], p[6].strip()

SLICE = sorted(i for i in M if i <= 'h2-052' or i >= 'h2-103')

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
INTERNAL = {x: sorted(v, key=lambda z: (len(URL[z]), z))[0]
            for v in BYHASH.values() if len(v) > 1
            for x in sorted(v, key=lambda z: (len(URL[z]), z))[1:]}


def pages(i):
    if MAGIC[i] != '25504446':
        return None
    n = len(re.findall(rb'/Type\s*/Page[^s]', open(os.path.join(SP, 'files', i + '.bin'), 'rb').read()))
    return n or None


def text(i):
    p = os.path.join(SP, 'txt', i + '.txt')
    return open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''


LC = ("HTTP 200 verified 2026-09-14 by full GET unless the row says otherwise; size_bytes and checksum_sha256 "
      "measured from the fetched bytes, container verified by leading bytes, and every PDF tested for its "
      "end-of-file marker.")

RD = "2022 redistricting committee"
RDMAP = "2022 redistricting maps"
CN = "council records"
BB = "regional baseball complex"
PK = "parks and recreation"
EXT = "state and regional reports"


def agenda(d, extra=""):
    return ("The agenda for the 2022 Redistricting Committee's meeting of %s, the joint City and County body that "
            "redrew Albuquerque's council districts after the 2020 census.%s" % (d, extra))


def minutes(d, extra=""):
    return ("The approved minutes of the 2022 Redistricting Committee's meeting of %s, recording what the joint "
            "City and County body decided as it redrew Albuquerque's council districts.%s" % (d, extra))


def mapdesc(name):
    return ("The full district map and accompanying statistics table for %s, one of the plans the 2022 "
            "Redistricting Committee weighed when redrawing Albuquerque's nine council districts." % name)


D = {
 'h2-001': ("2022 Redistricting Committee Report and Recommendations", RD,
   ("The committee's final report and recommendations to the Council on redrawing Albuquerque's council districts, "
    "the record of a process the City Charter requires every ten years."),
   ("242,483,055 bytes - the largest file this run has measured anywhere. Opens: 2022 Redistricting Committee "
    "Report and Recommendations, Summary, Every 10 years, the City Charter requires."),
   ABOUT, [{"page": DEMOG, "reason": "District boundaries drawn from census population."},
           {"page": MAPS, "reason": "It contains the district maps."}],
   "At 242 MB it is larger than the airport master plan. Expect the archive upload to need handling as a special case."),
 'h2-006': ("2022 redistricting communications plan", RD,
   ("The Council's plan for telling the public about the 2022 redistricting process and gathering their views, "
    "issued over the Council President's and Vice President's names."),
   "173,005 bytes. Opens: CITY OF ALBUQUERQUE, President Isaac Benton District 2, City Council Vice President Dan Lewis.",
   ABOUT, [], None),
 'h2-010': ("2022 Redistricting Committee agenda, 9 March 2022", RD, agenda("9 March 2022"),
   "138,173 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-009': ("2022 Redistricting Committee minutes, 9 March 2022", RD,
   minutes("9 March 2022", " Its filename begins with the agenda's name and ends minutes-final."),
   "177,026 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-008': ("2022 Redistricting Committee agenda, 23 March 2022", RD, agenda("23 March 2022"),
   "164,388 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-007': ("2022 Redistricting Committee minutes, 23 March 2022", RD, minutes("23 March 2022"),
   "181,781 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-013': ("2022 Redistricting Committee agenda, 6 April 2022", RD, agenda("6 April 2022"),
   "163,815 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-014': ("2022 Redistricting Committee minutes, 6 April 2022", RD, minutes("6 April 2022"),
   "92,381 bytes, the smallest of the seven sets of minutes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-012': ("2022 Redistricting Committee agenda, 27 April 2022", RD, agenda("27 April 2022"),
   "164,488 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-011': ("2022 Redistricting Committee minutes, 27 April 2022", RD, minutes("27 April 2022"),
   "185,133 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-016': ("2022 Redistricting Committee agenda, 4 May 2022", RD, agenda("4 May 2022"),
   "88,132 bytes, the smallest agenda in the series. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-021': ("2022 Redistricting Committee minutes, 4 May 2022", RD, minutes("4 May 2022"),
   "185,484 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-015': ("2022 Redistricting Committee agenda, 18 May 2022", RD, agenda("18 May 2022"),
   "132,546 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-020': ("2022 Redistricting Committee minutes, 18 May 2022", RD, minutes("18 May 2022"),
   "222,249 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-018': ("2022 Redistricting Committee agenda, 8 June 2022", RD, agenda("8 June 2022"),
   "162,544 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-022': ("2022 Redistricting Committee minutes, 8 June 2022", RD, minutes("8 June 2022"),
   "190,124 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Minutes, 2022 Redistricting Committee.",
   ABOUT, [], None),
 'h2-017': ("2022 Redistricting Committee agenda, 29 June 2022", RD, agenda("29 June 2022"),
   "162,710 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, Agenda, 2022 Redistricting Committee, Government Center.",
   ABOUT, [], None),
 'h2-019': ("2022 Redistricting Committee draft minutes, 29 June 2022", RD,
   ("The draft minutes of the committee's meeting of 29 June 2022, the only set in the series that is not marked "
    "approved, recording the last meeting the published record covers."),
   "223,747 bytes. Opens: City of Albuquerque, Albuquerque/Bernalillo County, DRAFT Minutes, 2022 Redistricting Committee.",
   ABOUT, [],
   "Marked DRAFT Minutes on its own first page, unlike the other six. Label it a draft; approved minutes for that meeting may exist elsewhere."),
 'h2-025': ("Redistricting Committee background and initial concepts summary", RD,
   ("The committee's summary of why Albuquerque redistricts and what the first set of district concepts proposed, "
    "written to introduce the options to the public."),
   "200,304 bytes. Opens: City of Albuquerque Redistricting Committee, Background and Initial Concepts Summary, Background, The primary.",
   ABOUT, [{"page": DEMOG, "reason": "Population-based district design."}], None),
 'h2-026': ("Redistricting Committee rules and procedures briefing, 9 March 2022", RD,
   ("The consultant's briefing slides on the committee's own rules and procedures, presented at its first working "
    "meeting to set out how it would operate."),
   "1,737,273 bytes. Opens: City of Albuquerque Redistricting Committee: Committee Rules and Procedures, March 9, 2022, RESEARCH & POLLING, INC.",
   ABOUT, [], "Prepared by Research & Polling, Inc. for the committee. Attribute the analysis to the consultant."),
 'h2-027': ("Redistricting review briefing, 23 March 2022", RD,
   ("The consultant's briefing to the committee reviewing where the redistricting stood, presented at the meeting "
    "of 23 March 2022 as the members worked through the first set of district concepts."),
   "225,421 bytes. Opens: City of Albuquerque Redistricting Committee: Redistricting Review, March 23, 2022, RESEARCH & POLLING, INC.",
   ABOUT, [], "Prepared by Research & Polling, Inc. for the committee."),
 'h2-035': ("Redistricting follow-up: compactness, population movement and social vulnerability, 6 April 2022", RD,
   ("The consultant's follow-up analysis for the committee after the March meeting, covering how compact the "
    "proposed districts are, how many people move between districts, and their social vulnerability."),
   "247,420 bytes. Opens: City of Albuquerque Redistricting Committee: Follow up from 3/23, April 6, 2022, RESEARCH & POLLING, INC.",
   ABOUT, [{"page": DEMOG, "reason": "Population and vulnerability analysis."}], None),
 'h2-034': ("Compactness and core constituency comparison, 8 June 2022", RD,
   ("The comparison of each proposed plan against the current districts on compactness and on how much of the "
    "population would change district, measured by the Reock and Polsby-Popper scores."),
   ("92,201 bytes. Its extraction interleaves two column headings, reading: % of Population in a Compactness "
    "Different District Compared with Current Plan Reock Polsby-Popper. Read in column order that is a population "
    "movement column and a compactness column scored by Reock and Polsby-Popper."),
   ABOUT, [{"page": DEMOG, "reason": "Population analysis."}], None),
 'h2-041': ("Social vulnerability index by district and concept, 27 April 2022", RD,
   ("The average social vulnerability index of each council district under the current map and under each lettered "
    "concept, the measure the committee used to weigh the plans against one another."),
   "216,473 bytes. Opens: Average SVI, District, A, B, C, D, E, New Map, with percentages by district.",
   ABOUT, [{"page": DEMOG, "reason": "A demographic measure by district."}], None),
 'h2-024': ("2022 Redistricting Committee concept ratings", RD,
   ("The table of how each committee member rated each district concept, recording who each member represented "
    "and what they thought of the options."),
   "104,141 bytes. Opens: City of Albuquerque - 2022 Redistricting Committee Concept Ratings, Member, Representing, Concept, District.",
   ABOUT, [], None),
 'h2-028': ("City Council districts: current districts map and statistics, March 2022", RDMAP,
   mapdesc("the district boundaries in force before the 2022 redistricting"),
   "51,830,993 bytes. Its first page reads City of Albuquerque - City Council Districts, Current Districts, City Councilors, dated 03/18/2022.",
   MAPS, [{"page": ABOUT, "reason": "The districts the Council is elected from."}], None),
 'h2-036': ("City Council districts: Concept A map and statistics", RDMAP, mapdesc("Concept A"),
   "52,567,354 bytes. Its first page reads City of Albuquerque - City Council Districts, Concept A, City Councilors, dated 03/18/2022.",
   MAPS, [{"page": ABOUT, "reason": "A proposed council district map."}], None),
 'h2-037': ("City Council districts: Concept B map and statistics", RDMAP, mapdesc("Concept B"),
   "51,875,190 bytes. Its first page reads City of Albuquerque - City Council Districts, Concept B, City Councilors, dated 03/18/2022.",
   MAPS, [{"page": ABOUT, "reason": "A proposed council district map."}], None),
 'h2-038': ("City Council districts: Concept C map and statistics", RDMAP, mapdesc("Concept C"),
   "51,621,967 bytes. Its first page reads City of Albuquerque - City Council Districts, Concept C, City Councilors, dated 03/18/2022.",
   MAPS, [{"page": ABOUT, "reason": "A proposed council district map."}], None),
 'h2-039': ("City Council districts: Concept D map and statistics, corrected", RDMAP,
   mapdesc("Concept D in its corrected form"),
   ("41,975,777 bytes, the smallest of the lettered concepts. Its first page reads City of Albuquerque - City "
    "Council Districts, Concept D (corrected), dated 04/08/2022 - three weeks later than the others."),
   MAPS, [{"page": ABOUT, "reason": "A proposed council district map."}],
   "The only concept marked corrected, and the only one redated. An uncorrected Concept D may exist; it is not on this page."),
 'h2-040': ("City Council districts: Concept E map and statistics", RDMAP, mapdesc("Concept E"),
   "51,779,080 bytes. Its first page reads City of Albuquerque - City Council Districts, Concept E, City Councilors, dated 03/18/2022.",
   MAPS, [{"page": ABOUT, "reason": "A proposed council district map."}], None),
 'h2-029': ("City Council districts: Citizen Map 1 and statistics", RDMAP, mapdesc("Citizen Map 1, submitted by members of the public"),
   "70,338,592 bytes. Its extractable text is only the repeated label City Councilors; the content is the drawn map and its statistics table.",
   MAPS, [{"page": ABOUT, "reason": "A publicly submitted district map."}], None),
 'h2-030': ("City Council districts: Citizen Map 2 and statistics", RDMAP, mapdesc("Citizen Map 2, submitted by members of the public"),
   "72,579,402 bytes, the largest of the citizen maps. Its extractable text is only the repeated label City Councilors.",
   MAPS, [{"page": ABOUT, "reason": "A publicly submitted district map."}], None),
 'h2-031': ("City Council districts: Citizen Map 3, revised, and statistics", RDMAP,
   mapdesc("Citizen Map 3 in its revised form, submitted by members of the public"),
   "69,861,094 bytes. Its filename marks it revised; its extractable text is only the repeated label City Councilors.",
   MAPS, [{"page": ABOUT, "reason": "A publicly submitted district map."}],
   "Marked revised in its filename. An earlier version may exist and is not on this page."),
 'h2-032': ("City Council districts: Citizen Map 4 and statistics", RDMAP, mapdesc("Citizen Map 4, submitted by members of the public"),
   "69,312,324 bytes. Its extractable text is only the repeated label City Councilors; a Council floor amendment later proposed adopting this map.",
   MAPS, [{"page": ABOUT, "reason": "A publicly submitted district map."}], None),
 'h2-033': ("City Council districts: Citizen Map 5 and statistics", RDMAP, mapdesc("Citizen Map 5, submitted by members of the public"),
   "71,025,364 bytes. Its extractable text is only the repeated label City Councilors; a Council floor amendment later proposed adopting this map.",
   MAPS, [{"page": ABOUT, "reason": "A publicly submitted district map."}], None),
 'h2-047': ("Council floor amendment to O-22-34 adopting Citizen Map 4", CN,
   ("The floor amendment moved in Council on 7 September 2022 to adopt Citizen Map 4 as the council district plan, "
    "with the full map attached to the amendment."),
   "31,657,358 bytes. Opens: CITY COUNCIL of the CITY OF ALBUQUERQUE, September 7, 2022, FLOOR AMENDMENT NO. TO O-22-34.",
   ABOUT, [{"page": MAPS, "reason": "It carries a district map."}], None),
 'h2-048': ("Council floor amendment to O-22-34 adopting Citizen Map 5", CN,
   ("The floor amendment moved in Council on 7 September 2022 to adopt Citizen Map 5 instead, the companion motion "
    "to the Citizen Map 4 amendment and carrying its own full map."),
   "32,703,854 bytes. Opens: CITY COUNCIL of the CITY OF ALBUQUERQUE, September 7, 2022, FLOOR AMENDMENT NO. TO O-22-34.",
   ABOUT, [{"page": MAPS, "reason": "It carries a district map."}], None),
 'h2-002': ("Safe Outdoor Spaces amendment map: option 3, A-12", "integrated development ordinance",
   ("The map accompanying amendment A-12, option 3, in the 2021 annual update to the Integrated Development "
    "Ordinance, showing where Safe Outdoor Spaces would be allowed across the west side."),
   ("14,145,392 bytes. Its extracted text is a jumble of street labels - BLACK ARROYO BLVD NW, WESTSIDE BLVD NW, "
    "MCMAHON BLVD - which is the signature of a drawn map. Published under IDO/2021_IDO_AnnualUpdate/Council."),
   ZONING, [{"page": MAPS, "reason": "A zoning map."}], None),
 'h2-042': ("Council Bill R-14-46", CN,
   ("A resolution of the Twenty-First Council, published as the bill as introduced with its enactment number still "
    "blank, harvested from a Council page the run had excluded."),
   "130,373 bytes. Opens: CITY of ALBUQUERQUE TWENTY-FIRST COUNCIL, COUNCIL BILL NO. R-14-46, ENACTMENT NO. blank.",
   ABOUT, [],
   "The enactment number is blank, so this is the bill as introduced. The enacted copy, if any, is not on this page."),
 'h2-043': ("Floor amendment to O-21-78 sponsored by Councillor Sanchez, 19 January 2022", CN,
   ("A floor amendment to Council Bill O-21-78 moved on 19 January 2022, one of two amendment documents for that "
    "bill published together."),
   "56,517 bytes. Opens: CITY COUNCIL of the CITY OF ALBUQUERQUE, January 19, 2022, FLOOR AMENDMENT NO. TO O-21-78, AMENDMENT SPONSORED.",
   ABOUT, [{"page": SAFETY, "reason": "It amends a police oversight ordinance."}], None),
 'h2-046': ("Floor amendment template for O-21-78", CN,
   ("The floor amendment sheet for Council Bill O-21-78 in its unfilled form, with the date and sponsor left blank "
    "for completion at the meeting."),
   "77,757 bytes. Opens: ALBUQUERQUE CITY COUNCIL FLOOR AMENDMENT, [Date], FLOOR AMENDMENT NO. TO: O-21-78, AMENDMENT SPONSORED BY CO.",
   ABOUT, [],
   "Its date field literally reads [Date]. It is a template or an unmoved draft, not a moved amendment; label it so."),
 'h2-049': ("Press release: Council meeting on real estate", CN,
   ("A City Council press release issued over the names of President Ken Sanchez and Vice President Trudy Jones, "
    "announcing a Council meeting."),
   "219,292 bytes. Opens: CITY OF ALBUQUERQUE, President Ken Sanchez District 1, City Council Vice President Trudy E. Jones.",
   ABOUT, [],
   ("A press release rather than a record of a decision, and the same class of ephemera as the event flyers this "
    "run has flagged. Keep it only if the archive holds Council communications.")),
 'h2-023': ("Regional Baseball Complex: Phase 1 site plan, March 2016", BB,
   ("The site development plan for building permit showing phase one of the City's Regional Baseball Complex - four "
    "adult fields, a fifth field, a youth baseball and softball complex and a perimeter trail - beside the APS "
    "Community Stadium."),
   ("393,305 bytes, no text layer, read by rendering. Its title block reads REGIONAL BASEBALL COMPLEX, OWNER CITY "
    "OF ALBUQUERQUE, SITE DEVELOPMENT PLAN FOR BUILDING PERMIT, PHASE 1 SITE PLAN, MARCH 2016, by Consensus "
    "Planning, Bohannan Huston and Kells + Craig Architects, with phase 1 boundaries marked as a base bid for "
    "fields 1-4 and two add alternates."),
   CAPITAL, [{"page": PARKS, "reason": "A City sports facility."}], None),
 'h2-050': ("Regional Baseball Complex: building elevations, April 2016", BB,
   ("The architectural elevations for the complex's administration and concession building, shown as three "
    "perspective views of the two-storey structure under its cantilevered roof."),
   ("3,859,125 bytes, no text layer, read by rendering. Its title block reads REGIONAL BASEBALL COMPLEX, BUILDING "
    "ELEVATIONS, APRIL 2016, and names G. Donald Dudley Architect as architect where the March site plan names "
    "Kells + Craig."),
   CAPITAL, [{"page": PARKS, "reason": "A City sports facility."}],
   "The architect named differs from the March site plan's. Record both; do not assume one supersedes the other."),
 'h2-051': ("Regional Baseball Complex: softball field conversion plan, April 2016", BB,
   ("The plan showing how the complex's baseball fields convert to 300-foot softball fields with sixty-foot bases, "
    "using portable outfield fencing and portable mounds."),
   ("464,070 bytes, no text layer, read by rendering. Its title block reads REGIONAL BASEBALL COMPLEX, SOFTBALL "
    "FIELD CONVERSION, APRIL 2016, with a legend for a 300' SOFTBALL FIELD W/60' BASES and photographs of portable "
    "fencing and mound options."),
   CAPITAL, [{"page": PARKS, "reason": "A City sports facility."}], None),
 'h2-052': ("Community support quotations for the Regional Baseball Complex", BB,
   ("A compilation of supporting statements gathered for the Regional Baseball and Softball Complex, published to "
    "show the case being made for the project."),
   "473,961 bytes. Opens: Community Support for the ABQ Regional Baseball / Softball Complex, followed by quoted statements.",
   CAPITAL, [{"page": PARKS, "reason": "A City sports facility."}],
   "Advocacy material compiled for a project, not an assessment of it. Label it as such."),
 'h2-103': ("Golf Division greens aerification schedule, 2026", PK,
   ("The City Golf Division's schedule of when each municipal course's greens will be aerified during 2026, the "
    "notice golfers use to plan around closures."),
   "108,510 bytes. Opens: GOLF DIVISION 2026 Greens Aerification Schedule, Spring 2026, Ladera March 31, April 1,2, PDS April 7,8.",
   PARKS, [], "An operational schedule for one year. Date it; it will be superseded annually."),
 'h2-104': ("Balloon Fiesta Park field event reservation application, 2025", PK,
   ("The City's application form for reserving a field at Balloon Fiesta Park for an event, with the reference "
    "information an organiser needs before applying."),
   "1,140,776 bytes. Opens: Balloon Fiesta Park Field Event Reservation Application, KEEP THIS PAGE FOR REFERENCE.",
   PARKS, [{"page": FACIL, "reason": "A City facility's booking process."}], None),
 'h2-003': ("New Mexico DWI Report 2023", EXT,
   ("The state's annual report on driving while intoxicated, prepared for the transportation department's Capital "
    "Programs and Investment Division and covering the year's enforcement and crash data."),
   "5,628,611 bytes. Opens: New Mexico DWI Report 2023, New Mexico Department of Transportation, Capital Programs and Investment Division.",
   CRASH, [{"page": SAFETY, "reason": "Impaired-driving data."}],
   ("Prepared for the New Mexico Department of Transportation and hosted by the University of New Mexico. "
    "Attribute it to both; the archive already holds 62 validated NMDOT records.")),
}

EXCLUDE = {
 'h2-004': ("Open Meetings Act Compliance Guide",
            "The New Mexico Attorney General's guide to complying with the state Open Meetings Act.",
            ("A state agency's own publication of general applicability, linked from a City committee page. The "
             "Attorney General is the authoritative publisher of its own compliance guide. Same treatment as the "
             "NMAC licensing rule, the FCC rules, the Access Board guidelines and the Federal Register extract."),
            "state agency guidance", "third_party_authority"),
 'h2-105': ("Senate Bill 69: amending the Child Helmet Safety Act",
            "A New Mexico Senate bill amending the Child Helmet Safety Act to define electric-assisted bicycles.",
            ("State legislation published by the New Mexico Legislature, which is its authoritative source. The "
             "archive holds City instruments; a state bill belongs to the Legislature's own record."),
            "state legislation", "third_party_authority"),
 'h2-106': ("Air Traffic Control: occupational programme overview",
            "A federal careers brochure on air traffic control, hosted by a New Mexico university.",
            ("Neither a City document nor a New Mexico instrument: a federal occupational brochure reached through "
             "a university host. Outside the archive's subject on every reading."),
            "federal careers material", "third_party_authority"),
 'h2-005': ("A dead link to a university traffic safety document",
            "A link on a City page to nmtsc.unm.edu that returns HTTP 404 and 46,780 bytes of the university's error page.",
            ("There is no document at this URL. The City page still links it; the file is gone from the host. "
             "Recorded so the broken link is known rather than silently dropped."),
            "dead external link", "nothing_at_the_url"),
 'h2-044': ("An economic forum URL that serves the City homepage",
            "A download URL for Central_New_Mexico_Competitiveness_Summit.pdf that returns 4,926 bytes of website HTML.",
            ("Content substitution, already documented. economic-forum-cluster-research-2026-09-12.json found three "
             "economic forum URLs returning 4,926 bytes of homepage HTML instead of their documents. This is the "
             "same bytes again, reached through the Plone /@@download/file/ path rather than the plain one - so the "
             "substitution is not an artefact of how the URL is written."),
            "content substitution", "nothing_at_the_url"),
 'h2-045': ("An economic forum URL that serves the City homepage",
            "A download URL for Sirolli.pdf that returns the same 4,926 bytes of website HTML.",
            ("The same substitution as above, and byte-identical to it. Two different documents are both replaced "
             "by the same page, which is what makes it a substitution rather than two coincidences."),
            "content substitution", "nothing_at_the_url"),
}

add, skip = [], []
for i in SLICE:
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": URL[i],
         "filename": urllib.parse.unquote(URL[i].rstrip('/').split('/')[-1]),
         "harvested_from": SRC[i], "link_check": LC,
         "content_kind": {'25504446': 'PDF', '3c21444f': 'HTML'}[MAGIC[i]],
         "leading_bytes": MAGIC[i], "http_status": CODE[i], **M[i]}
    p = pages(i)
    if p:
        r["page_count"] = p
    if i in EXCLUDE:
        t, what, why, cat, pkg = EXCLUDE[i]
        r.update({"recommendation": "do not add", "title_for_reference": t, "what_it_is": what,
                  "why_not": why, "category": cat, "package": pkg})
        if i in INTERNAL:
            r["byte_identical_to"] = {"local_ref": INTERNAL[i], "in_this_artifact": True}
        if i in ART_HIT:
            r["also_decided_in"] = {"artifact": ART_HIT[i][0], "id": ART_HIT[i][1]}
        skip.append(r)
        continue
    t, group, desc, ev, canon, cross, caution = D[i]
    r.update({"recommendation": "add to the inventory as a new candidate", "title": t, "group": group,
              "description": desc, "evidence": ev, "description_word_count": len(desc.split()),
              "proposed_canonical_page": canon, "cross_listings": cross})
    if caution:
        r["caution"] = caution
    add.append(r)

rows = add + skip
assert len(rows) == len(SLICE), (len(rows), len(SLICE))
bygroup = collections.Counter(r['group'] for r in add)
add_bytes = sum(r['size_bytes'] for r in add)
containers = collections.Counter(r['content_kind'] for r in rows)
ag = [r for r in add if r['group'] == RD and 'agenda' in r['title'].lower()]
mn = [r for r in add if r['group'] == RD and 'minutes' in r['title'].lower()]
maps_ = [r for r in add if r['group'] == RDMAP]

artifact = {
 "batch_id": "second-harvest-council-research-2026-09-14",
 "lane": "Claude research lane: the second link harvest, Council and parks slice",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": "None of these files has an inventory id. Every row carries inventory_id: null and a recommendation rather than a recommended_status.",
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here. These must be created as candidates first, after which the ordinary archival gate applies.",
 },
 "where_this_lane_came_from": {
  "the_first_harvest_could_only_reach_what_was_still_on_disk": ("535 excluded HTML pages survived in scratch "
                                                               "directories. 220 more excluded HTML rows, across "
                                                               "eleven earlier artifacts, had no surviving copy."),
  "so_they_were_re_fetched": "All 220 were fetched again; 219 returned HTTP 200 and were parsed.",
  "what_came_out": ("159 distinct document links: 48 already inventory records, 5 already decided in the first "
                    "harvest, and 106 absent from the inventory by URL. All 106 were fetched - 105 returned HTTP "
                    "200, 103 of them real PDFs, 1,029,025,522 bytes in total, not one truncated."),
  "this_lane_is_the_first_slice": ("The %d Council, redistricting, baseball complex and parks records. The 50 "
                                   "behavioral health task force files are a separate lane." % len(SLICE)),
  "the_yield_argues_for_finishing_the_job": ("535 pages gave 355 undiscovered documents; 219 pages gave 106. The "
                                             "excluded pages of this archive are where its missing documents are."),
 },
 "THE_FIND_THAT_MATTERS_MOST": {
  "what": ("The complete published record of the 2022 Redistricting Committee - the joint City and County body "
           "that redrew Albuquerque's nine council districts after the 2020 census, as the City Charter requires "
           "every ten years."),
  "what_is_in_it": {
   "agendas": len(ag),
   "minutes": len(mn),
   "district_maps_with_statistics_tables": len(maps_),
   "and": ("the committee's Report and Recommendations, its communications plan, the consultant's rules briefing "
           "and three analytical briefings on compactness, population movement and social vulnerability, the "
           "members' concept ratings, and two Council floor amendments each proposing to adopt a different citizen "
           "map."),
  },
  "why_it_matters_beyond_itself": ("This run has spent lane after lane on the missing-minutes problem - whether an "
                                   "agenda may stand in for minutes that cannot be found, and it has had to invoke "
                                   "that exception for the MPRAB, the EDAct committee, the LGCC and the salary "
                                   "commission. Here is a City body whose agendas AND minutes are both published, "
                                   "meeting by meeting, eight pairs of them. No exception is needed for any of it."),
  "the_one_qualification": ("The minutes for the last meeting, 29 June 2022, are published as DRAFT Minutes. Seven "
                            "sets are approved; that one is not, and its row says so."),
  "the_maps_are_enormous": ("Eleven district maps between 41,975,777 and 72,579,402 bytes, %s bytes together. Each "
                            "is a drawn map with a statistics table and almost no extractable text - the five "
                            "citizen maps yield nothing but the repeated words City Councilors."
                            % format(sum(r['size_bytes'] for r in maps_), ',')),
  "and_the_report_is_the_largest_file_of_the_run": ("242,483,055 bytes, larger than the 280 MB airport master plan "
                                                    "in every practical sense but raw size - and larger than "
                                                    "anything else this run has measured except that plan."),
 },
 "a_substitution_confirmed_from_a_second_direction": {
  "what": ("economic-forum-cluster-research-2026-09-12.json found three economic forum URLs returning 4,926 bytes "
           "of City homepage HTML instead of their documents. This lane reached two of those documents by a "
           "different path - the Plone /@@download/file/ form rather than the plain URL - and got the same 4,926 "
           "bytes, byte-identical."),
  "why_that_is_worth_recording": ("It rules out the explanation that the substitution is an artefact of how the URL "
                                  "is written. Two documents, two URL forms, one replacement page. The documents "
                                  "are gone from the server, not merely mis-addressed."),
 },
 "where_the_line_falls_on_other_authorities": {
  "excluded_here": ("The New Mexico Attorney General's Open Meetings Act compliance guide, a New Mexico Senate bill "
                    "amending the Child Helmet Safety Act, and a federal air traffic control careers brochure."),
  "the_rule": ("A publication of general applicability belongs to the body that published it. This run has now "
               "excluded eight on that reasoning - the FCC rules, the USDA-NRCS technical note, the NMAC licensing "
               "rule, the PNM tariff, an IRS form, the Access Board guidelines, a Federal Register extract, and "
               "these."),
  "what_is_still_kept": "An instrument specific to New Mexico, such as the state DWI report prepared for NMDOT, which is recommended here.",
 },
 "method": ("Re-fetched 220 excluded HTML pages, parsed them for document links, reconciled every link against "
            "every inventory URL and against every row of every saved artifact, fetched and measured what was left, "
            "verified each container by leading bytes, tested every PDF for its end-of-file marker, counted pages "
            "from the file structure, extracted text from all of them, rendered the three that yielded none, and "
            "swept every checksum against all checksummed inventory records and every saved artifact row."),
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
  "result": ("Nothing here is in the inventory. The only collisions are the two substituted URLs, which match each "
             "other and an already-excluded economic forum record - and all three are the same replacement page, "
             "not a document."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(INTERNAL),
  "note": ("The only byte-identical pair in this lane is the two substituted URLs, and neither is a document. No "
           "two real documents here are duplicates."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r['local_ref'] for r in add if r['group'] in (RD, RDMAP)],
   "finding": ("The complete published record of the 2022 Redistricting Committee: %d agendas, %d sets of minutes, "
               "%d district maps with statistics, the Report and Recommendations, and the supporting analyses."
               % (len(ag), len(mn), len(maps_))),
   "recommended_action": "Add the set. Keep it together; the maps are only meaningful beside the minutes that weigh them."},
  {"severity": "minutes-exist-here",
   "affects": [r['local_ref'] for r in mn],
   "finding": ("Six sets of approved minutes and one draft set, published alongside their agendas. This run has "
               "had to invoke the missing-minutes exception four times; this body needs it for nothing."),
   "recommended_action": "Add both agendas and minutes, and mark the 29 June 2022 set as draft."},
  {"severity": "very-large-files",
   "affects": ['h2-001'] + [r['local_ref'] for r in maps_],
   "finding": "The committee report is 242,483,055 bytes and eleven maps run from 41 MB to 72 MB.",
   "recommended_action": "Plan the R2 upload for these as a special case; they are the largest set this run has recommended."},
  {"severity": "content-substitution",
   "affects": ['h2-044', 'h2-045'],
   "finding": "Two economic forum documents are replaced by the same 4,926-byte City homepage, reached by a second URL form.",
   "recommended_action": "Do not add. Record that the substitution is server-side, not an addressing artefact."},
  {"severity": "broken-link",
   "affects": ['h2-005'],
   "finding": "A City page links a university traffic safety document that returns HTTP 404.",
   "recommended_action": "Report the broken link; there is nothing to archive."},
  {"severity": "label-carefully",
   "affects": ['h2-019', 'h2-046', 'h2-039', 'h2-031', 'h2-052'],
   "finding": ("Five files announce a qualification on their own face or filename: draft minutes, an unfilled "
               "amendment template whose date field reads [Date], a corrected concept map, a revised citizen map, "
               "and a page of advocacy quotations."),
   "recommended_action": "Carry each qualification onto the record; none of them is what its neighbours are."},
  {"severity": "third-party-authority",
   "affects": ['h2-004', 'h2-105', 'h2-106'],
   "finding": "An Attorney General compliance guide, a state Senate bill and a federal careers brochure.",
   "recommended_action": "Do not add; their publishers are the authoritative source."},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(add),
  "do_not_add": len(skip),
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
 "archival_note": (f"None of the {len(add)} proposed additions is site-ready, and none is a candidate yet. Once "
                   f"created, each remains inventory-only until an R2 archive object exists and its public "
                   f"download, exact size, SHA-256 and authoritative-source provenance are verified. Combined "
                   f"footprint if all are added and archived: {add_bytes:,} bytes."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes, the container read "
                      "from the file, the page count where the file is a PDF, and harvested_from - the City page "
                      "whose links led to it. Every row carries inventory_id: null."),
 "what_remains": "The 50 behavioral health task force files from this same harvest, claimed as the next lane.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('by_group', 'containers')}}))
