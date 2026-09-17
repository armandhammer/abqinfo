"""Claude research lane. Inventory-wide audit of records sharing one URL.

Reads master-inventory.json and checkpoint.json and writes one dated decision
artifact. It never modifies master-inventory.json, checkpoint.json,
r2-inventory.json, site content, or R2, and it creates no inventory record.

Prompted by the councilor-district-2 cluster, where twelve URLs in one directory
were found to carry twenty-six records.
"""

import collections
import datetime
import json
import os

OUT = r'C:\Users\ben\Documents\ABQinfo\project-state\discovery\inventory-url-collision-audit-2026-09-11.json'
INV = r'C:\Users\ben\Documents\ABQinfo\project-state\master-inventory.json'
CKPT = r'C:\Users\ben\Documents\ABQinfo\project-state\checkpoint.json'

DOC_EXT = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.kmz')

# One URL is a live web application, not a document. 229 distinct transportation
# projects are catalogued against it. Counting it as a collision would be wrong
# and would have inflated every figure in this artifact roughly fivefold.
LIVE_SERVICE_URLS = {'https://mrmpo.nm.tipviewer.pmgpro.com'}

inv = json.load(open(INV, encoding='utf-8'))
ckpt = json.load(open(CKPT, encoding='utf-8'))
IDX = {x['id']: x for x in inv['candidates']}


def norm(u):
    return (u or '').replace('/view', '').rstrip('/')


def url_of(x):
    return norm(x.get('direct_file_url') or x.get('source_url') or '')


by_url = collections.defaultdict(list)
for x in inv['candidates']:
    u = url_of(x)
    if u.startswith('http') and u not in LIVE_SERVICE_URLS:
        by_url[u].append(x['id'])

multi = {u: r for u, r in by_url.items() if len(r) > 1}
doc_multi = {u: r for u, r in multi.items() if u.lower().endswith(DOC_EXT)}

excess_all, excess_doc = collections.Counter(), collections.Counter()
for u, r in multi.items():
    c = collections.Counter(IDX[i]['status'] for i in r)
    for s, n in c.items():
        if n > 1:
            excess_all[s] += n - 1
            if u in doc_multi:
                excess_doc[s] += n - 1


def recs(r):
    return [{"id": i, "status": IDX[i]['status'], "title": (IDX[i].get('title') or '')[:80],
             "checksum_sha256": IDX[i].get('checksum_sha256'), "size_bytes": IDX[i].get('size_bytes')}
            for i in r]


pending_groups, pending_only_groups, multi_terminal, conflicts = [], [], [], []
for u, r in sorted(doc_multi.items()):
    rr = recs(r)
    g = {"url": u, "record_count": len(rr), "records": rr}
    has_pending = any(x['status'] == 'pending review' for x in rr)
    has_terminal = any(x['status'] != 'pending review' for x in rr)
    if has_pending and has_terminal:
        pending_groups.append(g)
    elif has_pending:
        pending_only_groups.append(g)
    if sum(1 for x in rr if x['status'] in ('validated', 'implemented')) > 1:
        multi_terminal.append(g)
    cs = {x['checksum_sha256'] for x in rr if x['checksum_sha256']}
    if len(cs) > 1:
        conflicts.append(g)

twin_status = collections.Counter()
for g in pending_groups:
    for x in g['records']:
        if x['status'] != 'pending review':
            twin_status[x['status']] += 1

size_dist = collections.Counter(len(r) for r in doc_multi.values())

artifact = {
 "batch_id": "inventory-url-collision-audit-2026-09-11",
 "lane": "Claude research lane: inventory-wide audit of records sharing one URL",
 "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "type": "inventory audit, not a cluster triage",
 "why_this_exists": (
  "The councilor-district-2 cluster triaged on the same date turned up twelve URLs in one directory carrying "
  "twenty-six inventory records between them, including three URLs with two validated records each. Seven of the "
  "extra records were still pending and their disposition was already settled by an excluded twin. That is a "
  "detection method no earlier lane in this run had used, and it costs nothing to run inventory-wide, so this "
  "artifact does."),
 "method": (
  "Grouped all 7,074 inventory candidates by their direct_file_url, falling back to source_url, with a trailing "
  "/view and any trailing slash stripped. No fetching, no hashing, no text extraction: two records pointing at one "
  "URL are one document by definition. Then separated the groups whose URL ends in a document extension from those "
  "whose URL is a page or service, because only the former are necessarily one document."),
 "classification_only": True,
 "shared_state_written": [],
 "creates_no_inventory_record": True,
 "false_positive_excluded": {
  "url": sorted(LIVE_SERVICE_URLS)[0],
  "records": 231,
  "what_it_is": ("The Mid-Region Metropolitan Planning Organization TIP Viewer, a live web application. 229 distinct "
                 "transportation projects are catalogued against this single application URL, plus one validated "
                 "record for the viewer itself and one duplicate."),
  "why_it_is_not_a_collision": ("These are different projects, not different records of one document. The repository "
                                "already treats live official services as a category of their own, exempt from the "
                                "archival rule, and this is that category behaving normally."),
  "impact_of_not_excluding_it": ("A first pass that counted it reported 296 excess records. Excluding it, the real "
                                 "figure is 68. Every headline number in this artifact would have been wrong by "
                                 "roughly a factor of four. Any future run of this audit must exclude live-service "
                                 "URLs before reporting."),
 },
 "findings": {
  "distinct_urls": len(by_url),
  "urls_with_more_than_one_record": len(multi),
  "records_in_those_groups": sum(len(r) for r in multi.values()),
  "document_urls_with_more_than_one_record": len(doc_multi),
  "records_in_document_groups": sum(len(r) for r in doc_multi.values()),
  "excess_records_beyond_one_per_url": {
   "all_urls": dict(excess_all), "all_urls_total": sum(excess_all.values()),
   "document_urls_only": dict(excess_doc), "document_urls_total": sum(excess_doc.values()),
  },
  "document_group_size_distribution": {str(k): v for k, v in sorted(size_dist.items())},
  "scale_note": ("68 excess records against 7,074 candidates is a small defect rate, and the finding is not that the "
                 "inventory is broadly unreliable. It is that a cheap check nobody was running catches a real class "
                 "of error, and that two of the affected numbers are ones the project reports."),
 },
 "effect_on_reported_counts": {
  "source": "project-state/checkpoint.json counts_by_status, recorded 2026-09-11T19:15:00Z",
  "validated": {"reported": ckpt['counts_by_status']['validated'],
                "excess_on_document_urls": excess_doc['validated'],
                "on_a_one_record_per_document_basis": ckpt['counts_by_status']['validated'] - excess_doc['validated']},
  "excluded": {"reported": ckpt['counts_by_status']['excluded'],
               "excess_on_document_urls": excess_doc['excluded'],
               "on_a_one_record_per_document_basis": ckpt['counts_by_status']['excluded'] - excess_doc['excluded']},
  "pending_review": {"reported": ckpt['counts_by_status']['pending review'],
                     "excess_on_document_urls": excess_doc['pending review'],
                     "note": (f"{excess_doc['pending review']} pending records are second records for a document another pending "
                              f"record already covers. Separately, {len(pending_groups)} document groups carry a pending "
                              f"record whose twin is already terminal; those are not excess pending records, they are "
                              f"pending records with a settled answer.")},
  "honest_reading": ("The validated count is overstated by 16 on a one-record-per-document basis, about 1.2 per cent. "
                     "That is small but it is the number the project reports as its archive size, so it is worth "
                     "stating correctly rather than leaving to be rediscovered."),
 },
 "actionable_now": {
  "headline": f"{len(pending_groups)} document URLs carry a pending record alongside a record that is already terminal.",
  "why_it_matters": ("Each of these is a pending record whose disposition is already decided, because the other record "
                     "is the same file. They need no fetching, no measurement and no judgement: they inherit. At "
                     "roughly four per cluster they are the cheapest pending records in the inventory to clear."),
  "twin_status_breakdown": dict(twin_status),
  "recommended_rule": ("Where a pending record shares a normalised document URL with a terminal record, recommend it "
                       "duplicate with the terminal record as canonical, and carry the canonical's reasoning across "
                       "rather than re-deriving it. Recording it as a duplicate rather than silently re-applying the "
                       "twin's status preserves the fact that the inventory double-counted one document."),
  "worked_example": ("The councilor-district-2 artifact of the same date applies exactly this rule to seven records, "
                     "each a Complete Streets letter of support titled once from the organisation that wrote it and "
                     "once from the link text on the Council page."),
  "groups": pending_groups,
 },
 "pending_pairs_still_needing_triage": {
  "headline": f"{len(pending_only_groups)} document URLs carry two pending records and no terminal record.",
  "why_separated": ("These are not a cheap win and must not be confused with the group above. Neither record has a "
                    "disposition to inherit, so the document still needs triaging on its merits. What the collision "
                    "gives is a saving of effort, not an answer: triage the document once and apply the result to both "
                    "records rather than fetching and measuring it twice."),
  "recommended_rule": ("Collapse each pair to one record at triage time: classify one on the merits and recommend the "
                       "other duplicate against it. Whichever cluster lane reaches the URL first should do this rather "
                       "than leaving the second record for a later lane that will redo the work."),
  "groups": pending_only_groups,
 },
 "needs_codex_adjudication": {
  "headline": f"{len(multi_terminal)} document URLs carry more than one validated or implemented record.",
  "why_this_lane_cannot_decide_it": ("Every record in these groups is already terminal, and the coordination rules "
                                     "reserve terminal records to the integration lane. Claude modified none of them."),
  "the_ambiguity_to_resolve_first": ("Some pairs are validated plus implemented, which may be deliberate if the project "
                                     "distinguishes an inventory record from a site-placement record. Others are "
                                     "validated plus validated, which is harder to read as intentional. Decide what a "
                                     "validated-and-implemented pair means before treating any of these as errors, "
                                     "because that decision determines how many of the 135 are real."),
  "groups": multi_terminal,
 },
 "checksum_conflicts": {
  "headline": f"{len(conflicts)} document URLs carry records with different recorded checksums.",
  "why_it_matters": ("These are the only groups where the records are not merely duplicated but disagree about what "
                     "the file is. One URL served different bytes at different capture times, which is a currency "
                     "question rather than a hygiene one."),
  "groups": conflicts,
  "reading": [
   ("The 2024 Bikeway and Trail Facilities Plan has two records at 68,233,939 bytes sharing one checksum and a third "
    "at 19,715,991 bytes with a different one. The small one is already requires human review. The City replaced the "
    "file at that URL; the archive captured both. Establish which is current before any site use."),
   ("The South Yale Boulevard Study Area sheet has one record at 167,088 bytes and two at 526,773 bytes sharing a "
    "checksum. The odd one out is already a duplicate, so this group may already be correctly resolved and needs only "
    "confirmation."),
  ],
 },
 "method_note_for_future_lanes": {
  "rule": ("Run the URL group-by before fetching anything in a new cluster. It is the cheapest of the four duplicate-"
           "detection methods this run has used and it catches a class the others cannot."),
  "the_four_methods_and_what_each_catches": [
   {"method": "byte hashing", "catches": "identical republished files", "misses": "anything re-encoded, re-scanned, or extracted"},
   {"method": "normalized-text and token-coverage comparison", "catches": "re-typeset versions and component-in-container relationships", "misses": "image-only files, and it over-calls on sparse slide text"},
   {"method": "fetching the R2 object and locating content by printed page", "catches": "image-only extracts of a document the archive already holds", "misses": "nothing in that class, but it is the most expensive"},
   {"method": "URL group-by", "catches": "two inventory records for one file", "misses": "the same file published at two different URLs"},
  ],
  "complementarity": ("The last two are opposites and together they close the gap: URL group-by finds one file with two "
                      "records, and content measurement finds one document at two URLs. Neither alone is sufficient and "
                      "this run has now hit both failure modes in real clusters."),
 },
 "integration_flags": [
  {"severity": "reported-figure",
   "affects": ["project-state/checkpoint.json counts_by_status"],
   "finding": f"The validated count of {ckpt['counts_by_status']['validated']} includes {excess_doc['validated']} records that are second records for a document another validated record already covers.",
   "recommended_action": "State the archive size on a one-record-per-document basis, or reconcile the groups first. Either is fine; reporting the raw count without the caveat is not."},
  {"severity": "cheap-win",
   "affects": [f"{len(pending_groups)} groups listed in actionable_now.groups"],
   "finding": "Each carries a pending record whose disposition is already settled by a terminal twin at the same URL.",
   "recommended_action": "Apply the recommended_rule. This clears pending records at a fraction of the cost of a normal triage and needs no research lane."},
  {"severity": "effort-saving",
   "affects": [f"{len(pending_only_groups)} groups listed in pending_pairs_still_needing_triage.groups"],
   "finding": "Two pending records for one document, with nothing to inherit from. These still need triaging on the merits.",
   "recommended_action": "Triage the document once and collapse the pair, rather than letting two lanes fetch and measure the same file."},
  {"severity": "correctness",
   "affects": [f"{len(multi_terminal)} groups listed in needs_codex_adjudication.groups"],
   "finding": "More than one validated or implemented record per document URL.",
   "recommended_action": "Decide what a validated-and-implemented pair means first, then reconcile. Claude modified none of these."},
  {"severity": "currency",
   "affects": [g['url'] for g in conflicts],
   "finding": "Two URLs carry records with genuinely different checksums: the same URL served different files at different times.",
   "recommended_action": "Establish which capture is current before any site use of either."},
  {"severity": "method",
   "affects": ["future research lanes"],
   "finding": "A live-service URL with 229 project records against it inflated the first pass of this audit roughly fourfold.",
   "recommended_action": "Exclude live-service URLs before reporting any URL-collision figure. The exclusion list is in this artifact."},
 ],
 "counts": {
  "candidates_examined": len(inv['candidates']),
  "document_url_groups_reported": len(doc_multi),
  "groups_with_a_pending_record_and_a_terminal_twin": len(pending_groups),
  "groups_with_two_pending_records_and_no_terminal": len(pending_only_groups),
  "multi_validated_groups": len(multi_terminal),
  "checksum_conflict_groups": len(conflicts),
 },
 "safeguards": ["no master-inventory.json write", "no checkpoint.json write", "no r2-inventory.json write",
                "no site content change", "no R2 upload", "no commit, merge, or deploy",
                "no terminal record modified", "no inventory record created", "no network access: this audit reads local state only"],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(artifact, f, indent=1, ensure_ascii=False)
print(json.dumps({"output": OUT, "counts": artifact["counts"]}))
