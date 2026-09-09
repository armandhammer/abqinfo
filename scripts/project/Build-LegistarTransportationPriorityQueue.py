#!/usr/bin/env python3
"""Build a transportation-focused, matter-aware queue from CABQ Legistar discovery."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


CORE = re.compile(
    r"\b(transportation|transit|rail|road(?:way)?|traffic|pedestrian|walk(?:ing|ability)?|"
    r"bicycl\w*|bike|trail|sidewalk|corridor|multi[- ]modal|parking|airport|aviation|"
    r"vision zero|complete streets|right[- ]of[- ]way|streetscape|rapid transit|ART project)\b",
    re.IGNORECASE,
)
CORRIDOR = re.compile(r"\b(route 66|avenue|boulevard|street|road)\b", re.IGNORECASE)
CORRIDOR_ACTION = re.compile(
    r"\b(plan|study|report|analysis|assessment|design|improvement|reconstruct|rehabilitat|convert|safety|road diet)\b",
    re.IGNORECASE,
)
MAJOR_MODE = re.compile(
    r"\b(transit|rail|bicycl\w*|bike|pedestrian|trail|complete streets|vision zero|multi[- ]modal|corridor)\b",
    re.IGNORECASE,
)
DURABLE = re.compile(
    r"\b(plan|study|report|assessment|analysis|recommendations?|design|map|appendix|attachment|exhibit)\b",
    re.IGNORECASE,
)
REPORT_PACKET = re.compile(r"\b(plan|study|report|assessment|analysis)\b", re.IGNORECASE)
PROCUREMENT = re.compile(
    r"\b(mayor['’]s recommendation|recommendation of award|award to|consultants?|engineering services|design services)\b",
    re.IGNORECASE,
)
GENERIC_WRAPPER = re.compile(
    r"^(?:(?:FS|CS) )?(?:AC|C|EC|M|O|R)[- _]?\d+(?:\.pdf)?$",
    re.IGNORECASE,
)
APPEAL = re.compile(r"\bappeal", re.IGNORECASE)
LAND_USE_CASE = re.compile(r"\b(site plan|zone|zoning|variance|special exception)\b", re.IGNORECASE)


def role(name: str, matter_file: str | None, matter_title: str) -> str:
    if re.search(r"enacted", name, re.IGNORECASE):
        return "enacted_legislation"
    if re.search(r"amendment|blueline|redline|greenline", name, re.IGNORECASE):
        return "legislative_amendment_or_redline"
    if DURABLE.search(name) and not GENERIC_WRAPPER.fullmatch(name.strip()):
        return "substantive_attachment"
    if re.search(r"final|draft|substitute", name, re.IGNORECASE):
        return "legislative_draft_or_final"
    if (
        (matter_file or "").upper().startswith("EC-")
        and REPORT_PACKET.search(matter_title)
        and not PROCUREMENT.search(matter_title)
    ):
        return "potential_substantive_packet"
    if GENERIC_WRAPPER.fullmatch(name.strip()) or re.match(
        r"^(?:DAC|NODAC|NOHAC|D\(\d+\)AC)[- _]?\d", name, re.IGNORECASE
    ):
        return "legislative_or_administrative_wrapper"
    return "other_attachment"


def is_transportation_matter(title: str) -> bool:
    if APPEAL.search(title) and LAND_USE_CASE.search(title):
        return False
    return bool(CORE.search(title) or (CORRIDOR.search(title) and CORRIDOR_ACTION.search(title)))


def score(matter: dict, attachment: dict, delivery_role: str) -> int:
    title = matter.get("title") or ""
    name = attachment.get("name") or ""
    value = 6
    value += min(8, 2 * len({match.group(0).lower() for match in CORE.finditer(title)}))
    if MAJOR_MODE.search(title):
        value += 6
    if DURABLE.search(title):
        value += 5
    if CORRIDOR.search(title) and CORRIDOR_ACTION.search(title):
        value += 4
    if delivery_role == "substantive_attachment":
        value += 9
    elif delivery_role == "potential_substantive_packet":
        value += 8
    elif delivery_role == "enacted_legislation":
        value += 7
    elif delivery_role == "legislative_amendment_or_redline":
        value += 1
    elif delivery_role == "legislative_draft_or_final":
        value += 2
    else:
        value -= 2
    if MAJOR_MODE.search(name):
        value += 3
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    discovery = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    queue = []
    eligible_matters = 0
    eligible_attachments = 0
    for matter in discovery["matters"]:
        title = matter.get("title") or ""
        if not is_transportation_matter(title):
            continue
        eligible_matters += 1
        latest = max(row["date"] for row in matter["agenda_occurrences"])
        versions = []
        for attachment in matter["attachments"]:
            if not attachment.get("is_new_to_inventory"):
                continue
            delivery_role = role(attachment.get("name") or "", matter.get("matter_file"), title)
            versions.append({
                "discovery_id": attachment["discovery_id"],
                "attachment_name": attachment.get("name") or "",
                "attachment_url": attachment["url"],
                "delivery_role": delivery_role,
            })
        if not versions:
            continue
        eligible_attachments += len(versions)

        if PROCUREMENT.search(title) and not any(
            REPORT_PACKET.search(version["attachment_name"]) for version in versions
        ):
            continue

        primary_roles = {
            "substantive_attachment", "potential_substantive_packet", "enacted_legislation"
        }
        selected = [version for version in versions if version["delivery_role"] in primary_roles]
        if not selected:
            selected = [max(
                versions,
                key=lambda version: (
                    version["delivery_role"] == "legislative_draft_or_final",
                    version["delivery_role"] == "legislative_amendment_or_redline",
                    version["attachment_name"],
                ),
            )]

        related = sorted(versions, key=lambda version: (version["delivery_role"], version["attachment_name"], version["attachment_url"]))
        for selected_version in selected:
            attachment = next(
                item for item in matter["attachments"]
                if item["discovery_id"] == selected_version["discovery_id"]
            )
            queue.append({
                "priority_score": score(matter, attachment, selected_version["delivery_role"]),
                "discovery_id": attachment["discovery_id"],
                "matter_id": matter["matter_id"],
                "matter_file": matter.get("matter_file"),
                "matter_type": matter.get("matter_type"),
                "matter_title": title,
                "latest_agenda_date": latest,
                "attachment_name": attachment.get("name") or "",
                "attachment_url": attachment["url"],
                "delivery_role": selected_version["delivery_role"],
                "related_delivery_versions": related,
                "wrapper_policy": (
                    "Preserve this attachment as a versioned Legistar delivery record. Before archival, compare its "
                    "hash and extracted/rendered substantive content with related Legistar versions and existing "
                    "City-source copies; retain one canonical original and record wrapper relationships."
                ),
                "agenda_occurrences": matter["agenda_occurrences"],
                "review_status": "pending transportation document review",
            })

    queue.sort(key=lambda row: (row.get("matter_file") or "", row["attachment_url"]))
    queue.sort(key=lambda row: row["latest_agenda_date"], reverse=True)
    queue.sort(key=lambda row: row["priority_score"], reverse=True)
    total_ranked = len(queue)
    queue = queue[: args.limit]
    output = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_discovery": args.input.replace("\\", "/"),
        "selection": (
            "Transportation matters are selected from official CABQ Legistar titles. Substantive plans, studies, "
            "reports, corridor/mode records, enacted legislation, and potential executive-communication packets "
            "are prioritized. Zoning appeals and generic plan references are excluded. Related legislative files "
            "remain explicit versioned delivery records rather than independent canonical documents."
        ),
        "limit": args.limit,
        "count": len(queue),
        "eligible_transportation_matters": eligible_matters,
        "eligible_new_attachment_versions": eligible_attachments,
        "ranked_primary_records_before_limit": total_ranked,
        "items": queue,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "queued": len(queue),
        "eligible_transportation_matters": eligible_matters,
        "eligible_new_attachment_versions": eligible_attachments,
        "ranked_primary_records_before_limit": total_ranked,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
