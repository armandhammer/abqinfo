#!/usr/bin/env python3
"""Regression for the bounded 13-original Planning preparation stage."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def read(path): return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))
expected = {
"src-16b33375ffbddc62":(1340591,"673d90a0c41b2548f824aa50b248496e444f700aa3cf33d93d4d5524ad9c8930",34),
"src-1fa6ae851ddf282d":(1746980,"a60c5babe0cdca83937bcdb0086153d0024d92ff17896a68b89d44a0483f56f9",76),
"src-513fe9056bf9b34c":(1028761,"d0d15d835381400a3c05092dfef8e473423c32acd6b4ffc6f8d548815096d661",45),
"src-c54e59cd5c25282d":(1495629,"26fe18c4e274cd4384b83216c2436a0dc1724a3220a1e26894a7d98e2123942b",38),
"src-7de0f5803d442e8f":(16542346,"60d4fd8f74ddfa5a250a50b1b5cae3ce3dbe8bf52f6b2008e5b6b8b07add1c38",98),
"src-8740362a1b751e26":(7312527,"70a6a68c0d3870ec0fd8f93e73ab1e0ff1bd0d1698c7fe3d90e58070f26b26e2",123),
"src-99fe2201b73355c4":(49626419,"4c68c600323dd42171ab42d954008b6f30d0ad304b0ce20e43d05283a97d4d99",168),
"src-afac0cf84867a22f":(15918465,"002ef0e4f24a5f09d9701dd2359b653e18d09b4b418d8112c896fd5fd5ebcc77",105),
"src-c87775c045d8acc4":(15409,"610913cb0fce2deff67a891986e1da515924fb2c4b3c0dfd373c574bae1051c4",1),
"src-d9bf34830a9467e2":(8719030,"c2081c6cbc60b029c2b558a73ad975b429b03e89cc1837c393f8b5c30191ae19",150),
"src-eb0f4b39798d29df":(1969125,"da74a6536568142b82485e0753fe488358d589d6a5f0f689973c419669317f20",5),
"src-f528ec2e0e955690":(8976542,"7e1291301365c09fa76bd2c495aa0e563b2e6ce8e864458d5213ea343d449ad7",82),
"src-fb6e95610a43c7a4":(16276532,"15ca95c5d9662e2984024c3b98c4e3824ae1bde53a82ac3d3a24c1ef1f6414a8",153),
}
a=read("project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json")
d=read("project-state/discovery/planning-documents-root-residual-decision-2026-09-20.json")
inventory={r["id"]:r for r in read("project-state/master-inventory.json")["candidates"]}
reconciliation_path=ROOT/'project-state/discovery/planning-documents-root-barelas-duplicate-reconciliation-2026-09-26.json'
reconciled=reconciliation_path.exists() and read(reconciliation_path.relative_to(ROOT).as_posix()).get('state')=='reconciled_exact_duplicate'
archive_path=ROOT/'project-state/discovery/planning-documents-root-archive-public-byte-verification-2026-09-26.json'
archived=archive_path.exists() and read(archive_path.relative_to(ROOT).as_posix()).get('state')=='complete_all_12_public_byte_verified_and_inventory_reconciled'
assert len(expected)==len(a["records"])==len(set(a["scope_candidate_ids"]))==13
assert set(expected)==set(a["scope_candidate_ids"])=={r["id"] for r in a["records"]}
assert sum(s for s,_,_ in expected.values())==a["summary"]["source_bytes_total"]==130968356
assert sum(p for _,_,p in expected.values())==a["summary"]["pdf_pages_rendered"]==1078
assert a["summary"]["source_bytes_verified"]==a["summary"]["representative_visual_reviews_passed"]==13
assert a["summary"]["unique_proposed_new_keys"]==12 and a["summary"]["archived_same_hash_conflicts"]==1
assert a["r2_mutation"] is False and a["visitor_visible_content_changed"] is False
assert a["inventory_rows_changed"] is False and a["r2_snapshot"]["unchanged_exact_key_size_etag_comparison"] is True
assert "63 characters" in a["expected_identity_transcription_note"]
family=a["planning_impact_area_family"]
assert len(family["component_ids"])==4 and set(family["component_ids"])==set(list(expected)[:4])
assert family["delivered_chapters"]==["1.0","3","5","8"]
assert family["complete_study_recovered"] is False and family["other_chapters_inferred"] is False and family["synthesized_pdf"] is False
assert "incomplete" in family["state"] and "one grouped" in family["future_public_treatment"]
assert len(list((ROOT/"research/staging/planning-documents-root-archive-preparation-2026-09-25").glob("*.pdf")))==13
keys=[]
for r in a["records"]:
    rid=r["id"]; size,sha,pages=expected[rid]; row=inventory[rid]
    path=ROOT/r["staged_local_path"]
    assert path.stat().st_size==r["size_bytes"]==row["size_bytes"]==size
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    assert h.hexdigest()==r["sha256"]==row["checksum_sha256"]==sha
    assert r["page_count"]==r["pdf_qa"]["rendered_pages"]==pages
    assert r["pdf_qa"]["structural_result"]=="opens_without_password_or_repair" and r["pdf_qa"]["representative_visual_qa"].startswith("passed_")
    assert r["direct_file_url"]==row["direct_file_url"]==r["final_url"] and r["http_status"]==200 and not r["redirected"]
    assert row["status"]==("duplicate" if reconciled and rid=="src-d9bf34830a9467e2" else "placement assigned" if archived else "approved for addition") and row["scope_assessment"]["final_scope_decision"]=="passes_both_gates"
    assert (row["r2_key"],row["r2_url"]) == ((r["proposed_r2_key"],r["proposed_public_archive_url"]) if archived and rid!="src-d9bf34830a9467e2" else (None,None))
    assert not r["saved_key_collision"] and not r["live_key_collision"]
    if rid in family["component_ids"]:
        assert "incomplete" in r["presentation_treatment"] and "independent" in r["visitor_caveat"]
    if rid=="src-d9bf34830a9467e2":
        assert r["proposed_r2_key"] is None and r["proposed_public_archive_url"] is None
        assert r["collision_resolution"]["existing_canonical_inventory_id"]=="src-28418cab91a745a6"
        assert inventory["src-28418cab91a745a6"]["checksum_sha256"]==sha
    else:
        assert r["preparation_blocker"] is None and r["proposed_public_archive_url"]=="https://files.abqinfo.com/"+r["proposed_r2_key"]
        keys.append(r["proposed_r2_key"].casefold())
assert len(keys)==len(set(keys))==12
if reconciled:
    assert a['blockers']==[] and a['current_derived_state']['exact_duplicate_deliveries_reconciled']==1
    assert a['current_derived_state']['unique_upload_bytes']==122249326 and a['current_derived_state']['unique_upload_pages']==928
for r in d["records"]:
    if r["id"] not in expected:
        assert inventory[r["id"]]["status"]==r["disposition"]
assert sum(r["disposition"]=="duplicate" for r in d["records"])==2
assert sum(r["disposition"]=="excluded" for r in d["records"])==4
assert (a["r2_snapshot"]["saved"]["objects"],a["r2_snapshot"]["saved"]["bytes"])==(1237,9218281842)
assert (a["r2_snapshot"]["live_read_only"]["objects"],a["r2_snapshot"]["live_read_only"]["bytes"])==(1237,9218281842)
for args in (["git","diff","--name-only",a["reviewed_baseline_commit"],"--","content"],["git","ls-files","--others","--exclude-standard","content"]):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=True)
    assert not result.stdout.strip(),result.stdout
print("Planning preparation: 13 exact PDFs, 130,968,356 bytes, 1,078 pages; 12 unique keys; Barelas exact duplicate " + ("reconciled" if reconciled else "awaiting reconciliation") + "; historical preparation involved no content/R2 mutation")
