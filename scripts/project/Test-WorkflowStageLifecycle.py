"""Normal-suite checks for sealed history, continuous coverage and active mutations."""
import copy
import importlib
import subprocess
from WorkflowStageLifecycle import ROOT, registry, validate_registry, validate_evidence, validate_evidence_bytes
import hashlib
from unittest.mock import patch
from types import SimpleNamespace

data=registry();active=validate_registry(data)
suite=(ROOT/'scripts/project/Invoke-ProjectValidation.ps1').read_text(encoding='utf-8')
for stage in data['stages']+data.get('completed_audits',[]):
    for script in stage['regression_scripts']:
        assert (ROOT/script).exists() and script.split('/')[-1] in suite, 'Stage regression missing from normal suite'
    if stage.get('baseline_commit') and stage.get('end_commit'):
        result=subprocess.run(['git','merge-base','--is-ancestor',stage['baseline_commit'],stage['end_commit']],cwd=ROOT)
        assert result.returncode==0, 'Invalid historical stage interval'
validate_evidence(data)
guard=active['exact_delta_guard'];getattr(importlib.import_module(guard['module']),guard['function'])()
for kind in ('gap','missing_guard','multiple_active'):
    bad=copy.deepcopy(data)
    if kind=='gap': bad['stages'][0]['end_commit']='0'*40
    elif kind=='missing_guard': bad['stages'][-1].pop('exact_delta_guard')
    else: bad['stages'][0].pop('end_commit')
    try: validate_registry(bad)
    except (AssertionError,KeyError): pass
    else: raise AssertionError('Lifecycle registry accepted '+kind)
for old,live in [(b'original',b'changed'),(b'changed',b'changed')]:
    try: validate_evidence_bytes(hashlib.sha256(b'original').hexdigest(),old,live)
    except AssertionError: pass
    else: raise AssertionError('Historical evidence corruption escaped')

# The reusable interval delegates to the full current governance check and
# rejects baselines outside its history; it is not an empty lifecycle guard.
from WorkflowStageLifecycle import guard_governed_tasks, StageSnapshot
import TaskGovernance as G
task={'population':'fixture-population'}
pop={'baseline_commit':'a'*40}
with patch('WorkflowStageLifecycle.StageSnapshot',return_value=SimpleNamespace(stage={'baseline_commit':'b'*40})), \
     patch.object(G,'load',side_effect=[task,pop]), \
     patch('WorkflowStageLifecycle.subprocess.run',return_value=SimpleNamespace(returncode=0)), \
     patch.object(G,'active_check') as check:
    guard_governed_tasks()
    check.assert_called_once_with('final')
for results in ([1],[0,1]):
    with patch('WorkflowStageLifecycle.StageSnapshot',return_value=SimpleNamespace(stage={'baseline_commit':'b'*40})), \
         patch.object(G,'load',side_effect=[task,pop]), \
         patch('WorkflowStageLifecycle.subprocess.run',side_effect=[SimpleNamespace(returncode=x) for x in results]), \
         patch.object(G,'active_check') as check:
        try: guard_governed_tasks()
        except AssertionError: pass
        else: raise AssertionError('Invalid generic interval baseline accepted')
        check.assert_not_called()

# The historical closeout extension admits only its exact additional artifact,
# not a widened candidate population or arbitrary paths.
import LeadCoalHistoricalPublication as publication
read_snapshot=StageSnapshot.load_json
for field,extra in [('candidate_ids','src-unrelated'),('artifact_paths','unrelated.txt')]:
    def corrupt_snapshot(self,path,field=field,extra=extra):
        value=read_snapshot(self,path)
        if path.endswith('/postmerge-population.json'):
            value[field]=value[field]+[extra]
        return value
    with patch.object(StageSnapshot,'load_json',corrupt_snapshot):
        try: publication.guard()
        except AssertionError: pass
        else: raise AssertionError('Historical closeout scope expansion accepted')
print(f'PASS: {len(data["stages"])} contiguous stage intervals; {len(data["protected_evidence"])} unchanged historical evidence files; all regressions in normal suite; active exact-delta guard and negative coverage fixtures passed.')
