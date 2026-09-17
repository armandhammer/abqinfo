"""Build local annual DPM Executive Committee compilation PDFs from a manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader, PdfWriter
import fitz


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "project-state/discovery/dpm-executive-committee-consolidation-manifest-2026-09-17.json"
OUTPUT_DIR = ROOT / "output/pdf/dpm-executive-committee"
TEMP_INPUT_DIR = ROOT / "tmp/pdfs/dpm-input"


def component_path(component: dict) -> Path:
    if component.get("local_path"):
        return ROOT / component["local_path"]
    return TEMP_INPUT_DIR / f"{component['source_master_id']}.pdf"


def make_contents_page(packet: dict, output: Path) -> None:
    doc = fitz.open()
    def new_contents_page(continuation: bool):
        page = doc.new_page(width=612, height=792)
        page.insert_text((54, 54), "City of Albuquerque", fontsize=16, fontname="hebo")
        heading = f"Development Process Manual Executive Committee\nAgendas and Minutes - {packet['year']}"
        if continuation:
            heading += "\nContents (continued)"
        page.insert_text((54, 82), heading, fontsize=18 if not continuation else 14, fontname="hebo", lineheight=1.25)
        if not continuation:
            page.insert_text((54, 152), "Contents", fontsize=13, fontname="hebo")
            return page, 176
        return page, 148

    page, y = new_contents_page(False)
    for component in packet["components"]:
        if y + 34 > 684:
            page.insert_textbox(fitz.Rect(54, 720, 558, 760), "Original City PDF pages follow in chronological order. Agenda-only records are not minutes substitutes.", fontsize=8, fontname="helv", lineheight=1.15)
            page, y = new_contents_page(True)
        label = component["display_label"]
        if component["document_kind"] == "agenda_approved_minutes_not_located":
            label += " (agenda only; does not establish meeting occurrence)"
        page.insert_textbox(fitz.Rect(54, y, 558, y + 34), label, fontsize=10, fontname="helv", lineheight=1.15)
        y += 38
    footer = "Original City PDF pages follow in chronological order. Agenda-only records are not minutes substitutes."
    page.insert_textbox(fitz.Rect(54, 720, 558, 760), footer, fontsize=8, fontname="helv", lineheight=1.15)
    doc.save(output, garbage=4, deflate=True)
    doc.close()


def build_packet(packet: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / packet["proposed_filename"]
    cover = OUTPUT_DIR / f".{packet['year']}-contents.pdf"
    make_contents_page(packet, cover)
    writer = PdfWriter()
    writer.append(str(cover))
    contents_page_count = len(PdfReader(str(cover)).pages)
    total_source_pages = 0
    for component in packet["components"]:
        source = component_path(component)
        if not source.is_file():
            raise FileNotFoundError(f"Missing component source: {source}")
        reader = PdfReader(str(source))
        component["source_page_count"] = len(reader.pages)
        total_source_pages += len(reader.pages)
        writer.append(str(source))
    with output.open("wb") as handle:
        writer.write(handle)
    cover.unlink()
    data = output.read_bytes()
    packet["resulting_page_count"] = total_source_pages + contents_page_count
    packet["resulting_size_bytes"] = len(data)
    packet["resulting_sha256"] = hashlib.sha256(data).hexdigest()
    packet["local_output_path"] = str(output.relative_to(ROOT)).replace("\\", "/")
    packet["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for packet in manifest["annual_packets"]:
        build_packet(packet)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for packet in manifest["annual_packets"]:
        print(f"{packet['proposed_filename']}: {packet['resulting_page_count']} pages, {packet['resulting_size_bytes']} bytes, {packet['resulting_sha256']}")


if __name__ == "__main__":
    main()
