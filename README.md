# 考研练习 · 研习系列

数学分为研习高数、研习线代、研习概率三个独立 App，另保留研习政治，共四个 Android 离线练习 App。按章节、考点练习，支持错题本、已有参考答案，以及使用个人 API Key 请求解析。

1.3.0 调整三个数学 App 界面：做题页底部固定解析、复制和收藏工具栏；题源可展开；图片选项下只显示 A–D 作答按钮；收藏夹展示题图缩略图，取消收藏后可撤销。首页缩小装饰区，统一线条图标，保留原卷点击放大及绿／红描边自评。

## 直接下载 APK

四个安装包发布于 [2026-10-27 Release](https://github.com/chy-3825/kaoyan/releases/tag/apps-20261027)，附 [SHA-256 校验表](apk/SHA256SUMS)。数学题按原卷图片显示，点图可放大；“复制题目”复制排版文字和选项。每题均有解析：951 题为文字解析，其余 31 题直接查看原卷答案图。数学 App 还支持收藏夹及筛选、收藏练习、字号调整和旧学习记录迁移。主观题使用白底绿框绿字“正确”、白底红框红字“错误”。

| App | 版本 | 下载 |
| --- | --- | --- |
| 研习政治 | 1.7.0 | [下载 APK](https://github.com/chy-3825/kaoyan/releases/download/apps-20261027/yanxi-politics-1.7.0.apk) |
| 研习高数 | 1.3.0 | [下载 APK](https://github.com/chy-3825/kaoyan/releases/download/apps-20261027/yanxi-calculus-1.3.0.apk) |
| 研习概率 | 1.3.0 | [下载 APK](https://github.com/chy-3825/kaoyan/releases/download/apps-20261027/yanxi-probability-1.3.0.apk) |
| 研习线代 | 1.3.0 | [下载 APK](https://github.com/chy-3825/kaoyan/releases/download/apps-20261027/yanxi-linear-algebra-1.3.0.apk) |

APK 适用于 Android 8.0（API 26）及以上版本。高数、线代、概率分别独立安装，数一、数二、数三保留为题源标记。政治配图已修复，数学 2026 年题图沿用已修复裁图。


## 项目分区

| 分区 | App | 源码题数 | 历年题 / 补充题 | 入口 |
| --- | --- | ---: | ---: | --- |
| `apps/politics` | 研习政治 | 1,500 | 594 / 906 | [说明与构建](apps/politics/README.md) |
| `apps/calculus` | 研习高数 | 650 | 650 / 0 | [说明与构建](apps/calculus/README.md) |
| `apps/probability` | 研习概率 | 149 | 149 / 0 | [说明与构建](apps/probability/README.md) |
| `apps/linear-algebra` | 研习线代 | 183 | 183 / 0 | [说明与构建](apps/linear-algebra/README.md) |

三个数学 App 共 982 道合并后真题，对应原 1,224 条试卷记录；合并 242 条重复记录，所有原 ID、试卷出处及旧答题记录映射均保留。文字解析来自真题资料，部分缺失处已补推导；没有文字解析的题目保留原卷答案图。数一、数二、数三按相同题目合并，题目仍显示原卷图，复制功能使用文字版。政治内容不变。

## 各分区主要内容

- `android/src/`：Android 原生代码；`android/res/`、`AndroidManifest.xml`：图标、样式及应用配置。
- `android/web/`：HTML/CSS/JavaScript 界面、运行题库 `questions.js`、离线题图与答案图 `images/`。
- `data/`：JSONL 题库、统计；部分分区另含来源清单和补充题源数据。
- `scripts/`：题库生成与校验脚本；`android/build.py`：APK 构建脚本。
- [`sources/math-bank/`](sources/math-bank/README.md) 保存原数学总库题源、维护脚本和 2026 原始 PDF，用于核对及重新裁图，没有数学总库 App。

为了保持各 App 独立构建，此次保留各自完整资源与目录，尚未抽取公共代码或图片。

## 开始使用

已有题库和图片随源码保存，构建 APK 不必先联网重新抓题。请按[构建说明](docs/BUILD.md)配置 JDK 与 Android SDK，然后进入相应 App 目录运行 `python3 android/build.py`。

可以在仓库根目录运行 `python3 scripts/verify_repository.py` 检查题库、图片引用、Python 语法和敏感文件排除情况。

## 版本与质量说明

源码目录保存当前快照，不提交签名密钥。四个当前版本的安装包在 [`apk/`](apk/)，历史安装包仍在 [旧版 Release](https://github.com/chy-3825/kaoyan/releases/tag/local-apk-archive-20261021)。研习数学总库 App 已由研习高数替换；原总库数据作为题源资料保留。高数使用独立包名和本地新签名，原研习数学的学习记录不会自动迁移；已安装历史高数版时可能需要先备份、卸载旧版再安装。

2026-10-26 已补齐政治两道原卷配图、修复并同步数学 2026 年题图裁切，并生成四个可安装 APK，详见[题图修复记录](docs/IMAGE_AUDIT.md)。答案小图过度放大等剩余问题见[问题清单](docs/KNOWN_ISSUES.md)；题库尚未经全部人工审核。

## 题库来源与授权说明

历年题目索引、考点、题图及部分参考答案来自 [lx-ruc/kaoyanshuxue](https://github.com/lx-ruc/kaoyanshuxue) 的公开整理资料，其说明提到真题墙；2026 年索引及原卷来源记录在 [来源清单](sources/math-bank/data/source_manifest.json)，包含 `static.kaoyan.cn` 等来源。数学自编补充题已删除。

保留来源信息不等于取得再发行授权；部分第三方题图与解析图的再发行授权尚未确认。代码与第三方题库素材的权利应分别判断。本仓库不以统一开源许可证授予第三方素材的使用权，也不承诺可作商业分发。

## 私密文件

正式签名私钥及密码、API 密钥、个人作答记录、草稿、解析缓存和本机 SDK 不应提交。各 App 首次本地构建会生成新的本地签名，不能代替旧安装包的正式签名；如需覆盖升级旧版本，应使用自己备份的原签名。

## 政治题库许可

政治题库中的 C-Eval、CMMLU 拓展题按原项目 CC BY-NC-SA 4.0 标注，来源与版本见 [政治来源清单](apps/politics/sources/manifest.json)和[项目说明](apps/politics/README.md)。第三方真题与解析授权情况另行说明，不适用代码的统一授权。
