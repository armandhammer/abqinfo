"""Repository authority, immutable task contracts and executable implementation checks.

No relevance ranking or newest-file precedence: every active registry row is loaded.
Selectors are unions; candidate/family membership expands transitively before matching.
"""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = 'project-state/governance-registry.json'
ACTIVE_TASK = 'project-state/governance/active-task.json'
OPERATIONS = {
    'document_review', 'family_review', 'inventory_disposition', 'quality_assessment',
    'consolidation', 'archive', 'content_implementation', 'content_removal',
    'placement', 'cross_listing', 'visitor_visible_change', 'external_mutation',
    'governance_audit', 'governance_implementation', 'background_integration',
}


class GovernanceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise GovernanceError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path, root=ROOT):
    # Git's Windows checkout conversion must not invalidate an authority artifact.
    return hashlib.sha256((root / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def load(path, root=ROOT):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def write_once(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def population(value):
    required = ('task_id', 'baseline_commit', 'candidate_ids', 'families', 'pages',
                'operation_classes', 'artifact_paths')
    require(all(k in value for k in required), 'Population needs every explicit selector and baseline')
    result = {k: value[k] for k in required}
    require(re.fullmatch(r'[a-zA-Z0-9_.-]+', result['task_id']) is not None, 'Invalid task ID')
    require(re.fullmatch(r'[0-9a-f]{40}', result['baseline_commit']) is not None, 'Invalid baseline commit')
    for key in required[2:]:
        require(isinstance(result[key], list) and all(isinstance(x, str) for x in result[key]),
                'Population selectors must be string lists: ' + key)
        result[key] = sorted(set(result[key]))
    require(set(result['operation_classes']) <= OPERATIONS, 'Unknown operation class')
    require(bool(result['operation_classes']), 'No intended operations')
    require(all(re.fullmatch(r'[a-z][a-z0-9-]+', x) for x in result['candidate_ids']), 'Invalid candidate ID')
    for name in result['pages'] + result['artifact_paths']:
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name,
                'Selectors must be repository-relative POSIX paths')
    result['archive_objects'] = sorted(value.get('archive_objects', []), key=lambda x:x['r2_key'])
    require(len({x['r2_key'] for x in result['archive_objects']})==len(result['archive_objects']), 'Duplicate frozen R2 key')
    for item in result['archive_objects']:
        require(item['candidate_id'] in result['candidate_ids'] and item['r2_key'] and
                re.fullmatch(r'[0-9a-f]{64}',item['sha256']) is not None, 'Incomplete frozen archive object')
    return result


def registry(root=ROOT):
    data = load(REGISTRY, root)
    require(data['schema_version'] == 1, 'Unknown governance schema')
    require(file_hash(data['audit_artifact'], root) == data['audit_sha256'], 'Authority audit changed without registry refresh')
    rows = data['entries']
    ids = {r['governance_id'] for r in rows}
    require(len(ids) == len(rows), 'Duplicate governance ID')
    for row in rows:
        require(row['state'] in ('active', 'superseded'), 'Unknown authority state')
        require(row['category'] in data['categories'], 'Unknown authority category')
        require(row['scope'] and row['binding_requirement'] and row['authority'], 'Incomplete authority')
        require(row['controlling_artifacts'], 'No controlling evidence')
        for artifact in row['controlling_artifacts']:
            require(file_hash(artifact['path'], root) == artifact['sha256'],
                    'Controlling artifact changed: ' + artifact['path'])
        if row['state'] == 'superseded':
            require(row.get('superseded_by') in ids and row.get('supersession_evidence'),
                    'Supersession requires explicit controlling evidence and replacement ID')
    return data


def expanded_members(pop, rows):
    ids, families = set(pop['candidate_ids']), set(pop['families'])
    # Caller cannot bypass a family rule by omitting its family name.
    for row in rows:
        membership = row.get('family_memberships')
        if membership is None:
            membership = {f: row['scope'].get('candidate_ids', []) for f in row['scope'].get('families', [])}
        for family, candidates in membership.items():
            if ids.intersection(candidates):
                families.add(family)
    # An umbrella rule applying to several families does not make them one family.
    return ids, families


def matches(row, pop, members):
    scope = row['scope']
    if scope.get('global'):
        return True
    if 'governance_audit' in pop['operation_classes'] and any(a['path'] in pop['artifact_paths'] for a in row['controlling_artifacts']):
        return True
    ids, families = members
    return (bool(ids.intersection(scope.get('candidate_ids', []))) or
            pop['task_id'] in scope.get('task_ids', []) or
            bool(families.intersection(scope.get('families', []))) or
            bool(set(pop['pages']).intersection(scope.get('pages', []))) or
            bool(set(pop['operation_classes']).intersection(scope.get('operation_classes', []))) or
            bool(set(pop['artifact_paths']).intersection(scope.get('artifact_paths', []))) or
            any(p.startswith(prefix) for p in pop['artifact_paths']
                for prefix in scope.get('artifact_prefixes', [])))


def conflicts(rows):
    facts, result = {}, []
    for row in rows:
        for rule in row.get('constraints', []):
            key = rule['subject'] + ':' + rule['field']
            if key in facts and facts[key][0] != rule['equals']:
                result.append({'subject_field': key, 'governance_ids': [facts[key][1], row['governance_id']]})
            facts[key] = (rule['equals'], row['governance_id'])
    return result


def resolve(pop, data, registry_hash):
    pop = population(pop)
    rows = [r for r in data['entries'] if r['state'] == 'active']
    members = expanded_members(pop, rows)
    applicable = [r for r in rows if matches(r, pop, members)]
    applicable.sort(key=lambda x: x['governance_id'])
    return {
        'schema_version': 1, 'task_population': pop, 'population_sha256': digest(pop),
        'registry_sha256': registry_hash, 'active_registry_ids_sha256': digest(sorted(r['governance_id'] for r in rows)),
        'governance_ids': [r['governance_id'] for r in applicable],
        'controlling_artifacts': sorted({(a['path'], a['sha256']) for r in applicable for a in r['controlling_artifacts']}),
        'resolved_rules': applicable,
        'required_actions': [{'governance_id': r['governance_id'], 'action': a}
                             for r in applicable for a in r.get('required_actions', [])],
        'prohibited_actions': [{'governance_id': r['governance_id'], 'action': a}
                               for r in applicable for a in r.get('prohibited_actions', [])],
        'settled_decisions': [{'governance_id': r['governance_id'], **s}
                              for r in applicable for s in r.get('settled_decisions', [])],
        'unresolved_gates': [{'governance_id': r['governance_id'], **g}
                             for r in applicable for g in r.get('unresolved_gates', [])
                             if not g.get('scope') or matches({'scope':g['scope'],'controlling_artifacts':[]},pop,members)],
        'conflicts': conflicts(applicable),
        'record_rules': {i: [r['governance_id'] for r in applicable
                            if matches(r, {**pop, 'candidate_ids': [i]}, expanded_members({**pop, 'candidate_ids': [i]}, rows))]
                         for i in pop['candidate_ids']},
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_commit': pop['baseline_commit'],
    }


def freshness(contract, pop, data, registry_hash):
    expected = resolve(pop, data, registry_hash)
    for key in expected:
        if key == 'timestamp_utc':
            continue
        require(canonical(contract.get(key)) == canonical(expected[key]), 'Governance contract stale/incomplete: ' + key)
    return expected


def validate_plan(contract, plan, phase='review'):
    require(not contract['conflicts'], 'Conflicting active rules require explicit supersession')
    require(set(plan.get('respected_governance_ids', [])) == set(contract['governance_ids']),
            'Implementation must account for every applicable governance ID')
    require(plan.get('population_sha256') == contract['population_sha256'], 'Plan population changed')
    declarations = plan.get('subjects', {})
    for row in contract['resolved_rules']:
        for rule in row.get('constraints', []):
            if not set(plan.get('actions', [])) & set(rule.get('operation_classes', OPERATIONS - {'governance_audit','governance_implementation','background_integration'})):
                continue
            require(declarations.get(rule['subject'], {}).get(rule['field']) == rule['equals'],
                    'Binding implementation constraint violated: ' + row['governance_id'] + ':' + rule['field'])
        for action in plan.get('actions', []):
            require(action not in row.get('prohibited_operation_classes', []),
                    'Prohibited operation: ' + row['governance_id'] + ':' + action)
    require(set(plan.get('actions', [])) <= set(contract['task_population']['operation_classes']),
            'Operation outside frozen population')
    settled = {s['question_id'] for s in contract['settled_decisions']}
    for event in plan.get('events', []):
        require(event['operation'] in contract['task_population']['operation_classes'], 'Activity outside task operations')
        require(set(event.get('candidate_ids', [])) <= set(contract['task_population']['candidate_ids']), 'Activity population changed')
        require(set(event.get('governance_ids', [])) <= set(contract['governance_ids']), 'Activity cites unresolved authority')
        if event.get('question_id') in settled:
            require(event.get('action') not in ('research','decide','research_unsettled','decide_unsettled','re_research', 're_decide', 'request_human_review'),
                    'Settled decision cannot be reopened or sent for human review: ' + event['question_id'])
        for candidate in event.get('candidate_ids', []):
            require(event.get('use_contract_record_rules') is True or
                    set(contract['record_rules'][candidate]) <= set(event.get('governance_ids',[])),
                    'Activity omitted applicable record governance: '+candidate)
    if phase == 'mutation':
        for gate in contract['unresolved_gates']:
            condition=gate.get('when_subject_fact')
            if condition and declarations.get(condition['subject'],{}).get(condition['field'])!=condition['equals']:
                continue
            if set(plan.get('actions', [])) & set(gate.get('blocks_operations', [])):
                require(gate['gate_id'] in plan.get('satisfied_gates', {}), 'Unresolved gate: ' + gate['gate_id'])
                evidence = plan['satisfied_gates'][gate['gate_id']]
                require(evidence.get('path') and evidence.get('sha256') == file_hash(evidence['path']), 'Invalid gate receipt')
                releasing=[r for r in contract['resolved_rules'] if gate['gate_id'] in r.get('releases_gates',[]) and
                           'owner' in r['authority'].lower() and any(a['path']==evidence['path'] and a['sha256']==evidence['sha256'] for a in r['controlling_artifacts'])]
                require(releasing, 'Gate release requires registered explicit authority; a self-attestation is insufficient')
    return True


def check_registry_transition(before, after, proposals):
    old = {r['governance_id']: r for r in before['entries']}
    new = {r['governance_id']: r for r in after['entries']}
    for gid, row in old.items():
        if row['state'] != 'active':
            require(gid in new and canonical(row) == canonical(new[gid]), 'Historical supersession evidence changed')
            continue
        require(gid in new, 'Active decision silently removed: ' + gid)
        if canonical(row) != canonical(new[gid]):
            # Artifact hash refresh alone does not replace an authority requirement.
            a = {k: v for k, v in row.items() if k != 'controlling_artifacts'}
            b = {k: v for k, v in new[gid].items() if k != 'controlling_artifacts'}
            if canonical(a) == canonical(b):
                previous={a['path']:a for a in row['controlling_artifacts']}
                changed=[a for a in new[gid]['controlling_artifacts'] if a['path'] in previous and a['sha256']!=previous[a['path']]['sha256']]
                # Implementation refreshes invalidate preflight but cannot replace a decision.
                decision_changed=any(a.get('binding_pointers')!=['/implementation'] for a in changed)
                if not decision_changed:
                    continue
            proposal = proposals.get(gid, {})
            require(new[gid]['state'] == 'superseded' and proposal.get('authorized') is True,
                    'Silent supersession: ' + gid)
            require(all(proposal.get(k) for k in ('existing_governance_id', 'current_decision',
                    'controlling_evidence', 'new_evidence', 'proposed_replacement', 'consequences', 'authorization_artifact')),
                    'Incomplete supersession proposal: ' + gid)
            require(proposal['current_decision'] == row['binding_requirement'], 'Supersession changes the current decision')
            require(proposal['authorization_artifact'] in [a['path'] for r in after['entries']
                    for a in r['controlling_artifacts']], 'Supersession authorization unregistered')


def binding_artifact(path, text):
    """Detect project instructions, excluding source documents, generated contracts and logs.

    All newly authored governance-bearing JSON/Markdown must be classified. This is a
    deterministic backstop, not semantic proof about unrecorded conversational work.
    """
    if Path(path).suffix.lower() not in ('.json', '.md', '.txt', '.yaml', '.yml', '.toml'):
        return False
    if path.startswith(('content/', 'research/')):
        return False
    return bool(re.search(r'governance_metadata|"(?:binding_requirement|owner_decision|family_decision|decision|disposition|publication_form|publication_gate|safeguards|constraints|visible_form|packet_policy)"|\b(?:must|never|shall|do not|not authorized|supersedes)\b', text, re.I))


def check_unregistered(data, paths, root=ROOT):
    registered = {a['path'] for r in data['entries'] for a in r['controlling_artifacts']} | {data['audit_artifact'],REGISTRY}
    audited = {r['path']: r for r in load(data['audit_artifact'], root)['artifacts']}
    for path in paths:
        if path in registered or not (root / path).is_file():
            continue
        text = (root / path).read_text(encoding='utf-8-sig', errors='replace')
        if path.endswith('.json'):
            try:
                value = json.loads(text)
            except ValueError:
                value = None
            # Resolver-produced rule snapshots are derived evidence, never new authority.
            if isinstance(value, dict) and 'resolved_rules' in value:
                audit = audited.get(path)
                if audit and audit['sha256'] == file_hash(path, root) and audit['classification'] == 'historical evidence only / non-binding':
                    continue
                expected = resolve(value.get('task_population', {}), data, file_hash(REGISTRY, root))
                require(set(value) == set(expected), 'Unrecognized instruction added to derived contract')
                freshness(value, value['task_population'], data, file_hash(REGISTRY, root))
                continue
            if isinstance(value, dict) and value.get('artifact_type')=='task_implementation_plan':
                # A completed task imported from another branch is immutable
                # historical evidence. Its contract may predate this registry;
                # only an exact audited copy may bypass current freshness.
                audit = audited.get(path)
                if audit and audit['sha256'] == file_hash(path, root) and audit['classification'] == 'historical evidence only / non-binding':
                    continue
                allowed={'artifact_type','contract','contract_sha256','population_sha256','respected_governance_ids',
                         'subjects','actions','events','satisfied_gates','completion_evidence','status'}
                require(set(value)<=allowed,'Implementation plan contains unregistered instruction fields')
                require(file_hash(value['contract'],root)==value['contract_sha256'],'Implementation plan contract changed')
                contract=load(value['contract'],root)
                freshness(contract,contract['task_population'],data,file_hash(REGISTRY,root))
                fields={}
                for row in contract['resolved_rules']:
                    for rule in row.get('constraints',[]):fields.setdefault(rule['subject'],set()).add(rule['field'])
                require(all(subject in fields and set(facts)<=fields[subject] for subject,facts in value.get('subjects',{}).items()),
                        'Implementation plan introduces an unregistered architecture rule')
                validate_plan(contract,value)
                continue
            if isinstance(value,dict) and value.get('artifact_type')=='governance_supersession_proposal':
                require(set(value)<={'artifact_type','proposal_state','existing_governance_id','current_decision',
                                    'controlling_evidence','new_evidence','proposed_replacement','consequences'},
                        'Proposal contains unregistered active authority fields')
                require(value.get('proposal_state')=='pending_owner_authorization','A proposal is not active authority')
                row=next((r for r in data['entries'] if r['governance_id']==value.get('existing_governance_id') and r['state']=='active'),None)
                require(row and value.get('current_decision')==row['binding_requirement'],'Proposal misstates controlling decision')
                require(all(value.get(k) for k in ('controlling_evidence','new_evidence','proposed_replacement','consequences')),'Incomplete supersession proposal')
                require(value['controlling_evidence']==row['controlling_artifacts'],'Proposal evidence differs from active authority')
                continue
        if not binding_artifact(path, text):
            continue
        audit = audited.get(path)
        require(audit and audit['sha256'] == file_hash(path, root) and
                audit['classification'] == 'historical evidence only / non-binding',
                'New/changed binding instruction is unregistered: ' + path)


def changed_paths(baseline):
    tracked = git('diff', '--name-only', baseline).splitlines()
    untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
    return sorted(set(tracked + untracked) - {'backups/'})


def task_lifecycle(task,phase,operation):
    require(task.get('state','in_progress') in ('in_progress','complete'),'Unknown task contract lifecycle state')
    require(task.get('state')!='complete' or (phase=='final' and operation is None),
            'Completed task contract cannot authorize another substantive task; freeze and resolve a new task')


def actual_presentations(contract,reader,changed_pages):
    """Check output bytes, not just a plan's assertion that a master was implemented."""
    capital='content/city-data/capital-spending.md'
    if capital not in changed_pages:
        return
    selected=set(contract['task_population']['candidate_ids'])
    declared=set(contract['task_population']['families'])
    page=reader(capital)
    for row in contract['resolved_rules']:
        families=row.get('family_memberships',{})
        affected=any(selected.intersection(ids) or family in declared for family,ids in families.items())
        if affected:
            for url in row.get('expected_master_archives',[]):
                require(url in page,'Actual page violates decided master-PDF architecture: '+row['governance_id']+': '+url)
            require(not any(url in page for url in row.get('capital_component_links_to_replace',[])),
                    'Actual page retains component entries forbidden by the decided master architecture: '+row['governance_id'])
            for topical,urls in row.get('topical_original_archives',{}).items():
                if topical in changed_pages:
                    require(all(url in reader(topical) for url in urls),'Topical originals redirected/removed contrary to active architecture: '+row['governance_id']+': '+topical)
        if selected.intersection(row['scope'].get('candidate_ids',[])):
            require(all(url in page for url in row.get('retained_original_archives',[])),
                    'Independent instrument evidence removed contrary to active architecture: '+row['governance_id'])


def task_supersession_proposals(task, data):
    path = task.get('supersession_proposals_path')
    if not path:
        return task.get('supersession_proposals', {})
    require(any(a['path'] == path and a['sha256'] == file_hash(path)
                for r in data['entries'] if r['state'] == 'active'
                for a in r['controlling_artifacts']), 'Supersession proposal receipt is unregistered')
    return load(path)['proposals']


def active_check(phase='final', operation=None, candidate_ids=(), pages=(), r2_key=None, source_sha256=None):
    require((ROOT / ACTIVE_TASK).exists(), 'No active task governance contract')
    task = load(ACTIVE_TASK)
    task_lifecycle(task,phase,operation)
    data = registry()
    contract = load(task['contract'])
    pop = load(task['population'])
    require(file_hash(task['contract']) == task['contract_sha256'], 'Immutable contract modified')
    freshness(contract, pop, data, file_hash(REGISTRY))
    plan = load(task['implementation'])
    validate_plan(contract, plan, 'review')
    if phase=='final':
        evidence=plan.get('completion_evidence',{})
        require(set(evidence)==set(contract['governance_ids']), 'Final implementation lacks complete governance accounting')
        for receipts in evidence.values():
            require(receipts and all(file_hash(r['path'])==r['sha256'] for r in receipts), 'Completion evidence missing/changed')
        if set(plan.get('actions',[])) & {'document_review','family_review','quality_assessment','consolidation'}:
            covered={i for e in plan.get('events',[]) for i in e.get('candidate_ids',[])}
            require(set(pop['candidate_ids'])<=covered,'Final review omits frozen records')
    if operation:
        require(operation in contract['task_population']['operation_classes'], 'Mutation operation outside task contract')
        require(set(candidate_ids) <= set(pop['candidate_ids']), 'Mutation record outside frozen population')
        require(set(pages) <= set(pop['pages']), 'Mutation page outside frozen population')
    if phase == 'mutation':
        validate_plan(contract, {**plan,'actions':[operation] if operation else plan.get('actions',[])}, 'mutation')
    if r2_key:
        require(any(x['r2_key']==r2_key and x['sha256']==source_sha256 for x in contract['task_population']['archive_objects']),
                'R2 object/bytes outside frozen task population')
    changes = changed_paths(pop['baseline_commit'])
    check_unregistered(data, changes)
    if phase=='final':
        actual_presentations(contract,lambda p:(ROOT/p).read_text(encoding='utf-8-sig'),changes)
    for path in changes:
        if path.startswith(('content/', 'layouts/', 'assets/', 'static/')) or path == 'hugo.toml':
            require(path in pop['pages'], 'Changed visitor-visible path outside frozen contract: ' + path)
        elif not path.startswith('backups/'):
            require(path in pop['artifact_paths'],
                    'Changed artifact outside frozen contract: ' + path)
    # Changing inventory directly cannot bypass Update-Candidate's entry gate.
    if 'project-state/master-inventory.json' in changes:
        require('inventory_disposition' in pop['operation_classes'], 'Inventory change not authorized by task operations')
        before = json.loads(git('show', pop['baseline_commit'] + ':project-state/master-inventory.json'))
        after = load('project-state/master-inventory.json')
        def records(d):
            return {r['id']: r for r in d['candidates']}
        a, b = records(before), records(after)
        delta = {i for i in set(a) | set(b) if canonical(a.get(i)) != canonical(b.get(i))}
        require(delta <= set(pop['candidate_ids']), 'Inventory delta outside frozen contract')
    baseline_registry = subprocess.run(['git', 'show', 'HEAD:' + REGISTRY], cwd=ROOT,
                                       capture_output=True)
    if baseline_registry.returncode == 0:
        proposals = task_supersession_proposals(task, data)
        check_registry_transition(json.loads(baseline_registry.stdout), data, proposals)
    else:
        require(pop['task_id']=='governance-bootstrap-2026-09-27' and
                pop['baseline_commit']=='940e3032d96f868eed8cff7c3deeaf1c556f50a2',
                'No committed authority baseline; only the exact owner-invoked bootstrap is permitted')
    return {'task_id': pop['task_id'], 'phase': phase, 'applicable_rules': len(contract['governance_ids']),
            'population_sha256': contract['population_sha256'], 'changed_paths': changes}
