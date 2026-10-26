# 考研数学 · 研习系列

四个独立 Android 离线练习 App 的源码与题库。按课程、章节、考点练习，支持错题本、已有参考答案，以及使用个人 API Key 请求解析。

## 项目分区

| 分区 | App | 源码题数 | 历年题 / 补充题 | 入口 |
| --- | --- | ---: | ---: | --- |
| `apps/politics` | 研习政治 | 1,500 | 594 / 906 | [说明与构建](apps/politics/README.md) |
| `apps/math` | 研习数学：数学一、二、三总库 | 1,464 | 1,224 / 240 | [说明与构建](apps/math/README.md) |
| `apps/probability` | 研习概率 | 221 | 181 / 40 | [说明与构建](apps/probability/README.md) |
| `apps/linear-algebra` | 研习线代 | 318 | 270 / 48 | [说明与构建](apps/linear-algebra/README.md) |

两个数学专题 App 与数学总库有题目重叠，以上题数不能相加作为独立题目总量。数学历年题涵盖 2009–2026 年；政治含 2009–2026 年真题选择题及 C-Eval、CMMLU 拓展题；补充练习单独标记，不冒充真题。

## 各分区主要内容

- `android/src/`：Android 原生代码；`android/res/`、`AndroidManifest.xml`：图标、样式及应用配置。
- `android/web/`：HTML/CSS/JavaScript 界面、运行题库 `questions.js`、离线题图与答案图 `images/`。
- `data/`：JSONL 题库、统计；部分分区另含来源清单和补充题源数据。
- `scripts/`：题库生成与校验脚本；`android/build.py`：APK 构建脚本。
- 数学总库另包含 `sources/2026/` 原始 PDF，用于重新裁图。

为了保持各 App 独立构建，此次保留各自完整资源与目录，尚未抽取公共代码或图片。

## 开始使用

已有题库和图片随源码保存，构建 APK 不必先联网重新抓题。请按[构建说明](docs/BUILD.md)配置 JDK 与 Android SDK，然后进入相应 App 目录运行 `python3 android/build.py`。

可以在仓库根目录运行 `python3 scripts/verify_repository.py` 检查题库、图片引用、Python 语法和敏感文件排除情况。

## 版本与质量说明

源码目录保存当前本地快照，不含正式签名密钥。历史五个 App 的安装包与 SHA-256 校验表已放在 [Releases 归档](https://github.com/chy-3825/kaoyan/releases/tag/local-apk-archive-20261021)，未重新构建。研习高数独立 App 已移除，高等数学题目仍保留在研习数学总库。数学总库源码已有 1,464 题，早期 1.0.0 APK 只有 1,224 题，两者不要混用为同一数据版本。

2026-10-26 已补齐政治两道原卷配图、修复并同步数学 2026 年题图裁切，详见[题图修复记录](docs/IMAGE_AUDIT.md)。答案小图过度放大等剩余问题见[问题清单](docs/KNOWN_ISSUES.md)；题库尚未经全部人工审核。

## 题库来源与授权说明

历年题目索引、考点、题图及部分参考答案来自 [lx-ruc/kaoyanshuxue](https://github.com/lx-ruc/kaoyanshuxue) 的公开整理资料，其说明提到真题墙；2026 年索引及原卷来源记录在 [来源清单](apps/math/data/source_manifest.json)，包含 `static.kaoyan.cn` 等来源。补充题保留原创专题练习标记。

保留来源信息不等于取得再发行授权；部分第三方题图与解析图的再发行授权尚未确认。代码与第三方题库素材的权利应分别判断。本仓库不以统一开源许可证授予第三方素材的使用权，也不承诺可作商业分发。

## 私密文件

正式签名私钥及密码、API 密钥、个人作答记录、草稿、解析缓存和本机 SDK 不应提交。数学 App 首次本地构建会生成新的本地签名，不能代替旧安装包的正式签名；如需覆盖升级旧版本，应使用自己备份的原签名。

## 政治题库许可

政治题库中的 C-Eval、CMMLU 拓展题按原项目 CC BY-NC-SA 4.0 标注，来源与版本见 [政治来源清单](apps/politics/sources/manifest.json)和[项目说明](apps/politics/README.md)。第三方真题与解析授权情况另行说明，不适用代码的统一授权。
