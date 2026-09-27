"""Negative fixtures prove that historical sealing cannot hide later mutations."""
import copy
from PlanningPublicationLifecycle import validate_delta, guard_current_delta

assessment={'final_scope_decision':'passes_both_gates'}
prior={'candidates':[{'id':'one','status':'placement assigned','scope_assessment':assessment,'source_url':'official'},{'id':'other','status':'validated'}]}
current=copy.deepcopy(prior);current['candidates'][0]['status']='implemented'
pages=['content/'+str(n)+'.md' for n in range(6)]; hashes={p:'unchanged' for p in pages}
data={'implemented_inventory_ids':['one'],'changed_pages':pages,'page_sha256':hashes}
validate_delta(data,prior,current,pages,hashes,{}, {})
cases=[]
unauthorized=copy.deepcopy(current);unauthorized['candidates'][1]['status']='implemented';cases.append((unauthorized,pages,hashes,{}))
provenance=copy.deepcopy(current);provenance['candidates'][0]['source_url']='replacement';cases.append((provenance,pages,hashes,{}))
cases.append((current,pages+['content/unapproved.md'],hashes,{}))
altered=hashes.copy();altered[pages[0]]='tampered';cases.append((current,pages,altered,{}))
cases.append((current,pages,hashes,{'objects':['unexpected']}))
for row,paths,values,r2 in cases:
    try: validate_delta(data,prior,row,paths,values,{},r2)
    except AssertionError: pass
    else: raise AssertionError('Unauthorized mutation escaped the current-stage guard')
guard_current_delta()
print('PASS: historical seals reject unrelated row transitions, changed provenance, unauthorized content, altered approved pages and R2 mutations; actual current delta passes.')
