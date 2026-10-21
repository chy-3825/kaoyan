#!/usr/bin/env python3
"""Validate, order, and package this app's complete standalone question bank."""
import collections, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
WEB=ROOT/"android"/"web"
SOURCE=DATA/"questions.jsonl"
OUTPUT=WEB/"questions.js"
SUBJECT='高等数学'
EXPECTED=925
CHAPTER_ORDER=['函数、极限与连续', '一元函数微分学', '一元函数积分学', '常微分方程与差分方程', '向量代数与空间解析几何', '多元函数微分学', '多元函数积分学', '无穷级数']
TOPIC_ORDER={'函数、极限与连续': ['函数极限的计算', '数列极限的概念与性质', '数列极限的计算', '数列敛散性的判定', '无穷小量', '无穷小量的比较', '极限的等价变换', '函数的连续性', '函数的连续性与间断点的类型', '确定极限中的参数', '等价无穷小与泰勒展开'], '一元函数微分学': ['导数与微分的概念', '导数与微分的计算', '导数的几何意义', '反函数的导数', '参数方程确定函数的二阶导数', '函数的单调性、极值与最值', '曲线的凹凸性、拐点及渐近线', '函数的渐近线', '导数的应用', '微分中值定理', '微分中值定理与导数估计', '泰勒公式', '方程根的存在性与个数', '不等式', '不等式的证明', '凹凸性与割线斜率', '单调性积分不等式与罗尔定理', '微分学在经济学中的应用', '隐式曲线的曲率与曲率半径'], '一元函数积分学': ['不定积分的计算', '定积分的概念与性质', '定积分的概念、性质及几何意义', '定积分的计算', '定积分的对称性与换元', '变限积分', '变限积分的求导与连续性', '定积分的应用', '连续线密度的引力积分', '连续购买下的加权平均价格', '定积分平均值', '一元函数积分学综合题', '反常积分的计算与敛散性', '广义积分的敛散性', '含对数函数的广义积分'], '常微分方程与差分方程': ['微分方程的解与线性微分方程的解的结构', '线性微分方程的解的结构', '可分离变量的微分方程', '可分离变量的微分方程与齐次方程', '一阶线性微分方程', '二阶常系数线性微分方程', '常系数齐次线性微分方程', '二阶常系数非齐次线性微分方程', '非齐次线性方程特解的线性组合', '微分方程的应用', '其他方程', '差分方程'], '向量代数与空间解析几何': ['向量场的散度'], '多元函数微分学': ['偏导数的概念与计算', '全微分的概念与计算', '全微分存在条件与原函数', '复合函数的链式求导', '隐函数的偏导数', '方向导数和梯度', '多元函数微分学的几何应用', '多元函数的极值问题', '二元函数的极值'], '多元函数积分学': ['二重积分的概念与性质', '二重积分的计算', '二重积分的极坐标变换', '二次积分与变换积分次序', '交换积分次序与坐标系之间的转化', '二重积分的黎曼和与区域对称性', '二重积分的综合与应用', '二重积分的应用', '重积分的概念与性质', '重积分的计算', '重积分的应用', '三重积分的柱面与球面坐标', '无界区域旋转体体积', '第一类曲线积分', '第二类曲线积分', '格林公式与闭曲线积分', '第一类曲面积分', '第二类曲面积分', '旋度的定义'], '无穷级数': ['数项级数', '常数项级数敛散性的判定', '幂级数的收敛区间', '幂级数', '求幂级数的收敛半径、收敛区间和收敛域', '幂级数的和函数及幂级数展开式', '积分方程与幂级数展开', '傅里叶级数']}
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
    summary={"subject":SUBJECT,"total":len(rows),"pastExam":len(past),"supplemental":len(supplemental),"byExam":dict(collections.Counter(q["exam"] for q in rows)),"byChapter":by_chapter,"byTopic":{c:dict(collections.Counter(q["topic"] for q in rows if q["chapter"]==c)) for c in by_chapter},"types":dict(collections.Counter(q["questionType"] for q in rows)),"questionsWithImage":sum(bool(q.get("image")) for q in rows),"questionsWithAnswerImage":sum(bool(q.get("answerImage")) for q in rows),"uniqueImages":len({asset for q in rows for asset in (q.get("image"),q.get("answerImage")) if asset}),"note":'全部高等数学题；原题库中的多元函数微积分混合章节按题目考点拆分为微分学、积分学。'}
    (DATA/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Built {SUBJECT}: {len(rows)} questions ({len(past)} past exam + {len(supplemental)} supplemental).")
    print("Chapters: "+", ".join(f"{c} {n}" for c,n in by_chapter.items()))
if __name__=="__main__": main()
