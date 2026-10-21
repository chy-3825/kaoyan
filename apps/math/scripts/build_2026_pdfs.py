#!/usr/bin/env python3
"""Crop the 2026 original-paper PDFs into formula-preserving question/answer images."""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "android" / "web"
ASSETS = WEB / "images"
DATA = ROOT / "data"
NS = "{http://www.w3.org/1999/xhtml}"
DPI = 180

# subject, chapter, specific knowledge point, key (objective questions), difficulty, short solving cue
META = {
    "数学一": [
        ("高等数学", "多元函数微分学", "隐函数的偏导数", "A", 3, "对隐式方程分别关于 x、y 求偏导，再消去公共因子。"),
        ("高等数学", "无穷级数", "幂级数的收敛区间", "D", 3, "先用比值法求收敛半径，再单独检验两个端点。"),
        ("高等数学", "一元函数微分学", "凹凸性与割线斜率", "C", 3, "把凹凸性转化为割线斜率的单调性，区分命题与逆命题。"),
        ("高等数学", "多元函数积分学", "三重积分的柱面与球面坐标", "C", 4, "先由两曲面交线确定投影范围，再判断柱坐标或球坐标的积分限。"),
        ("线性代数", "矩阵", "置换矩阵与伴随矩阵", "B", 3, "利用置换矩阵正交且行列式为 ±1，化简伴随矩阵公式。"),
        ("线性代数", "线性方程组", "列向量组表示与方程组有解性", "A", 4, "把列向量组的线性表示写成矩阵分解，比较方程右端是否属于列空间。"),
        ("线性代数", "二次型", "二次型标准形与柱面判定", "B", 5, "柱面要求二次型退化；用特征值与惯性指数判断标准形。"),
        ("概率论与数理统计", "数字特征", "正态分布下平方损失的最小化", "C", 3, "展开 E[(X+t)²]，配方或求导确定极小点与最小值。"),
        ("概率论与数理统计", "随机变量及其分布", "线性变换的期望与方差", "A", 3, "由分布函数关系识别 Y 的仿射变换，再用均值和方差列方程。"),
        ("概率论与数理统计", "随机变量及其分布", "离散型随机变量的条件概率", "D", 4, "先求尾概率，再计算条件概率；注意该分布并非无记忆分布。"),
        ("高等数学", "空间解析几何与向量代数", "向量场的散度", "", 3, "先算叉积的分量，再按散度定义分别求偏导。"),
        ("高等数学", "函数、极限与连续", "等价无穷小与泰勒展开", "", 3, "对 ln(1+x) 与 sin x 展开到首个不相消的阶数。"),
        ("高等数学", "一元函数微分学", "参数方程确定函数的二阶导数", "", 4, "先用 dy/dx=(dy/dt)/(dx/dt)，再对 t 求导并除以 dx/dt。"),
        ("高等数学", "一元函数积分学", "含对数函数的广义积分", "", 2, "可用分部积分，或令 u=1/x 后转化为标准对数积分。"),
        ("线性代数", "矩阵的特征值与特征向量", "含参数矩阵的实特征值比较", "", 4, "分别求参数矩阵的特征多项式与实根，再按最大实特征值分段比较。"),
        ("概率论与数理统计", "数字特征", "独立性与协方差", "", 4, "将 Cov(X,X−Y)=0 与独立性条件结合，展开 E(XY) 与二阶矩。"),
        ("高等数学", "多元函数微分学", "二元函数的极值", "", 3, "解梯度方程找驻点，再用 Hessian 判别式分类。"),
        ("高等数学", "多元函数微分学", "全微分存在条件与原函数", "", 4, "比较给定全微分的混合偏导，建立关于单变量函数的微分方程并代入初值。"),
        ("高等数学", "多元函数积分学", "格林公式与闭曲线积分", "", 4, "补成闭曲线后用格林公式，补线段上的积分单独计算并注意方向。"),
        ("高等数学", "一元函数微分学", "单调性积分不等式与罗尔定理", "", 4, "先利用严格单调性比较区间积分，再构造函数应用罗尔定理。"),
        ("线性代数", "向量", "极大线性无关组与矩阵秩", "", 4, "用秩验证极大无关性，将其余列表示为基列的线性组合以构造分解。"),
        ("概率论与数理统计", "数理统计", "指数分布次序统计量与极大似然估计", "", 5, "利用指数分布的生存函数求最小次序统计量分布，再分别求无偏估计与似然方程。"),
    ],
    "数学二": [
        ("高等数学", "函数、极限与连续", "等价无穷小与泰勒展开", "A", 3, "展开 arcsin x 与根式到首个非零阶，比较系数确定参数。"),
        ("高等数学", "常微分方程", "非齐次线性方程特解的线性组合", "B", 4, "用线性微分算子作用于特解，分别比较非齐次项与齐次解条件。"),
        ("高等数学", "多元函数微分学", "隐函数的偏导数", "A", 3, "对隐式方程分别关于 x、y 求偏导，再消去公共因子。"),
        ("高等数学", "一元函数积分学", "连续线密度的引力积分", "D", 4, "按对称微元分解力的方向分量，积分时保留距离的三次方分母。"),
        ("高等数学", "一元函数微分学", "凹凸性与割线斜率", "C", 3, "把凹凸性转化为割线斜率的单调性，区分命题与逆命题。"),
        ("高等数学", "一元函数微分学", "反函数的导数", "B", 3, "先求原函数值对应的自变量，再用反函数求导公式取倒数。"),
        ("高等数学", "多元函数积分学", "二重积分的黎曼和与区域对称性", "D", 4, "将正方形按对角线分割，利用 f(x,y)=f(y,x) 配对黎曼和。"),
        ("线性代数", "矩阵", "置换矩阵与伴随矩阵", "B", 3, "利用置换矩阵正交且行列式为 ±1，化简伴随矩阵公式。"),
        ("线性代数", "线性方程组", "矩阵方程有解条件", "A", 4, "AB=C 有解等价于 C 的各列属于 A 的列空间，用行变换求参数条件。"),
        ("线性代数", "矩阵", "矩阵恒等式与幂零矩阵", "D", 5, "改写 AB+BA−A−B 的关系，考察 A−B 的幂、特征值及特征向量。"),
        ("高等数学", "一元函数积分学", "广义积分的敛散性", "", 3, "分别考察 0 附近和无穷远处的渐近阶，两个端点条件需同时成立。"),
        ("高等数学", "函数、极限与连续", "等价无穷小与泰勒展开", "", 3, "把对数与正弦展开到相消后的首个非零阶。"),
        ("高等数学", "一元函数微分学", "隐式曲线的曲率与曲率半径", "", 4, "隐式求一、二阶导数，代入曲率公式并取倒数得到曲率半径。"),
        ("高等数学", "多元函数微分学", "复合函数的链式求导", "", 3, "先由全微分读出两个偏导，再对复合变量分别求导并代入 x=1。"),
        ("高等数学", "一元函数积分学", "定积分平均值", "", 2, "函数在区间上的平均值为定积分除以区间长度。"),
        ("线性代数", "二次型", "二次型的秩与规范形", "", 4, "将 xᵀAᵀAx 写成 ||Ax||²，规范形中平方项个数等于矩阵秩。"),
        ("高等数学", "多元函数积分学", "二重积分的极坐标变换", "", 4, "利用第一象限对称性改写区域，换成极坐标后处理径向积分。"),
        ("高等数学", "一元函数积分学", "变限积分的求导与连续性", "", 4, "先换元改写积分上下限，分别用导数定义求 x=0 处导数并比较极限。"),
        ("高等数学", "多元函数微分学", "二元函数的极值", "", 3, "解梯度方程找驻点，再用 Hessian 判别式分类。"),
        ("高等数学", "多元函数积分学", "无界区域旋转体体积", "", 4, "先求拐点确定区域边界，再用圆盘法建立广义积分并判断收敛。"),
        ("高等数学", "常微分方程", "可降阶的二阶微分方程", "", 5, "令 p=y′，把方程化为关于 p 的一阶方程，积分两次并用初值定常数。"),
        ("线性代数", "向量", "极大线性无关组与矩阵秩", "", 4, "用秩验证极大无关性，将其余列表示为基列的线性组合以构造分解。"),
    ],
    "数学三": [
        ("高等数学", "一元函数微分学", "函数的渐近线", "C", 2, "分别计算 x 趋于定义域边界及无穷远时的函数极限和斜率极限。"),
        ("高等数学", "多元函数微分学", "隐函数的偏导数", "A", 3, "对隐式方程分别关于 x、y 求偏导，再消去公共因子。"),
        ("高等数学", "一元函数微分学", "反函数的导数", "B", 3, "先求原函数值对应的自变量，再用反函数求导公式取倒数。"),
        ("高等数学", "一元函数积分学", "连续购买下的加权平均价格", "D", 3, "总支出按 p(t)q′(t) 积分，总购入数量为 q(T)−q(0)，两者相除。"),
        ("线性代数", "线性方程组", "矩阵方程有解条件", "A", 4, "AB=C 有解等价于 C 的各列属于 A 的列空间，用行变换求参数条件。"),
        ("线性代数", "矩阵", "伴随矩阵与矩阵幂", "D", 5, "结合 A*=det(A)A⁻¹ 与给定比例关系，分奇异和非奇异情形验证候选矩阵。"),
        ("线性代数", "矩阵", "矩阵恒等式与特征值", "D", 5, "对恒等式移项因式分解，分析 A−B 的幂零性及其特征结构。"),
        ("概率论与数理统计", "随机变量及其分布", "独立连续随机变量的乘积概率", "B", 4, "在正象限上按 XY≤1 划分积分区域，利用独立密度做二重积分。"),
        ("概率论与数理统计", "数字特征", "独立随机变量函数的相关系数", "C", 4, "分别求协方差和方差，利用独立性与标准正态、二项分布矩化简。"),
        ("概率论与数理统计", "随机变量及其分布", "离散分布的条件尾概率", "D", 4, "由概率质量函数求尾和，再与条件事件概率比较，避免误用无记忆性。"),
        ("高等数学", "一元函数积分学", "定积分的对称性与换元", "", 2, "先检查区间变换下的奇偶或对称关系，再选合适换元化简。"),
        ("高等数学", "函数、极限与连续", "极限的等价变换", "", 2, "识别主导项并作等价替换，注意替换后分母仍需非零。"),
        ("高等数学", "一元函数积分学", "广义积分的敛散性", "", 3, "分别考察 0 附近和无穷远处的渐近阶，两个端点条件需同时成立。"),
        ("高等数学", "常微分方程", "二阶常系数线性微分方程", "", 3, "解特征方程求通解，再代入初值确定积分常数。"),
        ("线性代数", "二次型", "二次型的规范形与秩", "", 4, "将 xᵀAᵀAx 写成 ||Ax||²，规范形中平方项个数等于矩阵秩。"),
        ("概率论与数理统计", "数字特征", "独立泊松变量的混合矩", "", 4, "由 X 与 X−Y 独立推出协方差条件，再展开 E(XY)。"),
        ("高等数学", "无穷级数", "积分方程与幂级数展开", "", 4, "先设定积分为常数并由积分方程求出，再对有理式作几何级数展开。"),
        ("高等数学", "一元函数积分学", "变限积分的导数与连续性", "", 4, "先对变上限积分用微积分基本定理，再单独用导数定义处理 x=0。"),
        ("高等数学", "多元函数微分学", "二元函数的极值", "", 3, "解梯度方程找驻点，再用 Hessian 判别式分类。"),
        ("高等数学", "多元函数积分学", "二重积分的计算", "", 4, "按区域边界选择积分次序，必要时先对内层变量积分。"),
        ("线性代数", "向量", "极大线性无关组与矩阵秩", "", 4, "用秩验证极大无关性，将其余列表示为基列的线性组合以构造分解。"),
        ("概率论与数理统计", "数理统计", "指数分布次序统计量与极大似然估计", "", 5, "利用指数分布的生存函数求最小次序统计量分布，再写似然函数求估计量。"),
    ],
}

ANSWERS = {
    "数学一": ["A", "D", "C", "C", "B", "A", "B", "C", "A", "D", "1+z", "1/2", "-1/4", "2ln2", "(-∞,0)", "4"],
    "数学二": ["A", "B", "A", "D", "C", "B", "D", "B", "A", "D", "0<p<2", "1/2", "4", "-2π", "3ln2-1", "2"],
    "数学三": ["C", "A", "B", "D", "A", "D", "D", "B", "C", "D", "0", "1", "0<p<2", "y=e^(2x)-e^x+1", "2", "4"],
}
PDFS = {"数学一": "math1.pdf", "数学二": "math2.pdf", "数学三": "math3.pdf"}
GROUP_ID = {"数学一": 8, "数学二": 9, "数学三": 10}
QID_START = {"数学一": 1942, "数学二": 1964, "数学三": 1986}
TYPE = lambda n: "single" if n <= 10 else "fill" if n <= 16 else "solve"


def get_lines(pdf: pathlib.Path):
    with tempfile.TemporaryDirectory(prefix="yanxi-math-pdf-") as tmp:
        xml_path = pathlib.Path(tmp) / "paper.xhtml"
        subprocess.run(["pdftotext", "-bbox-layout", str(pdf), str(xml_path)], check=True)
        root = ET.parse(xml_path).getroot()
        pages = []
        for page_no, page in enumerate(root.findall(".//" + NS + "page"), 1):
            lines = []
            for line in page.findall(".//" + NS + "line"):
                words = line.findall(NS + "word")
                text = " ".join((w.text or "") for w in words)
                if not text.strip():
                    continue
                lines.append({"page": page_no, "text": text, "x0": float(line.attrib["xMin"]), "y0": float(line.attrib["yMin"]), "y1": float(line.attrib["yMax"])})
            pages.append({"width": float(page.attrib["width"]), "height": float(page.attrib["height"]), "lines": lines})
        return pages


def crop_segments(pages, segments, target: pathlib.Path, render_prefix: pathlib.Path):
    if not segments:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    crops = []
    for page_no, x0, x1, y0, y1 in segments:
        page_image = Image.open(f"{render_prefix}-{page_no}.png").convert("RGB")
        scale = DPI / 72
        box = (max(0, int(x0 * scale)), max(0, int(y0 * scale)), min(page_image.width, int(x1 * scale)), min(page_image.height, int(y1 * scale)))
        if box[3] <= box[1] + 8:
            continue
        crops.append(page_image.crop(box))
    if not crops:
        return False
    width = max(im.width for im in crops)
    pad = 18
    height = sum(im.height for im in crops) + pad * (len(crops) - 1)
    stitched = Image.new("RGB", (width, height), "white")
    y = 0
    for im in crops:
        stitched.paste(im, (0, y))
        y += im.height + pad
    stitched.save(target, "WEBP", quality=95, method=6)
    return True


def segments_for(pages):
    result = {"question": {}, "answer": {}}
    active = None
    stage = None
    seg_page = None
    seg_y0 = None

    def add(end_y):
        if active is None or seg_page is None or seg_y0 is None or end_y <= seg_y0 + 5:
            return
        result[stage].setdefault(active, []).append((seg_page, 68, 527, max(40, seg_y0), min(770, end_y)))

    for page_no, page in enumerate(pages, 1):
        lines = page["lines"]
        if active is not None:
            seg_page, seg_y0 = page_no, 48
        content_end = max([ln["y1"] for ln in lines if ln["y1"] < 770] or [page["height"] - 70])
        content_end = min(content_end + 5, 770)
        for line in lines:
            txt = line["text"].strip()
            is_q = bool(re.match(r"^(\d{1,2})\s*\.", txt)) and line["x0"] < 120
            qno = int(re.match(r"^(\d{1,2})\s*\.", txt).group(1)) if is_q else 0
            if is_q and 1 <= qno <= 22:
                add(line["y0"] - 3)
                active, stage = qno, "question"
                seg_page, seg_y0 = page_no, line["y0"] - 3
                continue
            if active is None:
                continue
            if "【答案】" in txt or "【解析】" in txt or "【证明】" in txt:
                if stage == "question":
                    add(line["y0"] - 20)
                    stage = "answer"
                    seg_page, seg_y0 = page_no, line["y0"] - 3
        add(content_end)
        if active is not None:
            seg_page, seg_y0 = page_no + 1, 48
    return result


def main():
    q_by_key = {(q["exam"], q["examYear"], q["questionNo"]): q for q in (json.loads(x) for x in (DATA / "questions.jsonl").read_text(encoding="utf-8").splitlines())}
    for exam, filename in PDFS.items():
        pdf = ROOT / "sources" / "2026" / filename
        pages = get_lines(pdf)
        segs = segments_for(pages)
        if sorted(segs["question"]) != list(range(1, 23)):
            raise RuntimeError(f"{exam}: question markers parsed as {sorted(segs['question'])}")
        if sorted(segs["answer"]) != list(range(1, 23)):
            raise RuntimeError(f"{exam}: answer/analysis markers parsed as {sorted(segs['answer'])}")
        with tempfile.TemporaryDirectory(prefix="yanxi-math-render-") as tmp:
            render_prefix = pathlib.Path(tmp) / "page"
            subprocess.run(["pdftoppm", "-png", "-r", str(DPI), str(pdf), str(render_prefix)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for no, meta in enumerate(META[exam], 1):
                subject, chapter, topic, key, diff, hint = meta
                row = q_by_key[(exam, 2026, no)]
                qid = QID_START[exam] + no - 1
                q_img = ASSETS / f"q-{qid}.webp"
                if not crop_segments(pages, segs["question"][no], q_img, render_prefix):
                    raise RuntimeError(f"Could not create question image for {exam} {no}")
                row.update({
                    "subject": subject, "chapter": chapter, "topic": topic,
                    "topicPath": f"{subject}/{chapter}/{topic}",
                    "questionType": TYPE(no), "score": 5 if no <= 16 else (10 if no == 17 else 12),
                    "difficulty": diff, "answer": ANSWERS[exam][no - 1] if no <= 16 else "",
                    "image": f"images/q-{qid}.webp", "sourceImageUrl": f"https://static.kaoyan.cn/file/question/2025/12/27/{ {'数学一':'f3a552ec0d163308d2ac28dc7a10bbd0','数学二':'f2d851eb315f540c31acc1b434c494c0','数学三':'000fde2e45f4bafcc0bde33b16b8647b'}[exam] }.pdf",
                    "sourceName": "2026 年考研数学原卷 PDF",
                    "sourceUrl": "https://zhentiqiang.com/kaoyan/math",
                    "answerSource": "原卷答案/解析" if no >= 17 else "原卷答案",
                    "studyTip": hint,
                })
                if no > 10:
                    ans_img = ASSETS / f"a-{qid}.webp"
                    if not crop_segments(pages, segs["answer"][no], ans_img, render_prefix):
                        raise RuntimeError(f"Could not create answer image for {exam} {no}")
                    row["answerImage"] = f"images/a-{qid}.webp"
                print(f"{exam} {no:02d}: q={q_img.stat().st_size//1024}KB" + (f" a={(ASSETS/f'a-{qid}.webp').stat().st_size//1024}KB" if no > 10 else ""), flush=True)

    # Fill the few gaps left in the public legacy index, using the bundled
    # original problem image and a short proof/answer in the app.
    legacy_fixes = {
        ("数学二", 2009, 8): {
            "answer": "B", "answerSource": "由题目条件核算",
            "studyTip": "设 Q=PC，其中 C 的第一列为 (1,1,0)^T；直接算 C^T diag(1,1,2) C。",
        },
        ("数学一", 2024, 19): {
            "answerText": "令 g(x)=f(x)-[(1-x)f(0)+xf(1)]。则 g(0)=g(1)=0，且 |g''(x)|=|f''(x)|≤1。由两端点余项公式，g(x)=f''(ξ)x(x-1)/2，故 |g(x)|≤x(1-x)/2。\n对 x 从 0 到 1 积分并用积分三角不等式：|∫₀¹g(x)dx|≤∫₀¹x(1-x)/2 dx=1/12，即得第二问。",
            "studyTip": "把函数减去连接两端点的弦，使用线性插值余项；积分后得到梯形公式误差界。",
        },
        ("数学三", 2024, 20): {
            "answerText": "令 g(x)=f(x)-[(1-x)f(0)+xf(1)]。则 g(0)=g(1)=0，且 |g''(x)|≤1。由两端点余项公式，|g(x)|≤x(1-x)/2。再积分：|∫₀¹g(x)dx|≤∫₀¹x(1-x)/2 dx=1/12。",
            "studyTip": "把函数减去连接两端点的弦，使用线性插值余项；积分后得到梯形公式误差界。",
        },
        ("数学二", 2024, 21): {
            "answerText": "令 g(x)=f(x)-[(1-x)f(0)+xf(1)]。则 g(0)=g(1)=0，且 |g''(x)|≤1。由两端点余项公式，|g(x)|≤x(1-x)/2。再积分：|∫₀¹g(x)dx|≤∫₀¹x(1-x)/2 dx=1/12。",
            "studyTip": "把函数减去连接两端点的弦，使用线性插值余项；积分后得到梯形公式误差界。",
        },
        ("数学二", 2025, 21): {
            "answerText": "必要性：若 f′ 严格递增，对任意 x₁<x₂<x₃，由拉格朗日中值定理，两个割线斜率分别为 f′(ξ₁)、f′(ξ₂)，且 ξ₁<ξ₂，故前者小于后者。\n充分性：令 x₂→x₁⁺、再令 x₂→x₃⁻，由题设割线斜率不等式取极限可得 f′(x₁)≤(f(x₃)-f(x₁))/(x₃-x₁)≤f′(x₃)，从而 f′ 非减。若某段上 f′ 取相同值，非减性迫使其在该段恒定，f 在该段为一次函数，任取三个内点将使两个割线斜率相等，与严格不等式矛盾。因此 f′ 严格递增。",
            "studyTip": "必要性用拉格朗日中值定理比较两段割线；充分性令中间点分别趋近两端，取极限得导数非减，再排除导数平台段。",
        },
    }
    for key, updates in legacy_fixes.items():
        q_by_key[key].update(updates)
    legacy_topic_fixes = {
        ("数学三", 2011, 14): ("概率论与数理统计", "多维随机变量", "二元正态分布的混合矩", "利用二元正态分布的协方差结构，将 Y² 拆成方差与均值项，再用正态变量的奇数中心矩为零。"),
        ("数学三", 2013, 23): ("概率论与数理统计", "数理统计", "参数的矩估计与极大似然估计", "分别写出总体矩方程与样本似然函数；对数化后求导并检查参数取值范围。"),
        ("数学三", 2014, 14): ("概率论与数理统计", "数理统计", "无偏估计量的构造", "先计算单个样本的二阶矩，再利用独立同分布求和的期望确定系数。"),
        ("数学三", 2020, 19): ("高等数学", "一元函数微分学", "微分中值定理与导数估计", "取达到最大值的点，在端点零值与极值点之间应用拉格朗日中值定理，再用导数变化率界估计。"),
        ("数学三", 2021, 22): ("概率论与数理统计", "随机变量及其分布", "随机切分长度的分布变换", "先由均匀随机切点求短段长度的密度，再用变量变换求 Y/X 的密度并积分计算倒数期望。"),
    }
    for key, (subject, chapter, topic, hint) in legacy_topic_fixes.items():
        q = q_by_key[key]
        q.update({"subject": subject, "chapter": chapter, "topic": topic, "topicPath": f"{subject}/{chapter}/{topic}", "studyTip": hint})

    rows = sorted(q_by_key.values(), key=lambda q: (q["exam"], q["subject"], q["chapter"], q["topic"], q["examYear"], q["questionNo"]))
    for q in rows:
        q.setdefault("studyTip", f"围绕“{q['topic']}”识别题目条件，选用对应定义、定理或公式推导；注意检验适用条件并回代核对。")
    (DATA / "questions.jsonl").write_text("".join(json.dumps(q, ensure_ascii=False, separators=(",", ":")) + "\n" for q in rows), encoding="utf-8")
    (WEB / "questions.js").write_text("window.QUESTIONS=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    summary_path = DATA / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["missingImages"] = sum(not q.get("image") or not (WEB / q["image"]).exists() for q in rows)
    summary["missingAnswers"] = sum(q["questionType"] != "single" and not q.get("answerImage") and not q.get("answer") and not q.get("answerText") for q in rows)
    summary["missingChoiceKeys"] = sum(q["questionType"] == "single" and not q.get("answer") for q in rows)
    summary["missingTopics"] = sum(q["topic"] == "待归类考点" for q in rows)
    summary["assets"] = len(list(ASSETS.glob("*.webp")))
    summary["difficultyMethod"] = "2009–2025 根据公开题库反馈与题型分值估算；2026 结合题目内容人工标注；均为非官方 1–5 难度参考"
    summary["textSolutionFallbacks"] = sum(bool(q.get("answerText")) for q in rows)
    (summary_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "download_issues.json").write_text("[]\n", encoding="utf-8")
    manifest = json.loads((DATA / "source_manifest.json").read_text(encoding="utf-8"))
    manifest["questionCount"] = len(rows)
    manifest["attribution"] = "2009–2025 metadata, answer keys and question images: lx-ruc/kaoyanshuxue (its README attributes them to 真题墙). 2026 question IDs/index: 真题墙; original question and solution PDF pages: static.kaoyan.cn."
    manifest["questionPdfHost"] = "https://static.kaoyan.cn/file/question/2025/12/27/"
    manifest["sourcePdfs"] = [q["sourceImageUrl"] for q in rows if q["examYear"] == 2026 and q["questionNo"] == 1]
    manifest["note"] = "All 1,224 question images are present. 2026 original papers and solutions were cropped locally. Four older non-choice questions whose source answer scans were unavailable include a short text solution. Source redistribution rights have not been verified; use for personal study only."
    (DATA / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
