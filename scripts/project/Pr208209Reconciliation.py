"""Separate governed PR208 production closeout and PR209 background reconciliation."""
import gzip
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import TaskGovernance as G
from WorkflowStageLifecycle import StageSnapshot, VISIBLE_PATHS, canonical_bytes, git as git_bytes
import runpy

A = 'project-state/governance/pr208-postmerge-closeout-2026-10-03/'
B = 'project-state/governance/pr209-reconciliation-2026-10-03/'
CAMPAIGN = 'project-state/governance/remaining-approved-review-2026-10-03/'
MERGE = '26442ad202d696f8582b634ecf5283ee56b8482a'
REVIEWED = '78327bed8cdc2cc25e540d1737cde22096ec8e83'
CAMPAIGN_HEAD = '758e29120fd40b4a5a20d791c2cbc62445ddd36e'
ROUTES = ['transportation/bicycling', 'development-land-use/development-process',
          'public-works/capital-projects', 'public-works/parks-recreation']


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    target = G.ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=G.ROOT))


def audit(paths):
    registry = G.load(G.REGISTRY)
    data = G.load(registry['audit_artifact'])
    indexed = {r['path']: r for r in data['artifacts']}
    for path in paths:
        indexed[path] = dict(path=path, sha256=G.file_hash(path), hash_kind='normalized-file-bytes',
                             classification='historical evidence only / non-binding', governance_ids=[],
                             rationale='Preserved task execution, baseline, verification or integration evidence; no independent continuing authority.')
    data['artifacts'] = sorted(indexed.values(), key=lambda r: r['path'])
    save(registry['audit_artifact'], data)
    registry['audit_sha256'] = G.file_hash(registry['audit_artifact'])
    save(G.REGISTRY, registry)


def bind(path, gid, requirement, scope):
    registry = G.load(G.REGISTRY)
    assert not any(r['governance_id'] == gid for r in registry['entries'])
    registry['entries'].append(dict(governance_id=gid, category='active owner decision', title=gid,
        scope=scope, authority='Explicit current owner instruction: two separate governed phases after manual PR208 merge',
        decision_date='2026-10-03', effective_date='2026-10-03', state='active',
        controlling_artifacts=[dict(path=path, sha256=G.file_hash(path), binding_pointers=['/'])],
        binding_requirement=requirement, required_actions=[requirement], prohibited_actions=[], constraints=[],
        settled_decisions=[], unresolved_gates=[], implementation_status='bounded task authorization'))
    save(G.REGISTRY, registry)


def refresh(prefix):
    old = sorted((G.ROOT / prefix).glob('contract-v*.json'))
    audit([p.relative_to(G.ROOT).as_posix() for p in old])
    n = max(int(p.stem.split('-v')[1]) for p in old) + 1
    contract_path = prefix + f'contract-v{n}.json'
    populations = list((G.ROOT / prefix).glob('population-v*.json'))
    population_path = max(populations, key=lambda p: int(p.stem.split('-v')[1])).relative_to(G.ROOT).as_posix() if populations else prefix + 'population.json'
    subprocess.run([sys.executable, str(G.ROOT / 'scripts/project/Resolve-TaskGovernance.py'), 'resolve',
                    '--population', population_path, '--output', contract_path], cwd=G.ROOT,
                   check=True, stdout=subprocess.DEVNULL)
    c = G.load(contract_path)
    assert not c['conflicts'] and not c['unresolved_gates'], (c['conflicts'], c['unresolved_gates'])
    subjects = {}
    for row in c['resolved_rules']:
        for fact in row.get('constraints', []):
            subjects.setdefault(fact['subject'], {})[fact['field']] = fact['equals']
    plan = G.load(prefix + 'implementation.json')
    plan.update(contract=contract_path, contract_sha256=G.file_hash(contract_path),
                population_sha256=c['population_sha256'], respected_governance_ids=c['governance_ids'], subjects=subjects)
    for event in plan['events']:
        event['governance_ids'] = c['governance_ids']
    if (G.ROOT / (prefix + 'receipt.json')).exists():
        plan['completion_evidence'] = {gid: [dict(path=prefix + 'receipt.json', sha256=G.file_hash(prefix + 'receipt.json'))]
                                       for gid in c['governance_ids']}
    save(prefix + 'implementation.json', plan)
    save(G.ACTIVE_TASK, dict(population=population_path, contract=contract_path,
                            contract_sha256=G.file_hash(contract_path), implementation=prefix + 'implementation.json',
                            state='in_progress'))
    print('Fresh contract:', contract_path, len(c['governance_ids']), 'rules; no conflicts/gates')


def setup_a():
    G.active_check('mutation', 'governance_implementation')
    G.write_once(A + 'authority.json', dict(authority='Explicit current owner instruction',
        phase='A', instruction='Verify actual PR208 production at exact merge commit, preserve historical review/preview evidence, '
        'record two City resources live and Animal Care, Paradise Hills and Sunport companion exclusions binding. '
        'Dedicated closeout branch from current main; background-only integration into main is authorized after full validation. '
        'No new visitor-visible, inventory, R2 or substantive review changes. PR209 reconciliation is a later separate phase; '
        'planning-snapshot remains at reviewed head until final background state is settled.'))
    bind(A + 'authority.json', 'owner-pr208-postmerge-closeout-2026-10-03',
         G.load(A + 'authority.json')['instruction'], {'task_ids': ['pr208-postmerge-closeout-2026-10-03']})
    G.write_once(A + 'supersession.json', dict(proposals={}))
    G.write_once(A + 'starting-remote-state.json', dict(checked_at_utc=now(), refs={r: G.git('rev-parse', r) for r in
        ['origin/main', 'origin/chatgpt/planning-snapshot', 'origin/codex/remaining-approved-review-2026-10-03']},
        pr208=gh('pr', 'view', '208', '--json', 'number,state,mergedAt,mergeCommit,headRefOid,headRefName,url'),
        pr209=gh('pr', 'view', '209', '--json', 'number,state,isDraft,headRefOid,headRefName,baseRefName,url')))
    stages = G.load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id'] == 'pr208-county-scope-correction'
    stages['stages'][-1]['end_commit'] = MERGE
    stages['stages'].append(dict(id='pr208-postmerge-closeout', baseline_commit=MERGE,
        regression_scripts=['scripts/project/Pr208209Reconciliation.py'],
        exact_delta_guard=dict(module='Pr208209Reconciliation', function='guard_a')))
    save('project-state/workflow-stage-lifecycle.json', stages)
    runner = G.ROOT / 'scripts/project/Invoke-ProjectValidation.ps1'
    text = runner.read_text(encoding='utf-8')
    pos = text.index('Set-StrictMode -Version Latest')
    text = text[:pos] + "& python \"$PSScriptRoot/Pr208209Reconciliation.py\" guard\nif ($LASTEXITCODE) { throw 'PR208/209 governed reconciliation guard failed.' }\n" + text[pos:]
    runner.write_text(text, encoding='utf-8', newline='\n')
    audit([A + 'starting-remote-state.json', 'project-state/workflow-stage-lifecycle.json'])
    refresh(A)
    G.active_check('mutation', 'governance_implementation')


def presentation(body):
    helper = runpy.run_path(str(G.ROOT / 'scripts/project/Verify-Pr198Production.py'))
    html, decoded = helper['normalize_cloudflare_email'](body.decode('utf-8'))
    article = helper['Article']()
    article.feed(html)
    normal = runpy.run_path(str(G.ROOT / 'scripts/project/Verify-Pr202Production.py'))['normalize_protected_email_links']
    return normal(article.result()), decoded


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'ABQInfo official-source verification',
        'Cache-Control': 'no-cache, no-store, max-age=0', 'Pragma': 'no-cache'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read(), dict(response.headers), response.status, response.url


def verify_a():
    G.active_check('mutation', 'governance_implementation')
    pr = gh('pr', 'view', '208', '--json', 'number,state,mergedAt,mergeCommit,headRefOid,headRefName,baseRefName,url')
    assert pr['state'] == 'MERGED' and pr['mergeCommit']['oid'] == MERGE and pr['headRefOid'] == REVIEWED
    assert G.git('rev-parse', MERGE + '^{tree}') == G.git('rev-parse', REVIEWED + '^{tree}')
    checks = gh('api', 'repos/armandhammer/abqinfo/commits/' + MERGE + '/check-runs')
    runs = [r for r in checks['check_runs'] if r['name'] == 'Cloudflare Pages']
    assert len(runs) == 1
    run = runs[0]
    assert run['head_sha'] == MERGE and run['status'] == 'completed' and run['conclusion'] == 'success'
    deployment = 'https://' + run['external_id'][:8] + '.abqinfo.pages.dev'
    preview = G.load('project-state/governance/pr208-county-scope-correction-2026-10-03/preview-verification.json')
    report = dict(result='passed', verified_at_utc=now(), merge_commit=MERGE, reviewed_head=REVIEWED,
                  comparison='Complete ordered article text, links and anchors; only Cloudflare protected email normalized.', pages=[])
    for i, route in enumerate(ROUTES):
        witnesses, values = [], []
        for label, host in [('production', 'https://abqinfo.com'), ('merge_deployment', deployment),
                            ('reviewed_preview', preview['preview_url'])]:
            url = host + '/' + route + '/'
            if label == 'production':
                url += '?pr208-production-verification=' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            body, headers, status, final = get(url)
            assert status == 200, (url, status)
            value, decoded = presentation(body)
            values.append(value)
            witness_path = A + f'page-{i}-{label}.html.gz'
            (G.ROOT / witness_path).write_bytes(gzip.compress(body, mtime=0))
            witnesses.append(dict(label=label, requested_url=url, final_url=final, http_status=status,
                response_headers=headers, size_bytes=len(body), html_sha256=hashlib.sha256(body).hexdigest(),
                article_sha256=hashlib.sha256(G.canonical(value)).hexdigest(), saved_witness=witness_path,
                cloudflare_email_decodes=decoded))
        assert values[0] == values[1] == values[2], ('Production/merge/preview semantic mismatch', route)
        text, links, anchors = values[0]
        assert 'Animal Care and Resource Center (2017)' not in text and 'Historical County Parks Investment' not in text
        assert 'animal-care-and-resource-center-2017' not in anchors and 'historical-county-parks-investment' not in anchors
        if i < 2:
            path = G.load(A + 'population.json')['pages'][i]
            md = (G.ROOT / path).read_text(encoding='utf-8')
            title = ['Bike Facilities in Albuquerque — Live City Guide',
                     'Online Planning Services, Permitting & Applications — Live City Services'][i]
            match = re.search(r'- \[' + re.escape(title) + r'\]\(([^)]+)\)\s+([^\n]+)', md)
            assert match and title in text and links.count(match[1]) == 1
            assert ' '.join(match[2].strip().split()) in text
            assert ['facility-types-and-crossings', 'current-city-review-process'][i] in anchors
        report['pages'].append(dict(route=route, article_identical_across_witnesses=True,
            rejected_county_sections_absent=True, witnesses=witnesses))
    G.write_once(A + 'merge-deployment.json', dict(checked_at_utc=now(), pr=pr, merge_commit=MERGE,
        current_main=G.git('rev-parse', 'origin/main'), reviewed_head=REVIEWED,
        merge_tree=G.git('rev-parse', MERGE + '^{tree}'), merge_tree_matches_reviewed_head=True,
        checks=runs, deployment_url=deployment))
    G.write_once(A + 'production-verification.json', report)
    source_results = []
    from urllib.error import HTTPError
    for path in G.load(A + 'population.json')['pages'][:2]:
        md = (G.ROOT / path).read_text(encoding='utf-8')
        url = re.search(r'\[.*? — Live City (?:Guide|Services)\]\(([^)]+)\)', md)[1]
        try:
            body, headers, status, final = get(url)
            source_results.append(dict(requested_url=url, final_url=final, http_status=status,
                response_bytes=len(body), response_sha256=hashlib.sha256(body).hexdigest()))
        except HTTPError as error:
            source_results.append(dict(requested_url=url, http_status=error.code,
                limitation='Fresh source request blocked; preserved official-source review remains historical evidence.'))
    G.write_once(A + 'source-link-verification.json', dict(checked_at_utc=now(), publication_form='live_service',
        archive_objects=0, public_archive_verification='not applicable to two maintained HTML services', records=source_results))
    print('PASS: production, exact merge deployment and corrected reviewed preview agree on all four pages.')


def current_text(phase):
    intro = ('[PR #208](https://github.com/armandhammer/abqinfo/pull/208) merged as `26442ad202d696f8582b634ecf5283ee56b8482a`; '
             'production verified. Bike Facilities and Online Planning Services are live. Animal Care, Paradise Hills parks and Sunport companion exclusions remain binding. ')
    if phase == 'A':
        intro += 'PR #209 is the next background reconciliation item. Planning-snapshot remains at reviewed PR208 head. Queue: 13 approved, 372 pending.'
    else:
        intro += 'PR #209’s completed 13-record background campaign is integrated: 11 excluded, airport plan retained with archive/delivery hold, 2nd Street pending exact FHWA identity. Queue: 1 approved, 373 pending. No active unfinished publication task or new review population. Both holds need separate future governed research; no current owner choice.'
    return ('# Current project state\n\n' + intro + '\n\nR2 unchanged. ' +
        '[PR208 closeout](governance/pr208-postmerge-closeout-2026-10-03/receipt.json) · ' +
        ('[PR209 reconciliation](governance/pr209-reconciliation-2026-10-03/receipt.json) · [campaign accounting](governance/remaining-approved-review-2026-10-03/accounting.json) · ' if phase != 'A' else '') +
        '[active task](governance/active-task.json) · [PR207 correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · '
        '[PR207 closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · '
        '[ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · '
        '[triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · '
        '[queue](ordinary-queue-current.json) · [workflow](governance-workflow.md) · [registry](governance-registry.json).\n')


def finish_a():
    G.active_check('mutation', 'governance_implementation')
    production = G.load(A + 'production-verification.json')
    assert production['result'] == 'passed'
    G.write_once(A + 'receipt.json', dict(artifact_type='postmerge_closeout_receipt', task_id='pr208-postmerge-closeout-2026-10-03',
        state='production_verified_background_closeout', merge_commit=MERGE, reviewed_head=REVIEWED,
        pr=G.load(A + 'merge-deployment.json')['pr'], production_pages_verified=4, live_city_resources=2,
        exclusions_preserved=['Animal Care and Resource Center (2017)', 'Paradise Hills parks', 'Sunport companion'],
        closeout_visitor_visible_changes=0, closeout_inventory_changes=0, closeout_r2_changes=0,
        historical_review_receipts_preserved=True, next_item='PR209 background campaign reconciliation',
        production_evidence=A + 'production-verification.json', normal_validation='pending'))
    checkpoint = G.load('project-state/checkpoint.json')
    checkpoint['pr208_postmerge_closeout'] = dict(state='production_verified', merge_commit=MERGE,
        receipt=A + 'receipt.json', next_item='PR209 background reconciliation', r2_changes=0)
    save('project-state/checkpoint.json', checkpoint)
    (G.ROOT / 'project-state/CURRENT.md').write_text(current_text('A'), encoding='utf-8', newline='\n')
    plan = G.load(A + 'implementation.json')
    plan['events'] = [dict(operation='governance_implementation', candidate_ids=G.load(A+'population.json')['candidate_ids'],
        action='implements', use_contract_record_rules=True, evidence=A+'receipt.json',
        summary='Verified merged production and preserved all settled exclusions; closeout bookkeeping only.')]
    plan['status'] = 'production_verified'
    save(A + 'implementation.json', plan)
    audit([A + n for n in ['receipt.json', 'production-verification.json', 'merge-deployment.json', 'source-link-verification.json']])
    refresh(A)
    G.active_check('final')
    guard_a()


def validated(prefix):
    receipt = G.load(prefix + 'receipt.json')
    receipt['normal_validation'] = 'passed'
    receipt['validation_log_sha256'] = G.file_hash(prefix + 'validation.log')
    save(prefix + 'receipt.json', receipt)
    audit([prefix + 'receipt.json'])
    refresh(prefix)
    G.active_check('final')


def guard_a():
    stage = StageSnapshot('pr208-postmerge-closeout')
    stage.assert_no_visible_changes(MERGE, G.git('rev-parse', MERGE + ':content'))
    for path in ['project-state/master-inventory.json', 'project-state/r2-inventory.json',
                 'project-state/r2-storage-policy.json', 'project-state/ordinary-queue-current.json']:
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git_bytes('show', MERGE + ':' + path)), path
    paths = git_bytes('ls-tree', '-r', '--name-only', MERGE, '--',
        'project-state/governance/strong-five-review-2026-10-03',
        'project-state/governance/pr208-county-scope-correction-2026-10-03',
        'project-state/governance/pr207-owner-correction-2026-09-30').decode().splitlines()
    for path in paths:
        assert canonical_bytes(stage.read_bytes(path)) == canonical_bytes(git_bytes('show', MERGE + ':' + path)), path
    pop = stage.load_json(stage.load_json(G.ACTIVE_TASK)['population'])
    changed = set(git_bytes('diff', MERGE, stage.end, '--name-only').decode().splitlines()) if stage.end else set(G.changed_paths(MERGE))
    assert changed <= set(pop['artifact_paths']), 'Unfrozen closeout delta: ' + str(changed - set(pop['artifact_paths']))
    receipt = stage.load_json(A + 'receipt.json')
    assert receipt['merge_commit'] == MERGE and receipt['live_city_resources'] == 2
    assert receipt['closeout_visitor_visible_changes'] == receipt['closeout_inventory_changes'] == receipt['closeout_r2_changes'] == 0
    production = stage.load_json(A + 'production-verification.json')
    assert production['result'] == 'passed' and len(production['pages']) == 4
    for page in production['pages']:
        assert page['article_identical_across_witnesses'] and page['rejected_county_sections_absent']
        assert len({w['article_sha256'] for w in page['witnesses']}) == 1
        for witness in page['witnesses']:
            raw = gzip.decompress(stage.read_bytes(witness['saved_witness']))
            assert len(raw) == witness['size_bytes'] and hashlib.sha256(raw).hexdigest() == witness['html_sha256']
    if receipt['normal_validation'] == 'passed':
        assert G.file_hash(A+'validation.log') == receipt['validation_log_sha256']
    print('PASS: PR208 closeout exact-delta, production witnesses and historical evidence preserved.')


def guard():
    if (G.ROOT / (A + 'receipt.json')).exists():
        guard_a()


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'guard'
    if command == 'validated_a':
        validated(A)
    else:
        globals()[command]()
