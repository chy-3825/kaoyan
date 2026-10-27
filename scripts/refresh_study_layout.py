"""Apply the shared layout to standalone math apps and synchronize assets."""
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
for name in ('calculus','linear-algebra','probability'):
    base=ROOT/'apps'/name
    web=base/'android/web'
    path=web/'app.js'
    s=path.read_text()
    if '${StudyUI.dock(q,index,list.length)}' not in s:
        s=s.replace("const options = q.questionType === 'single' &&", "const options = !q.image && q.questionType === 'single' &&",1)
        s=re.sub(r'<div class="question-meta">.*?</div><div class="question-topic">', '${StudyUI.meta(q)}<div class="question-topic">',s,count=1)
        s=re.sub(r'      <div class="question-tools">.*?</div>\n', '',s,count=1)
        s=re.sub(r'</article><nav class="bottom-nav">.*?</nav></div>', '</article>${StudyUI.dock(q,index,list.length)}</div>',s,count=1)
        s=s.replace("q.answerText||q.answerImage?", "q.analysisRich||q.answerRich||q.answerText||q.answerImage?")
        s=s.replace("${q.questionType==='fill'?'核对答案':'完成作答 · 查看答案'}", '查看答案与解析')
        s=s.replace("else if (page === 'settings') app.innerHTML = settingsView();", "else if (page === 'settings') app.innerHTML = settingsView();\n  StudyUI.polish();")
        s=s.replace('DeepSeek 解析</button>', 'AI 进一步讲解</button>')
        path.write_text(s)
    for asset in ('study-ui.js','study-ui.css'):
        shutil.copy2(ROOT/'scripts'/asset,web/asset)

for doc in [ROOT/'README.md',*(ROOT/'apps'/name/'README.md' for name in ('calculus','linear-algebra','probability'))]:
    doc.write_text(doc.read_text().replace('1.2.1','1.3.0'))
