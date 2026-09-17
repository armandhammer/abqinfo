#!/usr/bin/env python3
"""Integrate the reviewed undiscovered-document artifact as pending candidates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_RESEARCH = Path(
    "project-state/discovery/undiscovered-documents-research-2026-09-14.json"
)
DEFAULT_INVENTORY = Path("project-state/master-inventory.json")
DEFAULT_RESULT = Path(
    "project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json"
)
EXPECTED_RECOMMENDATION = "add to the inventory as a new candidate"


def stable_id(url: str) -> str:
    digest = hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()
    return "src-" + digest[:16]


def write_json(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp-integration")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def candidate_from_row(row: dict, research_path: Path, now: str, discovered_at: str) -> dict:
    if row.get("inventory_id") is not None:
        raise ValueError(f"{row.get('local_ref')} unexpectedly already has an inventory ID")
    if row.get("recommendation") != EXPECTED_RECOMMENDATION:
        raise ValueError(f"{row.get('local_ref')} has an unexpected recommendation")
    if row.get("content_kind") != "PDF" or row.get("leading_bytes") != "25504446":
        raise ValueError(f"{row.get('local_ref')} is not a verified PDF")
    if str(row.get("http_status")) != "200":
        raise ValueError(f"{row.get('local_ref')} does not have saved HTTP 200 evidence")
    if len(str(row.get("checksum_sha256", ""))) != 64 or int(row["size_bytes"]) <= 0:
        raise ValueError(f"{row.get('local_ref')} lacks exact storage metadata")

    description = str(row["description"])
    word_count = len(description.split())
    if word_count != int(row["description_word_count"]):
        raise ValueError(
            f"{row.get('local_ref')} description count is {word_count}, "
            f"not {row.get('description_word_count')}"
        )

    notes = [
        f"Integrated from {research_path.as_posix()} row {row['local_ref']}.",
        str(row["link_check"]),
        str(row["evidence"]),
    ]
    if row.get("caution"):
        notes.append("Research caution: " + str(row["caution"]))
    for cross_listing in row.get("cross_listings", []):
        notes.append(
            "Research-proposed future cross-listing: "
            + str(cross_listing["page"])
            + " — "
            + str(cross_listing["reason"])
        )

    url = str(row["authoritative_url"])
    return {
        "id": stable_id(url),
        "status": "pending review",
        "source_url": url,
        "direct_file_url": url,
        "r2_url": None,
        "r2_key": None,
        "r2_etag": None,
        "r2_last_modified": None,
        "agency": "City of Albuquerque",
        "title": str(row["title"]),
        "date": None,
        "file_type": "PDF",
        "size_bytes": int(row["size_bytes"]),
        "checksum_sha256": str(row["checksum_sha256"]),
        "parent_url": None,
        "referring_urls": [],
        "discovery_path": [
            research_path.as_posix(),
            "reported-in:" + str(row["reported_in"]),
            url,
        ],
        "discovery_method": "saved authoritative-source research integration",
        "crawl_depth": None,
        "cited_predecessors": [],
        "cited_successors": [],
        "provenance_status": (
            "authoritative City URL, exact size, SHA-256, PDF signature, and HTTP 200 "
            "recorded in saved research"
        ),
        "proposed_canonical_page": row.get("proposed_canonical_page"),
        "description": description,
        "description_word_count": word_count,
        "processing_notes": notes,
        "implementation_location": None,
        "implementation_locations": [],
        "cross_listing_approved": False,
        "validation_status": "research evidence saved; normal archival and publication validation not run",
        "exclusion_reason": None,
        "local_path": None,
        "discovered_at": discovered_at,
        "updated_at": now,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research", type=Path, default=DEFAULT_RESEARCH)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    research = json.loads(args.research.read_text(encoding="utf-8"))
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    rows = research.get("add_to_inventory", [])
    if len(rows) != 44:
        raise SystemExit(f"Expected 44 add_to_inventory rows; found {len(rows)}")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    proposed = [
        candidate_from_row(row, args.research, now, str(research["generated_at"]))
        for row in rows
    ]
    proposed_ids = [record["id"] for record in proposed]
    proposed_urls = [record["source_url"] for record in proposed]
    proposed_hashes = [record["checksum_sha256"] for record in proposed]
    if len(set(proposed_ids)) != 44 or len(set(proposed_urls)) != 44 or len(set(proposed_hashes)) != 44:
        raise SystemExit("Research additions are not unique by ID, URL, and SHA-256")

    candidates = inventory["candidates"]
    existing_ids = {record["id"]: record for record in candidates}
    existing_urls = {
        url: record["id"]
        for record in candidates
        for url in (record.get("source_url"), record.get("direct_file_url"))
        if url
    }
    existing_hashes = {
        record["checksum_sha256"]: record["id"]
        for record in candidates
        if record.get("checksum_sha256")
    }

    collisions: list[dict] = []
    new_records: list[dict] = []
    already_integrated: list[dict] = []
    for record in proposed:
        candidate_id = record["id"]
        if candidate_id in existing_ids:
            existing = existing_ids[candidate_id]
            if (
                existing.get("source_url") != record["source_url"]
                or existing.get("checksum_sha256") != record["checksum_sha256"]
                or int(existing.get("size_bytes") or 0) != record["size_bytes"]
            ):
                collisions.append({"candidate_id": candidate_id, "kind": "stable_id_mismatch"})
            else:
                already_integrated.append(existing)
            continue
        if record["source_url"] in existing_urls:
            collisions.append(
                {
                    "candidate_id": candidate_id,
                    "kind": "url",
                    "existing_id": existing_urls[record["source_url"]],
                }
            )
        if record["checksum_sha256"] in existing_hashes:
            collisions.append(
                {
                    "candidate_id": candidate_id,
                    "kind": "sha256",
                    "existing_id": existing_hashes[record["checksum_sha256"]],
                }
            )
        new_records.append(record)

    if collisions:
        raise SystemExit("Current inventory collisions: " + json.dumps(collisions))
    if already_integrated and new_records:
        raise SystemExit("Artifact is only partially integrated; refusing a mixed update")

    action = "already_integrated" if already_integrated else "would_add"
    if args.apply and new_records:
        inventory["candidates"] = sorted(candidates + new_records, key=lambda record: record["id"])
        counts = Counter(record["status"] for record in inventory["candidates"])
        inventory["counts"] = {
            status: counts.get(status, 0) for status in inventory["allowed_statuses"]
        }
        pending_statuses = {
            "pending review",
            "approved for addition",
            "downloaded",
            "parsed",
            "description drafted",
            "placement assigned",
        }
        pending = [
            record
            for record in inventory["candidates"]
            if record["status"] in pending_statuses
            or (record["status"] == "implemented" and record.get("validation_status") != "passed")
        ]
        inventory["next_pending_id"] = min((record["id"] for record in pending), default=None)
        inventory["generated_at"] = now
        write_json(args.inventory, inventory)
        action = "added"

    result_records = proposed if new_records else already_integrated
    result = {
        "schema_version": 1,
        "artifact_type": "saved_research_candidate_integration",
        "generated_at": now,
        "source_artifact": args.research.as_posix(),
        "inventory_path": args.inventory.as_posix(),
        "action": action,
        "summary": {
            "records": len(result_records),
            "total_size_bytes": sum(int(record["size_bytes"]) for record in result_records),
            "status": "pending review",
            "content_changes": 0,
            "r2_changes": 0,
        },
        "records": [
            {
                "local_ref": row["local_ref"],
                "candidate_id": record["id"],
                "source_url": record["source_url"],
                "size_bytes": record["size_bytes"],
                "checksum_sha256": record["checksum_sha256"],
                "proposed_canonical_page": record["proposed_canonical_page"],
                "status": record["status"],
            }
            for row, record in zip(rows, proposed, strict=True)
        ],
        "safeguards": [
            "No site content was changed.",
            "No R2 object was uploaded, deleted, overwritten, or otherwise modified.",
            "Every record remains pending review until the normal archive and publication gates pass.",
        ],
    }
    if args.apply:
        write_json(args.result, result)
    print(json.dumps(result["summary"] | {"action": action}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
