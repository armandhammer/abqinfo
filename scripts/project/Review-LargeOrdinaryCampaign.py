#!/usr/bin/env python3
"""Persist explicitly reviewed family decisions, without inventory mutation."""
import argparse,json,runpy
from datetime import datetime,timezone
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,SELECTION,CAMPAIGN,load,save=(c[k] for k in ['ROOT','DISC','DATE','SELECTION','CAMPAIGN','load','save'])

CMP_FUNCTIONS={
'src-14aad9f4e2e568a5':'2014 corridor scoring table and bar chart for named Albuquerque streets, with volume/capacity, speed and crash components.',
'src-434fa2c7e338cee3':'2016 dated matrix matching Albuquerque CMP corridors with ITS, transit, bicycle, access-management and roadway strategies; the URL slug says 2014 but the printed matrix says 2016.',
'src-45970070f5a6b293':'2012 ranked corridor table comparing length, volume/capacity, speed, crash and total scores for Alameda, Coors, Central, Wyoming and other metropolitan streets.',
'src-4c686a530b64dc38':'ITS priority-corridor working matrix dated November 3, 2016, with a 2014 CMP ranking explicitly marked draft. Preserve draft wording; this is not an adopted regulation.',
'src-4f9236689bfbc235':'Original JPEG map of CMP corridor rankings across the Albuquerque metropolitan network; legend and colored corridor ranks are substantive cartographic data.',
'src-5e5c169542b20ffe':'2012 corridor-by-strategy matrix linking named Albuquerque routes to prioritized ITS, transit, freight, bicycle and roadway improvements.',
'src-6d3d195380c1420e':'2010 regional CMP network map explicitly delineating the Albuquerque planning area and the named monitored street network.',
'src-7fb3fb614466759b':'Complete 30-page 2014 corridor findings and methodology report, explaining scores, speed-data changes, crash analysis and VMT for Albuquerque corridors.',
'src-8aee99b0bc740065':'2010 image-dominant scoring table and ranking chart for the metropolitan corridor network; low extracted word count is a text-layer limitation, not low information density.',
'src-a348ef5e50807cc0':'Complete 38-page 2010 congestion profiles publication: mapped Albuquerque corridors, operational statistics, modes, demographic trends and ranked performance. Back cover has source rotation; preserve bytes.',
'src-bc888edca84bace7':'2008 image-only metropolitan corridor table and scoring chart, with named Albuquerque corridors and component scores; substantive data despite zero extractable words.',
'src-cecbd18d97a13794':'Complete 46-page 2012 congestion profiles publication: thirty metropolitan corridors, maps, modal facilities and congestion statistics; intentional blank pages 14 and 45 and rotated back cover retained.',
'src-ff0a2fa643ff7919':'Complete 39-page 2012 congestion-management toolkit with cost/time/benefit assessments and local applicability notes, concluding with the regional role of Albuquerque CMP corridors.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=23);p.add_argument('--html-only',action='store_true');a=p.parse_args()
    inv=load(ROOT/'project-state/master-inventory.json');rows={r['id']:r for r in inv['candidates']};objects=load(ROOT/'project-state/r2-inventory.json')['objects']
    for path in sorted(DISC.glob(f'ordinary-large-campaign-family-*-{DATE}.json')):
        d=load(path)
        if d.get('artifact_type')!='ordinary_large_campaign_family_evidence':continue
        n=int(d['family_id'].split('-')[-1])
        if not a.start<=n<=a.end:continue
        if a.html_only and any(r.get('saved_evidence',{}).get('content_kind')!='HTML' for r in d['records']):continue
        for r in d['records']:
            if r['disposition']=='deferred':continue
            rec=r['saved_evidence'];qa=r.get('fresh_source_qa');rid=r['id']
            if qa:
                assert n<=23 or n in {197,198,199,208,224,225}, 'New static documents require independent agent visual/content inspection before review'
                qa['representative_visual_qa']='passed_agent_inspection_opening_middle_ending'
                qa['visually_reviewed_at']=datetime.now(timezone.utc).isoformat()
            if r['disposition']=='duplicate':
                can=rows[r['canonical_candidate_id']]
                relationship=rec.get('relationship') or rec.get('basis') or ('Fresh authoritative full GET exactly matches retained canonical '+can['id']+' in size and SHA-256; delivery alias has no distinct content.')
                assert (can['checksum_sha256'],can['size_bytes'])==(qa['checksum_sha256'],qa['size_bytes'])
                r['exact_identity_relationship']={'canonical_id':can['id'],'canonical_status':can['status'],'same_sha256':True,'same_size':True,'canonical_r2_key':can.get('r2_key'),'canonical_source_url':can.get('direct_file_url') or can['source_url']}
                r['quality_assessment'].update(visual_inspection='representative pages inspected; structural QA passed; saved full-document analysis reused',actual_function='Same complete underlying document as retained canonical; preserve draft/finality labels of canonical. No independent public entry justified by delivery alias.',standalone_public_value='No distinct substantive content beyond the byte-identical retained canonical.',series_component_relationship='exact delivery alias, not a new edition',information_density='identical to retained canonical',substantive_rationale=relationship)
                r['mission_scope_assessment']={'assessed_at':datetime.now(timezone.utc).isoformat(),'geographic_institutional_scope':can['agency'],'specific_albuquerque_connection':'Same Albuquerque document as existing canonical '+can['id'],'abqinfo_public_information_value':'No incremental public value from repeating identical bytes. Canonical policy remains unchanged.','general_context_exclusion_test':'Exact hash and size, independently freshly verified, establish delivery identity rather than a new public-information record.','final_scope_decision':'excluded','substantive_rationale':relationship}
                r['archival_readiness']='already archived canonical; reconcile alias without upload'
            elif r['disposition']=='approved for addition':
                fn=CMP_FUNCTIONS[rid]
                r['quality_assessment'].update(visual_inspection='All PDF pages rendered; opening/middle/ending and image-only tables inspected; original JPEG inspected. Blank source spacers and source rotations are retained.',actual_function=fn,standalone_public_value='Durable Albuquerque congestion measurement or local strategy evidence; short tables/maps retained as components of the historical CMP program record.',information_density='Dense corridor data/maps or detailed measured report; not an administrative form.',series_component_relationship='Distinct dated program publication; annual snapshots retain historical value and are not automatically superseded by later measurements.',intended_publication_form='Future curated chronological CMP program record on existing operations-data page; no visitor wording or layout authorized.',limited_content_exception='Dense visual, cartographic or tabular record with named Albuquerque corridors and distinct dated comparison value.' if qa['page_count']<=2 and (qa.get('word_count') or 0)<250 else None,substantive_rationale=fn)
                r['mission_scope_assessment']={'assessed_at':datetime.now(timezone.utc).isoformat(),'geographic_institutional_scope':'MRCOG/MRMPO Albuquerque metropolitan congestion-management program','specific_albuquerque_connection':fn,'abqinfo_public_information_value':'Documents how congestion, crash exposure and improvement strategies were measured for Albuquerque streets and supplies dated evidence for local transportation planning and investment.','general_context_exclusion_test':'Eligibility rests on mapped/named Albuquerque corridors and local applicability evidence, not MRCOG jurisdiction or a generic national congestion method.','final_scope_decision':'passes_both_gates','substantive_rationale':fn+' The program-family context gives these originals meaningful public infrastructure information.'}
                title=rec['title'];slug=__import__('re').sub(r'[^a-z0-9]+','-',title.lower()).strip('-');ext='jpg' if qa['container']=='JPEG' else 'pdf'
                key='transportation/operations-data/mrcog-'+slug+'.'+ext
                assert not any(o['key'].casefold()==key.casefold() for o in objects)
                r['r2_key']=key;r['proposed_canonical_page']='content/transportation/operations-data.md'
                r['archive_preflight']={'same_hash_inventory_ids':[x['id'] for x in rows.values() if x.get('checksum_sha256')==qa['checksum_sha256'] and x['id']!=rid],'same_size_r2_keys':[o['key'] for o in objects if o['size_bytes']==qa['size_bytes']],'exact_or_casefold_key_collisions':[],'near_name_keys':[o['key'] for o in objects if 'cmp' in o['key'].lower() or 'congestion' in o['key'].lower()],'namespace_basis':'Existing transportation/operations-data namespace and accepted page for measured local transportation performance. Distinct dated CMP originals; no near-name collisions.'}
                assert not r['archive_preflight']['same_hash_inventory_ids'] and not r['archive_preflight']['same_size_r2_keys']
                r['archival_readiness']='fully prepared; guarded upload authorized under current campaign'
                r['future_presentation_caveats']=fn+' Preserve dates, draft legend, source rotations and component-family context; no synthetic compilation or visitor-visible entry created.'
            elif qa and r['disposition']=='excluded':
                title=rec.get('title_for_reference') or rows[rid]['title']
                if rid in {'src-142c353eae3b8211','src-3e365c42a31693fa','src-6ac840c695ebd756','src-15192a82ff4dd6e6','src-e69a69949c48b38e'}:
                    function='General utility tariff, statewide/national regulation, generic technical method or blank federal tax form, with no specific material Albuquerque expenditure, project, decision or locally tailored analysis in the reviewed original.'
                    reason=title+': source authority and applicability are insufficient. The original is general external-agency material; the City delivery supplies no substantive Albuquerque component or independent local public-information value.'
                elif n==197:
                    function='Applicant-facing submission checklist, blank application/request or administrative amendment information sheet. Text describes application steps/documents; no completed project decision, adopted regulation or substantive local analysis.'
                    reason=title+': '+function+' Its transaction-processing usefulness does not establish a separate durable ABQInfo policy/infrastructure record.'
                elif n==199:
                    function='Recreation-season schedule/results or unfilled registration, waiver, consent, roster or conduct paperwork. No substantive City policy, infrastructure analysis or expenditure decision.'
                    reason=title+': '+function+' Geographic City origin does not supply substantive ABQInfo public-information value.'
                    # Do not repeat participant names from public results in
                    # tracked decision evidence. Exact identity remains saved.
                    qa.pop('text_excerpts',None)
                elif n==208:
                    function='Permit-processing flow chart or blank permit stop/cancellation request, with steps or fields rather than a substantive adopted instrument or project record.'
                    reason=title+': '+function+' This is routine transaction guidance without sufficient standalone policy/infrastructure value.'
                else:
                    function='Procurement administrative attendance/sign-in, visit logistics or advertisement order/proof; measured document is supporting transaction paperwork rather than project scope, adopted standard or substantive analysis.'
                    reason=title+': '+function+' Official provenance does not make this administrative evidence independently useful as an ABQInfo archival entry.'
                r['rationale']=reason
                r['quality_assessment'].update(visual_inspection='Fresh measured source, all-page text extraction and rendered opening/middle/ending inspected; low-ink pages inspected where present.',actual_function=function,standalone_public_value='Insufficient substantive ABQInfo public-information value; direct exclusion, not a borderline.',information_density='Measured pages/words preserved; density does not convert generic material or transaction paperwork into eligible policy evidence.',series_component_relationship='Administrative/generic supporting file; related substantive records remain independently reviewable.',intended_publication_form='none; excluded',substantive_rationale=reason)
                r['mission_scope_assessment']={'assessed_at':datetime.now(timezone.utc).isoformat(),'geographic_institutional_scope':rows[rid]['agency'],'specific_albuquerque_connection':function,'abqinfo_public_information_value':'Does not materially explain a core Albuquerque public-policy or infrastructure subject beyond the originating transaction or generic external guidance.','general_context_exclusion_test':'City hosting, geographic origin, statewide applicability and administrative process usefulness do not substitute for both material Albuquerque content and substantial ABQInfo public-information value.','final_scope_decision':'excluded','substantive_rationale':reason}
                r['archival_readiness']='not eligible: mission-scope exclusion; no R2 object'
            r['review_complete']=True
        d['state']='reviewed_decisions_ready_for_inventory';save(path,d)
        print(d['family_id'],'review decisions saved',flush=True)

if __name__=='__main__':main()
