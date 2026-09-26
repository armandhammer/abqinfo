#!/usr/bin/env python3
"""Apply only reviewed decisions through established repository update tools."""
import argparse,json,runpy,subprocess,sys
from pathlib import Path
c=runpy.run_path(str(Path(__file__).with_name('Build-LargeOrdinaryCampaign.py')))
ROOT,DISC,DATE,BASE,SELECTION,CAMPAIGN,load,save,digest=(c[k] for k in ['ROOT','DISC','DATE','BASE','SELECTION','CAMPAIGN','load','save','digest'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=999);a=p.parse_args()
    s=load(SELECTION);qs={q['id']:q for q in s['all_pending_records']};d=load(CAMPAIGN)
    for f in s['candidate_families']:
        if not a.start<=f['order']<=a.end:continue
        path=DISC/f"ordinary-large-campaign-{f['family_id']}-{DATE}.json"
        if not path.exists():continue
        fam=load(path)
        if fam.get('state')!='reviewed_decisions_ready_for_inventory':continue
        if any(x['family_id']==f['family_id'] for x in d['families_processed']):continue
        selected=[r for r in fam['records'] if r.get('review_complete') and r['disposition']!='deferred']
        if len(d['resolved_records'])+len(selected)>500:continue
        rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
        app=[]
        for r in selected:
            rid=r['id'];row=rows[rid]
            note='Ordinary large campaign 2026-09-26: reviewed evidence '+path.relative_to(ROOT).as_posix()+'. No content or publication changes.'
            if row['status']!='pending review':
                assert note in row['processing_notes'] and row['status']==r['disposition'],'Unrelated transition or inconsistent resume state'
                continue
            assert digest(row)==qs[rid]['baseline_row_sha256'],'Candidate changed since selection'
            assert not qs[rid]['completed_or_gated'] and rid not in s['excluded_gated_pending_ids']
            saved=r['saved_evidence'];qa=r.get('fresh_source_qa')
            if r['disposition']=='approved for addition':
                assert r['mission_scope_assessment']['final_scope_decision']=='passes_both_gates'
                assert qa['source_exact_verified'] and qa['representative_visual_qa']=='passed_agent_inspection_opening_middle_ending'
                changes=dict(status='approved for addition',title=saved['title'],agency='Mid-Region Council of Governments',size_bytes=qa['size_bytes'],checksum_sha256=qa['checksum_sha256'],file_type=qa['container'],local_path=qa['staged_path'],scope_assessment=r['mission_scope_assessment'],proposed_canonical_page=r['proposed_canonical_page'],processing_notes=row['processing_notes']+[note],validation_status='source and quality reviewed; original archive prepared; no visitor-visible implementation')
                request=DISC/f"ordinary-large-campaign-{rid}-update-{DATE}.json";save(request,changes)
                command="$changes=Get-Content -Raw -Encoding UTF8 '"+request.relative_to(ROOT).as_posix()+"' | ConvertFrom-Json -AsHashtable -DateKind String; & scripts/project/Update-Candidate.ps1 -Id '"+rid+"' -Set $changes | Out-Null"
                subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-Command',command],cwd=ROOT,check=True)
            else:
                # Keep original titles and source URLs; measured identity and
                # historical research are additions, not provenance replacement.
                rec=dict(id=rid,recommended_status=r['disposition'],scope_assessment=r['mission_scope_assessment'],evidence_note=note)
                if qa:rec.update(size_bytes=qa['size_bytes'],checksum_sha256=qa['checksum_sha256'])
                else:
                    if row.get('checksum_sha256') and row['checksum_sha256']!=saved['checksum_sha256']:raise ValueError('Historical checksum conflicts; requires independent review')
                    rec.update(size_bytes=saved['size_bytes'],checksum_sha256=saved['checksum_sha256'])
                if r['disposition']=='excluded':rec['exclusion_reason']=r['rationale']
                else:rec.update(canonical_id=r['canonical_candidate_id'],relationship=saved.get('relationship') or saved.get('basis') or r['quality_assessment']['substantive_rationale'])
                app.append(rec)
        if app:
            application=DISC/f"ordinary-large-campaign-{f['family_id']}-application-{DATE}.json";save(application,{'decisions':app,'source_evidence_artifact':path.relative_to(ROOT).as_posix(),'visitor_visible_content_changed':False})
            subprocess.run([sys.executable,'-B',str(ROOT/'scripts/project/Apply-SavedTerminalResearch.py'),'--research',str(application),'--ids',','.join(r['id'] for r in app)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        rows={r['id']:r for r in load(ROOT/'project-state/master-inventory.json')['candidates']}
        done={r['id'] for r in d['resolved_records']}
        for r in selected:
            assert rows[r['id']]['status']==r['disposition']
            if r['id'] not in done:d['resolved_records'].append(dict(id=r['id'],initial_status='pending review',decision=r['disposition'],current_status=rows[r['id']]['status'],family_id=f['family_id'],evidence_artifact=path.relative_to(ROOT).as_posix()))
        for r in fam['records']:
            if r['disposition']=='deferred' and not any(x['id']==r['id'] for x in d['deferred_records']):d['deferred_records'].append(dict(id=r['id'],family_id=f['family_id'],reason=r['error']))
        d['families_processed'].append(dict(family_id=f['family_id'],family=f['family'],resolved_count=len(selected),deferred_count=len(fam['records'])-len(selected),complete=len(selected)==len(fam['records']),artifact=path.relative_to(ROOT).as_posix()))
        d['state']='inventory_decisions_applied_archive_and_integrity_pending';save(CAMPAIGN,d)
        checkpoint_command="& scripts/project/Write-ProjectCheckpoint.ps1 -CompletedRange 'Ordinary large campaign: "+str(len(d['resolved_records']))+" formerly pending records dispositioned; background archive/integrity work remains. Evidence: project-state/discovery/ordinary-queue-large-resolution-campaign-2026-09-26.json.' -ResumeCommand 'Resume campaign evidence and reviewed families; retain all human gates; no content changes.' | Out-Null"
        subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-Command',checkpoint_command],cwd=ROOT,check=True)
        print(f['family_id'],'applied',len(selected),'campaign',len(d['resolved_records']),flush=True)

if __name__=='__main__':main()
