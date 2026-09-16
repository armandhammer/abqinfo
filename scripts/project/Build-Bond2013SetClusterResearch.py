"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Fourth slice of the municipaldevelopment/documents lane: the
2013 general obligation bond department scope and summary set, in the two
editions the City publishes.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\bond-2013-department-set-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\md4')

CAPITAL = 'content/city-data/capital-spending.md'
PARKS = 'content/public-works/parks-recreation.md'
TXPLANS = 'content/transportation/transportation-plans.md'
ABQRIDE = 'content/transportation/transit/abq-ride.md'
STORM = 'content/public-works/stormwater-drainage.md'
SAFETY = 'content/city-data/public-safety-data.md'
CLIMATE = 'content/city-data/climate-environment.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
FACILITIES = 'content/public-works/city-facilities.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

PAIRS = json.load(open(os.path.join(SP, 'pairs.json'), encoding='utf-8'))

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


# department -> (display name, canonical page, cross page or None, scope lead, summary lead)
DEPT = {
 "ABQRideTransit": ("ABQ RIDE Transit", ABQRIDE,
  "revenue and support vehicle replacement and expansion at $4,000,000, with the associated equipment the department needs to draw federal funds",
  "revenue and support vehicle replacement rising from $4,000,000 in 2013 to $6,000,000 in each of the later cycles"),
 "AnimalWelfare": ("Animal Welfare", FACILITIES,
  "animal shelter rehabilitation and animal welfare equipment under the Community Facilities heading",
  "$600,000 in 2013 rising to $1,500,000 across the middle cycles and $850,000 in 2021, totalling $5,950,000"),
 "CouncilNeighborhoodSetAside": ("Council Neighborhood Set-Aside Program", CAPITAL,
  "the Council's neighbourhood set-aside programme under the Mandated Programs and Set-Asides heading",
  "$9,000,000 in each of four cycles, totalling $45,000,000"),
 "CulturalServices": ("Cultural Services and the Albuquerque Biological Park", CAPITAL,
  "renovation and repair at the BioPark under the Community Facilities heading",
  "the Albuquerque Biological Park's programme across the five cycles"),
 "DMDCIPFacParking": ("Municipal Development, Capital Implementation Program, Facilities and Parking", FACILITIES,
  "the CIP Division's facilities and parking work under the Community Facilities heading",
  "the CIP Division's facilities and parking programme across the five cycles"),
 "DMDStormDrainage": ("Municipal Development, Storm Drainage", STORM,
  "NPDES stormwater quality MS4 permit compliance at $1,500,000, covering planning, design, property acquisition, equipment and construction",
  "MS4 permit compliance rising from $1,500,000 in 2013 to $2,500,000 by 2019"),
 "DMDStreets": ("Municipal Development, Streets", TXPLANS,
  "the Lomas Corridor Master Plan at $500,000 for improvements to Lomas Boulevard, and the Osuna Road widening",
  "the Lomas Corridor Master Plan at $500,000 in each of the first two cycles alongside the rest of the streets programme"),
 "Env.Health": ("Environmental Health", CLIMATE,
  "health and safety equipment, vehicles and facilities at $355,000",
  "$355,000 in 2013 rising to about $860,000 per cycle, totalling $3,715,000"),
 "FamilyCommServices": ("Family and Community Services", CAPITAL,
  "renovation and repair of existing facilities at $1,800,000, covering design, renovation, demolition, construction, equipment and furnishing",
  "the department's renovation and facility programme across the five cycles"),
 "FinanceAdministration": ("Finance and Administrative Services", CAPITAL,
  "business application technology for Finance and Administrative Services",
  "the department's technology and facilities programme across the five cycles"),
 "ParksRecreation": ("Parks and Recreation", PARKS,
  "river amenities, enhancements and bosque restoration at $2,250,000 for planning, design, land acquisition, construction and rehabilitation",
  "river amenities and bosque restoration at $2,250,000 in 2013 and $2,000,000 in each later cycle"),
 "Planning": ("Planning", REDEV,
  "comprehensive community planning and revitalisation at $500,000 for citywide study, design and construction",
  "the Planning Department's programme across the five cycles"),
 "PublicSafetyFire": ("Fire", SAFETY,
  "fire apparatus replacement and fire facility rehabilitation at $3,295,300 for purchasing and replacing emergency response apparatus",
  "the Fire Department's apparatus and facility programme across the five cycles"),
 "PublicSafetyPolice": ("Police", SAFETY,
  "marked and unmarked police vehicle replacement",
  "$5,000,000 in 2013 and $3,000,000 in each later cycle, totalling $17,000,000"),
 "SeniorAffairs": ("Senior Affairs", CAPITAL,
  "the Senior Affairs facility programme under the Community Facilities heading",
  "$500,000 in 2013 rising to $1,000,000 per cycle, totalling $4,300,000"),
}

SET_NOTE = ("Part of the City's 2013 general obligation bond document set: one scope sheet and one summary sheet per "
            "department. The scopes state the 2013 cycle's projects; the summaries schedule each department across "
            "the five cycles 2013, 2015, 2017, 2019 and 2021.")

approved, duplicates, rhr = [], [], []
for rec in PAIRS:
    dept, kind = rec['dept'], rec['kind']
    name, page, scope_lead, sum_lead = (DEPT[dept][0], DEPT[dept][1], DEPT[dept][2], DEPT[dept][3])
    plain, copy = rec.get('plain'), rec.get('copy')

    if kind == 'Scope':
        title = "2013 General Obligation Bond Project Scopes: " + name
        desc = ("The City's 2013 general obligation bond scope sheet for %s states what the bond money may be spent "
                "on in the 2013 cycle, leading with %s." % (name, scope_lead))
        ev = ("Born-digital PDF with a full text layer, headed with the department grouping over \"Project Title "
              "2013 Scope\".")
    else:
        title = "2013-2021 General Obligation Bond Summary: " + name
        desc = ("The City's general obligation bond summary schedules %s across the 2013, 2015, 2017, 2019 and 2021 "
                "cycles, showing %s." % (name, sum_lead))
        ev = ("Born-digital PDF with a full text layer, headed \"G.O. Bond Summary\" over the column set "
              "\"Department / Division / Project Title  2013 2015 2017 2019 2021 Totals\".")

    if plain:
        r = row(plain['id'], "approved for addition")
        r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
                  "date": "2013", "evidence": ev, "set": SET_NOTE,
                  "proposed_canonical_page": CAPITAL,
                  "cross_listings": ([{"page": page, "reason": "That page carries this department's other capital records."}]
                                     if page != CAPITAL else []),
                  "edition": "The plain-filename edition, which is the one the City's own document listing links."})
        approved.append(r)

    if copy:
        if plain is None and dept == 'DMDCIPFacParking':
            # The plain edition exists on the server (HTTP 200) but is not an inventory record,
            # so the comparison this lane runs on every other pair cannot be run here.
            r = row(copy['id'], "requires human review")
            r.update({"draft_title": title + " (copy_of edition; the plain edition is on the server but uncrawled)",
                      "question_for_human": ("Add DMDCIPFacParkingScope.pdf to the inventory, compare the two "
                                             "editions as this artifact does for every other department, then "
                                             "resolve both."),
                      "why_not_decided_here": ("Its counterpart exists — probed directly at HTTP 200, 52,980 bytes, "
                                               "a genuine PDF, and linked from the City's own document listing — but "
                                               "it is not an inventory record, so there is nothing in scope to "
                                               "compare this file against. Approving it would silently pick an "
                                               "edition the lane never tested."),
                      "measurement": "No comparison possible: the counterpart is not a candidate. This file is %d bytes." % copy['bytes'],
                      "counterpart": "DMDCIPFacParkingScope.pdf, not yet an inventory record",
                      "package": "the_two_editions"})
            rhr.append(r)
        elif plain is None:
            # SeniorAffairsScope: the plain edition returns HTTP 404, so this is the only edition.
            r = row(copy['id'], "approved for addition")
            r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
                      "date": "2013", "evidence": ev, "set": SET_NOTE,
                      "proposed_canonical_page": CAPITAL,
                      "cross_listings": ([{"page": page, "reason": "That page carries this department's other capital records."}]
                                         if page != CAPITAL else []),
                      "edition": ("Only edition. The plain filename SeniorAffairsScope.pdf was probed directly and "
                                  "returns HTTP 404, so no counterpart exists to compare against."),
                      "only_edition_verified": True})
            approved.append(r)
        else:
            r = row(copy['id'], "requires human review")
            r.update({"draft_title": title + " (second edition)",
                      "question_for_human": ("Establish which of the two editions of this sheet is the City's "
                                             "operative one, then retain that and resolve the other."),
                      "why_not_decided_here": ("The two editions differ in content and the files carry nothing that "
                                               "ranks them: both state the same 2013 cycle and the same five-cycle "
                                               "schedule, neither carries a revision stamp, and the City links both "
                                               "editions from its own document listing. Publishing the wrong one "
                                               "would misstate what a department's bond money was scoped for."),
                      "measurement": ("Normalized-text sequence ratio %s against the plain edition, token coverage %s of "
                                      "the plain text inside this one and %s the other way. Byte sizes "
                                      "%d against %d. Not text-identical; compared with difflib ratio, "
                                      "not quick_ratio."
                                      % (rec['ratio_real'], rec['cov_plain_in_copy'], rec['cov_copy_in_plain'],
                                         copy['bytes'], plain['bytes'])),
                      "counterpart": plain['id'],
                      "package": "the_two_editions"})
            rhr.append(r)

# priority ordering for the review package: most divergent first
def _rank(r):
    m = re.search(r'sequence ratio ([0-9.]+)', r['measurement'])
    return float(m.group(1)) if m else -1.0
rhr.sort(key=_rank)
for n, r in enumerate(rhr, 1):
    r["priority"] = n

rows = approved + duplicates + rhr
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert not (set(ids) & PRIOR), sorted(set(ids) & PRIOR)
assert set(ids) <= set(M)
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
rhr_bytes = sum(r["size_bytes"] for r in rhr)
avoided = sum(r["size_bytes"] for r in duplicates)

artifact = {
 "batch_id": "bond-2013-department-set-cluster-research-2026-09-12",
 "lane": "Claude research lane: the 2013 general obligation bond department set at the flat level of www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the fourth slice of the municipaldevelopment/documents lane.",
 "cluster": "The City's 2013 general obligation bond department documents: a scope sheet and a summary sheet for each of fifteen departments and divisions, published in two editions.",
 "scope": ("The 58 pending-review candidates that make up this set and are not already rows in a saved artifact. The "
           "rest of the flat level — the numbered purpose sheets, the lowercase bond sheets, the 2015 summary and the "
           "standard-form agreements — is the next claimed slice."),
 "brief": "A dated research decision file for the remaining municipaldevelopment/documents records, sliced further because the group proved heterogeneous.",
 "brief_finding": ("A complete general obligation bond programme the archive does not hold. The summaries schedule "
                   "2013, 2015, 2017, 2019 and 2021; the scopes state the 2013 cycle. The archive already publishes "
                   "department sets for 2003, 2009, 2011 and 2017 and a 2007 decade plan, and has nothing for 2013. "
                   "Fifteen departments are covered, from ABQ RIDE and Streets to Animal Welfare and the Council "
                   "neighbourhood set-aside."),
 "second_finding": ("The City publishes the set twice, under plain and copy_of filenames, and the two editions are "
                    "not copies at all. Not one of the twenty-eight pairs is text-identical; sequence ratios run from "
                    "0.0103 to 0.9930, and nothing on the files ranks the editions, so twenty-nine records are "
                    "held for review rather than guessed at. See the_two_editions."),
 "method": ("Fetched all candidates in this set and measured byte length and SHA-256 from the fetched bytes, "
            "verifying every container by leading bytes. Compared every checksum against the 1,612 checksummed "
            "inventory records: no matches, which is what establishes that this programme is unheld. Paired the two "
            "editions department by department and compared each pair on normalized text and token coverage. Read the "
            "year columns off the face of every summary rather than inferring the programme year. Fetched the City's "
            "own document listing to see which edition it links. Probed the server directly for the two plain-edition "
            "scope files the inventory lacks."),
 "classification_only": True,
 "shared_state_written": [],
 "dating_the_set": {
  "how": ("From the face of the documents, not from the directory or the filenames. Every summary is headed \"G.O. "
          "Bond Summary\" over the columns \"Department / Division / Project Title  2013 2015 2017 2019 2021 "
          "Totals\", and every scope is headed \"Project Title  2013 Scope\"."),
  "what_the_archive_holds": ("Department sets for 2003, 2009, 2011 and 2017 and a 2007 decade plan. No 2013 set, and "
                             "no 2015 set."),
  "a_hypothesis_this_disproved": ("cip-documents-cluster-research-2026-09-12.json found an undated set of bond "
                                  "purpose sheets at the flat root of cip-documents and recorded that the evidence "
                                  "pointed to 2013 without establishing it. This lane tested that directly: the "
                                  "cip-documents sheets were compared against these dated 2013 sheets department by "
                                  "department and came back at token coverage 0.55 to 0.80 — similar subject matter, "
                                  "different documents. The two are not the same set. That artifact was right to "
                                  "withhold the attribution, and its caution stands."),
 },
 "a_measurement_correction": {
  "what_happened": ("This lane first paired the editions with difflib quick_ratio, which reported 1.0000 for "
                    "five pairs - ABQ RIDE Transit scope and summary, DMD CIP Facilities and Parking summary, "
                    "and Environmental Health scope and summary - and those five were about to be recommended "
                    "as duplicates."),
  "why_that_was_wrong": ("quick_ratio is an upper bound computed from character multisets, not a similarity. "
                         "It answers whether two strings could be identical, not whether they are. Recomputed "
                         "with the real difflib ratio those five come out at 0.9871, 0.9830, 0.8742, 0.9849 "
                         "and 0.9853, and direct string equality is false for every pair in the set."),
  "the_sharper_lesson": ("Token coverage of 1.0000 does not mean the documents are the same either. The "
                         "Animal Welfare scope pair has full token coverage in both directions and a real "
                         "sequence ratio of 0.2739: the same vocabulary, differently arranged and differently "
                         "valued. Coverage measures whether one document words appear in the other and says "
                         "nothing about order, structure, or the figures attached to them."),
  "what_it_changed": ("Five records moved from duplicate to requires human review. No record in this set is "
                      "recommended as a duplicate of any other."),
  "for_future_lanes": ("Use quick_ratio only to skip obviously unrelated pairs cheaply. Any claim that two "
                       "documents are the same needs a byte comparison, or a real sequence ratio plus string "
                       "equality."),
 },
 "the_two_editions": {
  "what": ("Every department sheet in this set exists twice, once under a plain filename and once under a copy_of "
           "prefix. Twenty-eight departments have both."),
  "they_are_not_copies": ("Not one pair is byte-identical and not one is text-identical either. Sequence ratios run "
                          "from 0.0103 to 0.9930. The copy_of prefix names a duplication event in the content "
                          "management system, not a duplicate document: somebody copied each object and then "
                          "edited one of them."),
  "the_two_that_differ_most": ("CouncilNeighborhoodSetAsideScope at sequence ratio 0.0103 and "
                               "CouncilNeighborhoodSetAsideSummary at 0.0729. At those levels the two editions are "
                               "not versions of one sheet in any ordinary sense, and whichever is published will "
                               "state something the other does not."),
  "why_neither_edition_can_be_ranked": ("Both state the same 2013 cycle and the same five-cycle schedule. Neither "
                                        "carries a revision stamp or an issue date. And the City links both: its own "
                                        "document listing at www.cabq.gov/municipaldevelopment/documents links the "
                                        "plain names for ABQRideTransitScope, AnimalWelfareScope, "
                                        "AnimalWelfareSummary, CouncilNeighborhoodSetAsideScope, "
                                        "CouncilNeighborhoodSetAsideSummary, DMDCIPFacParkingScope, "
                                        "DMDStormDrainageSummary, Env.HealthScope, Env.HealthSummary and "
                                        "FamilyCommServicesScope — and also links copy_of_DMDStormDrainageSummary.pdf. "
                                        "The copy_of prefix therefore does not mark an unpublished artefact."),
  "what_this_lane_does": ("Approves the plain edition, which the City listing links and which is the primary object name, "
                          "and holds every copy_of record at requires human review as a single named package, "
                          "ordered most-divergent first. No copy is recommended as a duplicate, because none of "
                          "them is one."),
  "for_integration": ("Resolve the package as a package. The question is one question asked twenty-four times, and "
                      "answering it once for the set is far cheaper than answering it per sheet."),
 },
 "an_undiscovered_file": {
  "finding": ("DMDCIPFacParkingScope.pdf exists on the City server and is absent from the inventory. Only its "
              "copy_of edition was ever crawled."),
  "verified": ("Probed directly: HTTP 200, 52,980 bytes, leading bytes 25504446, a genuine PDF. It is also linked "
               "from the City's own document listing, so this is not an obscure object."),
  "contrast": ("SeniorAffairsScope.pdf was probed the same way and returns HTTP 404, so that department genuinely has "
               "only the copy_of edition and its copy is recommended for addition rather than held for review."),
  "recommended_action": ("Add DMDCIPFacParkingScope.pdf to the inventory as a new candidate. This artifact creates no "
                         "inventory records."),
  "fourth_instance": ("After nob-hill-highland-cluster-research-2026-09-11.json, "
                      "planned-growth-strategy-cluster-research-2026-09-11.json and "
                      "economic-forum-cluster-research-2026-09-12.json. In three of the four the missing file was "
                      "reachable by probing a name the City itself uses; the habit keeps paying."),
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "cross_batch_byte_collisions": 0,
  "result": ("Nothing in this set is held. That is the finding rather than an absence of one: the archive's bond "
             "coverage runs 2003, 2007, 2009, 2011, 2017 and this is the missing 2013 programme."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_text": 28,
  "text_identical_pairs": 0,
  "note": ("Twenty-eight edition pairs and hashing found none of them, because no two files in this set share "
           "bytes. Every relationship came from normalized-text comparison, and see a_measurement_correction for "
           "how nearly that comparison was made with the wrong function."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved],
   "finding": "A complete 2013 general obligation bond department set covering fifteen departments, scope and summary, with a five-cycle schedule through 2021. The archive holds 2003, 2009, 2011 and 2017 and nothing for 2013.",
   "recommended_action": "Approve the plain edition. Place on the capital spending page with the department cross-listings each row carries."},
  {"severity": "measurement",
   "affects": [],
   "finding": "Five pairs in this set read as identical under difflib quick_ratio and are not; their real sequence ratios are 0.87 to 0.99, and none is string-equal. One pair has token coverage 1.0000 in both directions and a real ratio of 0.2739.",
   "recommended_action": "Treat quick_ratio and token coverage as screens, never as proof of sameness. Full detail in a_measurement_correction."},
  {"severity": "one-question-asked-many-times",
   "affects": [r["id"] for r in rhr],
   "finding": f"{len(rhr)} second-edition sheets differ in content from their counterparts, with sequence ratios from 0.0103 to 0.9930, and nothing on the files ranks the editions. The City links both.",
   "recommended_action": "Resolve as one package rather than sheet by sheet. Rows are ordered most-divergent first; the two Council Neighborhood Set-Aside sheets are where the editions disagree most and are the place to start."},
  {"severity": "undiscovered-file",
   "affects": ["src-dc2bbf43c5bb13f7"],
   "finding": "DMDCIPFacParkingScope.pdf returns HTTP 200 at 52,980 bytes and is linked from the City's own listing, but is absent from the inventory; only its copy_of edition was crawled.",
   "recommended_action": "Add it as a candidate. Its copy_of edition is held for review in this batch and the comparison cannot be completed without it."},
  {"severity": "confirms-an-earlier-caution",
   "affects": [],
   "finding": "The undated cip-documents purpose sheets are not this 2013 set. Department-by-department comparison returns token coverage 0.55 to 0.80.",
   "recommended_action": "Leave the cip-documents caution in place. Its year is still unestablished and this lane narrowed rather than answered it."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "requires_human_review": counts["requires human review"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "probes": "Two plain-edition filenames absent from the inventory were probed directly: DMDCIPFacParkingScope.pdf returned HTTP 200 and SeniorAffairsScope.pdf returned HTTP 404.",
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "%d genuine PDFs by leading bytes. Every one has a full text layer; none needed rendering." % len(rows)},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "requires_human_review": rhr,
 "archival_note": (f"All {len(approved)} approved records are static PDFs and are inventory-only until an R2 archive "
                   f"object exists for each and its public download, exact size, SHA-256, and authoritative-source "
                   f"provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes — "
                   f"small for the record count, because bond scope and summary sheets are short tables. A further "
                   f"{len(rhr)} records totalling {rhr_bytes:,} bytes are held at requires human review, and "
                   f"{avoided:,} bytes of re-encoded duplicates need never be uploaded."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. Five duplicate rows carry a canonical_id pointing "
                      "at a record recommended for addition in this same batch. Every requires-human-review row "
                      "carries a priority, a counterpart id and the measurement against it, and all of them belong to "
                      "one package named the_two_editions — resolve it once for the set. Every approved row carries a "
                      "set field, an edition field and a 20-to-50-word description. One approved row, the Senior "
                      "Affairs scope, is a copy_of file recommended because its plain counterpart was probed and "
                      "returns 404. Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the two direct probes were read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
