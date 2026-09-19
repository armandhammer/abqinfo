#!/usr/bin/env python3
"""Apply explicit saved terminal research decisions to inventory once."""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def walk(value, found):
    if isinstance(value, dict):
        if value.get('id') and value.get('recommended_status') in {'excluded','duplicate','superseded'}: found[value['id']] = value
        for child in value.values(): walk(child, found)
    elif isinstance(value, list):
        for child in value: walk(child, found)

p=argparse.ArgumentParser(); p.add_argument('--research',required=True); p.add_argument('--inventory',default='project-state/master-inventory.json'); p.add_argument('--ids',required=True); a=p.parse_args()
research=json.loads(Path(a.research).read_text(encoding='utf-8-sig')); found={}; walk(research,found)
ids=a.ids.split(','); assert len(ids)==len(set(ids)) and all(i in found for i in ids)
path=Path(a.inventory); inventory=json.loads(path.read_text(encoding='utf-8-sig')); rows={r['id']:r for r in inventory['candidates']}; assert all(i in rows for i in ids)
now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
for i in ids:
    row, rec=rows[i], found[i]; row['status']=rec['recommended_status']; row['updated_at']=now
    if rec['recommended_status']=='excluded': row['exclusion_reason']=rec['exclusion_reason']
counts={s:sum(r['status']==s for r in inventory['candidates']) for s in inventory['allowed_statuses']}; inventory['counts']=counts
pending={'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'}
eligible=[r['id'] for r in inventory['candidates'] if r['status'] in pending or (r['status']=='implemented' and r.get('validation_status')!='passed')]
inventory['next_pending_id']=min(eligible) if eligible else None; inventory['generated_at']=now
tmp=path.with_name(path.name+'.terminal-update.tmp'); tmp.write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); tmp.replace(path)
print(json.dumps({'applied':len(ids),'counts':counts,'next_pending_id':inventory['next_pending_id']}))
