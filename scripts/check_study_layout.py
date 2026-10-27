"""Check mobile dock, image reading, text clipboard, and reversible collection actions."""
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/microsoft-edge',headless=True,args=['--no-sandbox'])
        for name in ('calculus','linear-algebra','probability'):
            for width in (320,390):
                page=browser.new_page(viewport={'width':width,'height':844})
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/apps/{name}/android/web/index.html')
                assert page.locator('.home-action').evaluate_all('(els)=>els.map(e=>e.dataset.action)')==['directory','mistakes','favorites']
                page.screenshot(path=f'/tmp/layout-{name}-{width}-home.png',full_page=True)
                page.evaluate("window.AndroidApp={copyText:t=>{window.copied=t;return true}};const q=bank.find(q=>q.questionType==='single'&&q.analysisRich);openQuestion(questionKey(q),byTopic(questionKey(q)).findIndex(x=>x.id===q.id));")
                page.wait_for_function("document.querySelector('.question-image').naturalWidth>0")
                assert page.locator('.written-options').count()==0
                assert page.locator('.choice-chip').count()==4
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                dock=page.locator('.study-dock').bounding_box()
                assert abs(dock['y']+dock['height']-844)<2
                page.locator('.dock-tools [data-action="share"]').click()
                assert page.evaluate('copied.includes(current().questionText)')
                page.locator('.favorite-toggle').click()
                assert page.locator('.favorite-toggle').get_attribute('aria-pressed')=='true'
                page.locator('[data-action="zoom-question"]').click()
                assert page.locator('#image-view').evaluate('d=>d.open')
                page.locator('[data-action="close-image"]').click()
                page.screenshot(path=f'/tmp/layout-{name}-{width}-question.png',full_page=True)
                page.locator('.dock-tools [data-action="toggle-answer"]').click()
                assert page.locator('.answer-panel').count()==1
                assert page.locator('.ai-followup').count()==1
                page.evaluate("go('favorites')")
                page.wait_for_function("document.querySelector('.favorite-preview img').naturalWidth>0")
                page.screenshot(path=f'/tmp/layout-{name}-{width}-favorites.png',full_page=True)
                page.locator('.favorite-remove').click()
                assert page.locator('.favorite-row').count()==0
                page.locator('[data-undo-favorite]').click()
                assert page.locator('.favorite-row').count()==1
                page.reload()
                assert page.evaluate('Object.keys(state.favorites).length')==1
                assert not errors,errors
                page.close()
                print(name,width,'PASS',flush=True)
        browser.close()
finally:server.shutdown()
