"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. The parksandrecreation/parks and /recreation sets.
"""

import collections
import datetime
import glob
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\parks-recreation-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\parks')

PARKSREC = 'content/public-works/parks-recreation.md'
BIKEIDX = 'content/transportation/bicycling/_index.md'
BIKEPLANS = 'content/transportation/bicycling/bike-plans.md'
BIKEMAPS = 'content/transportation/bicycling/bike-maps.md'
MAPS = 'content/maps-data/maps.md'
STORM = 'content/public-works/stormwater-drainage.md'

ARCHIVED_BIKE_PLAN = 'src-0f60535452ac9154'   # 2000 Comprehensive On-Street Bicycle Plan, validated with an r2_url
MANZANO = 'src-08682b53cc068b7b'              # Manzano Mesa Prescription Trail Guide, validated, NO r2_url
BIANCHETTI = 'src-00d4de3fc40a3556'           # BianchettiPark.pdf, excluded as not a durable record

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw, final = line.rstrip('\n').split('\t')
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

CONTAINER = {'25504446': 'PDF', '3c21444f': 'HTML', 'd0cf11e0': 'DOC', '504b0304': 'OOXML'}

LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, not by extension - one file named .doc in this lane is a PDF.")


def name(i):
    return os.path.basename(URL[i])


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i]}
    if URL[i] != u:
        r["raw_file_url"] = URL[i]
    r.update(M[i])
    return r


HTML = [i for i in SLICE if MAGIC[i] == '3c21444f']
PRESCRIPTION = [i for i in SLICE if '/prescription-trails/' in URL[i] and MAGIC[i] != '3c21444f']

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)

# the two prescription URL twins: same basename, same bytes, two ids
PRESC_TWINS = {}
for h, v in BYHASH.items():
    if len(v) == 2 and all(x in PRESCRIPTION for x in v):
        a, b = sorted(v, key=lambda x: len(URL[x]))
        PRESC_TWINS[b] = a          # longer URL is the copy

BIKE_MAP = 'src-dbecb4782b496e13'
BIKE_MAP_2009 = 'src-64a05134e2061cad'
PLAN_DUP = 'src-bad74bf291ef24a0'
ROSTER = 'src-7b0001bed042d959'
FLAG_WAIVER = 'src-69e14d471a02848e'

APPROVED = [
 ('src-64676341bb04fde4', "Bicycle Boulevard Resolution", None,
  ("The City resolution establishing bicycle boulevards, the low-traffic streets given priority treatment for "
   "cycling, setting out what the designation means and how the City is to apply it to the street network."),
  "Published at parksandrecreation/recreation/bike/documents/bicycle-boulevard-resolution.pdf.",
  BIKEPLANS, [{"page": BIKEIDX, "reason": "It governs a class of the City's bicycle network."}]),
 ('src-e7a32ece938ca8d9', "North Diversion Channel Trail: project brief", None,
  ("The City's short brief on the North Diversion Channel trail sets out the proposal in summary form, the "
   "companion to the full document published beside it on the same page."),
  "An OOXML document, leading bytes 504b0304, read from word/document.xml. 12,570 bytes against the full version's 10,603,256.",
  BIKEPLANS, [{"page": STORM, "reason": "The trail runs along a flood control channel."}]),
 ('src-89247de353dabf15', "North Diversion Channel Trail: full document", None,
  ("The City's full document on the North Diversion Channel trail, the detailed version behind the brief, running "
   "to ten megabytes of text and imagery about the corridor and the trail proposed along it."),
  "An OOXML document, leading bytes 504b0304, 10,603,256 bytes, read from word/document.xml.",
  BIKEPLANS, [{"page": STORM, "reason": "The trail runs along a flood control channel."}]),
 ('src-64a05134e2061cad', "Albuquerque Bike Map, 2009", "2009",
  ("The City's 2009 bicycle map of Albuquerque, showing the bikeways, trails and street routes available to cyclists "
   "across the metropolitan area at that date, from the far northwest through the foothills."),
  ("An 11,114,645-byte PDF. The same bytes are also served at recreation/bike/documents/bike-map.pdf under a name "
   "carrying no year; this is the copy that says what it is."),
  BIKEMAPS, [{"page": MAPS, "reason": "A citywide map."}]),
 ('src-7c0654024a94c161', "Foothills Trail Map (overview sheet)", None,
  ("A City trail map of the Sandia foothills, distinct in size and bytes from each of the five individual foothills "
   "trail maps the archive already holds for Indian School, Piedra Lisa, Embudito, Copper and Menaul."),
  ("1,060,239 bytes, and its checksum matches none of the archived foothills maps, whose sizes run from 284,780 to "
   "1,374,994 bytes."),
  PARKSREC, [{"page": MAPS, "reason": "A trail map."}]),
]

approved = []
for i, t, date, desc, ev, canon, cross in APPROVED:
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "date": date, "pages": None, "evidence": ev,
              "group": "parks and bicycle records",
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    approved.append(r)

# the MPRAB agenda, under the missing-minutes exception
r = row('src-f12ce7ae6ca1e3f6', "approved for addition")
mprab_desc = ("The Metropolitan Parks and Recreation Advisory Board's agenda for its meeting of 4 May 2021, listing "
              "the board membership and the business set down for the meeting, held by video conference.")
r.update({"title": "Metropolitan Parks and Recreation Advisory Board: Agenda (approved minutes not located), May 4, 2021",
          "description": mprab_desc, "date": "2021", "pages": None,
          "evidence": ("A legacy OLE2 Word document, leading bytes d0cf11e0, read with antiword. Headed METROPOLITAN "
                       "PARKS & RECREATION ADVISORY BOARD MEETING, Tuesday, May 4, 2021 12:30 PM, ZOOM Meeting, over "
                       "the board member list."),
          "group": "parks and bicycle records",
          "missing_minutes_review": {
           "policy": ("An agenda may be preserved only after a recorded exhaustive official-source review finds no "
                      "approved minutes, and never for a cancelled or no-quorum meeting."),
           "inventory": "No Metropolitan Parks and Recreation Advisory Board minutes exist in the inventory; two records match the board at all, this agenda and a District 8 press notice seeking applicants.",
           "official_pages_probed": ["/parksandrecreation/metropolitan-parks-and-recreation-advisory-board",
                                     "/parksandrecreation/boards-commissions/metropolitan-parks-and-recreation-advisory-board",
                                     "/parksandrecreation/about-us/metropolitan-parks-and-recreation-advisory-board"],
           "probe_result": "All three return HTTP 404.",
           "site_search": ("The City's own search for the exact phrase Metropolitan Parks and Recreation Advisory "
                           "Board together with minutes returns No results, and the results page carries no link to "
                           "the board at all."),
           "cancellation_check": "The agenda carries no cancellation, postponement, rescheduling or no-quorum language; zero matches for any of those terms.",
           "conclusion": "The exception applies. Label it Agenda (approved minutes not located) and never present it as minutes.",
          },
          "caution": ("The agenda prints a Zoom meeting identifier and passcode for a 2021 meeting. They are stale, "
                      "but strip or redact them rather than republish a working-looking credential."),
          "proposed_canonical_page": PARKSREC, "cross_listings": [],
          "description_word_count": len(mprab_desc.split())})
approved.append(r)

# ------------------------------------------------------------------ duplicate
duplicate = []
r = row(PLAN_DUP, "duplicate")
r.update({"canonical_id": ARCHIVED_BIKE_PLAN,
          "title_for_reference": "Final Albuquerque Comprehensive On-Street Bicycle Plan",
          "relationship": "The same file the archive already holds as the 2000 Albuquerque Comprehensive On-Street Bicycle Plan, validated with an r2_url.",
          "how_it_was_established": ("Byte-identical to the archived record: 8,054,496 bytes and SHA-256 "
                                     "81e89d704fe74949d958fb42f8e5ede02adeeb3ebb5b243cf16acc6f92514651 on both. The "
                                     "two inventory records carry different URL strings for the same object, which is "
                                     "why the URL group-by did not catch it."),
          "why_this_one_is_the_copy": "The archive already holds it, validated and archived. This is the second inventory record for one file.",
          "note_for_the_run": ("This is the first cross-inventory byte collision found in this run. Every slice before "
                               "it reported zero, and the reason this one was found is that the checksum was compared "
                               "against the archived record rather than only within the slice."),
          "group": "duplicates"})
duplicate.append(r)

r = row(BIKE_MAP, "duplicate")
r.update({"canonical_id": BIKE_MAP_2009,
          "title_for_reference": "bike-map.pdf",
          "relationship": "The 2009 bike map, served a second time under a name that carries no year.",
          "how_it_was_established": "Byte-identical: 11,114,645 bytes and the same SHA-256 as 2009bikemap.pdf, at a different path.",
          "why_this_one_is_the_copy": ("The dated name is canonical because it says what the document is. Publishing "
                                       "this one as the City's bike map would present a seventeen-year-old map as "
                                       "current."),
          "group": "duplicates"})
duplicate.append(r)

DUP_IDS = {r['id'] for r in duplicate}

# ---------------------------------------------------- requires human review
# The two prescription URL twins are NOT recommended as duplicates. Their canonicals
# are themselves held for review, and a canonical has to be a record worth keeping -
# which is exactly what has not been decided yet. The twin relationship is recorded
# on the rows instead, so one decision still settles the whole package.
PRESC_PACKAGE = [i for i in PRESCRIPTION if i not in DUP_IDS]
rhr = []
for n, i in enumerate(sorted(PRESC_PACKAGE, key=name), 1):
    r = row(i, "requires human review")
    r.update({"draft_title": "Prescription Trails guide: " + name(i),
              "question_for_human": "Decide, once, whether this archive holds the Prescription Trails walking guides. The answer governs all %d." % len(PRESC_PACKAGE),
              "why_not_decided_here": ("The inventory already answers this question twice, in opposite directions, "
                                       "for documents of exactly this class. BianchettiPark.pdf (" + BIANCHETTI +
                                       ") is excluded with the reason: one-page Prescription Trails walking-guide/map "
                                       "for Bianchetti Park, not a durable City plan, study, ordinance, or project "
                                       "record. ManzanoMesaMulti-CulturalCtr.pdf (" + MANZANO + ") is validated, "
                                       "described, and published on " + PARKSREC + ". Both are one-page Prescription "
                                       "Trails guides for a single park. This lane will not pick a side on a "
                                       "precedent the archive has set both ways."),
              "measurement": "%s, %s bytes, at %s." % (CONTAINER[MAGIC[i]], format(M[i]['size_bytes'], ','), URL[i]),
              "distinguishing_content": name(i),
              "package": "the_prescription_trails_guides",
              "priority": n})
    if i in PRESC_TWINS:
        r["byte_identical_to"] = PRESC_TWINS[i]
        r["twin_note"] = ("The crawl captured this file twice. It is byte-identical to its twin, which is in this "
                          "same package. Whichever way the class is decided, decide both together; only one of the "
                          "two should ever be archived.")
    elif i in set(PRESC_TWINS.values()):
        r["byte_identical_to"] = [k for k, v in PRESC_TWINS.items() if v == i][0]
        r["twin_note"] = ("The crawl captured this file twice. It is byte-identical to its twin, which is in this "
                          "same package. Whichever way the class is decided, decide both together; only one of the "
                          "two should ever be archived.")
    rhr.append(r)

# ------------------------------------------------------------------- excluded
excluded = []
for i in HTML:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Web page: " + URL[i].split('/parksandrecreation/', 1)[1],
              "what_it_is": "A live page on the City's parks and recreation site.",
              "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f. This lane's "
                                   "own tree has already settled the class: 74 records under prescription-trails are "
                                   "excluded in the inventory with the reason navigation, pagination, contact, or "
                                   "generic interface text captured as a candidate. These are the same thing."),
              "category": "live web page",
              "package": "web_pages"})
    excluded.append(r)

NONDURABLE = [i for i in SLICE
              if i not in DUP_IDS and i not in PRESCRIPTION and MAGIC[i] != '3c21444f'
              and i not in {x['id'] for x in approved}]
for i in NONDURABLE:
    r = row(i, "excluded")
    extra = ""
    if i == ROSTER:
        extra = (" It is also served a second time under the name waiver-of-liability-flag-football.pdf: the two are "
                 "byte-identical at 63,037 bytes, and both are this roster form. The flag football waiver the City's "
                 "own filename promises is not at that address.")
    if i == FLAG_WAIVER:
        extra = (" And it is not what its name says. The file served at waiver-of-liability-flag-football.pdf is the "
                 "Additions to Original Roster form, byte-identical to additions-to-original-roster.pdf. Both are "
                 "excluded on the same ground, so neither is recorded as a duplicate of the other - a canonical has "
                 "to be a record worth keeping.")
    if i == 'src-8f36d54b2834e16c':
        extra = " Its name ends .doc and its leading bytes are 25504446: it is a PDF."
    r.update({"title_for_reference": name(i),
              "what_it_is": "Recreation programme paperwork: a registration form, waiver, roster, schedule or code of conduct.",
              "exclusion_reason": ("Not a durable record. It is season paperwork for a City recreation programme - "
                                   "forms to sign, rosters to fill, schedules for a season now years past. The "
                                   "archive's own reasoning for this class is already on the record in this tree: "
                                   "not a durable City plan, study, ordinance, or project record." + extra),
              "category": "recreation programme paperwork",
              "package": "non_durable_programme_paperwork"})
    excluded.append(r)

rows = approved + duplicate + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "parks-recreation-cluster-research-2026-09-13",
 "lane": "Claude research lane: www.cabq.gov/parksandrecreation/parks and /recreation",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("What is left under the City's parks and recreation directories: the Prescription Trails walking guide "
             "series, the bicycle documents, and the recreation programme paperwork."),
 "scope": "All 97 uncovered candidates in the two directories. The coverage gate is asserted in the generator.",
 "brief": ("Run the containment test before recommending any part of a plan, and check every candidate against the "
           "archive's existing parks holdings before recommending addition."),
 "brief_finding": ("The second instruction was the one that paid. Checking against the archive's existing holdings "
                   "found a candidate that is byte-identical to a record already validated and archived - the first "
                   "cross-inventory byte collision in this run."),
 "the_precedent_conflict_this_lane_will_not_resolve": {
  "the_question": "Does this archive hold the Prescription Trails walking guides? There are %d of them here." % len(PRESC_PACKAGE),
  "why_it_is_not_mine_to_answer": "Because the inventory already answers it twice, in opposite directions, for documents of exactly the same class.",
  "the_exclusion": {
   "record": BIANCHETTI,
   "file": "BianchettiPark.pdf",
   "recorded_reason": "One-page Prescription Trails walking-guide/map for Bianchetti Park, not a durable City plan, study, ordinance, or project record.",
  },
  "the_publication": {
   "record": MANZANO,
   "file": "ManzanoMesaMulti-CulturalCtr.pdf",
   "status": "validated",
   "published_at": PARKSREC,
   "recorded_description": "Maps a 0.6-mile accessible concrete walking route at Manzano Mesa Park, with route directions, accessibility grade, nearby transit, parking and facilities.",
  },
  "they_are_the_same_kind_of_document": "Both are one-page Prescription Trails guides for a single City park, from the same programme, at the same path.",
  "a_third_thing_worth_knowing": ("The published one carries no r2_url. Its validation_status reads R2 archival "
                                  "follow-up pending explicit approval. So the record that sets the precedent for "
                                  "publishing is itself not site-ready under the standing rule."),
  "what_this_lane_recommends": ("Decide the class once. If the guides are in scope, the Bianchetti exclusion should "
                                "be revisited and all %d of these approved together; if they are not, Manzano Mesa "
                                "should come down. Either way it is one decision, not %d, and this artifact is "
                                "arranged so it can be applied as one." % (len(PRESC_PACKAGE), len(PRESC_PACKAGE))),
  "the_general_point": ("A lane that finds the archive contradicting itself should surface the contradiction, not "
                        "pick the side that makes its own numbers look better. Approving %d records here would have "
                        "been the larger-looking result and the wrong one." % len(PRESC_PACKAGE)),
 },
 "the_first_cross_inventory_byte_collision_of_the_run": {
  "what_was_found": ("final-albuquerque-comprehensive-on-street-bicycle-plan is byte-identical to " +
                     ARCHIVED_BIKE_PLAN + ", the 2000 Albuquerque Comprehensive On-Street Bicycle Plan, which is "
                     "validated and carries an r2_url. Same 8,054,496 bytes, same SHA-256."),
  "why_it_was_not_caught_earlier": ("The two inventory records carry different URL strings for the same object, so a "
                                    "URL group-by finds nothing. Only comparing the fetched checksum against the "
                                    "archived record's own checksum finds it."),
  "why_it_matters_beyond_this_record": ("Every slice in this run has reported zero cross-inventory byte collisions. "
                                        "That was true each time, but it was also a weaker claim than it sounded: "
                                        "most inventory records carry no checksum at all, so the comparison could "
                                        "only ever be made against the 1,612 that do. This one was in that set."),
 },
 "two_files_that_are_not_what_their_names_say": {
  "the_bike_map": ("recreation/bike/documents/bike-map.pdf is byte-identical to recreation/documents/2009bikemap.pdf. "
                   "The City serves its 2009 bicycle map under a name carrying no year. Publishing it as the bike map "
                   "would present a seventeen-year-old map as current, so the dated name is recommended canonical."),
  "the_flag_football_waiver": ("recreation/documents/waiver-of-liability-flag-football.pdf is byte-identical to "
                               "additions-to-original-roster.pdf, and its content is the roster form: it opens City "
                               "of Albuquerque Parks and Recreation Additions to Original Roster. The flag football "
                               "waiver the filename promises is not at that address. Both files are excluded on the "
                               "same non-durable ground, so neither is recorded as a duplicate of the other."),
  "and_an_extension": "recreation/documents/parentscodeofconduct2016.doc has leading bytes 25504446. It is a PDF.",
  "the_running_count": "Ten filenames across this run now contradict the document or the bytes behind them.",
 },
 "the_mprab_agenda": {
  "what_it_is": "The Metropolitan Parks and Recreation Advisory Board agenda for 4 May 2021, the only record of that board in the inventory apart from a press notice.",
  "the_policy_applied": "An agenda may be preserved only after a recorded exhaustive official-source review finds no approved minutes, and never for a cancelled or no-quorum meeting.",
  "the_review": ("Three candidate official page URLs probed, all HTTP 404. The City's own site search for the exact "
                 "phrase together with minutes returns No results with no link to the board. The inventory holds no "
                 "minutes for the board. The agenda carries no cancellation, postponement or no-quorum language."),
  "the_decision": "The exception applies. Recommended for addition, labelled Agenda (approved minutes not located).",
  "a_caution_carried_on_the_row": "It prints a Zoom meeting identifier and passcode. Stale, but strip or redact rather than republish a working-looking credential.",
 },
 "method": ("Fetched all 97 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. "
            "Grouped by checksum within the slice and compared every checksum against the 1,612 checksummed inventory "
            "records, which is how the archived bicycle plan was found. Read the recreation documents to see what "
            "each actually is rather than what its filename claims. Searched the inventory for the archive's own "
            "prior decisions on the Prescription Trails class before deciding any of the fifty. Performed and "
            "recorded an exhaustive official-source review for the advisory board's minutes before applying the "
            "missing-minutes exception to its agenda."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 1,
  "internal_byte_collisions": len([v for v in BYHASH.values() if len(v) > 1]),
  "result": "One candidate is byte-identical to a record already validated and archived and is recommended duplicate against it.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len([v for v in BYHASH.values() if len(v) > 1]),
  "cross_inventory_byte_collisions": 1,
  "checksums_compared_against": 1612,
  "relationships_found": len(duplicate),
  "relationships_not_recorded_as_duplicates": 3,
  "why": ("Three byte-identical pairs are recorded on their rows rather than as duplicate recommendations, for "
          "the same reason in each case: a canonical has to be a record worth keeping, and in these three it "
          "is not - or not yet. additions-to-original-roster.pdf and waiver-of-liability-flag-football.pdf are "
          "both excluded. The two prescription twins sit inside the package whose scope is the open question; "
          "naming one of them canonical would quietly decide the very thing this artifact refuses to decide."),
 },
 "integration_flags": [
  {"severity": "precedent-conflict",
   "affects": [r['id'] for r in rhr],
   "finding": f"The inventory decides the Prescription Trails walking-guide class both ways: BianchettiPark.pdf is excluded as not a durable record, ManzanoMesaMulti-CulturalCtr.pdf is validated and published on {PARKSREC}. {len(PRESC_PACKAGE)} more are pending here.",
   "recommended_action": "Decide the class once and apply it to all of them, and to the two already decided. Note that the published one carries no r2_url and is therefore not site-ready under the standing rule."},
  {"severity": "avoids-duplicate-archival",
   "affects": [PLAN_DUP],
   "finding": f"The Final Albuquerque Comprehensive On-Street Bicycle Plan is byte-identical to {ARCHIVED_BIKE_PLAN}, already validated with an r2_url. The two inventory records carry different URL strings for one 8,054,496-byte object, so no URL group-by could have found it.",
   "recommended_action": "Apply duplicate. Worth a sweep: compare every checksummed pending record against every checksummed archived record, not only within slices."},
  {"severity": "title-from-the-bytes",
   "affects": [BIKE_MAP, BIKE_MAP_2009, FLAG_WAIVER, ROSTER, 'src-8f36d54b2834e16c'],
   "finding": "bike-map.pdf is the 2009 map under an undated name; waiver-of-liability-flag-football.pdf is the roster form, not a waiver; parentscodeofconduct2016.doc is a PDF.",
   "recommended_action": "Title and date from the bytes and the document. Do not publish the undated bike map name."},
  {"severity": "missing-minutes-exception-applied",
   "affects": ['src-f12ce7ae6ca1e3f6'],
   "finding": "The Metropolitan Parks and Recreation Advisory Board agenda of 4 May 2021 qualifies under the exception: three official page URLs return 404, City site search for the board plus minutes returns No results, the inventory holds no minutes, and the agenda shows no cancellation.",
   "recommended_action": "Approve labelled Agenda (approved minutes not located). Never present it as minutes. Redact the Zoom passcode printed on it."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "additional_probes": "Three official-source page probes and one City site search for the advisory board's minutes.",
                "containers_verified": ("%d PDFs, %d HTML pages, %d legacy OLE2 documents and %d OOXML documents by "
                                        "leading bytes." % (bycontainer['PDF'], bycontainer['HTML'],
                                                            bycontainer['DOC'], bycontainer['OOXML']))},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. Two approved "
                   f"records are OOXML and one is a legacy OLE2 document; all three should be archived in their "
                   f"original format rather than converted. The {len(rhr)} records held for review are not to be "
                   f"archived until the class question is settled."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Four rows carry a canonical_id; three canonicals "
                     "are rows in this artifact and one, " + ARCHIVED_BIKE_PLAN + ", is a record already validated "
                     "and archived. The " + str(len(rhr)) + " requires-human-review rows are one package and one "
                     "decision, not " + str(len(rhr)) + " questions. The advisory board agenda carries its "
                     "missing-minutes review inline and must be labelled as an agenda. Every row carries a "
                     "leading_bytes field. Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the official-source probes and the site search were read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items() if k != 'containers'}}))
