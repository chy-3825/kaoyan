# 数学题库维护资料

这里保留原研习数学总库的 1,464 道题、题图、来源清单、2026 原卷 PDF 和生成脚本，用于核对及维护三个专题 App。这里没有 Android 应用、安装入口或 APK 构建器。

三个独立 App 位于 `apps/calculus`、`apps/linear-algebra`、`apps/probability`，分别收录 925、318、221 题，题目 ID 集合互不重叠，合计 1,464 题。

- `data/`：原总库数据及来源。
- `generated/web/`：题库维护脚本输出的 `questions.js` 和全部原图，只作为题源资料。
- `sources/2026/`：原卷 PDF。
- `scripts/`：原抓题、裁图及补充题生成脚本，输出位置已改为 `generated/web/`。

在本目录运行原生成脚本会覆盖维护资料中的数据。正常打包无需运行它们。只重新裁图可用 `python3 scripts/build_2026_pdfs.py --images-only`，然后在仓库根目录运行 `python3 scripts/sync_math_images.py`，将图同步到三个 App。

更新题目内容时应按原题 ID 将更改应用到专题 App 的题库输入，再运行各 App 的 `scripts/build_bank.py`；图片同步脚本只同步图片。原来源及授权信息继续适用。
