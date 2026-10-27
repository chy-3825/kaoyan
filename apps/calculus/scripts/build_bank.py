#!/usr/bin/env python3
"""Validate and assemble the standalone, offline calculus question bank."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
WEB = ROOT / 'android/web'
CHAPTERS = ['函数、极限与连续', '一元函数微分学', '一元函数积分学',
            '空间解析几何与向量代数', '多元函数微分学', '多元函数积分学',
            '无穷级数', '常微分方程与差分方程']
EXAMS = ['数学一', '数学二', '数学三']


def normalize(row):
    row = dict(row)
    chapter = row['chapter']
    if chapter == '函数、极限、连续':
        chapter = '函数、极限与连续'
    elif chapter == '常微分方程':
        chapter = '常微分方程与差分方程'
    elif chapter == '多元函数微积分学':
        chapter = '多元函数积分学' if '积分' in row['topic'] else '多元函数微分学'
    row['chapter'] = chapter
    row['topicPath'] = f"{row['subject']}/{chapter}/{row['topic']}"
    return row


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(q, ensure_ascii=False, separators=(',', ':')) + '\n' for q in rows), encoding='utf-8')


def main():
    groups = []
    for filename, expected, supplemental in [('past_questions.jsonl', 773, False), ('supplemental_questions.jsonl', 152, True)]:
        rows = [normalize(json.loads(line)) for line in (DATA / filename).read_text().splitlines() if line.strip()]
        if len(rows) != expected or any(q['subject'] != '高等数学' or bool(q.get('isSupplemental')) != supplemental for q in rows):
            raise SystemExit(f'{filename}: expected {expected} calculus questions with correct source labels')
        groups.append(rows)
    past, supplemental = groups
    rows = sorted(past + supplemental, key=lambda q: (CHAPTERS.index(q['chapter']), q['topic'], q.get('examYear') or 9999, EXAMS.index(q['exam']), q.get('questionNo') or 9999, q['id']))
    if len({q['id'] for q in rows}) != len(rows):
        raise SystemExit('Duplicate question IDs')
    for q in rows:
        if not (q.get('image') or q.get('questionText')) or not (q.get('answer') or q.get('answerText') or q.get('answerImage')):
            raise SystemExit(f"Missing prompt or answer: {q['id']}")
        if q['exam'] not in EXAMS or q['questionType'] not in ('single', 'fill', 'solve'):
            raise SystemExit(f"Invalid exam or question type: {q['id']}")
        if q.get('isSupplemental'):
            if q.get('examYear') is not None or q.get('questionNo') is not None:
                raise SystemExit(f"Supplemental question labeled as past exam: {q['id']}")
        elif not (2009 <= q.get('examYear', 0) <= 2026 and q.get('questionNo')):
            raise SystemExit(f"Missing past exam provenance: {q['id']}")
        if q['questionType'] == 'single' and q.get('answer') not in ('A', 'B', 'C', 'D'):
            raise SystemExit(f"Invalid choice key: {q['id']}")
        for field in ('image', 'answerImage'):
            if q.get(field):
                path = (WEB / q[field]).resolve()
                if not path.is_relative_to(WEB.resolve()) or not path.is_file():
                    raise SystemExit(f"Missing or unsafe {field}: {q['id']}")
    for exam in EXAMS:
        if {q['examYear'] for q in past if q['exam'] == exam} != set(range(2009, 2027)):
            raise SystemExit(f'Missing exam years: {exam}')
    for filename, values in [('past_questions.jsonl', past), ('supplemental_questions.jsonl', supplemental), ('questions.jsonl', rows)]:
        write_rows(DATA / filename, values)
    (WEB / 'questions.js').write_text('window.QUESTIONS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    summary = {'total': len(rows), 'pastExam': len(past), 'supplemental': len(supplemental), 'byExam': dict(Counter(q['exam'] for q in rows)), 'pastByExam': dict(Counter(q['exam'] for q in past)), 'supplementalByExam': dict(Counter(q['exam'] for q in supplemental)), 'byChapter': dict(Counter(q['chapter'] for q in rows)), 'types': dict(Counter(q['questionType'] for q in rows)), 'note': '数学一、二、三全部高等数学题，保留原题 ID、题源、答案和难度；章节名称统一，补充练习单独标记。'}
    (DATA / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'calculus: {len(rows)} questions ({len(past)} past + {len(supplemental)} supplemental), {len(CHAPTERS)} chapters')


if __name__ == '__main__':
    main()
