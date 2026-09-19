#!/usr/bin/env python3
"""Verify any generated ordinary-queue terminal-integration batch artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    args = parser.parse_args()
    artifact_path = ROOT / args.artifact
    data = load(artifact_path)
    inventory = {row["id"]: row for row in load(ROOT / "project-state/master-inventory.json")["candidates"]}
    research = load(ROOT / data["source_research"])
    results = data["results"]
    if not results or len({row["candidate_id"] for row in results}) != len(results):
        raise AssertionError("Batch must contain unique terminal decisions")
    for row in results:
        candidate_id = row["candidate_id"]
        saved = find_nested(research, candidate_id)
        if not saved or inventory[candidate_id]["status"] != row["status"] or saved.get("recommended_status") != row["status"]:
            raise AssertionError(f"Saved terminal disposition changed for {candidate_id}")
        if row["status"] in {"duplicate", "superseded"}:
            if not row.get("canonical_candidate_id") or row["canonical_candidate_id"] != saved.get("canonical_id"):
                raise AssertionError(f"Canonical relationship missing or changed for {candidate_id}")
    if any(data["safeguards_observed"].values()):
        raise AssertionError("Batch records a prohibited side effect")
    print(f"PASS: {artifact_path.name} retains {len(results)} saved terminal inventory decisions.")


if __name__ == "__main__":
    main()
