#!/usr/bin/env python3
"""Browser image loading, mobile rendering and zoom smoke check (requires Playwright)."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import os, tempfile
ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=Path(tempfile.mkdtemp(prefix='yanxi-image-ui-'))
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE'),headless=True,args=['--no-sandbox'])
 for name,layout in [('calculus','android/web'),('probability','android/web'),('linear-algebra','android/web'),('politics','android/web'),('politics','app/dist')]:
  page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  url=f'http://127.0.0.1:{server.server_port}/apps/{name}/{layout}/index.html';page.goto(url)
  page.wait_for_function('window.QUESTIONS?.length > 0')
  rows=page.evaluate('window.QUESTIONS')
  refs=sorted(set(q[k] for q in rows for k in ['image','answerImage'] if q.get(k)))
  failures=page.evaluate('''async refs => {
    const bad=[];
    for(let i=0;i<refs.length;i+=30) await Promise.all(refs.slice(i,i+30).map(src=>new Promise(resolve=>{
      const img=new Image();img.onload=()=>{if(!img.naturalWidth)bad.push(src);resolve()};img.onerror=()=>{bad.push(src);resolve()};img.src=src;
    })));
    return bad;
  }''',refs)
  assert not failures,(name,layout,failures)
  selected=['K政治-2010-03','K政治-2012-04'] if name=='politics' else [q['id'] for q in rows if q.get('examYear')==2026][:1]
  if name=='calculus':selected=['M-8-2026-11','M-10-2026-12','M-8-2019-02']
  for id in selected:
   if name=='politics':
    page.evaluate('''id=>{const q=byId.get(id);openQuestion(q.topicTag,byTag(q.topicTag).findIndex(x=>x.id===id));}''',id)
    im=page.locator('.question-figure-image');im.wait_for();page.wait_for_function("document.querySelector('.question-figure-image')?.naturalWidth>0")
    page.screenshot(path=str(ARTIFACTS / f'{name}-{layout.replace("/","-")}-{id.split("-")[-2]}-{id.split("-")[-1]}.png'),full_page=True)
    page.locator('[data-action="zoom-question"]').click();assert page.locator('#question-image-view').evaluate('(el)=>el.open')
    page.wait_for_function("document.querySelector('#question-zoom-image').naturalWidth>0")
    page.locator('[data-action="zoom-figure"]').click();assert page.evaluate('handleAndroidBack()')
    assert not page.locator('#question-image-view').evaluate('(el)=>el.open')
   else:
    page.evaluate('''id=>{const q=byId.get(id);state.subject=q.subject;const key=questionKey(q);openQuestion(key,byTopic(key,q.subject).findIndex(x=>x.id===id));}''',id)
    page.wait_for_function("document.querySelector('.question-image')?.naturalWidth>0")
    page.screenshot(path=str(ARTIFACTS / f'{name}-{id}.png'),full_page=True)
    page.locator('[data-action="zoom-question"]').click()
    assert page.locator('#image-view').evaluate('(el)=>el.open')
    page.wait_for_function("document.getElementById('zoom-image').naturalWidth>0")
    assert page.evaluate('handleAndroidBack()')
    assert not page.locator('#image-view').evaluate('(el)=>el.open')
  assert not errors,(name,layout,errors)
  print(name,layout,len(refs),'image URLs loaded; rendering/zoom passed',flush=True)
  page.close()
 browser.close()

server.shutdown()
print('Screenshots:', ARTIFACTS)
