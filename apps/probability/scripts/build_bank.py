#!/usr/bin/env python3
"""Validate, order, and package this app's complete standalone question bank."""
import collections, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
WEB=ROOT/"android"/"web"
SOURCE=DATA/"questions.jsonl"
OUTPUT=WEB/"questions.js"
SUBJECT='概率论与数理统计'
EXPECTED=221
CHAPTER_ORDER=['随机事件和概率', '随机变量及其分布', '多维随机变量及其分布', '随机变量的数字特征', '大数定律和中心极限定理', '数理统计的基本概念', '参数估计与假设检验']
TOPIC_ORDER={'随机事件和概率': ['随机事件和概率'], '随机变量及其分布': ['随机变量及其分布', '离散型随机变量的条件概率', '离散分布的条件尾概率', '随机切分长度的分布变换', '独立连续随机变量的乘积概率', '线性变换的期望与方差'], '多维随机变量及其分布': ['二维随机变量及其分布', '边缘分布与条件分布', '二元正态分布的混合矩'], '随机变量的数字特征': ['数学期望与方差', '独立泊松变量的混合矩', '独立随机变量函数的相关系数', '协方差与相关系数', '独立性与协方差', '正态分布下平方损失的最小化'], '大数定律和中心极限定理': ['大数定律和中心极限定理'], '数理统计的基本概念': ['数理统计的基本概念'], '参数估计与假设检验': ['矩估计和最大似然估计', '参数估计', '参数的矩估计与极大似然估计', '指数分布次序统计量与极大似然估计', '无偏估计量的构造', '估计量的无偏性', '区间估计和置信区间', '假设检验']}
EXAMS=("数学一","数学二","数学三")
def rank(items,value):
    try: return items.index(value)
    except ValueError: return len(items)
def main():
    rows=[json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows)!=EXPECTED or any(q.get("subject")!=SUBJECT for q in rows):
        raise SystemExit(f"Expected {EXPECTED} rows for {SUBJECT}; got {len(rows)}")
    ids=[q.get("id") for q in rows]
    if not all(ids) or len(set(ids))!=len(ids): raise SystemExit("Question IDs must be nonempty and unique")
    if any(q.get("chapter") not in CHAPTER_ORDER for q in rows):
        raise SystemExit("Question bank contains a chapter missing from the textbook order")
    for q in rows:
        if q.get("exam") not in EXAMS: raise SystemExit(f"Unexpected exam for {q['id']}: {q.get('exam')}")
        if q.get("questionType") not in {"single","fill","solve"}: raise SystemExit(f"Unknown type: {q['id']}")
        if not (q.get("image") or q.get("questionText")): raise SystemExit(f"Missing prompt: {q['id']}")
        if not (q.get("answer") or q.get("answerText") or q.get("answerImage")): raise SystemExit(f"Missing answer: {q['id']}")
        expected_path=f"{SUBJECT}/{q['chapter']}/{q['topic']}"
        if q.get("topicPath")!=expected_path: raise SystemExit(f"Bad topic path for {q['id']}")
        for field in ("image","answerImage"):
            asset=q.get(field)
            if asset and not (WEB/asset).is_file(): raise SystemExit(f"Missing {field}: {q['id']} {asset}")
    rows.sort(key=lambda q:(rank(CHAPTER_ORDER,q["chapter"]),rank(TOPIC_ORDER.get(q["chapter"],[]),q["topic"]),q["topic"],q.get("examYear") or 9999,rank(EXAMS,q["exam"]),q.get("questionNo") or 9999,q["id"]))
    SOURCE.write_text("".join(json.dumps(q,ensure_ascii=False,separators=(",",":"))+"\n" for q in rows),encoding="utf-8")
    OUTPUT.write_text("window.QUESTIONS="+json.dumps(rows,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
    past=[q for q in rows if not q.get("isSupplemental")]
    supplemental=[q for q in rows if q.get("isSupplemental")]
    chapter_counts=collections.Counter(q["chapter"] for q in rows)
    by_chapter={c:chapter_counts[c] for c in CHAPTER_ORDER if chapter_counts[c]}
    summary={"subject":SUBJECT,"total":len(rows),"pastExam":len(past),"supplemental":len(supplemental),"byExam":dict(collections.Counter(q["exam"] for q in rows)),"byChapter":by_chapter,"byTopic":{c:dict(collections.Counter(q["topic"] for q in rows if q["chapter"]==c)) for c in by_chapter},"types":dict(collections.Counter(q["questionType"] for q in rows)),"questionsWithImage":sum(bool(q.get("image")) for q in rows),"questionsWithAnswerImage":sum(bool(q.get("answerImage")) for q in rows),"uniqueImages":len({asset for q in rows for asset in (q.get("image"),q.get("answerImage")) if asset}),"note":'全部概率论与数理统计题；同一考点的重复章节标签已合并到教材知识结构。'}
    (DATA/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Built {SUBJECT}: {len(rows)} questions ({len(past)} past exam + {len(supplemental)} supplemental).")
    print("Chapters: "+", ".join(f"{c} {n}" for c,n in by_chapter.items()))
if __name__=="__main__": main()
