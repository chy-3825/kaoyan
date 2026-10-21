# 构建与题库更新

## 使用已有题库打包

需要 Python 3.10+、JDK 17，以及 Android SDK Build Tools 36 与 Android 平台包。
构建器不是 Gradle 工程，直接调用 `aapt2`、`d8`、`zipalign`、`apksigner`、`javac`、`keytool`。

现有脚本期望以下布局（版本目录名称可不同）：

```text
$YANXI_ANDROID_SDK/
├── tools/36.0.0/             # aapt2、d8、zipalign、apksigner 及对应 lib/
└── platform/android-36/      # android.jar 等平台文件
```

默认路径为 `~/.cache/yanxi-android`；这不是标准 SDK 目录布局。使用已有标准 SDK 时，可在单独目录中建立 `tools/<版本>` 指向 `build-tools/<版本>`、`platform/<版本>` 指向 `platforms/<版本>` 的符号链接，再设置 `YANXI_ANDROID_SDK`。需保持工具附带的 `lib/` 等文件完整。

例如构建线代：

```sh
export YANXI_ANDROID_SDK=/path/to/compatible-sdk-layout
cd apps/linear-algebra
python3 android/build.py
```

其他 App 替换目录即可；APK 和 SHA-256 校验文件输出到各 App 根目录。
首次构建会在其 `android/signing/` 创建本地签名私钥与密码。该目录被忽略，原始正式密钥不在仓库中。

## 题库检查

从仓库根目录运行：

```sh
python3 scripts/verify_repository.py
```

该检查验证 JSONL 和运行题库的一致性、题目与答案资源引用、Python 语法，以及当前待跟踪文件的敏感文件名和常见密钥格式。它不证明题目或答案内容正确。

## 更新题库（可选，会写入数据）

构建现有 APK 不需要此步骤。先保存当前数据再重新生成，以免覆盖已人工修改的题目。

数学总库联网更新依赖：

```sh
cd apps/math
python3 -m pip install -r requirements.txt
python3 scripts/build_bank.py
python3 scripts/build_2026_pdfs.py
python3 scripts/build_supplemental.py
```

PDF 脚本还需系统安装 Poppler 的 `pdftotext` 和 `pdftoppm`。网络源可变，重新生成结果不保证与快照相同；2026 裁图问题仍需修复。

高数、概率、线代的 `scripts/build_bank.py` 根据各自本地题库整理生成运行数据。更新数学总库不会自动同步到三个专题 App。

## 政治 App

政治分区保留原有独立 Web 版本 `app/dist/` 和 Android 版本 `android/web/`，两者功能版本不同，使用 Android 当前题库时以 `android/web/` 为准。构建与环境见 [Android 说明](../apps/politics/android/README.md)；题库重建依赖见其 `requirements.txt` 和根 README。
