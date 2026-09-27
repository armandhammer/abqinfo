"""Deterministic surgical preflight insertion; no original business logic is rewritten."""
import ast
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
tools={}
excluded={'Invoke-ProjectValidation.ps1','Resolve-TaskGovernance.py','TaskGovernance.py','GovernedEntrypoint.py',
          'Assert-TaskGovernance.ps1','Update-Candidate.ps1','Update-CandidatesBatch.py','Remove-R2Object.ps1'}
for path in sorted((ROOT/'scripts/project').iterdir()):
    if path.suffix not in ('.py','.ps1') or path.name in excluded or path.name.startswith('Test-'):
        continue
    name=path.name
    # Enumerate every record-review builder, disposition writer and content/archive workflow.
    selected=(re.match(r'(Apply|Complete|Finalize|Normalize|Reconcile|Update|Import|Set)-',name) or
              (name.startswith(('Build-','build_','New-')) and re.search(r'Research|research|Decision|decisions|Review|review|Compilation|Consolidation|Archive|Inventory|Quality|ParallelVerification',name)) or
              name.startswith('Invoke-') and re.search(r'Archive|Campaign|Coordinator',name) or
              name in ('BackgroundCampaign.py','SecondLargeOrdinaryCampaign.py'))
    if not selected:
        continue
    text=path.read_text(encoding='utf-8-sig')
    operation='family_review'
    if name.startswith(('Apply-','Update-','Import-','Normalize-','Reconcile-','Finalize-')): operation='inventory_disposition'
    if 'Quality' in name: operation='quality_assessment'
    if re.search(r'Content|Hugo|Consolidation',name) and re.search(r'content/|content\\',text): operation='visitor_visible_change'
    if name.startswith('Invoke-') and 'Archive' in name: operation='archive'
    relative=path.relative_to(ROOT).as_posix()
    tools[relative]={'operation_class':operation,
                     'candidate_ids':sorted(set(re.findall(r'\bsrc-[0-9a-f]{16}\b',text))),
                     'pages':sorted(set(re.findall(r'content/[a-zA-Z0-9_./-]+\.md',text))),
                     'check_is_read_only':name=='Build-ConsolidatedHumanReviewQueue.py'}
    if path.suffix=='.py':
        if 'require_tool_governance(__file__)' in text: continue
        tree=ast.parse(text)
        offset=0
        for node in tree.body:
            if isinstance(node,(ast.Import,ast.ImportFrom)) or isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                offset=node.end_lineno
            else: break
        lines=text.splitlines(keepends=True)
        lines.insert(offset,"\nif __name__ == '__main__':\n    from GovernedEntrypoint import require_tool_governance\n    require_tool_governance(__file__)\n\n")
        text=''.join(lines)
    else:
        if 'Assert-TaskGovernance -ToolPath $PSCommandPath' in text: continue
        # All parameter-bearing operational scripts start with CmdletBinding/param.
        match=re.search(r'(?m)^Set-StrictMode|^\$ErrorActionPreference\s*=|^\.[ ]+"\$PSScriptRoot/',text)
        if not match:
            # Parameterless scripts may start directly with assignments.
            match=re.search(r'(?m)^(?!#|\s*$)[^\r\n]+',text)
        assert match,path
        text=text[:match.start()]+'. "$PSScriptRoot/Assert-TaskGovernance.ps1"\nAssert-TaskGovernance -ToolPath $PSCommandPath -Parameters $PSBoundParameters\n\n'+text[match.start():]
    path.write_text(text.replace('\r\n','\n'),encoding='utf-8')
(ROOT/'project-state/governance/entrypoints.json').write_text(json.dumps({'schema_version':1,
    'authority':'policy-durable-task-governance','tools':tools},indent=2)+'\n',encoding='utf-8')
print('Guarded substantive entrypoints:',len(tools))
