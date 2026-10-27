#!/usr/bin/env python3
"""Exercise the standalone calculus workflow in a mobile-size browser."""
import json
import os
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    artifacts = Path(tempfile.mkdtemp(prefix='yanxi-calculus-ui-'))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE'), headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/apps/calculus/android/web/index.html')
            page.wait_for_function('window.QUESTIONS?.length === 925')
            assert page.title() == '研习高数'
            page.screenshot(path=str(artifacts / 'home.png'), full_page=True)
            page.locator('[data-action="directory"]').click()
            assert page.locator('.chapter-card').count() == 8
            assert page.evaluate('topicsFor().flatMap(t=>t.rows).length') == 925
            assert page.evaluate('CHAPTER_ORDER.every(c=>chapterRows(c).length>0)')
            page.screenshot(path=str(artifacts / 'chapters.png'), full_page=True)
            page.locator('.chapter-card').first.click()
            assert page.locator('.subtopic-list').is_visible()
            # Use original IDs to open representatives of every question type.
            def open_type(kind):
                return page.evaluate('''kind=>{const q=bank.find(q=>q.questionType===kind && q.isSupplemental);
                    openQuestion(questionKey(q),byTopic(questionKey(q)).findIndex(x=>x.id===q.id));return q.id;}''', kind)
            single = open_type('single')
            wrong = page.evaluate("'ABCD'.split('').find(c=>c!==current().answer)")
            page.locator(f'[data-choice="{wrong}"]').click()
            assert page.locator('.result.wrong').is_visible()
            page.reload()
            page.wait_for_function('window.QUESTIONS?.length === 925')
            assert page.evaluate('pendingMistakes().length') == 1
            page.locator('[data-action="mistakes"]').click()
            page.locator('[data-action="review-all"]').click()
            correct = page.evaluate('current().answer')
            page.locator(f'[data-choice="{correct}"]').click()
            page.locator('[data-action="mastered"]').click()
            assert page.evaluate('pendingMistakes().length') == 0
            fill = open_type('fill')
            page.locator('#fill-answer').fill('练习草稿')
            page.locator('[data-action="reveal"]').click()
            assert page.locator('.answer-panel').is_visible()
            assert page.evaluate('state.drafts[current().id]') == '练习草稿'
            page.locator('[data-action="self-wrong"]').click()
            solve = open_type('solve')
            page.locator('[data-action="toggle-manual-mistake"]').click()
            assert page.evaluate('state.mistakes[current().id].count') == 0
            assert page.evaluate('state.mistakes[current().id].manual')
            page.evaluate("state.drafts[current().id]='解题草稿';save()")
            page.locator('[data-action="reveal"]').click()
            assert page.locator('.answer-panel').is_visible()
            backup = page.evaluate('backupPayload()')
            payload = json.loads(backup)
            assert payload['format'] == 'yanxi-calculus-backup'
            assert set(payload['state']['attempts']) == {single, fill}
            assert payload['state']['drafts'][solve] == '解题草稿'
            # Import filters unrelated question IDs and restores offline progress.
            payload['state']['attempts']['foreign-id'] = {'correct': True}
            page.evaluate('json=>{state.attempts={};state.mistakes={};save();restoreBackup(json)}', json.dumps(payload, ensure_ascii=False))
            assert page.evaluate('Object.keys(state.attempts).length') == 2
            assert page.evaluate('pendingMistakes().length') == 2
            assert page.evaluate("Object.hasOwn(state.mistakes, 'foreign-id')") is False
            page.evaluate("restoreBackup('{\"format\":\"yanxi-probability-backup\",\"version\":1,\"state\":{}}')")
            assert page.evaluate('Object.keys(state.attempts).length') == 2
            page.evaluate("go('settings')")
            assert '925 题' in page.locator('#app').inner_text()
            page.screenshot(path=str(artifacts / 'settings.png'), full_page=True)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not errors, errors
            browser.close()
        print('PASS: 925 questions accessible, 8 chapters, answer/review/drafts, persistence, backup isolation and mobile layout')
        print('Screenshots:', artifacts)
    finally:
        server.shutdown()


if __name__ == '__main__':
    main()
