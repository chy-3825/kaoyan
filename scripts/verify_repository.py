#!/usr/bin/env python3
"""Check the repository snapshot without downloading or rewriting question data."""
import ast
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
EXPECTED = {'math': 1464, 'probability': 221, 'linear-algebra': 318, 'politics': 1500}
PUBLIC_APKS = {}
for name in EXPECTED:
    manifest = ET.parse(ROOT / 'apps' / name / 'android/AndroidManifest.xml').getroot()
    version = manifest.get('{http://schemas.android.com/apk/res/android}versionName')
    PUBLIC_APKS[f'apk/yanxi-{name}-{version}.apk'] = name


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
    if (path.suffix.lower() in forbidden_suffixes and relative not in PUBLIC_APKS) or 'signing' in path.parts or 'build' in path.parts or path.name in {'password', '.env', 'credentials.json', 'secrets.json'}:
        error(f'forbidden upload: {relative}')
    if path.suffix.lower() in {'.py', '.js', '.json', '.jsonl', '.md', '.txt', '.xml', '.html', '.css', '.properties', '.env'}:
        text = path.read_text(errors='replace')
        if any(re.search(pattern, text) for pattern in secret_patterns):
            error(f'potential embedded secret: {relative}')

# Public APK exceptions are exact versioned paths. Verify their embedded assets
# against source so a published binary cannot silently retain older question art.
if (ROOT / 'apk').is_dir():
    sums = ROOT / 'apk/SHA256SUMS'
    expected_sums = {}
    if sums.is_file():
        for line in sums.read_text().splitlines():
            digest, filename = line.split(maxsplit=1)
            expected_sums[filename] = digest
    else:
        error('apk/SHA256SUMS: missing checksums')
    if set(expected_sums) != {Path(p).name for p in PUBLIC_APKS}:
        error('apk/SHA256SUMS: expected exactly the current four APKs')
    for relative, name in PUBLIC_APKS.items():
        path = ROOT / relative
        if not path.is_file():
            error(f'missing public APK: {relative}')
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sums.get(path.name):
            error(f'APK checksum mismatch: {relative}')
        with zipfile.ZipFile(path) as package:
            if 'classes.dex' not in package.namelist() or 'AndroidManifest.xml' not in package.namelist():
                error(f'incomplete APK: {relative}')
            web = ROOT / 'apps' / name / 'android/web'
            for asset in web.rglob('*'):
                if asset.is_file():
                    key = 'assets/' + asset.relative_to(web).as_posix()
                    if key not in package.namelist() or package.read(key) != asset.read_bytes():
                        error(f'{relative}: stale or missing {key}')
        print(f'{relative}: checksum and all embedded Web assets checked')

if ERRORS:
    raise SystemExit('\n'.join(ERRORS))
print('PASS: data, image references, Python syntax and upload exclusions')
