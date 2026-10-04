"""Mechanical source-evidence preservation closeout; no inventory research."""
import hashlib, subprocess, sys
import SourceHoldResolution as S
from WorkflowStageLifecycle import canonical_bytes, git

TASK='source-hold-resolution-evidence-closeout-2026-10-04'
P='project-state/governance/'+TASK+'/'
BASE='1d7805406b37d1ae4d15192cd9bbd6b7d6652ea2'
ALLOWED={S.P+'.gitattributes','scripts/project/SourceHoldEvidenceCloseout.py',
         'scripts/project/SourceHoldResolution.py','project-state/CURRENT.md',
         S.G.REGISTRY,S.G.ACTIVE_TASK,S.G.registry()['audit_artifact']}

def refresh():
    old=list((S.G.ROOT/P).glob('contract-v*.json'))
    S.audit([p.relative_to(S.G.ROOT).as_posix() for p in old])
    n=max(int(p.stem.split('-v')[1]) for p in old)+1
    path=P+f'contract-v{n}.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve',
                    '--population',P+'population.json','--output',path],check=True,stdout=subprocess.DEVNULL)
    c=S.G.load(path);assert not c['conflicts'] and not c['unresolved_gates']
    plan=S.G.load(P+'implementation.json')
    plan.update(contract=path,contract_sha256=S.G.file_hash(path),
                population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'])
    for e in plan['events']:e['governance_ids']=c['governance_ids']
    plan['completion_evidence']={gid:[dict(path=P+'receipt.json',sha256=S.G.file_hash(P+'receipt.json'))] for gid in c['governance_ids']}
    S.save(P+'implementation.json',plan)
    S.save(S.G.ACTIVE_TASK,dict(population=P+'population.json',contract=path,
                              contract_sha256=S.G.file_hash(path),implementation=P+'implementation.json',state='in_progress'))
    print(path,'complete registry resolved; no conflicts or gates')

def guard():
    population=S.G.load(P+'population.json');assert population['candidate_ids']==S.IDS
    changes=set(S.G.changed_paths(BASE))
    assert all(p in ALLOWED or p.startswith(P) for p in changes),changes-ALLOWED
    for path in ['project-state/master-inventory.json','project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert canonical_bytes((S.G.ROOT/path).read_bytes())==canonical_bytes(git('show',BASE+':'+path)),path
    # Every original research finding, receipt, contract and source witness stays sealed.
    originals=git('ls-tree','-r','--name-only',BASE,'--',S.P).decode().splitlines()
    for path in originals:
        assert canonical_bytes((S.G.ROOT/path).read_bytes())==canonical_bytes(git('show',BASE+':'+path)),path
    assert not git('diff',S.BASE,'--name-only','--','content','layouts','assets','static','hugo.toml').strip()
    assert not git('ls-files','--others','--exclude-standard','--','content','layouts','assets','static').strip()
    result=subprocess.run(['git','diff','--check',S.BASE],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    print('Evidence closeout: full original-baseline diff check passed; exact research/inventory/R2/visible bytes preserved.')

if __name__=='__main__':
    {'refresh':refresh,'guard':guard}[sys.argv[1] if len(sys.argv)>1 else 'guard']()
