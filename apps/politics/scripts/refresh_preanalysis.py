#!/usr/bin/env python3
"""Refresh generated offline notes and write a content coverage audit."""
from __future__ import annotations
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from preanalysis import generate_preanalysis

BANK = ROOT / 'data/questions.jsonl'
rows = [json.loads(line) for line in BANK.read_text(encoding='utf8').splitlines() if line.strip()]
for row in rows:
    if row.get('explanationKind') == 'generated':
        row['explanation'] = generate_preanalysis(row)
    elif row.get('explanation', '').strip():
        row['explanationReviewStatus'] = 'source_provided'

counts = collections.Counter()
by_topic = collections.defaultdict(collections.Counter)
invalid = []
for row in rows:
    status = row.get('explanationReviewStatus', 'missing')
    counts[status] += 1
    by_topic[row.get('topicTag', '未分类')][status] += 1
    answer = ''.join(ch for ch in str(row.get('answer', '')).upper() if ch in 'ABCD')
    if not answer or answer != str(row.get('answer', '')).upper() or any(ch not in row.get('options', {}) for ch in answer):
        invalid.append(row.get('id'))
    if not row.get('explanation', '').strip():
        invalid.append(row.get('id'))

report = {
    'total': len(rows),
    'sourceProvidedExplanations': counts['source_provided'],
    'generatedWithSpecificRationaleRule': counts['specific_rationale'],
    'generatedAnswerHintsNeedSubjectReview': counts['answer_hint'],
    'invalidAnswerOrMissingExplanation': sorted(set(invalid)),
    'byCourse': {tag: dict(topic_counts) for tag, topic_counts in sorted(by_topic.items())},
    'note': 'A matched rationale rule is a focused draft, not independent expert verification. Answer hints explicitly lack item-specific distractor analysis.'
}
(ROOT / 'data/preanalysis_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
summary_path = ROOT / 'data/summary.json'
summary = json.loads(summary_path.read_text(encoding='utf8'))
summary['total'] = len(rows)
summary['withPreanalysis'] = sum(bool(row.get('explanation', '').strip()) for row in rows)
summary['generatedPreanalysis'] = sum(row.get('explanationKind') == 'generated' for row in rows)
summary['generatedWithSpecificRationaleRule'] = counts['specific_rationale']
summary['generatedAnswerHintsNeedSubjectReview'] = counts['answer_hint']
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
canonical = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
BANK.write_text(canonical, encoding='utf8')
js = 'window.QUESTIONS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';'
for path in (ROOT / 'app/dist/questions.js', ROOT / 'android/web/questions.js'):
    path.write_text(js, encoding='utf8')
print(json.dumps({key: report[key] for key in ('total', 'sourceProvidedExplanations', 'generatedWithSpecificRationaleRule', 'generatedAnswerHintsNeedSubjectReview', 'invalidAnswerOrMissingExplanation')}, ensure_ascii=False))
