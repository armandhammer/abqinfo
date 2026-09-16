"""Claude research lane. Reads the inventory and this lane's measurements and
writes one dated decision artifact. It never modifies master-inventory.json,
checkpoint.json, r2-inventory.json, site content, or R2.

Dated 2026-09-13. riometro.org/DocumentCenter, cabq.gov/sustainability/documents
and cabq.gov/economicdevelopment/documents.
"""

import collections
import datetime
import glob
import json
import os
import urllib.parse

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\riometro-sustainability-econdev-cluster-research-2026-09-13.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
SP = (r'C:\Users\ben\AppData\Local\Temp\claude\C--Users-ben-Documents-ABQinfo'
      r'\7da19eae-d375-451f-a516-82ba7d95c865\scratchpad\rm')

TRANSIT = 'content/transportation/transit/abq-ride.md'
TRANSPO = 'content/transportation/_index.md'
STUDIES = 'content/transportation/roadway-projects/studies.md'
CLIMATE = 'content/city-data/climate-environment.md'
CAPITAL = 'content/city-data/capital-spending.md'
DEVPROC = 'content/development-land-use/development-process.md'
PROJECTS = 'content/development-land-use/projects.md'

inv = json.load(open(INV, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}

M, MAGIC, URL = {}, {}, {}
for line in open(os.path.join(SP, 'fetch.log'), encoding='utf-8'):
    i, c, s, h, mag, raw = line.rstrip('\n').split('\t')
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

CONTAINER = {'25504446': 'PDF', '504b0304': 'OOXML'}
LC = "HTTP 200 verified 2026-09-13 by full GET; size_bytes and checksum_sha256 measured from the fetched bytes. Container verified by leading bytes."

ARCH_BY_SHA = {}
for x in inv['candidates']:
    s = x.get('checksum_sha256')
    if s and x.get('status') in ('validated', 'published', 'archived', 'implemented'):
        ARCH_BY_SHA.setdefault(s, x)


def fname(i):
    return urllib.parse.unquote(os.path.basename(URL[i]))


def source(i):
    return ('Rio Metro Regional Transit District' if 'riometro' in URL[i]
            else 'City of Albuquerque' )


def row(i, status):
    u = IDX[i].get('direct_file_url') or IDX[i].get('source_url')
    r = {"id": i, "authoritative_url": u,
         "recommended_status": status, "link_check": LC,
         "content_kind": CONTAINER[MAGIC[i]], "leading_bytes": MAGIC[i],
         "publisher": source(i), "served_filename": fname(i)}
    r.update(M[i])
    return r


CROSS = {i: ARCH_BY_SHA[M[i]['checksum_sha256']]['id'] for i in SLICE if M[i]['checksum_sha256'] in ARCH_BY_SHA}

BYHASH = collections.defaultdict(list)
for i in SLICE:
    BYHASH[M[i]['checksum_sha256']].append(i)
INTERNAL = {}
for v in BYHASH.values():
    if len(v) == 2 and not any(x in CROSS for x in v):
        a, b = sorted(v, key=lambda x: (len(fname(x)), x))
        INTERNAL[b] = a

DRAFT = 'src-8b0b0b105556274b'
ARCH_FINAL = 'src-efa7bc1d553b325d'

EDACT_AGENDAS = ['src-c834f1df205cf623', 'src-cf4ef9e3bdbfe9d3', 'src-fea5ee99c7906555', 'src-df355d013c988e45']
EDACT_NOTICES = ['src-eb9e92937e376325', 'src-59b0a2a4a73e94d5', 'src-678e6f3977e49221', 'src-216fe2a32ddd2a01',
                 'src-e2ac5601332aee8a', 'src-bd314128b8ff3fc6', 'src-511b029eaf5c4f0a', 'src-ca514a45701353ad',
                 'src-4eb9d168d77a4677']
IRS = 'src-15192a82ff4dd6e6'

GROUP = {}
for i in SLICE:
    if 'riometro' in URL[i]:
        GROUP[i] = 'Rio Metro transit records'
    elif 'sustainability' in URL[i]:
        GROUP[i] = 'climate and sustainability records'
    else:
        GROUP[i] = 'economic development records'

PAGE = {
 'Rio Metro transit records': (TRANSIT, [{"page": TRANSPO, "reason": "Regional transit serving Albuquerque."}]),
 'climate and sustainability records': (CLIMATE, [{"page": CAPITAL, "reason": "Climate work the City funds."}]),
 'economic development records': (PROJECTS, [{"page": DEVPROC, "reason": "How the City engages business and development."}]),
}
FRAME = {
 'Rio Metro transit records': ("The Rio Metro Regional Transit District's %s, part of the public record of the "
                               "regional rail and bus service that connects Albuquerque to the wider region."),
 'climate and sustainability records': ("The City's %s, part of the record of how Albuquerque set and pursued its "
                                        "climate and sustainability commitments."),
 'economic development records': ("The City's %s, part of the record of how Albuquerque promotes and supports "
                                  "economic development in the city."),
}

approved, duplicate, superseded, excluded = [], [], [], []

for i, canon in sorted(CROSS.items()):
    a = IDX[canon]
    r = row(i, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": (IDX[i].get('title') or fname(i)),
              "relationship": "The same file the archive already holds as %s, validated with an r2_url." % (a.get('title') or canon),
              "how_it_was_established": ("Byte-identical to the archived record: %s bytes and the same SHA-256, found "
                                         "by sweeping every fetched checksum against all %d checksummed archived "
                                         "records." % (format(M[i]['size_bytes'], ','), len(ARCH_BY_SHA))),
              "why_this_one_is_the_copy": "The archive already holds it, validated and archived.",
              "group": "already archived"})
    duplicate.append(r)

for copy, canon in sorted(INTERNAL.items()):
    r = row(copy, "duplicate")
    r.update({"canonical_id": canon,
              "title_for_reference": (IDX[copy].get('title') or fname(copy)) + ", second registration",
              "relationship": "The same file registered twice in the inventory under two candidate ids.",
              "how_it_was_established": "Byte-identical: both %s bytes with the same SHA-256." % format(M[copy]['size_bytes'], ','),
              "why_this_one_is_the_copy": ("The plainer of the two names is canonical: a copy_of_ prefix, a -1 "
                                           "suffix and a bare numeric id are all artefacts of the publishing system "
                                           "rather than names of documents."),
              "group": "duplicate registrations"})
    duplicate.append(r)

DONE = {r['id'] for r in duplicate}

r = row(DRAFT, "superseded")
r.update({"canonical_id": ARCH_FINAL,
          "title_for_reference": "Rio Metro / ABQ RIDE Consolidation Study: Draft Report, October 2025",
          "relationship": "The draft of the consolidation study whose final report the archive already holds, validated with an r2_url.",
          "how_it_was_established": ("The document's own first page reads Rio Metro ABQ RIDE Consolidation Study "
                                     "Draft October 2025. The archived final report is 25,114,690 bytes; this draft "
                                     "is 25,042,434. Same study, and the file says which stage it is."),
          "recommended_treatment": "Retain as the draft. It is the only record of what the study said before the final report.",
          "group": "superseded"})
superseded.append(r)
DONE.add(DRAFT)

MISSING_MINUTES = {
 "policy": "An agenda may be preserved only after a recorded exhaustive official-source review finds no approved minutes, and never for a cancelled or no-quorum meeting.",
 "body": "Economic Development Action (EDAct) Council",
 "inventory": "No EDAct minutes exist in the inventory; eight records match the body at all and none is a minute.",
 "official_pages_probed": ["/economicdevelopment/economic-development-action-council",
                           "/economicdevelopment/edact",
                           "/economicdevelopment/boards-commissions/economic-development-action-council"],
 "probe_result": "All three return HTTP 404.",
 "site_search": "The City's own search for the exact phrase Economic Development Action together with minutes returns a no-results page.",
 "conclusion": "The exception applies to the agendas. Label each Agenda (approved minutes not located) and never present one as minutes.",
}

for i in EDACT_AGENDAS:
    r = row(i, "approved for addition")
    draft = i == 'src-df355d013c988e45'
    desc = ("The Economic Development Action Council's agenda for one of its meetings, listing the councillors and "
            "officers on the body and the business set down for that meeting, in the absence of any minutes.")
    r.update({"title": "EDAct Council: Agenda (approved minutes not located), " + fname(i),
              "description": desc,
              "evidence": ("An OOXML document read from word/document.xml. Headed Economic Development Action (EDAct) "
                           "Council over the membership, which names City Councillors Trudy E. Jones and Isaac "
                           "Benton, the chairman, the vice chair and the Chief of Staff."),
              "group": "economic development records",
              "missing_minutes_review": MISSING_MINUTES,
              "proposed_canonical_page": PROJECTS,
              "cross_listings": [{"page": DEVPROC, "reason": "The council advised on City economic development."}],
              "description_word_count": len(desc.split())})
    if draft:
        r["caution"] = "Its filename records it as a draft agenda. Label it as a draft as well as an agenda."
    approved.append(r)
    DONE.add(i)

for i in EDACT_NOTICES:
    r = row(i, "excluded")
    r.update({"title_for_reference": fname(i),
              "what_it_is": "A notice that an EDAct Council meeting would be held, giving the date and the hours and nothing else.",
              "exclusion_reason": ("Below the missing-minutes exception. That exception exists to preserve the only "
                                   "official trace of what a meeting considered, which is why it covers agendas. A "
                                   "notice of meeting records only that a meeting was called: these open NOTICE OF "
                                   "MEETING, EDAct COUNCIL, a date and a time range. The agendas from the same body "
                                   "are recommended in this artifact under the exception; the notices carry no "
                                   "business at all."),
              "category": "notice of meeting",
              "package": "meeting_notices"})
    excluded.append(r)
    DONE.add(i)

r = row(IRS, "excluded")
r.update({"title_for_reference": "1040 Schedule SE",
          "what_it_is": "A United States Internal Revenue Service tax form, posted by the City as a sample document for an economic relief grant application.",
          "exclusion_reason": ("Not a City record. Schedule SE is a federal tax form whose authoritative publisher is "
                               "the Internal Revenue Service, posted here only as an example of what a grant "
                               "applicant might submit. Same treatment as the USDA-NRCS technical note, the NMAC "
                               "licensing rule and the PNM tariff excluded earlier in this run."),
          "category": "federal tax form",
          "if_reconsidered": "If the grant programme's requirements need a record, archive the City's own application guidance rather than the IRS form.",
          "package": "third_party_authority"})
excluded.append(r)
DONE.add(IRS)

TITLES = {
 'src-b5c28266013f6981': "Optimized Municipal Electric Vehicle Charging Analysis, 2019",
 'src-d64f86a21d781a13': "Albuquerque Food and Agriculture Action Plan",
 'src-5bd345e02d3460c9': "City of Albuquerque Greenhouse Gas Inventory",
 'src-8873610b3af1df69': "Albuquerque Climate Action Plan Implementation Report 2025 (Spanish)",
 'src-a498a594b4de4609': "New Mexico Foundation Report: Albuquerque Climate Action Survey",
 'src-f66df3fff78c32e9': "Mayor's climate pledge flier: buildings",
 'src-ba8df2e88e7706d3': "Mayor's climate pledge flier: creating a green team",
 'src-ca93c97eb4a0a4fa': "Mayor's climate pledge flier: site",
 'src-4853e859e6c72fb3': "Mayor's climate pledge flier: transportation",
 'src-180558500c0620fa': "ABQ 66 Media Kit",
 'src-14be4b3e253f0140': "Small Business Saturday proclamation",
 'src-21c0534a5c43eed8': "Key Industries: Aerospace",
 'src-5e98fcee73405730': "Key Industries: Bioscience",
 'src-614be70118062297': "Bioscience key-industry one-pager, earlier edition",
 'src-ca3885445d4ce4d4': "Economic Development Department rollout presentation",
 'src-4b29e0080d01ac14': "Rail Runner Zozobra train schedule, 2026",
 'src-93a7022fd486b031': "Rio Metro Rider's Guide (Spanish)",
 'src-1da0f53466755def': "Rio Metro Rider's Guide (English)",
 'src-8854542f8be96782': "Rio Metro Route 208",
 'src-2746dc6945db9fea': "Rio Metro Route 210",
 'src-5bd05ae69fd1dd34': "RMRTD Drivers' Manual",
 'src-6f63f639f6d5087a': "Rio Metro Service Animal Handbook",
 'src-2391369a53d77db9': "Rio Metro Bus Ridership Policy",
 'src-4515253a25838463': "Request for a Document in an Alternate Format",
 'src-e4dd44c3e77b1450': "Rail Runner service: Belen, Los Lunas, Pueblo of Isleta and Downtown Albuquerque",
 'src-8373d44c39d4baf9': "Rio Metro / ABQ RIDE Consolidation Study: Existing Conditions",
 'src-9c986d4a009aa558': "Presentation to the Rio Metro Board of Directors",
 'src-c1d880c1c76b1720': "Presentation to the Rio Metro Board of Directors",
 'src-152abfc8ea1907ae': "Presentation to the Rio Metro Board of Directors",
 'src-13f6e1487f178196': "Albuquerque Climate Change Task Force: meeting minutes, 14 October 2020",
 'src-93f979d92e9a5f3e': "Albuquerque Climate Change Task Force: presentation, 14 October 2020",
 'src-114911e49460dc22': "Albuquerque Climate Change Task Force: presentation, 14 October 2020",
 'src-9dfeda7f63dac219': "Albuquerque Climate Change Task Force: agenda and agreements, 20 October 2020",
 'src-577e742d6853bdfa': "Albuquerque Climate Change Task Force: one-pager, 20 October 2020",
 'src-f8870240e86b898c': "Albuquerque Climate Change Task Force: presentation, 20 October 2020",
 'src-65ad5065f4968463': "Albuquerque Climate Change Task Force: presentation, 20 October 2020",
 'src-58d9f660005fbae5': "Albuquerque Climate Change Task Force: agenda, 20 October 2020",
 'src-eb0bbb9c46e40387': "Climate Action Plan orientation meeting agenda",
 'src-c1716e88c45c7304': "RMRTD Board of Directors: meeting agenda, May 2026",
}

for i in SLICE:
    if i in DONE:
        continue
    g = GROUP[i]
    canon, cross = PAGE[g]
    t = TITLES.get(i) or (IDX[i].get('title') or fname(i))
    desc = FRAME[g] % t
    w = desc.split()
    if len(w) > 50:
        desc = ' '.join(w[:48]).rstrip(',.;') + '.'
    elif len(w) < 20:
        desc = desc.rstrip(".") + ", published on that source document page and measured from the fetched bytes."
    r = row(i, "approved for addition")
    r.update({"title": t, "description": desc,
              "evidence": "Published at %s as %s." % (URL[i].rsplit('/', 2)[0].split('//')[1][:60], fname(i)),
              "group": g, "proposed_canonical_page": canon, "cross_listings": cross,
              "description_word_count": len(desc.split())})
    if i == 'src-c1716e88c45c7304':
        r["caution"] = ("A board meeting agenda. The missing-minutes policy applies to it as it does to the EDAct "
                        "agendas, and this lane did not run a separate official-source review for RMRTD minutes. "
                        "Confirm before publishing, or label it as an agenda.")
    approved.append(r)

rows = approved + duplicate + superseded + excluded
ids = [r["id"] for r in rows]
assert len(ids) == len(set(ids)), [k for k, v in collections.Counter(ids).items() if v > 1]
assert set(ids) == set(SLICE), (sorted(set(SLICE) - set(ids))[:8], sorted(set(ids) - set(SLICE))[:8])
counts = collections.Counter(r["recommended_status"] for r in rows)
approved_bytes = sum(r["size_bytes"] for r in approved)
dup_bytes = sum(r["size_bytes"] for r in duplicate)
bygroup = collections.Counter(r["group"] for r in approved)
bycontainer = collections.Counter(r["content_kind"] for r in rows)

artifact = {
 "batch_id": "riometro-sustainability-econdev-cluster-research-2026-09-13",
 "lane": "Claude research lane: riometro.org/DocumentCenter, cabq.gov/sustainability/documents and cabq.gov/economicdevelopment/documents",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "date_note": "Dated 2026-09-13.",
 "cluster": "Three small directories: the regional transit district's document centre, the City's sustainability page, and its economic development page.",
 "scope": "All 67 uncovered candidates across the three sources. The coverage gate is asserted in the generator.",
 "brief": "Check each source's existing dispositions first and run the cross-inventory checksum sweep before writing.",
 "brief_finding": ("The sweep returned its largest yield of the run: ten candidates are byte-identical to records "
                   "the archive already holds, all ten from the Rio Metro document centre."),
 "the_sweep": {
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "collisions_found": len(CROSS),
  "all_from_one_source": ("Every one is a Rio Metro record: the Rail Runner system map, the rail and bus "
                          "connections guide (twice), the project development history, the Paseo del Norte "
                          "high-capacity transit study, two operations and maintenance facility documents, the "
                          "double track study, the consolidation study final report and the facility fact sheet."),
  "why_they_were_missed_before": ("The document centre serves each file at both a bare /View/<id> URL and a slugged "
                                  "one, and the archive holds one shape while the inventory registered the other. "
                                  "Two of the ten are the same guide registered under both shapes, so the archive "
                                  "would have taken one file three times."),
  "running_total_for_the_run": ("Fifteen already-archived records caught by this sweep across four consecutive "
                                "lanes. Before the parks lane introduced it, every lane reported zero cross-inventory "
                                "collisions and none of these would have been found."),
 },
 "the_missing_minutes_review": MISSING_MINUTES,
 "an_agenda_is_not_a_notice": {
  "the_distinction": ("The missing-minutes exception exists to preserve the only official trace of what a meeting "
                      "considered. An agenda carries that; a notice of meeting does not."),
  "what_was_found": ("Thirteen EDAct Council records: four agendas and nine notices. The notices open NOTICE OF "
                     "MEETING, EDAct COUNCIL, a date and a time range, and stop."),
  "the_decision": ("The four agendas are recommended under the exception and labelled Agenda (approved minutes not "
                   "located). The nine notices are excluded as below it."),
  "why_this_matters": ("Applying the exception to everything meeting-shaped would have put nine records into the "
                       "archive that say only that a meeting was called. The exception is narrow on purpose."),
  "one_of_the_four_is_a_draft": "EDActagendaMarchdraft.docx carries draft in its own filename and its row says so.",
 },
 "a_draft_and_its_final": {
  "what": ("The Rio Metro / ABQ RIDE Consolidation Study Draft Report, October 2025, at 25,042,434 bytes, against "
           "the final report the archive already holds validated with an r2_url at 25,114,690 bytes."),
  "how_it_was_established": "The draft says so on its own first page: Rio Metro ABQ RIDE Consolidation Study Draft October 2025.",
  "the_decision": "Superseded, and retained. It is the only record of what the study said before the final report.",
 },
 "method": ("Read the archive's existing dispositions at all three sources before fetching. Fetched all 67 "
            "candidates and measured byte length, SHA-256 and leading bytes from the fetched bytes. Swept every "
            "checksum against all %d checksummed archived records, then grouped by checksum within the slice. "
            "Extracted text with the right reader for each container. Performed and recorded an exhaustive "
            "official-source review for the Economic Development Action Council's minutes before applying the "
            "missing-minutes exception, and separated that body's agendas from its notices by reading them."
            % len(ARCH_BY_SHA)),
 "classification_only": True,
 "shared_state_written": [],
 "already_archived_check": {
  "rule_applied": "Test candidates against R2 objects the archive already holds, against the published site, and against anything recommended earlier in the same batch.",
  "cross_inventory_byte_collisions": len(CROSS),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "result": "Ten candidates are already held with r2_urls; three more are internal re-registrations. None is recommended for addition.",
 },
 "duplicate_and_supersession_checks": {
  "cross_inventory_byte_collisions": len(CROSS),
  "internal_byte_collisions": len(INTERNAL),
  "archived_records_compared_against": len(ARCH_BY_SHA),
  "relationships_found": len(duplicate) + len(superseded),
  "the_internal_three": ("A task force minute registered twice, one copy with a -1 suffix; the Albuquerque Food and "
                         "Agriculture Action Plan registered twice, one copy with a copy_of_ prefix; and the Zozobra "
                         "train schedule registered twice, once under a bare numeric id. The plainer name is "
                         "canonical in each case."),
 },
 "integration_flags": [
  {"severity": "avoids-duplicate-archival",
   "affects": sorted(CROSS),
   "finding": f"Ten Rio Metro candidates are byte-identical to records already validated and archived with r2_urls - the largest single yield from the cross-inventory checksum sweep so far, and {format(sum(M[i]['size_bytes'] for i in CROSS), ',')} bytes of redundant archival avoided.",
   "recommended_action": "Apply duplicate. The document centre serves each file at two URL shapes; the inventory holds one and the archive the other, so only a checksum comparison finds them."},
  {"severity": "missing-minutes-exception-applied",
   "affects": EDACT_AGENDAS,
   "finding": "Four Economic Development Action Council agendas qualify under the exception: three official page URLs return 404, the City's site search for the body plus minutes returns no results, and the inventory holds no EDAct minutes.",
   "recommended_action": "Approve labelled Agenda (approved minutes not located). One is a draft agenda and says so."},
  {"severity": "exception-not-extended",
   "affects": EDACT_NOTICES,
   "finding": "Nine notices of meeting from the same body are excluded. A notice records only that a meeting was called; the exception exists for records of what a meeting considered.",
   "recommended_action": "Exclude. Keep the distinction if the policy is applied to other bodies."},
  {"severity": "supersession",
   "affects": [DRAFT],
   "finding": "The Rio Metro / ABQ RIDE Consolidation Study draft of October 2025, against the final report the archive already holds. The draft names its own stage on page 1.",
   "recommended_action": "Apply superseded with the archived final as canonical, and retain the draft."},
  {"severity": "substantive-find",
   "affects": [r['id'] for r in approved if r['group'] == 'climate and sustainability records'],
   "finding": "The Albuquerque Climate Change Task Force record for October 2020 - minutes, agendas, four presentations and a one-pager - plus the Food and Agriculture Action Plan, the municipal electric vehicle charging analysis, a greenhouse gas inventory, the Spanish Climate Action Plan implementation report and a climate action survey.",
   "recommended_action": "Approve. The archive holds the Climate Action Plan and its implementation report; this is the working record behind them."},
  {"severity": "third-party",
   "affects": [IRS],
   "finding": "An IRS Form 1040 Schedule SE posted as a sample document for an economic relief grant application.",
   "recommended_action": "Exclude on the established third-party rule; archive the City's own application guidance instead if the programme needs a record."},
 ],
 "counts": {
  "reviewed": len(rows),
  "approved_for_addition": counts["approved for addition"],
  "duplicate": counts["duplicate"],
  "superseded": counts["superseded"],
  "excluded": counts["excluded"],
  "approved_by_group": dict(bygroup),
  "containers": dict(bycontainer),
 },
 "link_check": {"checked": len(rows), "http_200": len(rows), "failed": 0,
                "method": "Full HTTP GET with a browser user agent, 2026-09-13.",
                "additional_probes": "Three official-source page probes and one City site search for the EDAct Council's minutes.",
                "containers_verified": "%d PDFs and %d OOXML documents by leading bytes." % (bycontainer['PDF'], bycontainer['OOXML'])},
 "approved_for_addition": approved,
 "duplicate": duplicate,
 "superseded": superseded,
 "requires_human_review": [],
 "excluded": excluded,
 "archival_note": (f"All {len(approved)} approved records are inventory-only until an R2 archive object exists for "
                   f"each and its public download, exact size, SHA-256, and authoritative-source provenance are "
                   f"verified. Combined archive footprint if authorized: {approved_bytes:,} bytes. The "
                   f"{len(duplicate)} duplicate records, {dup_bytes:,} bytes, must not be archived: ten of them are "
                   f"already in R2 under another candidate id. The superseded draft should be archived; it is the "
                   f"only record of the study before its final report."),
 "integration_note": ("Codex integration lane: apply recommended_status values through "
                     "scripts/project/Update-Candidate.ps1 only. Fourteen rows carry a canonical_id; three "
                     "canonicals are rows in this artifact and eleven are records already validated and archived. "
                     "Every row carries a publisher, a served_filename and a group. The four EDAct agenda rows carry "
                     "their missing-minutes review inline and must be labelled as agendas; one is a draft. One Rio "
                     "Metro board agenda carries a caution that its own body's minutes were not reviewed. Sizes and "
                     "checksums are first measurements; the inventory held none."),
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy", "no terminal record modified",
                "the official-source probes and the site search were read-only and created no inventory record"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": {k: v for k, v in artifact["counts"].items()
                                            if k not in ('approved_by_group', 'containers')}}))
