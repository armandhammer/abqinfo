"""Claude research lane. The two City traffic studies published only through the
City file-transfer host, retrieved through a browser by the repository owner
after automated fetches could not reach them.

One resolves an open human-review row in an earlier artifact; the other is a
proposed addition. It never modifies master-inventory.json, checkpoint.json,
r2-inventory.json, site content, or R2.

Dated 2026-09-14.
"""

import datetime
import glob
import hashlib
import json
import os
import re
import subprocess

OUT = (r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
       r'\file-share-retrieval-research-2026-09-14.json')
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
DISC = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery'
STAGE = r'C:\Users\ben\Documents\ABQinfo\research\staging\document-review'

ROADWAY = 'content/transportation/roadway-projects/_index.md'
SPEED = 'content/transportation/roadway-projects/speed-management.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
CRASH = 'content/transportation/safety-crash-data.md'
ABOUT = 'content/about/_index.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

FILES = {
 'mcduffie': 'COA Final McDuffie_Traffic Calming Study 052024.pdf',
 'sandia': 'SandiaHSTrafficCalmingSafetyStudy_FinalwApp_01-2024.pdf',
}

M = {}
for k, fn in FILES.items():
    b = open(os.path.join(STAGE, fn), 'rb').read()
    out = subprocess.run(['pdftotext', '-layout', os.path.join(STAGE, fn), '-'],
                         capture_output=True).stdout.decode('utf-8', 'replace')
    M[k] = {"filename_as_downloaded": fn,
            "size_bytes": len(b),
            "checksum_sha256": hashlib.sha256(b).hexdigest(),
            "leading_bytes": b[:4].hex(),
            "content_kind": "PDF",
            "page_count": out.count('\f'),
            "complete_to_its_end_marker": b'%%EOF' in b[-2048:]}

ALL_SHA, ARCH_SHA = {}, {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s:
        ALL_SHA.setdefault(s, (x['id'], x.get('status')))
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
                PRIOR_SHA.setdefault(r['checksum_sha256'],
                                     (os.path.basename(f), r.get('id') or r.get('local_ref')))

HITS = {k: (ALL_SHA.get(v['checksum_sha256']), PRIOR_SHA.get(v['checksum_sha256'])) for k, v in M.items()}

PROVENANCE = ("Retrieved through a browser by the repository owner from the share URL recorded here, and placed in "
              "research/staging/document-review. I measured the file as staged. I did not perform the retrieval and "
              "cannot independently attest that these bytes came from that URL; see how_these_bytes_were_obtained.")

mc = dict(M['mcduffie'])
mc.update({
 "id": "src-2f89e1bc040e1d33",
 "inventory_id": "src-2f89e1bc040e1d33",
 "recommended_status": "approved for addition",
 "authoritative_url": "https://sfftp.cabq.gov/f/cf8779d97e34c92c",
 "the_page_that_links_it": ("https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/"
                            "traffic-street-improvements/copy2_of_the-mcduffie-twin-parks-traffic-calming-study"),
 "inventory_title": (IDX.get('src-2f89e1bc040e1d33') or {}).get('title'),
 "title": "McDuffie / Twin Parks Neighborhood Traffic Calming Study, final report, 7 May 2024",
 "description": ("The final traffic calming study for the McDuffie and Twin Parks neighbourhood, prepared for the "
                 "City by consulting engineers, covering the data analysis, two public meetings and the measures "
                 "recommended for the neighbourhood's residential streets."),
 "evidence": ("11,940,327 bytes, 321 pages, complete to its end marker. Its cover reads City of Albuquerque, "
              "McDuffie/Twin Parks Neighborhood, Albuquerque, NM, 5/7/2024, Traffic Calming Study, Prepared for "
              "City of Albuquerque, Prepared by Wilson & Company, Inc., Engineers & Architects of 4401 Masthead "
              "Street NE. Its contents list sections for Public Meeting #1 and Public Meeting #2 with post-meeting "
              "comments, and a summary."),
 "group": "traffic calming studies",
 "proposed_canonical_page": STUDIES,
 "cross_listings": [{"page": SPEED, "reason": "Traffic calming measures on residential streets."},
                    {"page": ROADWAY, "reason": "A neighbourhood roadway project study."}],
 "provenance": PROVENANCE,
 "the_measurement_problem_this_record_had": (
   "The inventory record's URL is a file-share page, not a file. Fetching it returns HTTP 200 and 1,344 bytes of "
   "JavaScript application shell, which is what final-sweep-cluster-research-2026-09-13.json measured and, at "
   "first, wrongly excluded as a live web page. The size and checksum on this row are the document's, not the "
   "URL's."),
 "what_must_be_archived": ("The retrieved PDF, not the share page. Any future verification of this record has to "
                           "compare against 11,940,327 bytes and this SHA-256, because re-fetching the "
                           "authoritative_url will never produce them."),
})
mc["description_word_count"] = len(mc["description"].split())

sn = dict(M['sandia'])
sn.update({
 "local_ref": "fsr-001",
 "inventory_id": None,
 "recommendation": "add to the inventory as a new candidate",
 "authoritative_url": "https://sfftp.cabq.gov/f/7e1d61fbc4c19830",
 "the_page_that_links_it": ("https://www.cabq.gov/council/find-your-councilor/district-7/district-7-projects/"
                            "traffic-street-improvements/sandia-high-school-area-safety-and-traffic-calming-measures"),
 "how_it_is_labelled_on_that_page": "Report - View the completed Sandia High School Safety and Traffic Calming Study",
 "title": "Sandia High School Area Traffic Calming and Safety Study, final report with appendices, January 2024",
 "description": ("The final traffic calming and safety study for the neighbourhood around Sandia High School, "
                 "setting out the scope, data analysis, field observations and recommended countermeasures for the "
                 "area's local residential streets, with its appendices."),
 "evidence": ("10,493,498 bytes, 157 pages, complete to its end marker. Its cover reads Traffic Calming and Safety "
              "Study, Sandia High School Area, Final Report | January 2024, and carries a New Mexico professional "
              "engineer's seal. Its executive summary gives the study area as bounded by Louisiana Boulevard to the "
              "west, Wyoming Boulevard to the east, Comanche Road to the north and Phoenix Avenue to the south, and "
              "states that the scope excludes the bounding arterial and collector roadways."),
 "group": "traffic calming studies",
 "proposed_canonical_page": STUDIES,
 "cross_listings": [{"page": SPEED, "reason": "Traffic calming measures on residential streets."},
                    {"page": CRASH, "reason": "A safety analysis of a specific area."}],
 "provenance": PROVENANCE,
 "what_must_be_archived": ("The retrieved PDF. Its authoritative_url is a share page that returns 1,344 bytes of "
                           "application shell to any fetch, so the recorded size and checksum can never be "
                           "reproduced from that URL."),
})
sn["description_word_count"] = len(sn["description"].split())

artifact = {
 "batch_id": "file-share-retrieval-research-2026-09-14",
 "lane": "Claude research lane: the two traffic studies published only through the City file-transfer host",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-14.",
 "why_this_artifact_exists": {
  "the_problem": ("Two City traffic studies are published only through sfftp.cabq.gov, a file-transfer host whose "
                  "share URLs return 1,344 bytes of JavaScript application shell to any automated fetch. The "
                  "document loads only when that application runs. The host's REST API answers 401 without "
                  "credentials, and I did not attempt to work around it."),
  "what_it_cost_the_archive": ("One of the two, the McDuffie/Twin Parks study, was already an inventory candidate - "
                               "and final-sweep-cluster-research-2026-09-13.json excluded it as a live web page, "
                               "because its bytes really are HTML. The other was not in the inventory at all."),
  "how_it_was_resolved": "Both were retrieved through a browser and staged for measurement.",
 },
 "how_these_bytes_were_obtained": {
  "who_retrieved_them": ("The repository owner, through a browser, after I reported that I could not and that the "
                         "files needed manual retrieval."),
  "what_i_did": ("Measured the two files as staged in research/staging/document-review: byte length, SHA-256, "
                 "leading bytes, page count, end-of-file marker, and the text of their opening pages."),
  "the_limitation_this_leaves": ("Every other measurement in this run was taken from bytes I fetched myself, so the "
                                 "URL and the bytes were verified in one act. Here they were not. I can attest that "
                                 "these files are what they say they are and that nothing in the archive matches "
                                 "them; I cannot independently attest that they came from the URLs recorded on "
                                 "these rows."),
  "why_that_is_acceptable_here_but_should_be_recorded": ("The alternative was to leave a real City study "
                                                         "permanently excluded on the strength of a shell page. But "
                                                         "the provenance chain is weaker than every other row this "
                                                         "run has produced, and the rows say so rather than "
                                                         "presenting these as ordinary measurements."),
  "what_would_strengthen_it": ("A second retrieval by anyone else, through the same share links, reproducing these "
                               "checksums."),
 },
 "a_correction_this_retrieval_forces": {
  "what_i_wrote": ("find-your-councilor-cluster-research-2026-09-14.json approved the Sandia meeting presentation "
                   "and recorded, from the deck's own schedule slide, that the final report was due July 2023 - "
                   "and that if it existed it was not in the inventory."),
  "what_is_actually_the_case": ("The final report exists and is dated January 2024, six months later than the "
                                "schedule promised. The deck was right that a final report was coming and right "
                                "that it was not itself that report; the date it gave was a plan, not a fact."),
  "the_rule": ("A schedule inside a document tells you what was intended on the day it was written. It is not "
               "evidence of when anything happened, and a row should not carry it as though it were."),
  "what_still_stands": ("The presentation is still correctly labelled as the meeting deck rather than the study, "
                        "which is the distinction the project page itself draws."),
 },
 "what_this_resolves_elsewhere": {
  "final-sweep-cluster-research-2026-09-13.json": ("Its one requires-human-review row, src-2f89e1bc040e1d33, held "
                                                   "pending browser retrieval. Retrieved. That artifact is updated "
                                                   "to approved for addition and points here."),
  "undiscovered-documents-research-2026-09-14.json": ("Its one_file_found_and_not_retrievable block recommended "
                                                      "retrieving the Sandia study through a browser. Done; the "
                                                      "block now points here."),
  "find-your-councilor-cluster-research-2026-09-14.json": ("Its caution on the Sandia deck said the July 2023 final "
                                                           "report was not in the inventory. Corrected above and "
                                                           "pointed here."),
 },
 "the_wider_finding_this_does_not_resolve": {
  "what": ("Any City document published only through sfftp.cabq.gov is invisible to a crawler in exactly this way. "
           "Two surfaced only because two pages happened to link them, and one of those two was found by harvesting "
           "a licence-file link out of the application shell."),
  "what_would_settle_it": ("A sweep of the City site for every sfftp.cabq.gov link. The harvest lanes covered 754 "
                           "pages and found these two; 2,586 page-shaped inventory records have never been parsed "
                           "at all."),
  "recommended_action": "Treat an sfftp.cabq.gov URL as a document that needs manual retrieval, never as a web page.",
 },
 "measurements": M,
 "already_archived_check": {
  "rule_applied": "Both checksums swept against every checksummed inventory record and every row of every saved artifact.",
  "all_checksummed_records_compared_against": len(ALL_SHA),
  "archived_records_compared_against": len(ARCH_SHA),
  "artifact_rows_compared_against": len(PRIOR_SHA),
  "cross_inventory_byte_collisions": sum(1 for a, b in HITS.values() if a),
  "collisions_with_earlier_artifacts": sum(1 for a, b in HITS.values() if b and not a),
  "result": ("Neither file matches anything the archive holds or anything this run has already decided. Both are "
             "new documents."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "note": ("The two studies are different documents for different neighbourhoods, 11,940,327 and 10,493,498 bytes, "
           "with different checksums."),
 },
 "integration_flags": [
  {"severity": "provenance-is-weaker-here",
   "affects": ["src-2f89e1bc040e1d33", "fsr-001"],
   "finding": ("These bytes were retrieved by a person through a browser, not by a fetch I performed. URL and bytes "
               "were not verified in one act, as they were for every other row in this run."),
   "recommended_action": ("Record the provenance note with each record. A second independent retrieval reproducing "
                          "these checksums would close the gap.")},
  {"severity": "the-url-can-never-reproduce-the-bytes",
   "affects": ["src-2f89e1bc040e1d33", "fsr-001"],
   "finding": ("Both authoritative URLs are file-share pages that return 1,344 bytes of application shell to any "
               "fetch. Re-fetching them will never produce the recorded size or checksum."),
   "recommended_action": ("Archive the retrieved PDFs and mark these records as not verifiable by re-fetch, or the "
                          "next verification pass will flag them as failures.")},
  {"severity": "resolves-an-open-row",
   "affects": ["src-2f89e1bc040e1d33"],
   "finding": "The final-sweep lane's only human-review row is answered: there is a document, and it is a 321-page final traffic calming study of May 2024.",
   "recommended_action": "Apply approved for addition."},
  {"severity": "new-candidate",
   "affects": ["fsr-001"],
   "finding": "The Sandia High School Area study's final report, January 2024, 157 pages with appendices, is not in the inventory under any path.",
   "recommended_action": "Create it as a candidate; it then falls under the ordinary archival gate."},
  {"severity": "date-correction",
   "affects": [],
   "finding": "The Sandia deck's schedule promised a final report in July 2023; the final report is dated January 2024.",
   "recommended_action": "Do not carry a document's internal schedule as though it recorded what happened."},
 ],
 "counts": {
  "reviewed": 2,
  "resolves_an_existing_candidate": 1,
  "add_to_the_inventory_as_a_new_candidate": 1,
 },
 "link_check": {"checked": 2,
                "method": ("Not applicable in the usual form. Both share URLs were fetched during earlier lanes and "
                           "return HTTP 200 with 1,344 bytes of application shell; the documents were retrieved "
                           "through a browser instead."),
                "integrity": "Both files measured from the staged bytes; both carry their end-of-file marker."},
 "resolves_an_existing_candidate": [mc],
 "add_to_inventory": [sn],
 "archival_note": ("Neither record is site-ready. The McDuffie study is an existing candidate and the Sandia study "
                   "is not a candidate at all yet. Each remains inventory-only until an R2 archive object exists "
                   "and its public download, exact size, SHA-256 and authoritative-source provenance are verified - "
                   "and for these two, provenance verification cannot mean re-fetching the URL. Combined footprint "
                   "if both are archived: %s bytes." % format(M['mcduffie']['size_bytes'] + M['sandia']['size_bytes'], ',')),
 "integration_note": ("Codex integration lane: the McDuffie row carries an inventory id and can be applied through "
                      "Update-Candidate.ps1. The Sandia row carries inventory_id: null and must be created first. "
                      "Both rows' size and checksum are the document's, not the URL's response, and both carry a "
                      "provenance note that must travel with the record."),
 "shared_state_written": [],
 "classification_only": True,
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "no inventory candidate created", "staged files read only, not moved or altered"],
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"],
                  "mcduffie": M['mcduffie']['size_bytes'], "sandia": M['sandia']['size_bytes']}))
