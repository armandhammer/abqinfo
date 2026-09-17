"""Validate deterministic annual DPM Executive Committee compilation outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json"
MASTER = ROOT / "project-state/master-inventory.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packets = manifest["annual_packets"]
    if [packet["year"] for packet in packets] != [2014, 2015, 2016, 2017, 2018]:
        raise AssertionError("Annual packet years are not the expected deterministic 2014-2018 sequence.")
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    included_ids = [component["source_master_id"] for packet in packets for component in packet["components"]]
    if len(included_ids) != 44 or len(included_ids) != len(set(included_ids)):
        raise AssertionError("Expected 44 unique DPM packet components.")
    required_agendas = {"src-a8dda335fb901049", "src-f2716dd03961455e", "src-48eb68305e18d8ad"}
    if required_agendas - set(included_ids):
        raise AssertionError("One or more required same-date agenda components is missing.")
    if "src-2448a4409efca23b" in included_ids:
        raise AssertionError("The duplicate April 15, 2015 minutes delivery was included.")
    excluded = {record["source_master_id"]: record for record in manifest["excluded_or_out_of_scope_records"]}
    if excluded.get("src-2448a4409efca23b", {}).get("disposition") != "exclude_duplicate_source":
        raise AssertionError("The genuine duplicate source does not have its justified exclusion.")
    expected_legacy_ids = set(included_ids) | {"src-2448a4409efca23b"}
    if set(included_ids) - set(component["source_master_id"] for packet in packets for component in packet["components"]):
        raise AssertionError("Included component coverage is internally inconsistent.")
    if set(excluded) - {"src-2448a4409efca23b", "src-28ce1d8748abb9a2", "src-89d7a6448976c52e", "src-04dfcbe1dcde70f8", "src-100dcafff14a7b22", "src-dc3a192d194d3d65"}:
        raise AssertionError("Manifest contains an unjustified legacy DPM exclusion.")
    if "src-2448a4409efca23b" not in set(excluded) or expected_legacy_ids - (set(included_ids) | set(excluded)):
        raise AssertionError("Eligible legacy DPM records are not exactly covered by inclusion or justified exclusion.")
    for packet in packets:
        components = packet["components"]
        identifiers = [component["source_master_id"] for component in components]
        if len(identifiers) != len(set(identifiers)):
            raise AssertionError(f"{packet['year']} contains a duplicate source component.")
        dates_and_kinds = [(component["meeting_date"], 0 if component["document_kind"].startswith("agenda") else 1) for component in components]
        if dates_and_kinds != sorted(dates_and_kinds):
            raise AssertionError(f"{packet['year']} components are not chronological.")
        if any(component["source_page_count"] is None for component in components):
            raise AssertionError(f"{packet['year']} lacks recorded component page counts.")
        output = ROOT / packet["local_output_path"]
        if not output.is_file():
            raise AssertionError(f"Missing packet output: {output}")
        if output.stat().st_size != packet["resulting_size_bytes"]:
            raise AssertionError(f"{packet['year']} output size does not match manifest.")
        if digest(output) != packet["resulting_sha256"]:
            raise AssertionError(f"{packet['year']} output SHA-256 does not match manifest.")
        page_count = len(PdfReader(str(output)).pages)
        if page_count != packet["resulting_page_count"]:
            raise AssertionError(f"{packet['year']} output page count does not match manifest.")
        if page_count < sum(component["source_page_count"] for component in components) + 1:
            raise AssertionError(f"{packet['year']} omits source pages.")
        for component in components:
            candidate = next(candidate for candidate in master["candidates"] if candidate["id"] == component["source_master_id"])
            is_agenda = "agenda" in " ".join(str(candidate.get(key) or "") for key in ("title", "direct_file_url", "r2_key")).lower()
            expected_kind = "agenda_approved_minutes_not_located" if component["source_master_id"] in {"src-7e7af2af147d96d7", "src-f6feb3549d055097"} else ("agenda" if is_agenda else "approved_minutes")
            if component["document_kind"] != expected_kind:
                raise AssertionError(f"{component['source_master_id']} has incorrect document_kind.")
            if component["document_kind"] == "agenda_approved_minutes_not_located" and "approved minutes not located" not in component["display_label"].lower():
                raise AssertionError(f"{packet['year']} agenda-only component lacks the required limitation.")
    print(f"PASS: validated {len(packets)} annual DPM packets with {sum(packet['component_count'] for packet in packets)} unique chronological components.")


if __name__ == "__main__":
    main()
