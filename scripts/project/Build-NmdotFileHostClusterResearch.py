"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. The NMDOT public file host at api.realfile.rtsclients.com.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\nmdot-file-host-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\rf')

TRANSPO = 'content/transportation/_index.md'
TRANSIT = 'content/transportation/transit/abq-ride.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
SAFETY = 'content/transportation/safety-crash-data.md'
DESIGNREF = 'content/transportation/design-references.md'
OPSDATA = 'content/transportation/operations-data.md'
DEVPROC = 'content/development-land-use/development-process.md'
CAPITAL = 'content/city-data/capital-spending.md'
CLIMATE = 'content/city-data/climate-environment.md'
MAPS = 'content/maps-data/maps.md'

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

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML', 'd0cf11e0': 'OLE2'}

LC = ("HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. "
      "Container verified by leading bytes, not by extension - one file named .xls in this set is a legacy OLE2 "
      "document and was read as one.")


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i]))


def invtitle(i):
    return (IDX[i].get('title') or '').strip()


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i],
         "publisher": "New Mexico Department of Transportation",
         "served_filename": fname(i)}
    r.update(M[i])
    return r


BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
TWIN_GROUPS = [sorted(v) for v in BYHASH.values() if len(v) > 1]

# id -> (title, group, canonical page, crosses, evidence-extra)
TRUCK = ['src-1f8378fe0d939884', 'src-1ce9fae6e4b2e675', 'src-a5f4c28aefd1ce20', 'src-57017bee270744dd',
         'src-68d5d6b446b98b35', 'src-b07a77c5f6cd79b3', 'src-84c88a71842b2ed1']
FTA = ['src-e5a3f02506f8a4f1', 'src-15cbbf915ccd9c8d', 'src-92870e1ee8d3cc8c', 'src-c427f1031b8c0a99',
       'src-ed690ceff6122f7a', 'src-cc7cc72752250807', 'src-67aa71fbec16d4fb', 'src-4411ec8b5839b8f9',
       'src-a5bd813703037d72', 'src-b3c1915b03ebdb15']
CIVIL = ['src-a028cb0d25814dcc', 'src-fa2f190eeab51564', 'src-215f7ebe10448449', 'src-30c9d7ca833e35e9',
         'src-6843518427df8109', 'src-ec9bd5ed1b7aca50', 'src-88f944dbfe6f4831', 'src-d82a0ffd1bb9d8f2',
         'src-5d29975d450c87e7', 'src-da117aa947705598', 'src-8859e639d264ca7e', 'src-2c5e9cba41f05696',
         'src-f23bf095fc3eac20', 'src-a89dd585b7d6d020']
RESEARCH = ['src-bfd6a6e8dc936c4d', 'src-2826813909b1548c', 'src-1a3dbc1c91c6784e', 'src-1c75e93666315529',
            'src-2ddb235150419d93']
GRANTS = ['src-1238f81673c19398', 'src-b8b65025c4f54a63', 'src-fa13a1cec10ea9d0', 'src-80a1ba651fd935cd',
          'src-087c613a50cf2f77', 'src-9a2d7938040450e4', 'src-7a0927957c7eacfd', 'src-de1be5126ebdb066',
          'src-ba150abfb1b8a847', 'src-3983b9dec570f033', 'src-3ed48708a5cd8eb4', 'src-15424a3ed5d9118b',
          'src-d617f438901ade14', 'src-db216e455e924569', 'src-fe26357deaa58dbb', 'src-41b913bce3be7d93',
          'src-71fa71c632ce4b6a', 'src-3d73a376de5f93d7']
SERVICE = ['src-648b476ad99e49d3', 'src-355191ce536edca9', 'src-dba9abf49749fbfb', 'src-7f6b47365f88a1d9',
           'src-62412d766f736954', 'src-5f05f0b7ab695763', 'src-796499c95ca7baf9', 'src-135f806284239cdd',
           'src-99489f2f648c9c72', 'src-4a925842f67b6990', 'src-ea1e46d50c2e92f1', 'src-9b0e6cf43add0b5f',
           'src-a3781e257fc415ed', 'src-53c9738d30d79896', 'src-f6525df049a656f7', 'src-e387ed43fdb6a196']

TITLE_FROM_DOC = {
 'src-4a925842f67b6990': ("NMDOT Transit and Rail Division: 2023 Transit Guide",
                          "The inventory title reads Related Links, which is the navigation text of the page it was found on. The document is the 2023 Transit Guide of the NMDOT Transit and Rail Division."),
 'src-a89dd585b7d6d020': ("NMDOT Event and Comment Form",
                          "The inventory title reads Event (1).Pdf. The document is headed Event/Comment Form and collects a member of the public's name, email and telephone with their comment."),
 'src-648b476ad99e49d3': ("NMDOT Park and Ride: Northern New Mexico route letter, 2026",
                          "The inventory title reads Green Route - Espanola-Los Alamos; the served file is NM Northern Routes Letter 2026.pdf and covers the northern route set."),
 'src-355191ce536edca9': ("NMDOT Park and Ride: Santa Fe route letter, 2026",
                          "The inventory title reads National Guard/Corrections Shuttle; the served file is NM Santa Fe Routes Letter 2026.pdf."),
 'src-dba9abf49749fbfb': ("NMDOT Park and Ride: Southern New Mexico route letter, 2026 (Spanish)",
                          "The inventory title reads Rutas del Sur NMDOT Park and Ride Horario; the served file is NM Southern Routes Letter 2026.pdf."),
 'src-da37e2197d571ffd': ("Mid-Region RTPO/MPO Coordinated Public Transit - Human Services Transportation Plan, 2024",
                          "Headed Mid-Region RTPO/MPO, Coordinated Public Transit - Human Services Transportation Plan, over New Mexico Department of Transportation. A Mid-Region Council of Governments plan served from NMDOT's file host."),
 'src-553ffa2b017f3175': ("FHWA Vulnerability Assessment and Adaptation Framework, Third Edition",
                          "Headed Vulnerability Assessment and Adaptation Framework, THIRD EDITION, FEDERAL HIGHWAY ADMINISTRATION. A federal publication served from NMDOT's file host."),
}

GROUP_OF = {}
for i in TRUCK:
    GROUP_OF[i] = "statewide truck parking study"
for i in FTA:
    GROUP_OF[i] = "FTA transit budget awards"
for i in CIVIL:
    GROUP_OF[i] = "civil rights notices and complaint forms"
for i in RESEARCH:
    GROUP_OF[i] = "NMDOT research reports"
for i in GRANTS:
    GROUP_OF[i] = "grant administration and application"
for i in SERVICE:
    GROUP_OF[i] = "Park and Ride and transit service"
for i in SLICE:
    GROUP_OF.setdefault(i, "statewide planning and standards")

PAGE_OF = {
 "statewide truck parking study": (STUDIES, [{"page": TRANSPO, "reason": "A statewide freight study."}]),
 "FTA transit budget awards": (TRANSIT, [{"page": CAPITAL, "reason": "Federal transit money awarded to New Mexico providers."}]),
 "civil rights notices and complaint forms": (TRANSIT, [{"page": DEVPROC, "reason": "The process by which a rider files a civil rights complaint."}]),
 "NMDOT research reports": (DESIGNREF, [{"page": STUDIES, "reason": "State transportation research."}]),
 "grant administration and application": (DEVPROC, [{"page": CAPITAL, "reason": "How federal and state transportation grants are applied for and administered."}]),
 "Park and Ride and transit service": (TRANSIT, [{"page": TRANSPO, "reason": "Statewide transit service reaching Albuquerque."}]),
 "statewide planning and standards": (TRANSPO, [{"page": OPSDATA, "reason": "Statewide transportation planning and measurement."}]),
}

FRAME = {
 "statewide truck parking study": ("Part of the New Mexico Department of Transportation's statewide truck parking "
                                   "study: %s, one of the seven numbered deliverables in which the study was "
                                   "published."),
 "FTA transit budget awards": ("The New Mexico Department of Transportation's record of %s, listing the transit "
                               "providers across the state that received federal money that year and how much each "
                               "was awarded."),
 "civil rights notices and complaint forms": ("The New Mexico Department of Transportation's %s, part of the notices "
                                              "and complaint machinery it must publish under federal civil rights "
                                              "law for the transit services it funds and operates."),
 "NMDOT research reports": ("A research report commissioned by the New Mexico Department of Transportation: %s, "
                            "carried out for the department and published on its own file host."),
 "grant administration and application": ("The New Mexico Department of Transportation's %s, part of the paperwork "
                                          "by which transit providers and local governments apply for state and "
                                          "federal transportation money and account for it."),
 "Park and Ride and transit service": ("The New Mexico Department of Transportation's %s, part of the public "
                                       "information for the statewide Park and Ride and transit services that reach "
                                       "Albuquerque."),
 "statewide planning and standards": ("The New Mexico Department of Transportation's %s, a statewide planning, "
                                      "standards or measurement record published on the department's own file "
                                      "host."),
}

approved, duplicate = [], []
DUP_IDS = set()
for grp in TWIN_GROUPS:
    canon = grp[0]
    for copy in grp[1:]:
        DUP_IDS.add(copy)
        r = row(copy, "duplicate")
        r.update({"canonical_id": canon,
                  "title_for_reference": invtitle(copy) or fname(copy),
                  "relationship": "The same file registered twice in the inventory under two candidate ids.",
                  "how_it_was_established": ("Byte-identical: both %s bytes with the same SHA-256, and both served "
                                             "the same filename, %s." % (format(M[copy]['size_bytes'], ','), fname(copy))),
                  "why_this_one_is_the_copy": "Arbitrary between two identical registrations; the first id is taken as canonical and the relationship is what matters.",
                  "group": "duplicates"})
        duplicate.append(r)

for i in SLICE:
    if i in DUP_IDS:
        continue
    g = GROUP_OF[i]
    canon, cross = PAGE_OF[g]
    if i in TITLE_FROM_DOC:
        t, extra = TITLE_FROM_DOC[i]
        subject = t
    else:
        t = invtitle(i) or fname(i)
        subject = t
        extra = ""
    desc = FRAME[g] % subject
    w = desc.split()
    if len(w) > 50:
        desc = ' '.join(w[:48]).rstrip(',.;') + '.'
    ev = "Served from NMDOT's public file host as %s." % fname(i)
    if extra:
        ev += " " + extra
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc, "evidence": ev, "group": g,
              "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if i in ('src-da37e2197d571ffd', 'src-553ffa2b017f3175', 'src-747cfb4eb2710678'):
        r["publisher"] = ("Mid-Region Council of Governments" if i == 'src-da37e2197d571ffd'
                          else "Federal Highway Administration")
        r["hosted_by"] = "New Mexico Department of Transportation"
    approved.append(r)

rows = approved + duplicate
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:6], sorted(set(ids) - set(SLICE))[:6])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

HELD_FTA = ["FY 2022", "FY 2023", "FY 2024", "FY 2025", "FY 2026", "FY 2027"]

artifact = {
 "batch_id": "nmdot-file-host-cluster-research-2026-09-13",
 "lane": "Claude research lane: the NMDOT public file host at api.realfile.rtsclients.com",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("Everything still uncovered on the file host the New Mexico Department of Transportation serves its "
             "public documents from: a seven-part statewide truck parking study, a decade of federal transit budget "
             "awards, the department's civil rights notices and complaint forms, its commissioned research, its "
             "grant paperwork, and its Park and Ride service information."),
 "scope": "All 87 uncovered candidates on the endpoint. The coverage gate is asserted in the generator.",
 "brief": ("This is a third-party document-hosting endpoint rather than a City domain, so establish first what "
           "agency the files belong to and whether the endpoint is the authoritative source or a vendor mirror."),
 "brief_answered": {
  "whose_files_they_are": ("NMDOT's. Across the extracted text of the 87 files, NMDOT appears 256 times and New "
                           "Mexico Department of Transportation 76 times. Santa Fe Trails appears 11 times, "
                           "Mid-Region 8, Rio Metro 4, ABQ RIDE once."),
  "whether_the_endpoint_is_authoritative": ("It is. The endpoint is not a mirror of dot.nm.gov; it is where "
                                            "dot.nm.gov's own pages link their files. The archive's existing records "
                                            "from this endpoint carry parent_url values on dot.nm.gov - one of them "
                                            "the department's Research and Climate Bureau page."),
  "and_the_archive_has_already_decided_this": ("42 records from this exact endpoint are already validated, 41 of "
                                               "them with an r2_url, filed under agency values NMDOT, New Mexico "
                                               "Department of Transportation, and Other authoritative source. "
                                               "Separately the archive holds 62 validated NMDOT records overall."),
 },
 "a_correction_to_my_own_practice": {
  "what_happened": ("This is the second lane running whose brief I wrote on the assumption that a partner agency's "
                    "material might fall under the third-party rule, and the second time the inventory answered the "
                    "question before I asked it. For MRCOG the archive already held 117 validated records; for "
                    "NMDOT it holds 62, and 42 from this very endpoint."),
  "the_lesson": ("Check the inventory for the archive's existing decisions about a source before writing the brief "
                 "for a lane, not after. A brief that starts from the wrong premise costs a whole lane's framing, "
                 "and twice now the correction has been the first thing the artifact had to say."),
  "what_it_did_not_change": ("Nothing in the dispositions. Both lanes would have reached the same recommendations; "
                             "what was wrong was the question I told myself to answer."),
 },
 "a_series_extended_backwards_by_a_decade": {
  "what_the_archive_holds": ("Six years of FTA transit budget awards, FY2022 through FY2027, every one validated "
                             "with an r2_url."),
  "what_this_lane_found": ("Ten more, FY2012 through FY2021, including the year the CARES Act money appears. "
                           "Together they make an unbroken FY2012 to FY2027 run."),
  "why_it_matters": ("These list, year by year, which transit providers in New Mexico received federal money and how "
                     "much. A six-year window shows the current position; a sixteen-year run shows how the money "
                     "moved."),
  "the_years_added": ["FY 2012", "FY 2013", "FY 2014", "FY 2015", "FY 2016", "FY 2017", "FY 2018", "FY 2019",
                      "FY 2020", "FY 2021"],
  "the_years_already_held": HELD_FTA,
 },
 "the_truck_parking_study": {
  "count": len(TRUCK),
  "what_it_is": ("A complete seven-part statewide truck parking study, published as numbered deliverables: project "
                 "management plan, stakeholder engagement plan, literature review and best practices, freight "
                 "activity evaluation, truck parking supply and demand, interstate truck parking assessment, and "
                 "recommendation and implementation plan."),
  "note": ("The final deliverable is 55,752,016 bytes, the largest single file in this lane. Five of the seven are "
           "OOXML rather than PDF and should be archived in their original format."),
 },
 "three_documents_that_are_not_NMDOTs": {
  "count": 3,
  "which": ["The Mid-Region RTPO/MPO Coordinated Public Transit - Human Services Transportation Plan, 2024, which is MRCOG's.",
            "The FHWA Vulnerability Assessment and Adaptation Framework, Third Edition, which is the Federal Highway Administration's.",
            "Model Performance Measures for State Traffic Records Systems, a federal publication."],
  "how_they_are_recorded": ("Their rows carry the actual publisher in the publisher field and NMDOT in hosted_by, so "
                            "the distinction survives integration. They are recommended, not excluded: the archive "
                            "has already validated a Federal Highway Administration record from this same endpoint, "
                            "and MRCOG is in scope on the evidence of 117 validated records."),
  "why_it_is_worth_flagging_anyway": ("A file host is not a publisher. Reading provenance off the domain would have "
                                      "attributed all three to NMDOT."),
 },
 "seven_inventory_titles_that_are_not_the_document": {
  "count": len(TITLE_FROM_DOC),
  "the_worst": ("A 17,401,443-byte record titled Related Links. The document is the NMDOT Transit and Rail "
                "Division's 2023 Transit Guide. Related Links is the navigation text of the page the crawler found "
                "it on."),
  "others": ["Event (1).Pdf is an Event/Comment Form.",
             "Green Route - Espanola-Los Alamos is the NM Northern Routes Letter 2026.",
             "National Guard/Corrections Shuttle is the NM Santa Fe Routes Letter 2026.",
             "Rutas del Sur NMDOT Park and Ride Horario is the NM Southern Routes Letter 2026."],
  "how_they_are_handled": "Every row carries a served_filename field alongside the title taken from the document, so the mismatch is visible rather than buried.",
  "the_running_count": "Seventeen records across this run now carry a title, filename or extension that contradicts the document or the bytes behind it.",
 },
 "method": ("Fetched all 87 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. "
            "Extracted text with the right reader for each container and fingerprinted the whole set for agency "
            "names to answer the brief's first question. Read the inventory for the archive's existing treatment of "
            "this endpoint and of NMDOT generally, which answered the second. Grouped by checksum to find records "
            "registered twice. Read every file whose inventory title did not match its served filename."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": len(TWIN_GROUPS),
  "result": "Nothing here duplicates anything the archive holds. The three byte collisions are internal: the same file registered twice under two candidate ids.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": len(TWIN_GROUPS),
  "cross_inventory_byte_collisions": 0,
  "checksums_compared_against": 1612,
  "relationships_found": len(duplicate),
  "note": ("Three pairs are byte-identical and each pair is one document registered twice: the Title VI complaint "
           "form in English, the same form in Spanish, and the ADA modification request and process in Spanish. The "
           "English and Spanish notices of non-discrimination look like the same case and are not - 206,129 against "
           "109,311 bytes for the English pair and 246,573 against 104,486 for the Spanish. Different files, both "
           "retained."),
 },
 "integration_flags": [
  {"severity": "scope-correction",
   "affects": [],
   "finding": "This lane's brief treated the endpoint as a possibly-third-party vendor host. It is NMDOT's own file host, linked from dot.nm.gov pages, and the archive already holds 42 validated records from it plus 62 validated NMDOT records overall.",
   "recommended_action": "Record the endpoint as an accepted NMDOT source. And check the inventory for prior decisions about a source before framing a lane around it; this is the second lane in a row where that would have saved a wrong premise."},
  {"severity": "completes-a-series",
   "affects": FTA,
   "finding": "Ten years of FTA Section 5310/5311 transit budget awards, FY2012 through FY2021, against the six years FY2022 to FY2027 the archive already holds validated with r2_urls. Together an unbroken sixteen-year run.",
   "recommended_action": "Approve and publish as one series with the six already held."},
  {"severity": "substantive-find",
   "affects": TRUCK,
   "finding": "A complete seven-part statewide truck parking study, from project management plan through recommendation and implementation plan. Five parts are OOXML; the final report is 55,752,016 bytes.",
   "recommended_action": "Approve as a set. Archive the OOXML parts in their original format rather than converting them."},
  {"severity": "provenance",
   "affects": ['src-da37e2197d571ffd', 'src-553ffa2b017f3175', 'src-747cfb4eb2710678'],
   "finding": "Three documents on this host are not NMDOT's: an MRCOG coordinated transit plan and two federal publications. Their rows carry the real publisher and record NMDOT as hosted_by.",
   "recommended_action": "Keep the distinction through integration. A file host is not a publisher."},
  {"severity": "title-from-the-document",
   "affects": sorted(TITLE_FROM_DOC),
   "finding": "Seven inventory titles do not describe their document. The clearest is a 17.4 MB record titled Related Links which is the NMDOT 2023 Transit Guide.",
   "recommended_action": "Use the titles in this artifact; every row also carries served_filename so the mismatch stays visible."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "containers_verified": ("%d PDFs, %d OOXML files and %d legacy OLE2 documents by leading bytes."
                                        % (bycontainer['PDF'], bycontainer['OOXML'], bycontainer['OLE2']))},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "requires_human_review": [],
 "excluded": [],
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, the largest of any "
                   f"lane in this run and dominated by the truck parking study and the research reports. "
                   f"{bycontainer['OOXML']} approved records are OOXML and {bycontainer['OLE2']} are legacy OLE2 "
                   f"documents; all should be archived in their original format rather than converted."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Three rows carry a canonical_id and all three "
                     "canonicals are approved rows in this artifact. Every row carries a publisher, a "
                     "served_filename and a group; three rows carry a publisher that is not NMDOT together with "
                     "hosted_by. Seven rows are titled from the document rather than from the inventory and say so "
                     "in their evidence. Nothing in this lane is excluded or held for review. Sizes and checksums "
                     "are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
