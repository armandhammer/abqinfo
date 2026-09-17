"""Write compact editorial-resolution and externally gated action artifacts."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / 'project-state/discovery'
MANIFEST = DISCOVERY / 'dpm-executive-committee-consolidation-manifest-2026-09-17.json'

def main() -> None:
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    dpm = json.loads(MANIFEST.read_text(encoding='utf-8'))
    decisions = {
        'artifact_type': 'archive_reconciliation_editorial_resolution', 'generated_at': now,
        'resolved_cases': [
            {'master_id':'src-6735737588d294e0','disposition':'validated_for_capital_spending_content','limitation':'EPC recommendation and Notice of Decision preceding later Mayor/Council action; not enacted capital program.'},
            {'master_id':'src-3c9907796a0cfaf3','disposition':'validated_for_capital_spending_content','limitation':'Official standalone WIZ map, appendix page B-6; parent document not located and no parent-plan title inferred.'},
            {'master_id':'src-f6feb3549d055097','disposition':'validated_for_annual_dpm_packet','limitation':'Agenda - approved minutes not located; inclusion does not establish meeting occurrence or adopted action.'}
        ],
        'dpm_content_transition': 'Annual packets are locally generated but not yet in R2. Existing visible individual records remain until an authorized upload makes a real archive URL available; no placeholder content link was created.',
        'deployment_lag_current_branch_links': 53,
        'live_r2_mutated': False, 'deployment_performed': False
    }
    uploads=[]
    for p in dpm['annual_packets']:
        uploads.append({'action':'upload_new_dpm_annual_compilation','local_path':p['local_output_path'],'r2_key':p['proposed_r2_key'],'public_url':p['proposed_public_url'],'size_bytes':p['resulting_size_bytes'],'sha256':p['resulting_sha256'],'page_count':p['resulting_page_count'],'requires_explicit_authorization':True})
    external = {'artifact_type':'archive_reconciliation_external_action_manifest','generated_at':now,
        'dpm_uploads':uploads,
        'other_uploads':{'separate_pending_17_pdf_batch':'excluded from this authorization; remains separately gated'},
        'deployment':{'current_branch_deployment_lag_links':53,'requires_explicit_authorization':True},
        'future_duplicate_deletion_candidate':{'r2_key':'transportation/transportation-plans/mrmppo-unified-planning-work-program-ffy-2027-2028.pdf','requires_explicit_authorization':True},
        'prohibitions_observed':['No R2 upload','No R2 deletion or overwrite','No deployment','No merge or PR']}
    (DISCOVERY/'archive-reconciliation-editorial-resolution-2026-09-17.json').write_text(json.dumps(decisions,indent=2)+'\n',encoding='utf-8')
    (DISCOVERY/'archive-reconciliation-external-action-manifest-2026-09-17.json').write_text(json.dumps(external,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote 2 artifacts with {len(uploads)} externally gated DPM uploads.')
if __name__ == '__main__': main()
