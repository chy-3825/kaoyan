#!/usr/bin/env python3
"""Extract reviewed embedded exam figures, keeping the source pixels unchanged.

Requires PyMuPDF and Pillow. No network access and no AI-generated exam pictures.
"""
import io
import json
from pathlib import Path

import pymupdf
from PIL import Image

from question_images import attach_images

ROOT = Path(__file__).resolve().parents[1]


def main():
    specs = json.loads((ROOT / 'sources/question_images.json').read_text())['images']
    for spec in specs:
        with pymupdf.open(ROOT / spec['pdf']) as doc:
            page = doc[spec['page'] - 1]
            matches = [im for im in page.get_images() if list(im[2:4]) == spec['size']]
            if len(matches) != 1:
                raise ValueError(f"Ambiguous source figure for {spec['id']}")
            source = doc.extract_image(matches[0][0])
            image = Image.open(io.BytesIO(source['image'])).convert('RGB')
            for layout in ('android/web', 'app/dist'):
                out = ROOT / layout / spec['image']
                out.parent.mkdir(parents=True, exist_ok=True)
                image.save(out, 'WEBP', lossless=True)
        print(f"{spec['id']}: {spec['image']} {spec['size']}")
    bank = ROOT / 'data/questions.jsonl'
    rows = [json.loads(line) for line in bank.read_text().splitlines() if line.strip()]
    attach_images(rows)
    bank.write_text(''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in rows))
    for layout in ('android/web', 'app/dist'):
        (ROOT / layout / 'questions.js').write_text('window.QUESTIONS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';')


if __name__ == '__main__':
    main()
