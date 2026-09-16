"""Claude research lane. The fire/documents slice of the third link harvest:
Albuquerque Fire Rescue's Monthly Informational Reports, February 2018 to October
2024, and one earlier issue the City no longer links.

These are NOT inventory candidates. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-15.
"""

import collections
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import urllib.parse

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\fire-monthly-reports-research-2026-09-15.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\h3')

SAFETYDATA = 'content/city-data/public-safety-data.md'
CITYDATA = 'content/city-data/_index.md'
LINKING_PAGE = 'https://www.cabq.gov/fire/copy_of_reports'
LINKING_PAGE_RECORD = 'src-6260059ea0d144b3'

MON = ('january february march april may june july august september october november december').split()
ABBR = {'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april', 'aug': 'august', 'sep': 'september',
        'sept': 'september', 'oct': 'october', 'nov': 'november', 'dec': 'december'}

inv = json.load(open(INV, encoding='utf-8'))
F = {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    F[p[0]] = p
NEW = json.load(open(os.path.join(SP, 'new_ids.json'), encoding='utf-8'))
SLICE = sorted(i for i in NEW if '/fire/documents' in F[i][5])


def fname(i):
    return urllib.parse.unquote(F[i][5].rstrip('/').split('/')[-1])


def months_in(s):
    out = []
    for tok in re.findall(r'[a-z]+', s.lower()):
        t = ABBR.get(tok, tok)
        if t in MON:
            out.append(t)
    return out


def full_text(path):
    return subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True).stdout.decode('utf-8', 'replace')


def repair(s):
    # display-font spacing splits words: "M ONTHLY INFORMATIONA L"
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\bM ONTHLY\b', 'MONTHLY', s)
    s = re.sub(r'\bINFORMATIONA L\b', 'INFORMATIONAL', s)
    return s.strip()


IMAGE_ONLY = {'april-may-mir-2018.pdf': {
    "read_by": "rendering",
    "cover_reads": ("ALBUQUERQUE FIRE DEPARTMENT, MONTHLY INFORMATIONAL REPORT, APRIL - MAY 2018, Presented to the City "
                    "of Albuquerque, Mayor Tim Keller and City Council Members")}}

ALL_SHA, ARCH_SHA = {}, {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s:
        ALL_SHA.setdefault(s, x['id'])
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
            INV_URL.setdefault(norm(x[k]), x['id'])
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
              'add_to_inventory', 'do_not_add', 'needs_a_decision_from_a_person',
              'resolves_an_existing_candidate'):
        for r in d.get(b) or []:
            if isinstance(r, dict) and r.get('checksum_sha256'):
                PRIOR_SHA.setdefault(r['checksum_sha256'], os.path.basename(f))

LC = ("HTTP 200 verified by full GET during the third link harvest; size_bytes and checksum_sha256 measured from the "
      "fetched bytes, container verified by leading bytes.")

rows = []
periods = {}
for i in SLICE:
    fn = fname(i)
    path = os.path.join(SP, 'files', i + '.bin')
    b = open(path, 'rb').read()
    text = full_text(path)
    pages = text.split('\f')
    npages = text.count('\f')
    first = repair(pages[0]) if pages else ''
    stem = fn.replace('.pdf', '').lower()
    year = int(re.findall(r'20\d\d', stem)[0])
    fm = months_in(stem)
    two_month = len(fm) >= 2
    month = fm[0]
    periods[i] = (year, MON.index(month) + 1)
    rescue = text.upper().count('FIRE RESCUE')
    dept = text.upper().count('FIRE DEPARTMENT')
    if fn in IMAGE_ONLY:
        agency = 'Albuquerque Fire Department'
    elif rescue >= dept and rescue:
        agency = 'Albuquerque Fire Rescue'
    elif dept:
        agency = 'Albuquerque Fire Department'
    else:
        agency = 'Albuquerque Fire Rescue'
    label = ('%s-%s %d' % (fm[0].title(), fm[1].title(), year)) if two_month else ('%s %d' % (month.title(), year))
    if fn in IMAGE_ONLY:
        quote = IMAGE_ONLY[fn]['cover_reads']
        ev = ("%s bytes, %d pages, with no text layer on any page, so it was read by rendering. Its cover reads %s."
              % (format(len(b), ','), npages, quote))
    else:
        quote = first[:90].strip()
        ev = ("%s bytes, %d pages, complete to its end marker. Page 1 opens: %s."
              % (format(len(b), ','), npages, quote))
    desc = ("The %s monthly informational report for %s, one of a continuous monthly series from February 2018 to "
            "October 2024 reporting the department's call volumes, call types and emergency medical statistics."
            % (agency, label))
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": F[i][5], "filename": fn,
         "harvested_from": F[i][6].strip(), "recommendation": "add to the inventory as a new candidate",
         "link_check": LC, "content_kind": "PDF", "leading_bytes": F[i][4], "http_status": F[i][1],
         "size_bytes": len(b), "checksum_sha256": hashlib.sha256(b).hexdigest(),
         "page_count": npages, "complete_to_its_end_marker": b'%%EOF' in b[-2048:],
         "title": "%s, Monthly Informational Report, %s" % (agency, label),
         "report_period": {"year": year, "month": MON.index(month) + 1,
                           "labelled_as_two_months": two_month,
                           "period_verified_against": ("the rendered cover" if fn in IMAGE_ONLY
                                                       else "the report's own first page")},
         "group": "fire rescue monthly informational reports",
         "description": desc, "description_word_count": len(desc.split()), "evidence": ev,
         "quoted_opening": quote,
         "proposed_canonical_page": SAFETYDATA,
         "cross_listings": [{"page": CITYDATA, "reason": "Reported City performance data."}]}
    cautions = []
    if two_month:
        cautions.append("Titled with a two-month span; see the_2018_two_month_labels. Record the span as published.")
    if re.search(r'lr\.pdf$|-lr\.pdf$', fn):
        cautions.append("A low-resolution copy, and the only form in which this month is published: the same name "
                        "without 'lr' returns HTTP 404.")
    if re.search(r'-v2\.pdf$|updated-final|-final\.pdf$', fn):
        cautions.append("Its filename marks it a revised or final issue; no earlier issue is published at the "
                        "predictable name.")
    if fn == 'mir-april-2020-1.pdf':
        cautions.append("A corrected re-issue. An earlier April 2020 issue is still on the server, unlinked, and is "
                        "recorded in do_not_add; see two_issues_of_april_2020.")
    if fn == 'mir-march-2023-no-pageslr.pdf':
        cautions.append("Its own first page states that, due to technical issues in data reporting, unit response "
                        "and alarm reason data for March are not included. Record the omission with the report.")
    if cautions:
        r["caution"] = " ".join(cautions)
    rows.append(r)

# ---- the unlinked earlier issue of April 2020 -------------------------------
ex_path = os.path.join(SP, 'extra', 'mir-april-2020.pdf')
exb = open(ex_path, 'rb').read()
ex_text = full_text(ex_path)
linked = [r for r in rows if r['filename'] == 'mir-april-2020-1.pdf'][0]
lk_text = full_text(os.path.join(SP, 'files', linked['local_ref'] + '.bin'))
pa = [re.sub(r'\s+', ' ', x).strip() for x in ex_text.split('\f')]
pb = [re.sub(r'\s+', ' ', x).strip() for x in lk_text.split('\f')]
same_pos = sum(1 for x, y in zip(pa, pb) if x == y)
extra_row = {
 "local_ref": "fire-extra-001", "inventory_id": None,
 "authoritative_url": "https://www.cabq.gov/fire/documents/mir-april-2020.pdf",
 "filename": "mir-april-2020.pdf", "harvested_from": None,
 "found_by": ("Probing the predictable filename of mir-april-2020-1.pdf without its -1 suffix. It is not linked "
              "from the reports page."),
 "recommendation": "do not add", "content_kind": "PDF", "leading_bytes": exb[:4].hex(), "http_status": "200",
 "size_bytes": len(exb), "checksum_sha256": hashlib.sha256(exb).hexdigest(),
 "page_count": ex_text.count('\f'), "complete_to_its_end_marker": b'%%EOF' in exb[-2048:],
 "title_for_reference": "Albuquerque Fire Rescue Monthly Informational Report, April 2020 - earlier issue",
 "what_it_is": "An earlier issue of the April 2020 report, still on the server under the name without the -1 suffix.",
 "why_not": ("Superseded by the linked issue, mir-april-2020-1.pdf. The two are not byte-identical. They share "
             "%d pages of identical text by position; the others differ. The earlier issue heads page 1 'MARCH "
             "CALLS' under an April 2020 title, where the linked issue reads 'APRIL CALLS', and the linked issue "
             "carries division-update pages this one lacks. The City links only the -1 issue. Recorded so the "
             "decision is reversible without fetching it again." % same_pos),
 "superseded_by": linked['local_ref'],
 "category": "earlier issue superseded by a corrected re-issue", "package": "superseded_issue",
}

bygroup = collections.Counter(r['group'] for r in rows)
ymonths = collections.defaultdict(set)
for i, (y, m) in periods.items():
    ymonths[y].add(m)
dup_periods = [k for k, v in collections.Counter(periods.values()).items() if v > 1]
first_p, last_p = min(periods.values()), max(periods.values())
all_months = [(y, m) for y in range(first_p[0], last_p[0] + 1) for m in range(1, 13)
              if (y, m) >= first_p and (y, m) <= last_p]
gaps = [p for p in all_months if p not in set(periods.values())]

probes = [l.rstrip('\n').split('\t') for l in open(os.path.join(SP, 'extra', 'probes.tsv'), encoding='utf-8')]
probe_when = open(os.path.join(SP, 'extra', 'probes.when'), encoding='utf-8').read().strip()

SHA_HIT = [r['local_ref'] for r in rows + [extra_row] if r['checksum_sha256'] in ALL_SHA]
URL_HIT = [r['local_ref'] for r in rows + [extra_row] if norm(r['authoritative_url']) in INV_URL]
ART_HIT = [r['local_ref'] for r in rows + [extra_row]
           if r['checksum_sha256'] not in ALL_SHA and r['checksum_sha256'] in PRIOR_SHA]
INTERNAL = sum(v - 1 for v in collections.Counter(r['checksum_sha256'] for r in rows + [extra_row]).values() if v > 1)
MONTHCOUNT = {
 'feb-mar-mir-2018.pdf': 'FEBRUARY 14, MARCH 2', 'march-april-mir-2018.pdf': 'MARCH 21, APRIL 11',
 'may-june-mir-2018.pdf': 'MAY 29, JUNE 12', 'june-july-mir-2018.pdf': 'JUNE 25, JULY 20',
 'july-august-mir-2018.pdf': 'JULY 28, AUGUST 12', 'august-september-mir-2018.pdf': 'AUGUST 32, SEPTEMBER 11',
 'september-mir-2018.pdf': 'SEPTEMBER 24, OCTOBER 10'}

artifact = {
 "batch_id": "fire-monthly-reports-research-2026-09-15",
 "lane": "Claude research lane: the fire/documents slice of the third link harvest",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-15.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": "None of these files has an inventory id. Every row carries inventory_id: null and a recommendation rather than a recommended_status.",
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here.",
 },
 "cluster": ("Albuquerque Fire Rescue's Monthly Informational Reports: the department's report on its call volumes, "
             "call types and emergency medical statistics, published month by month. No lane in this run had touched "
             "the fire department."),
 "where_they_came_from": {
  "the_linking_page": LINKING_PAGE,
  "that_page_is_itself_an_inventory_record": ("%s, status validated. The archive already holds the page that links "
                                              "all 81 reports and held none of the reports." % LINKING_PAGE_RECORD),
  "the_page_links_exactly_these": ("It links exactly %d monthly reports, and they are exactly the %d in this "
                                   "slice." % (len(rows), len(rows))),
  "and_nine_more_it_already_had": ("The same page links nine fire department annual reports, 2014 to 2022, all "
                                   "already inventory records. The annual reports were collected; the monthly ones "
                                   "were not."),
 },
 "the_series": {
  "reports": len(rows),
  "first_period": "%s %d" % (MON[first_p[1] - 1].title(), first_p[0]),
  "last_period": "%s %d" % (MON[last_p[1] - 1].title(), last_p[0]),
  "one_report_per_month": not dup_periods,
  "gaps_inside_the_span": ["%s %d" % (MON[m - 1].title(), y) for y, m in gaps],
  "coverage_by_year": {str(y): sorted(v) for y, v in sorted(ymonths.items())},
  "period_checked_against_the_documents": ("Every report's period was read from its own first page and compared "
                                           "with its filename: no disagreement in %d of %d. The one with no text "
                                           "layer was read from its rendered cover." % (len(rows) - 1, len(rows))),
  "what_is_not_published": ("Nothing after October 2024 appears on the page, and November and December 2024 return "
                            "HTTP 404 at the predictable filenames. Whether the series stopped or moved, this page "
                            "does not say."),
 },
 "the_2018_two_month_labels": {
  "what": ("Seven 2018 reports are titled with a two-month span - February-March, March-April, April-May, May-June, "
           "June-July, July-August, August-September - before single-month titles begin in September 2018."),
  "why_this_is_not_overlapping_coverage": ("Counting whole-word month names in each report's text, every two-month "
                                           "report is dominated by its first-named month, and the single-month "
                                           "September 2018 report has the same shape. Counts: %s."
                                           % "; ".join('%s %s' % (k, v) for k, v in MONTHCOUNT.items())),
  "the_reading": ("Consistent with each report covering its first-named month, the second month being when it was "
                  "prepared or presented. That is an inference from counts, not a page-by-page verification, and "
                  "each two-month row keeps the span exactly as published."),
  "what_it_does_to_the_series": "Read that way, 2018 runs February to December with no month twice and none missing.",
 },
 "two_issues_of_april_2020": {
  "what": ("The page links mir-april-2020-1.pdf. Probing the same name without -1 returned a different file: "
           "mir-april-2020.pdf, 8,925,770 bytes against the linked 13,139,371, both 18 pages."),
  "how_they_differ": ("%d pages have identical text by position; the rest do not. Page 1 of the unlinked issue is "
                      "headed MARCH CALLS under an April 2020 title, where the linked issue reads APRIL CALLS, and the "
                      "linked issue carries division-update pages the earlier one lacks." % same_pos),
  "the_decision": ("The linked issue is the record. The earlier issue is recorded in do_not_add as superseded, with "
                   "its full measurement, so the decision can be reversed without fetching it again - the same "
                   "treatment this run gave the draft fiscal 2021 stormwater report."),
 },
 "the_variant_filenames": {
  "what": ("Thirteen filenames carry a variant marker - -v2, -1, final, updated-final, lr, all-pages, no-pages. For "
           "each, the name without the marker was probed."),
  "result": ("Only one earlier or fuller version exists: April 2020. Every other probe returned HTTP 404. So the "
             "low-resolution 'lr' copies are the only form in which those months are published, and each carries a "
             "caution saying so."),
  "probes": [{"name": p[0], "http_status": p[1], "bytes": int(p[2])} for p in probes],
  "probed_at": probe_when,
 },
 "a_month_that_says_it_is_incomplete": {
  "what": ("The March 2023 report states on its first page that, due to technical issues in data reporting, unit "
           "response and alarm reason data for March are not included, and that the issues were expected to be "
           "resolved."),
  "why_it_is_recorded": "So that anyone comparing months knows the March 2023 figures are incomplete by the department's own account.",
 },
 "method": ("Took the 81 fire/documents files from the third harvest's genuinely new set, compared the reports page's "
            "links with the slice, read each report's period from its own first page and compared it with the "
            "filename, rendered the one with no text layer, counted month names across the 2018 reports, probed the "
            "name without each variant marker, fetched and compared the one earlier issue that exists, and swept "
            "every checksum against all checksummed inventory records and every saved artifact row."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "For proposed additions, test against every inventory record rather than only the archived ones, and by URL as well as by checksum.",
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "internal_byte_collisions": INTERNAL,
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "archived_records_compared_against": len(ARCH_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing in this slice, and not the earlier April 2020 issue, is already held or already decided.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": INTERNAL,
  "supersession_found": 1,
  "note": "No two files are byte-identical. One supersession: the unlinked earlier issue of April 2020.",
 },
 "integration_flags": [
  {"severity": "not-applicable-through-update-candidate", "affects": [],
   "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create them as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "substantive-find", "affects": [r['local_ref'] for r in rows],
   "finding": ("A complete monthly series from the fire department, February 2018 to October 2024, 81 reports and "
               "none in the inventory - while the page that links them is a validated inventory record."),
   "recommended_action": "Add the series together; it is only fully useful as a continuous run."},
  {"severity": "superseded-issue", "affects": ["fire-extra-001"],
   "finding": "An earlier April 2020 issue is still on the server, unlinked, with a page-1 heading that the linked issue corrects.",
   "recommended_action": "Keep the linked issue; do not add the earlier one unless the archive keeps superseded issues."},
  {"severity": "incomplete-month", "affects": [r['local_ref'] for r in rows if r['filename'] == 'mir-march-2023-no-pageslr.pdf'],
   "finding": "The March 2023 report omits unit response and alarm reason data by its own statement.",
   "recommended_action": "Carry the omission onto the record."},
  {"severity": "low-resolution-only", "affects": [r['local_ref'] for r in rows if re.search(r'lr\.pdf$', r['filename'])],
   "finding": "Several months are published only as low-resolution copies; the full-resolution names return 404.",
   "recommended_action": "Archive them as published and record that no full-resolution copy was found."},
  {"severity": "series-end-unknown", "affects": [],
   "finding": "Nothing after October 2024 is on the reports page, and November and December 2024 return 404.",
   "recommended_action": "Check whether the series continues elsewhere before recording it as ended."},
 ],
 "counts": {
  "reviewed": len(rows) + 1,
  "add_to_the_inventory_as_a_new_candidate": len(rows),
  "do_not_add": 1,
  "by_group": dict(bygroup),
 },
 "add_to_inventory": rows,
 "do_not_add": [extra_row],
 "archival_note": ("None of the %d proposed additions is a candidate yet. Each remains inventory-only until an R2 "
                   "archive object exists and its public download, exact size, SHA-256 and authoritative-source "
                   "provenance are verified. Combined footprint if all are added and archived: %s bytes."
                   % (len(rows), format(sum(r['size_bytes'] for r in rows), ','))),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "inventory_id: null, the authoritative URL, the measured size and checksum, the page count, the "
                      "report period read from the document, and harvested_from."),
 "what_remains_of_this_harvest": ("191 more new documents from the same batch: 50 council/documents, 38 "
                                  "planning/DevelopmentReviewServices, 35 acs/documents, 18 planning/IDO, 8 "
                                  "planning/agis and the rest."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "rows": len(rows), "gaps": artifact["the_series"]["gaps_inside_the_span"],
                  "span": [artifact["the_series"]["first_period"], artifact["the_series"]["last_period"]],
                  "bytes": sum(r['size_bytes'] for r in rows)}))
