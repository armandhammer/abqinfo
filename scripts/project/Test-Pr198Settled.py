"""Actual-record and output-form regressions for the settled PR198 architecture."""
import copy
import importlib.util
import TaskGovernance as G
from Pr198SettledLifecycle import guard_current_delta
from PublicationQuality import validate_affected_records

visible=guard_current_delta()
support=G.load('project-state/governance/pr198-support-2026-09-27/support-records.json')
assert len(support['review_boundary_ids'])==32
assert list(map(len,support['master_components'].values()))==[24,21,46]
assert 'src-7567c5f27fceba0a' not in sum(support['master_components'].values(),[])
rows={r['id']:r for r in G.load('project-state/master-inventory.json')['candidates']}
validate_affected_records([rows[i] for i in support['support_ids']])
task=G.load(G.ACTIVE_TASK);contract=G.load(task['contract'])
if visible:
    validate_affected_records([rows[i] for i in support['review_boundary_ids']])
    reader=lambda p:(G.ROOT/p).read_text(encoding='utf-8-sig')
    G.actual_presentations(contract,reader,visible)
    capital=reader('content/city-data/capital-spending.md')
    for v in G.load('project-state/governance/pr198-archive-authorized-2026-09-27/public-verification.json'):
        assert capital.count(v['url'])==1
        broken=lambda p,url=v['url']:reader(p).replace(url,'https://example.invalid/summary')
        try:G.actual_presentations(contract,broken,visible)
        except G.GovernanceError:pass
        else:raise AssertionError('Webpage-only substitution escaped '+v['r2_key'])
    owner=rows['src-7567c5f27fceba0a']
    assert '- ['+owner['title']+' (Archived PDF)]('+owner['r2_url']+')' in capital
    assert owner['publication_quality_decision']['assessment']['publication_form']=='standalone'
    assert any('owner-keep' in e for e in owner['publication_quality_decision']['evidence'])
    for rid in ['src-b049c4df2812749b','src-768a6855fcfaf443','src-a58b458f5d0f5284','src-040d6e306c1c448c','src-047e8956baad212d']:
        assert rows[rid]['r2_url'] in capital
spec=importlib.util.spec_from_file_location('contract_bytes',G.ROOT/'project-state/governance/pr198-resume-2026-09-27/test_contract_bytes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.main()
print('PASS: exact32 review boundary; 24/21/46 complete master components; independent instruments; unchanged original evidence; actual quality; empty/malformed fail closed; master/output-form checks.')
