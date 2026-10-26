#!/usr/bin/env python3
"""Check the repository snapshot without downloading or rewriting question data."""
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
EXPECTED = {'math': 1464, 'probability': 221, 'linear-algebra': 318, 'politics': 1500}


def error(message):
    ERRORS.append(message)


for name, expected in EXPECTED.items():
    app = ROOT / 'apps' / name
    rows = [json.loads(line) for line in (app / 'data/questions.jsonl').read_text().splitlines() if line.strip()]
    text = (app / 'android/web/questions.js').read_text().strip()
    prefix = 'window.QUESTIONS='
    if not text.startswith(prefix):
        error(f'{name}: unexpected runtime bank format')
        continue
    runtime = json.loads(text[len(prefix):].removesuffix(';'))
    if len(rows) != expected:
        error(f'{name}: expected {expected} rows, got {len(rows)}')
    if len({q['id'] for q in rows}) != len(rows):
        error(f'{name}: duplicate question IDs')
    if {q['id']: q for q in rows} != {q['id']: q for q in runtime} or len(rows) != len(runtime):
        error(f'{name}: source and runtime banks differ')
    refs = 0
    for q in rows:
        if not (q.get('image') or q.get('questionText') or q.get('question') or q.get('stem')):
            error(f"{name}/{q['id']}: missing prompt")
        for key in ('image', 'answerImage'):
            value = q.get(key)
            if not value:
                continue
            path = (app / 'android/web' / value).resolve()
            if not path.is_relative_to(app.resolve()):
                error(f"{name}/{q['id']}: image path escapes app")
            elif not path.is_file():
                error(f"{name}/{q['id']}: missing {key}")
            refs += 1
    print(f'{name}: {len(rows)} questions, {refs} local image references checked')

for path in ROOT.rglob('*.py'):
    if '.git' not in path.parts:
        ast.parse(path.read_text(), filename=str(path))

tracked = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
forbidden_suffixes = {'.jks', '.keystore', '.p12', '.pfx', '.pem', '.key', '.apk', '.aab', '.idsig'}
secret_patterns = [r'\bsk-[A-Za-z0-9_-]{20,}', r'\bgh[pousr]_[A-Za-z0-9]{30,}', r'\bgithub_pat_[A-Za-z0-9_]{30,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
for relative in filter(None, tracked):
    path = ROOT / relative
    if path.suffix.lower() in forbidden_suffixes or 'signing' in path.parts or 'build' in path.parts or path.name in {'password', '.env', 'credentials.json', 'secrets.json'}:
        error(f'forbidden upload: {relative}')
    if path.suffix.lower() in {'.py', '.js', '.json', '.jsonl', '.md', '.txt', '.xml', '.html', '.css', '.properties', '.env'}:
        text = path.read_text(errors='replace')
        if any(re.search(pattern, text) for pattern in secret_patterns):
            error(f'potential embedded secret: {relative}')

if ERRORS:
    raise SystemExit('\n'.join(ERRORS))
print('PASS: data, image references, Python syntax and upload exclusions')
