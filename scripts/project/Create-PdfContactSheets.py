#!/usr/bin/env python3
"""Render every PDF page as compact contact sheets for visual review."""

from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--rows", type=int, default=5)
    args = parser.parse_args()

    pdf = Path(args.pdf)
    output_dir = Path(args.output_dir)
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    prefix = pages_dir / pdf.stem
    subprocess.run([
        args.pdftoppm, "-jpeg", "-r", "20", str(pdf), str(prefix)
    ], check=True)
    images = sorted(pages_dir.glob(f"{pdf.stem}-*.jpg"))
    expected = len(PdfReader(pdf).pages)
    if len(images) != expected:
        raise RuntimeError(f"Expected {expected} rendered pages, found {len(images)}")

    first = Image.open(images[0])
    thumb_w, thumb_h = first.size
    label_h = 22
    per_sheet = args.columns * args.rows
    for sheet_number in range(math.ceil(len(images) / per_sheet)):
        subset = images[sheet_number * per_sheet:(sheet_number + 1) * per_sheet]
        sheet = Image.new("RGB", (args.columns * thumb_w, args.rows * (thumb_h + label_h)), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, image_path in enumerate(subset):
            page_number = sheet_number * per_sheet + slot + 1
            x = (slot % args.columns) * thumb_w
            y = (slot // args.columns) * (thumb_h + label_h)
            with Image.open(image_path) as page:
                sheet.paste(page.convert("RGB"), (x, y))
            draw.text((x + 4, y + thumb_h + 3), f"Page {page_number}", fill="black")
        sheet.save(output_dir / f"{pdf.stem}-sheet-{sheet_number + 1:02d}.jpg", quality=90)
    print(f"{pdf.stem}: {expected} pages, {math.ceil(len(images) / per_sheet)} sheets")


if __name__ == "__main__":
    main()
