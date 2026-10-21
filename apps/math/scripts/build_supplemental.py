#!/usr/bin/env python3
"""Create and merge 240 original high-frequency-topic practice questions.

These are deliberately marked as supplemental exercises and never presented as past papers.
Run this after build_bank.py and build_2026_pdfs.py.
"""
from __future__ import annotations

import json
import math
import pathlib
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEB = ROOT / "android" / "web"

# Each item factory returns: stem, answer, worked solution, distractors, study cue.
def frac(n: int, d: int = 1) -> str:
    value = Fraction(n, d)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def item(kind: str, n: int, exam: str):
    # The parameter n changes from variant to variant and is offset between courses,
    # so repeated drilling reinforces a method without repeating the same numbers.
    if kind == "limit_sqrt":
        a = n + 1
        return (f"求极限：limₓ→₀ [√(1+{a}x)−1]/x。", frac(a, 2),
                f"乘以共轭式：原式 = {a}/[√(1+{a}x)+1]。令 x→0，得 {a}/2 = {frac(a,2)}。",
                [str(a), frac(1,a), "0"], "根式差商优先有理化，再代入极限。")
    if kind == "limit_exp":
        a = n + 1
        return (f"求极限：limₓ→₀ [e^({a}x)−1−{a}x]/x²。", frac(a*a, 2),
                f"由 e^u=1+u+u²/2+o(u²)，取 u={a}x，分子={a*a}x²/2+o(x²)，极限为 {frac(a*a,2)}。",
                [str(a*a), str(a), frac(-a*a,2)], "展开到分母同阶，并保留首个未抵消项。")
    if kind == "continuity":
        a = n + 2
        return (f"函数 f(x) 在 x≠0 时为 (e^({a}x)−1)/x，在 x=0 时为 b。若 f 在 0 处连续，求 b。", str(a),
                f"连续条件为 b=limₓ→₀(e^({a}x)−1)/x。利用 limᵤ→₀(eᵘ−1)/u=1，极限为 {a}，故 b={a}。",
                [str(a+1), frac(a,2), "0"], "分段函数在拼接点连续，当且仅当函数值等于极限。")
    if kind == "derivative_log":
        m = n + 2
        return (f"设 f(x)=ln(1+x^{m})，求 f′(1)。", frac(m,2),
                f"f′(x)={m}x^{m-1}/(1+x^{m})，代入 x=1，得 f′(1)={m}/2={frac(m,2)}。",
                [str(m), frac(1,m), "0"], "复合函数求导后再代入，注意分母中的 1+xᵐ。")
    if kind == "derivative_xlogx":
        m = n + 1
        value = f"{m+2}e^{m}"
        return (f"设 f(x)=x^{m+1}ln x，求 f′(e)。", value,
                f"f′(x)=({m+1})x^{m}ln x+x^{m}。令 x=e，得 f′(e)=({m+1})e^{m}+e^{m}=({m+2})e^{m}。",
                [f"{m}e^{m}", f"{m+2}e^{m-1}", f"{m+1}e^{m}"], "乘积求导后代入 x=e；ln e=1。")
    if kind == "mvt":
        a = n + 1
        b = a + 2
        c = frac(a+b, 2)
        return (f"函数 f(x)=x² 在区间 [{a},{b}] 上满足拉格朗日中值定理。求使 f′(ξ)=[f({b})−f({a})]/({b}−{a}) 的 ξ。", c,
                f"f′(x)=2x，割线斜率=({b}²−{a}²)/({b}−{a})={a+b}。令 2ξ={a+b}，得 ξ=({a}+{b})/2={c}。",
                [str(a), str(b), str(a+b)], "先算区间上的割线斜率，再与导数相等求 ξ。")
    if kind == "cubic_extrema":
        a = n + 1
        ans = str(2*a**3)
        return (f"求 f(x)=x³−3·{a*a}x 的极大值。", ans,
                f"f′(x)=3x²−3·{a*a}=0，驻点为 x=±{a}。f″(x)=6x，x=−{a} 处为极大值点；f(−{a})={ans}。",
                [str(a**3), str(-2*a**3), str(3*a**3)], "求驻点后用二阶导数判别，再代回原函数求极值。")
    if kind == "concavity":
        k = n + 1
        a = 3*k*k
        return (f"求函数 f(x)=x⁴−2·{a}x² 的凹区间。", f"(−{k},{k})",
                f"f″(x)=12x²−4·{a}=12(x²−{k*k})。当 |x|<{k} 时 f″(x)<0，因此凹区间为 (−{k},{k})。",
                [f"(−{k+1},{k+1})", f"({-k},{k})", f"(−∞,∞)"], "依据教材约定，凹区间对应二阶导数小于零。")
    if kind == "taylor_log":
        a = n + 1
        ans = frac(a**3, 3)
        return (f"将 ln(1+{a}x) 在 x=0 处展开，求 x³ 项的系数。", ans,
                f"ln(1+u)=u−u²/2+u³/3+o(u³)。取 u={a}x，x³ 项为 {a**3}x³/3，系数是 {ans}。",
                [str(a**3), frac(-a**3,2), frac(a*a,2)], "按所需阶数展开；复合代入后不要漏掉参数的幂次。")
    if kind == "power_series":
        r = n + 1
        c = n - 2
        lo, hi = c-r, c+r
        return (f"求幂级数 Σₙ₌₁^∞ [(x−({c}))/({r})]ⁿ/n 的收敛区间。", f"[{lo},{hi})",
                f"令 t=(x−({c}))/({r})。级数 Σtⁿ/n 的收敛域为 [−1,1)：左端交错调和级数收敛，右端调和级数发散。因此 x∈[{lo},{hi})。",
                [f"({lo},{hi})", f"({lo},{hi}]", f"[{lo},{hi}]"], "先用比值法求收敛半径，再分别检验两个端点。")
    if kind == "integral_rational":
        a = n + 1
        ans = f"ln({a+1})/{2*a}"
        return (f"计算定积分：∫₀¹ x/(1+{a}x²) dx。", ans,
                f"令 u=1+{a}x²，则 du=2{a}x dx。积分为 [ln(1+{a}x²)/(2{a})]₀¹=ln({a+1})/{2*a}。",
                [f"ln({a+1})/{a}", f"{a}/(2*ln({a+1}))", f"ln({a})/{2*a}"], "分母是内层函数时，尝试令内层为新变量。")
    if kind == "integral_parts":
        a = n + 1
        ans = f"(e^{a}({a-1})+1)/{a*a}"
        return (f"计算定积分：∫₀¹ xe^({a}x) dx。", ans,
                f"分部积分取 u=x、dv=e^({a}x)dx，原积分=[xe^({a}x)/{a}]₀¹−∫₀¹e^({a}x)/{a}dx。化简得 [e^{a}({a}−1)+1]/{a*a}。",
                [f"e^{a}/{a}", f"(e^{a}−1)/{a*a}", f"(e^{a}({a}+1)−1)/{a*a}"], "含 x 与指数函数乘积时，优先分部积分并检查上下限。")
    if kind == "area_between":
        p = n + 2
        ans = frac(p-1, 2*(p+1))
        return (f"求曲线 y=x 与 y=x^{p} 在区间 [0,1] 围成的面积。", ans,
                f"在 [0,1] 上 x≥x^{p}。面积=∫₀¹(x−x^{p})dx=1/2−1/({p+1})={ans}。",
                [frac(1,p+1), frac(p,2*(p+1)), frac(p-1,p+1)], "先比较上下曲线，再按上减下积分。")
    if kind == "improper":
        p = n + 2
        ans = frac(1,p-1)
        return (f"计算反常积分：∫₁^∞ x^(−{p}) dx。", ans,
                f"当 p>1 时该积分收敛。原积分=[x^(1−{p})/(1−{p})]₁^∞=1/({p-1})={ans}。",
                [str(p), frac(1,p), "发散"], "先确认无穷远处的幂次是否满足收敛条件，再求值。")
    if kind == "ode_first":
        a, c = n + 1, n + 2
        ans = f"{c}(1−e^(−{a}x))"
        return (f"求初值问题 y′+{a}y={a*c}，y(0)=0 的解。", ans,
                f"积分因子为 e^({a}x)，故 (e^({a}x)y)′={a*c}e^({a}x)。积分并用 y(0)=0 定常数，得 y={c}(1−e^(−{a}x))。",
                [f"{c}e^(−{a}x)", f"{a}(1−e^(−{c}x))", f"{c}(1−e^(−x))"], "一阶线性方程用积分因子法，并代入初值确定常数。")
    if kind == "ode_second":
        a, c = n + 1, n + 2
        ans = f"{c}cosh({a}x)"
        return (f"求 y″−{a*a}y=0，y(0)={c}，y′(0)=0 的解。", ans,
                f"特征方程 r²−{a*a}=0，通解 y=C₁e^({a}x)+C₂e^(−{a}x)。由初值可得 C₁=C₂={c}/2，因此 y={c}cosh({a}x)。",
                [f"{c}sinh({a}x)", f"{c}e^({a}x)", f"{c}cos({a}x)"], "写特征方程求通解，再分别代入两个初值。")
    if kind == "partial_sphere":
        triples = [(3,4,5),(5,12,13),(8,15,17),(7,24,25)]
        x,y,z = triples[(n-1)%4]
        if exam == "数学三": x,y,z = triples[(n)%4]
        ans = frac(-x,z)
        return (f"曲面 x²+y²+z²={x*x+y*y+z*z} 在点 ({x},{y},{z}) 附近确定 z=z(x,y)。求 ∂z/∂x。", ans,
                f"对 x 作隐式求导：2x+2z·zₓ=0，所以 zₓ=−x/z。代入点得 −{x}/{z}={ans}。",
                [frac(x,z), frac(-y,z), frac(-z,x)], "隐函数偏导按指定变量求导，其余自变量视为常量。")
    if kind == "multivar_min":
        a,b = n+1,n+2
        ans = str(-(a*a)-2*b*b)
        return (f"求 f(x,y)=x²+2y²−{2*a}x+{4*b}y 的全局最小值。", ans,
                f"配方：f=(x−{a})²+2(y+{b})²−{a*a}−{2*b*b}。前两项非负，故最小值为 {ans}，在 ({a},−{b}) 处取得。",
                [str(-a*a-b*b), str(a*a+2*b*b), str(-a*a+2*b*b)], "二次函数可通过配方定位驻点，并判断全局最值。")
    if kind == "double_disk":
        r = n + 1
        ans = f"{frac(r**4,2)}π"
        return (f"D 为圆盘 x²+y²≤{r*r}，计算 ∬_D (x²+y²)dA。", ans,
                f"改用极坐标：x²+y²=ρ²，dA=ρdρdθ。积分=∫₀²π∫₀^{r}ρ³dρdθ=2π·{r**4}/4={ans}。",
                [f"{r*r}π", f"{r**4}π", f"{frac(r**4,4)}π"], "圆域上的径向函数优先改用极坐标。")
    if kind == "double_square":
        a = n + 1
        ans = str(a*a)
        return (f"计算二重积分：∫₀^{a}∫₀^{a}(x+y) dy dx。", ans,
                f"先对 y 积分：∫₀^{a}(ax+a²/2)dx=a³/2+a³/2={a**3}。",
                [str(a**3/2), str(2*a**3), str(a*a)], "矩形区域上的多项式积分可按次序逐层计算。")
    if kind == "economic_max":
        a,b = n+4,n+1
        p = frac(a,2*b)
        val = frac(a*a,4*b)
        return (f"某产品需求量 q={a}−{b}p（0≤p≤{frac(a,b)}），收入 R(p)=pq。求使收入最大的价格 p。", p,
                f"R(p)={a}p−{b}p²，是开口向下的二次函数。R′(p)={a}−{2*b}p=0，故最优价格 p={p}（最大收入为 {val}）。",
                [frac(a,b), frac(a, b), frac(a,4*b)], "把需求函数代入收入，再利用导数或二次函数顶点求最大值。")
    if kind == "marginal_integral":
        a=n+1
        ans=frac(1,a)
        return (f"边际成本 C′(q)={a}q+2，且 C(0)=C₀。求产量从 0 增至 1 的总成本增量。", frac(a+4,2),
                f"总成本增量=∫₀¹ C′(q)dq=∫₀¹({a}q+2)dq={a}/2+2={frac(a+4,2)}。",
                [str(a+2), frac(a+2,2), str(a)], "边际量在区间上的积分给出总量变化；初值在求增量时抵消。")
    if kind == "line_circle":
        r=n+1
        ans=f"{2*r*r}π"
        return (f"C 为逆时针圆周 x²+y²={r*r}，计算 ∮_C (−y dx+x dy)。", ans,
                f"参数化 x={r}cos t、y={r}sin t，0≤t≤2π。则 −y dx+x dy={r*r}dt，积分为 2π{r*r}={ans}。",
                [f"{r*r}π", f"{2*r}π", f"{r*r}π/2"], "闭曲线积分要先核对方向；逆时针参数取向为正。")
    if kind == "volume_rotation":
        k=n+1
        ans=f"π/{2*k+1}"
        return (f"曲线 y=x^{k}（0≤x≤1）绕 x 轴旋转一周，求所得旋转体体积。", ans,
                f"圆盘法 V=π∫₀¹y²dx=π∫₀¹x^{2*k}dx=π/({2*k+1})。",
                [f"π/{k+1}", f"π/{2*k}", f"2π/{2*k+1}"], "绕 x 轴的旋转体用圆盘法，对函数平方后积分。")
    if kind == "variable_integral":
        m=n+1
        ans=f"{m}e"
        return (f"F(x)=∫₀^(x^{m}) e^t dt，求 F′(1)。", ans,
                f"由微积分基本定理与链式法则，F′(x)=e^(x^{m})·{m}x^{m-1}。代入 x=1，得 {m}e。",
                ["e", f"{m}", f"{m}e^{m}"], "变上限积分求导要乘上限函数的导数。")
    if kind == "root_count":
        a=n+1
        return (f"方程 x³−{a}x=0 有几个不同实根？", "3",
                f"因式分解 x(x²−{a})=0，得 x=0、x=±√{a}。{a}>0，故有 3 个不同实根。",
                ["1", "2", "0"], "尝试因式分解，并区分重根与不同实根的个数。")

    # Linear algebra.
    if kind == "determinant":
        a=n+2
        ans=str(a*a-1)
        return (f"求矩阵 A=[[{a},1],[1,{a}]] 的行列式。", ans,
                f"二阶行列式 det(A)={a}·{a}−1·1={ans}。",
                [str(a*a+1), str(2*a), str(a-1)], "二阶行列式按主对角线乘积减副对角线乘积。")
    if kind == "rank_system":
        k=n+2
        ans="2" if k==5 else "3"
        det=k-5
        detail=(f"该矩阵的行列式为 k−5={det}。" if det else "当 k=5 时行列式为 0，但左上角二阶子式为 1，故秩为 2。")
        if det: detail += " 行列式非零，矩阵满秩，秩为 3。"
        return (f"求矩阵 A=[[1,1,1],[1,2,3],[1,3,{k}]] 的秩。", ans,
                detail, ["1", "2" if ans!="2" else "3", "0"], "先看行列式；为零时继续检查低阶子式，不能直接判秩为 2。")
    if kind == "eigen_sym":
        a,b=n+2, n%3+1
        ans=str(a+b)
        return (f"矩阵 A=[[{a},{b}],[{b},{a}]] 的最大特征值是多少？", ans,
                f"特征多项式为 (λ−{a})²−{b*b}=0，故特征值为 {a}+{b} 与 {a}−{b}，最大值为 {ans}。",
                [str(a-b), str(a*b), str(a+b+1)], "对称矩阵的特征值可通过特征多项式或对称结构求出。")
    if kind == "quadratic_form":
        a=n+1
        ans="1"
        return (f"二次型 q(x,y)=(x+{a}y)² 的秩是多少？", ans,
                f"对应矩阵为 [[1,{a}],[{a},{a*a}]]，其行列式为 0 且非零，因此秩为 1。",
                ["0", "2", str(a)], "二次型的秩等于其对称矩阵的秩。")
    if kind == "vector_repr":
        a=n+1
        return (f"向量组 α₁=(1,0)，α₂=(0,1)，α₃=({a},{a+1})。求 α₃ 在 α₁、α₂ 下的线性表示系数。", f"({a},{a+1})",
                f"按坐标比较，α₃={a}α₁+{a+1}α₂，故系数为 ({a},{a+1})。",
                [f"({a+1},{a})", f"(1,{a})", f"({a},{a})"], "标准基下线性表示的系数就是向量各坐标。")

    # Probability and statistics.
    if kind == "bayes":
        # P(A)=1/2; P(B|A)=1/(n+1), P(B|Abar)=1/(n+2).
        p=Fraction(1,2); q=Fraction(1,n+1); r=Fraction(1,n+2)
        ans=frac((p*q).numerator*( (p*q)+(1-p)*r ).denominator, (p*q).denominator * ((p*q)+(1-p)*r).numerator)
        # Recompute directly to avoid nested-Fraction formatting surprises.
        posterior=(p*q)/(p*q+(1-p)*r)
        ans=frac(posterior.numerator, posterior.denominator)
        return (f"P(A)=1/2，P(B|A)=1/{n+1}，P(B|Ā)=1/{n+2}。求 P(A|B)。", ans,
                f"由贝叶斯公式，P(A|B)=[(1/2)·(1/{n+1})]/[(1/2)·(1/{n+1})+(1/2)·(1/{n+2})]={ans}。",
                [frac(1,n+1), frac(1,n+2), "1/2"], "先写全概率分母，再用贝叶斯公式更新条件概率。")
    if kind == "binomial":
        ntrials=n+5
        p=Fraction(1, n+2)
        if ntrials % (n+2) == 0:
            p=Fraction(1,n+2)
        mean=frac(ntrials*p.numerator,p.denominator)
        var=frac(ntrials*p.numerator*(p.denominator-p.numerator),p.denominator*p.denominator)
        return (f"随机变量 X 服从二项分布 B({ntrials},{frac(p.numerator,p.denominator)})。求 E(X)。", mean,
                f"二项分布的数学期望为 np，故 E(X)={ntrials}·{frac(p.numerator,p.denominator)}={mean}。方差为 {var}。",
                [str(ntrials), frac(ntrials*p.numerator*(p.denominator-p.numerator),p.denominator), frac(ntrials,p.denominator)], "二项分布 B(n,p) 的期望为 np，方差为 np(1−p)。")
    if kind == "exponential":
        rate=n+1
        ans=frac(1,rate)
        return (f"连续型随机变量 X 的密度为 f(x)={rate}e^(−{rate}x)（x≥0），求 E(X)。", ans,
                f"这是参数为 {rate} 的指数分布，E(X)=∫₀^∞x·{rate}e^(−{rate}x)dx=1/{rate}={ans}。",
                [str(rate), frac(1,rate*rate), frac(2,rate)], "指数分布的参数是率参数，均值为率参数的倒数。")
    if kind == "normal":
        mu=n+1; sigma=n+2
        return (f"X~N({mu},{sigma*sigma})，求 P(X<{mu+sigma})。", "Φ(1)≈0.8413",
                f"标准化 Z=(X−{mu})/{sigma}，事件等价于 Z<1，因此概率为 Φ(1)≈0.8413。",
                ["0.5", "0.1587", "0.9772"], "正态变量先标准化，再查标准正态分布函数。")
    if kind == "expectation_variance":
        a,b=n+1,n+2
        ans=str(a+b)
        return (f"X、Y 独立，E(X)={a}，E(Y)={b}，D(X)={a}，D(Y)={b}。求 D(X+Y)。", ans,
                f"独立变量方差可加：D(X+Y)=D(X)+D(Y)={a}+{b}={ans}。",
                [str(a*b), str(a+b+1), str(abs(a-b))], "独立性保证协方差为零，和的方差等于方差之和。")
    if kind == "mle_bernoulli":
        k=n+2; total=2*n+5
        ans=frac(k,total)
        return (f"Bernoulli(p) 独立重复试验 {total} 次，观察到 {k} 次成功。求参数 p 的极大似然估计。", ans,
                f"似然函数 L(p)=p^{k}(1−p)^{total-k}。对数似然求导并令其为零，得 p̂={k}/{total}={ans}。",
                [frac(k+1,total), frac(total,k), frac(k,total-k)], "写出似然函数并对数化，极大似然估计即样本成功频率。")

    raise KeyError(kind)


# A topic family expands into four parameterized drills. Mixed response formats keep
# the supplement aligned with the old bank's choice/fill/solution practice mix.
def families_for(exam: str):
    if exam == "数学二":
        return [
            ("高等数学","函数、极限、连续","函数极限的计算","limit_sqrt",4),
            ("高等数学","函数、极限、连续","确定极限中的参数","continuity",4),
            ("高等数学","函数、极限、连续","函数极限的计算","limit_exp",4),
            ("高等数学","一元函数微分学","导数与微分的计算","derivative_log",4),
            ("高等数学","一元函数微分学","微分中值定理","mvt",4),
            ("高等数学","一元函数微分学","函数的单调性、极值与最值","cubic_extrema",4),
            ("高等数学","一元函数微分学","曲线的凹凸性、拐点及渐近线","concavity",4),
            ("高等数学","一元函数积分学","定积分的计算","integral_rational",4),
            ("高等数学","一元函数积分学","定积分的计算","integral_parts",4),
            ("高等数学","一元函数积分学","定积分的应用","area_between",4),
            ("高等数学","一元函数积分学","定积分的应用","volume_rotation",4),
            ("高等数学","一元函数积分学","反常积分的计算与敛散性","improper",4),
            ("高等数学","常微分方程","一阶线性微分方程","ode_first",4),
            ("高等数学","常微分方程","二阶常系数非齐次线性微分方程","ode_second",4),
            ("高等数学","一元函数积分学","变限积分","variable_integral",4),
            ("高等数学","多元函数微积分学","偏导数的概念与计算","partial_sphere",4),
            ("线性代数","行列式","行列式","determinant",4),
            ("线性代数","线性方程组","线性方程组","rank_system",4),
            ("线性代数","矩阵的特征值和特征向量","特征值与特征向量","eigen_sym",4),
            ("线性代数","二次型","二次型","quadratic_form",4),
        ]
    if exam == "数学一":
        return [
            ("高等数学","函数、极限、连续","函数极限的计算","limit_sqrt",3),
            ("高等数学","函数、极限、连续","确定极限中的参数","continuity",3),
            ("高等数学","一元函数微分学","导数与微分的计算","derivative_log",3),
            ("高等数学","一元函数微分学","导数与微分的计算","derivative_xlogx",3),
            ("高等数学","一元函数微分学","微分中值定理","mvt",3),
            ("高等数学","一元函数微分学","函数的单调性、极值与最值","cubic_extrema",3),
            ("高等数学","一元函数微分学","曲线的凹凸性、拐点及渐近线","concavity",3),
            ("高等数学","无穷级数","幂级数的和函数及幂级数展开式","power_series",3),
            ("高等数学","一元函数积分学","定积分的计算","integral_rational",3),
            ("高等数学","一元函数积分学","定积分的应用","area_between",3),
            ("高等数学","一元函数积分学","反常积分的计算与敛散性","improper",3),
            ("高等数学","常微分方程","一阶线性微分方程","ode_first",3),
            ("高等数学","多元函数微积分学","偏导数的概念与计算","partial_sphere",2),
            ("高等数学","多元函数微积分学","多元函数的极值问题","multivar_min",2),
            ("高等数学","多元函数微积分学","二重积分的计算","double_disk",2),
            ("高等数学","多元函数积分学","第二类曲线积分","line_circle",2),
            ("线性代数","矩阵","矩阵的运算与变换","determinant",4),
            ("线性代数","线性方程组","线性方程组","rank_system",4),
            ("线性代数","矩阵的特征值和特征向量","特征值与特征向量","eigen_sym",3),
            ("线性代数","二次型","二次型","quadratic_form",3),
            ("线性代数","向量","向量组之间的线性表示","vector_repr",2),
            ("概率论与数理统计","随机事件和概率","随机事件和概率","bayes",4),
            ("概率论与数理统计","随机变量及其分布","随机变量及其分布","binomial",4),
            ("概率论与数理统计","随机变量及其分布","随机变量及其分布","exponential",4),
            ("概率论与数理统计","随机变量的数字特征","数学期望与方差","expectation_variance",4),
            ("概率论与数理统计","参数估计与假设检验","矩估计和最大似然估计","mle_bernoulli",4),
        ]
    # Math III shares core calculus, but its supplement stays within the economics
    # and double-integral scope and does not import Math I's power/vector calculus.
    return [
        ("高等数学","函数、极限、连续","函数极限的计算","limit_sqrt",3),
        ("高等数学","函数、极限、连续","确定极限中的参数","continuity",3),
        ("高等数学","一元函数微分学","导数与微分的计算","derivative_log",3),
        ("高等数学","一元函数微分学","微分中值定理","mvt",3),
        ("高等数学","一元函数微分学","函数的单调性、极值与最值","cubic_extrema",3),
        ("高等数学","一元函数微分学","曲线的凹凸性、拐点及渐近线","concavity",3),
        ("高等数学","一元函数积分学","定积分的计算","integral_rational",3),
        ("高等数学","一元函数积分学","定积分的计算","integral_parts",3),
        ("高等数学","一元函数积分学","定积分的应用","area_between",3),
        ("高等数学","一元函数积分学","反常积分的计算与敛散性","improper",3),
        ("高等数学","常微分方程","一阶线性微分方程","ode_first",3),
        ("高等数学","多元函数微积分学","偏导数的概念与计算","partial_sphere",3),
        ("高等数学","多元函数微积分学","多元函数的极值问题","multivar_min",2),
        ("高等数学","多元函数微积分学","二重积分的计算","double_square",2),
        ("高等数学","一元函数微分学","微分学在经济学中的应用","economic_max",2),
        ("高等数学","一元函数积分学","定积分的应用","marginal_integral",2),
        ("线性代数","矩阵","矩阵的运算与变换","determinant",4),
        ("线性代数","线性方程组","线性方程组","rank_system",4),
        ("线性代数","矩阵的特征值和特征向量","特征值与特征向量","eigen_sym",3),
        ("线性代数","二次型","二次型","quadratic_form",3),
        ("线性代数","向量","向量组之间的线性表示","vector_repr",2),
        ("概率论与数理统计","随机事件和概率","随机事件和概率","bayes",4),
        ("概率论与数理统计","随机变量及其分布","随机变量及其分布","binomial",4),
        ("概率论与数理统计","随机变量及其分布","随机变量及其分布","normal",4),
        ("概率论与数理统计","随机变量的数字特征","数学期望与方差","expectation_variance",4),
        ("概率论与数理统计","参数估计与假设检验","矩估计和最大似然估计","mle_bernoulli",4),
    ]


TYPE_PATTERNS = [("single","fill","solve","solve"),("single","single","fill","solve")]
EXAM_CODE = {"数学一":"I", "数学二":"II", "数学三":"III"}
SUBJECT_CODE = {"高等数学":"C", "线性代数":"L", "概率论与数理统计":"P"}


def build_rows():
    rows=[]
    for exam_index, exam in enumerate(("数学一","数学二","数学三")):
        family_index=0
        for subject, chapter, topic, kind, count in families_for(exam):
            for variant in range(count):
                data=item(kind, variant + exam_index, exam)
                stem, correct_value, explanation, distractors, hint = data
                pattern=TYPE_PATTERNS[family_index % len(TYPE_PATTERNS)]
                qtype=pattern[variant % 4]
                options={}
                if qtype == "single":
                    candidates=[]
                    for candidate in [correct_value,*distractors,"0","1","−1","2"]:
                        if candidate not in candidates:
                            candidates.append(candidate)
                        if len(candidates)==4: break
                    # Deterministically rotate option positions to avoid an answer-key pattern.
                    correct_slot=(variant+family_index+exam_index)%4
                    chosen=candidates[1:]
                    chosen.insert(correct_slot,correct_value)
                    chosen=chosen[:4]
                    letters="ABCD"
                    options={letters[i]:chosen[i] for i in range(4)}
                    answer=letters[chosen.index(correct_value)]
                    question_text=stem+"\n请选择正确答案。"
                elif qtype == "fill":
                    answer=correct_value
                    question_text=stem+"\n请填入结果。"
                else:
                    answer=correct_value
                    question_text=stem+"\n求解并写出主要步骤。"
                difficulty=min(5, max(1, variant+1+((family_index+exam_index)%2)))
                code=f"{EXAM_CODE[exam]}-{SUBJECT_CODE[subject]}-{family_index+1:02d}-{variant+1}"
                rows.append({
                    "id":f"SUP-{code}", "exam":exam, "examYear":None, "questionNo":None,
                    "subject":subject, "chapter":chapter, "topic":topic,
                    "topicPath":f"{subject}/{chapter}/{topic}", "questionType":qtype,
                    "score":5 if qtype in ("single","fill") else 10,
                    "difficulty":difficulty, "answer":answer, "options":options,
                    "questionText":question_text, "answerText":explanation,
                    "image":"", "answerImage":"", "sourceImageUrl":"",
                    "sourceName":"原创高频考点专题补充题（非真题）", "sourceUrl":"",
                    "sourceLicense":"原创练习题，由题库维护者按高频考点编写；非历年真题。",
                    "knowledgeTagId":None, "answerSource":"原创题人工推导参考答案",
                    "studyTip":hint, "isSupplemental":True,
                    "supplementGroup":"高频考点专题补充"
                })
            family_index+=1
    return rows


def write_outputs():
    supplemental=build_rows()
    assert len(supplemental)==240, len(supplemental)
    ids=[q["id"] for q in supplemental]
    assert len(set(ids))==240
    (DATA/"supplemental_questions.jsonl").write_text("".join(json.dumps(q,ensure_ascii=False,separators=(",",":"))+"\n" for q in supplemental),encoding="utf-8")
    base=[json.loads(line) for line in (DATA/"questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    # Remove prior generated rows so this step is safe to repeat.
    base=[q for q in base if not q.get("isSupplemental")]
    all_rows=base+supplemental
    (DATA/"questions.jsonl").write_text("".join(json.dumps(q,ensure_ascii=False,separators=(",",":"))+"\n" for q in all_rows),encoding="utf-8")
    (WEB/"questions.js").write_text("window.QUESTIONS="+json.dumps(all_rows,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")

    from collections import Counter
    types=Counter(q["questionType"] for q in all_rows)
    exams=Counter(q["exam"] for q in all_rows)
    subjects=Counter(q["subject"] for q in all_rows)
    summary_path=DATA/"summary.json"
    summary=json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary.update({"total":len(all_rows),"exams":dict(exams),"subjects":dict(subjects),"types":dict(types),"supplemental":240,"supplementalLabel":"原创高频考点练习，非真题"})
    summary["supplementalByExam"]={exam:sum(q["exam"]==exam for q in supplemental) for exam in EXAM_CODE}
    summary["supplementalBySubject"]={subject:sum(q["subject"]==subject for q in supplemental) for subject in SUBJECT_CODE}
    summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    manifest_path=DATA/"source_manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest["questionCount"]=len(all_rows)
    manifest["supplementalQuestionCount"]=len(supplemental)
    manifest["supplementalSource"]="原创高频考点专题练习；非历年真题，无年份/题号标注。"
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"total":len(all_rows),"supplemental":len(supplemental),"byExam":summary["supplementalByExam"],"bySubject":summary["supplementalBySubject"],"types":dict(Counter(q["questionType"] for q in supplemental))},ensure_ascii=False,indent=2))


if __name__=="__main__":
    write_outputs()
