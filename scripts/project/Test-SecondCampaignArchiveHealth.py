#!/usr/bin/env python3
"""Exact health-population coverage; independent saved/live object accounting."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/"project-state/discovery"
def load(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
h=load(D/"second-large-campaign-archive-health-2026-09-26.json");c=load(D/"ordinary-queue-second-large-resolution-campaign-2026-09-26.json");first=load(D/"ordinary-queue-large-resolution-campaign-2026-09-26.json");old=load(D/"approved-backlog-background-archive-campaign-2026-09-26.json")
assert h["state"]=="complete_for_recorded_population" and not h.get("failures")
expected={r["r2_key"]:(r["size_bytes"],r["expected_sha256"],"prior_30") for r in old["records"]+old["generated_packages"] if r.get("public_verification")}
assert len(expected)==30
for name,records in [("prior_13",first["archive_objects"]),("second_campaign",c["archive_objects"])]:
 for r in records:assert r["key"] not in expected;expected[r["key"]]=(r["size_bytes"],r["checksum_sha256"],name)
receipts={r["key"]:r for r in h["receipts"]};pop={r["key"]:r for r in h["population"]}
assert len(receipts)==len(h["receipts"])==len(expected) and pop.keys()==receipts.keys()==expected.keys()
live=load(ROOT/h["live_listing_artifact"]);objects={r["key"]:r for r in live["objects"]}
saved=load(ROOT/"project-state/r2-inventory.json")
identity=lambda d:{r["key"]:(r["size_bytes"],r["etag"]) for r in d["objects"]}
assert identity(live)==identity(saved) and live["total_bytes"]==saved["total_bytes"]<=10000000000
baseline=load(ROOT/c["baseline_r2_artifact"])
for r in baseline["objects"]:assert objects[r["key"]]["size_bytes"]==r["size_bytes"] and objects[r["key"]]["etag"]==r["etag"]
for key,x in receipts.items():
 assert (x["size_bytes"],x["checksum_sha256"],x["cohort"])==expected[key]
 assert x["etag"]==objects[key]["etag"] and x["source_local_hash_verified"] and x["byte_identical"]
 get=x["full_public_GET"];assert get["http_status"]==200 and get["requested_url"]=="https://files.abqinfo.com/"+key
 assert (get["size_bytes"],get["checksum_sha256"])==expected[key][:2]
 assert x["verified_at"]>=c["started_at"]
assert h["summary"]["full_GET_verified"]==len(expected) and h["summary"]["bytes_fully_verified"]==sum(r[0] for r in expected.values())
print("PASS: 30 prior + 13 first-campaign +",len(c["archive_objects"]),"new objects; all full public GETs, sizes, hashes, ETags and saved/live equality.")
