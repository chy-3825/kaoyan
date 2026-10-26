"""Attach reviewed original-paper figure references on every bank rebuild."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def attach_images(rows):
    specs = json.loads((ROOT / 'sources/question_images.json').read_text())['images']
    by_id = {q['id']: q for q in rows}
    for spec in specs:
        if spec['id'] not in by_id:
            raise ValueError(f"Missing figure question: {spec['id']}")
        for layout in ('android/web', 'app/dist'):
            if not (ROOT / layout / spec['image']).is_file():
                raise ValueError(f"Run scripts/build_question_images.py first: {spec['image']}")
        by_id[spec['id']].update(image=spec['image'], imageAlt=spec['imageAlt'])
