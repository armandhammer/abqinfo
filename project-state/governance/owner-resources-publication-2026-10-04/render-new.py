"""Owner-authorized isolated installed Chrome review of the two exact public URLs."""
import hashlib,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,'scripts/project')
import OwnerResources20261004 as S
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
P=S.prefix(S.B)
S.G.active_check('mutation','document_review',S.NEW)
scratch=S.G.ROOT/'research/staging'/S.B
scratch.mkdir(parents=True,exist_ok=True)
out=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000})
    for n,rid in enumerate(S.NEW):
        row=next(r for r in S.G.load('project-state/master-inventory.json')['candidates'] if r['id']==rid)
        page=context.new_page();page.set_default_timeout(10000)
        r=dict(candidate_id=rid,url=row['source_url'],observed_at=S.now(),tool='Playwright installed Google Chrome, isolated ephemeral browser context, desktop 1440x1000',steps=[],page_errors=[])
        page.on('pageerror',lambda e:r['page_errors'].append(str(e)[:1000]))
        response=page.goto(row['source_url'],wait_until='domcontentloaded',timeout=60000)
        r.update(status=response.status,title=page.title(),resolved_url=page.url)
        page.wait_for_timeout(22000)
        def capture(label):
            shot=scratch/f'new-{n}-{label}.png';page.screenshot(path=str(shot),full_page=False)
            step=dict(label=label,screenshot=shot.relative_to(S.G.ROOT).as_posix(),sha256=hashlib.sha256(shot.read_bytes()).hexdigest(),visible_text=page.locator('body').inner_text()[:35000],aria=page.locator('body').aria_snapshot()[:50000])
            r['steps'].append(step);print(label,step['aria'][:17000],flush=True)
        capture('initial')
        if n==0:
            page.get_by_role('button',name='Close information panel',exact=True).click()
            page.get_by_role('button',name='Open legend',exact=True).click()
            page.wait_for_timeout(3000);capture('legend')
            page.get_by_role('button',name='Close legend',exact=True).click()
            page.get_by_role('button',name='Open search',exact=True).click()
            page.get_by_role('searchbox',name='Search',exact=True).fill('1 Civic Plaza NW, Albuquerque')
            page.get_by_role('searchbox',name='Search',exact=True).press('Enter')
            page.wait_for_timeout(9000);capture('address-search')
            page.mouse.click(760,525);page.wait_for_timeout(5000);capture('feature-popup')
            # Dismiss the official introductory panel, then inspect the map tools.
            for name in ['OK','Close','Close introduction','Close dialog','Explore']:
                button=page.get_by_role('button',name=name,exact=True)
                if button.count() and button.first.is_visible():
                    button.first.click();page.wait_for_timeout(4000);capture('dismissed');break
            capture('map')
        else:
            title=page.get_by_role('heading',name='Neighborhood Association Websites',exact=True)
            title.scroll_into_view_if_needed();page.wait_for_timeout(1000);capture('directory')
        S.save(P+f'evidence-{4+n}.json',r)
        page.close()
    browser.close()
