"""Keep completed stage audits sealed; independently constrain the publication delta."""
import json
import subprocess
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / 'project-state/discovery/planning-documents-root-hugo-implementation-2026-09-26.json'
BASELINE = '2c5e170e1dda5a4b3ad44dc328f6e3cb1b458063'
_guarded = False

def validate_delta(data, prior, current, changed_paths, page_hashes, r2_before, r2_current):
    """A historical seal is usable only when every current mutation is accounted for."""
    ids=set(data['implemented_inventory_ids'])
    old={r['id']:r for r in prior['candidates']}; rows={r['id']:r for r in current['candidates']}
    assert rows.keys()==old.keys() and {i for i in rows if rows[i]!=old[i]}==ids
    allowed={'status','implementation_location','implementation_locations','description','description_word_count','quality_assessment','validation_status','processing_notes','updated_at'}
    for rid in ids:
        r=rows[rid]
        assert {k for k in r if r[k]!=old[rid].get(k)}<=allowed
        assert r['status']=='implemented' and r['scope_assessment']['final_scope_decision']=='passes_both_gates'
    assert set(changed_paths)==set(data['changed_pages']) and len(changed_paths)==6
    assert page_hashes==data['page_sha256']
    assert r2_before==r2_current

def guard_current_delta():
    global _guarded
    data=implementation()
    if not data or _guarded: return
    def prior(path):
        return json.loads(subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT).decode('utf-8-sig'))
    def current(path): return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
    paths=subprocess.check_output(['git','diff',BASELINE,'--name-only','--','content','layouts','assets','static','hugo.toml'],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','content','layouts','assets','static'],cwd=ROOT,text=True).splitlines()
    assert not untracked
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in data['changed_pages']}
    validate_delta(data,prior('project-state/master-inventory.json'),current('project-state/master-inventory.json'),paths,hashes,prior('project-state/r2-inventory.json'),current('project-state/r2-inventory.json'))
    _guarded=True

def implementation():
    if not ARTIFACT.exists():
        return None
    data = json.loads(ARTIFACT.read_text(encoding='utf-8'))
    assert data['baseline_commit'] == BASELINE
    assert len(data['implemented_inventory_ids']) == len(set(data['implemented_inventory_ids'])) == 12
    return data

def sealed_json(path):
    data = implementation()
    relative = Path(path).resolve().relative_to(ROOT).as_posix()
    if data:
        guard_current_delta()
        return json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + relative], cwd=ROOT).decode('utf-8-sig'))
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
