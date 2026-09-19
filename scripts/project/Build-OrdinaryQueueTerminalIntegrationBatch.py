#!/usr/bin/env python3
"""Record a deterministic ordinary-queue batch applied from saved research."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
FINAL_SWEEP = ROOT / "project-state/discovery/final-sweep-cluster-research-2026-09-13.json"
PARKS = ROOT / "project-state/discovery/parks-recreation-cluster-research-2026-09-13.json"
MS4 = ROOT / "project-state/discovery/2014-ms4-package-decision-2026-09-18.json"
OUTPUT = ROOT / "project-state/discovery/ordinary-queue-terminal-integration-batch-2026-09-19.json"

BATCH_IDS = [
    "src-0634d4e49bad3dc6", "src-093f5e8cf8345147", "src-10d16d79d48b3ed3",
    "src-11530a38d98fc336", "src-1159833fa8f60d94", "src-1323738fd259ca87",
    "src-13a851bdd0cf9760", "src-1496e29f73a0d65b", "src-14ba382a64272c57",
    "src-14d6041a0e4f2d24", "src-1572bcbe7b66faca", "src-168e53d86eef9f25",
    "src-186ce68b60d7338a", "src-18a9c99faa3c5552", "src-1995be319d4ca0d1",
    "src-1ae45062c8c23206", "src-1aff457c47017b14", "src-1cc751b439d14547",
    "src-1d0624c3e233da05", "src-1f6920d5ed639ae2", "src-20e3f712e957128e",
    "src-2178cc5a27804157", "src-21b923dee2964556", "src-220560ae9c580e15",
    "src-2240084019050486", "src-23caf8cf5302ebc3", "src-23ff2eec964d7511",
    "src-24aaa1fcbf52c373", "src-2501af06d39c90e6", "src-264417ad69bfe8fb",
]
NEXT_ID = "src-065b5f5fc704c3a6"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_nested(value: object, candidate_id: str) -> dict | None:
    if isinstance(value, dict):
        if value.get("id") == candidate_id:
            return value
        for child in value.values():
            found = find_nested(child, candidate_id)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_nested(child, candidate_id)
            if found:
                return found
    return None


def main() -> None:
    inventory = {row["id"]: row for row in load(INVENTORY)["candidates"]}
    final_sweep = load(FINAL_SWEEP)
    saved = {row["id"]: row for key in ("excluded", "duplicate") for row in final_sweep[key]}
    if len(BATCH_IDS) != 30 or len(BATCH_IDS) != len(set(BATCH_IDS)):
        raise ValueError("Expected exactly 30 unique batch IDs")
    if set(BATCH_IDS) - set(inventory) or set(BATCH_IDS) - set(saved):
        raise ValueError("Batch is not completely represented in inventory and saved research")
    rows = []
    for candidate_id in BATCH_IDS:
        candidate = inventory[candidate_id]
        research = saved[candidate_id]
        if candidate["status"] != research["recommended_status"]:
            raise ValueError(f"{candidate_id} does not retain its saved terminal disposition")
        row = {"candidate_id": candidate_id, "title": candidate["title"], "status": candidate["status"], "saved_research_category": research.get("category")}
        if candidate["status"] == "duplicate":
            row["canonical_candidate_id"] = research["canonical_id"]
            row["relationship"] = research["relationship"]
        else:
            row["reason"] = research["exclusion_reason"]
        rows.append(row)
    next_research = find_nested(load(PARKS), NEXT_ID)
    if not next_research or next_research.get("recommended_status") != "excluded":
        raise ValueError("Next ordinary-queue candidate lacks the saved Parks research disposition")
    ms4_ids = {row["candidate_id"] for row in load(MS4)["components"]}
    if "src-05ec421cb265b29a" not in ms4_ids or inventory["src-05ec421cb265b29a"]["status"] != "pending review":
        raise ValueError("MS4 family skip boundary changed")
    data = {
        "schema_version": 1,
        "artifact_type": "ordinary_queue_terminal_integration_batch",
        "recorded_at": "2026-09-19",
        "state": "terminal_inventory_decisions_applied_no_archive_or_content_action",
        "source_research": str(FINAL_SWEEP.relative_to(ROOT)).replace("\\", "/"),
        "selection_rule": "The first 30 pending ordinary-queue candidates at or after the prior non-MS4 resume point that already had final-sweep terminal recommendations, in deterministic inventory-ID order. The 2014 MS4 package was not a candidate for this batch.",
        "results": rows,
        "summary": {"total": 30, "excluded_live_html_pages": sum(row["status"] == "excluded" for row in rows), "duplicate_deliveries": sum(row["status"] == "duplicate" for row in rows)},
        "ordinary_queue_handoff": {"generated_next_pending_id": "src-05ec421cb265b29a", "skip_family": "2014 MS4 Annual Report", "skip_evidence": str(MS4.relative_to(ROOT)).replace("\\", "/"), "next_actionable_candidate": NEXT_ID, "next_saved_research": str(PARKS.relative_to(ROOT)).replace("\\", "/"), "next_saved_recommendation": "excluded", "instruction": "Do not start this candidate without a new task instruction."},
        "safeguards_observed": {"r2_mutation": False, "content_changed": False, "pdf_built": False, "ms4_reviewed": False, "capital_spending_work": False, "merge_or_deploy": False},
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} for {len(rows)} terminal decisions")


if __name__ == "__main__":
    main()
