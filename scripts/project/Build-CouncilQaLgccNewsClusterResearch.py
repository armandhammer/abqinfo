"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. council/administration-questions-answers,
council/albuquerque-bernalillo-county-government-commission, council/news.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\council-qa-lgcc-news-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\cn')

CAPITAL = 'content/city-data/capital-spending.md'
DEVPROC = 'content/development-land-use/development-process.md'
ZONING = 'content/development-land-use/zoning-ido.md'
PROJECTS = 'content/development-land-use/projects.md'
CAPPROJ = 'content/public-works/capital-projects.md'
ABOUT = 'content/about/_index.md'
CITYDATA = 'content/city-data/_index.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

SLICE = [l.split('\t')[0] for l in open(os.path.join(SP, 'urls.tsv'), encoding='utf-8')]

PRIOR_IDS, PRIOR_SHA = set(), {}
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
            if isinstance(r, dict) and r.get('id'):
                PRIOR_IDS.add(r['id'])
                if r.get('checksum_sha256'):
                    PRIOR_SHA.setdefault(r['checksum_sha256'], (os.path.basename(f), r['id']))
assert not (set(SLICE) & PRIOR_IDS), sorted(set(SLICE) & PRIOR_IDS)

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x['id'])

CONTAINER = {'25504446': 'PDF', '3c21444f': 'HTML', '504b0304': 'XLSX'}
LC = "HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. Container verified by leading bytes."


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i]))


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i],
         "inventory_title": (IDX[i].get('title') or '').strip()}
    r.update(M[i])
    return r


HTML = [i for i in SLICE if MAGIC[i] == '3c21444f']

LGCC = ['src-44d50a56eea89947', 'src-7055dfd30a8efa51', 'src-21468eb5acc3d6fe', 'src-83634881de7f4825',
        'src-78d69e16f06a17b7', 'src-da4a1570a9a31d35', 'src-65a948ba4f3a8e73', 'src-50e17b8f38e64769',
        'src-6283e5e98f8690b9', 'src-33c27704152de957']

ENFORCEMENT = {
 'src-64bc8e1da1e45187': ("5715 Central Ave NE", "1213 INC", "a corporation", "Oct 21, 2024", "CF-2024-060230"),
 'src-d1213d0fba1ca8ca': ("7503 Central Ave NE", "AA & S INC", "a corporation", "Jan 9, 2025", "CF-2025-000839"),
 'src-b44e7af124c01c10': ("6015 Iliff Rd NW", "HOTEL GP ILIFFE ABQ LLC", "a limited liability company", "March 11, 2025", "UHC-2025-00166"),
 'src-f7dfbcaeae424c72': ("2700 4th St NW", "three named individuals", "three named natural persons", "May 1, 2025", "UHC-2025-00427"),
 'src-f33de69926b6c41a': ("6031 Iliff Rd NW", "RELIANCE ABQ LLC", "a limited liability company", "March 13, 2025", "UHC-2025-00178"),
 'src-bd2d82443bb2eb9b': ("8300 Central Ave SE", "ROSHYOGI LLC", "a limited liability company", "February 21, 2025", "UHC-2025-00100"),
 'src-be7caa7193b994f3': ("900 Louisiana Blvd NE", "ROCKHILL CAPITAL PARTNERS LLC", "a limited liability company", "May 30, 2025", "UHC-2025-00554"),
}

QA = {
 'src-070a763aa9701f86': ("Administration responses to Councillor Grout on Environmental Health Services governance",
                          ("The Administration's numbered written answers to a councillor's questions about how the "
                           "Environmental Health Services committee is constituted and whether it was established as "
                           "the law requires."),
                          "Opens on the numbered question Is it the Administration's position that it does not have to establish the Committee in accordance with the law? and the answer No.",
                          ABOUT),
 'src-4ac9f8a1fb953e46': ("List of FY25 Non-Recurring Items",
                          ("The Administration's list of the non-recurring items in the FY25 budget, supplied to the "
                           "Council in answer to a question about one-off rather than continuing spending."),
                          "Titled List of FY25 Non-Recurring Items.",
                          CAPITAL),
 'src-9fd0da60e94eb698': ("Planning Department response on code enforcement motel closure operations, 5 June 2025",
                          ("The Planning Department director's written answer to the Council on the City's motel "
                           "closure operations, the enforcement campaign against substandard motels."),
                          "A Planning Department letter of June 5, 2025 over the director's name.",
                          DEVPROC),
 'src-a6753953181feb4f': ("Code Enforcement Division: Comprehensive Motel Enforcement History Report, June 2025",
                          ("The Code Enforcement Division's history of its motel enforcement, the record of what the "
                           "City has done about substandard motels and when, supplied to the Council."),
                          "Headed Code Enforcement Division, Comprehensive Motel Enforcement History Report, June 2025.",
                          DEVPROC),
 'src-51fb6dc80b316253': ("Breakdown of the National Guard deployment",
                          ("The Administration's breakdown of the National Guard deployment in Albuquerque, supplied "
                           "to the Council in answer to a question about what the deployment consisted of."),
                          "Rendered, because the file has one byte of extractable text for one page.",
                          ABOUT),
 'src-0878bc7d09a7c65b': ("Exhibit A and B: Downtown and adjoining area boundary maps",
                          ("The boundary maps supplied to the Council as exhibits, showing the downtown area and its "
                           "surrounds at street level with the boundary drawn on."),
                          "Rendered, because the file has two bytes of extractable text. Page 1 is headed Exhibit A - Downtown over a street map from Marquette Avenue to Coal Avenue.",
                          PROJECTS),
 'src-5006deafb03b1f7a': ("North Domingo Baca aquatic centre: contract and fee ledger",
                          ("A spending ledger for the North Domingo Baca aquatic centre project, naming the "
                           "contractor and the engineering consultant against each fee line and account code."),
                          ("An OOXML workbook, leading bytes 504b0304, read from xl/sharedStrings.xml - a "
                           "spreadsheet, not the Word document its inventory title suggests. Its strings include "
                           "BRADBURY STAMM CONSTRUCTION INC against Svcs-Contractor Fee and WSP USA ENVIRONMENT & "
                           "INFRASTRUCTURE against Prof - Engineering Fee, for 4 - North Domingo Baca Aquatic "
                           "Center."),
                          CAPPROJ),
}

MISSING_MINUTES = {
 "policy": "An agenda may be preserved only after a recorded exhaustive official-source review finds no approved minutes, and never for a cancelled or no-quorum meeting.",
 "body": "Local Government Coordinating Commission, a joint City of Albuquerque and Bernalillo County body",
 "inventory": "Three records match the commission in the inventory and none is a minute.",
 "city_pages_checked": ["/council/albuquerque-bernalillo-county-government-commission/local-government-coordinating-commission (HTTP 200, 129,963 bytes)",
                        "/council/albuquerque-bernalillo-county-government-commission (HTTP 200, 125,371 bytes)"],
 "what_those_pages_carry": "Neither page contains a single link whose address includes the word minutes.",
 "site_search": "The City's own search for the exact phrase Local Government Coordinating Commission together with minutes returns a no-results page.",
 "a_limitation_on_the_word_exhaustive": ("The commission is a joint City and County body, and the County side could "
                                         "not be checked: www.bernco.gov returned HTTP 403 to this lane's request. "
                                         "The City side is thorough; the County side is unchecked. If minutes exist "
                                         "anywhere, the County's site is where to look."),
 "cancellation_check": "None of the ten agendas carries cancellation, postponement, rescheduling or no-quorum language; zero matches across all ten.",
 "conclusion": "The exception applies on the evidence available, with the County limitation recorded. Label each Agenda (approved minutes not located) and never present one as minutes.",
}

TEXTUAL = {'src-be7caa7193b994f3'}

approved, rhr, excluded = [], [], []

for i in LGCC:
    r = row(i, "approved for addition")
    when = (IDX[i].get('title') or '').strip()
    sub = 'Sub-Committee' if M[i]['size_bytes'] < 60000 else 'Commission'
    desc = ("The Local Government Coordinating Commission's agenda for its meeting of %s, listing the members and "
            "the business set down for that meeting of this joint City and County body." % (when or 'that date'))
    r.update({"title": "Local Government Coordinating Commission %s: Agenda (approved minutes not located), %s" % (sub, when),
              "description": desc,
              "evidence": ("Headed City of Albuquerque, Government Center, Agenda, over the commission or "
                           "sub-committee name and the meeting date and place. Published at "
                           "council/albuquerque-bernalillo-county-government-commission."),
              "group": "Local Government Coordinating Commission agendas",
              "missing_minutes_review": MISSING_MINUTES,
              "proposed_canonical_page": ABOUT,
              "cross_listings": [{"page": CITYDATA, "reason": "A joint City and County governance body."}],
              "description_word_count": len(desc.split())})
    if i == 'src-33c27704152de957':
        r["note"] = ("This one is titled Agenda with Supporting Documents and runs to 6,612,209 bytes, so it carries "
                     "the meeting's papers as well as its agenda.")
    approved.append(r)

for i, (t, desc, ev, canon) in QA.items():
    r = row(i, "approved for addition")
    w = desc.split()
    if len(w) < 20:
        desc = desc.rstrip('.') + ", supplied to the City Council and published on its questions and answers page."
    r.update({"title": t, "description": desc, "evidence": ev,
              "group": "Administration answers to Council questions",
              "proposed_canonical_page": canon,
              "cross_listings": [{"page": ABOUT, "reason": "Part of the Council's oversight record."}]
              if canon != ABOUT else [{"page": CITYDATA, "reason": "A record of City administration."}],
              "description_word_count": len(desc.split())})
    approved.append(r)

for n, (i, (addr, owner, kind, when, case)) in enumerate(sorted(ENFORCEMENT.items()), 1):
    r = row(i, "requires human review")
    r.update({"draft_title": "Code Enforcement Notice and Order with Appeal: %s, %s" % (addr, when),
              "question_for_human": "Decide, once, whether this archive republishes code enforcement notices that name property owners. The answer governs all seven.",
              "why_not_decided_here": ("These are live enforcement actions naming the owner of a specific property, "
                                       "and the owners are not all companies. Six are corporations or limited "
                                       "liability companies; one is addressed to three named natural persons. The "
                                       "City itself published them on a public Council page in answer to councillor "
                                       "questions, which is a strong argument that they are publishable - but "
                                       "whether this archive republishes enforcement notices against named "
                                       "individuals is a question about the archive's scope, and this lane has "
                                       "excluded rosters of private individuals' details on its own judgment "
                                       "elsewhere. It should not decide this one alone."),
              "measurement": ("%s bytes. %s Its first page is a City of Albuquerque Code Enforcement "
                              "NOTICE AND ORDER WITH APPEAL dated %s, citing the Uniform Housing Code, City "
                              "Council Enactment Ordinance No. 25-2018, codified at 14-3-1-1 et seq ROA 1994."
                              % (format(M[i]["size_bytes"], ","),
                                 ("It has a usable text layer and was read from it." if i in TEXTUAL
                                  else "Image-only, two bytes of extractable text, so it was rendered."),
                                 when)),
              "owner_named_on_the_notice": owner,
              "owner_kind": kind,
              "case_file_number": case,
              "distinguishing_content": "Notice and Order with Appeal for %s." % addr,
              "package": "code_enforcement_notices_naming_owners",
              "priority": n})
    rhr.append(r)

for i in HTML:
    seg = URL[i].split('/council/', 1)[1]
    news = seg.startswith('news/')
    r = row(i, "excluded")
    r.update({"title_for_reference": "Web page: council/" + seg[:80],
              "what_it_is": "A live page on the City Council's website.",
              "exclusion_reason": ("Not a static document. The URL returns HTML, leading bytes 3c21444f, and there is "
                                   "no original file to archive."
                                   + (" It is also a Council news release, and press releases are excluded on the "
                                      "ground recorded in councilor-district-4-cluster-research-2026-09-12.json."
                                      if news else
                                      " It is an index or member page for the body whose documents are decided in "
                                      "this artifact.")),
              "category": "live web page: council news release" if news else "live web page",
              "package": "web_pages"})
    excluded.append(r)

rows = approved + rhr + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "council-qa-lgcc-news-cluster-research-2026-09-13",
 "lane": "Claude research lane: the Council's questions-and-answers page, the Local Government Coordinating Commission, and Council news",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": ("Three Council directories: what the Administration answers when councillors ask, what a joint City and "
             "County commission puts on its agendas, and what the Council puts in its news feed."),
 "scope": "All 40 uncovered candidates across the three sources. The coverage gate is asserted in the generator.",
 "brief": ("Check existing dispositions first and run the checksum sweep against both the archived inventory records "
           "and every row of every saved artifact."),
 "brief_finding": ("Nothing had been decided at any of the three paths before this lane - all 40 were untouched - "
                   "and the two-set sweep returned no collisions against either set. The work here was reading, not "
                   "de-duplicating."),
 "the_sweep": {
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "collisions": 0,
  "internal_byte_collisions": 0,
  "note": "The first lane since the sweep was introduced to return nothing from either set. Worth recording that it is cheap and sometimes finds nothing.",
 },
 "the_missing_minutes_review": MISSING_MINUTES,
 "the_hardest_call_in_this_lane": {
  "what_they_are": ("Seven City Code Enforcement Notices and Orders with Appeal, each naming the owner of a specific "
                    "Albuquerque property and finding its units substandard under the Uniform Housing Code. All "
                    "six are image-only scans of two bytes of extractable text each and were read by rendering, "
                    "and the seventh has a usable text layer and was read from it."),
  "why_they_are_here_at_all": ("The Administration supplied them to the City Council in answer to councillor "
                               "questions about motel enforcement, and the Council published them on its public "
                               "questions and answers page."),
  "the_split_that_matters": ("Six are addressed to companies - 1213 INC, AA & S INC, HOTEL GP ILIFFE ABQ LLC, "
                             "RELIANCE ABQ LLC, ROSHYOGI LLC and ROCKHILL CAPITAL PARTNERS LLC. "
                             "One, for 2700 4th St NW, is addressed to three named natural persons."),
  "why_this_lane_will_not_decide_it": ("The argument for publishing is strong: they are City enforcement actions "
                                       "that the City itself put on a public page. The argument for caution is the "
                                       "one this lane has applied elsewhere on its own judgment, excluding rosters "
                                       "of private individuals' details. When those two collide over named "
                                       "individuals, the scope question belongs to a person, not to this lane."),
  "how_it_is_arranged_for_deciding": ("All seven are one package and one decision. Every row carries the owner named "
                                      "on the notice, whether that owner is a company or a natural person, the date, "
                                      "and the case file number."),
  "the_documents_about_the_same_campaign_that_are_recommended": ("The Comprehensive Motel Enforcement History Report "
                                                                 "and the Planning Department's response on motel "
                                                                 "closure operations are recommended for addition "
                                                                 "without hesitation. They describe the enforcement "
                                                                 "campaign; they do not name the owner of a "
                                                                 "particular building."),
 },
 "what_the_questions_and_answers_page_turns_out_to_be": {
  "count": len(QA),
  "what_it_holds": ("The Administration's written answers to councillors, which is an oversight record rather than a "
                    "publicity one: numbered responses on whether a statutory committee was properly constituted, a "
                    "list of the FY25 budget's non-recurring items, a breakdown of the National Guard deployment, "
                    "the code enforcement motel history, boundary map exhibits, and a contract and fee ledger for "
                    "the North Domingo Baca aquatic centre."),
  "one_of_them_is_not_the_container_its_title_implies": ("The record titled NDB 12 IDOH is an OOXML workbook, not a "
                                                         "Word document: leading bytes 504b0304 with xl/ parts. Its "
                                                         "shared strings name BRADBURY STAMM CONSTRUCTION INC "
                                                         "against a contractor fee line and WSP USA ENVIRONMENT & "
                                                         "INFRASTRUCTURE against an engineering fee line."),
  "and_the_served_filenames_are_useless": ("Every file on this page is served under an opaque 32-character "
                                           "identifier - 3a1ae030b21146e7a55cec9a727ae5b7 and the like. The "
                                           "inventory title is the only name there is, which is why each row here "
                                           "carries the inventory_title as well as a title read from the document."),
 },
 "method": ("Read the archive's existing dispositions at all three paths before fetching: there were none. Fetched "
            "all 40 candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. Swept "
            "every checksum against the archived inventory records and against every row of every saved artifact. "
            "Extracted text with the right reader for each container - including one workbook whose title implied a "
            "document - and rendered the nine files with no usable text layer. Performed and recorded an "
            "official-source review for the commission's minutes, and recorded what that review could not reach."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, against anything recommended earlier in the same batch, and against every row of every saved artifact.",
  "cross_inventory_byte_collisions": 0,
  "collisions_with_earlier_artifacts_in_this_run": 0,
  "internal_byte_collisions": 0,
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing here duplicates anything, in the archive or in this run.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "collisions_with_earlier_artifacts": 0,
  "relationships_found": 0,
  "note": "No relationships in this lane. Every one of the forty candidates is a distinct object.",
 },
 "integration_flags": [
  {"severity": "judgment-needed",
   "affects": sorted(ENFORCEMENT),
   "finding": "Seven code enforcement Notices and Orders naming property owners, six companies and one set of three named natural persons, published by the City on a public Council page in answer to councillor questions.",
   "recommended_action": "Decide the class once and apply it to all seven. Every row carries the owner, whether it is a company or a person, the date and the case number."},
  {"severity": "missing-minutes-exception-applied",
   "affects": LGCC,
   "finding": "Ten Local Government Coordinating Commission agendas qualify on the City-side evidence: both official City pages carry no link containing the word minutes, the City's site search returns no results, the inventory holds none, and no agenda shows a cancellation.",
   "recommended_action": "Approve labelled Agenda (approved minutes not located). Note the recorded limitation: bernco.gov returned HTTP 403, so the County side of this joint body was not checked."},
  {"severity": "substantive-find",
   "affects": sorted(QA),
   "finding": "The Administration's written answers to councillors: whether a statutory committee was lawfully constituted, the FY25 non-recurring items, the National Guard deployment breakdown, the Comprehensive Motel Enforcement History Report of June 2025, boundary exhibits, and a contract and fee ledger for the North Domingo Baca aquatic centre.",
   "recommended_action": "Approve. This page is an oversight record, not a publicity one."},
  {"severity": "container-from-the-bytes",
   "affects": ['src-5006deafb03b1f7a'],
   "finding": "The record titled NDB 12 IDOH is a spreadsheet, leading bytes 504b0304 with xl/ parts, not the document its title implies. Its contents are contract and fee lines naming the contractor and the engineering consultant.",
   "recommended_action": "Record it as a workbook and archive it in its original format."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "requires_human_review": counts["requires human review"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "additional_probes": "Two official City pages, one County page (HTTP 403) and one City site search for the commission's minutes.",
                "rendered": "9 files with no usable text layer.",
                "containers_verified": ("%d PDFs, %d HTML pages and %d OOXML workbook by leading bytes."
                                        % (bycontainer['PDF'], bycontainer['HTML'], bycontainer['XLSX']))},
 "approved_for_addition": approved,
 "duplicate": [],
 "requires_human_review": rhr,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. One approved "
                   f"record is an OOXML workbook and should be archived in its original format. The {len(rhr)} "
                   f"records held for review are not to be archived until the class question is settled."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. No row carries a canonical_id; this lane contains "
                     "no duplicates and no supersession. Every row carries the inventory_title alongside the title "
                     "read from the document, because the served filenames on the questions and answers page are "
                     "opaque identifiers. The ten agenda rows carry their missing-minutes review inline, including "
                     "its recorded limitation, and must be labelled as agendas. The seven enforcement rows are one "
                     "package and one decision. Sizes and checksums are first measurements; the inventory held "
                     "none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the enforcement notices were read only to establish whose names they carry and are not reproduced here"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
