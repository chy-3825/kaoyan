#!/usr/bin/env python3
"""Assemble and validate the complete linear algebra question bank."""
import json
from collections import Counter
from pathlib import Path

if __name__ == '__main__':
    import runpy
    runpy.run_path(str(Path(__file__).resolve().parents[3] / 'scripts/build_math_study.py'))['build']('linear-algebra')
    raise SystemExit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB = ROOT / "android" / "web"
OUTPUT = WEB / "questions.js"
COMBINED = DATA / "questions.jsonl"
EXAMS = ("数学一", "数学二", "数学三")
EXPECTED = {"past": 270, "supplemental": 0, "total": 270}
TOPIC_ALIASES = {
    "二次型的规范形与秩": "二次型的秩与规范形",
}
def read_rows(name):
    path = DATA / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize(row):
    if row.get("chapter") == "矩阵的特征值和特征向量":
        row["chapter"] = "矩阵的特征值与特征向量"

    row["topic"] = TOPIC_ALIASES.get(row.get("topic"), row.get("topic"))

    row["topicPath"] = f"{row['subject']}/{row['chapter']}/{row['topic']}"
    return row


def write_rows(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main():
    past = [normalize(row) for row in read_rows("past_questions.jsonl")]
    supplemental = []
    if (len(past), len(supplemental), len(past) + len(supplemental)) != (
        EXPECTED["past"], EXPECTED["supplemental"], EXPECTED["total"]
    ):
        raise SystemExit(f"Unexpected bank size: {len(past)} past + {len(supplemental)} supplemental")
    if any(q.get("subject") != "线性代数" or q.get("isSupplemental") for q in past):
        raise SystemExit("past_questions.jsonl must contain only past exam linear algebra questions")
    if Counter(q["exam"] for q in past) != Counter({exam: 90 for exam in EXAMS}):
        raise SystemExit("Expected all 90 past questions per exam type")
    expected_years = set(range(2009, 2027))
    for exam in EXAMS:
        exam_rows = [q for q in past if q["exam"] == exam]
        if {q.get("examYear") for q in exam_rows} != expected_years or any(not q.get("questionNo") for q in exam_rows):
            raise SystemExit(f"Past questions for {exam} must cover 2009–2026 and include question numbers")

    rows = past + supplemental
    if len({q["id"] for q in rows}) != len(rows):
        raise SystemExit("Question IDs must be unique")
    for q in rows:
        if q.get("exam") not in EXAMS:
            raise SystemExit(f"Unexpected exam for {q['id']}: {q.get('exam')}")
        if not q.get("image") and not q.get("questionText"):
            raise SystemExit(f"Question has no prompt: {q['id']}")
        if not (q.get("answer") or q.get("answerText") or q.get("answerImage")):
            raise SystemExit(f"Question has no answer reference: {q['id']}")
        for field in ("image", "answerImage"):
            asset = q.get(field)
            if asset and not (WEB / asset).is_file():
                raise SystemExit(f"Missing {field} for {q['id']}: {asset}")
        if q["questionType"] == "single":
            options = q.get("options") or {}
            if q.get("answer") not in "ABCD" or (options and (q["answer"] not in options or len(options) != 4)):
                raise SystemExit(f"Malformed single-choice answer for {q['id']}")
    rows.sort(key=lambda q: (EXAMS.index(q["exam"]), bool(q.get("isSupplemental")),
                             q.get("examYear") or 9999, q.get("questionNo") or 9999, q["id"]))
    write_rows(DATA / "past_questions.jsonl", past)
    write_rows(COMBINED, rows)
    OUTPUT.write_text("window.QUESTIONS=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

    summary = {
        "total": len(rows),
        "pastExam": len(past),
        "supplemental": len(supplemental),
        "byExam": dict(Counter(q["exam"] for q in rows)),
        "pastByExam": dict(Counter(q["exam"] for q in past)),
        "supplementalByExam": dict(Counter(q["exam"] for q in supplemental)),
        "byChapter": dict(Counter(q["chapter"] for q in rows)),
        "types": dict(Counter(q["questionType"] for q in rows)),
        "note": "仅包含数学一、数学二、数学三线性代数历年真题，按教材章节整理。",
    }
    (DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote all {len(rows)} questions: {len(past)} past questions and {len(supplemental)} supplemental questions.")


if __name__ == "__main__":
    main()
