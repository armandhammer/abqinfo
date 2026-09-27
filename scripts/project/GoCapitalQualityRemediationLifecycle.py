"""Exact owner-review delta: 32 queue matches, two required masters, six pages."""
import json,hashlib
from WorkflowStageLifecycle import ROOT,StageSnapshot,git,canonical_bytes,digest
from PublicationQuality import validate_affected_records
PREFIX='project-state/discovery/go-capital-quality-remediation-2026-09-27/'
QUEUE='project-state/discovery/publication-quality-remediation-2026-09-26.json'
ALLOWED={'project-state/workflow-stage-lifecycle.json','scripts/project/GoCapitalQualityRemediationLifecycle.py','scripts/project/Test-GoCapitalQualityRemediation.py','scripts/project/Invoke-ProjectValidation.ps1','project-state/master-inventory.json',QUEUE,QUEUE.removesuffix('.json')+'.md','project-state/CURRENT.md','project-state/checkpoint.json','project-state/discovery/consolidated-human-review-queue.json'}
def validate_delta(data,prior,current,oldq,q,hashes,r2old,r2new):
    old={r['id']:r for r in prior['candidates']};rows={r['id']:r for r in current['candidates']}
    assert len(old)==len(prior['candidates'])==len(rows)==len(current['candidates']) and old.keys()==rows.keys()
    assert {i for i in rows if rows[i]!=old[i]}==set(data['changed_inventory_ids'])
    assert {k:v for k,v in prior.items() if k!='candidates'}=={k:v for k,v in current.items() if k!='candidates'}
    assert {i:digest(rows[i]) for i in data['changed_inventory_ids']}==data['expected_row_digests']
    allowed={'publication_quality_decision','publication_relationship','scope_assessment','updated_at','processing_notes','implementation_location','implementation_locations','cross_listing_approved'}
    for i in data['changed_inventory_ids']:
        assert {k for k in rows[i].keys()|old[i].keys() if rows[i].get(k)!=old[i].get(k)}<=allowed
        assert rows[i]['processing_notes'][:-1]==old[i]['processing_notes'] and rows[i].get('quality_assessment')==old[i].get('quality_assessment') and rows[i]['status']==old[i]['status']
        assert rows[i]['scope_assessment']['final_scope_decision']=='passes_both_gates'
    validate_affected_records([rows[i] for i in data['changed_inventory_ids']])
    olddebt={r['id']:r for r in oldq['failures']};debt={r['id']:r for r in q['failures']}
    assert len(olddebt)==1608 and len(debt)==1574
    assert olddebt.keys()-debt.keys()==set(data['debt_resolved_ids']) and not debt.keys()-olddebt.keys() and all(r==olddebt[i] for i,r in debt.items())
    assert all(oldq[k]==q[k] for k in oldq if k not in {'failures','passing_ids','september_13_reconciliation'})
    before={r['id']:r for r in oldq['september_13_reconciliation']};after={r['id']:r for r in q['september_13_reconciliation']}
    assert before.keys()==after.keys() and all(before[i]==after[i] for i in before if i not in data['target_ids'])
    expected={r['id'] for r in before.values() if r['disposition']=='unresolved visible quality finding' and r['prior_status']=='does not meet standalone standard' and ('Bond' in r['title'] or 'Capital Facilities' in r['title'])}
    assert set(data['target_ids'])==expected and len(expected)==32
    assert set(data['master_ids'])=={'src-8c5d2888cc22b991','src-cb8cd727e3ca1fde'} and set(data['changed_inventory_ids'])==expected|set(data['master_ids'])
    for i in expected:
        assert after[i]['prior_status']==before[i]['prior_status'] and after[i]['finding_id']==before[i]['finding_id']
    assert {r['id'] for r in after.values() if r['disposition']=='unresolved visible quality finding'}=={r['id'] for r in before.values() if r['disposition']=='unresolved visible quality finding'}-expected
    assert set(q['passing_ids'])==set(oldq['passing_ids'])|(set(data['changed_inventory_ids'])-{'src-047e8956baad212d'})
    assert hashes==data['page_sha256'] and r2old==r2new and data['added_r2_bytes']==0 and not data['r2_mutation']
def guard_current_delta():
    stage=StageSnapshot('go-capital-quality-remediation');base=stage.stage['baseline_commit'];data=stage.load_json(PREFIX+'implementation.json');assert base==data['baseline_commit']=='940e3032d96f868eed8cff7c3deeaf1c556f50a2'
    def before(p):return json.loads(git('show',base+':'+p).decode('utf-8-sig'))
    hashes={p:hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() for p in data['changed_pages']};current=stage.load_json('project-state/master-inventory.json')
    validate_delta(data,before('project-state/master-inventory.json'),current,before(QUEUE),stage.load_json(QUEUE),hashes,before('project-state/r2-inventory.json'),stage.load_json('project-state/r2-inventory.json'))
    endpoint=stage.end or 'HEAD';changed=set(git('diff',base,endpoint,'--name-only').decode().splitlines())
    if not stage.end:changed.update(git('diff',endpoint,'--name-only').decode().splitlines());changed.update(git('ls-files','--others','--exclude-standard').decode().splitlines())
    assert all(p in ALLOWED or p in data['changed_pages'] or p.startswith(PREFIX) or p.startswith('backups/') for p in changed),'Unrelated repository delta'
    assert {p for p in changed if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'}==set(data['changed_pages'])
    for ext in ('json','md'):assert canonical_bytes(stage.read_bytes(PREFIX+'baseline-remediation.'+ext))==canonical_bytes(git('show',base+':'+QUEUE.removesuffix('.json')+'.'+ext))
    rows={r['id']:r for r in current['candidates']};originals={r['candidate_id']:r for r in before('project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json')['documents']};review=stage.load_json(PREFIX+'review.json')
    assert review['preserved_negative_findings']=={i:originals[i] for i in data['target_ids']};validate_affected_records(review['presentation_records']);assert len(review['presentation_records'])==4
    receipts=stage.load_json(PREFIX+'public-byte-measurements.json');assert {r['id'] for r in receipts}==set(data['changed_inventory_ids']) and len(receipts)==34
    for r in receipts:assert r['verified'] and r['url']==rows[r['id']]['r2_url'] and r['sha256']==rows[r['id']]['checksum_sha256'] and r['size_bytes']==rows[r['id']]['size_bytes']
    assert stage.load_json(PREFIX+'owner-count-direction.json')['owner_reply']=='I have no idea. Add it as a question in the PR and let me look at it.' and data['owner_count_question_pending']
    reg=stage.load_json('project-state/workflow-stage-lifecycle.json');oldreg=before('project-state/workflow-stage-lifecycle.json')
    assert reg['stages'][:-2]==oldreg['stages'][:-1] and reg['stages'][-2]==dict(oldreg['stages'][-1],end_commit=base)
    assert reg['protected_evidence'][:len(oldreg['protected_evidence'])]==oldreg['protected_evidence']
    assert all(s['commit']==base and s['path'].startswith('project-state/discovery/pr196-production-closeout-2026-09-27/') for s in reg['protected_evidence'][len(oldreg['protected_evidence']):])
    oldqueue=before('project-state/discovery/consolidated-human-review-queue.json');newqueue=stage.load_json('project-state/discovery/consolidated-human-review-queue.json')
    assert {k:v for k,v in oldqueue.items() if k!='inventory_sha256'}=={k:v for k,v in newqueue.items() if k!='inventory_sha256'}
    return data
