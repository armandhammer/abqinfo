#!/usr/bin/env python3
"""Second campaign evidence operations. Decisions require explicit review input."""
import argparse, collections, concurrent.futures, hashlib, json, re, runpy, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
sys.stdout.reconfigure(encoding='utf-8')

ROOT=Path(__file__).resolve().parents[2]
DISC=ROOT/'project-state/discovery'
DATE='2026-09-26'
BASE='34ccc0fe230ffb8290652979cbe8603c69db3115'
ART=DISC/f'ordinary-queue-second-large-resolution-campaign-{DATE}.json'
SEL=DISC/f'ordinary-queue-second-large-campaign-selection-{DATE}.json'
STAGE=ROOT/f'research/staging/ordinary-second-large-campaign-{DATE}'
QA=ROOT/f'tmp/ordinary-second-large-campaign-qa-{DATE}'

def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def save(p,d):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');t.replace(p)
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def nodes(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from nodes(x)
    elif isinstance(v,list):
        for x in v:yield from nodes(x)
def family_path(f):return DISC/f"ordinary-second-large-campaign-{f['family_id']}-{DATE}.json"

START=[
 ('Later MRCOG CMP measurement releases',['src-b9f68064d83c5038','src-ba0a4030fcc63e6e','src-d5e398345f6eec6b']),
 ('Municipal Development CIP transaction forms',['src-7db522c233d09f76','src-9b8823612d4eae10','src-c5a719e610edf283','src-cf6ea129deaacd75']),
 ('Municipal Development construction permit supporting documents',['src-5962fd01c9b7f0a4','src-8939a2f1f9f4b382','src-906f674e57f311e0','src-a76b5c8c3ad10b52']),
 ('Council redistricting starting documentary unit',['src-48b982c1c959a31b','src-757e91ccdac87f26','src-a919849dfe495cb0','src-b80b979585cddac4','src-bc66b8e82ed23dbb','src-e7c627b2b1b1b955','src-ff26854cb2f1e490']),
 ('Planning online forms and regulatory instructions',['src-6f478812572d6cf8','src-744bfa29e25ce9ab','src-8370979b7d21890b','src-d9b63150144be31e','src-ec6c7cd6b216ce05','src-f3d1b969631a7c61'])]

def init():
    assert not ART.exists() and not SEL.exists(),'Resume existing evidence; never reset'
    inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    old=load(DISC/f'ordinary-queue-large-campaign-selection-{DATE}.json')
    post=load(DISC/f'ordinary-queue-next-position-post-large-campaign-{DATE}.json')
    pending={i:r for i,r in rows.items() if r['status']=='pending review'}
    research=collections.defaultdict(list)
    for p in sorted(DISC.glob('*cluster-research*.json')):
        for n in nodes(load(p)):
            if n.get('id') in pending and n.get('recommended_status'):research[n['id']].append((rel(p),n))
    qs=[]
    blocked=set(post['source_or_structural_blocked_pending_ids']);gates=post['gated_pending_ids']
    for oldq in old['all_pending_records']:
        if oldq['id'] not in pending:continue
        q=dict(oldq);q['baseline_row_sha256']=digest(rows[q['id']]);q['research_artifacts']=[p for p,n in research[q['id']]]
        q['saved_evidence']=research[q['id']][-1][1] if research[q['id']] else None
        q['gated']=q['id'] in gates or q['id'] in blocked
        qs.append(q)
    byid={q['id']:q for q in qs};groups=[];used=set()
    for name,ids in START:
        ids=[i for i in ids if i in pending and not byid[i]['gated']]
        assert ids
        groups.append((name,ids));used.update(ids)
    rest=collections.defaultdict(list)
    for q in qs:
        if q['gated'] or q['id'] in used:continue
        # DocumentCenter needs explicit program regrouping after content review.
        rec=q['saved_evidence'] or {};name=q['inferred_family']
        if 'mrcog-nm.gov/DocumentCenter' in name:name='MRCOG ungrouped publication '+str(rec.get('mrcog_document_number') or q['id'])
        if 'riometro.org/DocumentCenter' in name:name='Rio Metro ungrouped publication '+str(rec.get('title') or q['title'])
        rest[name].append(q)
    def rank(x):
        name,g=x; statuses={q['saved_recommendation'] for q in g}
        return (0 if statuses=={'duplicate'} else 1 if statuses=={'excluded'} else 2,-len(g),name)
    groups += [(n,[q['id'] for q in g]) for n,g in sorted(rest.items(),key=rank)]
    families=[dict(family_id=f'family-{i:03}',family=n,candidate_ids=sorted(ids),order=i,candidate_count=len(ids),boundary='Discovery unit; split before decisions if document purposes differ.') for i,(n,ids) in enumerate(groups,1)]
    live=load(DISC/f'ordinary-queue-second-large-campaign-r2-baseline-{DATE}.json');saved=load(ROOT/'project-state/r2-inventory.json')
    ident=lambda d:{o['key']:(o['size_bytes'],o['etag']) for o in d['objects']}
    assert ident(live)==ident(saved) and live['total_bytes']<=10000000000
    save(SEL,dict(schema_version=1,baseline_commit=BASE,all_pending_records=qs,candidate_families=families,gated_pending_ids=gates,structural_blocked_ids=sorted(blocked),starting_population=sorted(pending),baseline_row_digests={i:digest(r) for i,r in rows.items()},visitor_visible_content_changed=False))
    save(ART,dict(schema_version=1,artifact_type='ordinary_queue_second_large_resolution_campaign',baseline_commit=BASE,started_at=now(),baseline_inventory_counts=inv['counts'],baseline_r2={'object_count':live['object_count'],'total_bytes':live['total_bytes']},baseline_r2_artifact=rel(DISC/f'ordinary-queue-second-large-campaign-r2-baseline-{DATE}.json'),selection_artifact=rel(SEL),state='selection_built',primary_target=600,preferred_target=650,hard_cap_formerly_pending=700,families_processed=[],resolved_records=[],deferred_records=[],archive_objects=[],capacity_deferrals=[],project_storage_limit_bytes=10000000000,visitor_visible_content_changed=False,content_tree_baseline=subprocess.check_output(['git','rev-parse',BASE+':content'],cwd=ROOT,text=True).strip(),integration={}))
    print(json.dumps({'pending':len(pending),'gated':len(gates),'structural':len(blocked),'ungated':sum(not q['gated'] for q in qs),'families':len(families),'first':families[:8]}))

def prepare(a):
    common=runpy.run_path(str(ROOT/'scripts/project/Prepare-LargeOrdinaryCampaign.py'))
    inspect=common['inspect']; inspect.__globals__['STAGE']=STAGE;inspect.__globals__['QA']=QA
    STAGE.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    s=load(SEL);qs={q['id']:q for q in s['all_pending_records']}
    for f in s['candidate_families']:
        if not a.start<=f['order']<=a.end:continue
        p=family_path(f);fam=load(p) if p.exists() else dict(schema_version=1,artifact_type='ordinary_second_large_campaign_family_evidence',family_id=f['family_id'],family=f['family'],scope_ids=f['candidate_ids'],records=[],visitor_visible_content_changed=False)
        done={r['id'] for r in fam['records']}
        def fetch(rid):
            try:
                q=dict(qs[rid]);r=dict(q['saved_evidence'] or {});kind=r.get('content_kind','')
                if kind.startswith('PDF'):r['content_kind']='PDF'
                if not kind or not (kind.startswith('PDF') or kind in ['HTML','JPEG']):raise ValueError('Needs format-specific independent preparation: '+kind)
                if not r.get('authoritative_url'):r['authoritative_url']=q.get('direct_file_url') or q['source_url']
                q['saved_evidence']=r
                return inspect(q)
            except Exception as e:return dict(id=rid,disposition='deferred',error=str(e),saved_evidence=qs[rid]['saved_evidence'],historical_source_evidence_preserved=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
            for r in pool.map(fetch,[i for i in f['candidate_ids'] if i not in done]):
                fam['records'].append(r);save(p,fam)
        fam['state']='prepared_pending_independent_review';save(p,fam)
        print(f['family_id'],f['family'],len(fam['records']),'prepared',sum(r['disposition']=='deferred' for r in fam['records']),'deferred',flush=True)

def show(a):
    s=load(SEL)
    for f in s['candidate_families']:
        if not a.start<=f['order']<=a.end:continue
        print(f['family_id'],f['family'],f['candidate_count'])
        p=family_path(f)
        if not p.exists():continue
        for r in load(p)['records']:
            rec=r['saved_evidence'] or {};q=r.get('fresh_source_qa',{})
            print(r['id'],r['disposition'],rec.get('title') or rec.get('title_for_reference') or rec.get('file'),q.get('page_count'),q.get('word_count'),r.get('error',''))
            print('basis:',r.get('rationale') or rec.get('basis'),rec.get('description') or rec.get('what_it_is'))
            if a.text and q.get('full_text_path'):
                t=(ROOT/q['full_text_path']).read_text(encoding='utf-8');print(t[:a.text]);print('ENDING',t[-min(a.text//3,1500):])
            if a.images:print('images',q.get('contact_sheets'))

def review(a):
    """Explicit decisions supplied after independent content/visual review."""
    decisions=load(ROOT/a.decisions)['decisions'];s=load(SEL)
    rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
    objects=load(ROOT/'project-state/r2-inventory.json')['objects']
    for f in s['candidate_families']:
        p=family_path(f)
        if not p.exists():continue
        fam=load(p);changed=False
        for r in fam['records']:
            if r['id'] not in decisions:continue
            x=decisions[r['id']];qa=r.get('fresh_source_qa');rec=r['saved_evidence'];status=x['status']
            assert status in ['approved for addition','excluded','duplicate','superseded']
            assert x['rationale'] and (qa or rec['content_kind']=='HTML')
            if qa:
                assert qa['source_exact_verified'] and x.get('visual_review')
                qa['representative_visual_qa']='passed_agent_inspection_opening_middle_ending'
                qa['visual_review_evidence']=x['visual_review'];qa['visually_reviewed_at']=now()
            r['disposition']=status;r['rationale']=x['rationale'];r['independent_review_input']=a.decisions
            r['quality_assessment'].update(visual_inspection=x.get('visual_review','Saved full HTML content analysis; no static original'),actual_function=x['rationale'],standalone_public_value=x.get('public_value') or ('No distinct eligible standalone public record. '+x['rationale']),information_density=x.get('density','Measured full-document pages/words and source container are retained in QA.'),series_component_relationship=x.get('relationship','Family boundary reviewed; independent original or administrative supporting file as identified in rationale.'),intended_publication_form=x.get('presentation','none; no visitor-visible implementation authorized'),substantive_rationale=x['rationale'])
            if qa and qa['page_count']<=2 and (qa.get('word_count') or 0)<250 and status=='approved for addition':
                assert x.get('limited_content_exception');r['quality_assessment']['limited_content_exception']=x['limited_content_exception']
            r['mission_scope_assessment']=dict(assessed_at=now(),geographic_institutional_scope=x.get('institution') or rows[r['id']]['agency'],specific_albuquerque_connection=x.get('connection') or x['rationale'],abqinfo_public_information_value=x.get('public_value') or 'No substantive additional ABQInfo policy/infrastructure information is established by this delivery.',general_context_exclusion_test=x.get('exclusion_test') or 'City hosting, jurisdiction, geographic origin and procedural usefulness alone are insufficient; the actual document function and distinct public value control.',final_scope_decision='passes_both_gates' if status=='approved for addition' else 'excluded',substantive_rationale=x['rationale'])
            if status in ['duplicate','superseded']:
                cid=x.get('canonical_id') or r['canonical_candidate_id'];can=rows[cid];assert cid!=r['id'];r['canonical_candidate_id']=cid
                if status=='duplicate':
                    assert (qa['size_bytes'],qa['checksum_sha256'])==(can['size_bytes'],can['checksum_sha256'])
                    r['exact_identity_relationship']=dict(canonical_id=cid,canonical_status=can['status'],same_sha256=True,same_size=True,canonical_r2_key=can.get('r2_key'))
                else:assert x.get('chronology_evidence');r['chronology_evidence']=x['chronology_evidence']
                r['archival_readiness']='Retain canonical relationship; no second upload'
            if status=='approved for addition':
                assert qa and x.get('connection') and x.get('public_value') and x.get('page')
                r['proposed_canonical_page']=x['page'];assert (ROOT/x['page']).exists()
                key=x.get('key') or x['page'].removeprefix('content/').removesuffix('.md')+'/'+re.sub(r'[^a-z0-9]+','-',(x.get('title') or rec['title']).lower()).strip('-')+'.pdf'
                assert not any(o['key'].casefold()==key.casefold() for o in objects)
                aliases=[z['id'] for z in rows.values() if z['id']!=r['id'] and z.get('checksum_sha256')==qa['checksum_sha256']]
                assert not any(rows[i]['status'] in ['placement assigned','implemented','validated','approved for addition'] for i in aliases),'Retained exact canonical unresolved'
                r['archive_preflight']=dict(same_hash_inventory_ids=aliases,key_collision=False,namespace_basis='Established page and R2 topical namespace: '+x['page'])
                r['r2_key']=key;r['archival_readiness']='Original fully prepared; authorized guarded upload pending'
                r['reviewed_title']=x.get('title') or rec['title']
            r['review_complete']=True;changed=True
        if changed:fam['state']='reviewed_decisions_ready_for_inventory';save(p,fam)
    print('Explicit reviewed decisions saved:',len(decisions))

def apply(a):
    s=load(SEL);qs={q['id']:q for q in s['all_pending_records']};d=load(ART)
    for f in s['candidate_families']:
        if not a.start<=f['order']<=a.end:continue
        p=family_path(f)
        if not p.exists():continue
        fam=load(p);selected=[r for r in fam['records'] if r.get('review_complete')]
        done={r['id'] for r in d['resolved_records']};selected=[r for r in selected if r['id'] not in done]
        if not selected:continue
        assert len(d['resolved_records'])+len(selected)<=700,'Hard cap; choose a smaller coherent remaining unit'
        rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']};terminal=[];approved=[]
        for r in selected:
            i=r['id'];row=rows[i];q=qs[i];assert not q['gated']
            note='Second large ordinary campaign 2026-09-26: explicit reviewed evidence '+rel(p)+'. Background only; no content or publication changes.'
            assert (row['status']=='pending review' and digest(row)==q['baseline_row_sha256']) or note in row['processing_notes'],'Unexpected concurrent row mutation'
            qa=r.get('fresh_source_qa');rec=r['saved_evidence']
            if r['disposition']=='approved for addition':
                assert r['mission_scope_assessment']['final_scope_decision']=='passes_both_gates'
                approved.append(dict(id=i,changes=dict(status='approved for addition',title=r.get('reviewed_title') or rec['title'],agency=rec.get('publisher') or row['agency'],size_bytes=qa['size_bytes'],checksum_sha256=qa['checksum_sha256'],file_type=qa['container'],local_path=qa['staged_path'],scope_assessment=r['mission_scope_assessment'],proposed_canonical_page=r['proposed_canonical_page'],processing_notes=row['processing_notes']+[note],validation_status='Full source/quality/scope reviewed; original prepared; no implementation')))
            else:
                z=dict(id=i,recommended_status=r['disposition'],scope_assessment=r['mission_scope_assessment'],evidence_note=note,size_bytes=(qa or rec)['size_bytes'],checksum_sha256=(qa or rec)['checksum_sha256'])
                if row.get('checksum_sha256'):assert row['checksum_sha256']==z['checksum_sha256'],'Historical source identity changed'
                if r['disposition']=='excluded':z['exclusion_reason']=r['rationale']
                else:z.update(canonical_id=r['canonical_candidate_id'],relationship=r['rationale'])
                terminal.append(z)
        application=DISC/f"ordinary-second-large-campaign-{f['family_id']}-application-{DATE}.json"
        save(application,dict(decisions=terminal,approved_updates=approved,source_evidence_artifact=rel(p),visitor_visible_content_changed=False))
        if terminal:subprocess.run([sys.executable,'-B',str(ROOT/'scripts/project/Apply-SavedTerminalResearch.py'),'--research',str(application),'--ids',','.join(z['id'] for z in terminal)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        if approved:subprocess.run([sys.executable,'-B',str(ROOT/'scripts/project/Update-CandidatesBatch.py'),'--requests',rel(application)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
        for r in selected:
            assert rows[r['id']]['status']==r['disposition']
            d['resolved_records'].append(dict(id=r['id'],initial_status='pending review',decision=r['disposition'],current_status=rows[r['id']]['status'],family_id=f['family_id'],evidence_artifact=rel(p)))
        d['families_processed']=[x for x in d['families_processed'] if x['family_id']!=f['family_id']]+[dict(family_id=f['family_id'],family=f['family'],resolved_count=sum(x['family_id']==f['family_id'] for x in d['resolved_records']),complete=all(x.get('review_complete') for x in fam['records']),artifact=rel(p))]
        d['state']='pending_review_and_archive_in_progress';save(ART,d)
        print(f['family_id'],'applied',len(selected),'total',len(d['resolved_records']),flush=True)
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/project/Write-ProjectCheckpoint.ps1','-CompletedRange',f"Second large campaign in progress: {len(d['resolved_records'])} formerly pending resolutions; archives and remaining review tracked in {rel(ART)}",'-ResumeCommand','Resume second campaign evidence; no content changes; preserve all gates.'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['init','prepare','show','review','apply']);p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=5);p.add_argument('--workers',type=int,default=4);p.add_argument('--text',type=int,default=0);p.add_argument('--images',action='store_true');p.add_argument('--decisions');a=p.parse_args()
    {'init':init,'prepare':lambda:prepare(a),'show':lambda:show(a),'review':lambda:review(a),'apply':lambda:apply(a)}[a.operation]()
if __name__=='__main__':main()
