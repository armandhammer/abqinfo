#!/usr/bin/env python3
"""Finalize exact later-MS4 archive preparation; never contact or mutate R2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
inspection_spec = importlib.util.spec_from_file_location("later_ms4_inspection", Path(__file__).with_name("Inspect-LaterMs4ArchivePreparation.py"))
inspection_module = importlib.util.module_from_spec(inspection_spec)
inspection_spec.loader.exec_module(inspection_module)
EXPECTED, STAGING = inspection_module.EXPECTED, inspection_module.STAGING

ARTIFACT = ROOT / "project-state/discovery/later-ms4-archive-preparation-2026-09-24.json"
INVENTORY = ROOT / "project-state/master-inventory.json"
SAVED_R2 = ROOT / "project-state/r2-inventory.json"
LIVE_R2 = ROOT / "tmp/later-ms4-live-r2-listing-2026-09-24.json"
LEDGER = STAGING / "pdf-inspection-ledger.json"
KEYS = (
    "public-works/stormwater-drainage/epa-middle-rio-grande-watershed-ms4-general-permit-2014.pdf",
    "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2016.pdf",
    "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2017.pdf",
    "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2019.pdf",
    "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2020-final.pdf",
    "public-works/stormwater-drainage/cabq-ms4-annual-report-fy2021-final.pdf",
)
IDENTITIES = (
    "2014 EPA Middle Rio Grande watershed-based MS4 general permit, NMR04A000",
    "City signed and compiled FY2016 MS4 Annual Report, July 2015-June 2016",
    "City FY2017 MS4 Annual Report, July 2016-June 2017",
    "City FY2019 MS4 Annual Report, July 2018-June 2019",
    "City final FY2020 MS4 Annual Report, July 2019-June 2020",
    "City final FY2021 MS4 Annual Report, July 2020-June 2021",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    inventory, saved, live, ledger = map(load, (INVENTORY, SAVED_R2, LIVE_R2, LEDGER))
    rows = {row["id"]: row for row in inventory["candidates"]}
    inspections = ledger["records"]
    assert len(EXPECTED) == len(KEYS) == len(inspections) == 6
    assert [item[0] for item in EXPECTED] == [item["id"] for item in inspections]
    assert sum(item[2] for item in EXPECTED) == 426926738
    assert (saved["object_count"], saved["total_bytes"]) == (live["object_count"], live["total_bytes"])
    assert {obj["key"].casefold() for obj in saved["objects"]} == {obj["key"].casefold() for obj in live["objects"]}
    assert saved["object_count"] == len(saved["objects"]) and live["object_count"] == len(live["objects"])
    all_keys = {obj["key"].casefold() for obj in saved["objects"]}
    assert len(set(key.casefold() for key in KEYS)) == 6
    assert all(key.casefold() not in all_keys for key in KEYS)
    sizes = {item[2] for item in EXPECTED}
    same_size = [obj["key"] for obj in live["objects"] if obj["size_bytes"] in sizes]
    assert not same_size, same_size
    expected_hashes = {item[3] for item in EXPECTED}
    archived_same_hash = [row["id"] for row in inventory["candidates"] if row.get("r2_key") and row.get("checksum_sha256") in expected_hashes]
    assert not archived_same_hash, archived_same_hash
    records = []
    for order, ((record_id, filename, size, sha), key, identity, inspection) in enumerate(zip(EXPECTED, KEYS, IDENTITIES, inspections), 1):
        row = rows[record_id]
        path = STAGING / filename
        assert row["status"] == "approved for addition" and row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert (row["size_bytes"], row["checksum_sha256"]) == (size, sha)
        assert (path.stat().st_size, digest(path)) == (size, sha)
        assert path.open("rb").read(5) == b"%PDF-"
        assert inspection["id"] == record_id and inspection["rendered_pages"] == inspection["page_count"]
        assert inspection["structural_result"] == "opens_without_password_or_repair"
        assert all((ROOT / sheet).exists() for sheet in inspection["contact_sheets"])
        if order != 4:
            assert inspection["low_ink_pages_1_based"] == []
        else:
            assert inspection["low_ink_pages_1_based"] == [389, 391, 419, 422, 431, 442, 445, 447, 448, 449, 1232]
        source_history = None
        if order == 2:
            source_history = "Same City URL delivered the saved original on 2026-09-14, returned HTTP 404 on 2026-09-20, and delivered these exact bytes again on 2026-09-24. No replacement or migration is claimed."
        elif order == 5:
            source_history = "Prior City URL returned 404 on 2026-09-20; the verified documents.cabq.gov lowercase-nmr04a014 path delivers the saved original and is the current authoritative source."
        result = {
            "order": order,
            "id": record_id,
            "identity": identity,
            "authoritative_source_url": row["direct_file_url"],
            "source_path_history": source_history,
            "retrieval": {"method": "official_source_full_GET_2026-09-24", "http_status": 200, "content_type": "application/pdf", "pdf_magic_verified": True},
            "staged_original": inspection["staged_original"],
            "size_bytes": size,
            "checksum_sha256": sha,
            "page_count": inspection["page_count"],
            "pdf_qa": {
                "structure": inspection["structural_result"],
                "render": inspection["render_result"],
                "rendered_pages": inspection["rendered_pages"],
                "text_layer_pages": inspection["text_layer_pages"],
                "low_ink_pages_1_based": inspection["low_ink_pages_1_based"],
                "contact_sheets": inspection["contact_sheets"],
                "visual_result": "passed_representative_first_middle_final_and_flagged_page_review",
                "visual_note": "Eleven sparse/blank FY2019 attachment pages were inspected in sequence and are consistent with the surrounding spreadsheet/chart delivery; no truncation or corrupt render observed." if order == 4 else "Opening, representative middle, and final pages show the expected original and intact attachments; no obvious truncation or corrupt render observed.",
            },
            "identity_check": "NMR04A000 governing watershed permit; distinct from the 2005 City permit." if order == 1 else "FY2016 signed/compiled 173-page filing, City/NMR04A014, July 2015-June 2016." if order == 2 else "Final FY2021 382-page City filing, July 2020-June 2021; distinct saved hash and size from the superseded draft." if order == 6 else "City/NMR04A014 and fiscal-year reporting period match the saved family decision on page 7.",
            "proposed_r2_key": key,
            "proposed_future_archive_url": "https://files.abqinfo.com/" + key,
            "collision_check": {"saved_exact_key": False, "live_exact_key": False, "saved_or_live_same_size_object": False, "inventory_archived_same_sha256": False, "semantic_near_name": "Existing distinct FY2018 and FY2022-FY2025 annual-report keys use the same series convention; the older 2005 City MS4 permit is a different instrument."},
            "archive_preparation_ready": True,
            "r2_mutation": False,
        }
        records.append(result)
        row["local_path"] = result["staged_original"]
        row["validation_status"] = "Later-MS4 archive preparation complete: exact official-source size/SHA-256 and local PDF render/visual QA passed; proposed R2 key collision-free. R2 upload/public-byte verification and visible content remain separately gated."
    assert sum(record["page_count"] for record in records) == 5917
    artifact = {
        "schema_version": 1,
        "artifact_type": "later_ms4_archive_preparation",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "state": "archive_preparation_complete_ready_for_separately_authorized_upload",
        "family": "Later MS4 annual reports and permit instrument",
        "family_decision": "project-state/discovery/later-ms4-annual-reports-and-permit-instruments-decision-2026-09-20.json",
        "fy2016_source_recovery": "project-state/discovery/later-ms4-fy2016-source-recovery-2026-09-24.json",
        "candidate_ids_in_order": [item[0] for item in EXPECTED],
        "future_canonical_page": "content/public-works/stormwater-drainage.md",
        "family_presentation": "One future curated chronological MS4 compliance series. The 2014 EPA permit is program-level context; FY2016, FY2017, FY2019, final FY2020, and final FY2021 are distinct unchanged annual originals. Do not synthesize reports or infer a missing FY2018 filing. The 2015 coverage letter is context only, FY2021 draft is superseded, and the separate 2014 MS4 28-record package remains gated.",
        "explicit_exclusions": ["src-185f33493177b085", "src-3408f5b9a86bcb5c", "separate 2014 MS4 annual-report body and 27 attachments", "inferred FY2018 filing"],
        "saved_r2_snapshot": {field: saved[field] for field in ("generated_at", "object_count", "total_bytes")},
        "live_r2_snapshot": {field: live[field] for field in ("generated_at", "object_count", "total_bytes")},
        "collision_check_method": "Case-insensitive exact-key and near-name review of saved and read-only live 1,231-object listings; same-size screening across both lists; inventory archived SHA-256 cross-check. No object has any proposed exact key or candidate size, so exact same bytes under another key are ruled out by size.",
        "records": records,
        "summary": {"candidates": 6, "exact_source_matches": 6, "total_staged_bytes": 426926738, "pdf_pages_rendered": 5917, "visual_reviews_passed": 6, "saved_exact_key_collisions": 0, "live_exact_key_collisions": 0, "same_size_r2_objects": 0, "blockers": []},
        "remaining_gate": "Separately authorized unchanged-original R2 upload followed by exact public-byte size and SHA-256 verification. Visitor-visible Hugo work and site-content PR remain separately gated.",
        "safeguards": {"r2_mutation": False, "public_byte_verification_performed": False, "visitor_visible_content_changed": False, "site_content_pr_created": False, "gated_2014_ms4_package_touched": False},
    }
    save(ARTIFACT, artifact)
    save(INVENTORY, inventory)
    print(json.dumps(artifact["summary"], indent=2))


if __name__ == "__main__":
    main()
