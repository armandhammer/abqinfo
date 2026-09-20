#!/usr/bin/env python3
"""Apply a durable archive-preparation decision without hand-editing inventory.

The decision artifact remains the review record.  This helper limits inventory
writes to explicitly listed mutable fields, recalculates aggregates, and
refuses to turn a preparation decision into public implementation.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
ALLOWED_FIELDS = {
    "status", "title", "source_url", "direct_file_url", "description",
    "document_date", "content_type", "sha256", "size_bytes",
    "content_length", "validation_status", "exclusion_reason",
    "processing_notes", "cited_successors", "implementation_locations",
    "cross_listing_approved",
}
TERMINAL = {"excluded", "duplicate", "superseded", "requires human review"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    parser.add_argument("--inventory", default=str(INVENTORY))
    parser.add_argument("--updated-at")
    args = parser.parse_args()
    decision_path = Path(args.decision)
    if not decision_path.is_absolute():
        decision_path = ROOT / decision_path
    inventory_path = Path(args.inventory)
    if not inventory_path.is_absolute():
        inventory_path = ROOT / inventory_path
    decision = load(decision_path)
    records = decision.get("records", [])
    if not records or len({record.get("id") for record in records}) != len(records):
        raise ValueError("Decision must contain unique records")
    inventory = load(inventory_path)
    rows = {row["id"]: row for row in inventory["candidates"]}
    now = args.updated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    applied: list[str] = []
    for record in records:
        candidate_id = record.get("id")
        update = record.get("inventory_update")
        if candidate_id not in rows or not isinstance(update, dict):
            raise ValueError(f"{candidate_id}: missing inventory row or inventory_update")
        unknown = set(update) - ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"{candidate_id}: unsupported inventory fields: {sorted(unknown)}")
        status = update.get("status")
        if status not in inventory["allowed_statuses"]:
            raise ValueError(f"{candidate_id}: invalid status")
        if status in {"implemented", "validated"} or record.get("r2_action") not in {None, "none"}:
            raise ValueError(f"{candidate_id}: preparation cannot implement, validate, or mutate R2")
        if status in TERMINAL and not update.get("exclusion_reason"):
            raise ValueError(f"{candidate_id}: terminal decision needs exclusion_reason")
        if status == "approved for addition":
            for field in ("sha256", "size_bytes", "content_type", "direct_file_url"):
                if not update.get(field):
                    raise ValueError(f"{candidate_id}: approved preparation lacks {field}")
        row = rows[candidate_id]
        for key, value in update.items():
            row[key] = value
        if "description" in update:
            row["description_word_count"] = len((update["description"] or "").split())
        row["updated_at"] = now
        applied.append(candidate_id)
    inventory["counts"] = {
        status: sum(row["status"] == status for row in inventory["candidates"])
        for status in inventory["allowed_statuses"]
    }
    pending = {"pending review", "approved for addition", "downloaded", "parsed", "description drafted", "placement assigned"}
    eligible = [row["id"] for row in inventory["candidates"] if row["status"] in pending or (row["status"] == "implemented" and row.get("validation_status") != "passed")]
    inventory["next_pending_id"] = min(eligible) if eligible else None
    inventory["generated_at"] = now
    temporary = inventory_path.with_name(inventory_path.name + ".archive-preparation.tmp")
    temporary.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(inventory_path)
    print(json.dumps({"applied": len(applied), "ids": applied, "counts": inventory["counts"], "next_pending_id": inventory["next_pending_id"]}))


if __name__ == "__main__":
    main()
