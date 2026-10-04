"""Read-only desktop Chromium rendering and supporting official-source captures."""
import argparse, hashlib, json, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
import InteractiveAppResolution as I

SCRATCH=I.G.ROOT/'research/staging'/I.TASK
SCRATCH.mkdir(parents=True,exist_ok=True)

def render(url,number,actions=None):
    I.G.active_check('mutation','document_review')
    result=dict(requested_url=url,observed_at_utc=I.S.now(),viewport={'width':1440,'height':1000},tool='Python Playwright with installed Google Chrome',screenshots=[],frames=[],errors=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        context=browser.new_context(viewport=result['viewport'])
        page=context.new_page()
        page.on('pageerror',lambda e:result['errors'].append(str(e)[:600]))
        try:
            response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
            result['http_status']=response.status if response else None
            page.wait_for_timeout(18000)
        except Exception as e:result['navigation_error']=str(e)
        result['resolved_url']=page.url if '/oauth2/authorize' not in page.url else page.url.split('?')[0]+'?generated_oauth_parameters=redacted'
        result['interactions']=[]
        for action in actions or []:
            try:
                page.get_by_role(action.get('role','button'),name=action['name'],exact=action.get('exact',True)).click(timeout=8000)
                page.wait_for_timeout(4000)
                result['interactions'].append(dict(action=action,visible_text=page.locator('body').inner_text()[:45000]))
            except Exception as e:result['interactions'].append(dict(action=action,error=str(e)))
        try:result['visible_title']=page.title()
        except Exception as e:result['title_error']=str(e)
        for frame in page.frames:
            try:result['frames'].append(dict(url=frame.url,visible_text=frame.locator('body').inner_text(timeout=5000)[:60000],links=frame.locator('a').evaluate_all('(xs)=>xs.filter(x=>x.getClientRects().length).map(x=>({text:x.innerText,url:x.href})).filter(x=>!x.url.includes("translate.google"))'),iframe_sources=frame.locator('iframe').evaluate_all('(xs)=>xs.map(x=>x.src)'),controls=frame.locator('button,[role=button],input,select').evaluate_all('(xs)=>xs.filter(x=>x.getClientRects().length).map(x=>({tag:x.tagName,text:x.innerText,label:x.getAttribute("aria-label"),title:x.title}))')))
            except Exception as e:result['frames'].append(dict(url=frame.url,error=str(e)))
        image=SCRATCH/f'render-{number}.png';page.screenshot(path=str(image),full_page=False)
        result['screenshots'].append(dict(path=image.relative_to(I.G.ROOT).as_posix(),sha256=hashlib.sha256(image.read_bytes()).hexdigest(),bytes=image.stat().st_size,committed=False))
        browser.close()
    for f in result['frames']:
        if '/oauth2/authorize' in f['url']:f['url']=f['url'].split('?')[0]+'?generated_oauth_parameters=redacted'
    I.save(I.P+f'render-{number}.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='frames'},ensure_ascii=True,indent=2))
    for f in result['frames']:print(json.dumps({k:v for k,v in f.items() if k!='links'},ensure_ascii=True,indent=2))

def fetch(url,number):
    result=dict(requested_url=url,observed_at_utc=I.S.now(),role='Supporting authoritative-source evidence; not rendered usability proof')
    try:
        with urllib.request.urlopen(url,timeout=40) as r:
            data=r.read();result.update(resolved_url=r.url,http_status=r.status,content_type=r.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        try:result['data']=json.loads(data)
        except Exception:result['text']=data.decode('utf-8',errors='replace')
    except Exception as e:result['error']=str(e)
    I.save(I.P+f'evidence-{number}.json',result)
    print(json.dumps(result,ensure_ascii=True,indent=2)[:14000])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('number',type=int);p.add_argument('--fetch',action='store_true');p.add_argument('--actions');a=p.parse_args();fetch(a.url,a.number) if a.fetch else render(a.url,a.number,json.loads(a.actions) if a.actions else None)
