"""Durable exact-population setup for Central Avenue provenance research."""
import json
import sys
from pathlib import Path
import subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent))
from TaskGovernance import digest, file_hash, load, write_once

ROOT = Path(__file__).resolve().parents[2]
TASK = 'central-station-area-family-resolution-2026-10-04'
BASE = 'project-state/governance/' + TASK
IDS = ['src-c1d5a2b0b33b331a','src-5f3ea18d2262dd4e','src-80ee860e3cfa60bf','src-bad7cd0818045625','src-2641b5b13214d7ee','src-5ade756c56baac45','src-ed916e54f80ece6f','src-863e82803d9e7cac','src-c070ab7e5a4a2622','src-2bbfb64ecf6455b3','src-d7b006f3aceaa405','src-61107c696c0e35b5','src-e0748ccf7ebc1a77']

def save(path, value):
    (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def refresh():
    import OwnerResources20261004 as S
    paths=[p.relative_to(ROOT).as_posix() for p in (ROOT/BASE).rglob('*') if p.is_file() and p.name!='implementation.json']
    S.audit(paths+['project-state/master-inventory.json','project-state/CURRENT.md','project-state/checkpoint.json','project-state/ordinary-queue-current.json','scripts/project/CentralStationAreaFamilyResolution.py','project-state/discovery/consolidated-human-review-queue.json','project-state/discovery/consolidated-human-review-queue.md'])
    n=max(int(p.stem.split('-v')[1]) for p in (ROOT/BASE).glob('contract-v*.json'))+1
    contract=BASE+f'/contract-v{n}.json'
    versions=list((ROOT/BASE).glob('population-v*.json'))
    pop=max(versions,key=lambda p:int(p.stem.split('-v')[1])).relative_to(ROOT).as_posix() if versions else BASE+'/population.json'
    subprocess.run([sys.executable,'scripts/project/Resolve-TaskGovernance.py','resolve','--population',pop,'--output',contract],check=True,stdout=subprocess.DEVNULL)
    c=load(contract); p=load(BASE+'/implementation.json')
    p.update(contract=contract,contract_sha256=file_hash(contract),population_sha256=c['population_sha256'],respected_governance_ids=c['governance_ids'])
    for e in p['events']:e['governance_ids']=c['governance_ids']
    save(BASE+'/implementation.json',p)
    save('project-state/governance/active-task.json',dict(population=pop,contract=contract,contract_sha256=file_hash(contract),implementation=BASE+'/implementation.json',state='in_progress'))
    print(contract)

def history():
    sources=['project-state/near-complete-review-decisions-2026-08-20.json','project-state/near-complete-review-archive-plan-2026-08-20.json','project-state/near-complete-review-public-validation-2026-08-20.json','project-state/discovery/codex-human-review-followup-queue.json']
    sources += [p.relative_to(ROOT).as_posix() for p in (ROOT/'project-state/discovery/background-followup-2026-09-26').glob('*.json')]
    sources += [a[0] for a in load(BASE+'/contract-v1.json')['controlling_artifacts'] if a[0].startswith('project-state/discovery/')]
    out=[]
    def selected(v):
        result=[]
        if isinstance(v,dict):
            if any(i in json.dumps(v,ensure_ascii=False) for i in IDS) and (any(v.get(k) in IDS for k in ['id','candidate_id','document_id']) or any(k in v for k in ['family_id','family'])):
                return [v]
            for x in v.values():result+=selected(x)
        elif isinstance(v,list):
            for x in v:result+=selected(x)
        return result
    for path in sorted(set(sources)):
        v=load(path); matches=selected(v)
        out.append(dict(path=path,sha256=file_hash(path),matches=matches))
    save(BASE+'/existing-evidence.json',out)
    for x in out:
        if x['matches']:print(x['path'],json.dumps(x['matches'],ensure_ascii=False)[:12000])

def inspect():
    import hashlib
    sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'))
    import pymupdf
    evidence=[]
    for x in load(BASE+'/starting-state.json')['rows']:
        r=x['row'];p=ROOT/r['local_path'];data=p.read_bytes()
        assert len(data)==r['size_bytes'] and hashlib.sha256(data).hexdigest()==r['checksum_sha256']
        with pymupdf.open(p) as d:
            texts=[page.get_text() for page in d]
            e=dict(id=r['id'],sha256=r['checksum_sha256'],size_bytes=len(data),pages=len(d),words=len(' '.join(texts).split()),metadata=d.metadata,first_pages=texts[:3],last_pages=texts[-2:],uri_links=[link['uri'] for page in d for link in page.get_links() if 'uri' in link])
            (ROOT/BASE/(r['id']+'.txt')).write_text('\n\f\n'.join(texts),encoding='utf8')
            d[0].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(ROOT/BASE/(r['id']+'.png'))
            evidence.append(e)
            print(json.dumps(e,ensure_ascii=False))
    save(BASE+'/pdf-inspection.json',evidence)

def fetch():
    import hashlib, urllib.request, concurrent.futures
    from datetime import datetime, timezone
    from html.parser import HTMLParser
    from urllib.parse import urljoin
    tasks=load(BASE+'/'+sys.argv[2])
    def one(t):
        e=dict(t,retrieved_at=datetime.now(timezone.utc).isoformat())
        try:
            with urllib.request.urlopen(urllib.request.Request(t['url'],headers={'User-Agent':'Mozilla/5.0 (ABQInfo provenance research)'}),timeout=40) as r:
                data=r.read(150000001); assert len(data)<150000001
                e.update(http_status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            suffix='pdf' if data.startswith(b'%PDF') else 'html'
            path=BASE+f"/evidence-{t['n']}.{suffix}"
            (ROOT/path).write_bytes(data);e['witness']=path
            if suffix=='pdf':
                sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
                with pymupdf.open(stream=data,filetype='pdf') as d:
                    text='\n\f\n'.join(p.get_text() for p in d);e.update(pages=len(d),words=len(text.split()),metadata=d.metadata)
                    (ROOT/BASE/f"evidence-{t['n']}.txt").write_text(text,encoding='utf8')
                    d[0].get_pixmap().save(ROOT/BASE/f"evidence-{t['n']}.png")
            else:
                class Links(HTMLParser):
                    def __init__(self): super().__init__();self.links=[]
                    def handle_starttag(self,tag,attrs):
                        if tag=='a':
                            a=dict(attrs)
                            if 'href' in a:self.links.append(urljoin(e['final_url'],a['href']))
                p=Links();p.feed(data.decode('utf8',errors='replace'));e['links']=p.links
        except Exception as error:e['error']=str(error)
        return e
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for e in pool.map(one,tasks):
            out.append(e);save(BASE+'/'+sys.argv[3],out);print(e['n'],e.get('http_status'),e.get('pages'),e.get('size_bytes'),e.get('error'),flush=True)

def compare():
    import re,difflib,hashlib
    sys.path.insert(0,str(ROOT/'tmp/pgs-pdf-deps'));import pymupdf
    combined=pymupdf.open(ROOT/BASE/'evidence-3.pdf')
    rows={x['id']:x['row'] for x in load(BASE+'/starting-state.json')['rows']}
    def norm(text):
        text=text.replace('DRAFT FOR PUBLIC COMMENT','').replace('DRAFT FOR COMMENT','').replace('\u00ad','')
        return re.findall(r'\w+|[^\w\s]',text)
    offset=0;out=[]
    for rid in IDS[:11]:
        with pymupdf.open(ROOT/rows[rid]['local_path']) as d:
            pages=[]
            for i,p in enumerate(d):
                old=norm(p.get_text());new=norm(combined[offset+i].get_text())
                changes=[]
                for tag,a,b,c,e in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
                    if tag!='equal':changes.append(dict(kind=tag,old=' '.join(old[a:b]),new=' '.join(new[c:e])))
                pages.append(dict(local_page=i+1,official_2018_page=offset+i+1,equal_after_draft_label_normalization=old==new,changes=changes))
            out.append(dict(id=rid,pages=len(d),official_page_start=offset+1,official_page_end=offset+len(d),unchanged_text_pages=sum(p['equal_after_draft_label_normalization'] for p in pages),page_comparisons=pages))
            offset+=len(d)
    assert offset==len(combined)==237
    save(BASE+'/evidence-52.json',dict(method='Every page compared in original order; remove public-comment labels, soft hyphens and whitespace only; retain all substantive wording, numbers and punctuation.',official_document=load(BASE+'/evidence-42.json'),records=out,infrastructure_absent_from_combined=True))
    for r in out:
        print(r['id'],r['unchanged_text_pages'],'/',r['pages'])
        for p in r['page_comparisons']:
            if p['changes']:print('PAGE',p['local_page'],json.dumps(p['changes'],ensure_ascii=False)[:4000])

def setup_authority():
    import OwnerResources20261004 as S
    pop=load(BASE+'/population-v2.json')
    text='Current user authorizes a new governed background provenance/family-resolution review for exactly the thirteen Central Avenue IDs in this population: deep original-PDF and authoritative-source research, family/finality and current mission/quality findings, evidence-based background inventory dispositions, deterministic accounting and complete validation. No visitor-visible changes, new population, R2 upload/deletion/overwrite/replacement, or owner preference as proof of provenance. Clean background-only integration into main and synchronization of chatgpt/planning-snapshot are explicitly authorized. Preserve all original bytes, provenance, prior source/R2 history and settled governance; register any new binding decision with exact evidence.'
    write_once(BASE+'/authority.json',dict(authority='Explicit current user instruction dated 2026-10-04',candidate_ids=IDS,instruction=text))
    S.bind(BASE+'/authority.json','owner-'+TASK,text,dict(candidate_ids=IDS,task_ids=[TASK]))
    r=load('project-state/governance-registry.json')
    row=next(x for x in r['entries'] if x['governance_id']=='owner-'+TASK)
    row['authority']='Explicit current user Central Avenue family-resolution instruction dated 2026-10-04'
    save('project-state/governance-registry.json',r)
    stages=load('project-state/workflow-stage-lifecycle.json')
    assert stages['stages'][-1]['id']=='pr210-postmerge-closeout-2026-10-04'
    stages['stages'][-1]['end_commit']=pop['baseline_commit']
    stages['stages'].append(dict(id=TASK,baseline_commit=pop['baseline_commit'],regression_scripts=['scripts/project/CentralStationAreaFamilyResolution.py'],exact_delta_guard=dict(module='CentralStationAreaFamilyResolution',function='guard')))
    save('project-state/workflow-stage-lifecycle.json',stages)
    path=ROOT/'scripts/project/Invoke-ProjectValidation.ps1';t=path.read_text(encoding='utf8')
    t=t.replace('Set-StrictMode -Version Latest','& python "$PSScriptRoot/CentralStationAreaFamilyResolution.py" guard\nif ($LASTEXITCODE) { throw \'Central Avenue exact-population background guard failed.\' }\nSet-StrictMode -Version Latest',1)
    path.write_text(t,encoding='utf8',newline='\n')
    # Refresh only the validation runner implementation hash changed by this stage.
    for row in r['entries']:
        for a in row['controlling_artifacts']:
            if a['path']=='scripts/project/Invoke-ProjectValidation.ps1' and a.get('binding_pointers')==['/implementation']:a['sha256']=file_hash(a['path'])
    save('project-state/governance-registry.json',r)
    S.audit(['project-state/workflow-stage-lifecycle.json','scripts/project/Invoke-ProjectValidation.ps1'])
    refresh()

def public_verify():
    import hashlib,urllib.request,concurrent.futures
    from datetime import datetime,timezone
    rows={x['id']:x['row'] for x in load(BASE+'/starting-state.json')['rows']}
    def one(rid):
        r=rows[rid];e=dict(id=rid,url=r['r2_url'],retrieved_at=datetime.now(timezone.utc).isoformat())
        try:
            h=hashlib.sha256();size=0
            with urllib.request.urlopen(urllib.request.Request(r['r2_url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as response:
                e['http_status']=response.status
                while chunk:=response.read(1048576):h.update(chunk);size+=len(chunk)
            e.update(size_bytes=size,sha256=h.hexdigest(),byte_identical=size==r['size_bytes'] and h.hexdigest()==r['checksum_sha256'])
        except Exception as error:e['error']=str(error)
        return e
    result=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for e in pool.map(one,IDS):
            result.append(e);save(BASE+'/public-verification.json',result);print(e['id'],e.get('byte_identical'),e.get('error'),flush=True)
    assert all(e.get('byte_identical') for e in result)

def prepare_decisions():
    from datetime import datetime, timezone
    now=datetime.now(timezone.utc).isoformat()
    rows={x['id']:x['row'] for x in load(BASE+'/starting-state.json')['rows']}
    measured={r['id']:r for r in load(BASE+'/pdf-inspection.json')}
    compared={r['id']:r for r in load(BASE+'/evidence-52.json')['records']}
    subjects=[
        'City sponsors, workshop process, corridor investment goals and nonbinding draft strategies',
        'ART station typologies, zoning, street design, access, bicycle and parking recommendations',
        'Coors/Atrisco infill sites, development concepts, public spaces and West Central barriers',
        'Old Town plaza and museum connections, pedestrian/bicycle access and parking coordination',
        'Downtown infill, civic connections, public-realm and parking priorities',
        'EDo infill around Albuquerque High and Innovate ABQ, crossings and neighborhood connections',
        'UNM/University infill, Yale streetscape, bicycle connections and neighborhood barriers',
        'Nob Hill infill, street connectivity, parking and neighborhood walkability',
        'International District infill at Louisiana/San Pedro, stormwater, zoning and access barriers',
        'Corridor housing affordability, displacement, transportation costs and equitable participation',
        'Value capture, TIDD, land assembly, predevelopment funding and project priorities',
        'ART growth and capacity assumptions for water, sewer, stormwater, power, gas, telecom and streets',
        'Urban3 parcel-value models, Central redevelopment and Nob Hill projected property-tax returns']
    release=[(19,18),(19,18),(36,31),(49,44),(37,31),(46,44),(35,31),(67,69),(66,69),(64,69),(65,69),(65,69),None]
    research=dict(task_id=TASK,
        conclusion='Eleven continuously paginated sections form one September 2017 City-commissioned public-comment station-area/corridor strategies report. Infrastructure is a separate Crabtree supporting draft released alongside Finance. Urban3 is a separate fiscal study; exact preserved scan provenance/completeness remains unresolved.',
        authority_chain=[
            dict(evidence=BASE+'/evidence-76.txt',finding='Federal Register: City grant D2015-TODP-0018, Central Avenue TOD planning, allocation $860000.'),
            dict(evidence=BASE+'/evidence-72.html',finding='City EC-16-216 awards ABQ Central Corridor TOD Planning to PlaceMakers.'),
            dict(evidence=BASE+'/evidence-83.html',finding='Council approval on 2016-11-21 is procurement authorization, not adoption of the later report.'),
            dict(evidence=BASE+'/evidence-91.txt',finding='Official contract requires stakeholder engagement, station-area concepts and a publicly supported Strategies Report with infrastructure inputs.'),
            dict(evidence=BASE+'/evidence-19.html',finding='September 29, 2017 project announcement publishes eleven report sections for comment following March workshop; final report intended for possible incorporation into action plans.'),
            dict(evidence=BASE+'/evidence-65.html',finding='Finance release separately publishes Crabtree Infrastructure Needs Assessment with 11MB pages and 2MB spreads links.'),
            dict(evidence=BASE+'/evidence-5.html',finding='Current City index distinguishes adopted 2014 Route66 facility plan from 2018 Greater Central/Route66 other study.')],
        family=dict(report_component_ids=IDS[:11],report_pages=237,printed_pagination='Front matter and pages1-235; Station16, West52, Old82, Downtown100, EDo120, University140, Nob168, International190, Equity214, Finance222',infrastructure_id=IDS[11],infrastructure_role='Separate 15-page supporting engineering draft, not chapter12',urban3_id=IDS[12],urban3_role='Separate public-sector financial ROI study, not a continuous chapter',combined_edition='Exact City-delivered revised 2018 combined edition verified; no exact combined September2017 original recovered.',official_2018=load(BASE+'/evidence-42.json')),
        provenance_method='Independent establishment from official grant/procurement, contemporaneous project release statements and delivery links, original credits/date/pagination and all-page comparison with City-delivered successor. No claim that 2017 delivery bytes were freshly recovered or hash-match revised2018 bytes.',
        delivery_limitations='Former Drive print links redirect to sign-in. Introduction/Station Types first-release page has no recovered capture; all-sections announcement and continuous corresponding City2018 content independently establish their project identity. Local/R2 byte identity is separately verified and does not establish government origin.',
        finality=dict(draft_2017='Public comment draft; potential amendment; expressly nonmandatory recommendations.',study_2018='Complete revised study delivered by City; draft/date labels removed, but Potential Amendment and nonmandatory language retained. Documentary successor, not an established adopted amendment.',adoption='No enactment adopting the2017/2018 work, wholesale incorporation or formal abandonment recovered. Current City taxonomy lists2014 adopted plan separately. This finding does not assert a universal legal negative.',later_context='2018 Economic Development whitepaper supports Greater Central partnerships; FY19 approved budget describes future action plan for Council consideration. FTA2018 technical assistance concerns San Mateo/International District capacity and antidisplacement. These parallel efforts do not replace the complete report. Comp Plan/IDO are separate adopted instruments; no whole-report incorporation inferred.',infrastructure='Absent from237-page2018 study; distinct utility-capacity assumptions remain. No final revision/superseding delivery established.',urban3='Historical consultant case study corroborates City commission and fiscal analysis, not exact five-page scan delivery/date/completeness.'),
        durable_value='The complete public-review package records actual proposals offered to residents before2018 revisions, especially financing and public-realm choices. Some neighborhood components are carried forward with no unique standalone claim; retain their original place in the single chronological primary source. Infrastructure adds separate capacity evidence absent from successor.',
        eventual_presentation='One curated historical master presentation for eleven-section September2017 public-comment package, with Infrastructure separately labeled as supporting draft. No thirteen standalone entries. Prefer the completed2018 study as lead reference after separately authorized archival/publication work addresses its260287731-byte original and150000000-byte ceiling. Withhold Urban3 from new publication pending source/completeness recovery.',
        exhaustion=dict(covered=['City Planning index, official OnBase combined document and official directories/URL migration evidence','City Council/Legistar grant, procurement and Route66/GreaterCentral/PlaceMakers/TOD title queries','Former project domain CDX index, homepage/about/downloads and individual draft release pages','Former Drive print deliveries and archive lookup','Gridics, PlaceMakers and archived Urban3 consultant evidence','Later City2018 whitepaper, FY19 budget and FTA2018 technical-assistance evidence','Full text/metadata/pagination/links of originals, internal rendered maps/tables and final pages','All237 successor page texts compared in order'],remaining='Exact Urban3 scan delivery/date/completeness is factual source work, not an owner preference.',limits=['No recovered enactment does not prove no enactment ever existed.','FTA2018 full-PDF GET returned403 twice; authoritative cached excerpt used only to distinguish parallel project.','No live GreaterCentral domain; project captures are historical delivery evidence.']))
    save(BASE+'/research.json',research)
    records=[];updates=[]
    for index,rid in enumerate(IDS):
        old=rows[rid];m=measured[rid];blocked=index==12
        ev=[BASE+'/research.json',BASE+'/pdf-inspection.json',BASE+'/'+rid+'.txt',BASE+'/public-verification.json',BASE+f'/evidence-{96+list(rows).index(rid)//4}.png']
        if index<11:ev += [BASE+'/evidence-52.json',BASE+'/evidence-3.txt',BASE+'/evidence-19.html']
        source=None
        if release[index]:
            n,receipt=release[index];ev.append(BASE+f'/evidence-{n}.html')
            source=next(e['final_url'] for e in load(BASE+f'/evidence-{receipt}.json') if e['n']==n)
        if index==11:ev += [BASE+'/evidence-91.txt',BASE+'/evidence-16.txt']
        if blocked:ev += [BASE+'/evidence-85.html']+[BASE+f'/evidence-{n}.png' for n in range(25,30)]
        scope=dict(assessed_at=now,geographic_institutional_scope='City of Albuquerque Central Avenue / ART corridor and named station areas',specific_albuquerque_connection=subjects[index]+'. Direct analysis of Albuquerque sites, City policy and public investment.',abqinfo_public_information_value='Substantive primary information about Albuquerque transit-linked land use, infrastructure, public finance and historical planning choices.',general_context_exclusion_test='Not statewide guidance, a generic TOD template or incidental geography. Specific Albuquerque sites, corridor assumptions and public investment are the material subject; branding and contextual usefulness alone would fail.',final_scope_decision='passes_both_gates',substantive_rationale='Direct Albuquerque ART corridor planning with substantial information about '+subjects[index].lower()+'. Both geographic and public-information gates pass independently of provenance, archival presence and family numbering.')
        c=compared.get(rid)
        finding=('Corresponding2018 pages'+str(c['official_page_start'])+'-'+str(c['official_page_end'])+'; '+str(c['unchanged_text_pages'])+'/'+str(c['pages'])+' page texts match after draft-label normalization. Complete changes are recorded; textual match is not a claim of identical graphics/source bytes.' if c else research['finality']['infrastructure' if index==11 else 'urban3'])
        later=dict(status='historical_superseded' if c else 'historical_status_uncertain',authoritative_sources=['https://www.cabq.gov/planning/plans-publications',BASE+'/research.json'],finding=finding,publication_qualification='Dated historical planning source, not adopted regulations or evidence of implemented projects. Preserve draft/projection qualifications.')
        rationale=('Retain as a component of one historical public-comment master package. Official procurement, archived public release and City-delivered2018 content independently establish project origin. The package records choices presented before revisions; this component provides '+subjects[index].lower()+'. Substantively unchanged components have no separate unique-entry claim. Complete family context supports primary-source retention rather than serial standalone publication.' if c else ('Retain a separately labeled supporting historical draft in the curated family. Archived Finance delivery explicitly publishes the Crabtree assessment. Fifteen independently paginated pages explain utility capacity, growth and flood/green-infrastructure assumptions absent from237-page successor. These are substantive public investment choices beyond generic operating specifications.' if not blocked else 'Remain pending factual recovery. Dense Albuquerque fiscal scenarios and a corroborated City consultant commission establish credible public value, but2021 scanner metadata and observed numbering do not establish exact complete original, delivery date or acceptance. Final Deliverable on cover is insufficient. No human scope or owner preference decision is warranted.'))
        q=dict(assessed_at=now,reviewed_document_content=True,visual_inspection_completed=True,visual_inspection_evidence=ev,document_function='Historical public-comment planning component' if c else ('Supporting historical infrastructure assessment' if not blocked else 'Scanned consultant financial ROI study with unresolved completeness'),substantive_content=subjects[index]+'. Full extracted content and selected internal visual maps/tables were reviewed against complete family.',durable_public_usefulness=rationale,information_density=str(m['pages'])+' pages and '+str(m['words'])+' extracted words; substantive local analytical maps/tables and recommendations. Urban3 is image-only and was inspected visually.',unique_information='Dated public-review component in original complete package; no standalone uniqueness asserted where2018 carries content forward.' if c else ('Utility capacity and March2017 consultation assumptions absent from combined successor.' if not blocked else 'Locally specific tax-return scenarios; completeness/unique original cannot be settled from this scan.'),standalone_public_value='low' if c else 'substantive',series_relationship='component',publication_form='grouped_component',aggregation_decision=dict(form='grouped_component',rationale='Use one curated historical master; preserve original report components and distinguish Infrastructure as separate supporting draft. Urban3 remains withheld until factual recovery.',evidence=[BASE+'/research.json']),page_count=m['pages'],extracted_word_count=m['words'],currentness_review_required=True,currentness_review=later,rationale=rationale,decision='requires_factual_source_completeness_review' if blocked else 'passes_as_historical_grouped_component')
        if c:q.update(public_engagement=True,engagement_assessment=dict(function='Analytical public-comment recommendations from City-commissioned workshop, not raw votes/meeting notes.',durable_unique_information='Records policy/investment proposals actually offered before later revisions to the complete study.',evidence=[BASE+'/evidence-19.html',BASE+'/evidence-52.json'],substantive_basis='analysis'))
        changes=dict(status='pending review' if blocked else 'approved for addition',scope_assessment=scope,quality_assessment=q,processing_notes=old['processing_notes']+['2026-10-04 governed family resolution: '+rationale+' Evidence: '+BASE+'/decisions.json'],validation_status='Background research complete; exact Urban3 scan source/date/completeness remains factually blocked.' if blocked else 'Background provenance/family/currentness and grouped historical quality review complete.',review_reason='source_provenance_and_completeness_unresolved' if blocked else None,provenance_status='Underlying City Urban3 commission corroborated; exact later scan unreconciled' if blocked else 'Official project public-comment origin independently established; historical original preserved unchanged')
        if not blocked:changes.update(publication_quality_decision=dict(decision='passes',finding_id=TASK+':'+rid,rationale=rationale,evidence=ev,assessment=q),source_url=source)
        records.append(dict(id=rid,title=old['title'],family_component_role='report_component' if c else ('separate_infrastructure_supporting_draft' if not blocked else 'separate_financial_supporting_study_scan'),provenance=dict(conclusion=changes['provenance_status'],evidence=ev,historical_delivery_hash_freshly_recovered=False,verified_original_sha256=m['sha256'],verified_original_size_bytes=m['size_bytes']),later_document_relationship=later,scope_assessment=scope,quality_assessment=q,disposition=changes['status'],rationale=rationale,evidence=ev,owner_decision_required=False))
        updates.append(dict(id=rid,changes=changes))
    save(BASE+'/decisions.json',dict(task_id=TASK,records=records,approved_ids=IDS[:12],pending_ids=IDS[12:],owner_decisions_needed=[],binding_requirement='Retain eleven official2017 public-comment report components and separate Crabtree supporting draft as one curated historical family; keep exact Urban3 scan pending factual provenance/completeness. Preserve all originals, prior source/R2 history and draft qualifications. No new visible presentation or R2 mutation. Documentary2018 successor is not an established adopted amendment.'))
    save(BASE+'/record-updates.json',updates)
    print('Exactly13 decisions prepared:12 historical grouped approvals, one factual hold')

def guard():
    from WorkflowStageLifecycle import StageSnapshot,git
    from TaskGovernance import changed_paths
    stage=StageSnapshot(TASK)
    pop=stage.load_json(BASE+'/population-v8.json'); baseline=pop['baseline_commit']
    assert pop['candidate_ids']==IDS and len(set(IDS))==13
    stage.assert_no_visible_changes(baseline, subprocess.check_output(['git','rev-parse',baseline+':content'],text=True).strip())
    for p in ['project-state/r2-inventory.json','project-state/r2-storage-policy.json']:
        assert stage.read_bytes(p).replace(b'\r\n',b'\n')==git('show',baseline+':'+p).replace(b'\r\n',b'\n'),p
    before=json.loads(git('show',baseline+':project-state/master-inventory.json'))
    after=stage.load_json('project-state/master-inventory.json')
    a={x['id']:x for x in before['candidates']};b={x['id']:x for x in after['candidates']}
    assert a.keys()==b.keys()
    assert {i for i in a if a[i]!=b[i]}<=set(IDS)
    for i in IDS:
        for k in ['checksum_sha256','size_bytes','local_path','r2_key','r2_url','r2_etag','r2_last_modified']:
            assert a[i].get(k)==b[i].get(k),(i,k)
        assert b[i]['processing_notes'][:len(a[i]['processing_notes'])]==a[i]['processing_notes']
    if stage.end or (ROOT/BASE/'queue.json').is_file():
        decisions=stage.load_json(BASE+'/decisions.json')
        assert [x['id'] for x in decisions['records']]==IDS
        requested={x['id']:x['changes'] for x in stage.load_json(BASE+'/record-updates.json')}
        from PublicationQuality import require_publication_quality
        for rid in IDS:
            assert all(b[rid][k]==v for k,v in requested[rid].items()),rid
            assert b[rid]['scope_assessment']['final_scope_decision']=='passes_both_gates'
            if rid in IDS[:12]:require_publication_quality(b[rid])
            else:assert b[rid]['status']=='pending review' and b[rid]['review_reason']=='source_provenance_and_completeness_unresolved'
            assert {k for k in set(a[rid])|set(b[rid]) if a[rid].get(k)!=b[rid].get(k)}<=set(requested[rid])|{'updated_at'}
        q=stage.load_json(BASE+'/queue.json')
        pending={i for i,r in b.items() if r['status']=='pending review'}
        approved={i for i,r in b.items() if r['status']=='approved for addition'}
        assert set(q['pending_ids'])==pending and set(x['id'] for x in q['newly_approved_backlog'])==approved
        assert set(q['gated_pending_ids'])|set(q['source_or_structural_blocked_pending_ids'])|set(q['ungated_pending_ids'])==pending
        assert len(approved)==12 and len(pending)==351 and q['gated_pending_count']==321 and q['source_or_structural_blocked_pending_count']==30
    paths=set(git('diff',baseline,stage.end,'--name-only').decode().splitlines()) if stage.end else set(changed_paths(baseline))
    assert paths<=set(pop['artifact_paths']),paths-set(pop['artifact_paths'])
    print('Central Avenue exact 13-record boundary: passed; zero visible/R2 delta')

def account():
    import copy
    from datetime import datetime,timezone
    from WorkflowStageLifecycle import git
    inv=load('project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']}
    start=load(BASE+'/starting-state.json');before={r['id']:r['row'] for r in start['rows']}
    pointer=json.loads(git('show',start['baseline_commit']+':project-state/ordinary-queue-current.json'))
    prior=json.loads(git('show',start['baseline_commit']+':'+pointer['artifact']))
    q=copy.deepcopy(prior);pending={i for i,r in rows.items() if r['status']=='pending review'}
    q.update(artifact_type='central_station_area_family_resolution_queue',recorded_at=inv['generated_at'],source_queue_artifact=pointer['artifact'],inventory_generated_at=inv['generated_at'],inventory_sha256=file_hash('project-state/master-inventory.json'),pending_review_count=len(pending),pending_ids=sorted(pending))
    for kind in ['gated','source_or_structural_blocked']:
        q[kind+'_pending_ids']={i:why for i,why in prior[kind+'_pending_ids'].items() if i in pending}
        q[kind+'_pending_count']=len(q[kind+'_pending_ids'])
    q['source_or_structural_blocked_pending_ids'][IDS[-1]]='Underlying Urban3 City commission corroborated, but exact preserved five-page later scan delivery/date/completeness remains unestablished; factual source recovery, not owner judgment.'
    ungated=pending-set(q['gated_pending_ids'])-set(q['source_or_structural_blocked_pending_ids'])
    q.update(ungated_pending_ids=sorted(ungated),ungated_pending_count=len(ungated),newly_approved_backlog=[dict(id=i,title=rows[i]['title'],reason='Approved only for curated historical family presentation; no separate serial entry or new publication authority.',review=BASE+'/decisions.json') for i in sorted(rows) if rows[i]['status']=='approved for addition'],approved_count=sum(r['status']=='approved for addition' for r in rows.values()),in_progress_publication=None)
    q['actionable_ungated_pending_ids']=[i for i in prior['actionable_ungated_pending_ids'] if i in ungated]
    q['genuinely_actionable_ungated_pending_count']=len(q['actionable_ungated_pending_ids'])
    q['unresolved_ungated_prerequisites']=[r for r in prior['unresolved_ungated_prerequisites'] if r['id'] in ungated]
    q['background_family_groups']=[dict(f,candidate_ids=[i for i in f['candidate_ids'] if i in pending],candidate_count=len(set(f['candidate_ids'])&pending)) for f in prior['background_family_groups'] if set(f['candidate_ids'])&pending]
    q['central_station_area_resolution']=dict(task=TASK,population=BASE+'/population-v8.json',accounting=BASE+'/accounting.json',blockers_cleared=IDS[:12],remaining_factual_hold=IDS[-1],eventual_visible_entries=1,owner_decisions_needed=[])
    save(BASE+'/queue.json',q);save('project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=BASE+'/queue.json',task=TASK))
    ledger=[dict(id=i,before_row_sha256=digest(before[i]),after_row_sha256=digest(rows[i]),before_status=before[i]['status'],after_status=rows[i]['status'],family_component_role=next(r['family_component_role'] for r in load(BASE+'/decisions.json')['records'] if r['id']==i),original_sha256=rows[i]['checksum_sha256'],original_size_bytes=rows[i]['size_bytes'],r2_key=rows[i]['r2_key'],prior_processing_notes_preserved=rows[i]['processing_notes'][:len(before[i]['processing_notes'])]==before[i]['processing_notes'],decision=BASE+'/decisions.json') for i in IDS]
    save(BASE+'/accounting.json',dict(task_id=TASK,records=ledger,exactly_once=True,changed_inventory_ids=IDS,queue=dict(approved=12,pending=351,governance_gated=321,source_or_structural_blocked=30,ungated=0),source_structural_blockers_cleared=12,owner_decisions_needed=[],visitor_visible_changes=0,r2_added_objects=0,r2_deleted_objects=0,r2_overwritten_objects=0,r2_delta_bytes=0))
    save(BASE+'/progress.json',dict(task_id=TASK,stage='all thirteen reviews and dispositions durably complete; validation/integration pending',records=[dict(id=i,state='review_complete',resulting_disposition=rows[i]['status'],inventory_saved=True,remaining_factual_blocker=i==IDS[-1]) for i in IDS],remaining=['complete validation','authorized background integration and final remote verification'],no_next_population=True))
    baseline_current=git('show',start['baseline_commit']+':project-state/CURRENT.md').decode('utf8')
    links=baseline_current[baseline_current.index('[PR210 closeout]'):]
    (ROOT/'project-state/CURRENT.md').write_text('# Current project state\n\nCentral Avenue family review completed: eleven official2017 public-comment report components plus a separate Crabtree supporting draft retained for one historical master presentation. Exact Urban3 scan remains pending factual provenance/completeness. Queue:12 approved /351 pending (321 governance-gated /30 source-structural blocked);12 blockers cleared. No owner decision or publication task. Zero visible/R2 changes; full validation and authorized background integration pending.\n\n[Family review](governance/'+TASK+'/decisions.json) · '+links,encoding='utf8',newline='\n')
    refresh()
    plan=load(BASE+'/implementation.json')
    plan['completion_evidence']={gid:[dict(path=BASE+'/accounting.json',sha256=file_hash(BASE+'/accounting.json')),dict(path=BASE+'/decisions.json',sha256=file_hash(BASE+'/decisions.json')),dict(path=BASE+'/research.json',sha256=file_hash(BASE+'/research.json'))] for gid in plan['respected_governance_ids']}
    save(BASE+'/implementation.json',plan)
    guard()

if __name__ == '__main__' and len(sys.argv)>1:
    {'refresh':refresh,'history':history,'inspect':inspect,'fetch':fetch,'compare':compare,'setup-authority':setup_authority,'guard':guard,'public-verify':public_verify,'prepare-decisions':prepare_decisions,'account':account}[sys.argv[1]]()
elif __name__ == '__main__' and (ROOT/(BASE+'/authority.json')).exists():
    guard()
elif __name__ == '__main__':
    inventory = load('project-state/master-inventory.json')
    rows = inventory['documents'] if 'documents' in inventory else inventory['candidates']
    selected = [r for r in rows if r['id'] in IDS]
    assert len(selected) == 13
    outputs = ['population.json','starting-state.json','authority.json','implementation.json','progress.json','existing-evidence.json','research.json','decisions.json','accounting.json','receipt.json','validation.log']
    pop = dict(task_id=TASK, baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),candidate_ids=IDS,families=[],pages=[],operation_classes=['document_review','family_review','quality_assessment','inventory_disposition','consolidation','governance_implementation','background_integration'],artifact_paths=[BASE+'/'+p for p in outputs]+[BASE+f'/contract-v{i}.json' for i in range(1,21)]+['scripts/project/CentralStationAreaFamilyResolution.py','project-state/master-inventory.json','project-state/governance/active-task.json','project-state/governance-registry.json','project-state/governance/audit-2026-09-27/artifact-audit.json','project-state/CURRENT.md'])
    write_once(BASE+'/population.json',pop)
    write_once(BASE+'/starting-state.json',dict(baseline_commit=pop['baseline_commit'],remote_refs={'main':pop['baseline_commit'],'chatgpt/planning-snapshot':pop['baseline_commit']},remote_verified_by='git ls-remote origin refs/heads/main refs/heads/chatgpt/planning-snapshot',rows=[{'id':r['id'],'row_sha256':digest(r),'row':r} for r in selected],inventory_sha256=file_hash('project-state/master-inventory.json'),active_task=load('project-state/governance/active-task.json')))
    print(json.dumps(selected,ensure_ascii=False,indent=2))
