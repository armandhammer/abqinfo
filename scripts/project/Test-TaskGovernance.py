"""Negative coverage for every required failure class, using the actual PR198 population."""
import copy
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
import TaskGovernance as G

passed=[]
def rejects(name, function):
    try:
        function()
    except (G.GovernanceError, FileNotFoundError):
        passed.append(name)
    else:
        raise AssertionError('Governance accepted '+name)

data=G.registry()
tools=G.load('project-state/governance/entrypoints.json')['tools']
for path in tools:
    source=(G.ROOT/path).read_text(encoding='utf-8-sig')
    assert ('require_tool_governance(__file__)' if path.endswith('.py') else 'Assert-TaskGovernance -ToolPath $PSCommandPath') in source,path
passed.append('every_substantive_legacy_entrypoint_guarded')
pop=G.load('project-state/governance/pr198/population.json')
contract=G.resolve(pop,data,G.file_hash(G.REGISTRY))
ids=set(contract['governance_ids'])
expected={'capital-2009-historical-master','capital-2011-two-masters','capital-2007-2016-decade-master',
          'capital-2005-2013-ccip-master','capital-energy-water-cycle-master','capital-september18-closeout'}
assert expected <= ids, 'September18 decision omitted from real PR198 population'
global_ids={r['governance_id'] for r in data['entries'] if r['state']=='active' and r['scope'].get('global')}
assert global_ids <= ids
assert len(pop['candidate_ids'])==32

subjects={}
for row in contract['resolved_rules']:
    for rule in row['constraints']:
        subjects.setdefault(rule['subject'],{})[rule['field']]=rule['equals']
plan={'population_sha256':contract['population_sha256'],'respected_governance_ids':contract['governance_ids'],
      'subjects':subjects,'actions':['consolidation'],'events':[]}
G.validate_plan(contract,plan)
passed.append('compliant_master_pdf_architecture_passes')
assert not any(g['gate_id']=='pr198:31-versus-32' for g in contract['unresolved_gates'])
assert subjects['go-2009']['master_count']==1
assert len(subjects['pr198']['candidate_ids'])==32
wrong=copy.deepcopy(plan);wrong['subjects']['pr198']['candidate_ids'].remove('src-7567c5f27fceba0a')
rejects('arbitrary_32nd_record_drop_rejected',lambda:G.validate_plan(contract,wrong))
wrong=copy.deepcopy(plan);wrong['subjects']['src-7567c5f27fceba0a']['inside_go_2009_master']=True
rejects('authorization_inside_24_component_master_rejected',lambda:G.validate_plan(contract,wrong))
wrong=copy.deepcopy(plan);wrong['subjects']['src-7567c5f27fceba0a']['retained_visitor_visible']=False
rejects('owner_kept_authorization_removal_rejected',lambda:G.validate_plan(contract,wrong))

def pr198_reader(path):return subprocess.check_output(['git','show',pop['baseline_commit']+':'+path],cwd=G.ROOT).decode('utf-8-sig')
pr198_page=pr198_reader('content/city-data/capital-spending.md')
rejects('actual_pr198_page_bytes_lack_decided_master_pdfs',lambda:G.actual_presentations(contract,pr198_reader,pop['pages']))
for gid in ('capital-2009-historical-master','capital-2011-two-masters'):
    single={**contract,'resolved_rules':[r for r in contract['resolved_rules'] if r['governance_id']==gid]}
    rejects('actual_page_rejected_'+gid,lambda c=single:G.actual_presentations(c,lambda p:pr198_page,pop['pages']))
compliant_page='\n'.join(url for row in contract['resolved_rules'] for url in row.get('expected_master_archives',[])+row.get('retained_original_archives',[]))
topical={}
for row in contract['resolved_rules']:
    for path,urls in row.get('topical_original_archives',{}).items():topical.setdefault(path,[]).extend(urls)
def compliant_reader(path):return compliant_page if path=='content/city-data/capital-spending.md' else '\n'.join(topical.get(path,[]))
G.actual_presentations(contract,compliant_reader,pop['pages'])
passed.append('actual_master_archive_link_fixture_passes_output_form')
wrong_page=compliant_page+'\n'+next(r for r in contract['resolved_rules'] if r['governance_id']=='capital-2011-two-masters')['capital_component_links_to_replace'][0]
rejects('master_links_do_not_exempt_retained_2011_component_entries',lambda:G.actual_presentations(contract,lambda p:wrong_page,pop['pages']))
if set(topical)&set(pop['pages']):
    rejects('master_links_do_not_exempt_broad_topical_redirects',lambda:G.actual_presentations(contract,lambda p:compliant_page if p=='content/city-data/capital-spending.md' else '',pop['pages']))
webpage=copy.deepcopy(plan)
webpage['subjects']['go-2009']['publication_form']='webpage_only'
rejects('pr198_webpage_only_2009_rejected',lambda:G.validate_plan(contract,webpage))
webpage=copy.deepcopy(plan);webpage['subjects']['go-2011']['publication_form']='webpage_only'
rejects('pr198_webpage_only_2011_rejected',lambda:G.validate_plan(contract,webpage))
wrong=copy.deepcopy(plan);wrong['subjects']['go-2011']['master_count']=1
rejects('pr198_single_2011_master_rejected',lambda:G.validate_plan(contract,wrong))
wrong=copy.deepcopy(plan);wrong['subjects']['go-2009']['topical_cross_listing']='broad_master_redirect'
rejects('ignored_topical_architecture_rejected',lambda:G.validate_plan(contract,wrong))

with patch.object(G,'ACTIVE_TASK','tmp/nonexistent-governance-test-contract.json'):
    rejects('missing_task_contract',lambda:G.active_check())
rejects('completed_contract_cannot_authorize_new_work',lambda:G.task_lifecycle({'state':'complete'},'mutation','background_integration'))
G.task_lifecycle({'state':'complete'},'final',None)
different=copy.deepcopy(pop);different['candidate_ids'].pop()
rejects('changed_population',lambda:G.freshness(contract,different,data,G.file_hash(G.REGISTRY)))
rejects('changed_registry',lambda:G.freshness(contract,pop,data,'changed'))
for label,gid in [('omitted_global_rule',next(iter(global_ids))),('omitted_scoped_rule','capital-2011-two-masters')]:
    bad=copy.deepcopy(contract);bad['governance_ids'].remove(gid)
    rejects(label,lambda b=bad:G.freshness(b,pop,data,G.file_hash(G.REGISTRY)))
bad=copy.deepcopy(contract);bad['controlling_artifacts'][0]=['changed','changed']
rejects('changed_governing_artifact_after_preflight',lambda:G.freshness(bad,pop,data,G.file_hash(G.REGISTRY)))
new=copy.deepcopy(data);row=copy.deepcopy(next(r for r in new['entries'] if r['governance_id']=='policy-agents'))
row['governance_id']='new-global-rule';new['entries'].append(row)
rejects('new_applicable_active_decision',lambda:G.freshness(contract,pop,new,G.file_hash(G.REGISTRY)))
wrong=copy.deepcopy(plan);wrong['respected_governance_ids'].pop()
rejects('unaccounted_implementation_rule',lambda:G.validate_plan(contract,wrong))
for action in ('re_research','re_decide','request_human_review'):
    wrong=copy.deepcopy(plan);wrong['events']=[{'operation':'consolidation','action':action,
                                             'question_id':'go-2009:publication-architecture'}]
    rejects('settled_question_'+action,lambda w=wrong:G.validate_plan(contract,w))
quality=next(s['question_id'] for s in contract['settled_decisions'] if 'september13-standalone-quality' in s['question_id'])
wrong=copy.deepcopy(plan);wrong['events']=[{'operation':'quality_assessment','action':'re_decide','question_id':quality}]
rejects('september13_negative_not_reopened',lambda:G.validate_plan(contract,wrong))
conflicting=copy.deepcopy(data);row=copy.deepcopy(next(r for r in conflicting['entries'] if r['governance_id']=='capital-2009-historical-master'))
row['governance_id']='conflicting-active-architecture';row['constraints'][0]['equals']='webpage_only';conflicting['entries'].append(row)
conflict_contract=G.resolve(pop,conflicting,'test-registry');wrong=copy.deepcopy(plan)
wrong['respected_governance_ids']=conflict_contract['governance_ids']
rejects('conflicting_active_rules',lambda:G.validate_plan(conflict_contract,wrong))
new=copy.deepcopy(data);new['entries']=[r for r in new['entries'] if r['governance_id']!='capital-2009-historical-master']
rejects('silent_removal',lambda:G.check_registry_transition(data,new,{}))
new=copy.deepcopy(data);next(r for r in new['entries'] if r['governance_id']=='capital-2009-historical-master')['binding_requirement']='Use a webpage.'
rejects('silent_supersession',lambda:G.check_registry_transition(data,new,{}))
fixture={'entries':[{'state':'active','controlling_artifacts':[{'path':'proposal.json','sha256':'known'}]}]}
with patch.object(G,'file_hash',return_value='known'), patch.object(G,'load',return_value={'proposals':{'test':'receipt'}}):
    assert G.task_supersession_proposals({'supersession_proposals_path':'proposal.json'},fixture)=={'test':'receipt'}
    rejects('unregistered_supersession_receipt',lambda:G.task_supersession_proposals({'supersession_proposals_path':'other.json'},fixture))
with patch.object(G,'file_hash',return_value='changed'):
    rejects('changed_supersession_receipt',lambda:G.task_supersession_proposals({'supersession_proposals_path':'proposal.json'},fixture))
passed.append('registered_exact_supersession_receipt_supported')
new=copy.deepcopy(data)
next(r for r in new['entries'] if r['governance_id']=='capital-2009-historical-master')['controlling_artifacts'][0]['sha256']='f'*64
rejects('silent_controlling_decision_hash_refresh',lambda:G.check_registry_transition(data,new,{}))
wrong=copy.deepcopy(plan);wrong['actions']=['archive']
rejects('master_architecture_does_not_release_archive_gate',lambda:G.validate_plan(contract,wrong,'mutation'))
wrong=copy.deepcopy(plan);wrong['actions']=['content_implementation']
rejects('2004_2013_supersession_gate_preserved',lambda:G.validate_plan(contract,wrong,'mutation'))
with tempfile.TemporaryDirectory(dir=G.ROOT/'tmp') as directory:
    root=Path(directory)
    (root/'audit.json').write_text(json.dumps({'artifacts':[]}),encoding='utf-8')
    (root/'new-decision.json').write_text(json.dumps({'decision':'Never replace the master PDF with a webpage.'}),encoding='utf-8')
    rejects('new_unregistered_binding_instruction',lambda:G.check_unregistered({'entries':[],'audit_artifact':'audit.json'},['new-decision.json'],root))
    (root/'new-decision.json').write_text(json.dumps({'governance_metadata':{'state':'active','governance_id':'not-registered'}}),encoding='utf-8')
    rejects('metadata_without_registration',lambda:G.check_unregistered({'entries':[],'audit_artifact':'audit.json'},['new-decision.json'],root))
    (root/'hidden-decision.txt').write_text('Never replace the decided capital master with a webpage.',encoding='utf-8')
    rejects('unregistered_plain_text_instruction',lambda:G.check_unregistered({'entries':[],'audit_artifact':'audit.json'},['hidden-decision.txt'],root))

# Candidate-only inputs infer actual family rules: no dependence on contextual labels.
for gid in ('capital-2009-historical-master','capital-2011-two-masters'):
    row=next(r for r in data['entries'] if r['governance_id']==gid)
    member=next(i for i in pop['candidate_ids'] if any(i in members for members in row['family_memberships'].values()))
    single={**pop,'candidate_ids':[member],'families':[],'pages':[],'artifact_paths':[]}
    assert gid in G.resolve(single,data,'fixture')['governance_ids']
passed.append('candidate_only_family_resolution')
for gid in ('owner-fiber-correspondence','owner-wireless-checklist','owner-art-advocacy-primary-sources','owner-dpm-historical-drafts'):
    owner=next(r for r in data['entries'] if r['governance_id']==gid)
    op='archive' if gid in ('owner-fiber-correspondence','owner-wireless-checklist') else 'content_implementation'
    one={**pop,'candidate_ids':owner['scope']['candidate_ids'],'families':[],'pages':[],'artifact_paths':[],'operation_classes':[op]}
    oc=G.resolve(one,data,'fixture');facts={}
    for row in oc['resolved_rules']:
        for fact in row['constraints']:facts.setdefault(fact['subject'],{})[fact['field']]=fact['equals']
    owner_plan={'population_sha256':oc['population_sha256'],'respected_governance_ids':oc['governance_ids'],'subjects':facts,'actions':[op],'events':[]}
    if op=='content_implementation':
        G.validate_plan(oc,owner_plan)
        facts[owner['scope']['families'][0]]['public_presentation']='official_current_standard'
    rejects('owner_form_enforced_'+gid,lambda c=oc,p=owner_plan:G.validate_plan(c,p))
audited=G.load(data['audit_artifact'])
frozen=G.load('project-state/governance/audit-2026-09-27/bootstrap-population.json')
assert set(frozen['artifact_paths']) <= {a['path'] for a in audited['artifacts']}
assert set(data['categories']) <= {r['category'] for r in data['entries']}
print(json.dumps({'result':'passed','checks':passed,'actual_pr198_applicable_ids':contract['governance_ids'],
                  'active_entries':sum(r['state']=='active' for r in data['entries']),
                  'superseded_entries':sum(r['state']=='superseded' for r in data['entries']),
                  'audited_artifacts':len(audited['artifacts'])},indent=2))
