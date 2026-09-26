"""Persist validated/integrated task state using hashed validation and live-ref receipts."""
import argparse,hashlib
from BackgroundFollowup import ROOT,F,load,save
p=argparse.ArgumentParser();p.add_argument('--validation',required=True);p.add_argument('--integration');a=p.parse_args()
v=load(ROOT/a.validation);assert v['result']=='passed'
assert hashlib.sha256((ROOT/v['log_artifact']).read_bytes()).hexdigest()==v['log_sha256']
auth=load(F/'authorization.json');summary=load(F/'summary.json');cp=load(ROOT/'project-state/checkpoint.json')
state='validated_pending_background_integration'
paragraph='Full project validation passed. Authorized background-only integration and branch reconciliation remain pending.'
if a.integration:
 r=load(ROOT/a.integration);assert r['state']=='branches_reconciled' and r['tracked_worktree_clean']
 assert len(set(r['refs'].values()))==1 and set(r['live_remote_refs'].values())==set(r['refs'].values())
 assert r['content_tree_sha']==auth['content_tree']
 state='complete_background_followup';auth['integration_artifact']=a.integration;auth['primary_integration_refs']=r['refs'];save(F/'integration.json',r)
 paragraph='Full project validation and primary background-only integration passed. Main and planning-snapshot were reconciled locally and on origin. The final metadata integration receipt is `project-state/campaign-runtime/background-followup-2026-09-26/final-integration.json`; verify its live refs before another task.'
auth.update(state=state,validation_artifact=a.validation);summary.update(state=state,validation_artifact=a.validation);cp['background_followup'].update(state=state,validation_artifact=a.validation,integration_artifact=auth.get('integration_artifact'))
save(F/'authorization.json',auth);save(F/'summary.json',summary);save(ROOT/'project-state/checkpoint.json',cp)
current=ROOT/'project-state/CURRENT.md';s=current.read_text(encoding='utf-8');old='Review/archive stages are complete; full validation and authorized background integration/reconciliation remain pending.'
old2='Full project validation passed. Authorized background-only integration and branch reconciliation remain pending.'
assert old in s or old2 in s
s=s.replace(old,paragraph).replace(old2,paragraph);current.write_text(s,encoding='utf-8')
print(state)
