#!/usr/bin/env python3
"""Regression checks against the bundled PDFs and installed offline image banks."""
import importlib.util
import json
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('math_crops', ROOT / 'sources/math-bank/scripts/build_2026_pdfs.py')
crops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crops)


class CropRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {exam: crops.get_lines(crops.ROOT / 'sources/2026' / filename)
                     for exam, filename in crops.PDFS.items()}
        cls.segments = {exam: crops.segments_for(pages) for exam, pages in cls.pages.items()}

    def test_all_2026_questions_and_solutions_have_segments(self):
        for exam, segments in self.segments.items():
            with self.subTest(exam=exam):
                self.assertEqual(sorted(segments['question']), list(range(1, 23)))
                self.assertEqual(sorted(segments['answer']), list(range(1, 23)))

    def test_short_divergence_question_keeps_whole_line(self):
        # The previous crop ended at y=569.3, before the equation's bottom.
        page, _, _, top, bottom = self.segments['数学一']['question'][11][0]
        self.assertEqual(page, 3)
        self.assertLess(top, 562.84)
        self.assertGreater(bottom, 582.85)

    def test_matrix_tops_and_vector_tops_are_not_cut(self):
        for exam, no, max_top in [('数学一', 15, 279), ('数学一', 21, 75),
                                 ('数学二', 9, 75), ('数学二', 22, 341),
                                 ('数学三', 5, 75), ('数学三', 21, 231)]:
            with self.subTest(exam=exam, question=no):
                self.assertLess(self.segments[exam]['question'][no][0][3], max_top)

    def test_bitmap_formula_in_math_three_is_not_cut(self):
        # Q12 contains an embedded image whose radical starts above the number.
        page, _, _, top, bottom = self.segments['数学三']['question'][12][0]
        self.assertEqual(page, 3)
        self.assertLess(top, 568.16)
        self.assertGreater(bottom, 598.91)

    def test_answer_fraction_does_not_leak_into_question(self):
        # Math I Q12's answer numerator starts above the answer label.
        question = self.segments['数学一']['question'][12][-1]
        answer = self.segments['数学一']['answer'][12][0]
        self.assertEqual(question[0], answer[0])
        self.assertAlmostEqual(question[4], answer[3])
        self.assertLess(question[4], 693.91)


class OfflineImageTests(unittest.TestCase):
    def test_every_referenced_image_decodes_and_subject_copies_match(self):
        for name in ('calculus', 'probability', 'linear-algebra', 'politics'):
            app = ROOT / 'apps' / name
            rows = [json.loads(line) for line in (app / 'data/questions.jsonl').read_text().splitlines()]
            for q in rows:
                for key in ('image', 'answerImage'):
                    path = q.get(key)
                    if not path:
                        continue
                    with self.subTest(app=name, question=q['id'], field=key):
                        target = app / 'android/web' / path
                        with Image.open(target) as image:
                            image.load()
                            self.assertGreater(image.width, 0)
                            self.assertGreater(image.height, 0)
                        if name in ('calculus', 'probability', 'linear-algebra'):
                            self.assertEqual(target.read_bytes(), (ROOT / 'sources/math-bank/generated/web' / path).read_bytes())

    def test_politics_figures_exist_in_both_runtime_banks(self):
        app = ROOT / 'apps/politics'
        specs = json.loads((app / 'sources/question_images.json').read_text())['images']
        self.assertEqual({s['id'] for s in specs}, {'K政治-2010-03', 'K政治-2012-04'})
        for layout in ('android/web', 'app/dist'):
            text = (app / layout / 'questions.js').read_text().strip()
            rows = {q['id']: q for q in json.loads(text.removeprefix('window.QUESTIONS=').removesuffix(';'))}
            for item in specs:
                self.assertEqual(rows[item['id']]['image'], item['image'])
                with Image.open(app / layout / item['image']) as image:
                    self.assertEqual(list(image.size), item['size'])


if __name__ == '__main__':
    unittest.main()
