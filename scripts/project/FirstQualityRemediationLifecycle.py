"""Exact three-family remediation; preserve historical failures and all original bytes."""
import json, hashlib, subprocess
from WorkflowStageLifecycle import ROOT, StageSnapshot, git, digest, canonical_bytes
from PublicationQuality import validate_affected_records

PREFIX='project-state/discovery/quality-remediation-first-2026-09-27/'
QUEUE='project-state/discovery/publication-quality-remediation-2026-09-26.json'

def validate_delta(data, prior, current, old_queue, queue, page_hashes, r2_before, r2_after):
    old={r['id']:r for r in prior['candidates']};rows={r['id']:r for r in current['candidates']}
    assert len(rows)==len(current['candidates'])==len(old)==len(prior['candidates'])
    assert rows.keys()==old.keys()
    assert {i for i in rows if rows[i]!=old[i]}==set(data['changed_inventory_ids'])
    assert {k:v for k,v in current.items() if k!='candidates'}=={k:v for k,v in prior.items() if k!='candidates'}
    assert {i:digest(rows[i]) for i in data['changed_inventory_ids']}==data['expected_row_digests']
    allowed={'publication_quality_decision','publication_relationship','scope_assessment','updated_at','processing_notes','implementation_location','implementation_locations','cross_listing_approved'}
    for i in data['changed_inventory_ids']:
        assert {k for k in rows[i].keys()|old[i].keys() if rows[i].get(k)!=old[i].get(k)}<=allowed
        assert rows[i]['processing_notes'][:-1]==old[i]['processing_notes']
        assert rows[i].get('quality_assessment')==old[i].get('quality_assessment')
    validate_affected_records([rows[i] for i in data['changed_inventory_ids']])
    old_debt={r['id']:r for r in old_queue['failures']};debt={r['id']:r for r in queue['failures']}
    assert len(old_debt)==1638 and len(debt)==1608
    assert old_debt.keys()-debt.keys()==set(data['debt_resolved_ids']) and not debt.keys()-old_debt.keys()
    assert all(r==old_debt[i] for i,r in debt.items())
    assert set(queue['passing_ids'])==set(old_queue['passing_ids'])|set(data['master_ids'])|{i for i in data['target_ids'] if i not in {r['id'] for r in queue['september_13_reconciliation'] if not r['current_visible_pages']}}
    assert all(queue[k]==old_queue[k] for k in old_queue if k not in {'failures','passing_ids','september_13_reconciliation'})
    before={r['id']:r for r in old_queue['september_13_reconciliation']};after={r['id']:r for r in queue['september_13_reconciliation']}
    assert before.keys()==after.keys()
    assert all(before[i]==after[i] for i in before if i not in data['target_ids'])
    assert page_hashes==data['page_sha256']
    assert r2_before==r2_after

def guard_current_delta():
    stage=StageSnapshot('quality-remediation-first');data=stage.load_json(PREFIX+'implementation.json');baseline=data['baseline_commit']
    assert baseline==stage.stage['baseline_commit']
    def before(p):return json.loads(git('show',baseline+':'+p).decode('utf-8-sig'))
    pages={p:hashlib.sha256(canonical_bytes(stage.read_bytes(p))).hexdigest() for p in data['changed_pages']}
    validate_delta(data,before('project-state/master-inventory.json'),stage.load_json('project-state/master-inventory.json'),before(QUEUE),stage.load_json(QUEUE),pages,before('project-state/r2-inventory.json'),stage.load_json('project-state/r2-inventory.json'))
    visible=git('diff',baseline,*([stage.end] if stage.end else []),'--name-only','--','content','layouts','assets','static','hugo.toml').decode().splitlines()
    assert set(visible)==set(data['changed_pages'])
    if not stage.end:assert not git('ls-files','--others','--exclude-standard','--','content','layouts','assets','static','hugo.toml').strip()
    allowed=set(data['changed_pages'])|{'project-state/master-inventory.json',QUEUE,QUEUE.removesuffix('.json')+'.md','project-state/workflow-stage-lifecycle.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/discovery/consolidated-human-review-queue.json','scripts/project/WorkflowStageLifecycle.py','scripts/project/Test-PublicationQuality.py','scripts/project/FirstQualityRemediationLifecycle.py','scripts/project/Test-FirstQualityRemediation.py','scripts/project/Invoke-ProjectValidation.ps1'}
    changed=set(git('diff',baseline,*([stage.end] if stage.end else []),'--name-only').decode().splitlines())
    assert all(p in allowed or p.startswith(PREFIX) for p in changed), 'Unrelated repository delta'
    for suffix in ('json','md'):
        assert canonical_bytes(stage.read_bytes(PREFIX+'baseline-remediation.'+suffix))==canonical_bytes(git('show',baseline+':project-state/discovery/publication-quality-remediation-2026-09-26.'+suffix))
    for p in ['project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json','project-state/discovery/dpm-annual-compilations-visual-qa-2026-09-13.json','project-state/discovery/dpm-annual-compilations-build-2026-09-13.json']:
        assert canonical_bytes(stage.read_bytes(p))==canonical_bytes(git('show',baseline+':'+p))
    rows={r['id']:r for r in stage.load_json('project-state/master-inventory.json')['candidates']}
    review=stage.load_json(PREFIX+'review.json');assert set(review['preserved_negative_findings'])==set(data['target_ids'])
    originals=before('project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json')
    findings={r['candidate_id']:r for r in originals['documents']}
    assert all(review['preserved_negative_findings'][i]==findings[i] for i in data['target_ids'])
    texts=[stage.read_text(p) for p in data['changed_pages']]
    for i in data['target_ids']:
        if 'Executive Committee' in rows[i]['title']:
            assert all(rows[i]['r2_url'] not in t and rows[i]['direct_file_url'] not in t for t in texts)
            master=next(f for f in data['families'] if i in f['component_ids']);assert master['id'] in data['master_ids']
    validate_affected_records(review['presentation_records'])
    receipts=stage.load_json(PREFIX+'public-byte-measurements.json')
    assert {r['id'] for r in receipts}==set(data['changed_inventory_ids']) and len(receipts)==30
    for receipt in receipts:
        row=rows[receipt['id']]
        assert receipt['verified'] and receipt['url']==row['r2_url'] and receipt['sha256']==row['checksum_sha256'] and receipt['size_bytes']==row['size_bytes']
    old_registry=before('project-state/workflow-stage-lifecycle.json');new_registry=stage.load_json('project-state/workflow-stage-lifecycle.json')
    assert new_registry['stages'][:-2]==old_registry['stages'][:-1]
    assert {k:v for k,v in new_registry['stages'][-2].items() if k!='end_commit'}==old_registry['stages'][-1]
    assert new_registry['stages'][-2]['end_commit']==baseline
    assert len(new_registry['protected_evidence'])==len(old_registry['protected_evidence'])
    for old_seal,new_seal in zip(old_registry['protected_evidence'],new_registry['protected_evidence']):
        assert {k:v for k,v in new_seal.items() if k!='live_path'}==old_seal
        if 'live_path' in new_seal:assert old_seal['path'] in {QUEUE,QUEUE.removesuffix('.json')+'.md'} and new_seal['live_path']==PREFIX+'baseline-remediation.'+old_seal['path'].split('.')[-1]
    queue_before=before('project-state/discovery/consolidated-human-review-queue.json');queue_after=stage.load_json('project-state/discovery/consolidated-human-review-queue.json')
    assert {k:v for k,v in queue_before.items() if k!='inventory_sha256'}=={k:v for k,v in queue_after.items() if k!='inventory_sha256'}
    return data
