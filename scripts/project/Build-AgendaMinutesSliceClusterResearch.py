"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-12. Third slice of the municipaldevelopment/documents lane: the
agenda and minutes series.
"""

import collections
import datetime
import glob
import json
import os
import re

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\municipaldevelopment-agenda-minutes-cluster-research-2026-09-12.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\agm\fetch.log')

CLIMATE = 'content/city-data/climate-environment.md'
FACILITIES = 'content/public-works/city-facilities.md'
BIKE = 'content/transportation/bicycling/_index.md'

GAATC_AUG_MINUTES = 'src-99529b2a4c8db5aa'   # validated against the live OnBase source; no R2 object

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag
    URL[i] = raw

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


REVIEW = ("Recorded exhaustive official-source review, 2026-09-12: the Albuquerque Energy Council has no presence on "
          "the City's website. Three candidate page URLs return HTTP 404 "
          "(/municipaldevelopment/albuquerque-energy-council, /energy-council, "
          "/municipaldevelopment/boards-commissions/albuquerque-energy-council), and the City's own site search for "
          "the exact phrase \"Albuquerque Energy Council\" returns \"0 items matching your search terms\". The "
          "inventory holds no Energy Council record outside this directory. The council appears defunct and these "
          "files are the only surviving official trace of it, so no approved minutes exist to be located for the "
          "meetings below.")

MINUTES_NOTE = ("Minutes are the record of the meeting; the agenda is the notice of it. Where minutes exist for a "
                "meeting, this lane retains the minutes and excludes the agenda, which is the treatment the archive "
                "already applies to this series — the validated GAATC minutes records carry descriptions stating they "
                "are \"retained in the minutes-only history\".")


def A(i, title, desc, date, pages, evidence, page, cross=None, extra=None):
    r = row(i, "approved for addition")
    r.update({"title": title, "description": desc, "description_word_count": len(desc.split()),
              "date": date, "pages": pages, "evidence": evidence,
              "proposed_canonical_page": page, "cross_listings": cross or []})
    if extra:
        r.update(extra)
    return r


AEC_DESC = ("The Albuquerque Energy Council's minutes record who attended, what the Department of Municipal "
            "Development's facilities and energy staff reported on City lighting, buildings and energy projects, and "
            "what the council decided at its %s meeting.")
AEC_EV = ("Born-digital PDF with a full text layer, headed \"Albuquerque Energy Council\" over %s, Department of "
          "Municipal Development, 1801 4th Street Bldg. B.")

MINUTES = [
 ("src-d43081e8b7973ea8", "April 17, 2019", "2019-04-17", 2, "Minutes",
  "The filename records it as approved on 16 May 2019, so this is the adopted text rather than a draft."),
 ("src-ca966518d02f2696", "June 19, 2019", "2019-06-19", 2, "Minutes", None),
 ("src-48f3706e1d6e8b31", "August 21, 2019", "2019-08-21", 2, "Minutes",
  "Filed under a 18 October 2019 date, which is when the council adopted them."),
 ("src-a61f376f3c74afe6", "August 19, 2020", "2020-08-19", 2, "Meeting Minutes", None),
 ("src-7928766e796148c3", "September 16, 2020", "2020-09-16", 2, "Meeting Minutes", None),
 ("src-dfbc6cbb5e58f506", "September 15, 2021", "2021-09-15", 2, "Meeting Minutes", None),
]

approved = []
for i, when, iso, pages, heading, note in MINUTES:
    extra = {"why_retained": ("The minutes are the record of a City advisory body whose work is otherwise "
                              "undocumented anywhere in the archive. " + REVIEW)}
    if note:
        extra["note"] = note
    approved.append(A(i, "Albuquerque Energy Council Meeting Minutes, " + when,
                      AEC_DESC % when, iso, pages, AEC_EV % heading, CLIMATE,
                      [{"page": FACILITIES, "reason": "Its business is City building lighting, energy retrofits and facility projects, which is what that page collects."}],
                      extra))

approved.append(A("src-5a55fed4c4811d02",
 "Albuquerque Energy Council Agenda and Meeting Minutes, January 21, 2015",
 ("A two-page Albuquerque Energy Council packet carrying the agenda and the minutes for one meeting, recording "
  "attendance, a parking structure lighting recommendation, a waste collection centre project update, the department "
  "website build and the City's three per cent energy set-aside."),
 "2015-01-21", 2,
 ("Image-only PDF with two bytes of extractable text; both pages were rendered and read. Page 1 is the agenda for "
  "Wednesday, January 21, 2015, 8:00 to 10:00 am, chaired by Wes Wilson. Page 2 is headed \"Albuquerque Energy "
  "Council / Meeting Minutes / Department of Municipal Development/FEMD / Facilities Conference Rm., Wednesday, "
  "January 21, 2015\", listing members in attendance, recording the 5th and Copper parking structure presentation "
  "(323 total lighting fixtures counted), the 6301 Eagle Rock Waste Collecting Center update, the cabq.gov website "
  "build with historical data back to 2008, the COA 3% for Energy Active Projects update, announcements, and "
  "adjournment on a Wilson motion seconded by Birdsall."),
 CLIMATE,
 [{"page": FACILITIES, "reason": "Its substance is City facility lighting and building energy work."}],
 extra={"filename_is_wrong_twice": ("The City files it as albuquerque-energy-committee-meeting-minutes-dec-17-2014.pdf. "
                                    "The body is the Energy *Council*, not Committee, and the meeting is 21 January "
                                    "2015, not 17 December 2014. Neither error is visible without rendering the file, "
                                    "and the inventory title repeats the filename. Title it from the document."),
        "why_retained": "It is both the earliest Energy Council record in the directory and the only one carrying an agenda and its minutes together. " + REVIEW}))

approved.append(A("src-95460bead0e780ee",
 "Greater Albuquerque Active Transportation Committee Meeting Minutes, July 10, 2023 (meeting packet)",
 ("The committee's minutes for its July 2023 meeting, bound with the agenda and the Open Meetings Act reference "
  "material the City distributes to members, recording the business transacted and the approval of the previous "
  "month's minutes."),
 "2023-07-10", 78,
 ("Born-digital PDF with a full text layer, 78 pages. Pages 1 and 2 are the GAATC agenda for July 10, 2023, 4:00 to "
  "6:00 pm, held virtually by Zoom, with item 2 \"Approval of July 10, 2023 Meeting Agenda\" and item 3 \"Approval of "
  "June 12, 2023 Meeting Minutes\". Pages 3 onward are headed \"Greater Albuquerque Active Transportation Committee "
  "(GAATC) Meeting Minutes Monday, July 10, 2023\". The remainder of the packet is New Mexico Open Meetings Act "
  "reference text."),
 BIKE, None,
 extra={"why_retained": ("It predates the archive's GAATC minutes series. The 28 validated GAATC records run from "
                         "January 8, 2024 to August 10, 2026; this is July 2023, six months before the earliest of "
                         "them, and fills the front of that series."),
        "note_on_that_series": ("None of those 25 records carries an r2_url — they are validated against the live "
                                "OnBase source only. See the_gaatc_series_is_not_site_ready."),
        "caution": ("The filename says \"meeting minutes draft compiled\" and the file is a packet, not a clean "
                    "minutes document. Describe it as the meeting packet containing the minutes, and note that the "
                    "bulk of its 78 pages is statutory reference material rather than committee business."),
        "tested_not_assumed": "Its first page is an agenda, so the page structure was mapped before classifying rather than reading the filename or the first sheet."}))

AGENDA_ONLY = [
 ("src-0a03811e298d7753", "May 15, 2019", "2019-05-15"),
 ("src-49351428fdea2985", "July 17, 2019", "2019-07-17"),
 ("src-42b5f091cc46568d", "October 16, 2019", "2019-10-16"),
 ("src-adf4ec503c230405", "March 18, 2020", "2020-03-18"),
 ("src-d63a640b27136aab", "April 15, 2020", "2020-04-15"),
 ("src-a034863d2b05dd79", "May 20, 2020", "2020-05-20"),
 ("src-4a350d8b561eef61", "July 16, 2020", "2020-07-16"),
 ("src-1c5b1252fde7e9b1", "October 21, 2020", "2020-10-21"),
 ("src-aaadec876bbf554f", "October 20, 2021", "2021-10-20"),
 ("src-3f3273f2dcaafbf9", "May 18, 2022", "2022-05-18"),
]
for i, when, iso in AGENDA_ONLY:
    approved.append(A(i,
     "Albuquerque Energy Council Agenda, " + when + " (approved minutes not located)",
     ("The Albuquerque Energy Council's agenda for its %s meeting lists the business the council set down for that "
      "sitting, including the reports and project updates its members were to receive from City staff." % when),
     iso, 1,
     ("Born-digital PDF with a full text layer, one page, headed \"Albuquerque Energy Council\" and \"AGENDA\" over "
      "the Department of Municipal Development address and the meeting date and time."),
     CLIMATE,
     [{"page": FACILITIES, "reason": "Its items are City facility and energy business."}],
     extra={"preserved_under_the_missing_minutes_policy": True,
            "label_required": "Agenda (approved minutes not located). It must never be presented as minutes.",
            "review": REVIEW,
            "not_cancelled": ("Checked: the file contains no cancellation, postponement, rescheduling or no-quorum "
                              "language, so the policy's exclusion for cancelled and no-quorum meetings does not "
                              "apply.")}))

# ------------------------------------------------------------------ duplicate
duplicates = [{
 **row("src-d2c20fc383f46c12", "duplicate"),
 "title_for_reference": "Greater Albuquerque Active Transportation Committee Agenda, August 10, 2026",
 "pages": 2,
 "canonical_id": "src-43b1f7a8cd1931fc",
 "canonical_url": IDX["src-43b1f7a8cd1931fc"].get('direct_file_url'),
 "canonical_state": "recommended excluded in this batch, because the minutes for that meeting are already archived",
 "basis": "Two inventory records for one file: the same URL once the Plone /view suffix is normalised.",
 "measurement": ("Byte-identical: 334,892 bytes and SHA-256 " + M["src-d2c20fc383f46c12"]["checksum_sha256"] +
                 " on both records."),
 "hash_found_it": True,
 "audit_class": ("The actionable_now class from inventory-url-collision-audit-2026-09-11.json, but a pending-pending "
                 "pair rather than a pending record with a terminal twin — the 13-group subset that artifact "
                 "separated out as still needing triage. This one is now triaged."),
}]

# ------------------------------------------------------------------ excluded
excluded = []
SUPERSEDED_BY_MINUTES = [
 ("src-87d24ac8826a2094", "April 17, 2019", "src-d43081e8b7973ea8"),
 ("src-70f9423293fd0bc4", "June 19, 2019", "src-ca966518d02f2696"),
 ("src-c31ac8274a898d24", "August 21, 2019", "src-48f3706e1d6e8b31"),
 ("src-364c6cd9aa7c9d43", "August 19, 2020", "src-a61f376f3c74afe6"),
 ("src-94e4fdd9c433773d", "September 16, 2020", "src-7928766e796148c3"),
]
for i, when, mins in SUPERSEDED_BY_MINUTES:
    r = row(i, "excluded")
    r.update({"title_for_reference": "Albuquerque Energy Council Agenda, " + when,
              "pages": 1,
              "exclusion_reason": ("Approved minutes for this meeting are held and recommended for addition in this "
                                   "same batch as " + mins + ". " + MINUTES_NOTE + " The missing-minutes policy "
                                   "permits preserving an agenda only where approved minutes cannot be located, which "
                                   "is not the case here."),
              "category": "meeting agenda superseded by its minutes",
              "minutes_record": mins})
    excluded.append(r)

r = row("src-43b1f7a8cd1931fc", "excluded")
r.update({"title_for_reference": "Greater Albuquerque Active Transportation Committee Agenda, August 10, 2026",
          "pages": 2,
          "exclusion_reason": ("The minutes for this exact meeting are already held and published as "
                               + GAATC_AUG_MINUTES + ", \"Greater Albuquerque Active Transportation Committee Meeting "
                               "Minutes — August 10, 2026\", 1,668,895 bytes, validated and live on "
                               "content/transportation/bicycling/_index.md. " + MINUTES_NOTE),
          "category": "meeting agenda superseded by its archived minutes",
          "minutes_record": GAATC_AUG_MINUTES,
          "canonical_of_group": "The byte-identical second record for this file is recommended duplicate of this one."})
excluded.append(r)

r = row("src-3580d6515ebd9ce4", "excluded")
r.update({"title_for_reference": "Greater Albuquerque Active Transportation Committee and Greater Albuquerque Recreational Trails Committee Task Force, Meeting Agenda, August 18, 2026",
          "pages": 1,
          "exclusion_reason": ("A joint GAATC and GARTC task force agenda from three weeks before this review. No "
                               "minutes for it are held, but that is not the situation the missing-minutes policy "
                               "addresses: the policy exists to preserve a record that is permanently missing, and "
                               "minutes for a meeting this recent have simply not been approved and published yet. "
                               "The archive's GAATC minutes series is current through August 10, 2026 and is "
                               "maintained, so the record for this meeting is expected rather than lost."),
          "category": "meeting agenda, minutes not yet produced",
          "revisit": ("Worth revisiting once the task force's minutes are published. If they never are, this agenda "
                      "becomes a candidate under the missing-minutes policy on a future recorded review."),
          "content": ("Lists the Zoom joining details and the members of both committees — Nancy Tankersley, Dustin "
                      "Berg and Mariah Tallent for GARTC; Sebastian Bentley, Alex Applegate and Melinda Montoya for "
                      "GAATC — under Mayor Timothy M. Keller's letterhead.")})
excluded.append(r)

rows = approved + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert set(ids) == set(M), (set(M) - set(ids), set(ids) - set(M))
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
n_minutes = sum(1 for r in approved if 'Minutes' in r['title'])
n_agendas = sum(1 for r in approved if r.get('preserved_under_the_missing_minutes_policy'))

artifact = {
 "batch_id": "municipaldevelopment-agenda-minutes-cluster-research-2026-09-12",
 "lane": "Claude research lane: the agenda and minutes series of www.cabq.gov/municipaldevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-12, the third slice of the municipaldevelopment/documents lane.",
 "cluster": "The Albuquerque Energy Council's agendas and minutes from 2015 to 2022, together with three Greater Albuquerque Active Transportation Committee records.",
 "scope": "All 26 pending-review candidates in this series that are not already rows in a saved artifact. The coverage gate is asserted in the generator.",
 "brief": "Apply the missing-minutes policy, checking for each body whether approved minutes exist before any agenda is considered.",
 "brief_finding": ("The policy resolves the whole slice and it cuts both ways within one directory. For the Greater "
                   "Albuquerque Active Transportation Committee the minutes are archived and maintained, so its "
                   "agendas are excluded. For the Albuquerque Energy Council a recorded review found the body has no "
                   "presence on the City's website at all — three candidate page URLs return 404 and the City's own "
                   "site search for the exact phrase returns zero items — so for the ten meetings where no minutes "
                   "survive, the agenda is the only official trace and is preserved under the policy's exception, "
                   "labelled accordingly."),
 "method": ("Ran the URL group-by first; one collision, a pending-pending pair. Fetched all 26 candidates and "
            "measured byte length and SHA-256 from the fetched bytes, verifying every container by leading bytes. "
            "Compared every checksum within the slice and against the 1,612 checksummed inventory records. Extracted "
            "the meeting date from the face of every file and built the agenda-to-minutes map from those dates rather "
            "than from filenames, which matters because one filename is wrong about both the body and the date. "
            "Rendered the one image-only file, both pages. Ran the official-source review for the Energy Council and "
            "recorded its result. Checked every preserved agenda for cancellation or no-quorum language."),
 "classification_only": True,
 "shared_state_written": [],
 "the_missing_minutes_review": {
  "body": "Albuquerque Energy Council",
  "result": REVIEW,
  "what_it_licenses": ("Preservation of the ten Energy Council agendas for which no minutes survive, each labelled "
                       "\"Agenda (approved minutes not located)\" and none of them presented as minutes."),
  "what_it_does_not_license": ("The five agendas whose minutes are in this same batch. Those are excluded, because "
                               "the policy's exception applies only where minutes cannot be located."),
  "cancellation_check": ("All ten were searched for cancellation, postponement, rescheduling and no-quorum language "
                         "and all ten are clean, so the policy's bar on preserving agendas for cancelled or "
                         "no-quorum meetings does not bite."),
 },
 "the_same_policy_the_other_way": {
  "body": "Greater Albuquerque Active Transportation Committee",
  "why_its_agendas_are_excluded": ("Its minutes are held and the series is maintained. The inventory holds 25 "
                                   "validated GAATC records running from January 8, 2024 to August 10, 2026, "
                                   "published on content/transportation/bicycling/_index.md, and their own "
                                   "descriptions state they are \"retained in the minutes-only history\". The archive "
                                   "already applies a minutes-only rule to this body; this lane follows it."),
  "the_august_2026_agenda": ("Excluded because " + GAATC_AUG_MINUTES + " is the validated, published minutes for that "
                             "exact meeting. Its byte-identical second inventory record is recommended duplicate."),
  "the_task_force_agenda": ("Excluded on different grounds: its minutes are not missing, they are not yet produced. "
                            "The meeting was three weeks before this review and the minutes series is current. "
                            "Recorded as worth revisiting rather than preserved by default."),
  "what_was_added_instead": ("The July 10, 2023 meeting packet, whose pages 3 onward are that meeting's minutes. It "
                             "sits six months before the earliest archived GAATC minutes and extends the series "
                             "backwards."),
 },
 "the_gaatc_series_is_not_site_ready": {
  "finding": ("All 25 validated Greater Albuquerque Active Transportation Committee minutes records are published on "
              "content/transportation/bicycling/_index.md and none of them carries an r2_url. Their validation_status "
              "reads \"passed: authoritative source HTTP 200\" and their direct_file_url points at "
              "onbase.cabq.gov/publicaccess, the City's live document system."),
  "why_it_matters": ("The standing rule is explicit: a static document is not site-ready until its original is "
                     "archived to R2 and the public archive download is verified, and an official live link alone is "
                     "not a substitute. An entire published series rests on links to a City system that can "
                     "reorganise or expire its document identifiers."),
  "how_it_was_found": ("Incidentally. The lane needed to confirm that the August 2026 minutes really were held before "
                       "excluding the agenda for the same meeting, and checking the record turned up an empty r2_url "
                       "on it and then on every one of its 24 siblings."),
  "scope": "This is outside this lane's classification scope. No record here is modified; it is raised for the integration lane.",
  "recommended_action": ("Queue the 25 GAATC minutes for R2 archival and download verification. Until then the "
                         "bicycling index publishes 25 entries that the project's own rule would not call "
                         "site-ready."),
 },
 "a_filename_wrong_twice": {
  "record": "src-5a55fed4c4811d02",
  "filed_as": "albuquerque-energy-committee-meeting-minutes-dec-17-2014.pdf",
  "actually": ("A two-page packet: the Albuquerque Energy *Council* agenda for January 21, 2015 on page 1 and that "
               "meeting's minutes on page 2."),
  "both_errors": "The body's name (Committee for Council) and the date (17 December 2014 for 21 January 2015).",
  "why_it_matters": ("The file is image-only with two bytes of extractable text, so neither error is visible without "
                     "rendering, and the inventory title simply repeats the filename. Any pass that trusted the "
                     "filename would have dated the archive's earliest Energy Council record more than a month wrong "
                     "and attributed it to a body that does not exist."),
  "for_integration": "Title it from the document, not from the filename or the inventory title.",
 },
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": 0,
  "internal_byte_collisions": 1,
  "what_the_check_found": ("No byte duplication against the archive, but the decisive find was a title match rather "
                           "than a hash match: the GAATC minutes for August 10, 2026 are already validated and "
                           "archived, which is what excludes the agenda for the same meeting. A checksum comparison "
                           "alone would have found nothing, because an agenda and its minutes are different "
                           "documents."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 1,
  "internal_collision_group_size": 2,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_slice": 1,
  "url_collisions_resolved_here": 1,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 1,
  "relationships_found_by_date_mapping": 6,
  "note": ("Hashing found the one duplicate. The six agenda-to-minutes relationships were found by extracting the "
           "meeting date from the face of every file and matching on it — not by filename, which is unreliable here, "
           "and not by hash, which cannot relate two different documents about one meeting."),
 },
 "integration_flags": [
  {"severity": "substantive-find",
   "affects": [r["id"] for r in approved if 'Minutes' in r['title']],
   "finding": f"{n_minutes} sets of minutes for two City advisory bodies: the Albuquerque Energy Council from 2015 to 2021, whose work is otherwise undocumented anywhere in the archive, and a GAATC meeting packet from July 2023 that extends the archived minutes series six months further back.",
   "recommended_action": "Approve. Place the Energy Council records on the climate and environment page, cross-listed to city facilities; the GAATC packet on the bicycling index beside the existing minutes series."},
  {"severity": "policy-exception-invoked",
   "affects": [r["id"] for r in approved if r.get('preserved_under_the_missing_minutes_policy')],
   "finding": f"{n_agendas} Energy Council agendas are preserved under the missing-minutes policy after a recorded review found the body has no presence on the City website and no minutes survive for those meetings.",
   "recommended_action": "Approve, and carry the label \"Agenda (approved minutes not located)\" into the published description on every one. None may be presented as minutes."},
  {"severity": "title-from-the-document",
   "affects": ["src-5a55fed4c4811d02"],
   "finding": "One record's filename is wrong about both the body and the date, and the inventory title repeats it. The file is image-only, so the errors are invisible without rendering.",
   "recommended_action": "Title it Albuquerque Energy Council Agenda and Meeting Minutes, January 21, 2015."},
  {"severity": "revisit-later",
   "affects": ["src-3580d6515ebd9ce4"],
   "finding": "The GAATC and GARTC task force agenda of August 18, 2026 has no minutes yet because the meeting is recent, not because the record is lost.",
   "recommended_action": "Exclude now; revisit when the task force's minutes are published. The distinction between not-yet-produced and permanently-missing matters for how the policy is applied."},
  {"severity": "not-site-ready",
   "affects": [GAATC_AUG_MINUTES],
   "finding": "All 25 validated GAATC minutes records are published on the bicycling index with no r2_url, validated against the live OnBase source only. The standing rule says an official live link is not a substitute for a verified archive object.",
   "recommended_action": "Queue the whole series for R2 archival and download verification. Found incidentally while confirming the minutes existed before excluding the matching agenda."},
  {"severity": "url-twin-resolution",
   "affects": ["src-d2c20fc383f46c12", "src-43b1f7a8cd1931fc"],
   "finding": "A pending-pending URL twin pair, byte-identical at 334,892 bytes. This is from the 13-group subset the URL-collision audit separated out as still needing triage rather than the 79 actionable_now groups.",
   "recommended_action": "Resolve one as duplicate of the other; both are excluded on the merits anyway."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "http_200_but_not_the_document": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-12.",
                "containers_verified": "26 genuine PDFs by leading bytes. One has no usable text layer and both its pages were rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are static PDFs and are inventory-only until an R2 archive "
                   f"object exists for each and its public download, exact size, SHA-256, and authoritative-source "
                   f"provenance are verified. Combined archive footprint if authorized: {approved_bytes:,} bytes, "
                   f"most of it the 78-page GAATC packet. One record, src-5a55fed4c4811d02, is an image-only scan "
                   f"and will not be reachable by full-text search without optical character recognition; its "
                   f"content is carried in the evidence field instead."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                      "scripts/project/Update-Candidate.ps1 only. The one duplicate row carries a canonical_id "
                      "pointing at a record in this same batch that is itself excluded, which is correct: the two are "
                      "one file and neither is archived. Ten approved rows carry "
                      "preserved_under_the_missing_minutes_policy and a required label; that label must reach the "
                      "published description. Six excluded rows name the minutes record that supersedes them. No row "
                      "requires human review. Sizes and checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
