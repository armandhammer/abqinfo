"""Owner correction: exact two-record exclusions and no PR207 public-page delta."""
import ast, copy, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE='07a0485306963f2e485a93030ece81c6a2c01da9'
START='8a189e21f2a01f03d7f52cb35f820f6e9dba11d3'
IDS={'src-4db14cde9f1460db','src-e2c19c0b6111c542'}
def old(commit,path):
    return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def guard_current_delta():
    page='content/public-works/city-facilities.md'
    assert (ROOT/page).read_bytes().replace(b'\r\n',b'\n')==old(BASE,page).replace(b'\r\n',b'\n'), 'City Facilities differs from authoritative main'
    before={r['id']:r for r in json.loads(old(START,'project-state/master-inventory.json'))['candidates']}
    after={r['id']:r for r in load('project-state/master-inventory.json')['candidates']}
    assert {i for i in before if before[i]!=after[i]}==IDS,'Inventory delta exceeds owner correction'
    for i in IDS:
        assert after[i]['status']=='excluded'
        assert after[i]['scope_assessment']['final_scope_decision']=='fails_public_information_gate'
        assert after[i]['publication_quality_decision']['decision']=='excluded'
        assert after[i]['publication_quality_decision']['authority']=='owner-youth-justice-publication-exclusion-2026-09-30'
    assert sum(r['status']=='approved for addition' for r in after.values())==18
    pointer=load('project-state/ordinary-queue-current.json');q=load(pointer['artifact'])
    assert set(q['youth_justice_owner_excluded_ids'])==IDS
    assert q['pending_review_count']==372 and len(q['newly_approved_backlog'])==18
    for path in ('project-state/r2-storage-policy.json','project-state/discovery/retained-source-audit-queue.json'):
        assert (ROOT/path).read_bytes().replace(b'\r\n',b'\n')==old(BASE,path).replace(b'\r\n',b'\n')
    evidence='project-state/governance/ordinary-youth-justice-publication-2026-09-30/'
    for path in subprocess.check_output(['git','ls-tree','-r','--name-only',START,evidence],cwd=ROOT,text=True).splitlines():
        assert (ROOT/path).read_bytes().replace(b'\r\n',b'\n')==old(START,path).replace(b'\r\n',b'\n'),'Historical PR207 evidence changed: '+path
    visible=subprocess.check_output(['git','diff','--name-only',BASE,'--','content','layouts','assets','static','hugo.toml'],cwd=ROOT,text=True)
    assert not visible.strip(),'PR207 retains visitor-visible changes'
    # The actual owner negatives fail the existing publication gate, including
    # attempted reuse of the previous positive assessment without supersession.
    from PublicationQuality import quality_errors, require_quality_transition
    previous=load('project-state/governance/pr207-owner-correction-2026-09-30/owner-decision.json')
    for prior in previous['prior_records']:
        assert quality_errors(after[prior['id']])
        attempted=copy.deepcopy(prior)
        try: require_quality_transition(after[prior['id']],attempted)
        except ValueError: pass
        else: raise AssertionError('Previous positive assessment silently reversed owner exclusion')
    tree=ast.parse((ROOT/'scripts/project/Build-HumanReviewReassessment.py').read_text(encoding='utf-8-sig'))
    branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="pkg == 'bernco-project-pages'")
    generic=branch.body[0].orelse[0].orelse
    assert len(generic)==1 and isinstance(generic[0],ast.Raise),'Shared County-page eligibility shortcut remains executable'
    return True
if __name__=='__main__':
    guard_current_delta()
    print('PASS: exact two owner exclusions; other records unchanged; queue18/pending372; source evidence preserved; no public changes or R2 mutation.')
