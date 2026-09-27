"""Persist validation and verified integration without inventing completion."""
import argparse,gzip
from OwnerDecisions import *
p=argparse.ArgumentParser();p.add_argument('--validation',required=True);p.add_argument('--integration');o=p.parse_args();v=load(ROOT/o.validation);assert v['result']=='passed';assert hashlib.sha256((ROOT/v['log_artifact']).read_bytes()).hexdigest()==v['log_sha256'];assert hashlib.sha256(gzip.decompress((ROOT/v['log_artifact']).read_bytes())).hexdigest()==v['uncompressed_log_sha256']
a=load(F/'authorization.json');s=load(F/'summary.json');cp=load(ROOT/'project-state/checkpoint.json');state='validated_pending_background_integration';text='Full project validation passed; background-only integration and branch reconciliation remain pending.'
if o.integration:
 r=load(ROOT/o.integration);assert r['state']=='branches_reconciled' and r['tracked_worktree_clean'] and len(set(r['refs'].values()))==1 and set(r['live_remote_refs'].values())==set(r['refs'].values()) and r['content_tree_sha']==a['content_tree'];save(F/'integration.json',r);state='complete_owner_decisions';text='Full project validation and primary background-only integration passed. Local main and planning-snapshot were reconciled with both live origin refs. Final metadata integration receipt: `project-state/campaign-runtime/owner-decisions-2026-09-26/final-integration.json`; verify its live refs before new work.'
for d in [a,s,cp['owner_decisions']]:d.update(state=state,validation_artifact=o.validation)
if o.integration:a['integration_artifact']=o.integration;s['integration_artifact']=o.integration;cp['owner_decisions']['integration_artifact']=o.integration
save(F/'authorization.json',a);save(F/'summary.json',s);save(ROOT/'project-state/checkpoint.json',cp)
p=ROOT/'project-state/CURRENT.md';t=p.read_text(encoding='utf-8');t=t.replace('Full validation and background-only integration/reconciliation remain pending.',text).replace('Full project validation passed; background-only integration and branch reconciliation remain pending.',text);p.write_text(t,encoding='utf-8');print(state)
