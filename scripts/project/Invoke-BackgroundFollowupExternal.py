"""Journal the owner's explicitly authorized background Git/GitHub integration."""
import argparse, json, msvcrt, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TASK = 'background-followup-2026-09-26'
F = ROOT / 'project-state/discovery' / TASK
RUNTIME = ROOT / 'project-state/campaign-runtime' / TASK
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def now(): return datetime.now(timezone.utc).isoformat()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command
    if cmd and cmd[0]=='--':cmd=cmd[1:]
    assert cmd and cmd[0] in ['git','gh']
    assert not any(x in cmd for x in ['--force','--force-with-lease','reset','clean','delete','--admin'])
    with (ROOT/'tmp/background-followup-writer.lock').open('a+b') as lock:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        authority=load(F/'authorization.json')
        assert 'background integration and branch reconciliation' in authority['task']
        assert not git('diff',authority['baseline_commit'],'--name-only','--','content')
        assert git('rev-parse','HEAD:content')==authority['content_tree']
        assert all(p.startswith(('project-state/','scripts/project/')) for p in git('diff',authority['baseline_commit'],'--name-only').splitlines()), 'Task integration includes an unauthorized or visitor-visible path'
        path=RUNTIME/'external-action-journal.json'
        journal=load(path) if path.exists() else dict(schema_version=1,task=TASK,authority_artifact=(F/'authorization.json').relative_to(ROOT).as_posix(),actions=[])
        entry=dict(label=a.label,command=cmd,started_at=now(),state='intent_saved_before_external_mutation');journal['actions'].append(entry);save(path,journal)
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        entry.update(completed_at=now(),state='completed' if result.returncode==0 else 'failed_requires_reconciliation',exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr);save(path,journal)
        print(result.stdout);print(result.stderr,file=sys.stderr);return result.returncode
if __name__=='__main__':sys.exit(main())
