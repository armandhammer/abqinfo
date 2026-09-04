#!/usr/bin/env python3
"""Build a deterministic human-review queue from CABQ Legistar discovery output."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


HIGH_VALUE = re.compile(
    r"\b(study|plan|assessment|analysis|report|map|design|toolkit|application|grant|"
    r"capital|CIP|ICIP|infrastructure|transportation|transit|traffic|street|road|"
    r"parking|redevelopment|land use|zoning|bicycle|pedestrian|trail|airport|aviation)\b",
    re.IGNORECASE,
)
GENERIC = re.compile(r"^(?:EC|R|O|C|M|AC)[- _]?\d", re.IGNORECASE)
STRONG_MATTER = re.compile(r"\b(study|plan|assessment|analysis|report|master plan|capital implementation program)\b", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    discovery = json.loads(Path(args.input).read_text(encoding="utf-8"))
    queue = []
    for matter in discovery["matters"]:
        latest = max(row["date"] for row in matter["agenda_occurrences"])
        matter_hits = len(set(match.group(0).lower() for match in HIGH_VALUE.finditer(matter["title"] or "")))
        for attachment in matter["attachments"]:
            if not attachment["is_new_to_inventory"]:
                continue
            name = attachment["name"] or ""
            attachment_hits = len(set(match.group(0).lower() for match in HIGH_VALUE.finditer(name)))
            strong_matter = bool(STRONG_MATTER.search(matter["title"] or ""))
            if attachment_hits == 0 and not strong_matter:
                continue
            score = min(matter_hits, 4) + 3 * min(attachment_hits, 4) + (3 if strong_matter else 0)
            if GENERIC.search(name.strip()):
                score -= 2
            if score < 3:
                continue
            queue.append({
                "priority_score": score,
                "discovery_id": attachment["discovery_id"],
                "matter_file": matter["matter_file"],
                "matter_title": matter["title"],
                "latest_agenda_date": latest,
                "attachment_name": name,
                "attachment_url": attachment["url"],
                "agenda_occurrences": matter["agenda_occurrences"],
                "review_status": "pending document review",
            })
    queue.sort(key=lambda row: (row["matter_file"] or "", row["attachment_url"]))
    queue.sort(key=lambda row: row["latest_agenda_date"], reverse=True)
    queue.sort(key=lambda row: row["priority_score"], reverse=True)
    queue = queue[: args.limit]
    output = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_discovery": args.input.replace("\\", "/"),
        "selection": "New-to-inventory attachment URLs scored by durable-document terms in attachment and matter titles; generic legislation filenames are demoted. No relevance or archival decision is implied.",
        "limit": args.limit,
        "count": len(queue),
        "items": queue,
    }
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"queued": len(queue)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
