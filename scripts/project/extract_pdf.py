import json
import sys

import pdfplumber
from pypdf import PdfReader


path = sys.argv[1]
reader = PdfReader(path)
text_pages = []
fallback_pages = []
with pdfplumber.open(path) as plumber:
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text_pages.append(page.extract_text() or "")
        except Exception:
            fallback_pages.append(page_number)
            text_pages.append(plumber.pages[page_number - 1].extract_text() or "")
text = "\n".join(text_pages)
links = []
seen_links = set()
for page_number, page in enumerate(reader.pages, start=1):
    for annotation_ref in page.get("/Annots", []) or []:
        annotation = annotation_ref.get_object()
        action = annotation.get("/A")
        uri = action.get("/URI") if action else None
        if not uri:
            continue
        uri = str(uri)
        key = (page_number, uri)
        if key in seen_links:
            continue
        seen_links.add(key)
        links.append({"page": page_number, "url": uri})
print(
    json.dumps(
        {
            "pages": len(reader.pages),
            "metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
            "text": text,
            "links": links,
            "pdfplumber_fallback_pages": fallback_pages,
        },
        ensure_ascii=True,
    )
)
