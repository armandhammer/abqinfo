#!/usr/bin/env python3
"""Materialize exact 2011 compilation inputs locally without changing R2."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "project-state/discovery/2011-capital-spending-consolidation-manifest-2026-09-18.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def valid(path: Path, source: dict) -> bool:
    return path.is_file() and path.stat().st_size == source["size_bytes"] and digest(path) == source["checksum_sha256"]


def existing_source(source: dict) -> Path | None:
    matches = list((ROOT / "research/staging").rglob(f"{source['candidate_id']}.pdf"))
    for match in matches:
        if valid(match, source):
            return match
    return None


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "ABQInfo/1.0 provenance-preserving local compilation preparation"})
    temporary = target.with_suffix(".download")
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    temporary.replace(target)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = {source["candidate_id"]: source for compilation in manifest["compilations"] for source in compilation["sources"]}
    reused = downloaded = already_valid = 0
    for source in sources.values():
        target = ROOT / source["local_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if valid(target, source):
            already_valid += 1
            continue
        local = existing_source(source)
        if local:
            shutil.copyfile(local, target)
            reused += 1
        else:
            url = source["archive_url"] if source["archive_status"] == "verified_public_r2" else source["source_url"]
            download(url, target)
            downloaded += 1
        if not valid(target, source):
            target.unlink(missing_ok=True)
            raise ValueError(f"Source identity mismatch after retrieval: {source['candidate_id']}")
    print(json.dumps({"sources": len(sources), "already_valid": already_valid, "reused_local": reused, "downloaded_read_only": downloaded}))


if __name__ == "__main__":
    main()
