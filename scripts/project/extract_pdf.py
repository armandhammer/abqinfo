import json
import sys

from pypdf import PdfReader


path = sys.argv[1]
reader = PdfReader(path)
text = "\n".join((page.extract_text() or "") for page in reader.pages)
print(
    json.dumps(
        {
            "pages": len(reader.pages),
            "metadata": {str(key): str(value) for key, value in (reader.metadata or {}).items()},
            "text": text,
        },
        ensure_ascii=True,
    )
)
