"""Fast-forward only branch reconciliation and durable final live-ref receipt."""
import importlib.util,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('task_external',Path(__file__).with_name('Invoke-OwnerDecisionsExternal.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert m.git('branch','--show-current')=='chatgpt/planning-snapshot'
assert not m.git('diff','--name-only') and not m.git('diff','--cached','--name-only')
def action(label,*cmd):subprocess.run([sys.executable,'-B','scripts/project/Invoke-OwnerDecisionsExternal.py','--label',label,'--',*cmd],cwd=m.ROOT,check=True)
action('reconcile-refresh-origin','git','fetch','origin')
action('reconcile-planning-fast-forward','git','merge','--ff-only','origin/main')
action('reconcile-local-main-fast-forward','git','fetch','.','origin/main:refs/heads/main')
action('reconcile-remote-planning-fast-forward','git','push','origin','chatgpt/planning-snapshot')
refs={r:m.git('rev-parse',r) for r in ['HEAD','main','chatgpt/planning-snapshot','origin/main','origin/chatgpt/planning-snapshot']}
live={line.split()[1]:line.split()[0] for line in m.git('ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot').splitlines()}
assert len(set(refs.values()))==1 and set(live.values())==set(refs.values())
assert m.git('rev-parse','HEAD:content')==m.load(m.F/'authorization.json')['content_tree']
r=dict(schema_version=1,task=m.TASK,verified_at=m.now(),state='branches_reconciled',refs=refs,live_remote_refs=live,content_tree_sha=m.git('rev-parse','HEAD:content'),tracked_worktree_clean=not bool(m.git('status','--porcelain','--untracked-files=no')))
assert r['tracked_worktree_clean'];m.save(m.RUNTIME/'final-integration.json',r)
print(r)
