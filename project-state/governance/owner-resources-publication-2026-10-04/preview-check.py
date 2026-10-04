"""Verify complete preview articles and inspect every changed resource in isolated Chrome."""
import hashlib,json,re,subprocess,sys,urllib.request
from playwright.sync_api import sync_playwright
sys.path.insert(0,'scripts/project');import OwnerResources20261004 as S
from Pr208209Reconciliation import presentation
P=S.prefix(S.B);S.G.active_check('mutation','external_mutation')
head=S.G.git('rev-parse','HEAD')
checks=json.loads(subprocess.check_output(['gh','api','repos/armandhammer/abqinfo/commits/'+head+'/check-runs'],encoding='utf-8'))
run=next(r for r in checks['check_runs'] if r['name']=='Cloudflare Pages')
assert run['head_sha']==head and run['status']=='completed' and run['conclusion']=='success'
host=re.search(r'https://[a-z0-9]+\.abqinfo\.pages\.dev',run['output']['summary']).group(0)
render=S.G.load(P+'rendered-checks.json');proof=[]
for page in S.PAGES:
    route=page.removeprefix('content/').removesuffix('.md')+'/'
    url=host+'/'+route
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=60) as r:
        remote=r.read();assert r.status==200
    local=(S.G.ROOT/('tmp/site-build/'+route+'index.html')).read_bytes()
    value,decoded=presentation(remote);expected,_=presentation(local)
    assert value==expected,('Complete preview article differs',page)
    section_checks=[x for x in render['checks'] if x['page']==page]
    for x in section_checks:assert x['anchor'] in value[2] and value[1].count(x['url'])==1
    proof.append(dict(page=page,url=url,sections=[dict(anchor=x['anchor'],preview_url=url+'#'+x['anchor'],candidate_id=x['candidate_id']) for x in section_checks],http_status=200,html_sha256=hashlib.sha256(remote).hexdigest(),article_sha256=hashlib.sha256(S.G.canonical(value)).hexdigest(),matches_validated_local_article=True,email_protection_decodes=decoded))
scratch=S.G.ROOT/'research/staging'/S.B;scratch.mkdir(parents=True,exist_ok=True);visual=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();page.set_default_timeout(15000)
    for i,x in enumerate(render['checks']):
        url=host+'/'+x['route']+'#'+x['anchor'];response=page.goto(url,wait_until='domcontentloaded',timeout=60000);assert response.status==200
        target=page.locator('article a').evaluate_all('(xs,url)=>xs.filter(x=>x.href===url).length',x['url'])
        assert target==1
        # Exact URL comparison avoids CSS escaping of ArcGIS query strings.
        page.locator('article a').evaluate_all('(xs,url)=>xs.find(x=>x.href===url).scrollIntoView({block:"center"})',x['url'])
        page.wait_for_timeout(1200)
        shot=scratch/f'preview-section-{i}.png';page.screenshot(path=str(shot))
        visual.append(dict(candidate_id=x['candidate_id'],page=x['page'],anchor=x['anchor'],preview_url=url,screenshot=shot.relative_to(S.G.ROOT).as_posix(),sha256=hashlib.sha256(shot.read_bytes()).hexdigest(),article_text=page.locator('article').inner_text(),tool='Installed desktop Google Chrome / Playwright / isolated ephemeral task context'))
        print('Rendered',i,x['candidate_id'],x['page'],flush=True)
    browser.close()
S.save(P+'preview-render.json',dict(result='rendered_for_visual_inspection',head_sha=head,viewport=dict(width=1440,height=1000),sections=visual))
S.save(P+'preview.json',dict(result='semantic_verification_passed_visual_inspection_pending',verified_at=S.now(),deployment_head_sha=head,content_tree_oid=S.G.git('rev-parse','HEAD:content'),preview_url=host,cloudflare_check=dict(id=run['id'],head_sha=head,status=run['status'],conclusion=run['conclusion'],details_url=run['details_url']),comparison='Complete ordered article text, links and anchors equal local validated Hugo build; Cloudflare email protection normalized.',pages=proof,rendered_sections=len(visual),visual_evidence=P+'preview-render.json'))
print(host)
