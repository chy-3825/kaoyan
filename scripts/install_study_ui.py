"""Synchronize shared study UI into the three standalone applications."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
for name in ('calculus', 'linear-algebra', 'probability'):
    base = ROOT / 'apps' / name
    web = base / 'android/web'
    for filename in ('study-ui.js', 'study-ui.css'):
        shutil.copy2(ROOT / 'scripts' / filename, web / filename)
    vendor = web / 'vendor/katex'
    vendor.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'scripts/KATEX-LICENSE.txt', vendor / 'LICENSE.txt')
    for filename in ('katex.min.js', 'katex.min.css'):
        shutil.copy2(Path('/tmp/yanxi-katex-dist/katex') / filename, vendor / filename)
    shutil.copytree('/tmp/yanxi-katex-dist/katex/fonts', vendor / 'fonts', dirs_exist_ok=True)
    path = web / 'index.html'
    s = path.read_text()
    if 'study-ui.js' not in s:
        s = s.replace('  <script defer src="app.js"></script>', '  <link rel="stylesheet" href="vendor/katex/katex.min.css">\n  <link rel="stylesheet" href="study-ui.css">\n  <script defer src="vendor/katex/katex.min.js"></script>\n  <script defer src="study-ui.js"></script>\n  <script defer src="app.js"></script>')
    path.write_text(s)
    path = web / 'app.js'
    s = path.read_text()
    if 'StudyUI.migrate(state, bank)' not in s:
        s = s.replace('for (const [id, item] of Object.entries(state.explanationCache || {}))', 'state = StudyUI.migrate(state, bank);\nStudyUI.applyFont();\nfor (const [id, item] of Object.entries(state.explanationCache || {}))', 1)
    if 'StudyUI.migrate(state, bank)' not in s:
        pass
    else:
        path.write_text(s)
        s = None
    if s is None:
        java = next((base / 'android/src').rglob('MainActivity.java'))
        java.write_text(java.read_text().replace('path.matches("/images/[a-zA-Z0-9._-]+\\\\.webp")','path.matches("/images/(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+\\\\.webp")'))
        continue
    s = re.sub(r'const examSource = q =>[\s\S]*?;\nconst questionKey', 'const examSource = q => StudyUI.sourceLabel(q);\nconst questionKey', s, count=1)
    s = s.replace('q.options', '(q.textOptions || q.options)')
    s = s.replace("esc((q.textOptions || q.options)[letter] || '')", "StudyUI.rich((q.textOptions || q.options)[letter] || '')")
    s = s.replace('${esc(answerLabel)}', '${StudyUI.rich(answerLabel)}')
    s = re.sub(r'      \$\{q.image \? .*?\}\n      \$\{options\}', '      ${StudyUI.question(q)}\n      ${options}', s)
    start = s.index('  const answerContent =')
    end = s.index('\n', start)
    s = s[:start] + '''  const answerContent = showAnswer ? `<section class="answer-panel"><div class="answer-heading">参考答案 ${esc(q.answer || '')}</div>${StudyUI.reference(q)}${q.questionType === 'single' ? '' : `<div class="self-assess"><button class="self-correct" data-action="self-correct">正确</button><button class="self-wrong" data-action="self-wrong">错误</button></div>`}</section>` : '';''' + s[end:]
    s = s.replace('${rating(q.difficulty)}</div><div class="question-topic">', '${rating(q.difficulty)}${StudyUI.star(q)}</div><div class="question-topic">')
    s = s.replace('<div class="home-actions">', '<div class="home-actions"><button class="home-action" data-action="favorites"><span class="action-symbol">☆</span><strong>收藏夹</strong><span class="action-count">${Object.keys(state.favorites || {}).length}</span><span class="action-arrow">›</span></button>')
    s = s.replace("else if (page === 'mistakes')", "else if (page === 'favorites') app.innerHTML = StudyUI.favoritesView();\n  else if (page === 'mistakes')")
    s = s.replace('<h1>设置</h1></div>', '<h1>设置</h1></div>${StudyUI.readingSettings()}')
    s = s.replace("case 'home':", "case 'favorites': go('favorites'); break;\n    case 'toggle-favorite': StudyUI.toggleFavorite(); break;\n    case 'review-favorites': StudyUI.startFavorites(); break;\n    case 'home':")
    s = s.replace('const source = payload.state;', 'const source = StudyUI.migrate(payload.state, bank);')
    s = s.replace('      cursorByTopic: cursors,', '      cursorByTopic: cursors,\n      favorites: entriesForQuestions(source.favorites, item => item && typeof item === "object"),\n      fontSize: [18,20,22].includes(source.fontSize) ? source.fontSize : 18,')
    s = s.replace("review ? 'mistakes' : 'topicQuestions'", "review ? (review.kind === 'favorites' ? 'favorites' : 'mistakes') : 'topicQuestions'")
    s = s.replace("review ? '错题本' : '题目列表'", "review ? (review.kind === 'favorites' ? '收藏夹' : '错题本') : '题目列表'")
    s = s.replace("review ? '错题复习' :", "review ? (review.kind === 'favorites' ? '收藏练习' : '错题复习') :")
    s = s.replace('if (review) {\n      review.ids.splice', "if (review && review.kind !== 'favorites') {\n      review.ids.splice")
    s = s.replace('if (review) {\n    review.ids.splice', "if (review && review.kind !== 'favorites') {\n    review.ids.splice")
    s = s.replace("if (review) go('mistakes');", "if (review) go(review.kind === 'favorites' ? 'favorites' : 'mistakes');")
    s = s.replace("if (review) { go('mistakes'); return true; }", "if (review) { go(review.kind === 'favorites' ? 'favorites' : 'mistakes'); return true; }")
    s = s.replace('原创高频考点练习独立推导，核对给出的参考答案；不要把它称为历年真题', '历年真题独立推导，核对给出的参考答案')
    s = s.replace('if (q.isSupplemental && q.questionText)', 'if (q.questionText)')
    s = s.replace('${q.exam} · 原创高频考点补充题（非真题）', '${examSource(q)} · 历年真题')
    s = s.replace("${q.isSupplemental?'复制整题':'分享原题图'}", '复制题目')
    path.write_text(s)
    java = next((base / 'android/src').rglob('MainActivity.java'))
    s = java.read_text()
    marker = 'assets.put("/app.js","application/javascript");'
    extra = '\n        assets.put("/study-ui.js","application/javascript"); assets.put("/study-ui.css","text/css");\n        assets.put("/vendor/katex/katex.min.js","application/javascript"); assets.put("/vendor/katex/katex.min.css","text/css");\n'
    fonts = vendor / 'fonts'
    extra += ''.join('        assets.put("/vendor/katex/fonts/'+p.name+'","'+ {'woff2':'font/woff2','woff':'font/woff','ttf':'font/ttf'}[p.suffix[1:]]+'");\n' for p in sorted(fonts.iterdir()) if p.suffix[1:] in ('woff2','woff','ttf'))
    java.write_text(s.replace(marker, marker + extra))
