#!/usr/bin/env python3
"""Fresh-source preparation of the settled 13 Planning originals; no storage mutation."""
from __future__ import annotations

import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tmp/pgs-pdf-deps"))
import pymupdf as fitz
from PIL import Image, ImageDraw

DECISION = ROOT / "project-state/discovery/planning-documents-root-residual-decision-2026-09-20.json"
INVENTORY = ROOT / "project-state/master-inventory.json"
SAVED_R2 = ROOT / "project-state/r2-inventory.json"
LIVE_R2 = ROOT / "tmp/planning-documents-root-live-r2-2026-09-25.json"
STAGING = ROOT / "research/staging/planning-documents-root-archive-preparation-2026-09-25"
QA = ROOT / "tmp/planning-documents-root-archive-qa-2026-09-25"
OUTPUT = ROOT / "project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json"

PLAN = {
    "src-16b33375ffbddc62": ("city-data/demographics/cabq-planning-impact-area-chapter-01-executive-summary.pdf", "content/city-data/demographics.md", "Historical Planning Impact Area study components", "One grouped incomplete four-component set; Chapter 1.0", "No independent entry; no completion or missing-chapter claim."),
    "src-1fa6ae851ddf282d": ("city-data/demographics/cabq-planning-impact-area-chapter-05.pdf", "content/city-data/demographics.md", "Historical Planning Impact Area study components", "One grouped incomplete four-component set; Chapter 5", "No independent entry; no completion or missing-chapter claim."),
    "src-513fe9056bf9b34c": ("city-data/demographics/cabq-planning-impact-area-chapter-08.pdf", "content/city-data/demographics.md", "Historical Planning Impact Area study components", "One grouped incomplete four-component set; Chapter 8", "No independent entry; no completion or missing-chapter claim."),
    "src-c54e59cd5c25282d": ("city-data/demographics/cabq-planning-impact-area-chapter-03.pdf", "content/city-data/demographics.md", "Historical Planning Impact Area study components", "One grouped incomplete four-component set; Chapter 3", "No independent entry; no completion or missing-chapter claim."),
    "src-7de0f5803d442e8f": ("public-works/city-facilities/cabq-electric-system-transmission-generation-facility-plan-2010-2020.pdf", "content/public-works/city-facilities.md", "Energy and City Facilities", "Distinct historical electric system facility plan", "Identify the 2010–2020 planning period."),
    "src-8740362a1b751e26": ("development-land-use/zoning-ido/cabq-planned-communities-criteria-policy-element-1991.pdf", "content/development-land-use/zoning-ido.md", "Planning and Regulatory Context", "Distinct historical planned-community policy element", "Label historical February 1991 policy, not current IDO text."),
    "src-99fe2201b73355c4": ("development-land-use/area-sector-plans/cabq-barelas-sector-development-plan-2008.pdf", "content/development-land-use/area-sector-plans.md", "Barelas", "Distinct adopted 2008 sector plan", "Retain adoption date and distinguish from commercial-area revitalization plan."),
    "src-afac0cf84867a22f": ("public-works/parks-recreation/cabq-bosque-action-plan-rio-grande-valley-state-park-1993.pdf", "content/public-works/parks-recreation.md", "Arroyo and Open Space Planning History", "Distinct final Bosque action plan", "Identify final January 1993 plan and State Park scope."),
    "src-c87775c045d8acc4": ("development-land-use/zoning-ido/cabq-h1-historic-old-town-zone-design-guidelines-1998.pdf", "content/development-land-use/zoning-ido.md", "Old Town Regulatory Review", "Distinct former H-1 design guideline", "Historical, amended through April 9, 1998; distinguish later HPO-5 controls."),
    "src-d9bf34830a9467e2": (None, "content/development-land-use/redevelopment-plans.md", "Historical and Retained Area Plans", "Already represented by the archived canonical Barelas revitalization-plan row", "Exact byte-identical archived original; no second object or public entry."),
    "src-eb0f4b39798d29df": ("development-land-use/zoning-ido/cabq-unser-boulevard-overlay-zone-complete-legislation.pdf", "content/development-land-use/zoning-ido.md", "Planning and Regulatory Context", "Distinct historical overlay-zone legislation", "Source has blank enactment-number line; do not claim a numbered final enactment."),
    "src-f528ec2e0e955690": ("development-land-use/area-sector-plans/cabq-volcano-trails-sector-development-plan-enacted-package-2011.pdf", "content/development-land-use/area-sector-plans.md", "Southwest Mesa and Volcano Area", "Enacted 2011 package adjacent to held plan and adoption resolution", "Describe relationship to held plan and resolution; do not call it the same original."),
    "src-fb6e95610a43c7a4": ("public-works/parks-recreation/cabq-major-public-open-space-facility-plan-1999.pdf", "content/public-works/parks-recreation.md", "System and Facility Plans", "Distinct 1999 systemwide open-space facility plan", "Historical plan; distinguish from West Side steering presentation."),
}

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(value):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(OUTPUT)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch(url, path, expected_size, expected_sha):
    temp = path.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ABQInfo archival source verification)"})
    try:
        with urllib.request.urlopen(req, timeout=120) as response, temp.open("wb") as target:
            code, final, mime = response.status, response.url, response.headers.get("Content-Type", "")
            for block in iter(lambda: response.read(1024 * 1024), b""):
                target.write(block)
        if code != 200 or "pdf" not in mime.lower() or temp.open("rb").read(5) != b"%PDF-":
            raise ValueError(f"Source is not a successful PDF: HTTP {code}, MIME {mime}")
        if (temp.stat().st_size,digest(temp)) != (expected_size,expected_sha):
            rejected=path.with_suffix(".changed-source")
            temp.replace(rejected)
            raise ValueError("Fresh source differs from canonical bytes; preserved separately as " + rejected.relative_to(ROOT).as_posix())
        temp.replace(path)
        return {"http_status": code, "final_url": final, "content_type": mime, "redirected": final != url}
    finally:
        temp.unlink(missing_ok=True)

def inspect(path, pages, record_id):
    doc = fitz.open(path)
    if doc.needs_pass or doc.is_repaired or doc.page_count != pages:
        raise ValueError(f"PDF password, repair, or page-count mismatch: {doc.page_count} vs {pages}")
    QA.mkdir(parents=True, exist_ok=True)
    sheets, low_ink, text_pages = [], [], 0
    excerpts = {}
    width, height, columns, per_sheet = 128, 170, 8, 80
    for start in range(0, pages, per_sheet):
        end = min(start + per_sheet, pages)
        sheet = Image.new("RGB", (columns * width, math.ceil((end-start)/columns) * height), "#e5e5e5")
        draw = ImageDraw.Draw(sheet)
        for i in range(start, end):
            page = doc[i]
            if page.rect.width <= 0 or page.rect.height <= 0:
                raise ValueError(f"Invalid geometry page {i+1}")
            text = page.get_text()
            if text.strip(): text_pages += 1
            if i in (0, min(1,pages-1), pages-1): excerpts[str(i+1)] = text[:450]
            scale = min((width-8)/page.rect.width, (height-25)/page.rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
            image = Image.frombytes("RGB", (pix.width,pix.height), pix.samples)
            pixels = image.convert("L").tobytes()[::17]
            if sum(v < 245 for v in pixels)/max(1,len(pixels)) < .001: low_ink.append(i+1)
            slot = i-start
            x,y = slot%columns*width, slot//columns*height
            sheet.paste(image,(x+(width-image.width)//2,y))
            draw.text((x+5,y+height-18),str(i+1),fill="#111111")
        out = QA / f"{record_id}-{start+1:03d}-{end:03d}.jpg"
        sheet.save(out,quality=82)
        sheets.append(out.relative_to(ROOT).as_posix())
    metadata = doc.metadata
    doc.close()
    return {"structural_result":"opens_without_password_or_repair", "render_result":"all_pages_rendered", "rendered_pages":pages, "text_layer_pages":text_pages, "low_ink_pages_1_based":low_ink, "contact_sheets":sheets, "pdf_metadata_title":metadata.get("title",""), "page_text_excerpts":excerpts, "representative_visual_qa":"pending_human_review"}

def main():
    decision = load(DECISION)
    selected = [r for r in decision["records"] if r["disposition"] == "approved for addition"]
    assert len(selected) == 13 and set(PLAN) == {r["id"] for r in selected}
    inventory_all = load(INVENTORY)["candidates"]
    inventory = {r["id"]:r for r in inventory_all}
    saved, live = load(SAVED_R2), load(LIVE_R2)
    assert (saved["object_count"],saved["total_bytes"]) == (live["object_count"],live["total_bytes"]) == (1237,9218281842)
    saved_keys = {o["key"].casefold():o for o in saved["objects"]}
    live_keys = {o["key"].casefold():o for o in live["objects"]}
    STAGING.mkdir(parents=True,exist_ok=True)
    artifact = {"schema_version":1,"artifact_type":"planning_documents_root_archive_preparation","recorded_at":"2026-09-25","decision_artifact":DECISION.relative_to(ROOT).as_posix(),"source_research_artifacts":["project-state/discovery/ntmp-planning-documents-cluster-research-2026-09-13.json","project-state/discovery/harvested-planning-documents-research-2026-09-14.json","project-state/discovery/urban-design-planning-research-2026-09-14.json"],"scope_candidate_ids":[r["id"] for r in selected],"planning_impact_area_family":{"component_ids":[r["id"] for r in selected if r["id"] in list(PLAN)[:4]],"delivered_chapters":["1.0","3","5","8"],"state":"incomplete City-delivered component set","future_public_treatment":"one grouped historical component set, never four independent entries","complete_study_recovered":False,"other_chapters_inferred":False,"synthesized_pdf":False},"r2_snapshot":{"saved":{"objects":saved["object_count"],"bytes":saved["total_bytes"]},"live_read_only":{"objects":live["object_count"],"bytes":live["total_bytes"],"generated_at":live["generated_at"]}},"records":[],"r2_mutation":False,"visitor_visible_content_changed":False,"preparation_readiness":"in_progress","blockers":[]}
    for n, source in enumerate(selected,1):
        rid = source["id"]
        row = inventory[rid]
        assert row["status"] == "approved for addition" and row["scope_assessment"]["final_scope_decision"] == "passes_both_gates"
        assert (row["size_bytes"],row["checksum_sha256"]) == (source["size_bytes"],source["sha256"])
        key,page,section,treatment,caveat = PLAN[rid]
        assert row["proposed_canonical_page"] == page
        filename = rid + "-" + Path(row["direct_file_url"]).name
        staged = STAGING / filename
        record = {"id":rid,"title":row["title"],"source_url":row["source_url"],"direct_file_url":row["direct_file_url"],"saved_provenance":row.get("provenance_status"),"staged_local_path":staged.relative_to(ROOT).as_posix(),"expected_size_bytes":source["size_bytes"],"expected_sha256":source["sha256"],"expected_page_count":source["pages"],"proposed_r2_key":key,"proposed_public_archive_url":("https://files.abqinfo.com/"+key) if key else None,"proposed_canonical_page":page,"proposed_future_section":section,"presentation_treatment":treatment,"visitor_caveat":caveat,"cross_listing_recommendation":"none; canonical page is sufficient","inventory_proposal":"retain","preparation_blocker":None}
        artifact["records"].append(record)
        try:
            record.update(fetch(row["direct_file_url"],staged,source["size_bytes"],source["sha256"]))
            record["size_bytes"] = staged.stat().st_size
            record["sha256"] = digest(staged)
            if (record["size_bytes"],record["sha256"]) != (source["size_bytes"],source["sha256"]):
                raise ValueError("Fresh source differs from saved canonical size/SHA-256")
            record["page_count"] = source["pages"]
            record["pdf_qa"] = inspect(staged,source["pages"],rid)
            record["saved_key_collision"] = bool(key and key.casefold() in saved_keys)
            record["live_key_collision"] = bool(key and key.casefold() in live_keys)
            record["saved_same_size_object_count"] = sum(o["size_bytes"] == source["size_bytes"] for o in saved["objects"])
            record["live_same_size_object_count"] = sum(o["size_bytes"] == source["size_bytes"] for o in live["objects"])
            record["same_sha256_inventory_rows"] = [{"id":other["id"],"status":other["status"],"r2_key":other.get("r2_key")} for other in inventory_all if other["id"] != rid and other.get("checksum_sha256") == source["sha256"]]
            terms = [w for w in Path(key or "barelas-neighborhood-commercial-area-revitalization-plan").stem.split("-") if len(w)>4 and w not in ("cabq","historical","facility","plan","chapter")]
            record["near_name_saved_r2_keys"] = [o["key"] for o in saved["objects"] if sum(w in o["key"].casefold() for w in terms) >= min(2,len(terms))][:20]
            if rid == "src-d9bf34830a9467e2":
                matches = record["same_sha256_inventory_rows"]
                assert len(matches)==1 and matches[0]["id"] == "src-28418cab91a745a6" and matches[0]["r2_key"] in {o["key"] for o in saved["objects"]}
                record["preparation_blocker"] = "Already archived byte-identical canonical original src-28418cab91a745a6; no second object or independent public entry may be proposed. Settled retained disposition needs a separate reconciliation decision."
                artifact["blockers"].append({"id":rid,"reason":record["preparation_blocker"]})
            elif record["saved_key_collision"] or record["live_key_collision"]:
                record["preparation_blocker"] = "Proposed key already exists"
                artifact["blockers"].append({"id":rid,"reason":record["preparation_blocker"]})
        except Exception as exc:
            record["preparation_blocker"] = str(exc)
            artifact["blockers"].append({"id":rid,"reason":str(exc)})
        artifact["summary"] = {"intended_originals":13,"source_bytes_verified":sum(r.get("sha256")==r["expected_sha256"] and r.get("size_bytes")==r["expected_size_bytes"] for r in artifact["records"]),"source_bytes_total":sum(r.get("size_bytes",0) for r in artifact["records"]),"pdf_pages_rendered":sum(r.get("pdf_qa",{}).get("rendered_pages",0) for r in artifact["records"]),"r2_upload_ready_originals":sum(r.get("pdf_qa",{}).get("render_result")=="all_pages_rendered" and not r["preparation_blocker"] for r in artifact["records"])}
        save(artifact)
        print(f"{n:02d}/13 {rid}: {record.get('size_bytes')} bytes, {record.get('page_count')} pages, blocker={record['preparation_blocker']}",flush=True)
    artifact["preparation_readiness"] = "source_and_render_verified_pending_visual_review_and_duplicate_reconciliation" if artifact["summary"]["source_bytes_verified"]==13 and artifact["summary"]["pdf_pages_rendered"]==1078 else "partially_prepared"
    save(artifact)

if __name__ == "__main__": main()
