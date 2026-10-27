#!/usr/bin/env python3
"""Build deduplicated past-paper banks with source text and stable legacy ID mappings."""
import hashlib
import importlib.util
import json
import re
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / 'sources/math-bank/text'
SUBJECTS = {'calculus': '高等数学', 'linear-algebra': '线性代数', 'probability': '概率论与数理统计'}
MANUAL_EXPLANATIONS = runpy.run_path(str(TEXT / 'manual_explanations.py'))['MANUAL_EXPLANATIONS']


def clean(text):
    text = text.replace(r'\underline{___}', r'\underline{\qquad}')
    text = text.replace(r'{x^{\alpha}\cos \frac{1}{x^{\beta}},}&{x>0,\\0,&x\leqslant 0}', r'x^{\alpha}\cos \frac{1}{x^{\beta}},&x>0,\\0,&x\leqslant 0')
    text = text.replace(r'{\frac{\mathrm{e}^{x}-1}{x},}&{x\neq0,\\{1,}&{x=0}', r'\frac{\mathrm{e}^{x}-1}{x},&x\neq0,\\1,&x=0')
    text = re.sub(r'<equation>(.*?)</equation>', lambda m: '$' + m[1].strip() + '$', text, flags=re.S)
    text = re.sub(r'```(?:latex|math)?\s*\n?(.*?)```', lambda m: '$$' + m[1].strip() + '$$', text, flags=re.S)
    text = re.sub(r'\n\s*---+\s*(?=\n|$)', '', text)
    text = re.sub(r'^\*\*.*?\*\*\s*$', '', text, flags=re.M)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.M)
    return text.strip()


def split_choices(prompt):
    masked = re.sub(r'\$\$.*?\$\$|\$[^$]*\$', lambda m: ' ' * len(m[0]), prompt, flags=re.S)
    markers = list(re.finditer(r'(?<![A-Za-z])[（(]?([ABCD])[.．、)）]\s*', masked))
    for start in range(len(markers)):
        four = markers[start:start+4]
        if len(four) == 4 and {m[1] for m in four} == set('ABCD'):
            options = {m[1]: prompt[m.end():four[i+1].start() if i < 3 else len(prompt)].strip() for i, m in enumerate(four)}
            return prompt[:four[0].start()].strip(), options
    return prompt, {}


def fingerprint(text):
    text = clean(text)
    for command in ('left', 'right', 'displaystyle', 'textstyle', 'quad', 'qquad'):
        text = re.sub(r'\\' + command + r'\b', '', text)
    text = re.sub(r'\\(?:mathrm|operatorname|text)\s*\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\\[,;! ]', '', text)
    text = text.replace('′', r'\prime').replace('（', '(').replace('）', ')')
    return re.sub(r'[\s$，。；：、,.!?！？;:]', '', text)


def build(name):
    app = ROOT / 'apps' / name
    source = [q for q in map(json.loads, (ROOT / 'sources/math-bank/data/questions.jsonl').read_text().splitlines()) if q['subject'] == SUBJECTS[name]]
    # Use previously reviewed chapter/topic labels from the subject app.
    metadata = {q['id']: q for q in map(json.loads, (app / 'data/questions.jsonl').read_text().splitlines())}
    raw_past = app / 'data/past_questions.jsonl'
    if raw_past.exists():
        metadata.update({q['id']: q for q in map(json.loads, raw_past.read_text().splitlines())})
    transcripts = json.loads((TEXT / 'index.json').read_text())
    spec = importlib.util.spec_from_file_location('manual', TEXT / 'manual_transcripts.py')
    manual = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manual)
    rows = []
    for original in source:
        q = dict(metadata.get(original['id'], original))
        # Existing enriched rows must not feed their merged metadata back into inputs.
        for field in ('aliases', 'sources', 'questionText', 'textOptions', 'answerRich', 'analysisRich', 'textSource'):
            q.pop(field, None)
        if name == 'calculus':
            chapter = q['chapter']
            if chapter == '函数、极限、连续': chapter = '函数、极限与连续'
            if chapter == '常微分方程': chapter = '常微分方程与差分方程'
            if chapter == '多元函数微积分学': chapter = '多元函数积分学' if '积分' in q['topic'] else '多元函数微分学'
            q['chapter'] = chapter
            q['topicPath'] = f"{q['subject']}/{chapter}/{q['topic']}"
        key = f"{q['exam']}/{q['examYear']}/{q['questionNo']}"
        transcript = transcripts.get(key, {})
        if q['id'] in manual.TRANSCRIPTS:
            prompt, options = manual.TRANSCRIPTS[q['id']]
            options = dict(zip('ABCD', options)) if options else {}
            text_source = 'bundled-original-question-image'
        else:
            prompt = clean(transcript.get('prompt', ''))
            prompt, options = split_choices(prompt) if q['questionType'] == 'single' else (prompt, {})
            text_source = transcript.get('source', '')
        if not prompt or (q['questionType'] == 'single' and len(options) != 4):
            raise ValueError(f"{q['id']}: missing text or four options")
        q.update(questionText=clean(prompt), textOptions={k: clean(v) for k, v in options.items()}, textSource=text_source,
                 answerRich=clean(transcript.get('answer', '')), analysisRich=clean(transcript.get('analysis', '')))
        q['sources'] = [{k: original.get(k) for k in ('id', 'exam', 'examYear', 'questionNo', 'image', 'answerImage', 'answer', 'sourceUrl')}]
        q['aliases'] = [original['id']]
        rows.append(q)
    # Union only exact image matches or normalized full prompts AND all options.
    parents = list(range(len(rows)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, q in enumerate(rows):
        image = app / 'android/web' / q['image']
        correct = fingerprint(q['textOptions'].get(q.get('answer'), q.get('answer') or '')) if q['questionType'] == 'single' else ''
        content = fingerprint(q['questionText']) + '|' + '|'.join(fingerprint(q['textOptions'].get(c, '')) for c in 'ABCD')
        keys = [('image', q['questionType'], hashlib.sha256(image.read_bytes()).hexdigest()),
                ('text', q['questionType'], content, correct)]
        for key in keys:
            if key in seen:
                a, b = find(i), find(seen[key])
                parents[max(a,b)] = min(a,b)
            else:
                seen[key] = i
    groups = {}
    for i, row in enumerate(rows): groups.setdefault(find(i), []).append(row)
    unique = []
    for members in groups.values():
        q = dict(members[0])
        q['aliases'] = [r['id'] for r in members]
        q['sources'] = [s for r in members for s in r['sources']]
        # A longer textual solution is useful when another source has only an answer scan.
        q['answerRich'] = max((r['answerRich'] for r in members), key=len)
        analyses = [r['analysisRich'] for r in members if r['analysisRich']]
        q['analysisRich'] = max(analyses, key=len) if analyses else next((MANUAL_EXPLANATIONS[r['id']] for r in members if r['id'] in MANUAL_EXPLANATIONS), '')
        q['answerImage'] = next((r['answerImage'] for r in members if r.get('answerImage')), q.get('answerImage', ''))
        unique.append(q)
    unique.sort(key=lambda q: (q['chapter'],q['topic'],q['examYear'],q['exam'],q['questionNo']))
    def write_rows(path, values):
        path.write_text(''.join(json.dumps(q, ensure_ascii=False, separators=(',', ':')) + '\n' for q in values), encoding='utf-8')
    # Raw past-paper inputs preserve every original exam reference for reproducibility.
    write_rows(raw_past, [{k:v for k,v in q.items() if k not in ('aliases','sources','questionText','textOptions','textSource','answerRich','analysisRich')} for q in rows])
    write_rows(app / 'data/questions.jsonl', unique)
    (app / 'android/web/questions.js').write_text('window.QUESTIONS=' + json.dumps(unique, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    summary = {'total':len(unique), 'pastExam':len(unique), 'sourceEntries':len(source), 'mergedEntries':len(source)-len(unique), 'supplemental':0,
               'byChapter':dict(Counter(q['chapter'] for q in unique)), 'types':dict(Counter(q['questionType'] for q in unique)),
               'textQuestions':len(unique), 'note':'仅真题，合并完全相同题目并保留所有原题 ID 与试卷来源。题源文字并非全部人工校对，支持查看原图。'}
    (app / 'data/summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    (app / 'data/duplicate_groups.json').write_text(json.dumps([q['sources'] for q in unique if len(q['sources'])>1], ensure_ascii=False, indent=2)+'\n')
    print(name, summary['sourceEntries'], 'source entries ->', len(unique), 'text questions; merged', summary['mergedEntries'])


if __name__ == '__main__':
    import sys
    for name in sys.argv[1:] or SUBJECTS: build(name)
