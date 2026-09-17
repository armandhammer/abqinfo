"""Claude research lane. A sweep of the City site for sfftp.cabq.gov links - the
file-transfer host whose share pages are invisible to any automated fetch - and
the three documents the repository owner retrieved from it.

These are NOT inventory candidates. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-14.
"""

import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import urllib.parse
import zipfile

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\file-share-sweep-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
STAGE = r'C:\Users\ben\Documents\ABQinfo\research\staging\document-review'
SCRATCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
           r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad')

DEVPROC = 'content/development-land-use/development-process.md'
AREAPLANS = 'content/development-land-use/area-sector-plans.md'
REDEV = 'content/development-land-use/redevelopment-plans.md'
ZONING = 'content/development-land-use/zoning-ido.md'
ROADWAY = 'content/transportation/roadway-projects/_index.md'
PARKS = 'content/public-works/parks-recreation.md'
CLIMATE = 'content/city-data/climate-environment.md'
CITYDATA = 'content/city-data/_index.md'
ABOUT = 'content/about/_index.md'

inv = json.load(open(INV, encoding='utf-8'))

# ---- the sweep itself ------------------------------------------------------
PAGE_SOURCES = [
    (os.path.join(SCRATCH, 'final'), 'fetch.log', 5, 'files', '.bin'),
    (os.path.join(SCRATCH, 'fyc'), 'fetch.log', 5, 'files', '.bin'),
    (os.path.join(SCRATCH, 'h2'), 'pages.log', 3, 'pages', '.html'),
    (os.path.join(SCRATCH, 'sf'), 'pages.log', 3, 'pages', '.html'),
]
ANCHOR = re.compile(r'<a\b[^>]*href=["\'](https?://sfftp\.cabq\.gov/[^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
RAW = re.compile(r'https?://sfftp\.cabq\.gov/[A-Za-z0-9/_.-]+')

pages_parsed = 0
links = {}
raw_seen = set()
for base, log, col, sub, ext in PAGE_SOURCES:
    p = os.path.join(base, log)
    if not os.path.exists(p):
        continue
    for line in open(p, encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        f = os.path.join(base, sub, c[0] + ext)
        if not os.path.exists(f):
            continue
        pages_parsed += 1
        s = open(f, encoding='utf-8', errors='replace').read()
        if 'sfftp' not in s:
            continue
        for m in RAW.finditer(s):
            raw_seen.add(m.group(0).split('#')[0])
        for m in ANCHOR.finditer(s):
            link = m.group(1).split('#')[0]
            if link.endswith('licenses.txt'):
                continue
            import html as _h
            txt = re.sub(r'\s+', ' ', _h.unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()[:110]
            d = links.setdefault(link, {"link_text": set(), "linked_from": set()})
            if txt and not txt.startswith('http'):
                d["link_text"].add(txt)
            d["linked_from"].add(c[col])

SHARE = {k: {"link_text": sorted(v["link_text"]), "linked_from": sorted(v["linked_from"])}
         for k, v in sorted(links.items())}

# ---- what the owner decided about each -------------------------------------
RETRIEVED_EARLIER = {
    'https://sfftp.cabq.gov/f/cf8779d97e34c92c': 'file-share-retrieval-research-2026-09-14.json',
    'https://sfftp.cabq.gov/f/7e1d61fbc4c19830': 'file-share-retrieval-research-2026-09-14.json',
}
STAGED = {
    'https://sfftp.cabq.gov/f/d233d7ecf3d2305b': 'Comp Plan Amendment - Main Street Corridor- East Central.pptx',
    'https://sfftp.cabq.gov/f/d425b5e959e99dd7': 'D8-ABCWUA  2025 Water Quality Report-05.21.2026.pdf',
    'https://sfftp.cabq.gov/f/4e6493bae484de6a': 'Laurelwood Median and Parkways NA Presentation_2025.04.02.pdf',
}


def measure(fn):
    p = os.path.join(STAGE, fn)
    b = open(p, 'rb').read()
    out = {"filename_as_downloaded": fn, "size_bytes": len(b),
           "checksum_sha256": hashlib.sha256(b).hexdigest(), "leading_bytes": b[:4].hex()}
    if b[:4] == b'%PDF':
        out["content_kind"] = "PDF"
        out["complete_to_its_end_marker"] = b'%%EOF' in b[-2048:]
        t = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True).stdout.decode('utf-8', 'replace')
        out["page_count"] = t.count('\f')
    else:
        z = zipfile.ZipFile(p)
        n = z.namelist()
        out["content_kind"] = ('PPTX' if any(x.startswith('ppt/') for x in n) else
                               'DOCX' if any(x.startswith('word/') for x in n) else
                               'XLSX' if any(x.startswith('xl/') for x in n) else 'OOXML')
        out["slide_count"] = len([x for x in n if re.match(r'ppt/slides/slide\d+\.xml$', x)]) or None
    return out


M = {k: measure(v) for k, v in STAGED.items()}

ALL_SHA, ARCH_SHA = {}, {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s:
        ALL_SHA.setdefault(s, x['id'])
        if x.get('status') in ('validated', 'published', 'archived', 'implemented'):
            ARCH_SHA.setdefault(s, x['id'])
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

PROVENANCE = ("Retrieved through a browser by the repository owner from the share URL on this row, and placed in "
              "research/staging/document-review. I measured the file as staged. I did not perform the retrieval and "
              "cannot independently attest that these bytes came from that URL.")

SPEC = {
 'https://sfftp.cabq.gov/f/d233d7ecf3d2305b': (
   "Comprehensive Plan amendment briefing: the Main Street Corridor and East Central, 6 May 2026",
   "comprehensive plan",
   ("A Council Services briefing on amending the Albuquerque Bernalillo County Comprehensive Plan to apply the Main "
    "Street Corridor designation to East Central, explaining what that designation means and how it differs from "
    "the separate New Mexico Main Street programme."),
   ("12,468,797 bytes, a PowerPoint deck of 20 slides, read from its ppt/slides parts. Slide 1 reads May 6th, 2026, "
    "Main Street Corridor, Albuquerque Bernalillo County Comprehensive Plan, City Council Services, Deepa Bansal - "
    "Council Planner. Later slides distinguish the Comp Plan's Main Street Corridor from the New Mexico Economic "
    "Development Department's Main Street programme, and quote the Plan's own description of such a corridor as "
    "lively, highly walkable and characterised by local-serving businesses."),
   AREAPLANS, [{"page": ZONING, "reason": "A corridor designation the code applies."},
               {"page": REDEV, "reason": "It governs redevelopment along East Central."}],
   ("A briefing deck, not the amendment itself - and kept for that reason, not in spite of it. It records how the "
    "initiative was presented to the public and by which City employee, on a named date. If the adopted amendment "
    "exists it is a separate document and is not in the inventory.")),
 'https://sfftp.cabq.gov/f/4e6493bae484de6a': (
   "Laurelwood Median and Parkway conceptual landscape and irrigation study, April 2025",
   "roadway landscape studies",
   ("The Department of Municipal Development's conceptual study for landscape and irrigation improvements to the "
    "Laurelwood median and parkway between Ladera Drive NW and Hanover Road, covering existing conditions, design "
    "analysis and the options considered."),
   ("1,970,463 bytes, 14 pages, complete to its end marker. Its cover reads LAURELWOOD MEDIAN AND PARKWAY "
    "CONCEPTUAL LANDSCAPE AND IRRIGATION IMPROVEMENTS, LADERA DR. NW TO HANOVER RD., Laurelwood Median and Parkway "
    "Conceptual Study, Department of Municipal Development, April 2025, followed by a table of contents running "
    "from median existing conditions through design opportunities."),
   ROADWAY, [{"page": PARKS, "reason": "Median and parkway landscaping."}],
   ("Its filename calls it an NA Presentation - the version shown to a neighbourhood association. The document "
    "itself is titled a conceptual study. Title it from the document and note the audience.")),
 'https://sfftp.cabq.gov/f/d425b5e959e99dd7': (
   "Briefing on the 2025 Drinking Water Consumer Confidence Report, May 2026",
   "drinking water quality",
   ("A briefing on the federally required annual drinking water quality report for 2025, explaining what the report "
    "covers, where Albuquerque's water comes from, how it is treated and monitored, and what the laboratory results "
    "mean."),
   ("1,220,118 bytes, 13 pages, complete to its end marker. Page 1 reads Drinking Water Consumer Confidence Report "
    "for 2025, May 2026, Danielle Shuryn, Compliance Division Manger - the misspelling is the document's. Later "
    "pages cover outreach and education, understanding water supply, treatment processes, required monitoring, and "
    "the Unregulated Contaminant Monitoring Rule detections for lithium and PFAS."),
   CLIMATE, [{"page": CITYDATA, "reason": "Reported environmental data."}],
   ("Two things this is not. It is **not the Consumer Confidence Report itself** - it is a briefing about that "
    "report, and cataloguing it under the report's name would be wrong. And its filename credits ABCWUA, the "
    "Albuquerque Bernalillo County Water Utility Authority, which is a separate authority from the City; **the "
    "document's own text never names ABCWUA or the City anywhere**. Attribute it from the filename only, and say "
    "so.")),
}

OWNER_REJECTED = {
 'https://sfftp.cabq.gov/f/d425b5e959e99dd7': {
  "title_for_reference": "Briefing on the 2025 Drinking Water Consumer Confidence Report, May 2026",
  "what_it_is": ("A 13-page slide deck walking an audience through what the federally required annual drinking "
                 "water quality report covers."),
  "why_not": ("The repository owner reviewed it after retrieval and determined it does not meet the standard for "
              "the site: a low-value slide deck. The document the archive actually wants is the Consumer "
              "Confidence Report itself, which this is not and which is not in the inventory."),
  "category": "briefing deck superseded by a document that should be sought instead",
  "package": "owner_rejected",
  "what_should_be_sought_instead": ("The 2025 Drinking Water Consumer Confidence Report as published - the EPA-"
                                    "required annual report itself. Its publisher is the Albuquerque Bernalillo "
                                    "County Water Utility Authority, a separate authority from the City, so it will "
                                    "not be found on a City path. It is not in master-inventory.json under any "
                                    "URL."),
  "and_this_is_why_the_distinction_mattered": ("This lane recorded that the file is a briefing about the report and "
                                               "not the report, against the link text on the City page which calls "
                                               "it the report. Had it been catalogued under that link text, the "
                                               "decision now taken could not have been taken: the archive would "
                                               "have believed it already held what it is still missing."),
 },
}

rows, rejected = [], []
for url, fn in STAGED.items():
    t, group, desc, ev, canon, cross, caution = SPEC[url]
    r = {"local_ref": "fss-%03d" % (len(rows) + 1), "inventory_id": None,
         "recommendation": "add to the inventory as a new candidate",
         "authoritative_url": url,
         "the_page_that_links_it": SHARE[url]["linked_from"][0],
         "how_it_is_labelled_on_that_page": SHARE[url]["link_text"],
         "title": t, "group": group, "description": desc, "evidence": ev,
         "description_word_count": len(desc.split()),
         "proposed_canonical_page": canon, "cross_listings": cross,
         "caution": caution, "provenance": PROVENANCE,
         "what_must_be_archived": ("The retrieved file. This authoritative_url returns 1,344 bytes of application "
                                   "shell to any fetch, so the recorded size and checksum can never be reproduced "
                                   "from it."),
         **M[url]}
    if url in OWNER_REJECTED:
        keep = {k: v for k, v in r.items()
                if k in ('local_ref', 'inventory_id', 'authoritative_url', 'the_page_that_links_it',
                         'how_it_is_labelled_on_that_page', 'filename_as_downloaded', 'size_bytes',
                         'checksum_sha256', 'leading_bytes', 'content_kind', 'page_count', 'slide_count',
                         'complete_to_its_end_marker', 'provenance')}
        keep["recommendation"] = "do not add"
        keep.update(OWNER_REJECTED[url])
        rejected.append(keep)
    else:
        rows.append(r)

not_taken = {k: v for k, v in SHARE.items() if k not in STAGED and k not in RETRIEVED_EARLIER}

artifact = {
 "batch_id": "file-share-sweep-research-2026-09-14",
 "lane": "Claude research lane: sweeping the City site for file-transfer-host links, and the documents retrieved from them",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "THIS_ARTIFACT_IS_NOT_A_TRIAGE_OF_CANDIDATES": {
  "what_that_means": "None of these files has an inventory id. Every row carries inventory_id: null and a recommendation rather than a recommended_status.",
  "so_it_cannot_be_applied_the_usual_way": "Update-Candidate.ps1 cannot act on any row here.",
 },
 "why_this_sweep_was_run": {
  "the_problem": ("sfftp.cabq.gov is a City file-transfer host. Its share URLs return 1,344 bytes of JavaScript "
                  "application shell to any automated fetch, so a document published only through it is invisible "
                  "to discovery. Two had already surfaced by accident."),
  "the_question": "How many more are there, and what are they?",
 },
 "A_GAP_IN_MY_OWN_HARVEST_THAT_THIS_SWEEP_EXPOSED": {
  "what_was_wrong": ("Both link harvests filtered candidate links by file extension - pdf, doc, docx, xls, xlsx, "
                     "ppt, pptx, csv, rtf, txt. A share URL looks like /f/39395977f639746c and has no extension at "
                     "all, so every one of them was silently discarded."),
  "how_close_it_came_to_never_being_noticed": ("Exactly one sfftp string survived the harvest: "
                                               "sfftp.cabq.gov/f/licenses.txt, the application's own licence file, "
                                               "and only because it happens to end in .txt. That one link is what "
                                               "exposed the wrongly excluded McDuffie study - and it is also what "
                                               "eventually exposed this."),
  "what_it_cost": ("The harvest lanes reported 461 undiscovered documents and implied that was what those pages "
                   "held. They also linked at least %d file-share documents that the harvest never reported."
                   % len(SHARE)),
  "the_rule": ("Filtering links by extension assumes every document URL carries one. Sweep for known document "
               "hosts by hostname as well, not only by the shape of the filename."),
 },
 "the_sweep": {
  "pages_parsed": pages_parsed,
  "where_they_came_from": ("804 pages already stored from the two link harvests, plus 1,364 City pages the "
                           "inventory records and nothing in this run had ever parsed, fetched for this sweep "
                           "(1,337 returned HTTP 200)."),
  "distinct_share_links_found": len(SHARE),
  "what_the_coverage_is_not": ("These are only pages that appear in master-inventory.json. Any City page the "
                               "original crawl never recorded could link more, and this sweep cannot see it. "
                               "%d links from %d pages is a floor, not a total." % (len(SHARE), pages_parsed)),
  "every_link_found": SHARE,
 },
 "what_the_repository_owner_decided": {
  "the_question_put_to_them": ("The sweep produced %d share links, of which 2 had already been retrieved. The "
                               "remaining %d were listed with the text each linking page uses, and the owner was "
                               "asked which were worth retrieving by hand."
                               % (len(SHARE), len(SHARE) - len(RETRIEVED_EARLIER))),
  "what_they_determined": ("Three met the standard for the site and were retrieved. The other %d did not."
                           % len(not_taken)),
  "why_that_is_recorded_here_rather_than_decided_by_me": ("Whether a food-assistance flyer published by a county "
                                                          "food bank, a photo gallery of a tree-lighting, or a "
                                                          "festival notice belongs in this archive is a scope "
                                                          "question about what the site is for. This run has "
                                                          "referred five such questions to a person. This one the "
                                                          "owner answered directly."),
  "the_links_not_taken": not_taken,
  "what_that_does_not_mean": ("It does not mean those files are not City documents, and it does not mean they are "
                              "gone. They are recorded above with their link text and their linking page, so the "
                              "decision can be revisited without running the sweep again."),
 },
 "the_owner_reviewed_the_three_and_reversed_one": {
  "what_happened": ("This lane recommended all three retrieved files for addition. The repository owner then "
                    "reviewed them and rejected one - the drinking water briefing - as a low-value slide deck, and "
                    "confirmed the other two."),
  "it_was_never_added_anywhere": ("Checked before the reversal: the file appears in no record of "
                                  "master-inventory.json by checksum or URL, nowhere in r2-inventory.json, and "
                                  "nowhere in site content. It existed only as a recommendation in this artifact, "
                                  "which is the whole point of a research lane writing recommendations rather than "
                                  "records."),
  "what_the_owner_wants_instead": ("The Consumer Confidence Report itself, when it is found. Recorded as a wanted "
                                   "document below."),
  "and_the_reason_the_other_deck_was_confirmed": ("The Main Street Corridor briefing is kept **because** it is a "
                                                  "briefing. In the owner's words, it shows how these initiatives "
                                                  "develop and are presented to the public by city employees. That "
                                                  "is a different kind of value from the document an initiative "
                                                  "eventually produces, and the archive wants it."),
  "the_principle_this_settles": ("A briefing deck is not automatically lesser than the document it describes. It is "
                                 "kept when it is itself the record of a public process - who presented what, to "
                                 "whom, when - and not kept when it is only a summary of a document the archive "
                                 "should hold directly. The drinking water deck is the second kind; the Main Street "
                                 "deck is the first."),
  "where_this_bears_on_earlier_lanes": ("Several rows in this run carry a caution that a deck is not the document "
                                        "it describes - the Sandia meeting presentation, the DRB transition "
                                        "briefing, the redistricting consultant briefings. Those cautions remain "
                                        "correct as statements of what the files are. This principle says they are "
                                        "not, by themselves, reasons to exclude. None of those rows is changed "
                                        "here; the reasoning is recorded so the owner can apply it if they wish."),
 },
 "documents_this_lane_wants_and_did_not_find": [
  {"what": "The 2025 Drinking Water Consumer Confidence Report itself, as published.",
   "why": "The briefing retrieved here describes it; the archive should hold the report, not the description.",
   "where_it_will_not_be": ("On a City path. Its publisher is the Albuquerque Bernalillo County Water Utility "
                            "Authority, a separate authority, and no URL in master-inventory.json points at it."),
   "how_it_came_to_be_wanted": "The owner rejected the briefing and named the report as the thing worth having."},
 ],
 "the_two_retrieved_and_recommended": {
  "count": len(rows),
  "combined_bytes": sum(r['size_bytes'] for r in rows),
  "why_the_main_street_deck_is_kept": ("Not despite being a briefing but because of it. It records a Council "
                                       "planner presenting a Comprehensive Plan amendment to the public on a named "
                                       "date - how the initiative was explained, and by whom. The adopted amendment, "
                                       "if it exists, is a separate document and is not in the inventory."),
  "the_other_names_itself_differently_from_its_file": ("Laurelwood Median and Parkways NA Presentation is the "
                                                       "filename; the document is titled a Conceptual Study. Same "
                                                       "pattern this run met throughout the MasterDevelopmentPlans "
                                                       "directory: title from the document, not the filename."),
 },
 "the_finding_that_outlasts_this_lane": {
  "what": ("One of the %d links is an agenda - the African American Advisory Board's agenda for 4 August 2026, "
           "published through the file share." % len(SHARE)),
  "why_it_matters": ("This run invoked the missing-minutes exception four times, each after searching official "
                     "pages and finding no minutes. A document published through this host looks like a web page "
                     "to every check those reviews ran. I am not claiming that is what happened for the MPRAB, the "
                     "EDAct committee or the LGCC; I am recording that my searches could not have distinguished "
                     "it, and that any future missing-minutes review must check for sfftp.cabq.gov links before "
                     "concluding nothing was published."),
  "recommended_action": "Treat an sfftp.cabq.gov URL as a document needing manual retrieval, never as a web page - in discovery, in link checking, and in any exhaustive-search claim.",
 },
 "how_these_bytes_were_obtained": {
  "who_retrieved_them": "The repository owner, through a browser.",
  "what_i_did": "Measured the three files as staged: byte length, SHA-256, leading bytes, container from the bytes, page or slide count, end-of-file marker, and their text.",
  "the_limitation_this_leaves": ("URL and bytes were not verified in one act, as they were everywhere else in this "
                                 "run. I can attest the files are what they say they are and that nothing in the "
                                 "archive matches them; I cannot independently attest they came from the URLs on "
                                 "these rows."),
  "what_would_strengthen_it": "A second retrieval by anyone else reproducing these checksums.",
 },
 "already_archived_check": {
  "rule_applied": "All three checksums swept against every checksummed inventory record and every row of every saved artifact, and all three share URLs against every inventory URL.",
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "archived_records_compared_against": len(ARCH_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "cross_inventory_byte_collisions": sum(1 for r in rows if r['checksum_sha256'] in ALL_SHA),
  "collisions_with_earlier_artifacts": sum(1 for r in rows if r['checksum_sha256'] in PRIOR_SHA),
  "cross_inventory_url_collisions": 0,
  "result": "All three are new to the archive by checksum and by URL.",
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "note": "The three are different documents with different checksums.",
 },
 "integration_flags": [
  {"severity": "method-gap-now-closed",
   "affects": [],
   "finding": ("Both link harvests filtered by file extension and therefore discarded every extensionless share "
               "URL. At least %d file-share documents were linked from pages the harvests parsed and none was "
               "reported." % len(SHARE)),
   "recommended_action": "Sweep for known document hosts by hostname as well as by filename shape."},
  {"severity": "owner-rejected-after-retrieval",
   "affects": [r['local_ref'] for r in rejected],
   "finding": ("The drinking water briefing was retrieved, recommended by this lane, and then rejected by the "
               "repository owner as a low-value slide deck. It was never added to any record."),
   "recommended_action": ("Do not add. Seek the Consumer Confidence Report itself, which is published by ABCWUA "
                          "rather than the City and is in no inventory record.")},
  {"severity": "wanted-document",
   "affects": [],
   "finding": "The 2025 Drinking Water Consumer Confidence Report is not in the inventory and is what the archive actually wants.",
   "recommended_action": "Add it to the discovery queue against ABCWUA, not against a City path."},
  {"severity": "provenance-is-weaker-here",
   "affects": [r['local_ref'] for r in rows + rejected],
   "finding": "These bytes were retrieved by a person through a browser, not by a fetch I performed.",
   "recommended_action": "Carry the provenance note with each record."},
  {"severity": "never-verifiable-by-refetch",
   "affects": [r['local_ref'] for r in rows + rejected],
   "finding": "All three authoritative URLs return 1,344 bytes of application shell to any fetch.",
   "recommended_action": "Mark these records as not verifiable by re-fetch, or the next verification pass will flag them as failures."},
  {"severity": "affects-every-exhaustive-search-claim",
   "affects": [],
   "finding": "A City advisory board publishes its agenda through this host, where it is indistinguishable from a web page to any automated check.",
   "recommended_action": "Any future missing-minutes or exhaustive-source review must check for sfftp.cabq.gov links before concluding nothing was published."},
 ],
 "counts": {
  "share_links_found": len(SHARE),
  "already_retrieved_in_an_earlier_lane": len(RETRIEVED_EARLIER),
  "retrieved_and_recommended_here": len(rows),
  "retrieved_and_rejected_by_the_owner": len(rejected),
  "not_retrieved_reviewed_by_the_owner": len(not_taken),
 },
 "link_check": {"checked": len(rows) + len(rejected),
                "method": ("Not applicable in the usual form: every share URL returns HTTP 200 with 1,344 bytes of "
                           "application shell. The documents were retrieved through a browser instead."),
                "integrity": "All three measured from the staged bytes; both PDFs carry their end-of-file marker and the deck's slide count was read from its ppt/slides parts."},
 "add_to_inventory": rows,
 "do_not_add": rejected,
 "archival_note": ("None of the %d proposed additions is a candidate yet. Each remains inventory-only until an R2 "
                   "archive object exists and its public download, exact size, SHA-256 and authoritative-source "
                   "provenance are verified - and for these, provenance verification cannot mean re-fetching the "
                   "URL. Combined footprint if all are archived: %s bytes."
                   % (len(rows), format(sum(r['size_bytes'] for r in rows), ','))),
 "a_note_on_what_was_not_added": ("The drinking water briefing is in do_not_add. It was measured, recommended, "
                                  "reviewed by the owner and rejected, all before any record existed. Its "
                                  "measurements are kept so the decision is reversible without retrieving it "
                                  "again."),
 "integration_note": ("Codex integration lane: this artifact creates nothing and changes nothing. Every row carries "
                      "inventory_id: null, the share URL, the page that links it, the text that page uses, the "
                      "measured size and checksum of the retrieved file, and a provenance note that must travel "
                      "with the record."),
 "shared_state_written": [],
 "classification_only": True,
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created", "staged files read only, not moved or altered"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"], "pages_parsed": pages_parsed}))
