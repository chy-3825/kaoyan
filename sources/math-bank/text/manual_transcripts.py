"""Transcribed from the bundled original question images, never generated exercises.

Keys are original stable question IDs. Each value is (prompt, optional A–D options).
Original figures remain accessible in the app for comparison.
"""

TRANSCRIPTS = {
 'M-8-2026-01': (r'设 $z=z(x,y)$ 由方程 $x-az=e^{y+az}$（$a$ 是非零常数）确定，则（　）。', [r'$\frac{\partial z}{\partial x}-\frac{\partial z}{\partial y}=\frac1a$',r'$\frac{\partial z}{\partial x}+\frac{\partial z}{\partial y}=-\frac1a$',r'$\frac{\partial z}{\partial x}-\frac{\partial z}{\partial y}=-\frac1a$',r'$\frac{\partial z}{\partial x}+\frac{\partial z}{\partial y}=\frac1a$']),
 'M-8-2026-02': (r'幂级数 $\displaystyle\sum_{n=1}^{\infty}\left(\frac{3+(-1)^n}{4}\right)^n x^{2n}$ 的收敛域为（　）。', [r'$[-2,2]$',r'$[-1,1]$',r'$(-2,2)$',r'$(-1,1)$']),
 'M-8-2026-03': (r'已知 $f(x)$ 在区间 $[-1,1]$ 内有定义，则（　）。', [r'当 $f(x)$ 在 $(-1,0)$ 内单调递减、$(0,1)$ 内单调递增时，$f(0)$ 是极小值。',r'当 $f(0)$ 是极小值时，$f(x)$ 在 $(-1,0)$ 内单调递减、$(0,1)$ 内单调递增。',r'当 $f(x)$ 在区间 $[-1,1]$ 内是凹函数时，$\frac{f(x)-f(1)}{x-1}$ 在 $[-1,1]$ 上单调递增。',r'当 $\frac{f(x)-f(1)}{x-1}$ 在 $[-1,1]$ 上单调递增时，$f(x)$ 在区间 $[-1,1]$ 内是凹函数。']),
 'M-8-2026-04': (r'设 $z=\sqrt{4-x^2-y^2}$、$z=\sqrt{x^2+y^2}$ 两个曲面相交的有界闭区域为 $\Omega$，$f(u)$ 为连续函数，则 $\iiint_{\Omega}f(x^2+y^2+z^2)\,dv$ 可表示为（　）。', [r'$\int_0^{2\pi}d\theta\int_0^2dr\int_r^{\sqrt{4-r^2}}f(r^2+z^2)\,dz$',r'$\int_0^{2\pi}d\theta\int_0^{\sqrt2}dr\int_0^{\sqrt{4-r^2}}f(r^2+z^2)\,dz$',r'$\int_0^{2\pi}d\theta\int_0^{\pi/4}d\varphi\int_0^2f(r^2)r^2\sin\varphi\,dr$',r'$\int_0^{2\pi}d\theta\int_0^{\pi/2}d\varphi\int_0^2f(r^2)r^2\sin\varphi\,dr$']),
 'M-8-2026-05': (r'单位阵经过若干次两行互换得到的矩阵为置换矩阵。设 $A$ 为 $n$ 阶置换矩阵，$A^*$ 为 $A$ 的伴随矩阵，则（　）。',[r'$A^*$ 为置换矩阵',r'$A^{-1}$ 为置换矩阵',r'$A^*=A^{-1}$',r'$A^*=-A^{-1}$']),
 'M-8-2026-06': (r'设三阶矩阵 $A,B$，其中 $A$ 的列向量组可由 $B$ 的列向量组线性表示，则（　）。',[r'$Ax=\beta$ 有解时，$Bx=\beta$ 有解',r'$Bx=\beta$ 有解时，$Ax=\beta$ 有解',r'$A^{T}x=\beta$ 有解时，$B^{T}x=\beta$ 有解',r'$B^{T}x=\beta$ 有解时，$A^{T}x=\beta$ 有解']),
 'M-8-2026-07': (r'设 $f(x_1,x_2,x_3)=a(x_1^2+x_2^2+x_3^2)+4x_1x_2+4x_1x_3+4x_2x_3$，若 $f(x_1,x_2,x_3)=-1$ 表示柱面，则（　）。',[r'$a=-4$，对应的规范形为 $-y_1^2-y_2^2-y_3^2$',r'$a=-4$，在正交变换下的标准形为 $-6y_1^2-6y_2^2$',r'$a=2$，对应的规范形为 $-y_1^2-y_2^2-y_3^2$',r'$a=2$，在正交变换下的标准形为 $-6y_1^2-6y_2^2$']),
 'M-8-2026-08': (r'设随机变量 $X\sim N(1,2)$，$f(t)=E[(X+t)^2]$，则 $f(t)$ 的最小值点与最小值为（　）。',[r'$1,2$',r'$1,4$',r'$-1,2$',r'$-1,4$']),
 'M-8-2026-09': (r'设连续型随机变量 $X$ 的分布函数为 $F(x)$，随机变量 $Y$ 的分布函数为 $F(aY+b)$，$X$ 的数学期望为 $\mu$，方差为 $\sigma^2\ (\sigma>0)$，若 $Y$ 的数学期望与方差分别为 $0$ 和 $1$，则（　）。',[r'$a=\sigma,b=\mu$',r'$a=\sigma,b=-\mu$',r'$a=\frac1\sigma,b=\mu$',r'$a=\frac1\sigma,b=-\mu$']),
 'M-8-2026-10': (r'设随机变量 $X$ 的概率分布为 $P\{X=k\}=\frac1{2^{k+1}}+\frac1{3^k}\ (k=1,2,\ldots)$，则对任意的正整数 $m,n$ 有（　）。',[r'$P\{X>m+n\mid X>m\}=P\{X>m\}$',r'$P\{X>m+n\mid X>m\}=P\{X>n\}$',r'$P\{X>m+n\mid X>m\}>P\{X>m\}$',r'$P\{X>m+n\mid X>m\}>P\{X>n\}$']),
 'M-8-2026-11': (r'$\mathbf v_1=(0,x,z)$，$\mathbf v_2=(y,0,1)$，$\mathbf F(x,y,z)=\mathbf v_1\times\mathbf v_2$，则 $\operatorname{div}\mathbf F=$ ______。',None),
 'M-8-2026-12': (r'极限 $\displaystyle\lim_{x\to0}\left[\frac1x-\frac{\ln(1+x)}{x\sin x}\right]=$ ______。',None),
 'M-8-2026-13': (r'设函数 $y=y(x)$ 由参数方程 $\begin{cases}x=2\sin^2t,\\y=t+\cos t\end{cases}\ (t\in(0,\frac\pi2))$ 确定，则 $\left.\frac{d^2y}{dx^2}\right|_{t=\pi/4}=$ ______。',None),
 'M-8-2026-14': (r'$\displaystyle\int_1^{+\infty}\frac{\ln(1+x)}{x^2}\,dx=$ ______。',None),
 'M-8-2026-15': (r'设矩阵 $A=\begin{pmatrix}1&0&0\\2&a&2\\0&2&a\end{pmatrix}$，$B=\begin{pmatrix}a&-1&-1\\-1&2&1\\-1&-1&a\end{pmatrix}$，$m(X)$ 是矩阵 $X$ 的实值特征值的最大值，且 $m(A)<m(B)$，则 $a$ 的取值范围为 ______。',None),
 'M-8-2026-16': (r'设随机变量 $X$ 服从参数为 $1$ 的泊松分布，$Y$ 服从参数为 $3$ 的泊松分布，且 $X$ 和 $X-Y$ 相互独立，则 $E(XY)=$ ______。',None),
 'M-8-2026-17': (r'求函数 $f(x,y)=(2x^2-y^2)e^x$ 的极值。',None),
 'M-8-2026-18': (r'若函数 $f(u)$ 在区间 $(0,+\infty)$ 内有 $3$ 阶连续导数，且存在可微函数 $F(x,y)$ 使 $dF(x,y)=\frac{f(xy)}{x^2y}\,dx+\frac{f^{\prime\prime}(xy)}{xy^2}\,dy\ (xy>0)$。' '\n\n' r'（1）证明：$\frac{f^{\prime\prime}(u)}u-\frac{f(u)}u=C$，其中 $C$ 为任意常数。' '\n\n' r'（2）若 $f(1)=1,f^{\prime}(1)=-1,f^{\prime\prime}(1)=0$，求函数 $f(u)$ 的表达式。',None),
 'M-8-2026-19': (r'设有向曲线 $L$ 为椭圆 $x^2+3y^2=1$ 沿逆时针方向从点 $A(-\frac12,-\frac12)$ 到点 $B(\frac12,\frac12)$ 的部分，计算 $I=\int_L(e^{x^2}\sin x-2xy)\,dx+(6x-x^2-y\cos^4y)\,dy$。',None),
 'M-8-2026-20': (r'设可导函数 $f(x)$ 严格单调递增，且 $\int_{-1}^1f(x)\,dx=0$，设 $a=\int_0^1f(x)\,dx$。' '\n\n' r'（1）证明：$a>0$。' '\n\n' r'（2）若 $F(x)=a(1-x^2)+\int_1^xf(t)\,dt$，证明存在 $\xi\in(-1,1)$，使得 $F^{\prime\prime}(\xi)=0$。',None),
 'M-8-2026-21': (r'设向量组 $\alpha_1=(1,0,-1,-1)^T$，$\alpha_2=(1,-1,0,-2)^T$，$\alpha_3=(0,-1,1,-1)^T$，$\alpha_4=(0,1,-1,-1)^T$，$A=(\alpha_1,\alpha_2,\alpha_3,\alpha_4)$，$G=(\alpha_1,\alpha_2)$。' '\n\n' r'（1）证明 $\alpha_1,\alpha_2$ 是 $\alpha_1,\alpha_2,\alpha_3,\alpha_4$ 的一个极大无关组。' '\n\n' r'（2）求 $H$，满足 $A=GH$，并求 $A^{10}$。',None),
 'M-8-2026-22': (r'假设某种元件的寿命服从指数分布，其均值 $\theta$ 是未知参数。为估计 $\theta$，取 $n$ 个这种元件同时做寿命试验，试验到出现 $k$ 个元件失效时停止。' '\n\n' r'（1）若 $k=1$，失效元件的寿命记为 $T$：①计算 $T$ 的概率密度；②记 $\hat\theta=aT$，确定 $a$ 使得 $\hat\theta$ 是 $\theta$ 的无偏估计量，并求 $D(\hat\theta)$。' '\n\n' r'（2）已知 $k$ 个失效元件的寿命值分别为 $0\le t_1\le t_2\le\cdots\le t_k$，似然函数 $L(\theta)=\frac1{\theta^k}e^{-\frac1\theta[\sum_{i=1}^kt_i+(n-k)t_k]}$，求 $\theta$ 的最大似然估计值。',None),
}

TRANSCRIPTS.update({
 'M-9-2026-01': (r'已知当 $x\to0$ 时，$ax^2+bx+\arcsin x$ 与 $\sqrt[3]{1+x^2}-1$ 是等价无穷小，则（　）。',[r'$a=\frac13,b=-1$',r'$a=\frac13,b=1$',r'$a=\frac23,b=-1$',r'$a=\frac23,b=1$']),
 'M-9-2026-02': (r'设 $y_1(x),y_2(x)$ 是某二阶非齐次线性微分方程的两个特解。若常数 $\lambda,\mu$ 使得 $2\lambda y_1(x)+\mu y_2(x)$ 是该方程的解，$\lambda y_1(x)-2\mu y_2(x)$ 是该方程对应的齐次方程的解，则（　）。',[r'$\lambda=\frac15,\mu=\frac25$',r'$\lambda=\frac25,\mu=\frac15$',r'$\lambda=\frac14,\mu=\frac12$',r'$\lambda=\frac12,\mu=\frac14$']),
 'M-9-2026-04': (r'线密度为 $1$ 的线段在 $(-1,0)$ 和 $(1,0)$ 之间，质量为 $m$ 的质点在 $(0,1)$ 点，求质点对线段的引力（　）。',[r'$\int_0^1\frac{2Gmx}{(1+x^2)^{1/2}}\,dx$',r'$\int_0^1\frac{2Gm}{(1+x^2)^{1/2}}\,dx$',r'$\int_0^1\frac{2Gmx}{(1+x^2)^{3/2}}\,dx$',r'$\int_0^1\frac{2Gm}{(1+x^2)^{3/2}}\,dx$']),
 'M-9-2026-06': (r'已知 $f(x)=\int_1^{x^2}\frac{e^t}{1+t^2}\,dt$，$g(x)$ 为 $f(x)$ 的反函数，则（　）。',[r'$g(0)=1,g^{\prime}(0)=\frac32e$',r'$g(0)=1,g^{\prime}(0)=\frac2{3e}$',r'$g(1)=0,g^{\prime}(0)=\frac32e$',r'$g(1)=0,g^{\prime}(0)=\frac2{3e}$']),
 'M-9-2026-07': (r'设函数 $f(x,y)$ 在区域 $D=\{(x,y)\mid0\le x\le1,0\le y\le1\}$ 上连续，且 $f(x,y)=f(y,x)$，则 $\iint_Df(x,y)\,d\sigma=$（　）。',[r'$2\lim_{n\to\infty}\sum_{i=1}^n\sum_{j=n+1-i}^nf(\frac in,\frac jn)\frac1{n^2}$',r'$\frac12\lim_{n\to\infty}\sum_{i=1}^n\sum_{j=i}^nf(\frac in,\frac jn)\frac1{n^2}$',r'$2\lim_{n\to\infty}\sum_{i=1}^{2n}\sum_{j=1}^{2n+1-i}f(\frac i{2n},\frac j{2n})\frac1{n^2}$',r'$\frac12\lim_{n\to\infty}\sum_{i=1}^{2n}\sum_{j=1}^{i}f(\frac i{2n},\frac j{2n})\frac1{n^2}$']),
 'M-9-2026-09': (r'设矩阵 $A=\begin{pmatrix}1&0&1\\0&0&1\\1&1&3\\1&1&1\end{pmatrix}$，$C=\begin{pmatrix}2&0\\1&1\\1&1\\a&b\end{pmatrix}$，若存在矩阵 $B$ 满足 $AB=C$，则（　）。',[r'$a=-1,b=-1$',r'$a=2,b=2$',r'$a=-1,b=2$',r'$a=2,b=-1$']),
 'M-9-2026-10': (r'设三阶矩阵 $A,B$ 满足 $AB+BA=A^2+B^2$，且 $A\ne B$，则下列结论中错误的是（　）。',[r'$(A-B)^3=O$',r'$A-B$ 只有零特征值',r'$A$ 和 $B$ 不能都是对角矩阵',r'$A-B$ 只有一个线性无关的特征向量']),
 'M-9-2026-11': (r'已知 $p$ 为实数，$\int_0^{+\infty}\frac{\arctan x}{x^p(1+x)}\,dx$ 收敛，则 $p$ 的取值范围为 ______。',None),
 'M-9-2026-13': (r'求曲线 $x^2+2\sqrt3xy+y^2=1$ 在 $(0,1)$ 处的曲率半径 $R=$ ______。',None),
 'M-9-2026-14': (r'$f(x,y)$ 可微，且 $df(0,0)=\pi\,dx+3\,dy$，$g(x)=f(\ln x,\sin\pi x)$，计算 $g^{\prime}(1)=$ ______。',None),
 'M-9-2026-15': (r'求 $f(x)=\ln(2+x)$ 在 $[0,2]$ 上的平均值为 ______。',None),
 'M-9-2026-16': (r'设 $A=\begin{pmatrix}1&b&-1\\a+2&3&-3a\end{pmatrix}$，二次型 $x^TAA^Tx$ 的规范形为 $y_1^2$，则 $a+b=$ ______。',None),
 'M-9-2026-17': (r'计算 $I=\int_{-1}^1dx\int_{|x|}^{\sqrt{2-x^2}}y\sin\sqrt{x^2+y^2}\,dy$。',None),
 'M-9-2026-18': (r'设 $g(x)$ 连续，$f(x)=\int_0^{x^2}g(xt)\,dt$，求 $f^{\prime}(x)$ 表达式，并判断 $f^{\prime}(x)$ 在 $x=0$ 处的连续性。',None),
 'M-9-2026-20': (r'设 $M(x_0,y_0)$ 是曲线 $y=\frac1{1+x^2}\ (x\ge0)$ 的拐点，$O$ 为坐标原点。区域 $D$ 是第一象限中由曲线 $y=\frac1{1+x^2}\ (x\ge x_0)$、线段 $OM$ 及 $x$ 轴正半轴围成的无界区域，求区域 $D$ 绕 $x$ 轴旋转所生成的旋转体的体积。',None),
 'M-9-2026-21': (r'求微分方程 $x^2y^{\prime\prime}-2xy^{\prime}-(y^{\prime})^2=0\ (x>2)$ 满足 $y|_{x=3}=\frac12$、$y^{\prime}|_{x=3}=-9$ 的解。',None),
})
for target, source in {3:1,5:3,8:5,12:12,19:17,22:21}.items():
    TRANSCRIPTS[f'M-9-2026-{target:02d}'] = TRANSCRIPTS[f'M-8-2026-{source:02d}']

TRANSCRIPTS.update({
 'M-10-2011-14': (r'设二维随机变量 $(X,Y)$ 服从正态分布 $N(\mu,\mu;\sigma^2,\sigma^2;0)$，则 $E(XY^2)=$ ______。',None),
 'M-10-2013-23': (r'设总体 $X$ 的概率密度为 $f(x;\theta)=\begin{cases}\frac{\theta^2}{x^3}e^{-\theta/x},&x>0,\\0,&\text{其他},\end{cases}$ 其中 $\theta$ 为未知参数且大于零。$X_1,X_2,\ldots,X_n$ 为来自总体 $X$ 的简单随机样本。' '\n\n' r'（1）求 $\theta$ 的矩估计量。' '\n\n' r'（2）求 $\theta$ 的最大似然估计量。',None),
 'M-10-2014-14': (r'设总体 $X$ 的概率密度为 $f(x;\theta)=\begin{cases}\frac{2x}{3\theta^2},&\theta<x<2\theta,\\0,&\text{其他},\end{cases}$ 其中 $\theta$ 是未知参数。$X_1,X_2,\ldots,X_n$ 为来自总体 $X$ 的简单随机样本。若 $E(c\sum_{i=1}^nX_i^2)=\theta^2$，则 $c=$ ______。',None),
 'M-10-2020-19': (r'设函数 $f(x)$ 在区间 $[0,2]$ 上具有连续导数，$f(0)=f(2)=0$，$M=\max_{x\in[0,2]}\{|f(x)|\}$。证明：' '\n\n' r'（1）存在 $\xi\in(0,2)$，使得 $|f^{\prime}(\xi)|\ge M$。' '\n\n' r'（2）若对任意的 $x\in(0,2)$，$|f^{\prime}(x)|\le M$，则 $M=0$。',None),
 'M-10-2021-22': (r'在区间 $(0,2)$ 上随机取一点，将该区间分成两段，较短一段的长度记为 $X$，较长一段的长度记为 $Y$，令 $Z=\frac YX$。' '\n\n' r'（1）求 $X$ 的概率密度。' '\n\n' r'（2）求 $Z$ 的概率密度。' '\n\n' r'（3）求 $E(\frac XY)$。',None),
 'M-10-2026-01': (r'$f(x)=xe^{1/x}$ 的渐近线（　）。',[r'无水平渐近线，无铅直渐近线',r'有水平渐近线，有铅直渐近线',r'无水平渐近线，有铅直渐近线',r'有水平渐近线，无铅直渐近线']),
 'M-10-2026-04': (r'设 $t$ 时刻某证券的交易单价为 $p(t)$，某机构持有该证券的份额为 $q(t)$。若该机构在 $t\in[0,T]$ 持续购入一定份额该证券，则这些证券的平均购入价格为（　）。',[r'$\frac1T\int_0^Tp(t)\,dt$',r'$\frac1{q(T)-q(0)}\int_0^Tp(t)\,dt$',r'$\frac1T\int_0^Tp(t)q^{\prime}(t)\,dt$',r'$\frac1{q(T)-q(0)}\int_0^Tp(t)q^{\prime}(t)\,dt$']),
 'M-10-2026-06': (r'$A$ 为三阶非零矩阵，$A^*$ 为 $A$ 的伴随矩阵，$A^*=-2A$，则 $A^2=$（　）。',[r'$\begin{pmatrix}-4&0&0\\0&-4&0\\0&0&-4\end{pmatrix}$',r'$\begin{pmatrix}-4&0&0\\0&-4&0\\0&0&4\end{pmatrix}$',r'$\begin{pmatrix}-4&0&0\\0&4&0\\0&0&4\end{pmatrix}$',r'$\begin{pmatrix}4&0&0\\0&4&0\\0&0&4\end{pmatrix}$']),
 'M-10-2026-08': (r'已知随机变量 $X$ 和 $Y$ 独立同分布，且 $X$ 的概率密度为 $f(x)=\begin{cases}\frac1{(1+x)^2},&x>0,\\0,&x\le0,\end{cases}$ 则 $P\{XY\le1\}=$（　）。',[r'$\frac34$',r'$\frac12$',r'$\frac13$',r'$\frac16$']),
 'M-10-2026-09': (r'随机变量 $X\sim N(0,1)$，随机变量 $Y\sim B(2,\frac12)$，且 $X$ 与 $Y$ 独立，则 $XY$ 与 $X+Y$ 的相关系数为（　）。',[r'$\frac{\sqrt6}3$',r'$\frac{\sqrt2}2$',r'$\frac23$',r'$\frac12$']),
 'M-10-2026-11': (r'$\displaystyle\int_0^1x(x-1)(x-\frac12)\,dx=$ ______。',None),
 'M-10-2026-12': (r'极限 $\displaystyle\lim_{x\to0}\frac1x\left(\frac{\sqrt{1+x^2}}{\sin x}-\frac1{\tan x}\right)=$ ______。',None),
 'M-10-2026-14': (r'微分方程 $y^{\prime\prime}-2y^{\prime}=e^x$ 满足条件 $y(0)=1,y^{\prime}(0)=1$ 的解为 $y=$ ______。',None),
 'M-10-2026-17': (r'已知函数 $f(x)$ 满足 $f(x)=\frac1{(2-x)^2}-\int_0^1f(x)\,dx$，将 $f(x)$ 展开为 $x$ 的幂级数。',None),
 'M-10-2026-20': (r'已知平面区域 $D=\{(x,y)\mid0\le x\le1,0\le y\le1\}$，计算二重积分 $\iint_D\frac{y}{(1+x^2+y^2)^{3/2}}\,dx\,dy$。',None),
})
for target, source in {2:'8-01',3:'9-06',5:'9-09',7:'9-10',10:'8-10',13:'9-11',15:'9-16',16:'8-16',18:'9-18',19:'8-17',21:'8-21',22:'8-22'}.items():
    group, no = source.split('-')
    TRANSCRIPTS[f'M-10-2026-{target:02d}'] = TRANSCRIPTS[f'M-{group}-2026-{no}']

# Missing or malformed historical transcription fragments, checked against images.
TRANSCRIPTS.update({
 'M-8-2010-07': (r'设随机变量 $X$ 的分布函数 $F(x)=\begin{cases}0,&x<0,\\\frac12,&0\le x<1,\\1-e^{-x},&x\ge1,\end{cases}$ 则 $P\{X=1\}=$（　）。',[r'$0$',r'$\frac12$',r'$\frac12-e^{-1}$',r'$1-e^{-1}$']),
 'M-8-2010-10': (r'$\displaystyle\int_0^{\pi^2}\sqrt x\cos\sqrt x\,dx=$ ______。',None),
 'M-8-2011-15': (r'求极限 $\displaystyle\lim_{x\to0}\left[\frac{\ln(1+x)}x\right]^{\frac1{e^x-1}}$。',None),
 'M-10-2021-11': (r'若 $y=\cos e^{-\sqrt x}$，则 $\left.\frac{dy}{dx}\right|_{x=1}=$ ______。',None),
 'M-10-2018-10': (r'$\displaystyle\int e^x\arcsin\sqrt{1-e^{2x}}\,dx=$ ______。',None),
 'M-10-2011-09': (r'设 $f(x)=\lim_{t\to0}x(1+3t)^{x/t}$，则 $f^{\prime}(x)=$ ______。',None),
 'M-10-2012-15': (r'求极限 $\displaystyle\lim_{x\to0}\frac{e^{x^2}-e^{2-2\cos x}}{x^4}$。',None),
 'M-10-2017-15': (r'求 $\displaystyle\lim_{x\to0^+}\frac{\int_0^x\sqrt{x-t}\,e^t\,dt}{\sqrt{x^3}}$。',None),
 'M-10-2022-03': (r'已知 $f(t)$ 连续，令 $F(x,y)=\int_0^{x-y}(x-y-t)f(t)\,dt$，则（　）。',[r'$\frac{\partial F}{\partial x}=\frac{\partial F}{\partial y},\frac{\partial^2F}{\partial x^2}=\frac{\partial^2F}{\partial y^2}$',r'$\frac{\partial F}{\partial x}=\frac{\partial F}{\partial y},\frac{\partial^2F}{\partial x^2}=-\frac{\partial^2F}{\partial y^2}$',r'$\frac{\partial F}{\partial x}=-\frac{\partial F}{\partial y},\frac{\partial^2F}{\partial x^2}=\frac{\partial^2F}{\partial y^2}$',r'$\frac{\partial F}{\partial x}=-\frac{\partial F}{\partial y},\frac{\partial^2F}{\partial x^2}=-\frac{\partial^2F}{\partial y^2}$']),
 'M-10-2015-04': (r'下列级数中发散的是（　）。',[r'$\sum_{n=1}^{\infty}\frac n{3^n}$',r'$\sum_{n=1}^{\infty}\frac1{\sqrt n}\ln(1+\frac1n)$',r'$\sum_{n=2}^{\infty}\frac{(-1)^n+1}{\ln n}$',r'$\sum_{n=1}^{\infty}\frac{n!}{n^n}$']),
 'M-9-2018-11': (r'$\displaystyle\int_5^{+\infty}\frac1{x^2-4x+3}\,dx=$ ______。',None),
 'M-9-2024-07': (r'设非负函数 $f(x)$ 在 $[0,+\infty)$ 上连续，给出以下三个命题：' '\n\n' r'①若 $\int_0^{+\infty}f^2(x)\,dx$ 收敛，则 $\int_0^{+\infty}f(x)\,dx$ 收敛。' '\n\n' r'②若存在 $p>1$，使得 $\lim_{x\to+\infty}x^pf(x)$ 存在，则 $\int_0^{+\infty}f(x)\,dx$ 收敛。' '\n\n' r'③若 $\int_0^{+\infty}f(x)\,dx$ 收敛，则存在 $p>1$，使得 $\lim_{x\to+\infty}x^pf(x)$ 存在。' '\n\n' r'其中真命题的个数为（　）。',['0','1','2','3']),
 'M-9-2025-06': (r'设单位质点 $P,Q$ 分别位于点 $(0,0)$ 和 $(0,1)$ 处，$P$ 从点 $(0,0)$ 出发沿 $x$ 正向移动，记 $G$ 为引力常量，则当质点 $P$ 移动到点 $(l,0)$ 时，克服质点 $Q$ 的引力所做的功为（　）。',[r'$\int_0^l\frac G{x^2+1}\,dx$',r'$\int_0^l\frac{Gx}{(x^2+1)^{3/2}}\,dx$',r'$\int_0^l\frac G{(x^2+1)^{3/2}}\,dx$',r'$\int_0^l\frac{G(x+1)}{(x^2+1)^{3/2}}\,dx$']),
})
TRANSCRIPTS['M-9-2017-15'] = TRANSCRIPTS['M-10-2017-15']
TRANSCRIPTS['M-9-2022-04'] = TRANSCRIPTS['M-10-2022-03']
