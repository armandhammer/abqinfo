#!/usr/bin/env python3
"""Deterministic cross-inventory identity audit; records ambiguous legacy facts."""
import collections,json,re,runpy
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,unquote
c=runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,BASE,CAMPAIGN,load,save=(c[k] for k in ['ROOT','DISC','DATE','BASE','CAMPAIGN','load','save'])

def build():
    inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};r2=load(ROOT/'project-state/r2-inventory.json');objects={o['key']:o for o in r2['objects']};hashes=collections.defaultdict(list);keys=collections.defaultdict(list);anomalies=[]
    for r in rows.values():
        if r.get('checksum_sha256'):hashes[r['checksum_sha256'].lower()].append(r)
        key=r.get('r2_key')
        if not key and r.get('r2_url') and urlsplit(r['r2_url']).netloc=='files.abqinfo.com':key=unquote(urlsplit(r['r2_url']).path.lstrip('/'))
        if key:
            keys[key].append(r)
            if key not in objects:anomalies.append(dict(type='claimed_r2_key_absent_from_saved_listing',id=r['id'],key=key))
            elif r.get('size_bytes') and r['size_bytes']!=objects[key]['size_bytes']:anomalies.append(dict(type='inventory_source_size_differs_from_r2_size',id=r['id'],key=key,source_size_bytes=r['size_bytes'],r2_size_bytes=objects[key]['size_bytes'],note='May describe source/wrapper or historical source; no automatic replacement of provenance.'))
        if r['status'] in ['duplicate','superseded']:
            text=str(r.get('exclusion_reason',''))+' '+' '.join(str(n) for n in r.get('processing_notes',[]) if n is not None)
            explicit=set(re.findall(r'canonical inventory record ((?:src|lin)-[a-f0-9]{16})',text))
            explicit.update(x for x in r.get('cited_successors',[]) if re.fullmatch(r'(?:src|lin)-[a-f0-9]{16}',x))
            if r.get('duplicate_of'):explicit.add(r['duplicate_of'])
            for target in sorted(explicit):
                if target not in rows:anomalies.append(dict(type='missing_explicit_canonical_or_successor_id',id=r['id'],target=target))
            if r['status']=='superseded' and not explicit and not r.get('cited_successors'):
                anomalies.append(dict(type='legacy_supersession_target_not_structured',id=r['id'],note='Historical prose may identify successor; no deterministic target ID or cited-successor metadata. Retain evidence for later research, without reopening disposition.'))
    groups=[]
    for h,rs in sorted(hashes.items()):
        if len(rs)<2:continue
        retained=[r for r in rs if r['status'] not in ['excluded','duplicate','superseded','requires human review','pending review']]
        correct=True
        for r in rs:
            if r['status']=='duplicate' and retained:
                urls={x.get('source_url') for x in retained}|{x.get('direct_file_url') for x in retained}|{x.get('r2_url') for x in retained}
                evidence=str(r.get('exclusion_reason',''))+' '+' '.join(str(n) for n in r.get('processing_notes',[]) if n is not None)
                linked=bool(set(r.get('cited_successors',[])) & (urls-{None})) or any(x['id'] in evidence for x in retained)
                if not linked:correct=False
        if not retained and any(r['status']=='duplicate' for r in rs):
            correct=False
        classification='already_correct_relationship_or_all_excluded' if correct and len(retained)<=1 else 'legacy_relationship_needs_research'
        if len(retained)>1:anomalies.append(dict(type='multiple_retained_later_state_rows_share_exact_hash',checksum_sha256=h,ids=[r['id'] for r in retained],note='Read-only audit: protected/settled later-state rows are not reopened; original/component/page semantics need research.'))
        elif not correct:anomalies.append(dict(type='duplicate_hash_group_relationship_not_explicit',checksum_sha256=h,ids=[r['id'] for r in rs]))
        groups.append(dict(checksum_sha256=h,size_values=sorted({r.get('size_bytes') for r in rs if r.get('size_bytes') is not None}),records=[dict(id=r['id'],status=r['status'],size_bytes=r.get('size_bytes'),source_url=r.get('source_url'),r2_key=r.get('r2_key'),cited_successors=r.get('cited_successors',[])) for r in rs],classification=classification,cross_directory_alias=len({(r.get('source_url') or '').rsplit('/',1)[0] for r in rs})>1))
    duplicate_keys=[]
    for key,rs in sorted(keys.items()):
        if len(rs)>1:
            hs={r.get('checksum_sha256') for r in rs}-{None};sizes={r.get('size_bytes') for r in rs}-{None};consistent=len(hs)<=1 and len(sizes)<=1
            duplicate_keys.append(dict(key=key,ids=[r['id'] for r in rs],identity_consistent=consistent))
            if not consistent:anomalies.append(dict(type='inconsistent_duplicate_r2_key_metadata',key=key,ids=[r['id'] for r in rs]))
    counts=collections.Counter(r['status'] for r in rows.values())
    assert len(rows)==len(inv['candidates'])==7137
    assert inv['counts']=={s:counts[s] for s in inv['allowed_statuses']}
    campaign=load(CAMPAIGN)
    return dict(schema_version=1,artifact_type='inventory_exact_identity_integrity_audit',recorded_at=datetime.now(timezone.utc).isoformat(),audit_population=7137,checksummed_records=sum(len(v) for v in hashes.values()),exact_hash_groups=groups,already_correct_groups=sum(g['classification']=='already_correct_relationship_or_all_excluded' for g in groups),newly_reconciled_aliases=[r['id'] for r in campaign['resolved_records'] if r['decision']=='duplicate'],automatic_audit_status_changes=[],duplicate_r2_key_groups=duplicate_keys,unresolved_anomalies=anomalies,status_counts=inv['counts'],saved_r2_summary={'object_count':r2['object_count'],'total_bytes':r2['total_bytes']},visitor_visible_content_changed=False,method='All inventory rows; exact non-null SHA-256 and size, explicit canonical ID/cited-successor metadata, R2 key/URL existence and size. No near-name guesses or subjective reopening. Ambiguous legacy discrepancies recorded for independent future research.')

if __name__=='__main__':
    d=build();save(DISC/f'inventory-exact-identity-integrity-audit-{DATE}.json',d)
    print(json.dumps({'population':d['audit_population'],'exact_hash_groups':len(d['exact_hash_groups']),'already_correct_groups':d['already_correct_groups'],'anomalies':len(d['unresolved_anomalies']),'automatic_audit_status_changes':0}))
