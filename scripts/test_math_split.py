#!/usr/bin/env python3
"""Ensure the split keeps every source question and all calculus content."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calculus_bank', ROOT / 'apps/calculus/scripts/build_bank.py')
calculus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculus)


def read(path):
    return {q['id']: q for q in map(json.loads, path.read_text().splitlines())}


class MathSplitTests(unittest.TestCase):
    def test_three_apps_partition_original_bank(self):
        source = {id: q for id, q in read(ROOT / 'sources/math-bank/data/questions.jsonl').items() if not q.get('isSupplemental')}
        seen = set()
        for app, subject in [('calculus', '高等数学'), ('linear-algebra', '线性代数'), ('probability', '概率论与数理统计')]:
            rows = read(ROOT / f'apps/{app}/data/questions.jsonl')
            aliases = [id for q in rows.values() for id in q['aliases']]
            self.assertEqual(len(aliases), len(set(aliases)))
            self.assertEqual(set(aliases), {id for id, q in source.items() if q['subject'] == subject})
            self.assertFalse(seen.intersection(aliases))
            self.assertTrue(all(q['subject'] == subject for q in rows.values()))
            self.assertTrue(all(not q.get('isSupplemental') and q.get('examYear') and q.get('questionNo') for q in rows.values()))
            self.assertTrue(all(q.get('questionText') for q in rows.values()))
            self.assertTrue(all(set(q['textOptions']) == set('ABCD') for q in rows.values() if q['questionType'] == 'single'))
            seen.update(aliases)
        self.assertEqual(seen, set(source))
        self.assertEqual(len(seen), 1224)

    def test_calculus_preserves_content_and_answers(self):
        source = read(ROOT / 'sources/math-bank/data/questions.jsonl')
        rows = read(ROOT / 'apps/calculus/data/questions.jsonl')
        for q in rows.values():
            self.assertEqual(q['image'], source[q['id']]['image'])
            self.assertEqual({s['id'] for s in q['sources']}, set(q['aliases']))
            for ref in q['sources']:
                self.assertEqual(ref['answer'], source[ref['id']]['answer'])
        self.assertEqual({q['chapter'] for q in rows.values()}, set(calculus.CHAPTERS))


if __name__ == '__main__':
    unittest.main()
