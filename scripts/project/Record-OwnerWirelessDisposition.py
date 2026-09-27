"""Record explicit wireless exclusion with the standard scope-history schema."""
from OwnerDecisions import *
import importlib.util
spec=importlib.util.spec_from_file_location('scope',ROOT/'scripts/project/Apply-MissionScopeBorderlineDispositions.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
inv=load(ROOT/'project-state/master-inventory.json');row=next(r for r in inv['candidates'] if r['id']=='src-333e4b4b3970edc1');prior=next(r for r in load(F/'baseline-records.json') if r['id']==row['id'])['scope_assessment'];rationale='Owner editorial exclusion: Exclude. Final wireless regulations offer the substantive public information more directly than this internal staff application-routing checklist.';item=dict(id=row['id'],decision='Exclude',rationale=rationale);key=m.disposition_key(F/'authorization.json',item)
row['scope_assessment']=m.excluded_assessment(prior,rationale,'2026-09-26');row['exclusion_reason']=rationale
history=row.setdefault('scope_assessment_history',[])
if not any(e.get('disposition_key')==key for e in history):history.append(dict(disposition_key=key,recorded_at='2026-09-26',review_reason='mission_scope_borderline',prior_scope_assessment=prior,human_decision='Exclude',human_rationale=rationale))
row['updated_at']=datetime.now(timezone.utc).isoformat();m.recompute(inv);save(ROOT/'project-state/master-inventory.json',inv)
q=load(ROOT/'project-state/discovery/mission-scope-borderline-human-review-queue.json');q['resolved_records']=[e for e in q['resolved_records'] if e['id']!=row['id']]+[dict(id=row['id'],disposition_key=key,recorded_at='2026-09-26',decision='Exclude',rationale=rationale,prior_scope_assessment=prior,resulting_status='excluded',final_scope_assessment=row['scope_assessment'],decision_artifact=(F/'authorization.json').relative_to(ROOT).as_posix())];save(ROOT/'project-state/discovery/mission-scope-borderline-human-review-queue.json',q)
save(F/'wireless-scope-disposition.json',dict(decision_artifact=(F/'authorization.json').relative_to(ROOT).as_posix(),dispositions=[item],disposition_key=key))
print('Recorded standard scope history and resolved queue entry')
