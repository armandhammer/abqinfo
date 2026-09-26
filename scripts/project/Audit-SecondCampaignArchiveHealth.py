#!/usr/bin/env python3
"""Resumable full-GET health receipts for the three September 26 archive populations."""
import concurrent.futures,hashlib,json,runpy,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DISC=ROOT/"project-state/discovery";DATE="2026-09-26";REPORT=DISC/f"second-large-campaign-archive-health-{DATE}.json";LIVE=DISC/f"second-large-campaign-archive-health-live-r2-{DATE}.json"
def load(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def save(p,d):
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");t.replace(p)
now=lambda:datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
a=load(DISC/f"approved-backlog-background-archive-campaign-{DATE}.json");b=load(DISC/f"ordinary-queue-large-resolution-campaign-{DATE}.json");c=load(DISC/f"ordinary-queue-second-large-resolution-campaign-{DATE}.json");pop=[]
rows={r['id']:r for r in load(ROOT/"project-state/master-inventory.json")["candidates"]}
for r in a["records"]+a["generated_packages"]:
 if r.get("public_verification"):
  pop.append({"key":r["r2_key"],"id":r["id"],"cohort":"prior_30","size_bytes":r["size_bytes"],"checksum_sha256":r["expected_sha256"],"source_path":r["staged_path"]})
assert len(pop)==30
for cohort,records in [("prior_13",b["archive_objects"]),("second_campaign",c["archive_objects"])]:
 for r in records:
  row=rows[r["id"]]
  pop.append({"key":r["key"],"id":r["id"],"cohort":cohort,"size_bytes":r["size_bytes"],"checksum_sha256":r["checksum_sha256"],"source_path":row["local_path"]})
assert len({r["key"] for r in pop})==len(pop)
subprocess.run(["pwsh","-NoProfile","-ExecutionPolicy","Bypass","-File",str(ROOT/"scripts/project/Get-R2Inventory.ps1"),"-OutputPath",str(LIVE)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
live=load(LIVE);objects={o["key"]:o for o in live["objects"]}
report=load(REPORT) if REPORT.exists() else {"schema_version":1,"artifact_type":"focused_september26_archive_health","started_at":now(),"receipts":[],"visitor_visible_content_changed":False}
receipts={r["key"]:r for r in report["receipts"]};report["population"]=pop;report["state"]="verifying_full_public_GETs";report["live_listing_artifact"]=LIVE.relative_to(ROOT).as_posix()
for x in pop:
 o=objects[x["key"]];assert o["size_bytes"]==x["size_bytes"];x["live_etag"]=o["etag"]
 if x["key"] in receipts:assert receipts[x["key"]]["etag"]==o["etag"]
save(REPORT,report)
get=runpy.run_path(str(ROOT/"scripts/project/Prepare-LargeOrdinaryCampaign.py"))["source_get"]
def verify(x):
 p=ROOT/x["source_path"];assert p.stat().st_size==x["size_bytes"] and hashlib.file_digest(p.open("rb"),"sha256").hexdigest()==x["checksum_sha256"]
 url="https://files.abqinfo.com/"+x["key"];data,v=get(url);assert v["http_status"]==200 and (v["size_bytes"],v["checksum_sha256"])==(x["size_bytes"],x["checksum_sha256"])
 return {"key":x["key"],"id":x["id"],"cohort":x["cohort"],"etag":x["live_etag"],"size_bytes":x["size_bytes"],"checksum_sha256":x["checksum_sha256"],"byte_identical":True,"source_local_hash_verified":True,"full_public_GET":v,"verified_at":now()}
work=[x for x in pop if x["key"] not in receipts]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 future={pool.submit(verify,x):x for x in work}
 for f in concurrent.futures.as_completed(future):
  x=future[f]
  try:r=f.result();receipts[r["key"]]=r;report["receipts"]=[receipts[k] for k in sorted(receipts)];report["last_receipt_at"]=now();save(REPORT,report);print("Full GET verified",len(receipts),"/",len(pop),x["key"],flush=True)
  except Exception as e:report.setdefault("failures",[]).append({"key":x["key"],"error":str(e)});save(REPORT,report);raise
report["state"]="complete_for_recorded_population";report["completed_at"]=now();report["last_live_metadata_verified_at"]=now();report["summary"]={"prior_30":30,"prior_13":13,"second_campaign":len(c["archive_objects"]),"full_GET_verified":len(receipts),"bytes_fully_verified":sum(r["size_bytes"] for r in receipts.values()),"all_saved_keys_exist":True,"all_sizes_match":True,"all_etags_match":True};save(REPORT,report);print(json.dumps(report["summary"]))
