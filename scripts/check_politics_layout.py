"""Exercise politics layout and single/multiple choice behavior on both clients."""
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
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
        for layout in ('android/web','app/dist'):
            for width in (320,390):
                page=browser.new_page(viewport={'width':width,'height':844})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/apps/politics/{layout}/index.html')
                assert page.title()=='研习政治'
                assert page.evaluate('bank.length')==1500
                page.screenshot(path=f'/tmp/politics-{width}-home.png',full_page=True)
                page.evaluate("window.AndroidApp={copyText:t=>{window.copied=t;return true}};const q=bank.find(q=>q.questionType==='single');openQuestion(q.topicTag,byTag(q.topicTag).findIndex(x=>x.id===q.id));")
                assert page.locator('.option').count()==4
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                box=page.locator('.study-dock').bounding_box();assert abs(box['y']+box['height']-844)<2
                page.locator('.dock-tool[data-action="copy"]').click()
                assert page.evaluate('copied.includes(current().stem)')
                page.locator('.dock-tool[data-action="explain"]').click()
                assert page.locator('#explanation').evaluate('e=>e.open')
                page.locator('[data-action="close"]').click()
                answer=page.evaluate('current().answer')
                page.locator(f'[data-choice="{answer}"]').click()
                assert page.locator('.result.correct').count()==1
                page.evaluate("const q=bank.find(q=>q.questionType==='multiple');openQuestion(q.topicTag,byTag(q.topicTag).findIndex(x=>x.id===q.id));")
                assert page.locator('[data-action="submit"]').is_disabled()
                answers=page.evaluate('current().answer')
                for a in answers:page.locator(f'[data-choice="{a}"]').click()
                assert page.locator('.result').count()==0
                page.screenshot(path=f'/tmp/politics-{width}-question.png',full_page=True)
                page.locator('[data-action="submit"]').click()
                assert page.locator('.result.correct').count()==1
                page.evaluate("const q=bank.find(q=>q.questionType==='single'&&!state.attempts[q.id]);openQuestion(q.topicTag,byTag(q.topicTag).findIndex(x=>x.id===q.id));")
                wrong=page.evaluate("'ABCD'.split('').find(a=>a!==current().answer)")
                page.locator(f'[data-choice="{wrong}"]').click()
                assert page.locator('.result.wrong').count()==1
                page.evaluate('startReview()')
                assert page.locator('.dock-navigation [data-action="next"]').inner_text().strip()=='完成复习'
                page.locator('.dock-navigation [data-action="next"]').click()
                page.reload()
                assert page.evaluate('Object.keys(state.attempts).length')==3
                assert not errors,errors
                page.close();print(layout,width,'PASS',flush=True)
        browser.close()
finally:server.shutdown()
