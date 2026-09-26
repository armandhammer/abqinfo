#!/usr/bin/env python3
"""Normalize only already-settled legacy links; never infer editions or change statuses."""
import argparse,collections,copy,json,pathlib,re,subprocess,sys
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[2];DISC=ROOT/"project-state/discovery";DATE="2026-09-26";BASE="34ccc0fe230ffb8290652979cbe8603c69db3115"
def load(p):return json.loads(pathlib.Path(p).read_text(encoding="utf-8-sig"))
def save(p,d):
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");t.replace(p)
p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true");a=p.parse_args()
inv=load(ROOT/"project-state/master-inventory.json");rows={r["id"]:r for r in inv["candidates"]};audit=load(DISC/f"inventory-exact-identity-integrity-audit-{DATE}.json");observations=audit["unresolved_anomalies"];assert len(observations)==174
campaign=load(DISC/f"ordinary-queue-second-large-resolution-campaign-{DATE}.json")
if a.apply:assert len(campaign["resolved_records"])>=600,"Primary pending-resolution target must precede hardening"
targets={};evidence={}
# Explicit target IDs in existing durable prose, with known conflicting/protected cases withheld.
protected={"src-185f33493177b085","src-2cdb21bc19db1fb9","src-4c0d4f6dbc0c78a1"}
conflict={"src-053b77f24a962cd0":"The prose names the final 2015 NTMP Manual but its embedded ID resolves to Old Albuquerque High School MRA Plan. Conflicting historical target evidence cannot be normalized without new research."}
for ob in observations:
 if ob["type"]!="legacy_supersession_target_not_structured":continue
 i=ob["id"];r=rows[i];prose=" ".join(r["processing_notes"])+" "+str(r.get("exclusion_reason") or "");ids=list(dict.fromkeys(re.findall(r"src-[a-f0-9]{16}",prose)));ids=[z for z in ids if z in rows and z!=i]
 if len(ids)==1 and i not in conflict and i not in protected:targets[i]=ids;evidence[i]="Existing unchanged processing_notes/exclusion_reason explicitly name target ID "+ids[0]
# Settled signed R-25-117 chain, exact mapping recorded by the retained-source family audit.
r117=load(DISC/"r-25-117-retained-source-audit-2026-09-06.json")
for x in r117["attachments"]:
 if x["candidate_id"] in {o.get("id") for o in observations} and x["decision"].startswith("superseded"):
  targets[x["candidate_id"]]=[r117["canonical_candidate_id"]];evidence[x["candidate_id"]]="r-25-117-retained-source-audit-2026-09-06.json: "+x["reason"]+"; canonical_candidate_id and result explicitly retain signed 31-page R-2025-014 with final Attachment A."
r126=load(DISC/"r-25-126-retained-source-audit-2026-09-06.json");canonical=next(x["canonical_candidate_id"] for x in r126["attachments"] if x.get("canonical_candidate_id"))
for x in r126["attachments"]:
 if x["decision"].startswith("superseded"):targets[x["candidate_id"]]=[canonical];evidence[x["candidate_id"]]="r-25-126-retained-source-audit-2026-09-06.json explicitly retains signed R-2025-031; enacted delivery comparison names canonical "+canonical
# Captured enacted counterparts map by exact authoritative URL and hash, not near titles.
for x in load(DISC/"council-enacted-counterpart-capture-2026-09-20.json")["records"]:
 if not x.get("direct_file_url") or not x.get("checksum_sha256"):continue
 matches=[r for r in rows.values() if r.get("direct_file_url")==x["direct_file_url"] and r.get("checksum_sha256")==x["checksum_sha256"]]
 if len(matches)==1:targets[x["held_substitute_id"]]=[matches[0]["id"]];evidence[x["held_substitute_id"]]="council-enacted-counterpart-capture-2026-09-20.json: exact recorded enacted original URL/SHA matches inventory "+matches[0]["id"]+"; earlier held substitute chronology already settled."
for ob in observations:
 if ob["type"]!="legacy_supersession_target_not_structured":continue
 i=ob["id"];text=rows[i].get("exclusion_reason") or ""
 if text.startswith("Superseded by City of Albuquerque CIP Building Design Standards and Guidelines, Revision 17"):
  targets[i]=["src-e9eb53c6a03fbaba"];evidence[i]="Existing exclusion_reason explicitly names the unique City CIP Building Design Standards Revision 17; target title, official revision and retained original are unambiguous."
# Further explicit unique enacted targets already named in finality prose.
for i,c in {"src-af4dce5dc2c0d75e":"src-241c664f388493fc","src-4b429f5077e7e49a":"src-241c664f388493fc","src-3f628ea52a79829e":"src-09fdd8da28f09ff5"}.items():
 targets[i]=[c];evidence[i]="Existing exclusion_reason explicitly names signed enactment; unique retained target title/key and saved finality evidence identify "+c
result=[];updates={};now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
fields=["id","status","title","source_url","direct_file_url","size_bytes","checksum_sha256","cited_successors","exclusion_reason","processing_notes","r2_key","proposed_canonical_page"]
for j,ob in enumerate(observations,1):
 ids=ob.get("ids") or [ob["id"]];rs=[rows[i] for i in ids];z={"observation_number":j,"original_observation":ob,"records":[{k:r.get(k) for k in fields} for r in rs],"structured_targets":[],"updates":[],"status_changes":[]}
 if ob["type"]=="multiple_retained_later_state_rows_share_exact_hash":
  assert len({r["checksum_sha256"] for r in rs})==1 and len({r["size_bytes"] for r in rs})==1
  assert len({r["r2_key"] for r in rs})==1
  z.update(action="deferred_inventory_mutation",reason="Both inventory discoveries reference the same unchanged original bytes, same R2 object and same public page, so this is not generated-versus-source material or additional storage. Three groups contain an explicit historical duplicate-discovery reason; the Santa Clara group preserves direct-file and landing-page provenance. All involved later-state rows lack positive scope and remain frozen legacy rows. Changing metadata/status would require a new positive assessment and re-review outside this deterministic exercise. Preserve both rows and one object; no automatic collapse.",shared_object_key=rs[0]["r2_key"],saved_shared_object_evidence=True)
 elif ob["type"]=="duplicate_hash_group_relationship_not_explicit":
  canon=[r for r in rs if r["status"]!="duplicate"]
  if any(r["size_bytes"]==0 for r in rs):z.update(action="deferred",reason="SHA-256 of empty bytes establishes only empty staging placeholders, not document identity. Preserve prior prose target without treating a zero-byte hash group as authentic originals.")
  elif len(canon)!=1:z.update(action="deferred",reason="All members already have duplicate status; no unambiguous retained canonical within this exact-hash group. A missing/outside target cannot be guessed from titles.")
  else:
   can=canon[0];assert all((r["size_bytes"],r["checksum_sha256"])==(can["size_bytes"],can["checksum_sha256"]) for r in rs)
   z["structured_targets"]=[can["id"]];z["relationship_evidence"]="Exact nonempty SHA-256 and size match; one existing nonduplicate canonical, whose existing "+can["status"]+" state is preserved."
   for r in rs:
    if r["status"]=="duplicate":
     old=r.get("cited_successors");values=old if isinstance(old,list) else [old] if old else [];url=can.get("direct_file_url") or can["source_url"]
     if url in values and can["id"] in " ".join(r["processing_notes"])+str(r.get("exclusion_reason") or ""):continue
     new=list(values)
     if url not in new:new.append(url)
     note="Legacy deterministic relationship hardening 2026-09-26: exact-byte alias of canonical "+can["id"]+"; unchanged status/source/public presentation. Canonical status remains "+can["status"]+"."
     change={"cited_successors":new,"processing_notes":r["processing_notes"]+[note]};updates[r["id"]]=change;z["updates"].append({"id":r["id"],"before":{k:r.get(k) for k in change},"after":change})
   z["action"]="hardened" if z["updates"] else "already_structured"
 elif ob["id"] in protected:z.update(action="deferred",reason="Protected completed later-MS4 or Notices and Orders lineage. Settled prose is retained; no protected row reopened or mutated.")
 elif ob["id"] in conflict:z.update(action="deferred_conflicting_target",reason=conflict[ob["id"]])
 elif ob["id"] not in targets:z.update(action="deferred",reason="No explicit unambiguous current target ID/URL or uniquely named edition can be established from existing settled evidence. Broad family names, contextual similarity and component-versus-full distinctions require separate bounded research; existing terminal status is preserved.")
 else:
  r=rs[0];assert r["status"]=="superseded";tids=targets[r["id"]];z["structured_targets"]=tids;z["relationship_evidence"]=evidence[r["id"]];old=r.get("cited_successors");values=old if isinstance(old,list) else [old] if old else [];new=list(values)
  for cid in tids:
   url=rows[cid].get("direct_file_url") or rows[cid]["source_url"]
   if url not in new:new.append(url)
  note="Legacy deterministic relationship hardening 2026-09-26: settled supersession target "+", ".join(tids)+". "+evidence[r["id"]]+" No chronology, status or public presentation changed."
  change={"cited_successors":new,"processing_notes":r["processing_notes"]+[note]};updates[r["id"]]=change;z["updates"]=[{"id":r["id"],"before":{k:r.get(k) for k in change},"after":change}];z["action"]="hardened"
 result.append(z)
report={"schema_version":1,"artifact_type":"inventory_legacy_relationship_hardening","baseline_commit":BASE,"original_audit_artifact":"project-state/discovery/inventory-exact-identity-integrity-audit-2026-09-26.json","recorded_at":now,"state":"applied" if a.apply else "reviewed_plan","observations":result,"changed_ids":sorted(updates),"summary":{"observations":len(result),"actions":dict(collections.Counter(z["action"] for z in result)),"metadata_rows_hardened":len(updates),"status_changes":0},"visitor_visible_content_changed":False}
if a.apply:
 req=ROOT/"tmp/legacy-hardening-requests.json";save(req,[{"id":i,"changes":v} for i,v in updates.items()]);subprocess.run([sys.executable,"-B",str(ROOT/"scripts/project/Update-CandidatesBatch.py"),"--requests",str(req)],cwd=ROOT,check=True)
 report["applied_at"]=now
save(DISC/f"inventory-legacy-relationship-hardening-{DATE}.json",report)
print(json.dumps(report["summary"]))
