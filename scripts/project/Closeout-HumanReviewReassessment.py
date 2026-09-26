"""Persist validation/integration closeout without altering inventory decisions."""
import argparse, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
F=ROOT/'project-state/discovery/human-review-reassessment-2026-09-26'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=argparse.ArgumentParser();p.add_argument('--validation',required=True);p.add_argument('--integration');args=p.parse_args()
v=load(ROOT/args.validation);assert v['result']=='passed'
assert hashlib.sha256((ROOT/v['log_artifact']).read_bytes()).hexdigest()==v['log_sha256']
a=load(F/'authorization.json');a['validation_artifact']=args.validation
a['state']='validated_pending_background_integration'
paragraph='Full project validation passed. Background integration/reconciliation is the remaining closeout stage; inspect the reassessment validation and integration receipts before resuming.'
if args.integration:
    receipt=load(ROOT/args.integration)
    assert receipt['state']=='branches_reconciled' and receipt['tracked_worktree_clean']
    assert len(set(receipt['refs'].values()))==1 and set(receipt['live_remote_refs'].values())==set(receipt['refs'].values())
    assert receipt['content_tree_sha']==a['content_tree']
    a['state']='complete_background_reassessment'
    a['integration_artifact']=args.integration
    a['integration_baseline_refs']=receipt['refs']
    paragraph='Full project validation and primary background integration passed; main and planning-snapshot were reconciled locally and on origin. The final metadata handoff uses the durable runtime receipt at `project-state/campaign-runtime/human-review-reassessment-2026-09-26/final-integration.json`; verify its refreshed live refs before starting another task.'
save(F/'authorization.json',a)
cp=load(ROOT/'project-state/checkpoint.json');cp['human_review_reassessment'].update(state=a['state'],validation_artifact=args.validation,integration_artifact=a.get('integration_artifact'));save(ROOT/'project-state/checkpoint.json',cp)
current=ROOT/'project-state/CURRENT.md';s=current.read_text(encoding='utf-8-sig')
old=s[s.index('Review and archive work are durably complete.'):s.index(' Run `Invoke-ProjectValidation.ps1`')]
s=s.replace(old,'Review and archive work are durably complete. '+paragraph)
current.write_text(s,encoding='utf-8')
print(a['state'])
