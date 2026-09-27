"""One-time, reviewable baseline authority backfill; never invoked by task resolution.

Classification uses artifact purpose and binding fields, not filename dates. Completed
action receipts and saved recommendations are not future authority. The explicit
special cases below preserve presentation decisions independently of upload gates.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/project'))
from TaskGovernance import file_hash
BASE = '940e3032d96f868eed8cff7c3deeaf1c556f50a2'
OUT = ROOT / 'project-state/governance/audit-2026-09-27'
CATEGORIES = ['active project-wide policy', 'active owner decision', 'active family decision',
              'active publication architecture', 'active storage/external-action authorization',
              'active workflow requirement', 'explicitly superseded historical decision']

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))

def save(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def strings(value, pointer=''):
    if isinstance(value, dict):
        for k,v in value.items():
            # Snapshots and copied processing history do not establish fresh authority.
            if k not in ('processing_notes', 'baseline_records', 'baseline_row_digests',
                         'original_row_digests', 'baseline_inventory', 'baseline_owner_packages', 'decision_history'):
                yield from strings(v, pointer+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(value, list):
        for i,v in enumerate(value):
            yield from strings(v, pointer+'/'+str(i))
    elif isinstance(value, str):
        yield pointer, value

def selectors(path, value):
    leaves = list(strings(value))
    text = '\n'.join(v for _,v in leaves)
    ids = sorted(set(re.findall(r'\b(?:src|lin)-[0-9a-f]{16}\b', text)))
    pages = sorted(set(re.findall(r'content/[a-zA-Z0-9_./-]+\.md', text)))
    scope = {'candidate_ids': ids, 'pages': pages, 'artifact_paths': [path]}
    # Exact declaration is retained even where an old artifact has no candidate ID.
    if not ids and not pages:
        scope['global'] = True  # Conservative coverage, never silently omit unscoped instructions.
    return scope

entries = []
by_path = {}

def add(gid, path, category, requirement, scope=None, authority='durable recorded project decision',
        pointers=None, constraints=None, settled=None, gates=None, prohibited=None, date=None):
    value = read(path) if path.endswith('.json') else (ROOT/path).read_text(encoding='utf-8-sig')
    row = {'governance_id': gid, 'category': category, 'title': requirement.split('.')[0],
           'scope': scope or selectors(path, value), 'authority': authority,
           'decision_date': date or (value.get('reviewed_at', value.get('updated_at', value.get('generated_at')))
                                    if isinstance(value, dict) else None),
           'effective_date': date or 'as recorded in controlling artifact; no chronology precedence',
           'state': 'active', 'controlling_artifacts': [{'path':path, 'sha256':file_hash(path),
                                                      'binding_pointers': pointers or ['/']}],
           'binding_requirement': requirement,
           'required_actions': [requirement], 'prohibited_actions': prohibited or ['Do not infer new external authorization from this artifact.'],
           'constraints': constraints or [], 'settled_decisions': settled or [], 'unresolved_gates': gates or [],
           'implementation_status': 'Preserve continuing consequence; completion receipts do not confer new authority.'}
    entries.append(row)
    by_path.setdefault(path, []).append(gid)
    return row

special = {
 'AGENTS.md': ('policy-agents','active project-wide policy','Apply all ABQInfo instructions: scope, actual-record quality, exact archive provenance, owner review of visible changes, durable checkpoints and external-action authority.'),
 'project-state/README.md': ('policy-project-state','active project-wide policy','Use inventory as authoritative state; preserve qualifying originals and official links; reject XFA placeholders; govern source recovery, current contacts, official outbound discovery and deferred-source priorities.'),
 'project-state/publication-quality-policy.md': ('policy-publication-quality','active project-wide policy','Assess actual records and complete families independently of scope/provenance/rendering; preserve negative findings; no consolidation exemption or unsupported limited-content exception.'),
 'project-state/r2-storage-policy.json': ('policy-r2-storage','active storage/external-action authorization','Standing ceiling is 13000000000 decimal bytes and campaign objects 150000000 maximum; no overwrite/deletion for capacity. Storage eligibility never authorizes an external mutation.'),
 'project-state/discovery/mission-scope-review-policy-2026-09-22.json': ('policy-mission-scope','active project-wide policy','Apply both material Albuquerque connection and substantive public-information value gates; require complete structured positive assessment for every eligible changed state; exclude definitive failures and cap exclusive borderline queue at 20.'),
 'project-state/discovery/mission-scope-legacy-cutover-2026-09-23.json': ('policy-mission-scope-legacy','active project-wide policy','The exact frozen legacy scope exemption applies only to unchanged historical status and timestamp. Any changed legacy record must pass both gates.'),
 'project-state/project-recency-policy.json': ('policy-project-recency','active project-wide policy','Apply recorded project-currentness windows and historical placement; do not imply an old project is current.'),
 'project-state/tip-stip-retention-policy.json': ('policy-tip-stip-retention','active family decision','Retain distinct stable/adopted TIP/STIP finals and version lineage; do not treat unlabelled regenerated viewer snapshots as adopted plans.'),
 'project-state/campaign-workflow.md': ('workflow-background-campaign','active workflow requirement','Honor complete durable campaign workflow, exact invocation/population/family receipts, protected boundaries, storage guards, immutable recovery and mandatory governance preflight.'),
 'project-state/workflow-stage-lifecycle.md': ('workflow-stage-lifecycle','active workflow requirement','Seal prior lifecycle stages at immutable endpoints; authorize exact later deltas; preserve historical evidence and remediation baselines unchanged.'),
 'project-state/governance-workflow.md': ('policy-durable-task-governance','active workflow requirement','Freeze population, resolve every active global/applicable scoped rule, attach per-record rules, freshness-check before mutation, validate final implementation and register every new binding artifact. Explicit supersession only.'),
 'project-state/governance/audit-2026-09-27/bootstrap-authority.json': ('owner-durable-governance-2026-09-27','active owner decision','Pause PR198. This task is background-only: no content, inventory dispositions, R2 or publication changes. Audit all durable authority, build exhaustive deterministic governance and regressions, run normal validation, integrate background fix and reconcile main/planning.'),
 'project-state/PARALLEL-VERIFICATION.md': ('workflow-parallel-verification','active workflow requirement','If explicitly authorized, parallel verification uses frozen disjoint shards and detached worktrees; only one integrator changes durable state. This does not invoke parallel work.'),
 'project-state/AUTONOMOUS-VERIFICATION-CAMPAIGNS.md': ('workflow-autonomous-verification','active workflow requirement','Verification campaign selections, operation intents/results and recovery evidence are immutable; honor explicit campaign invocation and integrator boundaries.'),
 'project-state/AGENT-HANDOFF.md': ('workflow-handoff-retirement','active workflow requirement','Former dual-agent work ledger is explicitly retired. Preserve it as historical evidence and use the governance registry for active authority.'),
 'project-state/source-priorities.json': ('policy-source-priorities','active project-wide policy','Follow recorded primary/deferred/last-resort source priorities; jurisdiction and discovery do not establish mission scope.'),
 'project-state/quality-exclusions.json': ('policy-quality-exclusions','active project-wide policy','Preserve recorded source/quality exclusions and their exact reasons; evidence recovery does not silently reverse an owner exclusion.'),
}
for path,(gid,cat,req) in special.items():
    row=add(gid,path,cat,req,{'global':True},'standing project policy / explicit owner instruction')
    if path.endswith('.md'):
        # Policy text is small. Carry it completely; do not let summaries omit a clause.
        row['required_actions'].append((ROOT/path).read_text(encoding='utf-8-sig').replace('\r\n','\n'))
entries[-(len(special)-list(special).index('project-state/governance/audit-2026-09-27/bootstrap-authority.json'))]['prohibited_operation_classes'] = [
    'content_implementation','content_removal','inventory_disposition','archive','visitor_visible_change','external_mutation']
# The current task boundary is task-specific, not a permanent ban on future publication.
owner_boot = next(r for r in entries if r['governance_id']=='owner-durable-governance-2026-09-27')
owner_boot['scope']={'families':['repository-governance'], 'artifact_paths':['project-state/governance/audit-2026-09-27/bootstrap-authority.json']}
freeze='project-state/governance/pr198/freeze-evidence.json'
if (ROOT/freeze).exists():
    add('pr198-population-boundary',freeze,'active owner decision',
        'The immutable queue has 32 capital matches against the requested 31. Owner directed that the exclusion question be left in the PR, not guessed. PR198 is paused; no arbitrary exclusion or implementation before resolution.',
        {'task_ids':['pr198-go-capital-next-step'],'artifact_paths':[freeze]},'explicit owner response / pause instruction',date='2026-09-27',
        gates=[{'gate_id':'pr198:31-versus-32','requirement':'Owner resolves the exact population boundary; preserve all 32 observed matches meanwhile.',
                'blocks_operations':['inventory_disposition','archive','content_implementation','content_removal','placement','cross_listing','visitor_visible_change']}])

capital = [
 ('capital-2009-historical-master','2009-capital-spending-consolidation-decision-2026-09-18.json','go-2009',1,24),
 ('capital-2011-two-masters','2011-capital-spending-consolidation-manifest-2026-09-18.json','go-2011',2,67),
 ('capital-2007-2016-decade-master','2007-2016-capital-details-consolidation-decision-2026-09-18.json','go-2007-2016',1,18),
 ('capital-2005-2013-ccip-master','2005-2013-impact-fee-ccip-consolidation-decision-2026-09-18.json','ccip-2005-2013',1,6),
 ('capital-energy-water-cycle-master','2011-2023-energy-water-public-facilities-system-modernization-cycle-scopes-decision-2026-09-18.json','energy-water-cycles',1,6),
]
for gid,name,family,count,components in capital:
    path='project-state/discovery/'+name
    value=read(path);scope=selectors(path,value);scope['families']=[family]
    scope['pages']=sorted(set(scope['pages']+['content/city-data/capital-spending.md']))
    facts={'publication_form':'master_pdf','master_count':count,'component_count':components,
           'preserve_originals':True,'topical_cross_listing':'individual_originals','version_finality':'no_unsupported_inference'}
    if family=='go-2011': facts.update({'preliminary_components':21,'published_components':46,'capital_standalone_component_links':0})
    row=add(gid,path,'active publication architecture',
            f'{family}: use {count} provenance-preserving historical master PDF(s), with {components} distinct originals. Preserve cycle/stage/version distinctions and independently useful topical original links; a webpage-only grouping is not the decided master.',
            scope,constraints=[{'subject':family,'field':k,'equals':v} for k,v in facts.items()],
            settled=[{'question_id':family+':publication-architecture','decision':facts}],
            gates=[{'gate_id':family+':archive-publication-authorization',
                    'requirement':'Separately authorized archival, full public-byte verification and owner-reviewed preview are required; this decision is architecture, not upload permission.',
                    'blocks_operations':['archive','content_implementation','visitor_visible_change','external_mutation']}], date='2026-09-18')
    row['required_actions'] += [v for p,v in strings(value) if re.search(r'(safeguard|treatment|provenance|cross.list|version|publication_gate|visible|chronology|duplicate|rationale)',p,re.I)
                              and not re.search(r'(description|title|url|filename|path)',p,re.I)]
    groups=[c['sources'] for c in value['compilations']] if 'compilations' in value else [value['proposed_compilation']['components']]
    member_ids=sorted({c['candidate_id'] for group in groups for c in group})
    assert len(member_ids)==components,(family,len(member_ids),components)
    row['family_memberships']={family:member_ids}
    keys=[c['proposed_r2_key'] for c in value['compilations']] if 'compilations' in value else [value['proposed_compilation']['future_r2_key']]
    row['expected_master_archives']=['https://files.abqinfo.com/'+key for key in keys]
    row['capital_component_links_to_replace']=([c.get('archive_url') or 'https://files.abqinfo.com/'+c['proposed_r2_key'] for group in groups for c in group]
                                               if family=='go-2011' else value.get('future_capital_spending_treatment',{}).get('replace_current_links',[]))
    row['topical_original_archives']={}
    for group in groups:
        for c in group:
            archive=c.get('archive_url') or c.get('current_archive_url')
            for page in c.get('current_implementation_locations',[]):
                page=page.split('#',1)[0]
                if archive and page!='content/city-data/capital-spending.md':row['topical_original_archives'].setdefault(page,[]).append(archive)
    row['unresolved_gates'][0]['scope']={'candidate_ids':member_ids,'families':[family]}
    row['constraints'].append({'subject':family,'field':'component_ids','equals':member_ids})
    if family=='go-2011':
        row['constraints'].append({'subject':family,'field':'master_boundaries',
                                   'equals':[[c['candidate_id'] for c in group] for group in groups]})

close='project-state/discovery/capital-spending-consolidation-closeout-status-2026-09-18.json'
value=read(close)
row=add('capital-september18-closeout',close,'active family decision',
        'All September18 Capital Spending presentation research is settled: implement the five exact compilation boundaries, keep the specified independent/nonmember records, preserve original provenance and topical originals, and honor external gates. No further architecture research is needed.',
        {'families':[x[2] for x in capital]+['go-2003','street-bond-2004','go-2013'],
         'pages':['content/city-data/capital-spending.md']},
        pointers=['/scope','/completed_future_compilation_boundaries','/reviewed_and_intentionally_unconsolidated','/provenance_and_cross_listing_rule','/remaining_external_publication_archive_gates'],date='2026-09-18')
row['required_actions'] += [x['treatment'] for x in value['reviewed_and_intentionally_unconsolidated']]
row['settled_decisions']=[{'question_id':'capital-september18:research-complete','decision':value['scope']['finding']}]
for family,ids,index in [('street-bond-2004',['src-a58b458f5d0f5284'],0),
                         ('go-2013',['src-040d6e306c1c448c','src-047e8956baad212d'],1)]:
    treatment=value['reviewed_and_intentionally_unconsolidated'][index]['treatment']
    add('capital-'+family+'-independent-instruments',close,'active publication architecture',treatment,
        {'families':[family],'candidate_ids':ids,'pages':['content/city-data/capital-spending.md']},
        pointers=['/reviewed_and_intentionally_unconsolidated/'+str(index)],date='2026-09-18',
        constraints=[{'subject':family,'field':'publication_form','equals':'retain_distinct_instruments'}],
        settled=[{'question_id':family+':publication-architecture','decision':treatment}])
auth_ids=['src-7567c5f27fceba0a','src-768a6855fcfaf443','src-b049c4df2812749b']
path='project-state/discovery/2009-capital-spending-consolidation-decision-2026-09-18.json'
add('capital-2009-independent-authorizations',path,'active publication architecture',
    'Keep the separately visible 2009 Library, community-center and Public Safety authorization instruments outside the 24-component master boundary; preserve their separate instruments and individual browsing treatment.',
    {'families':['go-2009-authorizations'],'candidate_ids':auth_ids,'pages':['content/city-data/capital-spending.md']},
    pointers=['/separately_visible_records','/future_capital_spending_treatment/retain_individual_visible_records'],date='2026-09-18',
    constraints=[{'subject':'go-2009-authorizations','field':'publication_form','equals':'retain_distinct_instruments'}],
    settled=[{'question_id':'go-2009-authorizations:publication-architecture','decision':'Three authorization instruments remain separately visible, outside the 24-component master.'}])
six=auth_ids+['src-a58b458f5d0f5284','src-040d6e306c1c448c','src-047e8956baad212d']
conflict=add('capital-retained-instruments-quality-conflict','project-state/discovery/publication-quality-remediation-2026-09-26.json',
             'active workflow requirement','Preserve six distinct independent instruments and their original negative findings. Implement both decisions through substantive assessed programme/family context while retaining independently traceable instrument evidence. Changing their settled independent relationship requires explicit supersession; the negative findings are not reopened.',
             {'candidate_ids':six},'deterministic derived conflict between registered active decisions',
             pointers=['/september_13_reconciliation'],
             constraints=[{'subject':'capital-independent-instruments','field':'changes_settled_independent_relationships','equals':False}],
             gates=[{'gate_id':'capital-six-retained-instruments:explicit-supersession',
                     'candidate_ids':six,'requirement':'Conditional gate: replacing the settled independent-instrument relationships requires explicit authorized supersession. Keeping distinct original evidence in substantive assessed family context implements both decisions and does not reopen a settled question.',
                     'when_subject_fact':{'subject':'capital-independent-instruments','field':'changes_settled_independent_relationships','equals':True},
                     'blocks_operations':['inventory_disposition','content_implementation','content_removal','placement','cross_listing','visitor_visible_change']}])
inventory=read('project-state/master-inventory.json')
conflict['retained_original_archives']=[r['r2_url'] for r in inventory['candidates'] if r['id'] in six and r.get('r2_url')]
conflict['authority']='deterministic compatibility rule implementing both registered decisions; no new owner disposition'
negative_path='project-state/discovery/publication-quality-remediation-2026-09-26.json'
negative_rows=[r for r in read(negative_path)['september_13_reconciliation'] if r['prior_status']=='does not meet standalone standard']
add('policy-settled-september13-findings',negative_path,'active project-wide policy',
    'Preserve every original September13 negative finding as settled historical evidence. Resolve weak standalone presentation through substantive assessed family/master forms; current visibility and consolidation are not quality exemptions and do not reopen the original finding.',
    {'candidate_ids':[r['id'] for r in negative_rows]},'explicit owner instruction / standing actual-record quality policy',
    pointers=['/september_13_reconciliation'],date='2026-09-13',
    settled=[{'question_id':r['id']+':september13-standalone-quality','decision':r['prior_status']} for r in negative_rows])
old='project-state/discovery/capital-spending-consolidation-status-2026-09-17.json'
row=add('capital-september17-resume-state',old,'explicitly superseded historical decision',
        'September17 resume-state instructions are superseded only as resume state by explicit September18 closeout.',{'pages':['content/city-data/capital-spending.md']},pointers=['/normal_resume_point'])
row.update(state='superseded',superseded_by='capital-september18-closeout',
           supersession_evidence={'path':close,'pointer':'/supersedes_as_resume_state'})

# Exact owner packages: older human-review requests remain historical evidence, never active gates.
path='project-state/discovery/owner-decisions-2026-09-26/authorization.json'
auth=read(path);changes=read('project-state/discovery/owner-decisions-2026-09-26/decisions.json')
for package,decision in auth['decisions'].items():
    ids=[r['id'] for r in changes if r['owner_package']==package]
    row=add('owner-'+package,path,'active owner decision',decision,{'candidate_ids':ids,'families':[package]},
            'explicit owner decision',pointers=['/decisions/'+package],date='2026-09-26',
            settled=[{'question_id':'owner-disposition:'+i,'decision':decision} for i in ids])
    if package in ('fiber-correspondence','wireless-checklist'):
        row['constraints']=[{'subject':package,'field':'public_presentation','equals':'excluded'}]
        row['prohibited_actions']=['No original, derivative or summary publication; preserve historical evidence.']
        row['prohibited_operation_classes']=['archive','content_implementation','placement','cross_listing','visitor_visible_change']
    if package=='art-advocacy-primary-sources':
        row['constraints']=[{'subject':package,'field':k,'equals':v} for k,v in
                            {'public_presentation':'attributed_historical_sources','official_city_findings':False,'approved_minutes':False}.items()]
    if package=='dpm-historical-drafts':
        row['constraints']=[{'subject':package,'field':k,'equals':v} for k,v in
                            {'public_presentation':'dated_historical_proposals','current_standards':False,'enacted_standards':False}.items()]

# All named disposition/family decisions are retained, independently of research recency.
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT).decode().splitlines()
explicit_extra={
 'project-state/contributed-document-review-2026-08-14.json',
 'project-state/discovery/bernco-technical-standards-archival-review.json',
 'project-state/discovery/dmd-poster-map-ntmp-archival-review.json',
 'project-state/discovery/go2017-official-master-consolidation-2026-09-16.json',
 'project-state/discovery/inventory-validation-repair-2026-09-09.json',
 'project-state/discovery/municipaldevelopment-agenda-minutes-archive-preparation-2026-09-20.json',
 'project-state/discovery/municipaldevelopment-standard-forms-archive-preparation-2026-09-19.json',
 'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json',
 'project-state/discovery/theory-of-change-review-2026-09-19.json',
 'project-state/discovery/council-documents-topical-cluster-research-2026-09-12.json',
 'project-state/discovery/council-projects-planning-forms-cluster-research-2026-09-13.json',
 'project-state/discovery/facility-environmental-compliance-cluster-research-2026-09-12.json',
 'project-state/discovery/project-procurement-records-cluster-research-2026-09-12.json',
 'project-state/discovery/r-22-38-retained-source-audit-2026-09-06.json',
 'project-state/discovery/r-22-92-retained-source-audit-2026-09-06.json',
 'project-state/discovery/r-23-100-retained-source-audit-2026-09-06.json',
 'project-state/discovery/r-25-117-retained-source-audit-2026-09-06.json',
 'project-state/discovery/r-25-126-retained-source-audit-2026-09-06.json',
 'project-state/inventory-overrides.json',
 'project-state/scoped-source-review-2026-08-04.md',
 'project-state/discovery/unm-cnm-focused-source-scope.json',
 'project-state/discovery/publication-quality-remediation-2026-09-26.json',
 'project-state/discovery/council-closeout-status-2026-09-20.json',
 'project-state/discovery/cabq-legistar-transportation-priority-200-2006-2019-audit.json',
 'project-state/discovery/2014-ms4-family-package-gate-2026-09-18.json',
 'project-state/discovery/energy-water-public-facilities-capital-spending-family-map-2026-09-18.json',
 'project-state/discovery/go2009-bond-version-and-duplicate-review-2026-09-17.json',
 'project-state/discovery/code-enforcement-snapshot-supersession-2026-09-11.json',
 'project-state/discovery/ordinary-second-large-campaign-1993-canonical-correction-2026-09-26.json',
 'project-state/discovery/old-town-quality-correction-2026-09-26/record-decisions.json',
 'project-state/discovery/quality-remediation-first-2026-09-27/review.json',
 'project-state/discovery/planning-publication-lifecycle-authorization-2026-09-26.json',
 'project-state/discovery/council-substitute-bill-enacted-text-reconciliation-2026-09-20.json',
 'project-state/discovery/archive-reconciliation-editorial-resolution-2026-09-17.json',
}
for path in paths:
    if (not path.endswith('.json') and path not in explicit_extra) or path in by_path:
        continue
    named=bool(re.search(r'(?:^|[-/])(decisions?|policy)(?:[-.]|/)|consolidation-manifest|family-package-gate',path))
    if path not in explicit_extra and not named:
        continue
    if any(x in path for x in ('baseline-', 'validation', 'pr-description', 'r2-plan', 'archive-plan',
                               'source-validation', 'r2-validation', 'baseline-owner', 'summary', 'integration')):
        continue
    value=read(path) if path.endswith('.json') else (ROOT/path).read_text(encoding='utf-8-sig')
    gid='decision-'+Path(path).stem[:65]+'-'+hashlib.sha256(path.encode()).hexdigest()[:8]
    cat='active publication architecture' if 'consolidation' in path or 'compilation-decisions' in path else 'active family decision'
    if 'old-town-quality-correction' in path: cat='active owner decision'
    row=add(gid,path,cat,'Preserve the exact recorded family/disposition, canonical/version/duplicate, publication and provenance decisions in this artifact. Saved recommendations and completed-action receipts do not authorize new disposition or external action.',pointers=['/'])
    # Include every substantive normative clause, not a context-selected top-N excerpt.
    row['required_actions'] += [v for p,v in strings(value) if re.search(r'(decision|conclusion|treatment|policy|safeguard|boundary|constraint|prohibit|require|gate|visible_form|packet_policy|edition_treatment)',p.rsplit('/',1)[-1],re.I)
                               and len(v)>35 and not re.search(r'(url|path|artifact|checksum|sha256|processing_notes)',p.rsplit('/',1)[-1],re.I)]
    row['required_actions']=list(dict.fromkeys(row['required_actions']))
    row['settled_decisions']=[{'question_id':'artifact-decision:'+gid,'decision':row['binding_requirement']}]
    if 'go2013-department-set' in path: row['scope']['families']=['go-2013']
    if 'go2013-department-set' in path: row['controlling_artifacts'][0]['binding_pointers']=['/program_book','/department_set','/edition_treatment']
    if 'go2011-bond-version' in path: row['scope']['families']=['go-2011']
    if 'go2009-bond-version' in path: row['scope']['families']=['go-2009']
    if 'dpm-' in path: row['scope']['families']=['dpm-executive-committee']
    if 'dpm-annual-compilations-decisions' in path:
        row['constraints']=[{'subject':'dpm-executive-committee','field':k,'equals':v}
                            for k,v in {'publication_form':'annual_master_pdf','years':[2014,2015,2016,2017,2018],
                                        'preserve_originals':True,'agenda_not_meeting_proof':True}.items()]
    if 'go2017-official-master-consolidation' in path:
        row['scope']['families']=['go-2017']
        row['category']='active publication architecture'
        row['constraints']=[{'subject':'go-2017','field':k,'equals':v} for k,v in
                            {'publication_form':'official_master_pdf','master_count':1,'original_component_count':30,
                             'capital_standalone_component_links':0,'preserve_originals':True}.items()]
    if 'fiber-rulemaking-meeting-records-decision' in path:
        row.update(state='superseded',superseded_by='owner-fiber-correspondence',
                   supersession_evidence={'path':'project-state/discovery/owner-decisions-2026-09-26/authorization.json','pointer':'/decisions/fiber-correspondence'})
        row['category']='explicitly superseded historical decision'
    if 'old-town-quality-correction' in path:
        row['settled_decisions']=[{'question_id':'old-town:four-negative-records','decision':'Four owner-rejected Old Town records stay excluded; assess remaining Planning records; preserve multipart and duplicate relationships.'}]
    if path=='project-state/discovery/publication-quality-remediation-2026-09-26.json':
        row['required_actions']=[value['policy']]
        row['settled_decisions']=[{'question_id':r['id']+':september13-standalone-quality',
                                  'decision':r['prior_status']} for r in value['september_13_reconciliation']
                                 if r['prior_status']=='does not meet standalone standard']

# Standing profiles grant ONLY their explicitly invoked class, not a future campaign invocation.
for path in paths:
    if path.startswith('project-state/campaign-profiles/') and path.endswith('.json'):
        add('authorization-profile-'+Path(path).stem,path,'active storage/external-action authorization',
            'Only an owner invocation activates the exact profile population and unchanged-original archival/background-integration class. No visible content, protected-family, destructive or credential action is authorized.',
            {'operation_classes':['archive','family_review','inventory_disposition','background_integration']},'standing owner-authorized profile')

# Deprecated ledger retirement is explicit, not inferred from dates.
old='project-state/history/AGENT-HANDOFF-legacy-2026-09-16.md'
row=add('workflow-legacy-dual-agent-ledger',old,'explicitly superseded historical decision',
        'Former dual-agent ledger is retired by explicit handoff notice.',{'global':True},pointers=['/text'])
row.update(state='superseded',superseded_by='workflow-handoff-retirement',supersession_evidence={'path':'project-state/AGENT-HANDOFF.md','pointer':'/text'})
row=add('policy-r2-former-10gb','project-state/r2-storage-policy.json','explicitly superseded historical decision',
        'Former 10000000000-byte ceiling was explicitly replaced by owner instruction; historical receipts keep dated limits.',{'global':True},pointers=['/authority'])
row.update(state='superseded',superseded_by='policy-r2-storage',supersession_evidence={'path':'project-state/r2-storage-policy.json','pointer':'/authority'})

# Bind executable global workflow implementation and future artifact standard.
row=next(r for r in entries if r['governance_id']=='policy-durable-task-governance')
for path in ['scripts/project/TaskGovernance.py','scripts/project/Resolve-TaskGovernance.py',
             'scripts/project/Test-TaskGovernance.py','scripts/project/GovernanceLifecycle.py',
             'scripts/project/Invoke-ProjectValidation.ps1','scripts/project/GovernedEntrypoint.py',
             'scripts/project/Assert-TaskGovernance.ps1','project-state/governance/entrypoints.json'] + list(read('project-state/governance/entrypoints.json')['tools']):
    if (ROOT/path).exists():
        row['controlling_artifacts'].append({'path':path,'sha256':file_hash(path),'binding_pointers':['/implementation']})
        by_path.setdefault(path,[]).append(row['governance_id'])

audit=[]
all_paths=sorted(set(paths+list(by_path)))
all_paths=sorted(set(all_paths+[p.relative_to(ROOT).as_posix() for p in (ROOT/'project-state/governance').rglob('*contract-v[123456789].json')]))
for path in all_paths:
    ids=by_path.get(path,[])
    if ids:
        categories=sorted({r['category'] for r in entries if r['governance_id'] in ids})
        classification=categories[0] if len(categories)==1 else 'multiple binding categories'
        rationale='Registered exact continuing policy/decision clauses; dates do not determine precedence. Historical receipts and recommendations outside binding clauses confer no authority.'
    elif path.startswith(('scripts/','layouts/','assets/','static/')):
        classification='historical evidence only / non-binding'
        rationale='Executable implementation/rendering/resource; governing policy is registered separately. No independent owner decision is established by code.'
    elif path.startswith(('content/','research/')) or Path(path).suffix not in ('.json','.md','.txt'):
        classification='historical evidence only / non-binding'
        rationale='Published/source/rendered bytes or binary/log evidence, not project authority.'
    else:
        classification='historical evidence only / non-binding'
        rationale='Research recommendation, source capture, queue/snapshot, completed-action receipt or navigation/resume evidence. Continuing decisions are indexed separately; saved recommendations are evidence, not dispositions or new authorization.'
    hash_value=file_hash(path) if (ROOT/path).is_file() else hashlib.sha256(subprocess.check_output(['git','ls-tree',BASE,path],cwd=ROOT)).hexdigest()
    audit.append({'path':path,'sha256':hash_value,'hash_kind':'normalized-file-bytes' if (ROOT/path).is_file() else 'git-tree-entry', 'classification':classification,
                  'governance_ids':ids,'rationale':rationale})
audit_path='project-state/governance/audit-2026-09-27/artifact-audit.json'
save(audit_path,{'schema_version':1,'baseline_commit':BASE,'method':'Entire tracked baseline enumerated; structured authority clauses classified separately from research/source/snapshot/receipt text. Named files are discovery seeds, never a precedence rule. Explicit exceptions and supersession evidence are reviewable in build_registry.py.',
                 'artifacts':audit,'categories':CATEGORIES+['historical evidence only / non-binding']})
save('project-state/governance-registry.json',{'schema_version':1,'effective_date':'2026-09-27',
     'categories':CATEGORIES,'precedence_rule':'No newest-artifact precedence. Active until explicit authorized supersession.',
     'audit_artifact':audit_path,'audit_sha256':file_hash(audit_path),'entries':sorted(entries,key=lambda r:r['governance_id'])})
print(json.dumps({'entries':len(entries),'active':sum(r['state']=='active' for r in entries),
                  'superseded':sum(r['state']=='superseded' for r in entries),'audited':len(audit)}))
