"""Validate deterministic annual DPM Executive Committee compilation outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packets = manifest["annual_packets"]
    if [packet["year"] for packet in packets] != [2014, 2015, 2016, 2017, 2018]:
        raise AssertionError("Annual packet years are not the expected deterministic 2014-2018 sequence.")
    for packet in packets:
        components = packet["components"]
        identifiers = [component["source_master_id"] for component in components]
        if len(identifiers) != len(set(identifiers)):
            raise AssertionError(f"{packet['year']} contains a duplicate source component.")
        dates = [component["meeting_date"] for component in components]
        if dates != sorted(dates):
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
            if component["document_kind"] == "agenda_approved_minutes_not_located" and "approved minutes not located" not in component["display_label"].lower():
                raise AssertionError(f"{packet['year']} agenda-only component lacks the required limitation.")
    print(f"PASS: validated {len(packets)} annual DPM packets with {sum(packet['component_count'] for packet in packets)} unique chronological components.")


if __name__ == "__main__":
    main()
