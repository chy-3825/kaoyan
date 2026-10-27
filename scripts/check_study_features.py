"""Mobile regression checks for text, favorites, outline controls, and migration."""
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/microsoft-edge', headless=True, args=['--no-sandbox'])
        for name, count in [('calculus',650),('linear-algebra',183),('probability',149)]:
            page = browser.new_page(viewport={'width':390,'height':844})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/apps/{name}/android/web/index.html')
            page.wait_for_function('typeof StudyUI !== "undefined" && typeof bank !== "undefined"')
            assert page.evaluate('bank.length') == count
            page.evaluate("const q=bank.find(q=>q.questionType==='solve');openQuestion(questionKey(q),byTopic(questionKey(q)).findIndex(x=>x.id===q.id))")
            assert page.locator('.question-image').evaluate('(img)=>img.complete && img.naturalWidth>0')
            page.locator('[data-action="toggle-favorite"]').click()
            page.locator('[data-action="zoom-question"]').click()
            assert page.locator('#image-view').evaluate('(dialog)=>dialog.open')
            page.locator('[data-action="close-image"]').click()
            page.locator('[data-action="reveal"]').click()
            for selector, color in [('.self-correct','rgb(46, 125, 50)'),('.self-wrong','rgb(198, 40, 40)')]:
                style = page.locator(selector).evaluate('(e)=>{const s=getComputedStyle(e);return [s.color,s.borderTopColor,s.backgroundColor]}')
                assert style == [color,color,'rgb(255, 255, 255)'], style
            page.locator('[data-action="self-wrong"]').click()
            page.evaluate("go('favorites')")
            assert page.locator('.favorite-row').count() == 1
            page.locator('[data-action="review-favorites"]').click()
            page.locator('[data-action="self-correct"]').click()
            assert page.evaluate('review.ids.length') == 1
            page.screenshot(path=f'/tmp/yanxi-{name}-text.png',full_page=True)
            page.reload()
            page.wait_for_function('typeof state !== "undefined"')
            assert page.evaluate('Object.keys(state.favorites).length') == 1
            assert page.evaluate('''()=>{const q=bank.find(q=>q.aliases.length>1);const s=StudyUI.migrate({favorites:{[q.aliases[1]]:{at:1}},attempts:{[q.aliases[1]]:{correct:true,at:2}}},bank);return !!s.favorites[q.id]&&s.attempts[q.id].correct}''')
            assert not errors, errors
            print(name, 'PASS', flush=True)
            # Parse every formula, including reference answers and analyses.
            failures = page.evaluate('''()=>{let fail=[];for(const q of bank){for(const [field,text] of Object.entries({prompt:q.questionText,...q.textOptions,answer:q.answerRich,analysis:q.analysisRich})){for(const m of String(text||'').matchAll(/\\$\\$([\\s\\S]*?)\\$\\$|\\$([^$]*?)\\$/g)){try{katex.renderToString(m[1]??m[2],{throwOnError:true,strict:'ignore'})}catch(e){fail.push([q.id,field,m[1]??m[2],e.message])}}}}return fail}''')
            print(name,'formula parse failures',len(failures), failures[:8],flush=True)
            page.close()
        browser.close()
finally:
    server.shutdown()
