"""Keep completed stage audits sealed; independently constrain the publication delta."""
import json
import subprocess
import hashlib
from collections import Counter
from pathlib import Path
from WorkflowStageLifecycle import StageSnapshot, canonical_bytes, digest

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / 'project-state/discovery/planning-documents-root-hugo-implementation-2026-09-26.json'
BASELINE = '2c5e170e1dda5a4b3ad44dc328f6e3cb1b458063'
_guarded = False
STAGE = StageSnapshot('planning-publication')

def validate_delta(data, prior, current, changed_paths, page_hashes, r2_before, r2_current):
    """A historical seal is usable only when every current mutation is accounted for."""
    ids=set(data['implemented_inventory_ids'])
    old={r['id']:r for r in prior['candidates']}; rows={r['id']:r for r in current['candidates']}
    assert len(rows)==len(current['candidates'])==len(old)==len(prior['candidates'])
    assert prior.keys()==current.keys()
    assert all(prior[k]==current[k] for k in prior if k not in {'candidates','generated_at','counts','next_pending_id'})
    assert rows.keys()==old.keys() and {i for i in rows if rows[i]!=old[i]}==ids
    allowed={'status','implementation_location','implementation_locations','description','description_word_count','quality_assessment','validation_status','processing_notes','updated_at'}
    for rid in ids:
        r=rows[rid]
        assert old[rid]['status']=='placement assigned'
        assert {k for k in r if r[k]!=old[rid].get(k)}<=allowed
        assert r['status']=='implemented' and r['scope_assessment']['final_scope_decision']=='passes_both_gates'
    if data.get('expected_row_digests'):
        assert {rid:digest(rows[rid]) for rid in ids}==data['expected_row_digests'], 'Unexpected value in authorized inventory row'
    if 'counts' in current:
        counts=Counter(r['status'] for r in rows.values())
        assert current['counts']=={s:counts[s] for s in current['allowed_statuses']}
        pending=[r['id'] for r in rows.values() if r['status'] in {'pending review','approved for addition','downloaded','parsed','description drafted','placement assigned'} or r['status']=='implemented' and r.get('validation_status')!='passed']
        assert current['next_pending_id']==(min(pending) if pending else None)
    assert set(changed_paths)==set(data['changed_pages']) and len(changed_paths)==6
    assert page_hashes==data['page_sha256']
    assert r2_before==r2_current

def guard_current_delta():
    global _guarded
    data=implementation()
    if not data or _guarded: return
    def prior(path):
        return json.loads(subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT).decode('utf-8-sig'))
    def current(path): return STAGE.load_json(path)
    endpoint=STAGE.end
    args=['git','diff',BASELINE]+([endpoint] if endpoint else [])+['--name-only','--','content','layouts','assets','static','hugo.toml']
    paths=subprocess.check_output(args,cwd=ROOT,text=True).splitlines()
    if not endpoint:
        untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','content','layouts','assets','static','hugo.toml'],cwd=ROOT,text=True).splitlines()
        assert not untracked
    verified=json.loads((ROOT/data['archive_artifact']).read_text(encoding='utf-8'))
    assert set(data['implemented_inventory_ids'])=={r['id'] for r in verified['results']}
    prep=json.loads((ROOT/'project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json').read_text(encoding='utf-8'))
    approved_pages={r['proposed_canonical_page'] for r in prep['records']}
    assert set(data['changed_pages'])==approved_pages
    hashes={p:hashlib.sha256(canonical_bytes(STAGE.read_bytes(p))).hexdigest() for p in data['changed_pages']}
    reference={p:hashlib.sha256(canonical_bytes(subprocess.check_output(['git','show',data['page_hash_reference_commit']+':'+p],cwd=ROOT))).hexdigest() for p in data['changed_pages']}
    assert reference==data['page_sha256'], 'Recorded page hashes differ from the reviewed implementation snapshot'
    validate_delta(data,prior('project-state/master-inventory.json'),current('project-state/master-inventory.json'),paths,hashes,prior('project-state/r2-inventory.json'),current('project-state/r2-inventory.json'))
    before_queue=prior('project-state/discovery/retained-source-audit-queue.json')
    after_queue=current('project-state/discovery/retained-source-audit-queue.json')
    validate_queue_delta(data,before_queue,after_queue,current('project-state/master-inventory.json'))
    _guarded=True

def validate_queue_delta(data,before,after,inventory):
    old={r['source_url']:r for r in before['records']}; new={r['source_url']:r for r in after['records']}
    assert len(new)==len(after['records']) and old.keys()<=new.keys()
    assert all(new[url]==record for url,record in old.items()), 'Historical source audit changed'
    rows={r['id']:r for r in inventory['candidates']}
    expected={rows[rid]['source_url']:rid for rid in data['implemented_inventory_ids']}
    assert new.keys()-old.keys()==expected.keys(), 'Unapproved retained-source queue delta'
    assert all(before[k]==after[k] for k in before if k not in {'generated_at','counts','next_pending_source_url','records'})
    for url,rid in expected.items():
        r=new[url]
        assert r['candidate_id']==rid and r['canonical_page']==rows[rid]['proposed_canonical_page']
        assert r['audit_status']=='pending descendant crawl' and r['crawl_output'] is None
        assert r['discovered_documents']==r['archived_documents']==0
    counts=Counter(r['audit_status'] for r in new.values())
    assert after['counts']=={s:counts[s] for s in after['allowed_statuses']}

def implementation():
    if not ARTIFACT.exists():
        return None
    data = STAGE.load_json(ARTIFACT)
    assert data['baseline_commit'] == BASELINE
    assert STAGE.stage['baseline_commit']==BASELINE
    assert len(data['implemented_inventory_ids']) == len(set(data['implemented_inventory_ids'])) == 12
    assert set(data['expected_row_digests'])==set(data['implemented_inventory_ids'])
    return data

def sealed_json(path):
    data = implementation()
    relative = Path(path).resolve().relative_to(ROOT).as_posix()
    if data:
        guard_current_delta()
        return json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + relative], cwd=ROOT).decode('utf-8-sig'))
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
