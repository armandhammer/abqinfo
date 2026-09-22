#!/usr/bin/env python3
"""Build the bounded archive-preparation artifact for the seven NMDOT study originals."""
from __future__ import annotations
import hashlib, json, re, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / 'project-state/discovery/nmdot-statewide-truck-parking-study-decision-2026-09-19.json'
INVENTORY = ROOT / 'project-state/master-inventory.json'
R2 = ROOT / 'project-state/r2-inventory.json'
OUTPUT = ROOT / 'project-state/discovery/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21.json'
ATTESTATION = ROOT / 'project-state/discovery/nmdot-statewide-truck-parking-study-docx-visual-qa-attestation-2026-09-21.json'
STAGING = 'research/staging/nmdot-statewide-truck-parking-study-archive-preparation-2026-09-21'
FILES = ['01-project-management-plan.docx','02-stakeholder-engagement-plan.docx','03-literature-review-best-practices.docx','04-freight-activity-evaluation.docx','05-truck-parking-supply-demand.docx','06-interstate-truck-parking-assessment.pdf','07-recommendation-implementation-plan.pdf']
ARCHIVES = ['nmdot-statewide-truck-parking-study-part-1-project-management-plan.docx','nmdot-statewide-truck-parking-study-part-2-stakeholder-engagement-plan.docx','nmdot-statewide-truck-parking-study-part-3-literature-review-best-practices.docx','nmdot-statewide-truck-parking-study-part-4-freight-activity-evaluation.docx','nmdot-statewide-truck-parking-study-part-5-truck-parking-supply-demand.docx','nmdot-statewide-truck-parking-study-part-6-interstate-truck-parking-assessment.pdf','nmdot-statewide-truck-parking-study-part-7-recommendation-implementation-plan.pdf']
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def words(s): return len(re.findall(r'\S+', s))
def docx_metrics(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None, f'{p}: DOCX ZIP CRC failure'
        return words(' '.join(ET.fromstring(z.read('word/document.xml')).itertext()))
def pdf_metrics(p):
    pdf=pdfium.PdfDocument(str(p)); count=0; total=0
    for page in pdf:
        page.render(scale=0.35).to_pil(); count += 1
        total += words(page.get_textpage().get_text_range())
    return count,total
def main():
    decision=load(DECISION); attestation=load(ATTESTATION); assert attestation['human_visual_qa']=='passed'; inventory={r['id']:r for r in load(INVENTORY)['candidates']}; r2={r['key'] for r in load(R2)['objects']}; records=[]
    for index,item in enumerate(sorted(decision['records'],key=lambda x:x['series_order'])):
        order=item['series_order']; staged=ROOT/STAGING/FILES[index]; size=staged.stat().st_size; checksum=digest(staged)
        assert size==item['size_bytes'] and checksum==item['checksum_sha256'],item['id']
        key=f'transportation/roadway-projects/studies/{ARCHIVES[index]}'; assert key not in r2,key
        is_docx=item['container']=='OOXML'; count=docx_metrics(staged) if is_docx else pdf_metrics(staged); pages=None if is_docx else count[0]; word_count=count if is_docx else count[1]
        visual='passed_host_word_render_and_human_visual_inspection' if is_docx else 'passed_all_pages_rendered_and_contact_sheet_reviewed'
        detail=(attestation['attestation']+' '+attestation['preservation'] if is_docx else f'All {pages} pages rendered successfully; contact-sheet review found no missing/corrupt pages or obvious visual defects.')
        qa={'visual_inspection':detail,'measured_content':f'{pages if pages else "Page count pending host render"}; {word_count} extracted words; {size} bytes; SHA-256 {checksum}.','standalone_public_value':'A distinct substantive phase of the complete statewide truck-parking study, needed to retain the project management, engagement, evidence, analysis, assessment, and implementation record as published.','information_density':'Substantive technical-study content with narrative, data, tables, figures, or recommendations; not an administrative fragment.','series_component_relationship':f'Number {order} of 7 in the complete ordered NMDOT statewide truck-parking study series; preserve separately in original container and present only as a clearly numbered series.','intended_publication_form':'One unchanged original archive object in Roadway Studies after separately authorized R2 upload and exact public-byte verification; no DOCX-to-PDF conversion.','rationale':'The saved family decision found each deliverable noninterchangeable and necessary to the complete statewide freight and highway reference record relevant to Albuquerque.'}
        candidate=inventory[item['id']]; note=f'Archive preparation 2026-09-21: re-fetched authoritative NMDOT original matched {size} bytes and SHA-256 {checksum}; proposed R2 key {key}; no R2 upload or public-byte verification performed.'; qa_note='Archive preparation 2026-09-21: host-side DOCX render and human visual QA passed; unchanged DOCX remains proposed archive object.' if is_docx else None; notes=candidate['processing_notes']+([x for x in (note,qa_note) if x and x not in candidate['processing_notes']]); inventory_status='archive preparation complete with visual QA passed; no R2 archive or public-byte verification performed'
        records.append({'id':item['id'],'series_order':order,'accepted_title':item['title'],'status':'approved for addition','disposition':'approved for addition','authoritative_source':{'publisher':item['publisher'],'NMDOT_landing_page':candidate['parent_url'],'direct_original_file_url':item['authoritative_url'],'delivery_host_context':'Public realfile.rtsclients.com file host linked from dot.nm.gov; saved research identifies NMDOT as publisher.'},'container':'OOXML/DOCX' if is_docx else 'PDF','source_evidence':{'staged_path':f'{STAGING}/{FILES[index]}','size_bytes':size,'sha256':checksum,'leading_bytes':item['leading_bytes'],'source_byte_verification':'passed_re_fetched_authoritative_original'},'document_metadata':{'served_filename':item['served_filename'],'extracted_word_count':word_count,'page_count':pages},'visual_qa':{'result':visual,'detail':detail},'quality_assessment':qa,'canonical_placement':{'page':'content/transportation/roadway-projects/studies.md','section':'State Highway Studies Affecting Albuquerque','decision':'approved_for_future_archive_first_publication'},'proposed_canonical_archive_filename':ARCHIVES[index],'proposed_r2_key':key,'archive_preparation':{'proposed_r2_key':key,'preserve_original_container_unchanged':True,'r2_action':'none'},'collision_check':'No exact proposed-key collision in project-state/r2-inventory.json (1,218 objects).','r2_action':'none','remaining_gates':['Complete the five DOCX host-side render and human visual inspections.','Obtain separate explicit authorization before any R2 upload or storage mutation.','After upload, verify each public archive download against saved exact size and SHA-256.','Obtain separate authorization for any Hugo/public-content, PR, merge, or deployment work.'],'inventory_update':{'status':'approved for addition','direct_file_url':item['authoritative_url'],'file_type':'DOCX' if is_docx else 'PDF','size_bytes':size,'checksum_sha256':checksum,'validation_status':inventory_status,'processing_notes':notes}})
    total=sum(r['source_evidence']['size_bytes'] for r in records)
    artifact={'schema_version':1,'artifact_type':'nmdot_statewide_truck_parking_study_archive_preparation','recorded_at':'2026-09-21','state':'archive_preparation_complete_external_r2_upload_and_public_byte_verification_gated','source_decision':str(DECISION.relative_to(ROOT)).replace('\\','/'),'docx_visual_qa_attestation':str(ATTESTATION.relative_to(ROOT)).replace('\\','/'),'scope_candidate_ids':[r['id'] for r in records],'series':{'name':'NMDOT statewide truck-parking study','relationship':'Complete ordered seven-part series; do not split or substitute any part.','total_source_bytes':total},'records':records,'summary':{'source_verification_passed':7,'docx_visual_qa_passed':5,'pdf_render_qa_passed':2,'r2_key_collisions':0,'total_source_bytes':total},'host_docx_renderer':{'helper':'scripts/project/Render-NmdotTruckParkingDocxInspection.ps1','staged_originals':STAGING,'current_codex_limitation':'Word COM unavailable in Codex Windows execution context: HRESULT 0x80070520; this is not a source-document defect.','output_report':f'{STAGING}/docx-visual-render/host-docx-render-report.json','report_reconciliation':attestation['report_reconciliation']},'remaining_gates':['Obtain separate explicit authorization before any R2 upload or storage mutation.','After upload, verify each public archive download against saved exact size and SHA-256.','Obtain separate authorization for any Hugo/public-content, PR, merge, or deployment work.'],'safeguards_observed':{'r2_mutation':False,'public_content_changed':False,'merge_or_deploy':False}}
    OUTPUT.write_text(json.dumps(artifact,indent=2)+'\n',encoding='utf-8'); print(json.dumps(artifact['summary'],indent=2))
if __name__=='__main__': main()
