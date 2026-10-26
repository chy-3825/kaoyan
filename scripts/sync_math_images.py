#!/usr/bin/env python3
"""Copy reviewed math question/answer images into the two subject apps."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    math = ROOT / 'apps/math'
    source = {q['id']: q for q in map(json.loads, (math / 'data/questions.jsonl').read_text().splitlines())}
    for name in ('probability', 'linear-algebra'):
        app = ROOT / 'apps' / name
        copied = 0
        for q in map(json.loads, (app / 'data/questions.jsonl').read_text().splitlines()):
            for key in ('image', 'answerImage'):
                path = q.get(key)
                if not path:
                    continue
                if source[q['id']].get(key) != path:
                    raise ValueError(f"{name}/{q['id']}: {key} differs from math bank")
                src, dest = math / 'android/web' / path, app / 'android/web' / path
                if not dest.is_file() or src.read_bytes() != dest.read_bytes():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dest)
                    copied += 1
        print(f'{name}: synchronized {copied} changed images')


if __name__ == '__main__':
    main()
