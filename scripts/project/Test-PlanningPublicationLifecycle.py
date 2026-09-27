"""Negative fixtures prove that historical sealing cannot hide later mutations."""
import copy
from PlanningPublicationLifecycle import validate_delta, guard_current_delta, validate_queue_delta
from WorkflowStageLifecycle import digest

assessment={'final_scope_decision':'passes_both_gates'}
prior={'candidates':[{'id':'one','status':'placement assigned','scope_assessment':assessment,'source_url':'official'},{'id':'other','status':'validated'}]}
current=copy.deepcopy(prior);current['candidates'][0]['status']='implemented'
pages=['content/'+str(n)+'.md' for n in range(6)]; hashes={p:'unchanged' for p in pages}
data={'implemented_inventory_ids':['one'],'changed_pages':pages,'page_sha256':hashes,'expected_row_digests':{'one':digest(current['candidates'][0])}}
validate_delta(data,prior,current,pages,hashes,{}, {})
cases=[]
unauthorized=copy.deepcopy(current);unauthorized['candidates'][1]['status']='implemented';cases.append((unauthorized,pages,hashes,{}))
provenance=copy.deepcopy(current);provenance['candidates'][0]['source_url']='replacement';cases.append((provenance,pages,hashes,{}))
cases.append((current,pages+['content/unapproved.md'],hashes,{}))
altered=hashes.copy();altered[pages[0]]='tampered';cases.append((current,pages,altered,{}))
cases.append((current,pages,hashes,{'objects':['unexpected']}))
altered_row=copy.deepcopy(current);altered_row['candidates'][0]['description']='unapproved';cases.append((altered_row,pages,hashes,{}))
duplicate=copy.deepcopy(current);duplicate['candidates'].append(duplicate['candidates'][0]);cases.append((duplicate,pages,hashes,{}))
replaced=pages.copy();replaced[-1]='content/unapproved.md';cases.append((current,replaced,hashes,{}))
metadata=copy.deepcopy(current);metadata['schema_version']='changed';cases.append((metadata,pages,hashes,{}))
for row,paths,values,r2 in cases:
    try: validate_delta(data,prior,row,paths,values,{},r2)
    except AssertionError: pass
    else: raise AssertionError('Unauthorized mutation escaped the current-stage guard')
guard_current_delta()
inventory={'candidates':[{'id':'one','source_url':'new','proposed_canonical_page':'page'}]}
oldq={'records':[{'source_url':'old','audit_status':'crawled'}],'allowed_statuses':['crawled','pending descendant crawl'],'counts':{'crawled':1,'pending descendant crawl':0}}
newq=copy.deepcopy(oldq);newq['records'].append({'source_url':'new','candidate_id':'one','canonical_page':'page','audit_status':'pending descendant crawl','crawl_output':None,'discovered_documents':0,'archived_documents':0});newq['counts']['pending descendant crawl']=1
validate_queue_delta(data,oldq,newq,inventory)
for kind in ('history','unknown','false_completion'):
    bad=copy.deepcopy(newq)
    if kind=='history': bad['records'][0]['audit_status']='pending descendant crawl'
    elif kind=='unknown': bad['records'][-1]['source_url']='unapproved'
    else: bad['records'][-1]['audit_status']='crawled'
    try: validate_queue_delta(data,oldq,bad,inventory)
    except AssertionError: pass
    else: raise AssertionError('Retained-source queue accepted '+kind)
print('PASS: nine negative fixtures reject unrelated rows, provenance, unknown or replaced pages, altered page hashes, R2 mutations, unapproved row values, duplicate rows and top-level metadata; actual current delta passes.')
print('PASS: three queue fixtures reject rewritten historical audits, unknown sources and false completion; only twelve pending Planning source roots added.')
