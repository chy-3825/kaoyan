# 研习数学

Android 离线考研数学题库，覆盖数学一、数学二、数学三的 2009–2026 年真题，按课程、章节和考点训练。题目保留原卷图，适合含复杂公式的数学题。

## 题库

- 当前源码题库共 1,464 题：1,224 道历年题、240 道专题补充练习。此前本地 1.0.0 APK 只有 1,224 道历年题；本仓库保存的是含补充题的源码快照。
- 历年题包含 468 道选择题、180 道填空题和 576 道解答题；补充练习另计。
- 2026 年题目已补齐考点、答案和解答题原卷解析图；旧题目录使用来源索引的考点标签，少数原答案图缺失的题附有文字解答。
- 每题标 1–5 难度：旧题参考公开题库反馈和分值估算，2026 年人工估分。它是复习参考，不是官方评级。
- 各题提供考点提示；点击“DeepSeek 解析”可让视觉模型同时读取原题与现有答案/解析图，生成逐步说明。也可分享题图给其他 AI。

## App 功能

- 数学一、二、三分开选择；再按高等数学、线性代数、概率论与数理统计及各自考点目录筛题。
- 选择题自动核对；填空题、解答题可查看答案后自我评定。
- 本地保存作答进度和错题，可再次作答、标记掌握。
- 不配置 API Key 也能离线训练、查看已有答案图并使用错题本。

## 构建 APK

```sh
python3 -m pip install -r requirements.txt
python3 android/build.py
```

APK 输出到本 App 项目根目录。首次构建会在 `android/signing/` 生成本 App 专用签名密钥。

## 更新题库数据

```sh
python3 scripts/build_bank.py
python3 scripts/build_2026_pdfs.py
python3 scripts/build_supplemental.py
```

第二个脚本会从 `sources/2026/` 的原卷 PDF 重新切出 2026 题图、答案和解析图，并生成 `android/web/questions.js`。题量与数据缺项统计见 `data/summary.json`。

## 来源与使用

- 2009–2025 年题目索引、考点、答案键及题图：[`lx-ruc/kaoyanshuxue`](https://github.com/lx-ruc/kaoyanshuxue)，该项目 README 说明其数据来自真题墙。
- 2026 年题号索引来自真题墙；原卷题图和解析 PDF 来自 `static.kaoyan.cn`，具体源地址见 `data/source_manifest.json`。

来源方未提供可确认的再发行授权。当前题图用于个人离线备考；公开发布或商业分发前应先取得题目与答案图片的授权。

题库生成脚本可能覆盖当前题库；使用已有题库构建 APK 只需运行 `python3 android/build.py`。详细环境和更新顺序见[仓库构建说明](../../docs/BUILD.md)。
