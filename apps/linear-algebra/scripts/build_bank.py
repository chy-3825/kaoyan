#!/usr/bin/env python3
"""Assemble and validate the complete linear algebra question bank."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB = ROOT / "android" / "web"
OUTPUT = WEB / "questions.js"
COMBINED = DATA / "questions.jsonl"
EXAMS = ("数学一", "数学二", "数学三")
EXPECTED = {"past": 270, "supplemental": 48, "total": 318}
TOPIC_ALIASES = {
    "二次型的规范形与秩": "二次型的秩与规范形",
}
SUPPLEMENT_COUNTS = {
    "17": (4, 4, 4),
    "18": (4, 4, 4),
    "19": (3, 4, 3),
    "20": (3, 4, 3),
    "21": (2, 0, 2),
}


def read_rows(name):
    path = DATA / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def set_choices(row, correct, distractors):
    correct = str(correct)
    values = []
    for value in [correct, *distractors]:
        value = str(value)
        if value not in values:
            values.append(value)
    for value in ("0", "1", "2", "3", "4", "5"):
        if value not in values:
            values.append(value)
        if len(values) >= 4:
            break
    answer_letter = row.get("answer") if row.get("answer") in "ABCD" else "A"
    other_values = iter([value for value in values if value != correct])
    row["options"] = {letter: (correct if letter == answer_letter else next(other_values)) for letter in "ABCD"}
    row["answer"] = answer_letter


def normalize_supplemental(row):
    match = re.fullmatch(r"SUP-[^-]+-L-(\d+)-(\d+)", row.get("id", ""))
    if not match or match.group(1) not in SUPPLEMENT_COUNTS:
        return row
    group, ordinal = match.group(1), int(match.group(2))
    exam_index = EXAMS.index(row["exam"])
    offset = sum(SUPPLEMENT_COUNTS[group][:exam_index])
    parameter_index = offset + ordinal - 1
    question_type = row["questionType"]
    prompt = {"single": "请选择正确答案。", "fill": "请填入结果。", "solve": "求解并写出主要步骤。"}[question_type]

    if group == "17":
        value = 2 + parameter_index
        answer = value * value - 1
        row["chapter"], row["topic"] = "行列式", "行列式"
        row["questionText"] = f"求矩阵 A=[[{value},1],[1,{value}]] 的行列式。\n{prompt}"
        row["answerText"] = f"二阶行列式 det(A)={value}·{value}−1·1={answer}。"
        if question_type == "single":
            set_choices(row, answer, [value * value, value * value - 2, 0])
        else:
            row["answer"] = str(answer)

    elif group == "18":
        value = 2 + parameter_index
        answer = 2 if value == 5 else 3
        row["chapter"], row["topic"] = "矩阵", "矩阵的秩"
        row["questionText"] = f"求矩阵 A=[[1,1,1],[1,2,3],[1,3,{value}]] 的秩。\n{prompt}"
        if value == 5:
            row["answerText"] = "矩阵行列式为0，但左上角二阶子式为1不为0，所以矩阵的秩为2。"
        else:
            row["answerText"] = f"矩阵行列式为 {value}−5={value - 5}，不为0，所以矩阵满秩，秩为3。"
        if question_type == "single":
            set_choices(row, answer, [0, 1, 2, 3])
        else:
            row["answer"] = str(answer)

    elif group == "19":
        value = 2 + parameter_index
        off_diagonal = 1 + parameter_index % 3
        answer = value + off_diagonal
        row["chapter"], row["topic"] = "矩阵的特征值与特征向量", "特征值与特征向量"
        row["questionText"] = f"矩阵 A=[[{value},{off_diagonal}],[{off_diagonal},{value}]] 的最大特征值是多少？\n{prompt}"
        row["answerText"] = (f"特征多项式为 (λ−{value})²−{off_diagonal ** 2}=0，特征值为 "
                             f"{value}+{off_diagonal} 与 {value}−{off_diagonal}，最大值为 {answer}。")
        if question_type == "single":
            set_choices(row, answer, [answer - 1, answer + 1, value - off_diagonal])
        else:
            row["answer"] = str(answer)

    elif group == "20":
        value = 1 + parameter_index
        row["chapter"], row["topic"] = "二次型", "二次型"
        row["questionText"] = f"二次型 q(x,y)=(x+{value}y)² 的秩是多少？\n{prompt}"
        row["answerText"] = (f"对应矩阵为 [[1,{value}],[{value},{value ** 2}]]，其行列式为0且矩阵非零，"
                             "因此秩为1。")
        if question_type != "single":
            row["answer"] = "1"

    elif group == "21":
        x = 1 + parameter_index
        y = x + 1
        row["chapter"], row["topic"] = "向量", "向量组之间的线性表示"
        row["questionText"] = (f"向量组 α₁=(1,0)，α₂=(0,1)，α₃=({x},{y})。"
                               f"求 α₃ 在 α₁、α₂ 下的线性表示系数。\n{prompt}")
        row["answerText"] = f"按坐标比较，α₃={x}α₁+{y}α₂，故系数为 ({x},{y})。"
        if question_type == "single":
            set_choices(row, f"({x},{y})", [f"({y},{x})", f"({x},{x})", "0"])
        else:
            row["answer"] = f"({x},{y})"
    return row


def normalize(row):
    if row.get("chapter") == "矩阵的特征值和特征向量":
        row["chapter"] = "矩阵的特征值与特征向量"

    row["topic"] = TOPIC_ALIASES.get(row.get("topic"), row.get("topic"))

    if row.get("isSupplemental"):
        row = normalize_supplemental(row)

    row["topicPath"] = f"{row['subject']}/{row['chapter']}/{row['topic']}"
    return row


def write_rows(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main():
    past = [normalize(row) for row in read_rows("past_questions.jsonl")]
    supplemental = [normalize(row) for row in read_rows("supplemental_questions.jsonl")]
    if (len(past), len(supplemental), len(past) + len(supplemental)) != (
        EXPECTED["past"], EXPECTED["supplemental"], EXPECTED["total"]
    ):
        raise SystemExit(f"Unexpected bank size: {len(past)} past + {len(supplemental)} supplemental")
    if any(q.get("subject") != "线性代数" or q.get("isSupplemental") for q in past):
        raise SystemExit("past_questions.jsonl must contain only past exam linear algebra questions")
    if any(q.get("subject") != "线性代数" or not q.get("isSupplemental") for q in supplemental):
        raise SystemExit("supplemental_questions.jsonl must contain only labeled supplemental questions")
    if Counter(q["exam"] for q in past) != Counter({exam: 90 for exam in EXAMS}):
        raise SystemExit("Expected all 90 past questions per exam type")
    if Counter(q["exam"] for q in supplemental) != Counter({exam: 16 for exam in EXAMS}):
        raise SystemExit("Expected all 16 supplemental questions per exam type")
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
            if q.get("isSupplemental") and len(options) != 4:
                raise SystemExit(f"Supplemental single-choice question needs four options: {q['id']}")
        if q.get("isSupplemental") and (q.get("examYear") is not None or q.get("questionNo") is not None):
            raise SystemExit(f"Supplemental question must not be labeled as a past exam: {q['id']}")
        if q.get("isSupplemental"):
            match = re.fullmatch(r"SUP-[^-]+-L-(\d+)-(\d+)", q["id"])
            group, ordinal = match.group(1), int(match.group(2))
            exam_index = EXAMS.index(q["exam"])
            offset = sum(SUPPLEMENT_COUNTS[group][:exam_index])
            parameter_index = offset + ordinal - 1
            expected_answer = None
            if group == "17":
                value = 2 + parameter_index
                expected_answer = str(value * value - 1)
            elif group == "18":
                value = 2 + parameter_index
                expected_answer = str(2 if value == 5 else 3)
            elif group == "19":
                value, off_diagonal = 2 + parameter_index, 1 + parameter_index % 3
                expected_answer = str(value + off_diagonal)
            elif group == "20":
                expected_answer = "1"
            elif group == "21":
                x = 1 + parameter_index
                expected_answer = f"({x},{x+1})"
            actual = q.get("options", {}).get(q.get("answer")) if q["questionType"] == "single" else str(q.get("answer"))
            if actual != expected_answer:
                raise SystemExit(f"Incorrect supplemental answer for {q['id']}: {actual!r}, expected {expected_answer!r}")
            if not q.get("answerText") or not q.get("studyTip"):
                raise SystemExit(f"Supplemental question needs offline explanation and a study tip: {q['id']}")

    rows.sort(key=lambda q: (EXAMS.index(q["exam"]), bool(q.get("isSupplemental")),
                             q.get("examYear") or 9999, q.get("questionNo") or 9999, q["id"]))
    write_rows(DATA / "past_questions.jsonl", past)
    write_rows(DATA / "supplemental_questions.jsonl", supplemental)
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
        "note": "包含数学一、数学二、数学三题库中的全部线性代数题；按教材章节整理，历年真题与补充练习分别标记。",
    }
    (DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote all {len(rows)} questions: {len(past)} past questions and {len(supplemental)} supplemental questions.")


if __name__ == "__main__":
    main()
