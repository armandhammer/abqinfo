#!/usr/bin/env python3
"""Exact observation coverage and metadata-only settlement; protect all legacy statuses."""
import collections,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/"project-state/discovery"
def load(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
a=load(D/"inventory-exact-identity-integrity-audit-2026-09-26.json");h=load(D/"inventory-legacy-relationship-hardening-2026-09-26.json");assert h["state"]=="applied"
b=json.loads(subprocess.check_output(["git","show",h["baseline_commit"]+":project-state/master-inventory.json"],cwd=ROOT).decode("utf-8-sig"));prior={r["id"]:r for r in b["candidates"]};rows={r["id"]:r for r in load(ROOT/"project-state/master-inventory.json")["candidates"]}
assert [z["original_observation"] for z in h["observations"]]==a["unresolved_anomalies"] and len(h["observations"])==174
expected={};seen=set()
for z in h["observations"]:
 assert z["observation_number"] not in seen;seen.add(z["observation_number"])
 assert z["status_changes"]==[] and z["action"] in ["hardened","already_structured","deferred","deferred_conflicting_target","deferred_inventory_mutation"]
 if z["action"].startswith("deferred"):assert z["reason"] and not z["updates"]
 for snapshot in z["records"]:
  r=prior[snapshot["id"]];assert snapshot=={k:r.get(k) for k in snapshot},("Unexpected legacy re-review",snapshot["id"])
 for change in z["updates"]:
  i=change["id"];assert i not in expected;expected[i]=change
  assert prior[i]["status"] in ["duplicate","superseded"] and rows[i]["status"]==prior[i]["status"]
  assert set(change["after"])=={"cited_successors","processing_notes"}
  assert change["before"]=={k:prior[i].get(k) for k in change["before"]}
  for k,v in change["after"].items():assert rows[i][k]==v
  for k,v in prior[i].items():
   if k not in ["cited_successors","processing_notes","updated_at"]:assert rows[i][k]==v,(i,k)
  old=prior[i]["cited_successors"];old=old if isinstance(old,list) else [old] if old else [];assert all(x in rows[i]["cited_successors"] for x in old)
  assert rows[i]["processing_notes"][:-1]==prior[i]["processing_notes"]
  assert z["structured_targets"] and z["relationship_evidence"]
  for cid in z["structured_targets"]:
   assert cid in rows and (rows[cid].get("direct_file_url") or rows[cid]["source_url"]) in rows[i]["cited_successors"]
   if cid not in h["changed_ids"]:assert rows[cid]==prior[cid],"Target/protected row was mutated"
   else:assert rows[cid]["status"]==prior[cid]["status"]
  if z["original_observation"]["type"]=="duplicate_hash_group_relationship_not_explicit":
   can=rows[z["structured_targets"][0]];assert rows[i]["size_bytes"]>0 and (rows[i]["size_bytes"],rows[i]["checksum_sha256"])==(can["size_bytes"],can["checksum_sha256"])
assert set(expected)==set(h["changed_ids"]) and len(expected)==95
assert h["summary"]["actions"]==dict(collections.Counter(z["action"] for z in h["observations"]))
assert h["summary"]["actions"]=={"hardened":84,"deferred_conflicting_target":1,"deferred":83,"deferred_inventory_mutation":4,"already_structured":2}
assert h["summary"]["status_changes"]==0 and h["visitor_visible_content_changed"] is False
assert rows["src-053b77f24a962cd0"]==prior["src-053b77f24a962cd0"]
for z in h["observations"]:
 if z["original_observation"]["type"]=="multiple_retained_later_state_rows_share_exact_hash":
  rs=[rows[i] for i in z["original_observation"]["ids"]];assert all(r==prior[r["id"]] for r in rs)
  assert len({r["r2_key"] for r in rs})==len({r["checksum_sha256"] for r in rs})==1 and z["action"]=="deferred_inventory_mutation"
print("PASS: all 174 observations accounted; 84 hardened/2 already structured, 95 metadata rows; no status/source/protected changes.")
