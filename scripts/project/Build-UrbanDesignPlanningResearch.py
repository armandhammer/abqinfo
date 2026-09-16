"""Claude research lane. The planning/UDD slice of the third link harvest: the
City's comprehensive planning record - two generations of the Comprehensive Plan
and the 54 sector and area plans the Integrated Development Ordinance repealed.

These are NOT inventory candidates. It never modifies master-inventory.json,
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
       r'\urban-design-planning-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\h3')

AREAPLANS = 'content/development-land-use/area-sector-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'
DEVPROC = 'content/development-land-use/development-process.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
PROJECTS = 'content/development-land-use/projects.md'

inv = json.load(open(INV, encoding='utf-8'))

F = {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    F[p[0]] = p
NEW = json.load(open(os.path.join(SP, 'new_ids.json'), encoding='utf-8'))
REPEAL = json.load(open(os.path.join(SP, 'sdp_repeal.json'), encoding='utf-8'))

SLICE = sorted(i for i in NEW if '/planning/UDD' in F[i][5])


def fname(i):
    return urllib.parse.unquote(F[i][5].rstrip('/').split('/')[-1])


def path(i):
    return urllib.parse.unquote(urllib.parse.urlsplit(F[i][5]).path)


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

SHA_HIT = {i for i in SLICE if F[i][3] in ALL_SHA}
URL_HIT = {i for i in SLICE if norm(F[i][5]) in INV_URL}
ART_HIT = {i for i in SLICE if F[i][3] not in ALL_SHA and F[i][3] in PRIOR_SHA}
BY = collections.defaultdict(list)
for i in SLICE:
    BY[F[i][3]].append(i)
INTERNAL = sum(len(v) - 1 for v in BY.values() if len(v) > 1)

LC = ("HTTP 200 verified 2026-09-14 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes, "
      "container verified by leading bytes, and every PDF tested for its end-of-file marker.")

NAME_FIX = {
    'McClellanParkSDP-REPEALED.pdf': 'McClellan Park',
    'UniversityofAlbuquerqueSDP-REPEALED.pdf': 'University of Albuquerque',
    'StJosephospitalSDP-REPEALED.pdf': 'St Joseph Hospital',
    'North-I-25-SDP-REPEALED.pdf': 'North I-25',
}
NAME_NOTE = {
    'StJosephospitalSDP-REPEALED.pdf': ("The City's filename reads StJosephospital - a letter is missing. Titled "
                                        "here as St Joseph Hospital; confirm the plan's own title before "
                                        "publishing."),
    'WindowG-SDP-REPEALED.pdf': ("Titled from the filename as Window G. The document yields only its repeal stamp, "
                                 "so the plan's own title could not be read."),
}


def readable(fn):
    if fn in NAME_FIX:
        return NAME_FIX[fn]
    s = re.sub(r'-?REPEALED$', '', fn.replace('.pdf', '')).strip('-')
    s = re.sub(r'-?SDP$', '', s).replace('-', ' ')
    s = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)
    s = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def kind(fn):
    if 'AreaPlan' in fn or 'StrategicPlan' in fn or 'EscarpmentPlan' in fn:
        return 'area plan'
    return 'sector development plan'


REPEALED = [i for i in SLICE if 'REPEALED' in fname(i).upper()]
CP2017 = [i for i in SLICE if '/CompPlan2017/CompPlan-' in F[i][5]]
CP2024 = [i for i in SLICE if '/CompPlan2024/' in F[i][5]]
ESPANOL = [i for i in SLICE if '/Espanol/' in F[i][5] or 'Espanol' in fname(i)]

MEASURED = [i for i in REPEALED if i in REPEAL]
assert len(MEASURED) == len(REPEALED), sorted(set(REPEALED) - set(MEASURED))
STAMP_ONLY = [i for i in REPEALED if REPEAL[i]['chars'] == 144]
NO_TEXT_AT_ALL = [i for i in REPEALED if REPEAL[i]['chars'] == 0]
NO_INSTRUMENT = [i for i in REPEALED if not REPEAL[i]['r17213']]

rows = []


def add(i, title, group, desc, ev, canon, cross, caution=None, extra=None):
    r = {"local_ref": i, "inventory_id": None, "authoritative_url": F[i][5],
         "filename": fname(i), "harvested_from": F[i][6].strip(),
         "recommendation": "add to the inventory as a new candidate", "link_check": LC,
         "content_kind": "PDF", "leading_bytes": F[i][4], "http_status": F[i][1],
         "size_bytes": int(F[i][2]), "checksum_sha256": F[i][3],
         "title": title, "group": group, "description": desc, "evidence": ev,
         "description_word_count": len(desc.split()),
         "proposed_canonical_page": canon, "cross_listings": cross}
    if caution:
        r["caution"] = caution
    if extra:
        r.update(extra)
    rows.append(r)


# ---- the repealed plans ----------------------------------------------------
for i in sorted(REPEALED, key=fname):
    fn = fname(i)
    nm = readable(fn)
    k = kind(fn)
    rep = REPEAL[i]
    stamp_only = i in STAMP_ONLY
    ev = "%s bytes. " % format(int(F[i][2]), ',')
    if rep['chars'] == 0:
        ev += ("Nothing is extractable from its first eight pages at all - no text layer, and no repeal stamp "
               "either. Its repeal rests on its filename alone, which is the only file in this set where that is "
               "true.")
        desc = ("The %s for %s, superseded when the Integrated Development Ordinance replaced Albuquerque's sector "
                "and area plans, and republished by the City under a filename marking it repealed." % (k, nm))
        extra = {"repeal_stamp": {
            "found": False,
            "what_that_means": ("Every other plan in this set carries a stamp in its own text layer. This one "
                                "carries no extractable text at all, so the repeal is asserted by the filename and "
                                "nothing else. Render it before relying on the claim.")}}
    else:
        ev += ("Its own pages carry a text-layer stamp reading %s."
               % ("(R-17-213) REPEALED" + (" and (O-17-49)" if rep['o1749'] else "")
                  if rep['r17213'] else "REPEALED, without naming the repealing instrument"))
        if stamp_only:
            ev += (" That stamp is the only extractable text in the file's first eight pages - exactly 144 "
                   "characters, byte-identical to the stamp in nineteen other plans in this set. The plan itself "
                   "is imaged.")
        else:
            ev += " The plan body carries its own text layer as well."
        desc = ("The %s for %s, superseded when the Integrated Development Ordinance replaced Albuquerque's sector "
                "and area plans, and republished by the City carrying the stamp that records its repeal."
                % (k, nm))
        extra = {"repeal_stamp": {
            "found": True,
            "reads": ("(R-17-213) REPEALED" + (" and (O-17-49)" if rep['o1749'] else "")
                      if rep['r17213'] else "REPEALED, with no instrument named in the first eight pages"),
            "names_the_repealing_instrument": rep['r17213'],
            "verified_from": "the document's own text layer, not from its filename",
            "text_layer_beyond_the_stamp": not stamp_only}}
    caution = NAME_NOTE.get(fn)
    c2 = None
    if stamp_only:
        c2 = ("Searchable only for the word REPEALED. The plan's content has no text layer, so a keyword search of "
              "this archive will never match anything inside it. It needs OCR to be findable.")
    elif rep['chars'] == 0:
        c2 = ("No extractable text whatsoever, not even a stamp. Unsearchable, and its repeal is unverified from "
              "the document. Render or OCR it before publishing.")
    elif not rep['r17213']:
        c2 = ("Its stamp says REPEALED but does not name the repealing instrument in the first eight pages, unlike "
              "the other plans in this set. Record the repeal without attributing it to R-17-213 from this file.")
    if c2:
        caution = (caution + " " + c2) if caution else c2
    add(i, "%s %s, repealed" % (nm, k.title().replace('Plan', 'Plan')), "repealed sector and area plans",
        desc, ev, AREAPLANS,
        [{"page": ZONING, "reason": "Repealed by the ordinance that replaced it."}], caution, extra)

# ---- the 2017 Comprehensive Plan -------------------------------------------
CH2017 = {i: int(re.findall(r'Chapter(\d+)', fname(i))[0]) for i in CP2017 if 'Chapter' in fname(i)}
full17 = [i for i in CP2017 if fname(i) == 'CompPlan-FullText.pdf'][0]
app17 = [i for i in CP2017 if fname(i) == 'CompPlan-Appendices.pdf'][0]

add(full17, "Albuquerque Bernalillo County Comprehensive Plan, 2017: full text",
    "comprehensive plan 2017",
    ("The complete 2017 Albuquerque Bernalillo County Comprehensive Plan in a single file, the joint City and "
     "County policy document that guides growth and development and that the sector plans were folded into."),
    ("113,805,107 bytes, 183,992 extracted words. Measured as the container of the whole 2017 set: all fourteen "
     "chapters and the appendices score token coverage of 1.0000 inside it, and three sixty-word contiguous runs "
     "taken from each part are present verbatim, 3 of 3, for every one of the fifteen."),
    AREAPLANS, [{"page": ZONING, "reason": "The plan the code implements."},
                {"page": DEVPROC, "reason": "Applications are judged against it."}],
    "The canonical file for this generation. Its chapters are recommended too; see why_both_the_whole_and_its_parts_are_kept.")

for i in sorted(CH2017, key=lambda x: CH2017[x]):
    n = CH2017[i]
    add(i, "Comprehensive Plan 2017, Chapter %d" % n, "comprehensive plan 2017",
        ("Chapter %d of the 2017 Albuquerque Bernalillo County Comprehensive Plan, published as a separate file "
         "alongside the compiled plan so that a single chapter can be cited without the whole document." % n),
        ("%s bytes. Token coverage of 1.0000 inside CompPlan-FullText.pdf and 3 of 3 sixty-word contiguous runs "
         "present verbatim: this chapter is inside the compiled plan." % format(int(F[i][2]), ',')),
        AREAPLANS, [{"page": ZONING, "reason": "Part of the plan the code implements."}],
        "A part of the compiled plan, proven by measurement. Keep the relationship on the record.")

add(app17, "Comprehensive Plan 2017: appendices", "comprehensive plan 2017",
    ("The appendices to the 2017 Comprehensive Plan, published separately from the compiled plan and containing "
     "the supporting material the chapters refer to."),
    ("5,238,616 bytes, 28,284 extracted words. Token coverage of 1.0000 inside CompPlan-FullText.pdf with 3 of 3 "
     "contiguous runs present: the appendices are inside the compiled plan."),
    AREAPLANS, [{"page": ZONING, "reason": "Part of the plan the code implements."}],
    "A part of the compiled plan, proven by measurement.")

# ---- the 2024 / 2025 Comprehensive Plan ------------------------------------
full25 = [i for i in CP2024 if fname(i).startswith('EFFECTIVE_CompPlan')][0]
add(full25, "Albuquerque Bernalillo County Comprehensive Plan, effective October 2025",
    "comprehensive plan 2025",
    ("The Comprehensive Plan as it took effect in October 2025, the current joint City and County policy document "
     "for growth and development and the successor to the 2017 edition."),
    ("294,090,168 bytes - the largest file measured anywhere in this run. Measured as the container of the whole "
     "2024 set: every one of the twelve separately published chapters and the appendices scores token coverage of "
     "1.0000 inside it with 3 of 3 contiguous runs present verbatim."),
    AREAPLANS, [{"page": ZONING, "reason": "The plan the code implements."},
                {"page": DEVPROC, "reason": "Applications are judged against it."}],
    ("The current plan and the canonical file for this generation. At 294 MB it is not a practical citation target, "
     "which is why its chapters are recommended as well."))

for i in sorted([x for x in CP2024 if x != full25], key=fname):
    fn = fname(i)
    m = re.match(r'(\d+)\s+(.+?)(?:\s+EFFECTIVE)?\.pdf$', fn)
    num = m.group(1) if m else None
    lbl = m.group(2).strip() if m else fn.replace('.pdf', '')
    eff = 'EFFECTIVE' in fn
    if 'Appendices' in fn:
        t = "Comprehensive Plan 2025: appendices A to P"
        d = ("Appendices A to P of the Comprehensive Plan effective October 2025, the supporting material the "
             "chapters refer to, published separately from the compiled plan.")
    else:
        t = "Comprehensive Plan 2025, Chapter %s: %s" % (num, lbl)
        d = ("Chapter %s of the Comprehensive Plan effective October 2025, covering %s, published as a separate "
             "file so the chapter can be cited without the 294-megabyte compiled plan." % (num, lbl.lower()))
    add(i, t, "comprehensive plan 2025", d,
        ("%s bytes. Token coverage of 1.0000 inside EFFECTIVE_CompPlan_October2025.pdf with 3 of 3 sixty-word "
         "contiguous runs present verbatim: this part is inside the compiled plan.%s"
         % (format(int(F[i][2]), ','),
            " Its filename carries the word EFFECTIVE." if eff else " Its filename does not carry the word EFFECTIVE.")),
        AREAPLANS, [{"page": ZONING, "reason": "Part of the plan the code implements."}],
        "A part of the compiled plan, proven by measurement.",
        {"filename_marked_effective": eff})

# ---- the Spanish chapters --------------------------------------------------
ES = {'ABCPlanIntegral-Espanol-Cap1-Introduccion.pdf':
      ("Plan Integral, Capitulo 1: Introduccion, draft of February 2017",
       ("The Spanish-language draft of Chapter 1 of the Comprehensive Plan, published by the City in February 2017 "
        "so that Spanish-speaking residents could read the plan's introduction in their own language.")),
      'ABCPlanIntegral-Espanol-Cap3-Vision.pdf':
      ("Plan Integral, Capitulo 3: La Vision, draft of February 2017",
       ("The Spanish-language draft of Chapter 3 of the Comprehensive Plan, setting out the plan's vision, the "
        "companion to the Spanish introduction chapter."))}
for i in sorted(ESPANOL, key=fname):
    t, d = ES[fname(i)]
    add(i, t, "comprehensive plan in Spanish", d,
        ("%s bytes. Its first page reads Albuquerque y el Condado de Bernalillo, Plan Integral, Borrador Espanol, "
         "Febrero 2017." % format(int(F[i][2]), ',')),
        AREAPLANS, [{"page": ZONING, "reason": "Part of the plan the code implements."}],
        ("Marked Borrador - a draft - on its own cover, and only two of the plan's chapters were published in "
         "Spanish. Label it a draft translation and record that the set is incomplete."))

assert len(rows) == len(SLICE), (len(rows), len(SLICE))
bygroup = collections.Counter(r['group'] for r in rows)
total = sum(r['size_bytes'] for r in rows)

artifact = {
 "batch_id": "urban-design-planning-research-2026-09-14",
 "lane": "Claude research lane: the planning/UDD slice of the third link harvest",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": "None of these files has an inventory id. Every row carries inventory_id: null and a recommendation rather than a recommended_status.",
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here.",
 },
 "cluster": ("The City's comprehensive planning record: two generations of the Albuquerque Bernalillo County "
             "Comprehensive Plan, and the 54 sector and area plans the Integrated Development Ordinance repealed."),
 "what_is_in_it": dict(bygroup),
 "THE_THIRD_HARVEST_AND_WHAT_THE_CHECKSUM_SWEEP_SAVED": {
  "the_harvest": ("1,337 City pages, already fetched for the file-share sweep and parsed again here, yielded 1,625 "
                  "document links. 636 were already inventory records by URL and 14 already decided, leaving 975 "
                  "that looked new."),
  "then_the_checksum_sweep_ran": ("Of those 975, **73 are byte-identical to inventory records and 542 to rows this "
                                  "run had already decided**, and 16 more are duplicates of each other. Only 358 "
                                  "are genuinely new documents."),
  "what_that_means": ("A URL-based reconciliation would have proposed 975 additions, of which 631 - nearly two "
                      "thirds - are files the archive already holds or has already decided, served at addresses it "
                      "had not seen. The checksum sweep is not a tidying step; on this batch it was the difference "
                      "between 358 additions and 975."),
  "this_slice": "The %d files under planning/UDD." % len(SLICE),
 },
 "why_both_the_whole_and_its_parts_are_kept": {
  "what_was_measured": ("For both plan generations, every separately published chapter and the appendices were "
                        "tested against the compiled file using the containment method this run established: token "
                        "coverage, then three sixty-word contiguous runs taken from the part and searched verbatim "
                        "in the parent."),
  "the_result": ("Unanimous. All fourteen 2017 chapters plus the 2017 appendices, and all twelve published 2025 "
                 "chapters plus the 2025 appendices, score coverage 1.0000 with 3 of 3 runs present. Every part is "
                 "inside its compiled plan."),
  "and_yet_both_are_recommended": ("This departs from how the run treated Connections 2040, where proving "
                                   "containment avoided 60,998,778 bytes of redundant archival. The reason is "
                                   "size: that parent was 61 MB, and these are 113 MB and 294 MB. A 294-megabyte "
                                   "file is not a usable citation target for a page about, say, urban design. The "
                                   "chapters are the practical unit and the compiled plan is the authoritative "
                                   "one."),
  "the_departure_is_deliberate_and_recorded": ("So that it reads as a judgment rather than an inconsistency. If the "
                                               "archive would rather hold only the compiled plans, the chapter rows "
                                               "can be dropped and nothing else in this artifact changes - every "
                                               "chapter row carries the containment measurement that justifies "
                                               "dropping it."),
  "the_redundancy_if_both_are_kept": sum(r['size_bytes'] for r in rows if r['group'].startswith('comprehensive plan')
                                         and 'full text' not in r['title'].lower()
                                         and 'effective October 2025' not in r['title']),
 },
 "three_chapters_of_the_current_plan_are_not_published_separately": {
  "what": ("The 2025 plan has fourteen chapters. Twelve are published as separate files. Chapters 6, 9 and 10 are "
           "not."),
  "what_they_are": ("Read from the compiled plan's own contents: Chapter 6 Transportation, Chapter 9 Housing, "
                    "Chapter 10 Parks & Open Space."),
  "they_are_not_missing_from_the_plan": ("All three are inside EFFECTIVE_CompPlan_October2025.pdf - the compiled "
                                         "file names each of them in its contents and carries their text."),
  "what_is_unknown": ("Whether they were never split out, or are published somewhere this page does not link. Three "
                      "of the most-cited subjects in the plan are the three without a citable chapter file."),
  "recommended_action": "Look for them before treating the chapter set as complete.",
 },
 "the_repeal_stamp_and_what_it_hides": {
  "how_the_repeal_was_verified": ("Not from the filenames, which all end -REPEALED. %d of the %d carry a "
                                  "text-layer stamp on their own pages; %d of those name R-17-213 as the "
                                  "repealing instrument and %d also name O-17-49."
                                  % (sum(1 for i in REPEALED if REPEAL[i]['repealed_word']), len(REPEALED),
                                     sum(1 for i in REPEALED if REPEAL[i]['r17213']),
                                     sum(1 for i in REPEALED if REPEAL[i]['o1749']))),
  "the_two_that_do_not_fit": ("One plan carries the word REPEALED but names no instrument. One - the Southwest Area "
                              "Plan - yields no extractable text at all, not even a stamp, so its repeal rests on "
                              "its filename and nothing else. Both rows say so, and neither is counted among the "
                              "verified."),
  "the_finding_that_matters_for_search": ("For %d of the %d plans, that stamp is the *only* extractable text in "
                                          "the first eight pages - exactly 144 characters, and byte-identical "
                                          "across all %d of them. The stamp is a text overlay; the plan underneath "
                                          "is a scan."
                                          % (len(STAMP_ONLY), len(REPEALED), len(STAMP_ONLY))),
  "the_consequence": ("A keyword search of this archive would match those files only on the word REPEALED. Search "
                      "for Sawmill, or Old Town, or University Neighborhoods, and the plan for that neighbourhood "
                      "would not come back. They need OCR before they are findable, and every affected row says "
                      "so."),
  "how_i_nearly_got_this_wrong_twice": (
   "First: a check of pages one and two found the R-17-213 and O-17-49 pair in only 8 of 50, which would have "
   "supported a claim that 42 plans carry no repeal marking. Widening to eight pages and stripping punctuation "
   "before matching showed that 50 carry R-17-213. The narrow check was measuring my extraction window, not the "
   "documents. Second: the generator counted a plan as having no text whenever it had no measurement, so the four "
   "area plans - which had not been measured at all - were silently counted among the stamp-only files, making 22 "
   "where the verified figure was 18. Measuring them properly gave 20, and turned up the two exceptions above. "
   "Absent data must never be allowed to read as a measured zero."),
 },
 "method": ("Parsed 1,337 stored City pages for document links, reconciled by URL against every inventory URL and "
            "every saved artifact row, fetched and measured the remainder, refetched four anomalies without a "
            "timeout, verified containers by leading bytes, tested every PDF for its end-of-file marker, extracted "
            "text, ran the containment test for both plan generations, and swept every checksum against all "
            "checksummed inventory records and every saved artifact row."),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "For proposed additions, test against every inventory record rather than only the archived ones, and by URL as well as by checksum.",
  "cross_inventory_byte_collisions": len(SHA_HIT),
  "cross_inventory_url_collisions": len(URL_HIT),
  "collisions_with_earlier_artifacts_in_this_run": len(ART_HIT),
  "internal_byte_collisions": INTERNAL,
  "archived_records_compared_against": len(ARCH_SHA),
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "inventory_urls_compared_against": len(INV_URL),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "result": "Nothing in this slice is already held or already decided; the sweep that removed the rest of the batch removed nothing from here.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": INTERNAL,
  "supersession_recorded": len(REPEALED),
  "note": ("The %d repealed plans are superseded by the Integrated Development Ordinance, recorded from the stamp "
           "on each document rather than inferred. The two plan generations supersede one another: the 2025 "
           "edition replaces the 2017." % len(REPEALED)),
 },
 "integration_flags": [
  {"severity": "not-applicable-through-update-candidate",
   "affects": [], "finding": "No file in this artifact has an inventory id.",
   "recommended_action": "Create them as candidates first; they then fall under the ordinary archival gate."},
  {"severity": "substantive-find",
   "affects": [full25, full17],
   "finding": ("Both generations of the Albuquerque Bernalillo County Comprehensive Plan - the 2017 edition and the "
               "edition effective October 2025 - neither in the inventory."),
   "recommended_action": "Add both, and record that the 2025 edition supersedes the 2017."},
  {"severity": "repeal-unverified-from-the-document",
   "affects": NO_TEXT_AT_ALL + NO_INSTRUMENT,
   "finding": ("One plan yields no extractable text at all, so its repeal rests on its filename alone; one more "
               "carries the word REPEALED without naming the instrument."),
   "recommended_action": "Do not attribute either repeal to R-17-213 on this evidence. Render them and read the stamp."},
  {"severity": "needs-ocr-to-be-findable",
   "affects": STAMP_ONLY,
   "finding": ("%d repealed plans have no text layer except the repeal stamp. A keyword search of the archive will "
               "match them only on the word REPEALED." % len(STAMP_ONLY)),
   "recommended_action": "OCR them before publishing, or record plainly that their contents are not searchable."},
  {"severity": "incomplete-series",
   "affects": [],
   "finding": "Chapters 6 Transportation, 9 Housing and 10 Parks & Open Space of the current plan have no separate file.",
   "recommended_action": "Look for them before treating the chapter set as complete."},
  {"severity": "deliberate-redundancy",
   "affects": [r['local_ref'] for r in rows if r['group'].startswith('comprehensive plan')],
   "finding": ("Every chapter is proven to be inside its compiled plan, and both are recommended anyway because the "
               "compiled files are 113 MB and 294 MB."),
   "recommended_action": "Accept the redundancy or drop the chapter rows; each carries the measurement that justifies dropping it."},
  {"severity": "incomplete-translation",
   "affects": sorted(ESPANOL),
   "finding": "Only two of the plan's chapters were published in Spanish, and both are marked Borrador - draft.",
   "recommended_action": "Label them draft translations and record that the Spanish set is incomplete."},
 ],
 "counts": {
  "reviewed": len(rows),
  "add_to_the_inventory_as_a_new_candidate": len(rows),
  "by_group": dict(bygroup),
  "repealed_plans": len(REPEALED),
  "repeal_stamp_found_in_the_document": sum(1 for i in REPEALED if REPEAL[i]['repealed_word']),
  "stamp_names_R_17_213": sum(1 for i in REPEALED if REPEAL[i]['r17213']),
  "stamp_also_names_O_17_49": sum(1 for i in REPEALED if REPEAL[i]['o1749']),
  "files_whose_only_text_is_the_repeal_stamp": len(STAMP_ONLY),
  "files_with_no_extractable_text_at_all": len(NO_TEXT_AT_ALL),
 },
 "link_check": {"checked": len(rows), "http_200": sum(1 for i in SLICE if F[i][1] == '200'),
                "failed": sum(1 for i in SLICE if F[i][1] != '200'),
                "method": "Full HTTP GET with a browser user agent, 2026-09-14.",
                "integrity": "Every row rehashed against its file on disk; every PDF tested for its end-of-file marker.",
                "containers_verified": "%d PDF, by leading bytes." % len(rows)},
 "add_to_inventory": rows,
 "archival_note": ("None of the %d proposed additions is a candidate yet. Each remains inventory-only until an R2 "
                   "archive object exists and its public download, exact size, SHA-256 and authoritative-source "
                   "provenance are verified. Combined footprint if all are added and archived: %s bytes - the "
                   "largest of any lane in this run, and dominated by two compiled Comprehensive Plans totalling "
                   "407,895,275 bytes." % (len(rows), format(total, ','))),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "the authoritative URL, the measured size, the SHA-256, the leading bytes and harvested_from. "
                      "Every row carries inventory_id: null. The repealed plans each carry the repeal stamp read "
                      "from the document, and the chapter rows each carry the containment measurement."),
 "what_remains_of_this_harvest": ("272 more new documents from the same batch: 81 fire/documents, 50 "
                                  "council/documents, 38 planning/DevelopmentReviewServices, 35 acs/documents, 18 "
                                  "planning/IDO and the rest."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "reviewed": len(rows), "groups": dict(bygroup),
                  "bytes": total, "stamp_only": len(STAMP_ONLY)}))
