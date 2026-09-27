"""Deterministic owner-review implementation, scoped to queue matches and two masters."""
import json, re, sys, hashlib, subprocess, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/project'))
from WorkflowStageLifecycle import digest, canonical_bytes
from PublicationQuality import validate_affected_records
import runpy
auditmod=runpy.run_path(str(ROOT/'scripts/project/Audit-VisiblePublicationQuality.py'))
BASE='940e3032d96f868eed8cff7c3deeaf1c556f50a2';PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
QUEUE='project-state/discovery/publication-quality-remediation-2026-09-26.json'
def before(p):return json.loads(subprocess.check_output(['git','show',BASE+':'+p]).decode('utf-8-sig'))
def save(p,v): (ROOT/p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
inv=before('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};oldq=before(QUEUE)
targets=json.loads((OUT/'preparation.json').read_text(encoding='utf-8'))['capital_candidate_ids']
masters=['src-8c5d2888cc22b991','src-cb8cd727e3ca1fde'];changed=targets+masters
measure={r['id']:r for r in json.loads((OUT/'public-byte-measurements.json').read_text(encoding='utf-8'))}
group={y:[i for i in targets if ('2011' in rows[i]['title'] if y=='2011' else '2009' in rows[i]['title'] if y=='2009' else i in ['src-040d6e306c1c448c','src-047e8956baad212d'] if y=='2013' else i=='src-a58b458f5d0f5284')] for y in ['2004','2009','2011','2013']}
def link(i,label):return f"[{label}]({rows[i]['r2_url']}) · [City original]({rows[i]['direct_file_url']})"
capital='content/city-data/capital-spending.md'
pages={p for i in targets for p in next(r for r in oldq['september_13_reconciliation'] if r['id']==i)['current_visible_pages']}
texts={p:subprocess.check_output(['git','show',BASE+':'+p]).decode('utf-8-sig').replace('\r\n','\n') for p in pages}
removed=[]
def remove_entry(p,i):
    text=texts[p];blocks=list(re.finditer(r'^- \[.*?(?=^- \[|^#{1,6} |\Z)',text,re.M|re.S))
    matches=[m for m in blocks if rows[i]['r2_url'] in m.group() and rows[i]['r2_url'] in m.group().splitlines()[0]]
    assert len(matches)==1,(p,i,len(matches))
    m=matches[0];removed.append({'page':p,'id':i,'original_entry':m.group()});texts[p]=text[:m.start()]+text[m.end():]
for i in targets:
    for p in next(r for r in oldq['september_13_reconciliation'] if r['id']==i)['current_visible_pages']:remove_entry(p,i)
# Relocate only the required EPC master, preserving its archive/source pairing.
remove_entry(capital,'src-cb8cd727e3ca1fde')

text2004="""The 2004 street program connects a proposed borrowing question to a ten-page project list totaling $52,514,950. The list covers paving and street reconstruction, bridges, intersections, sidewalks, bicycle and pedestrian improvements, traffic management, and named corridors including Paseo del Norte, Unser Boulevard and McMahon Boulevard. It identifies project scopes and intended funding, allowing the borrowing purpose to be read against specific infrastructure proposals. The related amendment resolution records a distinct Council programming action; the planning-process summary explains the review framework.

The question placed before voters on November 2, 2004 asked whether the City should issue those bonds. The ballot wording is component evidence, not a record of the election result, completed construction or actual expenditure.

"""+"Ballot component: "+link('src-a58b458f5d0f5284','November 2, 2004 question')+'\n\n'
marker='- [2004 Street General Obligation Bond Project Titles, Amounts, and Scopes'
idx=texts[capital].index(marker);texts[capital]=texts[capital][:idx]+text2004+texts[capital][idx:]
texts[capital]=texts[capital].replace('The related 2004 streets records remain separate.','The related 2004 street program below connects the project list, ballot wording and governing context.')

text2009="""#### Public Safety and Community Capital Components, 2009–2017

The 2009 scope sheets and 2009–2017 schedules describe different layers of capital planning. The Police scope assigns $5.7 million to Sixth Area Command Phase II and marked vehicles; its schedule places those projects alongside later-cycle facility work. The Fire scope assigns $2.5 million to apparatus and station rehabilitation, while the multi-cycle schedule includes land for Station 9 and renovation of Station 2. Those scheduled later-cycle items are not additional 2009 expenditures. The public-safety authorization sheet also identifies district facility work and public art within its $8.444 million purpose total.

Family and Community Services lists $14.5 million for centers, renovations, storage and vehicles. The broader $22.736 million senior/family/community authorization adds senior-center and district improvements, so it overlaps that departmental scope without being an identical document. The $5.101 million library sheet identifies materials, automation, repairs, renovation and district libraries. The Council neighborhood schedule supplies district-level project categories across bond-cycle columns; it is not a ledger of completed projects. The Police and Fire schedule files also carry appended Council neighborhood rows; those overlapping rows are not additional Police or Fire allocations. Together these components explain how department requests and broad bond purposes relate. The allocation chart and citywide totals elsewhere in this annual section provide the wider program context.

These are historical scope, funding-schedule and authorization-purpose records. Their amounts describe planned or authorized purposes, not proof of ultimate spending, and the source folder alone does not establish election results or adoption of every later schedule.

| Program evidence | Preserved originals |
|---|---|
"""
for label,items in [('Police scope and multi-cycle schedule',[('src-5603714dac7351ba','2009 scope'),('src-535234f371b3922c','2009–2017 schedule')]),('Fire scope and multi-cycle schedule',[('src-e69e9150b150bc1a','2009 scope'),('src-b7ef66c741b8a886','2009–2017 schedule')]),('Public-safety bond purpose',[('src-b049c4df2812749b','authorization sheet')]),('Community and senior facilities',[('src-0352ae60169eac10','department scope'),('src-7567c5f27fceba0a','broader authorization sheet')]),('Libraries',[('src-768a6855fcfaf443','authorization sheet')]),('Council neighborhood set-asides',[('src-cb27c408e8c26a66','2009–2017 district schedule')])]:
    text2009+='| '+label+' | '+'; '.join(link(i,l) for i,l in items)+' |\n'
text2009+='\n'
heading='### 2009 General Obligation Bond Program\n\n';texts[capital]=texts[capital].replace(heading,heading+text2009,1)

text2011="""#### Department Scopes and Initial Versions, 2011–2019

The City’s 2011 GO directory preserves department scope sheets, a citywide funding table and labeled initial versions. Read the scopes as proposed work within a program cycle and the schedules as allocations across 2011, 2013, 2015, 2017 and 2019, rather than construction deadlines or spending accounts. The totals table reports $727.29 million across those cycles; it does not establish that this amount was borrowed or spent.

Several initial/published differences materially affect the program history. Affordable Housing retains a $10 million amount, but the initial sheet includes a North Fourth Street acquisition allocation absent from the shorter published wording. Family and Community Services changes from $7.5 million to $8.8 million, with a changed center-project mix. Fire changes from $4.8 million to $4.625 million, with the initial Station 13 renovation absent from the published scope. Planning changes from $6.55 million to $3 million and changes its redevelopment-project mix. These are distinct editions; the labels and chronology do not establish final approval or supersession.

The other components show how the program would support City buildings, parking, vehicles, environmental monitoring, senior-center renovation, transit fleet and facility work, police vehicles and information systems. The initial Streets scope and schedule connect named road projects with multiple funding cycles; the Finance, Planning and Fire initial schedules preserve department-level context. The table below keeps the originals available as evidence for this program comparison without giving each fragment a separate descriptive listing. Remaining scope and schedule records on this page complement this selected family; this is not a complete approved-program book. The October 2010 EPC records below belong to a separate preliminary source collection.

| Department or program layer | Published-directory evidence | Labeled initial evidence |
|---|---|---|
"""
table=[('Citywide totals',['src-2746069f062780cf'],[]),('Affordable Housing',['src-54665bf864159096'],['src-25501032bfbfa682']),('Family and Community Services',['src-352694313c3e5710'],['src-b08cdbd2624ad1a0']),('Fire',['src-db9fefd23083da69'],['src-e6ca25d4cfa80752','src-a547a0278fb86fb9']),('Planning',['src-b7f0628556085641'],['src-89b36d5577443f99','src-c9af414f77032660']),('Streets',[],['src-be70a79a59ae0915','src-a31943aca401c7f0']),('Finance and Administrative Services',[],['src-542056c326cf2578']),('City Facilities, CIP and Parking',['src-2ed981e6df5e99d2'],[]),('Environmental Health',['src-4bafa6f452f2f586'],[]),('Senior Affairs',['src-b90b07ac62c4f7fd','src-4cd84ecef3756fb0'],[]),('ABQ RIDE Transit',['src-b37593a011f57fae'],[]),('Police',['src-f74d655ffb05fd08'],[])]
for label,pub,initial in table:
    def cells(ids):return '; '.join(link(i,'totals' if 'Totals' in rows[i]['title'] else 'schedule' if 'Schedule' in rows[i]['title'] else 'scope') for i in ids) or '—'
    text2011+='| '+label+' | '+cells(pub)+' | '+cells(initial)+' |\n'
text2011+='\n'
heading='### 2011 Published Scope and Version Records\n\n';texts[capital]=texts[capital].replace(heading,heading+text2011,1)

text2013="""### 2013–2022 EPC Program and Related Summary

The November 2012 Environmental Planning Commission program book is the broad historical record for the 2013 bond cycle: it brings together selection criteria, department scopes, biennial funding schedules, maps, enterprise-fund and impact-fee context, and governing legislation. It records the EPC planning stage, not an enacted or voter-approved final program. Its City Facilities/CIP/Parking section (printed pages 37–39, PDF pages 40–42) already contains the $1.3 million scope for vehicles, building rehabilitation, parking, Plaza del Sol, security, roofs and low-flow fixtures; a second standalone DMD scope entry would repeat that substance.

The separately published two-page 2013 summary is useful as a comparison component because its allocations differ from the EPC book—for example, the 2013 Streets column lists $56.19 million rather than $33 million. The preserved evidence does not establish this table’s approval stage or rank it as a final successor. Compare the editions as historical planning records; do not combine their allocations or treat them as actual expenditures.

"""+ '- '+link('src-cb8cd727e3ca1fde','2013–2022 Decade Plan and 2013 GO Program: EPC-stage book')+'\n\n'+'Comparison component: '+link('src-040d6e306c1c448c','separate 2013 summary table; approval stage unestablished')+'\n\n'
heading='### Complete Program Books\n\n';texts[capital]=texts[capital].replace(heading,text2013+heading,1)

cross={
'content/city-data/public-safety-data.md':('## Fire and Emergency Response\n\n','The [2009 capital-program family](/city-data/capital-spending/#public-safety-and-community-capital-components-20092017) explains Police and Fire scopes, later-cycle schedules and the public-safety authorization purpose together. The [2011 department/version family](/city-data/capital-spending/#department-scopes-and-initial-versions-20112019) places Fire and Police projects in their program context and distinguishes the initial Fire scope from the published edition. These records describe capital purposes and planned allocations, not completed work or actual expenditures.\n\n'),
'content/public-works/city-facilities.md':('## Historical Capital Programming\n\n','The [2011 department/version family](/city-data/capital-spending/#department-scopes-and-initial-versions-20112019) explains the published City Facilities, CIP and Parking scope alongside the other department records: vehicles, building rehabilitation, Plaza del Sol, security, roofs, water efficiency and parking. Its program amounts do not establish actual spending.\n\n'),
'content/transportation/transportation-plans.md':('## Historical Capital Programming\n\n','The [2004 street-program record](/city-data/capital-spending/#20032004-general-obligation-bond-program) connects the ten-page project list with the November 2 ballot question and programming context. The question asked permission to issue $52,514,950; it does not establish the election result or completed street improvements.\n\n'),
'content/transportation/transit/abq-ride.md':('## Facilities and Fleet Planning History\n\n','The [2011 department/version family](/city-data/capital-spending/#department-scopes-and-initial-versions-20112019) includes ABQ RIDE’s proposed $6.2 million scope for vehicles, park-and-ride facilities, technology, facility rehabilitation, maintenance equipment and stops, alongside the wider capital-program context. These are scope allocations, not evidence of final spending.\n\n'),
'content/development-land-use/redevelopment-plans.md':('## Historical Capital Programming\n\n','The [2011 department/version family](/city-data/capital-spending/#department-scopes-and-initial-versions-20112019) compares the Planning scope editions and their redevelopment-project mix, including the change from the $6.55 million initial scope to the $3 million published scope. It preserves both versions without treating either as final approval or actual expenditure.\n\n')}
for p,(marker,prose) in cross.items():
    if marker not in texts[p]:
        # Retain the actual existing page heading when its level differs.
        matching=re.search(r'^#{2,4} (?:Historical Capital Programming|Facilities and Fleet Planning History)\n\n',texts[p],re.M)
        assert matching,(p,marker)
        marker=matching.group()
    texts[p]=texts[p].replace(marker,marker+prose,1)
for p,t in texts.items():(ROOT/p).write_text(t,encoding='utf-8')

families=[]
for year,prose,anchor,master in [('2004',text2004,'20032004-general-obligation-bond-program',masters[0]),('2009',text2009,'public-safety-and-community-capital-components-20092017',None),('2011',text2011,'department-scopes-and-initial-versions-20112019',None),('2013',text2013,'20132022-epc-program-and-related-summary',masters[1])]:
    famids=group[year]+([master] if master else [])
    families.append({'id':master or 'go-capital-family-'+year,'year':year,'page':capital,'anchor':anchor,'component_ids':group[year],'master_id':master,'presentation_text':prose,'page_count':sum(measure[i]['page_count'] for i in famids),'extracted_word_count':sum(measure[i]['extracted_word_count'] for i in famids)})
evidence=[PREFIX+'review.json',PREFIX+'public-byte-measurements.json',PREFIX+'candidate-reconciliation.json']
save(PREFIX+'review.json',{'families':families,'state':'reviewed_family_decisions_before_atomic_inventory_application'})
def decision(i,f,form):
    a={'document_function':f['presentation_text'],'substantive_content':f['presentation_text'],'durable_public_usefulness':'Compare specific Albuquerque capital-project purposes, planning stages and bond cycles within the '+f['year']+' family.','information_density':'Measured original pages and words are recorded separately; sparse components contribute only their specific scope, table or instrument evidence to the substantive family explanation.','unique_information':rows[i]['title']+' supplies a program-stage component; repeated substance is represented by the required master rather than a second listing.','rationale':'Readers gain a coherent account of Albuquerque capital priorities and material version differences by connecting project scopes with cycle schedules and governing context. This assessed presentation preserves specific useful facts and expressly limits approval and expenditure inferences; consolidation alone is not the basis for passing.','standalone_public_value':'low' if i in targets else 'substantive','publication_form':form,'reviewed_document_content':True,'visual_inspection_completed':True,'series_relationship':'component','page_count':measure[i]['page_count'],'extracted_word_count':measure[i]['extracted_word_count'],'aggregation_decision':{'form':form,'evidence':evidence,'rationale':f['presentation_text']}}
    supersedes=[]
    if i in targets:
        supersedes.append({'finding_id':'post-pr132-2026-09-13:'+i,'new_evidence_rationale':'Original standalone failure remains settled and preserved. Its presentation is replaced by the reviewed '+f['year']+' family; component usefulness does not reverse the historical standalone judgment.','new_evidence':evidence})
    return {'decision':'passes','assessed_at':'2026-09-27T00:00:00Z','evidence':evidence,'assessment':a,'supersedes_findings':supersedes}
for i in changed:
    f=next(f for f in families if i in f['component_ids'] or i==f['master_id'])
    rows[i]['publication_quality_decision']=decision(i,f,'consolidated_master' if i in masters else 'grouped_component')
    rows[i]['publication_relationship']={'family_id':f['id'],'master_id':f['master_id'],'component_ids':f['component_ids'] if i in masters else None,'form':'consolidated_master' if i in masters else 'substantively_represented_by_master' if i=='src-047e8956baad212d' else 'grouped_component','canonical_page':capital,'anchor':f['anchor'],'version_status':'distinct initial edition; final/adopted precedence not established' if 'Initial Version' in rows[i]['title'] else 'historical program-stage evidence; no final expenditure inference'}
    rows[i]['scope_assessment']={'assessed_at':'2026-09-27T00:00:00Z','geographic_institutional_scope':'City of Albuquerque capital improvement and general-obligation bond program, '+f['year']+' cycle.','specific_albuquerque_connection':rows[i]['title']+' identifies City department capital purposes, projects or funding allocations.','abqinfo_public_information_value':'Explains Albuquerque infrastructure priorities, proposed capital funding and program/version relationships in the reviewed family presentation.','general_context_exclusion_test':'The evidence concerns specific Albuquerque capital allocations and public facilities, rather than statewide applicability, generic templates or incidental location references.','final_scope_decision':'passes_both_gates','substantive_rationale':'This record materially documents Albuquerque municipal infrastructure and public investment decisions. Its meaningful public use is assessed within the specific historical program family while the settled weak standalone judgment remains preserved.'}
    rows[i]['processing_notes']=rows[i].get('processing_notes',[])+['GO/capital standalone remediation: '+PREFIX+'review.json; historical negative finding retained; grouped component/master presentation only; original archive/source bytes and status unchanged.']
    rows[i]['updated_at']='2026-09-27T00:00:00Z'
    rows[i]['implementation_location']=capital
    rows[i]['implementation_locations']=[capital]
    rows[i]['cross_listing_approved']=False
validate_affected_records([rows[i] for i in changed])
presentation=[]
for f in families:
    seed=copy.deepcopy(rows[f['master_id'] or f['component_ids'][0]]);seed['id']=f['id'];seed['title']=f['year']+' Albuquerque GO capital-program family presentation'
    seed['quality_assessment']=None;seed['publication_quality_decision']=copy.deepcopy(seed['publication_quality_decision']);a=seed['publication_quality_decision']['assessment'];a.update({'publication_form':'consolidated_master','standalone_public_value':'substantive','page_count':f['page_count'],'extracted_word_count':f['extracted_word_count']});a['aggregation_decision']['form']='consolidated_master';presentation.append(seed)
validate_affected_records(presentation)
save('project-state/master-inventory.json',inv)
result=auditmod['audit'](inv,auditmod['visible_links']())
newq=copy.deepcopy(oldq);newq['failures']=result['failures'];newq['passing_ids']=result['passing_ids']
rec={r['id']:r for r in result['september_13_reconciliation']}
for r in newq['september_13_reconciliation']:
    if r['id'] in targets:
        extra=r.get('later_related_evidence');r.update(rec[r['id']]);r['later_related_evidence']=extra
oldfails={r['id']:r for r in oldq['failures']};newfails={r['id']:r for r in newq['failures']}
assert all(r==oldfails[i] for i,r in newfails.items()),'Unrelated debt changed'
assert oldfails.keys()-newfails.keys()==set(changed),(oldfails.keys()-newfails.keys(),set(changed))
save(QUEUE,newq)
md=Path(ROOT/QUEUE).with_suffix('.md');baseline=subprocess.check_output(['git','show',BASE+':'+md.relative_to(ROOT).as_posix()]).decode('utf-8')
md.write_text(baseline+'\n## GO/capital remediation owner-review delta, September 27\n\n32 queue-matched capital negatives (owner requested the 31/32 discrepancy be flagged in the PR) and two required existing masters assessed. Debt: 1608 → 1574. Unresolved September 13 findings: 42 → 10. Seven questionable and three unrelated negative findings are unchanged. Original negative findings and queue baseline remain preserved under '+PREFIX+'. No R2 mutation.\n',encoding='utf-8')
findings={r['candidate_id']:r for r in before('project-state/discovery/post-pr132-content-quality-audit-2026-09-13.json')['documents']}
save(PREFIX+'review.json',{'families':families,'presentation_records':presentation,'preserved_negative_findings':{i:findings[i] for i in targets},'visual_review':'All 49 component pages and all ten 2004 master pages rendered and inspected in contact sheets. EPC cover, contents, allocation pages and printed pages 37–39 inspected; scanned master has zero extractable words but substantive visual/tabular content.','2013_relationship':'DMD scope projects/amounts substantively match EPC printed pages 38–39 (PDF 41–42), with different pagination; no byte-duplicate claim. Separate totals table differs (2013 Streets 56.19m vs EPC 33m); no finality ranking.','2011_relationship':'All twenty targets are members of the prepared 46-component published-directory compilation, not the 21-component October 2010 EPC compilation. No evidence establishes final/adopted precedence.','removed_entries':removed})
save(PREFIX+'implementation.json',{'baseline_commit':BASE,'target_ids':targets,'requested_target_count':31,'actual_queue_matched_count':32,'owner_count_question_pending':True,'changed_inventory_ids':changed,'master_ids':masters,'debt_resolved_ids':changed,'debt_before':1608,'debt_after':1574,'september_13_before':42,'september_13_after':10,'changed_pages':sorted(pages),'page_sha256':{p:hashlib.sha256(canonical_bytes((ROOT/p).read_bytes())).hexdigest() for p in sorted(pages)},'expected_row_digests':{i:digest(rows[i]) for i in changed},'families':families,'r2_mutation':False,'added_r2_bytes':0})
print('Implemented 32 queue-matched components and two required masters across six pages; debt 1608->1574; September 13 42->10; owner count question remains in PR.')
