#!/usr/bin/env python3
"""Deterministically discover topical CABQ Legistar matters and attachments from meeting agendas."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


API = "https://webapi.legistar.com/v1/cabq"
TOPIC_PATTERN = re.compile(
    r"\b(transportation|transit|rail|road(?:way)?|street|traffic|pedestrian|walkability|walking|"
    r"bicycl\w*|bike|trail|parking|airport|aviation|vision zero|complete streets|"
    r"metropolitan redevelopment|redevelopment|land use|zoning|comprehensive plan|"
    r"sector development|area plan|master plan|capital improvements?|"
    r"capital implementation program|general obligation bond|infrastructure|growth strategy)\b",
    re.IGNORECASE,
)


def fetch_json(url: str):
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ABQInfo deterministic discovery/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(0.5 * (attempt + 1))


def api_url(path: str, params: dict[str, str] | None = None) -> str:
    return f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")


def stable_id(url: str) -> str:
    return "legistar-" + hashlib.sha256(url.strip().lower().encode()).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2026-09-05", help="Exclusive end date")
    parser.add_argument("--body-ids", default="1,44,46,9,6,50")
    parser.add_argument("--inventory", default="project-state/master-inventory.json")
    parser.add_argument("--output", default="project-state/discovery/cabq-legistar-historical-2020-2026.json")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    body_ids = [int(value) for value in args.body_ids.split(",")]
    bodies = {body["BodyId"]: body["BodyName"] for body in fetch_json(api_url("bodies", {"$top": "1000"}))}

    events = []
    for body_id in body_ids:
        query = (
            f"EventBodyId eq {body_id} and EventDate ge datetime'{start.isoformat()}T00:00:00' "
            f"and EventDate lt datetime'{end.isoformat()}T00:00:00'"
        )
        events.extend(fetch_json(api_url("events", {"$filter": query, "$top": "1000", "$orderby": "EventDate"})))
    events = sorted({event["EventId"]: event for event in events}.values(), key=lambda row: (row["EventDate"], row["EventId"]))

    def get_items(event):
        return event, fetch_json(api_url(f"events/{event['EventId']}/eventitems", {"$top": "1000"}))

    matches: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for event, items in pool.map(get_items, events):
            for item in items:
                matter_id = item.get("EventItemMatterId")
                searchable = " ".join(str(item.get(key) or "") for key in (
                    "EventItemTitle", "EventItemMatterFile", "EventItemMatterType", "EventItemAgendaNote"
                ))
                terms = sorted({match.group(0).lower() for match in TOPIC_PATTERN.finditer(searchable)})
                if not matter_id or not terms:
                    continue
                record = matches.setdefault(matter_id, {
                    "matter_id": matter_id,
                    "matter_guid": item.get("EventItemMatterGuid"),
                    "matter_file": item.get("EventItemMatterFile"),
                    "matter_type": item.get("EventItemMatterType"),
                    "title": item.get("EventItemTitle"),
                    "matched_terms": set(),
                    "agenda_occurrences": [],
                })
                record["matched_terms"].update(terms)
                record["agenda_occurrences"].append({
                    "event_id": event["EventId"],
                    "body_id": event["EventBodyId"],
                    "body": event["EventBodyName"],
                    "date": event["EventDate"][:10],
                    "agenda_url": event.get("EventAgendaFile"),
                    "agenda_sequence": item.get("EventItemAgendaSequence"),
                })

    for record in matches.values():
        by_event = {}
        for occurrence in record["agenda_occurrences"]:
            event_id = occurrence["event_id"]
            prior = by_event.get(event_id)
            if prior is None or (prior["agenda_sequence"] is None and occurrence["agenda_sequence"] is not None):
                by_event[event_id] = occurrence
        record["agenda_occurrences"] = list(by_event.values())

    def get_attachments(record):
        return record["matter_id"], fetch_json(api_url(f"matters/{record['matter_id']}/attachments"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        attachment_results = dict(pool.map(get_attachments, matches.values()))

    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8-sig"))
    known_urls: dict[str, list[str]] = {}
    for candidate in inventory["candidates"]:
        for key in ("source_url", "direct_file_url", "r2_url"):
            if candidate.get(key):
                known_urls.setdefault(candidate[key].rstrip("/"), []).append(candidate["id"])

    matters = []
    attachment_count = 0
    new_attachment_count = 0
    for matter_id in sorted(matches):
        record = matches[matter_id]
        attachments = []
        for item in sorted(attachment_results[matter_id], key=lambda row: (row.get("MatterAttachmentSort") or 0, row["MatterAttachmentId"])):
            url = item.get("MatterAttachmentHyperlink")
            if not url:
                continue
            existing = sorted(set(known_urls.get(url.rstrip("/"), [])))
            attachments.append({
                "discovery_id": stable_id(url),
                "attachment_id": item["MatterAttachmentId"],
                "name": item.get("MatterAttachmentName"),
                "url": url,
                "existing_inventory_ids": existing,
                "is_new_to_inventory": not bool(existing),
            })
            attachment_count += 1
            new_attachment_count += not bool(existing)
        matters.append({
            **{key: value for key, value in record.items() if key not in ("matched_terms", "agenda_occurrences")},
            "matched_terms": sorted(record["matched_terms"]),
            "agenda_occurrences": sorted(record["agenda_occurrences"], key=lambda row: (row["date"], row["event_id"])),
            "attachments": attachments,
        })

    event_counts_by_body = {
        str(body_id): sum(1 for event in events if event["EventBodyId"] == body_id)
        for body_id in body_ids
    }
    matched_occurrences_by_body = {
        str(body_id): sum(
            1 for matter in matters for occurrence in matter["agenda_occurrences"]
            if occurrence["body_id"] == body_id
        )
        for body_id in body_ids
    }

    output = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": API,
        "method": "Official Legistar events were bounded by date and body; each structured agenda item was topic-matched, then official matter attachments were enumerated and compared with ABQInfo inventory URLs.",
        "bounds": {"start_inclusive": args.start, "end_exclusive": args.end},
        "body_ids": body_ids,
        "bodies": [{"id": body_id, "name": bodies.get(body_id)} for body_id in body_ids],
        "topic_pattern": TOPIC_PATTERN.pattern,
        "counts": {
            "events_reviewed": len(events),
            "events_by_body_id": event_counts_by_body,
            "matched_matters": len(matters),
            "matched_agenda_occurrences_by_body_id": matched_occurrences_by_body,
            "attachments_found": attachment_count,
            "attachments_new_to_inventory_by_url": new_attachment_count,
        },
        "matters": matters,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output["counts"], separators=(",", ":")))


if __name__ == "__main__":
    main()
