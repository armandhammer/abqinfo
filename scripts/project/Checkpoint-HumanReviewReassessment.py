"""Persist the reassessment's separate work queue and truthful closeout state."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
F = ROOT / 'project-state/discovery/human-review-reassessment-2026-09-26'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inv = load(ROOT/'project-state/master-inventory.json')
q = load(ROOT/'project-state/campaigns/ordinary-review-large-2026-09-26-third/next-ordinary-queue.json')
work = load(ROOT/'project-state/discovery/codex-human-review-followup-queue.json')['records']
q['pending_ids'] = sorted(r['id'] for r in inv['candidates'] if r['status']=='pending review')
q['pending_review_count'] = len(q['pending_ids'])
q['source_or_structural_blocked_pending_ids'].update({r['id']:r['required_evidence'] for r in work})
q['source_or_structural_blocked_pending_count'] = len(q['source_or_structural_blocked_pending_ids'])
q['mission_borderline_queue_size'] = 1
q['actionability_basis'] = 'Existing nine live-service prerequisites remain unchanged. Fifty-five former human holds now require specific Codex source/family/finality verification; these are work prerequisites, not owner decisions. No new ordinary campaign is launched by this queue.'
q['reassessment_artifact'] = F.relative_to(ROOT).as_posix()+'/summary.json'
q['research_prerequisite_artifact'] = 'project-state/discovery/codex-human-review-followup-queue.json'
q['newly_approved_backlog'] = q.get('newly_approved_backlog',[]) + [dict(id=r['id'],title=r['title'],status=r['status'],prepared=False,reason='Positive scope/quality established; inventory-only approval. Static records require authorized exact archive/public verification before any visible publication; live project pages require a separate editorial stage.') for r in inv['candidates'] if r['id'] in load(F/'authorization.json')['allowed_ids'] and r['status']=='approved for addition']
save(F/'next-ordinary-queue.json',q)
save(ROOT/'project-state/ordinary-queue-current.json',dict(schema_version=1,artifact=(F/'next-ordinary-queue.json').relative_to(ROOT).as_posix(),task='human-review-reassessment-2026-09-26'))
a = load(F/'authorization.json'); a['state']='review_and_archival_complete_validation_in_progress';save(F/'authorization.json',a)
cp = load(ROOT/'project-state/checkpoint.json')
cp['human_review_reassessment'] = dict(artifact=(F/'summary.json').relative_to(ROOT).as_posix(),fully_dispositioned=139,research_prerequisites=55,owner_records=11,owner_packages=4,removed_obsolete_human_gates=194,exact_archives=3,added_r2_bytes=381871978,state=a['state'])
save(ROOT/'project-state/checkpoint.json',cp)
