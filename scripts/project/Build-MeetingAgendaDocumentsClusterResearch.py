"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\meeting-agenda-documents-cluster-research-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
FETCH = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
         r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\mad\fetch.log')
BASE = 'https://www.cabq.gov/council/documents/meeting-agenda-documents/'

SURVEYS = 'content/city-data/city-progress-surveys.md'
SAFETY = 'content/city-data/public-safety-data.md'

PRECEDENT = 'src-00f9dae00dbfbbc4'   # already-excluded Winrock TIDD agenda in this directory

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC = {}, {}
for line in open(FETCH, encoding='utf-8'):
    i, c, s, h, mag = line.rstrip('\n').split('\t')
    M[i] = {"size_bytes": int(s), "checksum_sha256": h}
    MAGIC[i] = mag

LC = ("HTTP 200 verified 2026-09-11 by full GET; size_bytes and checksum_sha256 measured "
      "from the fetched bytes, because the inventory record carried neither")

SUBSTANCE_TEST = (
 "Agenda only: it lists items for consideration but contains none of the resolutions, reports or plans it names. "
 "This is the test the directory's own terminal record already applies. src-00f9dae00dbfbbc4, the Winrock Town Center "
 "Tax Increment Development Districts board agenda of January 20 2009, is excluded with the reason \"Meeting agenda "
 "lists consideration of two Winrock TID resolutions but contains neither final resolution nor supporting substantive "
 "plan\" and the validation status \"excluded: agenda only; does not contain the referenced adopted resolutions or "
 "substantive planning record\".")


def row(i, status):
    r = {"id": i, "authoritative_url": IDX[i].get('direct_file_url') or IDX[i].get('source_url'),
         "recommended_status": status, "link_check": LC,
         "content_kind": "PDF" if MAGIC[i] == '25504446' else "HTML"}
    r.update(M[i])
    return r


approved = [
 {**row("src-1f47a1d06392eecc", "approved for addition"),
  "title": "Resolution of the Committee on Guidelines for Negotiations Determining Reasonable Notice of Meetings for Calendar Year 2014, With the March 19, 2014 Meeting Agenda",
  "description": "The City committee that sets collective bargaining negotiation guidelines adopts its annual Open Meetings Act notice resolution, fixing seventy-two hours' notice, how agendas are published, and the conditions under which emergency meetings may be called.",
  "date": "2014-03-19", "pages": 3,
  "proposed_canonical_page": SURVEYS,
  "cross_listings": [{"page": SAFETY, "reason": "The Committee on Guidelines for Negotiations sets the City's bargaining guidelines, which is the process behind the police union agreement recommended in the police-oversight artifact of the same date."}],
  "evidence": ("Image-only PDF with no text layer; pages 1 and 2 were rendered and read. Page 1 is the agenda of the "
               "Committee on Guidelines for Negotiations for Wednesday March 19 2014, chaired by Chief Administrative "
               "Officer Robert J. Perry as interim chair. Page 2 begins the full text of the \"Resolution of the "
               "Committee on Guidelines for Negotiations to Determine Reasonable Notice of Meetings for the Calendar "
               "Year 2014\", reciting Section 10-15-1(B) and (D) of the Open Meetings Act, NMSA 1978 Sections 10-15-1 "
               "to 4, and resolving five numbered sections on meeting notice."),
  "why_retained": ("The only file in this directory that passes the test its own terminal record sets. Every other "
                   "agenda here lists resolutions without containing them; this one contains the adopted resolution "
                   "in full. Its filename says so and the render confirms it: 31914GuidlinesCommitteeAgendaand"
                   "ResolutionFINAL.pdf."),
  "identification_note": ("Nothing in the inventory title, which is the bare filename, indicates that a resolution is "
                          "attached. It was found by rendering, because the file has no text layer at all."),
  "caveat": "It is a procedural notice resolution, not a substantive policy instrument. Describe it as what it is."},
]
for r in approved:
    r["description_word_count"] = len(r["description"].split())

duplicates = [
 {**row("src-d5cfa0fec162e3c1", "duplicate"),
  "title_for_reference": "Albuquerque City Council Study Session Agenda, March 7, 2014",
  "pages": 1,
  "canonical_id": "src-ff9893ec1cd700be",
  "canonical_url": "https://www.cabq.gov/council/documents/police-oversight-task-force-documents/3-7-14%20Study%20Session%20Agenda%20-%20FINAL.pdf",
  "canonical_state": "recommended requires human review in the police-oversight-task-force artifact of the same date",
  "basis": ("The same City Council study session agenda of March 7 2014, published in two Council directories. "
            "Normalized text is identical at ratio 1.0000 with full token coverage in both directions and an identical "
            "1,132 normalized characters; the files differ by 177 bytes of encoding, 71,569 here against 71,392 there."),
  "hash_found_it": False,
  "note": ("The canonical is held at requires human review because Council keeps study session minutes as a running "
           "series and the policy precondition that no approved minutes exist is not met. Pointing this copy at it "
           "keeps that question answered once rather than twice. Integrate the two artifacts together."),
  "cross_directory": True},
]


def X(i, title, body, pages, reason=None, extra=None):
    r = row(i, "excluded")
    r.update({"title_for_reference": title, "body": body, "pages": pages,
              "exclusion_reason": reason or SUBSTANCE_TEST,
              "precedent": PRECEDENT})
    if extra:
        r.update(extra)
    return r


excluded = [
 X("src-9de32e0dd9c4a8e0", "Albuquerque City Council Agenda, January 22, 2014", "Albuquerque City Council", 4),
 X("src-2d75c127adec9fc9", "Albuquerque City Council Agenda, February 3, 2014", "Albuquerque City Council", 4),
 X("src-976d642659a9c1b2", "Albuquerque City Council Letter of Introduction, January 22, 2014",
   "Albuquerque City Council", 1,
   reason=("A Letter of Introduction is the Council's list of communications and bills introduced at a meeting, "
           "recording for each an item number, a one-line subject and the committee it was referred to. It names "
           "records without containing them, which is the same defect as an agenda under the directory's substance "
           "test, and it is the companion document to the January 22 2014 agenda also excluded here."),
   extra={"sample_content": "Item 1a is EC-14-22, the Mayor's appointment of Mrs. Karen L. Hudson to the Environmental Planning Commission, referred to the Land Use, Planning, and Zoning Committee; item 1b is EC-14-23, submission of the Five-Year Forecast."}),
 X("src-fda00a8093561da6", "Albuquerque City Council Letter of Introduction, February 3, 2014",
   "Albuquerque City Council", 3,
   reason="Same document type and same ground as the January 22 Letter of Introduction above."),
 X("src-09b266eabc8aa975", "Finance and Government Operations Committee Agenda, February 10, 2014",
   "Finance and Government Operations Committee", 2),
 X("src-42c51b56f4c6fa2e", "Finance and Government Operations Committee Agenda, March 10, 2014",
   "Finance and Government Operations Committee", 3),
 X("src-8c067aacd117389a", "Albuquerque/Bernalillo County Government Commission Agenda, March 3, 2009",
   "Albuquerque/Bernalillo County Government Commission", 1),
 X("src-d0bc37f3b3711f5d", "Albuquerque/Bernalillo County Government Commission Agenda, March 17, 2011",
   "Albuquerque/Bernalillo County Government Commission", 1,
   extra={"note": "Its membership list is the one durable detail: the commission seats the Mayor, four County Commissioners and four City Councilors. That fact needs no archived agenda to record it."}),
 X("src-ffa1c53ba6478833", "The Trails Public Improvement District Board Agenda, February 4, 2014",
   "The Trails Public Improvement District", 1,
   extra={"lists_without_containing": "Resolution 2014-01 establishing an Open Meetings Policy and Annual Schedule of Meetings, and Resolution 2014-02 approving Quarterly Reports to the Department of Finance and Administration.",
          "minutes_signal": "Item 3 is \"Review of minutes of August 1, 2013 meeting\", which again shows this board kept minutes it did not publish."}),
 X("src-de4897208bd2a7b7", "The Trails Public Improvement District Board Agenda, February 12, 2014",
   "The Trails Public Improvement District", 1,
   extra={"lists_without_containing": "Resolution 2014-03 approving a professional contract with David Taussig and Associates for election services, plus reports on a proposed settlement and on foreclosure proceedings."}),
 X("src-bf9851ed23cd8281", "Saltillo Public Improvement District Board Agenda, February 4, 2014",
   "Saltillo Public Improvement District", 1,
   extra={"lists_without_containing": "Resolutions 2014-01, 2014-02 and 2014-03, the last approving the Land Ownership Report."}),
 X("src-c40120beb93660b5", "Mesa del Sol Public Improvement Districts Board Agenda, February 12, 2014",
   "Mesa del Sol Public Improvement District", 1,
   extra={"masthead_note": "The masthead reads DISTRICTS plural here and DISTRICT singular on the May 6 2014 agenda. The City varies its own wording between meetings; it is one body."}),
 X("src-e34955a7c649cde1", "Mesa del Sol Public Improvement District Special Board Meeting Agenda, May 6, 2014",
   "Mesa del Sol Public Improvement District", 1),
 X("src-d47f5aece7717493", "Mesa del Sol Tax Increment Development Districts 1 to 5 Meeting Agenda, February 5, 2009",
   "Mesa del Sol Tax Increment Development Districts 1-5", 1),
 X("src-3241b0da2e08730c", "Winrock Town Center Tax Increment Development Districts Board Agenda, November 14, 2008",
   "Winrock Town Center Tax Increment Development Districts", 1,
   extra={"direct_precedent": ("This is the same board as the already-excluded src-00f9dae00dbfbbc4, two months "
                               "earlier. It lists Resolution 2008-01 establishing an Open Meetings Policy and "
                               "Resolution 2008-02 approving Bylaws, and contains neither. The precedent applies "
                               "without interpretation.")}),
 X("src-3a79439ff2bba95d", "Quorum at ABQ Uptown Tax Increment Development District Board Agenda, January 20, 2009",
   "Quorum at ABQ Uptown Tax Increment Development District", 1),
 X("src-d810ef001941f846", "Quorum at ABQ Uptown Tax Increment Development District Board Agenda, November 14, 2008",
   "Quorum at ABQ Uptown Tax Increment Development District", 1,
   extra={"filename_trap": ("The file is named bhfsdocs-1209862-v2-hunt_board_agenda.pdf and the inventory titles it "
                            "\"BHFSDOCS-1209862-v2-HuntBoardAgenda\". Its masthead reads QUORUM AT ABQ UPTOWN TAX "
                            "INCREMENT DEVELOPMENT DISTRICT, not Hunt. The BHFSDOCS prefix is a document-management "
                            "stamp from the outside law firm that drafted it, and the client name in the filename is "
                            "not the name of the body meeting. If this record is ever cited, cite the masthead.")}),
 X("src-645154f89f6064aa", "Meeting agenda documents collection landing page", "n/a", 0,
   reason="The Plone collection landing page for this directory, not a document.",
   extra={"content_kind_note": "HTML by leading bytes, unlike the twenty PDFs."}),
]

rows = approved + duplicates + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids))
assert len(ids) == 20, len(ids)
counts = collections.Counter(r["recommended_status"] for r in rows)
bodies = collections.Counter(r["body"] for r in excluded if r["body"] != "n/a")

artifact = {
 "batch_id": "meeting-agenda-documents-cluster-research-2026-09-11",
 "lane": "Claude research lane: www.cabq.gov/council/documents/meeting-agenda-documents cluster",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "cluster": "The Albuquerque City Council's posted meeting agendas for Council, its committees, and the tax increment and public improvement district boards it seats.",
 "scope": "All 20 pending-review candidates in that directory. The directory holds 21 records; the twenty-first is already excluded and is what decides most of this artifact.",
 "brief": "Apply the missing-minutes agenda policy and its recorded exhaustive-review method, running the URL group-by first.",
 "brief_finding": "The brief pointed at the wrong policy. The missing-minutes policy governs whether an agenda may be preserved when minutes cannot be found; this directory's own terminal record decides these files on a different and prior question, whether the agenda carries any substance at all. Eighteen of the twenty list resolutions, reports and plans without containing any of them. One is a study session agenda already held in another directory. One turns out not to be an agenda at all: it carries the full adopted text of a City committee's Open Meetings Act notice resolution, and nothing in its inventory title says so.",
 "method": "Ran the URL group-by across the directory first, per the inventory URL-collision audit of the same date; it found no collisions. Fetched all 20 candidates and recorded exact byte length and SHA-256 for each. Read the already-excluded record's recorded reasoning before classifying anything, which is what supplied the test. Read every agenda's masthead and business list rather than its filename. Rendered the one file with no text layer. Compared all checksums against the 1,612 checksummed inventory records, and compared one file by normalized text against a copy in another Council directory.",
 "classification_only": True,
 "shared_state_written": [],
 "governing_test": {
  "source": f"{PRECEDENT}, already excluded in this same directory",
  "recorded_reason": "Meeting agenda lists consideration of two Winrock TID resolutions but contains neither final resolution nor supporting substantive plan.",
  "recorded_validation_status": "excluded: agenda only; does not contain the referenced adopted resolutions or substantive planning record",
  "the_test": "Does the agenda contain the substance it names, or only name it?",
  "why_it_governs_here": ("Every board agenda in this directory has the same shape: call to order, approval of agenda, "
                          "consideration of numbered resolutions, reports, adjourn. The resolutions are named and never "
                          "included. The precedent applies without interpretation, and applying it uniformly is what "
                          "makes the one exception visible."),
  "relationship_to_the_missing_minutes_policy": (
   "They are not in conflict and they are not the same question. The AGENTS.md missing-minutes policy is permissive: "
   "after an exhaustive review finds no approved minutes, ABQInfo MAY preserve a verified original official agenda. It "
   "never requires preservation. The substance test asks a prior question and can answer no before the minutes "
   "question is reached. The rail-yards and redistricting artifacts of the same date preserved orphan agendas that "
   "carried substantive business of their own; this directory's agendas do not, which is why the outcome differs."),
 },
 "revises_an_earlier_recommendation": {
  "affects": ["src-bc1dbb930feefaaf", "src-b657a1bd0d19ffe8", "src-a6bd9f4f6ae1cb40",
              "src-7e3d417f146c307b", "src-c393d59e029b52e9", "src-15bd43bb6a15984d",
              "src-9dbe491dce873f71"],
  "where": "project-state/discovery/council-documents-cluster-research-2026-09-11.json",
  "what_that_artifact_said": ("It held six Trails Public Improvement District agendas and one Local Government "
                              "Coordinating Commission agenda at requires human review, pending a single series-level "
                              "decision, and stated that the review it had run could not be called exhaustive."),
  "what_this_lane_found": ("That artifact did not have this directory's terminal precedent, which was not in the flat "
                           "level it triaged. The Winrock exclusion decides those records on the substance test "
                           "without needing the minutes question answered at all: the Trails agendas in this directory "
                           "have exactly the same structure as the ones held there, listing Resolutions 2014-01 "
                           "through 2014-03 and containing none of them."),
  "recommended_revision": ("Resolve the six Trails PID agendas to excluded on the substance test, citing "
                           f"{PRECEDENT}. The Local Government Coordinating Commission agenda should be checked "
                           "against the same test before being resolved the same way, since this lane did not fetch "
                           "it. This removes six of the seven requires-human-review rows that artifact raised, and "
                           "removes the series decision it asked for."),
  "claude_did_not_modify": "Those records remain as that artifact left them. This is a recommendation to the integration lane, not a change.",
 },
 "bodies_represented": {
  "note": "Nine distinct public bodies across eighteen excluded agendas, which is why the directory looks miscellaneous. Counted by body, not by masthead wording: the City writes Mesa del Sol Public Improvement District(s) both ways.",
  "counts": dict(bodies),
  "observation": ("Six of the nine are tax increment or public improvement district boards, seated by the Council and "
                  "administered in several cases by an outside law firm whose document-management stamps survive in "
                  "the filenames. They meet to adopt open-meetings policies, approve bylaws and quarterly reports, and "
                  "receive foreclosure and settlement updates. The substance of that work is in their resolutions and "
                  "reports, none of which this directory holds."),
 },
 "duplicate_and_supersession_checks": {
  "internal_byte_collisions": 0,
  "cross_inventory_byte_collisions": 0,
  "url_collisions_in_this_directory": 0,
  "checksums_compared_against": 1612,
  "relationships_found_by_hash": 0,
  "relationships_found_by_normalized_text": 1,
  "note": ("One relationship and hashing misses it by 177 bytes. The March 7 2014 Council study session agenda is "
           "published in this directory and in the police-oversight directory with identical normalized text and "
           "different encodings. This is the second cross-directory pair in the Council tree found only by text "
           "comparison, after the DOJ findings letter, and the third distinct near-miss size: 177 bytes here against "
           "a fivefold difference for O-03-132 and a complete byte divergence for the DOJ scan."),
 },
 "integration_flags": [
  {"severity": "revises-earlier-artifact",
   "affects": ["project-state/discovery/council-documents-cluster-research-2026-09-11.json"],
   "finding": "Six Trails PID agendas held there at requires human review are decided by this directory's terminal precedent, which that lane had not seen.",
   "recommended_action": "Apply the revision in revises_an_earlier_recommendation. It closes six requires-human-review rows and the series decision that artifact requested."},
  {"severity": "identification",
   "affects": ["src-1f47a1d06392eecc"],
   "finding": "The one retainable record in the directory has no text layer and an inventory title that is just its filename. It contains an adopted Open Meetings Act notice resolution and was found only by rendering.",
   "recommended_action": "Title it for the resolution it contains, not for the agenda on its first page. It is the fourth record in this run whose identity was recoverable only by rendering an image-only PDF."},
  {"severity": "filename-trap",
   "affects": ["src-d810ef001941f846"],
   "finding": "A file named and inventoried as a Hunt board agenda is a Quorum at ABQ Uptown Tax Increment Development District agenda on its masthead. The filename carries an outside law firm's document-management stamp and a client name, not the name of the body that met.",
   "recommended_action": "Cite the masthead. Where a filename carries a third-party document-management prefix such as BHFSDOCS, treat the rest of the filename as that firm's internal labelling rather than a description."},
  {"severity": "cross-artifact",
   "affects": ["src-d5cfa0fec162e3c1", "src-ff9893ec1cd700be"],
   "finding": "The March 7 2014 study session agenda is the same document in two Council directories; the canonical is held at requires human review in the police-oversight artifact.",
   "recommended_action": "Integrate the two artifacts together so the study-session minutes question is answered once."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "excluded": counts["excluded"],
  "superseded": 0, "requires_human_review": 0,
  "distinct_public_bodies_in_excluded_agendas": len(bodies),
 },
 "link_check": {"checked": 20, "http_200": 20, "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-11.",
                "containers_verified": "19 genuine PDFs and one HTML collection page by leading bytes. One PDF has no text layer and was rendered."},
 "approved_for_addition": approved,
 "duplicate": duplicates,
 "excluded": excluded,
 "archival_note": f"The single approved record is a static PDF and is inventory-only until an R2 archive object exists and its public download, exact size, SHA-256, and authoritative-source provenance are verified. Archive footprint if authorized: {sum(r['size_bytes'] for r in approved):,} bytes.",
 "integration_note": "Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Eighteen rows are excluded on the substance test and each names the terminal record that supplies it, so the ground is traceable rather than asserted. The single duplicate row's canonical lies in the police-oversight artifact of the same date and is itself at requires human review. The one approved row carries a title, a 20-to-50-word description, a proposed_canonical_page and a cross_listing. This artifact raises no requires-human-review row and, in revises_an_earlier_recommendation, proposes closing six raised by an earlier one. Sizes and checksums are first measurements; the inventory held neither.",
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
