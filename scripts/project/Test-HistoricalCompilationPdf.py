#!/usr/bin/env python3
"""Verify that compiled source pages render and extract identically to originals."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops
from pypdf import PdfReader


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def image_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Image.open(path) as image:
        digest.update(image.convert("RGB").tobytes())
    return digest.hexdigest()


def render(pdftoppm: str, pdf: Path, prefix: Path, first: int | None = None, last: int | None = None) -> list[Path]:
    command = [pdftoppm, "-png", "-r", "72"]
    if first is not None:
        command.extend(["-f", str(first), "-l", str(last)])
    command.extend([str(pdf), str(prefix)])
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
    return sorted(prefix.parent.glob(prefix.name + "-*.png"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--build-validation", required=True, type=Path)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    build = json.loads(args.build_validation.read_text(encoding="utf-8-sig"))
    compiled_path = Path(build["output_path"])
    compiled = PdfReader(str(compiled_path))
    source_by_id = {source["candidate_id"]: source for source in manifest["sources"]}
    checks = []

    with TemporaryDirectory(prefix="abqinfo-compilation-qa-") as temp_dir:
        temp = Path(temp_dir)
        for entry in build["sources"]:
            source = source_by_id[entry["candidate_id"]]
            source_path = Path(source["local_path"])
            source_reader = PdfReader(str(source_path))
            source_start = entry["section_page"] + 1
            source_end = source_start + entry["source_pages"] - 1
            original_images = render(args.pdftoppm, source_path, temp / f"{entry['candidate_id']}-original")
            compiled_images = render(args.pdftoppm, compiled_path, temp / f"{entry['candidate_id']}-compiled", source_start, source_end)
            if len(original_images) != len(compiled_images) or len(original_images) != entry["source_pages"]:
                raise ValueError(f"Rendered page-count mismatch for {entry['candidate_id']}")
            page_checks = []
            for index, (original_image, compiled_image) in enumerate(zip(original_images, compiled_images)):
                with Image.open(original_image) as left, Image.open(compiled_image) as right:
                    if left.size != right.size or ImageChops.difference(left.convert("RGB"), right.convert("RGB")).getbbox() is not None:
                        raise ValueError(f"Rendered source page changed for {entry['candidate_id']} page {index + 1}")
                original_text = normalize(source_reader.pages[index].extract_text())
                compiled_text = normalize(compiled.pages[source_start - 1 + index].extract_text())
                if original_text != compiled_text:
                    raise ValueError(f"Extracted source text changed for {entry['candidate_id']} page {index + 1}")
                page_checks.append({"page": index + 1, "rendered_pixel_sha256": image_sha(original_image), "text_equal": True})
            separator = compiled.pages[entry["section_page"] - 1]
            annotations = separator.get("/Annots") or []
            uri_count = sum(1 for annotation in annotations if annotation.get_object().get("/A", {}).get("/URI"))
            if uri_count < 2:
                raise ValueError(f"Separator lacks both provenance links for {entry['candidate_id']}")
            checks.append({
                "candidate_id": entry["candidate_id"],
                "source_pages": entry["source_pages"],
                "compiled_source_start_page": source_start,
                "rendered_pages_pixel_identical": True,
                "extracted_text_identical": True,
                "separator_uri_links": uri_count,
                "page_checks": page_checks,
            })

    result = {
        "schema_version": 1,
        "compilation": str(compiled_path).replace("\\", "/"),
        "source_document_count": len(checks),
        "source_page_count": sum(item["source_pages"] for item in checks),
        "rendered_source_pages_pixel_identical": True,
        "extracted_source_text_identical": True,
        "all_separator_provenance_links_present": True,
        "checks": checks,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("compilation", "source_document_count", "source_page_count", "rendered_source_pages_pixel_identical", "extracted_source_text_identical")}))


if __name__ == "__main__":
    main()
