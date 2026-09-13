#!/usr/bin/env python3
"""Build a clearly labelled ABQInfo browsing compilation from preserved PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def footer(canv: canvas.Canvas, doc) -> None:
    canv.saveState()
    canv.setFont("Helvetica", 8)
    canv.setFillColor(colors.HexColor("#52606d"))
    canv.drawCentredString(letter[0] / 2, 0.42 * inch, f"ABQInfo historical compilation - page {doc.page}")
    canv.restoreState()


def build_intro(manifest: dict, entries: list[dict], path: Path) -> int:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CompilationTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#123b5d"), alignment=TA_CENTER, spaceAfter=14))
    styles.add(ParagraphStyle(name="CompilationSub", parent=styles["Normal"], fontSize=11, leading=15, textColor=colors.HexColor("#364152"), alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="Notice", parent=styles["Normal"], fontSize=9.5, leading=13, backColor=colors.HexColor("#eef5f9"), borderColor=colors.HexColor("#85a9bd"), borderWidth=0.7, borderPadding=10, spaceAfter=18))
    styles.add(ParagraphStyle(name="TOC", parent=styles["Normal"], fontSize=9.5, leading=12))
    styles.add(ParagraphStyle(name="TOCHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=colors.white))

    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.65 * inch, title=manifest["title"], author="ABQInfo")
    story = [
        Spacer(1, 0.25 * inch),
        Paragraph(manifest["title"], styles["CompilationTitle"]),
        Paragraph("ABQInfo historical browsing compilation", styles["CompilationSub"]),
        Paragraph(
            "This file is an ABQInfo-created convenience compilation, not a single publication issued by the City of Albuquerque. "
            "Each City document is reproduced as a complete section after a provenance sheet. The separately archived original files, "
            "their checksums, and their official source links remain the archival record.",
            styles["Notice"],
        ),
        Paragraph("Contents", styles["Heading2"]),
        Spacer(1, 0.08 * inch),
    ]
    rows = [[Paragraph("Meeting record", styles["TOCHeader"]), Paragraph("Section", styles["TOCHeader"])]]
    for entry in entries:
        rows.append([Paragraph(f"<b>{entry['date']}</b><br/>{entry['title']}", styles["TOC"]), Paragraph(f"page {entry['section_page']}", styles["TOC"])])
    table = Table(rows, colWidths=[6.15 * inch, 0.7 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123b5d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b7c4ce")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
    ]))
    story.extend([table, Spacer(1, 0.18 * inch), Paragraph(f"Coverage: {manifest['coverage_note']}", styles["Normal"]), PageBreak(), Paragraph("Compilation provenance", styles["Heading2"]), Paragraph(manifest["provenance_note"], styles["Normal"]), Spacer(1, 0.14 * inch), Paragraph("How to cite a section", styles["Heading3"]), Paragraph("Cite the original City document title and date shown on its provenance sheet. Use the original archive URL when a stable file citation is required; use this compilation only as a convenient collected edition.", styles["Normal"])])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return len(PdfReader(str(path)).pages)


def build_separator(manifest: dict, entry: dict, path: Path, compilation_page: int) -> None:
    canv = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    canv.setTitle(f"{entry['date']} - {entry['title']}")
    canv.setFillColor(colors.HexColor("#123b5d"))
    canv.rect(0, height - 1.25 * inch, width, 1.25 * inch, fill=1, stroke=0)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("SectionTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#123b5d"), spaceAfter=12)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#263746"), spaceAfter=8)
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8.2, leading=11, textColor=colors.HexColor("#52606d"), wordWrap="CJK")
    story = [
        Paragraph("Original City record", styles["Heading3"]),
        Paragraph(entry["title"], title_style),
        Paragraph(f"<b>Meeting date:</b> {entry['date']}<br/><b>Original pages:</b> {entry['source_pages']}<br/><b>Inventory ID:</b> {entry['candidate_id']}", body_style),
        Paragraph(f"<b>Official City source:</b> <link href=\"{entry['source_url']}\" color=\"#075985\">{entry['source_url']}</link>", small_style),
        Spacer(1, 0.08 * inch),
        Paragraph(f"<b>Byte-identical archived original:</b> <link href=\"{entry['archive_url']}\" color=\"#075985\">{entry['archive_url']}</link>", small_style),
        Spacer(1, 0.08 * inch),
        Paragraph(f"<b>Original SHA-256:</b> {entry['checksum_sha256']}<br/><b>Original size:</b> {entry['size_bytes']:,} bytes", small_style),
        Spacer(1, 0.22 * inch),
        Paragraph("The complete original document begins on the following page. It remains separately available at the archive URL above.", body_style),
    ]
    frame_x, frame_y, frame_w, frame_h = 0.72 * inch, 0.72 * inch, width - 1.44 * inch, height - 2.25 * inch
    from reportlab.platypus import Frame
    Frame(frame_x, frame_y, frame_w, frame_h, showBoundary=0).addFromList(story, canv)
    canv.setFont("Helvetica", 8)
    canv.setFillColor(colors.HexColor("#52606d"))
    canv.drawRightString(width - 0.65 * inch, 0.42 * inch, f"{manifest['short_title']} - compilation page {compilation_page}")
    canv.save()


def build(manifest_path: Path, output_path: Path, validation_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    entries = []
    for source in manifest["sources"]:
        path = Path(source["local_path"])
        if not path.exists():
            raise FileNotFoundError(path)
        actual_size = path.stat().st_size
        actual_sha = sha256(path)
        if actual_size != source["size_bytes"] or actual_sha != source["checksum_sha256"]:
            raise ValueError(f"Source integrity mismatch: {source['candidate_id']}")
        entries.append({**source, "source_pages": len(PdfReader(str(path)).pages), "section_page": 0})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="abqinfo-compilation-") as temp_dir:
        temp = Path(temp_dir)
        intro = temp / "intro.pdf"
        intro_pages = build_intro(manifest, entries, intro)
        cursor = intro_pages + 1
        for entry in entries:
            entry["section_page"] = cursor
            cursor += 1 + entry["source_pages"]
        regenerated_pages = build_intro(manifest, entries, intro)
        if regenerated_pages != intro_pages:
            raise ValueError("Contents pagination changed after page numbers were inserted")

        writer = PdfWriter()
        writer.append(str(intro))
        for index, entry in enumerate(entries):
            separator = temp / f"separator-{index:03d}.pdf"
            build_separator(manifest, entry, separator, entry["section_page"])
            section_index = len(writer.pages)
            writer.append(str(separator))
            writer.add_outline_item(f"{entry['date']} - {entry['title']}", section_index)
            writer.append(entry["local_path"])
        writer.add_metadata({
            "/Title": manifest["title"],
            "/Author": "ABQInfo; original records by the City of Albuquerque",
            "/Subject": "Historical browsing compilation with provenance links to separately preserved originals",
            "/Keywords": "Albuquerque, Development Process Manual, Executive Committee, minutes, historical compilation",
        })
        with output_path.open("wb") as stream:
            writer.write(stream)

    final_reader = PdfReader(str(output_path))
    expected_pages = intro_pages + sum(1 + entry["source_pages"] for entry in entries)
    if len(final_reader.pages) != expected_pages:
        raise ValueError(f"Final page mismatch: {len(final_reader.pages)} != {expected_pages}")
    result = {
        "schema_version": 1,
        "title": manifest["title"],
        "output_path": str(output_path).replace("\\", "/"),
        "size_bytes": output_path.stat().st_size,
        "checksum_sha256": sha256(output_path),
        "page_count": len(final_reader.pages),
        "intro_pages": intro_pages,
        "source_count": len(entries),
        "sources": [
            {
                "candidate_id": entry["candidate_id"],
                "date": entry["date"],
                "title": entry["title"],
                "source_pages": entry["source_pages"],
                "section_page": entry["section_page"],
                "size_bytes": entry["size_bytes"],
                "checksum_sha256": entry["checksum_sha256"],
                "official_source_url": entry["source_url"],
                "archive_url": entry["archive_url"],
            }
            for entry in entries
        ],
        "integrity_note": "Every input was verified against its recorded exact byte size and SHA-256 before assembly. Separately archived originals remain unchanged.",
    }
    validation_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output_path), "pages": result["page_count"], "bytes": result["size_bytes"], "sha256": result["checksum_sha256"]}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    args = parser.parse_args()
    build(args.manifest, args.output, args.validation)


if __name__ == "__main__":
    main()
