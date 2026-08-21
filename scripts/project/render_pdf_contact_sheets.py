import json
import math
import pathlib
import sys

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


def main() -> None:
    inventory_path = pathlib.Path(sys.argv[1])
    decisions_path = pathlib.Path(sys.argv[2])
    output_path = pathlib.Path(sys.argv[3])
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    decisions = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    by_id = {item["id"]: item for item in inventory["candidates"]}
    thumbs = []
    for decision in decisions["decisions"]:
        candidate = by_id[decision["id"]]
        pdf = pdfium.PdfDocument(candidate["local_path"])
        page_indexes = sorted({0, len(pdf) // 2, len(pdf) - 1})
        for page_index in page_indexes:
            image = pdf[page_index].render(scale=0.55).to_pil().convert("RGB")
            image.thumbnail((300, 390))
            canvas = Image.new("RGB", (320, 440), "white")
            canvas.paste(image, ((320 - image.width) // 2, 28))
            draw = ImageDraw.Draw(canvas)
            draw.text((8, 5), f"{decision['date']} - page {page_index + 1}/{len(pdf)}", fill="black")
            thumbs.append(canvas)
    columns = 4
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new("RGB", (columns * 320, rows * 440), "#d8d8d8")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * 320, (index // columns) * 440))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, optimize=True)


if __name__ == "__main__":
    main()
