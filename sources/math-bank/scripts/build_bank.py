#!/usr/bin/env python3
"""Build a compact offline image-based bank for the 2009–2026 math exams.

The exam images preserve mathematical notation. Metadata and question images are
attributed in data/source_manifest.json; source answer images are included where
available. DeepSeek Vision can generate a worked explanation on demand with the
user's own API key.
"""
from __future__ import annotations

import concurrent.futures
import io
import json
import math
import os
import pathlib
import re
import sys
import time
import urllib.request
import urllib.parse

import requests
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "generated" / "web"
ASSETS = WEB / "images"
DATA = ROOT / "data"
RAW = "https://raw.githubusercontent.com/lx-ruc/kaoyanshuxue/main/"
API = "https://zhentiqiang.com"
GROUPS = {"数学一": 8, "数学二": 9, "数学三": 10}
YEARS = range(2009, 2027)
USER_AGENT = "YanxiMathOfflineStudy/1.0 (personal study app)"

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json, image/*, */*"})


def get_bytes(url: str, *, timeout: tuple[int, int] = (7, 25), retries: int = 4) -> bytes:
    error: Exception | None = None
    for attempt in range(retries):
        try:
            if "zhentiqiang.com/static/photos/" in url or "zhentiqiang.com/api/papers/" in url:
                candidates = [url]
                if "zhentiqiang.com/api/papers/" in url and url.startswith("https://"):
                    candidates.append(url.replace("https://", "http://", 1))
                for candidate in candidates:
                    try:
                        request = urllib.request.Request(candidate, headers={"User-Agent": USER_AGENT})
                        with urllib.request.urlopen(request, timeout=timeout[1]) as response:
                            return response.read()
                    except Exception as source_error:
                        if getattr(source_error, "code", None) == 404:
                            raise
                        error = source_error
                raise error or RuntimeError("source request failed")
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except Exception as exc:  # intermittent source CDN/TLS errors are retried
            if isinstance(exc, requests.HTTPError) and exc.response is not None and exc.response.status_code == 404:
                raise
            if getattr(exc, "code", None) == 404:
                raise
            error = exc
            time.sleep(min(0.5 * (attempt + 1), 2))
    raise RuntimeError(f"download failed: {url}: {error}")


def get_json(url: str, *, timeout: tuple[int, int] = (7, 25), retries: int = 4):
    return json.loads(get_bytes(url, timeout=timeout, retries=retries).decode("utf-8"))


def raw_path(path: str) -> str:
    return RAW + urllib.parse.quote(path, safe="/")


def raw_image(path: str) -> str:
    return raw_path(path)


def to_webp(data: bytes, target: pathlib.Path) -> bool:
    try:
        with Image.open(io.BytesIO(data)) as source:
            image = source.convert("RGB") if source.mode not in ("RGB", "RGBA") else source
            # Keep small formula crops lossless; use high quality for page snippets.
            if image.width <= 600 and image.height <= 360:
                image.save(target, "WEBP", lossless=True, method=6)
            else:
                image.save(target, "WEBP", quality=94, method=6)
        return True
    except Exception as exc:
        print(f"[image-convert] {target.name}: {exc}", file=sys.stderr, flush=True)
        return False


def fetch_2026_info(question_id: int) -> dict:
    # This endpoint is currently served over both schemes; HTTP is a fallback
    # because the source's HTTPS API edge occasionally drops TLS handshakes.
    errors = []
    for scheme, attempts in (("http", 2), ("https", 1)):
        for _ in range(attempts):
            try:
                url = f"{scheme}://zhentiqiang.com/api/question_info/{question_id}"
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://zhentiqiang.com/kaoyan/math"}, timeout=(3, 8))
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    return data
            except Exception as exc:
                errors.append(str(exc)[:100])
                time.sleep(0.4)
    return {"success": False, "_error": "; ".join(errors[-2:])}


def difficulty(q: dict) -> int:
    happy = max(0, int(q.get("happy_count") or 0))
    maybe = max(0, int(q.get("maybe_count") or 0))
    sad = max(0, int(q.get("sad_count") or 0))
    total = happy + maybe + sad
    if total < 8:
        qtype = int(q.get("question_type") or 1)
        no = int(q.get("index") or 0)
        score = int(q.get("score") or 0)
        if qtype == 1:
            return 2 if no <= 3 else 3 if no <= 7 else 4
        if qtype == 2:
            return 3 if score <= 5 else 4
        return 2 if score <= 10 else 3 if score <= 12 else 4
    hard_share = (sad + maybe * 0.45) / total
    return max(1, min(5, int(math.floor(1 + 4 * hard_share + 0.5))))


def classify(group: str, topic: str) -> tuple[str, str]:
    if any(word in topic for word in ("随机", "概率", "分布", "期望", "方差", "协方差", "统计", "估计", "假设检验", "大数定律", "中心极限定理")):
        subject = "概率论与数理统计"
        if any(word in topic for word in ("二维", "多维", "边缘", "条件分布")):
            chapter = "多维随机变量"
        elif any(word in topic for word in ("期望", "方差", "协方差", "相关系数", "数字特征")):
            chapter = "数字特征"
        elif any(word in topic for word in ("统计", "估计", "假设检验", "样本", "抽样")):
            chapter = "数理统计"
        elif any(word in topic for word in ("大数定律", "中心极限定理")):
            chapter = "大数定律与中心极限定理"
        else:
            chapter = "随机事件与概率" if "事件" in topic else "随机变量及其分布"
        return subject, chapter
    if any(word in topic for word in ("行列式", "矩阵", "向量", "线性方程", "特征值", "特征向量", "二次型", "相似对角化", "线性相关")):
        subject = "线性代数"
        if "行列式" in topic:
            chapter = "行列式"
        elif "矩阵" in topic or "相似对角化" in topic:
            chapter = "矩阵"
        elif "向量" in topic or "线性相关" in topic:
            chapter = "向量"
        elif "方程" in topic:
            chapter = "线性方程组"
        elif any(word in topic for word in ("特征值", "特征向量")):
            chapter = "矩阵的特征值与特征向量"
        else:
            chapter = "二次型"
        return subject, chapter
    subject = "高等数学"
    if any(word in topic for word in ("极限", "连续", "无穷小", "函数极限")):
        chapter = "函数、极限与连续"
    elif any(word in topic for word in ("偏导", "多元函数", "全微分", "方向导数", "梯度", "多元函数极值")):
        chapter = "多元函数微分学"
    elif any(word in topic for word in ("积分", "积分学", "曲线积分", "曲面积分", "重积分")):
        chapter = "多元函数积分学" if any(word in topic for word in ("重积分", "曲线积分", "曲面积分")) else "一元函数积分学"
    elif "级数" in topic or "幂级数" in topic or "傅里叶" in topic:
        chapter = "无穷级数"
    elif "微分方程" in topic or "常微分" in topic:
        chapter = "常微分方程"
    elif any(word in topic for word in ("空间", "平面", "直线", "曲面", "向量积")):
        chapter = "空间解析几何与向量代数"
    else:
        chapter = "一元函数微分学"
    return subject, chapter


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    # The public index contains normalized answers and a topic-to-question map
    # for 2009–2025; the exam source adds its current 2026 paper metadata.
    old_answers: dict[str, dict] = {}
    old_topics: dict[str, dict] = {}
    for group in GROUPS:
        old_answers[group] = get_json(raw_path(f"kaoyan_math_images/{group}/answers.json"))
        old_topics[group] = get_json(raw_path(f"kaoyan_math_by_topic/{group}/topic_index.json"))

    topic_by_ref: dict[tuple[str, int, int], str] = {}
    for group, index in old_topics.items():
        for topic_path, rows in index.items():
            for row in rows:
                topic_by_ref[(group, int(row["year"]), int(row["index"]))] = topic_path

    answer_by_ref: dict[tuple[str, int, int], dict] = {}
    for group, records in old_answers.items():
        for record in records.values():
            answer_by_ref[(group, int(record["paper"]), int(record["index"]))] = record

    # The source API is the only currently indexed source for 2026, and includes
    # all paper groups plus community response counts used for the difficulty estimate.
    api_records: dict[tuple[str, int, int], dict] = {}
    paper_ids: dict[tuple[str, int], int] = {}
    # Seed the older papers from the repository's complete normalized index,
    # so the build remains reproducible when the live source API is unavailable.
    for (group, year, no), legacy in answer_by_ref.items():
        if year < 2021:
            qtype = 1 if int(legacy.get("type") or 0) == 1 else (2 if no <= 10 else 3)
        else:
            qtype = 1 if int(legacy.get("type") or 0) == 1 else (2 if no <= 16 else 3)
        api_records[(group, year, no)] = {
            "id": int(legacy["question_id"]), "index": no, "question_type": qtype,
            "score": legacy.get("score", 0), "happy_count": 0, "maybe_count": 0, "sad_count": 0,
        }
    for group, group_id in GROUPS.items():
        try:
            papers_data = get_json(f"{API}/api/papers/{group_id}", timeout=(3, 8), retries=1)
            papers = papers_data.get("papers", papers_data) if isinstance(papers_data, dict) else papers_data
            for paper in papers:
                year_match = re.search(r"20\d{2}", str(paper.get("name", paper.get("year", ""))))
                if not year_match:
                    continue
                year = int(year_match.group())
                paper_ids[(group, year)] = int(paper["id"])
                for q in paper.get("questions", []):
                    api_records[(group, year, int(q["index"]))] = q
        except Exception as exc:
            print(f"Live metadata unavailable for {group}; using indexed years and fallback 2026 ids ({str(exc)[:120]})", flush=True)

    # The 2026 source's paper IDs and question ID ranges were published in its
    # paper index; synthesize the conventional 10/6/6 question-type split if
    # the live papers endpoint is temporarily unavailable.
    for group, group_id in GROUPS.items():
        paper_ids.setdefault((group, 2026), {8: 99, 9: 100, 10: 101}[group_id])
        start_id = {8: 1942, 9: 1964, 10: 1986}[group_id]
        for no in range(1, 23):
            qtype = 1 if no <= 10 else 2 if no <= 16 else 3
            api_records.setdefault((group, 2026, no), {
                "id": start_id + no - 1, "index": no, "question_type": qtype,
                "score": 5 if qtype in (1, 2) else 12,
                "happy_count": 0, "maybe_count": 0, "sad_count": 0,
            })

    current_refs = [(group, year, no, q) for (group, year, no), q in api_records.items() if year == 2026]
    print(f"Metadata loaded: {len(api_records)} questions across {len(paper_ids)} papers; fetching 2026 answer/topic details…", flush=True)
    current_info: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_2026_info, int(q["id"])): int(q["id"]) for _, _, _, q in current_refs}
        for future in concurrent.futures.as_completed(futures):
            qid = futures[future]
            try:
                current_info[qid] = future.result()
            except Exception:
                current_info[qid] = {"success": False}

    rows: list[dict] = []
    downloads: dict[str, tuple[str, pathlib.Path]] = {}
    for (group, year, no), api_q in sorted(api_records.items(), key=lambda item: item[0]):
        if year not in YEARS:
            continue
        qid = int(api_q["id"])
        qtype = int(api_q.get("question_type", 1))
        legacy = answer_by_ref.get((group, year, no), {})
        info = current_info.get(qid, {}) if year == 2026 else {}
        image_name = f"q-{qid}.webp"
        image_path = ASSETS / image_name

        if year <= 2025:
            exam_image = raw_image(f"kaoyan_math_images/{group}/{year}/Q{no:02d}_id{qid}.png")
        else:
            group_id = GROUPS[group]
            paper_id = paper_ids[(group, year)]
            exam_image = f"https://zhentiqiang.com/static/photos/group_{group_id}/paper_{paper_id}/{no}.png"
        if not image_path.exists():
            downloads[image_name] = (exam_image, image_path)

        answer_name = f"a-{qid}.webp"
        answer_path = ASSETS / answer_name
        if qtype in (2, 3) and year <= 2025 and not answer_path.exists():
            answer_url = raw_image(f"kaoyan_math_images/{group}/{year}/answers/Q{no:02d}_id{qid}_answer.png")
            downloads[answer_name] = (answer_url, answer_path)

        topic_path = topic_by_ref.get((group, year, no), "")
        if topic_path:
            parts = topic_path.split("/")
            subject = parts[0]
            chapter = parts[1] if len(parts) > 1 else "其他"
            topic = parts[-1]
        else:
            topic = str(info.get("knowledge_point_name") or legacy.get("knowledge_point") or "待归类考点")
            subject, chapter = classify(group, topic)
        answer = str(info.get("answer") or legacy.get("answer") or "").strip().upper()
        answer = "".join(ch for ch in answer if ch in "ABCD") if qtype == 1 else answer
        image_answer = f"images/{answer_name}" if qtype in (2, 3) else ""
        row = {
            "id": f"M-{GROUPS[group]}-{year}-{no:02d}",
            "exam": group,
            "examYear": year,
            "questionNo": no,
            "subject": subject or ("高等数学" if group == "数学二" else topic_path.split("/")[0] if topic_path else "待归类"),
            "chapter": chapter or ("待归类" if year == 2026 else "其他"),
            "topic": topic,
            "topicPath": topic_path,
            "questionType": {1: "single", 2: "fill", 3: "solve"}.get(qtype, "solve"),
            "score": int(api_q.get("score") or legacy.get("score") or 0),
            "difficulty": difficulty(api_q),
            "answer": answer,
            "image": f"images/{image_name}",
            "answerImage": image_answer,
            "sourceImageUrl": exam_image,
            "sourceName": "考研数学历年真题图片库（2009–2025）" if year <= 2025 else "真题墙考研数学题库（2026）",
            "sourceUrl": "https://github.com/lx-ruc/kaoyanshuxue" if year <= 2025 else "https://zhentiqiang.com/kaoyan/math",
            "sourceLicense": "题目与参考答案图片来自公开整理资料；授权状态未核实，当前仅用于个人本地备考。",
            "knowledgeTagId": api_q.get("knowledge_tags_id"),
            "answerSource": "题库答案索引" if answer else ("原题附图/AI 解析" if qtype != 1 else "待核对"),
        }
        rows.append(row)

    # Keep downloads bounded and resumable. Each response is transcoded to WebP.
    print(f"Downloading {len(downloads)} image assets…", flush=True)
    failures: list[tuple[str, str]] = []
    done = 0

    def fetch_one(item: tuple[str, tuple[str, pathlib.Path]]) -> tuple[str, bool, str]:
        name, (url, target) = item
        try:
            data = get_bytes(url, timeout=(8, 35), retries=4)
            if not to_webp(data, target):
                return name, False, "image decode failed"
            return name, True, ""
        except Exception as exc:
            return name, False, str(exc)[:240]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_one, item) for item in downloads.items()]
        for future in concurrent.futures.as_completed(futures):
            name, ok, error = future.result()
            done += 1
            if not ok:
                failures.append((name, error))
            if done % 40 == 0 or done == len(futures):
                print(f"  {done}/{len(futures)} assets ({len(failures)} missing)", flush=True)

    # Do not leave broken local image paths: the UI can still show source link.
    for row in rows:
        if not (WEB / row["image"]).exists():
            row["image"] = ""
        if row["answerImage"] and not (WEB / row["answerImage"]).exists():
            row["answerImage"] = ""

    rows.sort(key=lambda q: (q["exam"], q["subject"], q["chapter"], q["topic"], q["examYear"], q["questionNo"]))
    with (DATA / "questions.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    (WEB / "questions.js").write_text("window.QUESTIONS=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

    type_counts = {"single": 0, "fill": 0, "solve": 0}
    exam_counts = {}
    subject_counts = {}
    for row in rows:
        type_counts[row["questionType"]] += 1
        exam_counts[row["exam"]] = exam_counts.get(row["exam"], 0) + 1
        subject_counts[row["subject"]] = subject_counts.get(row["subject"], 0) + 1
    summary = {
        "total": len(rows), "years": [2009, 2026], "exams": exam_counts,
        "subjects": subject_counts, "types": type_counts,
        "assets": len(list(ASSETS.glob("*.webp"))),
        "missingImages": sum(not bool(q["image"]) for q in rows),
        "missingAnswers": sum(q["questionType"] != "single" and not q["answerImage"] and not q["answer"] for q in rows),
        "missingChoiceKeys": sum(q["questionType"] == "single" and not q["answer"] for q in rows),
        "missingTopics": sum(q["topic"] == "待归类考点" for q in rows),
        "difficultyMethod": "根据公开题库用户反馈（容易/一般/困难）比例估算；样本不足时记为3/5",
        "sources": ["https://github.com/lx-ruc/kaoyanshuxue", "https://zhentiqiang.com/kaoyan/math"],
    }
    (DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "download_issues.json").write_text(json.dumps([{"file": n, "error": e} for n, e in failures], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "questionCount": len(rows), "source": "考研数学历年真题图片库；真题墙补充2026元数据与原题图",
        "questionBankRepo": "https://github.com/lx-ruc/kaoyanshuxue",
        "sourceSite": "https://zhentiqiang.com/kaoyan/math",
        "attribution": "2009–2025 metadata and images: lx-ruc/kaoyanshuxue, sourced by its README from 真题墙; 2026 metadata/images: 真题墙.",
        "note": "No source authorization was found. Current APK is for the user's local personal study only; do not redistribute or sell this question image bundle without confirming rights.",
    }
    (DATA / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if failures:
        print(f"Image failures: {len(failures)} (see data/download_issues.json)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
