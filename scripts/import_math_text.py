#!/usr/bin/env python3
"""Download pinned public math transcripts and index their original exam references."""
import base64
import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'sources/math-bank/text'
REPO = 'lx-ruc/kaoyanshuxue'


def main():
    DEST.mkdir(exist_ok=True)
    commit = subprocess.check_output(['gh', 'api', f'repos/{REPO}/commits/main', '--jq', '.sha'], text=True).strip()
    def fetch(exam):
        name = f'feishu_part_{exam}.md'
        path = DEST / name
        if not path.exists():
            data = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPO}/contents/{name}?ref={commit}'], text=True))
            path.write_bytes(base64.b64decode(data['content']))
        text = path.read_text()
        headers = list(re.finditer(r'\*\*(20\d{2})年第(\d+)题\s*\|([^\n]*?)\*\*', text))
        records = {}
        for index, m in enumerate(headers):
            body = text[m.end():headers[index+1].start() if index+1 < len(headers) else len(text)]
            # Section headings between questions belong to the next question.
            body = re.split(r'\n#{1,6} ', body)[0].strip().strip('-').strip()
            key = f"{exam}/{m[1]}/{int(m[2])}"
            prompt = re.split(r'\*\*\s*(?:答案|解析)\s*[:：]|(?:^|\n)答案\s*[:：]', body)[0].strip()
            prompt = re.sub(r'^\d+[.．、]\s*', '', prompt)
            prompt = re.sub(r'^[（(]本题满分\s*\d+\s*分[）)]\s*', '', prompt)
            # Preserve the source as inert text; the app renders equations itself.
            answer = re.search(r'\*\*\s*答案\s*[:：]\s*\*\*(.*?)(?=\*\*\s*解析|$)', body, re.S)
            analysis = re.search(r'\*\*\s*解析\s*[:：]\s*\*\*(.*)', body, re.S)
            value = {'exam': exam, 'year': int(m[1]), 'no': int(m[2]), 'prompt': prompt, 'answer': answer[1].strip() if answer else '', 'analysis': analysis[1].strip() if analysis else '', 'source': f'https://github.com/{REPO}/blob/{commit}/{name}'}
            if key not in records or len(prompt) > len(records[key]['prompt']):
                records[key] = value
        print(exam, len(records), 'indexed', flush=True)
        return records, {'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, ['数学一', '数学二', '数学三']))
    records = {k: v for result, _ in results for k, v in result.items()}
    (DEST / 'index.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    (DEST / 'manifest.json').write_text(json.dumps({'repository': REPO, 'commit': commit, 'files': [v for _, v in results]}, ensure_ascii=False, indent=2) + '\n')
    source = [json.loads(s) for s in (ROOT / 'sources/math-bank/data/questions.jsonl').read_text().splitlines()]
    missing = [q['id'] for q in source if f"{q['exam']}/{q['examYear']}/{q['questionNo']}" not in records]
    print('Missing:', len(missing), missing)


if __name__ == '__main__':
    main()
