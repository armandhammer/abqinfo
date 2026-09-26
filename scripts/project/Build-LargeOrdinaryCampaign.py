#!/usr/bin/env python3
"""Record-level queue, never interpret research coverage as applied decisions."""
import collections, hashlib, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / 'project-state/discovery'
DATE = '2026-09-26'
BASE = 'b8a52bbdef5f78599187b1020d1f10b65c1a17b4'
SELECTION = DISC / f'ordinary-queue-large-campaign-selection-{DATE}.json'
CAMPAIGN = DISC / f'ordinary-queue-large-resolution-campaign-{DATE}.json'

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def save(p, d):
    t = p.with_suffix('.json.tmp')
    t.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    t.replace(p)

def digest(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def nodes(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from nodes(x)
    elif isinstance(v, list):
        for x in v:
            yield from nodes(x)

def family(row, rec):
    u = urlsplit(rec.get('authoritative_url') or row['source_url'])
    if rec.get('recommended_status')=='duplicate' and rec.get('canonical_id'):
        return 'Delivery aliases of '+rec['canonical_id']
    path = u.path.removesuffix('/view')
    p = path.split('/resolveuid/')[0]
    if '/resolveuid/' not in u.path:
        p = p.rsplit('/', 1)[0]
    if u.netloc == 'www.mrcog-nm.gov' and rec.get('mrcog_document_number') in range(2055,2068):
        return 'MRCOG historical congestion-management corridor data and strategies'
    return u.netloc + p

def main():
    assert not CAMPAIGN.exists() or load(CAMPAIGN)['state']=='queue_built', 'Resume existing campaign; do not reset its evidence'
    inv = load(ROOT / 'project-state/master-inventory.json')
    rows = {r['id']:r for r in inv['candidates']}
    pending = {i:r for i,r in rows.items() if r['status']=='pending review'}
    research = collections.defaultdict(list)
    for p in sorted(DISC.glob('*cluster-research*.json')):
        d = load(p)
        for n in nodes(d):
            if n.get('id') in pending and n.get('recommended_status'):
                research[n['id']].append((p.relative_to(ROOT).as_posix(),n))
    ms4 = set(load(DISC/'2014-ms4-family-package-gate-2026-09-18.json')['scope']['candidate_ids'])
    protected = set(ms4)
    gated = {}
    queue = []
    # These are pre-existing completed or independently gated scopes. Research
    # recommendations with shared_state_written=[] are not applied dispositions.
    frozen_scopes = ['capital-spending-consolidation-closeout-status-2026-09-18.json',
                     'dpm-executive-committee-consolidation-manifest-2026-09-17.json']
    for name in frozen_scopes:
        protected.update(re.findall(r'(?:src|lin)-[a-f0-9]{16}',(DISC/name).read_text(encoding='utf-8-sig')))
    for i,r in sorted(pending.items()):
        matches = research.get(i,[])
        rec = matches[-1][1] if matches else {}
        url = r['source_url'] or ''
        joined = (url+' '+r['title']).lower()
        gate = None
        if i in protected: gate = 'explicitly protected MS4, completed Capital Spending or DPM package scope'
        elif re.search(r'prescription.?trails|notices.?and.?orders|local-government-coordinating|lgcc|o-23-96|r-24-17',joined): gate = 'owner-named protected family'
        elif urlsplit(url).netloc.lower().endswith('dot.nm.gov'): gate = 'NMDOT scope precedent; excluded from campaign selection'
        elif any(n.get('recommended_status')=='requires human review' for _,n in matches): gate = 'saved human-review recommendation; do not bypass unresolved gate'
        elif any(w in joined for w in ['complaint','correspondence','prescription','enactment']): gate = 'privacy or finality risk; deferred from high-confidence selection'
        if gate: gated[i] = gate
        kind = rec.get('content_kind','')
        status = rec.get('recommended_status')
        html = status=='excluded' and kind=='HTML'
        static_exclusion = status=='excluded' and kind.startswith('PDF') and rec.get('exclusion_reason') and rec.get('checksum_sha256')
        can = rows.get(rec.get('canonical_id'),{})
        exact_alias = status=='duplicate' and kind.startswith('PDF') and rec.get('checksum_sha256') and can.get('checksum_sha256')==rec.get('checksum_sha256') and can.get('size_bytes')==rec.get('size_bytes') and can.get('status') in ['validated','implemented','placement assigned']
        cmp = status=='approved for addition' and rec.get('mrcog_document_number') in range(2055,2068)
        # ArcGIS/live services have a deliberate archival exception. A HTML
        # signature alone cannot establish their exclusion.
        if html and re.search(r'arcgis|/gis|map-view|dashboard|tracker|/services/',url,re.I): html=False
        actionable = not gate and (html or exact_alias or cmp or static_exclusion)
        u=urlsplit(url)
        queue.append(dict(id=i,title=r['title'],source_url=url,direct_file_url=r.get('direct_file_url'),parent_url=r.get('parent_url'),source_directory=u.path.rsplit('/',1)[0],host=u.netloc,inferred_family=family(r,rec),research_artifacts=[p for p,_ in matches],saved_recommendation=status,prior_identity_established=bool(rec.get('checksum_sha256')),candidate_container_type=kind or r['file_type'],likely_local_relevance='City/local-government source' if 'cabq.gov' in u.netloc or 'mrcog' in u.netloc or 'riometro' in u.netloc else 'must establish material Albuquerque component',disposition_difficulty='low: saved measured terminal evidence' if html or exact_alias else 'full source QA and scope required',completed_or_gated=bool(gate),skip_reason=gate or (None if actionable else 'not selected: substantive, live-service, unresolved or unsaved evidence; available for later independent review'),actionable=actionable,saved_evidence=rec if actionable else None,baseline_row_sha256=digest(r)))
    groups=collections.defaultdict(list)
    for q in queue:
        if q['actionable']:groups[q['inferred_family']].append(q)
    def rank(item):
        name,qs=item
        return (0 if name.startswith('MRCOG historical') else 1 if any(q['saved_recommendation']=='duplicate' for q in qs) else 2 if all(q['candidate_container_type']=='HTML' for q in qs) else 3,-len(qs),name)
    families=[]
    for n,(name,qs) in enumerate(sorted(groups.items(),key=rank),1):
        families.append(dict(family_id=f'family-{n:03}',family=name,candidate_ids=sorted(q['id'] for q in qs),candidate_count=len(qs),reason='unapplied classification-only recommendations, current pending state, no explicit gate; complete source-directory or documentary-program unit',order=n))
    baseline_r2=load(DISC/f'ordinary-queue-large-campaign-r2-baseline-{DATE}.json')
    saved_r2=load(ROOT/'project-state/r2-inventory.json')
    identity=lambda d:{o['key']:(o['size_bytes'],o['etag']) for o in d['objects']}
    assert identity(saved_r2)==identity(baseline_r2)
    selection=dict(schema_version=1,artifact_type='ordinary_queue_large_campaign_selection',recorded_at=datetime.now(timezone.utc).isoformat(),baseline_commit=BASE,total_pending_population=len(pending),excluded_gated_pending_ids=gated,all_pending_records=queue,candidate_families=families,selected_family_order=[f['family_id'] for f in families],target_resolved_minimum=300,target_family_minimum=20,target_resolved_maximum=500,reason_for_prior_queue_disagreement='Historical filter treated every ID mentioned in classification-only research as completed. This queue distinguishes applied current dispositions and explicit gates from unapplied recommendations. No settled terminal row is reopened.',visitor_visible_content_changed=False)
    save(SELECTION,selection)
    d=dict(schema_version=1,artifact_type='ordinary_queue_large_resolution_campaign',baseline_commit=BASE,baseline_inventory_counts=inv['counts'],baseline_r2_artifact=f'project-state/discovery/ordinary-queue-large-campaign-r2-baseline-{DATE}.json',baseline_r2={'object_count':baseline_r2['object_count'],'total_bytes':baseline_r2['total_bytes']},selection_artifact=SELECTION.relative_to(ROOT).as_posix(),state='queue_built',families_processed=[],resolved_records=[],deferred_records=[],archive_objects=[],project_storage_limit_bytes=10000000000,hard_cap_formerly_pending=500,visitor_visible_content_changed=False,content_tree_baseline=subprocess.check_output(['git','rev-parse',BASE+':content'],cwd=ROOT,text=True).strip(),integration={})
    save(CAMPAIGN,d)
    print(json.dumps({'pending':len(pending),'gated':len(gated),'eligible_records':sum(f['candidate_count'] for f in families),'families':len(families),'first_families':families[:5]}))

if __name__=='__main__':main()
