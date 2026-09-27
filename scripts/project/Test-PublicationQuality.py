"""Actual failure classes and integration guards, including no-write transitions."""
import copy
import importlib.util
import json
import subprocess
from PublicationQuality import ROOT, quality_errors, require_publication_quality, validate_affected_records, finding_id

EVIDENCE = ['project-state/discovery/planning-documents-root-residual-decision-2026-09-20.json']

def positive(title='Substantive short signed legal instrument'):
    return {'id':'quality-fixture','title':title,'status':'validated','publication_quality_decision':{
        'decision':'passes','evidence':EVIDENCE,'assessment':{
            'document_function':'Signed enactment formally establishing a defined Albuquerque public action.',
            'substantive_content':'Operative clauses identify the authorized public action, jurisdiction, date and signatory.',
            'durable_public_usefulness':'Readers can establish the actual authorization and its legal terms from the original instrument.',
            'unique_information':'The signed authorization and operative clauses are not adequately replaced by meeting summaries or informal descriptions.',
            'information_density':'Dense operative legal text; one page contains the entire signed authorization.',
            'rationale':'The operative signed terms provide durable public evidence of the specific authorization, independent of its short length and official provenance.',
            'reviewed_document_content':True,'visual_inspection_completed':True,'series_relationship':'standalone','publication_form':'standalone','page_count':1,'extracted_word_count':180,
            'limited_content_assessment':{'specific_substance':'The operative clauses and signature complete the legal instrument rather than merely announcing a process.','unique_durable_use':'A reader can identify the authorized action and the official signed terms without another document.','why_shortness_is_sufficient':'Legal effect and defined terms are expressed concisely in the complete signed instrument; extra length would not add necessary context.','evidence':EVIDENCE}}}}

def rejected(record, pattern, findings=None):
    errors=quality_errors(record,findings)
    assert any(pattern in e for e in errors), (pattern, errors)

for kind in ('signed legal instrument','substantive parcel map','dense engineering table','concise analytical finding'):
    record=positive(kind)
    record['publication_quality_decision']['assessment']['document_function']='Complete '+kind+' conveying distinct operative information for an Albuquerque public matter.'
    if kind != 'signed legal instrument':
        q=record['publication_quality_decision']['assessment']
        substance={'substantive parcel map':'Parcel boundaries, street labels, scale, legend and an adopted overlay boundary identify exactly where a public regulation applies.',
                   'dense engineering table':'Measured drainage design flows, units, return periods and named local facilities provide compact technical evidence usable without a narrative report.',
                   'concise analytical finding':'A complete formal finding identifies the question, evidence considered, conclusion and the public action recommended by the reviewing body.'}[kind]
        q['substantive_content']=substance;q['unique_information']=substance
        q['limited_content_assessment']['specific_substance']=substance
        q['limited_content_assessment']['unique_durable_use']='The complete '+kind+' records its own substantive result and context, unavailable in the informal page summary.'
        q['limited_content_assessment']['why_shortness_is_sufficient']='The '+kind+' expresses its complete substance compactly; the legend, units or formal finding supply the context necessary for independent use.'
    assert not quality_errors(record), quality_errors(record)
negative=positive();negative['id']='prior-negative'
rejected(negative,'prior negative',{'prior-negative':{'quality_review':{'status':'does not meet standalone standard'}}})
negative['publication_quality_decision']['supersedes_findings']=[{'finding_id':finding_id('prior-negative'),'new_evidence':EVIDENCE,'new_evidence_rationale':'Renewed inspection identifies operative signed clauses absent from the earlier superficial assessment and explicitly reverses that finding.'}]
assert not quality_errors(negative,{'prior-negative':{'finding':'negative'}})
historical=positive('One-page historical regulatory guideline, 1998');rejected(historical,'currentness')
thin=positive();thin['publication_quality_decision']['assessment'].pop('limited_content_assessment')
thin['publication_quality_decision']['assessment']['limited_content_exception']='This official record contains useful public information and merits independent preservation because it is authoritative and clearly relates to a local topic.'
rejected(thin,'limited content')
raw=positive('Official task-force ranking results');raw['publication_quality_decision']['assessment']['engagement_assessment']={'function':'Official engagement chart of participant rankings and vote distributions.','durable_unique_information':'Official charts preserve response data and the number of participating residents.','evidence':EVIDENCE,'substantive_basis':'official_data'}
rejected(raw,'raw engagement')
series=positive();series['publication_quality_decision']['assessment']['series_relationship']='component';rejected(series,'aggregation')
negative=positive();negative['publication_quality_decision']['decision']='excluded_from_publication';rejected(negative,'negative durable')
try:validate_affected_records([{'id':'no-gate-candidate','status':'implemented'}])
except ValueError:pass
else:raise AssertionError('Actual publication candidate escaped the gate')

# Every current visible implementation entrypoint must evaluate actual records.
for path in (ROOT/'scripts/project').glob('Test-*HugoImplementation.py'):
    source=path.read_text(encoding='utf-8')
    assert 'validate_affected_records(' in source or 'validate_completed_implementation(' in source, 'Implementation omits actual-record gate: '+path.name
for name in ('Update-Candidate.ps1','Set-CandidatesByUrl.ps1','Test-Candidate.ps1','Test-ImplementedEvidence.ps1','Test-ImplementedBatch.ps1'):
    assert 'Test-ActualRecordPublicationQuality.ps1' in (ROOT/'scripts/project'/name).read_text()

# Real atomic update path must reject an actual visible-status transition before writing.
real=json.loads((ROOT/'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
candidate=copy.deepcopy(next(r for r in real['candidates'] if r['id']=='src-7de0f5803d442e8f'))
candidate['status']='placement assigned';candidate.pop('publication_quality_decision')
folder=ROOT/'tmp/quality-transition-regression';folder.mkdir(exist_ok=True)
inventory=folder/'inventory.json';requests=folder/'requests.json'
inventory.write_text(json.dumps({'candidates':[candidate],'allowed_statuses':real['allowed_statuses'],'counts':{},'next_pending_id':candidate['id']}))
requests.write_text(json.dumps([{'id':candidate['id'],'changes':{'status':'implemented'}}]))
original=inventory.read_bytes()
result=subprocess.run(['python',str(ROOT/'scripts/project/Update-CandidatesBatch.py'),'--inventory',inventory.relative_to(ROOT).as_posix(),'--requests',requests.relative_to(ROOT).as_posix()],cwd=ROOT,capture_output=True)
assert result.returncode and inventory.read_bytes()==original, 'Ungated actual transition wrote inventory'

spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/project/Audit-VisiblePublicationQuality.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
visible_negative=positive();visible_negative['r2_url']='https://files.abqinfo.com/fixture.pdf';visible_negative['publication_quality_decision']['decision']='excluded_from_publication'
actual=audit.audit({'candidates':[visible_negative]},{visible_negative['r2_url']:{'content/example.md':1}})
assert len(actual['failures'])==1 and not actual['passing_ids'], 'Visible negative decision escaped repository audit'
shared=positive();shared['r2_url']='https://files.abqinfo.com/absent.pdf';shared['source_url']='https://www.cabq.gov/shared-directory/';shared['direct_file_url']='https://www.cabq.gov/shared-directory/original.pdf';shared['file_type']='PDF'
assert not audit.placements(shared,{shared['source_url']:{'content/example.md':1}}), 'Shared provenance hub falsely establishes document visibility'
debt={'failures':[{'id':'legacy','inventory_row_digest':'same','pages':{'a':1},'errors':['unresolved']}]}
audit.enforce_debt(copy.deepcopy(debt),debt)
for mutation in ({'id':'new'},{'id':'legacy','inventory_row_digest':'changed'},{'id':'legacy','inventory_row_digest':'same','pages':{'a':2},'errors':['unresolved']}):
    try:audit.enforce_debt({'failures':[mutation]},debt)
    except AssertionError:pass
    else:raise AssertionError('Quality debt growth escaped')
print('PASS: six publication failure classes; useful short legal/map/table/analytical positives; explicit reversal evidence; actual-record integration and atomic no-write transition; immutable bounded debt and link-count growth guards.')

# A pinned delta alone must not replace the actual-record quality gate.
from QualityCorrectionLifecycle import before, validate_delta, ARTIFACT
from WorkflowStageLifecycle import digest
manifest=json.loads((ROOT/ARTIFACT).read_text(encoding='utf-8'))
prior=before('project-state/master-inventory.json',manifest['baseline_commit'])
current=json.loads((ROOT/'project-state/master-inventory.json').read_text(encoding='utf-8-sig'))
r2=json.loads((ROOT/'project-state/r2-inventory.json').read_text(encoding='utf-8-sig'))
validate_delta(manifest,prior,current,manifest['correction_pages'],manifest['correction_page_sha256'],r2,r2)
bad=copy.deepcopy(current);rid=manifest['planning_publication_ids'][0]
row=next(r for r in bad['candidates'] if r['id']==rid);row.pop('publication_quality_decision')
repinned=copy.deepcopy(manifest);repinned['expected_row_digests'][rid]=digest(row)
try:validate_delta(repinned,prior,bad,manifest['correction_pages'],manifest['correction_page_sha256'],r2,r2)
except ValueError:pass
else:raise AssertionError('Publication delta never called the actual-record gate')
for paths,hashes,after in [(manifest['correction_pages']+['content/unapproved.md'],manifest['correction_page_sha256'],r2),(manifest['correction_pages'],{},r2),(manifest['correction_pages'],manifest['correction_page_sha256'],{})]:
    try:validate_delta(manifest,prior,current,paths,hashes,r2,after)
    except AssertionError:pass
    else:raise AssertionError('Corrected exact-delta guard accepted unauthorized content/hash/R2 mutation')
print('PASS: correction exact-delta negative fixtures; even repinned inventory values cannot omit the actual-record quality gate.')
