#!/usr/bin/env python3
"""Audit a CABQ Legistar priority queue against current inventory and matter families."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.parse
from pathlib import Path


CORE_TRANSPORTATION = re.compile(
    r"\b(transportation|transit|rail|road(?:way)?|traffic|pedestrian|walk(?:ing|ability)?|"
    r"bicycl\w*|bike|trail|sidewalk|corridor|multi[- ]modal|parking|airport|aviation|"
    r"vision zero|complete streets|right[- ]of[- ]way|streetscape)\b",
    re.IGNORECASE,
)
GENERAL_CAPITAL = re.compile(
    r"\b(capital implementation program|capital improvements?|decade plan|infrastructure capital|ICIP)\b",
    re.IGNORECASE,
)
LAND_USE = re.compile(
    r"\b(redevelopment|land use|zoning|site plan|metropolitan redevelopment|master plan)\b",
    re.IGNORECASE,
)
CORRIDOR = re.compile(r"\b(route 66|avenue|boulevard|street|road)\b", re.IGNORECASE)
CORRIDOR_ACTION = re.compile(
    r"\b(plan|study|report|analysis|assessment|design|improvement|reconstruct|rehabilitat|convert|safety|road diet)\b",
    re.IGNORECASE,
)
SUBSTANTIVE = re.compile(
    r"\b(plan|study|report|assessment|analysis|recommendations?|design|map|attachments?|exhibits?)\b",
    re.IGNORECASE,
)
MATTER_CODE = re.compile(r"\b(?:AC|C|EC|M|O|R)[- _]\d{2}[- _]\d+\b", re.IGNORECASE)


def normalized_code(value: str | None) -> str | None:
    if not value:
        return None
    return value.upper().replace("_", "-").replace(" ", "-")


def matter_codes(candidate: dict) -> set[str]:
    values: list[str] = []
    for key in ("title", "source_url", "direct_file_url", "parent_url", "exclusion_reason"):
        if candidate.get(key):
            values.append(str(candidate[key]))
    values.extend(str(value) for value in candidate.get("processing_notes", []))
    codes = {normalized_code(match.group(0)) for match in MATTER_CODE.finditer(" ".join(values))}
    return {code for code in codes if code}


def decision_matter_code(decision: dict) -> str | None:
    source_page = decision.get("source_page") or ""
    query = urllib.parse.parse_qs(urllib.parse.urlparse(source_page).query)
    search = query.get("Search", [None])[0]
    if search and MATTER_CODE.search(search):
        return normalized_code(MATTER_CODE.search(search).group(0))
    for value in (decision.get("title"), decision.get("description")):
        if value and MATTER_CODE.search(value):
            return normalized_code(MATTER_CODE.search(value).group(0))
    return None


def delivery_role(item: dict) -> str:
    name = (item.get("attachment_name") or "").strip()
    title = item.get("matter_title") or ""
    matter_file = normalized_code(item.get("matter_file")) or ""
    if re.search(r"enacted", name, re.IGNORECASE):
        return "enacted_legislation"
    if re.search(r"\b(amendment|blueline|redline|committee substitute|floor substitute)\b", name, re.IGNORECASE):
        return "legislative_amendment"
    if SUBSTANTIVE.search(name) and not re.fullmatch(r"(?:FS |CS )?[A-Z]+[- _]?\d+(?:final)?", name, re.IGNORECASE):
        return "substantive_attachment"
    if re.search(r"(final|draft)", name, re.IGNORECASE):
        return "legislative_draft_or_final"
    if matter_file.startswith("EC-") and SUBSTANTIVE.search(title):
        return "potential_substantive_packet"
    if re.match(r"^(?:AC|C|EC|M|O|R|FS R|CS R|DAC|NODAC|NOHAC|D\(\d+\)AC)[- _]?\d", name, re.IGNORECASE):
        return "legislative_or_administrative_wrapper"
    return "other_attachment"


def relevance(item: dict) -> str:
    title = item.get("matter_title") or ""
    name = item.get("attachment_name") or ""
    text = " ".join((title, name))
    if re.search(r"\bappeal", title, re.IGNORECASE) and re.search(r"\b(site plan|zoning|variance)\b", title, re.IGNORECASE):
        return "land_use_or_redevelopment"
    if CORE_TRANSPORTATION.search(text):
        return "core_transportation"
    if CORRIDOR.search(title) and CORRIDOR_ACTION.search(title):
        return "core_transportation"
    if re.search(r"\bstreet\b", text, re.IGNORECASE) and re.search(
        r"\b(traffic|roadway|convert|transportation|transit|bicycle|pedestrian|sidewalk|capital implementation program)\b",
        text,
        re.IGNORECASE,
    ):
        return "core_transportation"
    if GENERAL_CAPITAL.search(text):
        return "general_capital"
    if LAND_USE.search(text):
        return "land_use_or_redevelopment"
    return "incidental_or_false_positive"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--inventory", default="project-state/master-inventory.json")
    parser.add_argument("--decisions", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    queue_doc = json.loads(Path(args.queue).read_text(encoding="utf-8-sig"))
    inventory_doc = json.loads(Path(args.inventory).read_text(encoding="utf-8-sig"))
    candidates = inventory_doc["candidates"]

    exact_inventory: dict[str, list[dict]] = {}
    matter_inventory: dict[str, list[dict]] = {}
    for candidate in candidates:
        for key in ("source_url", "direct_file_url", "r2_url"):
            if candidate.get(key):
                exact_inventory.setdefault(candidate[key].rstrip("/"), []).append(candidate)
        expected_id = candidate.get("id")
        if expected_id:
            exact_inventory.setdefault(expected_id, []).append(candidate)
        for code in matter_codes(candidate):
            matter_inventory.setdefault(code, []).append(candidate)

    reviewed_matters: dict[str, list[dict]] = {}
    for decision_path in args.decisions:
        decision_doc = json.loads(Path(decision_path).read_text(encoding="utf-8-sig"))
        for decision in decision_doc.get("decisions", []):
            code = decision_matter_code(decision)
            if code:
                reviewed_matters.setdefault(code, []).append({
                    "id": decision.get("id"),
                    "title": decision.get("title"),
                    "source": decision_path.replace("\\", "/"),
                })

    audited = []
    for item in queue_doc["items"]:
        code = normalized_code(item.get("matter_file"))
        url = (item.get("attachment_url") or "").rstrip("/")
        expected_id = "src-" + item["discovery_id"].removeprefix("legistar-")
        exact = {candidate["id"]: candidate for candidate in exact_inventory.get(url, [])}
        for candidate in exact_inventory.get(expected_id, []):
            exact[candidate["id"]] = candidate
        family = {candidate["id"]: candidate for candidate in matter_inventory.get(code or "", [])}
        role = item.get("delivery_role") or delivery_role(item)
        topic = relevance(item)

        if exact:
            disposition = "resolved_exact_inventory_record"
        elif reviewed_matters.get(code or ""):
            disposition = "reviewed_matter_version_record"
        elif family:
            disposition = "reconciled_matter_family_inventory"
        elif topic == "core_transportation" and role in (
            "substantive_attachment", "potential_substantive_packet", "enacted_legislation"
        ):
            disposition = "high_priority_transportation_review"
        elif topic == "core_transportation":
            disposition = "transportation_wrapper_review_after_canonical"
        elif topic == "general_capital" and role == "enacted_legislation":
            disposition = "secondary_enacted_capital_review"
        else:
            disposition = "defer_outside_transportation_priority"

        audited.append({
            **item,
            "matter_file": code,
            "transportation_relevance": topic,
            "delivery_role": role,
            "audit_disposition": disposition,
            "exact_inventory_matches": [
                {"id": row["id"], "status": row["status"], "title": row.get("title")}
                for row in sorted(exact.values(), key=lambda row: row["id"])
            ],
            "matter_family_inventory_matches": [
                {"id": row["id"], "status": row["status"], "title": row.get("title")}
                for row in sorted(family.values(), key=lambda row: row["id"])
            ],
            "reviewed_canonical_records": reviewed_matters.get(code or "", []),
        })

    groups = []
    by_matter: dict[str, list[dict]] = {}
    for item in audited:
        by_matter.setdefault(item.get("matter_file") or "unknown", []).append(item)
    for code in sorted(by_matter):
        rows = by_matter[code]
        groups.append({
            "matter_file": code,
            "matter_title": rows[0].get("matter_title"),
            "attachment_count": len(rows),
            "transportation_relevance": rows[0]["transportation_relevance"],
            "delivery_roles": sorted({row["delivery_role"] for row in rows}),
            "audit_dispositions": sorted({row["audit_disposition"] for row in rows}),
            "reviewed_canonical_records": rows[0]["reviewed_canonical_records"],
            "matter_family_inventory_record_count": len(rows[0]["matter_family_inventory_matches"]),
        })

    def counts_by(key: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in audited:
            result[row[key]] = result.get(row[key], 0) + 1
        return dict(sorted(result.items()))

    output = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_queue": args.queue.replace("\\", "/"),
        "inventory": args.inventory.replace("\\", "/"),
        "method": (
            "Every queued URL was reconciled to the current inventory by exact URL and stable ID, then grouped by "
            "legislative matter. Attachments are classified as substantive records, enacted versions, amendments, "
            "draft/final versions, or delivery wrappers; related versions remain separate delivery records."
        ),
        "counts": {
            "items": len(audited),
            "matter_families": len(groups),
            "exact_inventory_matches": sum(bool(row["exact_inventory_matches"]) for row in audited),
            "reviewed_matter_versions": sum(bool(row["reviewed_canonical_records"]) for row in audited),
            "by_transportation_relevance": counts_by("transportation_relevance"),
            "by_delivery_role": counts_by("delivery_role"),
            "by_audit_disposition": counts_by("audit_disposition"),
        },
        "matter_groups": groups,
        "items": audited,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output["counts"], separators=(",", ":")))


if __name__ == "__main__":
    main()
