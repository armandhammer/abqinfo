#!/usr/bin/env python3
"""Persist bounded recovery conclusions without forcing inventory dispositions."""
import hashlib, runpy
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('BackgroundCampaign.py')))
ROOT,load,save,rel,context,now=(c[k] for k in ['ROOT','load','save','rel','context','now'])
path,d=context();e=load(path.parent/'bounded-source-investigation.json');sources={r['id']:r for r in e['records']}
# Run only at a quiescent mutation boundary; never race an archive writer.
import msvcrt
with (ROOT/'tmp/background-campaign-writer.lock').open('a+b') as lock:
 lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 records=[]
 local=ROOT/'research/staging/document-review/COA Final McDuffie_Traffic Calming Study 052024.pdf'
 measured=dict(local_path=rel(local),size_bytes=local.stat().st_size,sha256=hashlib.file_digest(local.open('rb'),'sha256').hexdigest())
 assert measured['size_bytes']==11940327 and measured['sha256']=='48b6d8d5f91290f55a56b22398aa754e5696378e69e0693ecc9914cd285fee15'
 reasons={
 'src-48c77cfd3533626b':'Fresh official original is still a repaired zero-page PDF. No new clean or authoritative replacement path is demonstrated; do not salvage or assign an uncertain disposition.',
 'src-2f89e1bc040e1d33':'Owner-retrieved 321-page McDuffie original remains exact saved bytes, but a fresh official share GET yields only a 1344-byte JavaScript shell. Attempted browser discovery reports no available apps or browsers; independent repeat retrieval/provenance cannot be established in this environment. Preserve original and owner chain; no upload.',
 'src-e63d4ebb9302ec96':'Original MRCOG annual-report URL now redirects to https://www.wccnm.org/wccnm-board/ with no annual-report link. Saved preparation never retrieved an original, so there is no deterministic report identity or replacement path. Do not treat unrelated redirect as the annual report.'}
 for i,why in reasons.items():
  records.append(dict(id=i,attempted_at=now(),review_authorized=False,outcome='source_or_structural_blocker_preserved',reason=why,source_receipt=sources[i],historical_evidence_preserved=True,inventory_unchanged=True,**({'owner_original_remeasurement':measured,'browser_inventory':'cua.getState returned apps=[] browsers=[] on 2026-09-26'} if i=='src-2f89e1bc040e1d33' else {})))
 d['recovery_records']=records
 # Preserve unfinished live-service identities, do not force exclusions from shells.
 pending=load(path.parent/'remaining-review-prerequisites.json')['records'];inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
 d['deferred_records']=[dict(r,category='live_application_render_or_relationship_blocker',state='unresolved_ungated_not_currently_actionable',browser_inventory='apps=[] browsers=[]') for r in pending if rows[r['id']]['status']=='pending review']
 save(path,d)
 print(len(records),'existing blockers preserved;',len(d['deferred_records']),'live-service prerequisites unresolved')
