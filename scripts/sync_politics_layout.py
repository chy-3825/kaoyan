"""Synchronize politics presentation without replacing platform-specific behavior."""
from pathlib import Path
import re
import shutil
ROOT=Path(__file__).resolve().parents[1]
web=ROOT/'apps/politics/android/web'
for target in (web,ROOT/'apps/politics/app/dist'):
    if target!=web:
        for filename in ('design.js','design.css'):shutil.copy2(web/filename,target/filename)
    p=target/'index.html';s=p.read_text()
    if 'design.js' not in s:
        s=s.replace('<script defer src="app.js"></script>','<link rel="stylesheet" href="design.css"><script defer src="design.js"></script><script defer src="app.js"></script>')
    s=s.replace('content="#f7f5f0"','content="#f4f6f7"');p.write_text(s)
    p=target/'app.js';s=p.read_text()
    if 'PoliticsDesign.dock' not in s:
        s=re.sub(r'<div class="question-tools">.*?</div></article>', '</article>',s,count=1)
        s=re.sub(r'<nav class="bottom-nav">.*?</nav></div>', '${PoliticsDesign.dock(index,total)}</div>',s,count=1)
        s=s.replace(": page === 'settings' ? settingsView() : mistakesView();", ": page === 'settings' ? settingsView() : mistakesView();\n  PoliticsDesign.polish();")
        p.write_text(s)
