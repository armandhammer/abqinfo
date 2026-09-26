#!/usr/bin/env python3
"""Record visual review and the already-archived Barelas collision."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json"
a = json.loads(PATH.read_text(encoding="utf-8"))
a["reviewed_baseline_commit"] = "f07a830ddbf6d5d75c87267f6dd5335594b74a07"
a["inventory_rows_changed"] = False
saved=json.loads((ROOT/"project-state/r2-inventory.json").read_text(encoding="utf-8-sig"))
live=json.loads((ROOT/"tmp/planning-documents-root-live-r2-2026-09-25.json").read_text(encoding="utf-8-sig"))
def object_identity(source):
    return {r["key"]:(r["size_bytes"],r["etag"]) for r in source["objects"]}
assert object_identity(saved)==object_identity(live)
a["r2_snapshot"]["unchanged_exact_key_size_etag_comparison"] = True
a["expected_identity_transcription_note"] = "The user-supplied Chapter 3 SHA-256 ends in 3942 and contains 63 characters. The authoritative settled decision and inventory end in 3942b; the fresh source exactly matches that full 64-character canonical hash. No canonical identity was replaced."
assert a["summary"]["source_bytes_verified"] == 13
assert a["summary"]["source_bytes_total"] == 130968356
assert a["summary"]["pdf_pages_rendered"] == 1078
assert len(a["blockers"]) == 1 and a["blockers"][0]["id"] == "src-d9bf34830a9467e2"
for r in a["records"]:
    r["source_verification_method"] = "fresh_full_GET_authoritative_City_source_2026-09-25"
    r["source_identity_result"] = "exact_saved_size_sha256_and_page_count_match"
    assert r["http_status"] == 200 and r["content_type"] == "application/pdf" and not r["redirected"]
    assert r["final_url"] == r["direct_file_url"]
    assert r["pdf_qa"]["render_result"] == "all_pages_rendered"
    assert not r["saved_key_collision"] and not r["live_key_collision"]
    r["pdf_qa"]["representative_visual_qa"] = "passed_opening_middle_final_pages"
    r["pdf_qa"]["representative_sheet"] = "tmp/planning-documents-root-archive-qa-2026-09-25/representative-" + str((a["records"].index(r)//5)+1) + ".jpg"
    r["pdf_qa"]["quality_note"] = "Representative rendered pages match the settled document identity. All pages opened and rendered."
    if r["pdf_qa"]["low_ink_pages_1_based"]:
        r["pdf_qa"]["quality_note"] += " Low-ink pages were flagged by the thumbnail scan; representative blank separator and sparse map pages are visible. Preserve the source layout."
    if r["id"] == "src-7de0f5803d442e8f":
        r["pdf_qa"]["quality_note"] += " Final two pages are blank in the delivered original; middle page is explicitly marked intentionally blank."
    if r["id"] == "src-afac0cf84867a22f":
        r["pdf_qa"]["quality_note"] += " Historical scan; sparse map sheets and final blank page are retained as delivered."
    if r["id"] == "src-c87775c045d8acc4":
        r["pdf_qa"]["quality_note"] += " Single dense text page qualifies as a distinct historical design-control instrument."
    if r["id"] == "src-eb0f4b39798d29df":
        r["visitor_caveat"] = "The rendered first page shows a handwritten enactment notation and the package includes map sheets; verify the handwritten number before publishing a numbered-enactment claim."
        r["pdf_qa"]["quality_note"] += " First page and map sheet inspected; handwritten notation is visible."
    if r["id"] == "src-7de0f5803d442e8f":
        r["presentation_treatment"] = "Distinct historical electric utility system facility plan under Energy and City Facilities; distinguish utility network planning from City-owned buildings."
    if r["id"] == "src-99fe2201b73355c4":
        r["cross_listing_recommendation"] = "A related-plan cross-link from Redevelopment Plans / Historical and Retained Area Plans to the future Barelas canonical section materially clarifies the distinction from the commercial-area revitalization plan; do not duplicate the document entry."
    if r["id"] == "src-d9bf34830a9467e2":
        r["cross_listing_recommendation"] = "A related-plan link from the future Area & Sector Plans / Barelas section to the existing canonical revitalization entry improves discoverability without a second archive or standalone entry."
    if r["id"] == "src-f528ec2e0e955690":
        r["pdf_qa"]["quality_note"] += " The source has a final intentionally blank page."
    if r["id"] == "src-d9bf34830a9467e2":
        r["collision_resolution"] = {"existing_canonical_inventory_id":"src-28418cab91a745a6","existing_r2_key":"development-land-use/redevelopment-plans/cabq-barelas-neighborhood-commercial-area-revitalization-plan.pdf","action":"no_second_archive_object; preserve the settled retained row and request a separate reconciliation decision before any upload plan includes it"}
    else:
        assert not r["same_sha256_inventory_rows"]
        r["collision_resolution"] = {"exact_key_saved_and_live":"absent","archived_same_sha256_inventory_row":"absent","near_name_review":"related topical objects are distinct by saved title, purpose, and source identity"}

a["summary"].update({"pdf_structural_checks_passed":13,"representative_visual_reviews_passed":13,"exact_key_collisions_saved":0,"exact_key_collisions_live":0,"archived_same_hash_conflicts":1,"unique_proposed_new_keys":12,"source_or_hash_discrepancies":0})
a["preparation_readiness"] = "13_exact_sources_and_pdf_qa_complete;_12_unique_upload_candidates;_one_already_archived_canonical_conflict_blocks_13_object_upload_plan"
a["presentation_plan_status"] = "background_plan_complete_no_content_edit"
a["next_gate"] = "First reconcile the already-archived Barelas original without changing the settled disposition in this stage; separately authorize R2 upload and exact public-byte verification for the unique eligible originals. Visitor-visible implementation remains a later manual-review content-PR stage."
a["r2_mutation"] = False
a["visitor_visible_content_changed"] = False
PATH.write_text(json.dumps(a,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(a["preparation_readiness"])
