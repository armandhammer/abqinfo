"""Persist the completed unmerged owner-review handoff; final refs remain observable via Git/GitHub."""
import json,re,subprocess,sys
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
P=S.prefix(S.B)
S.G.active_check('mutation','governance_implementation')
pr=json.loads(subprocess.check_output(['gh','pr','view','210','--json','number,url,state,mergedAt,headRefOid,headRefName,baseRefName,body'],encoding='utf-8'))
head=S.G.git('rev-parse','HEAD');assert pr['state']=='OPEN' and pr['mergedAt'] is None and pr['headRefOid']==head and pr['baseRefName']=='main'
assert pr['body'].strip()==(S.G.ROOT/(P+'pr-body.md')).read_text(encoding='utf-8').strip()
refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/heads/main','refs/heads/chatgpt/planning-snapshot','refs/heads/'+pr['headRefName']],encoding='utf-8').splitlines())
assert refs['refs/heads/main']=='1e56540c199d26384989074d497a9bffac60e3f4'
assert refs['refs/heads/chatgpt/planning-snapshot']==refs['refs/heads/'+pr['headRefName']]==head
preview=S.G.load(P+'preview.json');assert preview['result']=='passed' and preview['visual_inspected_sections']==10
tree=S.G.git('rev-parse','HEAD:content');assert tree==preview['content_tree_oid']
S.save(P+'pr.json',dict(observed_at=S.now(),number=pr['number'],url=pr['url'],state=pr['state'],merged_at=pr['mergedAt'],head_at_creation_checkpoint=head,base=pr['baseRefName'],body_verified_exactly=True,preview_url=preview['preview_url']))
S.save(P+'remote-final.json',dict(observed_at=S.now(),refs_before_final_handoff_metadata=refs,pr_state='OPEN',pr_merged_at=None,reviewed_content_tree_oid=tree,finalization='The following handoff metadata commit preserves this inspected content tree. Atomically fast-forward the PR branch and planning-snapshot to that exact final commit, then verify live refs and PR state. This is a timestamped pre-finalization observation, not a claim to know the future metadata commit SHA.',main_remains_phase_a=True))
receipt=S.G.load(P+'receipt.json');receipt.update(state='complete_unmerged_owner_review',pr_number=210,pr_url=pr['url'],pr_state='OPEN',pr_merged_at=None,content_unmerged=True,reviewed_content_tree_oid=tree,reviewed_head_before_final_metadata=head,planning_snapshot_verified_before_final_metadata=head,final_ref_method='Atomic fast-forward of content branch and planning-snapshot to final handoff metadata commit; final SHA observable in both remote refs and PR head.',normal_validation='passed',validation_exit_code=0,full_governance_accounting=True,preview_inspection='all ten resource placements passed',r2_final_listing=P+'r2-after.json',final_r2_metadata_matches_phase_a=True,remaining_authorized_work=[],next_stage='Owner manual PR review. Merge/production require subsequent owner approval.')
S.save(P+'receipt.json',receipt)
progress=S.G.load(P+'progress.json');progress.update(state='complete_unmerged_owner_review',remaining=[],pr_created=True,pr_number=210,pr_url=pr['url'],preview_created=True,preview_url=preview['preview_url'],planning_snapshot_synchronized=True,normal_final_validation='passed',owner_manual_review_pending=True,pr_unmerged=True)
S.save(P+'progress.json',progress)
q=S.G.load(P+'queue.json');q['artifact_type']='owner_publication_handoff_queue';q['in_progress_publication']=dict(task=S.B,implemented_ids=S.LIVE+[S.SUN]+S.NEW,not_live=True,pr_number=210,pr_url=pr['url'],pr_state='OPEN',manual_review_pending=True);S.save(P+'queue.json',q)
f=S.G.ROOT/'project-state/checkpoint.json';text=f.read_bytes().decode('utf-8')
for k,v in dict(completed_item_range='Frozen nine-record publication validated and visually inspected; unmerged owner-review PR210 prepared',resume_command='PR210 awaits owner manual review. Main contains only Phase A archival/governance integration; planning-snapshot follows the exact reviewed PR head. Do not merge or publish production without subsequent owner approval.').items():
    text,n=re.subn(r'("'+k+r'"\s*:\s*)"(?:[^"\\]|\\.)*"',lambda m:m.group(1)+json.dumps(v),text,count=1);assert n==1
f.write_bytes(text.encode('utf-8'))
links='[Active task](governance/active-task.json) · [Owner correction](governance/pr207-owner-correction-2026-09-30/receipt.json) · [Closeout](governance/pr207-postmerge-closeout-2026-09-30/receipt.json) · [Ref evidence](governance/pr207-final-ref-verification-2026-09-30/final-verification.json) · [Triage](governance/approved-queue-lightweight-triage-2026-09-30/triage.json) · [Queue](ordinary-queue-current.json) · [Workflow](governance-workflow.md) · [Registry](governance-registry.json).'
current='# Current project state\n\n[PR210](https://github.com/armandhammer/abqinfo/pull/210) is ready for owner manual review and remains unmerged. Nine frozen resources on seven existing pages; complete project/governance, Hugo, external and preview checks passed. Every changed placement inspected in installed Chrome. Planning-snapshot follows the reviewed PR head; content tree is preserved through final handoff metadata. Main remains Phase A at1e56540c199d26384989074d497a9bffac60e3f4. Sunport exact original:280024902 bytes /601 pages; full public GET matches authorized SHA256. R2:1612 objects /10971266597 bytes; standing ceilings unchanged. Branch queue:0 approved /363 pending. No additional Phase B R2 changes. Merge/production requires subsequent owner approval.\n\n[Publication receipt](governance/'+S.B+'/receipt.json) · [Sunport receipt](governance/'+S.A+'/receipt.json) · '+links+'\n'
(S.G.ROOT/'project-state/CURRENT.md').write_text(current,encoding='utf-8',newline='\n')
S.event(S.B,'external_mutation',S.LIVE+[S.SUN]+S.NEW,'Opened unmerged PR210 with validated exact page/section preview description; verified snapshot alignment. Final metadata integration will preserve the reviewed content tree and main Phase A.',P+'pr.json')
S.refresh(S.B);S.G.active_check('final');S.guard()
active=S.G.load(S.G.ACTIVE_TASK);active['state']='complete';S.save(S.G.ACTIVE_TASK,active)
plan=S.G.load(P+'implementation.json');plan['status']='complete';S.save(P+'implementation.json',plan)
S.G.active_check('final')
print('Completed handoff metadata ready for exact atomic final branch/snapshot push; main unchanged, PR210 unmerged.')
