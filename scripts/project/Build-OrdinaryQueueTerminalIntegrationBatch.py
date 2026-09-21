#!/usr/bin/env python3
"""Generate a durable ordinary-queue terminal-integration batch artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "project-state/master-inventory.json"
DEFAULT_MS4 = ROOT / "project-state/discovery/2014-ms4-package-decision-2026-09-18.json"


def path_arg(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def find_nested(value: object, candidate_id: str) -> dict | None:
    if isinstance(value, dict):
        if value.get("id") == candidate_id or value.get("candidate_id") == candidate_id:
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


def terminal_recommendations(value: object, results: dict[str, dict]) -> None:
    if isinstance(value, dict):
        if value.get("id") and value.get("recommended_status") in {"excluded", "duplicate", "superseded"}:
            results[value["id"]] = value
        for child in value.values():
            terminal_recommendations(child, results)
    elif isinstance(value, list):
        for child in value:
            terminal_recommendations(child, results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--recorded-at", required=True)
    parser.add_argument("--selection-rule", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--batch-ids", help="Comma-separated explicit candidate IDs")
    group.add_argument("--package", help="Saved research package label to select completely")
    parser.add_argument("--start-id", help="Inclusive deterministic inventory-ID start for package selection")
    parser.add_argument("--next-id", required=True)
    parser.add_argument("--next-research", required=True)
    parser.add_argument("--next-recommendation", required=True)
    parser.add_argument("--skip-family", default="2014 MS4 Annual Report")
    parser.add_argument("--skip-evidence", default=str(DEFAULT_MS4.relative_to(ROOT)).replace("\\", "/"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    research_path = path_arg(args.research)
    output = path_arg(args.output)
    next_research_path = path_arg(args.next_research)
    ms4_path = path_arg(args.skip_evidence)
    inventory = {row["id"]: row for row in load(INVENTORY)["candidates"]}
    research = load(research_path)
    saved: dict[str, dict] = {}
    terminal_recommendations(research, saved)
    if args.batch_ids:
        ids = [candidate_id for candidate_id in args.batch_ids.split(",") if candidate_id]
    else:
        ids = sorted(candidate_id for candidate_id, row in saved.items() if row.get("package") == args.package and (not args.start_id or candidate_id >= args.start_id))
    if not ids or len(ids) != len(set(ids)) or set(ids) - set(inventory) or set(ids) - set(saved):
        raise ValueError("Batch IDs must be unique terminal decisions represented in inventory and saved research")
    rows = []
    for candidate_id in ids:
        candidate = inventory[candidate_id]
        saved_row = saved[candidate_id]
        if candidate["status"] != saved_row["recommended_status"]:
            raise ValueError(f"{candidate_id} does not retain its saved terminal disposition")
        row = {"candidate_id": candidate_id, "title": candidate["title"], "status": candidate["status"], "saved_research_category": saved_row.get("category")}
        for key in ("bill", "parent_enacted_instrument_held"):
            if key in saved_row:
                row[key] = saved_row[key]
        if candidate["status"] in {"duplicate", "superseded"}:
            row["canonical_candidate_id"] = saved_row["canonical_id"]
            row["relationship"] = saved_row.get("relationship")
        else:
            row["reason"] = saved_row["exclusion_reason"]
            # Keep the saved source identity and measurement evidence with the
            # generic terminal decision.  This lets a batch artifact stand on
            # its own without treating a prior source fetch as a new action.
            evidence = {
                key: saved_row[key]
                for key in (
                    "authoritative_url", "link_check", "content_kind",
                    "leading_bytes", "size_bytes", "checksum_sha256",
                    "title_for_reference", "tested_not_assumed", "content",
                )
                if key in saved_row
            }
            if evidence:
                row["source_research_evidence"] = evidence
            # Some excluded live-service rows are navigational aliases rather
            # than independently useful archive objects.  Retain the saved
            # target/identity evidence in every generic terminal-batch
            # artifact without treating it as a canonical document relation.
            for key in ("resolves_to", "aliases_a_candidate_in_this_slice", "byte_identical_to"):
                if key in saved_row:
                    row[key] = saved_row[key]
        rows.append(row)
    next_research = find_nested(load(next_research_path), args.next_id)
    saved_next_status = next_research.get("recommended_status") if next_research else None
    if saved_next_status is None and next_research:
        saved_next_status = next_research.get("status")
    if not next_research or saved_next_status != args.next_recommendation:
        raise ValueError("Next ordinary-queue candidate lacks the declared saved research disposition")
    ms4 = load(ms4_path)
    ms4_ids = {row["candidate_id"] for row in ms4["components"]}
    if "src-05ec421cb265b29a" not in ms4_ids or inventory["src-05ec421cb265b29a"]["status"] != "pending review":
        raise ValueError("MS4 family skip boundary changed")
    data = {
        "schema_version": 1,
        "artifact_type": "ordinary_queue_terminal_integration_batch",
        "recorded_at": args.recorded_at,
        "state": "terminal_inventory_decisions_applied_no_archive_or_content_action",
        "source_research": relative(research_path),
        "selection_rule": args.selection_rule,
        "results": rows,
        "summary": {"total": len(rows), "excluded": sum(row["status"] == "excluded" for row in rows), "duplicate_deliveries": sum(row["status"] == "duplicate" for row in rows), "superseded": sum(row["status"] == "superseded" for row in rows)},
        "ordinary_queue_handoff": {"generated_next_pending_id": "src-05ec421cb265b29a", "skip_family": args.skip_family, "skip_evidence": relative(ms4_path), "next_actionable_candidate": args.next_id, "next_saved_research": relative(next_research_path), "next_saved_recommendation": args.next_recommendation, "instruction": "Do not start this candidate without a new task instruction."},
        "safeguards_observed": {"r2_mutation": False, "content_changed": False, "pdf_built": False, "ms4_reviewed": False, "capital_spending_work": False, "merge_or_deploy": False},
    }
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {relative(output)} for {len(rows)} terminal decisions")


if __name__ == "__main__":
    main()
