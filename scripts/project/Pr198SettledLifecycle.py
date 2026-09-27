"""Guard the authorized PR198 delta while preserving sealed prior stages."""
import json
from pathlib import Path
import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, git

SUPPORT='project-state/governance/pr198-support-2026-09-27/receipt.json'
IMPLEMENTATION='project-state/governance/pr198-implementation-authorized-2026-09-27/receipt.json'

def guard_current_delta():
    stage=StageSnapshot('pr198-settled-implementation')
    support=G.load(SUPPORT)
    selected=set(G.load('project-state/governance/pr198/population.json')['candidate_ids'])
    permitted=selected|set(support['changed_inventory_ids'])
    prior=json.loads(git('show',stage.stage['baseline_commit']+':project-state/master-inventory.json'))
    current=G.load('project-state/master-inventory.json')
    a={r['id']:r for r in prior['candidates']};b={r['id']:r for r in current['candidates']}
    delta={i for i in a.keys()|b.keys() if a.get(i)!=b.get(i)}
    assert delta<=permitted and not a.keys()-b.keys(), 'Unfrozen inventory delta'
    immutable={'source_url','direct_file_url','r2_url','r2_key','size_bytes','checksum_sha256','quality_assessment','status','provenance_status','parent_url','referring_urls','discovery_path'}
    for i in delta & a.keys():
        assert all(a[i].get(k)==b[i].get(k) for k in immutable), 'Original evidence changed: '+i
    pages=set(G.load('project-state/governance/pr198-remote-resume-2026-09-27/population.json')['pages'])
    paths=G.changed_paths(stage.stage['baseline_commit'])
    visible={p for p in paths if p.startswith(('content/','layouts/','assets/','static/')) or p=='hugo.toml'}
    assert visible<=pages, 'Visitor-visible delta outside six frozen pages'
    allowed={'project-state/master-inventory.json','project-state/r2-inventory.json','project-state/checkpoint.json','project-state/CURRENT.md','project-state/workflow-stage-lifecycle.json','project-state/governance-registry.json','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/publication-quality-remediation-2026-09-26.json','project-state/discovery/publication-quality-remediation-2026-09-26.md','scripts/project/Pr198SettledLifecycle.py','scripts/project/Test-Pr198Settled.py','scripts/project/Invoke-ProjectValidation.ps1'}
    assert all(p in allowed or p in pages or p.startswith(('project-state/governance/','project-state/discovery/go-capital-quality-remediation-2026-09-27/','backups/')) for p in paths), 'Unrelated implementation delta'
    if Path(IMPLEMENTATION).is_file():
        receipt=G.load(IMPLEMENTATION)
        assert {p:G.file_hash(p) for p in receipt['changed_pages']}==receipt['page_sha256']
        assert {i:G.digest(b[i]) for i in receipt['changed_inventory_ids']}==receipt['row_digests']
    return visible
