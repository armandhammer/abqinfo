#!/usr/bin/env python3
"""Apply explicit saved terminal research decisions to inventory once.

Duplicate and superseded decisions retain their saved canonical relationship in
the inventory's established provenance fields: the canonical source is added
to ``cited_successors`` and both the relationship and canonical candidate ID
are retained in the terminal reason and processing note.
"""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def walk(value, found):
    if isinstance(value, dict):
        if value.get('id') and value.get('recommended_status') in {'excluded','duplicate','superseded'}: found[value['id']] = value
        for child in value.values(): walk(child, found)
    elif isinstance(value, list):
        for child in value: walk(child, found)

p=argparse.ArgumentParser(); p.add_argument('--research',required=True); p.add_argument('--inventory',default='project-state/master-inventory.json'); p.add_argument('--ids',required=True); p.add_argument('--updated-at'); a=p.parse_args()
research=json.loads(Path(a.research).read_text(encoding='utf-8-sig')); found={}; walk(research,found)
ids=a.ids.split(','); assert len(ids)==len(set(ids)) and all(i in found for i in ids)
path=Path(a.inventory); inventory=json.loads(path.read_text(encoding='utf-8-sig')); rows={r['id']:r for r in inventory['candidates']}; assert all(i in rows for i in ids)
now=a.updated_at or datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
assert now.endswith('Z')
for i in ids:
    row, rec=rows[i], found[i]; status=rec['recommended_status']; row['status']=status; row['updated_at']=now
    authoritative_url=rec.get('authoritative_url')
    if authoritative_url:
        row['source_url']=authoritative_url
        row['direct_file_url']=authoritative_url
        row['parent_url']=row.get('parent_url') or authoritative_url.rsplit('/view',1)[0]
    if rec.get('content_kind') in {'PDF','DOCX','XLSX','CSV','ZIP'}: row['file_type']=rec['content_kind']
    if rec.get('size_bytes') is not None: row['size_bytes']=rec['size_bytes']
    if rec.get('checksum_sha256'): row['checksum_sha256']=rec['checksum_sha256']
    if rec.get('date') is not None: row['date']=rec['date']
    if rec.get('body'): row['agency']=rec['body']
    title=rec.get('title') or rec.get('title_for_reference')
    if title: row['title']=title
    if authoritative_url:
        row['provenance_status']='Saved research measured the directly fetched authoritative City container.'
        notes=row.setdefault('processing_notes', [])
        note='Saved terminal research supplied authoritative URL, exact size, and SHA-256.'
        if note not in notes: notes.append(note)
    if status == 'excluded':
        row['exclusion_reason']=rec['exclusion_reason']
        continue

    canonical_id=rec.get('canonical_id')
    relationship=rec.get('relationship') or rec.get('basis')
    assert canonical_id and relationship, f'{i} {status} decision lacks canonical_id or relationship'
    assert canonical_id in rows and canonical_id != i, f'{i} has an invalid canonical_id'
    canonical=rows[canonical_id]
    canonical_url=canonical.get('direct_file_url') or canonical.get('source_url')
    assert canonical_url, f'{i} canonical {canonical_id} lacks a source URL'
    successors=row.setdefault('cited_successors', [])
    if canonical_url not in successors: successors.append(canonical_url)
    row['exclusion_reason']=(
        f'{status.capitalize()} relationship to canonical inventory record {canonical_id}. '
        f'{relationship}'
    )
    row['validation_status']=f'terminal research decision: {status}; canonical relationship retained'
    note=(f'Saved terminal research: {status} relationship to canonical inventory record '
          f'{canonical_id}. {relationship}')
    notes=row.setdefault('processing_notes', [])
    if note not in notes: notes.append(note)
counts={s:sum(r['status']==s for r in inventory['candidates']) for s in inventory['allowed_statuses']}; inventory['counts']=counts
pending={'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'}
eligible=[r['id'] for r in inventory['candidates'] if r['status'] in pending or (r['status']=='implemented' and r.get('validation_status')!='passed')]
inventory['next_pending_id']=min(eligible) if eligible else None; inventory['generated_at']=now
tmp=path.with_name(path.name+'.terminal-update.tmp'); tmp.write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); tmp.replace(path)
print(json.dumps({'applied':len(ids),'counts':counts,'next_pending_id':inventory['next_pending_id']}))
